"""Shared construction helpers for adversarial attack builders (Lang/Compress/JacksonCore checkouts).
All edits are asserted-unique; patches come from `git diff` of TRACKED files (new files are added with `git add -N`
explicitly by name, never `git add -N .`)."""
import os, re, subprocess, sys, json, shutil
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/shim")
from callgraph import extract_methods_from_file
ENV = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
HIST_LANG_PATCH = f"{SP}/diagnostic-noncanonical-v3/new_bug_variants/Lang/bug-1/L20/CONVERSION-LONG-TREATMENT-01/variant.patch"

def sh(cmd, cwd, check=True, timeout=1800):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=ENV, timeout=timeout)
    if check and p.returncode != 0:
        raise SystemExit(f"FAILED {' '.join(cmd)}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}")
    return p.stdout + p.stderr

def reset(work):
    sh(["git", "reset", "-q", "--", "."], work); sh(["git", "checkout", "--", "."], work); sh(["git", "clean", "-fdq", "--", "src", "tests", "source"], work)
    dirty = [l for l in sh(["git", "status", "--short"], work).splitlines() if not l.startswith("??")]
    assert not dirty, dirty

def read(work, rel):
    raw = open(os.path.join(work, rel), "rb").read().decode("utf-8"); return raw.replace("\r\n", "\n"), ("\r\n" if "\r\n" in raw else "\n")

def write(work, rel, text, eol="\n"):
    os.makedirs(os.path.dirname(os.path.join(work, rel)), exist_ok=True)
    open(os.path.join(work, rel), "wb").write(text.replace("\n", eol).encode("utf-8"))

def replace_once(work, rel, old, new):
    t, eol = read(work, rel); assert t.count(old) == 1, (rel, old[:60], t.count(old)); write(work, rel, t.replace(old, new, 1), eol)

def insert_after_method(work, rel, method_name, block, nth=0):
    """Insert `block` (already indented, no trailing blank) after the closing brace of the nth method named method_name."""
    ms = [m for m in extract_methods_from_file(os.path.join(work, rel)) if m["name"] == method_name]
    assert ms, (rel, method_name); m = ms[nth]
    t, eol = read(work, rel); lines = t.split("\n"); at = m["end_line"]
    lines = lines[:at] + [""] + block.rstrip("\n").split("\n") + lines[at:]
    write(work, rel, "\n".join(lines), eol); return at + 2

def insert_before_class_end(work, rel, block):
    t, eol = read(work, rel); k = t.rstrip().rfind("}"); write(work, rel, t[:k].rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n}\n", eol)

def add_import(work, rel, line):
    t, eol = read(work, rel)
    if line in t: return
    imps = list(re.finditer(r"^import .*;$", t, re.M))
    if imps: k = imps[-1].end(); write(work, rel, t[:k] + "\n" + line + t[k:], eol); return
    pk = re.search(r"^package .*;$", t, re.M); assert pk, rel; k = pk.end(); write(work, rel, t[:k] + "\n\n" + line + t[k:], eol)

def add_test_method(work, test_rel, method_text):
    """Append a test method before the final closing brace of the test class."""
    insert_before_class_end(work, test_rel, method_text)

def apply_patch(work, patch):
    sh(["git", "apply", patch], work)

def new_file(work, rel, text):
    write(work, rel, text); sh(["git", "add", "-N", rel], work)

def diff_to(work, out_patch, paths=None):
    cmd = ["git", "diff", "--binary"] + (["--"] + paths if paths else [])
    p = subprocess.run(cmd, cwd=work, capture_output=True, env=ENV); open(out_patch, "wb").write(p.stdout); return len(p.stdout)

def compile_(work):
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(work, d), ignore_errors=True)
    o = sh(["defects4j", "compile"], work, check=False, timeout=1200); return ("BUILD FAILED" not in o and "error:" not in o), o

def trigger(work, tid):
    o = sh(["defects4j", "test", "-t", tid], work, check=False, timeout=900); m = re.search(r"Failing tests:\s*(\d+)", o)
    ft = open(os.path.join(work, "failing_tests")).read() if os.path.exists(os.path.join(work, "failing_tests")) else ""
    return (int(m.group(1)) if m else None), ft.strip().splitlines()[:3]

def package_dir(attack_id):
    d = f"{SP}/adversarial-break-v1/construction/packages/{attack_id}"; os.makedirs(d, exist_ok=True); return d

def split_patch_into_test_and_variant(work, out_dir, test_paths):
    """Write test.patch (only test files) and variant.patch (everything else) from the current diff."""
    all_changed = [l[3:] for l in sh(["git", "status", "--short"], work).splitlines() if l.strip()]
    tests = [p for p in all_changed if any(p.startswith(t) or p == t for t in test_paths)]
    prods = [p for p in all_changed if p not in tests]
    n1 = diff_to(work, f"{out_dir}/test.patch", tests); n2 = diff_to(work, f"{out_dir}/variant.patch", prods)
    return n1, n2, tests, prods
