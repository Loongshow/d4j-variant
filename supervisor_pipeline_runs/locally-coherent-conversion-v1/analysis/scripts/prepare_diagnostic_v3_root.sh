#!/bin/zsh
# PREPARED, NOT EXECUTED. Builds an isolated diagnostic root for the Conversion pair (mirrors diagnostic-noncanonical-v1/v2):
# frozen server copy, symlinked read-only inputs, byte copies of the packages, historical agent profiles. No model call, no server started.
set -euo pipefail
D=/Users/shawnli/Desktop/Honours/defects4j; RR=$D/supervisor_pipeline_runs; LC=$RR/locally-coherent-conversion-v1; PR=$RR/diagnostic-noncanonical-v3
[ -e "$PR" ] && { echo "refusing: $PR exists"; exit 2; }
mkdir -p "$PR/variant-lab" "$PR/new_bug_variants/Lang/bug-1/L20" "$PR/benchmark_runs" "$PR/runs"
cp -R "$D/variant-lab/server" "$PR/variant-lab/server"; cp "$D/variant-lab/package.json" "$PR/variant-lab/"; ln -s "$D/variant-lab/node_modules" "$PR/variant-lab/node_modules"
ln -s "$D/workspaces" "$PR/workspaces"; ln -s "$D/framework" "$PR/framework"; cp "$D/benchmark_runs/agents.json" "$PR/benchmark_runs/agents.json"
for V in CONVERSION-CONTROL-01 CONVERSION-TREATMENT-01; do cp -R "$LC/$V" "$PR/new_bug_variants/Lang/bug-1/L20/$V"; (cd "$LC/$V" && shasum -a 256 variant.patch test.patch) | diff - <(cd "$PR/new_bug_variants/Lang/bug-1/L20/$V" && shasum -a 256 variant.patch test.patch) && echo "copy verified: $V"; done
echo "root prepared at $PR (no server started, no run created); server port for this root: 8792"
