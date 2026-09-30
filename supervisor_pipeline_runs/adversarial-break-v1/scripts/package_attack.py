"""Package + install one validated attack variant. Usage: package_attack.py <attack.json> <validation.json>"""
import json, os, sys, hashlib, datetime, shutil
cfg = json.load(open(sys.argv[1])); val = json.load(open(sys.argv[2])); assert val["overall"] == "pass", val["overall"]
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1"
V = cfg["variant_id"]; pkg = cfg["package_dir"]; G = cfg["gold"]; h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
sig = val["trigger_runs"][0]["signature"]
man = {"schema_version": "d4j-variant-manifest/v1", "manifest_extension": "adversarial-break-v1/manifest/v1", "variant_id": V,
  "pair_id": cfg.get("attack_id", V), "arm": "ADVERSARIAL", "status": "non_canonical_validated", "benchmark_eligible": False, "non_canonical": True,
  "label": "NON-CANONICAL / ADVERSARIAL FAULT-LOCALIZATION BREAKING / EXPLORATORY",
  "source": {"defects4j_project": cfg["project"], "defects4j_bug_id": 1, "bug_slug": f"{cfg['project']}-1", "fixed_revision": "1f",
             "baseline_version": cfg.get("base_version", f"{cfg['project']}-1f"), "artifact_path": os.path.relpath(pkg, "/Users/shawnli/Desktop/Honours/defects4j") + "/"},
  "construction": {"method": "deterministic local construction (scripts/attacks/<id>.py) on a fresh checkout; git diff", "llm_generation_used": False, "paid_model_executed": False},
  "attack": {"id": cfg.get("attack_id"), "title": cfg.get("title"), "mechanism": cfg.get("mechanism"), "classification": cfg.get("classification"),
             "predicted_wrong_top1": cfg.get("predicted_wrong_top1"), "roles": cfg.get("roles"), "candidates": cfg.get("candidates"), "structure": cfg.get("structure")},
  "semantic_bug": {"family": cfg.get("family"), "buggy_line_text": G["bug_line"].strip(), "correct_line_text": G["orig_line"].strip(), "effect": cfg.get("effect")},
  "trigger": {"test_id": cfg["trigger"], "test_class": cfg["trigger"].split("::")[0], "test_method": cfg["trigger"].split("::")[1], "all_empirically_failing_tests": [cfg["trigger"]], "failure_signature": sig},
  "fault": {"locations": [{"class": G["class"], "method": G["method"], "file": G["file"], "production": True}], "gold": {"faulty_class": G["class"], "faulty_method": G["method"]}, "semantic_root_cause": cfg.get("family")},
  "synthetic_call_hops": cfg.get("hops", 0), "chain": cfg.get("chain"),
  "changed_files": cfg.get("changed_files", []),
  "reasoning": {"level": "L20", "level_semantics": "LEGACY DISCOVERY SLOT ONLY (storage directory name required by the frozen harness)", "changed_node": f"{G['class']}#{G['method']}"},
  "artifacts": {"manifest": "variant_manifest.json", "variant_patch": "variant.patch", "test_patch": "test.patch", "validation": "validation.json", "non_canonical_notice": "NON_CANONICAL.md"},
  "artifact_hashes": {"variant.patch": h(f"{pkg}/variant.patch"), "test.patch": h(f"{pkg}/test.patch")},
  "validation_summary": {"overall": val["overall"], "gates": [[g["gate"], g["status"]] for g in val["gates"]], "validated_at": val["finished_at"]},
  "provenance": {"toolchain": {"defects4j": "v3.0.1", "jdk": "OpenJDK 11.0.30"}, "note": "gold defined before any model run; no post-hoc gold changes"},
  "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
json.dump(man, open(f"{pkg}/variant_manifest.json", "w"), indent=1)
vj = {"schema_version": "d4j-validation/v1", "variant_id": V, "status": "accepted", "accepted": True, "non_canonical": True, "validator_version": "adversarial-break-v1/validate_attack.py",
      "validated_at": val["finished_at"], "gate": {g["gate"]: {"status": g["status"], "name": g["name"]} for g in val["gates"]},
      "trigger_runs": val["trigger_runs"], "baseline_full_suite_failures": val.get("baseline_full_suite_failures"), "buggy_full_suite_failures": val.get("buggy_full_suite_failures")}
json.dump(vj, open(f"{pkg}/validation.json", "w"), indent=1)
open(f"{pkg}/NON_CANONICAL.md", "w").write(f"""# NON-CANONICAL ADVERSARIAL VARIANT - {V}

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base {cfg['project']}-1f. Gold `{G['class']}#{G['method']}` ({G['file']}). Trigger `{cfg['trigger']}`.
Attack {cfg.get('attack_id')}: {cfg.get('title')}. Classification: {cfg.get('classification')}.
""")
dst = f"{R}/new_bug_variants/{cfg['project']}/bug-1/L20/{V}"
assert not os.path.exists(dst), dst
os.makedirs(dst)
for f in ("variant.patch", "test.patch", "variant_manifest.json", "validation.json", "NON_CANONICAL.md"): shutil.copyfile(f"{pkg}/{f}", f"{dst}/{f}")
print("installed", V, "->", dst.split("adversarial-break-v1/")[1], "| gold", man["reasoning"]["changed_node"])
