#!/opt/miniconda3/bin/python
"""Run a cue-trust-v3 plan on one server, one slot at a time, in plan order. Usage: ct_driver.py --server <name> --plan <plan.json>
Per slot: health gate (bounded smoke probe) -> preflight (root, agent/model, variant discovered) -> launch one run -> post-run checks
(status, protocol identity incl. the prompt arm, source integrity, leakage scan) -> archive the workspace out of the external root.
HALT (exit 1) on: provider credit/quota errors, repeated failing health gate, contamination, integrity or protocol-identity breaks.
A slot whose run ends as an infrastructure failure is retried once; it is never silently replaced after that."""
import json, os, sys, time, datetime, glob, subprocess, urllib.request, urllib.error, shutil, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
import ct_status as S
a = sys.argv; NAME = a[a.index("--server") + 1]; PLAN = json.load(open(a[a.index("--plan") + 1]))
CFG = json.load(open(f"{C.V3}/models/servers.json"))[NAME]; PORT = CFG["port"]; ROOT = f"{C.V3}/models/{NAME}"
import hashlib; PLAN_SHA = hashlib.sha256(open(a[a.index("--plan") + 1], "rb").read()).hexdigest()
AGENT = CFG.get("agent_id", "mini-swe-claude"); EFFORT = CFG.get("reasoning_effort")
RUNS = f"{ROOT}/benchmark_runs/{AGENT}"; D = f"{C.V3}/diagnostic"; os.makedirs(D, exist_ok=True)
FROZEN = {"base_prompt_sha256": "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89", "max_tool_calls": 50, "max_test_runs": 5,
          "timeout_seconds": 300, "model": CFG["model"], "agent_id": AGENT, "inspection_requirement": CFG["inspection"] == "1",
          "reasoning_effort": EFFORT, "config_reasoning_effort": EFFORT, "response_model_ok": True}
CREDIT = re.compile(r"credit balance is too low|insufficient_quota|billing|exceeded your current quota|credit_balance", re.I)
def now(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def log(m):
    line = f"[{now()}] [{NAME}] {m}"; print(line, flush=True); open(f"{D}/driver_{NAME}.log", "a").write(line + "\n")
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=30) as r: return json.load(r)
T_START = time.time()
def smoke_credit():
    """mini-swe-agent retries a provider 400 (e.g. an empty credit balance) with exponential backoff for about 250 s, so a credit
    refusal first shows up as a probe hang. Scan the finished smoke runs this driver started for the provider's credit message."""
    for sd in glob.glob(f"{ROOT}/benchmark_runs/_smoke/mini-swe-agent/smoke-*"):
        if os.path.getmtime(sd) < T_START - 5: continue
        for f in ("raw_agent_output.txt", "smoke_result.json", "mini-swe-agent-smoke.traj.json"):
            fp = os.path.join(sd, f)
            if os.path.exists(fp) and CREDIT.search(open(fp, errors="replace").read()): return os.path.basename(sd)
    return None
def probe():
    out = f"{D}/probe_{NAME}_{int(time.time())}.json"; t0 = time.time()
    try:
        r = subprocess.run(["curl", "-s", "-X", "POST", f"http://127.0.0.1:{PORT}/api/agents/mini-swe-agent/smoke-test", "-H", "content-type: application/json",
                            "-d", json.dumps({"agent_id": AGENT}), "-o", out, "-w", "%{http_code}"], capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        sd = smoke_credit()
        return False, "hang (no response in 90 s)" + (f"; finished smoke run {sd} shows the provider credit error" if sd else ""), bool(sd)
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
    p = [x for x in ags if x.get("agent_id") == AGENT][0]["provider_config"]; assert p.get("status") == "configured" and p.get("model") == CFG["model"], p
    vs = get("/api/variants"); vs = vs.get("variants") if isinstance(vs, dict) else vs
    rec = [x for x in vs if x.get("variant_id") == V]; assert rec and not rec[0].get("schema_errors"), f"{V} not discovered or schema error"
def launch(V):
    body = {"agent_id": AGENT, "task_type": "variant", "variant_id": V, "repeats": 1, "debug_allow_unreproduced_variant": True}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/benchmark-runs", method="POST", data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=1500) as r: return r.status, json.load(r)
    except urllib.error.HTTPError as e: return e.code, {"error": e.read().decode("utf-8", "replace")[:800]}
    except Exception as e: return None, {"error": f"client-side {type(e).__name__}: {str(e)[:300]}"}
def archive(V, run):
    rd = f"{RUNS}/{V}/{run}"; link = f"{rd}/workspace"
    if os.path.islink(link):
        target = os.readlink(link); dst = f"{C.V3}/workspace_archive/{NAME}/{V}/{run}"; os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(target): shutil.move(target, dst); os.remove(link); os.symlink(dst, link); return dst
    return None
def workspace_isolated(rd):
    """The agent's workspace must be a symlink to a directory under this server's external root and outside the experiment tree."""
    try:
        m_ = re.search(r"repository path:\s*(\S+)", open(f"{rd}/prompt.txt", errors="replace").read())
        ws = os.path.realpath(m_.group(1)); ext = os.path.realpath(CFG["external_workspace_root"]); v3 = os.path.realpath(C.V3)
        return os.path.islink(f"{rd}/workspace") and ws.startswith(ext + os.sep) and not ws.startswith(v3 + os.sep)
    except Exception: return False
def check(V, run, slot_index=None, attempt=None):
    rd = f"{RUNS}/{V}/{run}"; man = rj(f"{rd}/run_manifest.json"); ev = rj(f"{rd}/evaluation.json"); rk = rj(f"{rd}/ranking.json")
    iso_ok = workspace_isolated(rd)
    si = rj(f"{rd}/source_integrity.json"); pr = rj(f"{rd}/prompt.json"); traj = rj(f"{rd}/mini-swe-agent.traj.json")
    raw = open(f"{rd}/raw_agent_output.txt", errors="replace").read()[-6000:] if os.path.exists(f"{rd}/raw_agent_output.txt") else ""
    preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
    ident = {"base_prompt_sha256": (man.get("prompt") or {}).get("base_prompt_sha256"), "max_tool_calls": (man.get("budget") or {}).get("max_tool_calls"),
             "max_test_runs": (man.get("budget") or {}).get("max_test_runs"), "timeout_seconds": (man.get("budget") or {}).get("timeout_seconds"),
             "model": (man.get("agent") or {}).get("model"), "agent_id": (man.get("agent") or {}).get("agent_id"), "inspection_requirement": pr.get("inspection_requirement")}
    scan = json.loads(subprocess.run([sys.executable, f"{C.V3}/scripts/scan_v3.py", rd], capture_output=True, text=True).stdout or "{}")
    ms = (traj.get("info") or {}).get("model_stats") or {}
    cfg_txt = open(f"{rd}/mini-swe-agent.config.yaml", errors="replace").read() if os.path.exists(f"{rd}/mini-swe-agent.config.yaml") else ""
    m_eff = re.search(r"^\s*reasoning_effort:\s*\"?([A-Za-z]+)\"?\s*$", cfg_txt, re.M)
    resp_models = sorted({((x.get("extra") or {}).get("response") or {}).get("model") for x in traj.get("messages", []) if (x.get("extra") or {}).get("response")} - {None})
    ident["reasoning_effort"] = pr.get("reasoning_effort"); ident["config_reasoning_effort"] = m_eff.group(1) if m_eff else None
    ident["response_model_ok"] = all(str(m).startswith(CFG["model"]) for m in resp_models)
    status = man.get("status"); integrity_ok = si.get("ok", si.get("production_and_test_source_unchanged")) in (True, "true")
    credit = bool(CREDIT.search(raw + json.dumps(man)[:3000]))
    res = {"server": NAME, "run": f"{V}/{run}", "status": status, "gold_rank": ev.get("gold_rank"), "n_predictions": len(preds),
           "top3": [f"{(p.get('class') or '').split('.')[-1]}::{p.get('method')}" for p in preds[:3]], "protocol_identity_ok": ident == FROZEN,
           "identity_diff": None if ident == FROZEN else {k: (ident.get(k), FROZEN[k]) for k in FROZEN if ident.get(k) != FROZEN[k]},
           "source_integrity_ok": integrity_ok, "contaminated": bool(scan.get("contaminated")), "scan_reasons": scan.get("reasons"),
           "flagged_calls": len(scan.get("flagged_calls") or []), "api_calls": ms.get("api_calls"), "cost_usd": ms.get("instance_cost"),
           "response_models": resp_models, "reasoning_effort_recorded": ident["reasoning_effort"], "config_reasoning_effort": ident["config_reasoning_effort"],
           "credit_error": credit, "workspace_isolation_ok": iso_ok, "plan_sha256": PLAN_SHA, "slot_index": slot_index, "attempt": attempt,
           "checked_at": now()}
    cls = S.classify(rd); res["classified_status"] = cls["status"]; res["status_kind"] = cls["kind"]; res["final_gap_s"] = cls["final_gap_s"]
    identity_applies = bool(man) and bool(pr) and cls["kind"] == "behavioural"
    if credit: v = "HALT_PROVIDER_CREDIT"
    elif res["contaminated"]: v = "STOP_CONTAMINATION"
    elif si and not integrity_ok: v = "STOP_INTEGRITY"
    elif man and not iso_ok: v = "STOP_INTEGRITY"
    elif identity_applies and not res["protocol_identity_ok"]: v = "STOP_INTEGRITY"
    elif cls["kind"] == "infrastructure": v = "infrastructure"
    elif cls["kind"] == "behavioural": v = "valid"
    else: v = "HALT_UNKNOWN_STATUS"
    res["verdict"] = v; res["archived_to"] = archive(V, run)
    open(f"{D}/block_{NAME}.jsonl", "a").write(json.dumps(res) + "\n"); return res
PLAN_PATH = os.path.abspath(a[a.index("--plan") + 1])
def ledger():
    out = []
    for line in open(f"{D}/block_{NAME}.jsonl") if os.path.exists(f"{D}/block_{NAME}.jsonl") else []:
        try: out.append(json.loads(line))
        except Exception: pass
    return out
PAID = CFG.get("provider") == "openai" and not CFG.get("stub")
def verify_freeze(where):
    """Amendment A1/A2: no paid OpenAI call unless FREEZE_GPT56_PILOT.json exists, binds this plan to this server, and every guarded
    artifact still matches. Called before every health gate and every launch (both are paid calls)."""
    if not PAID: return
    import freeze_lib as FZ
    fz_path = f"{C.V3}/FREEZE_GPT56_PILOT.json"
    if not os.path.exists(fz_path): log("HALT: FREEZE_MISSING (FREEZE_GPT56_PILOT.json); no paid call without the freeze"); sys.exit(1)
    fz = json.load(open(fz_path)); rel = os.path.relpath(PLAN_PATH, C.V3); pe = fz["plans"].get(rel)
    if not pe: log(f"HALT: FREEZE_MISMATCH plan {rel} is not frozen"); sys.exit(1)
    if pe.get("server") != NAME: log(f"HALT: FREEZE_MISMATCH plan {rel} is frozen for server {pe.get('server')}, not {NAME}"); sys.exit(1)
    want = dict(fz["guarded_common"]); want.update(fz["guarded_by_server"].get(NAME, {})); want.update(pe["hashes"])
    have = FZ.guarded(NAME, PLAN_PATH); bad = sorted(k for k in set(have) | set(want) if want.get(k) != have.get(k))
    if bad: log(f"HALT: FREEZE_MISMATCH ({where}) {bad[:8]}"); sys.exit(1)
    if CFG.get("role") == "analysis":
        acc = rj(f"{D}/PHASE1_ACCEPTANCE.json")
        if not (acc.get("all_pass") is True and acc.get("freeze_sha256") == FZ.sha(fz_path)):
            log("HALT: PHASE1_NOT_ACCEPTED (diagnostic/PHASE1_ACCEPTANCE.json missing, failing, or for another freeze)"); sys.exit(1)
    return FZ.sha(fz_path)
def smoke_effort_ok():
    """The server's newest smoke run must carry the pinned reasoning effort (the server env is otherwise invisible to the driver)."""
    if not EFFORT: return True
    sds = sorted(glob.glob(f"{ROOT}/benchmark_runs/_smoke/mini-swe-agent/smoke-*"), key=os.path.getmtime)
    if not sds: return False
    t = open(f"{sds[-1]}/mini-swe-agent.config.yaml", errors="replace").read() if os.path.exists(f"{sds[-1]}/mini-swe-agent.config.yaml") else ""
    return bool(re.search(r'^\s*reasoning_effort:\s*"?%s"?\s*$' % re.escape(EFFORT), t, re.M))
# single driver per server
LOCK = f"{D}/driver_{NAME}.lock"
if os.path.exists(LOCK):
    try: other = int(open(LOCK).read().strip()); os.kill(other, 0); log(f"HALT: another driver (pid {other}) holds {LOCK}"); sys.exit(1)
    except (ValueError, ProcessLookupError, PermissionError): pass
open(LOCK, "w").write(str(os.getpid()))
import atexit; atexit.register(lambda: os.path.exists(LOCK) and open(LOCK).read().strip() == str(os.getpid()) and os.remove(LOCK))
# reconcile: every run directory on this server must have a ledger record
known = {r["run"] for r in ledger()}
unchecked = sorted(f"{os.path.basename(os.path.dirname(x))}/{os.path.basename(x)}" for x in glob.glob(f"{RUNS}/CTV-*/run-*") if f"{os.path.basename(os.path.dirname(x))}/{os.path.basename(x)}" not in known)
if unchecked: log(f"HALT: UNCHECKED_RUNS on {NAME} (run directories without a ledger record; review before continuing): {unchecked[:6]}"); sys.exit(1)
fz_sha = verify_freeze("start")
if fz_sha: log(f"freeze verified at start: FREEZE_GPT56_PILOT.json sha256 {fz_sha[:16]}; plan {os.path.relpath(PLAN_PATH, C.V3)} bound to {NAME}")
if "--verify-only" in a: log("verify-only: checks passed; no call made"); sys.exit(0)
need = 3
for i, slot in enumerate(PLAN["slots"]):
    V = slot["variant_id"]; recs = [r for r in ledger() if r.get("plan_sha256") == PLAN_SHA and r.get("slot_index") == i]
    if any(r["verdict"] == "valid" for r in recs): continue
    halting = [r for r in recs if r["verdict"] != "infrastructure"]
    if halting: log(f"HALT: slot {i} ({V}) already has a halting verdict on record ({halting[-1]['verdict']}, {halting[-1]['run']}); operator review needed"); sys.exit(1)
    prior = len(recs)
    if prior >= 2: log(f"HALT: slot {i} ({V}) failed twice as infrastructure (ledger)"); sys.exit(1)
    for attempt in range(prior + 1, 3):
        verify_freeze(f"slot {i} before gate")
        gate(need, "before launch")
        if not smoke_effort_ok(): log(f"HALT: the server's newest smoke config does not carry reasoning_effort {EFFORT}"); sys.exit(1)
        try: preflight(V)
        except Exception as e: log(f"HALT: preflight refused: {e}"); sys.exit(1)
        verify_freeze(f"slot {i} before launch")
        before = set(glob.glob(f"{RUNS}/{V}/run-*"))
        log(f"launch slot {i} {slot['instance_id']} {slot['level']} round {slot['round']} -> {V} (attempt {attempt})")
        code, payload = launch(V)
        new = sorted(set(glob.glob(f"{RUNS}/{V}/run-*")) - before)
        if len(new) != 1: log(f"HALT: expected one new run directory, found {len(new)} (http {code}): {str(payload)[:300]}"); sys.exit(1)
        run = os.path.basename(new[0])
        res = check(V, run, slot_index=i, attempt=attempt)
        log(f"post-run slot {i} {V}/{run}: {res['verdict']} status={res['status']} class={res['classified_status']} rank={res['gold_rank']} top3={res['top3']} cost={res['cost_usd']} flagged={res['flagged_calls']}")
        if res["verdict"] in ("HALT_PROVIDER_CREDIT", "STOP_CONTAMINATION", "STOP_INTEGRITY", "HALT_UNKNOWN_STATUS"): log(f"HALT: {res['verdict']} {res.get('scan_reasons') or res.get('identity_diff') or ''}"); sys.exit(1)
        if res["verdict"] == "valid": need = 1; break
        need = 3
    else:
        log(f"HALT: slot {i} ({V}) failed twice as infrastructure"); sys.exit(1)
log("PLAN FINISHED")
