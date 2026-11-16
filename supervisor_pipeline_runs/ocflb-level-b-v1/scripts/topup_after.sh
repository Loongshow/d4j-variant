#!/bin/sh
# Wait for a driver PID to exit, then top up that server's variants to the planned valid-attempt count (cap 4 extra per variant).
PID=$1; SERVER=$2; O=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1
while kill -0 "$PID" 2>/dev/null; do sleep 30; done
set -a; . /Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/.env; set +a
case $SERVER in opus*) D=$O/diagnostic-opus;; *) D=$O/diagnostic-sonnet;; esac
echo "[$(date -u +%FT%TZ)] driver $PID exited; topup $SERVER" >> $D/topup_$SERVER.log
/opt/miniconda3/bin/python $O/scripts/launch_runs.py topup $SERVER 4 >> $D/topup_$SERVER.log 2>&1
echo "[$(date -u +%FT%TZ)] topup done $SERVER" >> $D/topup_$SERVER.log
