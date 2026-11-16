#!/usr/bin/env python
"""MASTER_MANIFEST.json for adversarial-break-v1: deliverable hashes, run counts per attack x model, spend, servers, rules."""
import json, hashlib, glob, os, collections, datetime
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1"
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
docs = ["ATTACK_IDEA_CATALOG.md", "FAILURE_SURFACE_MODEL.md", "ATTACK_RANKING.md", "TOP5_ATTACKS.md", "SCREENING_RESULTS.md", "CONFIRMATION_RESULTS.md",
        "MAX_DIFFICULTY_RESULTS.md", "MODEL_COMPARISON.md", "FAILURE_TAXONOMY.md", "WHAT_ACTUALLY_BREAKS_LLM_FL.md", "CLEAN_VS_ARTIFACT_ATTACKS.md", "NEXT_STEP.md", "README.md", "VALIDITY_TEST_RUNNER.md", "FINAL_REPORT.md"]
rows = json.load(open(f"{R}/analysis/per_run/attack_run_metrics.json"))
cnt = collections.Counter((r["variant_id"], r["model"]) for r in rows)
spend = collections.defaultdict(float)
for r in rows: spend[r["model"]] += r["cost_usd"] or 0
pk = {}
for aj in sorted(glob.glob(f"{R}/construction/packages/*/attack.json")):
    a = json.load(open(aj)); d = os.path.dirname(aj)
    pk[a["variant_id"]] = {"attack_id": a.get("attack_id"), "project": a.get("project"), "gold": f'{a["gold"]["class"]}#{a["gold"]["method"]}', "classification": a.get("classification"),
                          "files": {os.path.basename(p): sha(p) for p in glob.glob(f"{d}/*") if os.path.isfile(p)}}
m = {"root": R, "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
     "deliverables": {d: {"sha256": sha(f"{R}/{d}"), "bytes": os.path.getsize(f"{R}/{d}")} for d in docs if os.path.exists(f"{R}/{d}")},
     "packages": pk, "runs_per_variant_model": {f"{v}|{mo}": n for (v, mo), n in sorted(cnt.items())}, "total_runs": len(rows),
     "status_counts": dict(collections.Counter(r["status"] for r in rows)), "spend_usd": {k: round(v, 4) for k, v in spend.items()}, "spend_total_usd": round(sum(spend.values()), 4),
     "models": {"opus55": "claude-opus-5-5", "sonnet46": "claude-sonnet-4-6", "haiku45": "claude-haiku-4-5-20251001"},
     "protocol": {"prompt": "d4j-localization-only/v2", "base_prompt_sha256": "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89", "max_tool_calls": 50, "max_test_runs": 5, "timeout_seconds": 300},
     "rules": ["gold and roles fixed in attack.json before any run", "no completed run modified", "provider_error and provider_stall excluded from Acc@1 denominators (diagnostic/PROVIDER_STALL_RULE.md)",
               "timeout with steady work and invalid_ranking at budget = agent exhaustion = miss over all attempts", "one paid slot per server; three fast probes before each block and after each anomaly"],
     "server_stops": open(f"{R}/diagnostic/server_stops.log").read().splitlines() if os.path.exists(f"{R}/diagnostic/server_stops.log") else []}
json.dump(m, open(f"{R}/MASTER_MANIFEST.json", "w"), indent=1); print("manifest:", m["total_runs"], "runs;", m["spend_total_usd"], "USD;", len(m["deliverables"]), "deliverables")
