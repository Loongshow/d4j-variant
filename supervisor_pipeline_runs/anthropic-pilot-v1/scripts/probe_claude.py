#!/opt/miniconda3/bin/python
"""Bounded Anthropic provider probe for the pilot (same mechanism as the frozen GPT-5.6 probes).
One tiny paid smoke call to the isolated pilot server under an EXTERNAL subprocess timeout (default 45 s).
Writes the raw server JSON to diagnostic/probe_claude_<n>.json only on HTTP 200 + parseable JSON, and one
line per probe to diagnostic/health_gate_claude.log. Verdict 'fast_pass' requires status == passed, wall
within the bound, exit 0, no timed_out and no retry/DNS/connection/rate-limit anomaly strings. Exit 0 = fast_pass."""
import glob, json, os, re, subprocess, sys, time, datetime
D = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/anthropic-pilot-v1/diagnostic'
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
nums = [int(re.search(r'_(\d+)\.json$', p).group(1)) for p in glob.glob(f'{D}/probe_claude_*.json')]
n = max(nums + [0]) + 1
out = f'{D}/probe_claude_{n}.json'; tmp = out + '.tmp'
ANOM = re.compile(r'retry|retrying|nodename nor servname|dns|connection (?:error|reset|refused)|timed? ?out|'
                  r'ECONNRESET|EAI_|APIConnectionError|RateLimit|overloaded_error|insufficient', re.I)
t0 = time.time(); stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
verdict = 'fail'; detail = ''; wall = None
try:
    r = subprocess.run(['curl', '-s', '-X', 'POST', 'http://127.0.0.1:8793/api/agents/mini-swe-agent/smoke-test',
                        '-H', 'content-type: application/json', '-d', '{"agent_id":"mini-swe-claude"}',
                        '-o', tmp, '-w', '%{http_code}'], capture_output=True, text=True, timeout=LIMIT)
    wall = time.time() - t0; code = r.stdout.strip()
    if code == '200' and os.path.exists(tmp):
        d = json.load(open(tmp)); os.replace(tmp, out)
        m = re.search(r'exit_code: (\S+)', d.get('commands', '') or ''); exit_code = m.group(1) if m else '?'
        timed = 'timed_out: true' in (d.get('commands', '') or '')
        anom = sorted(set(x.lower() for x in ANOM.findall((d.get('raw_output', '') or '') + (d.get('status_reason', '') or ''))))
        ok = d.get('status') == 'passed' and wall <= LIMIT and exit_code == '0' and not timed and not anom
        verdict = 'fast_pass' if ok else 'slow_or_anomalous'
        cost = ((d.get('model_stats') or {}) or {}).get('instance_cost')
        detail = f"status={d.get('status')} exit={exit_code} timed_out={timed} anomalies={anom or 'none'} run_id={d.get('run_id')}"
    else:
        detail = f'http={code}'
        if os.path.exists(tmp): os.remove(tmp)
except subprocess.TimeoutExpired:
    wall = time.time() - t0; verdict = 'hang_killed'; detail = f'no response within {LIMIT:.0f} s; curl killed'
    if os.path.exists(tmp): os.remove(tmp)
line = f'CLAUDE probe {n} at {stamp}: {verdict} | wall {wall:.1f}s (limit {LIMIT:.0f}s) | {detail}'
open(f'{D}/health_gate_claude.log', 'a').write(line + '\n'); print(line)
sys.exit(0 if verdict == 'fast_pass' else 1)
