"""OCFLB construction helpers. Every edit is asserted-unique; patches come from `git diff` of tracked files (new files are
added with `git add -N` by name). Shared by all pair builders; do not fork per pair."""
import os, re, subprocess, sys, json, shutil, hashlib
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/shim")
from callgraph import extract_methods_from_file
ENV = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
O = f"{SP}/ocflb-v1"
HIST = f"{SP}/diagnostic-noncanonical-v3/new_bug_variants"
def hist_patch(project, vid, kind="variant"): return f"{HIST}/{project}/bug-1/L20/{vid}/{kind}.patch"

def sh(cmd, cwd, check=True, timeout=1800):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=ENV, timeout=timeout)
    if check and p.returncode != 0: raise SystemExit(f"FAILED {' '.join(cmd)}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}")
    return p.stdout + p.stderr
def reset(work):
    sh(["git", "reset", "-q", "--", "."], work); sh(["git", "checkout", "--", "."], work); sh(["git", "clean", "-fdq", "--", "src", "tests", "source"], work)
    dirty = [l for l in sh(["git", "status", "--short"], work).splitlines() if not l.startswith("??")]; assert not dirty, dirty
def read(work, rel):
    raw = open(os.path.join(work, rel), "rb").read().decode("utf-8"); return raw.replace("\r\n", "\n"), ("\r\n" if "\r\n" in raw else "\n")
def write(work, rel, text, eol="\n"):
    os.makedirs(os.path.dirname(os.path.join(work, rel)), exist_ok=True); open(os.path.join(work, rel), "wb").write(text.replace("\n", eol).encode("utf-8"))
def replace_once(work, rel, old, new):
    t, eol = read(work, rel); assert t.count(old) == 1, (rel, old[:70], t.count(old)); write(work, rel, t.replace(old, new, 1), eol)
def add_import(work, rel, line):
    t, eol = read(work, rel)
    if line in t: return
    imps = list(re.finditer(r"^import .*;$", t, re.M))
    if imps: k = imps[-1].end(); write(work, rel, t[:k] + "\n" + line + t[k:], eol); return
    pk = re.search(r"^package .*;$", t, re.M); assert pk, rel; k = pk.end(); write(work, rel, t[:k] + "\n\n" + line + t[k:], eol)
def insert_before_class_end(work, rel, block):
    t, eol = read(work, rel); k = t.rstrip().rfind("}"); write(work, rel, t[:k].rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n}\n", eol)
def apply_patch(work, patch): sh(["git", "apply", patch], work)
def new_file(work, rel, text): write(work, rel, text); sh(["git", "add", "-N", rel], work)
def diff_to(work, out_patch, paths):
    p = subprocess.run(["git", "diff", "--binary", "--"] + paths, cwd=work, capture_output=True, env=ENV); open(out_patch, "wb").write(p.stdout); return len(p.stdout)
def method_span(work, rel, name, decl_substring=None):
    """(javadoc_start_line0, end_line0_exclusive) of the method `name` (optionally disambiguated by a declaration substring)."""
    t, _ = read(work, rel); lines = t.split("\n")
    ms = [m for m in extract_methods_from_file(os.path.join(work, rel)) if m["name"] == name]
    if decl_substring: ms = [m for m in ms if decl_substring in lines[m["start_line"] - 1]]
    assert len(ms) == 1, (rel, name, decl_substring, len(ms)); m = ms[0]
    s = m["start_line"] - 1
    while s > 0 and (lines[s - 1].strip().startswith(("*", "/**", "*/", "@")) or lines[s - 1].strip() == ""):
        if lines[s - 1].strip() == "" and not (s >= 2 and lines[s - 2].strip().startswith(("*", "/**"))): break
        s -= 1
    return s, m["end_line"]
def replace_method(work, rel, name, new_text, decl_substring=None):
    """Replace the whole method (javadoc + body) with new_text (indented, no trailing blank line)."""
    s, e = method_span(work, rel, name, decl_substring); t, eol = read(work, rel); lines = t.split("\n")
    write(work, rel, "\n".join(lines[:s] + new_text.rstrip("\n").split("\n") + lines[e:]), eol)
def method_text(work, rel, name, decl_substring=None):
    s, e = method_span(work, rel, name, decl_substring); t, _ = read(work, rel); return "\n".join(t.split("\n")[s:e])
def compile_(work):
    for d in ("target", "build", "build-tests"): shutil.rmtree(os.path.join(work, d), ignore_errors=True)
    o = sh(["defects4j", "compile"], work, check=False, timeout=1200); return ("BUILD FAILED" not in o and "error:" not in o), o
def trigger(work, tid):
    o = sh(["defects4j", "test", "-t", tid], work, check=False, timeout=900); m = re.search(r"Failing tests:\s*(\d+)", o)
    ft = open(os.path.join(work, "failing_tests")).read() if os.path.exists(os.path.join(work, "failing_tests")) else ""
    return (int(m.group(1)) if m else None), ft.strip()
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

def emit_pair(work, spec, build_arm, prod_files, test_files):
    """Standard emitter. build_arm(work, arm_name) must leave the checkout in the buggy state of that arm (production + tests
    applied). Writes <pair_dir>/<ARM>/variant.patch and test.patch, then pair.json. Verifies both arms share one test.patch."""
    pair_dir = spec["pair_dir"]; os.makedirs(pair_dir, exist_ok=True); hashes = {}
    for arm in ("DEFINER_FAULT", "ADAPTER_FAULT", "CORRECT"):        # CORRECT = the same chain with H2 and H3 both right (reference version)
        reset(work); build_arm(work, arm); d = f"{pair_dir}/{arm}"; os.makedirs(d, exist_ok=True)
        diff_to(work, f"{d}/variant.patch", prod_files); diff_to(work, f"{d}/test.patch", test_files)
        hashes[arm] = {"variant.patch": sha(f"{d}/variant.patch"), "test.patch": sha(f"{d}/test.patch")}
        if arm == "CORRECT": spec["correct_dir"] = d
        else: spec["arms"][arm]["package_dir"] = d
    assert hashes["DEFINER_FAULT"]["test.patch"] == hashes["ADAPTER_FAULT"]["test.patch"] == hashes["CORRECT"]["test.patch"], "all configurations must share one test.patch"
    reset(work); spec["package_hashes"] = hashes
    json.dump(spec, open(f"{pair_dir}/pair.json", "w"), indent=1); print("emitted", spec["pair_id"], {a: os.path.getsize(f"{pair_dir}/{a}/variant.patch") for a in hashes})
    return f"{pair_dir}/pair.json"
