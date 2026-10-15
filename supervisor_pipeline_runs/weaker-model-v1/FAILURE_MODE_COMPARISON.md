# Failure-mode comparison: gpt-5.5 (Stage A) vs GPT-5.6 on the same instances

## Method

- **gpt-5.5, 26 wrong runs (Stage A).** Each run was labelled by two separately launched agents instructed to work independently, without each
  other's labels or the coordinator's notes: a process lens (what the agent read, ran and saw) and an argument lens (the premises of the final
  evidence chain checked against the patches). Labels use the Phase 7 set preregistered in mechanism-search-v1. A third agent
  adjudicated any disagreement on primary label or defensibility. Each was pointed at the safe trajectory view and the two patches; the workflow record
  keeps a truncated prompt preview and tool-call counts (6 to 21 per labeller), not a log of what each labeller opened. Agreement on primary label and defensibility: 15 of 26 runs full, 2 primary-only, 9 none; 11 adjudicated. Secondary labels
  were not adjudicated; in 3 of the 15 agreeing runs the lenses differed on the secondary and the process lens's was kept. Records:
  `analysis/failure_modes/labels_stageA_blind.json`.
- **GPT-5.6 reference.** Its 12 blind-labelled screening misses span six S1 instances; 10 of them (COMPRESS-07 ×3, DEPTH-01 ×3,
  LB-CHART-01 ×2, MASK-01 ×2) are on the four RH instances re-hosted here, the other two (RH-ADV-DEFINER-01, RH-CF-V1) on
  instances gpt-5.5 never ran. They were labelled the same way in mechanism-search-v1 (post-hoc set mapped to the
  preregistered set in its X12). Its 5 misses on CHART-PIE-TREATMENT-03 and its 8 Closure misses carry the mining labels
  (`mechanism-search-v1/mining/classifications`): one annotator per family, no second lens, no adjudication, and those 16
  reference runs were made without the `reasoning_effort: medium` setting the mxF0 and w55 runs use, so label differences on
  the CHART and Closure rows below are not clean model contrasts. The four RH instances are tier EXPLORATORY (n = 3) in both
  roots; two of them (DEPTH-01, COMPRESS-07) have X4 validity revisions on which GPT-5.6 scored 3/3.
- **Mechanical split** (from the frozen per-run measures, no judgement): for every one of gpt-5.5's 26 misses the gold's fault
  line was displayed, the gold read in full and a test executed. 26/26 ATTRIBUTION_FAILURE by the mechanical definition; 0
  SEARCH_FAILURE, 0 DISCOVERY_WITHOUT_INSPECTION, 0 NO_ANSWER. Five of the 26 are on CHART-PIE-TREATMENT-03, whose gold is
  fixed by the label and the control arm rather than by in-repository evidence (W5), and 4 of the 26 rank-1 answers were
  judged defensible (below).

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
ATTRIBUTION_FAILURE 2, ENTRY_POINT_BIAS 1, none 1.

- The gold was named somewhere in the evidence chain in 22 of 26 misses, and the agent itself described the gold as the
  divergence in 14 of 26, then ranked something else first.
- **Defensibility of the rank-1 answer:** no 17, partly 5, yes 4. The four "yes" are the three CHART treatment runs that
  ranked `drift` first (the drift-vs-shift ownership is genuinely under-specified in that instance) and one DEPTH-01 run that
  cited the decoy's own doc contradiction. Every entry-point answer was judged not defensible: in 10 of the 12 the method ranked first is a
  pass-through facade with no arithmetic (`intArrayToLong`, `computeCheckSum`, `getArcBounds`), and in the other two (CLOSURE-12
  `canInline`, COMPRESS-07 `tally`) the rank-1 is a decoy with its own logic, ranked in call order on an undocumented
  requirement or a repair-site preference; in every case the agent had placed the divergence downstream itself.

## Side by side with GPT-5.6

| Instance | GPT-5.6 misses and labels | gpt-5.5 misses and labels |
|---|---|---|
| CHART-PIE-TREATMENT-03 | 5/5 wrong; all ranked `drift` first; LOCAL_ODDNESS_BIAS ×5 (secondary CONVENTION_PRIOR ×4, DISCOVERY_WITHOUT_INSPECTION ×1) | 5/5 wrong; `drift` ×3 (CONVENTION_PRIOR), `getArcBounds` ×2 (ENTRY_POINT_BIAS; the frozen rank-1 category codes these two as DECOY because `getArcBounds` is declared in both lists for this instance) |
| CLOSURE-12-OWN-001 | 4/5 wrong; ATTRIBUTION_FAILURE 3, LOCAL_ODDNESS_BIAS 1 | 4/5 wrong; EVIDENCE_INTEGRATION 2, CONVENTION_PRIOR 1, ENTRY_POINT 1 |
| CLOSURE-131-OWN-001 | 4/6 wrong; ATTRIBUTION_FAILURE 3, EVIDENCE_INTEGRATION 1; `isSimpleNameChars` first ×4 | 5/5 wrong; EVIDENCE_INTEGRATION 3, RETRIEVAL 1, ATTRIBUTION 1; `isSimpleNameChars` first ×5 |
| ADV-DEPTH-01 | 3/3 wrong; all blamed `overlay` (decoy doc contradiction) | 3/3 wrong; entry point ×2, `overlay` ×1 |
| ADV-MASK-01 | 2/3 wrong; entry point 1, `overlay` 1 | 3/3 wrong; entry point ×3 |
| LB-CHART-01-ADAPTER | 2/3 wrong; `ring` ×2 (convention / caller-argument) | 3/3 wrong; `ring` ×2, entry point ×1 |
| LB-COMPRESS-07-ADAPTER | 3/3 wrong; entry point ×3 | 3/3 wrong; entry point ×2, `tally` ×1 |

## What differs between the models

1. **Same instances break both; gpt-5.5 breaks on more runs** (26 of 27 vs GPT-5.6's 23 of 28 on the same seven breaker
   instances: CHART 5/5, CLOSURE-12 4/5, CLOSURE-131 4/6, DEPTH-01 3/3, MASK-01 2/3, LB-CHART-01 2/3, COMPRESS-07 3/3; the
   CHART control is 5/5 right for both). gpt-5.5 is lower on three instances (CLOSURE-131 0/5 vs 2/6, MASK-01 0/3 vs 1/3,
   LB-CHART-01 0/3 vs 1/3) and equal on the other four; the pooled difference is not distinguishable at these n (Fisher
   two-sided p ≈ 0.19), and without the CHART pair, whose gold is label-defined, it is 21 of 22 vs 18 of 23. The seven were
   chosen because GPT-5.6 had missed them (W5), so "same instances" holds by construction for GPT-5.6 and is a transfer result
   only for gpt-5.5.
2. **Entry-point ranking is the most common label for both models and rises on the shared instances** (GPT-5.6 screening 5 of
   12 over six S1 instances, 4 of 10 on the four RH instances compared here; gpt-5.5 12 of 26 overall, 9 of 12 on those four;
   neither overall share is a majority, and the rise on the four is not established at these n, Fisher p ≈ 0.19).
   gpt-5.5 more often stops at "the method the test calls returns the wrong value" even after naming the deeper cause, and it
   does so on instances where GPT-5.6 had blamed a specific decoy (DEPTH-01, CHART treatment).
3. **gpt-5.5 fetches the distant pin about as often, but never uses it.** On MASK-01 (second caller), LB-CHART-01 (passing
   offset tests, second caller) and CLOSURE-131 (the `TokenStream.isJSIdentifier` reference implementation) gpt-5.5 displayed
   the pin in 3/3, 3/3 and 3/5 of its misses (LB-CHART-01's frozen `evidence_displayed` is true for all three runs of both
   models; GPT-5.6's four CLOSURE-131 misses all have the reference judged retrieved) and never used it to settle ownership,
   whereas GPT-5.6 got rank 1 in one run each on MASK-01 and LB-CHART-01 and in two of six on CLOSURE-131. The difference the
   records show is integration, not retrieval, and gpt-5.5's labels there are evidence-integration or entry-point failures.
4. **Where the convention is under-specified, both models choose the same wrong hop** (`drift`, `ring`,
   `isSimpleNameChars`), which is the signature of the instance rather than of the model.

## Reading for the thesis

On these instances neither model's misses are search failures, with one exception: all 26 gpt-5.5 misses and 22 of GPT-5.6's
23 displayed and fully read the gold and then assigned the fault elsewhere (GPT-5.6's CHART run-003 submitted after grepping
only `shift`'s declaration line): to the entry point, to the hop that defines the convention, or to the method that visibly
lacks a step. On the one matched pair, the 5-hop arm supplies such candidates between the test and the gold and both models
misrank there; whether the weaker current model takes them more often than GPT-5.6 cannot be decided from 3 to 6 runs per
instance (26 of 27 vs 23 of 28 overall), and the chain's own contribution awaits Stage B. The honest limit is the one flagged
in W5's validity note (and restated in WEAKER_MODEL_RESULTS.md §4 and STAGE_B_DESIGN.md): in CHART-PIE-TREATMENT-03 hops 3, 4
and 5 are behaviourally equivalent repair sites, so its gold is defined by the control arm and the label, which is why fresh
Stage B instances with an externally pinned gold are needed before the effect is claimed as a property of chains rather than
of this instance.
