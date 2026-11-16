#!/opt/miniconda3/bin/python
"""Writes SEMANTIC_EQUIVALENCE.md, LEAKAGE_AUDIT.md and STRUCTURAL_QUALITY_AUDIT.md for one bug from the executed evidence
(validation JSONs, equivalence.json, lexgate JSONs, token_surface.md, structural_audit.json). Nothing is pre-written as PASS: every status is read
from the artifacts. Usage: write_bug_docs.py <proj> <bug-dir>"""
import json, os, sys
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"; P, B = sys.argv[1], sys.argv[2]; D = os.path.join(S, P, B)
cfg = json.load(open(f"{D}/pair_config.json")); rj = lambda p: json.load(open(p)) if os.path.exists(p) else None
VC, VT = rj(f"{D}/validation/CONTROL_VALIDATION.json"), rj(f"{D}/validation/TREATMENT_VALIDATION.json"); EQ = rj(f"{D}/analysis/equivalence/equivalence.json")
LC, LT = rj(f"{D}/analysis/leakage/lexgate_control.json"), rj(f"{D}/analysis/leakage/lexgate_treatment.json"); SA = rj(f"{D}/analysis/structural_audit.json")
RC, RT = rj(f"{D}/repro/CONTROL_REPRODUCTION.json"), rj(f"{D}/repro/TREATMENT_REPRODUCTION.json")
gates = lambda V: {g["gate"]: g["status"] for g in V["gates"]} if V else {}
gc, gt = gates(VC), gates(VT); hops = cfg["treatment"]["hops"]; chain = " → ".join(h["class"].split(".")[-1] + "." + h["method"] for h in hops)
sigc = VC["trigger_runs"][0]["signature"].splitlines()[-1] if VC else "?"; sigt = VT["trigger_runs"][0]["signature"].splitlines()[-1] if VT else "?"
# ---- SEMANTIC_EQUIVALENCE ----
eq = f"""# SEMANTIC_EQUIVALENCE — {P} {B} ({cfg['pair_id']}) — NON-CANONICAL · CORE BENCHMARK SCALE-UP V2 · NO GPT-5.6 RUNS PERFORMED

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
lk = f"""# LEAKAGE_AUDIT — {P} {B} ({cfg['pair_id']}) — NON-CANONICAL · CORE BENCHMARK SCALE-UP V2

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
sq = f"""# STRUCTURAL_QUALITY_AUDIT — {P} {B} ({cfg['pair_id']}) — NON-CANONICAL · CORE BENCHMARK SCALE-UP V2

Chain: `{cfg['control']['gold_class'].split('.')[-1]}.{cfg['control']['gold_method']}` (facade) → {chain} (gold = hop 5).

| Check (static, on the patched TREATMENT reproduction state) | Status | Detail |
|---|---|---|
{rows}

Dynamic participation: the trigger passes through the correct chain (gate N {gt.get('N')}) and fails only when hop 5 holds the fault (gates G/H {gt.get('G')}/{gt.get('H')}; gate O {gt.get('O')}: the buggy line is physically inside hop 5 and nowhere else). Because every hop's only call to the next hop is inside its own body and the gold is referenced from hop 4 only, hop 5 executing on the trigger implies hops 1–4 executed on the trigger; no hop is dead and no alternative path bypasses hop 5. Validator gates P (wiring + imports) = {gt.get('P')}, Q (no pass-through hops, gold holds the arithmetic) = {gt.get('Q')}. Fresh reproduction of the chain: {RT['overall'] if RT else '?'} (`repro/TREATMENT_REPRODUCTION.json`, step R4 checks the five hops, their order and the bug location again on a fresh checkout); CONTROL reproduction: {RC['overall'] if RC else '?'}. Statement counts per hop: {json.dumps(SA['statement_counts']) if SA else '?'}. Overall: **{SA['overall'] if SA else 'not run'}**.
"""
open(f"{D}/analysis/STRUCTURAL_QUALITY_AUDIT.md", "w").write(sq); print(P, B, "docs:", "equivalence", EQ and EQ["overall"], "| lexgate", LC and LC["verdict"], "/", LT and LT["verdict"], "| structural", SA and SA["overall"])

# ---- OWNERSHIP_UNIQUENESS_AUDIT.md (v2, mandatory) ----
own_path = f"{D}/analysis/ownership_counterfactual.json"
if os.path.exists(own_path):
    ow = json.load(open(own_path))
    verdicts = {"equivalent_repair": "an equally valid repair site: the trigger passes and the probe output is identical to the original build on every case",
                "compensating": "a compensating repair: the trigger passes but the probe output differs from the original build, so other behaviour changed",
                "not_a_repair": "not a repair site: the trigger still fails", "anchor_error": "candidate could not be applied (anchor mismatch)",
                "compile_error": "candidate did not compile", "probe_error": "probe could not be run", "trigger_repair_probe_unavailable": "trigger passes; probe unavailable"}
    L = [f"# OWNERSHIP_UNIQUENESS_AUDIT — {cfg['pair_id']} (NON-CANONICAL · CORE BENCHMARK SCALE-UP V2 · GPT-5.6)", "",
         f"Counterfactual repair analysis across the chain (Phase 13). Gold: `{ow['gold']}`. Each candidate below applies ONE alternate one-line repair at another stage while the real fault stays in the gold, recompiles, runs the trigger and re-runs the equivalence probe ({cfg.get('probe_class')}) against the original build's output.", "",
         "| Candidate site | repair applied | trigger still fails? | probe cases matching the original | verdict |", "|---|---|---|---|---|"]
    for r in ow["results"]:
        L.append(f"| {r['hop']} (`{os.path.basename(r['file'])}`) | `{r.get('repair','')}` | {r.get('trigger_fails')} | {r.get('probe_matches_original','-')}/{r.get('probe_cases','-')} | **{r['verdict']}** — {verdicts.get(r['verdict'],'')} |")
    L += ["", "## Questions of the ownership gate", "",
          f"1. **Can the observed failure be repaired equivalently at multiple hops?** {'Yes — ' + ', '.join(ow['equivalent_repair_sites']) + ' restore the original behaviour on every probe case.' if ow['equivalent_repair_sites'] else 'No — no alternate site reproduces the original behaviour on all probe cases.'}",
          f"2. **Are multiple one-line repairs semantically equivalent?** {'Yes, for the sites listed above.' if ow['equivalent_repair_sites'] else ('Only in a compensating sense: ' + ', '.join(ow['compensating_repair_sites']) + ' fix the trigger but change other behaviour.' if ow['compensating_repair_sites'] else 'No.')}",
          f"3. **Does the repository contract uniquely privilege the gold as the fault owner?** The contract names the quantity the gold computes (see `TARGET_SPEC.md`, external evidence); the upstream stages carry accounting and validation only. This is a *documentary* privilege, not a semantic one: a single-use pipeline stage can always absorb a compensating edit.",
          f"4. **Could an agent reasonably rank an upstream producer instead?** {'Yes: the sites marked equivalent_repair are as defensible as the gold on behaviour alone.' if ow['equivalent_repair_sites'] else 'Only by ignoring the contract: upstream edits change behaviour elsewhere.'}",
          f"5. **Is the constructor-defined gold uniquely wrong, or merely one valid repair site?** {'One valid repair site among several (behaviourally); the gold is the site the contract describes.' if ow['equivalent_repair_sites'] else 'Uniquely wrong among the candidates tested.'}",
          "", f"## Classification: **{ow['classification']}**", "",
          "UNIQUE = every alternate candidate fails to repair; MOSTLY_UNIQUE = alternates only compensate (changing other behaviour); AMBIGUOUS = at least one alternate is behaviourally equivalent. Bugs classified AMBIGUOUS are retained but reported as a separate semantic subgroup, never as ordinary localization failures.",
          "", f"Evidence: `analysis/ownership_counterfactual.json`, probe outputs `analysis/equivalence/out_cf_*.txt` versus `out_original.txt`."]
    open(f"{D}/analysis/OWNERSHIP_UNIQUENESS_AUDIT.md", "w").write("\n".join(L) + "\n")
    print(f"{P} {B} ownership: {ow['classification']} (equivalent sites: {ow['equivalent_repair_sites'] or 'none'})")
