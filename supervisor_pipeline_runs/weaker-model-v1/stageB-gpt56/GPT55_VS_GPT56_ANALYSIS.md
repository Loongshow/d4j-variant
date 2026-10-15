# Stage B: gpt-5.5 against GPT-5.6

The same 12 instances, prompt, budgets, run order and scoring were run on both models. gpt-5.5 ran on 2026-10-14 (server w55) and
GPT-5.6 on 2026-10-15 (server w56). Each model has 60 valid runs, 15 per cell.

Sources:
- `GPT55_VS_GPT56_STAGE_B.csv`, `GPT55_VS_GPT56_PROCESS.csv` and `model_compare.json`, from `../scripts/stageB_model_compare.py`;
- `process_extra.json`, from `../scripts/stageB_process_extra.py`;
- `cross_model_labels.json`, from `../scripts/stageB_label_compare.py`;
- `lie_scan.json`, from `../scripts/stageB_lie_scan.py`.

Intervals are Wilson 95%, and p values are two-sided Fisher exact tests.

This comparison is descriptive. Two models are not enough to support a claim that one capability causes these differences. The
models also differ in serving speed, command habits and price as well as in whatever capability separates them.

## By cell

| Cell | gpt-5.5 | GPT-5.6 | Difference (GPT-5.6 - gpt-5.5) | p |
|---|---|---|---|---|
| C00 1-hop, plain | 15/15 (0.80 to 1.00) | 15/15 (0.80 to 1.00) | 0.00 | 1.0 |
| C01 1-hop, odd sibling | 14/15 (0.70 to 0.99) | 15/15 (0.80 to 1.00) | +0.07 | 1.0 |
| C10 5-hop + lie, plain hop | 3/15 (0.07 to 0.45) | 15/15 (0.80 to 1.00) | +0.80 | 1.1e-5 |
| C11 5-hop + lie, odd hop | 4/15 (0.11 to 0.52) | 11/15 (0.48 to 0.89) | +0.47 | 0.027 |
| 1-hop pooled | 29/30 (0.83 to 0.99) | 30/30 (0.89 to 1.00) | +0.03 | 1.0 |
| 5-hop + lie pooled | 7/30 (0.12 to 0.41) | 26/30 (0.70 to 0.95) | +0.63 | 1.3e-6 |
| odd pooled (C01 + C11) | 18/30 | 26/30 | +0.27 | 0.039 |
| plain pooled (C00 + C10) | 18/30 | 30/30 | +0.40 | 1.2e-4 |
| all | 36/60 (0.47 to 0.71) | 56/60 (0.84 to 0.97) | +0.33 | 2.2e-5 |

## By project

| Project | Cell | gpt-5.5 | GPT-5.6 | p |
|---|---|---|---|---|
| Lang (B1 `indexOfAnyBut`, gold `isAnyOf`) | C00 / C01 | 5/5, 4/5 | 5/5, 5/5 | 1.0, 1.0 |
| | C10 / C11 | 1/5, 0/5 | 5/5, 3/5 | 0.048, 0.17 |
| | 5-hop + lie pooled | 1/10 | 8/10 | 0.0055 |
| Chart (B3 `findStackedRangeBounds`, gold `signedSums`) | C00 / C01 | 5/5, 5/5 | 5/5, 5/5 | 1.0, 1.0 |
| | C10 / C11 | 2/5, 4/5 | 5/5, 3/5 | 0.17, 1.0 |
| | 5-hop + lie pooled | 6/10 | 8/10 | 0.63 |
| Math (B4 `StatUtils.mode`, gold `tabulate`) | C00 / C01 | 5/5, 5/5 | 5/5, 5/5 | 1.0, 1.0 |
| | C10 / C11 | 0/5, 0/5 | 5/5, 5/5 | 0.0079, 0.0079 |
| | 5-hop + lie pooled | 0/10 | 10/10 | 1.1e-5 |

**Direction by project.** GPT-5.6 is at or above gpt-5.5 in 11 of the 12 project-by-cell entries. The exception is Chart C11
(3/5 against 4/5), which is within noise.

**Where the recovery is largest.** It is largest where gpt-5.5 had the most room to recover, Math (0/10 to 10/10) and Lang (1/10
to 8/10), and small on Chart, where gpt-5.5 had already kept 6/10.

## Model × cell pattern

| Quantity | gpt-5.5 | GPT-5.6 | Change |
|---|---|---|---|
| chain effect (5-hop + lie minus 1-hop, pooled) | -0.73 (p = 3.4e-9) | -0.13 (p = 0.11) | +0.60 |
| odd-hop effect (odd minus plain, pooled) | 0.00 (p = 1.0) | -0.13 (p = 0.11) | -0.13 |
| interaction (C11 - C01) - (C10 - C00) | +0.13 | -0.27 | -0.40 |
| C10 against C11 (plain against odd hop inside the chain) | 3/15 against 4/15 | 15/15 against 11/15 (p = 0.10) | |

**The chain-and-lie bundle.** It costs gpt-5.5 about three quarters of its rank-1 answers and costs GPT-5.6 none in the plain chain
cell.

**What is left on GPT-5.6.** Its small residual sits where the chain and the odd-looking correct hop meet, in Lang and Chart. On
gpt-5.5 that odd hop made no difference.

**A caution on the interaction.** It is not established. Four misses in fifteen are compatible with zero (S2 p = 0.10), and the
block was not powered for an interaction. The "Change" column above is descriptive and has no test. With C00, C01 and C10 all at
15/15, every GPT-5.6 contrast rests on the same four misses. In none of them was the odd hop ranked first or labelled
LOCAL_ODDNESS_BIAS. So if the odd hop matters for GPT-5.6, it is not by drawing the blame.

**Stage A does not bear on the model difference.** GPT-5.6 scored 0/5 on the Stage A instance CHART-PIE-TREATMENT-03, a chain with
a correct hop whose code reads backwards. That instance cannot speak to the difference between the models, for three reasons:

- gpt-5.5 also scored 0/5 on it, yet showed no odd-hop effect in Stage B.
- The instance bundles an ownership split, and it was selected because GPT-5.6 failed it.
- The GPT-5.6 reference is a September run made before the frozen protocol (`../MECHANISM_BY_MODEL.md`).

## Process: effort and how it is spent

| Measure (median per run) | gpt-5.5 1-hop | gpt-5.5 5-hop + lie | GPT-5.6 1-hop | GPT-5.6 5-hop + lie |
|---|---|---|---|---|
| tool calls | 12 | 19 | 14.5 | 29.5 |
| searches | 8.5 | 15.5 | 11.5 | 25 |
| step of the first gold display | 3 | 11 | 4 | 23 |
| seconds to the first gold display | 9.6 | 30.5 | 9.9 | 40.5 |
| calls after the first gold display | 7.5 | 7.5 | 10 | 6 |
| reasoning tokens | 1,432 | 1,898 | 916 | 1,098 |
| wall time (s) | 54.9 | 82.0 | 41.6 | 73.7 |
| cost ($) | 0.286 | 0.429 | 0.149 | 0.280 |
| gold displayed and read in full | 30/30 | 27/30 | 30/30 | 30/30 |
| gold exposed but misranked | 1 | 20 | 0 | 4 |
| facade ranked first | 1 | 22 | 0 | 4 |
| independent probe executed | 8/30 | 5/30 | 7/30 | 7/30 |
| failure values displayed | 29/30 | 24/30 | 24/30 | 26/30 |

**How the effort differs.**

- **GPT-5.6** explores longer in the chain cells before reaching the gold, with twice as many calls before the first gold display.
  This is more search, not more reading: it reads fewer files than gpt-5.5 (15 against 19.5) and about the same number of lines
  (1,381 against 1,332). It then commits with fewer calls after the gold (6 against 7.5).
- **gpt-5.5** reaches the gold sooner and makes the same number of post-gold calls as in its 1-hop cells. It then ranks the
  facade first in 22 of 30 runs.
- **Reasoning tokens** are lower for GPT-5.6 in every arm, which is a model-level offset rather than a sign of less deliberation.
  Token counts from two models are not a common scale. Against its own 1-hop cells, GPT-5.6's reasoning rises by about a fifth in
  the chain cells.

**The causal question stays open.** It may be that the extra search is what lets GPT-5.6 keep the fault location apart from the
behavioural entry point, but it cannot be shown with two models. Within GPT-5.6, the fair comparison for the four wrong runs is
the six correct C11 runs on the same two bugs. Against those, the wrong runs made 34.5 tool calls against 30.5, with the first
gold display at step 29 against 26, and 5 post-gold calls against 2.5 (medians). The ranges overlap: two correct runs made 37 calls.
With 4 runs against 6, this is description only.

**Cost.** GPT-5.6 was cheaper than gpt-5.5 on every cell: $12.92 against $21.91 for the 60 valid runs.

## Failure modes

Details are in `CROSS_MODEL_FAILURE_MODES.md`. In summary:

- **gpt-5.5, 24 misses:**
  - ENTRY_POINT_BIAS 17, CONVENTION_PRIOR 6 (all on Math, where only the facade's javadoc states the NaN convention),
    ATTRIBUTION_FAILURE 1;
  - the gold is named in the evidence chain in 24 of 24, and the divergence is placed at the gold in 22.
- **GPT-5.6, 4 misses:**
  - ENTRY_POINT_BIAS 4;
  - the gold is named in 4 of 4, and the divergence is placed at the gold in 4.
- **CONVENTION_PRIOR has not reappeared.** GPT-5.6 made no Math miss.
- **The facade lie is never repeated** in any evidence chain from either model (phrase scan of all 60 chain-cell submissions).

## Decision

**The preregistered rule.** It classifies GPT-5.6 as ATTENUATED: 26/30 in the chain cells, against an ELIMINATED threshold of
27/30. ATTENUATED maps to the brief's case 2 (partial recovery), whose decision is that "the decomposition is still recommended".
It is proposed, not launched.

**Added interpretation (not preregistered).** The rule recommends the decomposition but does not say on which model.

**What the design varies.** As described after the gpt-5.5 block (`../SUPERVISOR_UPDATE_STAGE_B.md`: 60 runs at about $0.43 each),
it keeps every cell at 5 hops and crosses two factors:
- hops placed inside the facade's own class, against hops dispersed across five hosts;
- the lie present, against the lie absent.

The preregistration's shorthand also lists "hop distance", which the described design does not vary.

**What it would show on each model.**
- **On GPT-5.6.** Only one of the four cells (dispersed hops, lie present) is the C10 condition, which scored 15/15 on GPT-5.6. The
  other three are untested there. I expect them near ceiling, on the assumption that removing a component does not make the task
  harder; the in-class arm also changes where the hops sit relative to the facade.
- **On gpt-5.5.** The decomposition would show which component drives gpt-5.5's -0.73 drop. It bears on the gap with GPT-5.6 only if
  GPT-5.6 is at ceiling in every cell, which is expected, not measured.

**My suggestion.** This goes beyond the rule.
- **If the decomposition is run, run it on gpt-5.5.** That is where there is an effect to take apart. It is about $26.
- **Running it on GPT-5.6 has a low expected yield**, but that yield is unmeasured. The one GPT-5.6 residual, the chain-by-odd-hop
  cell, would need a different and smaller question. That question is not designed here, per the brief.
- **The choice of model, and whether to run it at all, is the supervisor's.** The ATTENUATED class rests on a single run.
