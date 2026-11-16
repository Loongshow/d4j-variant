#!/bin/zsh
# Real Phase-5 run of the supervisor's pipeline (unmodified) on Lang-1f, seed 42.
# Prerequisite: ANTHROPIC_API_KEY exported in the calling shell (never stored here).
set -e
RR=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs
export PERL5LIB=$HOME/perl5/lib/perl5                       # Defects4J's Perl deps live in ~/perl5 (local::lib)
export PYTHONPATH=$RR/shim                                   # stand-in for the missing trajectory-analysis/callgraph.py
if [ -f "$RR/.env" ]; then set -a; source "$RR/.env"; set +a; fi   # optional: KEY=VALUE lines, never printed
unset ANTHROPIC_BASE_URL                                     # make sure the SDK talks to the public API, not a harness proxy
: "${ANTHROPIC_API_KEY:?export ANTHROPIC_API_KEY first}"
cd "$RR"
rm -rf "$RR/real/repro-checkout"                             # generate_chain refuses to reuse an existing repro dir
mkdir -p "$RR/real"
git -C "$RR/lang-1f-checkout" checkout -- .                  # start from a clean tree
/opt/miniconda3/bin/python -u /Users/shawnli/Desktop/Honours/thesis/generate_chain.py \
  --project Lang \
  --seed 42 \
  --checkout-dir "$RR/lang-1f-checkout" \
  --source-root src/main/java \
  --test-root src/test/java \
  --out-dir "$RR/real/out" \
  --log-dir "$RR/real/logs" \
  --repro-scratch-dir "$RR/real/repro-checkout" \
  --min-class-lines 1200 \
  --min-host-lines 900 "$@" 2>&1 | tee -a "$RR/real/run.log"
