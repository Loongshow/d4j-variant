"""Stage B release step: for each bug whose independent audit is CONFIRMED and whose four cells are READY, copy the spec into
instances/<iid>/spec.json (so the freeze hashes it), package the variant (stageB_package.py), then merge the key (stageB_key.py)
and print the plan command with the Stage B preregistration sha bound into the plan purpose.
Usage: stageB_release.py B1 B2 B3   (idempotent: already packaged cells are skipped)"""
import json, os, sys, shutil, subprocess, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
WM = C.V3; PY = sys.executable; done = []
for bug in sys.argv[1:]:
    ap = f"{WM}/construction/stageB/audits/SB-{bug}.json"
    assert os.path.exists(ap), f"no audit for {bug}"
    a = json.load(open(ap)); assert a.get("verdict") == "CONFIRMED", f"{bug} audit verdict {a.get('verdict')!r}: not packaging"
    for cell in ("C00", "C01", "C10", "C11"):
        iid = f"SB-{bug}-{cell}"; src = f"{WM}/construction/stageB/specs/{iid}.json"; dst = f"{WM}/instances/{iid}/spec.json"
        v = json.load(open(f"{WM}/instances/{iid}/validation.json")); assert v.get("overall") == "READY", f"{iid} not READY"
        if os.path.exists(dst) and json.load(open(dst)).get("variant_id"):
            print(iid, "already packaged as", json.load(open(dst))["variant_id"]); done.append(iid); continue
        shutil.copyfile(src, dst)
        r = subprocess.run([PY, f"{WM}/scripts/stageB_package.py", dst], capture_output=True, text=True); print(r.stdout.strip(), r.stderr.strip()[-300:])
        assert r.returncode == 0, iid
        shutil.copyfile(dst, src)   # keep the construction copy in step (variant_id, kind, fault_lines, gold_key)
        done.append(iid)
r = subprocess.run([PY, f"{WM}/scripts/stageB_key.py"], capture_output=True, text=True); print(r.stdout.strip(), r.stderr.strip()[-300:])
sha = hashlib.sha256(open(f"{WM}/STAGE_B_PREREGISTRATION.md", "rb").read()).hexdigest()
print("\nplan command:\n", f"{PY} scripts/mx_plan.py plans/B_stageB_gpt55.json --iids {','.join(done)} --runs 5 --seed 1014 --purpose \"Stage B 2x2 on gpt-5.5; STAGE_B_PREREGISTRATION.md sha256 {sha}\"")
