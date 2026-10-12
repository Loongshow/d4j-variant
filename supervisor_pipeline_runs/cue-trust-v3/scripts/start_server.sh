#!/bin/zsh
# Start one cue-trust-v3 model server from its patched root. Usage: start_server.sh <name>   (names in models/servers.json)
# Provider env is read from the authorized env file and never printed; all other provider credentials are unset.
set -u
V3=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3
SP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs
NAME=$1; ROOT=$V3/models/$NAME; DIAG=$V3/diagnostic; mkdir -p $DIAG
CFG=$(/opt/miniconda3/bin/python -c "import json;c=json.load(open('$V3/models/servers.json'))['$NAME'];print(c['model'],c['port'],c['inspection'],c['external_workspace_root'])")
MODEL=$(echo $CFG | cut -d' ' -f1); PORT=$(echo $CFG | cut -d' ' -f2); INSP=$(echo $CFG | cut -d' ' -f3); EXT=$(echo $CFG | cut -d' ' -f4)
[ -d $ROOT/variant-lab/server ] || { echo "no server root for $NAME"; exit 2; }
if [ -f $DIAG/server_$NAME.pid ] && kill -0 $(cat $DIAG/server_$NAME.pid) 2>/dev/null; then echo "$NAME already running pid $(cat $DIAG/server_$NAME.pid)"; exit 0; fi
set -a; . $SP/.env; set +a
[ -n "${ANTHROPIC_API_KEY:-}" ] || { echo "refusing: no ANTHROPIC_API_KEY in the authorized env file"; exit 2; }
for v in OPENAI_API_KEY D4J_OPENAI_API_KEY D4J_OPENAI_MODEL OPENAI_BASE_URL D4J_OPENAI_BASE_URL ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_BASE \
         CLAUDE_CODE_MESSAGING_TOKEN CLAUDE_CODE_OAUTH_SCOPES CLAUDECODE CLAUDE_CODE_ENTRYPOINT CLAUDE_CODE_SESSION_ID; do unset $v 2>/dev/null; done
export ANTHROPIC_BASE_URL=https://api.anthropic.com
export PERL5LIB=$HOME/perl5/lib/perl5
mkdir -p $EXT
cd $ROOT/variant-lab
D4J_API_PORT=$PORT D4J_CLAUDE_MODEL=$MODEL D4J_PROMPT_INSPECTION=$INSP D4J_EXTERNAL_WORKSPACE_ROOT=$EXT nohup node server/index.mjs > $DIAG/server_${NAME}_$PORT.log 2>&1 &
echo $! > $DIAG/server_$NAME.pid
echo "$(date -u +%FT%TZ) start $NAME pid $! port $PORT model $MODEL inspection $INSP ext $EXT" | tee -a $DIAG/server_lifecycle.log
