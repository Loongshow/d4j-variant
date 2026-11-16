#!/usr/bin/env python
"""Camouflage host metrics for Experiment A (see review/CAMOUFLAGE_METRICS.md).

Usage:
  host_metrics.py <java-file> [--gold-method NAME] [--gold-line N] [--repo-root DIR]
                  [--facade-package PKG] [--json OUT]

Method extraction uses the LABELLED SHIM `supervisor_pipeline_runs/shim/callgraph.py`
(`extract_methods_from_file`), i.e. the same extractor the supervisor pipeline is
exercised with here; it is a stand-in for the supervisor's real
trajectory-analysis/callgraph.py, which was not supplied.

All metric definitions are pre-registered here and applied identically to LOW and
HIGH hosts. No metric consults the run results.
"""
import argparse, difflib, json, os, re, sys

sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/shim")
from callgraph import extract_methods_from_file  # labelled shim

ARITH = re.compile(r"[+\-*/%]|<<|>>|>>>|&|\||\^|==|!=|<=|>=|<(?![\w])|>(?![\w])")
MODS = ("public", "protected", "private")


def code_loc(lines):
    n, in_block = 0, False
    for raw in lines:
        s = raw.strip()
        if in_block:
            if "*/" in s:
                in_block = False
            continue
        if s.startswith("/*"):
            if "*/" not in s:
                in_block = True
            continue
        if not s or s.startswith("//") or s.startswith("*"):
            continue
        n += 1
    return n


def split_camel(name):
    return [t.lower() for t in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", name)]


def header_of(m, lines):
    return lines[m["start_line"] - 1] if 0 < m["start_line"] <= len(lines) else ""


def visibility(hdr):
    for v in MODS:
        if re.search(r"\b%s\b" % v, hdr):
            return v
    return "package_private"


def ret_and_params(hdr):
    mm = re.search(r"([\w.$<>\[\],?]+)\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)", hdr)
    if not mm:
        return None, None, None
    ret, name, params = mm.group(1), mm.group(2), mm.group(3).strip()
    types = []
    if params:
        for p in params.split(","):
            toks = p.strip().split()
            if toks:
                types.append(toks[-2] if len(toks) >= 2 else toks[0])
    return ret, name, types


def analyse(path, gold_method=None, gold_line=None, repo_root=None, facade_package=None):
    raw = open(path, "rb").read().decode("utf-8", "replace")
    lines = raw.replace("\r\n", "\n").split("\n")
    methods = extract_methods_from_file(path)
    total = len(lines)
    out = {
        "file": path,
        "file_loc_total": total,
        "file_loc_code": code_loc(lines),
        "file_bytes": len(raw),
        "declared_methods": len(methods),
        "methods_by_visibility": {},
        "static_methods": 0,
    }
    vis = {"public": 0, "protected": 0, "private": 0, "package_private": 0}
    infos = []
    for m in methods:
        hdr = header_of(m, lines)
        v = visibility(hdr)
        vis[v] += 1
        ret, nm, types = ret_and_params(hdr)
        st = bool(re.search(r"\bstatic\b", hdr))
        out["static_methods"] += 1 if st else 0
        infos.append({"name": m["name"], "start": m["start_line"], "end": m["end_line"],
                      "visibility": v, "static": st, "ret": ret, "param_types": types,
                      "arith": bool(ARITH.search(m.get("body", "")))})
    out["methods_by_visibility"] = vis
    out["package"] = None
    pm = re.search(r"^\s*package\s+([\w.]+)\s*;", raw, re.MULTILINE)
    if pm:
        out["package"] = pm.group(1)

    gold = None
    if gold_method:
        cands = [i for i in infos if i["name"] == gold_method]
        if gold_line:
            cands = sorted(cands, key=lambda i: abs(i["start"] - gold_line))
        gold = cands[0] if cands else None
    elif gold_line:
        gold = next((i for i in infos if i["start"] <= gold_line <= i["end"]), None)

    if gold:
        g = gold
        out["gold"] = {"name": g["name"], "start_line": g["start"], "end_line": g["end"],
                       "visibility": g["visibility"], "static": g["static"],
                       "return_type": g["ret"], "param_types": g["param_types"]}
        win = [i for i in infos if i is not g and abs(i["start"] - g["start"]) <= 100]
        out["methods_within_100_lines"] = len(win)
        out["gold_percentile_in_file"] = round(100.0 * g["start"] / max(1, total), 2)
        out["lines_before_gold"] = g["start"] - 1
        out["lines_after_gold"] = total - g["end"]
        others = [i for i in infos if i is not g]
        sims = [difflib.SequenceMatcher(None, g["name"].lower(), i["name"].lower()).ratio() for i in others]
        wsims = [difflib.SequenceMatcher(None, g["name"].lower(), i["name"].lower()).ratio() for i in win]
        gtok = set(split_camel(g["name"]))
        tok_shared = sum(1 for i in others if gtok & set(split_camel(i["name"])))
        out["name_similarity"] = {
            "max_ratio_file": round(max(sims), 3) if sims else None,
            "mean_ratio_file": round(sum(sims) / len(sims), 3) if sims else None,
            "max_ratio_window100": round(max(wsims), 3) if wsims else None,
            "mean_ratio_window100": round(sum(wsims) / len(wsims), 3) if wsims else None,
            "methods_sharing_a_camel_token": tok_shared,
        }
        out["return_type_frequency_in_host"] = sum(1 for i in others if i["ret"] == g["ret"])
        out["param_signature_frequency_in_host"] = sum(
            1 for i in others if i["param_types"] == g["param_types"])
        out["same_arity_in_host"] = sum(
            1 for i in others if i["param_types"] is not None and g["param_types"] is not None
            and len(i["param_types"]) == len(g["param_types"]))
        # PRE-REGISTERED same-file candidate definitions, from strictest to broadest. All four
        # are reported for both arms; C3 (any arithmetic-bearing method) is the primary
        # "how many methods in this file could plausibly hold arithmetic" measure.
        NUM = {"int", "long", "double", "float", "short", "byte", "char"}
        c1 = [i for i in others if i["ret"] == g["ret"] and i["static"] == g["static"]
              and i["param_types"] is not None and g["param_types"] is not None
              and len(i["param_types"]) == len(g["param_types"]) and i["arith"]]
        c2 = [i for i in others if i["ret"] == g["ret"] and i["arith"]]
        c3 = [i for i in others if i["ret"] in NUM and i["arith"]]
        c4 = [i for i in others if i["arith"]]
        out["candidates"] = {
            "C1_same_type_arity_static_arith": len(c1),
            "C2_same_return_type_arith": len(c2),
            "C3_numeric_return_arith": len(c3),
            "C4_any_arith": len(c4),
            "C1_names": sorted(i["name"] for i in c1)[:40],
            "C3_names": sorted(i["name"] for i in c3)[:40],
        }
        out["plausible_same_file_candidates"] = len(c3)
        out["same_file_candidate_density_per_1k_loc"] = round(1000.0 * len(c3) / max(1, total), 3)
        out["candidate_density_per_1k_loc"] = {
            k: round(1000.0 * v / max(1, total), 3)
            for k, v in (("C1", len(c1)), ("C2", len(c2)), ("C3", len(c3)), ("C4", len(c4)))}
        for w in (50, 100, 200):
            out[f"methods_within_{w}_lines"] = sum(1 for i in others if abs(i["start"] - g["start"]) <= w)
            out[f"arith_methods_within_{w}_lines"] = sum(
                1 for i in others if i["arith"] and abs(i["start"] - g["start"]) <= w)
        if facade_package and out["package"]:
            a, b = facade_package.split("."), out["package"].split(".")
            shared = 0
            for x, y in zip(a, b):
                if x != y:
                    break
                shared += 1
            out["package_relatedness_to_facade"] = {
                "facade_package": facade_package, "host_package": out["package"],
                "same_package": facade_package == out["package"],
                "shared_prefix_segments": shared,
                "jaccard_segments": round(len(set(a) & set(b)) / len(set(a) | set(b)), 3),
            }
        if repo_root and g["ret"]:
            pat = r"%s\s+\w+\s*\(" % re.escape(g["ret"])
            n = 0
            for dp, _dn, fn in os.walk(repo_root):
                for f in fn:
                    if f.endswith(".java"):
                        try:
                            t = open(os.path.join(dp, f), "rb").read().decode("utf-8", "replace")
                        except Exception:
                            continue
                        n += len(re.findall(pat, t))
            out["repo_wide_same_return_type_signature_matches"] = n
    out["methods"] = [{"name": i["name"], "start": i["start"], "visibility": i["visibility"],
                       "static": i["static"], "ret": i["ret"]} for i in infos]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("java_file")
    ap.add_argument("--gold-method")
    ap.add_argument("--gold-line", type=int)
    ap.add_argument("--repo-root")
    ap.add_argument("--facade-package")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = analyse(a.java_file, a.gold_method, a.gold_line, a.repo_root, a.facade_package)
    if a.json:
        os.makedirs(os.path.dirname(a.json), exist_ok=True)
        json.dump(res, open(a.json, "w"), indent=1)
    slim = {k: v for k, v in res.items() if k != "methods"}
    print(json.dumps(slim, indent=1))


if __name__ == "__main__":
    main()
