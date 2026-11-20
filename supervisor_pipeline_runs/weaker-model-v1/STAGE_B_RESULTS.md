# Stage B results (weaker-model-v1), 2026-10-14 (block 1 B1+B3 40 runs; block 2 B4 20 runs)

Design and rules: STAGE_B_PREREGISTRATION.md (frozen into the block-1 plan by sha), STAGE_B_DESIGN.md, AMENDMENTS W11-W17.
Model gpt-5.5 under the frozen protocol (server w55, `reasoning_effort: medium`, 50 tool calls, 5 test runs, 300 s). Instances:
B1 Lang `StringUtils.indexOfAnyBut` (gold `isAnyOf`, surrogate-pair comparison omitted) and B3 Chart
`DatasetUtilities.findStackedRangeBounds` (gold `signedSums`, NaN admitted into the negative total); both CONFIRMED by independent
audit under the W13 single-owner rule (each with a recorded bypass, no competing repair). B2 Math (atanh) was withdrawn after
audit (W14) and replaced by B4 `StatUtils.mode` (gold `tabulate`, NaN skip omitted), CONFIRMED and run as block 2 (W15).

## Block 1: 40 runs, 8 cells (B1, B3), 5 runs per cell, all answered, none contaminated, no timeouts, $14.99 (B1 $7.09, B3 $7.90)

| Cell | n | Acc@1 | Wilson 95% | B1 Lang | B3 Chart | median tool calls | misses NA/SF/DWI/AF |
|---|---|---|---|---|---|---|---|
| C00 | 10 | 10/10 = 1.00 | 0.72-1.00 | 5:5 | 5:5 | 11.5 | 0/0/0/0 |
| C01 | 10 | 9/10 = 0.90 | 0.60-0.98 | 4:5 | 5:5 | 13.0 | 0/0/0/1 |
| C10 | 10 | 3/10 = 0.30 | 0.11-0.60 | 1:5 | 2:5 | 19.0 | 0/1/0/6 |
| C11 | 10 | 4/10 = 0.40 | 0.17-0.69 | 0:5 | 4:5 | 19.0 | 0/0/0/6 |

C00 = 1-hop plain; C01 = 1-hop with an odd-looking correct sibling; C10 = 5-hop recipe chain with the facade lie, plain hop 3;
C11 = the same chain with an odd-looking correct hop 3. NA/SF/DWI/AF = no answer / gold never displayed / displayed but not read
in full / read in full and ranked elsewhere (frozen definitions, `scripts/mx_metrics.py`).

**Main effects (pooled over the two bugs, n = 20 per level).**
- Chain: 5-hop 7/20 vs 1-hop 19/20, difference -0.60, Fisher two-sided p = 1.4e-4.
- Odd hop: odd 13/20 vs plain 13/20, difference +0.00, p = 1.0.
- Interaction (C11 - C01) - (C10 - C00) = +0.20 (within noise; Chart's C11 4/5 against C10 2/5, Lang's 0/5 against 1/5).

**Shape of the misses.** All 14 misses rank the gold second behind the facade, the method the test calls: `indexOfAnyBut` in
the ten B1 misses (C01 x1, C10 x4, C11 x5), `findStackedRangeBounds` in the four B3 misses (C10 x3, C11 x1). In 13 of 14 the gold's fault line was displayed and the gold read in full before the
submission (ATTRIBUTION after discovery); in one (B3-C10 run-002) the gold was never displayed (SEARCH_FAILURE). The chain cells
cost more search: median 19 tool calls against 11.5-13 in the 1-hop cells.

**Against the preregistered expectations** (STAGE_B_PREREGISTRATION.md, "Expectations stated before any run"): "C00 and C01 at or
near ceiling (>= 0.8)" held (10/10, 9/10). "C10 near ceiling unless the lie plus the 5-hop chain does work the 2-hop test did
not reveal (C10 <= 0.6 would say so)": C10 was 3/10, so the recipe chain with its lie does the work on its own. "C11 the lowest
cell" did not hold (4/10 against C10's 3/10): the odd hop added nothing on top of the chain, in either bug. "The result of
interest is the interaction": it is +0.2 and uninformative; the main effect of the chain is the finding of this block.

What the block does not separate: the chain arm bundles five hops across five host classes, the facade lie, and the gold moving
from the facade's own file into a 1500+-line host. Which of those carries the effect is the next question (STAGE_B_DESIGN.md
open question 1 covers the lie); the per-run blind labels (below) say what the agent did with each.

## Per-run outcomes, block 1

| Instance | Cell | runs: gold rank (rank-1 method when wrong) |
|---|---|---|
| SB-B1-C00 | C00 | 1, 1, 1, 1, 1 |
| SB-B1-C01 | C01 | 1, 1, 2 (indexOfAnyBut), 1, 1 |
| SB-B1-C10 | C10 | 2 (indexOfAnyBut), 2 (indexOfAnyBut), 2 (indexOfAnyBut), 1, 2 (indexOfAnyBut) |
| SB-B1-C11 | C11 | 2 (indexOfAnyBut), 2 (indexOfAnyBut), 2 (indexOfAnyBut), 2 (indexOfAnyBut), 2 (indexOfAnyBut) |
| SB-B3-C00 | C00 | 1, 1, 1, 1, 1 |
| SB-B3-C01 | C01 | 1, 1, 1, 1, 1 |
| SB-B3-C10 | C10 | 1, 2 (findStackedRangeBounds), 2 (findStackedRangeBounds), 1, 2 (findStackedRangeBounds) |
| SB-B3-C11 | C11 | 1, 1, 1, 1, 2 (findStackedRangeBounds) |

## Blind labels of the block-1 misses (two lenses per run, adjudicated)

Method as in Stage A (W9): one process-lens and one argument-lens labeller per miss, launched separately with only the brief
(`construction/stageB/LABEL_BRIEF.md`), the task file (gold, decoys, entry point, evidence, trigger), the safe trajectory view and
the variant patch; cell identity not given. Primary label agreed in 14 of 14 runs; defensibility or secondary split in 6 runs and
went to a third-lens adjudicator (`analysis/failure_modes/labels_block1_adjudicated.json`; rows marked * below).

**Result: ENTRY_POINT_BIAS is the primary label in 14 of 14 misses.** In every miss the agent named the gold in its final evidence
chain and its own narrative placed the first wrong value at the gold's fault line (14/14 on both counts), then ranked the facade
first (in the chain cells a null guard plus a one-line delegation; in the one 1-hop miss the facade holds the loop), justified as "the direct failing API", "the overload under test", "the primary
repair location". Final defensibility: 13 no, 1 partly (the one 1-hop miss, B1-C01 run 3, where the sibling
implementations hold the surrogate logic inline), 0 yes. Secondaries: LOCAL_ODDNESS_BIAS 2 (the agent cited the cross-package
delegation or the facade's delegation "looking suspicious next to neighbours"), EVIDENCE_INTEGRATION_FAILURE 1. No evidence chain cites the facade's inserted javadoc sentence (the lie); the labellers' rationales report it displayed and
unused in 9 of the 24 Stage B misses (one agent grepped for it), and the safe views show it in 14 of the 23 chain misses (the
others truncate the facade display), so "never cited" is established and "always displayed" is not. Several runs ran jshell differentials that isolated the char-array path as wrong and the CharSequence overload
as right, and ranked the facade first regardless.

Frozen-measure note (W16): CTV-4D1CCD/run-002 is coded SEARCH_FAILURE by the frozen `gold_exposed` (false), but the fault line
was displayed at call 8 in an `nl -ba | grep -n` window the matcher does not attribute; both labellers and the adjudicator read
it as displayed. The frozen value is kept and both readings are reported.

| Run | Cell | gold rank (rank 1) | primary | secondary | defensible | gold named / divergence at gold | frozen split |
|---|---|---|---|---|---|---|---|
| CTV-4D1CCD/run-002 | SB-B3-C10 | 2 (findStackedRangeBounds) | ENTRY_POINT_BIAS | - | no | yes / yes | SEARCH_FAILURE |
| CTV-4D1CCD/run-003 | SB-B3-C10 | 2 (findStackedRangeBounds) | ENTRY_POINT_BIAS | - | no* | yes / yes | ATTRIBUTION_FAILURE |
| CTV-4D1CCD/run-005 | SB-B3-C10 | 2 (findStackedRangeBounds) | ENTRY_POINT_BIAS | - | no | yes / yes | ATTRIBUTION_FAILURE |
| CTV-4DE6D2/run-001 | SB-B1-C10 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | EVIDENCE_INTEGRATION_FAILURE | no | yes / yes | ATTRIBUTION_FAILURE |
| CTV-4DE6D2/run-002 | SB-B1-C10 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | - | no* | yes / yes | ATTRIBUTION_FAILURE |
| CTV-4DE6D2/run-003 | SB-B1-C10 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | - | no | yes / yes | ATTRIBUTION_FAILURE |
| CTV-4DE6D2/run-005 | SB-B1-C10 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | - | no* | yes / yes | ATTRIBUTION_FAILURE |
| CTV-5818E6/run-001 | SB-B1-C11 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | - | no* | yes / yes | ATTRIBUTION_FAILURE |
| CTV-5818E6/run-002 | SB-B1-C11 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | - | no | yes / yes | ATTRIBUTION_FAILURE |
| CTV-5818E6/run-003 | SB-B1-C11 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | LOCAL_ODDNESS_BIAS | no | yes / yes | ATTRIBUTION_FAILURE |
| CTV-5818E6/run-004 | SB-B1-C11 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | - | no | yes / yes | ATTRIBUTION_FAILURE |
| CTV-5818E6/run-005 | SB-B1-C11 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | - | no* | yes / yes | ATTRIBUTION_FAILURE |
| CTV-73BEA3/run-003 | SB-B1-C01 | 2 (indexOfAnyBut) | ENTRY_POINT_BIAS | - | partly | yes / yes | ATTRIBUTION_FAILURE |
| CTV-E94DC6/run-005 | SB-B3-C11 | 2 (findStackedRangeBounds) | ENTRY_POINT_BIAS | LOCAL_ODDNESS_BIAS | no* | yes / yes | ATTRIBUTION_FAILURE |

## Block 2 (B4 Math, 20 runs, 2026-10-14 11:32-11:59Z, all answered, none contaminated, $6.93) and the pooled result

Block 2 ran B4 (`StatUtils.mode`, gold `tabulate`; W15) under the same server, freeze rules and driver (plan
`plans/B_stageB_gpt55_block2.json`, freeze `54e31d96…`). Per cell: C00 5/5, C01 5/5, C10 0/5, C11 0/5. Every chain miss ranked the
facade `StatUtils.mode` first (nine runs; gold rank 3 in C10's five, 2 or 3 in C11's) except C11 run 3, which ranked the odd hop 3
`MathArrays::mostFrequent` first with the gold second. Two misses carry the frozen `gold_exposed = false` code (C10 run 2, C11 run 5);
the blind labellers were asked to say whether the fault line was displayed (see the labels section below and W16).

### All three bugs pooled (60 runs; n = 15 per cell)

| Cell | n | Acc@1 | Wilson 95% | B1 Lang | B4 Math | B3 Chart | median tool calls | misses NA/SF/DWI/AF |
|---|---|---|---|---|---|---|---|---|
| C00 | 15 | 15/15 = 1.00 | 0.80-1.00 | 5:5 | 5:5 | 5:5 | 11 | 0/0/0/0 |
| C01 | 15 | 14/15 = 0.93 | 0.70-0.99 | 4:5 | 5:5 | 5:5 | 13 | 0/0/0/1 |
| C10 | 15 | 3/15 = 0.20 | 0.07-0.45 | 1:5 | 0:5 | 2:5 | 19 | 0/2/0/10 |
| C11 | 15 | 4/15 = 0.27 | 0.11-0.52 | 0:5 | 0:5 | 4:5 | 19 | 0/1/0/10 |

**Main effects (n = 30 per level).**
- Chain: 5-hop 7/30 vs 1-hop 29/30, difference -0.73, Fisher two-sided p = 3.42e-09.
- Odd hop: odd 18/30 vs plain 18/30, difference +0.00, p = 1.0.
- Interaction (C11 - C01) - (C10 - C00) = +0.13.
- Per bug, 1-hop vs 5-hop: Lang 9/10 vs 1/10; Chart 10/10 vs 6/10; Math 10/10 vs 0/10. The direction is the same in all three
  projects; the size varies (Chart's chain cells kept 6/10).

**Reading.** On three fresh bugs with a uniquely owned, externally pinned gold, the supervisor's recipe (five hops across five
existing classes of 1500+ lines, inserted at anonymous points, with a procedural lie in the facade javadoc) moved gpt-5.5 from
29/30 to 7/30 at rank 1, while the odd-looking correct hop that CHART-PIE-03 had made us expect to matter did nothing here, with
or without the chain. The chain cells cost more search (median 19 tool calls against 11-13) but every run answered within the
50-call / 300 s budget, so the drop is not a budget artefact. What the agent does in the chain cells is a ranking choice, not a
search or reading failure: the labels below show it locating the fault and then ranking the method the test calls above it.


## Blind labels of the block-2 misses (B4; two lenses per run, adjudicated)

Same method (`labels_block2/`, `labels_block2_adjudicated.json`; * = adjudicated, 6 of 10: five primary splits and one
secondary/defensibility split, so the block-2 primaries are adjudicator-determined in half the runs, unlike block 1). B4 differs from B1/B3 in one respect that
the labels pick up: the NaN-ignoring convention is stated in the facade `StatUtils.mode`'s own javadoc and nowhere else on the path
(the gold's javadoc is silent). The adjudicator fixed the primary by the agent's own stated reason for rank 1: **CONVENTION_PRIOR**
(6 of 10) where the reason was the documented contract ("its javadoc promises NaN are ignored", "mode-specific
filtering belongs here"), **ENTRY_POINT_BIAS** (3) where it was the tested public method or the repair site, and
**ATTRIBUTION_FAILURE** (1, C11 run 3) where the odd hop 3 `mostFrequent` was ranked first "as the method that forms the returned
array" (by role, not by its odd form: LOCAL_ODDNESS_BIAS was considered and rejected). Defensibility is "partly" in 9 of 10 under the
rule the adjudicator wrote down (a rank-1 method whose own documentation states the violated obligation is partly defensible even
though its body holds no faulty statement; a pre-delegation filter at the documented facade is a fix a careful engineer could
choose), "no" for the odd-hop run. The divergence was located at the gold in 8 of 10; in the two others (C10 run 5, C11 run 5) the
agent had displayed the unguarded loop and run its own probes, hedged between the facade and "the helper that tabulates", and
ranked the chain top-down (EVIDENCE_INTEGRATION_FAILURE secondary). W16 applies to two B4 runs (C10 run 2, C11 run 5): the frozen
`gold_exposed = false` is a matcher limitation; the fault line was displayed at calls 9 and 8 (`labels_block2_final.json`,
`extra_checks`).

| Run | Cell | gold rank (rank 1) | primary | secondary | defensible | divergence at gold | frozen split |
|---|---|---|---|---|---|---|---|
| CTV-7C06F2/run-001 | SB-B4-C11 | 3 (mode) | ENTRY_POINT_BIAS | CONVENTION_PRIOR | partly | yes | ATTRIBUTION_FAILURE |
| CTV-7C06F2/run-002 | SB-B4-C11 | 3 (mode) | CONVENTION_PRIOR | ENTRY_POINT_BIAS | partly | yes | ATTRIBUTION_FAILURE |
| CTV-7C06F2/run-003 | SB-B4-C11 | 2 (mostFrequent) | ATTRIBUTION_FAILURE | CONVENTION_PRIOR | no* | yes | ATTRIBUTION_FAILURE |
| CTV-7C06F2/run-004 | SB-B4-C11 | 2 (mode) | CONVENTION_PRIOR | ENTRY_POINT_BIAS | partly* | yes | ATTRIBUTION_FAILURE |
| CTV-7C06F2/run-005 | SB-B4-C11 | 2 (mode) | ENTRY_POINT_BIAS | EVIDENCE_INTEGRATION_FAILURE | partly* | no | SEARCH_FAILURE |
| CTV-CCA96B/run-001 | SB-B4-C10 | 3 (mode) | CONVENTION_PRIOR | ENTRY_POINT_BIAS | partly* | yes | ATTRIBUTION_FAILURE |
| CTV-CCA96B/run-002 | SB-B4-C10 | 3 (mode) | CONVENTION_PRIOR | ENTRY_POINT_BIAS | partly | yes | SEARCH_FAILURE |
| CTV-CCA96B/run-003 | SB-B4-C10 | 3 (mode) | CONVENTION_PRIOR | ENTRY_POINT_BIAS | partly | yes | ATTRIBUTION_FAILURE |
| CTV-CCA96B/run-004 | SB-B4-C10 | 3 (mode) | CONVENTION_PRIOR | ENTRY_POINT_BIAS | partly* | yes | ATTRIBUTION_FAILURE |
| CTV-CCA96B/run-005 | SB-B4-C10 | 3 (mode) | ENTRY_POINT_BIAS | EVIDENCE_INTEGRATION_FAILURE | partly* | no | ATTRIBUTION_FAILURE |

## Stage B synthesis (60 runs, 24 misses)

- **Effect.** The recipe chain alone lowers gpt-5.5's Acc@1 from 29/30 to 7/30 (difference -0.73, Fisher p = 3.4e-9) on three fresh
  bugs in three projects; the odd-looking correct hop has no effect (18/30 vs 18/30); the interaction is +0.13. Pre-stated
  expectations: the ceiling for C00/C01 held; "C10 near ceiling" did not (3/15); "C11 the lowest cell" did not (4/15 vs 3/15).
- **Mechanism, by the blind labels.** Primary over all 24 misses: ENTRY_POINT_BIAS 17, CONVENTION_PRIOR 6,
  ATTRIBUTION_FAILURE 1; by the blind labels no SEARCH_FAILURE and no DISCOVERY_WITHOUT_INSPECTION (the frozen split records 3
  SEARCH_FAILURE codes that W16 traces to a display-matcher gap), and no NO_ANSWER. The gold was named in the
  final evidence chain in 24 of 24 and the agent's own narrative placed the first wrong value at the gold in 22 of 24. The chain
  cells cost 19 tool calls against 11-13, all within budget. In B1 and B3 (no method on the path states the violated step; B1's hop 3 javadoc mentions surrogate pairs without the
  second-unit comparison) the rank-1 justification is "the method the test calls"; in B4 (the facade states it) the justification becomes "the method whose
  documentation promises it". Both are the same move: once the fault sits five hops below the entry point in a foreign class, the
  agent ranks the entry point above the hop it has itself identified as violating the convention. In the 1-hop cells the same
  agent ranks the gold first 29 times in 30.
- **Defensibility.** 14 of 24 misses not defensible, 10 partly (one B1 1-hop miss; nine B4 facade-first misses, where the facade's
  javadoc is the convention's only statement), 0 yes.
- **Odd hop.** The CHART-PIE-03 ingredient did nothing here. In two block-1 misses LOCAL_ODDNESS_BIAS is a secondary (the
  cross-package delegation "looked unusual"), and the single odd-hop-first ranking in Stage B (B4 C11 run 3) was justified by
  role, not by the hop's odd form. With a uniquely owned gold, the odd hop neither attracts blame nor protects the gold.
- **What is still bundled.** The chain arm changes five things at once: hop count, cross-class dispersal, host size, anonymous
  placement, and the facade lie. The lie was displayed in every chain-cell miss and cited in none (one agent grepped for it and
  did not use it), so the labels give no sign that it carries the effect; separating hop count from dispersal/host size is the
  next 2x2.

## Limitations recorded before the runs
- Bypasses exist for all three bugs (B1: the CharSequence overload and re-implemented pair checks; B3: `findMinimumStackedRangeValue`;
  B4: zeroing the NaN count at the extraction hop or recomputing without `getMode`); recorded in the audits, not counted as
  owners under the W13 repair/bypass distinction. An agent ranking the facade first on that reasoning would be labelled ENTRY_POINT_BIAS.
- Two bugs in block 1 (B2 withdrawn); B4 runs as a separate block in time (W14/W15).
- The CHART-PIE-03-shaped manipulation (odd hop) was tested here with the gold uniquely owned; its earlier effect may have
  depended on the ownership split that W10 identified.
