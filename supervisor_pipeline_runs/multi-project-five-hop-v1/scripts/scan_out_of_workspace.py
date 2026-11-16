"""Raw-trajectory scan for agent access outside its assigned workspace (observable commands + outputs only).
Usage: scan_out_of_workspace.py <runs_root> <out.json> <TARGET[:a-b]> [...]  e.g. MATH-NORM-CONTROL-01:6-10
Flags per bash call: cd to a path other than the workspace; parent-relative paths (../); absolute paths into the run tree / server root;
harness file names (workspace_manifest, method_catalog, evaluation, ranking, submission, variant.patch, .defects4j.config, build.properties);
and whether the OUTPUT displayed sibling-run, package, fixed-checkout or own-manifest CONTENT (contamination)."""
import json, os, re, sys, glob
RUNS, OUT = sys.argv[1], sys.argv[2]
def calls(rdir):
    try: t = json.load(open(os.path.join(rdir, "mini-swe-agent.traj.json")))
    except Exception: return []
    msgs = t.get("messages", []); outs = {m.get("tool_call_id"): (m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content"))) for m in msgs if m.get("role") == "tool"}
    res = []
    for m in msgs:
        if m.get("role") != "assistant": continue
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or {}
            try: args = json.loads(fn.get("arguments") or "{}")
            except Exception: args = {}
            if fn.get("name") == "bash": res.append((args.get("command", ""), outs.get(tc.get("id"), "") or ""))
    return res
CONTENT_MARKERS = {"sibling_run_content": re.compile(r'"gold_rank"|"predictions"|"structured_submission"|"hit_at_5"|exit_status|"status_reason"'),
                   "package_content": re.compile(r"^(\+\+\+|---) [ab]/|^@@ |NON_CANONICAL|variant_manifest|\"synthetic_call_hops\"", re.M),
                   "own_manifest_content": re.compile(r"variant_patch_results|patching file '|private_metadata_scan"),
                   "fixed_checkout_diff": re.compile(r"^diff -r|^[<>] .*(public|private|static)", re.M)}
result = {"runs": {}, "summary": {}}
for spec in sys.argv[3:]:
    V, _, rng = spec.partition(":"); lo, hi = (1, 999)
    if rng: lo, hi = [int(x) for x in rng.split("-")]
    ws_re = re.compile(re.escape(V) + r"/run-(\d+)/workspace/" + re.escape(V) + r"/?$")
    for rdir in sorted(glob.glob(os.path.join(RUNS, V, "run-*"))):
        n = int(os.path.basename(rdir).split("-")[-1])
        if not (lo <= n <= hi): continue
        ws = os.path.join(rdir, "workspace", V); flagged = []; contaminated = []
        for i, (cmd, o) in enumerate(calls(rdir), 1):
            m = re.match(r"\s*cd\s+'?([^'&;\s]+)'?\s*&&", cmd); target = m.group(1) if m else None; body = cmd[m.end():] if m else cmd
            flags = []
            if target and os.path.normpath(target) != os.path.normpath(ws): flags.append("cd outside workspace -> " + target.replace(RUNS, "<RUNS>"))
            if re.search(r"(^|[\s'\"=(])\.\./", body): flags.append("parent-relative path")
            if re.search(r"/Users/|benchmark_runs|new_bug_variants|workspaces/defects4j|run-0\d\d", body): flags.append("absolute/run path in body")
            if re.search(r"workspace_manifest|method_catalog|evaluation\.json|ranking\.json|fault-localization-submission|variant\.patch|test\.patch|variant_manifest|\.defects4j\.config|defects4j\.build\.properties|raw_agent_output|\.traj\.json|run_manifest", body): flags.append("harness/package file name")
            shown = [k for k, rx in CONTENT_MARKERS.items() if rx.search(o)]
            # own-run method catalog and prompt are not contamination (no gold information); everything else with content shown is
            if shown and not (re.search(r"method_catalog", body) and shown == []): pass
            if flags:
                rec = {"call": i, "flags": flags, "command": body[:240], "output_head": o[:300], "content_shown": shown}
                flagged.append(rec)
                if shown and not ("method_catalog" in body and shown == ["sibling_run_content"] and '"gold_rank"' not in o): contaminated.append(rec)
        result["runs"][f"{V}/run-{n:03d}"] = {"flagged_calls": flagged, "contaminated": bool(contaminated), "contaminating_calls": [c["call"] for c in contaminated]}
result["summary"] = {"runs_scanned": len(result["runs"]), "runs_with_out_of_workspace_flags": sum(1 for r in result["runs"].values() if r["flagged_calls"]), "contaminated_runs": [k for k, r in result["runs"].items() if r["contaminated"]]}
json.dump(result, open(OUT, "w"), indent=1)
print(json.dumps(result["summary"]))
for k, r in result["runs"].items():
    for f in r["flagged_calls"]: print(k, "call", f["call"], f["flags"], "| content shown:", f["content_shown"], "|", f["command"][:120].replace("\n", " "))
