"""Post-hoc, read-only re-check of the gold-exposure matcher (thesis v5 revision, W72; exploratory, not pre-registered).
The frozen mx_metrics.py marks a run gold_exposed when a fault line's normalised text occurs ANYWHERE in the concatenated tool
output (not tied to a file or position). This script adds a LOCATION-BOUND version: the fault line counts as exposed only if the
line at its own position inside the gold method (in the run's workspace copy of the gold's file) was displayed, using the same
file-attributed, location-aware display index (class Shown) that the frozen script uses for coverage. Nothing frozen is modified.
Reads per run only: mini-swe-agent.traj.json (tool calls and tool outputs, as mx_metrics does), method_catalog.json, the
workspace source file. Never opens raw_agent_output.txt, probe files or credentials. Output: main-run/analysis/exposure_check/."""
import csv, json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE); MR = f"{WM}/main-run"
src = open(f"{HERE}/mx_metrics.py").read(); prefix = src[:src.index("for server, cfg in SERVERS.items():")]
sys.argv = [sys.argv[0]]; sys.path.insert(0, HERE); exec(compile(prefix, "mx_metrics_prefix", "exec"))   # helpers only
AGENT = SERVERS["w55"]["agent_id"]
DBL = re.compile(r"(?m)^(\s*\d+[-:])(\s*\d+\t)")   # `nl -ba FILE | grep -n -A/-B`: grep's 'NNN-'/'NNN:' before nl's 'NNN<TAB>'; keep nl's number
OUT = f"{MR}/analysis/exposure_check"
CELLS = [("C10", "MAIN_RUN"), ("C10f", "MAIN_RUN_C10F"), ("C10i", "MAIN_RUN_C10I")]
rows = []
for cell, f in CELLS:
    res = {r["instance_id"]: r for r in csv.DictReader(open(f"{MR}/{f}_RESULTS.csv"))}
    for r in csv.DictReader(open(f"{MR}/{f}_RUNS.csv")):
        if r["included"] != "True" or res[r["instance_id"]]["counted_in_kpi"] != "True": continue
        V = r["variant_id"]; rd = f"{WM}/models/w55/benchmark_runs/{AGENT}/{V}/{r['run']}"; K = KEY[V]
        traj = rj(f"{rd}/mini-swe-agent.traj.json"); shown = Shown(); shown2 = Shown(); outs = []; outs2 = []; pending = {}
        for m in traj.get("messages", []):
            if m.get("role") == "assistant":
                for tc in m.get("tool_calls") or []:
                    fn = tc.get("function") or {}
                    try: args = json.loads(fn.get("arguments") or "{}")
                    except Exception: args = {}
                    cmd = args.get("command", "") if fn.get("name") == "bash" else ""
                    pending[tc.get("id")] = {os.path.basename(x) for x in re.findall(r"[\w./-]+\.(?:java|xml|txt|properties)", cmd)}
            elif m.get("role") == "tool":
                txt = tool_text(m.get("content")); outs.append(txt); shown.add_output(txt, pending.get(m.get("tool_call_id"), set()))
                txt2 = DBL.sub(r"\2", txt); outs2.append(txt2); shown2.add_output(txt2, pending.get(m.get("tool_call_id"), set()))
        shown_text = norm(" ".join(parse_line(l)[2] for l in "\n".join(outs).replace("\r", "").split("\n")))
        shown_text2 = norm(" ".join(parse_line(l)[2] for l in "\n".join(outs2).replace("\r", "").split("\n")))
        blocks = [str(fl) for fl in as_list(K.get("fault_lines")) if norm(str(fl))]
        orig = any(norm(fl) in shown_text for fl in blocks)          # the frozen rule, verbatim
        orig2 = any(norm(fl) in shown_text2 for fl in blocks)        # same rule after removing a grep prefix before an nl number
        cand, loc, loc2 = 0, False, False
        for fl in blocks:                                            # location-bound: the block at its own position in the gold
            bl = [norm(x) for x in fl.replace("\r", "").split("\n")]
            for g in as_list(K["gold"]):
                for e, L in spans(rd, V, g):
                    for i in range(e["line_start"], e["line_end"] - len(bl) + 2):
                        if all(bl[k] in L[i - 1 + k] if bl[k] else not L[i - 1 + k] for k in range(len(bl))):
                            cand += 1
                            loc = loc or all(shown.displayed(L, e["file"], i + k) for k in range(len(bl)) if substantive(bl[k]))
                            loc2 = loc2 or all(shown2.displayed(L, e["file"], i + k) for k in range(len(bl)) if substantive(bl[k]))
        rows.append({"cell": cell, "instance_id": r["instance_id"], "variant_id": V, "run": r["run"], "batch": r["batch"], "project": r["project"],
                     "answered": r["answered"], "shift": r["shift"], "failure_mode": r["failure_mode"], "rank1_category": r["rank1_category"],
                     "frozen_gold_exposed": r["gold_exposed"], "recomputed_text_match": str(orig), "fault_line_positions_in_gold": cand,
                     "location_bound_exposed": str(loc), "text_match_prefix_aware": str(orig2), "location_bound_prefix_aware": str(loc2)})
os.makedirs(OUT, exist_ok=True)
with open(f"{OUT}/exposure_recheck.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def tab(sel):
    c = collections.Counter((x["frozen_gold_exposed"], x["location_bound_exposed"]) for x in sel); return {f"frozen={a}|loc={b}": n for (a, b), n in sorted(c.items())}
S_ = {"runs": len(rows), "recompute_matches_frozen": sum(x["recomputed_text_match"] == x["frozen_gold_exposed"] for x in rows),
      "fault_line_not_located_in_gold": sum(x["fault_line_positions_in_gold"] == 0 for x in rows),
      "all": tab(rows), "shifted": tab([x for x in rows if x["shift"] == "True"]), "gold_first": tab([x for x in rows if x["failure_mode"] == "GOLD_FIRST"]),
      "shifted_loc_exposed": sum(x["shift"] == "True" and x["location_bound_exposed"] == "True" for x in rows),
      "facade_first_shifted_loc_exposed": sum(x["shift"] == "True" and x["rank1_category"] == "ENTRY_POINT" and x["location_bound_exposed"] == "True" for x in rows),
      "gold_first_loc_exposed": sum(x["failure_mode"] == "GOLD_FIRST" and x["location_bound_exposed"] == "True" for x in rows),
      "prefix_aware": {"text_all": sum(x["text_match_prefix_aware"] == "True" for x in rows), "loc_all": sum(x["location_bound_prefix_aware"] == "True" for x in rows),
                       "text_shifted": sum(x["shift"] == "True" and x["text_match_prefix_aware"] == "True" for x in rows),
                       "loc_shifted": sum(x["shift"] == "True" and x["location_bound_prefix_aware"] == "True" for x in rows),
                       "any_shifted": sum(x["shift"] == "True" and "True" in (x["frozen_gold_exposed"], x["location_bound_exposed"], x["text_match_prefix_aware"], x["location_bound_prefix_aware"]) for x in rows),
                       "any_all": sum("True" in (x["frozen_gold_exposed"], x["location_bound_exposed"], x["text_match_prefix_aware"], x["location_bound_prefix_aware"]) for x in rows),
                       "loc_facade_first_shifted": sum(x["shift"] == "True" and x["rank1_category"] == "ENTRY_POINT" and x["location_bound_prefix_aware"] == "True" for x in rows),
                       "loc_goldfirst": sum(x["failure_mode"] == "GOLD_FIRST" and x["location_bound_prefix_aware"] == "True" for x in rows)}}
json.dump(S_, open(f"{OUT}/exposure_recheck_summary.json", "w"), indent=1); print(json.dumps(S_, indent=1))
