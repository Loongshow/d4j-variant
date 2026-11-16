#!/usr/bin/env python
"""Assemble V15/V16 verdicts from grader outputs. Usage: assemble_blindness.py <grader_results.json> <pair_dir>
grader_results.json = list of {packet: "<ARM>_<H2|H3|H2H3>", grader, confidently_identifiable, verdict, named_faulty_hop, confidence_1to5, reasoning_summary}.
Rules: V15 pass iff, for both arms and both single packets (H2, H3), no grader says confidently_identifiable with verdict OWNER for the true gold
(a confident wrong verdict counts as exposure of a misleading cue and is recorded but does not fail V15 by itself: it is flagged);
V16 LOCAL_AMBIGUOUS iff, for both arms, no grader confidently names the true gold from the H2H3 packet."""
import json, sys, os
res = json.load(open(sys.argv[1])); pd = sys.argv[2]; spec = json.load(open(f"{pd}/pair.json"))
gold_of = {arm: spec["arms"][arm]["gold_role"] for arm in spec["arms"]}; meth = {r: spec["chain"][r]["method"] for r in ("H2", "H3")}
v15_fail, v15_flags, v16_fail = [], [], []
for r in res:
    arm, pk = r["packet"].rsplit("_", 1); gold = gold_of[arm]
    if pk in ("H2", "H3"):
        if r["confidently_identifiable"] and r["verdict"] == "OWNER" and pk == gold: v15_fail.append(r)          # the true owner is confidently identified from its own body
        elif r["confidently_identifiable"]: v15_flags.append(r)                                                   # confident but not the true owner (or NOT_OWNER): misleading cue
    else:
        named = (r.get("named_faulty_hop") or "").lower()
        if r["confidently_identifiable"] and r["verdict"] == "OWNER" and meth[gold].lower() in named: v16_fail.append(r)
V15 = "pass" if not v15_fail else "FAIL"; V16 = "LOCAL_AMBIGUOUS" if not v16_fail else "LOCAL_EXPOSED"
out = {"pair_id": spec["pair_id"], "V15": V15, "V16": V16, "v15_exposures": [(r["packet"], r["grader"], r["reasoning_summary"][:200]) for r in v15_fail], "v15_confident_but_not_gold": [(r["packet"], r["grader"], r["verdict"], r["reasoning_summary"][:200]) for r in v15_flags],
       "v16_exposures": [(r["packet"], r["grader"], r["named_faulty_hop"], r["reasoning_summary"][:200]) for r in v16_fail], "n_graders": len(res), "raw": res}
os.makedirs(f"{pd}/blindness", exist_ok=True); json.dump(out, open(f"{pd}/blindness/verdicts.json", "w"), indent=1); print(spec["pair_id"], "V15", V15, "V16", V16, "| exposures", len(v15_fail), "flags", len(v15_flags), "v16 exposures", len(v16_fail))
