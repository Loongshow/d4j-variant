#!/bin/sh
# Wait for a driver PID to exit, then start the next attack block on the same server (one slot per server).
WAIT_PID=$1; MODEL=$2; ATTACKS=$3; PLANNED=$4
R=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1
while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 30; done
echo "[$(date -u +%FT%TZ)] driver $WAIT_PID exited; starting $MODEL $ATTACKS x$PLANNED" >> $R/diagnostic/queue_after.log
set -a; . /Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/.env; set +a
exec /opt/miniconda3/bin/python $R/scripts/attack_driver.py --model "$MODEL" --attacks "$ATTACKS" --planned "$PLANNED"
