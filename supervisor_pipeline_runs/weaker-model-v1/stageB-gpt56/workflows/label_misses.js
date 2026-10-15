export const meta = {
  name: 'stageB-set2-miss-labels',
  description: 'Blind two-lens failure-mode labelling of Stage B misses (set 2) with the unchanged LABEL_BRIEF, adjudicating disagreements',
  phases: [
    { title: 'Label', detail: 'process lens and argument lens per miss, independent' },
    { title: 'Adjudicate', detail: 'third lens on runs where primary, secondary or defensibility differ' },
  ],
}
const WM = '/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/weaker-model-v1'
const LABELS = ['SEARCH_FAILURE', 'DISCOVERY_WITHOUT_INSPECTION', 'EVIDENCE_RETRIEVAL_FAILURE', 'EVIDENCE_INTEGRATION_FAILURE', 'CONVENTION_PRIOR', 'LOCAL_ODDNESS_BIAS', 'ENTRY_POINT_BIAS', 'LEXICAL_SHORTCUT', 'ATTRIBUTION_FAILURE', 'OTHER']
const LAB = {
  type: 'object',
  properties: {
    run: { type: 'string' }, lens: { type: 'string', enum: ['process', 'argument'] },
    primary: { type: 'string', enum: LABELS }, secondary: { type: ['string', 'null'], enum: [...LABELS, null] },
    defensible: { type: 'string', enum: ['yes', 'partly', 'no'] },
    gold_named_in_chain: { type: 'string', enum: ['yes', 'no'] }, divergence_located_at_gold: { type: 'string', enum: ['yes', 'no'] },
    lie_cited: { type: 'string', enum: ['yes', 'no', 'not_applicable'] },
    evidence_displayed: { type: 'array', items: { type: 'string' } }, rationale: { type: 'string' },
  },
  required: ['run', 'lens', 'primary', 'secondary', 'defensible', 'gold_named_in_chain', 'divergence_located_at_gold', 'lie_cited', 'evidence_displayed', 'rationale'],
}
const ADJ = {
  type: 'object',
  properties: {
    run: { type: 'string' }, primary: { type: 'string', enum: LABELS }, secondary: { type: ['string', 'null'], enum: [...LABELS, null] },
    defensible: { type: 'string', enum: ['yes', 'partly', 'no'] }, divergence_located_at_gold: { type: 'string', enum: ['yes', 'no'] },
    followed: { type: 'string', enum: ['process', 'argument', 'neither'] }, reason: { type: 'string' },
  },
  required: ['run', 'primary', 'secondary', 'defensible', 'divergence_located_at_gold', 'followed', 'reason'],
}
const RULES = `Read ONLY: the brief ${WM}/construction/stageB/LABEL_BRIEF.md, the task file named below, and the safe view and variant patch named in the task file. Do not open any other file, directory, trajectory, model output, report or analysis file; never open .env, raw_agent_output.txt, probe_*.json or diag_run_response.json. No network, no model/API calls. Write no files. Work independently. Additional field "lie_cited": does the agent's final evidence chain cite the facade's inserted javadoc sentence (a procedural description of how the method works that the code does not do)? Use "not_applicable" if the facade carries no such sentence.`
const LENS = { process: 'PROCESS lens as the brief defines it', argument: 'ARGUMENT lens as the brief defines it (check each premise of the final evidence chain against the patch and the displayed code)' }
phase('Label')
const out = await pipeline(args.tasks, async (t) => {
  const labs = await parallel(['process', 'argument'].map(lens => () => agent(`${RULES}\n\nBlind failure-mode labelling, ${LENS[lens]}, for run ${t.run}.\nTask file: ${t.task_file}\nReturn run exactly as "${t.run}" and lens "${lens}".`,
    { label: `${lens}:${t.run}`, phase: 'Label', schema: LAB })))
  return { run: t.run, process: labs[0], argument: labs[1] }
}, async (r) => {
  const p = r.process, a = r.argument
  if (!p || !a) return { ...r, adjudication: null, note: 'labeller failed' }
  if (p.primary === a.primary && p.secondary === a.secondary && p.defensible === a.defensible) return { ...r, adjudication: null, agreed: true }
  const task = args.tasks.find(x => x.run === r.run)
  const adj = await agent(`${RULES}\n\nYou are the third-lens ADJUDICATOR for run ${r.run}. Task file: ${task.task_file}. The two blind labellers disagree on the primary label, the secondary label or defensibility.\nProcess lens:\n${JSON.stringify(p, null, 1)}\nArgument lens:\n${JSON.stringify(a, null, 1)}\n\nRe-read the inputs and decide. Rules used for the earlier blocks of this study, apply them unchanged: (1) when ENTRY_POINT_BIAS and CONVENTION_PRIOR both apply to the same rank-1 choice, the primary follows the agent's own stated reason for rank 1 (documented contract -> CONVENTION_PRIOR primary; being the tested/public API or the repair site -> ENTRY_POINT_BIAS primary); (2) defensibility: "partly" only when the rank-1 method's OWN documentation states an obligation the trigger input observably violates; "no" when its only claim is being called by the test, lying on the call path, or forming the output while its documentation is silent on the violated property; "yes" requires the rank-1 body itself to contain the omission; (3) do not double-count: a secondary EVIDENCE_INTEGRATION_FAILURE is not added when the decisive evidence was used in the chain and the failure is only the ordering. Say which labeller you followed (under 120 words).`,
    { label: `adjudicate:${r.run}`, phase: 'Adjudicate', schema: ADJ })
  return { ...r, adjudication: adj, agreed: false }
})
return out.filter(Boolean)
