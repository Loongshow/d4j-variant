"""Stage B copy of mx_package_new.py (weaker-model-v1): id namespace weaker-model-v1, Stage B manifest extension, hop count and cell
recorded. Install a READY instance (built by stageB_validate.py) under an opaque id and mark its spec. Usage: stageB_package.py <spec.json>
Then run mx_rebuild_key.py. The variant is EXPLORATORY or HELDOUT per spec.tier; it is never modified after its first behavioural run."""
import json, os, sys, hashlib, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
MX = C.V3; sp_path = sys.argv[1]; s = json.load(open(sp_path)); IID = s["iid"]; B = f"{MX}/instances/{IID}/build"
val = json.load(open(f"{MX}/instances/{IID}/validation.json")); assert val.get("overall") == "READY", f"{IID} not READY"
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
V = "CTV-" + hashlib.sha256(f"weaker-model-v1:{IID}".encode()).hexdigest()[:6].upper()
G = s["gold"]; T = s["trigger"]; TRIG = f"{T['test_class']}::{T['test_method']}"
dst = f"{MX}/new_bug_variants/{s['project']}/bug-1/L20/{V}"
if os.path.exists(dst): shutil.rmtree(dst)
os.makedirs(dst)
for p in ("variant.patch", "test.patch"): shutil.copyfile(f"{B}/{p}", f"{dst}/{p}")
man = {"schema_version": "d4j-variant-manifest/v1", "manifest_extension": "weaker-model-v1/stageB/v1", "variant_id": V, "status": "non_canonical_validated",
       "benchmark_eligible": True, "non_canonical": True, "label": "NON-CANONICAL RESEARCH BENCHMARK",
       "source": {"defects4j_project": s["project"], "defects4j_bug_id": 1, "bug_slug": f"{s['project']}-1", "fixed_revision": "1f"},
       "construction": {"method": "deterministic builder (scripts/stageB_spec.py -> stageB_validate.py) from a hand-authored design; chain hosts and insertion anchors drawn by the supervisor recipe (scripts/generator, seed in construction/stageB/designs/host_draws.json)", "llm_generation_used": False, "design_model_assisted": True, "paid_model_executed": False},
       "semantic_bug": {"family": s.get("mechanism"), "buggy_line_text": "\n".join(e["new"] for e in G["edits"]), "correct_line_text": "\n".join(e["old"] for e in G["edits"])},
       "trigger": {"test_id": TRIG, "test_class": T["test_class"], "test_method": T["test_method"], "all_empirically_failing_tests": [TRIG], "failure_signature": val.get("signature", "")},
       "fault": {"locations": [{"class": G["class"], "method": G["method"], "file": G["file"], "production": True}], "gold": {"faulty_class": G["class"], "faulty_method": G["method"]}},
       "synthetic_call_hops": s.get("hops", 0), "stage_b": s.get("stage_b"), "changed_files": sorted({G["file"]} | {e["file"] for e in s.get("context_edits", [])}),
       "reasoning": {"level": "L20", "level_semantics": "LEGACY DISCOVERY SLOT ONLY", "changed_node": f"{G['class']}#{G['method']}"},
       "artifacts": {"manifest": "variant_manifest.json", "variant_patch": "variant.patch", "test_patch": "test.patch", "validation": "validation.json"},
       "artifact_hashes": {"variant.patch": h(f"{dst}/variant.patch"), "test.patch": h(f"{dst}/test.patch")},
       "provenance": {"toolchain": {"defects4j": "v3.0.1", "jdk": "OpenJDK 11.0.30"}}, "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
vrec = {"schema_version": "d4j-validation/v1", "variant_id": V, "status": "accepted", "accepted": True, "non_canonical": True, "validator_version": "weaker-model-v1/stageB_validate.py",
        "validated_at": val.get("finished_at"), "gate": {g["gate"]: {"status": g["status"], "name": g["name"]} for g in val["gates"]}, "trigger_runs": [{"signature": val.get("signature", "")}]}
json.dump(man, open(f"{dst}/variant_manifest.json", "w"), indent=1); json.dump(vrec, open(f"{dst}/validation.json", "w"), indent=1)
s["variant_id"] = V; s["kind"] = "new"
s["fault_lines"] = s.get("fault_lines") or [e["new"].strip() for e in G["edits"]]
s["gold_key"] = f"{G['class']}::{G['method']}"
json.dump(s, open(sp_path, "w"), indent=1)
print("packaged", IID, "->", V)
