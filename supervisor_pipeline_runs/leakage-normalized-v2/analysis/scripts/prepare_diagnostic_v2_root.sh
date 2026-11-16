#!/bin/zsh
# PREPARED, NOT EXECUTED. Builds an isolated diagnostic root for the -02 pair, mirroring diagnostic-noncanonical-v1
# (frozen server copy, symlinked read-only inputs, byte copies of the -02 packages, historical agent profiles).
# Performs NO model call and starts NO server. Refuses to touch an existing root.
set -euo pipefail
D=/Users/shawnli/Desktop/Honours/defects4j; RR=$D/supervisor_pipeline_runs; V2=$RR/leakage-normalized-v2; PR=$RR/diagnostic-noncanonical-v2
[ -e "$PR" ] && { echo "refusing: $PR exists"; exit 2; }
mkdir -p "$PR/variant-lab" "$PR/new_bug_variants/Lang/bug-1/L20" "$PR/benchmark_runs" "$PR/runs"
cp -R "$D/variant-lab/server" "$PR/variant-lab/server"; cp "$D/variant-lab/package.json" "$PR/variant-lab/"; ln -s "$D/variant-lab/node_modules" "$PR/variant-lab/node_modules"
ln -s "$D/workspaces" "$PR/workspaces"; ln -s "$D/framework" "$PR/framework"; cp "$D/benchmark_runs/agents.json" "$PR/benchmark_runs/agents.json"
for V in NUMBERUTILS-CONTROL-02 NUMBERUTILS-TREATMENT-02; do cp -R "$V2/$V" "$PR/new_bug_variants/Lang/bug-1/L20/$V"; (cd "$V2/$V" && shasum -a 256 variant.patch test.patch) | diff - <(cd "$PR/new_bug_variants/Lang/bug-1/L20/$V" && shasum -a 256 variant.patch test.patch) && echo "copy verified: $V"; done
echo "root prepared at $PR (no server started, no run created). The L20 path segment is a discovery slot only."
