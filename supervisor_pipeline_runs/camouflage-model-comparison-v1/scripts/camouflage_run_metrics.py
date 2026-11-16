#!/usr/bin/env python
"""A12 per-run camouflage metrics, from run artifacts only (never reasoning_content / reasoning_items).
Usage: camouflage_run_metrics.py <out_json>"""
import json, os, re, glob, sys, itertools, statistics

R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1"
A = f"{R}/experiment-a-camouflage"
RUNS = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6"
PAIRS = [("lang_conv", "LANG-CONV-CAMO", "Lang"), ("math_norm", "MATH-NORM-CAMO", "Math"), ("jkc_surr", "JKC-SURR-CAMO", "JacksonCore")]
out_path = sys.argv[1] if len(sys.argv) > 1 else f"{A}/results/per_run_camouflage_metrics.json"

DECL = re.compile(r"^\s*(?:public|protected|private)?\s*(?:static\s+|final\s+|synchronized\s+|abstract\s+)*"
                  r"[\w.$<>\[\],?]+\s+([A-Za-z_$][\w$]*)\s*\([^;{)]*\)\s*(?:throws [\w.,\s]+)?\s*\{?\s*$")
RANGE = re.compile(r"sed\s+-n\s+'?\"?\s*(\d+)\s*,\s*(\d+)\s*p|awk\s+'NR\s*[><=]|head\s+-n\s*\d+.*\|\s*tail")
FULL = re.compile(r"(?:^|&&|\|\s*)\s*(?:cat|nl|more|less)\s+[^|;]*\.java|sed\s+-n\s+'?1,\$p")


def rj(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}


def strip_cd(c):
    c = c.strip()
    m = re.match(r"^cd\s+\S+\s*&&\s*(.*)$", c, re.S)
    return m.group(1).strip() if m else c


def steps_of(traj):
    """[(idx, command, output)]: mini-swe-agent can emit several actions per assistant message, so
    flatten the actions in order and zip them with the tool messages in order (the health check's
    tool_calls count equals the number of tool messages)."""
    msgs = traj.get("messages") or []
    cmds, outs = [], []
    for m in msgs:
        role = m.get("role")
        if role == "assistant":
            acts = ((m.get("extra") or {}).get("actions")) or []
            for a in acts:
                if a.get("command"):
                    cmds.append(a["command"])
            if not acts:
                for tc in (m.get("tool_calls") or []):
                    try:
                        c = json.loads(tc["function"]["arguments"]).get("command")
                        if c:
                            cmds.append(c)
                    except Exception:
                        pass
        elif role == "tool":
            outs.append(str(m.get("content") or ""))
    return [(i + 1, cmds[i], outs[i]) for i in range(min(len(cmds), len(outs)))]


def tau(a, b):
    n = len(a)
    if n < 3:
        return None
    c = d = 0
    for i, j in itertools.combinations(range(n), 2):
        s = (a[i] - a[j]) * (b[i] - b[j])
        c += s > 0
        d += s < 0
    return (c - d) / (n * (n - 1) / 2)


rows = []
for sname, pair, proj in PAIRS:
    for arm in ("low", "high"):
        cfg = json.load(open(f"{A}/construction/configs/{sname}/pair_config_{arm}.json"))
        V = cfg["treatment_id"]; T = cfg["treatment"]
        met = json.load(open(f"{A}/review/metrics/{sname.split('_')[0]}_{arm}.json"))
        host_base = os.path.basename(T["gold_file"])
        host_methods = {m["name"] for m in met["methods"]}
        gold_name = T["gold_method"]; gold_decl = T["gold_decl"]; bug_line = T["bug_line"].strip()
        chain = [(f"H{h['n']}", h["class"].split(".")[-1], h["method"]) for h in T["hops"]]
        fac = (cfg["control"]["gold_class"].split(".")[-1], cfg["control"]["gold_method"])
        labels = {f"{fac[0]}::{fac[1]}": "facade"}
        for tag, cls, meth in chain:
            labels[f"{cls}::{meth}"] = tag
        ideal = ["H5", "H4", "H3", "H2", "H1", "facade"]
        for rd in sorted(glob.glob(f"{RUNS}/{V}/run-*")):
            man = rj(f"{rd}/run_manifest.json"); ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json")
            traj = rj(f"{rd}/mini-swe-agent.traj.json")
            if not traj:
                continue
            steps = steps_of(traj)
            preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions")
                     or (rk.get("submission") or {}).get("predictions") or [])
            top = [f"{(p.get('class') or '').split('.')[-1]}::{p.get('method')}" for p in preds[:10]]
            gold_rank = ev.get("gold_rank")
            gold_step = next((i for i, c, o in steps if (gold_decl in o) or (bug_line in o)), None)
            host_step = next((i for i, c, o in steps if host_base in c or host_base in o), None)
            full_scans = host_full = ranged = host_ranged = in_host_grep = repo_grep = other_grep = tests = 0
            host_lines_read = 0          # lines of the gold host file actually pulled into context
            direct_gold_search = None
            for i, c, o in steps:
                cc = strip_cd(c)
                is_grep = bool(re.search(r"\b(grep|rg|ack)\b", cc))
                touches_host = host_base in cc
                if FULL.search(cc):
                    full_scans += 1; host_full += touches_host
                    if touches_host:
                        host_lines_read += met["file_loc_total"]
                if RANGE.search(cc):
                    ranged += 1; host_ranged += touches_host
                    if touches_host:
                        for a_, b_ in re.findall(r"sed\s+-n\s+'?\"?\s*(\d+)\s*,\s*(\d+)\s*p", cc):
                            host_lines_read += max(0, int(b_) - int(a_) + 1)
                if is_grep:
                    if re.search(r"-r|-R|--include|--exclude|\bsrc/\b|\*\*|\bsrc\b\s*$", cc) and not touches_host:
                        repo_grep += 1
                    elif touches_host:
                        in_host_grep += 1
                    else:
                        other_grep += 1
                if "defects4j test" in cc:
                    tests += 1
                if direct_gold_search is None and is_grep and re.search(r"\b%s\b" % re.escape(gold_name), cc):
                    direct_gold_search = i
            seen_methods = {m for m in host_methods if re.search(r"\b%s\s*\(" % re.escape(m), " ".join(o for _, _, o in steps))}
            before = " ".join(o for i, _, o in steps if gold_step is None or i < gold_step)
            cand_before = {m.group(1) for line in before.split("\n") for m in [DECL.match(line)] if m}
            ms = ((traj.get("info") or {}).get("model_stats") or {})
            order = [t for t in top if t in labels]
            pos = {m: k for k, m in enumerate(order)}
            common = [m for m in ideal if m in {labels[x] for x in order}]
            inv = {labels[x]: pos[x] for x in order}
            t = tau([inv[m] for m in common], [ideal.index(m) for m in common]) if len(common) > 2 else None
            gold_key = f"{T['gold_class'].split('.')[-1]}::{gold_name}"
            rows.append({
              "pair": pair, "arm": arm.upper(), "variant_id": V, "project": proj,
              "run": os.path.basename(rd), "status": man.get("status"),
              "gold_rank": gold_rank, "acc_at_1": gold_rank == 1, "acc_at_3": bool(gold_rank and gold_rank <= 3),
              "acc_at_5": bool(gold_rank and gold_rank <= 5), "acc_at_10": bool(gold_rank and gold_rank <= 10),
              "mrr": round(1.0 / gold_rank, 4) if gold_rank else 0.0,
              "tool_calls": len(steps), "api_calls": sum(1 for m in (traj.get("messages") or []) if m.get("role") == "assistant"),
              "first_gold_exposure_step": gold_step, "first_host_file_step": host_step,
              "steps_from_host_to_gold": (gold_step - host_step) if (gold_step and host_step) else None,
              "full_file_scans": full_scans, "full_file_scans_of_host": host_full,
              "targeted_line_range_reads": ranged, "targeted_line_range_reads_of_host": host_ranged,
              "host_lines_read": host_lines_read,
              "host_lines_read_fraction": round(host_lines_read / met["file_loc_total"], 3),
              "same_file_methods_inspected": len(seen_methods),
              "same_file_methods_available": len(host_methods),
              "candidate_methods_seen_before_gold": len(cand_before),
              "greps_in_gold_host": in_host_grep, "repository_wide_searches": repo_grep, "other_greps": other_grep,
              "test_runs": tests,
              "direct_gold_name_search_step": direct_gold_search,
              "lexical_shortcut": bool(direct_gold_search and gold_step and direct_gold_search <= gold_step),
              "wall_clock_s": (man.get("timing") or {}).get("duration_s") or ms.get("duration_s"),
              "cost_usd": ms.get("cost", ms.get("instance_cost")),
              "submitted_top10": top, "submitted_chain_order": [labels[x] for x in order],
              "chain_members_in_top6": sum(1 for x in top[:6] if x in labels),
              "gold_rank_in_chain": (list(pos.keys()).index(gold_key) + 1) if gold_key in pos else None,
              "deepest_stage_rank": (top.index(gold_key) + 1) if gold_key in top else None,
              "kendall_tau_vs_reverse_depth": round(t, 3) if t is not None else None,
              "exact_reverse_depth": [labels[x] for x in order] == ideal,
            })
json.dump(rows, open(out_path, "w"), indent=1)
print(f"{len(rows)} runs; per arm:",
      {f"{r['pair']}/{r['arm']}": sum(1 for x in rows if x['pair'] == r['pair'] and x['arm'] == r['arm']) for r in rows})
for r in rows[:4]:
    print(f"  {r['variant_id']} {r['run']}: rank={r['gold_rank']} tc={r['tool_calls']} gold@{r['first_gold_exposure_step']} host@{r['first_host_file_step']} scans={r['full_file_scans']} ranged={r['targeted_line_range_reads']} methods={r['same_file_methods_inspected']}/{r['same_file_methods_available']} cand_before={r['candidate_methods_seen_before_gold']} hostgrep={r['greps_in_gold_host']} repo={r['repository_wide_searches']} tau={r['kendall_tau_vs_reverse_depth']}")
