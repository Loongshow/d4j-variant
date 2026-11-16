#!/opt/miniconda3/bin/python
"""Run a cue-trust-v3 plan on one server, one slot at a time, in plan order. Usage: ct_driver.py --server <name> --plan <plan.json>
Per slot: health gate (bounded smoke probe) -> preflight (root, agent/model, variant discovered) -> launch one run -> post-run checks
(status, protocol identity incl. the prompt arm, source integrity, leakage scan) -> archive the workspace out of the external root.
HALT (exit 1) on: provider credit/quota errors, repeated failing health gate, contamination, integrity or protocol-identity breaks.
A slot whose run ends as an infrastructure failure is retried once; it is never silently replaced after that."""
import json, os, sys, time, datetime, glob, subprocess, urllib.request, urllib.error, shutil, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
a = sys.argv; NAME = a[a.index("--server") + 1]; PLAN = json.load(open(a[a.index("--plan") + 1]))
CFG = json.load(open(f"{C.V3}/models/servers.json"))[NAME]; PORT = CFG["port"]; ROOT = f"{C.V3}/models/{NAME}"
RUNS = f"{ROOT}/benchmark_runs/mini-swe-claude"; D = f"{C.V3}/diagnostic"; os.makedirs(D, exist_ok=True)
FROZEN = {"base_prompt_sha256": "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89", "max_tool_calls": 50, "max_test_runs": 5,
          "timeout_seconds": 300, "model": CFG["model"], "agent_id": "mini-swe-claude", "inspection_requirement": CFG["inspection"] == "1"}
CREDIT = re.compile(r"credit balance is too low|insufficient_quota|billing|exceeded your current quota|credit_balance", re.I)
def now(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def log(m):
    line = f"[{now()}] [{NAME}] {m}"; print(line, flush=True); open(f"{D}/driver_{NAME}.log", "a").write(line + "\n")
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=30) as r: return json.load(r)
def probe():
    out = f"{D}/probe_{NAME}_{int(time.time())}.json"; t0 = time.time()
    try:
        r = subprocess.run(["curl", "-s", "-X", "POST", f"http://127.0.0.1:{PORT}/api/agents/mini-swe-agent/smoke-test", "-H", "content-type: application/json",
                            "-d", '{"agent_id":"mini-swe-claude"}', "-o", out, "-w", "%{http_code}"], capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired: return False, "hang (no response in 90 s)", False
    d = rj(out); text = json.dumps(d)[:4000]; credit = bool(CREDIT.search(text))
    ok = r.stdout.strip() == "200" and d.get("status") == "passed"
    return ok, f"http={r.stdout.strip()} status={d.get('status')} wall={time.time() - t0:.1f}s credit_error={credit}", credit
def gate(n, why):
    good = bad = 0; log(f"gate: {n} fast probe(s) needed ({why})")
    while good < n:
        ok, line, credit = probe(); log("  probe: " + line)
        if credit: log("HALT_PROVIDER_CREDIT: the provider reports an exhausted credit balance; no run launched"); sys.exit(1)
        if ok: good += 1
        else:
            good = 0; bad += 1
            if bad >= 6: log("HALT: health gate failed 6 times"); sys.exit(1)
            time.sleep(45)
def preflight(V):
    env = get("/api/env"); assert env.get("repoRoot") == ROOT, env.get("repoRoot")
    ags = get("/api/agents"); ags = ags.get("agents") if isinstance(ags, dict) else ags
    p = [x for x in ags if x.get("agent_id") == "mini-swe-claude"][0]["provider_config"]; assert p.get("status") == "configured" and p.get("model") == CFG["model"], p
    vs = get("/api/variants"); vs = vs.get("variants") if isinstance(vs, dict) else vs
    rec = [x for x in vs if x.get("variant_id") == V]; assert rec and not rec[0].get("schema_errors"), f"{V} not discovered or schema error"
def launch(V):
    body = {"agent_id": "mini-swe-claude", "task_type": "variant", "variant_id": V, "repeats": 1, "debug_allow_unreproduced_variant": True}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/benchmark-runs", method="POST", data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=1500) as r: return r.status, json.load(r)
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode("utf-8", "replace")[:800]}
def archive(V, run):
    rd = f"{RUNS}/{V}/{run}"; link = f"{rd}/workspace"
    if os.path.islink(link):
        target = os.readlink(link); dst = f"{C.V3}/workspace_archive/{NAME}/{V}/{run}"; os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(target): shutil.move(target, dst); os.remove(link); os.symlink(dst, link); return dst
    return None
def check(V, run):
    rd = f"{RUNS}/{V}/{run}"; man = rj(f"{rd}/run_manifest.json"); ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json")
    si = rj(f"{rd}/source_integrity.json"); pr = rj(f"{rd}/prompt.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json")
    raw = open(f"{rd}/raw_agent_output.txt", errors="replace").read()[-6000:] if os.path.exists(f"{rd}/raw_agent_output.txt") else ""
    preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
    ident = {"base_prompt_sha256": (man.get("prompt") or {}).get("base_prompt_sha256"), "max_tool_calls": (man.get("budget") or {}).get("max_tool_calls"),
             "max_test_runs": (man.get("budget") or {}).get("max_test_runs"), "timeout_seconds": (man.get("budget") or {}).get("timeout_seconds"),
             "model": (man.get("agent") or {}).get("model"), "agent_id": (man.get("agent") or {}).get("agent_id"), "inspection_requirement": pr.get("inspection_requirement")}
    scan = json.loads(subprocess.run([sys.executable, f"{C.V3}/scripts/scan_v3.py", rd], capture_output=True, text=True).stdout or "{}")
    ms = (traj.get("info") or {}).get("model_stats") or {}
    status = man.get("status"); integrity_ok = si.get("ok", si.get("production_and_test_source_unchanged")) in (True, "true")
    credit = bool(CREDIT.search(raw + json.dumps(man)[:3000]))
    res = {"server": NAME, "run": f"{V}/{run}", "status": status, "gold_rank": ev.get("gold_rank"), "n_predictions": len(preds),
           "top3": [f"{(p.get('class') or '').split('.')[-1]}::{p.get('method')}" for p in preds[:3]], "protocol_identity_ok": ident == FROZEN,
           "identity_diff": None if ident == FROZEN else {k: (ident.get(k), FROZEN[k]) for k in FROZEN if ident.get(k) != FROZEN[k]},
           "source_integrity_ok": integrity_ok, "contaminated": bool(scan.get("contaminated")), "scan_reasons": scan.get("reasons"),
           "flagged_calls": len(scan.get("flagged_calls") or []), "api_calls": ms.get("api_calls"), "cost_usd": ms.get("instance_cost"),
           "credit_error": credit, "checked_at": now()}
    if credit: v = "HALT_PROVIDER_CREDIT"
    elif res["contaminated"]: v = "STOP_CONTAMINATION"
    elif status == "completed" and preds and (not integrity_ok or not res["protocol_identity_ok"]): v = "STOP_INTEGRITY"
    elif status != "completed": v = "infrastructure"
    else: v = "valid"
    res["verdict"] = v; res["archived_to"] = archive(V, run)
    open(f"{D}/block_{NAME}.jsonl", "a").write(json.dumps(res) + "\n"); return res
def valid_count(V):
    n = 0
    for line in open(f"{D}/block_{NAME}.jsonl") if os.path.exists(f"{D}/block_{NAME}.jsonl") else []:
        r = json.loads(line)
        if r["run"].startswith(V + "/") and r["verdict"] == "valid": n += 1
    return n
done = {}
need = 3
for slot in PLAN["slots"]:
    V = slot["variant_id"]; target = done.get(V, valid_count(V) if V not in done else done[V])
    planned_so_far = sum(1 for s in PLAN["slots"][:PLAN["slots"].index(slot) + 1] if s["variant_id"] == V)
    if valid_count(V) >= planned_so_far: continue
    for attempt in (1, 2):
        gate(need, "before launch")
        try: preflight(V)
        except Exception as e: log(f"HALT: preflight refused: {e}"); sys.exit(1)
        n_before = len(glob.glob(f"{RUNS}/{V}/run-*")); run = f"run-{n_before + 1:03d}"
        log(f"launch {slot['instance_id']} {slot['level']} round {slot['round']} -> {V}/{run} (attempt {attempt})")
        code, payload = launch(V)
        if len(glob.glob(f"{RUNS}/{V}/run-*")) != n_before + 1: log(f"HALT: run directory not created (http {code}): {str(payload)[:300]}"); sys.exit(1)
        res = check(V, run)
        log(f"post-run {V}/{run}: {res['verdict']} status={res['status']} rank={res['gold_rank']} top3={res['top3']} cost={res['cost_usd']} flagged={res['flagged_calls']}")
        if res["verdict"] in ("HALT_PROVIDER_CREDIT", "STOP_CONTAMINATION", "STOP_INTEGRITY"): log(f"HALT: {res['verdict']} {res.get('scan_reasons') or res.get('identity_diff') or ''}"); sys.exit(1)
        if res["verdict"] == "valid": need = 1; break
        need = 3
    else:
        log(f"HALT: slot {V} failed twice as infrastructure"); sys.exit(1)
log("PLAN FINISHED")
