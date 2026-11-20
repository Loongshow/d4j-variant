"""Rebuild review/VARIANT_KEY.json from every instance spec (re-hosted: reproduction.json must say reproduced; new builds: validation
READY and a packaged variant). Makes key writes race-free when instances are processed in parallel. Usage: mx_rebuild_key.py"""
import json, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
MX = C.V3; key = {}
for sp in sorted(glob.glob(f"{MX}/instances/*/spec.json")):
    d = os.path.dirname(sp); s = json.load(open(sp)); V = s.get("variant_id")
    if not V: continue
    vdir = f"{MX}/new_bug_variants/{s['project']}/bug-1/L20/{V}"
    if not os.path.isdir(vdir): continue
    if s.get("kind") == "rehosted" and not json.load(open(f"{d}/reproduction.json")).get("reproduced"): continue
    if s.get("kind") != "rehosted" and json.load(open(f"{d}/validation.json")).get("overall") != "READY": continue
    man = json.load(open(f"{vdir}/variant_manifest.json"))
    key[V] = {"instance_id": s["iid"], "group": s.get("group"), "mechanism": s.get("mechanism"), "tags": s.get("tags"), "tier": s.get("tier"), "project": s["project"],
              "gold": s["gold"] if isinstance(s["gold"], list) else [f"{s['gold']['class']}::{s['gold']['method']}"],
              "decoys": [x if isinstance(x, str) else f"{x['class']}::{x['method']}" for x in s.get("decoys", [])], "entry_points": s.get("entry_points", []),
              "fault_lines": s.get("fault_lines", []), "evidence": s.get("evidence", []), "expected_signature": s.get("expected_signature"),
              "trigger": s.get("trigger") if isinstance(s.get("trigger"), str) else f"{s['trigger']['test_class']}::{s['trigger']['test_method']}",
              "fresh": f"{MX}/construction/fresh/{s['project']}", "variant_patch_sha256": man["artifact_hashes"]["variant.patch"], "test_patch_sha256": man["artifact_hashes"]["test.patch"]}
json.dump(key, open(f"{MX}/review/VARIANT_KEY.json", "w"), indent=1, sort_keys=True)
print(len(key), "variants in key:", sorted((v["instance_id"], k) for k, v in key.items()))
