"""Package + install both arms of a READY OCFLB pair. Usage: ocflb_package.py <pair.json>"""
import json, os, sys, hashlib, datetime, shutil
spec = json.load(open(sys.argv[1])); O = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"
val = json.load(open(f"{spec['pair_dir']}/validation/validation.json")); assert val["overall"] == "READY", val["overall"]
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest(); CH = spec["chain"]
for arm, A in spec["arms"].items():
    pkg = A["package_dir"]; G = A["gold"]; sig = val["arms"][arm]["trigger_runs"][0]["signature"]
    chain = {"facade": f"{CH['facade']['class']}#{CH['facade']['method']}"}
    for i, r in enumerate(["H1", "H2", "H3", "H4", "H5"], 1):
        chain[f"hop{i}"] = {"role": r, "class": CH[r]["class"], "method": CH[r]["method"], "file": CH[r]["file"], "holds_bug": (r == A["gold_role"])}
    man = {"schema_version": "d4j-variant-manifest/v1", "manifest_extension": "ocflb-level-b-v1/manifest/v1", "variant_id": A["variant_id"], "pair_id": spec["pair_id"], "arm": arm,
      "paired_variant": spec["arms"]["ADAPTER_FAULT" if arm == "DEFINER_FAULT" else "DEFINER_FAULT"]["variant_id"],
      "status": "non_canonical_validated", "benchmark_eligible": True, "non_canonical": True, "label": "NON-CANONICAL RESEARCH BENCHMARK / OCFLB (Ownership-Controlled Fault Localization Benchmark)",
      "source": {"defects4j_project": spec["project"], "defects4j_bug_id": 1, "bug_slug": f"{spec['project']}-1", "fixed_revision": "1f", "baseline_version": spec["base_version"], "seed_variant": spec.get("seed_variant")},
      "construction": {"method": "deterministic pair builder on a fresh checkout (scripts/pairs/build_*.py); git diff; shared test.patch across arms", "llm_generation_used": False, "paid_model_executed": False},
      "semantic_bug": {"family": spec["family"], "convention": spec.get("convention"), "buggy_line_text": G["bug_line"].strip(), "correct_line_text": G["orig_line"].strip(), "effect": spec.get("effect")},
      "trigger": {"test_id": spec["trigger"], "test_class": spec["trigger"].split("::")[0], "test_method": spec["trigger"].split("::")[1], "all_empirically_failing_tests": [spec["trigger"]] + (A.get("declared_collateral") or []), "failure_signature": sig},
      "fault": {"locations": [{"class": G["class"], "method": G["method"], "file": G["file"], "production": True}], "gold": {"faulty_class": G["class"], "faulty_method": G["method"]}, "gold_role": A["gold_role"], "semantic_root_cause": spec["family"]},
      "ownership": {"classification": val["arms"][arm].get("ownership"), "pin_test": spec["pin_test"], "second_caller": spec.get("second_caller"), "compensating_repair_target": A["compensating"]["role"]},
      "synthetic_call_hops": 5, "chain": chain, "changed_files": spec.get("changed_files", []),
      "reasoning": {"level": "L20", "level_semantics": "LEGACY DISCOVERY SLOT ONLY (storage directory name required by the frozen harness)", "changed_node": f"{G['class']}#{G['method']}"},
      "artifacts": {"manifest": "variant_manifest.json", "variant_patch": "variant.patch", "test_patch": "test.patch", "validation": "validation.json", "non_canonical_notice": "NON_CANONICAL.md"},
      "artifact_hashes": {"variant.patch": h(f"{pkg}/variant.patch"), "test.patch": h(f"{pkg}/test.patch")},
      "validation_summary": {"overall": val["overall"], "validated_at": val["finished_at"]},
      "provenance": {"toolchain": {"defects4j": "v3.0.1", "jdk": "OpenJDK 11.0.30"}, "note": "gold, roles, pin and compensating repair fixed in pair.json before any model run"},
      "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    json.dump(man, open(f"{pkg}/variant_manifest.json", "w"), indent=1)
    open(f"{pkg}/NON_CANONICAL.md", "w").write(f"# NON-CANONICAL RESEARCH BENCHMARK - OCFLB {A['variant_id']}\n\nArm {arm} of pair {spec['pair_id']} ({spec['project']}, {spec['family']}). Gold `{G['class']}#{G['method']}` ({A['gold_role']}). Trigger `{spec['trigger']}`. Pin `{spec['pin_test']}`. Not a canonical Defects4J bug; pending human review.\n")
    dst = f"{O}/new_bug_variants/{spec['project']}/bug-1/L20/{A['variant_id']}"; assert not os.path.exists(dst), dst; os.makedirs(dst)
    for f in ("variant.patch", "test.patch", "variant_manifest.json", "validation.json", "NON_CANONICAL.md"): shutil.copyfile(f"{pkg}/{f}", f"{dst}/{f}")
    print("installed", A["variant_id"], "gold", man["reasoning"]["changed_node"], "ownership", man["ownership"]["classification"])
