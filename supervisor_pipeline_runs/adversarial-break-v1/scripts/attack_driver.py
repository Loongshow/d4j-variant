#!/opt/miniconda3/bin/python
"""Run attack variants on one model server, one slot at a time, up to --planned runs per variant.
Health gate: 3 fast probes before the block and after any anomaly, 1 between normal slots. Never replaces a slot.
Usage: attack_driver.py --model <opus55|sonnet46|haiku45> --attacks V1,V2,... --planned N"""
import json, os, sys, time, datetime, glob, subprocess, urllib.request, urllib.error, hashlib
R = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1'; D = f'{R}/diagnostic'; PY = sys.executable
PORTS = {'opus55': 8793, 'sonnet46': 8794, 'haiku45': 8795, 'opus55t': 8796, 'sonnet46t': 8797}
MODELS = {'opus55': 'claude-opus-5-5', 'sonnet46': 'claude-sonnet-4-6', 'haiku45': 'claude-haiku-4-5-20251001', 'opus55t': 'claude-opus-5-5', 'sonnet46t': 'claude-sonnet-4-6'}
a = sys.argv; NAME = a[a.index('--model') + 1]; ATT = a[a.index('--attacks') + 1].split(','); PLANNED = int(a[a.index('--planned') + 1])
PORT = PORTS[NAME]; RUNS = f'{R}/models/{NAME}/benchmark_runs/mini-swe-claude'
FROZEN = {'base_prompt_sha256': '845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89', 'max_tool_calls': 50, 'max_test_runs': 5, 'timeout_seconds': 300, 'model': MODELS[NAME], 'agent_id': 'mini-swe-claude'}
def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def log(m):
    line = f'[{now()}] [{NAME}] {m}'; print(line, flush=True); open(f'{D}/driver_{NAME}.log', 'a').write(line + '\n')
def rj(p):
    try: return json.load(open(p))
    except Exception: return {}
def probe():
    r = subprocess.run([PY, f'{R}/scripts/probe_model.py', str(PORT), NAME, '60'], capture_output=True, text=True); return r.returncode == 0, r.stdout.strip()
def gate(n, why):
    ok = failed = 0; log(f'gate: need {n} fast probes ({why})')
    while ok < n:
        p, line = probe(); log('  ' + line)
        if p: ok += 1
        else:
            ok = 0; failed += 1
            if failed >= 8: return False
            time.sleep(45)
    return True
def get(path):
    with urllib.request.urlopen(f'http://127.0.0.1:{PORT}{path}', timeout=30) as r: return json.load(r)
def preflight(V):
    env = get('/api/env'); assert env.get('repoRoot') == f'{R}/models/{NAME}', env.get('repoRoot')
    ags = get('/api/agents'); ags = ags.get('agents') if isinstance(ags, dict) else ags
    p = [x for x in ags if x.get('agent_id') == 'mini-swe-claude'][0]['provider_config']; assert p.get('status') == 'configured' and p.get('model') == MODELS[NAME], p
    vs = get('/api/variants'); vs = vs.get('variants') if isinstance(vs, dict) else vs; assert V in {x.get('variant_id') for x in vs}, f'{V} not discovered'
def launch(V):
    body = {'agent_id': 'mini-swe-claude', 'task_type': 'variant', 'variant_id': V, 'repeats': 1, 'debug_allow_unreproduced_variant': True}
    req = urllib.request.Request(f'http://127.0.0.1:{PORT}/api/benchmark-runs', method='POST', data=json.dumps(body).encode(), headers={'content-type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=1500) as r: return r.status, json.load(r)
    except urllib.error.HTTPError as e: return e.code, {'error': e.read().decode('utf-8', 'replace')[:500]}
def check(V, run):
    rd = f'{RUNS}/{V}/{run}'; man = rj(f'{rd}/run_manifest.json'); ev = rj(f'{rd}/evaluation.json'); rk = rj(f'{rd}/ranking.json'); si = rj(f'{rd}/source_integrity.json'); traj = rj(f'{rd}/mini-swe-agent.traj.json')
    preds = ((rk.get('structured_submission') or {}).get('predictions') or rk.get('predictions') or [])
    ident = {'base_prompt_sha256': (man.get('prompt') or {}).get('base_prompt_sha256'), 'max_tool_calls': (man.get('budget') or {}).get('max_tool_calls'), 'max_test_runs': (man.get('budget') or {}).get('max_test_runs'),
             'timeout_seconds': (man.get('budget') or {}).get('timeout_seconds'), 'model': (man.get('agent') or {}).get('model'), 'agent_id': (man.get('agent') or {}).get('agent_id')}
    ms = (traj.get('info') or {}).get('model_stats') or {}
    oow_out = f'{D}/oow_{NAME}_{V}_{run}.json'; n = int(run.split('-')[-1])
    subprocess.run([PY, '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1/scripts/scan_out_of_workspace.py', RUNS, oow_out, f'{V}:{n}-{n}'], capture_output=True, text=True)
    oow = rj(oow_out); rrec = next((v for k, v in (oow.get('runs') or {}).items() if k.endswith(run)), {}) or {}
    contaminated = bool(rrec.get('contaminating_calls') or rrec.get('contaminated'))
    status = man.get('status'); integrity_ok = si.get('ok', si.get('production_and_test_source_unchanged')) in (True, 'true')
    res = {'model': NAME, 'run': f'{V}/{run}', 'status': status, 'gold_rank': ev.get('gold_rank'), 'n_predictions': len(preds), 'top3': [f"{(p.get('class') or '').split('.')[-1]}::{p.get('method')}" for p in preds[:3]],
           'protocol_identity_ok': ident == FROZEN, 'identity_diff': None if ident == FROZEN else {k: (ident[k], FROZEN[k]) for k in FROZEN if ident[k] != FROZEN[k]},
           'source_integrity_ok': integrity_ok, 'contaminated': contaminated, 'oow_flagged': len(rrec.get('flagged_calls') or []),
           'tool_calls': sum(1 for m in (traj.get('messages') or []) if m.get('role') == 'tool'), 'api_calls': ms.get('api_calls'), 'cost_usd': ms.get('instance_cost'), 'checked_at': now()}
    if contaminated: v = 'STOP_CONTAMINATION'
    elif status == 'completed' and preds and (not integrity_ok or not res['protocol_identity_ok']): v = 'STOP_INTEGRITY'
    elif status != 'completed': v = 'infrastructure'
    elif preds: v = 'continue'
    else: v = 'continue_after_gate'
    res['verdict'] = v; open(f'{D}/block_{NAME}.log', 'a').write(json.dumps(res) + '\n'); return res
need = 3
for V in ATT:
    while len(glob.glob(f'{RUNS}/{V}/run-*')) < PLANNED:
        if not gate(need, 'before launch'): log('HALT: provider gate repeatedly fails'); sys.exit(1)
        try: preflight(V)
        except Exception as e: log(f'HALT: preflight refused: {e}'); sys.exit(1)
        n_before = len(glob.glob(f'{RUNS}/{V}/run-*')); run = f'run-{n_before + 1:03d}'; log(f'launching {V} {run}')
        code, payload = launch(V)
        if len(glob.glob(f'{RUNS}/{V}/run-*')) != n_before + 1: log(f'HALT: unexpected run count after launch (http {code}): {str(payload)[:300]}'); sys.exit(1)
        res = check(V, run)
        log(f"post-run {V}/{run}: {res['verdict']} status={res['status']} rank={res['gold_rank']} top3={res['top3']} tc={res['tool_calls']} cost={res['cost_usd']} contaminated={res['contaminated']}")
        if res['verdict'] == 'continue': need = 1
        elif res['verdict'] in ('infrastructure', 'continue_after_gate'): need = 3
        else: log(f"HALT: {res['verdict']}"); sys.exit(1)
log('BLOCK FINISHED: ' + ','.join(ATT) + f' x{PLANNED}')
