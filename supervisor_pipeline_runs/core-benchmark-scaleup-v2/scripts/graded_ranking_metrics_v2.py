"""Graded within-chain outcome for every TREATMENT run, computed from existing artefacts (no paid runs).
For each run: the submitted order of the six chain methods, the gold's rank INSIDE that permutation, and Kendall tau
between the submitted chain order and reverse-depth order (H5, H4, H3, H2, H1, facade). Writes
results-gpt56/analysis/tables/graded_within_chain.md and .../graded_within_chain.json."""
import json, itertools, statistics
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"
d = json.load(open(S + "/results-gpt56/scaleup_v2_results.json")); man = json.load(open(S + "/SCALEUP_MANIFEST.json"))
def chain_names(bug_id):
    b = next(x for x in man["bugs"] if x["bug_id"] == bug_id); cfg = json.load(open(f"{S}/{b['dir']}/pair_config.json"))
    fac = cfg["facade_file"].split("/")[-1][:-5] + "::" + cfg["facade_decl"].split("(")[0].split()[-1]
    hops = [h["class"].split(".")[-1] + "::" + h["method"] for h in cfg["treatment"]["hops"]]
    return fac, hops            # hops[0]=H1 ... hops[4]=H5(gold)
def tau(a, b):
    n = len(a); c = dis = 0
    for i, j in itertools.combinations(range(n), 2):
        s = (a[i] - a[j]) * (b[i] - b[j])
        if s > 0: c += 1
        elif s < 0: dis += 1
    return (c - dis) / (n * (n - 1) / 2)
rows = []; per_bug = {}
for bug in [b["bug_id"] for b in d["bugs_new"] if "effect" in b]:
    fac, hops = chain_names(bug); ideal = [hops[4], hops[3], hops[2], hops[1], hops[0], fac]   # reverse depth
    labels = {fac: "facade", **{h: f"H{i+1}" for i, h in enumerate(hops)}}
    taus = []; inranks = []
    for x in [r for r in d["per_run"] if r["bug_id"] == bug and r["condition"] == "TREATMENT"]:
        top = [t.split(".")[-1] for t in x["submitted_ranking_top10"]]
        order = [t for t in top if t in labels]                       # submitted order of chain members
        pos = {m: i for i, m in enumerate(order)}
        gold_in_chain = pos.get(hops[4], None)
        common = [m for m in ideal if m in pos]
        t = tau([pos[m] for m in common], [ideal.index(m) for m in common]) if len(common) > 2 else None
        taus.append(t); inranks.append(None if gold_in_chain is None else gold_in_chain + 1)
        rows.append({"bug": bug, "run": x["run_id"].split("/")[1], "gold_rank_overall": x["gold_rank"], "gold_rank_in_chain": None if gold_in_chain is None else gold_in_chain + 1,
                     "chain_members_in_top6": sum(1 for t2 in top[:6] if t2 in labels), "submitted_chain_order": [labels[m] for m in order],
                     "kendall_tau_vs_reverse_depth": None if t is None else round(t, 3), "exact_reverse_depth": [labels[m] for m in order] == ["H5", "H4", "H3", "H2", "H1", "facade"]}
                    )
    per_bug[bug] = {"gold_rank_in_chain": inranks, "mean_tau": round(statistics.mean([t for t in taus if t is not None]), 3),
                    "exact_reverse_depth_runs": sum(1 for r in rows if r["bug"] == bug and r["exact_reverse_depth"])}
allt = [r["kendall_tau_vs_reverse_depth"] for r in rows if r["kendall_tau_vs_reverse_depth"] is not None]
summary = {"runs": len(rows), "chain_fills_top6_runs": sum(1 for r in rows if r["chain_members_in_top6"] == 6),
           "gold_first_in_chain_runs": sum(1 for r in rows if r["gold_rank_in_chain"] == 1),
           "mean_kendall_tau_vs_reverse_depth": round(statistics.mean(allt), 3), "median_tau": round(statistics.median(allt), 3),
           "runs_with_tau_1": sum(1 for t in allt if t == 1.0), "exact_reverse_depth_runs": sum(1 for r in rows if r["exact_reverse_depth"]), "per_bug": per_bug}
json.dump({"summary": summary, "runs": rows}, open(S + "/results-gpt56/analysis/tables/graded_within_chain.json", "w"), indent=1)
L = ["# Graded within-chain outcome (no new paid runs)", "",
     "Acc@1 is saturated, so this table reports the sensitive outcome the data already contains: where the gold sits **inside the six-method chain permutation** the agent submits, and how closely that permutation follows **reverse-depth order** (H5, H4, H3, H2, H1, facade). The confound this addresses: the gold has been the deepest stage in every variant ever built, so 'ranks the gold first' and 'ranks the deepest stage first' have made identical predictions on all 140 runs.", "",
     "| Bug | Run | Gold rank (overall) | Gold rank in chain | Chain members in top 6 | Submitted chain order | Kendall τ vs reverse depth | Exact reverse depth |", "|" + "---|" * 8]
for r in rows:
    L.append(f"| `{r['bug']}` | {r['run']} | {r['gold_rank_overall']} | {r['gold_rank_in_chain']} | {r['chain_members_in_top6']}/6 | {' > '.join(r['submitted_chain_order'])} | {r['kendall_tau_vs_reverse_depth']} | {'yes' if r['exact_reverse_depth'] else 'no'} |")
L += ["", "## Summary", "", "| Item | Value |", "|---|---|",
      f"| Treatment runs analysed | {summary['runs']} |",
      f"| Runs whose top 6 is exactly the six chain methods | {summary['chain_fills_top6_runs']}/{summary['runs']} |",
      f"| Runs ranking the gold first within the chain | {summary['gold_first_in_chain_runs']}/{summary['runs']} |",
      f"| Mean / median Kendall τ against reverse-depth order | {summary['mean_kendall_tau_vs_reverse_depth']} / {summary['median_tau']} |",
      f"| Runs whose chain order is perfectly reverse-depth (τ = 1) | {summary['runs_with_tau_1']}/{summary['runs']} |",
      f"| Runs whose full order is exactly H5 > H4 > H3 > H2 > H1 > facade | {summary['exact_reverse_depth_runs']}/{summary['runs']} |", "",
      "| Bug | Gold rank in chain per run | Mean τ | Exact reverse-depth runs |", "|---|---|---|---|"]
for k, v in per_bug.items(): L.append(f"| `{k}` | {v['gold_rank_in_chain']} | {v['mean_tau']} | {v['exact_reverse_depth_runs']}/5 |")
L += ["", "Reading: the submitted permutation tracks reverse-depth order closely (mean τ = " + str(summary["mean_kendall_tau_vs_reverse_depth"]) + "), and because the gold has always been the terminal stage, this benchmark cannot yet distinguish localization from a depth-first ranking prior. The experiment that separates them is a chain whose gold sits at H2 or H3 with genuine, correct, documented work downstream of it."]
open(S + "/results-gpt56/analysis/tables/graded_within_chain.md", "w").write("\n".join(L) + "\n")
print(json.dumps(summary, indent=1))
