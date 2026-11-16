"""Analysis-only copy of the frozen mx_metrics helper block (parsing, location-aware display matching, command classification, catalog
spans). Used by retrospective mining; the frozen mx_metrics.py is not imported (it runs on import) and not modified."""
import json, os, re, shlex
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
