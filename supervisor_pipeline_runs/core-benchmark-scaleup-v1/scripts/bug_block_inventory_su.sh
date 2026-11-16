#!/bin/zsh
# Records the integrity state at a bug-block boundary: run artifact hashes of the bug's two variants, package/server-copy byte-identity, protected trees
# (launcher PREFLIGHT_ONLY), manifest + prompt hash, v3 package-copy hashes. Usage: bug_block_inventory_su.sh <CONTROL-ID> <TREATMENT-ID> <label>
set -uo pipefail
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1; SU=$S/diagnostic-gpt56; V3=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3; RUNS=$V3/benchmark_runs/mini-swe-agent-openai-gpt-5-6
C=$1; T=$2; L=$3; PT=${4:-$T}; OUT=$SU/bug_block_${L}_inventory.txt   # PT = a target with an open slot, used only for the non-paid PREFLIGHT_ONLY protected-tree checks
{ echo "== bug block $L ($C, $T) integrity record at $(date -u +%FT%TZ) =="
  echo "-- run artifact hashes (top-level files of every run of both variants)"; (cd $RUNS && for V in $C $T; do [ -d $V ] && find $V -mindepth 2 -maxdepth 2 -type f; done | sort | xargs shasum -a 256 | sort -k2)
  echo "-- manifest sha256: $(shasum -a 256 $S/BENCHMARK_MANIFEST.json | cut -c1-64)"; echo "-- prompt: $(/opt/miniconda3/bin/python -c "import json;d=json.load(open('$V3/benchmark_runs/mini-swe-agent-openai-gpt-5-6/HA-HIGH-01/run-005/prompt.json'));print(d.get('version'),d.get('base_prompt_sha256'))")"
  echo "-- packages vs manifest reference"; (cd $S && shasum -a 256 -c $SU/package_hashes.txt --quiet) && echo "all ten packages unchanged" || echo "PACKAGE CHANGED"
  echo "-- server package copies"; (cd $V3/new_bug_variants && shasum -a 256 -c $SU/v3_packages_existing_before.txt --quiet) && echo "server package copies unchanged" || echo "SERVER PACKAGE COPY CHANGED"
  echo "-- protected trees (launcher preflight, non-paid)"; (cd $S && CRFLB_APPROVED_PAID_RUN=1 PREFLIGHT_ONLY=1 MP_TARGETS="$PT" MP_REPEATS=1 MP_ALLOW_EXISTING=1 MP_MAX_RUNS=5 D4J_API_PORT=8792 zsh scripts/run_su_attach.sh 2>&1 | grep -E "unchanged|refusing|PREFLIGHT_ONLY|discovered")
  echo "-- per-run prompt identity"; for RD in $RUNS/$C/run-* $RUNS/$T/run-*; do [ -f $RD/prompt.json ] && printf "%s %s\n" "${RD#$RUNS/}" "$(/opt/miniconda3/bin/python -c "import json;d=json.load(open('$RD/prompt.json'));print(d.get('version'),(d.get('base_prompt_sha256') or '')[:16])")"; done
  echo "== end =="; } > $OUT 2>&1; grep -E "unchanged|CHANGED|refusing|== " $OUT | cut -c1-160; echo "record: $OUT ($(wc -l < $OUT) lines)"
