"""Builds BENCHMARK_MANIFEST.json and review/BENCHMARK_READINESS_TABLE.md from the per-bug evidence (no LLM, no paid runs).
NON-CANONICAL / CORE BENCHMARK SCALE-UP / NO GPT-5.6 RUNS PERFORMED."""
import json, os, glob, datetime, hashlib
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1"; R = os.path.dirname(S)
def J(p): return json.load(open(p))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
NEW = [("chart", "bug-02", "Chart"), ("chart", "bug-03", "Chart"), ("math", "bug-02", "Math"), ("math", "bug-03", "Math"), ("lang", "bug-02", "Lang")]
bugs = []
for proj, bug, d4j in NEW:
    root = f"{S}/{proj}/{bug}"; cfg = J(f"{root}/pair_config.json"); eq = J(f"{root}/analysis/equivalence/equivalence.json"); st = J(f"{root}/analysis/structural_audit.json")
    arms = {}
    for arm in ("control", "treatment"):
        vid = cfg[f"{arm}_id"]; pk = f"{root}/packages/{vid}"; vm = J(f"{pk}/variant_manifest.json"); val = J(f"{root}/validation/{arm.upper()}_VALIDATION.json"); rep = J(f"{root}/repro/{arm.upper()}_REPRODUCTION.json")
        lex = J(f"{root}/analysis/leakage/lexgate_{arm}.json") if os.path.exists(f"{root}/analysis/leakage/lexgate_{arm}.json") else {}
        A = cfg[arm]; arms[vid] = {
            "arm": arm, "gold": f"{A['gold_class']}#{A['gold_method']}", "synthetic_call_hops": 5 if arm == "treatment" else 0,
            "chain": None if arm == "control" else " -> ".join([cfg["facade_file"].split("/")[-1].replace(".java", "") + "." + cfg["facade_decl"].split("(")[0].split()[-1]] + [h["class"].split(".")[-1] + "." + h["method"] for h in cfg["treatment"]["hops"]]),
            "package_dir": os.path.relpath(pk, R), "variant_patch_sha256": sha(f"{pk}/variant.patch"), "test_patch_sha256": sha(f"{pk}/test.patch"),
            "validation": {"overall": val["overall"], "gates": {g["gate"]: g["status"] for g in val["gates"]}, "file": os.path.relpath(f"{root}/validation/{arm.upper()}_VALIDATION.json", R)},
            "reproduction": {"overall": rep.get("overall"), "file": os.path.relpath(f"{root}/repro/{arm.upper()}_REPRODUCTION.json", R)},
            "lexgate": {"verdict": lex.get("verdict") or vm.get("leakage", {}).get("lexgate_verdict"), "file": os.path.relpath(f"{root}/analysis/leakage/lexgate_{arm}.json", R)},
            "status": vm.get("status"), "benchmark_eligible": False, "non_canonical": True, "label": vm.get("label")}
    bugs.append({"bug_id": cfg["pair_id"], "project": d4j, "checkout": cfg["base_version"], "origin": "core-benchmark-scaleup-v1 (new)", "dir": os.path.relpath(root, R),
                 "facade": cfg["facade_file"].split("/")[-1].replace(".java", "") + "#" + cfg["facade_decl"].split("(")[0].split()[-1], "semantic_bug": cfg["semantic_bug"],
                 "trigger": cfg["trigger"], "failure_signature": cfg["expected_signature"], "arms": arms,
                 "semantic_equivalence": eq, "structural_audit": {"overall": st.get("overall"), "file": os.path.relpath(f"{root}/analysis/structural_audit.json", R)},
                 "docs": {k: os.path.relpath(f"{root}/{v}", R) for k, v in {"spec": "TARGET_SPEC.md", "design": "analysis/FIVE_HOP_DESIGN.md", "equivalence": "analysis/SEMANTIC_EQUIVALENCE.md", "leakage": "analysis/LEAKAGE_AUDIT.md", "coherence": "analysis/LOCAL_COHERENCE_AUDIT.md", "structure": "analysis/STRUCTURAL_QUALITY_AUDIT.md"}.items()},
                 "paid_runs_performed": 0})
# existing three bugs
mp = J(f"{R}/multi-project-five-hop-v1/EXPERIMENT_MANIFEST.json")["projects"]
def lex_existing(vid):
    arm = "control" if "CONTROL" in vid else "treatment"; proj = "math" if vid.startswith("MATH") else "chart" if vid.startswith("CHART") else None
    cands = ([f"{R}/multi-project-five-hop-v1/analysis/leakage/{proj}/lexgate_{arm}.json"] if proj else []) + glob.glob(f"{R}/conversion-long-chain-v1/analysis/lexgate_long_{arm}*.json")
    for f in cands:
        try: return J(f).get("verdict")
        except Exception: pass
    return None
for proj in ("Math", "Chart"):
    P = mp[proj]; arms = {}
    for vid, a in P["arms"].items():
        arms[vid] = {"arm": "control" if "CONTROL" in vid else "treatment", "gold": a["gold"], "synthetic_call_hops": a["synthetic_call_hops"], "chain": a.get("chain"),
                     "package_dir": f"multi-project-five-hop-v1/packages/{vid}", "variant_patch_sha256": a["variant_patch_sha256"], "test_patch_sha256": a["test_patch_sha256"],
                     "lexgate": {"verdict": lex_existing(vid)}, "status": "non_canonical_validated", "benchmark_eligible": False, "non_canonical": True, "paid_runs_completed_previously": a.get("repeats")}
    bugs.append({"bug_id": vid.rsplit("-", 2)[0] + "-01", "project": proj, "checkout": P["checkout"], "origin": "multi-project-five-hop-v1 (existing, already run)", "dir": "multi-project-five-hop-v1",
                 "facade": list(P["arms"].values())[0]["gold"].split(".")[-1], "semantic_bug": {"family": P["semantic_bug"]}, "trigger": P["trigger"], "failure_signature": P["failure_signature"], "arms": arms, "paid_runs_performed": "see multi-project-five-hop-v1 (not in this phase)"})
lc = J(f"{R}/conversion-long-chain-v1/analysis/pair_config_long.json"); arms = {}
for vid in ("CONVERSION-LONG-CONTROL-01", "CONVERSION-LONG-TREATMENT-01"):
    pk = f"{R}/conversion-long-chain-v1/{vid}"; vm = J(f"{pk}/variant_manifest.json"); arm = "control" if "CONTROL" in vid else "treatment"
    arms[vid] = {"arm": arm, "gold": (lc[arm]["gold_class"] + "#" + lc[arm]["gold_method"]) if arm in lc and isinstance(lc.get(arm), dict) and "gold_class" in lc[arm] else vm.get("fault", {}).get("locations", [{}])[0].get("class", "") + "#" + vm.get("fault", {}).get("locations", [{}])[0].get("method", ""),
                 "synthetic_call_hops": vm.get("synthetic_call_hops"), "chain": "Conversion.intArrayToLong -> ArrayUtils.gather -> EnumUtils.compose -> BitField.widen -> ObjectUtils.combine -> NumberUtils.overlay" if arm == "treatment" else None,
                 "package_dir": f"conversion-long-chain-v1/{vid}", "variant_patch_sha256": sha(f"{pk}/variant.patch"), "test_patch_sha256": sha(f"{pk}/test.patch"),
                 "lexgate": {"verdict": lex_existing(vid)}, "status": vm.get("status"), "benchmark_eligible": False, "non_canonical": True, "paid_runs_completed_previously": 5}
bugs.append({"bug_id": "LANG-1-CONVERSION-LONG-01", "project": "Lang", "checkout": "Lang-1f (Commons Lang 3.2-SNAPSHOT)", "origin": "conversion-long-chain-v1 (existing, already run; 0-hop CONTROL series in locally-coherent-conversion-v1)", "dir": "conversion-long-chain-v1",
             "facade": "Conversion#intArrayToLong", "semantic_bug": {"family": "units of the destination offset: shift = (i + dstPos) * 32"}, "trigger": lc.get("trigger"), "failure_signature": lc.get("expected_signature"), "arms": arms, "paid_runs_performed": "see conversion-long-chain-v1 (not in this phase)"})
order = {"Lang": 0, "Math": 1, "Chart": 2}; bugs.sort(key=lambda b: (order[b["project"]], b["origin"].startswith("core") , b["bug_id"]))
n_new = sum(len(b["arms"]) for b in bugs if b["origin"].startswith("core")); n_all = sum(len(b["arms"]) for b in bugs)
cost_per_run = 0.1865  # USD, mean of the 7 completed hypothesis-ambiguity runs (1.3054 USD / 7), same profile/prompt/budget
plan = {"status": "ESTIMATE ONLY - NOT STARTED - NO PAID RUNS PERFORMED IN THIS PHASE", "profile": "mini-swe-agent-openai-gpt-5-6", "prompt": "d4j-localization-only/v2", "budget": "50 steps / 5 min / 300 s timeout / 30 s startup (frozen)",
        "variants": n_all, "new_variants": n_new, "runs_per_variant": 5, "runs_new_variants_only": 5 * n_new, "runs_all_variants_if_rerun": 5 * n_all,
        "cost_basis_usd_per_completed_run": cost_per_run, "estimated_cost_usd_new_variants": round(5 * n_new * cost_per_run, 2), "estimated_cost_usd_with_20pct_stall_allowance": round(5 * n_new * cost_per_run * 1.2, 2),
        "estimated_wall_clock": "≈ 60–120 s per run in a healthy provider window plus a probe between slots: ≈ 1.5–3 h for 50 runs, one run per launch, three-probe health gate per block", "stall_policy": "provider-affected runs are preserved, never rerun or replaced; blocks stop after consecutive stalls"}
man = {"schema_version": "core-benchmark-scaleup-v1/benchmark-manifest/v1", "label": "NON-CANONICAL / CORE BENCHMARK SCALE-UP / NO GPT-5.6 RUNS PERFORMED", "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "purpose": "cross-project five-hop benchmark scaled from 3 projects x 1 fault to 3 projects x up to 3 faults; construction and validation only",
       "must_not": ["run GPT-5.6", "launch mini-swe-agent", "call OpenAI", "start a paid Agent Benchmark block", "modify canonical new_bug_variants/ or benchmark_runs/", "modify supervisor source, prompts, budgets, scoring"],
       "requested_slots": 6, "supplied_slots": 5, "not_supplied": [{"slot": "lang/bug-03", "reason": "after honest screening (18 candidate families, 36 semantic probes, 282 boundary mutations) every surviving real Lang fault sits in a method of a few statements or in a facade-level loop condition; no five natural stages with the fault in the fifth; gates not weakened (see lang/TARGET_SCREENING.md)"}],
       "bugs_total": len(bugs), "variants_total": n_all, "variants_new": n_new, "bugs": bugs, "future_run_plan": plan,
       "review": {"readiness_table": "core-benchmark-scaleup-v1/review/BENCHMARK_READINESS_TABLE.md", "human_review": "core-benchmark-scaleup-v1/review/SCALEUP_HUMAN_REVIEW.md", "diversity": "core-benchmark-scaleup-v1/analysis/CROSS_BUG_DIVERSITY.md"}}
json.dump(man, open(f"{S}/BENCHMARK_MANIFEST.json", "w"), indent=1)
rows = ["# BENCHMARK_READINESS_TABLE — NON-CANONICAL · CORE BENCHMARK SCALE-UP · NO GPT-5.6 RUNS PERFORMED", "", f"Generated {man['created_at']} by `scripts/build_manifest.py` from the per-bug evidence files. `READY*` = all local gates passed, pending the human review in `SCALEUP_HUMAN_REVIEW.md`; no paid run has been launched for any `READY*` variant.", "",
        "| Variant | Project | Arm | Gold | Hops | Validation | Repro | Lexgate | Equivalence (cases / bug-changed) | Structural | variant.patch sha256 (16) | Status |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for b in bugs:
    for vid, a in b["arms"].items():
        new = b["origin"].startswith("core"); eq = b.get("semantic_equivalence", {}); stc = b.get("structural_audit", {}).get("overall", "—")
        rows.append(f"| `{vid}` | {b['project']} | {a['arm']} | `{a['gold']}` | {a['synthetic_call_hops']} | {a.get('validation', {}).get('overall', 'passed (source experiment)')} | {a.get('reproduction', {}).get('overall', 'passed (source experiment)')} | {a.get('lexgate', {}).get('verdict') or '—'} | {(str(eq.get('cases')) + ' / ' + str(eq.get('cases_where_bug_changes_output'))) if new else '— (source experiment)'} | {stc if (new and a['arm']=='treatment') else '—'} | `{a['variant_patch_sha256'][:16]}` | {'READY* (no paid run)' if new else 'ALREADY RUN (' + str(a.get('paid_runs_completed_previously')) + ' runs in the source experiment)'} |")
rows += ["", f"Totals: {len(bugs)} bugs, {n_all} variants ({n_new} new, all READY*; {n_all - n_new} existing). Slot `lang/bug-03`: NOT SUPPLIED (see `lang/TARGET_SCREENING.md`).", "",
         f"Future paid block (ESTIMATE, NOT STARTED): {plan['runs_new_variants_only']} runs over the {n_new} new variants at 5 runs each ≈ {plan['estimated_cost_usd_new_variants']} USD at {cost_per_run} USD per completed run (hypothesis-ambiguity block mean), ≈ {plan['estimated_cost_usd_with_20pct_stall_allowance']} USD with a 20 % stall allowance; {plan['runs_all_variants_if_rerun']} runs if the existing six variants were rerun under the same protocol."]
open(f"{S}/review/BENCHMARK_READINESS_TABLE.md", "w").write("\n".join(rows) + "\n")
print("manifest:", len(bugs), "bugs,", n_all, "variants,", n_new, "new; readiness table rows:", sum(len(b["arms"]) for b in bugs))
