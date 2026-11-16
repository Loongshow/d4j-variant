#!/bin/zsh
# Runs the frozen observable-only analyzers over the twelve v2 variants: per-bug trajectory analysis, per-bug tables, phase timing, out-of-workspace scan.
set -uo pipefail
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2; MP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1/scripts
RUNS=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6; PY=/opt/miniconda3/bin/python; A=$S/results-gpt56/analysis; RANGE=${1:-1-5}
for PAIR in CMP-CKSUM-01 CMP-LAYOUT-02 CMP-OCTAL-03 JKC-SURR-04 JKC-OFFSET-05 CMP-ALIGN-06; do
  $PY $MP/analyze_multiproject.py $A/spec_$PAIR.json $RUNS $A/per_bug/${PAIR}_results.json --runs $RANGE > $A/per_bug/${PAIR}_analyze_stdout.txt 2>&1 && echo "analyzed $PAIR: $(grep -c '^###' $A/per_bug/${PAIR}_analyze_stdout.txt) runs" || { echo "analyzer failed for $PAIR"; tail -3 $A/per_bug/${PAIR}_analyze_stdout.txt; }
  [ -s $A/per_bug/${PAIR}_results.json ] && $PY $MP/render_multiproject_tables.py $A/per_bug/${PAIR}_results.json $A/tables/tables_$PAIR.md > /dev/null 2>&1 && echo "  tables -> analysis/tables/tables_$PAIR.md"
done
V="CMP-CKSUM-CONTROL-01 CMP-CKSUM-TREATMENT-01 CMP-LAYOUT-CONTROL-02 CMP-LAYOUT-TREATMENT-02 CMP-OCTAL-CONTROL-03 CMP-OCTAL-TREATMENT-03 JKC-SURR-CONTROL-04 JKC-SURR-TREATMENT-04 JKC-OFFSET-CONTROL-05 JKC-OFFSET-TREATMENT-05 CMP-ALIGN-CONTROL-06 CMP-ALIGN-TREATMENT-06"
$PY $MP/phase_timing.py $RUNS $A/per_run/phase_timing_v2.json $A/per_run/phase_timing_v2.md ${=V} > /dev/null 2>&1 && echo "phase timing -> $($PY -c "import json;print(len(json.load(open('$A/per_run/phase_timing_v2.json'))))") runs"
$PY $MP/scan_out_of_workspace.py $RUNS $A/per_run/out_of_workspace_scan_v2.json ${=V} > /dev/null 2>&1 && echo "oow scan: $($PY -c "import json;print(json.load(open('$A/per_run/out_of_workspace_scan_v2.json'))['summary'])")"
