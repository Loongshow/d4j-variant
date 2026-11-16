#!/bin/zsh
export PERL5LIB=$HOME/perl5/lib/perl5; MP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1; PY=/opt/miniconda3/bin/python
CFG=$MP/construction/chart/pair_config_chart.json
for ARM in control treatment; do ID=$($PY -c "import json;print(json.load(open('$CFG'))['${ARM}_id'])")
  echo "=== chart repro $ARM ($ID) start $(date -u +%FT%TZ) ==="
  $PY $MP/scripts/repro_pair.py $CFG $ARM $MP/repro/chart/$ARM-checkout $MP/packages/$ID $MP/repro/chart/${ARM:u}_REPRODUCTION.json > $MP/repro/chart/repro_$ARM.log 2>&1; echo "exit $?"; tail -1 $MP/repro/chart/repro_$ARM.log
done
echo "=== chart repro finished $(date -u +%FT%TZ) ==="
