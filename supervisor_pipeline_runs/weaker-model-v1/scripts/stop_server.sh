#!/bin/zsh
# Stop one cue-trust-v3 server by its recorded PID only (never by name pattern).
V3=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/weaker-model-v1
NAME=$1; P=$V3/diagnostic/server_$NAME.pid
[ -f $P ] || { echo "no pid file for $NAME"; exit 0; }
PID=$(cat $P); if kill -0 $PID 2>/dev/null; then kill $PID; echo "$(date -u +%FT%TZ) stop $NAME pid $PID" | tee -a $V3/diagnostic/server_lifecycle.log; fi; rm -f $P
