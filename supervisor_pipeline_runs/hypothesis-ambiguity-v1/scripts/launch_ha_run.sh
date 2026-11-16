#!/bin/zsh
# Single-run wrapper for the HA block. Usage: launch_ha_run.sh <HA-LOW-01|HA-HIGH-01>
# Copies the newest PASSED probe record (<30 min old) into diagnostic/preflight_smoke_mp.json (the launcher refuses older records), then launches exactly ONE run
# of the target through run_ha_attach.sh (MP_REPEATS=1, MP_ALLOW_EXISTING=1, MP_MAX_RUNS=5). Never replaces or reruns anything.
set -u; setopt +o nomatch
HA=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/hypothesis-ambiguity-v1; RUNS=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6; PY=/opt/miniconda3/bin/python
V=${1:?target}; case "$V" in HA-LOW-01|HA-HIGH-01) ;; *) echo "refusing: $V is not an HA target"; exit 2;; esac
P=$(ls -t $HA/diagnostic/probe_ha_*.json 2>/dev/null | head -1); [ -n "$P" ] || { echo "refusing: no HA probe record"; exit 2; }
[ -n "$(find "$P" -mmin -30)" ] || { echo "refusing: newest probe $P is older than 30 min"; exit 2; }
$PY -c "import json,sys;d=json.load(open('$P'));sys.exit(0 if d.get('status')=='passed' else 1)" || { echo "refusing: newest probe $P did not pass"; exit 2; }
cp "$P" $HA/diagnostic/preflight_smoke_mp.json
N=$(ls -d $RUNS/$V/run-* 2>/dev/null | wc -l | tr -d ' '); NEXT=$(printf '%03d' $((N + 1)))
[ $((N + 1)) -le 5 ] || { echo "refusing: $V already has $N runs (block limit 5)"; exit 2; }
LOG=$HA/diagnostic/launcher_${V}_run-${NEXT}.log
echo "launcher sha256: $(shasum -a 256 $HA/scripts/run_ha_attach.sh | cut -c1-16) | probe: $(basename $P) | $(date -u +%FT%TZ)" > "$LOG"
(cd $HA && MP_TARGETS="$V" MP_REPEATS=1 MP_ALLOW_EXISTING=1 MP_MAX_RUNS=5 CRFLB_APPROVED_PAID_RUN=1 D4J_API_PORT=8792 nohup zsh $HA/scripts/run_ha_attach.sh >> "$LOG" 2>&1 &)
sleep 6; echo "launched $V run-$NEXT at $(date -u +%FT%TZ) | log: $LOG"; tail -2 "$LOG"
