"""Supplementary-block (run-006..015) and combined n=15 descriptive analysis for CONVERSION-BRANCH-TREATMENT-01.
Inputs: the untouched first-block results (branch_dispatch_results.json, run-001..005) and the analyze_branch.py output for the
supplementary block (--runs 6-15). Re-reads each run's mini-swe-agent.traj.json ONLY for bash commands / tool outputs (full command
text, for the execution/emulation detector) and ranking.json for the submitted evidence chain (agent-reported, unverified).
Never reads reasoning_content / reasoning_items. Blocks stay separately identifiable; n=15 figures are descriptive (no test).
Usage: analyze_branch_supplementary.py <runs_root> <first_block_results.json> <supplementary_analyzer.json> <out.json> <tables.md>
       [--smoke preflight_smoke_supp.json] [--launcher run_branch_supplementary_attach.sh] [--env preflight_env_supp_launch.json]"""
import json, os, re, sys, statistics, argparse, math, hashlib, glob
from collections import Counter
ap = argparse.ArgumentParser(); ap.add_argument("runs_root"); ap.add_argument("first"); ap.add_argument("supp"); ap.add_argument("out"); ap.add_argument("tables")
ap.add_argument("--smoke"); ap.add_argument("--launcher"); ap.add_argument("--env"); ap.add_argument("--first-label", default="original block (run-001..005)"); ap.add_argument("--supp-label", default="supplementary block (run-006..015)"); a = ap.parse_args()
GOLD = "org.apache.commons.lang3.math.NumberUtils::overlay"; FACADE = "org.apache.commons.lang3.Conversion::intArrayToLong"; SELECTOR = "org.apache.commons.lang3.builder.Folding::forWidth"
WRAPPER = "org.apache.commons.lang3.builder.StandardFolding::fold"; ALT = "org.apache.commons.lang3.builder.NarrowFolding::fold"; ABSTRACT = "org.apache.commons.lang3.builder.Folding::fold"
EARLIER = {"org.apache.commons.lang3.ArrayUtils::gather", "org.apache.commons.lang3.EnumUtils::compose", "org.apache.commons.lang3.BitField::widen", "org.apache.commons.lang3.ObjectUtils::combine"}
CATS = ["A. actual gold (NumberUtils#overlay)", "B. facade (Conversion#intArrayToLong)", "C. selector (Folding#forWidth)", "D. abstraction/strategy (Folding#fold)", "E. StandardFolding wrapper", "F. NarrowFolding", "G. earlier chain hop", "H. other"]
def cat_of(top1):
    if top1 is None: return CATS[7]
    if top1 == GOLD: return CATS[0]
    if top1 == FACADE: return CATS[1]
    if top1 == SELECTOR: return CATS[2]
    if top1 == ABSTRACT or top1.split("::")[0].endswith(".builder.Folding"): return CATS[3]
    if top1 == WRAPPER or ".StandardFolding::" in top1: return CATS[4]
    if top1 == ALT or ".NarrowFolding::" in top1: return CATS[5]
    if top1 in EARLIER: return CATS[6]
    return CATS[7]
def strip_cd(c):
    c = c.strip()
    for _ in range(2):
        c = re.sub(r"""^cd\s+(?:'[^']*'|"[^"]*"|\S+)\s*(?:&&|;)\s*""", '', c)
        c = re.sub(r"""^ROOT=(?:'[^']*'|"[^"]*"|\S+)\s*;?\s*(?:cd\s+"?\$ROOT"?\s*(?:&&|;)\s*)?""", '', c)
    return c.replace('$ROOT/', '').replace('"$ROOT"/', '')
def rj(p):
    try: return json.load(open(p))
    except Exception: return None
def load_steps(rdir):
    traj = rj(os.path.join(rdir, "mini-swe-agent.traj.json")) or {}; msgs = traj.get("messages", [])
    outs = {m.get("tool_call_id"): (m.get("content") or "") for m in msgs if m.get("role") == "tool"}; steps = []
    for m in msgs:
        if m.get("role") != "assistant": continue
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or {}; args = fn.get("arguments")
            try: args = json.loads(args) if isinstance(args, str) else (args or {})
            except Exception: args = {}
            if fn.get("name") == "bash": steps.append({"idx": len(steps) + 1, "command": strip_cd(args.get("command", "")), "output": outs.get(tc.get("id"), "")})
    return steps
def exec_evidence(steps, gold_step):
    ev = []
    for s in steps:
        c = s["command"]; k = None
        if re.search(r"\bjavap\b", c) and re.search(r"NumberUtils|overlay", c): k = "javap of the gold class"
        elif re.search(r"\bjavap\b", c): k = "javap (other class)"
        elif re.search(r"\bjshell\b", c) and re.search(r"overlay|NumberUtils", c): k = "jshell on the gold"
        elif re.search(r"\bjshell\b", c): k = "jshell (facade/chain)"
        elif re.search(r"\bpython3?\b|\bperl\b|\bnode\b|\bbc\b|\bawk\b", c) and re.search(r"<<|>>|shift|\*\s*32\b|\*\s*width|0x[0-9A-Fa-f]{4,}", re.sub(r"<<-?\s*'?\w+'?", " ", c)): k = "scripted arithmetic emulation"
        elif re.search(r"\bpython3?\b|\bperl\b|\bbc\b", c) and re.search(r"\bhex\(|printf.*%x|obase", c): k = "value conversion (hex of assertion values)"
        elif re.search(r"\bjavac\b|\bjava\s+-cp\b|\bjava\s+-jar\b", c): k = "scratch Java compile/run"
        if k: ev.append({"step": s["idx"], "kind": k, "after_gold_exposure": bool(gold_step and s["idx"] > gold_step), "command": c[:220]})
    return ev
GOLD_KINDS = {"javap of the gold class", "jshell on the gold", "scripted arithmetic emulation", "scratch Java compile/run"}
def justification(rdir):
    rk = rj(os.path.join(rdir, "ranking.json")) or {}; ch = (rk.get("structured_submission") or {}).get("evidence_chain") or []
    gd = GOLD.replace("::", "."); fd = FACADE.replace("::", ".")
    txt = " ".join((it.get("evidence") or "") + " " + (it.get("inference_summary") or "") for it in ch)
    cands = [c for it in ch for c in (it.get("candidate_methods") or [])]
    gold_defect = bool(re.search(r"overlay[^.]{0,160}(defect|bug|fault|incorrect|wrong|shift|arith|formula|comput|mask|lost|drop)|(defect|bug|fault|incorrect|wrong|shift|arith|formula|comput)[^.]{0,160}overlay", txt, re.I))
    facade_primary = bool(re.search(r"intArrayToLong[^.]{0,200}(primary|entry|tested|public|api|owner|delegat|directly|responsib)|(primary|entry|tested|public|api|owner|delegat|directly|responsib)[^.]{0,200}intArrayToLong", txt, re.I))
    return {"present": bool(ch), "items": len(ch), "gold_named_in_candidates": gd in cands, "facade_named_in_candidates": fd in cands, "gold_text_links_it_to_the_defect": gold_defect, "facade_text_frames_it_as_entry_or_owner": facade_primary,
            "first_item_candidates": (ch[0].get("candidate_methods") if ch else None), "inference_summaries": [(it.get("inference_summary") or "")[:220] for it in ch], "gold_evidence_excerpt": next(((it.get("evidence") or "")[:300] for it in ch if "overlay" in (it.get("evidence") or "")), None), "note": "agent-reported in the submit_fault_localization call; observable but unverified; not hidden reasoning"}
def rank_of(top, key): return next((i + 1 for i, k in enumerate(top) if k == key), None)
def record(r, block):
    rdir = os.path.join(a.runs_root, r["run_id"]); steps = load_steps(rdir); gs = r.get("gold_first_exposed_step"); top = r.get("top10") or []; gr = r.get("gold_rank"); b = r.get("branch") or {}; d = r.get("dispatch") or {}; c = r.get("chain") or {}; i = r.get("info_distance") or {}
    rf, rs, rw, rab, ral = rank_of(top, FACADE), rank_of(top, SELECTOR), rank_of(top, WRAPPER), rank_of(top, ABSTRACT), rank_of(top, ALT); reh = min([rank_of(top, k) for k in EARLIER if rank_of(top, k)] or [None]) if any(rank_of(top, k) for k in EARLIER) else None
    ev = exec_evidence(steps, gs); gold_exec = [e for e in ev if e["kind"] in GOLD_KINDS and e["after_gold_exposure"]]
    inf = b.get("correct_runtime_branch_inferred_observably") or {}
    resolved = bool(d.get("dispatch_resolved")) and d.get("impl_call_first_shown") is not None and not b.get("wrong_branch_followed")
    mode = ("static: selector condition and its input (width = Integer.SIZE) both displayed before the next stage was exposed" if (inf.get("condition_shown_before_resolution") and inf.get("width_source_line_shown_before_resolution")) else ("executed: jshell on the dispatch" if inf.get("executed_selector_or_widen_in_jshell") else ("resolved; mode unclear from observables" if resolved else "not resolved")))
    outr = lambda x: bool(x is not None and (gr is None or x < gr))
    return {"run_id": r["run_id"], "run": r["run_id"].split("/")[1], "block": block, "status": r.get("status"), "gold_rank": gr, "reciprocal_rank": (1.0 / gr) if gr else 0.0, "tool_calls": r.get("tool_call_count"), "api_calls": r.get("api_calls"), "cost_usd": r.get("cost_usd"), "duration_s": round(((r.get("timing") or {}).get("duration_ms") or 0) / 1000), "provider_retry_lines": (r.get("timing") or {}).get("provider_retry_lines"), "timed_out": (r.get("timing") or {}).get("timed_out"), "source_integrity_ok": r.get("source_integrity_ok"),
            "branch_correctly_resolved": resolved, "branch_resolution_mode": mode, "selector_first_shown": b.get("selector_first_shown"), "condition_first_shown": b.get("condition_first_shown"), "width_source_first_shown": b.get("width_source_line_shown"), "calls_spent_resolving": d.get("calls_spent_resolving"), "dispatch_route": d.get("route"),
            "both_implementations_discovered": b.get("both_implementations_discovered"), "both_implementations_inspected": b.get("both_implementations_opened"), "standard_first_shown": b.get("standard_first_shown"), "narrow_first_shown": b.get("narrow_first_shown"), "wrong_branch_inspected_first": b.get("wrong_branch_inspected_first"), "wrong_branch_followed": b.get("wrong_branch_followed"), "backtracking_to_dispatch_layer": b.get("backtracking_occurred"),
            "gold_reached": gs is not None, "first_gold_exposure_step": gs, "gold_exposing_cmd": (r.get("gold_exposing_cmd") or "")[:160], "buggy_line_seen": r.get("buggy_line_first_shown") is not None, "buggy_line_first_shown": r.get("buggy_line_first_shown"), "calls_after_first_gold": i.get("calls_after_first_gold"), "chain_route": c.get("route"), "chain_path": c.get("chain_path"), "lexical_bypass": c.get("lexical_bypass"),
            "gold_executed_or_emulated": bool(gold_exec), "gold_execution_evidence": gold_exec, "all_execution_evidence": ev,
            "facade_contract_evidence_seen": r.get("first_contract_step") is not None, "first_contract_step": r.get("first_contract_step"), "contract_markers_count": i.get("external_contract_retrieval_count"), "contract_markers": {k: v for k, v in (r.get("contract_first_shown") or {}).items() if v}, "contract_markers_after_gold": i.get("contract_markers_after_gold"),
            "rank1": top[0] if top else None, "rank1_class": cat_of(top[0] if top else None), "top5": top[:5], "rank_of_gold": gr, "rank_of_facade": rf, "rank_of_selector": rs, "rank_of_wrapper": rw, "rank_of_abstraction": rab, "rank_of_narrow": ral, "rank_of_best_earlier_hop": reh,
            "facade_outranked_gold": outr(rf), "selector_outranked_gold": outr(rs), "wrapper_outranked_gold": outr(rw), "abstraction_outranked_gold": outr(rab), "narrow_outranked_gold": outr(ral), "earlier_hop_outranked_gold": outr(reh), "selector_or_wrapper_outranked_gold": outr(rs) or outr(rw),
            "discovery_success": gs is not None, "attribution_failure": bool(gs is not None and gr != 1), "observable_justification": justification(rdir), "tests_executed": i.get("tests_executed_count"), "source_files_opened": len(i.get("source_files_opened") or []), "unique_search_queries": i.get("unique_search_queries"), "novel_vocab_events": len(r.get("novel_search_vocabulary") or []), "steps": [{"idx": s["idx"], "command": s["command"][:300]} for s in steps]}
def mm(xs): xs = [x for x in xs if x is not None]; return {"mean": round(statistics.mean(xs), 2), "median": statistics.median(xs), "min": min(xs), "max": max(xs)} if xs else None
def wilson(k, n, z=1.96):
    if not n: return None
    p = k / n; den = 1 + z * z / n; centre = (p + z * z / (2 * n)) / den; half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]
def agg(recs, label):
    n = len(recs); comp = [r for r in recs if r["status"] == "completed"]; ranks = [r["gold_rank"] for r in recs]; cats = Counter(r["rank1_class"] for r in recs)
    cnt = lambda k: sum(1 for r in recs if r.get(k)); rate = lambda k: (cnt(k) / n) if n else None; hit = lambda t: (sum(1 for r in recs if r["gold_rank"] and r["gold_rank"] <= t) / n) if n else None
    dist = Counter("none" if x is None else x for x in ranks)
    out = {"label": label, "n": n, "completed": len(comp), "timeout": sum(1 for r in recs if r["status"] == "timeout"), "other_status": [(r["run_id"], r["status"]) for r in recs if r["status"] not in ("completed", "timeout")], "runs": [r["run"] for r in recs],
           "gold_ranks": ranks, "gold_rank_distribution": {str(k): dist[k] for k in sorted(dist, key=lambda x: (isinstance(x, str), x))}, "acc_at_1": hit(1), "acc_at_3": hit(3), "acc_at_5": hit(5), "acc_at_10": hit(10), "mrr": (sum(r["reciprocal_rank"] for r in recs) / n) if n else None,
           "rank1_classes": {c: cats.get(c, 0) for c in CATS}, "actual_gold_first": cats.get(CATS[0], 0), "actual_gold_first_rate": (cats.get(CATS[0], 0) / n) if n else None, "facade_first": cats.get(CATS[1], 0), "facade_first_rate": (cats.get(CATS[1], 0) / n) if n else None, "facade_first_wilson95_descriptive": wilson(cats.get(CATS[1], 0), n),
           "selector_first": cats.get(CATS[2], 0), "selector_first_rate": (cats.get(CATS[2], 0) / n) if n else None, "abstraction_first": cats.get(CATS[3], 0), "wrapper_first": cats.get(CATS[4], 0), "wrapper_first_rate": (cats.get(CATS[4], 0) / n) if n else None, "narrow_first": cats.get(CATS[5], 0), "earlier_hop_first": cats.get(CATS[6], 0), "other_first": cats.get(CATS[7], 0),
           "discovery_success": cnt("gold_reached"), "discovery_success_rate": rate("gold_reached"), "branch_resolution_success": cnt("branch_correctly_resolved"), "branch_resolution_success_rate": rate("branch_correctly_resolved"), "both_implementations_inspected": cnt("both_implementations_inspected"), "wrong_branch_followed": cnt("wrong_branch_followed"), "wrong_branch_inspected_first": cnt("wrong_branch_inspected_first"),
           "buggy_line_seen": cnt("buggy_line_seen"), "gold_executed_or_emulated": cnt("gold_executed_or_emulated"), "facade_contract_evidence_seen": cnt("facade_contract_evidence_seen"), "facade_outranked_gold": cnt("facade_outranked_gold"), "selector_or_wrapper_outranked_gold": cnt("selector_or_wrapper_outranked_gold"), "facade_runner_up": sum(1 for r in recs if r["rank_of_facade"] == 2), "attribution_failures": cnt("attribution_failure"), "lexical_bypass": cnt("lexical_bypass"),
           "first_gold_exposure": [r["first_gold_exposure_step"] for r in recs], "first_gold_exposure_stats": mm([r["first_gold_exposure_step"] for r in recs]), "buggy_line_first_shown": [r["buggy_line_first_shown"] for r in recs], "calls_after_first_gold": [r["calls_after_first_gold"] for r in recs], "calls_after_first_gold_stats": mm([r["calls_after_first_gold"] for r in recs]),
           "tool_calls": [r["tool_calls"] for r in recs], "tool_calls_stats": mm([r["tool_calls"] for r in recs]), "api_calls": [r["api_calls"] for r in recs], "api_calls_stats": mm([r["api_calls"] for r in recs]), "calls_spent_resolving": [r["calls_spent_resolving"] for r in recs], "calls_spent_resolving_stats": mm([r["calls_spent_resolving"] for r in recs]),
           "costs_usd": [r["cost_usd"] for r in recs], "cost_usd_total": round(sum(r["cost_usd"] or 0 for r in recs), 4), "cost_usd_mean": round(sum(r["cost_usd"] or 0 for r in recs) / n, 4) if n else None, "durations_s": [r["duration_s"] for r in recs], "provider_retry_lines_total": sum(r["provider_retry_lines"] or 0 for r in recs), "source_integrity_ok_all": all(r["source_integrity_ok"] for r in recs) if recs else None,
           "rank_of_facade": [r["rank_of_facade"] for r in recs], "rank_of_selector": [r["rank_of_selector"] for r in recs], "rank_of_wrapper": [r["rank_of_wrapper"] for r in recs], "rank_of_narrow": [r["rank_of_narrow"] for r in recs], "dispatch_routes": dict(Counter(r["dispatch_route"] for r in recs)), "chain_routes": dict(Counter(r["chain_route"] for r in recs)), "branch_resolution_modes": dict(Counter(r["branch_resolution_mode"] for r in recs)), "novel_vocab_events_total": sum(r["novel_vocab_events"] or 0 for r in recs)}
    return out
d1 = json.load(open(a.first)); d2 = json.load(open(a.supp))
recs1 = [record(r, a.first_label) for r in d1["runs"] if r["arm"] == "TREATMENT"]; recs2 = [record(r, a.supp_label) for r in d2["runs"] if r["arm"] == "TREATMENT"]
A1, A2, A12 = agg(recs1, a.first_label), agg(recs2, a.supp_label), agg(recs1 + recs2, "combined n=15 (blocks kept identifiable; descriptive only)")
ff = A12["facade_first"]
if ff >= 3: outcome = {"threshold_3_of_15_reached": True, "classification": "REACHED (facade-first >= 3/15)", "recommendation": "dedicated OWNERSHIP experiment next: manipulate where responsibility appears to reside while holding the semantic fault and the discovery path as constant as possible"}
elif ff == 2: outcome = {"threshold_3_of_15_reached": False, "classification": "AMBIGUOUS (facade-first = 2/15)", "recommendation": "modest replication or a multi-project ownership replication rather than immediately constructing a large new mechanism"}
else: outcome = {"threshold_3_of_15_reached": False, "classification": "NOT REACHED (facade-first 0-1/15)", "recommendation": "treat the earlier rank-2 outcomes as too sparse to justify a dedicated ownership study"}
prov = {"first_block_results_sha256": hashlib.sha256(open(a.first, "rb").read()).hexdigest(), "supplementary_analyzer_json": os.path.basename(a.supp), "runs_root": a.runs_root}
if a.launcher and os.path.exists(a.launcher): prov["launcher_sha256"] = hashlib.sha256(open(a.launcher, "rb").read()).hexdigest()
if a.smoke and os.path.exists(a.smoke):
    sm = rj(a.smoke) or {}; tp = sm.get("trajectory_path"); ms = ((rj(tp) or {}).get("info") or {}).get("model_stats") if tp and os.path.exists(tp) else {}
    prov["smoke"] = {"status": sm.get("status"), "run_id": sm.get("run_id"), "artifact_path": sm.get("artifact_path"), "retry_lines": (sm.get("raw_output") or "").count("Retrying"), "api_calls": (ms or {}).get("api_calls"), "cost_usd": (ms or {}).get("instance_cost")}
if a.env and os.path.exists(a.env):
    en = rj(a.env) or {}; pc = en.get("openai_provider") or {}
    prov["server"] = {"repoRoot": en.get("repoRoot"), "provider": pc.get("provider"), "model": pc.get("model"), "credential_configured": pc.get("credential_configured"), "credential_source_name": pc.get("credential_source")}
out = {"schema_version": "branch-supplementary-results/v1", "label": "NON-CANONICAL / BRANCH-DISPATCH DIAGNOSTIC / GPT-5.6 / SUPPLEMENTARY TREATMENT BLOCK + COMBINED n=15", "variant_id": "CONVERSION-BRANCH-TREATMENT-01", "gold": GOLD,
       "interpretation_rule": "Descriptive replication of one validated variant under the frozen protocol; not an L-level / reasoning-depth estimate; no CONTROL runs; no confirmatory test; the original block (run-001..005) and the supplementary block (run-006..015) are reported separately and then combined descriptively with block tags retained; timeouts (if any) are never treated as localization misses.",
       "rank1_classes_definition": CATS, "preregistered_decision_rule": {"rule": ">= 3/15 facade-first -> dedicated ownership experiment; 2/15 -> ambiguous (modest replication or multi-project ownership replication); 0-1/15 -> too sparse for a dedicated ownership study", "fixed_before_data": True, "facade_first_n15": ff, "outcome": outcome},
       "provenance": prov, "original_block": {"aggregates": A1, "runs": recs1}, "supplementary_block": {"aggregates": A2, "supplementary_analyzer_per_arm": (d2.get("per_arm") or {}).get("BRANCH_TREATMENT"), "runs": recs2}, "combined_n15": {"aggregates": A12, "per_run_index": [{"run": r["run"], "block": r["block"], "gold_rank": r["gold_rank"], "rank1_class": r["rank1_class"]} for r in recs1 + recs2]}}
json.dump(out, open(a.out, "w"), indent=1)
# ---------------- tables ----------------
def f(x, nd=2): return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))
def yn(x): return "yes" if x else "no"
T = []
T += ["## S1. Supplementary block run-006..015 — per-run summary (observable artifacts only)", "", "| Run | Status | Gold rank | Rank-1 | Class | Tool calls | API calls | Cost USD | Duration s | Retries | Gold first exposed | Buggy line shown | Calls after gold | Chain route | Dispatch route |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in recs2: T.append(f"| {r['run']} | {r['status']} | {r['gold_rank']} | `{(r['rank1'] or '-').split('.')[-1]}` | {r['rank1_class'].split('.')[0]} | {r['tool_calls']} | {r['api_calls']} | {f(r['cost_usd'],4)} | {r['duration_s']} | {r['provider_retry_lines']} | {f(r['first_gold_exposure_step'])} | {f(r['buggy_line_first_shown'])} | {f(r['calls_after_first_gold'])} | {(r['chain_route'] or '')[:60]} | {(r['dispatch_route'] or '')[:55]} |")
T += ["", "## S2. Supplementary block — the twelve per-run trajectory requirements", "", "| Run | Branch resolved | Resolution mode | Both impls inspected | Gold reached | First gold step | Buggy line seen (step) | Gold executed/emulated | Facade contract evidence (first step; markers) | Rank-1 | Gold rank | Facade > gold | Selector/wrapper > gold | Justification present |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in recs2:
    ge = "; ".join(sorted({e['kind'] for e in r['gold_execution_evidence']})) or "no"
    T.append(f"| {r['run']} | {yn(r['branch_correctly_resolved'])} | {r['branch_resolution_mode'].split(':')[0]} | {yn(r['both_implementations_inspected'])} | {yn(r['gold_reached'])} | {f(r['first_gold_exposure_step'])} | {yn(r['buggy_line_seen'])} ({f(r['buggy_line_first_shown'])}) | {ge} | {yn(r['facade_contract_evidence_seen'])} ({f(r['first_contract_step'])}; {r['contract_markers_count']}) | `{(r['rank1'] or '-').split('.')[-1]}` | {r['gold_rank']} | {yn(r['facade_outranked_gold'])} | {yn(r['selector_or_wrapper_outranked_gold'])} | {yn(r['observable_justification']['present'])} ({r['observable_justification']['items']} items) |")
T += ["", "## S3. Block aggregates — original vs supplementary vs combined (descriptive; blocks never pooled into a test)", "", "| Metric | Original run-001..005 | Supplementary run-006..015 | Combined n=15 |", "|---|---|---|---|"]
rows = [("Completed / timeout", lambda A: f"{A['completed']} / {A['timeout']}"), ("Gold ranks", lambda A: ", ".join(str(x) for x in A['gold_ranks'])), ("Gold rank distribution", lambda A: "; ".join(f"rank {k}: {v}" for k, v in A['gold_rank_distribution'].items())), ("Acc@1 / @3 / @5 / @10", lambda A: " / ".join(f(A[k]) for k in ("acc_at_1", "acc_at_3", "acc_at_5", "acc_at_10"))), ("MRR", lambda A: f(A['mrr'], 3)),
        ("Actual-gold-first count (rate)", lambda A: f"{A['actual_gold_first']} ({f(A['actual_gold_first_rate'])})"), ("Facade-first count (rate) [Wilson 95 %, descriptive]", lambda A: f"{A['facade_first']} ({f(A['facade_first_rate'])}) [{A['facade_first_wilson95_descriptive'][0]}–{A['facade_first_wilson95_descriptive'][1]}]"), ("Selector-first count (rate)", lambda A: f"{A['selector_first']} ({f(A['selector_first_rate'])})"), ("Wrapper-first count (rate)", lambda A: f"{A['wrapper_first']} ({f(A['wrapper_first_rate'])})"), ("Abstraction / NarrowFolding / earlier-hop / other first", lambda A: f"{A['abstraction_first']} / {A['narrow_first']} / {A['earlier_hop_first']} / {A['other_first']}"),
        ("Discovery success (gold exposed) count (rate)", lambda A: f"{A['discovery_success']} ({f(A['discovery_success_rate'])})"), ("Branch resolution success count (rate)", lambda A: f"{A['branch_resolution_success']} ({f(A['branch_resolution_success_rate'])})"), ("Both implementations inspected / wrong branch inspected first / followed", lambda A: f"{A['both_implementations_inspected']} / {A['wrong_branch_inspected_first']} / {A['wrong_branch_followed']}"), ("Buggy line seen / gold executed or emulated after exposure / facade contract evidence seen", lambda A: f"{A['buggy_line_seen']} / {A['gold_executed_or_emulated']} / {A['facade_contract_evidence_seen']}"),
        ("Facade outranked gold / selector-or-wrapper outranked gold / facade runner-up", lambda A: f"{A['facade_outranked_gold']} / {A['selector_or_wrapper_outranked_gold']} / {A['facade_runner_up']}"), ("First gold exposure: list; mean / median / min–max", lambda A: f"{', '.join(f(x) for x in A['first_gold_exposure'])}; {A['first_gold_exposure_stats']['mean']} / {A['first_gold_exposure_stats']['median']} / {A['first_gold_exposure_stats']['min']}–{A['first_gold_exposure_stats']['max']}" if A['first_gold_exposure_stats'] else "-"),
        ("Tool calls: list; mean / median / max", lambda A: f"{', '.join(f(x) for x in A['tool_calls'])}; {A['tool_calls_stats']['mean']} / {A['tool_calls_stats']['median']} / {A['tool_calls_stats']['max']}"), ("API (model) calls: list; mean", lambda A: f"{', '.join(f(x) for x in A['api_calls'])}; {A['api_calls_stats']['mean']}"), ("Calls spent resolving the dispatch: list; mean", lambda A: f"{', '.join(f(x) for x in A['calls_spent_resolving'])}; {A['calls_spent_resolving_stats']['mean'] if A['calls_spent_resolving_stats'] else '-'}"), ("Calls after first gold: list; mean", lambda A: f"{', '.join(f(x) for x in A['calls_after_first_gold'])}; {A['calls_after_first_gold_stats']['mean'] if A['calls_after_first_gold_stats'] else '-'}"),
        ("Cost USD: total (mean per run)", lambda A: f"{f(A['cost_usd_total'],4)} ({f(A['cost_usd_mean'],4)})"), ("Durations s", lambda A: ", ".join(str(x) for x in A['durations_s'])), ("Provider retry lines / source integrity ok (all)", lambda A: f"{A['provider_retry_lines_total']} / {A['source_integrity_ok_all']}"), ("Rank of facade per run", lambda A: ", ".join(f(x) for x in A['rank_of_facade'])), ("Rank of selector / wrapper / NarrowFolding (per run)", lambda A: f"{', '.join(f(x) for x in A['rank_of_selector'])} / {', '.join(f(x) for x in A['rank_of_wrapper'])} / {', '.join(f(x) for x in A['rank_of_narrow'])}"), ("Dispatch routes", lambda A: "; ".join(f"{k[:45]}: {v}" for k, v in A['dispatch_routes'].items())), ("Branch resolution modes", lambda A: "; ".join(f"{k.split(':')[0]}: {v}" for k, v in A['branch_resolution_modes'].items())), ("Lexical bypass / novel-vocabulary events", lambda A: f"{A['lexical_bypass']} / {A['novel_vocab_events_total']}")]
for lab, g in rows: T.append(f"| {lab} | {g(A1)} | {g(A2)} | {g(A12)} |")
T += ["", "## S4. Rank-1 attribution class per run, all 15 (A actual gold, B facade, C selector, D abstraction, E wrapper, F NarrowFolding, G earlier hop, H other)", "", "| Run | Block | Rank-1 | Class | Gold rank | Facade rank | Selector rank | Wrapper rank | NarrowFolding rank | Discovery | Attribution |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in recs1 + recs2: T.append(f"| {r['run']} | {r['block'].split(' (')[0]} | `{(r['rank1'] or '-').split('.')[-1]}` | {r['rank1_class']} | {r['gold_rank']} | {f(r['rank_of_facade'])} | {f(r['rank_of_selector'])} | {f(r['rank_of_wrapper'])} | {f(r['rank_of_narrow'])} | {'success' if r['discovery_success'] else 'FAIL'} | {'failure' if r['attribution_failure'] else 'correct'} |")
T += ["", "## S5. Supplementary block — branch resolution trace per run", "", "| Run | Selector shown | Condition shown | Width source shown | StandardFolding shown | NarrowFolding shown | Narrow first? | Narrow followed? | Calls spent resolving | Dispatch route | Backtracking | Files opened | Unique searches | Tests run |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in recs2: T.append(f"| {r['run']} | {f(r['selector_first_shown'])} | {f(r['condition_first_shown'])} | {f(r['width_source_first_shown'])} | {f(r['standard_first_shown'])} | {f(r['narrow_first_shown'])} | {yn(r['wrong_branch_inspected_first'])} | {yn(r['wrong_branch_followed'])} | {f(r['calls_spent_resolving'])} | {(r['dispatch_route'] or '')[:50]} | {yn(r['backtracking_to_dispatch_layer'])} | {r['source_files_opened']} | {r['unique_search_queries']} | {r['tests_executed']} |")
T += ["", "## S6. Supplementary block — submitted top-5 per run", "", "| Run | 1 | 2 | 3 | 4 | 5 |", "|---|---|---|---|---|---|"]
for r in recs2: t = r["top5"] + [""] * 5; T.append(f"| {r['run']} | " + " | ".join(f"`{x.split('.')[-1]}`" if x else "-" for x in t[:5]) + " |")
T += ["", "## S7. Supplementary block — execution / emulation evidence and contract markers", "", "| Run | Execution/emulation events (step: kind) | Gold executed/emulated after exposure | Contract markers first shown (step) | New contract markers after gold |", "|---|---|---|---|---|"]
for r in recs2: T.append(f"| {r['run']} | {'; '.join('{}: {}'.format(e['step'], e['kind']) for e in r['all_execution_evidence']) or 'none'} | {yn(r['gold_executed_or_emulated'])} | {', '.join(f'{k} {v}' for k, v in r['contract_markers'].items()) or 'none'} | {', '.join(r['contract_markers_after_gold'] or []) or 'none'} |")
T += ["", "## S8. Supplementary block — observable justification for the final ranking (agent-reported evidence chain in the submission call; unverified)", "", "| Run | Items | Gold in candidates | Gold text linked to the defect | Facade framed as entry/owner | Inference summaries (truncated) |", "|---|---|---|---|---|---|"]
for r in recs2: j = r["observable_justification"]; T.append(f"| {r['run']} | {j['items']} | {yn(j['gold_named_in_candidates'])} | {yn(j['gold_text_links_it_to_the_defect'])} | {yn(j['facade_text_frames_it_as_entry_or_owner'])} | {' ‖ '.join(s[:110] for s in j['inference_summaries'])} |")
open(a.tables, "w").write("\n".join(T) + "\n")
print(json.dumps({"original": {k: A1[k] for k in ("n", "gold_ranks", "acc_at_1", "mrr", "facade_first", "rank1_classes")}, "supplementary": {k: A2[k] for k in ("n", "completed", "timeout", "gold_ranks", "acc_at_1", "mrr", "facade_first", "selector_first", "wrapper_first", "discovery_success", "branch_resolution_success", "gold_executed_or_emulated", "first_gold_exposure_stats", "tool_calls_stats", "api_calls_stats", "cost_usd_total", "rank1_classes")}, "combined_n15": {k: A12[k] for k in ("n", "gold_rank_distribution", "acc_at_1", "mrr", "facade_first", "facade_first_rate", "facade_first_wilson95_descriptive", "selector_first", "wrapper_first", "actual_gold_first", "discovery_success_rate", "branch_resolution_success_rate", "first_gold_exposure_stats", "tool_calls_stats", "api_calls_stats", "cost_usd_total")}, "decision": outcome}, indent=1))
for r in recs2: print(f"{r['run']}: rank {r['gold_rank']} | rank1 {(r['rank1'] or '-').split('.')[-1]} [{r['rank1_class'].split('.')[0]}] | resolved {r['branch_correctly_resolved']} ({r['branch_resolution_mode'].split(':')[0]}) | both impls {r['both_implementations_inspected']} | gold@{r['first_gold_exposure_step']} buggy@{r['buggy_line_first_shown']} | exec {[e['kind'] for e in r['gold_execution_evidence']]} | contract@{r['first_contract_step']} ({r['contract_markers_count']}) | tc {r['tool_calls']} api {r['api_calls']} cost {round(r['cost_usd'] or 0,4)}")
