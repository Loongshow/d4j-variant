#!/usr/bin/env python
"""Generate the frozen analyzer's spec_<PAIR>_<ARM>.json for each camouflage arm, from that arm's
pair_config.json and its rendered payload. Same spec schema the multi-project analyzer already uses.
Usage: make_camouflage_specs.py"""
import json, os, re, glob

R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1"
A = f"{R}/experiment-a-camouflage"; OUT = f"{A}/results/analysis"
os.makedirs(f"{OUT}/per_bug", exist_ok=True); os.makedirs(f"{OUT}/per_run", exist_ok=True); os.makedirs(f"{OUT}/tables", exist_ok=True)
CONTRACTS = {
 "lang_conv": {"S_holder_mask": "field << shift", "I_word_extract": "words[i] = run[i] & field",
               "L_width_const": "final int width = Integer.SIZE", "R_guard": "is greather or equal to than 64",
               "H_shift_expr": "final int shift", "P_facade_loop": "System.arraycopy(array, startIndex, run, 0, count)"},
 "math_norm": {"S_thresholds": "rdwarf", "I_scaled_sum": "s1 + (s2 / x1max) / x1max",
               "L_branch_select": "if (major != 0)", "R_guard": "x < floor",
               "H_relative_expr": "final double relative", "P_sqrt_combine": "return scale * FastMath.sqrt(scaled + relative)"},
 "jkc_surr": {"S_surr_constants": "SURR1_FIRST", "I_inverse_split": "(char) (0xD800 + (ch >> 10))",
              "L_low_mask": "ch & 0x03FF", "R_range_check": "c > 0x10FFFF",
              "H_weight_hops": "final int bits", "P_plane_base": "final int base = 0x10000"},
}
for s in ("lang_conv", "math_norm", "jkc_surr"):
    for arm in ("low", "high"):
        cfg = json.load(open(f"{A}/construction/configs/{s}/pair_config_{arm}.json"))
        V = cfg["treatment_id"]; T = cfg["treatment"]
        chain = [["facade", cfg["control"]["gold_class"].split(".")[-1], cfg["control"]["gold_method"],
                  cfg["facade_decl"], T["facade_call"]]]
        for h in T["hops"]:
            chain.append([f"H{h['n']}", h["class"].split(".")[-1], h["method"], h["decl"], h["calls_next"]])
        pay = open(f"{A}/leakage/rendered_payload_{V}.txt", encoding="utf-8", errors="replace").read()
        toks = sorted({t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", pay) if not t.islower() or len(t) > 6})
        novel = sorted({h["class"].split(".")[-1] for h in T["hops"]} | {h["method"] for h in T["hops"]} |
                       {T["gold_method"], T["gold_class"].split(".")[-1]})
        spec = {"project": cfg["project"],
                "label": f"NON-CANONICAL / CONTROLLED LARGE-FILE CAMOUFLAGE / GPT-5.6 ({V})",
                "src_dir": cfg["src_dir"], "chain": chain,
                "arms": {V: {"arm": "TREATMENT", "gold_class": T["gold_class"], "gold_method": T["gold_method"],
                             "gold_decl": T["gold_decl"], "buggy": T["bug_line"].strip()}},
                "contract": CONTRACTS[s], "other": {"assertion_msg": cfg["expected_signature"],
                                                    "d4j_modified_class_output": "d4j.classes.modified"},
                "payload_tokens": toks, "novel_watch": novel,
                "gold_name_tokens": [T["gold_method"], T["gold_class"].split(".")[-1]]}
        p = f"{OUT}/spec_{V}.json"; json.dump(spec, open(p, "w"), indent=1)
        print("wrote", os.path.basename(p), "| chain", len(chain), "| payload tokens", len(toks))
