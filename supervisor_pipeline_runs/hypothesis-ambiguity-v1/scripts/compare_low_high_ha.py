#!/opt/miniconda3/bin/python
"""Seven-question LOW-vs-HIGH summary from hypothesis_ambiguity_results.json (descriptive only; completed runs vs provider-affected attempts kept separate).
Usage: compare_low_high_ha.py <results.json> <out.md>"""
import json, sys, statistics as st
d = json.load(open(sys.argv[1])); runs = d['runs']
def arm(a, completed=True): return [r for r in runs if r['arm'] == a and ((r['status'] == 'completed') == completed)]
def mean(xs): xs = [x for x in xs if x is not None]; return (round(st.mean(xs), 2) if xs else None)
def fmt(xs): return ', '.join('-' if x is None else str(x) for x in xs)
rows = []
def add(label, f):
    L, H = arm('LOW'), arm('HIGH'); lv, hv = [f(r) for r in L], [f(r) for r in H]
    rows.append(f'| {label} | {fmt(lv)} (mean {mean(lv)}) | {fmt(hv)} (mean {mean(hv)}) |')
L, H = arm('LOW'), arm('HIGH'); LP, HP = arm('LOW', False), arm('HIGH', False)
out = ['## LOW vs HIGH — completed runs only (LOW n=%d, HIGH n=%d); provider-affected attempts listed separately below' % (len(L), len(H)), '',
       '| Metric | LOW (completed) | HIGH (completed) |', '|---|---|---|']
rows.append('| Gold ranks | %s | %s |' % (fmt([r['gold_rank'] for r in L]), fmt([r['gold_rank'] for r in H])))
def acc(rs, k): return round(sum(1 for r in rs if r['gold_rank'] and r['gold_rank'] <= k) / len(rs), 2) if rs else None
def mrr(rs): return round(sum((1 / r['gold_rank']) if r['gold_rank'] else 0 for r in rs) / len(rs), 3) if rs else None
rows.append('| Acc@1 / Acc@3 / Acc@5 | %s / %s / %s | %s / %s / %s |' % (acc(L, 1), acc(L, 3), acc(L, 5), acc(H, 1), acc(H, 3), acc(H, 5)))
rows.append('| MRR | %s | %s |' % (mrr(L), mrr(H)))
add('Q1 candidate methods inspected', lambda r: r['n_candidate_methods_inspected'])
add('Q2 wrong candidates seriously investigated', lambda r: len(r['wrong_candidates_seriously_investigated']))
add('Q2b … after the gold was exposed', lambda r: len(r['wrong_candidates_seriously_investigated_after_gold']))
add('Q3 external evidence sources retrieved', lambda r: len(r['external_evidence_sources_used']))
add('Q4 backtracking events', lambda r: r['backtracking_events'])
add('Q5 wrong candidates ranked above gold', lambda r: len(r['wrong_candidates_ranked_above_gold']))
add('Q7 first gold exposure (tool-call step)', lambda r: r['gold_first_exposed_step'])
add('Tool calls to ranking', lambda r: r['tool_call_count'])
add('Calls after gold exposure', lambda r: r['calls_after_gold'])
add('Candidate elimination depth (step)', lambda r: r['candidate_elimination_depth_step'])
add('CED calls before ranking', lambda r: r['ced_calls_before_ranking'])
add('Cost USD', lambda r: round(r['cost_usd'], 4) if r['cost_usd'] is not None else None)
out += rows
def ranks(rs):
    keys = sorted({k for r in rs for k in (r.get('candidate_final_ranks') or {})}, key=lambda k: ['facade','pack','gold','gather','widen','merge','offset','advance','deposit'].index(k) if k in ['facade','pack','gold','gather','widen','merge','offset','advance','deposit'] else 99)
    return keys, [[(r.get('candidate_final_ranks') or {}).get(k) for r in rs] for k in keys]
for a, rs in (('LOW', L), ('HIGH', H)):
    keys, vals = ranks(rs); out += ['', f'**{a} final candidate ranks (completed runs)**', '', '| Candidate | ' + ' | '.join(r['run_id'].split('/')[-1] for r in rs) + ' |', '|---|' + '---|' * len(rs)]
    out += ['| %s | %s |' % (k, ' | '.join('-' if v is None else str(v) for v in vs)) for k, vs in zip(keys, vals)]
out += ['', '**Provider-affected attempts (kept separate; never localization failures)**', '', '| Attempt | Status | Tool calls | Gold exposed | Candidates inspected | Wrong seriously investigated | Evidence sources |', '|---|---|---|---|---|---|---|']
for r in LP + HP: out.append('| %s | %s | %s | %s | %s | %s | %s |' % (r['run_id'], r['status'], r['tool_call_count'], r['gold_first_exposed_step'], r['n_candidate_methods_inspected'], len(r['wrong_candidates_seriously_investigated']), len(r['external_evidence_sources_used'])))
out += ['', 'Classes (completed): LOW %s | HIGH %s' % ({r['run_id'].split('/')[-1]: r['discrimination_class'].split('.')[0] for r in L}, {r['run_id'].split('/')[-1]: r['discrimination_class'].split('.')[0] for r in H}),
        'Lexical-shortcut flags (completed): LOW %s | HIGH %s' % (sum(r['lexical_shortcut_flag'] for r in L), sum(r['lexical_shortcut_flag'] for r in H))]
open(sys.argv[2], 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
