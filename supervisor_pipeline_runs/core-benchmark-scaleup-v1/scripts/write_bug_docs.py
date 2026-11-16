#!/opt/miniconda3/bin/python
"""Writes SEMANTIC_EQUIVALENCE.md, LEAKAGE_AUDIT.md and STRUCTURAL_QUALITY_AUDIT.md for one bug from the executed evidence
(validation JSONs, equivalence.json, lexgate JSONs, token_surface.md, structural_audit.json). Nothing is pre-written as PASS: every status is read
from the artifacts. Usage: write_bug_docs.py <proj> <bug-dir>"""
import json, os, sys
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1"; P, B = sys.argv[1], sys.argv[2]; D = os.path.join(S, P, B)
cfg = json.load(open(f"{D}/pair_config.json")); rj = lambda p: json.load(open(p)) if os.path.exists(p) else None
VC, VT = rj(f"{D}/validation/CONTROL_VALIDATION.json"), rj(f"{D}/validation/TREATMENT_VALIDATION.json"); EQ = rj(f"{D}/analysis/equivalence/equivalence.json")
LC, LT = rj(f"{D}/analysis/leakage/lexgate_control.json"), rj(f"{D}/analysis/leakage/lexgate_treatment.json"); SA = rj(f"{D}/analysis/structural_audit.json")
RC, RT = rj(f"{D}/repro/CONTROL_REPRODUCTION.json"), rj(f"{D}/repro/TREATMENT_REPRODUCTION.json")
gates = lambda V: {g["gate"]: g["status"] for g in V["gates"]} if V else {}
gc, gt = gates(VC), gates(VT); hops = cfg["treatment"]["hops"]; chain = " → ".join(h["class"].split(".")[-1] + "." + h["method"] for h in hops)
sigc = VC["trigger_runs"][0]["signature"].splitlines()[-1] if VC else "?"; sigt = VT["trigger_runs"][0]["signature"].splitlines()[-1] if VT else "?"
# ---- SEMANTIC_EQUIVALENCE ----
eq = f"""# SEMANTIC_EQUIVALENCE — {P} {B} ({cfg['pair_id']}) — NON-CANONICAL · CORE BENCHMARK SCALE-UP · NO GPT-5.6 RUNS PERFORMED

| Property | CONTROL `{cfg['control_id']}` | TREATMENT `{cfg['treatment_id']}` | Evidence |
|---|---|---|---|
| Trigger | `{cfg['trigger']}` | same test (byte-identical `test.patch`: `{VC['package_hashes']['test.patch'][:16] if VC else '?'}` = `{VT['package_hashes']['test.patch'][:16] if VT else '?'}`) | package hashes |
| Correct-version behaviour | trigger passes on the original code (gate D {gc.get('D')}) | trigger passes through the correct five-hop chain (gate N {gt.get('N')}); full suite through the correct chain equals the baseline (gate N2 {gt.get('N2')}) | validation JSONs |
| Failure signature | `{sigc}` | `{sigt}` | gates G/H/I: {gc.get('G')}/{gc.get('H')}/{gc.get('I')} and {gt.get('G')}/{gt.get('H')}/{gt.get('I')} (3 identical runs each) |
| Underlying semantic fault | {cfg['semantic_bug']['family']} | the same fault in hop 5 only (gate O {gt.get('O')}); hops 1–4 hold the original arithmetic | `orig_line`/`bug_line` in `pair_config.json` |
| Collateral | baseline + trigger only (gates J/K {gc.get('J')}/{gc.get('K')}) | baseline + trigger only (gates J/K {gt.get('J')}/{gt.get('K')}) | full suites |
| Java probe (four build states) | {EQ['cases'] if EQ else '?'} random + boundary cases: original == correct chain in {EQ['original_equals_correct_chain'] if EQ else '?'}/{EQ['cases'] if EQ else '?'}; CONTROL(buggy) == TREATMENT(buggy) in {EQ['control_buggy_equals_treatment_buggy'] if EQ else '?'}/{EQ['cases'] if EQ else '?'}; the bug changes the output in {EQ['cases_where_bug_changes_output'] if EQ else '?'} cases | `analysis/equivalence/equivalence.json` (probe source and per-state outputs alongside) | overall **{EQ['overall'] if EQ else 'not run'}** |

Method: the equivalence is established by execution, not by reading — (1) the validator swaps the buggy hop-5 line for the original and runs the trigger and the complete existing suite through the chain; (2) the equivalence probe runs the facade on the original checkout, the packaged CONTROL, the packaged TREATMENT and a copy of the TREATMENT with the gold line restored, on identical random and boundary inputs, and compares the printed results line by line (exact string equality of the doubles/ints). The refactoring preserves every arithmetic expression and evaluation order of the original (see `FIVE_HOP_DESIGN.md`), so the doubles are bitwise identical rather than merely close.
"""
open(f"{D}/analysis/SEMANTIC_EQUIVALENCE.md", "w").write(eq)
# ---- LEAKAGE_AUDIT ----
def lex(L):
    if not L: return "not run"
    kr = "; ".join(f"`{k['token']}` ({k['total_hits']} hits{', scannable' if k.get('scannable') else ''})" for k in L.get("keyword_reach", [])) or "none"
    ne = L["name_exposure"]; return f"verdict **{L['verdict']}** — keyword reach into the gold: {kr}; gold method name in payload: {ne['gold_method_in_payload']} (declarations of that name: {ne['declarations_of_that_name']}, identifying: {ne['name_is_identifying']}); gold class in payload: {ne['gold_class_in_payload']}"
ts = open(f"{D}/analysis/leakage/token_surface.md").read() if os.path.exists(f"{D}/analysis/leakage/token_surface.md") else "(token surface not measured)"
lk = f"""# LEAKAGE_AUDIT — {P} {B} ({cfg['pair_id']}) — NON-CANONICAL · CORE BENCHMARK SCALE-UP

lexgate = the unchanged `benchmark_runs/analysis/discriminating-campaign/recipe/lexgate.py`, run on the patched fresh-checkout reproduction states with the agent-visible payload (failing test id, test source, Defects4J failure text; `analysis/leakage/rendered_payload_{{control,treatment}}.txt`).

| Arm | Result |
|---|---|
| CONTROL | {lex(LC)} |
| TREATMENT | {lex(LT)} |

Reading: CONTROL exposure is inherent whenever the payload names the method under test (the gold *is* the facade); TREATMENT must be DECOUPLED — no scannable payload token reaches the hop-5 gold, the gold method and class names are absent from the payload, and no method named in the payload calls the gold directly. Checked surfaces: trigger method name and body, literals, fully-qualified names, type vocabulary, imports, comments/javadocs added by the patches, the failure stack trace (all in the payload), unique hop/gold method names (token surface below) and broad grep shortcuts (lexgate keyword reach with `--max-hits 40`).

## Token surface on the patched states (main sources: hits / files / hits inside the gold; test sources not shown)

{ts}
"""
open(f"{D}/analysis/LEAKAGE_AUDIT.md", "w").write(lk)
# ---- STRUCTURAL_QUALITY_AUDIT ----
rows = "\n".join(f"| {c['check']} | {c['status']} | {c['detail'][:220]} |" for c in SA["checks"]) if SA else "| (not run) | | |"
sq = f"""# STRUCTURAL_QUALITY_AUDIT — {P} {B} ({cfg['pair_id']}) — NON-CANONICAL · CORE BENCHMARK SCALE-UP

Chain: `{cfg['control']['gold_class'].split('.')[-1]}.{cfg['control']['gold_method']}` (facade) → {chain} (gold = hop 5).

| Check (static, on the patched TREATMENT reproduction state) | Status | Detail |
|---|---|---|
{rows}

Dynamic participation: the trigger passes through the correct chain (gate N {gt.get('N')}) and fails only when hop 5 holds the fault (gates G/H {gt.get('G')}/{gt.get('H')}; gate O {gt.get('O')}: the buggy line is physically inside hop 5 and nowhere else). Because every hop's only call to the next hop is inside its own body and the gold is referenced from hop 4 only, hop 5 executing on the trigger implies hops 1–4 executed on the trigger; no hop is dead and no alternative path bypasses hop 5. Validator gates P (wiring + imports) = {gt.get('P')}, Q (no pass-through hops, gold holds the arithmetic) = {gt.get('Q')}. Fresh reproduction of the chain: {RT['overall'] if RT else '?'} (`repro/TREATMENT_REPRODUCTION.json`, step R4 checks the five hops, their order and the bug location again on a fresh checkout); CONTROL reproduction: {RC['overall'] if RC else '?'}. Statement counts per hop: {json.dumps(SA['statement_counts']) if SA else '?'}. Overall: **{SA['overall'] if SA else 'not run'}**.
"""
open(f"{D}/analysis/STRUCTURAL_QUALITY_AUDIT.md", "w").write(sq); print(P, B, "docs:", "equivalence", EQ and EQ["overall"], "| lexgate", LC and LC["verdict"], "/", LT and LT["verdict"], "| structural", SA and SA["overall"])
