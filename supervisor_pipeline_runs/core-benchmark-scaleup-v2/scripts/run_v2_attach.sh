#!/bin/zsh
# NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6 — attach-mode launcher (one run per invocation via launch_v2_run.sh).
# Attaches ONLY to the already-running frozen v3 server that holds the credential in its own environment; never reads, prints, logs or persists
# credential values. Same preflight and protected-tree checks as the v1 block. PREFLIGHT_ONLY=1 stops before the smoke assertion.
set -euo pipefail
: "${CRFLB_APPROVED_PAID_RUN:?refusing: export CRFLB_APPROVED_PAID_RUN=1 only for the approved 60-run v2 block}"
D=/Users/shawnli/Desktop/Honours/defects4j; RR=$D/supervisor_pipeline_runs; S=$RR/core-benchmark-scaleup-v2; PR=$S/diagnostic-gpt56; V3=$RR/diagnostic-noncanonical-v3
SERVER_ROOT=${MP_SERVER_ROOT:-$V3}; AGENT=mini-swe-agent-openai-gpt-5-6; PORT=${D4J_API_PORT:-8792}; REPEATS=${MP_REPEATS:-1}; API="http://127.0.0.1:$PORT"; PY=/opt/miniconda3/bin/python
TARGETS=(${=MP_TARGETS:?refusing: MP_TARGETS must name exactly one v2 variant})
ALL="CMP-CKSUM-CONTROL-01 CMP-CKSUM-TREATMENT-01 CMP-LAYOUT-CONTROL-02 CMP-LAYOUT-TREATMENT-02 CMP-OCTAL-CONTROL-03 CMP-OCTAL-TREATMENT-03 JKC-SURR-CONTROL-04 JKC-SURR-TREATMENT-04 JKC-OFFSET-CONTROL-05 JKC-OFFSET-TREATMENT-05 CMP-ALIGN-CONTROL-06 CMP-ALIGN-TREATMENT-06"
[ ${#TARGETS[@]} -eq 1 ] || { echo "refusing: one target per launch"; exit 2; }
for V in $TARGETS; do case " $ALL " in *" $V "*) ;; *) echo "refusing: $V is not a v2 target"; exit 2;; esac; done
proj_of() { case $1 in CMP-*) echo Compress;; JKC-*) echo JacksonCore;; esac; }
bugdir_of() { case $1 in CMP-CKSUM-*) echo projects/Compress/bug-01;; CMP-LAYOUT-*) echo projects/Compress/bug-02;; CMP-OCTAL-*) echo projects/Compress/bug-03;; JKC-SURR-*) echo projects/JacksonCore/bug-04;; JKC-OFFSET-*) echo projects/JacksonCore/bug-05;; CMP-ALIGN-*) echo projects/Compress/bug-06;; esac; }
echo "== preflight (non-paid) == server root: $SERVER_ROOT; target: $TARGETS; $(date -u +%FT%TZ)"
curl -sf "$API/api/env" > "$PR/preflight_env_launch.json" || { echo "no server on $PORT"; exit 2; }
$PY - "$PR/preflight_env_launch.json" "$SERVER_ROOT" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); root=sys.argv[2]
assert d.get("repoRoot")==root, f"server on this port is NOT the expected root: {d.get('repoRoot')}"
def find(o):
    if isinstance(o, dict):
        if "credential_configured" in o and "credential_source" in o: yield o
        for v in o.values(): yield from find(v)
    elif isinstance(o, list):
        for v in o: yield from find(v)
pc=next((b for b in find(d) if b.get("provider")=="openai"), None) or {}
ok = pc.get("credential_configured") is True and pc.get("credential_source")=="D4J_OPENAI_API_KEY" and pc.get("model")=="gpt-5.6" and pc.get("provider")=="openai"
print("server repoRoot OK:", d["repoRoot"], "| mini-swe-agent:", (d.get("mini_swe_agent") or {}).get("version"))
print("provider:", pc.get("provider"), "| model:", pc.get("model"), "| credential:", "AVAILABLE (source name: %s)"%pc.get("credential_source") if pc.get("credential_configured") else "UNAVAILABLE")
if not ok: print("refusing: provider/model/credential status does not match the frozen protocol"); sys.exit(3)
PY
RUNS="$SERVER_ROOT/benchmark_runs/$AGENT"
for V in $TARGETS; do
  if [ -e "$RUNS/$V" ]; then NEX=$(ls -d "$RUNS/$V"/run-* 2>/dev/null | wc -l | tr -d ' '); [ $((NEX + REPEATS)) -le ${MP_MAX_RUNS:-5} ] || { echo "refusing: $V already has $NEX runs"; exit 2; }; fi
done; echo "run-directory check passed for: $TARGETS"
for P in Compress JacksonCore; do [ -f "$D/workspaces/defects4j/$P-1/fixed/.defects4j.config" ] || { echo "refusing: harness fixed checkout missing for $P-1"; exit 2; }; done; echo "harness fixed checkouts present (Compress-1, JacksonCore-1)"
for V in $TARGETS; do P=$(proj_of $V); B=$(bugdir_of $V); (cd "$S/$B/packages/$V" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) | diff - <(cd "$SERVER_ROOT/new_bug_variants/$P/bug-1/L20/$V" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) > /dev/null && echo "package byte-identical to the server copy: $V" || { echo "refusing: package/server copy mismatch for $V"; exit 2; }; done
(cd "$S" && shasum -a 256 -c "$PR/package_hashes.txt" --quiet) && echo "all twelve packages unchanged since the manifest was built" || { echo "refusing: a package changed since packaging"; exit 2; }
curl -s "$API/api/variants" | $PY -c "import json,sys;d=json.load(sys.stdin);recs=d if isinstance(d,list) else d.get('variants',d.get('records',[]));ids={r.get('variant_id') or r.get('id') for r in recs};need=set('$TARGETS'.split());assert need<=ids, f'targets not discovered: {need-ids}';print('target discovered:',sorted(need))"
curl -s "$API/api/agents" | $PY -c "import json,sys;d=json.load(sys.stdin);a=d if isinstance(d,list) else d.get('agents',[]);p=[x for x in a if x.get('agent_id')=='$AGENT'];assert p and p[0].get('provider')=='openai' and p[0].get('model')=='gpt-5.6' and p[0].get('status')=='ready', f'agent profile not ready: {p}';print('agent profile ready: $AGENT (openai / gpt-5.6)')"
echo "== protected trees unchanged? =="
ls "$D/new_bug_variants/Lang/bug-1" | diff "$V3/v3_canon_variants_before.txt" - > /dev/null && ls "$D/benchmark_runs/$AGENT" | diff "$V3/v3_canon_runs_before.txt" - > /dev/null && echo "canonical variant and run listings unchanged" || { echo "refusing: canonical listings changed"; exit 2; }
(cd "$RUNS" && shasum -a 256 -c "$PR/run_artifact_hashes_existing.txt" --quiet) && echo "all pre-existing run artifacts unchanged" || { echo "refusing: a pre-existing run artifact changed"; exit 2; }
(cd "$SERVER_ROOT/new_bug_variants" && shasum -a 256 -c "$PR/v3_packages_before.txt" --quiet) && echo "all package copies in the server root unchanged" || { echo "refusing: a package copy in the server root changed"; exit 2; }
[ -f "$PR/run_artifact_hashes_v2.txt" ] && { (cd "$RUNS" && shasum -a 256 -c "$PR/run_artifact_hashes_v2.txt" --quiet) && echo "completed v2 run artifacts unchanged" || { echo "refusing: a completed v2 run artifact changed"; exit 2; }; }
if [ "${PREFLIGHT_ONLY:-0}" = "1" ]; then echo "== PREFLIGHT_ONLY: all non-paid checks passed =="; exit 0; fi
echo "== smoke: using the separately-run bounded provider probe in $PR/preflight_smoke_mp.json =="
[ -n "$(find "$PR/preflight_smoke_mp.json" -mmin -30 2>/dev/null)" ] || { echo "refusing: bounded smoke check missing or older than 30 min"; exit 2; }
$PY -c "import json;d=json.load(open('$PR/preflight_smoke_mp.json'));assert d.get('status')=='passed', 'refusing: bounded smoke check did not pass';print('smoke (pre-launch, bounded):',d.get('status'),'| run_id:',d.get('run_id'))"
echo "== launching $REPEATS run of $TARGETS =="
for V in $TARGETS; do
  echo "-- $V: $(date -u +%FT%TZ) --"
  curl -sf -X POST "$API/api/benchmark-runs" -H 'content-type: application/json' -d "{\"agent_id\":\"$AGENT\",\"task_type\":\"variant\",\"variant_id\":\"$V\",\"repeats\":$REPEATS,\"debug_allow_unreproduced_variant\":true}" > "$PR/launch_$V.json" || echo "request for $V returned an error (see launch_$V.json)"
  echo "-- $V finished: $(date -u +%FT%TZ) --"
done
echo "== per-run results =="; for V in $TARGETS; do for f in "$RUNS"/$V/run-*/evaluation.json; do [ -f "$f" ] || continue; printf '%s ' "${f#$RUNS/}"; $PY -c "import json,sys;e=json.load(open(sys.argv[1]));print('gold_rank',e.get('gold_rank'),'status',e.get('status'))" "$f"; done; done
echo "== launcher finished: $(date -u +%FT%TZ) =="
