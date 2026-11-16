#!/bin/zsh
# Validate both arms of one camouflage pair sequentially against that project's own checkout.
# Usage: validate_project_chain.sh <spec-name> <Project>
export PERL5LIB=$HOME/perl5/lib/perl5; PY=/opt/miniconda3/bin/python
R=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1; C=$R/experiment-a-camouflage/construction
S=$1; P=$2
for arm in low high; do
  VID=$($PY -c "import json;print(json.load(open('$C/specs/$S.json'))['arms']['$arm']['variant_id'])")
  echo "=== $VID start $(date -u +%FT%TZ)"
  $PY $R/scripts/validate_pair.py $C/configs/$S/pair_config_$arm.json treatment $C/checkouts/$P $C/packages/$VID $R/experiment-a-camouflage/validation/${VID}_VALIDATION.json
  echo "=== $VID done $(date -u +%FT%TZ)"
done
