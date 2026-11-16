# Failure-mode analysis (Phase 7): every wrong GPT-5.6 run in mechanism-search-v1

## Scope

- **Valid runs:** 140 in total, made up of 90 screening runs (S1 54, S2 36), 6 Phase 4 runs and 44 held-out runs.
- **Wrong runs (gold not at rank 1):** **13**, made up of 12 in S1 and 1 held-out no-answer.
- **Blocks with no wrong runs:** S2 and Phase 4.
- **Excluded from scoring:** runs that were infrastructure, contaminated or invalid (MECHANISM_SCREENING_REPORT.md,
  HELDOUT_CONFIRMATION_RESULTS.md).

## Method

1. **Coordinator labels.** Before the blind pass, the coordinator labelled the 12 S1 misses from their submitted evidence
   chains (`analysis/failure_modes/labels_S1.json`).
2. **Two blind labellers per run.** A workflow gave each of the 12 S1 wrong runs two independent labellers, who were not
   given the coordinator's labels (the archived record cannot confirm this: the stored prompt previews are truncated, and
   `labels_S1.json` was readable in the same worktree). The held-out no-answer run was not put through the workflow. The
   two lenses were:
   - a **process** lens: what the agent read, ran and saw, and where it turned away from the gold;
   - an **argument** lens: the premises and inferences in the final evidence chain, checked against the code and javadocs.
3. **Adjudication.** A third agent was to adjudicate any disagreement on mode or defensibility. No adjudication was needed.
4. **Inputs.** Labellers saw only `scripts/mx_traj_view.py`, a safe view showing the submission and the visible messages and
   tool calls (never hidden reasoning, raw output or credential files), plus the variant and test patches.
5. **Taxonomy and output.** The labels use a post-hoc taxonomy rather than the Phase 7 label set preregistered in
   PREREGISTRATION.md (Measures), and AMENDMENTS.md records no amendment for this change. The blind labellers' definitions
   were given in the labelling workflow script, which is not archived in this directory; only its output
   (`analysis/failure_modes/workflow_screening_raw.txt`, with truncated prompt previews) is. The coordinator's definitions
   are in `labels_S1.json` (`_definitions`). The results are in `analysis/failure_modes/labels_screening_blind.json`.

**Defensibility** asks whether the rank-1 method is itself a documentation-consistent fault location. It takes one of three
values:

- **yes:** the gold is ambiguous for this run;
- **partly:** the answer has a documented argument, but the gold is better supported;
- **no:** the answer contradicts documented contracts or evidence available in the repository.

## Results: S1 screening misses (12 runs, 6 instances)

| Run | Instance | Rank-1 | Gold rank | Primary mode | Secondary | Agent named the gold as the divergence | Defensible |
|---|---|---|---|---|---|---|---|
| CTV-1139CC/001 | LB-COMPRESS-07-ADAPTER | TarUtils::computeCheckSum (entry) | 3 | ENTRY_POINT_RANKING | ALTERNATIVE_REPAIR_SITE | yes | no |
| CTV-1139CC/002 | LB-COMPRESS-07-ADAPTER | TarUtils::computeCheckSum (entry) | 3 | ENTRY_POINT_RANKING | — | yes | no |
| CTV-1139CC/003 | LB-COMPRESS-07-ADAPTER | TarUtils::computeCheckSum (entry) | 3 | ENTRY_POINT_RANKING | ALTERNATIVE_REPAIR_SITE | yes | no |
| CTV-D0D56D/001 | ADV-MASK-01 | Conversion::intArrayToLong (entry) | 2 | ENTRY_POINT_RANKING | ALTERNATIVE_REPAIR_SITE | yes | no |
| CTV-E72EE8/002 | CF-V1 | PiePlot::getArcBounds (entry) | 2 | ENTRY_POINT_RANKING | — | yes | no |
| CTV-C9C374/001 | ADV-DEPTH-01 | NumberUtils::overlay | 2 | DECOY_DOC_CONTRADICTION | SINK_BLAME | yes | **yes** |
| CTV-C9C374/002 | ADV-DEPTH-01 | NumberUtils::overlay | 3 | DECOY_DOC_CONTRADICTION | SINK_BLAME | yes | **yes** |
| CTV-C9C374/003 | ADV-DEPTH-01 | NumberUtils::overlay | 2 | DECOY_DOC_CONTRADICTION | SINK_BLAME | yes | **yes** |
| CTV-AE931C/001 | LB-CHART-01-ADAPTER | CompassPlot::ring | 4 | CALLER_ARGUMENT_BLAME | CONVENTION_ATTRIBUTION | yes | no |
| CTV-AE931C/002 | LB-CHART-01-ADAPTER | CompassPlot::ring | 4 | CONVENTION_ATTRIBUTION | CALLER_ARGUMENT_BLAME | no | no |
| CTV-BFBD6F/001 | ADV-DEFINER-01 | PlotUtilities::drift | 5 | CONVENTION_ATTRIBUTION | — | no | no |
| CTV-D0D56D/003 | ADV-MASK-01 | NumberUtils::overlay | 4 | MASK_PLACEMENT_ATTRIBUTION | SINK_BLAME | no | no |

**Summary across the 12 runs:**

- **Gold read:** the agent read the gold in all 12, and named it somewhere in the evidence chain in all 12.
- **Gold as divergence:** the agent described the gold as producing or causing the wrong value in **9 of 12**, yet ranked
  another method first.
- **Primary modes:**
  - ENTRY_POINT_RANKING: 5;
  - DECOY_DOC_CONTRADICTION: 3;
  - CONVENTION_ATTRIBUTION: 2;
  - CALLER_ARGUMENT_BLAME: 1;
  - MASK_PLACEMENT_ATTRIBUTION: 1.
- **Secondary modes:** SINK_BLAME 4, ALTERNATIVE_REPAIR_SITE 3, CONVENTION_ATTRIBUTION 1, CALLER_ARGUMENT_BLAME 1, none 3.
- **Defensible:** yes 3 (all DEPTH-01), no 9.

**Reliability:**

- The two blind lenses agreed on primary mode and defensibility for **12/12** runs, and on secondary mode for 11/12: for
  LB-COMPRESS-07-ADAPTER run 1 the argument lens gave none, and the final label took the process lens's
  ALTERNATIVE_REPAIR_SITE without adjudication. Both lenses were the same model (claude-opus-5-5), and four of the five
  primary categories used reuse the coordinator's category names, so this shows consistency between lenses rather than
  independent inter-rater reliability.
- Their primary mode matches the coordinator's earlier label in **10/12** runs. The two differences are:
  - LB-CHART-01-ADAPTER run 1: caller-argument versus convention;
  - ADV-DEFINER-01: convention versus local oddness.
- The coordinator had judged more answers defensible: 5 "yes" and 5 "partly". The blind labellers called only the DEPTH-01
  answers defensible. The reports present both judgements (PROMISING_MECHANISMS.md).

### What the modes mean

1. **Entry-point ranking (5 runs).** The most frequent primary mode among the S1 misses (5/12, on 3 instances). This study
   ran only GPT-5.6, so it cannot show that the pattern is model-specific; in earlier frozen, non-randomised data,
   entry-point labels were more common for GPT-5.6 (7 of 26 misses) than for Claude (Sonnet 1, Opus 0). The agent locates
   the deep divergence correctly,
   often naming the gold, but ranks the public method the failing test calls first. For example:
   - "the direct API method and its immediate delegate are the strongest candidates";
   - "the test directly exposes PiePlot.getArcBounds()" (CF-V1 run 2; the same evidence step's separate inference reads
     "The exploded section is displaced in the opposite horizontal direction, making getArcBounds the primary localization
     target").

   The labellers gave 3 of these 5 runs the secondary mode ALTERNATIVE_REPAIR_SITE: COMPRESS-07 runs 1 (one lens only)
   and 3, and MASK-01 run 1. Only COMPRESS-07 offers a concrete alternative, its correct sibling `TarBuffer.digest`, which is
   present in all three of its runs. The process lens notes that the MASK-01 reroute (restoring the inline loop) is not
   supported by documentation, and the CF-V1 run has no secondary mode. An exploratory Phase 4 revision (X4) removed the sibling and its test, and the parent's 0/3 became **3/3**
   (P4-COMPRESS07-r1). With 3 runs per arm (two-sided Fisher p = 0.10), no re-run of the unchanged parent and a parent
   chosen for its 0/3, this is consistent with the sibling explanation but does not establish it. The held-out HA instances
   offer no alternative repair site, and they scored 14/14 on answered runs. HA's chains are specified as 3 or 4 classes,
   while HELDOUT_CONFIRMATION_PLAN.md attributes the CF-V1 and MASK-01 misses to a 5-hop chain, so HA does not separate the
   sibling explanation from chain length.
2. **Doc-contradiction blame (3 runs).** All three DEPTH-01 runs blamed a decoy whose own javadoc promises a mask that its
   code lacks. The answer is defensible, so the effect measures gold ambiguity. The S1 result carries the X3 caveat: the
   variant also fails `ConversionTest::testIntArrayToLong`, so an agent that ran the full suite saw two failing tests. In an exploratory Phase 4 revision that fixed the
   decoy's doc and pinned the gold's contract (two javadoc edits, same failure set as the parent), the parent's 0/3 became
   **3/3** (P4-DEPTH-01-r1). With 3 runs per arm (two-sided Fisher p = 0.10) and both edits made at once, this does not
   show which change mattered.
3. **Convention or caller attribution (3 runs) and mask placement (1 run).** These happen where a direction, offset or field
   convention spans methods. No such misses occurred where the convention was stated explicitly, but the
   controls do not isolate where the statement sits. CF-V3 differs from DEFINER-01 only by an explicit javadoc on the
   definer `drift` (a decoy), not on the gold `Plot.nudge`. OCFLB-CHART-01-ADAPTER, the explicit-contract twin of
   LB-CHART-01-ADAPTER, also changes operand order, names and the form of the gold fault, and drops the second caller. Both
   were 3/3 in S1. Held-out HC, where both the definer and the gold state the convention, was 15/15. No S1 or Phase 4
   control targets mask placement.

## Results: held-out (44 valid runs)

There is one wrong run. **HO-HA-COMPRESS-01 run-003** made no submission:

- the agent's first and only model call returned about 5.5 s after the timer started and issued three commands (a grep,
  a `defects4j test` run and a find);
- their results were recorded only at about 304.9 s, 4.9 s after the 300 s budget had run out (that step took about 299 s;
  the first step containing `defects4j test` took at most about 6 s in every other run), so the agent stopped with
  `TimeExceeded` before making a second model call (api_calls = 1);
- the frozen classifier counts it as a behavioural `timeout` (NO_ANSWER), because stall rule 2 needs more than 60 s of
  budget left after the last tool result, and the final gap was -4.9 s.

The run started at 12:16Z, shortly after a provider stall (run-002, 12:05Z) and a 574 s health probe (12:15Z), and after
three health probes that passed (X11). Its own model call returned promptly and the time was lost while its commands were
executing, so the record does not show that the provider caused the no-answer.

- **Mode:** NO_ANSWER_TIMEOUT, assigned in this report (the run was not put through the labelling workflow). No ranking
  was produced, and it is not a misattribution.
- **Answered runs:** none is wrong (43/43 correct).

## Results: S2 (36 runs) and Phase 4 (6 runs)

There are no wrong runs in either block.

## Context from frozen earlier experiments (MECHANISM_MINING.md)

The 26 answered GPT-5.6 misses in earlier frozen data show the same broad pattern of misranking after reading the gold,
though their most common label, local oddness, is not the blind primary label of any S1 miss (the coordinator gave it to
one, DEFINER-01):

- every miss ranked a declared competitor first;
- 25 of 26 had read the gold in full;
- their mining labels (Phase 7 taxonomy; MECHANISM_MINING.md does not say who assigned them) were LOCAL_ODDNESS_BIAS 12,
  ENTRY_POINT_BIAS 7, ATTRIBUTION_FAILURE 6 and EVIDENCE_INTEGRATION_FAILURE 1.

The strongest predictor there was visual asymmetry: a quiet gold beside a locally odd but correct competitor. Its clearest
frozen-data breaks (CHART-PIE-TREATMENT-03 and the CLOSURE-1 variants, each 0/5) were labelled local oddness: a correct
competitor that reads as backwards or permissive. Two weaker ones (CLOSURE-12-OWN 1/5, CLOSURE-131-OWN 2/6) were ownership
splits.

## Conclusion

GPT-5.6's wrong answers in this study are never failures to find the gold: it read the gold in every wrong answered run.
They are ranking and attribution decisions, made in two settings:

1. The repository offers a competing location with a documented argument: a doc-contradicting decoy (DEPTH-01), a sibling
   that permits an alternative repair (COMPRESS-07), or a convention not fixed at the gold (LB-CHART-01-ADAPTER). Only the
   3 DEPTH-01 answers are defensible on both judgements; the blind labellers judged the other 9 S1 answers not defensible,
   because the code, tests or a second caller settle the owner.
2. The agent ranks by proximity to the test even after naming the deep cause (the 5 entry-point runs).

Not every miss fits these settings: DEFINER-01 and MASK-01 run 3 blamed a non-gold hop on instances whose owner the blind
labellers found settled by a pinning test or a second caller.

No answered misses occurred on the two Phase 4 revisions (6/6), the explicit-contract controls in S1 or the nine held-out
instances (43/43 answered). This is consistent with the account above but does not establish it: every freshly built
instance in this study was at ceiling whatever its mechanism (S2 36/36, held-out 43/43 answered), P4-COMPRESS07-r1 removed a
sibling rather than changing documentation, the Phase 4 revisions are exploratory diagnostics (X4), and 0/43 still allows an
answered-error rate of up to about 0.08 (Wilson 95% upper bound). The result is for GPT-5.6 at medium effort only.
