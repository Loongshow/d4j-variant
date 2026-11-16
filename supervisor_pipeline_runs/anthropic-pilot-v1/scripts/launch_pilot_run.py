#!/opt/miniconda3/bin/python
"""Launch exactly ONE pilot run of one variant on the isolated Anthropic server, using the same request
shape the frozen GPT-5.6 blocks used, so the protocol is unchanged across models.

The request carries the harness's documented non-canonical allowance (the pilot panel's variants are
research variants marked benchmark_eligible=false, exactly as they were for every GPT-5.6 run of the same
instances); it is part of the frozen protocol, not a safety override.

Usage: launch_pilot_run.py <VARIANT-ID> [--out <response.json>]
"""
import json, sys, time, urllib.request, urllib.error

API = 'http://127.0.0.1:8793'
AGENT = 'mini-swe-claude'
V = sys.argv[1]
out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
body = {
    'agent_id': AGENT,
    'task_type': 'variant',
    'variant_id': V,
    'repeats': 1,
    'debug_allow_unreproduced_variant': True,
}
req = urllib.request.Request(f'{API}/api/benchmark-runs', method='POST',
                            data=json.dumps(body).encode(),
                            headers={'content-type': 'application/json'})
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=1200) as r:
        payload = json.load(r)
        code = r.status
except urllib.error.HTTPError as e:
    payload = {'http_error': e.code, 'body': e.read().decode('utf-8', 'replace')[:2000]}
    code = e.code
wall = round(time.time() - t0, 1)
res = {'variant_id': V, 'http': code, 'wall_s': wall, 'response': payload}
if out:
    json.dump(res, open(out, 'w'), indent=1)
summary = payload if not isinstance(payload, dict) else {k: payload.get(k) for k in
    ('status', 'run_id', 'runs', 'created', 'records') if k in payload}
print(json.dumps({'variant': V, 'http': code, 'wall_s': wall, 'summary_keys': sorted(payload.keys()) if isinstance(payload, dict) else None,
                  'summary': str(summary)[:600]}, indent=1))
