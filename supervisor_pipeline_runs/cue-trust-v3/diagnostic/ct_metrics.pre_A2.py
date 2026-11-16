"""cue-trust-v3 per-run measures, per-cell summaries and pre-specified pilot contrasts (definitions frozen before the first GPT-5.6 run;
see PREREGISTRATION.md amendment A1). Observable trajectory data only: reasoning content and encrypted reasoning items are never read.
Usage: ct_metrics.py [--include-diagnostic]
  -> analysis/per_run.json|csv (analysis servers), analysis/summary_by_cell.json, analysis/contrasts.json
     (--include-diagnostic also writes analysis/diagnostic_per_run.json for diagnostic/stub servers; never mixed into the above)

Definitions (one run):
  status            ct_status.classify (uniform provider-failure rule). Infrastructure runs are excluded from every denominator.
  answered          behavioural run whose final submission is a valid ten-method ranking (ranking.json predictions present).
  gold_rank         rank of the gold Class::method in the submission (None if absent or no answer). acc1 = answered and gold_rank == 1.
  rr                1/gold_rank if the gold is ranked, else 0 (no answer = 0). MRR = mean rr over behavioural runs.
  rank1_category    NO_ANSWER | GOLD | DECOY (any declared decoy) | ENTRY_POINT (frozen per-instance list, ENTRY_POINTS below) | OTHER.
  displayed text    the concatenated tool outputs the model received (tool message content), line-number prefixes stripped,
                    whitespace-normalised; "displayed line set" = the set of those normalised lines.
  gold_exposed      the instance's faulty line (spec gold.bug_line) appears in the displayed text.
  decoy_exposed     the signature line of any decoy (method-catalog line_start in the agent's workspace) is in the displayed line set.
  coverage(m)       share of the method's substantive lines (catalog span; lines that are not blank or brace-only) present in the
                    displayed line set; for overloads the best-covered span. CT-LANG-01's decoy is pinned to its declared overload by
                    parameter TYPES (names are cue-renamed in CD levels).
  full_gold_read    coverage(gold) >= 0.9.   full_decoy_read: max over decoys of coverage >= 0.9.
  top3_full_read    every method in the submitted top three has coverage >= 0.9 (F1 compliance; inspection measure for F0 too).
  cue_exposed       CG/CD runs only: a line that the run's cue level changes relative to C0 (from the variant patches) is in the
                    displayed line set. None for C0.
  decisive_evidence the instance's expected failure signature (spec expected_signature) appears in the displayed text.
  command segments  each bash command is split on unquoted ;, &&, ||, newlines; a segment is classified by its first program
                    (after env assignments): READ cat/sed/head/tail/nl/awk/less/more/bat/od/xxd; SEARCH grep/egrep/fgrep/rg/ag/ack/find/
                    'git grep'/locate; TEST 'defects4j test', ant, mvn test, gradle test; PROBE java/javac/jshell.
  file_reads, searches, test_executions, probe_executions   segment counts.  tests_executed / probe_executed: count > 0.
                    independent_probe_executed: a PROBE segment, or a 'defects4j test -t' whose target is not the trigger test.
  lines_read        output lines of tool results whose command contains at least one READ segment.
  model_calls       model_stats.api_calls. tool_calls: tool calls issued (bash + submissions).
  tokens            summed response usage: input = prompt_tokens, output = completion_tokens, reasoning =
                    completion_tokens_details.reasoning_tokens (part of output), total = input + output, cached = cached prompt tokens.
  cost_usd          model_stats.instance_cost.  wall_time_s: commands.log duration_ms / 1000.
  gold_exposed_misranked   gold_exposed and answered and gold_rank != 1.  strong_signal: gold_exposed and rank1_category == DECOY.
  sufficiency_class efficient / cue_override / premature / guess (pre-registration): sufficient = gold_exposed and decoy_exposed and
                    decisive_evidence."""
import json, os, re, sys, glob, csv, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C, ct_status as S
KEY = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); SERVERS = json.load(open(f"{C.V3}/models/servers.json"))
INCLUDE_DIAG = "--include-diagnostic" in sys.argv
# Frozen ENTRY_POINT lists: methods on the documented call path from the trigger to the gold (spec `entry` chain and `facade`), excluding
# the gold and the declared decoys. Fixed before any GPT-5.6 run.
ENTRY_POINTS = {
 "CT-CHART-01": ["org.jfree.chart.axis.NumberAxis::configure", "org.jfree.chart.axis.NumberAxis::autoAdjustRange", "org.jfree.chart.axis.ValueAxis::getUpperBound"],
 "CT-LANG-01": ["org.apache.commons.lang3.StringUtils::splitByWholeSeparator", "org.apache.commons.lang3.StringUtils::splitByWholeSeparatorPreserveAllTokens"],
 "CT-CHART-03": ["org.jfree.chart.axis.NumberAxis::setAutoRangeIncludesZero", "org.jfree.chart.plot.XYPlot::getDataRange",
                 "org.jfree.chart.renderer.xy.AbstractXYItemRenderer::findDomainBounds", "org.jfree.data.general.DatasetUtilities::findDomainBounds"],
 "CT-CHART-02": ["org.jfree.chart.JFreeChart::createBufferedImage", "org.jfree.chart.JFreeChart::draw", "org.jfree.chart.plot.XYPlot::draw",
                 "org.jfree.chart.renderer.xy.XYBlockRenderer::drawItem", "org.jfree.chart.renderer.xy.AbstractXYItemRenderer::addEntity"]}
READ = {"cat", "sed", "head", "tail", "nl", "awk", "less", "more", "bat", "od", "xxd"}
SEARCH = {"grep", "egrep", "fgrep", "rg", "ag", "ack", "find", "locate"}
PROBE = {"java", "javac", "jshell"}
SPECS, CUELINES = {}, {}
def spec(iid):
    if iid not in SPECS: SPECS[iid] = json.load(open(f"{C.V3}/instances/{iid}/spec.json"))
    return SPECS[iid]
def norm(s): return re.sub(r"\s+", " ", s.replace("\r", "")).strip()
PREFIX = re.compile(r"^\s*(?:[^\s:]+?:)?\d+(?:[:\t-]\s?|\s{2,})")
def strip_prefix(line): return PREFIX.sub("", line, count=1)
def tool_text(content):
    t = content if isinstance(content, str) else json.dumps(content)
    m = re.search(r"<output>\n?(.*?)\n?</output>", t, re.S)
    return m.group(1) if m else t
def substantive(line): return bool(re.search(r"[A-Za-z0-9]", line))
def patch_lines(iid, level, sign):
    p = f"{C.V3}/instances/{iid}/build/{level}/variant.patch"; out = set()
    for l in open(p, errors="replace").read().replace("\r", "").split("\n"):
        if l.startswith(sign) and not l.startswith(sign * 3):
            n = norm(l[1:])
            if n and substantive(n): out.add(n)
    return out
def cue_lines(iid, level):
    if (iid, level) not in CUELINES: CUELINES[(iid, level)] = patch_lines(iid, level, "+") - patch_lines(iid, "C0", "+") if level != "C0" else set()
    return CUELINES[(iid, level)]
def split_segments(cmd):
    segs, cur, q, i = [], "", None, 0
    while i < len(cmd):
        ch = cmd[i]
        if q:
            cur += ch; q = None if ch == q else q
        elif ch in "'\"": q = ch; cur += ch
        elif ch in ";\n": segs.append(cur); cur = ""
        elif cmd[i:i + 2] in ("&&", "||"): segs.append(cur); cur = ""; i += 1
        else: cur += ch
        i += 1
    segs.append(cur); return [s.strip() for s in segs if s.strip()]
def classify_segment(seg, trigger_test):
    words = [w for w in re.split(r"\s+", seg.split("|")[0].strip()) if w]
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]): words.pop(0)
    if not words: return None, False
    prog = os.path.basename(words[0])
    if prog == "defects4j" and len(words) > 1 and words[1] == "test":
        m = re.search(r"-t\s+(\S+)", seg); target = m.group(1).strip("'\"") if m else None
        return "TEST", bool(target) and target != trigger_test
    if prog == "ant" or (prog in ("mvn", "gradle") and "test" in words): return "TEST", False
    if prog == "git" and len(words) > 1 and words[1] == "grep": return "SEARCH", False
    if prog in READ: return "READ", False
    if prog in SEARCH: return "SEARCH", False
    if prog in PROBE: return "PROBE", True
    return None, False
def catalog_spans(rd, key, decl=None):
    cat = rj(f"{rd}/method_catalog.json").get("methods", []); cls, meth = key.split("::")
    return [e for e in cat if e.get("class") == cls and e.get("method") == meth]
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def method_lines(rd, V, entry):
    p = os.path.join(rd, "workspace", V, entry["file"])
    try: src = open(p, errors="replace").read().replace("\r", "").split("\n")
    except Exception: return None
    return [norm(l) for l in src[entry["line_start"] - 1: entry["line_end"]]]
def param_types(text):
    """Parameter type list of a declaration (names, `final` and annotations dropped), so overload matching survives cue renames."""
    inner = text[text.index("(") + 1:] if "(" in text else text
    inner = inner.split(")")[0]
    out = []
    for p in [x.strip() for x in inner.split(",") if x.strip()]:
        toks = [w for w in re.split(r"\s+", re.sub(r"@\w+", "", p)) if w and w != "final"]
        if len(toks) >= 2: out.append(" ".join(toks[:-1]))
    return out
def matches_decl(ls, decl):
    if not decl: return True
    want = param_types("(" + decl + ")"); head = " ".join(ls[:4])
    got = param_types(head[head.index("("):]) if "(" in head else []
    return bool(want) and got[-len(want):] == want
def coverage(rd, V, key, shown, decl=None):
    best = 0.0
    for e in catalog_spans(rd, key):
        ls = method_lines(rd, V, e)
        if ls is None: continue
        if not matches_decl(ls, decl): continue
        sub = [l for l in ls if substantive(l)]
        if sub: best = max(best, sum(1 for l in sub if l in shown) / len(sub))
    return round(best, 3)
def signature_shown(rd, V, key, shown, decl=None):
    for e in catalog_spans(rd, key):
        ls = method_lines(rd, V, e)
        if ls and matches_decl(ls, decl) and ls[0] in shown: return True
    return False
def med(xs):
    xs = [x for x in xs if x is not None]; return st.median(xs) if xs else None
rows, diag_rows = [], []
for server, cfg in SERVERS.items():
    agent = cfg.get("agent_id", "mini-swe-claude"); is_diag = cfg.get("role") != "analysis"
    if is_diag and not INCLUDE_DIAG: continue
    for rd in sorted(glob.glob(f"{C.V3}/models/{server}/benchmark_runs/{agent}/CTV-*/run-*")):
        V = os.path.basename(os.path.dirname(rd)); K = KEY.get(V)
        if not K: continue
        iid = K["instance_id"]; sp = spec(iid); cls = S.classify(rd)
        man = rj(f"{rd}/run_manifest.json"); ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json")
        preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
        keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]
        behavioural = cls["kind"] == "behavioural"; answered = behavioural and cls["status"] == "completed" and len(keys) == 10
        gold_rank = ev.get("gold_rank") if answered else None
        top1 = keys[0] if answered else None
        cat = ("NO_ANSWER" if not answered else "GOLD" if top1 == K["gold"] else "DECOY" if top1 in K["decoys"]
               else "ENTRY_POINT" if top1 in ENTRY_POINTS.get(iid, []) else "OTHER")
        decoy_ranks = [keys.index(d) + 1 for d in K["decoys"] if answered and d in keys]
        msgs = traj.get("messages", []); trig = sp["trigger"]["test_class"] + "::" + sp["trigger"]["test_method"]
        outs, cmds, reads_out_lines = [], [], 0
        segc = {"READ": 0, "SEARCH": 0, "TEST": 0, "PROBE": 0}; indep_probe = False; pending = {}
        for m in msgs:
            if m.get("role") == "assistant":
                for tc in m.get("tool_calls") or []:
                    fn = (tc.get("function") or {}); name = fn.get("name")
                    try: args = json.loads(fn.get("arguments") or "{}")
                    except Exception: args = {}
                    cmd = args.get("command", "") if name == "bash" else ""; cmds.append((name, cmd))
                    kinds = set()
                    for seg in split_segments(cmd):
                        k, ind = classify_segment(seg, trig)
                        if k: segc[k] += 1; kinds.add(k); indep_probe = indep_probe or ind
                    pending[tc.get("id")] = kinds
            elif m.get("role") == "tool":
                txt = tool_text(m.get("content")); outs.append(txt)
                if "READ" in pending.get(m.get("tool_call_id"), set()): reads_out_lines += txt.count("\n") + 1
        shown_raw = "\n".join(outs).replace("\r", "")
        shown_lines = {norm(strip_prefix(l)) for l in shown_raw.split("\n")} | {norm(l) for l in shown_raw.split("\n")}
        shown_text = norm(" ".join(strip_prefix(l) for l in shown_raw.split("\n")))
        dec_decl = {d["class"] + "::" + d["method"]: d.get("decl") for d in sp["decoys"]}
        gold_exposed = norm(sp["gold"]["bug_line"]) in shown_text
        decoy_exposed = any(signature_shown(rd, V, d, shown_lines, dec_decl.get(d)) for d in K["decoys"])
        cov_gold = coverage(rd, V, K["gold"], shown_lines); cov_decoy = max([coverage(rd, V, d, shown_lines, dec_decl.get(d)) for d in K["decoys"]] or [0.0])
        top3_full = answered and all(coverage(rd, V, k, shown_lines, dec_decl.get(k)) >= 0.9 for k in keys[:3])
        cl = cue_lines(iid, K["level"]); cue_exp = (any(l in shown_lines for l in cl)) if K["level"] != "C0" else None
        decisive = norm(sp["expected_signature"]) in shown_text
        usage = [((m.get("extra") or {}).get("response") or {}).get("usage") or {} for m in msgs if m.get("role") == "assistant"]
        tin = sum(u.get("prompt_tokens") or 0 for u in usage); tout = sum(u.get("completion_tokens") or 0 for u in usage)
        treas = sum(((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0) for u in usage)
        tcached = sum(((u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0) for u in usage)
        ms = (traj.get("info") or {}).get("model_stats") or {}
        try: dur = int(re.search(r"duration_ms: (\d+)", open(f"{rd}/commands.log").read()).group(1)) / 1000
        except Exception: dur = None
        correct = bool(answered and gold_rank == 1); sufficient = gold_exposed and decoy_exposed and decisive
        row = {"server": server, "model": cfg["model"], "reasoning_effort": cfg.get("reasoning_effort"), "F": "F1" if cfg["inspection"] == "1" else "F0",
               "variant_id": V, "run": os.path.basename(rd), "instance_id": iid, "level": K["level"], "condition": "C0" if K["level"] == "C0" else K["level"][:2],
               "stratum": K["stratum"], "status": cls["status"], "harness_status": cls["harness_status"], "status_kind": cls["kind"], "final_gap_s": cls["final_gap_s"],
               "answered": answered, "gold_rank": gold_rank, "acc1": int(correct), "rr": round(1 / gold_rank, 4) if gold_rank else 0.0,
               "rank1": top1, "rank1_category": cat, "best_decoy_rank": min(decoy_ranks) if decoy_ranks else None, "top3": keys[:3],
               "gold_exposed": gold_exposed, "decoy_exposed": decoy_exposed, "gold_coverage": cov_gold, "decoy_coverage": cov_decoy,
               "full_gold_read": cov_gold >= 0.9, "full_decoy_read": cov_decoy >= 0.9, "top3_full_read": bool(top3_full),
               "cue_exposed": cue_exp, "decisive_evidence_exposed": decisive,
               "tests_executed": segc["TEST"] > 0, "test_executions": segc["TEST"], "probe_executions": segc["PROBE"], "independent_probe_executed": indep_probe,
               "file_reads": segc["READ"], "searches": segc["SEARCH"], "lines_read": reads_out_lines,
               "model_calls": ms.get("api_calls"), "tool_calls": len(cmds), "chars_displayed": len(shown_raw),
               "input_tokens": tin, "output_tokens": tout, "reasoning_tokens": treas, "total_tokens": tin + tout, "cached_input_tokens": tcached,
               "cost_usd": ms.get("instance_cost"), "wall_time_s": dur,
               "gold_exposed_misranked": bool(gold_exposed and answered and gold_rank != 1), "strong_signal": bool(gold_exposed and cat == "DECOY"),
               "sufficiency_class": ("efficient" if correct else "cue_override") if sufficient else ("guess" if correct else "premature")}
        (diag_rows if is_diag else rows).append(row)
os.makedirs(f"{C.V3}/analysis", exist_ok=True)
def dump(rs, base):
    json.dump(rs, open(f"{base}.json", "w"), indent=1)
    if rs:
        with open(f"{base}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rs[0].keys())); w.writeheader(); w.writerows(rs)
dump(rows, f"{C.V3}/analysis/per_run")
if INCLUDE_DIAG: dump(diag_rows, f"{C.V3}/analysis/diagnostic_per_run")
cells = {}
for r in rows: cells.setdefault((r["model"], r["F"], r["instance_id"], r["condition"]), []).append(r)
summ = []
for (model, F, iid, cond), rs in sorted(cells.items()):
    b = [r for r in rs if r["status_kind"] == "behavioural"]; n = len(b); f = lambda k: sum(1 for r in b if r[k])
    summ.append({"model": model, "F": F, "instance_id": iid, "condition": cond, "attempted": len(rs), "excluded_infrastructure": sum(1 for r in rs if r["status_kind"] == "infrastructure"),
                 "excluded_integrity_or_unknown": sum(1 for r in rs if r["status_kind"] in ("integrity", "unknown")), "n": n,
                 "answered": f("answered"), "acc1": round(sum(r["acc1"] for r in b) / n, 3) if n else None, "mrr": round(sum(r["rr"] for r in b) / n, 3) if n else None,
                 "gold_ranks": [r["gold_rank"] for r in b], "rank1_categories": [r["rank1_category"] for r in b],
                 "decoy_first": sum(1 for r in b if r["rank1_category"] == "DECOY"), "entry_first": sum(1 for r in b if r["rank1_category"] == "ENTRY_POINT"),
                 "other_first": sum(1 for r in b if r["rank1_category"] == "OTHER"), "no_answer": sum(1 for r in b if r["rank1_category"] == "NO_ANSWER"),
                 "gold_exposed": f("gold_exposed"), "gold_exposed_misranked": f("gold_exposed_misranked"), "strong_signal": f("strong_signal"),
                 "full_gold_read_rate": round(f("full_gold_read") / n, 3) if n else None, "full_decoy_read_rate": round(f("full_decoy_read") / n, 3) if n else None,
                 "top3_full_read_rate": round(f("top3_full_read") / n, 3) if n else None,
                 "cue_exposure_rate": (round(sum(1 for r in b if r["cue_exposed"]) / n, 3) if n else None) if cond != "C0" else None,
                 "test_execution_rate": round(f("tests_executed") / n, 3) if n else None, "probe_rate": round(f("independent_probe_executed") / n, 3) if n else None,
                 "decisive_evidence_rate": round(f("decisive_evidence_exposed") / n, 3) if n else None,
                 "median_tool_calls": med([r["tool_calls"] for r in b]), "median_reasoning_tokens": med([r["reasoning_tokens"] for r in b]),
                 "median_total_tokens": med([r["total_tokens"] for r in b]), "median_cost_usd": med([r["cost_usd"] for r in b]),
                 "total_cost_usd": round(sum(float(r["cost_usd"] or 0) for r in rs), 4), "median_wall_time_s": med([r["wall_time_s"] for r in b]),
                 "sufficiency_classes": {k: sum(1 for r in b if r["sufficiency_class"] == k) for k in ("efficient", "cue_override", "premature", "guess")}})
json.dump(summ, open(f"{C.V3}/analysis/summary_by_cell.json", "w"), indent=1)
# Pre-specified pilot contrasts (amendment A1): per instance and prompt arm.
#   CG: delta = Acc@1(C0) - Acc@1(CG).   CD: delta = decoy@1 rate(CD) - decoy@1 rate(C0)  (Acc@1 change also reported).
#   class: STRONG delta >= 2/3 | WEAK delta = 1/3 | NULL delta = 0 | INVERTED delta < 0   (n = 3 per cell; computed on rates otherwise:
#   STRONG >= 0.5, WEAK > 0, NULL = 0, INVERTED < 0). Baseline flags: CG with C0 Acc@1 = 0 is FLOOR; CD with C0 decoy@1 = 1 is CEILING.
def klass(d):
    if d is None: return None
    return "STRONG" if d >= 0.5 else "WEAK" if d > 1e-9 else "NULL" if abs(d) <= 1e-9 else "INVERTED"
by = {(s["model"], s["F"], s["instance_id"], s["condition"]): s for s in summ}; con = []
for (model, F, iid, cond), s in sorted(by.items()):
    if cond != "C0": continue
    for c in ("CG", "CD"):
        t = by.get((model, F, iid, c))
        if not t or not s["n"] or not t["n"]: continue
        dacc = round(s["acc1"] - t["acc1"], 3); d1 = round(t["decoy_first"] / t["n"] - s["decoy_first"] / s["n"], 3)
        d = dacc if c == "CG" else d1
        flag = "FLOOR" if c == "CG" and s["acc1"] == 0 else "CEILING" if c == "CD" and s["decoy_first"] == s["n"] else None
        con.append({"model": model, "F": F, "instance_id": iid, "contrast": f"C0 vs {c}", "delta": d, "class": klass(d), "baseline_flag": flag,
                    "acc1_C0": s["acc1"], f"acc1_{c}": t["acc1"], "delta_acc1": dacc, "decoy_first_C0": s["decoy_first"], f"decoy_first_{c}": t["decoy_first"],
                    "delta_decoy_first_rate": d1, f"gold_exposed_misranked_{c}": t["gold_exposed_misranked"], f"strong_signal_{c}": t["strong_signal"]})
json.dump(con, open(f"{C.V3}/analysis/contrasts.json", "w"), indent=1)
print(f"{len(rows)} analysis runs" + (f", {len(diag_rows)} diagnostic runs" if INCLUDE_DIAG else ""))
for c in summ:
    print(f"{c['model']:16s} {c['F']} {c['instance_id']:12s} {c['condition']:3s} n={c['n']}/{c['attempted']} Acc@1={c['acc1']} MRR={c['mrr']} ranks={c['gold_ranks']} "
          f"decoy1={c['decoy_first']} goldExpMis={c['gold_exposed_misranked']} fullGold={c['full_gold_read_rate']} tests={c['test_execution_rate']} cost=${c['total_cost_usd']}")
for c in con: print(f"CONTRAST {c['model']} {c['F']} {c['instance_id']} {c['contrast']}: delta={c['delta']} {c['class']} {c['baseline_flag'] or ''}")
