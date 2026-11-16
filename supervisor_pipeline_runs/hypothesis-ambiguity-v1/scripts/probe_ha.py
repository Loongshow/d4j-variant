#!/opt/miniconda3/bin/python
"""Bounded provider probe for the HA resume gate.
One tiny paid smoke call (POST /api/agents/mini-swe-agent/smoke-test) executed under an EXTERNAL Python subprocess timeout
(default 30 s; the child curl is killed on expiry). Writes the raw server JSON to diagnostic/probe_ha_<n>.json only when the
HTTP call returned 200 with parseable JSON, and appends one line per probe to diagnostic/health_gate_resume.log.
Verdict 'fast_pass' requires: status == passed, wall time <= limit, exit 0 in the smoke command block, and no
retry/DNS/connection/timeout anomaly strings in the server's raw output. Exit code 0 = fast_pass, 1 otherwise.
"""
import glob, json, os, re, subprocess, sys, time, datetime
HA = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/hypothesis-ambiguity-v1'
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
nums = [int(re.search(r'_(\d+)\.json$', p).group(1)) for p in glob.glob(f'{HA}/diagnostic/probe_ha_*.json')]
n = max(nums + [20]) + 1
out = f'{HA}/diagnostic/probe_ha_{n}.json'; tmp = out + '.tmp'
ANOM = re.compile(r'retry|retrying|nodename nor servname|dns|connection (?:error|reset|refused)|timed? ?out|ECONNRESET|EAI_|APIConnectionError|RateLimit', re.I)
t0 = time.time(); stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
verdict = 'fail'; detail = ''
try:
    r = subprocess.run(['curl', '-s', '-X', 'POST', 'http://127.0.0.1:8792/api/agents/mini-swe-agent/smoke-test',
                        '-H', 'content-type: application/json', '-d', '{"agent_id":"mini-swe-agent-openai-gpt-5-6"}',
                        '-o', tmp, '-w', '%{http_code}'], capture_output=True, text=True, timeout=LIMIT)
    wall = time.time() - t0; code = r.stdout.strip()
    if code == '200' and os.path.exists(tmp):
        d = json.load(open(tmp)); os.replace(tmp, out)
        blob = json.dumps(d)
        m = re.search(r'exit_code: (\S+)', d.get('commands', '') or ''); exit_code = m.group(1) if m else '?'
        timed = 'timed_out: true' in (d.get('commands', '') or '')
        anom = sorted(set(x.lower() for x in ANOM.findall((d.get('raw_output', '') or '') + (d.get('status_reason', '') or ''))))
        ok = d.get('status') == 'passed' and wall <= LIMIT and exit_code == '0' and not timed and not anom
        verdict = 'fast_pass' if ok else 'slow_or_anomalous'
        detail = f"status={d.get('status')} exit={exit_code} timed_out={timed} anomalies={anom or 'none'} run_id={d.get('run_id')}"
    else:
        detail = f'http={code}'
        if os.path.exists(tmp): os.remove(tmp)
except subprocess.TimeoutExpired:
    wall = time.time() - t0; verdict = 'hang_killed'; detail = f'no response within {LIMIT:.0f} s; curl killed'
    if os.path.exists(tmp): os.remove(tmp)
line = f'HA probe {n} at {stamp}: {verdict} | wall {wall:.1f}s (limit {LIMIT:.0f}s) | {detail}'
open(f'{HA}/diagnostic/health_gate_resume.log', 'a').write(line + '\n'); print(line)
sys.exit(0 if verdict == 'fast_pass' else 1)
