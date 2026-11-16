#!/bin/zsh
# DIAGNOSTIC / NON-CANONICAL / LEAKAGE-EXPOSED — 10-run GPT-5.6 ceiling check on the supervisor pilot pair.
# PREPARED, NOT EXECUTED. Refuses to run without explicit approval. Spends OpenAI credits (~$2, worst case ~$9).
set -euo pipefail
: "${CRFLB_APPROVED_PAID_RUN:?refusing: export CRFLB_APPROVED_PAID_RUN=1 only after approving the 10 paid runs}"
: "${OPENAI_API_KEY:?OPENAI_API_KEY must be exported in this shell (never stored in the repo)}"
export D4J_OPENAI_MODEL="${D4J_OPENAI_MODEL:-gpt-5.6}"
export PERL5LIB="$HOME/perl5/lib/perl5"
PR=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v1
AGENT=mini-swe-agent-openai-gpt-5-6; PORT=${D4J_API_PORT:-8790}; REPEATS=5
[ -d "$PR/variant-lab/server" ] || { echo "pilot root missing"; exit 2; }
for V in NUMBERUTILS-CONTROL-01 NUMBERUTILS-TREATMENT-01; do
  [ -e "$PR/benchmark_runs/$AGENT/$V" ] && { echo "refusing: runs already exist for $V"; exit 2; }
done
# frozen server COPY inside the pilot root -> repoRoot = pilot root; canonical trees are never touched
if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then echo "refusing: port $PORT already in use (stale server?)"; exit 2; fi
(cd "$PR/variant-lab" && exec env D4J_API_PORT=$PORT node server/index.mjs >> "$PR/server.log" 2>&1) & SERVER_PID=$!   # exec: PID is node itself
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
for i in $(seq 1 40); do curl -sf "http://127.0.0.1:$PORT/api/env" >/dev/null 2>&1 && break; sleep 1; done
echo "server up on $PORT; variants visible:"; curl -s "http://127.0.0.1:$PORT/api/variants" | head -c 300; echo
for V in NUMBERUTILS-CONTROL-01 NUMBERUTILS-TREATMENT-01; do
  echo "== launching $REPEATS runs for $V =="
  curl -sf -X POST "http://127.0.0.1:$PORT/api/benchmark-runs" -H 'content-type: application/json' \
    -d "{\"agent_id\":\"$AGENT\",\"task_type\":\"variant\",\"variant_id\":\"$V\",\"repeats\":$REPEATS,\"debug_allow_unreproduced_variant\":true}" \
    > "$PR/launch_$V.json"; head -c 300 "$PR/launch_$V.json"; echo
done
# post-run: record the defects4j.build.properties information source per run (protocol-preserved, not removed)
for R in "$PR"/benchmark_runs/$AGENT/NUMBERUTILS-*/run-*; do
  WS=$(ls -d "$R"/workspace/*/ 2>/dev/null | head -1)
  /opt/miniconda3/bin/python - "$R" "$WS" <<'PY'
import json,sys,os,hashlib
R,WS=sys.argv[1],sys.argv[2]
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest() if os.path.exists(p) else None
out={"label":"DIAGNOSTIC / NON-CANONICAL / LEAKAGE-EXPOSED","workspace":WS,
     "defects4j.build.properties":{"present":os.path.exists(os.path.join(WS,"defects4j.build.properties")),"sha256":sha(os.path.join(WS,"defects4j.build.properties")),"policy":"preserved per frozen protocol; potential information source (names the original Lang-1 fix class)"},
     ".defects4j.config":{"present":os.path.exists(os.path.join(WS,".defects4j.config"))},
     "git_dir_present":os.path.exists(os.path.join(WS,".git")),
     "package_metadata_present":[f for f in ("variant.patch","test.patch","variant_manifest.json","validation.json") if os.path.exists(os.path.join(WS,f))]}
json.dump(out,open(os.path.join(R,"pilot_information_sources.json"),"w"),indent=1); print(R.split('/')[-2:], out["defects4j.build.properties"]["present"], "git:",out["git_dir_present"], "pkg-meta:",out["package_metadata_present"])
PY
done
echo "== per-run results =="; for f in "$PR"/benchmark_runs/$AGENT/NUMBERUTILS-*/run-*/evaluation.json; do printf '%s ' "${f#$PR/benchmark_runs/$AGENT/}"; /opt/miniconda3/bin/python -c "import json,sys;e=json.load(open(sys.argv[1]));print('gold_rank',e.get('gold_rank'),'hit@5',e.get('hit_at_5'),'hit@10',e.get('hit_at_10'),'status',e.get('status'))" "$f"; done
