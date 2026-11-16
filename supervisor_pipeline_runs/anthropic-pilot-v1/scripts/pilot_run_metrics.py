#!/usr/bin/env python
"""Provider-independent per-run metrics for the Claude pilot AND the frozen GPT-5.6 reference runs.

The same code, the same definitions and the same regexes are applied to both models' trajectories, so every
comparison in GPT56_VS_CLAUDE.md is measured rather than assembled from two different metric sets. Reads run
artifacts only (commands, tool outputs, ranking, evaluation, manifest); never reads reasoning_content or
reasoning_items.

Usage: pilot_run_metrics.py <out.json>
"""
import glob, itertools, json, os, re, sys

SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
R = f"{SP}/anthropic-pilot-v1"
CLAUDE_RUNS = f"{R}/benchmark_runs/mini-swe-claude"
GPT_RUNS = f"{SP}/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6"
out_path = sys.argv[1] if len(sys.argv) > 1 else f"{R}/analysis/per_run/pilot_run_metrics.json"

# unit -> (config path, arm, variant id per model)
PANEL = [
    ("CONVERSION-LONG-01", "Lang", f"{SP}/conversion-long-chain-v1/analysis/pair_config_long.json",
     [("CONTROL", "control", "CONVERSION-LONG-CONTROL-01"), ("TREATMENT", "treatment", "CONVERSION-LONG-TREATMENT-01")], None),
    ("CHART-PIE-03", "Chart", f"{SP}/core-benchmark-scaleup-v1/chart/bug-03/pair_config.json",
     [("CONTROL", "control", "CHART-PIE-CONTROL-03"), ("TREATMENT", "treatment", "CHART-PIE-TREATMENT-03")], None),
    ("CMP-LAYOUT-02", "Compress", f"{SP}/core-benchmark-scaleup-v2/projects/Compress/bug-02/pair_config.json",
     [("CONTROL", "control", "CMP-LAYOUT-CONTROL-02"), ("TREATMENT", "treatment", "CMP-LAYOUT-TREATMENT-02")], None),
    ("LANG-CONV-CAMO", "Lang",
     f"{SP}/camouflage-model-comparison-v1/experiment-a-camouflage/construction/configs/lang_conv/pair_config_low.json",
     [("LOW", "treatment", "LANG-CONV-CAMOUFLAGE-LOW")],
     f"{SP}/camouflage-model-comparison-v1/experiment-a-camouflage/review/metrics/lang_low.json"),
    ("LANG-CONV-CAMO", "Lang",
     f"{SP}/camouflage-model-comparison-v1/experiment-a-camouflage/construction/configs/lang_conv/pair_config_high.json",
     [("HIGH", "treatment", "LANG-CONV-CAMOUFLAGE-HIGH")],
     f"{SP}/camouflage-model-comparison-v1/experiment-a-camouflage/review/metrics/lang_high.json"),
]

DECL = re.compile(r"^\s*(?:public|protected|private)?\s*(?:static\s+|final\s+|synchronized\s+|abstract\s+)*"
                  r"[\w.$<>\[\],?]+\s+([A-Za-z_$][\w$]*)\s*\([^;{)]*\)\s*(?:throws [\w.,\s]+)?\s*\{?\s*$")
RANGE = re.compile(r"sed\s+-n\s+'?\"?\s*(\d+)\s*,\s*(\d+)\s*p|awk\s+'NR\s*[><=]|head\s+-n\s*\d+.*\|\s*tail")
FULL = re.compile(r"(?:^|&&|;|\|\s*)\s*(?:cat|nl|more|less)\s+[^|;]*\.java|sed\s+-n\s+'?1,\$p")
READ = re.compile(r"\b(?:cat|sed|head|tail|awk|nl|less|more)\b[^|;]*\.java|\.java\"?\s*$")
SEARCH = re.compile(r"\b(grep|rg|ack|ag)\b")
REPO_WIDE = re.compile(r"-r\b|-R\b|--include|--exclude|\bsrc/main\b|\bsrc\b\s*$|\*\*|-l\b.*\bsrc\b")


def rj(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}


def strip_cd(c):
    c = c.strip()
    m = re.match(r"^cd\s+\S+\s*(?:&&|;)\s*(.*)$", c, re.S)
    return m.group(1).strip() if m else c


def steps_of(traj):
    msgs = traj.get("messages") or []
    cmds, outs = [], []
    for m in msgs:
        if m.get("role") == "assistant":
            acts = ((m.get("extra") or {}).get("actions")) or []
            for a in acts:
                if a.get("command"):
                    cmds.append(a["command"])
                elif a.get("tool"):
                    cmds.append("TOOL:" + str(a.get("tool")))
            if not acts:
                for tc in (m.get("tool_calls") or []):
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except Exception:
                        args = {}
                    if args.get("command"):
                        cmds.append(args["command"])
        elif m.get("role") == "tool":
            outs.append(str(m.get("content") or ""))
    n = min(len(cmds), len(outs))
    return [(i + 1, cmds[i], outs[i]) for i in range(n)]


def tau(a, b):
    if len(a) < 3:
        return None
    c = d = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        s = (a[i] - a[j]) * (b[i] - b[j])
        c += s > 0
        d += s < 0
    return (c - d) / (len(a) * (len(a) - 1) / 2)


rows = []
for unit, proj, cfg_path, arms, host_metrics_path in PANEL:
    cfg = rj(cfg_path)
    if not cfg:
        print("missing config:", cfg_path, file=sys.stderr)
        continue
    hm = rj(host_metrics_path) if host_metrics_path else {}
    host_methods = {m["name"] for m in (hm.get("methods") or [])}
    host_base = os.path.basename(cfg["treatment"]["gold_file"]) if host_metrics_path else None
    host_loc = hm.get("file_loc_total")
    facade_decl = cfg["facade_decl"]
    facade_key = f"{cfg['control']['gold_class'].split('.')[-1]}::{cfg['control']['gold_method']}"
    hops = [(f"H{h['n']}", h["class"].split(".")[-1], h["method"], h["decl"]) for h in cfg["treatment"]["hops"]]
    labels = {facade_key: "facade"}
    for tag, cls, meth, _ in hops:
        labels[f"{cls}::{meth}"] = tag
    ideal = ["H5", "H4", "H3", "H2", "H1", "facade"]
    for arm_label, arm_key, variant in arms:
        A = cfg[arm_key]
        gold_decl, bug_line = A["gold_decl"], A["bug_line"].strip()
        gold_name, gold_cls = A["gold_method"], A["gold_class"].split(".")[-1]
        gold_key = f"{gold_cls}::{gold_name}"
        for model, runs_root in (("claude-opus-5-5", CLAUDE_RUNS), ("gpt-5.6", GPT_RUNS)):
            for rd in sorted(glob.glob(f"{runs_root}/{variant}/run-*")):
                man = rj(f"{rd}/run_manifest.json")
                traj = rj(f"{rd}/mini-swe-agent.traj.json")
                if not man:
                    continue
                ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json")
                steps = steps_of(traj)
                preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions")
                         or (rk.get("submission") or {}).get("predictions") or [])
                top = [f"{(p.get('class') or '').split('.')[-1]}::{p.get('method')}" for p in preds[:10]]
                gold_rank = ev.get("gold_rank")
                gold_step = next((i for i, c, o in steps if (gold_decl in o) or (bug_line in o)), None)
                facade_step = next((i for i, c, o in steps if facade_decl in o), None)
                hop_steps = {}
                for tag, cls, meth, decl in hops:
                    hop_steps[tag] = next((i for i, c, o in steps if decl in o), None)
                host_step = host_base and next((i for i, c, o in steps if host_base in c or host_base in o), None)
                reads = searches = repo_searches = full_scans = ranged = tests = 0
                host_opens = host_ranged = host_lines = host_context_lines = 0
                direct_gold = None
                for i, c, o in steps:
                    cc = strip_cd(c)
                    if READ.search(cc):
                        reads += 1
                    if FULL.search(cc):
                        full_scans += 1
                        if host_base and host_base in cc:
                            host_lines += host_loc or 0
                    if RANGE.search(cc):
                        ranged += 1
                        if host_base and host_base in cc:
                            host_ranged += 1
                            for a_, b_ in re.findall(r"sed\s+-n\s+'?\"?\s*(\d+)\s*,\s*(\d+)\s*p", cc):
                                host_lines += max(0, int(b_) - int(a_) + 1)
                    if host_base and host_base in cc:
                        host_opens += 1
                        # a symbol-targeted grep with context windows shows lines too; count them so a
                        # grep-driven reader is not scored as having read nothing
                        for fl, val in re.findall(r"-([ABC])\s*(\d+)", cc):
                            host_context_lines += int(val) * (2 if fl == "C" else 1)
                        if re.search(r"\b(grep|rg)\b", cc):
                            host_context_lines += 1
                    if SEARCH.search(cc):
                        searches += 1
                        if REPO_WIDE.search(cc):
                            repo_searches += 1
                        if direct_gold is None and re.search(r"\b%s\b" % re.escape(gold_name), cc):
                            direct_gold = i
                    if "defects4j test" in cc:
                        tests += 1
                alltext = " ".join(o for _, _, o in steps)
                seen_host_methods = len({m for m in host_methods if re.search(r"\b%s\s*\(" % re.escape(m), alltext)}) if host_methods else None
                before = " ".join(o for i, _, o in steps if gold_step is None or i < gold_step)
                cand_before = len({m.group(1) for line in before.split("\n") for m in [DECL.match(line)] if m})
                ms = ((traj.get("info") or {}).get("model_stats") or {})
                order = [t for t in top if t in labels]
                pos = {labels[t]: k for k, t in enumerate(order)}
                common = [m for m in ideal if m in pos]
                t_ = tau([pos[m] for m in common], [ideal.index(m) for m in common])
                rank1 = top[0] if top else None
                rows.append({
                    "unit": unit, "project": proj, "arm": arm_label, "variant_id": variant, "model": model,
                    "run": os.path.basename(rd), "status": man.get("status"),
                    "gold": gold_key, "gold_rank": gold_rank,
                    "acc_at_1": gold_rank == 1, "acc_at_3": bool(gold_rank and gold_rank <= 3),
                    "acc_at_5": bool(gold_rank and gold_rank <= 5), "acc_at_10": bool(gold_rank and gold_rank <= 10),
                    "mrr": round(1.0 / gold_rank, 4) if gold_rank else 0.0,
                    "submitted_top10": top, "n_predictions": len(preds),
                    "rank1_prediction": rank1,
                    "rank1_is_gold": rank1 == gold_key,
                    "rank1_chain_label": labels.get(rank1) if rank1 else None,
                    "rank1_off_chain": bool(rank1) and rank1 not in labels and rank1 != gold_key,
                    "tool_calls": len(steps),
                    "api_calls": ms.get("api_calls"),
                    "model_responses": sum(1 for m in (traj.get("messages") or []) if m.get("role") == "assistant"),
                    "first_gold_step": gold_step, "first_facade_step": facade_step,
                    "hop_exposure_steps": hop_steps,
                    "hops_exposed": sum(1 for v in hop_steps.values() if v),
                    "chain_traversal_in_order": [t for t, s in sorted(
                        [(t, s) for t, s in hop_steps.items() if s], key=lambda x: x[1])],
                    "file_reads": reads, "searches": searches, "repository_wide_searches": repo_searches,
                    "full_file_scans": full_scans, "targeted_line_range_reads": ranged, "test_runs": tests,
                    "direct_gold_search_step": direct_gold,
                    # "lexical_shortcut": the run searched the gold's own name at or before the step that first
                    # exposed the gold. On a CONTROL arm the gold name is the method under test, so this is
                    # trivially available. On a TREATMENT arm the name is absent from the payload (lexgate
                    # DECOUPLED), so the name is normally LEARNED while walking the chain and the search is
                    # navigation, not leakage. The strict form below is the leakage-relevant one.
                    "lexical_shortcut": bool(direct_gold and gold_step and direct_gold <= gold_step),
                    "gold_search_before_any_hop": bool(
                        direct_gold and [v for v in hop_steps.values() if v]
                        and direct_gold < min(v for v in hop_steps.values() if v)),
                    "calls_after_first_gold": (len(steps) - gold_step) if gold_step else None,
                    "candidate_methods_seen_before_gold": cand_before,
                    "host_file_opens": host_opens if host_base else None,
                    "host_targeted_reads": host_ranged if host_base else None,
                    "host_lines_read": host_lines if host_base else None,
                    "host_grep_context_lines": host_context_lines if host_base else None,
                    "host_lines_seen_total": (host_lines + host_context_lines) if host_base else None,
                    "host_methods_inspected": seen_host_methods,
                    "host_methods_available": len(host_methods) if host_methods else None,
                    "submitted_chain_order": [labels[t] for t in order],
                    "chain_members_in_top6": sum(1 for t in top[:6] if t in labels),
                    "gold_rank_in_chain": (list(pos.keys()).index(labels[gold_key]) + 1) if gold_key in labels and labels[gold_key] in pos else None,
                    "deepest_stage_rank": (top.index(f"{hops[-1][1]}::{hops[-1][2]}") + 1) if f"{hops[-1][1]}::{hops[-1][2]}" in top else None,
                    "kendall_tau_vs_reverse_depth": round(t_, 3) if t_ is not None else None,
                    "exact_reverse_depth": [labels[t] for t in order] == ideal,
                    "cost_usd": ms.get("instance_cost", ms.get("cost")),
                    "wall_clock_s": round((man.get("duration_ms") or 0) / 1000.0, 1) or None,
                })
json.dump(rows, open(out_path, "w"), indent=2)
byk = {}
for r in rows:
    byk.setdefault((r["model"], r["unit"], r["arm"]), []).append(r)
print(f"{len(rows)} runs measured")
for k, v in sorted(byk.items()):
    comp = [x for x in v if x["status"] == "completed"]
    print(f"  {k[0]:18s} {k[1]:20s} {k[2]:10s} n={len(comp)}/{len(v)} ranks={[x['gold_rank'] for x in comp]} "
          f"tc={[x['tool_calls'] for x in comp]} first_gold={[x['first_gold_step'] for x in comp]}")
