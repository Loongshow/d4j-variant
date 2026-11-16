"""Package and install every cue level of a READY cue-trust-v3 instance. Usage: ct_package.py <spec.json>
Variant IDs are OPAQUE (CTV-<6 hex>) because the server names the agent workspace after the variant ID and prints that path in the
prompt; a readable ID such as CT-CHART-01-CD1 would reveal the condition. The private key VID -> (instance, level, gold, decoys) is
written to review/VARIANT_KEY.json, which never enters any workspace."""
import json, os, sys, hashlib, datetime, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
spec = json.load(open(sys.argv[1])); IID = spec["instance_id"]; B = f"{C.V3}/instances/{IID}/build"
val = json.load(open(f"{C.V3}/instances/{IID}/validation.json")); assert val["overall"] == "READY", val["overall"]
T = spec["trigger"]; TRIG = f"{T['test_class']}::{T['test_method']}"; G = spec["gold"]
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
keyp = f"{C.V3}/review/VARIANT_KEY.json"; key = json.load(open(keyp)) if os.path.exists(keyp) else {}
def vid(level): return "CTV-" + hashlib.sha256(f"cue-trust-v3:{IID}:{level}".encode()).hexdigest()[:6].upper()
for level in C.LEVELS:
    V = vid(level); d = f"{B}/{level}"; lv = val["levels"][level]; sig = lv["trigger_runs"][0]["signature"]
    gates = {f"{g['gate']}{'' if not g['level'] else ':' + g['level']}": {"status": g["status"], "name": g["name"]}
             for g in val["gates"] if g["level"] in (None, level, "C0")}
    man = {"schema_version": "d4j-variant-manifest/v1", "manifest_extension": "cue-trust-v3/manifest/v1", "variant_id": V,
      "status": "non_canonical_validated", "benchmark_eligible": True, "non_canonical": True,
      "label": "NON-CANONICAL RESEARCH BENCHMARK / cue-trust-v3",
      "source": {"defects4j_project": spec["project"], "defects4j_bug_id": 1, "bug_slug": f"{spec['project']}-1", "fixed_revision": "1f"},
      "construction": {"method": "deterministic builder (scripts/ct_lib.py) from a model-assisted design spec; asserted text edits; git diff",
                       "llm_generation_used": False, "design_model_assisted": True, "paid_model_executed": False},
      "semantic_bug": {"family": spec["family"], "buggy_line_text": G["bug_line"], "correct_line_text": G["orig_line"]},
      "trigger": {"test_id": TRIG, "test_class": T["test_class"], "test_method": T["test_method"], "all_empirically_failing_tests": [TRIG], "failure_signature": sig},
      "fault": {"locations": [{"class": G["class"], "method": G["method"], "file": G["file"], "production": True}],
                "gold": {"faulty_class": G["class"], "faulty_method": G["method"]}, "semantic_root_cause": spec["family"]},
      "synthetic_call_hops": 0, "changed_files": spec["prod_files"],
      "reasoning": {"level": "L20", "level_semantics": "LEGACY DISCOVERY SLOT ONLY (storage directory name required by the frozen harness)", "changed_node": f"{G['class']}#{G['method']}"},
      "artifacts": {"manifest": "variant_manifest.json", "variant_patch": "variant.patch", "test_patch": "test.patch", "validation": "validation.json"},
      "artifact_hashes": {"variant.patch": h(f"{d}/variant.patch"), "test.patch": h(f"{d}/test.patch")},
      "validation_summary": {"overall": val["overall"], "validated_at": val["finished_at"]},
      "provenance": {"toolchain": {"defects4j": "v3.0.1", "jdk": "OpenJDK 11.0.30"}},
      "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    vrec = {"schema_version": "d4j-validation/v1", "variant_id": V, "status": "accepted", "accepted": True, "non_canonical": True,
            "validator_version": "cue-trust-v3/ct_validate.py", "validated_at": val["finished_at"], "gate": gates, "trigger_runs": lv["trigger_runs"]}
    dst = f"{C.V3}/new_bug_variants/{spec['project']}/bug-1/L20/{V}"
    if os.path.exists(dst): shutil.rmtree(dst)
    os.makedirs(dst)
    shutil.copyfile(f"{d}/variant.patch", f"{dst}/variant.patch"); shutil.copyfile(f"{d}/test.patch", f"{dst}/test.patch")
    json.dump(man, open(f"{dst}/variant_manifest.json", "w"), indent=1); json.dump(vrec, open(f"{dst}/validation.json", "w"), indent=1)
    key[V] = {"instance_id": IID, "level": level, "cue": spec["levels"][level]["cue"], "project": spec["project"], "stratum": spec["stratum"],
              "gold": f"{G['class']}::{G['method']}", "decoys": [f"{x['class']}::{x['method']}" for x in spec["decoys"]],
              "facade": spec.get("facade", []), "trigger": TRIG, "variant_patch_sha256": man["artifact_hashes"]["variant.patch"],
              "test_patch_sha256": man["artifact_hashes"]["test.patch"]}
    print("installed", V, "=", IID, level)
json.dump(key, open(keyp, "w"), indent=1, sort_keys=True)
