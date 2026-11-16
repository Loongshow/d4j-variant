#!/bin/zsh
# Runs the frozen observable-only analyzers over the ten scale-up variants: per-bug trajectory analysis (multi-project analyzer, spec-driven), per-bug markdown
# tables, phase timing, out-of-workspace scan. Usage: analyze_all_su.sh [run-range e.g. 1-5]
set -uo pipefail
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1; MP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1/scripts
RUNS=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6; PY=/opt/miniconda3/bin/python; A=$S/results-gpt56/analysis; RANGE=${1:-1-5}
for PAIR in CHART-POLAR-02 CHART-PIE-03 MATH-BICUBIC-02 MATH-HARMONIC-03 LANG-FOLD-02; do
  $PY $MP/analyze_multiproject.py $A/spec_$PAIR.json $RUNS $A/per_bug/${PAIR}_results.json --runs $RANGE > $A/per_bug/${PAIR}_analyze_stdout.txt 2>&1 && echo "analyzed $PAIR: $(grep -c '^###' $A/per_bug/${PAIR}_analyze_stdout.txt) runs" || { echo "analyzer failed for $PAIR"; tail -3 $A/per_bug/${PAIR}_analyze_stdout.txt; }
  [ -s $A/per_bug/${PAIR}_results.json ] && $PY $MP/render_multiproject_tables.py $A/per_bug/${PAIR}_results.json $A/tables/tables_$PAIR.md > /dev/null 2>&1 && echo "  tables -> analysis/tables/tables_$PAIR.md"
done
V="CHART-POLAR-CONTROL-02 CHART-POLAR-TREATMENT-02 CHART-PIE-CONTROL-03 CHART-PIE-TREATMENT-03 MATH-BICUBIC-CONTROL-02 MATH-BICUBIC-TREATMENT-02 MATH-HARMONIC-CONTROL-03 MATH-HARMONIC-TREATMENT-03 LANG-FOLD-CONTROL-02 LANG-FOLD-TREATMENT-02"
$PY $MP/phase_timing.py $RUNS $A/per_run/phase_timing_su.json $A/per_run/phase_timing_su.md ${=V} > /dev/null 2>&1 && echo "phase timing -> analysis/per_run/phase_timing_su.json ($($PY -c "import json;print(len(json.load(open('$A/per_run/phase_timing_su.json'))))") runs)"
$PY $MP/scan_out_of_workspace.py $RUNS $A/per_run/out_of_workspace_scan_su.json ${=V} > /dev/null 2>&1 && echo "out-of-workspace scan -> analysis/per_run/out_of_workspace_scan_su.json: $($PY -c "import json;d=json.load(open('$A/per_run/out_of_workspace_scan_su.json'));print(d['summary'])")"
