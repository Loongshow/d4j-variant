#!/bin/zsh
# Resume the paid blocks after the 2026-10-10 credit halt: S2_cont -> P4 -> HO, stopping at the first halt (exit != 0).
cd "$(dirname "$0")/.." || exit 2
PY=/opt/miniconda3/bin/python
$PY scripts/mx_tmp_audit.py || { echo "chain refused: /private/tmp leftovers" >> diagnostic/run_chain2.out; exit 1; }
for p in S2_cont P4 HO; do
  $PY scripts/ct_driver.py --server mxF0 --plan plans/$p.json > diagnostic/run_${p}_2.out 2>&1; rc=$?
  echo "$p exit $rc $(date -u +%FT%TZ)" >> diagnostic/run_chain2.out
  [ $rc -eq 0 ] || exit $rc
done
echo "CHAIN DONE" >> diagnostic/run_chain2.out
