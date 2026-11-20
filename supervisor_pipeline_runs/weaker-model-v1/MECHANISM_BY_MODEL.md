# Mechanism by model (GPT-5.6 reference vs gpt-5.5 vs gpt-5)

Same instances, same base prompt (sha `845e21e7…`) and budgets (50 calls, 5 tests, 300 s); GPT-5.6 numbers are frozen
references (never re-run). The held-out and RH references (mxF0) ran under the same frozen protocol (server tree byte-identical
to this root's; the scanner and freeze library differ only by the W6/W7 fixes). The CHART-pair
and Closure references are September GPT-5.6 runs (diagnostic-noncanonical-v3, 2026-09-24; the canonical benchmark_runs root,
2026-09-17) made with an in-tree workspace before the P1 external-workspace and P3 explicit-effort patches and the driver's
freeze and contamination gates, with reasoning effort unset (provider default, documented as medium); the Closure instances
were re-hosted with the W6c manifest relabel. For those four comparisons "only the model differs" is not documented.

## Held-out recipes (gold pinned by documentation)

| Recipe | GPT-5.6 | gpt-5.5 | gpt-5 (answered only) |
|---|---|---|---|
| HA entry-point ranking | 14/15 (0.93) | 9/9 | 5/5 answered, 4 timeouts |
| HB sink blame | 14/14 (1.00) | 9/9 | 7/7 answered, 2 timeouts |
| HC convention attribution | 15/15 (1.00) | 9/9 | 5/5 answered, 4 timeouts |
| gold-read-but-misranked rate | 0/44 (43 answered) | 0/27 | 0/17 answered (10 timeouts, no ranking) |

No model misranked a held-out gold. The weaker models lose answers (gpt-5) or nothing (gpt-5.5), never attribution.

## Frozen breakers (Stage A; gpt-5 not run)

Stage A is exploratory: added by AMENDMENTS W5 after the direction change, outside PREREGISTRATION.md's question and success
criteria, on frozen copies of the instances GPT-5.6 had missed (selected on that outcome), 3 to 5 runs each. The four RH
instances are tier EXPLORATORY S1 screening instances (n = 3); Wilson 95% upper bounds for the zeros are 0.43 to 0.56.

| Mechanism | Instance(s) | GPT-5.6 | gpt-5.5 | gpt-5.5 gold-read-but-misranked |
|---|---|---|---|---|
| chain + locally odd correct hop, convention unpinned (M6/M19) | CHART-PIE-TREATMENT-03 | 0/5 | 0/5 | 5/5 (gold ranks 6, 6, 6, 6, >10) |
| the same fault, no chain (control) | CHART-PIE-CONTROL-03 | 5/5 | 5/5 | 0 |
| ownership split, omission gold (M4) | CLOSURE-12-OWN, CLOSURE-131-OWN | 1/5, 2/6 | 1/5, 0/5 | 4/4, 5/5 |
| chain + decoy doc contradiction (M19) | ADV-DEPTH-01 | 0/3 | 0/3 | 3/3 |
| distant decisive evidence (M5) | ADV-MASK-01 | 1/3 | 0/3 | 3/3 |
| definer/adapter, convention under-specified (M3) | LB-CHART-01-ADAPTER | 1/3 | 0/3 | 3/3 |
| adapter chain with a correct sibling (M3) | LB-COMPRESS-07-ADAPTER | 0/3 | 0/3 | 3/3 |

## Which mechanism family separates the models most (descriptive: 3 to 6 runs per instance, instances selected on GPT-5.6's misses)

- **Largest absolute drop vs the same model's own ceiling:** the CHART pair: 5/5 → 0/5 for both GPT-5.6 and gpt-5.5, within
  one matched pair. The arms differ in the 5-hop decomposition with its odd-looking hop, but also in whether the gold is the
  method the test calls (the control's gold `getArcBounds` is the entry point and was ranked first in every control run; 2 of
  5 treatment misses ranked it first), so the pair does not separate chain length, the odd hop and gold-at-entry-point. The
  treatment gold is label-defined (hops 3, 4 and 5 are behaviourally equivalent repair sites: W5 validity note,
  STAGE_B_DESIGN.md), and the blind labellers judged 3 of gpt-5.5's 5 treatment misses (`drift` first) defensible; the chain's
  own contribution awaits Stage B.
- **Where gpt-5.5 is worse than GPT-5.6:** M5 (ADV-MASK-01, 1/3 → 0/3), M3 under-specified convention (LB-CHART-01-ADAPTER,
  1/3 → 0/3) and the Closure-131 ownership split (2/6 → 0/5). Each gap is one or two runs (Fisher two-sided p = 1.0, 1.0,
  0.45) on instances selected because GPT-5.6 missed them. On these gpt-5.5 displayed the distant pin (second caller, passing
  offset tests, reference implementation) in most runs (LB-CHART-01 3/3 by the frozen measure, as for GPT-5.6; MASK-01 2 of 3
  and CLOSURE-131 3 of 5 per the blind labels) but never used it to settle ownership; GPT-5.6's correct runs are unlabelled,
  so whether the pin decided them is not recorded.
- **Where the two models are identical:** DEPTH-01, COMPRESS-07 and the CHART treatment (0 for both), CLOSURE-12 (1/5 each),
  the CHART control (5/5 each), and the held-out set (no misranked gold for either; GPT-5.6 43/44 with one timeout, gpt-5.5
  27/27).
- **Entry-point ranking** is the frozen rank-1 category in 8 of gpt-5.5's 26 misses (MASK-01 ×3, COMPRESS-07 ×2, DEPTH-01 ×2,
  LB-CHART-01 ×1; the two CHART-treatment runs that ranked `getArcBounds` first are coded DECOY because that instance lists the
  method under both roles). On the same instances GPT-5.6 had 4 entry-point rank-1s in 23 misses (COMPRESS-07 ×3, MASK-01 ×1;
  none on DEPTH-01 or the CHART treatment), so the overlap is MASK-01 and COMPRESS-07 only; its screening figure of 5 of 12
  adds RH-CF-V1 and RH-ADV-DEFINER-01, which gpt-5.5 did not run. By blind primary label (W9) ENTRY_POINT_BIAS is 12 of 26
  for gpt-5.5; on the four RH instances both models ran it is 9 of gpt-5.5's 12 misses against 4 of GPT-5.6's 10 (Fisher
  two-sided p = 0.19).

Per-run labels with the preregistered Phase 7 set are in FAILURE_MODE_COMPARISON.md (W9): primary ENTRY_POINT_BIAS 12,
EVIDENCE_INTEGRATION_FAILURE 6, CONVENTION_PRIOR 5, LOCAL_ODDNESS_BIAS 1, EVIDENCE_RETRIEVAL_FAILURE 1, ATTRIBUTION_FAILURE 1.
The 8 of 26 above is the frozen rank-1 category, not the blind label.
