#!/bin/zsh
# Integrity record at a bug-block boundary. Usage: bug_block_inventory_v2.sh <CONTROL-ID> <TREATMENT-ID> <label> [preflight-target]
set -uo pipefail
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2; SU=$S/diagnostic-gpt56; V3=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3; RUNS=$V3/benchmark_runs/mini-swe-agent-openai-gpt-5-6
C=$1; T=$2; L=$3; PT=${4:-$T}; OUT=$SU/bug_block_${L}_inventory.txt
{ echo "== bug block $L ($C, $T) at $(date -u +%FT%TZ) =="
  echo "-- run artifact hashes"; (cd $RUNS && for V in $C $T; do [ -d $V ] && find $V -mindepth 2 -maxdepth 2 -type f; done | sort | xargs shasum -a 256 | sort -k2)
  echo "-- manifest sha256: $(shasum -a 256 $S/SCALEUP_MANIFEST.json | cut -c1-64)"
  echo "-- packages vs reference"; (cd $S && shasum -a 256 -c $SU/package_hashes.txt --quiet) && echo "all twelve packages unchanged" || echo "PACKAGE CHANGED"
  echo "-- server package copies"; (cd $V3/new_bug_variants && shasum -a 256 -c $SU/v3_packages_before.txt --quiet) && echo "server package copies unchanged" || echo "SERVER COPY CHANGED"
  echo "-- protected trees"; (cd $S && CRFLB_APPROVED_PAID_RUN=1 PREFLIGHT_ONLY=1 MP_TARGETS="$PT" MP_REPEATS=1 MP_MAX_RUNS=6 D4J_API_PORT=8792 zsh scripts/run_v2_attach.sh 2>&1 | grep -E "unchanged|refusing|PREFLIGHT_ONLY|discovered")
  echo "== end =="; } > $OUT 2>&1
grep -E "unchanged|CHANGED|refusing|== " $OUT | cut -c1-150; echo "record: $(basename $OUT) ($(wc -l < $OUT) lines)"
