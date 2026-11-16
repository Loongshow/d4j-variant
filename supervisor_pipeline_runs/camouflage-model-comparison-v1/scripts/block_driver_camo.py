#!/opt/miniconda3/bin/python
"""Block driver for the 30-run camouflage block (Experiment A): ONE slot at a time, LOW before HIGH per pair, in the frozen order. Health gate = N consecutive fast probes
(N = 3 before the first run and after any infrastructure-affected slot, N = 1 between normally completed slots). Never reruns, replaces or adds slots.
Halts on: contamination, integrity/identity failure, launcher refusal, a gate that fails 12 probes in a row, a launcher that does not finish within 4 h.
Writes diagnostic-gpt56/driver_camo.log and driver_state.json. Usage: block_driver_camo.py [--start-at VID]"""
import json, os, re, subprocess, sys, time, datetime, glob
S = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1'; SU = S + '/experiment-a-camouflage/diagnostic'; PY = sys.executable
RUNS = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6'
ORDER = ['LANG-CONV-CAMOUFLAGE-LOW', 'LANG-CONV-CAMOUFLAGE-HIGH', 'MATH-NORM-CAMOUFLAGE-LOW', 'MATH-NORM-CAMOUFLAGE-HIGH', 'JKC-SURR-CAMOUFLAGE-LOW', 'JKC-SURR-CAMOUFLAGE-HIGH']
PLANNED = 5; MAX_FAILED_PROBES_PER_GATE = 12; PROBE_RETRY_WAIT = 45
def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def log(msg):
    line = f'[{now()}] {msg}'; print(line, flush=True); open(f'{SU}/driver_camo.log', 'a').write(line + '\n')
state = {'started_at': now(), 'slots': [], 'halted': None, 'gate_events': []}
def save(): json.dump(state, open(f'{SU}/driver_state.json', 'w'), indent=1)
def probe():
    r = subprocess.run([PY, f'{S}/scripts/probe_camo.py', '30'], capture_output=True, text=True); return r.returncode == 0, r.stdout.strip()
def gate(n_needed, why):
    ok = 0; failed = 0; log(f'gate: need {n_needed} consecutive fast probes ({why})')
    while ok < n_needed:
        passed, line = probe(); log('  ' + line); state['gate_events'].append({'at': now(), 'line': line, 'why': why}); save()
        if passed: ok += 1
        else:
            ok = 0; failed += 1
            if failed >= MAX_FAILED_PROBES_PER_GATE: return False
            time.sleep(PROBE_RETRY_WAIT)
    return True
def existing_runs(v): return sorted(glob.glob(f'{RUNS}/{v}/run-*'))
need = 3; start_at = sys.argv[sys.argv.index('--start-at') + 1] if '--start-at' in sys.argv else None; started = start_at is None
for V in ORDER:
    if not started:
        if V == start_at: started = True
        else: continue
    while len(existing_runs(V)) < PLANNED:
        if not gate(need, 'before launch'):
            state['halted'] = {'at': now(), 'reason': 'provider health gate repeatedly fails', 'next_slot': V}; save(); log('HALT: provider health gate repeatedly fails'); sys.exit(1)
        n_before = len(existing_runs(V)); run_id = f'run-{n_before + 1:03d}'
        r = subprocess.run(['zsh', f'{S}/scripts/launch_camo_run.sh', V], capture_output=True, text=True); out = (r.stdout + r.stderr).strip(); log(f'launch {V} {run_id}: ' + out.replace('\n', ' | ')[:300])
        if 'refusing' in out or r.returncode != 0:
            state['halted'] = {'at': now(), 'reason': 'launcher refused: ' + out[-200:], 'next_slot': f'{V}/{run_id}'}; save(); log('HALT: launcher refused'); sys.exit(1)
        logp = f'{SU}/launcher_{V}_{run_id}.log'; t0 = time.time(); finished = False
        while time.time() - t0 < 4 * 3600:
            txt = open(logp, errors='replace').read() if os.path.exists(logp) else ''
            if '== launcher finished' in txt: finished = True; break
            if 'refusing' in txt: break
            time.sleep(15)
        if not finished:
            txt = open(logp, errors='replace').read() if os.path.exists(logp) else ''
            state['halted'] = {'at': now(), 'reason': 'launcher did not finish (refusal or 4 h wait)', 'slot': f'{V}/{run_id}', 'log_tail': txt[-400:]}; save(); log('HALT: launcher did not finish'); sys.exit(1)
        if len(existing_runs(V)) != n_before + 1:
            state['halted'] = {'at': now(), 'reason': f'unexpected run count for {V}: {len(existing_runs(V))} (expected {n_before + 1})'}; save(); log('HALT: unexpected run count'); sys.exit(1)
        c = subprocess.run([PY, f'{S}/scripts/post_run_check_camo.py', V, run_id], capture_output=True, text=True)
        try: res = json.loads(c.stdout.strip().splitlines()[-1])
        except Exception: res = {'verdict': 'STOP_INTEGRITY', 'error': (c.stdout + c.stderr)[-300:]}
        state['slots'].append({'variant': V, 'run': run_id, 'launched_at': now(), 'verdict': res.get('verdict'), 'status': res.get('status'), 'gold_rank': res.get('gold_rank'), 'tool_calls': res.get('tool_calls'), 'cost_usd': res.get('cost_usd'), 'wall_clock_s': res.get('wall_clock_s')}); save()
        log(f'post-run {V}/{run_id}: verdict={res.get("verdict")} status={res.get("status")} rank={res.get("gold_rank")} tc={res.get("tool_calls")} wall={res.get("wall_clock_s")} cost={res.get("cost_usd")} oow_flagged={res.get("oow_flagged_calls")} contaminated={res.get("contaminated")}')
        v = res.get('verdict')
        if v == 'continue': need = 1
        elif v in ('infrastructure', 'continue_after_gate'): need = 3; log(f'slot preserved as {v}; next launch requires 3 consecutive fast probes')
        else:
            state['halted'] = {'at': now(), 'reason': v, 'slot': f'{V}/{run_id}', 'detail': res}; save(); log(f'HALT: {v} at {V}/{run_id}'); sys.exit(1)
state['finished_at'] = now(); save(); log('BLOCK FINISHED: all planned slots attempted')
