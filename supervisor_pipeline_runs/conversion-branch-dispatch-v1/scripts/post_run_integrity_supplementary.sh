#!/bin/zsh
# Post-run integrity record for the supplementary block (run-006..015): after-inventory of the v3 root, path-keyed comparison with the
# pre-launch inventory (removed / changed / added), first-block manifest re-check, protected-tree re-check, new-run artifact manifest,
# and a credential-pattern scan of the new artifacts (encrypted provider reasoning blobs are known regex false positives; reported separately).
set -uo pipefail
D=/Users/shawnli/Desktop/Honours/defects4j; RR=$D/supervisor_pipeline_runs; R=$RR/conversion-branch-dispatch-v1; DP=$RR/conversion-dispatch-v1; LCH=$RR/conversion-long-chain-v1; V3=$RR/diagnostic-noncanonical-v3; LC=$RR/locally-coherent-conversion-v1
AGENT=mini-swe-agent-openai-gpt-5-6; V=CONVERSION-BRANCH-TREATMENT-01; RUNS=$V3/benchmark_runs/$AGENT; PY=/opt/miniconda3/bin/python; DATA=$R/analysis/data
echo "== after-inventory of the v3 root =="; (cd "$V3" && find . -type f | sort | xargs shasum -a 256) > "$DATA/v3_root_inventory_after_supp.txt"; wc -l "$DATA/v3_root_inventory_before_supp.txt" "$DATA/v3_root_inventory_after_supp.txt"
$PY - "$DATA/v3_root_inventory_before_supp.txt" "$DATA/v3_root_inventory_after_supp.txt" "$DATA/v3_root_inventory_diff_supp.json" <<'PY'
import json,sys,collections
old={}; new={}
for line in open(sys.argv[1]): h,p=line.rstrip('\n').split('  ',1); old[p]=h
for line in open(sys.argv[2]): h,p=line.rstrip('\n').split('  ',1); new[p]=h
removed=[p for p in old if p not in new]; changed=[p for p in old if p in new and old[p]!=new[p]]; added=[p for p in new if p not in old]
top=collections.Counter('/'.join(p.split('/')[:6]) if '/workspace/' in p else '/'.join(p.split('/')[:5]) for p in added)
out={"pre_existing_files":len(old),"files_after":len(new),"removed":removed,"changed":changed,"added_count":len(added),"added_outside_new_run_dirs_and_smoke":[p for p in added if not (('/CONVERSION-BRANCH-TREATMENT-01/run-0' in p and int(p.split('/run-')[1][:3])>=6) or '/_smoke/' in p)],"added_by_top_dir":dict(top)}
json.dump(out,open(sys.argv[3],'w'),indent=1)
print("pre-existing:",len(old),"| after:",len(new),"| removed:",len(removed),"| changed:",len(changed),"| added:",len(added)); print("added outside run-006..015 and _smoke:",out["added_outside_new_run_dirs_and_smoke"]); print("changed:",changed); print("removed:",removed)
PY
echo "== first block still intact? =="
(cd "$V3" && shasum -a 256 benchmark_runs/$AGENT/CONVERSION-BRANCH-*/run-00[1-5]/evaluation.json | cut -c1-16,66-) | diff "$DATA/branch_first_block_eval_hashes.txt" - > /dev/null && echo "first-block evaluation.json hashes: unchanged" || echo "FIRST-BLOCK EVALUATION HASHES CHANGED"
(cd "$RUNS" && shasum -a 256 -c "$DATA/run_artifact_hashes.txt" --quiet) && echo "first-block 200-file artifact manifest: unchanged" || echo "FIRST-BLOCK ARTIFACT MANIFEST CHANGED"
(cd "$R" && shasum -a 256 branch_dispatch_results.json | cut -c1-16,66-) | diff "$DATA/branch_first_block_results_hash.txt" - > /dev/null && echo "branch_dispatch_results.json: unchanged" || echo "branch_dispatch_results.json CHANGED"
echo "== protected trees unchanged? =="
ls "$D/new_bug_variants/Lang/bug-1" | diff "$V3/v3_canon_variants_before.txt" - && ls "$D/benchmark_runs/$AGENT" | diff "$V3/v3_canon_runs_before.txt" - && (cd "$RR/diagnostic-noncanonical-v1" && find . -maxdepth 1 -type f | sort | xargs shasum -a 256) | diff "$V3/v3_diag_v1_before.txt" - && (cd "$RR/diagnostic-noncanonical-v2" && find . -maxdepth 1 -type f | sort | xargs shasum -a 256) | diff "$V3/v3_diag_v2_before.txt" - && (cd "$RR/real/out" && find . -type f | sort | xargs shasum -a 256) | diff "$V3/v3_real_before.txt" - && (cd "$LC" && for A in CONVERSION-CONTROL-01 CONVERSION-TREATMENT-01; do for f in variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md; do shasum -a 256 "$A/$f"; done; done) | diff "$V3/v3_lc_packages_before.txt" - && (cd "$V3" && shasum -a 256 diagnostic_v3_results.json treatment_supplementary_results.json benchmark_runs/$AGENT/CONVERSION-CONTROL-01/run-*/evaluation.json benchmark_runs/$AGENT/CONVERSION-TREATMENT-01/run-*/evaluation.json | cut -c1-16,66-) | diff "$LCH/analysis/data/v3_all_runs_eval_hashes.txt" - && (cd "$V3" && shasum -a 256 benchmark_runs/$AGENT/CONVERSION-LONG-*/run-*/evaluation.json | cut -c1-16,66-) | diff "$DP/analysis/data/long_chain_eval_hashes.txt" - && (cd "$LCH" && shasum -a 256 CONVERSION-LONG-*/variant.patch CONVERSION-LONG-*/test.patch CONVERSION-LONG-*/variant_manifest.json CONVERSION-LONG-*/validation.json CONVERSION-LONG-*/NON_CANONICAL.md) | diff "$LCH/analysis/data/package_hashes.txt" - && (cd "$V3" && shasum -a 256 benchmark_runs/$AGENT/CONVERSION-DISPATCH-*/run-*/evaluation.json | cut -c1-16,66-) | diff "$DATA/dispatch_eval_hashes.txt" - && (cd "$DP" && shasum -a 256 CONVERSION-DISPATCH-*/variant.patch CONVERSION-DISPATCH-*/test.patch CONVERSION-DISPATCH-*/variant_manifest.json CONVERSION-DISPATCH-*/validation.json CONVERSION-DISPATCH-*/NON_CANONICAL.md) | diff "$DP/analysis/data/package_hashes.txt" - && (cd "$R" && shasum -a 256 CONVERSION-BRANCH-*/variant.patch CONVERSION-BRANCH-*/test.patch CONVERSION-BRANCH-*/variant_manifest.json CONVERSION-BRANCH-*/validation.json CONVERSION-BRANCH-*/NON_CANONICAL.md) | diff "$DATA/package_hashes.txt" - && echo "unchanged (canonical trees, v1/v2 roots, real/out, 2-hop packages, 15 v3 run evaluations, long-chain packages + 10 evaluations, dispatch packages + 10 evaluations, branch packages)" || echo "A PROTECTED TREE CHANGED"
echo "== new-run artifact manifest (run-006..015, top-level files) =="; (cd "$RUNS" && for i in 006 007 008 009 010 011 012 013 014 015; do [ -d "$V/run-$i" ] && find "$V/run-$i" -maxdepth 1 -type f; done | sort | xargs shasum -a 256) > "$DATA/run_artifact_hashes_supplementary.txt"; wc -l "$DATA/run_artifact_hashes_supplementary.txt"
echo "== credential-pattern scan of the new artifacts (names/counts only; values never printed) =="
$PY - "$RUNS/$V" <<'PY'
import os,re,sys,json
root=sys.argv[1]; pat=re.compile(rb"sk-[A-Za-z0-9_-]{16,}"); hits=[]; scanned=0
for i in range(6,16):
    rd=os.path.join(root,f"run-{i:03d}")
    if not os.path.isdir(rd): continue
    for dp,_,fs in os.walk(rd):
        if "/workspace/" in dp+"/": continue
        for fn in fs:
            p=os.path.join(dp,fn); scanned+=1
            try: b=open(p,'rb').read()
            except Exception: continue
            for m in pat.finditer(b):
                ctx=b[max(0,m.start()-400):m.start()]; hits.append({"file":os.path.relpath(p,root),"len":m.end()-m.start(),"inside_encrypted_content_blob":(b"encrypted_content" in ctx) or fn.endswith("traj.json") and b"encrypted_content" in b[max(0,m.start()-5000):m.start()]})
print("files scanned:",scanned,"| pattern hits:",len(hits),"| hits outside encrypted reasoning blobs:",sum(1 for h in hits if not h["inside_encrypted_content_blob"]))
for h in hits: print("  ",h["file"],"len",h["len"],"encrypted_content context:",h["inside_encrypted_content_blob"])
PY
echo "== integrity record finished: $(date -u +%FT%TZ) =="
