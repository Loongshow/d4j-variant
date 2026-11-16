#!/opt/miniconda3/bin/python
"""Claude pilot block driver: ONE slot at a time, CONTROL before TREATMENT (LOW before HIGH) in the frozen
panel order, 3 runs per arm. Health gate = 3 consecutive fast Anthropic probes before the block and after any
anomaly, 1 between normally completed slots. Never reruns, replaces or adds slots. Halts on contamination,
integrity/identity failure, preflight refusal, or a gate that fails 8 probes in a row.
Usage: pilot_driver.py [--planned N]"""
import json, os, subprocess, sys, time, datetime, glob

R = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/anthropic-pilot-v1'
D = f'{R}/diagnostic'; RUNS = f'{R}/benchmark_runs/mini-swe-claude'; PY = sys.executable
ORDER = ['CONVERSION-LONG-CONTROL-01', 'CONVERSION-LONG-TREATMENT-01',
         'CHART-PIE-CONTROL-03', 'CHART-PIE-TREATMENT-03',
         'CMP-LAYOUT-CONTROL-02', 'CMP-LAYOUT-TREATMENT-02',
         'LANG-CONV-CAMOUFLAGE-LOW', 'LANG-CONV-CAMOUFLAGE-HIGH']
PLANNED = int(sys.argv[sys.argv.index('--planned') + 1]) if '--planned' in sys.argv else 3
MAX_FAILED_PROBES = 8; PROBE_WAIT = 45


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def log(m):
    line = f'[{now()}] {m}'
    print(line, flush=True)
    open(f'{D}/driver_claude.log', 'a').write(line + '\n')


state = {'started_at': now(), 'planned_per_arm': PLANNED, 'panel': ORDER, 'slots': [], 'halted': None, 'gate_events': []}


def save():
    json.dump(state, open(f'{D}/driver_state_claude.json', 'w'), indent=1)


def probe():
    r = subprocess.run([PY, f'{R}/scripts/probe_claude.py', '45'], capture_output=True, text=True)
    return r.returncode == 0, r.stdout.strip()


def gate(n_needed, why):
    ok = failed = 0
    log(f'gate: need {n_needed} consecutive fast Anthropic probes ({why})')
    while ok < n_needed:
        passed, line = probe()
        log('  ' + line)
        state['gate_events'].append({'at': now(), 'line': line, 'why': why}); save()
        if passed:
            ok += 1
        else:
            ok = 0; failed += 1
            if failed >= MAX_FAILED_PROBES:
                return False
            time.sleep(PROBE_WAIT)
    return True


def existing(v):
    return sorted(glob.glob(f'{RUNS}/{v}/run-*'))


need = 3
for V in ORDER:
    while len(existing(V)) < PLANNED:
        if not gate(need, 'before launch'):
            state['halted'] = {'at': now(), 'reason': 'Anthropic health gate repeatedly fails', 'next_slot': V}
            save(); log('HALT: Anthropic health gate repeatedly fails'); sys.exit(1)
        pf = subprocess.run([PY, f'{R}/scripts/pilot_preflight.py', V], capture_output=True, text=True)
        if pf.returncode != 0:
            state['halted'] = {'at': now(), 'reason': 'preflight refused', 'detail': pf.stdout[-400:], 'next_slot': V}
            save(); log(f'HALT: preflight refused: {pf.stdout[-300:]}'); sys.exit(1)
        n_before = len(existing(V)); run_id = f'run-{n_before + 1:03d}'
        log(f'launching {V} {run_id}')
        lr = subprocess.run([PY, f'{R}/scripts/launch_pilot_run.py', V, '--out', f'{D}/launch_{V}_{run_id}.json'],
                            capture_output=True, text=True)
        log(f'  launcher exit {lr.returncode}: ' + (lr.stdout or lr.stderr).replace("\n", " ")[:220])
        if len(existing(V)) != n_before + 1:
            state['halted'] = {'at': now(), 'reason': f'unexpected run count for {V}: {len(existing(V))} (expected {n_before + 1})',
                               'launcher': (lr.stdout + lr.stderr)[-400:]}
            save(); log('HALT: unexpected run count'); sys.exit(1)
        c = subprocess.run([PY, f'{R}/scripts/post_run_check_claude.py', V, run_id], capture_output=True, text=True)
        try:
            res = json.loads(c.stdout.strip().splitlines()[-1])
        except Exception:
            res = {'verdict': 'STOP_INTEGRITY', 'error': (c.stdout + c.stderr)[-300:]}
        state['slots'].append({'variant': V, 'run': run_id, 'at': now(), 'verdict': res.get('verdict'),
                               'status': res.get('status'), 'gold_rank': res.get('gold_rank'),
                               'tool_calls': res.get('tool_calls'), 'api_calls': res.get('api_calls'),
                               'cost_usd': res.get('cost_usd'), 'wall_clock_s': res.get('wall_clock_s')})
        save()
        log(f'post-run {V}/{run_id}: verdict={res.get("verdict")} status={res.get("status")} rank={res.get("gold_rank")} '
            f'tc={res.get("tool_calls")} api={res.get("api_calls")} cost={res.get("cost_usd")} '
            f'oow={res.get("oow_flagged_calls")} contaminated={res.get("contaminated")}')
        v = res.get('verdict')
        if v == 'continue':
            need = 1
        elif v in ('infrastructure', 'continue_after_gate'):
            need = 3
            log(f'slot preserved as {v}; next launch requires 3 consecutive fast probes')
        else:
            state['halted'] = {'at': now(), 'reason': v, 'slot': f'{V}/{run_id}', 'detail': res}
            save(); log(f'HALT: {v} at {V}/{run_id}'); sys.exit(1)
state['finished_at'] = now(); save(); log('PILOT BLOCK FINISHED: all planned slots attempted')
