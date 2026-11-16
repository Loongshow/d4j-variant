#!/bin/zsh
# Post-run integrity record for the multi-project blocks: v3 root after-inventory vs the pre-install inventory (removed / changed / added), protected trees,
# new-run artifact manifest, credential-pattern scan of the new artifacts (encrypted provider reasoning blobs are known regex false positives).
set -uo pipefail
D=/Users/shawnli/Desktop/Honours/defects4j; RR=$D/supervisor_pipeline_runs; MP=$RR/multi-project-five-hop-v1; V3=$RR/diagnostic-noncanonical-v3; AGENT=mini-swe-agent-openai-gpt-5-6; RUNS=$V3/benchmark_runs/$AGENT; PY=/opt/miniconda3/bin/python; DATA=$MP/analysis/data
TARGETS=(MATH-NORM-CONTROL-01 MATH-NORM-TREATMENT-01)
echo "== after-inventory of the v3 root =="; (cd "$V3" && find . -type f | sort | xargs shasum -a 256) > "$DATA/v3_root_inventory_after_supp.txt"; wc -l "$DATA/v3_root_inventory_before_supp.txt" "$DATA/v3_root_inventory_after_supp.txt"
$PY - "$DATA/v3_root_inventory_before_supp.txt" "$DATA/v3_root_inventory_after_supp.txt" "$DATA/v3_root_inventory_diff_supp.json" <<'PY'
import json,sys,collections,re
old={}; new={}
for line in open(sys.argv[1]): h,p=line.rstrip('\n').split('  ',1); old[p]=h
for line in open(sys.argv[2]): h,p=line.rstrip('\n').split('  ',1); new[p]=h
removed=[p for p in old if p not in new]; changed=[p for p in old if p in new and old[p]!=new[p]]; added=[p for p in new if p not in old]
expected=lambda p: bool(re.search(r"/(MATH-NORM|CHART-AXIS)-(CONTROL|TREATMENT)-01/", p)) or '/_smoke/' in p
out={"pre_existing_files":len(old),"files_after":len(new),"removed":removed,"changed":changed,"added_count":len(added),"added_outside_new_targets_and_smoke":[p for p in added if not expected(p)],"added_by_top_dir":dict(collections.Counter('/'.join(p.split('/')[:5]) for p in added))}
json.dump(out,open(sys.argv[3],'w'),indent=1)
print("pre-existing:",len(old),"| after:",len(new),"| removed:",len(removed),"| changed:",len(changed),"| added:",len(added)); print("added outside the four target families and _smoke:",out["added_outside_new_targets_and_smoke"][:10]); print("changed:",changed[:10]); print("removed:",removed[:10])
PY
echo "== protected trees (same checks as the launcher preflight) =="; cd "$MP/diagnostic" && CRFLB_APPROVED_PAID_RUN=1 PREFLIGHT_ONLY=1 MP_TARGETS="MATH-NORM-CONTROL-01 MATH-NORM-TREATMENT-01" MP_REPEATS=1 MP_ALLOW_EXISTING=1 MP_MAX_RUNS=10 D4J_API_PORT=8792 zsh "$MP/scripts/run_multiproject_attach.sh" 2>&1 | grep -E "unchanged|refusing|packages" || true
echo "== new-run artifact manifest (top-level files of every run of the four targets) =="; (cd "$RUNS" && for V in $TARGETS; do [ -d "$V" ] && find "$V" -mindepth 2 -maxdepth 2 -type f; done | sort | xargs shasum -a 256) > "$DATA/run_artifact_hashes_supp.txt"; wc -l "$DATA/run_artifact_hashes_supp.txt"
echo "== credential-pattern scan of the new artifacts (names/counts only; values never printed) =="
$PY - "$RUNS" <<'PY'
import os,re,sys
root=sys.argv[1]; pat=re.compile(rb"sk-[A-Za-z0-9_-]{16,}"); hits=[]; scanned=0
for V in ("MATH-NORM-CONTROL-01","MATH-NORM-TREATMENT-01","CHART-AXIS-CONTROL-01","CHART-AXIS-TREATMENT-01"):
    for dp,_,fs in os.walk(os.path.join(root,V)):
        if "/workspace/" in dp+"/": continue
        for fn in fs:
            p=os.path.join(dp,fn); scanned+=1
            try: b=open(p,'rb').read()
            except Exception: continue
            for m in pat.finditer(b): hits.append((os.path.relpath(p,root), m.end()-m.start(), b"encrypted_content" in b[max(0,m.start()-5000):m.start()]))
print("files scanned:",scanned,"| pattern hits:",len(hits),"| hits outside encrypted reasoning blobs:",sum(1 for h in hits if not h[2]))
for h in hits: print("  ",h[0],"len",h[1],"encrypted_content context:",h[2])
PY
echo "== integrity record finished: $(date -u +%FT%TZ) =="
