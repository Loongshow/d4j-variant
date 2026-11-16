#!/bin/zsh
# Fresh-checkout reproduction of both arms of one bug from the packaged patches only, then the unchanged lexgate on the patched
# reproduction states (payload = failing test id + test source + Defects4J failure text). Usage: repro_and_lexgate.sh <proj> <bug-dir> <D4J project>
export PERL5LIB=$HOME/perl5/lib/perl5; S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1; PY=/opt/miniconda3/bin/python
LEX=/Users/shawnli/Desktop/Honours/defects4j/benchmark_runs/analysis/discriminating-campaign/recipe/lexgate.py
P=$1; B=$2; D4J=$3; CFG=$S/$P/$B/pair_config.json; R=$S/$P/$B/repro; A=$S/$P/$B/analysis/leakage; mkdir -p $R $A
SRC=$($PY -c "import json;print(json.load(open('$CFG'))['src_dir'])")
for ARM in control treatment; do
  ID=$($PY -c "import json;print(json.load(open('$CFG'))['${ARM}_id'])"); CO=$R/$ARM-checkout; rm -rf $CO
  defects4j checkout -p $D4J -v 1f -w $CO > $R/checkout_$ARM.log 2>&1
  echo "=== $P $B repro $ARM ($ID) start $(date -u +%FT%TZ) ==="
  $PY $S/scripts/repro_pair.py $CFG $ARM $CO $S/$P/$B/packages/$ID $R/${ARM:u}_REPRODUCTION.json > $R/repro_$ARM.log 2>&1; echo "exit $?"; tail -1 $R/repro_$ARM.log | cut -c1-300
  # lexgate on the patched reproduction state (failing_tests written by the trigger runs)
  $PY $S/scripts/render_payload.py $CFG $CO $A/rendered_payload_$ARM.txt
  GF=$($PY -c "import json;a=json.load(open('$CFG'))['$ARM'];print(a['gold_file'])"); GM=$($PY -c "import json;a=json.load(open('$CFG'))['$ARM'];print(a['gold_method'])"); GC=$($PY -c "import json;a=json.load(open('$CFG'))['$ARM'];print(a['gold_class'])")
  $PY $LEX --ws $CO --src $SRC --gold-file $GF --gold-method $GM --gold-class $GC --payload-file $A/rendered_payload_$ARM.txt --json > $A/lexgate_$ARM.json 2> $A/lexgate_$ARM.err; echo "lexgate $ARM exit $? verdict $($PY -c "import json;print(json.load(open('$A/lexgate_$ARM.json')).get('verdict'))" 2>/dev/null)"
done
echo "=== $P $B repro+lexgate finished $(date -u +%FT%TZ) ==="
