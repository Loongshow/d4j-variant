"""Install READY counterfactual variants into new_bug_variants (manifest compatible with the harness). Usage: install_cf.py V2 V3 ..."""
import json, sys, os, shutil, hashlib, datetime
D = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-differential-analysis-v1"; h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
for v in sys.argv[1:]:
    pkg = f"{D}/counterfactuals/packages/CF-{v}"; cf = json.load(open(f"{pkg}/cf.json")); val = json.load(open(f"{pkg}/validation.json")); assert val["overall"] == "READY", (v, val["overall"])
    G = cf["gold"]
    man = {"schema_version": "d4j-variant-manifest/v1", "manifest_extension": "ocflb-differential-analysis-v1/manifest/v1", "variant_id": cf["variant_id"], "pair_id": "ADV-DEFINER-01-counterfactuals", "arm": v,
           "status": "non_canonical_validated", "benchmark_eligible": True, "non_canonical": True, "label": "NON-CANONICAL RESEARCH VARIANT / differential counterfactual of ADV-DEFINER-01",
           "source": {"defects4j_project": "Chart", "defects4j_bug_id": 1, "bug_slug": "Chart-1", "fixed_revision": "1f", "baseline_version": "Chart-1f", "parent_variant": cf["parent"]},
           "construction": {"method": "scripts/build_counterfactuals.py (one change vs V0)", "llm_generation_used": False, "paid_model_executed": False}, "counterfactual": {"title": cf["title"], "changes": cf["changes"]},
           "semantic_bug": {"family": "sign / direction", "buggy_line_text": G["bug_line"].strip(), "correct_line_text": G["orig_line"].strip()},
           "trigger": {"test_id": cf["trigger"], "test_class": cf["trigger"].split("::")[0], "test_method": cf["trigger"].split("::")[1], "all_empirically_failing_tests": [cf["trigger"]], "failure_signature": val["signature"]},
           "fault": {"locations": [{"class": G["class"], "method": G["method"], "file": G["file"], "production": True}], "gold": {"faulty_class": G["class"], "faulty_method": G["method"]}, "gold_role": "H3"},
           "chain": {"facade": "org.jfree.chart.plot.PiePlot#getArcBounds", "hop1": {"role": "H1", "class": "org.jfree.chart.plot.CompassPlot", "method": "ring", "holds_bug": False}, "hop2": {"role": "H2-position", "class": "org.jfree.chart.plot.dial.StandardDialScale", "method": "rim", "holds_bug": False},
                     "hop3": {"role": "H2 definer", "class": "org.jfree.chart.plot.PlotUtilities", "method": "drift", "holds_bug": False}, "hop4": {"role": "H3 adapter", "class": "org.jfree.chart.plot.Plot", "method": "nudge", "holds_bug": True}, "hop5": {"role": "H5", "class": "org.jfree.chart.util.ShapeUtilities", "method": "shift", "holds_bug": False}},
           "reasoning": {"level": "L20", "level_semantics": "LEGACY DISCOVERY SLOT ONLY", "changed_node": f"{G['class']}#{G['method']}"},
           "artifacts": {"manifest": "variant_manifest.json", "variant_patch": "variant.patch", "test_patch": "test.patch", "validation": "validation.json", "non_canonical_notice": "NON_CANONICAL.md"},
           "artifact_hashes": {"variant.patch": h(f"{pkg}/variant.patch"), "test.patch": h(f"{pkg}/test.patch")}, "validation_summary": {"overall": val["overall"]}, "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    json.dump(man, open(f"{pkg}/variant_manifest.json", "w"), indent=1); open(f"{pkg}/NON_CANONICAL.md", "w").write(f"# NON-CANONICAL counterfactual {cf['variant_id']}\n\n{cf['title']}\n")
    dst = f"{D}/new_bug_variants/Chart/bug-1/L20/{cf['variant_id']}"; shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
    for f in ("variant.patch", "test.patch", "variant_manifest.json", "validation.json", "NON_CANONICAL.md"): shutil.copyfile(f"{pkg}/{f}", f"{dst}/{f}")
    print("installed", cf["variant_id"])
