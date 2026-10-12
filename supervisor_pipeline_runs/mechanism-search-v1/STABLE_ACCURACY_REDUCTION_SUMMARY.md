# Stable accuracy reduction: final summary (GPT-5.6, mechanism-search-v1)

## Answer

**No controlled, interpretable mechanism tested here reliably reduces GPT-5.6's method-level fault-localization accuracy
when the gold is uniquely defensible.**

- 17 mechanism families were screened. Three recipes, built from the failure modes of the strongest families, were frozen into nine
  fresh, independently built and audited held-out instances.
- All three are **NOT_SUPPORTED**. Held-out Acc@1 is 0.93 for HA, 1.00 for HB and 1.00 for HC. Overall, 43 of 44 valid runs
  ranked the gold first, and every answered run did.
- The preregistered global stop rule is met under **condition B**: at least 12 families screened, held-out confirmation done
  for three recipes built from the 3 strongest screening families (M19, M5, M3), none at or below 0.60. HB tests M19 and HC
  tests M3 directly. M5 has no recipe of its own: under the frozen plan its misses' failure modes went into HA (entry-point
  ranking, labelled M10, a family that screened NULL) and HB, and no held-out instance carries an M5 tag. Condition B holds
  on the plan's mapping of failure modes to recipes. The study therefore concludes that **GPT-5.6 is robust under the tested
  manipulations**.

**Where wrong rankings did appear,** all in screening (12 S1 misses) and all in instances tuned against Claude in earlier work,
most fit one of two patterns:

- **a second defensible fault location:** the blind labellers judged only the 3 DEPTH-01 answers defensible, where the decoy's
  own documentation contradicts its code. The coordinator's validity review also flagged a correct sibling that permits an
  alternative repair (COMPRESS-07) and an under-specified convention (CHART-01-ADAPTER), but the blind labellers judged those
  answers not defensible;
- **proximity ranking** of the method the test calls (5 runs), which appeared only when a correct sibling offered an
  alternative repair (COMPRESS-07) or the helper chain was long (MASK-01, CF-V1).

Not every miss fits these patterns. In ADV-MASK-01 run 3 the agent blamed a decoy although both judgements found the gold
better supported, and on the blind reading the CHART-01-ADAPTER and DEFINER-01 misses went against conventions pinned by tests
or documentation in the repository.

In exploratory Phase 4 revisions (n = 3 each), the two 0/3 instances became 3/3: COMPRESS-07 after the correct sibling and its
test were removed, and DEPTH-01 after two javadoc edits (the decoy's contradiction removed and the gold's contract pinned), so
which DEPTH-01 edit mattered is not identified. GPT-5.6 found and read the gold in every wrong answered run. Its errors were
ranking and attribution decisions, never search failures.

## Ranking of mechanisms

Ordered by strength of evidence for a reduction.

| Rank | Mechanism | Best screening evidence | Held-out | Label |
|---|---|---|---|---|
| 1 | **HA, entry-point ranking** (M10 as a failure mode; carrier M3) | LB-COMPRESS-07-ADAPTER 0/3, ENTRY_POINT ×3. It became 3/3 once the correct sibling was removed (P4). | 14/15 = 0.933 (Wilson 95%: 0.70 to 0.99); the only miss is a no-answer timeout | **NOT_SUPPORTED** |
| 2 | **HB, sink blame** (M19 + M6 + M2) | ADV-DEPTH-01 0/3, all answers citing the decoy's own doc contradiction. It became 3/3 once the doc was fixed and the contracts pinned (P4). | 14/14 = 1.000 (0.78 to 1.00) | **NOT_SUPPORTED** |
| 3 | **HC, convention attribution** (M3) | LB-CHART-01-ADAPTER 1/3; ADV-DEFINER-01 2/3. The explicit-contract twins scored 3/3. | 15/15 = 1.000 (0.80 to 1.00) | **NOT_SUPPORTED** |
| 4 | M5, distant decisive evidence | ADV-MASK-01 1/3; CF-V1 2/3 | no recipe of its own; its misses' failure modes were carried into HA and HB (above), whose instances carry no M5 tag | screening effect not confirmed (not held-out tested as a mechanism) |
| 5 | M1, M2, M7, M8, M9, M10 (as search), M11, M12, M13, M14, M15, M16, M17, M20 | all NULL (3/3 per instance; 16 instances, 48 runs across S1 and S2; M3 and the controls are counted elsewhere) | none | NULL in screening (exploratory; 1 or 2 instances per family, 3 runs each) |
| 6 | M0, structural displacement | frozen data only: tag-level Acc@1 0.97 (168 runs, 67 instances); displacement families 0.90 to 1.00 on valid behavioural runs | none | no reduction in frozen data (not run here) |
| — | M4, multiple plausible owners | the only dedicated instance (NEW-R4-M4) was INVALID: the harness rejects its gold. M4 is a secondary tag on two valid S1 instances (ADV-OWNER-01, ADV-REGISTRY-01), both 3/3 | none | UNTESTED |
| — | M18, non-idiomatic correct code | no instance in this study carries the tag (tag-level frozen Acc@1 0.42, from 5 earlier instances) | none | UNTESTED |

**No mechanism is SUPPORTED or PARTIALLY_SUPPORTED.** PARTIALLY_SUPPORTED would need pooled held-out Acc@1 ≤ 0.80, or one
held-out instance at Acc@1 ≤ 0.60 (AMENDMENTS X8, fixed before any held-out run). Phase 6 combinations were **not run**,
because the brief makes them conditional on moderate effects and none occurred. Phase 8 cross-model runs were **not run**,
because they are conditional on a STABLE result, and Anthropic was excluded by instruction.

## Evidence chain

1. **Mining** (MECHANISM_MINING.md): 954 earlier runs. GPT-5.6 misses concentrated where a correct competitor looked locally
   odd beside a quiet gold: Acc@1 0.38 over 26 runs and 7 instances.
2. **Screening** (MECHANISM_SCREENING_REPORT.md): 90 valid runs over 30 valid instances.
   - S1, the re-hosted adversarial instances, had Acc@1 0.78 (42/54), with 4 PROMISING and 2 WEAK instances.
   - S2, the 12 new recipe prototypes, had Acc@1 1.00 (36/36).
3. **Phase 4 diagnostics** (PROMISING_MECHANISMS.md): both 0/3 effects vanished, 3/3 each (exploratory, n = 3).
   COMPRESS-07 had one repair (the correct sibling and its test removed); DEPTH-01 had two javadoc edits (the decoy's
   contradiction removed and the gold's contract pinned).
4. **Failure modes** (FAILURE_MODE_ANALYSIS.md): two blind labellers per wrong run, agreeing on 12/12.
   - Primary modes: ENTRY_POINT_RANKING 5, DECOY_DOC_CONTRADICTION 3, CONVENTION_ATTRIBUTION 2, CALLER_ARGUMENT_BLAME 1,
     MASK_PLACEMENT_ATTRIBUTION 1.
   - The gold was read in 12/12 and named as the divergence in 9/12.
5. **Held-out confirmation** (HELDOUT_CONFIRMATION_RESULTS.md): 44 valid runs, 43/43 answered runs correct. The single miss
   is a no-answer timeout. Its one model call returned within seconds, but that turn's tool results were recorded only after
   the 300 s budget had expired, and no second model call was made. It followed a provider stall and a slow health probe, but
   the run's own records place the delay in the tool step, not in a model call.

## Validity and integrity

- **Separation of tiers.** Exploratory discovery (S1 and S2), Phase 4 diagnostics and held-out confirmation were kept apart.
  - No tuned instance counts as confirmation.
  - The held-out recipes were frozen at 2026-10-10T04:01Z, before any Phase 4 result.
  - The held-out instances were built by builders who never saw model output, and audited by separate agents.
  - No instance was modified after an agent step. The two Phase 4 revisions are new derived instances, built after their
    parents' screening runs; the parents were left unchanged.
  - INSTANCE_PROVENANCE.csv records every instance's tier, kind, parent and revision.
- **Frozen protocol.** Every benchmark run and health probe went through the frozen protocol, with freeze verification before each gate and
  launch. One diagnostic replay call for the halt review (`scripts/replay_stall_gpt.py`) was made outside it.
  The plans are `smoke`, `S1`, `S2`, `S2_cont`, `P4`, `HO`, `HO_cont` and `HO_top`.
- **Leakage.** A contamination scanner ran on every run. One run was stopped by it and excluded (X2); its exposure was
  unrelated to the answer.
- **Deviations** are disclosed in AMENDMENTS.md, entries X1 to X11, with one exception: the Phase 7 failure-mode labels use a
  different label set from the one fixed in PREREGISTRATION.md, and no amendment records that change. The most important
  entries:
  - one invalid screening instance, from the harness's test-class rule (X1);
  - a re-hosted instance (RH-ADV-DEPTH-01) with one collateral test failure (X3);
  - two held-out instances revised before any agent saw them (X6, X10);
  - gate G14 added after a harness staging incompatibility (X10);
  - one held-out cell left unfilled after four provider stalls, which cannot change any verdict (X11).

## Limitations

- **Scope.** One model (GPT-5.6) at one reasoning effort (medium), with one scaffold (mini-swe-agent, 50 steps, 300 s), on
  single-fault synthetic variants of Defects4J `bug-1` fixed versions in five projects.
- **Sample size.** 3 valid runs per screening instance, and 5 per held-out instance except HO-HB-COMPRESS-01 (n = 4). The
  per-recipe Wilson intervals all exclude 0.60, but their lower bounds (0.70 for HA, 0.78 for HB, 0.80 for HC) leave moderate
  reductions possible, reaching the PARTIALLY_SUPPORTED threshold of 0.80; only the interval pooled over all three recipes
  (43/44) has a lower bound near 0.88. A 5/5 instance has a Wilson lower bound of 0.57, so a single instance at or below 0.60
  is not excluded either. The NOT_SUPPORTED labels are point-estimate classifications.
- **Validity-first design.** Mechanisms that work only through gold ambiguity were tested only in their valid form, by design.
  Such "reductions" measure an ambiguous benchmark rather than a localization failure. A study of graded ownership ambiguity
  would need its own metric. This study did not test graded ambiguity; it found only that the valid-form recipes produced no held-out reduction.
- **Construction bias.** Independent builders aimed for objectively solvable instances, and auditors required documentation
  that fixes the owner. Instances meeting both standards may be inherently easy for a model that reads documentation and
  tests. Every held-out instance had unique documented ownership, and auditors flagged several held-out golds as locally
  salient (a ceiling risk), so the study cannot attribute the ceiling to documented ownership rather than to gold salience.
  That unique documented ownership protects remains a hypothesis, supported only by the exploratory n = 3 revisions and the
  explicit-contract twins.
- **Frozen-data tag accuracies** are confounded by overlapping tags and by under-specified ownership in earlier instances.
- **Unrun follow-ups.** Claude models were not run, by instruction. Earlier frozen data suggest Claude may be more susceptible to
  the visual-asymmetry condition: Sonnet 0.00 (57 runs) and Opus 0.18 (38 runs) Acc@1 there, against GPT-5.6's 0.38 (26 runs).
  The comparison is not like-for-like: the Claude and GPT-5.6 runs share only one instance (CHART-PIE-TREATMENT-03, with
  Opus), and 31 of the 38 Opus runs did not execute tests. On 7 of Sonnet's 8 instances, re-hosted in S1 under this study's
  protocol, GPT-5.6 scored 15/21 (0.71). A cross-model test on these held-out instances would
  show whether GPT-5.6's robustness is model-specific. It is a natural next step only if the user authorises it.

## Cost (COST_LEDGER.csv)

**Total: USD 28.83 for the mechanism search**, including estimated health-probe costs.

| Block | Cost (USD) |
|---|---|
| Smoke | 0.16 |
| S1 | 11.92 |
| S2 and its continuation | 6.83 |
| P4 | 1.51 |
| Held-out blocks | 8.42 |

The stall-replay diagnostic, a few cents, is not in the ledger. The earlier cue-trust GPT-5.6 pilot cost USD 5.21 and is
accounted separately.
