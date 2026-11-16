#!/usr/bin/env python
"""Integrity check after all runs: installed package hashes still equal the frozen manifest; every run's variant is a frozen variant;
protocol identity per run (budget, model, prompt hash when recorded); writes results/INTEGRITY.json and prints a verdict."""
import json, glob, os, hashlib
O = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1"; h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
man = json.load(open(f"{O}/BENCHMARK_MANIFEST.json")); problems = []; checked = 0
frozen_vids = {}
for pid, P in man["pairs"].items():
    for arm, A in P["arms"].items():
        frozen_vids[A["variant_id"]] = (pid, arm); d = f"{O}/new_bug_variants/{P['project']}/bug-1/L20/{A['variant_id']}"
        for f, hv in A["hashes"].items():
            if not os.path.exists(f"{d}/{f}") or h(f"{d}/{f}") != hv: problems.append(f"hash mismatch {A['variant_id']}/{f}")
rows = json.load(open(f"{O}/analysis/per_run/run_metrics.json"))
for r in rows:
    checked += 1
    if r["variant_id"] not in frozen_vids: problems.append(f"run on non-frozen variant {r['variant_id']} {r['server']} {r['run']}")
    rd = f"{O}/models/{r['server']}/benchmark_runs/mini-swe-claude/{r['variant_id']}/{r['run']}"; m = json.load(open(f"{rd}/run_manifest.json"))
    b = m.get("budget") or {}
    if (b.get("max_tool_calls"), b.get("max_test_runs"), b.get("timeout_seconds")) != (50, 5, 300): problems.append(f"budget drift {r['server']} {r['variant_id']} {r['run']}: {b}")
    if m.get("agent", {}).get("model") != r["model_id"]: problems.append(f"model drift {r['server']} {r['run']}")
    ph = (m.get("prompt") or {}).get("base_prompt_sha256") if isinstance(m.get("prompt"), dict) else None
    if ph and ph != man["protocol"]["base_prompt_sha256"]: problems.append(f"prompt drift {r['server']} {r['run']}")
frozen_at = man["frozen_at"]; earliest = min((json.load(open(f"{O}/models/{r['server']}/benchmark_runs/mini-swe-claude/{r['variant_id']}/{r['run']}/run_manifest.json")).get("started_at") or "9") for r in rows) if rows else None
if earliest and earliest != "9" and earliest < frozen_at: problems.append(f"earliest run started {earliest} before the freeze {frozen_at}")
res = {"runs_checked": checked, "frozen_variants": len(frozen_vids), "manifest_frozen_at": frozen_at, "earliest_run_created_at": earliest, "problems": problems, "verdict": "PASS" if not problems else "FAIL",
       "deliverable_hashes": {os.path.basename(p): h(p) for p in sorted(glob.glob(f"{O}/results/*.md") + glob.glob(f"{O}/results/*.csv") + glob.glob(f"{O}/results/*.json")) if not p.endswith("INTEGRITY.json")}}
json.dump(res, open(f"{O}/results/INTEGRITY.json", "w"), indent=1); print("integrity:", res["verdict"], "runs", checked, "problems", problems[:5])
