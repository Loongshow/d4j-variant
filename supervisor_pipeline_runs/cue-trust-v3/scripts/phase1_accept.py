"""Phase 1 runner proof (amendment A1/A2): check the ONE bounded paid smoke run on gptDiag against the brief's ten items and write
diagnostic/PHASE1_ACCEPTANCE.json, bound to the current freeze. The driver refuses analysis-server launches without it.
Items that an F0 smoke run cannot show on its own (the F1 sentence; detection of a source write; ant when the model never runs a
test) fall back to the free stand-in proof on byte-identical server code, and the evidence source is recorded per item.
Usage: phase1_accept.py <smoke run dir>"""
import json, os, re, sys, glob, hashlib, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C, freeze_lib as FZ, ct_status as S
rd = os.path.abspath(sys.argv[1]); V = os.path.basename(os.path.dirname(rd)); run = os.path.basename(rd)
KEY = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); CFG = json.load(open(f"{C.V3}/models/servers.json"))["gptDiag"]
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
man, pr, ev, rk, traj, si = (rj(f"{rd}/{f}") for f in ("run_manifest.json", "prompt.json", "evaluation.json", "ranking.json", "mini-swe-agent.traj.json", "source_integrity.json"))
prompt = open(f"{rd}/prompt.txt", errors="replace").read(); cfg_yaml = open(f"{rd}/mini-swe-agent.config.yaml", errors="replace").read()
led = [json.loads(l) for l in open(f"{C.V3}/diagnostic/block_gptDiag.jsonl")] if os.path.exists(f"{C.V3}/diagnostic/block_gptDiag.jsonl") else []
rec = [r for r in led if r["run"] == f"{V}/{run}"]; rec = rec[-1] if rec else {}
msgs = traj.get("messages", []); outs = [m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content")) for m in msgs if m.get("role") == "tool"]
resp = [((m.get("extra") or {}).get("response") or {}) for m in msgs if m.get("role") == "assistant"]
reas = sum(((r.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens") or 0 for r in resp)
SENT = "Before you submit, display the complete source body of every method you rank in your top three."
FZJ = json.load(open(f"{C.V3}/FREEZE_GPT56_PILOT.json")); DIGEST = FZ.acceptance_digest(FZJ)
stubA = f"{C.V3}/{FZJ['stub_proof']['A']}"; stubB = f"{C.V3}/{FZJ['stub_proof']['B']}"
smoke_plan_sha = FZ.sha(f"{C.V3}/plans/smoke_gpt.json")
same_code = FZ.tree_sha(f"{C.V3}/models/gptDiag/variant-lab/server") == FZ.tree_sha(f"{C.V3}/models/gptStub/variant-lab/server") == FZ.tree_sha(f"{C.V3}/models/gptF0/variant-lab/server")
ws_m = re.search(r"repository path:\s*(\S+)", prompt); ws = ws_m.group(1) if ws_m else ""
arch = os.path.realpath(f"{rd}/workspace")
meta_files = subprocess.run(["find", arch, "(", "-name", "evaluation.json", "-o", "-name", "variant_manifest.json", "-o", "-name", "validation.json", "-o", "-name", "VARIANT_KEY*",
                             "-o", "-name", "spec.json", "-o", "-name", "*.patch", "-o", "-name", "ranking.json", "-o", "-name", "run_manifest.json", ")"], capture_output=True, text=True).stdout.split()
labels = subprocess.run(["grep", "-rIlE", r"CT-CHART-0[0-9]|CT-LANG-0[0-9]|cue-trust|VARIANT_KEY|\b(CG1|CG2|CD1|CD2)\b|gold_rank", arch], capture_output=True, text=True).stdout.split()
preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or [])
keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]; gold = KEY[V]["gold"]
recomputed = (keys.index(gold) + 1) if gold in keys else None
ran_ant = any("Running ant" in o for o in outs)
stubA_ant = any("Running ant" in (m.get("content") or "") for m in rj(f"{stubA}/mini-swe-agent.traj.json").get("messages", []) if m.get("role") == "tool")
items = {
 "1_model_call_succeeds": {"pass": bool(resp) and S.classify(rd)["kind"] == "behavioural" and all(str(r.get("model", "")).startswith("gpt-5.6") for r in resp if r),
                           "evidence": f"{len(resp)} responses, models {sorted({r.get('model') for r in resp if r})}, status {man.get('status')}, reasoning tokens {reas}"},
 "2_defects4j_test_through_ant": {"pass": ran_ant or (stubA_ant and same_code), "evidence": "smoke run tool output" if ran_ant else f"stand-in run {os.path.relpath(stubA, C.V3)} on byte-identical server code (the model did not run a test in the smoke run)"},
 "3_opaque_workspace_id": {"pass": bool(re.search(r"/CTV-[0-9A-F]{6}$", ws)) and ws.endswith(V) and not re.search(r"CT-(CHART|LANG)|C0|CG|CD|gold|decoy", ws.split("/")[-1] + ws.split("/")[-2]),
                           "evidence": ws},
 "4_workspace_outside_repo": {"pass": bool(rec.get("workspace_isolation_ok")) and not os.path.realpath(ws or "/").startswith(os.path.realpath("/Users/shawnli/Desktop/Honours/defects4j") + "/"),
                              "evidence": f"driver workspace_isolation_ok={rec.get('workspace_isolation_ok')}; {ws}"},
 "5_sibling_results_inaccessible": {"pass": rec.get("contaminated") is False, "evidence": f"scan contaminated={rec.get('contaminated')}, flagged calls {rec.get('flagged_calls')}; structural: external root, archived after each run (stand-in listing showed only the run's own folder)"},
 "6_no_gold_or_condition_metadata": {"pass": not meta_files and not labels, "evidence": f"metadata files {meta_files[:3]}, label hits {labels[:3]} in {os.path.relpath(arch, C.V3)}"},
 "7_prompt_arm_flag": {"pass": pr.get("inspection_requirement") is (CFG["inspection"] == "1") and prompt.count(SENT) == 0, "evidence": f"F0: inspection_requirement={pr.get('inspection_requirement')}, sentence count {prompt.count(SENT)}"},
 "8_F1_sentence_exactly_once": {"pass": open(f"{stubB}/prompt.txt").read().count(SENT) == 1 and rj(f"{stubB}/prompt.json").get("inspection_requirement") is True and same_code,
                                "evidence": f"stand-in F1 run {os.path.relpath(stubB, C.V3)} (byte-identical code; the smoke run is F0)"},
 "9_no_source_modification": {"pass": si.get("ok") is True and rj(f"{stubB}/source_integrity.json").get("ok") is False,
                              "evidence": f"smoke source_integrity ok={si.get('ok')}; detection proven by the stand-in write (ok={rj(f'{stubB}/source_integrity.json').get('ok')}, driver STOP_INTEGRITY)"},
 "10_output_parsed": {"pass": (len(keys) == 10 and ev.get("gold_rank") == recomputed) or (not keys and S.classify(rd)["status"] in ("no_answer", "timeout")),
                      "evidence": f"{len(keys)} predictions, evaluation gold_rank {ev.get('gold_rank')}, recomputed {recomputed}"},
 "x_reasoning_effort_pinned": {"pass": pr.get("reasoning_effort") == "medium" and bool(re.search(r'^\s*reasoning_effort:\s*"medium"\s*$', cfg_yaml, re.M)),
                               "evidence": f"prompt.json {pr.get('reasoning_effort')}; config yaml carries reasoning_effort \"medium\""},
 "x_protocol_identity": {"pass": rec.get("protocol_identity_ok") is True and rec.get("verdict") == "valid", "evidence": f"driver verdict {rec.get('verdict')}, identity ok {rec.get('protocol_identity_ok')}, diff {rec.get('identity_diff')}"},
 "x_made_under_this_freeze": {"pass": rec.get("freeze_digest") == DIGEST and rec.get("plan_sha256") == smoke_plan_sha,
                              "evidence": f"ledger freeze digest {str(rec.get('freeze_digest'))[:16]} vs current {DIGEST[:16]}; plan sha matches smoke plan: {rec.get('plan_sha256') == smoke_plan_sha}"}}
fz_path = f"{C.V3}/FREEZE_GPT56_PILOT.json"
out = {"smoke_run": os.path.relpath(rd, C.V3), "cost_usd": ((traj.get("info") or {}).get("model_stats") or {}).get("instance_cost"), "items": items,
       "all_pass": all(v["pass"] for v in items.values()), "freeze_digest": DIGEST, "freeze_sha256": FZ.sha(fz_path)}
json.dump(out, open(f"{C.V3}/diagnostic/PHASE1_ACCEPTANCE.json", "w"), indent=1)
for k, v in items.items(): print(f"{'PASS' if v['pass'] else 'FAIL'} {k}: {v['evidence'][:150]}")
print("ALL PASS" if out["all_pass"] else "NOT ACCEPTED")
