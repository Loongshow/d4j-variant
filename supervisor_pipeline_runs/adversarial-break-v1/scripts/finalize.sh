#!/bin/sh
# Regenerate every table and the manifest; list any unfilled narrative markers.
R=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1; PY=/opt/miniconda3/bin/python
$PY $R/scripts/attack_run_metrics.py $R/analysis/per_run/attack_run_metrics.json > /dev/null && $PY $R/scripts/build_break_reports.py && $PY $R/scripts/build_manifest_break.py
echo "unfilled markers:"; grep -c "SONNET_PENDING" $R/*.md $R/analysis/narratives/*.md | grep -v ":0$" || echo "  none"
