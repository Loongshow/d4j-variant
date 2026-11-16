#!/usr/bin/env python
"""MASTER_MANIFEST.json + README.md for camouflage-model-comparison-v1. Usage: build_manifest_camo.py"""
import json, os, hashlib, glob, datetime

SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
R = f"{SP}/camouflage-model-comparison-v1"; A = f"{R}/experiment-a-camouflage"
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
cam = json.load(open(f"{A}/results/camouflage_results.json")) if os.path.exists(f"{A}/results/camouflage_results.json") else {}
inst = json.load(open(f"{A}/install/INSTALL_REPORT.json"))
variants = []
for rec in inst["installed"]:
    V = rec["variant_id"]; pkg = f"{A}/construction/packages/{V}"
    m = json.load(open(f"{pkg}/variant_manifest.json"))
    variants.append({"variant_id": V, "project": rec["project"], "pair_id": m["pair_id"], "arm": m["arm"],
                     "gold": m["fault"]["gold"]["faulty_class"] + "#" + m["fault"]["gold"]["faulty_method"],
                     "gold_host_file": m["fault"]["locations"][0]["file"],
                     "host_metrics": m["camouflage"]["host_metrics"],
                     "trigger": m["trigger"]["test_id"], "hops": m["synthetic_call_hops"],
                     "installed_at": rec["installed_at"].split("supervisor_pipeline_runs/")[1],
                     "artifact_hashes": m["artifact_hashes"], "benchmark_eligible": m["benchmark_eligible"]})
man = {
 "schema_version": "camouflage-model-comparison-v1/master-manifest/v1",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "root": "supervisor_pipeline_runs/camouflage-model-comparison-v1",
 "purpose": ("one continuous task with three experiments: A controlled large-file camouflage (executed), "
             "B GPT model-strength comparison (blocked), C Anthropic cross-model replication (blocked)"),
 "protocol": {"server": "diagnostic-noncanonical-v3 (port 8792, frozen)", "agent": "mini-swe-agent-openai-gpt-5-6",
              "model": "gpt-5.6", "prompt": "d4j-localization-only/v2",
              "base_prompt_sha256": "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89",
              "budget": {"max_tool_calls": 50, "max_test_runs": 5, "timeout_seconds": 300, "startup_timeout_seconds": 30},
              "runs_per_arm": 5, "one_run_per_launch": True, "scoring": "exact FQCN::method"},
 "experiments": {
   "A": {"status": "PARTIALLY_EXECUTED_BLOCKED_PROVIDER_QUOTA", "planned_runs": 30, "pairs": list((cam.get("pairs") or {}).keys()),
         "runs_attempted": (cam.get("block") or {}).get("runs_attempted"),
         "runs_completed": (cam.get("block") or {}).get("runs_completed"),
         "infrastructure_affected": (cam.get("block") or {}).get("infrastructure_affected"),
         "cost_usd": (cam.get("block") or {}).get("total_cost_usd")},
   "B": {"status": "BLOCKED_MODEL_AVAILABILITY", "runs": 0, "cost_usd": 0.0},
   "C": {"status": "BLOCKED_ADAPTER_SUPPORT", "runs": 0, "cost_usd": 0.0, "comparability": "NOT_COMPARABLE"}},
 "variants": variants,
 "deliverables": sorted(os.path.relpath(p, R) for p in
    glob.glob(f"{R}/**/*.md", recursive=True) + glob.glob(f"{R}/**/*.json", recursive=True)
    if "/construction/checkouts/" not in p and "/repro/" not in p and "/workspace" not in p
    and "/build/" not in p and "/equivalence/" not in p),
 "scripts": sorted(os.path.basename(p) for p in glob.glob(f"{R}/scripts/*")),
 "script_hashes": {os.path.basename(p): h(p) for p in sorted(glob.glob(f"{R}/scripts/*"))},
 "protected_trees": {"never_modified": [
    "supervisor_pipeline_runs/core-benchmark-scaleup-v1", "supervisor_pipeline_runs/core-benchmark-scaleup-v2",
    "supervisor_pipeline_runs/multi-project-five-hop-v1", "supervisor_pipeline_runs/conversion-long-chain-v1",
    "supervisor_pipeline_runs/hypothesis-ambiguity-v1", "Desktop/Honours/thesis (supervisor generator)",
    "defects4j/new_bug_variants (canonical)", "defects4j/benchmark_runs (canonical)"],
   "additive_only": ["diagnostic-noncanonical-v3/new_bug_variants/<project>/bug-1/L20/<six new variants>",
                     "diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6/<six new variants>"]},
}
json.dump(man, open(f"{R}/MASTER_MANIFEST.json", "w"), indent=1)

readme = f"""# camouflage-model-comparison-v1

One continuous research task with three experiments, run on 2026-09-25 against the frozen Variant Lab
server `diagnostic-noncanonical-v3` (port 8792) with the frozen GPT-5.6 localization protocol.

| Experiment | Question | Status |
|---|---|---|
| **A** controlled large-file camouflage | does the gold's host environment change localization behaviour when structural distance and the semantic fault are held fixed? | **built and validated in full; paid block BLOCKED_PROVIDER_QUOTA after 2 of 30 slots** ({(cam.get('block') or {}).get('runs_completed', '?')} of {(cam.get('block') or {}).get('runs_attempted', '?')} attempted slots completed, {(cam.get('block') or {}).get('total_cost_usd', '?')} USD) |
| **B** GPT model strength | is the benchmark's difficulty specific to GPT-5.6? | **BLOCKED_MODEL_AVAILABILITY** (the harness pins the OpenAI model to the server environment) |
| **C** Anthropic replication | does a Claude model behave the same way? | **BLOCKED_ADAPTER_SUPPORT** (credential present, adapter declares anthropic unsupported) |

## Start here

- `supervisor-recipe-audit/SUPERVISOR_RECIPE_AUDIT.md` - what the supervisor generator actually does, read
  from source, including the settled answer on "similar surrounding method names" (it is **not** in the recipe).
- `experiment-a-camouflage/review/CAMOUFLAGE_METRICS.md` - the metric definitions and the measured LOW/HIGH separation.
- `experiment-a-camouflage/review/CAMOUFLAGE_AUDIT.md` - proof that the arms differ only in the gold's host.
- `experiment-a-camouflage/review/OWNERSHIP_AUDIT.md` - behavioural and contractual ownership.
- `experiment-a-camouflage/review/READINESS.md` - A-R1..A-R13.
- `experiment-a-camouflage/results/CAMOUFLAGE_RESULTS.md` - the run results and Master Table 1.
- `combined-analysis/` - MASTER_RESULTS, CROSS_MODEL_TABLES, SEARCH_STRATEGY_AUDIT, DEPTH_PRIOR_ANALYSIS,
  THESIS_IMPLICATIONS, NEXT_EXPERIMENT_DECISION, and the two blocked-experiment records.

## The manipulation in one sentence

For each of three well-understood semantic faults, the same five-hop chain with the same trigger, the same
failure and a byte-identical gold method body was built twice, differing only in which existing production
class hosts the gold: a small sparse class (LOW) or a large method-dense class (HIGH) that clears the
supervisor recipe's own >= 1500-line host threshold.

## Reproduction

Construction is deterministic: `scripts/build_camouflage_variant.py` re-derives each arm from the
already-validated historical patch of the same fault. Validation, fresh reproduction, the five-state
equivalence probe, the camouflage audit and the ownership counterfactual all run from the scripts in
`scripts/`; `MASTER_MANIFEST.json` records their hashes and the six package hashes.
"""
open(f"{R}/README.md", "w").write(readme)
print("wrote MASTER_MANIFEST.json (", len(variants), "variants,", len(man["deliverables"]), "deliverables ) and README.md")
