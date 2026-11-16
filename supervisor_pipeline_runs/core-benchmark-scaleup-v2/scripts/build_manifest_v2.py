"""Builds SCALEUP_MANIFEST.json and review/BENCHMARK_READINESS_TABLE_V2.md from the per-bug evidence (no LLM, no paid runs).
NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
import json, os, hashlib, datetime
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"; R = os.path.dirname(S)
BUGS = ["projects/Compress/bug-01", "projects/Compress/bug-02", "projects/Compress/bug-03", "projects/JacksonCore/bug-04", "projects/JacksonCore/bug-05", "projects/Compress/bug-06"]
FAMILY = {"CMP-CKSUM-01": "unsigned-byte aggregation", "CMP-LAYOUT-02": "record-layout offset", "CMP-OCTAL-03": "radix / digit width",
          "JKC-SURR-04": "surrogate to code-point unit conversion", "JKC-OFFSET-05": "stream offset convention", "CMP-ALIGN-06": "padding parity / alignment"}
def J(p): return json.load(open(p))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
bugs = []; hashlines = []
for bug in BUGS:
    D = f"{S}/{bug}"; cfg = J(f"{D}/pair_config.json"); eq = J(f"{D}/analysis/equivalence/equivalence.json"); st = J(f"{D}/analysis/structural_audit.json"); ow = J(f"{D}/analysis/ownership_counterfactual.json")
    coh = open(f"{D}/analysis/OWNERSHIP_UNIQUENESS_AUDIT.md").read(); contractual = coh.split("Contractual (judged): ")[1].split("**")[0].strip() if "Contractual (judged): " in coh else None
    arms = {}
    for arm in ("control", "treatment"):
        vid = cfg[f"{arm}_id"]; pk = f"{D}/packages/{vid}"; val = J(f"{D}/validation/{arm.upper()}_VALIDATION.json"); rep = J(f"{D}/repro/{arm.upper()}_REPRODUCTION.json")
        lex = J(f"{D}/analysis/leakage/lexgate_{arm}.json"); A = cfg[arm]
        for f in ("variant.patch", "test.patch", "variant_manifest.json", "validation.json", "NON_CANONICAL.md"):
            if os.path.exists(f"{pk}/{f}"): hashlines.append(f"{sha(f'{pk}/{f}')}  {os.path.relpath(f'{pk}/{f}', S)}")
        arms[vid] = {"arm": arm, "gold": f"{A['gold_class']}#{A['gold_method']}", "synthetic_call_hops": 5 if arm == "treatment" else 0,
                     "chain": None if arm == "control" else " -> ".join([cfg["facade_file"].split("/")[-1][:-5] + "." + cfg["facade_decl"].split("(")[0].split()[-1]] + [h["class"].split(".")[-1] + "." + h["method"] for h in cfg["treatment"]["hops"]]),
                     "package_dir": os.path.relpath(pk, R), "variant_patch_sha256": sha(f"{pk}/variant.patch"), "test_patch_sha256": sha(f"{pk}/test.patch"),
                     "validation": {"overall": val["overall"], "gates": {g["gate"]: g["status"] for g in val["gates"]}}, "reproduction": {"overall": rep.get("overall")},
                     "lexgate": {"verdict": lex.get("verdict")}, "status": "non_canonical_validated", "benchmark_eligible": False, "non_canonical": True, "label": cfg["label"]}
    bugs.append({"bug_id": cfg["pair_id"], "project": cfg["project"], "checkout": cfg["base_version"], "origin": "core-benchmark-scaleup-v2 (new)", "dir": bug,
                 "facade": cfg["facade_file"].split("/")[-1][:-5] + "#" + cfg["facade_decl"].split("(")[0].split()[-1], "fault_family": FAMILY[cfg["pair_id"]],
                 "semantic_bug": cfg["semantic_bug"], "trigger": cfg["trigger"], "failure_signature": cfg["expected_signature"], "arms": arms,
                 "semantic_equivalence": eq, "structural_audit": {"overall": st.get("overall")},
                 "ownership": {"behavioural": ow["classification"], "equivalent_repair_sites": ow["equivalent_repair_sites"], "compensating_repair_sites": ow["compensating_repair_sites"], "contractual": contractual},
                 "docs": {k: f"{bug}/{v}" for k, v in {"spec": "TARGET_SPEC.md", "design": "analysis/FIVE_HOP_DESIGN.md", "equivalence": "analysis/SEMANTIC_EQUIVALENCE.md", "leakage": "analysis/LEAKAGE_AUDIT.md", "coherence": "analysis/LOCAL_COHERENCE_AUDIT.md", "structure": "analysis/STRUCTURAL_QUALITY_AUDIT.md", "ownership": "analysis/OWNERSHIP_UNIQUENESS_AUDIT.md"}.items()},
                 "paid_runs_performed": 0})
open(f"{S}/diagnostic-gpt56/package_hashes.txt", "w").write("\n".join(hashlines) + "\n")
# readiness: R1..R12
rows = []
for b in bugs:
    T = [a for a in b["arms"].values() if a["arm"] == "treatment"][0]; C = [a for a in b["arms"].values() if a["arm"] == "control"][0]
    st = b["structural_audit"]["overall"] == "pass"; eq = b["semantic_equivalence"]["overall"] == "pass"
    r = {"bug": b["bug_id"], "R1 deterministic trigger": C["validation"]["gates"].get("H") == "pass" and C["validation"]["gates"].get("I") == "pass",
         "R2 semantic equivalence": eq, "R3 full-suite validation": C["validation"]["overall"] == "pass" and T["validation"]["overall"] == "pass",
         "R4 fresh reproduction": C["reproduction"]["overall"] == "pass" and T["reproduction"]["overall"] == "pass",
         "R5 five-hop integrity": st and T["validation"]["gates"].get("O") == "pass" and T["validation"]["gates"].get("P") == "pass" and T["validation"]["gates"].get("Q") == "pass",
         "R6 treatment leakage acceptable": T["lexgate"]["verdict"] == "DECOUPLED", "R7 gold locally coherent": os.path.exists(f"{S}/{b['dir']}/analysis/LOCAL_COHERENCE_AUDIT.md"),
         "R8 all hops execute": T["validation"]["gates"].get("N") == "pass" and T["validation"]["gates"].get("P") == "pass",
         "R9 no second bug": T["validation"]["gates"].get("K") == "pass" and C["validation"]["gates"].get("K") == "pass",
         "R10 ownership documented": bool(b["ownership"]["contractual"]), "R11 package hash frozen": bool(T["variant_patch_sha256"]) and bool(C["variant_patch_sha256"]),
         "R12 protocol compatibility": T["validation"]["gates"].get("L") == "pass" and C["validation"]["gates"].get("L") == "pass"}
    r["READY"] = all(v for k, v in r.items() if k.startswith("R")); rows.append(r)
ready = [r for r in rows if r["READY"]]
cost_per_run = 0.19
plan = {"status": "planned", "runs_per_variant": 5, "ready_bugs": len(ready), "planned_runs": 10 * len(ready), "cost_basis_usd_per_completed_run": cost_per_run,
        "estimated_cost_usd": round(10 * len(ready) * cost_per_run, 2), "profile": "mini-swe-agent-openai-gpt-5-6", "prompt": "d4j-localization-only/v2",
        "budget": "50 tool calls / 5 test runs / 300 s / 30 s startup", "rules": ["one slot at a time", "no reruns", "no replacements", "three probes before the block and after any stall", "one probe between slots", "existing benchmark bugs are not rerun"]}
man = {"schema_version": "core-benchmark-scaleup-v2/manifest/v1", "label": "NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6", "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "purpose": "extend the cross-project five-hop benchmark from 8 bugs / 3 projects to 14 bugs / 5 projects by adding two new Defects4J projects",
       "new_projects": ["Compress", "JacksonCore"], "rejected_projects": {"Time": "P3 suite 996 s", "Collections": "P3 suite 1001 s + dense coverage", "JacksonDatabind": "P3 suite 959 s", "Mockito": "P1 compile 978 s / P3 suite 453 s", "Csv": "P6 only 8 source classes", "Cli": "P6 20 classes", "Codec": "P6/P7 relative", "Jsoup": "P6/T6 tokenizer state", "Gson": "P5/P6 relative", "JxPath": "P7 family concentration (best deferred alternative)", "Closure": "P1/P3 by inspection", "JacksonXml": "P4/P6 thin layer"},
       "bugs_new": len(bugs), "bugs_existing": 8, "bugs_total": 8 + len(bugs), "variants_new": 2 * len(bugs), "variants_total": 16 + 2 * len(bugs),
       "fault_families_new": sorted(set(FAMILY.values())), "bugs": bugs, "readiness": rows, "paid_run_plan": plan,
       "must_not": ["rerun the existing eight bugs", "modify variants, triggers, semantic faults, gold, model, prompt, tool budget or run count after freeze", "replace consumed slots", "tune per project or per bug"],
       "existing_benchmark_source": {"results": "core-benchmark-scaleup-v1/results-gpt56/scaleup_gpt56_results.json", "tables": "core-benchmark-scaleup-v1/results-gpt56/FINAL_8_BUG_BENCHMARK_RESULTS.md"}}
json.dump(man, open(f"{S}/SCALEUP_MANIFEST.json", "w"), indent=1)
L = ["# BENCHMARK_READINESS_TABLE_V2 — NON-CANONICAL · CORE BENCHMARK SCALE-UP V2 · GPT-5.6", "",
     f"Generated {man['created_at']} by `scripts/build_manifest_v2.py` from the per-bug evidence. `READY` means every gate R1–R12 passed; no paid run has been launched for any bug below.", "",
     "| Bug | Project | Family | R1 trigger | R2 equivalence | R3 validation | R4 repro | R5 five-hop | R6 leakage | R7 coherence | R8 hops execute | R9 no 2nd bug | R10 ownership | R11 hashes | R12 protocol | READY |", "|" + "---|" * 16]
for r in rows:
    b = next(x for x in bugs if x["bug_id"] == r["bug"])
    L.append(f"| `{r['bug']}` | {b['project']} | {b['fault_family']} | " + " | ".join("yes" if r[k] else "**NO**" for k in list(r)[1:-1]) + f" | {'**READY**' if r['READY'] else 'NOT READY'} |")
L += ["", f"Totals: {len(ready)}/{len(rows)} bugs READY ({2*len(ready)} variants). Ownership (behavioural / contractual): " + "; ".join(f"{b['bug_id']} {b['ownership']['behavioural']}/{b['ownership']['contractual']}" for b in bugs) + ".",
      "", "| Bug | CONTROL gold | TREATMENT gold | chain | equivalence cases (bug-changed) | lexgate C/T | trigger | signature |", "|---|---|---|---|---|---|---|---|"]
for b in bugs:
    C = [a for a in b["arms"].values() if a["arm"] == "control"][0]; T = [a for a in b["arms"].values() if a["arm"] == "treatment"][0]
    L.append(f"| `{b['bug_id']}` | `{C['gold'].split('.')[-1]}` | `{T['gold'].split('.')[-1]}` | {T['chain']} | {b['semantic_equivalence']['cases']} ({b['semantic_equivalence']['cases_where_bug_changes_output']}) | {C['lexgate']['verdict']} / {T['lexgate']['verdict']} | `{b['trigger'].split('::')[-1]}` | `{b['failure_signature']}` |")
L += ["", f"Planned paid block: {plan['planned_runs']} runs ({plan['ready_bugs']} bugs × 2 arms × 5) ≈ {plan['estimated_cost_usd']} USD at {cost_per_run} USD per completed run."]
open(f"{S}/review/BENCHMARK_READINESS_TABLE_V2.md", "w").write("\n".join(L) + "\n")
print(f"manifest: {len(bugs)} new bugs, {len(ready)} READY, {2*len(ready)} variants; package hash list {len(hashlines)} entries")
for r in rows:
    if not r["READY"]: print("  NOT READY:", r["bug"], [k for k, v in r.items() if k.startswith("R") and not v])
