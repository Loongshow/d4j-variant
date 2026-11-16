#!/bin/zsh
# DIAGNOSTIC / NON-CANONICAL / LEAKAGE-EXPOSED — attach-mode launcher.
# The backend server must ALREADY be running from the pilot root, started by the user in their own
# terminal with D4J_OPENAI_API_KEY exported there (the same mechanism as all previous GPT-5.6 runs).
# This script never reads, prints, logs or persists the credential; it only asks the server whether
# a credential is configured. Refuses to run without explicit approval.
set -euo pipefail
: "${CRFLB_APPROVED_PAID_RUN:?refusing: export CRFLB_APPROVED_PAID_RUN=1 only after approving the 10 paid runs}"
PR=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v1
D=/Users/shawnli/Desktop/Honours/defects4j
AGENT=mini-swe-agent-openai-gpt-5-6; PORT=${D4J_API_PORT:-8790}; REPEATS=5; API="http://127.0.0.1:$PORT"
PY=/opt/miniconda3/bin/python

echo "== preflight (non-paid) =="
curl -sf "$API/api/env" > "$PR/preflight_env.json" || { echo "no server on $PORT — start it from $PR/variant-lab in your own terminal first"; exit 2; }
$PY - "$PR/preflight_env.json" "$PR" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); pr=sys.argv[2]
assert d.get("repoRoot")==pr, f"server on this port is NOT the pilot root: {d.get('repoRoot')}"
def find(o):
    if isinstance(o, dict):
        if "credential_configured" in o and "credential_source" in o: yield o
        for v in o.values(): yield from find(v)
    elif isinstance(o, list):
        for v in o: yield from find(v)
blocks=list(find(d)); pc=next((b for b in blocks if b.get("credential_source")=="D4J_OPENAI_API_KEY" and b.get("model")=="gpt-5.6"), blocks[0] if blocks else {})
src=pc.get("credential_source",""); ok=bool(pc.get("credential_configured")) and pc.get("model")=="gpt-5.6"
print("server repoRoot OK:", d["repoRoot"]); print("defects4j:", (d.get("defects4j") or {}).get("available"), "| java:", (d.get("java") or {}).get("available"))
print("provider credential:", "AVAILABLE (source name: %s)"%src if ok else "UNAVAILABLE")
if not ok: sys.exit(3)
PY
for V in NUMBERUTILS-CONTROL-01 NUMBERUTILS-TREATMENT-01; do
  [ -e "$PR/benchmark_runs/$AGENT/$V" ] && { echo "refusing: runs already exist for $V"; exit 2; }
done
curl -s "$API/api/variants" | $PY -c "import json,sys;d=json.load(sys.stdin);recs=d if isinstance(d,list) else d.get('variants',d.get('records',[]));ids={r.get('variant_id') or r.get('variantId') for r in recs};need={'NUMBERUTILS-CONTROL-01','NUMBERUTILS-TREATMENT-01'};assert need<=ids, f'targets not discovered: {need-ids}';print('targets discovered:',sorted(need))"
ls "$D/new_bug_variants/Lang/bug-1" > "$PR/canonical_variants_before.txt"; ls "$D/benchmark_runs/$AGENT" > "$PR/canonical_runs_before.txt"

echo "== adapter smoke test (one tiny paid call; artifacts under pilot benchmark_runs/_smoke) =="
curl -sf -X POST "$API/api/agents/mini-swe-agent/smoke-test" -H 'content-type: application/json' -d "{\"agent_id\":\"$AGENT\"}" > "$PR/preflight_smoke.json"
$PY -c "import json;d=json.load(open('$PR/preflight_smoke.json'));print('smoke ok:',d.get('ok', d.get('status')), '| keys:', list(d)[:8])"

echo "== launching 5 + 5 runs sequentially (the harness awaits each run before the next) =="
for V in NUMBERUTILS-CONTROL-01 NUMBERUTILS-TREATMENT-01; do
  echo "-- $V: $(date) --"
  curl -sf -X POST "$API/api/benchmark-runs" -H 'content-type: application/json' \
    -d "{\"agent_id\":\"$AGENT\",\"task_type\":\"variant\",\"variant_id\":\"$V\",\"repeats\":$REPEATS,\"debug_allow_unreproduced_variant\":true}" \
    > "$PR/launch_$V.json" || echo "request for $V returned an error (see launch_$V.json); continuing with the other arm"
  echo "-- $V finished: $(date) --"
done

echo "== post-run: record information sources per run (protocol-preserved defects4j.build.properties) =="
for R in "$PR"/benchmark_runs/$AGENT/NUMBERUTILS-*/run-*; do
  WS=$(ls -d "$R"/workspace/*/ 2>/dev/null | head -1 || true)
  $PY - "$R" "${WS:-}" <<'PY'
import json,sys,os,hashlib
R,WS=sys.argv[1],sys.argv[2]
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest() if p and os.path.exists(p) else None
j=lambda *a: os.path.join(WS,*a) if WS else ""
out={"label":"DIAGNOSTIC / NON-CANONICAL / LEAKAGE-EXPOSED","workspace":WS,
     "defects4j.build.properties":{"present":bool(WS) and os.path.exists(j("defects4j.build.properties")),"sha256":sha(j("defects4j.build.properties")),
        "policy":"preserved per frozen protocol; potential information source (names the original Lang-1 fix class)"},
     ".defects4j.config":{"present":bool(WS) and os.path.exists(j(".defects4j.config"))},
     "git_dir_present":bool(WS) and os.path.exists(j(".git")),
     "package_metadata_present":[f for f in ("variant.patch","test.patch","variant_manifest.json","validation.json") if WS and os.path.exists(j(f))]}
json.dump(out,open(os.path.join(R,"pilot_information_sources.json"),"w"),indent=1); print("/".join(R.split("/")[-2:]), "d4j.build.properties:",out["defects4j.build.properties"]["present"],"git:",out["git_dir_present"],"pkg-meta:",out["package_metadata_present"])
PY
done
echo "== canonical trees untouched? =="; ls "$D/new_bug_variants/Lang/bug-1" | diff "$PR/canonical_variants_before.txt" - && ls "$D/benchmark_runs/$AGENT" | diff "$PR/canonical_runs_before.txt" - && echo "unchanged"
echo "== per-run results =="; for f in "$PR"/benchmark_runs/$AGENT/NUMBERUTILS-*/run-*/evaluation.json; do printf '%s ' "${f#$PR/benchmark_runs/$AGENT/}"; $PY -c "import json,sys;e=json.load(open(sys.argv[1]));print('gold_rank',e.get('gold_rank'),'hit@5',e.get('hit_at_5'),'hit@10',e.get('hit_at_10'),'status',e.get('status'))" "$f"; done
