"""mechanism-search-v1 per-run measures and per-instance screening classes (definitions frozen before the first run in this root).
Reuses, verbatim, the cue-trust-v3 helpers that passed two adversarial reviews and blind hand-label checks (line parsing, location-aware
file-attributed display matching, command classification, method spans from the run's method catalog, ct_status run classification).
Instance facts come from review/VARIANT_KEY.json (gold, decoys, entry_points, fault_lines, evidence, expected_signature, trigger).
Usage: mx_metrics.py [--include-diagnostic]  -> analysis/per_run.json|csv, analysis/summary_by_instance.json
Run measures:
  included            driver ledger verdict 'valid' and behavioural status (ct_status); others excluded and listed.
  answered/gold_rank/acc1/rr/rank1_category   as in cue-trust-v3: GOLD | DECOY (declared decoy/competitor) | ENTRY_POINT | OTHER | NO_ANSWER.
  gold_exposed        a fault line of the gold (as it reads in the variant) appears in the displayed text.
  gold_coverage / full_gold_read   location-aware coverage of the gold's catalog span (>= 0.9 = full).
  decoy_exposed / full_decoy_read  signature displayed / best decoy coverage >= 0.9.
  evidence_displayed  any declared external-evidence method's span reached coverage >= 0.5 (retrieval proxy; integration is judged by
                      the failure-mode classification, not here).
  tests_executed, failure_values_seen (expected_signature text displayed), independent_probe_executed, tool/model calls, tokens, cost, wall.
  gold_exposed_misranked = gold_exposed and answered and gold_rank != 1  (the target phenomenon: discovered, inspected, still misranked).
Instance screening class (pre-registered): PROMISING if Acc@1 <= 1/3, or >=2 runs gold-exposed AND >=2 misranked, or the same wrong
method above gold in >=2 of 3 runs; WEAK if exactly one of three mislocalizes; NULL if all rank the gold first."""

import json, os, re, sys, glob, csv, shlex, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C, ct_status as S
KEY = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); SERVERS = json.load(open(f"{C.V3}/models/servers.json"))
INCLUDE_DIAG = "--include-diagnostic" in sys.argv
READ = {"cat", "sed", "head", "tail", "nl", "awk", "less", "more", "bat", "od", "xxd"}
SEARCH = {"grep", "egrep", "fgrep", "rg", "ag", "ack", "find", "locate"}
PROBE = {"java", "javac", "jshell"}
WRAP = {"env", "time", "nohup", "command", "exec", "nice", "stdbuf", "builtin"}
FILECACHE = {}
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

def verdicts(server):
    v, p = {}, f"{C.V3}/diagnostic/block_{server}.jsonl"
    if os.path.exists(p):
        for l in open(p):
            try: r = json.loads(l); v[r["run"]] = r["verdict"]
            except Exception: pass
    return v
def as_list(x): return x if isinstance(x, list) else ([x] if x else [])
rows, diag_rows = [], []
for server, cfg in SERVERS.items():
    agent = cfg.get("agent_id"); is_diag = cfg.get("role") != "analysis"
    if is_diag and not INCLUDE_DIAG: continue
    VERD = verdicts(server)
    for rd in sorted(glob.glob(f"{C.V3}/models/{server}/benchmark_runs/{agent}/CTV-*/run-*")):
        V = os.path.basename(os.path.dirname(rd)); K = KEY.get(V)
        if not K: continue
        cls = S.classify(rd); run = os.path.basename(rd); verdict = VERD.get(f"{V}/{run}"); kind = cls["kind"]
        if kind == "behavioural" and verdict != "valid":
            kind = {"STOP_CONTAMINATION": "contaminated", "STOP_INTEGRITY": "integrity", None: "unchecked"}.get(verdict, "unchecked")
        ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json")
        preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
        keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]
        golds = as_list(K["gold"]); decoys = as_list(K.get("decoys")); entries = as_list(K.get("entry_points")); evid = as_list(K.get("evidence"))
        behavioural = kind == "behavioural"; answered = behavioural and cls["status"] == "completed" and len(keys) == 10
        gold_rank = ev.get("gold_rank") if answered else None; top1 = keys[0] if answered else None
        cat = ("NO_ANSWER" if not answered else "GOLD" if top1 in golds else "DECOY" if top1 in decoys else "ENTRY_POINT" if top1 in entries else "OTHER")
        above = keys[:(gold_rank - 1)] if (answered and gold_rank) else (keys if answered else [])
        msgs = traj.get("messages", []); trig = K.get("trigger", "")
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
        gold_exposed = any(norm(fl) in shown_text for fl in as_list(K.get("fault_lines")) if norm(fl))
        cov_gold = max([coverage(rd, V, g, shown) for g in golds] or [0.0])
        decoy_exposed = any(signature_shown(rd, V, d, shown) for d in decoys)
        cov_decoy = max([coverage(rd, V, d, shown) for d in decoys] or [0.0])
        evid_disp = any(coverage(rd, V, e, shown) >= 0.5 for e in evid if "::" in e)
        decisive = bool(K.get("expected_signature")) and norm(K["expected_signature"]) in shown_text
        usage = [((m.get("extra") or {}).get("response") or {}).get("usage") or {} for m in msgs if m.get("role") == "assistant"]
        tin = sum(u.get("prompt_tokens") or 0 for u in usage); tout = sum(u.get("completion_tokens") or 0 for u in usage)
        treas = sum(((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0) for u in usage)
        ms = (traj.get("info") or {}).get("model_stats") or {}
        try: dur = int(re.search(r"duration_ms: (\d+)", open(f"{rd}/commands.log").read()).group(1)) / 1000
        except Exception: dur = None
        correct = bool(answered and gold_rank == 1)
        row = {"server": server, "variant_id": V, "run": run, "instance_id": K["instance_id"], "group": K.get("group"), "mechanism": K.get("mechanism"),
               "tier": K.get("tier"), "project": K.get("project"), "status": cls["status"], "harness_status": cls["harness_status"], "driver_verdict": verdict,
               "status_kind": kind, "included": behavioural, "answered": answered, "gold_rank": gold_rank, "acc1": int(correct),
               "rr": round(1 / gold_rank, 4) if gold_rank else 0.0, "rank1": top1, "rank1_category": cat, "ranked_above_gold": above[:5],
               "gold_exposed": gold_exposed, "gold_coverage": cov_gold, "full_gold_read": cov_gold >= 0.9, "decoy_exposed": decoy_exposed,
               "decoy_coverage": cov_decoy, "full_decoy_read": cov_decoy >= 0.9, "evidence_displayed": evid_disp if evid else None,
               "tests_executed": segc["TEST"] > 0, "test_executions": segc["TEST"], "failure_values_seen": decisive, "independent_probe_executed": indep_probe,
               "file_reads": segc["READ"], "searches": segc["SEARCH"], "lines_read": reads_out_lines, "model_calls": ms.get("api_calls"), "tool_calls": len(cmds),
               "input_tokens": tin, "output_tokens": tout, "reasoning_tokens": treas, "total_tokens": tin + tout, "cost_usd": ms.get("instance_cost"),
               "wall_time_s": dur, "gold_exposed_misranked": bool(gold_exposed and answered and gold_rank != 1)}
        (diag_rows if is_diag else rows).append(row)
os.makedirs(f"{C.V3}/analysis", exist_ok=True)
def dump(rs, base):
    json.dump(rs, open(f"{base}.json", "w"), indent=1)
    if rs:
        with open(f"{base}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rs[0].keys())); w.writeheader(); w.writerows(rs)
dump(rows, f"{C.V3}/analysis/per_run")
if INCLUDE_DIAG: dump(diag_rows, f"{C.V3}/analysis/diagnostic_per_run")
by = collections.defaultdict(list)
for r in rows: by[(r["server"], r["variant_id"])].append(r)   # weaker-model-v1: one summary per (server/model, instance)
summ = []
for (SV, V), rs in sorted(by.items(), key=lambda kv: (kv[0][0], kv[1][0]["mechanism"] or "", kv[1][0]["instance_id"])):
    b = [r for r in rs if r["included"]]; n = len(b)
    acc = sum(r["acc1"] for r in b) / n if n else None
    exposed = sum(r["gold_exposed"] for r in b); mis = sum(1 for r in b if r["answered"] and r["gold_rank"] != 1)
    wrongs = collections.Counter(m for r in b if r["answered"] and r["gold_rank"] != 1 for m in r["ranked_above_gold"][:1])
    same_wrong = wrongs.most_common(1)[0][1] if wrongs else 0
    wrong_n = sum(1 for r in b if r["acc1"] == 0)
    if not n: klass = None
    elif (acc is not None and acc <= 1 / 3 + 1e-9) or (exposed >= 2 and mis >= 2) or (same_wrong >= 2 and n >= 3): klass = "PROMISING"
    elif wrong_n == 1: klass = "WEAK"
    elif wrong_n == 0: klass = "NULL"
    else: klass = "WEAK"
    summ.append({"server": SV, "model": SERVERS[SV]["model"], "variant_id": V, "instance_id": rs[0]["instance_id"], "mechanism": rs[0]["mechanism"], "tier": rs[0]["tier"], "project": rs[0]["project"],
                 "attempted": len(rs), "n": n, "acc1": round(acc, 3) if acc is not None else None, "mrr": round(sum(r["rr"] for r in b) / n, 3) if n else None,
                 "gold_ranks": [r["gold_rank"] for r in b], "rank1_categories": [r["rank1_category"] for r in b], "gold_exposed": exposed,
                 "gold_exposed_misranked": sum(r["gold_exposed_misranked"] for r in b), "most_common_wrong_top": wrongs.most_common(1)[0][0] if wrongs else None,
                 "same_wrong_count": same_wrong, "full_gold_read": sum(r["full_gold_read"] for r in b), "tests_executed": sum(r["tests_executed"] for r in b),
                 "evidence_displayed": sum(1 for r in b if r["evidence_displayed"]), "median_tool_calls": st.median([r["tool_calls"] for r in b]) if b else None,
                 "median_reasoning_tokens": st.median([r["reasoning_tokens"] for r in b]) if b else None,
                 "cost_usd": round(sum(float(r["cost_usd"] or 0) for r in rs), 4), "screening_class": klass})
json.dump(summ, open(f"{C.V3}/analysis/summary_by_instance.json", "w"), indent=1)
print(f"{len(rows)} analysis runs" + (f", {len(diag_rows)} diagnostic" if INCLUDE_DIAG else ""))
for s_ in summ: print(f"{s_['model']:13s} {s_['mechanism'] or '-':10s} {s_['instance_id'][:34]:34s} n={s_['n']}/{s_['attempted']} Acc@1={s_['acc1']} ranks={s_['gold_ranks']} cats={s_['rank1_categories']} goldExpMis={s_['gold_exposed_misranked']} class={s_['screening_class']} ${s_['cost_usd']}")
