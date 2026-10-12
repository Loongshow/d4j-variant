"""Phase 1 runner proof for mechanism-search-v1: check the ONE bounded paid smoke run on mxDiag and write
diagnostic/PHASE1_ACCEPTANCE.json bound to FREEZE.json's acceptance digest. The F1-sentence and source-write-detection items cite the
cue-trust-v3 stand-in proofs, valid here only because the server code tree is byte-identical (checked).
Usage: mx_phase1_accept.py <smoke run dir>"""
import json, os, re, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C, freeze_lib as FZ, ct_status as S
CT = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3"
rd = os.path.abspath(sys.argv[1]); V = os.path.basename(os.path.dirname(rd)); run = os.path.basename(rd)
KEY = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); K = KEY[V]
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
man, pr, ev, rk, traj, si = (rj(f"{rd}/{f}") for f in ("run_manifest.json", "prompt.json", "evaluation.json", "ranking.json", "mini-swe-agent.traj.json", "source_integrity.json"))
prompt = open(f"{rd}/prompt.txt", errors="replace").read(); cfg_yaml = open(f"{rd}/mini-swe-agent.config.yaml", errors="replace").read()
led = [json.loads(l) for l in open(f"{C.V3}/diagnostic/block_mxDiag.jsonl")] if os.path.exists(f"{C.V3}/diagnostic/block_mxDiag.jsonl") else []
rec = [r for r in led if r["run"] == f"{V}/{run}"]; rec = rec[-1] if rec else {}
msgs = traj.get("messages", []); outs = [m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content")) for m in msgs if m.get("role") == "tool"]
resp = [((m.get("extra") or {}).get("response") or {}) for m in msgs if m.get("role") == "assistant"]
reas = sum(((r.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens") or 0 for r in resp)
FZJ = json.load(open(f"{C.V3}/FREEZE.json")); DIGEST = FZ.acceptance_digest(FZJ); smoke_sha = FZ.sha(f"{C.V3}/plans/smoke.json")
CTF = json.load(open(f"{CT}/FREEZE_GPT56_PILOT.json")); stubA = f"{CT}/{CTF['stub_proof']['A']}"; stubB = f"{CT}/{CTF['stub_proof']['B']}"
same_code = FZ.tree_sha(f"{C.V3}/models/mxDiag/variant-lab/server") == FZ.tree_sha(f"{C.V3}/models/mxF0/variant-lab/server") == FZ.tree_sha(f"{CT}/models/gptStubF1/variant-lab/server")
SENT = "Before you submit, display the complete source body of every method you rank in your top three."
ws = (re.search(r"repository path:\s*(\S+)", prompt) or [None, ""])[1]; arch = os.path.realpath(f"{rd}/workspace")
labels_re = r"CT-CHART-0[0-9]|CT-LANG-0[0-9]|cue-trust|mechanism-search|VARIANT_KEY|gold_rank|" + "|".join(re.escape(x) for x in {K["instance_id"], K.get("group") or K["instance_id"]})
meta_files = subprocess.run(["find", arch, "(", "-name", "evaluation.json", "-o", "-name", "variant_manifest.json", "-o", "-name", "validation.json", "-o", "-name", "VARIANT_KEY*",
                             "-o", "-name", "spec.json", "-o", "-name", "*.patch", "-o", "-name", "ranking.json", "-o", "-name", "run_manifest.json", ")"], capture_output=True, text=True).stdout.split()
labels = subprocess.run(["grep", "-rIlE", labels_re, arch], capture_output=True, text=True).stdout.split()
preds = ((rk.get("structured_submission") or {}).get("predictions") or rk.get("predictions") or []); keys = [f"{p.get('class')}::{p.get('method')}" for p in preds]
golds = K["gold"] if isinstance(K["gold"], list) else [K["gold"]]; recomputed = min([keys.index(g) + 1 for g in golds if g in keys] or [None]) if keys else None
ran_ant = any("Running ant" in o for o in outs)
stubA_ant = any("Running ant" in (m.get("content") or "") for m in rj(f"{stubA}/mini-swe-agent.traj.json").get("messages", []) if m.get("role") == "tool")
items = {
 "1_model_call_succeeds": {"pass": bool(resp) and S.classify(rd)["kind"] == "behavioural" and all(str(r.get("model", "")).startswith("gpt-5.6") for r in resp if r), "evidence": f"{len(resp)} responses, status {man.get('status')}, reasoning tokens {reas}"},
 "2_defects4j_test_through_ant": {"pass": ran_ant or (stubA_ant and same_code), "evidence": "smoke run tool output" if ran_ant else "cue-trust-v3 stand-in run on byte-identical code"},
 "3_opaque_workspace_id": {"pass": bool(re.search(r"/CTV-[0-9A-F]{6}$", ws)) and ws.endswith(V), "evidence": ws},
 "4_workspace_outside_repo": {"pass": bool(rec.get("workspace_isolation_ok")) and not os.path.realpath(ws or "/").startswith("/Users/shawnli/Desktop/Honours/defects4j/"), "evidence": f"isolation_ok={rec.get('workspace_isolation_ok')}"},
 "5_sibling_results_inaccessible": {"pass": rec.get("contaminated") is False and rec.get("scan_ok") is True, "evidence": f"contaminated={rec.get('contaminated')} scan_ok={rec.get('scan_ok')} flagged={rec.get('flagged_calls')}"},
 "6_no_gold_or_condition_metadata": {"pass": not meta_files and not labels, "evidence": f"metadata {meta_files[:3]} labels {labels[:3]}"},
 "7_prompt_arm_flag": {"pass": pr.get("inspection_requirement") is False and prompt.count(SENT) == 0, "evidence": f"inspection_requirement={pr.get('inspection_requirement')}"},
 "8_F1_sentence_exactly_once": {"pass": open(f"{stubB}/prompt.txt").read().count(SENT) == 1 and same_code, "evidence": "cue-trust-v3 stand-in F1 run on byte-identical server code"},
 "9_no_source_modification": {"pass": si.get("ok") is True and rj(f"{stubB}/source_integrity.json").get("ok") is False and same_code, "evidence": f"smoke integrity ok={si.get('ok')}; detection proven by the cue-trust stand-in write"},
 "10_output_parsed": {"pass": len(keys) == 10 and ev.get("gold_rank") == recomputed, "evidence": f"{len(keys)} predictions, gold_rank {ev.get('gold_rank')} recomputed {recomputed}"},
 "x_reasoning_effort_pinned": {"pass": pr.get("reasoning_effort") == "medium" and bool(re.search(r'^\s*reasoning_effort:\s*"medium"\s*$', cfg_yaml, re.M)), "evidence": f"prompt.json {pr.get('reasoning_effort')}"},
 "x_protocol_identity": {"pass": rec.get("protocol_identity_ok") is True and rec.get("verdict") == "valid", "evidence": f"verdict {rec.get('verdict')} identity {rec.get('protocol_identity_ok')}"},
 "x_made_under_this_freeze": {"pass": rec.get("freeze_digest") == DIGEST and rec.get("plan_sha256") == smoke_sha, "evidence": f"digest match {rec.get('freeze_digest') == DIGEST}; plan match {rec.get('plan_sha256') == smoke_sha}"}}
out = {"smoke_run": os.path.relpath(rd, C.V3), "cost_usd": ((traj.get("info") or {}).get("model_stats") or {}).get("instance_cost"), "items": items,
       "all_pass": all(v["pass"] for v in items.values()), "freeze_digest": DIGEST, "same_server_code_as_cue_trust_proofs": same_code}
json.dump(out, open(f"{C.V3}/diagnostic/PHASE1_ACCEPTANCE.json", "w"), indent=1)
for k, v in items.items(): print(f"{'PASS' if v['pass'] else 'FAIL'} {k}: {v['evidence'][:140]}")
print("ALL PASS" if out["all_pass"] else "NOT ACCEPTED")
