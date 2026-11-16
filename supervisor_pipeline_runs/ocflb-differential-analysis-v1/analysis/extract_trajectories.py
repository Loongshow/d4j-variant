#!/usr/bin/env python
"""Observable-behaviour extraction for the trajectory differential (no hidden reasoning; only commands, tool outputs, submitted
evidence chains and rankings). Writes analysis/trajectory_differential.json and TRAJECTORY_DIFFERENTIAL.md (run table)."""
import json, re, os, glob
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"; D = f"{SP}/ocflb-differential-analysis-v1"
ADV = f"{SP}/adversarial-break-v1/models"; OC = f"{SP}/ocflb-v1/models"
# (label, run_dir, H2 method, H3 method, gold method, pin test class)
RUNS = []
for m, n in (("opus55", 5), ("opus55t", 5), ("sonnet46", 11)):
    for i in range(1, n + 1): RUNS.append((f"ADV/{m}/run-{i:03d}", f"{ADV}/{m}/benchmark_runs/mini-swe-claude/ADV-DEFINER-01/run-{i:03d}", "drift", "nudge", "nudge", "PlotUtilitiesTests", "adversarial"))
for s, v, h2, h3, pin in (("sonnetA", "OCFLB-CHART-01-ADAPTER", "drift", "nudge", "PlotUtilitiesTests"), ("opusA", "OCFLB-CHART-01-ADAPTER", "drift", "nudge", "PlotUtilitiesTests"), ("sonnetB", "OCFLB-CHART-02-ADAPTER", "pad", "place", "RangeTests"), ("sonnetA", "OCFLB-CHART-01-DEFINER", "drift", "nudge", "PlotUtilitiesTests"), ("opusA", "OCFLB-CHART-01-DEFINER", "drift", "nudge", "PlotUtilitiesTests")):
    for rd in sorted(glob.glob(f"{OC}/{s}/benchmark_runs/mini-swe-claude/{v}/run-*")):
        RUNS.append((f"OCFLB/{s}/{v.split('-',1)[1]}/{os.path.basename(rd)}", rd, h2, h3, (h3 if v.endswith("ADAPTER") else h2), pin, "ocflb"))
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def steps(traj):
    out = []; cmds = []
    for m in traj.get("messages") or []:
        if m.get("role") == "assistant":
            for a in ((m.get("extra") or {}).get("actions") or []): cmds.append(a.get("command") or ("TOOL:" + str(a.get("tool"))))
        elif m.get("role") == "tool": out.append(str((m.get("extra") or {}).get("raw_output") or m.get("content") or ""))
    return [(i + 1, re.sub(r"^cd \S+(; | && )", "", cmds[i]), out[i]) for i in range(min(len(cmds), len(out)))]
def clean(o): return re.sub(r"(?m)^\s*\d+[-:]", "", o)          # strip grep -n / -A / -B line prefixes so javadoc blocks match
def decl_rx(m): return re.compile(r"(static|public|protected|private)[^\n;{]*\b" + re.escape(m) + r"\s*\(")
def jdoc_rx(m): return re.compile(r"/\*\*[^{]*?\*/\s*(?:public|protected|private|static)[^\n;{]*\b" + re.escape(m) + r"\s*\(", re.S)
BODY = {"drift_adv": re.compile(r"point1\.getX\(\)\s*-\s*point2\.getX\(\)"), "nudge_adv": re.compile(r"double deltaX = drift\.getX\(\) \* explodePercent"), "drift_oc": re.compile(r"point2\.getX\(\)\s*-\s*point1\.getX\(\)"), "nudge_oc": re.compile(r"-drift\.getX\(\) \* explodePercent"), "pad": re.compile(r"padding\.getLength\(\)|index \* gap")}
rows = []
for label, rd, h2, h3, gold, pin, fam in RUNS:
    traj = rj(f"{rd}/mini-swe-agent.traj.json"); man = rj(f"{rd}/run_manifest.json"); rk = rj(f"{rd}/ranking.json"); ev = rj(f"{rd}/evaluation.json")
    if not traj: continue
    st = [(i, c, clean(o)) for i, c, o in steps(traj)]; ss = rk.get("structured_submission") or {}; preds = ss.get("predictions") or rk.get("predictions") or []
    top5 = [f"{p['class'].split('.')[-1]}::{p['method']}" for p in preds[:5]]
    first = lambda rx: next((i for i, c, o in st if rx.search(o)), None)
    ec = ss.get("evidence_chain") or []; rationale = " | ".join((e.get("evidence", "") + " => " + e.get("inference_summary", "")) for e in ec)[:900]
    rows.append({"label": label, "family": fam, "status": man.get("status"), "gold_rank": ev.get("gold_rank"), "tool_calls": len(st),
                 "first_query": st[0][1][:160] if st else None,
                 "first_h2_exposure": first(decl_rx(h2)), "first_h3_exposure": first(decl_rx(h3)), "first_gold_exposure": first(decl_rx(gold)),
                 "h2_javadoc_seen": first(jdoc_rx(h2)) is not None, "h3_javadoc_seen": first(jdoc_rx(h3)) is not None,
                 "h2_body_seen": first(BODY["drift_adv" if fam == "adversarial" else ("drift_oc" if h2 == "drift" else "pad")]) is not None,
                 "h3_body_seen": first(BODY["nudge_adv" if fam == "adversarial" else ("nudge_oc" if h3 == "nudge" else "pad")]) is not None,
                 "pin_test_opened": next((i for i, c, o in st if pin in c or pin in o or "testDrift" in c or "testPad" in c), None),
                 "tests_dir_searched": any(re.search(r"\btests?\b", c) and re.search(r"\b(grep|find|ls)\b", c) for i, c, o in st),
                 "test_executed": sum(1 for i, c, o in st if "defects4j test" in c), "runner_ok": any("Running ant" in o for i, c, o in st),
                 "arithmetic_check": any(re.search(r"python3|jshell|javac|cat > /tmp|bc\b", c) for i, c, o in st),
                 "mentions_javadoc_or_contract": bool(re.search(r"javadoc|documented|documentation|contract|convention|@return|comment says|described as", rationale, re.I)),
                 "mentions_sign_or_direction": bool(re.search(r"sign|direction|revers|invert|negat|opposite|toward|away", rationale, re.I)),
                 "mentions_pin_or_test_evidence": bool(re.search(r"PlotUtilitiesTests|testDrift|RangeTests|testPad|unit test|pinned|checked by", rationale, re.I)),
                 "rationale": rationale, "top5": top5})
json.dump(rows, open(f"{D}/analysis/trajectory_differential.json", "w"), indent=1)
L = ["# Trajectory differential (observable behaviour only)", "", "Columns: exposures are the tool-call step at which the method declaration first appeared in an output; javadoc seen = a /** ... */ block immediately above the declaration appeared in an output; pin opened = step at which the pin test class/method appeared in a command or output; rationale = the submitted evidence_chain text (the model's own stated reasoning in its structured submission).", "",
     "| Run | Status | Gold rank | Calls | H2 exp | H3 exp | Gold exp | H2 javadoc seen | H3 javadoc seen | H2 body seen | H3 body seen | Pin opened | tests searched | test runs | own arithmetic | rationale mentions doc/contract | mentions sign/direction | mentions test evidence | Top-5 |", "|" + "---|" * 19]
for r in rows: L.append(f"| {r['label']} | {r['status']} | {r['gold_rank']} | {r['tool_calls']} | {r['first_h2_exposure']} | {r['first_h3_exposure']} | {r['first_gold_exposure']} | {r['h2_javadoc_seen']} | {r['h3_javadoc_seen']} | {r['h2_body_seen']} | {r['h3_body_seen']} | {r['pin_test_opened']} | {r['tests_dir_searched']} | {r['test_executed']} | {r['arithmetic_check']} | {r['mentions_javadoc_or_contract']} | {r['mentions_sign_or_direction']} | {r['mentions_pin_or_test_evidence']} | {' > '.join(r['top5'])} |")
open(f"{D}/analysis/trajectory_table.md", "w").write("\n".join(L) + "\n"); print(len(rows), "runs extracted")
for fam in ("adversarial", "ocflb"):
    rs = [r for r in rows if r["family"] == fam and r["status"] == "completed"]
    print(fam, "answered", len(rs), "gold-first", sum(1 for r in rs if r["gold_rank"] == 1), "h2doc", sum(r["h2_javadoc_seen"] for r in rs), "h3doc", sum(r["h3_javadoc_seen"] for r in rs), "h2body", sum(r["h2_body_seen"] for r in rs), "h3body", sum(r["h3_body_seen"] for r in rs), "pin", sum(1 for r in rs if r["pin_test_opened"]), "doc-mention", sum(r["mentions_javadoc_or_contract"] for r in rs), "sign-mention", sum(r["mentions_sign_or_direction"] for r in rs), "test-evidence-mention", sum(r["mentions_pin_or_test_evidence"] for r in rs), "tests run", sum(r["test_executed"] > 0 for r in rs))
