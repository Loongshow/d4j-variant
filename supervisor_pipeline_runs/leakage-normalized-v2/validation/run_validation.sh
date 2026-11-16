#!/bin/zsh
V2=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/leakage-normalized-v2
export PERL5LIB=$HOME/perl5/lib/perl5
echo "=== validation started $(date) ==="
for arm in control treatment; do
  ARM=$(echo $arm | tr a-z A-Z)
  echo "--- $ARM-02: $(date) ---"
  /opt/miniconda3/bin/python "$V2/analysis/scripts/validate_02.py" $arm "$V2/work/$arm" "$V2/NUMBERUTILS-$ARM-02" "$V2/validation/${ARM}02_VALIDATION.json"
  echo "--- $ARM-02 done: $(date) (exit $?) ---"
done
echo "=== validation finished $(date) ==="
