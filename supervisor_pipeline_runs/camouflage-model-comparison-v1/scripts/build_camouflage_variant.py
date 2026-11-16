#!/usr/bin/env python
"""Build one arm (LOW or HIGH camouflage) of a camouflage matched pair.

Provenance: the facade edit and chain hops 1-4 are taken BYTE-IDENTICALLY from the
already-validated historical five-hop variant.patch of the same semantic bug. The only
changes this script makes are:
  (1) the inserted GOLD method text is moved out of the historical gold host and into
      the arm's gold host (byte-identical method text, same name, same body);
  (2) hop 4's call line is re-pointed at the arm's gold host class;
  (3) the import that hop 4 needed for the historical gold class is dropped, and an
      import for the arm's gold host is added when (and only when) hop 4's package
      differs from the arm's gold host package.
Everything else - trigger, test.patch, facade, hops 1-4, gold body, failure - is identical
across the two arms by construction.

Usage: build_camouflage_variant.py <spec.json> <low|high> <work-checkout> <out-dir>
Writes <out-dir>/variant.patch, <out-dir>/build_report.json and a copy of the patched
gold host file for the camouflage metrics. Leaves the checkout clean.
"""
import json, os, re, subprocess, sys

spec, arm, work, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/shim")
from callgraph import extract_methods_from_file

A = spec["arms"][arm]
HIST = spec["historical_patch"]
GOLD_FILE_HIST = spec["historical_gold_file"]
GOLD_DECL = spec["gold_decl_historical"]
GOLD_NAME_HIST = spec["gold_method_historical"]
GOLD_NAME = spec["gold_method"]
HOST_FILE = A["gold_host_file"]
HOST_CLASS = A["gold_host_class"]
rep = {"arm": arm, "variant_id": A["variant_id"], "spec": sys.argv[1], "steps": []}


def sh(cmd, cwd=work, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if check and p.returncode != 0:
        raise SystemExit(f"FAILED {' '.join(cmd)}\n{p.stdout}\n{p.stderr}")
    return p.returncode, p.stdout + p.stderr


def step(name, detail=""):
    rep["steps"].append({"step": name, "detail": str(detail)[:400]})
    print(name, detail, flush=True)


def read(rel):
    raw = open(os.path.join(work, rel), "rb").read().decode("utf-8")
    return raw, ("\r\n" if "\r\n" in raw else "\n")


def write(rel, text, eol):
    open(os.path.join(work, rel), "wb").write(text.replace("\n", eol).encode("utf-8"))


def depth_before(text, idx):
    """Brace depth at character idx, ignoring strings, chars and comments."""
    d, i, state = 0, 0, None
    while i < idx:
        c = text[i]
        if state is None:
            if c == '"':
                state = "str"
            elif c == "'":
                state = "chr"
            elif c == "/" and text[i:i + 2] == "//":
                state = "line"; i += 1
            elif c == "/" and text[i:i + 2] == "/*":
                state = "block"; i += 1
            elif c == "{":
                d += 1
            elif c == "}":
                d -= 1
        elif state == "str":
            if c == "\\":
                i += 1
            elif c == '"':
                state = None
        elif state == "chr":
            if c == "\\":
                i += 1
            elif c == "'":
                state = None
        elif state == "line":
            if c == "\n":
                state = None
        elif state == "block":
            if text[i:i + 2] == "*/":
                state = None; i += 1
        i += 1
    return d


# ---------------------------------------------------------------- 0. clean tree
sh(["git", "reset", "-q", "--", "."]); sh(["git", "checkout", "--", "."])
rc, o = sh(["git", "status", "--short"])
dirty = [l for l in o.splitlines() if not l.startswith("??")]
assert not dirty, dirty
rc, head = sh(["git", "rev-parse", "HEAD"])
rep["checkout_head"] = head.strip()
step("clean tree", rep["checkout_head"])

# --------------------------------------------- 1. apply the historical chain patch
sh(["git", "apply", HIST])
step("applied historical five-hop patch", os.path.basename(HIST))

# ------------------------------------- 2. recover the inserted gold method verbatim
patch = open(HIST, "rb").read().decode("utf-8")
sec = None
for chunk in patch.split("diff --git ")[1:]:
    if chunk.splitlines()[0].startswith("a/" + GOLD_FILE_HIST):
        sec = chunk
assert sec, GOLD_FILE_HIST
runs, cur = [], []
for line in sec.split("\n"):
    if line.startswith("+") and not line.startswith("+++"):
        cur.append(line[1:])
    else:
        if cur:
            runs.append(cur); cur = []
if cur:
    runs.append(cur)
blocks = [r for r in runs if any(GOLD_DECL in l for l in r)]
assert len(blocks) == 1, [len(b) for b in blocks]
block = blocks[0]
while block and not block[-1].strip():
    block.pop()
gold_text = "\n".join(block)
assert gold_text.count(GOLD_DECL) == 1
rep["gold_method_source_lines"] = len(block)
step("recovered gold method text from the historical patch", f"{len(block)} lines")

# --------------------------- 3. move the gold method to this arm's host (if needed)
if os.path.normpath(HOST_FILE) != os.path.normpath(GOLD_FILE_HIST) or spec.get("force_reposition"):
    src, eol = read(GOLD_FILE_HIST)
    t = src.replace("\r\n", "\n")
    assert t.count(gold_text) == 1, ("gold text not unique in historical host", t.count(gold_text))
    # remove the block together with exactly one adjoining blank line
    if ("\n\n" + gold_text + "\n") in t:
        t2 = t.replace("\n\n" + gold_text + "\n", "\n", 1)
    else:
        t2 = t.replace(gold_text + "\n", "", 1)
    assert GOLD_DECL not in t2
    write(GOLD_FILE_HIST, t2, eol)
    step("removed the gold method from the historical host", GOLD_FILE_HIST)

    host, heol = read(HOST_FILE)
    ht = host.replace("\r\n", "\n")
    assert not re.search(r"\b%s\s*\(" % re.escape(GOLD_NAME), ht), \
        f"{GOLD_NAME} already appears in {HOST_FILE}"
    hl = ht.split("\n")
    ms = extract_methods_from_file(os.path.join(work, HOST_FILE))
    offs, pos = [], 0
    for i, l in enumerate(hl):
        offs.append(pos); pos += len(l) + 1
    top = [m for m in ms if depth_before(ht, offs[m["start_line"] - 1]) == 1]
    assert len(top) >= 3, f"only {len(top)} top-level methods in {HOST_FILE}"
    # PRE-REGISTERED ANCHOR RULE, identical for LOW and HIGH: among the top-level methods
    # whose closing brace lies in the middle 35%-65% of the file, insert after the one with
    # the most method headers within +/-100 lines (densest legal neighbourhood); ties break
    # toward the file midpoint. Keeps the gold away from both file boundaries in both arms
    # and lets each host express its own local density.
    nl = len(hl)
    heads = [m["start_line"] for m in ms]
    dens = lambda line: sum(1 for h in heads if abs(h - line) <= 100)
    elig = [m for m in top if 0.35 * nl <= m["end_line"] <= 0.65 * nl] or top
    anchor = max(elig, key=lambda m: (dens(m["end_line"]), -abs(m["end_line"] - 0.5 * nl)))
    at = anchor["end_line"]                      # insert after this line (1-based)
    rep["anchor_rule"] = {"eligible_top_level_methods": len(elig), "top_level_methods": len(top),
                          "neighbour_headers_within_100": dens(at),
                          "file_lines_before_insert": nl}
    body = gold_text.replace(GOLD_NAME_HIST + "(", GOLD_NAME + "(") if GOLD_NAME != GOLD_NAME_HIST else gold_text
    for a_, b_ in spec.get("gold_text_replacements", []):
        assert body.count(a_) == 1, ("gold text replacement not unique", a_, body.count(a_))
        body = body.replace(a_, b_, 1)
    new = hl[:at] + [""] + body.split("\n") + hl[at:]
    write(HOST_FILE, "\n".join(new), heol)
    rep["insert_after_method"] = {"name": anchor["name"], "end_line": at}
    rep["gold_start_line_in_host"] = at + 2
    step("inserted the gold method into this arm's host",
         f"{HOST_FILE} after {anchor['name']} (line {at}) -> gold at ~{at + 2}")
else:
    ht, _ = read(HOST_FILE)
    rep["insert_after_method"] = "UNCHANGED: this arm's host is the historical gold host"
    m = re.search(r"^.*%s" % re.escape(GOLD_DECL), ht.replace("\r\n", "\n"), re.MULTILINE)
    rep["gold_start_line_in_host"] = ht.replace("\r\n", "\n")[:m.start()].count("\n") + 1
    step("gold stays in its historical host (no move)", HOST_FILE)

# ------------------------------------- 4. re-point hop 4's call at this arm's host
h4 = spec["hop4_file"]
src, eol = read(h4)
t = src.replace("\r\n", "\n")
old_call = spec["hop4_call_historical"]
new_call = A["hop4_call"]
if old_call != new_call:
    assert t.count(old_call) == 1, (h4, old_call, t.count(old_call))
    t = t.replace(old_call, new_call, 1)
    step("re-pointed hop 4's call", new_call.strip())
# imports: drop the historical gold-class import if this patch added one, add ours if needed
for line in spec.get("hop4_drop_imports", []):
    if line + "\n" in t:
        t = t.replace(line + "\n", "", 1)
        step("dropped historical gold-class import from hop 4", line)
for line in A.get("hop4_add_imports", []):
    if line not in t:
        imps = [m for m in re.finditer(r"^import .*;$", t, re.MULTILINE)]
        assert imps, h4
        k = imps[-1].end()
        t = t[:k] + "\n" + line + t[k:]
        step("added import to hop 4", line)
write(h4, t, eol)

# ------------------------------------------------------- 5. emit the variant patch
# NOTE: no `git add -N .` - this construction only edits files that are already tracked, and
# staging untracked files would sweep validation build artefacts into the patch.
p = subprocess.run(["git", "diff", "--binary"], cwd=work, capture_output=True, env=env)
open(os.path.join(out, "variant.patch"), "wb").write(p.stdout)
rep["variant_patch_bytes"] = len(p.stdout)
files = sorted(set(re.findall(r"^\+\+\+ b/(.*)$", p.stdout.decode("utf-8", "replace"), re.M)))
rep["patched_files"] = files
step("wrote variant.patch", f"{len(p.stdout)} bytes, {len(files)} files")

# keep the patched host for the camouflage metrics, then restore the checkout
open(os.path.join(out, "host_%s_%s" % (arm, os.path.basename(HOST_FILE))), "wb").write(
    open(os.path.join(work, HOST_FILE), "rb").read())
sh(["git", "reset", "-q", "--", "."]); sh(["git", "checkout", "--", "."])
rc, o = sh(["git", "status", "--short"])
rep["clean_after"] = not [l for l in o.splitlines() if not l.startswith("??")]
json.dump(rep, open(os.path.join(out, "build_report.json"), "w"), indent=1)
print("OK", A["variant_id"], rep["variant_patch_bytes"], "bytes; clean_after", rep["clean_after"])
