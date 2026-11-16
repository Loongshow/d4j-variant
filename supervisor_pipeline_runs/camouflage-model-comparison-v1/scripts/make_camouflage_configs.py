#!/usr/bin/env python
"""Build the per-arm pair_config.json files the existing validator/reproducer/packager consume.
Hops 1-4 and the facade come from the historical config verbatim; hop 5 and hop 4's call line
are the only per-arm differences. Usage: make_camouflage_configs.py <spec.json> <out-dir>"""
import json, os, sys, copy

spec = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
H = json.load(open(spec["historical_config"]))
ht = H["treatment"]
PAIR = spec["pair"]

for arm in ("low", "high"):
    A = spec["arms"][arm]
    hops = copy.deepcopy(ht["hops"][:4])
    hops[3]["calls_next"] = A["hop4_call"]
    gold_decl = spec["gold_decl_historical"].replace(
        spec["gold_method_historical"] + "(", spec["gold_method"] + "(")
    hops.append({"n": 5, "class": A["gold_host_class"], "method": spec["gold_method"],
                 "file": A["gold_host_file"], "decl": gold_decl,
                 "calls_next": None, "holds_bug": True})
    cfg = {
        "project": spec["project"], "bug_id": spec["bug_id"], "base_version": spec["base_version"],
        "pair_id": PAIR, "label": spec["label"],
        "camouflage_arm": arm.upper(), "camouflage_pair": PAIR,
        "control_id": spec["reference_id"], "treatment_id": A["variant_id"],
        "src_dir": "src/main/java", "test_dir": "src/test/java",
        "synthetic_call_hops": 5,
        "trigger": H["trigger"], "related_test": H.get("related_test"), "test_file": H["test_file"],
        "facade_file": H["facade_file"], "facade_decl": H["facade_decl"],
        "assertion_class_regex": H.get("assertion_class_regex", "AssertionError|AssertionFailedError"),
        "expected_signature": H["expected_signature"],
        "semantic_bug": spec["semantic_bug"],
        "control": copy.deepcopy(H["control"]),
        "treatment": {
            "gold_class": A["gold_host_class"], "gold_method": spec["gold_method"],
            "gold_file": A["gold_host_file"], "gold_decl": gold_decl,
            "orig_line": ht["orig_line"], "bug_line": ht["bug_line"],
            "facade_call": ht["facade_call"],
            "gold_arith_tokens": spec["gold_arith_tokens"],
            "hops": hops,
            "new_imports": [{"file": spec["hop4_file"], "line": l} for l in A.get("hop4_add_imports", [])],
        },
        "camouflage": {
            "manipulated_variable": "host environment of the gold method (file size, method count, same-file candidate count)",
            "held_constant": ["defects4j base", "semantic fault", "trigger", "expected and buggy value",
                              "failure signature", "facade", "hops 1-4 (byte-identical)", "hop count (5)",
                              "gold method name", "gold method body", "gold responsibility", "prompt",
                              "model", "tool budget", "test.patch (byte-identical)"],
            "gold_host": A["gold_host_class"],
            "historical_gold_host": spec["historical_gold_file"],
        },
    }
    p = os.path.join(out, f"pair_config_{arm}.json")
    json.dump(cfg, open(p, "w"), indent=1)
    print("wrote", p, "| gold", cfg["treatment"]["gold_class"] + "#" + cfg["treatment"]["gold_method"])
