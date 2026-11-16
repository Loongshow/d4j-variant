#!/usr/bin/env python
"""Freeze: BENCHMARK_MANIFEST.json with every installed variant's hashes, gold, trigger, ownership, plus prompt/protocol identity.
Usage: freeze_benchmark.py   (refuses to overwrite an existing manifest unless --refreeze-before-runs is given)"""
import json, glob, os, hashlib, sys, datetime
O = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"; out = f"{O}/BENCHMARK_MANIFEST.json"
if os.path.exists(out) and "--refreeze-before-runs" not in sys.argv: raise SystemExit("manifest exists; frozen")
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
ready = json.load(open(f"{O}/review/ready_pairs.json")); pairs = {}
for pj in sorted(glob.glob(f"{O}/projects/*/bug-*/pair.json")):
    s = json.load(open(pj))
    if s["pair_id"] not in ready: continue
    v = json.load(open(f"{s['pair_dir']}/validation/validation.json"))
    arms = {}
    for arm, A in s["arms"].items():
        d = f"{O}/new_bug_variants/{s['project']}/bug-1/L20/{A['variant_id']}"
        arms[arm] = {"variant_id": A["variant_id"], "gold_role": A["gold_role"], "gold": f"{A['gold']['class']}#{A['gold']['method']}", "gold_file": A["gold"]["file"], "bug_line": A["gold"]["bug_line"], "orig_line": A["gold"]["orig_line"],
                     "ownership": v["arms"][arm]["ownership"], "declared_collateral": A.get("declared_collateral") or [], "signature": v["arms"][arm]["trigger_runs"][0]["signature"],
                     "hashes": {f: h(f"{d}/{f}") for f in ("variant.patch", "test.patch", "variant_manifest.json", "validation.json")}}
    bv = json.load(open(f"{s['pair_dir']}/blindness/verdicts.json"))
    pairs[s["pair_id"]] = {"project": s["project"], "bug": s["bug"], "family": s["family"], "level": "B", "converted_from": s.get("converted_from"), "seed_variant": s.get("seed_variant"), "trigger": s["trigger"], "pin_test": s["pin_test"], "second_caller": s.get("second_caller"), "external_evidence_tests": s.get("external_evidence_tests"), "local_blindness": bv,
                           "chain": {r: f"{s['chain'][r]['class']}#{s['chain'][r]['method']}" for r in ("facade", "H1", "H2", "H3", "H4", "H5")}, "arms": arms, "validation_overall": v["overall"], "validated_at": v["finished_at"]}
# pre-registered Opus subset (review/OPUS_SUBSET.md): first READY pair per slot
SLOTS = [["LB-CHART-01"], ["LB-COMPRESS-07", "LB-LANG-03"], ["LB-MATH-05", "LB-LANG-04"]]   # three representative pairs for Opus (review/OPUS_SUBSET.md): sign, units/bytes, scale/representation; one project per slot where READY
opus_subset = []
for slot in SLOTS:
    pick = next((p for p in slot if p in pairs and p not in opus_subset), None)
    if pick: opus_subset.append(pick)
agents = json.load(open(f"{O}/models/sonnetA/benchmark_runs/agents.json")) if os.path.exists(f"{O}/models/sonnetA/benchmark_runs/agents.json") else {}
man = {"benchmark": "OCFLB Level B v1 (globally unique, locally ambiguous ownership)", "label": "NON-CANONICAL RESEARCH BENCHMARK - pending human review", "frozen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "pairs": pairs, "n_pairs": len(pairs), "n_variants": 2 * len(pairs), "opus_subset": opus_subset, "opus_subset_rule": "review/OPUS_SUBSET.md (fixed before any Sonnet result was read)",
       "protocol": {"prompt": "d4j-localization-only/v2", "base_prompt_sha256": "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89", "max_tool_calls": 50, "max_test_runs": 5, "timeout_seconds": 300, "agent_id": "mini-swe-claude",
                    "runner": "PERL5LIB exported in every server (defects4j test executes for the agent; proof in review/RUNNER_ENV_PROOF_*.md)", "models": {"primary": "claude-sonnet-4-6", "secondary": "claude-opus-5-5"}},
       "rules": ["gold, roles, pin and compensating repairs fixed in pair.json before any run", "no scientific modification after the first paid run", "provider stalls (uniform rule) excluded and topped up; no-answers counted as behavioural outcomes"],
       "sha256_of_this_manifest_excluding_itself": None}
body = json.dumps({k: v for k, v in man.items() if k != "sha256_of_this_manifest_excluding_itself"}, sort_keys=True).encode(); man["sha256_of_this_manifest_excluding_itself"] = hashlib.sha256(body).hexdigest()
json.dump(man, open(out, "w"), indent=1); json.dump({"frozen_at": man["frozen_at"], "protocol": man["protocol"], "n_pairs": man["n_pairs"], "n_variants": man["n_variants"], "opus_subset": man["opus_subset"], "package_hashes": {p: {a: v["hashes"] for a, v in P["arms"].items()} for p, P in pairs.items()}, "golds": {p: {a: v["gold"] for a, v in P["arms"].items()} for p, P in pairs.items()}, "triggers": {p: P["trigger"] for p, P in pairs.items()}, "ownership": {p: {a: v["ownership"] for a, v in P["arms"].items()} for p, P in pairs.items()}, "local_blindness": {p: P["local_blindness"] for p, P in pairs.items()}, "manifest_sha256": man["sha256_of_this_manifest_excluding_itself"]}, open(f"{O}/FREEZE_MANIFEST.json", "w"), indent=1); print("frozen", man["n_pairs"], "pairs", man["n_variants"], "variants", man["sha256_of_this_manifest_excluding_itself"][:16])
