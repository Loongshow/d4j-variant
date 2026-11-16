#!/bin/zsh
LC=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/locally-coherent-conversion-v1
export PERL5LIB=$HOME/perl5/lib/perl5
echo "=== validation started $(date) ==="
for arm in control treatment; do ARM=$(echo $arm | tr a-z A-Z); echo "--- $ARM-01: $(date) ---"
  /opt/miniconda3/bin/python "$LC/analysis/scripts/validate_pair.py" "$LC/analysis/pair_config.json" $arm "$LC/work/$arm" "$LC/CONVERSION-$ARM-01" "$LC/validation/${ARM}01_VALIDATION.json"
  echo "--- $ARM-01 done: $(date) ---"; done
echo "=== validation finished $(date) ==="
