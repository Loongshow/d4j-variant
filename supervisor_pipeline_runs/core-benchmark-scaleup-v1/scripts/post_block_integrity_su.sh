#!/bin/zsh
# Post-block integrity record for the scale-up block: v3 root after-inventory vs the before-block inventory (removed / changed / added; added must lie under the
# ten new variants' run dirs or _smoke), protected trees (launcher PREFLIGHT_ONLY), run-artifact hash manifest of all scale-up runs, credential-pattern scan of the
# new artifacts (names/counts only; encrypted provider reasoning blobs are known regex false positives). Writes diagnostic-gpt56/post_block_integrity_su.log.
set -uo pipefail
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1; SU=$S/diagnostic-gpt56; V3=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3; AGENT=mini-swe-agent-openai-gpt-5-6; RUNS=$V3/benchmark_runs/$AGENT; PY=/opt/miniconda3/bin/python
TARGETS=(CHART-POLAR-CONTROL-02 CHART-POLAR-TREATMENT-02 CHART-PIE-CONTROL-03 CHART-PIE-TREATMENT-03 MATH-BICUBIC-CONTROL-02 MATH-BICUBIC-TREATMENT-02 MATH-HARMONIC-CONTROL-03 MATH-HARMONIC-TREATMENT-03 LANG-FOLD-CONTROL-02 LANG-FOLD-TREATMENT-02)
{ echo "== post-block integrity record: $(date -u +%FT%TZ) =="
  echo "== after-inventory of the v3 root =="; (cd "$V3" && find . -type f | sort | xargs shasum -a 256) > "$SU/v3_root_inventory_after_su.txt"; wc -l "$SU/v3_root_inventory_before_su.txt" "$SU/v3_root_inventory_after_su.txt"
  $PY - "$SU/v3_root_inventory_before_su.txt" "$SU/v3_root_inventory_after_su.txt" "$SU/v3_root_inventory_diff_su.json" <<'PY'
import json,sys,collections,re
old={}; new={}
for line in open(sys.argv[1]): h,p=line.rstrip('\n').split('  ',1); old[p]=h
for line in open(sys.argv[2]): h,p=line.rstrip('\n').split('  ',1); new[p]=h
removed=[p for p in old if p not in new]; changed=[p for p in old if p in new and old[p]!=new[p]]; added=[p for p in new if p not in old]
expected=lambda p: bool(re.search(r"/(CHART-POLAR|CHART-PIE|MATH-BICUBIC|MATH-HARMONIC|LANG-FOLD)-(CONTROL|TREATMENT)-0[23]/", p)) or '/_smoke/' in p
out={"pre_existing_files":len(old),"files_after":len(new),"removed":removed,"changed":changed,"added_count":len(added),"added_outside_new_targets_and_smoke":[p for p in added if not expected(p)],"added_by_top_dir":dict(collections.Counter('/'.join(p.split('/')[:5]) for p in added))}
json.dump(out,open(sys.argv[3],'w'),indent=1)
print("pre-existing:",len(old),"| after:",len(new),"| removed:",len(removed),"| changed:",len(changed),"| added:",len(added)); print("added outside the ten new variants and _smoke:",out["added_outside_new_targets_and_smoke"][:10]); print("changed:",changed[:10]); print("removed:",removed[:10])
PY
  echo "== protected trees (launcher preflight, non-paid; MP_MAX_RUNS raised to 6 for the check only, no launch) =="; (cd "$S" && CRFLB_APPROVED_PAID_RUN=1 PREFLIGHT_ONLY=1 MP_TARGETS="LANG-FOLD-TREATMENT-02" MP_REPEATS=1 MP_ALLOW_EXISTING=1 MP_MAX_RUNS=6 D4J_API_PORT=8792 zsh scripts/run_su_attach.sh 2>&1 | grep -E "unchanged|refusing|PREFLIGHT_ONLY|discovered")
  echo "== run-artifact manifest (top-level files of every scale-up run) =="; (cd "$RUNS" && for V in $TARGETS; do [ -d "$V" ] && find "$V" -mindepth 2 -maxdepth 2 -type f; done | sort | xargs shasum -a 256) > "$SU/run_artifact_hashes_su_final.txt"; wc -l "$SU/run_artifact_hashes_su_final.txt"; echo "run dirs per variant: $(cd $RUNS && for V in $TARGETS; do printf '%s=%s ' $V $(ls -d $V/run-* 2>/dev/null | wc -l | tr -d ' '); done)"
  echo "== credential-pattern scan of the new artifacts (names/counts only; values never printed) =="
  $PY - "$RUNS" "${TARGETS[@]}" <<'PY'
import os,re,sys
root=sys.argv[1]; pat=re.compile(rb"sk-[A-Za-z0-9_-]{16,}"); hits=[]; scanned=0
for V in sys.argv[2:]:
    for dp,_,fs in os.walk(os.path.join(root,V)):
        if "/workspace/" in dp+"/": continue
        for fn in fs:
            p=os.path.join(dp,fn); scanned+=1
            try: b=open(p,'rb').read()
            except Exception: continue
            for m in pat.finditer(b): hits.append((os.path.relpath(p,root), m.end()-m.start(), b"encrypted_content" in b[max(0,m.start()-5000):m.start()]))
print("files scanned:",scanned,"| pattern hits:",len(hits),"| hits outside encrypted reasoning blobs:",sum(1 for h in hits if not h[2]))
for h in hits[:20]: print("  ",h[0],"len",h[1],"encrypted_content context:",h[2])
PY
  echo "== integrity record finished: $(date -u +%FT%TZ) =="; } 2>&1 | tee "$SU/post_block_integrity_su.log" | grep -E "pre-existing|added outside|changed:|removed:|unchanged|refusing|PREFLIGHT|run dirs|files scanned|finished" | cut -c1-200
