"""Stage B build library (weaker-model-v1). Wraps the supervisor's generator modules (vendored in scripts/generator,
see PROVENANCE.json) so a HAND-AUTHORED N-hop design can be built with the recipe's own host draw, anonymous anchors,
facade-javadoc lie and exact-substring fault application. No LLM is called anywhere here.

Recipe elements kept as code: host_search.pick_two_hosts (seeded draw over classes >= min_host_lines, package
diversity preferred), host_search.pick_insertion_anchor (seeded interior public method, 4-space indented, never first or
last), chain_transform.rewrite_facade (body replacement + lie appended inside the existing javadoc),
validate.apply_line_replacement (original line must occur exactly once).
Deviations, all recorded per cell: anchors never land on a hop inserted earlier (seed advanced until a pre-existing method
is drawn; the generator could anchor on its own hop); hosts that are interfaces or enums are skipped (a static method in
a 1.4-era interface does not compile); patches are captured byte-exact (CRLF files keep their CRs).
"""
import os, sys, re, json, shutil, subprocess, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "generator")
if GEN not in sys.path:
    sys.path.insert(0, GEN)
import host_search            # noqa: E402
import chain_transform        # noqa: E402
import extract_transform      # noqa: E402
import candidate_search       # noqa: E402
import validate               # noqa: E402

os.environ.setdefault("PERL5LIB", os.path.expanduser("~/perl5/lib/perl5"))
D4J_BIN = "/Users/shawnli/Desktop/Honours/defects4j/framework/bin"
if D4J_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = D4J_BIN + ":" + os.environ.get("PATH", "")

LAYOUT = {  # fixture-relative roots
    "Lang":  {"source_root": "src/main/java", "test_root": "src/test/java"},
    "Math":  {"source_root": "src/main/java", "test_root": "src/test/java"},
    "Chart": {"source_root": "source",        "test_root": "tests"},
}
ROOT = os.path.dirname(HERE)
FIXTURES = {p: os.path.realpath(os.path.join(ROOT, "construction", "fresh", p)) for p in LAYOUT}

# ---------------------------------------------------------------- byte-exact text edits (CRLF-safe, asserted)
_EOL = {}
def rd(p):
    raw = open(p, "rb").read().decode("utf-8")
    _EOL[p] = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n")
def wr(p, t):
    open(p, "wb").write(t.replace("\n", _EOL.get(p, "\n")).encode("utf-8"))
def edit(path, old, new):
    t = rd(path); n = t.count(old)
    assert n == 1, f"{os.path.basename(path)}: expected exactly one match for {old[:80]!r}, got {n}"
    wr(path, t.replace(old, new, 1))
def insert_before(path, anchor, block):
    t = rd(path); n = t.count(anchor)
    assert n == 1, f"{os.path.basename(path)}: anchor not unique ({n}): {anchor[:60]!r}"
    wr(path, t.replace(anchor, block + anchor, 1))
def add_import(path, existing_import_line, new_import_line):
    """Insert `new_import_line` right after an existing import line (both full lines without newline)."""
    t = rd(path)
    if new_import_line + "\n" in t:
        return False
    edit(path, existing_import_line + "\n", existing_import_line + "\n" + new_import_line + "\n")
    return True

# ---------------------------------------------------------------- work tree
def run(cmd, cwd, timeout=600, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env or os.environ)
def run_bytes(cmd, cwd, timeout=600):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout)
    assert p.returncode == 0, p.stdout.decode() + p.stderr.decode()
    return p.stdout
def prepare_work(project, work):
    """Copy the fixture to `work` (must not exist) and require a clean tracked tree."""
    src = FIXTURES[project]
    assert os.path.isdir(src), src
    assert not os.path.exists(work), f"{work} exists"
    shutil.copytree(src, work, symlinks=True)
    for d in ("build", "build-tests", "target"):
        shutil.rmtree(os.path.join(work, d), ignore_errors=True)
    dirty = [l for l in run(["git", "status", "--short"], work).stdout.splitlines() if not l.startswith("??")]
    assert not dirty, "work tree not clean: " + " ".join(dirty)
    return work
def status(work):
    return run(["git", "status", "--short"], work).stdout.strip()

# ---------------------------------------------------------------- recipe: hosts and anchors
_TYPE_RE = re.compile(r'^\s*((?:public\s+|abstract\s+|final\s+|strictfp\s+)*)(class|interface|enum|@interface)\s+(\w+)', re.M)
def top_level_kind(path):
    """(kind, name, public) of the first top-level type. Hosts must be public concrete classes: a package-private class (e.g.
    FastMathLiteralArrays) cannot be called from a hop in another package; the generator does not check this (W15)."""
    t = rd(path)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S); t = re.sub(r'//[^\n]*', '', t)
    m = _TYPE_RE.search(t)
    return (m.group(2), m.group(3), "public" in m.group(1)) if m else (None, None, False)
def host_pool(project, min_lines=1500, exclude_files=()):
    src = os.path.join(FIXTURES[project], LAYOUT[project]["source_root"])
    pool = candidate_search.find_large_classes(src, min_lines)
    out = []
    for f, n in pool:
        rel = os.path.relpath(f, src)
        if rel in exclude_files or f in exclude_files:
            continue
        kind, name, pub = top_level_kind(f)
        out.append({"file": rel, "lines": n, "kind": kind, "public": pub, "usable": kind == "class" and pub})
    return out
def draw_hosts(project, target_rel, n_hosts, seed, min_lines=1500, exclude_rel=()):
    """Draw n_hosts distinct host files with the recipe's pick_two_hosts, two at a time (seed, seed+1, ...), excluding
    the target, already drawn hosts, and non-class files. Returns [{file, lines, seed, note}] in draw order."""
    src = os.path.join(FIXTURES[project], LAYOUT[project]["source_root"])
    target_abs = os.path.join(src, target_rel)
    bad = {os.path.join(src, h["file"]) for h in host_pool(project, min_lines) if not h["usable"]}
    excluded = set(bad) | {os.path.join(src, r) for r in exclude_rel}
    drawn, s = [], seed
    while len(drawn) < n_hosts:
        remaining = [h for h in host_pool(project, min_lines) if os.path.join(src, h["file"]) not in excluded
                     and os.path.join(src, h["file"]) != target_abs]
        if len(remaining) == 1:   # pick_two_hosts needs two; take the last one directly, note it
            h = remaining[0]; drawn.append({"file": h["file"], "lines": h["lines"], "seed": s, "note": "last remaining host (pool exhausted)"})
            break
        if not remaining:
            break
        h1, h2, note = host_search.pick_two_hosts(src, target_abs, min_lines, seed=s, exclude_files=sorted(excluded))
        for h in (h1, h2):
            if len(drawn) < n_hosts:
                rel = os.path.relpath(h, src)
                drawn.append({"file": rel, "lines": sum(1 for _ in open(h, encoding="utf-8", errors="ignore")), "seed": s, "note": note})
                excluded.add(h)
        s += 1
    return drawn
def pick_anchor(host_abs, seed, exclude_names=(), max_tries=200):
    """Recipe anchor, but never a method named in exclude_names (hops inserted earlier). Returns (line_idx, name, seed_used)."""
    for k in range(max_tries):
        line_idx, name = host_search.pick_insertion_anchor(host_abs, seed + k)
        if name is None:
            return None, None, seed + k
        if name not in exclude_names:
            return line_idx, name, seed + k
    raise RuntimeError(f"no admissible anchor in {host_abs}")
def insert_hop(host_abs, method_text, seed, exclude_names=()):
    """chain_transform.insert_method_at_anonymous_point with the anchor exclusion. Returns an audit dict."""
    text, crlf = validate.read_text_smart(host_abs)
    line_idx, anchor_name, used = pick_anchor(host_abs, seed, exclude_names)
    lines = text.split("\n")
    indented = "\n".join("    " + l if l.strip() else l for l in method_text.strip().split("\n"))
    if line_idx is not None:
        new_lines = lines[:line_idx] + ["", indented, ""] + lines[line_idx:]
        validate.write_text_smart(host_abs, "\n".join(new_lines), crlf)
    else:
        last = text.rstrip().rindex("}")
        validate.write_text_smart(host_abs, text[:last] + "\n    " + indented + "\n\n" + text[last:], crlf)
    return {"host": host_abs, "anchor_after_method": anchor_name, "anchor_line_idx": line_idx, "seed_requested": seed, "seed_used": used}

# ---------------------------------------------------------------- facade and fault
def replace_method_body(path, method_name, new_body, near_line=None, lie_sentence=None):
    """With a lie: the recipe's rewrite_facade (body + lie in the javadoc). Without: the same body splice only."""
    if lie_sentence:
        chain_transform.rewrite_facade(path, method_name, new_body, lie_sentence, near_line=near_line)
        return
    text, crlf = validate.read_text_smart(path)
    span = extract_transform.find_method_span(text, method_name, near_line=near_line)
    assert span is not None, f"method {method_name} not found in {path}"
    header_start, body_end = span
    first_brace = text.index("{", header_start)
    text = text[:header_start] + text[header_start:first_brace + 1] + "\n        " + new_body.strip() + "\n    }" + text[body_end:]
    validate.write_text_smart(path, text, crlf)
def method_text(path, method_name, near_line=None):
    text, _ = validate.read_text_smart(path)
    span = extract_transform.find_method_span(text, method_name, near_line=near_line)
    assert span is not None, f"method {method_name} not found in {path}"
    return text[span[0]:span[1]]
def apply_fault(path, original_line, buggy_line):
    """Exact-once replacement like validate.apply_line_replacement, but CRLF-normalised like the validator's replace_once."""
    edit(path, original_line, buggy_line)

# ---------------------------------------------------------------- defects4j
def d4j(args, cwd, timeout=1800):
    return run(["defects4j"] + args, cwd, timeout=timeout)
def compile_ok(work):
    p = d4j(["compile"], work, timeout=900)
    ok = p.returncode == 0 and "BUILD FAILED" not in p.stdout + p.stderr
    return ok, (p.stdout + p.stderr)[-3000:]
_FAIL_RE = re.compile(r'Failing tests:\s*(\d+)')
_ID_RE = re.compile(r'-\s+([\w.$]+::\w+)')
def _parse(out):
    m = _FAIL_RE.search(out)
    return (int(m.group(1)) if m else None), set(_ID_RE.findall(out))
def test_one(work, test_id, timeout=600):
    p = d4j(["test", "-t", test_id], work, timeout=timeout)
    n, ids = _parse(p.stdout + p.stderr)
    ft = os.path.join(work, "failing_tests")
    detail = open(ft, encoding="utf-8", errors="ignore").read() if os.path.exists(ft) else ""
    return n, ids, detail[:4000]
def full_suite(work, timeout=3600):
    p = d4j(["test"], work, timeout=timeout)
    n, ids = _parse(p.stdout + p.stderr)
    return n, ids, (p.stdout + p.stderr)[-2000:]

# ---------------------------------------------------------------- packaging helpers
def emit_patches(work, src_files_rel, test_files_rel, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    vp = run_bytes(["git", "diff", "--"] + list(src_files_rel), work)
    tp = run_bytes(["git", "diff", "--"] + list(test_files_rel), work) if test_files_rel else b""
    open(os.path.join(out_dir, "variant.patch"), "wb").write(vp)
    open(os.path.join(out_dir, "test.patch"), "wb").write(tp)
    return {"variant.patch": hashlib.sha256(vp).hexdigest(), "test.patch": hashlib.sha256(tp).hexdigest(),
            "variant_lines": vp.count(b"\n"), "test_lines": tp.count(b"\n")}
def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)

if __name__ == "__main__":   # preview: hosts the recipe draws for a project/target/seed, with the anchors it would use
    project, target_rel, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    print("pool:", json.dumps(host_pool(project), indent=0))
    hosts = draw_hosts(project, target_rel, n, seed)
    src = os.path.join(FIXTURES[project], LAYOUT[project]["source_root"])
    for i, h in enumerate(hosts):
        li, name, used = pick_anchor(os.path.join(src, h["file"]), seed + 100 + i)
        print(f"hop{i+1}: {h['file']} ({h['lines']} lines) draw-seed {h['seed']} [{h['note']}] -> anchor after `{name}` at line {li} (seed {used})")
