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
  displayed text    the concatenated tool outputs the model received (tool message content), line-number and path prefixes stripped
                    (cat -n, nl, grep -n, grep -rn incl. context lines 'File.java-12-', path-only 'File.java:'), whitespace-normalised.
  displayed(F, i)   LOCATION-AWARE (amendment A2): line i of workspace file F counts as displayed when an output line attributed to F
                    (grep path prefix, or the command names F) shows it with its line number, or an UNNUMBERED output block shows it
                    together with its real neighbouring non-blank lines of F (prev,cur,next), or with one substantive neighbour (range
                    edges). A numbered output line credits only its own line number (A3).
  gold_exposed      the instance's faulty line for the run's level (spec gold.bug_line with that level's gold-method renames applied;
                    unique in the source tree) appears in the displayed text.
  decoy_exposed     displayed(F, line_start) for the signature line of any decoy (method catalog of the agent's workspace).
  coverage(m)       share of the method's substantive lines (catalog span; lines that are not blank or brace-only) with displayed(F, i);
                    for overloads the best-covered span. CT-LANG-01's decoy is pinned to its declared overload by parameter TYPES.
  full_gold_read    coverage(gold) >= 0.9.   full_decoy_read: max over decoys of coverage >= 0.9.
  top3_full_read    every method in the submitted top three has coverage >= 0.9 (F1 compliance; inspection measure for F0 too).
  cue_exposed       CG/CD runs only: displayed(F, i) for a cue line, i.e. a '+' line of the level's variant patch that C0's patch does not
                    add, located at its file and new line number from the hunk headers. None for C0.
  decisive_evidence the instance's expected failure signature (spec expected_signature) appears in the displayed text.
  command segments  each bash command is split on unquoted ;, &&, ||, newlines; wrappers are peeled (env/VAR=, time, timeout N, nohup,
                    command, exec, nice, a leading '(' or '{', and 'bash|sh|zsh -c/-lc <inner>' recursively); a segment is classified by
                    its first program: READ cat/sed/head/tail/nl/awk/less/more/bat/od/xxd; SEARCH grep/egrep/fgrep/rg/ag/ack/find/
                    'git grep'/locate; TEST 'defects4j test', ant, mvn test, gradle test; PROBE java/javac/jshell (not -version/-help).
  file_reads, searches, test_executions, probe_executions   segment counts.  tests_executed / probe_executed: count > 0.
                    independent_probe_executed: a PROBE segment, or a 'defects4j test -t' whose target is not the trigger test.
  lines_read        output lines of tool results whose command contains at least one READ segment.
  model_calls       model_stats.api_calls. tool_calls: tool calls issued (bash + submissions).
  tokens            summed response usage: input = prompt_tokens, output = completion_tokens, reasoning =
                    completion_tokens_details.reasoning_tokens (part of output), total = input + output, cached = cached prompt tokens.
  cost_usd          model_stats.instance_cost.  wall_time_s: commands.log duration_ms / 1000.
  gold_exposed_misranked   gold_exposed and answered and gold_rank != 1.  strong_signal: gold_exposed and rank1_category == DECOY.
  sufficiency_class answered runs: efficient / cue_override / premature / guess. Sufficient evidence (design §4.5, A3) = the faulty line
                    (gold_exposed) AND the decoy body (full_decoy_read) AND the observed failure value or a refuting test
                    (decisive_evidence or independent_probe_executed). Runs without an answer: no_answer (A2).
  inclusion         a run is counted only if the driver's ledger (diagnostic/block_<server>.jsonl, last record) says verdict 'valid' AND its
                    status kind is behavioural; contaminated / integrity / identity / unchecked runs are excluded and listed (A2).
  budget overruns   over_tool_budget: tool_calls > 50; over_test_budget: test_executions > 5 (recorded, not enforced, as in earlier runs)."""
import json, os, re, sys, glob, csv, shlex, statistics as st
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
WRAP = {"env", "time", "nohup", "command", "exec", "nice", "stdbuf", "builtin"}
SPECS, CUELINES, BUGLINES, FILECACHE = {}, {}, {}, {}
def spec(iid):
    if iid not in SPECS: SPECS[iid] = json.load(open(f"{C.V3}/instances/{iid}/spec.json"))
    return SPECS[iid]
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def norm(s): return re.sub(r"\s+", " ", s.replace("\r", "")).strip()
def substantive(line): return bool(re.search(r"[A-Za-z0-9]", line))
NUMRE = re.compile(r"^\s*(?:(?P<path>[^\s:]*\.[A-Za-z]+)[:-])?(?P<num>\d+)(?:[:\t-]\s?|\s{2,})(?P<rest>.*)$")
PATHONLY = re.compile(r"^(?P<path>[^\s:]*\.(?:java|xml|txt|properties|html|md)):(?P<rest>.*)$")
def parse_line(l):
    m = NUMRE.match(l)
    if m: return int(m.group("num")), m.group("path"), norm(m.group("rest"))
    m = PATHONLY.match(l)
    if m: return None, m.group("path"), norm(m.group("rest"))
    return None, None, norm(l)
def tool_text(content):
    t = content if isinstance(content, str) else json.dumps(content)
    m = re.search(r"<output>\n?(.*?)\n?</output>", t, re.S)
    return m.group(1) if m else t
def patch_plus(iid, level):
    """'+' lines of a level's variant patch with their (file, new line number)."""
    out, f, ln = [], None, 0
    for l in open(f"{C.V3}/instances/{iid}/build/{level}/variant.patch", errors="replace").read().replace("\r", "").split("\n"):
        if l.startswith("+++ b/"): f = l[6:].strip(); continue
        if l.startswith("--- ") or l.startswith("diff ") or l.startswith("index "): continue
        h = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", l)
        if h: ln = int(h.group(1)); continue
        if f is None: continue
        if l.startswith("+"): out.append((f, ln, norm(l[1:]))); ln += 1
        elif l.startswith("-"): pass
        else: ln += 1
    return out
def cue_lines(iid, level):
    if (iid, level) not in CUELINES:
        if level == "C0": CUELINES[(iid, level)] = []
        else:
            c0 = {t for _, _, t in patch_plus(iid, "C0")}
            CUELINES[(iid, level)] = [(f, ln, t) for f, ln, t in patch_plus(iid, level) if t and substantive(t) and t not in c0]
    return CUELINES[(iid, level)]
def level_bug_line(iid, level):
    if (iid, level) not in BUGLINES:
        sp = spec(iid); G = sp["gold"]; bl = G["bug_line"]
        for r in sp["levels"][level].get("renames", []):
            if r.get("scope") == "method" and r.get("method") == G["method"] and r.get("file", G["file"]) == G["file"]:
                bl = C._rename_text(bl, r["map"])
        plus = {t for _, _, t in patch_plus(iid, level)}
        assert norm(bl) in plus, f"{iid} {level}: derived faulty line {bl!r} is not added by the level patch"
        BUGLINES[(iid, level)] = norm(bl)
    return BUGLINES[(iid, level)]
def peel(words):
    """Drop env assignments and wrapper programs; return (words, inner_command_or_None)."""
    while words:
        w = words[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w) or w in ("(", "{", "do", "then", "else", "!") : words = words[1:]; continue
        if w.startswith("(") and len(w) > 1: words = [w[1:]] + words[1:]; continue
        if os.path.basename(w) in WRAP: words = words[1:]; continue
        if os.path.basename(w) == "timeout":
            words = words[1:]
            while words and (words[0].startswith("-") or re.match(r"^\d+[smhd]?$", words[0])): words = words[1:]
            continue
        if os.path.basename(w) in ("bash", "sh", "zsh") and len(words) > 1:
            for i, a in enumerate(words[1:], 1):
                if a.startswith("-") and "c" in a[1:] and i + 1 < len(words): return [], words[i + 1]
            return words, None
        break
    return words, None
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
    segs.append(cur); return [x.strip() for x in segs if x.strip()]
def classify_command(cmd, trigger_test, depth=0):
    """List of (kind, independent_probe) for every segment of a bash command, recursing into bash -c strings."""
    res = []
    for seg in split_segments(cmd):
        head = seg.split("|")[0].strip()
        try: words = shlex.split(head)
        except ValueError: words = head.split()
        words, inner = peel(words)
        if inner is not None and depth < 3: res += classify_command(inner, trigger_test, depth + 1); continue
        if not words: continue
        prog = os.path.basename(words[0])
        if prog == "defects4j" and len(words) > 1 and words[1] == "test":
            t = None
            for i, w in enumerate(words):
                if w == "-t" and i + 1 < len(words): t = words[i + 1].strip("'\")")
                elif w.startswith("-t") and len(w) > 2: t = w[2:].strip("'\")")
            res.append(("TEST", bool(t) and t != trigger_test)); continue
        if prog == "ant" or (prog in ("mvn", "gradle") and "test" in words): res.append(("TEST", False)); continue
        if prog == "git" and len(words) > 1 and words[1] == "grep": res.append(("SEARCH", False)); continue
        if prog in READ: res.append(("READ", False)); continue
        if prog in SEARCH: res.append(("SEARCH", False)); continue
        if prog in PROBE and not (words[1:] and all(w.lstrip("-") in ("version", "help", "h", "showversion") for w in words[1:])):
            res.append(("PROBE", True)); continue
    return res
def file_lines(rd, V, rel):
    k = (rd, rel)
    if k not in FILECACHE:
        try: FILECACHE[k] = [norm(l) for l in open(os.path.join(rd, "workspace", V, rel), errors="replace").read().replace("\r", "").split("\n")]
        except Exception: FILECACHE[k] = None
    return FILECACHE[k]
class Shown:
    """File-attributed, location-aware index of everything the model was shown."""
    def __init__(self):
        self.num, self.t3, self.p2 = {}, {}, {}
    def add_output(self, txt, cmd_files):
        seqs = {}
        for raw in txt.replace("\r", "").split("\n"):
            n, path, line = parse_line(raw)
            if not line: continue
            bases = {os.path.basename(path)} if path else set(cmd_files)
            for b in bases:
                if n is not None: self.num.setdefault(b, set()).add((n, line)); seqs.setdefault(b, []).append(None)   # A3: numbered lines credit only their own number
                else: seqs.setdefault(b, []).append(line)
        for b, sq in seqs.items():
            t3 = self.t3.setdefault(b, set()); p2 = self.p2.setdefault(b, set())
            for i in range(len(sq)):
                if i + 1 < len(sq) and None not in sq[i:i + 2]: p2.add((sq[i], sq[i + 1]))
                if i + 2 < len(sq) and None not in sq[i:i + 3]: t3.add((sq[i], sq[i + 1], sq[i + 2]))
    def displayed(self, L, rel, i):
        """L: normalised lines of workspace file rel; i: 1-based line number."""
        if not L or i < 1 or i > len(L): return False
        b = os.path.basename(rel); cur = L[i - 1]
        if not cur: return False
        if (i, cur) in self.num.get(b, ()): return True
        j = i - 2
        while j >= 0 and not L[j]: j -= 1
        k = i
        while k < len(L) and not L[k]: k += 1
        prev = L[j] if j >= 0 else None; nxt = L[k] if k < len(L) else None
        if prev is not None and nxt is not None and (prev, cur, nxt) in self.t3.get(b, ()): return True
        if substantive(cur):
            if prev is not None and substantive(prev) and (prev, cur) in self.p2.get(b, ()): return True
            if nxt is not None and substantive(nxt) and (cur, nxt) in self.p2.get(b, ()): return True
        return False
def param_types(text):
    """Parameter type list of a declaration (names, `final` and annotations dropped), so overload matching survives cue renames."""
    inner = text[text.index("(") + 1:] if "(" in text else text
    inner = inner.split(")")[0]; out = []
    for p in [x.strip() for x in inner.split(",") if x.strip()]:
        toks = [w for w in re.split(r"\s+", re.sub(r"@\w+", "", p)) if w and w != "final"]
        if len(toks) >= 2: out.append(" ".join(toks[:-1]))
    return out
def matches_decl(ls, decl):
    if not decl: return True
    want = param_types("(" + decl + ")"); head = " ".join(ls[:4])
    got = param_types(head[head.index("("):]) if "(" in head else []
    return bool(want) and got[-len(want):] == want
def spans(rd, V, key, decl=None):
    cls, meth = key.split("::"); out = []
    for e in rj(f"{rd}/method_catalog.json").get("methods", []):
        if e.get("class") == cls and e.get("method") == meth:
            L = file_lines(rd, V, e["file"])
            if L is None: continue
            if matches_decl(L[e["line_start"] - 1: e["line_start"] + 3], decl): out.append((e, L))
    return out
def coverage(rd, V, key, shown, decl=None):
    best = 0.0
    for e, L in spans(rd, V, key, decl):
        idx = [i for i in range(e["line_start"], e["line_end"] + 1) if substantive(L[i - 1])]
        if idx: best = max(best, sum(1 for i in idx if shown.displayed(L, e["file"], i)) / len(idx))
    return round(best, 3)
def signature_shown(rd, V, key, shown, decl=None):
    return any(shown.displayed(L, e["file"], e["line_start"]) for e, L in spans(rd, V, key, decl))
def med(xs):
    xs = [x for x in xs if x is not None]; return st.median(xs) if xs else None
def verdicts(server):
    v, p = {}, f"{C.V3}/diagnostic/block_{server}.jsonl"
    if os.path.exists(p):
        for l in open(p):
            try: r = json.loads(l); v[r["run"]] = r["verdict"]
            except Exception: pass
    return v
rows, diag_rows = [], []
for server, cfg in SERVERS.items():
    agent = cfg.get("agent_id", "mini-swe-claude"); is_diag = cfg.get("role") != "analysis"
    if is_diag and not INCLUDE_DIAG: continue
    VERD = verdicts(server)
    for rd in sorted(glob.glob(f"{C.V3}/models/{server}/benchmark_runs/{agent}/CTV-*/run-*")):
        V = os.path.basename(os.path.dirname(rd)); K = KEY.get(V)
        if not K: continue
        iid = K["instance_id"]; sp = spec(iid); cls = S.classify(rd); run = os.path.basename(rd)
        verdict = VERD.get(f"{V}/{run}"); kind = cls["kind"]
        if kind == "behavioural" and verdict != "valid":
            kind = {"STOP_CONTAMINATION": "contaminated", "STOP_INTEGRITY": "integrity", None: "unchecked"}.get(verdict, "unchecked")
        ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json")
        preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
        keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]
        behavioural = kind == "behavioural"; answered = behavioural and cls["status"] == "completed" and len(keys) == 10
        gold_rank = ev.get("gold_rank") if answered else None
        top1 = keys[0] if answered else None
        cat = ("NO_ANSWER" if not answered else "GOLD" if top1 == K["gold"] else "DECOY" if top1 in K["decoys"]
               else "ENTRY_POINT" if top1 in ENTRY_POINTS.get(iid, []) else "OTHER")
        decoy_ranks = [keys.index(d) + 1 for d in K["decoys"] if answered and d in keys]
        msgs = traj.get("messages", []); trig = sp["trigger"]["test_class"] + "::" + sp["trigger"]["test_method"]
        outs, cmds, reads_out_lines, shown = [], [], 0, Shown()
        segc = {"READ": 0, "SEARCH": 0, "TEST": 0, "PROBE": 0}; indep_probe = False; pending = {}
        for m in msgs:
            if m.get("role") == "assistant":
                for tc in m.get("tool_calls") or []:
                    fn = (tc.get("function") or {}); name = fn.get("name")
                    try: args = json.loads(fn.get("arguments") or "{}")
                    except Exception: args = {}
                    cmd = args.get("command", "") if name == "bash" else ""; cmds.append((name, cmd)); kinds = set()
                    for k, ind in classify_command(cmd, trig):
                        segc[k] += 1; kinds.add(k); indep_probe = indep_probe or ind
                    pending[tc.get("id")] = (kinds, {os.path.basename(x) for x in re.findall(r"[\w./-]+\.(?:java|xml|txt|properties)", cmd)})
            elif m.get("role") == "tool":
                txt = tool_text(m.get("content")); outs.append(txt); kinds, files = pending.get(m.get("tool_call_id"), (set(), set()))
                shown.add_output(txt, files)
                if "READ" in kinds: reads_out_lines += txt.count("\n") + 1
        shown_raw = "\n".join(outs).replace("\r", "")
        shown_text = norm(" ".join(parse_line(l)[2] for l in shown_raw.split("\n")))
        dec_decl = {d["class"] + "::" + d["method"]: d.get("decl") for d in sp["decoys"]}
        gold_exposed = level_bug_line(iid, K["level"]) in shown_text
        decoy_exposed = any(signature_shown(rd, V, d, shown, dec_decl.get(d)) for d in K["decoys"])
        cov_gold = coverage(rd, V, K["gold"], shown); cov_decoy = max([coverage(rd, V, d, shown, dec_decl.get(d)) for d in K["decoys"]] or [0.0])
        top3_full = answered and all(coverage(rd, V, k, shown, dec_decl.get(k)) >= 0.9 for k in keys[:3])
        if K["level"] == "C0": cue_exp = None
        else: cue_exp = any(shown.displayed(file_lines(rd, V, f), f, ln) for f, ln, _ in cue_lines(iid, K["level"]))
        decisive = norm(sp["expected_signature"]) in shown_text
        usage = [((m.get("extra") or {}).get("response") or {}).get("usage") or {} for m in msgs if m.get("role") == "assistant"]
        tin = sum(u.get("prompt_tokens") or 0 for u in usage); tout = sum(u.get("completion_tokens") or 0 for u in usage)
        treas = sum(((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0) for u in usage)
        tcached = sum(((u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0) for u in usage)
        ms = (traj.get("info") or {}).get("model_stats") or {}
        try: dur = int(re.search(r"duration_ms: (\d+)", open(f"{rd}/commands.log").read()).group(1)) / 1000
        except Exception: dur = None
        correct = bool(answered and gold_rank == 1); sufficient = gold_exposed and cov_decoy >= 0.9 and (decisive or indep_probe)   # A3: design §4.5
        suff = ("no_answer" if not answered else ("efficient" if correct else "cue_override") if sufficient else ("guess" if correct else "premature"))
        row = {"server": server, "model": cfg["model"], "reasoning_effort": cfg.get("reasoning_effort"), "F": "F1" if cfg["inspection"] == "1" else "F0",
               "variant_id": V, "run": run, "instance_id": iid, "level": K["level"], "condition": "C0" if K["level"] == "C0" else K["level"][:2],
               "stratum": K["stratum"], "status": cls["status"], "harness_status": cls["harness_status"], "agent_exit_status": cls["agent_exit_status"],
               "driver_verdict": verdict, "status_kind": kind, "included": behavioural, "final_gap_s": cls["final_gap_s"],
               "answered": answered, "gold_rank": gold_rank, "acc1": int(correct), "rr": round(1 / gold_rank, 4) if gold_rank else 0.0,
               "rank1": top1, "rank1_category": cat, "best_decoy_rank": min(decoy_ranks) if decoy_ranks else None, "top3": keys[:3],
               "gold_exposed": gold_exposed, "decoy_exposed": decoy_exposed, "gold_coverage": cov_gold, "decoy_coverage": cov_decoy,
               "full_gold_read": cov_gold >= 0.9, "full_decoy_read": cov_decoy >= 0.9, "top3_full_read": bool(top3_full),
               "cue_exposed": cue_exp, "decisive_evidence_exposed": decisive,
               "tests_executed": segc["TEST"] > 0, "test_executions": segc["TEST"], "probe_executions": segc["PROBE"], "independent_probe_executed": indep_probe,
               "file_reads": segc["READ"], "searches": segc["SEARCH"], "lines_read": reads_out_lines,
               "model_calls": ms.get("api_calls"), "tool_calls": len(cmds), "chars_displayed": len(shown_raw),
               "input_tokens": tin, "output_tokens": tout, "reasoning_tokens": treas, "total_tokens": tin + tout, "cached_input_tokens": tcached,
               "cost_usd": ms.get("instance_cost"), "wall_time_s": dur, "over_tool_budget": len(cmds) > 50, "over_test_budget": segc["TEST"] > 5,
               "gold_exposed_misranked": bool(gold_exposed and answered and gold_rank != 1), "strong_signal": bool(gold_exposed and cat == "DECOY"),
               "sufficiency_class": suff}
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
    b = [r for r in rs if r["included"]]; n = len(b); f = lambda k: sum(1 for r in b if r[k])
    summ.append({"model": model, "F": F, "instance_id": iid, "condition": cond, "attempted": len(rs),
                 "excluded_infrastructure": sum(1 for r in rs if r["status_kind"] == "infrastructure"),
                 "excluded_other": {k: sum(1 for r in rs if r["status_kind"] == k) for k in ("contaminated", "integrity", "unchecked", "unknown") if any(r["status_kind"] == k for r in rs)},
                 "n": n, "n_note": None if n == 3 else f"n={n} (planned 3)",
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
                 "over_tool_budget": f("over_tool_budget"), "over_test_budget": f("over_test_budget"),
                 "median_tool_calls": med([r["tool_calls"] for r in b]), "median_reasoning_tokens": med([r["reasoning_tokens"] for r in b]),
                 "median_total_tokens": med([r["total_tokens"] for r in b]), "median_cost_usd": med([r["cost_usd"] for r in b]),
                 "total_cost_usd": round(sum(float(r["cost_usd"] or 0) for r in rs), 4), "median_wall_time_s": med([r["wall_time_s"] for r in b]),
                 "sufficiency_classes": {k: sum(1 for r in b if r["sufficiency_class"] == k) for k in ("efficient", "cue_override", "premature", "guess", "no_answer")}})
json.dump(summ, open(f"{C.V3}/analysis/summary_by_cell.json", "w"), indent=1)
# Pre-specified pilot contrasts (amendment A1): per instance and prompt arm.
#   CG: delta = Acc@1(C0) - Acc@1(CG).   CD: delta = decoy@1 rate(CD) - decoy@1 rate(C0)  (Acc@1 change also reported).
#   class (A1 cuts on rates, A3): STRONG delta >= 2/3 | WEAK 0 < delta < 2/3 | NULL delta = 0 | INVERTED delta < 0; cells with n != 3 are
#   flagged (n_flag). Baseline flags: CG with C0 Acc@1 = 0 is FLOOR; CD with C0 decoy@1 = 1 is CEILING.
def klass(d):
    if d is None: return None
    return "STRONG" if d >= 2 / 3 - 1e-9 else "WEAK" if d > 1e-9 else "NULL" if abs(d) <= 1e-9 else "INVERTED"   # A1 cuts, A3
by = {(s_["model"], s_["F"], s_["instance_id"], s_["condition"]): s_ for s_ in summ}; con = []
for (model, F, iid, cond), s0 in sorted(by.items()):
    if cond != "C0": continue
    for c in ("CG", "CD"):
        t = by.get((model, F, iid, c))
        if not t or not s0["n"] or not t["n"]: continue
        dacc = round(s0["acc1"] - t["acc1"], 3); d1 = round(t["decoy_first"] / t["n"] - s0["decoy_first"] / s0["n"], 3)
        d = dacc if c == "CG" else d1
        flag = "FLOOR" if c == "CG" and s0["acc1"] == 0 else "CEILING" if c == "CD" and s0["decoy_first"] == s0["n"] else None
        con.append({"model": model, "F": F, "instance_id": iid, "contrast": f"C0 vs {c}", "delta": d, "class": klass(d), "baseline_flag": flag,
                    "n_flag": None if (s0["n"] == 3 and t["n"] == 3) else f"unequal n (C0 {s0['n']}, {c} {t['n']}): class from rates with the A1 cuts",
                    "n_C0": s0["n"], f"n_{c}": t["n"], "acc1_C0": s0["acc1"], f"acc1_{c}": t["acc1"], "delta_acc1": dacc, "decoy_first_C0": s0["decoy_first"],
                    f"decoy_first_{c}": t["decoy_first"], "delta_decoy_first_rate": d1, f"gold_exposed_misranked_{c}": t["gold_exposed_misranked"],
                    f"strong_signal_{c}": t["strong_signal"]})
json.dump(con, open(f"{C.V3}/analysis/contrasts.json", "w"), indent=1)
print(f"{len(rows)} analysis runs" + (f", {len(diag_rows)} diagnostic runs" if INCLUDE_DIAG else ""))
for c in summ:
    print(f"{c['model']:16s} {c['F']} {c['instance_id']:12s} {c['condition']:3s} n={c['n']}/{c['attempted']} Acc@1={c['acc1']} MRR={c['mrr']} ranks={c['gold_ranks']} "
          f"decoy1={c['decoy_first']} goldExpMis={c['gold_exposed_misranked']} fullGold={c['full_gold_read_rate']} tests={c['test_execution_rate']} cost=${c['total_cost_usd']}")
for c in con: print(f"CONTRAST {c['model']} {c['F']} {c['instance_id']} {c['contrast']}: delta={c['delta']} {c['class']} {c['baseline_flag'] or ''}")
