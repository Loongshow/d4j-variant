#!/bin/sh
# Regenerate readiness, (re)build every analysis and results artifact, run integrity. Freeze is separate (freeze_benchmark.py) and happens once.
L=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1; PY=/opt/miniconda3/bin/python; cd $L
$PY scripts/build_readiness.py && $PY scripts/build_lb_review.py && $PY scripts/ocflb_metrics.py > /dev/null && $PY scripts/build_results.py && $PY scripts/build_lb_analysis.py && ([ -f BENCHMARK_MANIFEST.json ] && $PY scripts/integrity_check.py && $PY scripts/verify_execution.py || echo "not frozen yet")
