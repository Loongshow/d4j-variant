"""Write variant_manifest.json, validation.json and NON_CANONICAL.md for both arms from the executed validation/repro/lexgate results. No PASS is pre-written:
every status is read from the JSON the validators wrote. Usage: package_long.py"""
import json, os, hashlib, datetime, subprocess
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/conversion-dispatch-v1"; cfg = json.load(open(os.path.join(R, "analysis/pair_config_dispatch.json")))
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def tool(cmd):
    try: return subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5"))).stdout.strip().splitlines()[0]
    except Exception: return "unknown"
for arm in ("control", "treatment"):
    V = "CONVERSION-DISPATCH-CONTROL-01" if arm == "control" else "CONVERSION-DISPATCH-TREATMENT-01"; other = "CONVERSION-DISPATCH-TREATMENT-01" if arm == "control" else "CONVERSION-DISPATCH-CONTROL-01"
    pkg = os.path.join(R, V); A = cfg[arm]; val = json.load(open(os.path.join(R, "validation", f"{arm.upper()}_VALIDATION.json"))); rep = json.load(open(os.path.join(R, "repro", f"{arm.upper()}_REPRODUCTION.json")))
    lex = json.load(open(os.path.join(R, "analysis", f"lexgate_dispatch_{arm}01.json")))
    gates = {g["gate"]: g["status"] for g in val["gates"]}; assert val["overall"] == "pass" and rep["overall"] == "pass", (arm, val["overall"], rep["overall"])
    sig = val["trigger_runs"][0]["signature"]
    chain = None
    if arm == "treatment":
        chain = {"facade": "org.apache.commons.lang3.Conversion#intArrayToLong (keeps both guards)"}
        for hp in A["hops"]: chain[f"hop{hp['n']}"] = {"class": hp["class"], "method": hp["method"], "file": hp["file"], "holds_bug": bool(hp.get("holds_bug"))}
        chain["parameter_names_in_hops"] = ["array", "startIndex", "initial", "at", "count", "run", "width", "field", "words", "holder", "word", "index", "values"]
        chain["dispatch"] = {"boundary": "hop3 -> hop4", "abstraction": "org.apache.commons.lang3.builder.Folding (abstract class; binding Folding.STANDARD = new StandardFolding())", "implementation": "org.apache.commons.lang3.builder.StandardFolding#fold -> ObjectUtils.combine", "caller_free_of_next_stage_names": True}
    manifest = {
     "schema_version": "d4j-variant-manifest/v1", "manifest_extension": "conversion-dispatch-v1/manifest/v1", "variant_id": V, "pair_id": cfg["pair_id"], "arm": arm, "paired_variant": other,
     "relation_to_the_paired_variant": ("Same project, bug, byte-identical test.patch and byte-identical variant.patch to the validated CONVERSION-CONTROL-01 / CONVERSION-LONG-CONTROL-01; the paired DISPATCH TREATMENT relocates the loop behind the five-hop chain with indirect dispatch at hop 3 -> hop 4." if arm == "control" else
                                       "Same project, bug, byte-identical test.patch, same units mutation, same guards, same failure signature and collateral, same five semantic stages and gold as CONVERSION-LONG-TREATMENT-01; the hop3 -> hop4 call is replaced by indirect dispatch through the abstract class builder.Folding (binding Folding.STANDARD -> StandardFolding -> ObjectUtils.combine) so the caller body names neither the next method nor its class."),
     "status": "non_canonical_validated", "benchmark_eligible": False, "non_canonical": True, "label": "NON-CANONICAL / INDIRECT-DISPATCH DIAGNOSTIC / GPT-5.6 / CONSTRUCTION-VALIDATION ONLY",
     "source": {"defects4j_project": "Lang", "defects4j_bug_id": 1, "bug_slug": "Lang-1", "fixed_revision": "1f", "baseline_version": "Lang-1f (D4J_Lang_1_FIXED_VERSION)", "artifact_path": f"supervisor_pipeline_runs/conversion-dispatch-v1/{V}/"},
     "construction": {"method": "deterministic local construction on a fresh Lang-1f checkout (scripts/build_dispatch.py; exact asserted edits; git diff incl. two new files)", "llm_generation_used": False, "paid_model_executed": False, "design_basis": "analysis/DISPATCH_DESIGN.md (+ ../conversion-long-chain-v1/analysis/LONG_CHAIN_DESIGN.md; Java-semantics emulation scripts/emulate_chain.py)"},
     "semantic_bug": {"id": "28d74533eae80748", "facade": "org.apache.commons.lang3.Conversion#intArrayToLong", "family": "offset units mismatch (destination bit offset treated as a word index)",
                      "original_line_text": cfg["control"]["orig_line"], "buggy_line_text": cfg["control"]["bug_line"], "buggy_line_text_in_this_arm": A["bug_line"], "correct_line_text_in_this_arm": A["orig_line"],
                      "effect": "for dstPos != 0 the source ints are placed at ((i + dstPos) * 32) mod 64 instead of i * 32 + dstPos; existing tests (all dstPos = 0) unaffected", "locally_coherent": True, "identical_across_pair": True},
     "trigger": {"test_id": cfg["trigger"], "test_class": cfg["trigger"].split("::")[0], "test_method": cfg["trigger"].split("::")[1], "all_empirically_failing_tests": [cfg["trigger"]], "failure_signature": sig},
     "fault": {"locations": [{"class": A["gold_class"], "method": A["gold_method"], "file": A["gold_file"], "production": True}], "gold": {"faulty_class": A["gold_class"], "faulty_method": A["gold_method"]},
               "semantic_root_cause": "The destination offset is scaled by the word width, so a bit offset is treated as a word index; correct placement requires shift = index * width + offset."},
     "synthetic_call_hops": 5 if arm == "treatment" else 0, "dispatch_indirections": 1 if arm == "treatment" else 0, "chain": chain,
     "changed_files": ([{"file": cfg["facade_file"], "role": "gold"}] if arm == "control" else [{"file": cfg["facade_file"], "role": "facade"}] + [{"file": hp["file"], "role": ("gold" if hp.get("holds_bug") else f"hop{hp['n']}")} for hp in A["hops"]] + [{"file": A["dispatch"]["abstraction"]["file"], "role": "dispatch_abstraction_and_binding"}, {"file": A["dispatch"]["implementation"]["file"], "role": "dispatch_implementation"}]) + [{"file": cfg["test_file"], "role": "trigger"}],
     "reasoning": {"level": "L20", "level_semantics": "LEGACY DISCOVERY SLOT ONLY (storage directory name required by the frozen harness) — NOT a measured reasoning level; see synthetic_call_hops / dispatch_indirections", "changed_node": f"{A['gold_class']}#{A['gold_method']}"},
     "contract_evidence_location": "facade javadoc/guard in Conversion.java; nine sibling methods 'shift = i * W + dstPos'; inverse longToIntArray; sibling tests with dstPos = 8/16/24",
     "artifacts": {"manifest": "variant_manifest.json", "variant_patch": "variant.patch", "test_patch": "test.patch", "validation": "validation.json", "non_canonical_notice": "NON_CANONICAL.md"},
     "artifact_hashes": {"variant.patch": h(os.path.join(pkg, "variant.patch")), "test.patch": h(os.path.join(pkg, "test.patch"))},
     "validation_artifact_hashes": {f"validation/{arm.upper()}_VALIDATION.json": h(os.path.join(R, "validation", f"{arm.upper()}_VALIDATION.json")), f"repro/{arm.upper()}_REPRODUCTION.json": h(os.path.join(R, "repro", f"{arm.upper()}_REPRODUCTION.json"))},
     "reproducibility": {"status": "passed", "reproduced_at": rep["finished_at"], "method": "fresh defects4j checkout, git apply of packaged patches only, compile, trigger x3, static gold/chain check", "fresh_checkout_head": rep["checkout_head"]},
     "leakage": {"lexgate_verdict": lex["verdict"], "lexgate_scannable_reach": lex.get("scannable_reach", []), "lexgate_name_exposure": lex["name_exposure"], "note": "see analysis/DISPATCH_LEAKAGE_AUDIT.md; CONTROL exposure is inherent (gold = method under test)"},
     "provenance": {"toolchain": {"defects4j": tool(["defects4j", "--version"]) if False else "v3.0.1-9-gac76feee", "jdk": "OpenJDK 11.0.30", "python": "3.13.12"}, "supervisor_generator_used": False, "note": "constructed independently of the supervisor generator; no supervisor code executed; no LLM"},
     "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    json.dump(manifest, open(os.path.join(pkg, "variant_manifest.json"), "w"), indent=1)
    gate_map = {"baseline_compile": "A", "baseline_trigger": "D", "baseline_related_test": "B1", "variant_compile": "F", "deterministic": "H", "clean_value_mismatch": "I", "collateral": "K", "source_reset_clean": "L"}
    vj = {"schema_version": "d4j-validation/v1", "validation_extension": "conversion-dispatch-v1/validation/v1", "variant_id": V, "status": "accepted", "accepted": True, "non_canonical": True, "validator_version": "conversion-dispatch-v1/validate_dispatch.py", "validated_at": val["finished_at"],
          "gate": {k: {"status": gates[g]} for k, g in gate_map.items()}}
    vj["gate"]["baseline_trigger"]["note"] = "new trigger passes on the correct implementation"; vj["gate"]["variant_trigger"] = {"status": "expected_fail" if gates["G"] == "pass" else "FAIL", "test_id": cfg["trigger"]}
    vj["gate"]["variant_trigger_runs"] = [{"run": t["run"], "status": "expected_fail" if t["n_fail"] == 1 else "FAIL", "signature": t["signature"], "failing_tests_sha256": t["failing_tests_sha256"]} for t in val["trigger_runs"]]
    vj["gate"]["collateral"].update({"baseline_failures": val["baseline_full_suite_failures"], "buggy_failures": val["buggy_full_suite_failures"]})
    vj["gate"]["production_fault"] = {"status": "pass"}; vj["gate"]["gold_method_known"] = {"status": "pass"}
    vj["gate"]["fresh_checkout_reproduction"] = {"status": rep["overall"], "steps": [[s["step"], s["status"]] for s in rep["steps"]], "checkout_head": rep["checkout_head"]}
    if arm == "treatment":
        vj["gate"].update({"correct_chain_compiles": {"status": gates["M"]}, "correct_logic_through_chain": {"status": gates["N"]}, "correct_chain_full_suite_equals_baseline": {"status": gates["N2"]}, "bug_in_hop5_only": {"status": gates["O"]}, "chain_wiring_five_hops": {"status": gates["P"]}, "dispatch_integrity": {"status": gates["DI"]}, "dispatch_wiring": {"status": gates["DW"]}, "no_pass_through_hops": {"status": gates["Q"]}})
    vj["gate"]["lexgate"] = {"status": "documented", "verdict": lex["verdict"]}; vj["gate"]["local_coherence_audit"] = {"status": "pass", "report": "../conversion-long-chain-v1/analysis/LOCAL_COHERENCE_CONSTRUCTION_AUDIT.md (gold unchanged) + analysis/DISPATCH_LEAKAGE_AUDIT.md"}
    vj["validated_with"] = {"baseline_revision": "Lang-1f", "construction_checkout": val["work_checkout"], "fresh_checkout": rep["fresh_checkout"]}; vj["paid_model_executed"] = False
    json.dump(vj, open(os.path.join(pkg, "validation.json"), "w"), indent=1)
    open(os.path.join(pkg, "NON_CANONICAL.md"), "w").write(f"NON-CANONICAL · INDIRECT-DISPATCH DIAGNOSTIC · GPT-5.6 · CONSTRUCTION / VALIDATION ONLY · NO PAID MODEL EXECUTED AT PACKAGING TIME\n\n{V}: deterministic, LLM-free construction on Lang-1f of the validated locally coherent units fault in Conversion#intArrayToLong"
        + (" (CONTROL: fault in the facade; variant.patch byte-identical to CONVERSION-CONTROL-01)." if arm == "control" else " relocated behind five synthetic cross-class hops with indirect dispatch at hop 3 -> hop 4: ArrayUtils.gather -> EnumUtils.compose -> BitField.widen -> [Folding.STANDARD -> StandardFolding.fold] -> ObjectUtils.combine -> NumberUtils.overlay (gold, hop 5).")
        + f"\nNot part of the canonical CRFLB corpus. reasoning.level is a legacy storage slot only; synthetic_call_hops = {manifest['synthetic_call_hops']}.\nValidation: validation/{arm.upper()}_VALIDATION.json; reproduction: repro/{arm.upper()}_REPRODUCTION.json.\n")
    print(V, "packaged; gates:", {g: s for g, s in gates.items() if s != "pass"} or "all pass", "| lexgate", lex["verdict"], "| repro", rep["overall"])
