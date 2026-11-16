#!/bin/zsh
# Full analysis of the HA block (runs 1-5 of both arms; the three preserved provider-affected LOW attempts stay in the same JSON, flagged by status).
# Writes: hypothesis_ambiguity_results.json, analysis/tables_ha.md, analysis/data/phase_timing_ha_all.{json,md}, analysis/data/out_of_workspace_scan_ha_all.json
set -uo pipefail
HA=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/hypothesis-ambiguity-v1; MP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1
RUNS=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6; PY=/opt/miniconda3/bin/python
cd $HA
cp hypothesis_ambiguity_results.json analysis/data/hypothesis_ambiguity_results_incomplete_block_backup.json 2>/dev/null || true
$PY scripts/analyze_ha.py analysis/spec_ha.json $RUNS hypothesis_ambiguity_results.json --runs 1-5 && $PY scripts/render_ha_tables.py hypothesis_ambiguity_results.json analysis/tables_ha.md > /dev/null && echo "analyzer + tables done"
$PY $MP/scripts/phase_timing.py $RUNS analysis/data/phase_timing_ha_all.json analysis/data/phase_timing_ha_all.md HA-LOW-01:1-5 HA-HIGH-01:1-5 > /dev/null && echo "phase timing done"
$PY $MP/scripts/scan_out_of_workspace.py $RUNS analysis/data/out_of_workspace_scan_ha_all.json HA-LOW-01:1-5 HA-HIGH-01:1-5 | tail -3
echo "block analysis finished $(date -u +%FT%TZ)"
