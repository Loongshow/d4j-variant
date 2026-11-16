#!/bin/zsh
export PERL5LIB=$HOME/perl5/lib/perl5; MP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1; PY=/opt/miniconda3/bin/python
P=chart; CFG=$MP/construction/$P/pair_config_$P.json; mkdir -p $MP/validation/$P
for ARM in control treatment; do
  ID=$($PY -c "import json;print(json.load(open('$CFG'))['${ARM}_id'])")
  echo "=== $P $ARM ($ID) start $(date -u +%FT%TZ) ==="
  $PY $MP/scripts/validate_pair.py $CFG $ARM $MP/construction/$P/work/$ARM $MP/packages/$ID $MP/validation/$P/${ARM:u}_VALIDATION.json > $MP/validation/$P/validate_$ARM.log 2>&1
  echo "=== $P $ARM exit $? end $(date -u +%FT%TZ) ==="; tail -1 $MP/validation/$P/validate_$ARM.log
done
echo "=== chart validation finished $(date -u +%FT%TZ) ==="
