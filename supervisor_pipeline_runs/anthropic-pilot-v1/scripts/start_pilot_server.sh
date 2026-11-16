#!/bin/zsh
# Starts the ISOLATED Anthropic pilot server (patched copy of the frozen harness) on port 8793.
#
# Provider environment is PINNED EXPLICITLY rather than inherited, so the run provenance is unambiguous:
#   - ANTHROPIC_API_KEY comes only from the benchmark area's own authorized .env, into this process only;
#     it is never echoed, never written to a file and never passed on a command line.
#   - ANTHROPIC_BASE_URL is pinned to the official endpoint instead of whatever the parent shell had.
#   - Every Claude Code variable that could redirect auth or routing is cleared.
#   - No OpenAI credential is provided, so this instance cannot spend OpenAI money at all.
# The user's frozen GPT-5.6 server is a separate process on port 8792 and is never touched by this script.
set -u
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs
R=$S/anthropic-pilot-v1
MODEL=${D4J_CLAUDE_MODEL:-claude-opus-5-5}
set -a; . $S/.env; set +a
[ -n "${ANTHROPIC_API_KEY:-}" ] || { echo "refusing: ANTHROPIC_API_KEY not present in the authorized env file"; exit 2; }
for v in OPENAI_API_KEY D4J_OPENAI_API_KEY D4J_OPENAI_MODEL OPENAI_BASE_URL D4J_OPENAI_BASE_URL \
         ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_BASE CLAUDE_CODE_MESSAGING_TOKEN CLAUDE_CODE_OAUTH_SCOPES \
         CLAUDECODE CLAUDE_CODE_ENTRYPOINT CLAUDE_CODE_SESSION_ID; do unset $v 2>/dev/null; done
export ANTHROPIC_BASE_URL=https://api.anthropic.com
cd $R/variant-lab
D4J_API_PORT=8793 D4J_CLAUDE_MODEL=$MODEL nohup node server/index.mjs > $R/diagnostic/server_8793.log 2>&1 &
PID=$!
echo $PID > $R/diagnostic/pilot_server.pid
echo "pilot server pid $PID on port 8793 | model $MODEL | endpoint api.anthropic.com (pinned)"
