#!/usr/bin/env python
"""EXPERIMENT_MANIFEST.json + README.md for anthropic-pilot-v1. Usage: build_pilot_manifest.py"""
import json, os, glob, hashlib, datetime

SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
R = f"{SP}/anthropic-pilot-v1"
res = json.load(open(f"{R}/claude_pilot_results.json"))
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
b = res["block"]
man = {
 "schema_version": "anthropic-pilot-v1/manifest/v1",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "root": "supervisor_pipeline_runs/anthropic-pilot-v1",
 "purpose": ("add legitimate Anthropic support to the benchmark harness, verify protocol comparability against "
             "the frozen GPT-5.6 setup, and run a small Claude pilot on frozen benchmark instances"),
 "adapter": {
   "strategy": "isolated copy of the frozen harness, patched; the frozen tree is never edited",
   "patch": "diagnostic/anthropic_adapter.patch",
   "files_changed": ["variant-lab/server/agents/providerConfig.mjs", "variant-lab/server/agents/miniSweAgentAdapter.mjs"],
   "edits": 4,
   "patch_sha256": h(f"{R}/diagnostic/anthropic_adapter.patch"),
   "openai_regression_check": "node --test server/__tests__/*.test.mjs on both trees: 198 tests, 197 pass, 1 pre-existing fail, identical per-test outcomes",
 },
 "protocol": {
   "server": "isolated patched copy on port 8793, repoRoot anthropic-pilot-v1",
   "agent": "mini-swe-claude", "framework": "mini-swe-agent 2.4.6", "provider": "anthropic",
   "model": "claude-opus-5-5", "runtime_model_string": "anthropic/claude-opus-5-5",
   "endpoint": "https://api.anthropic.com (pinned by the launcher)",
   "credential_source_name": "ANTHROPIC_API_KEY",
   "prompt": "d4j-localization-only/v2",
   "base_prompt_sha256": "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89",
   "budget": {"max_tool_calls": 50, "max_test_runs": 5, "timeout_seconds": 300, "startup_timeout_seconds": 30},
   "runs_per_arm": 3, "one_run_per_launch": True, "scoring": "exact FQCN::method",
   "comparability_verdict": "NEAR_EQUIVALENT",
 },
 "panel": [
   {"unit": "CONVERSION-LONG-01", "project": "Lang", "purpose": "stable long-chain baseline",
    "arms": ["CONVERSION-LONG-CONTROL-01", "CONVERSION-LONG-TREATMENT-01"]},
   {"unit": "CHART-PIE-03", "project": "Chart", "purpose": "GPT-5.6 ownership/rank degradation case",
    "arms": ["CHART-PIE-CONTROL-03", "CHART-PIE-TREATMENT-03"]},
   {"unit": "CMP-LAYOUT-02", "project": "Compress", "purpose": "occasional alternate-owner case",
    "arms": ["CMP-LAYOUT-CONTROL-02", "CMP-LAYOUT-TREATMENT-02"]},
   {"unit": "LANG-CONV-CAMO", "project": "Lang", "purpose": "host-density sensitivity (strongest validated camouflage pair)",
    "arms": ["LANG-CONV-CAMOUFLAGE-LOW", "LANG-CONV-CAMOUFLAGE-HIGH"]},
 ],
 "results_summary": b,
 "per_arm": res["per_arm"],
 "gpt56_reference": {"source": "frozen run artifacts under diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6",
                     "rerun": False, "runs_measured": b.get("gpt_reference_runs"),
                     "note": "re-measured with the same provider-independent script used for Claude"},
 "integrity": {"frozen_server_tree_files": 32, "frozen_run_artifacts": 4003, "variant_package_files": 218,
               "all_verified_unchanged_after_block": True,
               "incidents": ["diagnostic/INCIDENT_frozen_server_process.md"]},
 "scripts": {os.path.basename(p): h(p) for p in sorted(glob.glob(f"{R}/scripts/*"))},
 "deliverables": sorted(os.path.relpath(p, R) for p in glob.glob(f"{R}/*.md") + glob.glob(f"{R}/*.json")),
 "never_modified": ["any benchmark bug, trigger or gold definition", "any historical run",
                    "the frozen server code tree", "the canonical new_bug_variants tree",
                    "the installed mini-swe-agent or litellm packages", "the supervisor generator"],
}
json.dump(man, open(f"{R}/EXPERIMENT_MANIFEST.json", "w"), indent=1)

pa = res["per_arm"]
def row(unit, arm):
    c = pa.get(f"claude-opus-5-5|{unit}|{arm}", {}); g = pa.get(f"gpt-5.6|{unit}|{arm}", {})
    fmt = lambda v, k: ("-" if v.get(k) is None else v[k])
    return (f"| `{unit}` | {arm} | {fmt(c,'gold_ranks')} | {fmt(c,'tool_calls')} | {fmt(c,'first_gold')} | "
            f"{fmt(g,'gold_ranks')} | {fmt(g,'tool_calls')} | {fmt(g,'first_gold')} |")

readme = f"""# anthropic-pilot-v1

Anthropic support was added to the Defects4J fault-localization benchmark harness, verified against the
frozen GPT-5.6 protocol, and exercised in a small Claude pilot on frozen benchmark instances.

| | |
|---|---|
| Claude model | `claude-opus-5-5` via `anthropic/claude-opus-5-5` |
| Adapter change | 4 edits in 2 files, applied to an **isolated copy** of the harness; the frozen tree is byte-identical |
| OpenAI regression | both trees: 198 tests, 197 pass, 1 pre-existing fail, identical per-test outcomes |
| Protocol comparability | **NEAR_EQUIVALENT** (same prompt hash, tools, budget, timeouts, parser, scoring) |
| Pilot | {b['claude_runs_completed']}/{b['claude_runs_attempted']} runs completed, {b['claude_total_cost_usd']} USD |
| GPT-5.6 | not rerun; re-measured from frozen artifacts with the same script |

## Headline comparison

| Unit | Arm | Claude ranks | Claude tool calls | Claude first gold | GPT-5.6 ranks | GPT-5.6 tool calls | GPT-5.6 first gold |
|---|---|---|---|---|---|---|---|
{row('CONVERSION-LONG-01','CONTROL')}
{row('CONVERSION-LONG-01','TREATMENT')}
{row('CHART-PIE-03','CONTROL')}
{row('CHART-PIE-03','TREATMENT')}
{row('CMP-LAYOUT-02','CONTROL')}
{row('CMP-LAYOUT-02','TREATMENT')}
{row('LANG-CONV-CAMO','LOW')}
{row('LANG-CONV-CAMO','HIGH')}

## Read in this order

1. `ANTHROPIC_ADAPTER_AUDIT.md` - what blocked Anthropic, the four edits, and how non-interference was proven.
2. `ANTHROPIC_MODEL_SELECTION.md` - the 12 models the credential can reach and why `claude-opus-5-5` was frozen.
3. `PROTOCOL_COMPARABILITY.md` - item-by-item protocol comparison and the five residual differences.
4. `SMOKE_TEST.md` - three probes plus one non-panel run, with every Phase 5 check.
5. `CLAUDE_PILOT_RESULTS.md` / `claude_pilot_results.json` - the pilot itself.
6. `GPT56_VS_CLAUDE.md`, `CAMOUFLAGE_CROSS_MODEL.md`, `OWNERSHIP_CROSS_MODEL.md`, `DEPTH_PRIOR_CROSS_MODEL.md`.
7. `CLAUDE_TRAJECTORY_AUDIT.md` - what Claude actually ran, command by command.
8. `INFRASTRUCTURE_ACCOUNTING.md`, `COST_ACCOUNTING.md`, `NEXT_ANTHROPIC_DECISION.md`.

## Isolation

`repoRoot` resolves to this directory, so Claude runs write only here. Variant packages are reached
read-only through a symlink to the frozen root, so both models score byte-identical artifacts. The pilot
server holds no OpenAI credential and cannot execute an OpenAI run. One incident is recorded in
`diagnostic/INCIDENT_frozen_server_process.md`: an over-broad process-kill pattern stopped the user's frozen
GPT-5.6 server process, which the user must restart; no artifact was affected and all three protected trees
verify unchanged.
"""
open(f"{R}/README.md", "w").write(readme)
print("wrote EXPERIMENT_MANIFEST.json and README.md")
