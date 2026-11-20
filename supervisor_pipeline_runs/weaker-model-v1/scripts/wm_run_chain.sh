#!/bin/zsh
# Run a sequence of frozen plans on one server, stopping at the first halt. Usage: wm_run_chain.sh <server> <tag> <plan.json>...
# Refuses while any driver runs or /private/tmp holds leftovers. Holds the machine awake for its own lifetime (caffeinate -w),
# so sleep cannot stall a block even if the coordinating session goes idle (AMENDMENTS W3).
cd "$(dirname "$0")/.." || exit 2
PY=/opt/miniconda3/bin/python; SERVER=$1; TAG=$2; shift 2
pgrep -f "ct_driver.py" >/dev/null && { echo "refused: a driver is running" >> diagnostic/run_chain.out; exit 1; }
$PY scripts/mx_tmp_audit.py || { echo "refused: /private/tmp leftovers ($TAG)" >> diagnostic/run_chain.out; exit 1; }
caffeinate -i -w $$ &
for p in "$@"; do
  n=$(basename $p .json)
  $PY scripts/ct_driver.py --server $SERVER --plan $p > diagnostic/run_${n}.out 2>&1; rc=$?
  echo "$TAG $n exit $rc $(date -u +%FT%TZ)" >> diagnostic/run_chain.out
  [ $rc -eq 0 ] || exit $rc
done
echo "$TAG CHAIN DONE $(date -u +%FT%TZ)" >> diagnostic/run_chain.out
