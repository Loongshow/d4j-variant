#!/opt/miniconda3/bin/python
"""Bounded provider probe for one model server. Usage: probe_model.py <port> <name> [limit_s]"""
import glob, json, os, re, subprocess, sys, time, datetime
D = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/diagnostic'
PORT, NAME = sys.argv[1], sys.argv[2]; LIMIT = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
nums = [int(re.search(r'_(\d+)\.json$', p).group(1)) for p in glob.glob(f'{D}/probe_{NAME}_*.json')]
n = max(nums + [0]) + 1; out = f'{D}/probe_{NAME}_{n}.json'; tmp = out + '.tmp'
ANOM = re.compile(r'retry|retrying|nodename nor servname|dns|connection (?:error|reset|refused)|timed? ?out|ECONNRESET|EAI_|APIConnectionError|RateLimit|overloaded|insufficient', re.I)
t0 = time.time(); stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'); verdict = 'fail'; detail = ''; wall = None
try:
    r = subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:{PORT}/api/agents/mini-swe-agent/smoke-test', '-H', 'content-type: application/json',
                        '-d', '{"agent_id":"mini-swe-claude"}', '-o', tmp, '-w', '%{http_code}'], capture_output=True, text=True, timeout=LIMIT)
    wall = time.time() - t0; code = r.stdout.strip()
    if code == '200' and os.path.exists(tmp):
        d = json.load(open(tmp)); os.replace(tmp, out)
        m = re.search(r'exit_code: (\S+)', d.get('commands', '') or ''); exit_code = m.group(1) if m else '?'
        timed = 'timed_out: true' in (d.get('commands', '') or '')
        anom = sorted(set(x.lower() for x in ANOM.findall((d.get('raw_output', '') or '') + (d.get('status_reason', '') or ''))))
        ok = d.get('status') == 'passed' and wall <= LIMIT and exit_code == '0' and not timed and not anom
        verdict = 'fast_pass' if ok else 'slow_or_anomalous'
        detail = f"status={d.get('status')} exit={exit_code} anomalies={anom or 'none'} cost={(d.get('model_stats') or {}).get('instance_cost')}"
    else:
        detail = f'http={code}'
        if os.path.exists(tmp): os.remove(tmp)
except subprocess.TimeoutExpired:
    wall = time.time() - t0; verdict = 'hang_killed'; detail = f'no response within {LIMIT:.0f} s'
    if os.path.exists(tmp): os.remove(tmp)
line = f'{NAME} probe {n} at {stamp}: {verdict} | wall {wall:.1f}s | {detail}'
open(f'{D}/health_gate_{NAME}.log', 'a').write(line + '\n'); print(line); sys.exit(0 if verdict == 'fast_pass' else 1)
