"""cue-trust-v3 out-of-workspace and cross-variant leakage scan (observable commands and outputs only).
Usage: scan_v3.py <run_dir>   -> prints JSON {flagged_calls, contaminated, reasons}
A bash call is FLAGGED when it: refers to an absolute path outside the run's own workspace (realpath, so /tmp and /private/tmp agree);
cds outside the workspace or uses a relative (..), home (~, $HOME) or root path that resolves outside it (cd targets are followed, A3); names a harness or package file; checks out or clones a repository; lists the
environment or processes (env, printenv, set, ps, lsof, netstat); or uses a network tool or the local API (curl, wget, nc, localhost,
127.0.0.1).
CONTAMINATED (pre-registered exclusion; the driver halts) when any of:
  - a `defects4j checkout` or `git clone` is run (the fixed or pristine revision is forbidden by the prompt);
  - a command touches the Defects4J repository tree outside framework/ (it holds the pristine checkouts, project repositories and
    every run directory; the agent's workspace is outside it, and framework/ holds the legitimate defects4j tool);
  - any output shows another variant's id, or a cue identifier/comment that belongs to a DIFFERENT cue level of the same instance
    (distinctive: absent from the pristine source);
  - a flagged call's output shows harness content (gold labels, rankings, manifests, unified-diff headers) or a pristine-only
    source line, i.e. a line the variant patch removed that exists nowhere else in the variant tree (A2, A3);
  - ANY call's output shows a narrow harness marker (gold labels, submissions, manifests, VARIANT_KEY), the experiment name, or a
    path into the Defects4J repository tree outside framework/ (A3; e.g. a process listing of the harness)."""
import json, os, re, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
rd = sys.argv[1]; vid = os.path.basename(os.path.dirname(rd))
key = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); K = key[vid]; IID = K["instance_id"]
spec = json.load(open(f"{C.V3}/instances/{IID}/spec.json"))
prompt = open(os.path.join(rd, "prompt.txt"), errors="replace").read()
m = re.search(r"repository path:\s*(\S+)", prompt); ws = os.path.realpath(m.group(1)) if m else None
ws_alias = {ws, os.path.normpath(m.group(1))} if m else set()
def norm(s): return re.sub(r"\s+", " ", s.replace("\r", "")).strip()
SRC = os.path.join(spec["fresh"], spec["src_root"])
def distinctive(t):
    if len(t) < 4: return False
    if " " in t: return subprocess.run(["grep", "-rqF", t, SRC]).returncode != 0
    return subprocess.run(["grep", "-rqw", t, SRC]).returncode != 0
def tokens(level):
    lv = spec["levels"][level]; out = set()
    for r in lv.get("renames", []): out |= set(r["map"].values())
    c = norm(lv["comment"].lstrip("/ "))
    if c: out.add(c)
    return out
own = tokens(K["level"]); other = set()
for lvl in spec["levels"]:
    if lvl != K["level"]: other |= tokens(lvl)
other = {t for t in other - own if distinctive(t)}
# pristine-only lines: removed by this level's patch and absent from the variant's version of the patched files
patch = open(f"{C.V3}/instances/{IID}/build/{K['level']}/variant.patch", errors="replace").read().replace("\r", "")
removed, files = set(), set()
for l in patch.split("\n"):
    if l.startswith("+++ b/"): files.add(l[6:].strip())
    elif l.startswith("-") and not l.startswith("---") and len(norm(l[1:])) >= 8: removed.add(norm(l[1:]))
variant_lines = set()
for f in files:
    try: variant_lines |= {norm(x) for x in open(os.path.join(rd, "workspace", vid, f), errors="replace").read().replace("\r", "").split("\n")}
    except Exception: pass
import glob
other_lines = set()
for f_ in glob.glob(os.path.join(spec["fresh"], "**", "*.java"), recursive=True):
    if os.path.relpath(f_, spec["fresh"]) in files: continue
    try: other_lines |= {norm(x) for x in open(f_, errors="replace").read().replace("\r", "").split("\n")}
    except Exception: pass
PRISTINE_ONLY = removed - variant_lines - other_lines   # A3: absent from every file of the variant tree
try: traj = json.load(open(os.path.join(rd, "mini-swe-agent.traj.json")))
except Exception: traj = {"messages": []}
msgs = traj.get("messages", []); outs = {mm.get("tool_call_id"): (mm.get("content") if isinstance(mm.get("content"), str) else json.dumps(mm.get("content"))) for mm in msgs if mm.get("role") == "tool"}
MARK = re.compile(r'"gold_rank"|"gold_methods"|"predictions"|"structured_submission"|variant_manifest|^(\+\+\+|---) [ab]/|^@@ |cue-trust-v3|VARIANT_KEY', re.M)
HARNESS = re.compile(r"workspace_manifest|method_catalog|evaluation\.json|ranking\.json|fault-localization-submission|variant\.patch|test\.patch|variant_manifest|run_manifest|\.traj\.json|raw_agent_output|VARIANT_KEY|workspace_archive|new_bug_variants|benchmark_runs|cue-trust")
PROBE_ENV = re.compile(r"(^|[\s;&|(`$])(env|printenv|set|ps|lsof|netstat|curl|wget|nc)(\s|$|;|\|)|localhost|127\.0\.0\.1")
CHECKOUT = re.compile(r"defects4j\s+checkout|git\s+clone")
REPO = os.path.realpath("/Users/shawnli/Desktop/Honours/defects4j")
HOME = os.path.expanduser("~")
def resolve(tok, cwd):
    t = tok.strip("'\"")
    t = re.sub(r"^(?:~|\$HOME|\$\{HOME\})", HOME, t)
    return os.path.realpath(t if t.startswith("/") else os.path.join(cwd, t))
def inside(p): return bool(ws) and (p == ws or p.startswith(ws + os.sep))
def in_repo(p): return (p == REPO or p.startswith(REPO + os.sep)) and not p.startswith(REPO + "/framework")
NARROW = re.compile(r'"gold_rank"|"gold_methods"|"structured_submission"|variant_manifest|cue-trust-v3|VARIANT_KEY|' + re.escape(REPO) + r'/(?!framework/)')
PREFIX = re.compile(r"^\s*(?:[^\s:]+?[:-])?\d+(?:[:\t-]\s?|\s{2,})")
flagged, contaminated, reasons, n = [], False, [], 0
for mm in msgs:
    if mm.get("role") != "assistant": continue
    for tc in mm.get("tool_calls") or []:
        fn = tc.get("function") or {}
        if fn.get("name") != "bash": continue
        n += 1
        try: cmd = json.loads(fn.get("arguments") or "{}").get("command", "")
        except Exception: cmd = ""
        cmd = cmd if isinstance(cmd, str) else json.dumps(cmd)
        out = outs.get(tc.get("id"), "") or ""; flags = []
        # A3: resolve leading cd targets (incl. ~, $HOME, .., bare cd) from the workspace; judge paths by whether they leave it
        cwd, body = ws or "/", cmd
        while True:
            mcd = re.match(r"^\s*cd(?:\s+(?:-[PL]\s+)?(\S+))?\s*(?:&&|;|$)\s*", body)
            if not mcd or mcd.end() == 0: break
            cwd = resolve(mcd.group(1) or "~", cwd); body = body[mcd.end():]
            if not inside(cwd): flags.append("cd outside workspace")
            if in_repo(cwd): contaminated = True; reasons.append(f"call {n}: cd into the Defects4J repository tree outside framework/")
            if not body: break
        for tok in re.findall(r"(?:^|[\s'\"=(])((?:\.\.(?:/[^\s'\";|&)]*)?|(?:~|\$HOME|\$\{HOME\})(?:/[^\s'\";|&)]*)?))(?=[\s'\";|&)]|$)", body):
            rp = resolve(tok, cwd)
            if not inside(rp): flags.append("path leaves workspace: " + tok[:80])
            if in_repo(rp): contaminated = True; reasons.append(f"call {n}: Defects4J repository tree accessed outside framework/: {tok[:80]}")
        if re.search(r"(^|[\s;&|(])/(?=[\s;&|)]|$)", body): flags.append("filesystem root operand")
        if NARROW.search(out): contaminated = True; reasons.append(f"call {n}: harness marker, experiment name or repository-tree path in the output")
        for p in re.findall(r"(/(?:Users|private|tmp|var|Volumes|opt|etc|home)/[^\s'\";|&)]*)", cmd):
            rp = os.path.realpath(p)
            if (rp == REPO or rp.startswith(REPO + os.sep)) and not rp.startswith(REPO + "/framework"):
                contaminated = True; reasons.append(f"call {n}: Defects4J repository tree accessed outside framework/: {p[:120]}")
            if not ws or not any(rp == w or rp.startswith(w + os.sep) for w in ws_alias | {os.path.realpath(x) for x in ws_alias}):
                flags.append("absolute path outside workspace: " + p[:120])
        if HARNESS.search(body): flags.append("harness/package name")
        if PROBE_ENV.search(body): flags.append("environment/process/network probe")
        if CHECKOUT.search(body): flags.append("repository checkout or clone"); contaminated = True; reasons.append(f"call {n}: repository checkout/clone (fixed or pristine revision)")
        foreign = sorted(set(re.findall(r"CTV-[0-9A-F]{6}", out)) - {vid})
        out_n = norm(out); cross = sorted(t for t in other if (t in out_n if " " in t else re.search(r"\b%s\b" % re.escape(t), out)))
        if foreign: contaminated = True; reasons.append(f"call {n}: other variant ids displayed {foreign}")
        if cross: contaminated = True; reasons.append(f"call {n}: cross-level cue tokens displayed {cross}")
        if flags:
            shown_lines = {norm(PREFIX.sub("", x, count=1)) for x in out.replace("\r", "").split("\n")} | {norm(x) for x in out.split("\n")}
            pristine = sorted(PRISTINE_ONLY & shown_lines)
            shown = bool(MARK.search(out)) or bool(foreign) or bool(pristine)
            flagged.append({"call": n, "flags": flags, "command": cmd[:240], "harness_content_shown": shown, "pristine_lines_shown": pristine[:3]})
            if shown: contaminated = True; reasons.append(f"call {n}: harness content or pristine source displayed after out-of-workspace access")
print(json.dumps({"run": rd, "variant": vid, "workspace": ws, "bash_calls": n, "flagged_calls": flagged, "contaminated": contaminated, "reasons": reasons,
                  "cross_level_tokens_checked": sorted(other), "pristine_only_lines": len(PRISTINE_ONLY)}, indent=1))
