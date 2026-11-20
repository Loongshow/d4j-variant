#!/bin/zsh
# Main run, batch 5 on (W45): run frozen plans one block at a time with the pre-registered per-block checks.
# Usage: mr_run_blocks.sh <server> <tag> <cap> <plan.json>...   (plans in order; each block = one plan)
# Before each block: lid open, server answers /api/env, mr_cost_guard k >= instances in the block, mx_tmp_audit CLEAN, driver --verify-only.
# Stops at the first failed check or non-zero chain exit. Appends to diagnostic/run_blocks_<tag>.out.
cd "$(dirname "$0")/.." || exit 2
PY=/opt/miniconda3/bin/python; SERVER=$1; TAG=$2; CAP=$3; shift 3
LOG=diagnostic/run_blocks_${TAG}.out; PORT=$($PY -c "import json;print(json.load(open('models/servers.json'))['$SERVER']['port'])")
say() { echo "$(date -u +%FT%TZ) $*" | tee -a $LOG; }
remaining=0; for p in "$@"; do remaining=$((remaining + $($PY -c "import json;print(len(json.load(open('$p'))['instances']))"))); done
for p in "$@"; do
  n=$(basename $p .json); k_in=$($PY -c "import json;print(len(json.load(open('$p'))['instances']))")
  ioreg -r -k AppleClamshellState -d 1 2>/dev/null | grep -q '"AppleClamshellState" = No' || { say "STOP $n: lid closed"; exit 3; }
  for i in $(seq 1 60); do curl -s --max-time 3 http://127.0.0.1:$PORT/api/env >/dev/null && break; sleep 5; done
  curl -s --max-time 3 http://127.0.0.1:$PORT/api/env >/dev/null || { say "STOP $n: server $SERVER not answering on $PORT"; exit 4; }
  G=$($PY scripts/mr_cost_guard.py --left $remaining --cap $CAP) || { say "STOP $n: guard refused: $G"; exit 5; }
  k=$(echo "$G" | $PY -c "import json,sys;print(json.load(sys.stdin)['k'])"); C=$(echo "$G" | $PY -c "import json,sys;print(round(json.load(sys.stdin)['C'],2))")
  say "guard before $n: C=$C k=$k (block has $k_in instances, $remaining remaining, cap $CAP)"
  [ "$k" -ge "$k_in" ] || { say "STOP $n: guard admits k=$k < $k_in"; exit 5; }
  $PY scripts/mx_tmp_audit.py >/dev/null || { say "STOP $n: /private/tmp leftovers"; $PY scripts/mx_tmp_audit.py | tee -a $LOG; exit 6; }
  $PY scripts/ct_driver.py --server $SERVER --plan $p --verify-only >/dev/null 2>&1 || { say "STOP $n: verify-only failed"; exit 7; }
  say "START $n"
  zsh scripts/wm_run_chain.sh $SERVER ${TAG}_${n} $p; rc=$?
  say "END $n exit $rc $(tail -1 diagnostic/run_chain.out)"
  [ $rc -eq 0 ] || { say "STOP after $n (chain exit $rc)"; exit $rc; }
  remaining=$((remaining - k_in))
done
say "ALL BLOCKS DONE ($TAG)"
