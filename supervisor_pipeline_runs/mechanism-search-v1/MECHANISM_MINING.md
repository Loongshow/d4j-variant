# Retrospective mechanism mining (read-only, all completed experiments)

**Data.** 954 runs from 14 families across GPT-5.6, Claude Sonnet, Opus and Haiku (`MECHANISM_RUN_DATA.csv`, one row per run).
- *Instance annotations:* 200 variants were annotated by independent read-only agents (`mining/annotations/`). The fields cover
  bug type, local cues at the gold and competitors, ownership, external evidence, depth and mechanism tags.
- *Failure-mode labels:* all 263 non-correct runs were labelled with the Phase 7 taxonomy (`mining/classifications/`).
- *Trajectory features:* computed deterministically by `scripts/mx_mine.py` using the frozen display-matching helpers.
- *Analysis set:* below, it is valid behavioural runs only. Provider failures are excluded by the uniform rule; timeouts and
  no-answers are counted.

**Caveats.**
- Features are instance-level and co-occur, and each family had one annotator.
- Claude runs in adversarial-break, OCFLB and Level B could not execute tests (protocol v2) except in their validity blocks.
- These are associations across non-randomised instances. They are not causal estimates.

## 1. Where the misses are

| Model group | Valid runs | Instances | Acc@1 |
|---|---|---|---|
| GPT-5.6 | 460 | 149 | 0.92 |
| Claude Sonnet | 225 | 44 | 0.64 |
| Claude Opus | 139 | 31 | 0.77 |
| Claude Haiku | 24 | 9 | (mostly budget exhaustion) |

GPT-5.6's non-correct runs number 111. Most are not misses:

| Outcome | Runs |
|---|---|
| Provider failures (mainly the canonical benchmark) | 40 |
| Timeouts | 40 |
| Answered wrong | 26 |

**In all 26 answered GPT-5.6 misses, the agent ranked a declared competitor first. In 25 it had displayed and fully read the
gold.** These are attribution failures after discovery, not search failures. Their labels are LOCAL_ODDNESS_BIAS (12),
ENTRY_POINT_BIAS (7), ATTRIBUTION_FAILURE (6) and EVIDENCE_INTEGRATION_FAILURE (1).

Every Claude miss also exposed and fully read the gold (Sonnet 49/49, Opus 32/32). For Claude the dominant label is
CONVENTION_PRIOR: the model assumes an unverified sign or unit convention.

## 2. Predictors of a wrong rank-1

The table gives Acc@1 when the feature is present against absent, among valid runs; n is runs and inst is instances.

| Instance feature | GPT-5.6 | Claude Sonnet | Claude Opus |
|---|---|---|---|
| **Gold quiet AND competitor locally odd** | **0.38** (n 26, inst 7) | **0.00** (57, 8) | **0.18** (38, 7) |
| Gold quiet AND competitor quiet | 0.95 (92, 14) | 0.84 (25, 5) | 1.00 (22, 7) |
| Gold locally odd (self-incriminating) | 0.96 (342, 128) | 0.85 (143, 31) | 0.99 (79, 17) |
| Competitor locally odd, present vs absent | 0.74 vs 0.97 | 0.28 vs 0.91 | 0.48 vs 1.00 |
| Semantic convention ambiguity | 0.80 vs 0.97 | 0.40 vs 0.86 | 0.47 vs 0.99 |
| Ownership split | 0.83 vs 0.97 | 0.60 vs 0.92 | 0.71 vs 1.00 |
| Bug by omission | 0.85 vs 0.95 | 0.23 vs 0.81 | 0.50 vs 0.86 |
| Missing negation | (1 instance) | 0.00 vs 0.77 | 0.22 vs 0.85 |
| Wrong constant | 1.00 vs 0.91 | 0.75 vs 0.60 | 1.00 vs 0.73 |
| Second caller present | 0.95 vs 0.91 | 0.73 vs 0.42 | 0.84 vs 0.66 |

**Lowest-accuracy mechanism tags for GPT-5.6:**
- M6, correct method more suspicious than the gold: 0.36;
- M18, non-idiomatic correct code: 0.42;
- M20, evidence competition: 0.56;
- M1, local oddness: 0.57.

By contrast, M0 (displacement only) is 0.97, M17 (type semantics) 0.93 and M10 (entry point) 0.93.

**The strongest and most consistent predictor across all three models is visual asymmetry: a correct competitor contains locally
odd code while the gold is locally plausible.** A self-incriminating gold restores near-ceiling accuracy in every model. This
matches the differential pilot, where only a visible operator at the gold restored Sonnet, and the OCFLB finding that explicit,
locally decidable contracts protect.

Omission and missing-negation faults hurt Claude strongly. GPT-5.6 is hurt less, but still measurably.

## 3. The GPT-5.6 instances that already break (frozen data, not tuned on GPT)

**Clear attribution failures:**
- **CHART-PIE-TREATMENT-03** (displacement family): 0/5, all LOCAL_ODDNESS_BIAS. The definer `PlotUtilities.drift` computes
  `point1 − point2`, which reads as backwards, so the agents blamed it instead of the sign-split adapter.
- **CLOSURE-1 L10, L50 and NAME variants** (canonical): 0/5 overall, LOCAL_ODDNESS_BIAS. A correct competitor contains the
  original permissive rule (`modifyAllCallSites || !hasFollowing`), which looks like it allows the observed behaviour. The gold is
  a quietly widened guard.
- **CLOSURE-12-OWN** (1/5) and **CLOSURE-131-OWN** (2/6): ownership splits with an omission gold and a competitor that visibly
  lacks a check.

**Partial:** MATH-NORM-TREATMENT-01 (4/7): the competitor carries the original MINPACK arithmetic, which looks unusual but is
correct.

**Not genuine misses:** CODEC-14, LANG-34 and MOCKITO-28 score 0 only through infrastructure timeouts.

## 4. Implications for screening

1. **Prioritise M6 and M1, local oddness and visual asymmetry, with an omission or quiet gold.** This is the only family with
   GPT-5.6 Acc@1 below 0.5 in frozen data.
2. **M3 and M20 (definer/adapter, evidence competition) matter mainly through the same asymmetry.** The definer looks backwards
   while the adapter is quiet. Screen them as carriers of M6.
3. **M0 (displacement), M17, M10 and M16 alone are weak for GPT-5.6.** Screen them only as cheap checks or combinations.
4. **GPT-5.6 runs tests and reads full bodies** (25/26 misses read the gold fully). Mechanisms must survive inspection, so the
   decisive evidence must be global, not local.
