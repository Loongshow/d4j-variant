#!/bin/zsh
export PERL5LIB=$HOME/perl5/lib/perl5; MP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1; PY=/opt/miniconda3/bin/python
CFG=$MP/construction/math/pair_config_math.json
for ARM in control treatment; do ID=$($PY -c "import json;print(json.load(open('$CFG'))['${ARM}_id'])")
  echo "=== math repro $ARM ($ID) start $(date -u +%FT%TZ) ==="
  $PY $MP/scripts/repro_pair.py $CFG $ARM $MP/repro/math/$ARM-checkout $MP/packages/$ID $MP/repro/math/${ARM:u}_REPRODUCTION.json > $MP/repro/math/repro_$ARM.log 2>&1; echo "exit $?"; tail -1 $MP/repro/math/repro_$ARM.log
done
echo "=== timing one Math full suite on the clean control checkout (for the report) $(date -u +%FT%TZ) ==="
cd $MP/construction/math/work/control && git reset -q -- . && git checkout -- . && rm -rf target && T0=$(date +%s) && defects4j compile > /dev/null 2>&1 && T1=$(date +%s) && defects4j test > $MP/validation/math/fullsuite_timing.log 2>&1; T2=$(date +%s); echo "compile $((T1-T0)) s; full suite $((T2-T1)) s; $(grep -m1 'Failing tests' $MP/validation/math/fullsuite_timing.log); executed $(wc -l < all_tests | tr -d ' ')"
echo "=== math repro finished $(date -u +%FT%TZ) ==="
