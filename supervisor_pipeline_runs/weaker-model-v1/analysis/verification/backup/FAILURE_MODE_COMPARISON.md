# Failure-mode comparison: gpt-5.5 (Stage A) vs GPT-5.6 on the same instances

## Method

- **gpt-5.5, 26 wrong runs (Stage A).** Each run was labelled by two independent agents who never saw each other's labels or
  the coordinator's notes: a process lens (what the agent read, ran and saw) and an argument lens (the premises of the final
  evidence chain checked against the patches). Labels use the Phase 7 set preregistered in mechanism-search-v1. A third agent
  adjudicated any disagreement on primary label or defensibility. Inputs were the safe trajectory view and the two patches
  only. Agreement: 15 of 26 runs full, 2 primary-only, 9 none; 11 adjudicated. Records:
  `analysis/failure_modes/labels_stageA_blind.json`.
- **GPT-5.6 reference.** Its 12 screening misses on the four RH instances were labelled the same way in mechanism-search-v1
  (post-hoc set mapped to the preregistered set in its X12). Its 5 misses on CHART-PIE-TREATMENT-03 and its Closure misses
  carry the mining labels (`mechanism-search-v1/mining/classifications`).
- **Mechanical split** (from the frozen per-run measures, no judgement): for every one of gpt-5.5's 26 misses the gold's fault
  line was displayed, the gold read in full and a test executed. 26/26 ATTRIBUTION_FAILURE by the mechanical definition; 0
  SEARCH_FAILURE, 0 DISCOVERY_WITHOUT_INSPECTION, 0 NO_ANSWER.

## Preregistered labels, gpt-5.5

| Primary label | Runs | Instances |
|---|---|---|
| ENTRY_POINT_BIAS | 12 | MASK-01 ×3, COMPRESS-07 ×3, DEPTH-01 ×2, CHART treatment ×2, CLOSURE-12 ×1, LB-CHART-01 ×1 |
| EVIDENCE_INTEGRATION_FAILURE | 6 | CLOSURE-131 ×3, CLOSURE-12 ×2, LB-CHART-01 ×1 |
| CONVENTION_PRIOR | 5 | CHART treatment ×3, CLOSURE-12 ×1, LB-CHART-01 ×1 |
| LOCAL_ODDNESS_BIAS | 1 | DEPTH-01 |
| EVIDENCE_RETRIEVAL_FAILURE | 1 | CLOSURE-131 |
| ATTRIBUTION_FAILURE (unspecific) | 1 | CLOSURE-131 |

Secondary labels: EVIDENCE_INTEGRATION_FAILURE 9, LOCAL_ODDNESS_BIAS 7, CONVENTION_PRIOR 4, EVIDENCE_RETRIEVAL_FAILURE 2,
ATTRIBUTION_FAILURE 2, ENTRY_POINT_BIAS 1.

- The gold was named somewhere in the evidence chain in 22 of 26 misses, and the agent itself described the gold as the
  divergence in 14 of 26, then ranked something else first.
- **Defensibility of the rank-1 answer:** no 17, partly 5, yes 4. The four "yes" are the three CHART treatment runs that
  ranked `drift` first (the drift-vs-shift ownership is genuinely under-specified in that instance) and one DEPTH-01 run that
  cited the decoy's own doc contradiction. Every entry-point answer was judged not defensible: in each case the facade is a
  pass-through with no arithmetic, and the agent had placed the divergence downstream itself.

## Side by side with GPT-5.6

| Instance | GPT-5.6 misses and labels | gpt-5.5 misses and labels |
|---|---|---|
| CHART-PIE-TREATMENT-03 | 5/5 wrong; all ranked `drift` first; LOCAL_ODDNESS_BIAS / CONVENTION_PRIOR | 5/5 wrong; `drift` ×3 (CONVENTION_PRIOR), entry point ×2 (ENTRY_POINT_BIAS) |
| CLOSURE-12-OWN-001 | 4/5 wrong; ATTRIBUTION_FAILURE 3, LOCAL_ODDNESS_BIAS 1 | 4/5 wrong; EVIDENCE_INTEGRATION 2, CONVENTION_PRIOR 1, ENTRY_POINT 1 |
| CLOSURE-131-OWN-001 | 4/6 wrong; ATTRIBUTION_FAILURE 3, EVIDENCE_INTEGRATION 1; `isSimpleNameChars` first ×4 | 5/5 wrong; EVIDENCE_INTEGRATION 3, RETRIEVAL 1, ATTRIBUTION 1; `isSimpleNameChars` first ×5 |
| ADV-DEPTH-01 | 3/3 wrong; all blamed `overlay` (decoy doc contradiction) | 3/3 wrong; entry point ×2, `overlay` ×1 |
| ADV-MASK-01 | 2/3 wrong; entry point 1, `overlay` 1 | 3/3 wrong; entry point ×3 |
| LB-CHART-01-ADAPTER | 2/3 wrong; `ring` ×2 (convention / caller-argument) | 3/3 wrong; `ring` ×2, entry point ×1 |
| LB-COMPRESS-07-ADAPTER | 3/3 wrong; entry point ×3 | 3/3 wrong; entry point ×2, `tally` ×1 |

## What differs between the models

1. **Same instances break both; gpt-5.5 breaks on more runs** (26 of 27 vs GPT-5.6's 23 of 30 on the same eight instances:
   CHART 5/5, CLOSURE-12 4/5, CLOSURE-131 4/6, DEPTH-01 3/3, MASK-01 2/3, LB-CHART-01 2/3, COMPRESS-07 3/3).
2. **Entry-point ranking grows from a minority pattern to the dominant one** (GPT-5.6 screening 5 of 12; gpt-5.5 12 of 26).
   gpt-5.5 more often stops at "the method the test calls returns the wrong value" even after naming the deeper cause, and it
   does so on instances where GPT-5.6 had blamed a specific decoy (DEPTH-01, CHART treatment).
3. **gpt-5.5 fetches the distant pin less often.** On MASK-01 (second caller), LB-CHART-01 (passing offset tests, second
   caller) and CLOSURE-131 (the `TokenStream.isJSIdentifier` reference implementation), GPT-5.6 occasionally retrieved and used
   the pin and got rank 1; gpt-5.5 never did, and its labels there are evidence-integration or entry-point failures.
4. **Where the convention is under-specified, both models choose the same wrong hop** (`drift`, `ring`,
   `isSimpleNameChars`), which is the signature of the instance rather than of the model.

## Reading for the thesis

On these instances neither model fails to find the fault. Both find it, read it, and then assign it elsewhere: to the entry
point, to the hop that defines the convention, or to the method that visibly lacks a step. A longer chain supplies more such
candidates between the test and the gold, and the weaker current model takes them more often. The honest limit is the one
flagged in W5 and W8: in CHART-PIE-TREATMENT-03 three hops are equally valid repair sites, so its gold is defined by the
control arm and the label, which is why fresh Stage B instances with an externally pinned gold are needed before the effect is
claimed as a property of chains rather than of this instance.
