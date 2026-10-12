"""Retrospective mechanism mining: one row per completed run across all earlier experiments (read-only over their run directories).
Usage: mx_mine.py -> MECHANISM_RUN_DATA.csv, mining/run_data.json
Per run: family, model, variant, outcome (ct_status), gold rank, Acc@1, RR, effort; deterministic trajectory features (gold fault line
shown, gold coverage, decoy exposure/coverage, external-evidence display, test run, failure values seen, probe); instance features from
mining/annotations/*.json; failure mode / rationale for wrong runs from mining/classifications/*.json. Hidden reasoning is never read."""
import json, os, re, sys, glob, csv, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_status as S
from mx_helpers import *   # noqa
MX = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/mechanism-search-v1"
runs = json.load(open(f"{MX}/mining/all_runs.json"))
ANN = {}
for p in glob.glob(f"{MX}/mining/annotations/*.json"):
    a = json.load(open(p))
    for inst in a.get("instances", []): ANN[inst["variant"]] = inst
CLS = {}
for p in glob.glob(f"{MX}/mining/classifications/*.json"):
    for r in json.load(open(p)).get("runs", []): CLS[os.path.normpath(r["run_dir"])] = r
def as_list(x): return x if isinstance(x, list) else ([x] if x else [])
rows = []
for r in runs:
    rd = r["run_dir"]; V = r["variant"]; A = ANN.get(V, {})
    try: cls = S.classify(rd)
    except Exception: cls = {"status": None, "kind": "unknown"}
    ev = rj(f"{rd}/evaluation.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json"); rk = rj(f"{rd}/ranking.json")
    preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or []); keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]
    golds = as_list(A.get("gold")) or [f"{g.get('class')}::{g.get('method')}" for g in ev.get("gold_methods", [])]
    gr = ev.get("gold_rank"); answered = cls["status"] == "completed" and len(keys) == 10
    msgs = traj.get("messages", []); outs, cmds, shown = [], [], Shown(); pending = {}; segc = {"READ": 0, "SEARCH": 0, "TEST": 0, "PROBE": 0}; probe = False
    for m in msgs:
        if m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                fn = tc.get("function") or {}
                try: args = json.loads(fn.get("arguments") or "{}")
                except Exception: args = {}
                cmd = args.get("command", "") if fn.get("name") == "bash" else ""; cmds.append(cmd)
                for k, ind in classify_command(cmd, ""): segc[k] += 1; probe = probe or (k == "PROBE")
                pending[tc.get("id")] = {os.path.basename(x) for x in re.findall(r"[\w./-]+\.(?:java|xml|txt|properties)", cmd)}
        elif m.get("role") == "tool":
            txt = tool_text(m.get("content")); outs.append(txt); shown.add_output(txt, pending.get(m.get("tool_call_id"), set()))
    raw = "\n".join(outs).replace("\r", ""); stext = norm(" ".join(parse_line(l)[2] for l in raw.split("\n")))
    def cov(k):
        try: return coverage(rd, V, k, shown)
        except Exception: return None
    gold_cov = max([c for c in (cov(g) for g in golds) if c is not None] or [None]) if golds else None
    decoys = as_list(A.get("decoys")); dcov = [c for c in (cov(d) for d in decoys) if c is not None]
    evid = [e.get("location", "") for e in A.get("external_evidence", []) if "::" in e.get("location", "")]
    evid_keys = [re.match(r"([\w.$]+::\w+)", e).group(1) for e in evid if re.match(r"([\w.$]+::\w+)", e)]
    ecov = [c for c in (cov(e) for e in evid_keys) if c is not None]
    usage = [((m.get("extra") or {}).get("response") or {}).get("usage") or {} for m in msgs if m.get("role") == "assistant"]
    ms = (traj.get("info") or {}).get("model_stats") or {}; C_ = CLS.get(os.path.normpath(rd), {})
    rows.append({"family": r["family"], "model": r["model"], "variant": V, "run_dir": rd, "status": cls["status"], "status_kind": cls["kind"], "answered": answered,
                 "gold_rank": gr, "acc1": int(answered and gr == 1), "rr": round(1 / gr, 4) if (answered and gr) else 0.0, "rank1": keys[0] if keys else None,
                 "rank1_is_decoy": bool(keys and keys[0] in decoys), "rank1_is_entry": bool(keys and keys[0] in as_list(A.get("entry_points"))),
                 "gold_fault_line_shown": any(norm(fl) in stext for fl in as_list(A.get("fault_lines")) if norm(fl)) if A else None,
                 "gold_coverage": gold_cov, "gold_fully_read": (gold_cov or 0) >= 0.9 if gold_cov is not None else None,
                 "decoy_exposed": (max(dcov) > 0.2) if dcov else None, "decoy_coverage": max(dcov) if dcov else None,
                 "external_evidence_available": bool(A.get("external_evidence")), "external_evidence_displayed": (max(ecov) >= 0.5) if ecov else None,
                 "tests_executed": segc["TEST"] > 0, "failure_values_seen": bool(re.search(r"expected:<[^>]*> but was:<", raw)), "probe_executed": probe,
                 "tool_calls": len(cmds), "model_calls": ms.get("api_calls"), "reasoning_tokens": sum(((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0) for u in usage),
                 "cost_usd": ms.get("instance_cost"), "project": A.get("project"), "instance_label": A.get("instance_label"),
                 **{f: A.get(f) for f in ("bug_omission", "bug_wrong_operator", "bug_wrong_constant", "bug_wrong_variable", "bug_missing_negation", "bug_wrong_branch",
                                          "local_cue_gold", "local_cue_decoy", "ownership_split", "semantic_convention_ambiguity", "second_caller", "multiple_plausible_suspects", "search_depth_hops")},
                 "mechanism_tags": "|".join(A.get("mechanism_tags") or []), "annotated": bool(A),
                 "cls_outcome": C_.get("outcome"), "failure_mode": C_.get("failure_mode"), "secondary_mode": C_.get("secondary_mode"),
                 "ext_evidence_retrieved_judged": C_.get("external_evidence_retrieved"), "ext_evidence_integrated_judged": C_.get("external_evidence_integrated"),
                 "rationale_summary": (C_.get("rationale_summary") or "")[:300]})
json.dump(rows, open(f"{MX}/mining/run_data.json", "w"), indent=1)
with open(f"{MX}/MECHANISM_RUN_DATA.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "runs;", sum(r["annotated"] for r in rows), "annotated;", sum(1 for r in rows if r["failure_mode"]), "with failure-mode labels")
