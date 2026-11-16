#!/bin/zsh
# Prove that `defects4j test` executes under the exact environment a running OCFLB server hands to the agent.
# Usage: prove_runner_env.sh <server-pid> <checkout-dir> <trigger-test-id> <out.md>
# The harness builds the agent's process environment from the server's own environment (miniSweAgentAdapter.buildMiniSweProcessEnvironment
# -> buildProviderEnvironment(agent, this.env)), so the server process environment IS the agent environment apart from provider variables.
set -u
PID=$1; CK=$2; TRIG=$3; OUT=$4
ENVF=$(mktemp); ps eww -p $PID -o command= | tr ' ' '\n' | grep -E '^[A-Z_][A-Z0-9_]*=' | grep -vE '^(ANTHROPIC_API_KEY|D4J_ANTHROPIC_API_KEY)=' > $ENVF
PERL=$(grep '^PERL5LIB=' $ENVF | cut -d= -f2-); PATHV=$(grep '^PATH=' $ENVF | cut -d= -f2-); HOMEV=$(grep '^HOME=' $ENVF | cut -d= -f2-)
TMPW=$(mktemp -d)/work; cp -R $CK $TMPW
RES=$(cd $TMPW && env -i PATH="$PATHV" HOME="$HOMEV" PERL5LIB="$PERL" JAVA_HOME="${JAVA_HOME:-}" defects4j test -t $TRIG 2>&1 | tail -6)
{
echo "# Runner environment proof ($(date -u +%FT%TZ))"; echo
echo "Server pid $PID. PERL5LIB in the server process environment: \`${PERL:-<absent>}\`."
echo "Command executed with exactly the server's PATH/HOME/PERL5LIB (\`env -i\`) in a scratch copy of \`$CK\`:"; echo
echo '```'; echo "defects4j test -t $TRIG"; echo "$RES"; echo '```'; echo
if echo "$RES" | grep -q "Running ant" ; then echo "RESULT: PASS - the test runner executes through ant in the agent environment."; else echo "RESULT: FAIL - the runner did not execute; do not start paid runs."; fi
} > $OUT
rm -rf $(dirname $TMPW) $ENVF; cat $OUT | tail -3
