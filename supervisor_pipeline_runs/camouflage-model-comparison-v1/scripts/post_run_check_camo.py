#!/opt/miniconda3/bin/python
"""Post-run gate for the scale-up block. Usage: post_run_check_su.py <VARIANT-ID> <run-NNN>
Observable artifacts only: multi-project run_health_check + frozen-protocol identity + ranking submitted + source integrity + single-run out-of-workspace scan
(contamination) + gold rank. Prints one JSON line, appends it to diagnostic-gpt56/block_camo.log. Verdicts: continue | infrastructure (preserve; pause; 3-probe gate) |
continue_after_gate (completed without a ranking or other anomaly; slot consumed) | STOP_CONTAMINATION | STOP_INTEGRITY. Exit 0 only for 'continue'."""
import json, os, subprocess, sys, datetime, hashlib
S = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1/experiment-a-camouflage'; SU = S + '/diagnostic'
RUNS = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6'
MP = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1/scripts'
FROZEN = {'base_prompt_sha256': '845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89', 'max_tool_calls': 50, 'max_test_runs': 5, 'timeout_seconds': 300, 'model': 'gpt-5.6', 'agent_id': 'mini-swe-agent-openai-gpt-5-6'}
V, RUN = sys.argv[1], sys.argv[2]; R = f'{RUNS}/{V}/{RUN}'; n = int(RUN.split('-')[-1])
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
hc = subprocess.run([sys.executable, f'{MP}/run_health_check.py', R], capture_output=True, text=True)
try: h = json.loads(hc.stdout)
except Exception: h = {'raw': hc.stdout[-400:], 'err': hc.stderr[-400:]}
traj = rj(f'{R}/mini-swe-agent.traj.json'); ms = ((traj.get('info') or {}).get('model_stats') or {})
if h.get('cost_usd') is None: h['cost_usd'] = ms.get('cost', ms.get('instance_cost'))
man = rj(f'{R}/run_manifest.json'); rk = rj(f'{R}/ranking.json'); ev = rj(f'{R}/evaluation.json'); si = rj(f'{R}/source_integrity.json')
preds = (rk.get('structured_submission') or {}).get('predictions') or rk.get('predictions') or (rk.get('submission') or {}).get('predictions') or []
ident = {'base_prompt_sha256': (man.get('prompt') or {}).get('base_prompt_sha256'), 'max_tool_calls': (man.get('budget') or {}).get('max_tool_calls'), 'max_test_runs': (man.get('budget') or {}).get('max_test_runs'),
         'timeout_seconds': (man.get('budget') or {}).get('timeout_seconds'), 'model': (man.get('agent') or {}).get('model'), 'agent_id': (man.get('agent') or {}).get('agent_id')}
ident_ok = ident == FROZEN
oow_out = f'{SU}/oow_camo_{V}_{RUN}.json'
sc = subprocess.run([sys.executable, f'{MP}/scan_out_of_workspace.py', RUNS, oow_out, f'{V}:{n}-{n}'], capture_output=True, text=True); oow = rj(oow_out)
rrec = None
for k, v in (oow.get('runs') or {}).items():
    if k.endswith(RUN) or k == f'{V}/{RUN}' or k == RUN: rrec = v
if rrec is None and (oow.get('runs') or {}): rrec = list(oow['runs'].values())[0]
flagged = (rrec or {}).get('flagged') or (rrec or {}).get('flagged_calls') or []; contaminated = (rrec or {}).get('contaminated') or (rrec or {}).get('contamination') or []
status = man.get('status'); integrity_ok = si.get('ok', si.get('production_and_test_source_unchanged')) in (True, 'true')
res = {'run': f'{V}/{RUN}', 'status': status, 'status_reason': (man.get('status_reason') or '')[:120], 'ranking_submitted': bool(preds), 'n_predictions': len(preds), 'gold_rank': ev.get('gold_rank'),
       'health': h.get('verdict'), 'tool_calls': h.get('tool_calls'), 'model_responses': h.get('model_responses'), 'wall_clock_s': h.get('wall_clock_s'), 'first_response_s': h.get('start_to_first_response_s'),
       'max_gap_s': h.get('max_inter_response_gap_s'), 'retry_lines': h.get('retry_lines'), 'provider_error_lines': h.get('provider_error_lines'), 'source_integrity_ok': integrity_ok,
       'protocol_identity_ok': ident_ok, 'identity_diff': None if ident_ok else {k: (ident[k], FROZEN[k]) for k in FROZEN if ident[k] != FROZEN[k]}, 'cost_usd': h.get('cost_usd'),
       'oow_flagged_calls': len(flagged), 'oow_flagged': flagged[:6], 'contaminated': bool(contaminated), 'contamination_detail': contaminated[:4], 'oow_camo_file': os.path.relpath(oow_out, S),
       'checked_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
if contaminated: verdict = 'STOP_CONTAMINATION'
elif (status == 'completed' and preds) and (not integrity_ok or not ident_ok): verdict = 'STOP_INTEGRITY'
elif status in ('timeout', 'startup_timeout') or (status != 'completed'): verdict = 'infrastructure'
elif status == 'completed' and preds and res['health'] == 'normal completion': verdict = 'continue'
else: verdict = 'continue_after_gate'
res['verdict'] = verdict
if status == 'completed':  # protect this run's top-level artifacts for later preflights
    with open(f'{SU}/run_artifact_hashes_camo.txt', 'a') as f:
        for fn in sorted(os.listdir(R)):
            p = os.path.join(R, fn)
            if os.path.isfile(p): f.write(hashlib.sha256(open(p, 'rb').read()).hexdigest() + f'  {V}/{RUN}/{fn}\n')
line = json.dumps(res); print(line); open(f'{SU}/block_camo.log', 'a').write(line + '\n')
sys.exit(0 if verdict == 'continue' else 1)
