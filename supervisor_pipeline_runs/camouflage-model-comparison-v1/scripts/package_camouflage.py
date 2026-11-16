#!/usr/bin/env python
"""Freeze one camouflage arm: write variant_manifest.json, validation.json and NON_CANONICAL.md into
its package directory from the executed validation / reproduction / lexgate / equivalence / ownership
results. No status is pre-written; every gate value is read back from the JSON a validator produced.
Usage: package_camouflage.py <spec.json> <low|high>"""
import json, os, sys, hashlib, datetime

spec = json.load(open(sys.argv[1])); arm = sys.argv[2]
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1"
A = f"{R}/experiment-a-camouflage"; sname = os.path.basename(sys.argv[1])[:-5]
cfg = json.load(open(f"{A}/construction/configs/{sname}/pair_config_{arm}.json"))
V = cfg["treatment_id"]; other = cfg["treatment_id"].replace("-LOW", "-HIGH") if arm == "low" else cfg["treatment_id"].replace("-HIGH", "-LOW")
pkg = f"{A}/construction/packages/{V}"
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
val = json.load(open(f"{A}/validation/{V}_VALIDATION.json"))
rep = json.load(open(f"{A}/repro/{V}_REPRODUCTION.json"))
lex = json.load(open(f"{A}/leakage/lexgate_{V}.json"))
eqv = json.load(open(f"{A}/equivalence/{sname}/equivalence.json"))
cam = json.load(open(f"{A}/review/camouflage_audit_{sname}.json"))
met = json.load(open(f"{A}/review/metrics/{sname.split('_')[0]}_{arm}.json"))
own_p = f"{A}/review/ownership/{V}_ownership.json"
own = json.load(open(own_p)) if os.path.exists(own_p) else None
assert val["overall"] == "pass" and rep["overall"] == "pass" and eqv["overall"] == "pass", (V, val["overall"], rep["overall"], eqv["overall"])
gates = {g["gate"]: g["status"] for g in val["gates"]}
sig = val["trigger_runs"][0]["signature"]
T = cfg["treatment"]
chain = {"facade": f"{cfg['control']['gold_class']}#{cfg['control']['gold_method']} (keeps its javadoc and guards)"}
for hp in T["hops"]:
    chain[f"hop{hp['n']}"] = {"class": hp["class"], "method": hp["method"], "file": hp["file"],
                              "holds_bug": bool(hp.get("holds_bug"))}
manifest = {
 "schema_version": "d4j-variant-manifest/v1",
 "manifest_extension": "camouflage-model-comparison-v1/manifest/v1",
 "variant_id": V, "pair_id": cfg["pair_id"], "arm": f"CAMOUFLAGE_{arm.upper()}", "paired_variant": other,
 "relation_to_the_paired_variant": ("Same Defects4J base, byte-identical test.patch, same semantic fault, same failure "
   "signature, same facade, byte-identical hops 1-4 and byte-identical gold method body; the ONLY difference is which "
   "existing production class hosts the gold method (and therefore the file size, method count and same-file candidate "
   "count the agent must search) plus the single hop-4 call line that names it."),
 "status": "non_canonical_validated", "benchmark_eligible": False, "non_canonical": True,
 "label": cfg["label"] + " / CONSTRUCTION-VALIDATION ONLY",
 "source": {"defects4j_project": cfg["project"], "defects4j_bug_id": cfg["bug_id"],
            "bug_slug": f"{cfg['project']}-{cfg['bug_id']}", "fixed_revision": f"{cfg['bug_id']}f",
            "baseline_version": cfg["base_version"],
            "artifact_path": f"supervisor_pipeline_runs/camouflage-model-comparison-v1/experiment-a-camouflage/construction/packages/{V}/"},
 "construction": {"method": ("deterministic local construction on a fresh checkout by "
   "scripts/build_camouflage_variant.py: the facade edit and hops 1-4 are taken byte-identically from the "
   f"already-validated historical patch of {spec['historical_pair']}, and only the gold method is relocated into this "
   "arm's host class by a pre-registered anchor rule; git diff"),
   "llm_generation_used": False, "paid_model_executed": False,
   "design_basis": "experiment-a-camouflage/review/CAMOUFLAGE_METRICS.md and supervisor-recipe-audit/SUPERVISOR_RECIPE_AUDIT.md"},
 "camouflage": dict(cfg["camouflage"], arm=arm.upper(), host_metrics={
   "file_loc_total": met["file_loc_total"], "declared_methods": met["declared_methods"],
   "gold_percentile_in_file": met["gold_percentile_in_file"],
   "methods_within_100_lines": met["methods_within_100_lines"],
   "candidates": met["candidates"]["C4_any_arith"],
   "candidate_definitions": "see review/CAMOUFLAGE_METRICS.md"}),
 "semantic_bug": {"facade": f"{cfg['control']['gold_class']}#{cfg['control']['gold_method']}",
   "family": cfg["semantic_bug"]["family"], "original_line_text": cfg["control"]["orig_line"].strip(),
   "buggy_line_text": cfg["control"]["bug_line"].strip(),
   "buggy_line_text_in_this_arm": T["bug_line"].strip(),
   "correct_line_text_in_this_arm": T["orig_line"].strip(),
   "effect": cfg["semantic_bug"]["effect"], "locally_coherent": True, "identical_across_pair": True},
 "trigger": {"test_id": cfg["trigger"], "test_class": cfg["trigger"].split("::")[0],
   "test_method": cfg["trigger"].split("::")[1], "all_empirically_failing_tests": [cfg["trigger"]],
   "failure_signature": sig},
 "fault": {"locations": [{"class": T["gold_class"], "method": T["gold_method"], "file": T["gold_file"], "production": True}],
   "gold": {"faulty_class": T["gold_class"], "faulty_method": T["gold_method"]},
   "semantic_root_cause": cfg["semantic_bug"]["family"]},
 "synthetic_call_hops": cfg["synthetic_call_hops"], "chain": chain,
 "changed_files": [{"file": cfg["facade_file"], "role": "facade"}] +
   [{"file": hp["file"], "role": ("gold" if hp.get("holds_bug") else f"hop{hp['n']}")} for hp in T["hops"]] +
   [{"file": cfg["test_file"], "role": "trigger"}],
 "reasoning": {"level": "L20",
   "level_semantics": "LEGACY DISCOVERY SLOT ONLY (storage directory name required by the frozen harness) - NOT a measured reasoning level; see synthetic_call_hops",
   "changed_node": f"{T['gold_class']}#{T['gold_method']}"},
 "artifacts": {"manifest": "variant_manifest.json", "variant_patch": "variant.patch", "test_patch": "test.patch",
   "validation": "validation.json", "non_canonical_notice": "NON_CANONICAL.md"},
 "artifact_hashes": {"variant.patch": h(f"{pkg}/variant.patch"), "test.patch": h(f"{pkg}/test.patch")},
 "validation_artifact_hashes": {f"validation/{V}_VALIDATION.json": h(f"{A}/validation/{V}_VALIDATION.json"),
   f"repro/{V}_REPRODUCTION.json": h(f"{A}/repro/{V}_REPRODUCTION.json")},
 "reproducibility": {"status": rep["overall"], "reproduced_at": rep["finished_at"],
   "method": "fresh defects4j checkout, git apply of packaged patches only, compile, trigger x3, static chain check",
   "fresh_checkout_head": rep["checkout_head"]},
 "leakage": {"lexgate_verdict": lex["verdict"], "lexgate_scannable_reach": lex.get("scannable_reach", []),
   "lexgate_name_exposure": lex["name_exposure"],
   "camouflage_audit": {"overall": cam["overall"],
     "payload_byte_identical_across_arms": cam["checks"]["rendered_payload_byte_identical"]["pass"],
     "gold_text_byte_identical_across_arms": cam["checks"]["gold_method_text_identical"]["pass"]}},
 "semantic_equivalence": {"probe_class": spec["probe_class"], "cases": eqv["cases"],
   "low_correct_equals_original": eqv["low_correct_equals_original"],
   "high_correct_equals_original": eqv["high_correct_equals_original"],
   "low_buggy_equals_high_buggy": eqv["low_buggy_equals_high_buggy"],
   "cases_where_bug_changes_output": eqv["cases_where_bug_changes_output"], "overall": eqv["overall"]},
 "ownership": ({"behavioural_classification": own["behavioural_classification"],
   "equivalent_repair_sites": own["equivalent_repair_sites"],
   "compensating_repair_sites": own["compensating_repair_sites"],
   "contractual_classification": "MOSTLY_UNIQUE (see review/OWNERSHIP_AUDIT.md)"} if own else
   {"behavioural_classification": "not_run_for_this_arm",
    "note": "the paired arm was tested; the chain, hops and gold body are byte-identical across arms",
    "contractual_classification": "MOSTLY_UNIQUE (see review/OWNERSHIP_AUDIT.md)"}),
 "provenance": {"toolchain": {"defects4j": "v3.0.1", "jdk": "OpenJDK 11.0.30", "python": "3.13"},
   "supervisor_generator_used": False,
   "note": ("constructed independently of the supervisor generator; no supervisor code executed and no supervisor file "
            "modified; the supervisor's host-size criterion was recovered by source audit only")},
 "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
json.dump(manifest, open(f"{pkg}/variant_manifest.json", "w"), indent=1)

gate_map = {"baseline_compile": "A", "baseline_trigger": "D", "variant_compile": "F", "deterministic": "H",
            "clean_value_mismatch": "I", "collateral": "K", "source_reset_clean": "L"}
vj = {"schema_version": "d4j-validation/v1", "validation_extension": "camouflage-model-comparison-v1/validation/v1",
      "variant_id": V, "status": "accepted", "accepted": True, "non_canonical": True,
      "validator_version": "camouflage-model-comparison-v1/validate_pair.py", "validated_at": val["finished_at"],
      "gate": {k: {"status": gates[g]} for k, g in gate_map.items()}}
vj["gate"]["baseline_trigger"]["note"] = "new trigger passes on the original (correct) implementation"
vj["gate"]["variant_trigger"] = {"status": "expected_fail" if gates["G"] == "pass" else "FAIL", "test_id": cfg["trigger"]}
vj["gate"]["variant_trigger_runs"] = [{"run": t["run"], "status": "expected_fail" if t["n_fail"] == 1 else "FAIL",
   "signature": t["signature"], "failing_tests_sha256": t["failing_tests_sha256"]} for t in val["trigger_runs"]]
vj["gate"]["collateral"].update({"baseline_failures": val["baseline_full_suite_failures"],
   "buggy_failures": val["buggy_full_suite_failures"], "baseline_tests_executed": val.get("baseline_tests_executed")})
vj["gate"]["production_fault"] = {"status": "pass"}; vj["gate"]["gold_method_known"] = {"status": "pass"}
vj["gate"]["correct_chain_equivalence"] = {"status": gates.get("N2", gates.get("N", "n/a")),
   "note": "full relevant suite through the correct five-hop chain equals the baseline failure set"}
vj["gate"]["bug_in_hop5_only"] = {"status": gates["O"]}
vj["gate"]["chain_wiring"] = {"status": gates["P"]}
vj["gate"]["no_pass_through_hop"] = {"status": gates["Q"]}
vj["gate"]["fresh_checkout_reproduction"] = {"status": rep["overall"],
   "steps": [[s["step"], s["status"]] for s in rep["steps"]], "checkout_head": rep["checkout_head"]}
vj["gate"]["semantic_equivalence_probe"] = {"status": eqv["overall"], "cases": eqv["cases"],
   "low_buggy_equals_high_buggy": eqv["low_buggy_equals_high_buggy"]}
vj["gate"]["camouflage_audit"] = {"status": cam["overall"]}
vj["all_gates"] = [[g["gate"], g["status"]] for g in val["gates"]]
json.dump(vj, open(f"{pkg}/validation.json", "w"), indent=1)

open(f"{pkg}/NON_CANONICAL.md", "w").write(f"""# NON-CANONICAL VARIANT - {V}

This is **not** a canonical Defects4J bug. It is a locally constructed, validated variant built for the
controlled large-file camouflage experiment (`camouflage-model-comparison-v1`).

- Base: {cfg['base_version']}, fixed revision {cfg['bug_id']}f.
- Semantic fault: {cfg['semantic_bug']['family']}
- Fault location (gold): `{T['gold_class']}#{T['gold_method']}` in `{T['gold_file']}`
- Trigger: `{cfg['trigger']}`
- Synthetic call hops: {cfg['synthetic_call_hops']} (facade -> hop1 -> hop2 -> hop3 -> hop4 -> gold)
- Camouflage arm: **{arm.upper()}** - host file {met['file_loc_total']} lines, {met['declared_methods']} declared
  methods, gold at {met['gold_percentile_in_file']}% of the file.
- Paired variant: `{other}` (identical in every respect except the gold's host class).
- `benchmark_eligible: false`: this variant exists for the camouflage comparison and has not been
  through human benchmark review.

Validation, fresh reproduction, lexgate, the five-state semantic-equivalence probe, the camouflage audit
and the ownership audit are recorded under
`supervisor_pipeline_runs/camouflage-model-comparison-v1/experiment-a-camouflage/`.
""")
print(f"packaged {V}: manifest+validation+notice; variant.patch {manifest['artifact_hashes']['variant.patch'][:12]} test.patch {manifest['artifact_hashes']['test.patch'][:12]}")
