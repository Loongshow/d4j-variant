#!/usr/bin/env python
"""Top up the sonnet46 attacks so that each has up to 10 valid (non-stall, non-provider-error) attempts, capped at +6 extra runs per attack.
Sequential, one slot on the sonnet46 server. Usage: topup_valid.py"""
import json, subprocess, glob, os, sys
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1"; PY = "/opt/miniconda3/bin/python"
subprocess.run([PY, f"{R}/scripts/attack_run_metrics.py", f"{R}/analysis/per_run/attack_run_metrics.json"], check=True, capture_output=True)
rows = json.load(open(f"{R}/analysis/per_run/attack_run_metrics.json"))
log = open(f"{R}/diagnostic/topup.log", "a")
for V, target in (("ADV-DEFINER-01", 10), ("ADV-MASK-01", 10), ("ADV-LEX-01", 10), ("ADV-COMPOSITE-01", 10), ("CONVERSION-LONG-TREATMENT-01", 10)):
    rs = [r for r in rows if r["model"] == "sonnet46" and r["variant_id"] == V]
    valid = sum(1 for r in rs if r["status"] not in ("provider_error", "provider_stall")); existing = len(glob.glob(f"{R}/models/sonnet46/benchmark_runs/mini-swe-claude/{V}/run-*"))
    need = min(max(target - valid, 0), 6)
    log.write(f"{V}: existing={existing} valid={valid} -> extra={need}\n"); log.flush()
    if need: subprocess.run([PY, f"{R}/scripts/attack_driver.py", "--model", "sonnet46", "--attacks", V, "--planned", str(existing + need)])
log.write("topup finished\n")
