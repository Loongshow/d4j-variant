#!/opt/miniconda3/bin/python
"""Non-paid preflight before every pilot slot. Asserts: the isolated pilot server is the expected root,
the Claude profile is configured with the frozen model, the target variant is discovered, the variant
packages reached through the read-only symlink are unchanged, the frozen GPT-5.6 server tree is unchanged,
and the frozen root's run artifacts are untouched. Usage: pilot_preflight.py <VARIANT-ID>"""
import hashlib, json, os, subprocess, sys, urllib.request

SP = '/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs'
R = f'{SP}/anthropic-pilot-v1'; D = f'{R}/diagnostic'
V = sys.argv[1]
FROZEN_MODEL = 'claude-opus-5-5'; AGENT = 'mini-swe-claude'
fail = []


def get(path):
    with urllib.request.urlopen(f'http://127.0.0.1:8793{path}', timeout=30) as r:
        return json.load(r)


env = get('/api/env')
if env.get('repoRoot') != R:
    fail.append(f"pilot server root is {env.get('repoRoot')}, expected {R}")
ags = get('/api/agents'); ags = ags.get('agents') if isinstance(ags, dict) else ags
a = next((x for x in ags if x.get('agent_id') == AGENT), None)
pc = (a or {}).get('provider_config') or {}
if not a or pc.get('status') != 'configured' or pc.get('model') != FROZEN_MODEL or a.get('provider') != 'anthropic':
    fail.append(f"agent {AGENT} not ready as anthropic/{FROZEN_MODEL}: {pc.get('status')} {pc.get('model')}")
if (a or {}).get('defaults') != {'max_tool_calls': 50, 'max_test_runs': 5, 'timeout_seconds': 300}:
    fail.append(f"budget defaults differ from the frozen protocol: {(a or {}).get('defaults')}")
vs = get('/api/variants'); vs = vs.get('variants') if isinstance(vs, dict) else vs
ids = {x.get('variant_id') for x in vs}
if V not in ids:
    fail.append(f'variant {V} not discovered by the pilot server')
for name, root, manifest in (
        ('read-only variant packages', f'{SP}/diagnostic-noncanonical-v3/new_bug_variants', f'{D}/variant_packages_before.txt'),
        ('frozen GPT-5.6 server tree', f'{SP}/diagnostic-noncanonical-v3/variant-lab', f'{D}/frozen_server_tree_before.txt'),
        ('frozen GPT-5.6 run artifacts', f'{SP}/diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6', f'{D}/frozen_runs_before.txt')):
    if not os.path.exists(manifest):
        fail.append(f'{name}: baseline manifest missing ({manifest})'); continue
    p = subprocess.run(['shasum', '-a', '256', '-c', manifest, '--quiet'], cwd=root, capture_output=True, text=True)
    if p.returncode != 0:
        fail.append(f'{name} CHANGED: ' + (p.stdout + p.stderr)[-200:])
print(json.dumps({'variant': V, 'checks_failed': fail, 'ok': not fail}))
sys.exit(0 if not fail else 3)
