"""Static distance metrics for LOW vs HIGH (Phase 7). Usage: distance_ha.py <config.json> <low_checkout> <high_checkout> <out_json>"""
import json, os, re, subprocess, sys
cfg, states, out = json.load(open(sys.argv[1])), {"LOW": sys.argv[2], "HIGH": sys.argv[3]}, sys.argv[4]
def span(root, f, decl):
    L = open(os.path.join(root, f)).read().split("\n"); s = next((i for i, l in enumerate(L) if decl in l), None)
    if s is None: return None
    d = 0; st = False
    for j in range(s, len(L)):
        d += L[j].count("{") - L[j].count("}"); st = st or "{" in L[j]
        if st and d == 0: return (s + 1, j + 1)
def grep(root, pat):
    p = subprocess.run(["grep", "-rn", "-E", pat, os.path.join(root, "src/main/java")], capture_output=True, text=True); return p.stdout.splitlines()
res = {}
for arm, root in states.items():
    A = cfg[arm.lower()]; cands = A["candidates"]
    nodes = [("facade", cfg["facade_file"], cfg["facade_decl"]), ("hop1 pack", cfg["hop1"]["file"], cfg["hop1"]["decl"]), ("gold lane", cfg["gold_file"], cfg["gold_decl"])] + [(c["method"], c["file"], c["decl"]) for c in cands]
    spans = {n: span(root, f, d) for n, f, d in nodes}
    files_on_path = [cfg["facade_file"], cfg["hop1"]["file"], cfg["gold_file"]]; pkgs = ["/".join(f.split("/")[4:-1]) for f in files_on_path]
    lane_hits = grep(root, r"\blane\b"); lane_decls = grep(root, r"static int lane\(")
    cand_hits = {c["method"]: len(grep(root, r"\b%s\(" % c["method"])) for c in cands}
    res[arm] = {"facade_to_gold_call_edges": 2, "path": "Conversion.intArrayToLong -> ArrayUtils.pack -> BitField.lane", "files_on_path": files_on_path, "package_transitions_on_path": pkgs,
                "distinct_files_touched": sorted({f for _, f, _ in nodes}), "distinct_packages_touched": sorted({"/".join(f.split("/")[4:-1]) for _, f, _ in nodes}),
                "spans": spans, "gold_declaration_lines": spans["gold lane"], "gold_call_site_in_pack": [l for l in grep(root, r"BitField\.lane\(") if "ArrayUtils.java" in l],
                "lexical": {"'lane' word hits in src/main": len(lane_hits), "'lane(' declarations": len(lane_decls), "candidate name call/decl hits": cand_hits,
                            "pack body calls": [l.split(":", 2)[2].strip() for l in grep(root, r"BitField\.lane\(|BitField\.offset\(|BitField\.widen\(|advance\(|gather\(|NumberUtils\.deposit\(|NumberUtils\.merge\(") if "ArrayUtils.java" in l and "public static" not in l]},
                "first_possible_gold_discovery_route": "grep intArrayToLong -> open Conversion (facade body names ArrayUtils.pack) -> open pack (names BitField.lane) -> open lane; identical in both arms"}
json.dump(res, open(out, "w"), indent=1); print(json.dumps({a: {k: v for k, v in r.items() if k in ("facade_to_gold_call_edges", "files_on_path", "distinct_files_touched", "distinct_packages_touched", "gold_declaration_lines", "lexical")} for a, r in res.items()}, indent=1))
