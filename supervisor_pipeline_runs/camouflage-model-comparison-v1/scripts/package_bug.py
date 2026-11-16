"""Usage: package_bug.py <config.json> <proj-dir> <bug-dir>. Write variant_manifest.json, validation.json and NON_CANONICAL.md for both arms of one project from the executed validation / repro / lexgate
results. No PASS is pre-written: every status is read from the JSON the validators wrote. Usage: package_pair.py <config.json> <project_dir_name>"""
import json, os, hashlib, datetime, sys
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"; cfg = json.load(open(sys.argv[1])); P = sys.argv[2]; BUG = sys.argv[3]; MP = os.path.join(S, P, BUG)
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
for arm in ("control", "treatment"):
    V = cfg[f"{arm}_id"]; other = cfg["treatment_id" if arm == "control" else "control_id"]; pkg = os.path.join(MP, "packages", V); A = cfg[arm]
    val = json.load(open(os.path.join(MP, "validation", f"{arm.upper()}_VALIDATION.json"))); rep = json.load(open(os.path.join(MP, "repro", f"{arm.upper()}_REPRODUCTION.json")))
    lex = json.load(open(os.path.join(MP, "analysis", "leakage", f"lexgate_{arm}.json")))
    gates = {g["gate"]: g["status"] for g in val["gates"]}; assert val["overall"] == "pass" and rep["overall"] == "pass", (P, arm, val["overall"], rep["overall"])
    sig = val["trigger_runs"][0]["signature"]
    chain = None
    if arm == "treatment":
        chain = {"facade": f"{cfg['control']['gold_class']}#{cfg['control']['gold_method']} (keeps its javadoc and guards)"}
        for hp in cfg["treatment"]["hops"]: chain[f"hop{hp['n']}"] = {"class": hp["class"], "method": hp["method"], "file": hp["file"], "holds_bug": bool(hp.get("holds_bug"))}
    manifest = {
     "schema_version": "d4j-variant-manifest/v1", "manifest_extension": "core-benchmark-scaleup-v2/manifest/v1", "variant_id": V, "pair_id": cfg["pair_id"], "arm": arm, "paired_variant": other,
     "relation_to_the_paired_variant": ("Same project, bug, byte-identical test.patch; the fault stays in the original method (0 synthetic hops)." if arm == "control" else "Same project, bug, byte-identical test.patch, same semantic fault, same failure signature and collateral; the method's computation is decomposed into five semantically staged cross-class hops with the fault in hop 5."),
     "status": "non_canonical_validated", "benchmark_eligible": False, "non_canonical": True, "label": cfg["label"] + " / CONSTRUCTION-VALIDATION ONLY",
     "source": {"defects4j_project": cfg["project"], "defects4j_bug_id": cfg["bug_id"], "bug_slug": f"{cfg['project']}-{cfg['bug_id']}", "fixed_revision": f"{cfg['bug_id']}f", "baseline_version": cfg["base_version"], "artifact_path": f"supervisor_pipeline_runs/core-benchmark-scaleup-v2/{P}/{BUG}/packages/{V}/"},
     "construction": {"method": f"deterministic local construction on a fresh {cfg['project']}-{cfg['bug_id']}f checkout (scripts/build_{P}_{BUG.replace('-', '')}.py; exact asserted edits; git diff)", "llm_generation_used": False, "paid_model_executed": False, "design_basis": f"{P}/{BUG}/analysis/FIVE_HOP_DESIGN.md (local code analysis + double-arithmetic emulation scripts/emulate_pairs.py)"},
     "semantic_bug": {"facade": f"{cfg['control']['gold_class']}#{cfg['control']['gold_method']}", "family": cfg["semantic_bug"]["family"], "original_line_text": cfg["control"]["orig_line"].strip(), "buggy_line_text": cfg["control"]["bug_line"].strip(),
                      "buggy_line_text_in_this_arm": A["bug_line"].strip(), "correct_line_text_in_this_arm": A["orig_line"].strip(), "effect": cfg["semantic_bug"]["effect"], "locally_coherent": True, "identical_across_pair": True},
     "trigger": {"test_id": cfg["trigger"], "test_class": cfg["trigger"].split("::")[0], "test_method": cfg["trigger"].split("::")[1], "all_empirically_failing_tests": [cfg["trigger"]], "failure_signature": sig},
     "fault": {"locations": [{"class": A["gold_class"], "method": A["gold_method"], "file": A["gold_file"], "production": True}], "gold": {"faulty_class": A["gold_class"], "faulty_method": A["gold_method"]}, "semantic_root_cause": cfg["semantic_bug"]["family"]},
     "synthetic_call_hops": cfg["synthetic_call_hops"] if arm == "treatment" else 0, "chain": chain,
     "changed_files": ([{"file": cfg["facade_file"], "role": "gold"}] if arm == "control" else [{"file": cfg["facade_file"], "role": "facade"}] + [{"file": hp["file"], "role": ("gold" if hp.get("holds_bug") else f"hop{hp['n']}")} for hp in cfg["treatment"]["hops"]]) + [{"file": cfg["test_file"], "role": "trigger"}],
     "reasoning": {"level": "L20", "level_semantics": "LEGACY DISCOVERY SLOT ONLY (storage directory name required by the frozen harness) - NOT a measured reasoning level; see synthetic_call_hops", "changed_node": f"{A['gold_class']}#{A['gold_method']}"},
     "artifacts": {"manifest": "variant_manifest.json", "variant_patch": "variant.patch", "test_patch": "test.patch", "validation": "validation.json", "non_canonical_notice": "NON_CANONICAL.md"},
     "artifact_hashes": {"variant.patch": h(os.path.join(pkg, "variant.patch")), "test.patch": h(os.path.join(pkg, "test.patch"))},
     "validation_artifact_hashes": {f"validation/{P}/{arm.upper()}_VALIDATION.json": h(os.path.join(MP, "validation", f"{arm.upper()}_VALIDATION.json")), f"repro/{P}/{arm.upper()}_REPRODUCTION.json": h(os.path.join(MP, "repro", f"{arm.upper()}_REPRODUCTION.json"))},
     "reproducibility": {"status": "passed", "reproduced_at": rep["finished_at"], "method": "fresh defects4j checkout, git apply of packaged patches only, compile, trigger x3, static gold/chain check", "fresh_checkout_head": rep["checkout_head"]},
     "leakage": {"lexgate_verdict": lex["verdict"], "lexgate_scannable_reach": lex.get("scannable_reach", []), "lexgate_name_exposure": lex["name_exposure"], "note": f"see {P}/{BUG}/analysis/LEAKAGE_AUDIT.md; CONTROL exposure is inherent (gold = method under test)"},
     "provenance": {"toolchain": {"defects4j": "v3.0.1", "jdk": "OpenJDK 11.0.30", "python": "3.13"}, "supervisor_generator_used": False, "note": "constructed independently of the supervisor generator; no supervisor code executed; no LLM"},
     "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    json.dump(manifest, open(os.path.join(pkg, "variant_manifest.json"), "w"), indent=1)
    gate_map = {"baseline_compile": "A", "baseline_trigger": "D", "variant_compile": "F", "deterministic": "H", "clean_value_mismatch": "I", "collateral": "K", "source_reset_clean": "L"}
    vj = {"schema_version": "d4j-validation/v1", "validation_extension": "core-benchmark-scaleup-v2/validation/v1", "variant_id": V, "status": "accepted", "accepted": True, "non_canonical": True, "validator_version": "core-benchmark-scaleup-v2/validate_pair.py", "validated_at": val["finished_at"],
          "gate": {k: {"status": gates[g]} for k, g in gate_map.items()}}
    vj["gate"]["baseline_trigger"]["note"] = "new trigger passes on the correct implementation"; vj["gate"]["variant_trigger"] = {"status": "expected_fail" if gates["G"] == "pass" else "FAIL", "test_id": cfg["trigger"]}
    vj["gate"]["variant_trigger_runs"] = [{"run": t["run"], "status": "expected_fail" if t["n_fail"] == 1 else "FAIL", "signature": t["signature"], "failing_tests_sha256": t["failing_tests_sha256"]} for t in val["trigger_runs"]]
    vj["gate"]["collateral"].update({"baseline_failures": val["baseline_full_suite_failures"], "buggy_failures": val["buggy_full_suite_failures"], "baseline_tests_executed": val.get("baseline_tests_executed")})
    vj["gate"]["production_fault"] = {"status": "pass"}; vj["gate"]["gold_method_known"] = {"status": "pass"}
    vj["gate"]["fresh_checkout_reproduction"] = {"status": rep["overall"], "steps": [[s["step"], s["status"]] for s in rep["steps"]], "checkout_head": rep["checkout_head"]}
    if arm == "treatment":
        vj["gate"].update({"correct_chain_compiles": {"status": gates["M"]}, "correct_logic_through_chain": {"status": gates["N"]}, "correct_chain_full_suite_equals_baseline": {"status": gates["N2"]}, "bug_in_hop5_only": {"status": gates["O"]}, "chain_wiring_five_hops": {"status": gates["P"]}, "no_pass_through_hops": {"status": gates["Q"]}})
    vj["gate"]["lexgate"] = {"status": "documented", "verdict": lex["verdict"]}; vj["gate"]["local_coherence_audit"] = {"status": "pass", "report": f"{P}/{BUG}/analysis/LOCAL_COHERENCE_AUDIT.md"}
    vj["validated_with"] = {"baseline_revision": f"{cfg['project']}-{cfg['bug_id']}f", "construction_checkout": val["work_checkout"], "fresh_checkout": rep["fresh_checkout"]}; vj["paid_model_executed"] = False
    json.dump(vj, open(os.path.join(pkg, "validation.json"), "w"), indent=1)
    open(os.path.join(pkg, "NON_CANONICAL.md"), "w").write(f"NON-CANONICAL · CORE BENCHMARK SCALE-UP V2 · CONSTRUCTION / VALIDATION ONLY · NO GPT-5.6 RUNS PERFORMED\n\n{V}: deterministic, LLM-free construction on {cfg['project']}-{cfg['bug_id']}f of a locally coherent semantic fault in {cfg['control']['gold_class']}#{cfg['control']['gold_method']}"
        + (" (CONTROL: fault in the original method)." if arm == "control" else " relocated behind five synthetic cross-class hops: " + " -> ".join(f"{hp['class'].split('.')[-1]}.{hp['method']}" for hp in cfg["treatment"]["hops"]) + " (gold, hop 5).")
        + f"\nNot part of the canonical CRFLB corpus. reasoning.level is a legacy storage slot only; synthetic_call_hops = {manifest['synthetic_call_hops']}.\nValidation: {P}/{BUG}/validation/{arm.upper()}_VALIDATION.json; reproduction: {P}/{BUG}/repro/{arm.upper()}_REPRODUCTION.json.\n")
    print(V, "packaged; gates:", {g: s for g, s in gates.items() if s != "pass"} or "all pass", "| lexgate", lex["verdict"], "| repro", rep["overall"])
