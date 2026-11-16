#!/bin/zsh
# Keeps the camouflage block moving across provider stall windows WITHOUT violating the frozen policy:
# it never replaces or reruns a slot (the driver counts existing run dirs, so a preserved
# infrastructure-affected slot stays consumed), and it only restarts the driver after THREE consecutive
# bounded fast probes. One driver at a time. Exits when all 30 planned slots have been attempted.
set -u
R=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1
D=$R/experiment-a-camouflage/diagnostic; PY=/opt/miniconda3/bin/python
RUNS=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6
VS=(LANG-CONV-CAMOUFLAGE-LOW LANG-CONV-CAMOUFLAGE-HIGH MATH-NORM-CAMOUFLAGE-LOW MATH-NORM-CAMOUFLAGE-HIGH JKC-SURR-CAMOUFLAGE-LOW JKC-SURR-CAMOUFLAGE-HIGH)
log() { echo "[$(date -u +%FT%TZ)] watcher: $1" | tee -a $D/resume_watcher.log; }
attempted() { local n=0; for v in $VS; do n=$((n + $(ls -d $RUNS/$v/run-* 2>/dev/null | wc -l))); done; echo $n; }
log "started; slots attempted so far: $(attempted)/30"
while true; do
  N=$(attempted)
  if [ "$N" -ge 30 ]; then log "all 30 slots attempted; exiting"; break; fi
  if pgrep -f "block_driver_camo.py" > /dev/null; then sleep 120; continue; fi
  if $PY $R/scripts/probe_camo.py 30 > /dev/null 2>&1; then
    ok=1
    for i in 2 3; do sleep 8; $PY $R/scripts/probe_camo.py 30 > /dev/null 2>&1 || { ok=0; break; }; done
    if [ "$ok" = "1" ]; then
      log "three consecutive fast probes; restarting the block driver at slot count $N"
      (cd $D && CRFLB_APPROVED_PAID_RUN=1 nohup $PY $R/scripts/block_driver_camo.py >> driver_stdout.log 2>&1 &)
      sleep 90
    else
      log "probe series broke after the first pass; waiting"
      sleep 240
    fi
  else
    sleep 240
  fi
done
