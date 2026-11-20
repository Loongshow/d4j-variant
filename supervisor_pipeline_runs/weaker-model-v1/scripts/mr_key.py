"""Main-run copy of stageB_key.py: MR1 reads construction/mainrun/specs; MR2 variants under bug-<bugId>; MR3 the key carries bug_id
(freeze_lib reads it, W6) and fresh = the instance fixture (the scanner's pristine base). Original docstring follows.
Merge packaged Stage B instances into review/VARIANT_KEY.json (mx_rebuild_key.py entry format), keeping existing entries.
Usage: stageB_key.py  (reads construction/stageB/specs/*.json that carry a variant_id and a READY validation)"""
import json, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
WM = C.V3; KEY = f"{WM}/review/VARIANT_KEY.json"; key = json.load(open(KEY)) if os.path.exists(KEY) else {}
added = []
for sp in sorted(glob.glob(f"{WM}/construction/mainrun/specs/*.json")):   # MR1
    s = json.load(open(sp)); V = s.get("variant_id")
    if not V: continue
    vdir = f"{WM}/new_bug_variants/{s['project']}/bug-{int(s['bug_id'])}/L20/{V}"   # MR2
    if not os.path.isdir(vdir) or json.load(open(f"{WM}/instances/{s['iid']}/validation.json")).get("overall") != "READY": continue
    man = json.load(open(f"{vdir}/variant_manifest.json")); G = s["gold"]
    key[V] = {"instance_id": s["iid"], "group": s.get("group"), "mechanism": s.get("mechanism"), "tags": s.get("tags"), "tier": s.get("tier"), "project": s["project"],
              "gold": [f"{G['class']}::{G['method']}"], "decoys": [f"{x['class']}::{x['method']}" for x in s.get("decoys", [])], "entry_points": s.get("entry_points", []),
              "fault_lines": s.get("fault_lines") or [e["new"].strip() for e in G["edits"]], "evidence": s.get("evidence", []), "expected_signature": s.get("expected_signature"),
              "trigger": f"{s['trigger']['test_class']}::{s['trigger']['test_method']}",
              "bug_id": int(s["bug_id"]), "fixture_key": s["fixture_key"], "fresh": os.path.realpath(f"{WM}/construction/fresh-mr/{s['fixture_key']}"), "variant_patch_sha256": man["artifact_hashes"]["variant.patch"], "test_patch_sha256": man["artifact_hashes"]["test.patch"],
              "stage_b": s.get("stage_b")}
    added.append((s["iid"], V))
json.dump(key, open(KEY, "w"), indent=1, sort_keys=True)
print(len(key), "variants in key; main-run entries:", added)
