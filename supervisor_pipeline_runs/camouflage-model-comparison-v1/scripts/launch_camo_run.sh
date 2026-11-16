#!/bin/zsh
# Single-run wrapper for the camouflage block. Usage: launch_camo_run.sh <VARIANT-ID>
# Copies the newest fast_pass probe record (<30 min old) into diagnostic-gpt56/preflight_smoke_mp.json (the launcher refuses older records), then launches
# exactly ONE run of the target through run_camo_attach.sh (MP_REPEATS=1, MP_ALLOW_EXISTING=1, MP_MAX_RUNS=5). Never replaces or reruns anything.
set -u; setopt +o nomatch
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1; PR=$S/experiment-a-camouflage/diagnostic; RUNS=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6; PY=/opt/miniconda3/bin
V=${1:?target}
P=$(ls -t $PR/probe_camo_*.json 2>/dev/null | head -1); [ -n "$P" ] || { echo "refusing: no probe record"; exit 2; }
[ -n "$(find "$P" -mmin -30)" ] || { echo "refusing: newest probe $P is older than 30 min"; exit 2; }
$PY/python -c "import json,sys;d=json.load(open('$P'));sys.exit(0 if d.get('status')=='passed' else 1)" || { echo "refusing: newest probe $P did not pass"; exit 2; }
grep -q "$(basename $P .json | sed 's/probe_camo_/CAMO probe /') at .*fast_pass" $PR/health_gate_camo.log || { echo "refusing: newest probe $P was not a fast_pass"; exit 2; }
cp "$P" $PR/preflight_smoke_mp.json
N=$(ls -d $RUNS/$V/run-* 2>/dev/null | wc -l | tr -d ' '); NEXT=$(printf '%03d' $((N + 1)))
[ $((N + 1)) -le 5 ] || { echo "refusing: $V already has $N runs (block limit 5)"; exit 2; }
LOG=$PR/launcher_${V}_run-${NEXT}.log
echo "launcher sha256: $(shasum -a 256 $S/scripts/run_camo_attach.sh | cut -c1-16) | probe: $(basename $P) | $(date -u +%FT%TZ)" > "$LOG"
(cd $S && MP_TARGETS="$V" MP_REPEATS=1 MP_ALLOW_EXISTING=1 MP_MAX_RUNS=5 CRFLB_APPROVED_PAID_RUN=1 D4J_API_PORT=8792 nohup zsh $S/scripts/run_camo_attach.sh >> "$LOG" 2>&1 &)
sleep 6; echo "launched $V run-$NEXT at $(date -u +%FT%TZ) | log: $LOG"; tail -2 "$LOG"
