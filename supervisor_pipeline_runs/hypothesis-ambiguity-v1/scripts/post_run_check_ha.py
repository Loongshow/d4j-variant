#!/opt/miniconda3/bin/python
"""Post-run gate for the HA resume block. Usage: post_run_check_ha.py <HA-LOW-01|HA-HIGH-01> <run-NNN>
Runs the multi-project run_health_check (observable artifacts only) and adds the resume-block checks:
ranking submitted (ranking.json with predictions), frozen-protocol identity (base prompt sha, budget 50/5/300, model gpt-5.6,
agent profile), harness source integrity, gold rank. Prints one JSON line and a verdict; exit 0 = 'continue', 1 = 'stop'.
"""
import json, os, subprocess, sys, datetime
HA = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/hypothesis-ambiguity-v1'
RUNS = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6'
HC = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1/scripts/run_health_check.py'
FROZEN = {'base_prompt_sha256': '845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89', 'max_tool_calls': 50, 'max_test_runs': 5, 'timeout_seconds': 300, 'model': 'gpt-5.6', 'agent_id': 'mini-swe-agent-openai-gpt-5-6'}
V, RUN = sys.argv[1], sys.argv[2]; R = f'{RUNS}/{V}/{RUN}'
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
hc = subprocess.run([sys.executable, HC, R], capture_output=True, text=True)
try: h = json.loads(hc.stdout)
except Exception: h = {'raw': hc.stdout[-400:], 'err': hc.stderr[-400:]}
traj = rj(f'{R}/mini-swe-agent.traj.json'); ms = ((traj.get('info') or {}).get('model_stats') or {})
if h.get('cost_usd') is None: h['cost_usd'] = ms.get('cost', ms.get('instance_cost'))
man = rj(f'{R}/run_manifest.json'); rk = rj(f'{R}/ranking.json'); ev = rj(f'{R}/evaluation.json'); si = rj(f'{R}/source_integrity.json')
preds = rk.get('predictions') or (rk.get('submission') or {}).get('predictions') or []
ident = {'base_prompt_sha256': (man.get('prompt') or {}).get('base_prompt_sha256'), 'max_tool_calls': (man.get('budget') or {}).get('max_tool_calls'), 'max_test_runs': (man.get('budget') or {}).get('max_test_runs'),
         'timeout_seconds': (man.get('budget') or {}).get('timeout_seconds'), 'model': (man.get('agent') or {}).get('model'), 'agent_id': (man.get('agent') or {}).get('agent_id')}
ident_ok = ident == FROZEN
res = {'run': f'{V}/{RUN}', 'status': man.get('status'), 'ranking_submitted': bool(preds), 'n_predictions': len(preds), 'gold_rank': ev.get('gold_rank'),
       'health': h.get('verdict'), 'tool_calls': h.get('tool_calls'), 'model_responses': h.get('model_responses'), 'wall_clock_s': h.get('wall_clock_s'), 'first_response_s': h.get('start_to_first_response_s'),
       'max_gap_s': h.get('max_inter_response_gap_s'), 'retry_lines': h.get('retry_lines'), 'provider_error_lines': h.get('provider_error_lines'), 'source_integrity_ok': h.get('source_integrity_ok'),
       'protocol_identity_ok': ident_ok, 'identity_diff': None if ident_ok else {k: (ident[k], FROZEN[k]) for k in FROZEN if ident[k] != FROZEN[k]}, 'cost_usd': h.get('cost_usd'),
       'checked_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
cont = res['status'] == 'completed' and res['ranking_submitted'] and res['health'] == 'normal completion' and res['source_integrity_ok'] in (True, 'true') and ident_ok
res['verdict'] = 'continue' if cont else 'stop: ' + ('provider stall / harness event' if res['status'] != 'completed' else 'anomaly (see fields)')
line = json.dumps(res); print(line); open(f'{HA}/diagnostic/resume_block.log', 'a').write(line + '\n')
sys.exit(0 if cont else 1)
