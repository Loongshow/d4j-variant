"""cue-trust-v3 construction helpers (deterministic; no LLM). Reuses the asserted-edit helpers of OCFLB
(ocflb-level-b-v1/scripts/ocflb_lib.py, read-only import) and adds scoped identifier renames and anchored
comment insertion. Every edit is asserted: an anchor or rename target that is missing or ambiguous aborts."""
import os, re, sys, json, subprocess
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1/scripts")
import ocflb_lib as L  # noqa: E402

V3 = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/mechanism-search-v1"
ENV = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
LEVELS = ["C0", "CG1", "CG2", "CD1", "CD2"]

def sh(cmd, cwd, timeout=1800):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=ENV, timeout=timeout)
    return p.returncode, p.stdout + p.stderr

_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_$][A-Za-z0-9_$]*')

def _rename_text(text, mapping):
    """Simultaneous whole-identifier rename that skips string and char literals."""
    return _TOKEN.sub(lambda m: m.group(0) if m.group(0)[0] in "\"'" else mapping.get(m.group(0), m.group(0)), text)

def rename_in_method(work, rel, method, mapping, decl=None):
    """Rename local variables / parameters inside one method (javadoc included in the span)."""
    s, e = L.method_span(work, rel, method, decl); t, eol = L.read(work, rel); lines = t.split("\n")
    body = "\n".join(lines[s:e])
    for k in mapping: assert re.search(r"\b%s\b" % re.escape(k), body), (rel, method, "rename source absent", k)
    L.write(work, rel, "\n".join(lines[:s] + _rename_text(body, mapping).split("\n") + lines[e:]), eol)

def rename_fields(work, rel, mapping):
    """Rename private instance fields consistently: `this.f`, `that.f` and the declaration."""
    t, eol = L.read(work, rel); names = "|".join(re.escape(k) for k in mapping)
    decl = r"^(\s*private\s+(?:transient\s+)?(?:final\s+)?[\w.<>\[\]]+\s+)(%s)(\s*;)" % names
    assert len(re.findall(decl, t, re.M)) == len(mapping), (rel, "field declarations mismatch")
    t = re.sub(r"(\b(?:this|that)\.)(%s)\b" % names, lambda m: m.group(1) + mapping[m.group(2)], t)
    t = re.sub(decl, lambda m: m.group(1) + mapping[m.group(2)] + m.group(3), t, flags=re.M)
    L.write(work, rel, t, eol)

def insert_comment(work, rel, anchor, comment, where="after"):
    """Insert one comment line after/before a unique anchor line; indentation copied from the neighbouring line."""
    t, eol = L.read(work, rel); assert t.count(anchor) == 1, (rel, anchor[:60], t.count(anchor))
    k = t.index(anchor)
    if where == "after":
        pos = t.index("\n", k + len(anchor) - (1 if anchor.endswith("\n") else 0)) + 1
        nxt = t[pos:].split("\n", 1)[0]; indent = re.match(r"[ \t]*", nxt).group(0)
        t = t[:pos] + indent + comment + "\n" + t[pos:]
    else:
        ls = t.rfind("\n", 0, k) + 1; indent = re.match(r"[ \t]*", t[ls:]).group(0)
        t = t[:ls] + indent + comment + "\n" + t[ls:]
    L.write(work, rel, t, eol)

def apply_level(work, spec, level, with_fault=True):
    G = spec["gold"]; lv = spec["levels"][level]; ca = spec["comment_anchor"]
    if with_fault: L.replace_once(work, G["file"], G["orig"], G["bug"])
    insert_comment(work, ca["file"], ca["anchor_fault"] if with_fault else ca["anchor_correct"], lv["comment"], ca.get("where", "after"))
    for r in lv.get("renames", []):
        if r["scope"] == "fields": rename_fields(work, r["file"], r["map"])
        else: rename_in_method(work, r["file"], r["method"], r["map"], r.get("decl"))
    T = spec["trigger"]
    for imp in T.get("imports", []): L.add_import(work, T["test_file"], imp)
    L.insert_before_class_end(work, T["test_file"], T["code"])

def build(spec):
    work = spec["work"]; out = f"{V3}/instances/{spec['instance_id']}/build"; os.makedirs(out, exist_ok=True); hashes = {}
    for level in LEVELS + ["CORRECT"]:
        L.reset(work); apply_level(work, spec, "C0" if level == "CORRECT" else level, with_fault=(level != "CORRECT"))
        d = f"{out}/{level}"; os.makedirs(d, exist_ok=True)
        L.diff_to(work, f"{d}/variant.patch", spec["prod_files"]); L.diff_to(work, f"{d}/test.patch", spec["test_files"])
        hashes[level] = {"variant.patch": L.sha(f"{d}/variant.patch"), "test.patch": L.sha(f"{d}/test.patch")}
    L.reset(work)
    assert len({h["test.patch"] for h in hashes.values()}) == 1, "all configurations must share one test.patch"
    assert len({hashes[l]["variant.patch"] for l in LEVELS}) == len(LEVELS), "cue levels must differ"
    json.dump(hashes, open(f"{out}/hashes.json", "w"), indent=1)
    return out, hashes

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); o, h = build(spec)
    print("built", spec["instance_id"], "->", o)
    for k, v in h.items(): print(f"  {k:8s} variant {v['variant.patch'][:12]}  test {v['test.patch'][:12]}")
