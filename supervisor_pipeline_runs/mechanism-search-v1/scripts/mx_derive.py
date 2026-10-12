"""Phase 4 (EXPLORATORY) derived revision of an existing instance. Usage: mx_derive.py <derive_spec.json>
Spec: iid, parent_iid, revision, mechanism, tags, purpose, edits [{file, old, new, why}] (exact, each `old` occurs once),
  remove_files [path] (files the parent patches add, dropped whole), optional gold/decoys/entry_points/evidence overrides.
Applies the parent's variant.patch + test.patch to a copy of construction/fresh/<project>, applies the edits, and regenerates both
patches (files of the parent patches; an edited file joins the patch whose file list holds it, else main unless under a test root).
Validation on a second fresh copy: D1 apply + compile; D2 the parent's trigger fails 3x byte-identical with the parent's recorded
assertion; D3 full suite: only the trigger fails beyond the pristine baseline; D4 no fault vocabulary in added lines (builder's
FORBID list); D5 gold/decoys submittable (G13 rule). READY only if every gate passes. Installs under an opaque id
(namespace mechanism-search-v1) and writes the key entry atomically (the running driver reads the key)."""
import json, os, re, sys, shutil, hashlib, subprocess, tempfile, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
L = C.L; MX = C.V3
spec = json.load(open(sys.argv[1])); IID = spec["iid"]
keyp = f"{MX}/review/VARIANT_KEY.json"; key = json.load(open(keyp))
pv, pk = next((v, k) for v, k in key.items() if k["instance_id"] == spec["parent_iid"])
P = pk["project"]; FRESH = f"{MX}/construction/fresh/{P}"; PD = f"{MX}/new_bug_variants/{P}/bug-1/L20/{pv}"
B = f"{MX}/instances/{IID}/build"; os.makedirs(B, exist_ok=True); OUT = f"{MX}/instances/{IID}/validation.json"
ENV = {**os.environ, "PERL5LIB": os.path.expanduser("~/perl5/lib/perl5")}
FORBID = re.compile(r"\b(bug|bugs|buggy|fault|faulty|wrong|wrongly|incorrect|incorrectly|broken|gold|decoy|cue|fixme|todo|xxx|hack|mistake|erroneous|should be|inverted|reversed)\b", re.I)
R = {"schema_version": "mechanism-search-v1/derive-validation/v1", "iid": IID, "parent_iid": spec["parent_iid"], "parent_variant": pv,
     "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "gates": []}
def save(): json.dump(R, open(OUT, "w"), indent=1)
def gate(g, name, ok, out):
    R["gates"].append({"gate": g, "name": name, "status": "pass" if ok else "FAIL", "key_output": str(out)[-1500:]}); save()
    print(f"{g:3s} {'pass' if ok else 'FAIL'}  {name}", flush=True); return ok
def sh(cmd, cwd, timeout=5400):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=ENV); return p.returncode, p.stdout + p.stderr
def copy_fresh(tag):
    d = tempfile.mkdtemp(prefix="mxb-", dir="/private/tmp"); shutil.copytree(FRESH, f"{d}/w", symlinks=True)
    subprocess.run(["chmod", "-R", "u+w", f"{d}/w"]); return f"{d}/w"
def files_of(patch): return [l[6:].strip() for l in open(patch, errors="replace") if l.startswith("+++ b/")]
def compile_(w):
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(w, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"], w, 1800); return rc == 0 and "BUILD FAILED" not in o
def d4j_test(w, tid=None):
    rc, o = sh(["defects4j", "test"] + (["-t", tid] if tid else []), w)
    m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    fp = os.path.join(w, "failing_tests"); ft = open(fp, errors="replace").read().strip() if os.path.exists(fp) else ""
    return n, ft, sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M)))
ok = True
# build
main0, test0 = files_of(f"{PD}/variant.patch"), files_of(f"{PD}/test.patch")
w = copy_fresh("build")
ap = all(sh(["git", "apply", f"{PD}/{p}"], w)[0] == 0 for p in ("variant.patch", "test.patch"))
for e in spec.get("edits", []):
    t = open(f"{w}/{e['file']}").read(); c = t.count(e["old"])
    assert c == 1, f"edit old text occurs {c} times in {e['file']}: {e['old'][:80]!r}"
    open(f"{w}/{e['file']}", "w").write(t.replace(e["old"], e["new"], 1))
for f in spec.get("remove_files", []): os.remove(f"{w}/{f}")
istest = lambda f: f in test0 or "/test/" in f or f.startswith("tests/")
mainf = sorted({f for f in main0 + [e["file"] for e in spec.get("edits", [])] if not istest(f)})
testf = sorted({f for f in test0 + [e["file"] for e in spec.get("edits", [])] if istest(f)} - set(spec.get("remove_files", [])))
sh(["git", "add", "-N", "--"] + [f for f in mainf + testf if os.path.exists(f"{w}/{f}")], w)   # new files must show in the diff
L.diff_to(w, f"{B}/variant.patch", mainf); L.diff_to(w, f"{B}/test.patch", testf)
# D4 / D5 static
hits = [(p, m.group(0), l.strip()[:90]) for p in ("variant.patch", "test.patch") for l in open(f"{B}/{p}", errors="replace").read().splitlines()
        if l.startswith("+") and not l.startswith("+++") for m in FORBID.finditer(l)]
ok = gate("D4", "no fault vocabulary in added lines", not hits, hits or "clean") and ok
gold = spec.get("gold", pk["gold"]); decoys = spec.get("decoys", pk["decoys"])
def unsub(q): c, m = q.split("::"); return c.endswith("Test") or c.endswith("Tests") or ".junit." in c or ".test." in c or m.startswith("test")
blocked = [q for q in gold + decoys if unsub(q)]
ok = gate("D5", "gold and decoys submittable by the harness validator", not blocked, blocked or "submittable") and ok
# D1-D3 on a fresh copy
wf = copy_fresh("fresh")
a1 = all(sh(["git", "apply", f"{B}/{p}"], wf)[0] == 0 for p in ("variant.patch", "test.patch")) if os.path.getsize(f"{B}/test.patch") else \
     sh(["git", "apply", f"{B}/variant.patch"], wf)[0] == 0
gc = a1 and compile_(wf)
ok = gate("D1", "fresh copy: patches apply and compile", ap and gc, f"parent_apply={ap} apply={a1} compile={gc}") and ok
TRIG = pk["trigger"]; S0 = pk["expected_signature"]; runs = [d4j_test(wf, TRIG) for _ in range(3)] if gc else []
d2 = bool(runs) and all(r[0] == 1 for r in runs) and len({r[1] for r in runs}) == 1 and S0 in runs[0][1]
ok = gate("D2", "trigger fails 3x byte-identical with the parent's recorded assertion", d2, (runs[0][1][:400] if runs else "no run")) and ok
w0 = copy_fresh("base"); base = d4j_test(w0)[2] if compile_(w0) else None
full = d4j_test(wf)[2] if gc else None
if spec.get("d3_match_parent"):
    # behaviour-preserving (documentation-only) revision of a parent with recorded collateral: the full-suite failure set must equal
    # the parent's, measured here on a third fresh copy, and contain the trigger
    wp = copy_fresh("parent"); pa = all(sh(["git", "apply", f"{PD}/{p}"], wp)[0] == 0 for p in ("variant.patch", "test.patch"))
    pfull = d4j_test(wp)[2] if (pa and compile_(wp)) else None; shutil.rmtree(os.path.dirname(wp), ignore_errors=True)
    d3 = pfull is not None and full is not None and set(full) == set(pfull) and TRIG in full
    ok = gate("D3", "full suite: failure set identical to the parent's (documentation-only revision)", d3,
              {"baseline": base, "parent_full": pfull, "variant_full": full}) and ok
else:
    d3 = base is not None and full is not None and set(full) - set(base) == {TRIG}
    ok = gate("D3", "full suite: only the trigger fails beyond the pristine baseline", d3, {"baseline": base, "variant_full": full}) and ok
R["status"] = "READY" if ok else "NOT_READY"; R["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
for d in (w, wf, w0): shutil.rmtree(os.path.dirname(d), ignore_errors=True)
if not ok: print(f"{IID}: NOT READY"); sys.exit(1)
# install
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
V = "CTV-" + hashlib.sha256(f"mechanism-search-v1:{IID}".encode()).hexdigest()[:6].upper()
assert V not in key or key[V]["instance_id"] == IID, f"id collision {V}"
dst = f"{MX}/new_bug_variants/{P}/bug-1/L20/{V}"
if os.path.exists(dst): shutil.rmtree(dst)
os.makedirs(dst)
for p in ("variant.patch", "test.patch"): shutil.copyfile(f"{B}/{p}", f"{dst}/{p}")
man = json.load(open(f"{PD}/variant_manifest.json"))
man.update({"variant_id": V, "artifact_hashes": {"variant.patch": h(f"{dst}/variant.patch"), "test.patch": h(f"{dst}/test.patch")},
            "manifest_extension": "mechanism-search-v1/derived/v1", "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
man.pop("provenance", None)
json.dump(man, open(f"{dst}/variant_manifest.json", "w"), indent=1)
vrec = {"variant_id": V, "status": "validated", "derived_validation": R}; json.dump(vrec, open(f"{dst}/validation.json", "w"), indent=1)
ent = dict(pk); ent.update({"instance_id": IID, "mechanism": spec["mechanism"], "tags": spec["tags"], "tier": "EXPLORATORY", "gold": gold, "decoys": decoys,
            "entry_points": spec.get("entry_points", pk["entry_points"]), "evidence": spec.get("evidence", pk.get("evidence", [])),
            "variant_patch_sha256": man["artifact_hashes"]["variant.patch"], "test_patch_sha256": man["artifact_hashes"]["test.patch"]})
key = json.load(open(keyp)); key[V] = ent
tmp = keyp + ".tmp"; json.dump(key, open(tmp, "w"), indent=1, sort_keys=True); os.replace(tmp, keyp)
sp = {"iid": IID, "variant_id": V, "project": P, "kind": "derived", "tier": "EXPLORATORY", "parent_iid": spec["parent_iid"], "parent_variant": pv,
      "revision": spec["revision"], "mechanism": spec["mechanism"], "tags": spec["tags"], "purpose": spec["purpose"], "edits": spec.get("edits", []),
      "remove_files": spec.get("remove_files", []), "gold": gold, "decoys": decoys, "trigger": TRIG, "expected_signature": S0}
json.dump(sp, open(f"{MX}/instances/{IID}/spec.json", "w"), indent=1)
print(f"{IID}: READY -> {V}")
