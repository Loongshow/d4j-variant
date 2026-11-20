"""Main run (weaker-model-v1): per-instance fixtures so the verified Stage B C10 recipe can be built on real Defects4J bug identities.
An instance key is '<Project>-<bugId>' (e.g. 'Lang-3'). Its fixture is construction/fresh-mr/<key>: a REAL-DIRECTORY copy of the
frozen harness's own fixed checkout (realpath of models/w55/workspaces/defects4j/<key>/fixed, which the w55 server stages for the
agent), so builder patches apply byte-exactly to what the agent will see. This module registers that fixture and its source and
test roots (Defects4J dir-layout.csv for the fixed revision) in stageB_lib, so the Stage B recipe functions (seeded host draw,
anonymous anchors, facade rewrite with the lie, exact-once fault) are reused unchanged.
Never pass a symlinked path to the server's copy routines (incident W12): fixtures are made from the realpath and asserted real.

CLI:  mr_lib.py fixture <key>                       create/verify the fixture
      mr_lib.py seed <key>                          the instance's deterministic host-draw seed
      mr_lib.py preview <key> <target_rel> [n=5]    hosts the recipe draws for this target with the instance seed, and their anchors"""
import os, sys, csv, json, shutil, subprocess, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stageB_lib as L   # noqa: E402

D4J = "/Users/shawnli/Desktop/Honours/defects4j"; FW = f"{D4J}/framework/projects"
HARNESS = os.path.join(L.ROOT, "models/w55/workspaces/defects4j")
FRESH_MR = os.path.join(L.ROOT, "construction/fresh-mr")

def split(key):
    p, b = key.rsplit("-", 1); return p, int(b)

def fixed_rev(p, b):
    for r in csv.DictReader(open(f"{FW}/{p}/active-bugs.csv")):
        if int(r["bug.id"]) == b: return r["revision.id.fixed"]
    raise KeyError(f"{p}-{b} not an active Defects4J bug")

def layout(p, rev):
    for row in csv.reader(open(f"{FW}/{p}/dir-layout.csv")):
        if row and row[0] == rev: return row[1], row[2]
    raise KeyError(f"no dir-layout for {p} {rev}")

def seed(key):
    """Deterministic per-instance seed (fixed before any build), used for the host draw and the anchors (seed + 100 + i)."""
    return 2000 + int(hashlib.sha256(f"weaker-model-v1/main-run:{key}".encode()).hexdigest()[:8], 16) % 7000

def fixture(key, create=True):
    p, b = split(key); dst = os.path.join(FRESH_MR, key)
    if not os.path.isdir(dst):
        assert create, f"fixture {key} missing"
        src = os.path.realpath(os.path.join(HARNESS, key, "fixed"))
        assert os.path.isdir(src) and not os.path.islink(src), f"harness checkout missing: {src}"
        os.makedirs(FRESH_MR, exist_ok=True); shutil.copytree(src, dst, symlinks=True)
        for d in ("build", "build-tests", "target"): shutil.rmtree(os.path.join(dst, d), ignore_errors=True)
    assert not os.path.islink(dst) and os.path.isdir(os.path.join(dst, ".git")), f"{dst} must be a real checkout with .git"
    st = subprocess.run(["git", "status", "--short"], cwd=dst, capture_output=True, text=True).stdout
    dirty = [l for l in st.splitlines() if not l.startswith("??")]
    assert not dirty, f"{key} fixture has tracked modifications: {dirty[:5]}"
    src_root, test_root = layout(p, fixed_rev(p, b))
    L.LAYOUT[key] = {"source_root": src_root, "test_root": test_root}; L.FIXTURES[key] = os.path.realpath(dst)
    return os.path.realpath(dst)

if __name__ == "__main__":
    cmd, key = sys.argv[1], sys.argv[2]
    if cmd == "fixture":
        print(fixture(key), L.LAYOUT[key])
    elif cmd == "seed":
        print(seed(key))
    elif cmd == "preview":
        fixture(key); target_rel = sys.argv[3]; n = int(sys.argv[4]) if len(sys.argv) > 4 else 5; s = seed(key)
        pool = L.host_pool(key)
        print("seed", s, "| host pool:", json.dumps([{k: h[k] for k in ("file", "lines", "usable")} for h in pool]))
        hosts = L.draw_hosts(key, target_rel, n, s)
        src = os.path.join(L.FIXTURES[key], L.LAYOUT[key]["source_root"])
        for i, h in enumerate(hosts):
            li, name, used = L.pick_anchor(os.path.join(src, h["file"]), s + 100 + i)
            print(f"hop{i+1}: {h['file']} ({h['lines']} lines) draw-seed {h['seed']} [{h['note']}] -> anchor after `{name}` (line {li}, seed {used})")
