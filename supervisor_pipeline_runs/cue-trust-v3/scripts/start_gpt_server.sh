#!/bin/zsh
# Start one cue-trust-v3 GPT-5.6 server from its patched root. Usage: start_gpt_server.sh <name> [stub_port]
#   Real servers (gptF0, gptF1, gptDiag): the OpenAI key comes from the caller's environment (D4J_OPENAI_API_KEY or OPENAI_API_KEY,
#   e.g. exported in your own terminal) or, if absent there, from the authorized env file. It is never printed or logged.
#   The node process gets an ALLOWLISTED environment (amendment A2): every other exported variable, including all Anthropic/Claude
#   variables and any OpenAI base-URL override, is removed, so requests can only go to api.openai.com. D4J_AGENT_ENV_ALLOWLIST=1
#   turns on P4, which further restricts what the agent's own bash commands can see.
#   Stub server (gptStub, gptStubF1): never reads any credential; points litellm at the local stand-in on 127.0.0.1:<stub_port>.
set -u
V3=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3
SP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs
NAME=$1; ROOT=$V3/models/$NAME; DIAG=$V3/diagnostic; mkdir -p $DIAG
CFG=$(/opt/miniconda3/bin/python -c "
import json;c=json.load(open('$V3/models/servers.json'))['$NAME']
assert c['provider']=='openai', 'not an OpenAI server'
print(c['model'],c['port'],c['inspection'],c['external_workspace_root'],c['reasoning_effort'],'1' if c.get('stub') else '0')") || { echo "refusing: $NAME is not an OpenAI server in servers.json"; exit 2; }
MODEL=${${(s: :)CFG}[1]}; PORT=${${(s: :)CFG}[2]}; INSP=${${(s: :)CFG}[3]}; EXT=${${(s: :)CFG}[4]}; EFFORT=${${(s: :)CFG}[5]}; STUB=${${(s: :)CFG}[6]}
[ -d $ROOT/variant-lab/server ] || { echo "no server root for $NAME"; exit 2; }
if [ -f $DIAG/server_$NAME.pid ] && kill -0 $(cat $DIAG/server_$NAME.pid) 2>/dev/null; then echo "$NAME already running pid $(cat $DIAG/server_$NAME.pid)"; exit 0; fi
if [ "$STUB" = "1" ]; then
  STUB_PORT=${2:-8899}
  unset OPENAI_API_KEY D4J_OPENAI_API_KEY 2>/dev/null
  export OPENAI_API_KEY=stub-not-a-credential OPENAI_BASE_URL=http://127.0.0.1:$STUB_PORT/v1
  SRC="stub 127.0.0.1:$STUB_PORT"
else
  # A3: one credential, chosen deterministically; values are compared, never printed
  CK=${D4J_OPENAI_API_KEY:-${OPENAI_API_KEY:-}}; CNAME=$([ -n "${D4J_OPENAI_API_KEY:-}" ] && echo D4J_OPENAI_API_KEY || echo OPENAI_API_KEY)
  if [ -n "${D4J_OPENAI_API_KEY:-}" ] && [ -n "${OPENAI_API_KEY:-}" ] && [ "$D4J_OPENAI_API_KEY" != "$OPENAI_API_KEY" ]; then
    echo "refusing: D4J_OPENAI_API_KEY and OPENAI_API_KEY are both set in the caller environment with different values; unset one"; exit 2; fi
  FK=""; FNAME=""
  if [ -f $SP/.env ]; then
    FK=$(/bin/zsh -c "set -a; . $SP/.env >/dev/null 2>&1; set +a; print -r -- \${D4J_OPENAI_API_KEY:-\${OPENAI_API_KEY:-}}")
    FNAME=$(/bin/zsh -c "set -a; . $SP/.env >/dev/null 2>&1; set +a; [ -n \"\${D4J_OPENAI_API_KEY:-}\" ] && echo D4J_OPENAI_API_KEY || { [ -n \"\${OPENAI_API_KEY:-}\" ] && echo OPENAI_API_KEY; }")
  fi
  if [ -n "$CK" ] && [ -n "$FK" ] && [ "$CK" != "$FK" ]; then
    echo "refusing: the caller environment ($CNAME) and the authorized env file ($FNAME) hold different OpenAI keys; keep one"; exit 2; fi
  if [ -n "$CK" ]; then KEY_VAL=$CK; SRC="caller environment ($CNAME)"
  elif [ -n "$FK" ]; then KEY_VAL=$FK; SRC="authorized env file ($FNAME)"
  else echo "BLOCKED_OPENAI_CREDENTIAL: neither D4J_OPENAI_API_KEY nor OPENAI_API_KEY is set in the caller environment or the authorized env file"; exit 2; fi
  unset FK CK
  export D4J_OPENAI_API_KEY=$KEY_VAL OPENAI_API_KEY=$KEY_VAL; unset KEY_VAL
fi
ALLOW=(PATH HOME USER LOGNAME SHELL TMPDIR LANG LC_ALL LC_CTYPE TERM JAVA_HOME PERL5LIB TZ D4J_OPENAI_API_KEY OPENAI_API_KEY)
[ "$STUB" = "1" ] && ALLOW+=(OPENAI_BASE_URL)
for v in ${(k)parameters[(R)*export*]}; do (( ${ALLOW[(Ie)$v]} )) || unset $v 2>/dev/null; done
export PERL5LIB=$HOME/perl5/lib/perl5 D4J_OPENAI_MODEL=$MODEL D4J_REASONING_EFFORT=$EFFORT D4J_AGENT_ENV_ALLOWLIST=1
export D4J_API_PORT=$PORT D4J_PROMPT_INSPECTION=$INSP D4J_EXTERNAL_WORKSPACE_ROOT=$EXT
mkdir -p $EXT
cd $ROOT/variant-lab
nohup node server/index.mjs > $DIAG/server_${NAME}_$PORT.log 2>&1 &
echo $! > $DIAG/server_$NAME.pid
echo "$(date -u +%FT%TZ) start $NAME pid $! port $PORT model $MODEL effort $EFFORT inspection $INSP ext $EXT env=allowlist p4=on credential_source=${SRC:-none}" >> $DIAG/server_lifecycle.log
echo "started $NAME pid $! port $PORT model $MODEL effort $EFFORT inspection $INSP ext $EXT env=allowlist p4=on credential_source=${SRC:-none}"
