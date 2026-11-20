"""Stage B copy of mx_harness_check.py: stages with THIS root's evaluation server w55 (SB4). Harness-compatibility check (builder gate G14; AMENDMENTS X10). Usage: mx_harness_check.py <project> <variant.patch> <test.patch>
Reproduces the frozen server's workspace staging exactly: the checkout is copied with the server's OWN copyDirectoryFiltered and
stripHistoryDirs (models/mxF0/variant-lab/server/agents/agentAdapter.mjs, imported read-only with node), which drop *.bak / *.orig /
*.rej / *.patch files, private-metadata names and VCS/IDE/build directories. Both patches must then dry-run with the server's exact
command, `patch -p1 --forward --batch --dry-run`. The copy source is construction/fresh/<project> (the builders' base, identical
in content to the server's workspaces/defects4j/<project>-1/fixed). Prints PASS or FAIL with details; exit 0 = PASS."""
import json, os, sys, shutil, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
MX = C.V3; P, VP, TP = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
# SB4: stage with the Stage B evaluation server w55 (server tree byte-identical to mxF0)
HAR = f"{MX}/models/w55/variant-lab/server/agents/agentAdapter.mjs"
FRESH = os.path.realpath(f"{MX}/construction/fresh/{P}")   # SB5: ALWAYS the real directory. The server's copyDirectoryFiltered turns a
# symlinked source into a symlinked destination and stripHistoryDirs then deletes .git/.svn THROUGH the link in the real fixture
# (incident 2026-10-14, AMENDMENTS W12). The destination is asserted to be a real directory before anything is stripped.
d = tempfile.mkdtemp(prefix="mxb-", dir="/private/tmp"); dst = f"{d}/w"
js = (f"import({json.dumps(HAR)}).then(async m => {{ await m.copyDirectoryFiltered({json.dumps(FRESH)}, {json.dumps(dst)}); "
      f"await m.stripHistoryDirs({json.dumps(dst)}); }}).catch(e => {{ console.error(String(e)); process.exit(3); }})")
assert not os.path.islink(FRESH) and os.path.isdir(FRESH), FRESH
js = (f"import({json.dumps(HAR)}).then(async m => {{ await m.copyDirectoryFiltered({json.dumps(FRESH)}, {json.dumps(dst)}); "
      f"const fs = await import('node:fs'); if (fs.lstatSync({json.dumps(dst)}).isSymbolicLink()) {{ console.error('destination is a symlink'); process.exit(4); }} "
      f"await m.stripHistoryDirs({json.dumps(dst)}); }}).catch(e => {{ console.error(String(e)); process.exit(3); }})")
r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=900)
out = {"staging_rc": r.returncode, "staging_err": r.stderr[-400:], "patches": []}
ok = r.returncode == 0 and os.path.isdir(dst)
if ok:
    for p in (VP, TP):
        if not os.path.getsize(p): continue
        q = subprocess.run(["patch", "-p1", "--forward", "--batch", "--dry-run", "-i", p], cwd=dst, capture_output=True, text=True, timeout=120)
        out["patches"].append({"patch": os.path.basename(p), "rc": q.returncode, "output": (q.stdout + q.stderr)[-600:]})
        ok = ok and q.returncode == 0
shutil.rmtree(d, ignore_errors=True)
print(("PASS " if ok else "FAIL ") + json.dumps(out)); sys.exit(0 if ok else 1)
