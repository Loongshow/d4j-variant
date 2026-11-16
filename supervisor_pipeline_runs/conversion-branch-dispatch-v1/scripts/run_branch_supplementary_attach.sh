#!/bin/zsh
# NON-CANONICAL / BRANCH-DISPATCH DIAGNOSTIC / GPT-5.6 — SUPPLEMENTARY TREATMENT-ONLY block launcher (run-006..015, 10 runs).
# Derived from run_branch_attach.sh (same preflight and protected-tree checks) and run_treatment_supplementary_v3_attach.sh
# (TREATMENT only, first-block integrity gate, no in-launcher smoke call). Same variant, package, prompt, model, agent profile,
# budget, protocol and server as run-001..005. Runs are requested as two sequential batches of 5 (repeats=5 each; the harness
# executes the repeats of a batch sequentially and `nextRunId` allocates the first free run-NNN, so batch 1 = run-006..010 and
# batch 2 = run-011..015); batch 2 is refused if batch 1 did not produce exactly run-006..010. Nothing is retried or replaced.
# Attaches ONLY to an already-running frozen server that holds the credential in its own environment. Never reads, prints,
# logs or persists credential values. PREFLIGHT_ONLY=1 runs the non-paid checks and exits before the smoke assertion/launch.
set -euo pipefail
: "${CRFLB_APPROVED_PAID_RUN:?refusing: export CRFLB_APPROVED_PAID_RUN=1 only after approving the 10 supplementary paid TREATMENT runs}"
D=/Users/shawnli/Desktop/Honours/defects4j; RR=$D/supervisor_pipeline_runs; R=$RR/conversion-branch-dispatch-v1; DP=$RR/conversion-dispatch-v1; LCH=$RR/conversion-long-chain-v1; PR=$R/diagnostic; V3=$RR/diagnostic-noncanonical-v3; LC=$RR/locally-coherent-conversion-v1
SERVER_ROOT=${BRANCH_SERVER_ROOT:-$V3}; AGENT=mini-swe-agent-openai-gpt-5-6; PORT=${D4J_API_PORT:-8792}; API="http://127.0.0.1:$PORT"; PY=/opt/miniconda3/bin/python
V=CONVERSION-BRANCH-TREATMENT-01; BATCH=5; NEW_IDS=(006 007 008 009 010 011 012 013 014 015); B1=(006 007 008 009 010); B2=(011 012 013 014 015)
echo "== preflight (non-paid) == server root expected: $SERVER_ROOT; target: $V run-006..015 (TREATMENT only; no CONTROL runs)"
curl -sf "$API/api/env" > "$PR/preflight_env_supp_launch.json" || { echo "no server on $PORT"; exit 2; }
$PY - "$PR/preflight_env_supp_launch.json" "$SERVER_ROOT" <<'PY'
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
print("server repoRoot OK:", d["repoRoot"]); print("defects4j:", (d.get("defects4j") or {}).get("available"), "| java:", (d.get("java") or {}).get("available"))
print("provider:", pc.get("provider"), "| model:", pc.get("model"), "| credential:", "AVAILABLE (source name: %s)"%pc.get("credential_source") if pc.get("credential_configured") else "UNAVAILABLE")
if not ok: print("refusing: provider/model/credential status does not match the frozen protocol"); sys.exit(3)
PY
RUNS="$SERVER_ROOT/benchmark_runs/$AGENT"
echo "== first block (run-001..005, both arms) intact? =="
for A in CONVERSION-BRANCH-CONTROL-01 $V; do for i in 001 002 003 004 005; do [ -f "$RUNS/$A/run-$i/evaluation.json" ] || { echo "refusing: first-block $A/run-$i missing"; exit 2; }; done; done
(cd "$SERVER_ROOT" && shasum -a 256 benchmark_runs/$AGENT/CONVERSION-BRANCH-*/run-00[1-5]/evaluation.json | cut -c1-16,66-) | diff "$R/analysis/data/branch_first_block_eval_hashes.txt" - > /dev/null || { echo "refusing: first-block evaluation.json hashes changed"; exit 2; }
(cd "$RUNS" && shasum -a 256 -c "$R/analysis/data/run_artifact_hashes.txt" --quiet) || { echo "refusing: a first-block run artifact changed (200-file manifest)"; exit 2; }
(cd "$R" && shasum -a 256 branch_dispatch_results.json | cut -c1-16,66-) | diff "$R/analysis/data/branch_first_block_results_hash.txt" - > /dev/null || { echo "refusing: branch_dispatch_results.json changed"; exit 2; }
echo "first block intact (10 evaluation.json + 200 run artifacts + branch_dispatch_results.json)"
for i in $NEW_IDS; do [ -e "$RUNS/$V/run-$i" ] && { echo "refusing: $RUNS/$V/run-$i already exists"; exit 2; }; done
[ -e "$RUNS/$V/run-005" ] || { echo "refusing: run-005 missing, ids would not append"; exit 2; }; echo "supplementary slots run-006..015 free; next free id will be run-006"
(cd "$R/$V" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) | diff - <(cd "$SERVER_ROOT/new_bug_variants/Lang/bug-1/L20/$V" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) > /dev/null || { echo "refusing: server copy of $V differs from the packaged $V"; exit 2; }; echo "server copy of $V byte-identical to the packaged $V"
(cd "$R" && shasum -a 256 CONVERSION-BRANCH-*/variant.patch CONVERSION-BRANCH-*/test.patch CONVERSION-BRANCH-*/variant_manifest.json CONVERSION-BRANCH-*/validation.json CONVERSION-BRANCH-*/NON_CANONICAL.md) | diff "$R/analysis/data/package_hashes.txt" - && echo "branch packages unchanged since packaging"
curl -s "$API/api/variants" | $PY -c "import json,sys;d=json.load(sys.stdin);recs=d if isinstance(d,list) else d.get('variants',d.get('records',[]));ids={r.get('variant_id') or r.get('variantId') for r in recs};need={'$V'};assert need<=ids, f'target not discovered: {need-ids}';print('target discovered:',sorted(need))"
curl -s "$API/api/agents" | $PY -c "import json,sys;d=json.load(sys.stdin);a=d if isinstance(d,list) else d.get('agents',[]);p=[x for x in a if x.get('agent_id')=='$AGENT'];assert p and p[0].get('provider')=='openai' and p[0].get('model')=='gpt-5.6' and p[0].get('status')=='ready', f'agent profile not ready: {p}';print('agent profile ready:', p[0]['agent_id'], p[0]['model'])"
echo "== protected trees unchanged? =="
ls "$D/new_bug_variants/Lang/bug-1" | diff "$V3/v3_canon_variants_before.txt" - && ls "$D/benchmark_runs/$AGENT" | diff "$V3/v3_canon_runs_before.txt" - && (cd "$RR/diagnostic-noncanonical-v1" && find . -maxdepth 1 -type f | sort | xargs shasum -a 256) | diff "$V3/v3_diag_v1_before.txt" - && (cd "$RR/diagnostic-noncanonical-v2" && find . -maxdepth 1 -type f | sort | xargs shasum -a 256) | diff "$V3/v3_diag_v2_before.txt" - && (cd "$RR/real/out" && find . -type f | sort | xargs shasum -a 256) | diff "$V3/v3_real_before.txt" - && (cd "$LC" && for A in CONVERSION-CONTROL-01 CONVERSION-TREATMENT-01; do for f in variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md; do shasum -a 256 "$A/$f"; done; done) | diff "$V3/v3_lc_packages_before.txt" - && (cd "$V3" && shasum -a 256 diagnostic_v3_results.json treatment_supplementary_results.json benchmark_runs/$AGENT/CONVERSION-CONTROL-01/run-*/evaluation.json benchmark_runs/$AGENT/CONVERSION-TREATMENT-01/run-*/evaluation.json | cut -c1-16,66-) | diff "$LCH/analysis/data/v3_all_runs_eval_hashes.txt" - && (cd "$V3" && shasum -a 256 benchmark_runs/$AGENT/CONVERSION-LONG-*/run-*/evaluation.json | cut -c1-16,66-) | diff "$DP/analysis/data/long_chain_eval_hashes.txt" - && (cd "$LCH" && shasum -a 256 CONVERSION-LONG-*/variant.patch CONVERSION-LONG-*/test.patch CONVERSION-LONG-*/variant_manifest.json CONVERSION-LONG-*/validation.json CONVERSION-LONG-*/NON_CANONICAL.md) | diff "$LCH/analysis/data/package_hashes.txt" - && (cd "$V3" && shasum -a 256 benchmark_runs/$AGENT/CONVERSION-DISPATCH-*/run-*/evaluation.json | cut -c1-16,66-) | diff "$R/analysis/data/dispatch_eval_hashes.txt" - && (cd "$DP" && shasum -a 256 CONVERSION-DISPATCH-*/variant.patch CONVERSION-DISPATCH-*/test.patch CONVERSION-DISPATCH-*/variant_manifest.json CONVERSION-DISPATCH-*/validation.json CONVERSION-DISPATCH-*/NON_CANONICAL.md) | diff "$DP/analysis/data/package_hashes.txt" - && echo "unchanged (canonical trees, v1/v2 roots, real/out, 2-hop packages, 15 v3 run evaluations, long-chain packages + 10 evaluations, dispatch packages + 10 evaluations)" || { echo "refusing: a protected tree changed"; exit 2; }
if [ "${PREFLIGHT_ONLY:-0}" = "1" ]; then echo "== PREFLIGHT_ONLY: all non-paid checks passed; exiting before the smoke assertion and launch =="; exit 0; fi
echo "== smoke: using the separately-run bounded provider check recorded in $PR/preflight_smoke_supp.json (no second smoke call) =="
[ -n "$(find "$PR/preflight_smoke_supp.json" -mmin -30 2>/dev/null)" ] || { echo "refusing: bounded smoke check missing or older than 30 min"; exit 2; }
$PY -c "import json;d=json.load(open('$PR/preflight_smoke_supp.json'));assert d.get('status')=='passed', 'refusing: bounded smoke check did not pass';print('smoke (pre-launch, bounded):',d.get('status'),'| run_id:',d.get('run_id'))"
echo "== launching 10 supplementary TREATMENT-only runs as two sequential batches of $BATCH (the harness awaits each run; debug_allow_unreproduced_variant=true recorded as debug_override) =="
launch_batch() { local n=$1; echo "-- $V batch $n: $(date) --"
  curl -sf -X POST "$API/api/benchmark-runs" -H 'content-type: application/json' \
    -d "{\"agent_id\":\"$AGENT\",\"task_type\":\"variant\",\"variant_id\":\"$V\",\"repeats\":$BATCH,\"debug_allow_unreproduced_variant\":true}" \
    > "$PR/launch_${V}_supplementary_batch$n.json" || echo "request for batch $n returned an error (see launch_${V}_supplementary_batch$n.json)"
  echo "-- $V batch $n finished: $(date) --"; }
launch_batch 1
for i in $B1; do [ -f "$RUNS/$V/run-$i/evaluation.json" ] && echo "run-$i: evaluation.json present" || echo "run-$i: NO evaluation.json (anomaly; not retried)"; done
if [ -e "$RUNS/$V/run-010" ] && [ ! -e "$RUNS/$V/run-011" ]; then launch_batch 2; else echo "refusing batch 2: batch 1 did not end at run-010 with run-011 free (ids would not be run-011..015); stopping here, nothing retried"; fi
for i in $B2; do [ -f "$RUNS/$V/run-$i/evaluation.json" ] && echo "run-$i: evaluation.json present" || echo "run-$i: NO evaluation.json (anomaly; not retried)"; done
echo "== post-run: information sources per NEW run only (run-006..015) =="
for i in $NEW_IDS; do RD="$RUNS/$V/run-$i"; [ -d "$RD" ] || continue
  WS=$(ls -d "$RD"/workspace/*/ 2>/dev/null | head -1 || true)
  $PY - "$RD" "${WS:-}" <<'PY'
import json,sys,os,hashlib
R,WS=sys.argv[1],sys.argv[2]
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest() if p and os.path.exists(p) else None
j=lambda *a: os.path.join(WS,*a) if WS else ""
out={"label":"NON-CANONICAL / BRANCH-DISPATCH DIAGNOSTIC / GPT-5.6 / SUPPLEMENTARY BLOCK run-006..015","workspace":WS,
     "defects4j.build.properties":{"present":bool(WS) and os.path.exists(j("defects4j.build.properties")),"sha256":sha(j("defects4j.build.properties")),"policy":"preserved per frozen protocol; potential information source"},
     ".defects4j.config":{"present":bool(WS) and os.path.exists(j(".defects4j.config"))},"git_dir_present":bool(WS) and os.path.exists(j(".git")),
     "package_metadata_present":[f for f in ("variant.patch","test.patch","variant_manifest.json","validation.json","NON_CANONICAL.md") if WS and os.path.exists(j(f))]}
json.dump(out,open(os.path.join(R,"pilot_information_sources.json"),"w"),indent=1); print("/".join(R.split("/")[-2:]),"d4j.build.properties:",out["defects4j.build.properties"]["present"],"git:",out["git_dir_present"],"pkg-meta:",out["package_metadata_present"])
PY
done
echo "== per-run results (new runs) =="; for i in $NEW_IDS; do f="$RUNS/$V/run-$i/evaluation.json"; [ -f "$f" ] || { echo "run-$i: no evaluation.json"; continue; }; printf '%s ' "run-$i"; $PY -c "import json,sys;e=json.load(open(sys.argv[1]));print('gold_rank',e.get('gold_rank'),'hit@5',e.get('hit_at_5'),'hit@10',e.get('hit_at_10'),'status',e.get('status'))" "$f"; done
echo "== launcher finished: $(date) =="
