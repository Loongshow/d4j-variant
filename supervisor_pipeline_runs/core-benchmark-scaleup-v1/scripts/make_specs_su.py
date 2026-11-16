"""Generates analysis/spec_<bug>.json for analyze_multiproject.py from each bug's pair_config.json, its rendered TREATMENT payload and the treatment source.
Observable-only markers: exact source substrings (declarations, call lines, buggy lines, contract/javadoc snippets). No LLM."""
import json, os, re, sys
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1"
BUGS = {"chart/bug-02": "Chart", "chart/bug-03": "Chart", "math/bug-02": "Math", "math/bug-03": "Math", "lang/bug-02": "Lang"}
# contract / external-evidence markers per bug (substrings that appear in tool OUTPUT when the agent reads the evidence), chosen from TARGET_SPEC external evidence
CONTRACT = {
 "chart/bug-02": {"J_axis_range_javadoc": "the axis range", "A_lower_bound": "getLowerBound()", "A_upper_bound": "getUpperBound()", "S_valueToJava2D_sibling": "valueToJava2D(", "R_offset_from_lower_hops": "xv * (adjusted - lower)", "A_max_radius": "getMaxRadius()", "C_clamp_to_lower": "Math.max(radius"},
 "chart/bug-03": {"J_explode_javadoc": "explodePercent", "D_drawItem_call": "getArcBounds(", "R_ring_geometry": "getRadius()", "V_delta_vector_hops": "deltaX", "P_displacement_definition": "(point1.getX() - point2.getX()) * explodePercent", "T_translate_hops": "area.getX() + deltaX"},
 "math/bug-02": {"J_cross_javadoc": "cross partial derivative", "T_tricubic_sibling": "TricubicSplineInterpolator", "S_sibling_denominator": "(xval[nI] - xval[pI]) * (yval[nJ] - yval[pJ])", "D_dFdX_stage": "dFdX[i][j]", "D_dFdY_stage": "dFdY[i][j]", "D_spacing_hops": "final double dx = xval[nI] - xval[pI];", "F_function_ctor": "new BicubicSplineInterpolatingFunction("},
 "math/bug-03": {"J_model_javadoc": "f (t) = a cos (&omega; t + &phi;)", "J_B_minus_omega2": "B = - &omega;<sup>2</sup>", "R_relative_abscissa_hops": "t[i] - t[0]", "R_relative_abscissa_control": "getX() - observations[0].getX()", "M_math844_comment": "MATH-844", "D_deprecated_twin": "optimization.fitting", "Z_zero_range": "ZeroException"},
 "lang/bug-02": {"J_string_regionmatches_comment": "The same check as in String.regionMatches()", "S_string_fast_path": ".regionMatches(ignoreCase, thisStart, (String) substring, start, length)", "E_equalsIgnoreCase_javadoc": "ignoring case", "U_upper_fold": "Character.toUpperCase(", "L_lower_fold": "Character.toLowerCase(", "J_same_rule_javadoc": "(the same rule as in", "C_lower_fold_compare": "!= Character.toLowerCase(c2)"},
}
def idents(text): return sorted({t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text)})
for bug, proj in BUGS.items():
    root = f"{S}/{bug}"; cfg = json.load(open(f"{root}/pair_config.json")); T = cfg["treatment"]; C = cfg["control"]
    fac_cls = cfg["facade_file"].split("/")[-1].replace(".java", ""); fac_meth = cfg["facade_decl"].split("(")[0].split()[-1]
    fac_decl = cfg["facade_decl"].strip(); fac_call = T["facade_call"].strip()
    hops = T["hops"]; chain = [["facade", fac_cls, fac_meth, fac_decl, fac_call]]
    for i, h in enumerate(hops):
        tag = f"H{h['n']}"; chain.append([tag, h["class"].split(".")[-1], h["method"], h["decl"].strip(), (h["calls_next"] or "").strip() or None])
    def buggy_line(block):
        lines = [l.strip() for l in block.split("\n") if l.strip()]; return lines[-1] if len(lines) > 1 else lines[0]
    arms = {cfg["control_id"]: {"arm": "CONTROL", "gold_class": C["gold_class"], "gold_method": C["gold_method"], "gold_decl": C["gold_decl"].strip(), "buggy": buggy_line(C["bug_line"])},
            cfg["treatment_id"]: {"arm": "TREATMENT", "gold_class": T["gold_class"], "gold_method": T["gold_method"], "gold_decl": T["gold_decl"].strip(), "buggy": buggy_line(T["bug_line"])}}
    payload = open(f"{root}/analysis/leakage/rendered_payload_treatment.txt", errors="replace").read()
    payload_tokens = idents(payload)
    novel = sorted({h["method"] for h in hops} | {h["class"].split(".")[-1] for h in hops} | set(idents(T["orig_line"])) | set(idents(T["bug_line"])) - set(payload_tokens))
    spec = {"project": proj, "label": f"NON-CANONICAL / CORE BENCHMARK SCALE-UP / GPT-5.6 ({cfg['pair_id']})", "src_dir": cfg["src_dir"], "chain": chain, "arms": arms,
            "contract": CONTRACT[bug], "other": {"assertion_msg": cfg["expected_signature"], "d4j_modified_class_output": "d4j.classes.modified"},
            "payload_tokens": payload_tokens, "novel_watch": novel, "gold_name_tokens": [T["gold_method"], T["gold_class"].split(".")[-1]]}
    out = f"{S}/results-gpt56/analysis/spec_{cfg['pair_id']}.json"; json.dump(spec, open(out, "w"), indent=1)
    # sanity: every chain decl / call / buggy / gold_decl string must occur in the treatment repro checkout (control buggy in the control checkout)
    def grep(co, s):
        for dp, _, fs in os.walk(os.path.join(co, cfg["src_dir"])):
            for fn in fs:
                if fn.endswith(".java") and s in open(os.path.join(dp, fn), errors="replace").read().replace("\r\n", "\n"): return True
        return False
    tco = f"{root}/repro/treatment-checkout"; cco = f"{root}/repro/control-checkout"; missing = []
    for tag, cls, meth, decl, call in chain:
        if not grep(tco, decl): missing.append(("decl", tag, decl))
        if call and not grep(tco, call): missing.append(("call", tag, call))
    if not grep(tco, arms[cfg["treatment_id"]]["buggy"]): missing.append(("buggy", "T", arms[cfg["treatment_id"]]["buggy"]))
    if not grep(cco, arms[cfg["control_id"]]["buggy"]): missing.append(("buggy", "C", arms[cfg["control_id"]]["buggy"]))
    cm = {k: v for k, v in CONTRACT[bug].items() if not (grep(tco, v) or grep(cco, v) or v in payload)}
    print(f"{cfg['pair_id']:18s} spec -> {os.path.relpath(out, S)} | payload tokens {len(payload_tokens)} | novel_watch {len(novel)} | missing anchors: {missing or 'none'} | contract markers not found in source/payload: {cm or 'none'}")
