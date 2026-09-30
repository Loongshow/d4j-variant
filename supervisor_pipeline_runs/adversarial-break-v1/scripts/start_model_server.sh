#!/bin/zsh
# Start one isolated model server for the adversarial programme.
# Usage: start_model_server.sh <model-id> <port> <root-name>
# Each model gets its OWN repoRoot (adversarial-break-v1/models/<root-name>/) so run trees never collide;
# all roots share the adversarial variants through a symlink. Provider env is pinned exactly as in the pilot.
set -u
SP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs; R=$SP/adversarial-break-v1
MODEL=$1; PORT=$2; NAME=$3; ROOT=$R/models/$NAME
if [ ! -d $ROOT/variant-lab ]; then
  mkdir -p $ROOT/benchmark_runs $ROOT/runs
  mkdir -p $ROOT/variant-lab
  cp -R $SP/anthropic-pilot-v1/variant-lab/server $ROOT/variant-lab/server
  cp $SP/anthropic-pilot-v1/variant-lab/package.json $ROOT/variant-lab/package.json
  ln -sfn /Users/shawnli/Desktop/Honours/defects4j/variant-lab/node_modules $ROOT/variant-lab/node_modules
  ln -sfn $R/new_bug_variants $ROOT/new_bug_variants
  ln -sfn /Users/shawnli/Desktop/Honours/defects4j/workspaces $ROOT/workspaces
fi
set -a; . $SP/.env; set +a
[ -n "${ANTHROPIC_API_KEY:-}" ] || { echo "refusing: no ANTHROPIC_API_KEY in the authorized env file"; exit 2; }
for v in OPENAI_API_KEY D4J_OPENAI_API_KEY D4J_OPENAI_MODEL OPENAI_BASE_URL D4J_OPENAI_BASE_URL ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_BASE \
         CLAUDE_CODE_MESSAGING_TOKEN CLAUDE_CODE_OAUTH_SCOPES CLAUDECODE CLAUDE_CODE_ENTRYPOINT CLAUDE_CODE_SESSION_ID; do unset $v 2>/dev/null; done
export ANTHROPIC_BASE_URL=https://api.anthropic.com
cd $ROOT/variant-lab
D4J_API_PORT=$PORT D4J_CLAUDE_MODEL=$MODEL nohup node server/index.mjs > $R/diagnostic/server_${NAME}_$PORT.log 2>&1 &
echo $! > $R/diagnostic/server_${NAME}.pid
echo "$NAME: pid $! port $PORT model $MODEL root $ROOT"
