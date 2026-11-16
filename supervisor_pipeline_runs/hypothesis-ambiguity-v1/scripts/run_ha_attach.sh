#!/bin/zsh
# NON-CANONICAL / HYPOTHESIS-AMBIGUITY EXPERIMENT / GPT-5.6 — attach-mode launcher for HA-LOW-01 / HA-HIGH-01 (one run per invocation via launch_ha_run.sh).
# Attaches ONLY to an already-running frozen server that holds the credential in its own environment. Never reads, prints, logs or persists credential values.
# Derived from conversion-branch-dispatch-v1/scripts/run_branch_supplementary_attach.sh: same preflight, protected-tree checks, no in-launcher smoke call. PREFLIGHT_ONLY=1 stops before the smoke assertion.
set -euo pipefail
: "${CRFLB_APPROVED_PAID_RUN:?refusing: export CRFLB_APPROVED_PAID_RUN=1 only for the approved 5+5 HA block}"
D=/Users/shawnli/Desktop/Honours/defects4j; RR=$D/supervisor_pipeline_runs; MP=$RR/hypothesis-ambiguity-v1; PR=$MP/diagnostic; V3=$RR/diagnostic-noncanonical-v3; LC=$RR/locally-coherent-conversion-v1; LCH=$RR/conversion-long-chain-v1; DP=$RR/conversion-dispatch-v1; BR=$RR/conversion-branch-dispatch-v1
SERVER_ROOT=${MP_SERVER_ROOT:-$V3}; AGENT=mini-swe-agent-openai-gpt-5-6; PORT=${D4J_API_PORT:-8792}; REPEATS=${MP_REPEATS:-5}; API="http://127.0.0.1:$PORT"; PY=/opt/miniconda3/bin/python   # MP_REPEATS=1 = canary; MP_ALLOW_EXISTING=1 permits completing a target that already has runs (existing + REPEATS must stay <= 5)
TARGETS=(${=MP_TARGETS:-HA-LOW-01 HA-HIGH-01})   # MP_TARGETS="A B" restricts the launch to a subset (used to run the Chart blocks after the Math blocks were stopped by provider hangs)
proj_of() { case $1 in HA-*) echo Lang;; esac; }
echo "== preflight (non-paid) == server root expected: $SERVER_ROOT; targets: $TARGETS"
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
print("server repoRoot OK:", d["repoRoot"]); print("defects4j:", (d.get("defects4j") or {}).get("available"), "| java:", (d.get("java") or {}).get("available"))
print("provider:", pc.get("provider"), "| model:", pc.get("model"), "| credential:", "AVAILABLE (source name: %s)"%pc.get("credential_source") if pc.get("credential_configured") else "UNAVAILABLE")
if not ok: print("refusing: provider/model/credential status does not match the frozen protocol"); sys.exit(3)
PY
RUNS="$SERVER_ROOT/benchmark_runs/$AGENT"
for V in $TARGETS; do
  if [ -e "$RUNS/$V" ]; then
    if [ "${MP_ALLOW_EXISTING:-0}" = "1" ]; then NEX=$(ls -d "$RUNS/$V"/run-* 2>/dev/null | wc -l | tr -d ' '); [ $((NEX + REPEATS)) -le ${MP_MAX_RUNS:-5} ] || { echo "refusing: $V already has $NEX runs; $NEX + $REPEATS would exceed the planned ${MP_MAX_RUNS:-5} (set MP_MAX_RUNS=10 only for the user-instructed supplementary block run-006..010)"; exit 2; }; echo "$V: $NEX existing runs; this launch adds $REPEATS (slot limit ${MP_MAX_RUNS:-5}; no repetition of existing runs)"
    else echo "refusing: runs already exist for $V under $RUNS"; exit 2; fi
  fi
done; echo "run-directory check passed for: $TARGETS"
for P in Lang; do [ -f "$D/workspaces/defects4j/$P-1/fixed/.defects4j.config" ] || { echo "refusing: harness fixed checkout missing for $P-1"; exit 2; }; done; echo "harness fixed checkout present (Lang-1)"
for V in $TARGETS; do P=$(proj_of $V); (cd "$MP/packages/$V" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) | diff - <(cd "$SERVER_ROOT/new_bug_variants/$P/bug-1/L20/$V" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) > /dev/null || { echo "refusing: server copy of $V differs from the packaged $V"; exit 2; }; done; echo "server copies of the four packages byte-identical to $MP/packages"
(cd "$MP/packages" && shasum -a 256 */variant.patch */test.patch */variant_manifest.json */validation.json */NON_CANONICAL.md) | diff "$MP/analysis/package_hashes.txt" - && echo "packages unchanged since packaging"
curl -s "$API/api/variants" | $PY -c "import json,sys;d=json.load(sys.stdin);recs=d if isinstance(d,list) else d.get('variants',d.get('records',[]));ids={r.get('variant_id') or r.get('variantId') for r in recs};need=set('$TARGETS'.split());assert need<=ids, f'targets not discovered: {need-ids}';print('targets discovered:',sorted(need))"
curl -s "$API/api/agents" | $PY -c "import json,sys;d=json.load(sys.stdin);a=d if isinstance(d,list) else d.get('agents',[]);p=[x for x in a if x.get('agent_id')=='$AGENT'];assert p and p[0].get('provider')=='openai' and p[0].get('model')=='gpt-5.6' and p[0].get('status')=='ready', f'agent profile not ready: {p}';print('agent profile ready:', p[0]['agent_id'], p[0]['model'])"
echo "== protected trees unchanged? =="
ls "$D/new_bug_variants/Lang/bug-1" | diff "$V3/v3_canon_variants_before.txt" - && ls "$D/benchmark_runs/$AGENT" | diff "$V3/v3_canon_runs_before.txt" - && (cd "$RR/diagnostic-noncanonical-v1" && find . -maxdepth 1 -type f | sort | xargs shasum -a 256) | diff "$V3/v3_diag_v1_before.txt" - && (cd "$RR/diagnostic-noncanonical-v2" && find . -maxdepth 1 -type f | sort | xargs shasum -a 256) | diff "$V3/v3_diag_v2_before.txt" - && (cd "$RR/real/out" && find . -type f | sort | xargs shasum -a 256) | diff "$V3/v3_real_before.txt" - && (cd "$LC" && for A in CONVERSION-CONTROL-01 CONVERSION-TREATMENT-01; do for f in variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md; do shasum -a 256 "$A/$f"; done; done) | diff "$V3/v3_lc_packages_before.txt" - && (cd "$V3" && shasum -a 256 diagnostic_v3_results.json treatment_supplementary_results.json benchmark_runs/$AGENT/CONVERSION-CONTROL-01/run-*/evaluation.json benchmark_runs/$AGENT/CONVERSION-TREATMENT-01/run-*/evaluation.json | cut -c1-16,66-) | diff "$LCH/analysis/data/v3_all_runs_eval_hashes.txt" - && (cd "$V3" && shasum -a 256 benchmark_runs/$AGENT/CONVERSION-LONG-*/run-*/evaluation.json | cut -c1-16,66-) | diff "$DP/analysis/data/long_chain_eval_hashes.txt" - && (cd "$LCH" && shasum -a 256 CONVERSION-LONG-*/variant.patch CONVERSION-LONG-*/test.patch CONVERSION-LONG-*/variant_manifest.json CONVERSION-LONG-*/validation.json CONVERSION-LONG-*/NON_CANONICAL.md) | diff "$LCH/analysis/data/package_hashes.txt" - && (cd "$V3" && shasum -a 256 benchmark_runs/$AGENT/CONVERSION-DISPATCH-*/run-*/evaluation.json | cut -c1-16,66-) | diff "$BR/analysis/data/dispatch_eval_hashes.txt" - && (cd "$DP" && shasum -a 256 CONVERSION-DISPATCH-*/variant.patch CONVERSION-DISPATCH-*/test.patch CONVERSION-DISPATCH-*/variant_manifest.json CONVERSION-DISPATCH-*/validation.json CONVERSION-DISPATCH-*/NON_CANONICAL.md) | diff "$DP/analysis/data/package_hashes.txt" - && (cd "$BR" && shasum -a 256 CONVERSION-BRANCH-*/variant.patch CONVERSION-BRANCH-*/test.patch CONVERSION-BRANCH-*/variant_manifest.json CONVERSION-BRANCH-*/validation.json CONVERSION-BRANCH-*/NON_CANONICAL.md) | diff "$BR/analysis/data/package_hashes.txt" - && (cd "$RUNS" && shasum -a 256 -c "$BR/analysis/data/run_artifact_hashes.txt" --quiet) && (cd "$RUNS" && shasum -a 256 -c "$BR/analysis/data/run_artifact_hashes_supplementary.txt" --quiet) && echo "unchanged (canonical trees, v1/v2 roots, real/out, 2-hop packages, 15 v3 run evaluations, long-chain packages + 10 evaluations, dispatch packages + 10 evaluations, branch packages + 400 run artifacts of run-001..015)" || { echo "refusing: a protected tree changed"; exit 2; }
MPROOT=$RR/multi-project-five-hop-v1
(cd "$RUNS" && for V in MATH-NORM-CONTROL-01 MATH-NORM-TREATMENT-01 CHART-AXIS-CONTROL-01 CHART-AXIS-TREATMENT-01; do find "$V" -mindepth 2 -maxdepth 2 -type f; done | sort | xargs shasum -a 256 | sort -k2) | diff "$MP/analysis/data/mp_run_artifact_hashes_reference.txt" - > /dev/null && echo "multi-project run artifacts (Math/Chart, 30 runs) unchanged" || { echo "refusing: multi-project run artifacts changed"; exit 2; }
[ -f "$MP/analysis/data/run_artifact_hashes_ha.txt" ] && { (cd "$RUNS" && shasum -a 256 -c "$MP/analysis/data/run_artifact_hashes_ha.txt" --quiet) && echo "preserved HA attempts (run_artifact_hashes_ha.txt) unchanged" || { echo "refusing: a preserved HA run artifact changed"; exit 2; }; }
if [ "${PREFLIGHT_ONLY:-0}" = "1" ]; then echo "== PREFLIGHT_ONLY: all non-paid checks passed; exiting before the smoke assertion and launch =="; exit 0; fi
echo "== smoke: using the separately-run bounded provider check recorded in $PR/preflight_smoke_mp.json (no second smoke call) =="
[ -n "$(find "$PR/preflight_smoke_mp.json" -mmin -30 2>/dev/null)" ] || { echo "refusing: bounded smoke check missing or older than 30 min"; exit 2; }
$PY -c "import json;d=json.load(open('$PR/preflight_smoke_mp.json'));assert d.get('status')=='passed', 'refusing: bounded smoke check did not pass';print('smoke (pre-launch, bounded):',d.get('status'),'| run_id:',d.get('run_id'))"
echo "== launching $((${#TARGETS[@]} * REPEATS)) runs sequentially over: $TARGETS (harness awaits each run; debug_allow_unreproduced_variant=true recorded as debug_override) =="
for V in $TARGETS; do
  echo "-- $V: $(date) --"
  curl -sf -X POST "$API/api/benchmark-runs" -H 'content-type: application/json' \
    -d "{\"agent_id\":\"$AGENT\",\"task_type\":\"variant\",\"variant_id\":\"$V\",\"repeats\":$REPEATS,\"debug_allow_unreproduced_variant\":true}" \
    > "$PR/launch_$V.json" || echo "request for $V returned an error (see launch_$V.json); continuing with the next target"
  [ -n "${MP_STOP_AFTER_TIMEOUTS:-}" ] && { NT=$(ls "$RUNS"/$V/run-*/run_manifest.json 2>/dev/null | xargs -I{} $PY -c "import json,sys;print(json.load(open(sys.argv[1])).get('status'))" {} | grep -c timeout); [ "$NT" -ge "${MP_STOP_AFTER_TIMEOUTS}" ] && { echo "stopping after $V: $NT timeout runs (provider hangs) reached the MP_STOP_AFTER_TIMEOUTS=$MP_STOP_AFTER_TIMEOUTS threshold; remaining targets NOT launched"; break; }; }
  echo "-- $V finished: $(date) --"
  for i in 001 002 003 004 005; do [ -f "$RUNS/$V/run-$i/evaluation.json" ] && echo "  $V/run-$i: evaluation.json present" || echo "  $V/run-$i: NO evaluation.json (anomaly; not retried)"; done
done
echo "== post-run: information sources per run =="
for V in $TARGETS; do for RD in "$RUNS"/$V/run-*; do [ -d "$RD" ] || continue
  WS=$(ls -d "$RD"/workspace/*/ 2>/dev/null | head -1 || true)
  $PY - "$RD" "${WS:-}" <<'PY'
import json,sys,os,hashlib
R,WS=sys.argv[1],sys.argv[2]
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest() if p and os.path.exists(p) else None
j=lambda *a: os.path.join(WS,*a) if WS else ""
out={"label":"NON-CANONICAL / HYPOTHESIS-AMBIGUITY EXPERIMENT / GPT-5.6","workspace":WS,
     "defects4j.build.properties":{"present":bool(WS) and os.path.exists(j("defects4j.build.properties")),"sha256":sha(j("defects4j.build.properties")),"policy":"preserved per frozen protocol; potential information source"},
     ".defects4j.config":{"present":bool(WS) and os.path.exists(j(".defects4j.config"))},"git_dir_present":bool(WS) and os.path.exists(j(".git")),
     "package_metadata_present":[f for f in ("variant.patch","test.patch","variant_manifest.json","validation.json","NON_CANONICAL.md") if WS and os.path.exists(j(f))]}
json.dump(out,open(os.path.join(R,"pilot_information_sources.json"),"w"),indent=1); print("/".join(R.split("/")[-2:]),"d4j.build.properties:",out["defects4j.build.properties"]["present"],"git:",out["git_dir_present"],"pkg-meta:",out["package_metadata_present"])
PY
done; done
echo "== per-run results =="; for V in $TARGETS; do for f in "$RUNS"/$V/run-*/evaluation.json; do [ -f "$f" ] || continue; printf '%s ' "${f#$RUNS/}"; $PY -c "import json,sys;e=json.load(open(sys.argv[1]));print('gold_rank',e.get('gold_rank'),'hit@5',e.get('hit_at_5'),'hit@10',e.get('hit_at_10'),'status',e.get('status'))" "$f"; done; done
echo "== launcher finished: $(date) =="
