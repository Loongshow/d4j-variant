#!/bin/zsh
# DIAGNOSTIC / NON-CANONICAL / LOCALLY-COHERENT-CONVERSION-V1 — attach-mode launcher (v3).
# Attaches ONLY to the frozen server copy on port 8792 that the user started from the v3 root with the credential exported
# in their own terminal. Never reads, prints, logs, persists or copies credential values; asks the server only for safe status.
set -euo pipefail
: "${CRFLB_APPROVED_PAID_RUN:?refusing: export CRFLB_APPROVED_PAID_RUN=1 only after approving the 10 paid runs}"
D=/Users/shawnli/Desktop/Honours/defects4j; RR=$D/supervisor_pipeline_runs; PR=$RR/diagnostic-noncanonical-v3; LC=$RR/locally-coherent-conversion-v1
AGENT=mini-swe-agent-openai-gpt-5-6; PORT=${D4J_API_PORT:-8792}; REPEATS=5; API="http://127.0.0.1:$PORT"; PY=/opt/miniconda3/bin/python
echo "== preflight (non-paid) =="
curl -sf "$API/api/env" > "$PR/preflight_env.json" || { echo "no server on $PORT — start the frozen copy from $PR/variant-lab in your own terminal first"; exit 2; }
$PY - "$PR/preflight_env.json" "$PR" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); pr=sys.argv[2]
assert d.get("repoRoot")==pr, f"server on this port is NOT the v3 root: {d.get('repoRoot')}"
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
for V in CONVERSION-CONTROL-01 CONVERSION-TREATMENT-01; do [ -e "$PR/benchmark_runs/$AGENT/$V" ] && { echo "refusing: runs already exist for $V"; exit 2; }; done
curl -s "$API/api/variants" | $PY -c "import json,sys;d=json.load(sys.stdin);recs=d if isinstance(d,list) else d.get('variants',d.get('records',[]));ids={r.get('variant_id') or r.get('variantId') for r in recs};need={'CONVERSION-CONTROL-01','CONVERSION-TREATMENT-01'};assert need<=ids, f'targets not discovered: {need-ids}';print('targets discovered:',sorted(need))"
curl -s "$API/api/agents" | $PY -c "import json,sys;d=json.load(sys.stdin);a=d if isinstance(d,list) else d.get('agents',[]);p=[x for x in a if x.get('agent_id')=='$AGENT'];assert p and p[0].get('provider')=='openai' and p[0].get('model')=='gpt-5.6' and p[0].get('status')=='ready', f'agent profile not ready: {p}';print('agent profile ready:', p[0]['agent_id'], p[0]['model'])"
echo "== protected trees unchanged since root build? =="
ls "$D/new_bug_variants/Lang/bug-1" | diff "$PR/v3_canon_variants_before.txt" - && ls "$D/benchmark_runs/$AGENT" | diff "$PR/v3_canon_runs_before.txt" - && (cd "$RR/diagnostic-noncanonical-v1" && find . -maxdepth 1 -type f | sort | xargs shasum -a 256) | diff "$PR/v3_diag_v1_before.txt" - && (cd "$RR/diagnostic-noncanonical-v2" && find . -maxdepth 1 -type f | sort | xargs shasum -a 256) | diff "$PR/v3_diag_v2_before.txt" - && (cd "$RR/real/out" && find . -type f | sort | xargs shasum -a 256) | diff "$PR/v3_real_before.txt" - && (cd "$LC" && for V in CONVERSION-CONTROL-01 CONVERSION-TREATMENT-01; do for f in variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md; do shasum -a 256 "$V/$f"; done; done) | diff "$PR/v3_lc_packages_before.txt" - && echo "unchanged" || { echo "refusing: a protected tree changed"; exit 2; }
echo "== adapter smoke test (one tiny paid call; artifacts under $PR/benchmark_runs/_smoke) =="
curl -sf -X POST "$API/api/agents/mini-swe-agent/smoke-test" -H 'content-type: application/json' -d "{\"agent_id\":\"$AGENT\"}" > "$PR/preflight_smoke.json"
$PY -c "import json;d=json.load(open('$PR/preflight_smoke.json'));print('smoke:',d.get('status'))"
echo "== launching 5 + 5 runs sequentially (the harness awaits each run before creating the next; debug_allow_unreproduced_variant=true recorded as debug_override) =="
for V in CONVERSION-CONTROL-01 CONVERSION-TREATMENT-01; do
  echo "-- $V: $(date) --"
  curl -sf -X POST "$API/api/benchmark-runs" -H 'content-type: application/json' \
    -d "{\"agent_id\":\"$AGENT\",\"task_type\":\"variant\",\"variant_id\":\"$V\",\"repeats\":$REPEATS,\"debug_allow_unreproduced_variant\":true}" \
    > "$PR/launch_$V.json" || echo "request for $V returned an error (see launch_$V.json); continuing with the other arm"
  echo "-- $V finished: $(date) --"
done
echo "== post-run: information sources per run (defects4j.build.properties preserved per protocol) =="
for R in "$PR"/benchmark_runs/$AGENT/CONVERSION-*/run-*; do
  WS=$(ls -d "$R"/workspace/*/ 2>/dev/null | head -1 || true)
  $PY - "$R" "${WS:-}" <<'PY'
import json,sys,os,hashlib
R,WS=sys.argv[1],sys.argv[2]
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest() if p and os.path.exists(p) else None
j=lambda *a: os.path.join(WS,*a) if WS else ""
out={"label":"DIAGNOSTIC / NON-CANONICAL / LOCALLY-COHERENT-CONVERSION-V1","workspace":WS,
     "defects4j.build.properties":{"present":bool(WS) and os.path.exists(j("defects4j.build.properties")),"sha256":sha(j("defects4j.build.properties")),"policy":"preserved per frozen protocol; potential information source"},
     ".defects4j.config":{"present":bool(WS) and os.path.exists(j(".defects4j.config"))},"git_dir_present":bool(WS) and os.path.exists(j(".git")),
     "package_metadata_present":[f for f in ("variant.patch","test.patch","variant_manifest.json","validation.json","NON_CANONICAL.md") if WS and os.path.exists(j(f))]}
json.dump(out,open(os.path.join(R,"pilot_information_sources.json"),"w"),indent=1); print("/".join(R.split("/")[-2:]),"d4j.build.properties:",out["defects4j.build.properties"]["present"],"git:",out["git_dir_present"],"pkg-meta:",out["package_metadata_present"])
PY
done
echo "== per-run results =="; for f in "$PR"/benchmark_runs/$AGENT/CONVERSION-*/run-*/evaluation.json; do printf '%s ' "${f#$PR/benchmark_runs/$AGENT/}"; $PY -c "import json,sys;e=json.load(open(sys.argv[1]));print('gold_rank',e.get('gold_rank'),'hit@5',e.get('hit_at_5'),'hit@10',e.get('hit_at_10'),'status',e.get('status'))" "$f"; done
