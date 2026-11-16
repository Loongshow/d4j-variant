#!/usr/bin/env python
"""A8 camouflage audit: prove that the two arms of each pair differ only in the gold's host, and
check the nine unintended-difference channels. Usage: camouflage_audit.py <spec.json> <out.json>"""
import json, os, re, sys, hashlib, difflib

spec = json.load(open(sys.argv[1])); out_path = sys.argv[2]
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1"
A = f"{R}/experiment-a-camouflage"; sname = os.path.basename(sys.argv[1])[:-5]
cfgs = {a: json.load(open(f"{A}/construction/configs/{sname}/pair_config_{a}.json")) for a in ("low", "high")}
VID = {a: cfgs[a]["treatment_id"] for a in cfgs}
H = lambda b: hashlib.sha256(b).hexdigest()


def added_by_file(patch_text):
    d = {}
    for chunk in patch_text.split("diff --git ")[1:]:
        f = chunk.splitlines()[0].split(" b/")[-1]
        adds = [l[1:] for l in chunk.split("\n") if l.startswith("+") and not l.startswith("+++")]
        dels = [l[1:] for l in chunk.split("\n") if l.startswith("-") and not l.startswith("---")]
        d[f] = {"added": adds, "removed": dels}
    return d


P = {a: added_by_file(open(f"{A}/construction/packages/{VID[a]}/variant.patch").read()) for a in cfgs}
res = {"pair": spec["pair"], "low": VID["low"], "high": VID["high"], "checks": {}}

# ---- 1. test.patch byte identity
tp = {a: open(f"{A}/construction/packages/{VID[a]}/test.patch", "rb").read() for a in cfgs}
res["checks"]["test_patch_byte_identical"] = {
    "pass": tp["low"] == tp["high"], "sha256": H(tp["low"])}

# ---- 2. which files each arm touches, and the per-file added-line comparison
gold_files = {a: spec["arms"][a]["gold_host_file"] for a in cfgs}
shared = sorted(set(P["low"]) & set(P["high"]))
only = {a: sorted(set(P[a]) - set(P["low" if a == "high" else "high"])) for a in cfgs}
per_file = {}
for f in shared:
    la, ha = P["low"][f]["added"], P["high"][f]["added"]
    sm = [l for l in difflib.unified_diff(la, ha, lineterm="", n=0)][2:]
    per_file[f] = {"identical": la == ha, "added_lines_low": len(la), "added_lines_high": len(ha),
                   "diff": sm[:20]}
res["checks"]["shared_files_touched"] = shared
res["checks"]["files_only_in_one_arm"] = only
res["checks"]["per_shared_file_added_lines"] = per_file
non_identical = [f for f, v in per_file.items() if not v["identical"]]
res["checks"]["shared_files_that_differ"] = non_identical
res["checks"]["only_hop4_differs_among_shared_files"] = {
    "pass": non_identical == [spec["hop4_file"]] or non_identical == [],
    "differing": non_identical, "hop4_file": spec["hop4_file"]}

# ---- 3. the gold method text is byte-identical in both arms
def gold_block(adds, decl):
    i = next((k for k, l in enumerate(adds) if decl in l), None)
    if i is None:
        return None
    start = i
    while start > 0 and (adds[start - 1].strip().startswith(("*", "/**", "//")) or adds[start - 1].strip() == ""):
        start -= 1
    end = i
    depth = 0; seen = False
    for k in range(i, len(adds)):
        depth += adds[k].count("{") - adds[k].count("}")
        seen = seen or "{" in adds[k]
        end = k
        if seen and depth == 0:
            break
    return "\n".join(adds[start:end + 1]).strip()


decl = spec["gold_decl_historical"].replace(spec["gold_method_historical"] + "(", spec["gold_method"] + "(")
gb = {a: gold_block(P[a][gold_files[a]]["added"], decl) for a in cfgs}
res["checks"]["gold_method_text_identical"] = {
    "pass": gb["low"] is not None and gb["low"] == gb["high"],
    "sha256": H((gb["low"] or "").encode()), "lines": len((gb["low"] or "").split("\n")),
    "text": gb["low"]}

# ---- 4. rendered payload (what the agent is shown) byte identity
pay = {}
for a in cfgs:
    p = f"{A}/leakage/rendered_payload_{VID[a]}.txt"
    pay[a] = open(p, "rb").read() if os.path.exists(p) else b""
res["checks"]["rendered_payload_byte_identical"] = {
    "pass": pay["low"] == pay["high"] and pay["low"] != b"", "sha256": H(pay["low"]),
    "bytes": len(pay["low"])}

# ---- 5. lexgate parity
lex = {a: json.load(open(f"{A}/leakage/lexgate_{VID[a]}.json")) for a in cfgs}
res["checks"]["lexgate"] = {a: {"verdict": lex[a]["verdict"], "name_exposure": lex[a]["name_exposure"]} for a in cfgs}
res["checks"]["lexgate_parity"] = {
    "pass": lex["low"]["verdict"] == lex["high"]["verdict"] == "DECOUPLED"
            and lex["low"]["name_exposure"] == lex["high"]["name_exposure"]}

# ---- 6. fault-vocabulary presence in each host file (semantic class name / gold-only vocabulary)
vocab = spec["fault_vocabulary"]
hostsrc = {}
for a in cfgs:
    co = f"{A}/repro/{VID[a]}-checkout"
    hostsrc[a] = open(os.path.join(co, gold_files[a]), "rb").read().decode("utf-8", "replace")
res["checks"]["fault_vocabulary_in_host"] = {
    a: {w: len(re.findall(w, hostsrc[a], re.I)) for w in vocab} for a in cfgs}
res["checks"]["host_class_name_contains_fault_vocabulary"] = {
    a: [w for w in vocab if re.search(w, spec["arms"][a]["gold_host_class"], re.I)] for a in cfgs}

# ---- 7. hop 4 file: how often the gold host class is named there, pristine vs patched
h4 = spec["hop4_file"]
res["checks"]["gold_host_mentions_in_hop4_file"] = {}
for a in cfgs:
    co = f"{A}/repro/{VID[a]}-checkout"
    t = open(os.path.join(co, h4), "rb").read().decode("utf-8", "replace")
    simple = spec["arms"][a]["gold_host_class"].split(".")[-1]
    res["checks"]["gold_host_mentions_in_hop4_file"][a] = {
        "patched_total": len(re.findall(r"\b%s\b" % simple, t)),
        "added_import": len(spec["arms"][a].get("hop4_add_imports", []))}

# ---- 8. formatting sanity: indentation and line length of the inserted gold, both arms
def fmt(text):
    ls = [l for l in text.split("\n") if l.strip()]
    return {"min_indent": min(len(l) - len(l.lstrip()) for l in ls),
            "max_line_length": max(len(l) for l in ls),
            "tabs": sum(l.count("\t") for l in ls),
            "trailing_whitespace_lines": sum(1 for l in ls if l != l.rstrip())}
res["checks"]["inserted_gold_formatting"] = {a: fmt(gb[a]) for a in cfgs}

# ---- 9. insertion location, from the build reports
res["checks"]["insertion"] = {}
for a in cfgs:
    br = json.load(open(f"{A}/construction/build/{sname}/{a}/build_report.json"))
    res["checks"]["insertion"][a] = {"after_method": br.get("insert_after_method"),
                                     "anchor_rule": br.get("anchor_rule"),
                                     "gold_start_line": br.get("gold_start_line_in_host")}
verdicts = [res["checks"]["test_patch_byte_identical"]["pass"],
            res["checks"]["only_hop4_differs_among_shared_files"]["pass"],
            res["checks"]["gold_method_text_identical"]["pass"],
            res["checks"]["rendered_payload_byte_identical"]["pass"],
            res["checks"]["lexgate_parity"]["pass"]]
res["overall"] = "pass" if all(verdicts) else "REVIEW"
json.dump(res, open(out_path, "w"), indent=1)
print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != "text"})
                  for k, v in res["checks"].items()}, indent=1)[:2500])
print("OVERALL", res["overall"])
