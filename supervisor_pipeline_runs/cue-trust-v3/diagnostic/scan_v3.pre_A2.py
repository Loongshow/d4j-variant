"""cue-trust-v3 out-of-workspace and cross-variant leakage scan (observable commands and outputs only).
Usage: scan_v3.py <run_dir>   -> prints JSON {flagged_calls, contaminated, reasons}
Flags a bash call when it: cds or refers to an absolute path outside the run's own workspace; uses ../ to leave the workspace;
names a harness or package file; or its OUTPUT shows harness content (gold labels, rankings, manifests, patches) or an identifier
or comment that belongs to a DIFFERENT cue level of the same instance (cross-variant leakage). Contamination = a flagged call
whose output displayed such content, or any cross-level cue token in any output."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
rd = sys.argv[1]; vid = os.path.basename(os.path.dirname(rd))
key = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); K = key[vid]
spec = json.load(open(f"{C.V3}/instances/{K['instance_id']}/spec.json"))
prompt = open(os.path.join(rd, "prompt.txt"), errors="replace").read()
m = re.search(r"repository path:\s*(\S+)", prompt); ws = os.path.normpath(m.group(1)) if m else None
def tokens(level):
    lv = spec["levels"][level]; out = set()
    for r in lv.get("renames", []): out |= set(r["map"].values())
    words = re.findall(r"[A-Za-z]{6,}", lv["comment"]); out |= {" ".join(words)} if words else set()
    return out
own = tokens(K["level"]); other = set()
for lvl in spec["levels"]:
    if lvl != K["level"]: other |= tokens(lvl)
other -= own
import subprocess
def distinctive(t):
    if len(t) < 4: return False
    src = os.path.join(spec["fresh"], spec["src_root"])
    if " " in t: return subprocess.run(["grep", "-rqF", t, src]).returncode != 0
    return subprocess.run(["grep", "-rqw", t, src]).returncode != 0
other = {t for t in other if distinctive(t)}
try: traj = json.load(open(os.path.join(rd, "mini-swe-agent.traj.json")))
except Exception: traj = {"messages": []}
msgs = traj.get("messages", []); outs = {mm.get("tool_call_id"): (mm.get("content") if isinstance(mm.get("content"), str) else json.dumps(mm.get("content"))) for mm in msgs if mm.get("role") == "tool"}
MARK = re.compile(r'"gold_rank"|"gold_methods"|"predictions"|"structured_submission"|variant_manifest|^(\+\+\+|---) [ab]/|^@@ |cue-trust-v3|VARIANT_KEY', re.M)
HARNESS = re.compile(r"workspace_manifest|method_catalog|evaluation\.json|ranking\.json|fault-localization-submission|variant\.patch|test\.patch|variant_manifest|run_manifest|\.traj\.json|raw_agent_output|VARIANT_KEY|workspace_archive|new_bug_variants|benchmark_runs")
flagged, contaminated, reasons, n = [], False, [], 0
for mm in msgs:
    if mm.get("role") != "assistant": continue
    for tc in mm.get("tool_calls") or []:
        fn = tc.get("function") or {}
        if fn.get("name") != "bash": continue
        n += 1
        try: cmd = json.loads(fn.get("arguments") or "{}").get("command", "")
        except Exception: cmd = ""
        out = outs.get(tc.get("id"), "") or ""; flags = []
        for p in re.findall(r"(/(?:Users|private|tmp|var|Volumes)/[^\s'\";|&)]+)", cmd):
            pn = os.path.normpath(p)
            if not ws or not (pn == ws or pn.startswith(ws + os.sep)): flags.append("absolute path outside workspace: " + p[:120])
        body = re.sub(r"^\s*cd\s+\S+\s*(&&|;)", "", cmd)
        if re.search(r"(^|[\s'\"=(])\.\./", body): flags.append("parent-relative path")
        if HARNESS.search(body): flags.append("harness/package name")
        foreign = sorted(set(re.findall(r"CTV-[0-9A-F]{6}", out)) - {vid})
        shown = bool(MARK.search(out)) or bool(foreign); cross = sorted(t for t in other if t in out)
        if foreign: contaminated = True; reasons.append(f"call {n}: other variant ids displayed {foreign}")
        if cross: contaminated = True; reasons.append(f"call {n}: cross-level cue tokens displayed {cross}")
        if flags:
            flagged.append({"call": n, "flags": flags, "command": cmd[:240], "harness_content_shown": shown})
            if shown: contaminated = True; reasons.append(f"call {n}: harness content displayed after out-of-workspace access")
print(json.dumps({"run": rd, "variant": vid, "workspace": ws, "bash_calls": n, "flagged_calls": flagged, "contaminated": contaminated, "reasons": reasons}, indent=1))
