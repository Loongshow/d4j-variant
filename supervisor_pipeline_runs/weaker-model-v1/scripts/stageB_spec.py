"""Stage B spec generator. Usage: stageB_spec.py <design.py> <cell> [--check]
Builds one cell (C00 1-hop plain, C01 1-hop odd sibling, C10 5-hop + lie, C11 5-hop + lie + odd hop) on a scratch copy of the
fixture with the recipe functions (stageB_lib), derives unique old/new context edits from the result (verified to reproduce
the recipe output byte for byte), and writes construction/stageB/specs/<iid>.json for stageB_validate.py.
--check additionally applies the fault on the scratch copy, compiles, runs the trigger and prints the failure signature."""
import os, sys, json, difflib, shutil, importlib.util, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stageB_lib as L

SEED = json.load(open(os.path.join(L.ROOT, "construction/stageB/designs/host_draws.json")))["seed"]
CELLS = {"C00": dict(hops=1, odd=False, lie=False), "C01": dict(hops=1, odd=True, lie=False),
         "C10": dict(hops=5, odd=False, lie=True), "C11": dict(hops=5, odd=True, lie=True)}

def load_design(path):
    spec = importlib.util.spec_from_file_location("design", path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.DESIGN

def indent4(text):
    return "\n".join(("    " + l if l.strip() else l) for l in text.strip("\n").split("\n"))

def insert_after_method(path, method, near_line, block):
    """Insert `block` (column-0 method text) directly after the method's closing brace, separated by one blank line."""
    text, crlf = L.validate.read_text_smart(path)
    span = L.extract_transform.find_method_span(text, method, near_line=near_line); assert span, method
    end = span[1]
    text = text[:end] + "\n\n" + indent4(block) + text[end:]
    L.validate.write_text_smart(path, text, crlf)

def ensure_imports(path, imports):
    """Add missing import lines after the last existing import (ocflb_lib.add_import semantics)."""
    t = L.rd(path); added = []
    for imp in imports:
        line = f"import {imp};"
        if line in t: continue
        import re
        ms = list(re.finditer(r"^import .*;$", t, re.M)); assert ms, path
        k = ms[-1].end(); t = t[:k] + "\n" + line + t[k:]; added.append(line)
    if added: L.wr(path, t)
    return added

def derive_edits(orig, new):
    """Minimal contiguous old/new blocks (line granularity), each `old` expanded until unique in `orig`."""
    a, b = orig.split("\n"), new.split("\n"); sm = difflib.SequenceMatcher(None, a, b, autojunk=False); edits = []
    blocks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        if blocks and i1 - blocks[-1][1] <= 12:           # merge blocks separated by a few unchanged lines into one edit
            blocks[-1] = (blocks[-1][0], i2, blocks[-1][2], j2)
        else:
            blocks.append((i1, i2, j1, j2))
    for i1, i2, j1, j2 in blocks:
        lo, hi, nlo, nhi = i1, i2, j1, j2
        while True:
            old = "\n".join(a[lo:hi]); 
            if old and orig.count(old) == 1: break
            if lo > 0: lo -= 1; nlo -= 1
            if hi < len(a): hi += 1; nhi += 1
            if lo == 0 and hi == len(a): break
        edits.append({"old": "\n".join(a[lo:hi]), "new": "\n".join(b[nlo:nhi])})
    # verify sequential application reproduces `new`
    t = orig
    for e in edits:
        assert t.count(e["old"]) == 1, ("edit not unique after earlier edits", e["old"][:80]); t = t.replace(e["old"], e["new"], 1)
    assert t == new, "edits do not reproduce the recipe output"
    return edits

def main():
    dpath, cell = sys.argv[1], sys.argv[2]; check = "--check" in sys.argv
    D = load_design(dpath); C = CELLS[cell]; P = D["project"]
    iid = f"SB-{D['bug']}-{cell}"
    W = f"/private/tmp/d4j-stageB-{D['bug']}-{cell}"; shutil.rmtree(W, ignore_errors=True); L.prepare_work(P, W)
    F = D["facade"]; fac = os.path.join(W, F["file"]); touched = {F["file"]}; audit = {"cell": cell, **C, "seed": SEED, "hops": []}
    gold_file = F["file"]
    geometry = "one_hop" if C["hops"] == 1 else "chain"
    for e in D.get("pre_edits", {}).get("all", []) + D.get("pre_edits", {}).get(geometry, []):   # edits shared by the cells of a geometry
        L.edit(os.path.join(W, e["file"]), e["old"], e["new"]); touched.add(e["file"])
    if C["hops"] == 1:
        oh = D["one_hop"]
        L.edit(fac, oh["facade_old"], oh["facade_new"])
        sib = oh["sibling"]["odd" if C["odd"] else "plain"]
        insert_after_method(fac, oh.get("insert_after_method", F["method"]), oh.get("insert_after_line", F.get("near_line")), D["gold"]["text"])   # gold first, directly below the facade
        insert_after_method(fac, D["gold"]["method"], None, sib)                               # then the sibling below the gold
        decoys = [{"class": F["class"], "method": oh["sibling"]["method"], "file": F["file"]}]
    else:
        ch = D["chain"]; inserted = []
        for i, hop in enumerate(ch["hops"]):
            host = os.path.join(W, hop["file"]); touched.add(hop["file"])
            text = D["gold"]["text"] if hop.get("gold") else (hop["odd"] if (C["odd"] and "odd" in hop) else hop.get("plain", hop.get("text")))
            assert text, hop["method"]
            added = ensure_imports(host, hop.get("imports", []))
            a = L.insert_hop(host, text, SEED + 100 + i, exclude_names=inserted); inserted.append(hop["method"])
            audit["hops"].append({"hop": i + 1, "class": hop["class"], "method": hop["method"], "file": hop["file"], "anchor_after": a["anchor_after_method"],
                                  "anchor_seed": a["seed_used"], "imports_added": added, "role": "gold" if hop.get("gold") else ("odd" if (C["odd"] and "odd" in hop) else "plain")})
            if hop.get("gold"): gold_file = hop["file"]; gold_class = hop["class"]
        L.replace_method_body(fac, F["method"], ch["facade_body"], near_line=F.get("near_line"), lie_sentence=ch["lie"] if C["lie"] else None)
        decoys = [{"class": h["class"], "method": h["method"], "file": h["file"]} for h in ch["hops"] if not h.get("gold")]
    # derive edits per touched file against the fixture
    context_edits = []
    for rel in sorted(touched):
        orig = L.rd(os.path.join(L.FIXTURES[P], rel)); new = L.rd(os.path.join(W, rel))
        if orig == new: continue
        for e in derive_edits(orig, new): context_edits.append({"file": rel, "old": e["old"], "new": e["new"], "purpose": f"{iid} construction (recipe transform)"})
    gf = D["gold"]["fault"]; gold_abs = os.path.join(W, gold_file); assert L.rd(gold_abs).count(gf["old"]) == 1, "fault old text not unique in gold file"
    gold_class = F["class"] if C["hops"] == 1 else gold_class
    spec = {"iid": iid, "project": P, "group": f"SB-{D['bug']}", "mechanism": "STAGE_B_2x2", "tier": "STAGE_B",
            "tags": [cell, f"hops={C['hops']}", f"odd={int(C['odd'])}", f"lie={int(C['lie'])}", D["bug"]],
            "src_root": D["src_root"], "test_root": D["test_root"], "hops": C["hops"],
            "gold": {"class": gold_class, "method": D["gold"]["method"], "file": gold_file, "edits": [gf]},
            "context_edits": context_edits, "decoys": decoys, "entry_points": [f"{F['class']}::{F['method']}"],
            "evidence": D["evidence"], "ownership_reason": D["ownership_reason"], "ownership_tests": D["ownership_tests"],
            "trigger": D["trigger"], "extra_tests": [], "expected_signature": D["expected_signature"],
            "compensating": [{k: v for k, v in e.items() if k != "cells"} for e in D["compensating"]["chain" if C["hops"] == 5 else "one_hop"] if cell in e.get("cells", [cell])],
            "stage_b": audit, "design_file": os.path.relpath(dpath, L.ROOT)}
    out = os.path.join(L.ROOT, "construction/stageB/specs", f"{iid}.json"); L.save_json(out, spec)
    print(f"{iid}: {len(context_edits)} context edits over {len(touched)} files; gold {gold_class}::{D['gold']['method']} in {gold_file}; decoys {[d['method'] for d in decoys]}")
    if check:
        L.apply_fault(gold_abs, gf["old"], gf["new"]); t0 = time.time(); ok, log = L.compile_ok(W); print("  compile", ok, f"{time.time()-t0:.0f}s", "" if ok else log[-1500:])
        if ok:
            tid = f"{D['trigger']['test_class']}::{D['trigger']['test_method']}"; n, ids, det = L.test_one(W, tid)
            print("  trigger failing:", n, "| signature:", " | ".join(det.splitlines()[:2]))
            print("  expected signature present:", D["expected_signature"] in det)
    shutil.rmtree(W, ignore_errors=True)

if __name__ == "__main__":
    main()
