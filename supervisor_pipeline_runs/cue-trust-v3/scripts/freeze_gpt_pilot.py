"""Freeze the GPT-5.6 pilot before the first paid call (amendment A1). Usage:
  freeze_gpt_pilot.py                 -> writes FREEZE_GPT56_PILOT.json (refuses to overwrite)
  freeze_gpt_pilot.py --add-plan P --server S   -> appends a later plan (e.g. Phase 3) bound to server S; nothing else changes
The driver verifies the guarded hashes before every paid OpenAI launch."""
import json, os, sys, datetime, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C, freeze_lib as FZ
OUT = f"{C.V3}/FREEZE_GPT56_PILOT.json"; now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
PLAN_SERVER = {"plans/pilot.json": "gptF0", "plans/smoke_gpt.json": "gptDiag"}
def plan_entry(p, server):
    full = FZ.guarded(server, p)
    return {"server": server, "hashes": {k: v for k, v in full.items() if k.startswith(("plan/", "variant/", "instance/"))}}
if "--add-plan" in sys.argv:
    p = os.path.abspath(sys.argv[sys.argv.index("--add-plan") + 1]); server = sys.argv[sys.argv.index("--server") + 1]
    fz = json.load(open(OUT)); rel = os.path.relpath(p, C.V3)
    assert rel not in fz["plans"], f"{rel} already frozen"
    fz["plans"][rel] = plan_entry(p, server); fz.setdefault("later_plans", []).append({"plan": rel, "server": server, "frozen_at": now, "sha256": FZ.sha(p)})
    json.dump(fz, open(OUT, "w"), indent=1); print("added", rel, "freeze sha256", FZ.sha(OUT)); sys.exit(0)
assert not os.path.exists(OUT), "FREEZE_GPT56_PILOT.json exists; refusing to overwrite (use --add-plan for later plans)"
servers = json.load(open(f"{C.V3}/models/servers.json")); paid = [n for n, c in servers.items() if c.get("provider") == "openai" and not c.get("stub")]
g0 = FZ.guarded("gptF0", f"{C.V3}/plans/pilot.json")
common = {k: v for k, v in g0.items() if k.startswith("scripts/") or k in ("review/VARIANT_KEY.json", "models/servers.json", "PREREGISTRATION.md")}
by_server = {n: {k: v for k, v in FZ.guarded(n, f"{C.V3}/plans/pilot.json").items() if k.startswith(f"models/{n}/")} for n in paid}
plans = {rel: plan_entry(f"{C.V3}/{rel}", srv) for rel, srv in PLAN_SERVER.items()}
canon_agents = "/Users/shawnli/Desktop/Honours/defects4j/benchmark_runs/agents.json"
profile = [x for x in json.load(open(canon_agents))["agents"] if x["agent_id"] == "mini-swe-agent-openai-gpt-5-6"][0] if isinstance(json.load(open(canon_agents)), dict) and "agents" in json.load(open(canon_agents)) else \
          [x for x in json.load(open(canon_agents)) if x["agent_id"] == "mini-swe-agent-openai-gpt-5-6"][0]
pilot = json.load(open(f"{C.V3}/plans/pilot.json"))
def stub_proof():
    """The latest stand-in proof runs on the final harness, taken from the stub ledgers (A valid, B integrity stop, C contamination stop)."""
    def last(server, plan, verdict):
        psha = FZ.sha(f"{C.V3}/plans/{plan}"); hit = None
        for l in open(f"{C.V3}/diagnostic/block_{server}.jsonl"):
            r = json.loads(l)
            if r.get("plan_sha256") == psha and r["verdict"] == verdict: hit = r
        assert hit, f"no {verdict} record for {plan} on {server}; rerun the stand-in proof"
        return f"models/{server}/benchmark_runs/mini-swe-agent-openai-gpt-5-6/{hit['run']}"
    out = {"A": last("gptStub", "proof_A.json", "valid"), "B": last("gptStubF1", "proof_B.json", "STOP_INTEGRITY"),
           "C": last("gptStub", "proof_C.json", "STOP_CONTAMINATION"), "D_credit_then_replacement": last("gptStub", "proof_D.json", "valid"),
           "E_adopted_after_driver_kill": last("gptStub", "proof_E.json", "valid"), "requests_log": "diagnostic/stub/requests.jsonl",
           "requests_log_sha256": FZ.sha(f"{C.V3}/diagnostic/stub/requests.jsonl"), "server_code_identical_to_gptF0": True}
    assert FZ.tree_sha(f"{C.V3}/models/gptStub/variant-lab/server") == FZ.tree_sha(f"{C.V3}/models/gptF0/variant-lab/server"), "stub code differs from gptF0"
    return out
SENT = "Before you submit, display the complete source body of every method you rank in your top three."
fz = {"frozen_at": now, "purpose": "GPT-5.6-first cue-trust-v3 pilot (amendment A1); verified by ct_driver.py before every paid OpenAI launch",
      "model": {"agent_id": "mini-swe-agent-openai-gpt-5-6", "profile": profile, "provider": "openai", "model": "gpt-5.6", "runtime_model": "openai/gpt-5.6",
                "canonical_agents_json_sha256": FZ.sha(canon_agents), "client": {"litellm": "1.98.0", "mini-swe-agent": "2.4.6", "installed": "2026-08-26"},
                "endpoint": "OpenAI Responses API through litellm's bridge (gpt-5.4+ with function tools and active reasoning); identical for the "
                            "earlier unset-effort runs and for explicit medium (offline responses_api_bridge_check)",
                "response_model_check": "every model response must report a model starting with 'gpt-5.6' (driver protocol identity)"},
      "reasoning_effort": {"value": "medium", "explicit": True, "where": "model_kwargs.reasoning_effort (P3); recorded per run in prompt.json and mini-swe-agent.config.yaml; "
                                                                        "sent as reasoning.effort on the Responses request (shown by the stub proof)",
                           "why_this_value": "provider default used by the earlier GPT-5.6 runs, which sent no effort parameter",
                           "evidence": ["https://developers.openai.com/api/docs/guides/reasoning : GPT-5.6 'defaults to medium in both modes' (read 2026-10-08)",
                                        "https://developers.openai.com/api/docs/models/gpt-5.6 : reasoning.effort 'medium (default)' (read 2026-10-08)",
                                        "litellm 1.98.0 main.py responses_api_bridge_check comment: for gpt-5.4+ 'unset reasoning_effort means medium server-side'"],
                           "limitation": "earlier responses do not echo the effort, so the earlier value rests on documentation and client code"},
      "protocol": {"base_prompt_sha256": "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89", "prompt_version": "d4j-localization-only/v2",
                   "F0": "frozen base prompt, no extra sentence", "F1_sentence": SENT, "F1_sentence_sha256": hashlib.sha256(SENT.encode()).hexdigest(),
                   "max_tool_calls": 50, "max_test_runs": 5, "timeout_seconds": 300,
                   "budget_enforcement": "as in the earlier GPT-5.6 runs: 50 = mini-swe-agent step_limit (model calls); 300 s = harness kill; the "
                                         "5-test budget is recorded in the run manifest only (not stated in the prompt, not enforced); per-run overruns are reported",
                   "health_gate_probes": "each health-gate probe is a paid one-call smoke test; the gate needs 3 consecutive passing probes at every driver "
                                         "start and after any infrastructure attempt, and 1 before a launch that follows a valid run; a failed probe "
                                         "restarts the count and 6 failures halt",
                   "task": "localization-only, exactly ten ranked production methods",
                   "scoring": "exact Class::method gold rank (server evaluation.json)",
                   "ranking_parser": "agents/mini_swe_fault_localization.py submit_fault_localization validation + server evaluation (in the server tree hash)",
                   "workspace_isolation": "P1: workspace under D4J_EXTERNAL_WORKSPACE_ROOT/<uuid>/<opaque CTV id> (neutral root names), archived out after "
                                          "each run; opaque variant ids; P4: the agent's bash sees an allowlisted environment; the launcher gives the "
                                          "server an allowlisted environment; the driver checks the workspace location of every run",
                   "same_as_earlier_gpt_runs": "base prompt, budgets, profile, parser, client, endpoint; differences: explicit effort (same value), v3 isolation, F1 arm"},
      "pilot": {"plan": "plans/pilot.json", "plan_sha256": FZ.sha(f"{C.V3}/plans/pilot.json"), "server": "gptF0", "arm": "F0", "seed": pilot.get("seed"),
                "slots": len(pilot["slots"]), "order": [s["variant_id"] for s in pilot["slots"]]},
      "smoke": {"plan": "plans/smoke_gpt.json", "server": "gptDiag", "counted": False},
      "metrics_definitions": {"file": "scripts/ct_metrics.py", "sha256": FZ.sha(f"{C.V3}/scripts/ct_metrics.py"), "status_rule": "scripts/ct_status.py",
                              "status_rule_sha256": FZ.sha(f"{C.V3}/scripts/ct_status.py")},
      "stop_rules": {"driver": "scripts/ct_driver.py", "driver_sha256": FZ.sha(f"{C.V3}/scripts/ct_driver.py"), "preregistration_sha256": FZ.sha(f"{C.V3}/PREREGISTRATION.md"),
                     "halts": ["provider credit/quota", "health gate failing 6 times", "contamination", "integrity or protocol-identity break",
                               "unknown run status", "a slot failing twice as infrastructure", "freeze mismatch"]},
      "stub_proof": stub_proof(),
      "guarded_common": common, "guarded_by_server": by_server, "plans": plans}
fz["acceptance_digest"] = FZ.acceptance_digest(fz)
json.dump(fz, open(OUT, "w"), indent=1)
print("wrote", OUT, "sha256", FZ.sha(OUT), "acceptance digest", fz["acceptance_digest"][:16]); print("guarded common", len(common), "| servers", list(by_server), "| plans", {k: len(v) for k, v in plans.items()})
