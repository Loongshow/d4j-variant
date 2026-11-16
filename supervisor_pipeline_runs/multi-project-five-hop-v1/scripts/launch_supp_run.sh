#!/bin/zsh
# Single-run wrapper for the user-instructed Math supplementary block (run-006..010 per arm). Usage: launch_supp_run.sh <TARGET>
# Copies the newest PASSED probe record (<30 min old) into diagnostic/preflight_smoke_mp.json (the launcher refuses older records), then launches
# exactly ONE run of <TARGET> through run_multiproject_attach.sh (MP_REPEATS=1, MP_ALLOW_EXISTING=1, MP_MAX_RUNS=10). Never replaces or reruns anything.
set -u
MP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1; RUNS=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6; PY=/opt/miniconda3/bin/python
V=${1:?target}; case "$V" in MATH-NORM-CONTROL-01|MATH-NORM-TREATMENT-01) ;; *) echo "refusing: $V is not a Math supplementary target"; exit 2;; esac
P=$(ls -t $MP/diagnostic/probe_supp_*.json 2>/dev/null | head -1); [ -n "$P" ] || { echo "refusing: no supplementary probe record"; exit 2; }
[ -n "$(find "$P" -mmin -30)" ] || { echo "refusing: newest probe $P is older than 30 min"; exit 2; }
$PY -c "import json,sys;d=json.load(open('$P'));sys.exit(0 if d.get('status')=='passed' else 1)" || { echo "refusing: newest probe $P did not pass"; exit 2; }
cp "$P" $MP/diagnostic/preflight_smoke_mp.json
N=$(ls -d $RUNS/$V/run-* 2>/dev/null | wc -l | tr -d ' '); NEXT=$(printf '%03d' $((N + 1)))
[ $((N + 1)) -le 10 ] || { echo "refusing: $V already has $N runs (block limit 10)"; exit 2; }
LOG=$MP/diagnostic/launcher_supp_${V}_run-${NEXT}.log
echo "launcher sha256: $(shasum -a 256 $MP/scripts/run_multiproject_attach.sh | cut -c1-16) | probe: $(basename $P) | $(date -u +%FT%TZ)" > "$LOG"
(cd $MP && MP_TARGETS="$V" MP_REPEATS=1 MP_ALLOW_EXISTING=1 MP_MAX_RUNS=10 CRFLB_APPROVED_PAID_RUN=1 D4J_API_PORT=8792 nohup zsh $MP/scripts/run_multiproject_attach.sh >> "$LOG" 2>&1 &)
sleep 6; echo "launched $V run-$NEXT at $(date -u +%FT%TZ) | log: $LOG"; tail -2 "$LOG"
