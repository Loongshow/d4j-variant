#!/bin/zsh
# Fresh-checkout reproduction of one camouflage arm from its packaged patches only, then the
# UNCHANGED lexgate on the reproduced state. Usage: repro_and_lexgate_camo.sh <spec> <arm> <D4J project>
export PERL5LIB=$HOME/perl5/lib/perl5; PY=/opt/miniconda3/bin/python
LEX=/Users/shawnli/Desktop/Honours/defects4j/benchmark_runs/analysis/discriminating-campaign/recipe/lexgate.py
R=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1
C=$R/experiment-a-camouflage/construction; A=$R/experiment-a-camouflage
S=$1; ARM=$2; D4J=$3
CFG=$C/configs/$S/pair_config_$ARM.json
VID=$($PY -c "import json;print(json.load(open('$CFG'))['treatment_id'])")
CO=$A/repro/$VID-checkout; mkdir -p $A/repro $A/leakage
rm -rf $CO
echo "=== $VID repro start $(date -u +%FT%TZ)"
defects4j checkout -p $D4J -v 1f -w $CO > $A/repro/checkout_$VID.log 2>&1
$PY $R/scripts/repro_pair.py $CFG treatment $CO $C/packages/$VID $A/repro/${VID}_REPRODUCTION.json
$PY $R/scripts/render_payload.py $CFG $CO $A/leakage/rendered_payload_$VID.txt
GF=$($PY -c "import json;print(json.load(open('$CFG'))['treatment']['gold_file'])")
GM=$($PY -c "import json;print(json.load(open('$CFG'))['treatment']['gold_method'])")
GC=$($PY -c "import json;print(json.load(open('$CFG'))['treatment']['gold_class'])")
$PY $LEX --ws $CO --src src/main/java --gold-file $GF --gold-method $GM --gold-class $GC \
   --payload-file $A/leakage/rendered_payload_$VID.txt --json > $A/leakage/lexgate_$VID.json 2> $A/leakage/lexgate_$VID.err
echo "lexgate $VID verdict $($PY -c "import json;print(json.load(open('$A/leakage/lexgate_$VID.json')).get('verdict'))" 2>/dev/null)"
echo "=== $VID repro done $(date -u +%FT%TZ)"
