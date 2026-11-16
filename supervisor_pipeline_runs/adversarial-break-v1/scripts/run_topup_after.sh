#!/bin/sh
# wait for the Sonnet validity driver (PID $1) to exit, then run the sonnet46 top-ups (one slot on the sonnet46 server)
while kill -0 "$1" 2>/dev/null; do sleep 30; done
set -a; . /Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/.env; set +a
exec /opt/miniconda3/bin/python /Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts/topup_valid.py
