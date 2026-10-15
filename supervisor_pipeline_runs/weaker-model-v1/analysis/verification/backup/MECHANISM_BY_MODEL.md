# Mechanism by model (GPT-5.6 reference vs gpt-5.5 vs gpt-5)

Same instances, same frozen protocol; only the model differs. GPT-5.6 numbers are frozen references (never re-run).

## Held-out recipes (gold pinned by documentation)

| Recipe | GPT-5.6 | gpt-5.5 | gpt-5 (answered only) |
|---|---|---|---|
| HA entry-point ranking | 14/15 (0.93) | 9/9 | 5/5 answered, 4 timeouts |
| HB sink blame | 14/14 (1.00) | 9/9 | 7/7 answered, 2 timeouts |
| HC convention attribution | 15/15 (1.00) | 9/9 | 5/5 answered, 4 timeouts |
| gold-read-but-misranked rate | 0/44 | 0/27 | 0/27 |

No model misranked a held-out gold. The weaker models lose answers (gpt-5) or nothing (gpt-5.5), never attribution.

## Frozen breakers (Stage A; gpt-5 not run)

| Mechanism | Instance(s) | GPT-5.6 | gpt-5.5 | gpt-5.5 gold-read-but-misranked |
|---|---|---|---|---|
| chain + locally odd correct hop, convention unpinned (M6/M19) | CHART-PIE-TREATMENT-03 | 0/5 | 0/5 | 5/5 |
| the same fault, no chain (control) | CHART-PIE-CONTROL-03 | 5/5 | 5/5 | 0 |
| ownership split, omission gold (M4) | CLOSURE-12-OWN, CLOSURE-131-OWN | 0.20, 0.33 | 1/5, 0/5 | 4/4, 5/5 |
| chain + decoy doc contradiction (M19) | ADV-DEPTH-01 | 0/3 | 0/3 | 3/3 |
| distant decisive evidence (M5) | ADV-MASK-01 | 1/3 | 0/3 | 3/3 |
| definer/adapter, convention under-specified (M3) | LB-CHART-01-ADAPTER | 1/3 | 0/3 | 3/3 |
| adapter chain with a correct sibling (M3) | LB-COMPRESS-07-ADAPTER | 0/3 | 0/3 | 3/3 |

## Which mechanism family separates the models most

- **Largest absolute drop vs the same model's own ceiling:** the chain + odd-hop shape (CHART pair): 1.00 → 0.00 for both
  GPT-5.6 and gpt-5.5, within one matched pair.
- **Where gpt-5.5 is worse than GPT-5.6:** M5 (ADV-MASK-01, 0.33 → 0), M3 under-specified convention (LB-CHART-01-ADAPTER,
  0.33 → 0) and the Closure-131 ownership split (0.33 → 0). On these GPT-5.6 occasionally used the distant pin (second caller,
  reference implementation); gpt-5.5 did not in any run.
- **Where the two models are identical:** DEPTH-01, COMPRESS-07 and the CHART treatment (0 for both), and the held-out set
  (ceiling for both).
- **Entry-point ranking** appears as a rank-1 class in 8 of gpt-5.5's 26 misses (GPT-5.6 screening: 5 of 12), in the same
  instances (MASK-01, COMPRESS-07, CHART treatment, DEPTH-01).

Per-run labels with the preregistered Phase 7 set are in FAILURE_MODE_COMPARISON.md once the blind labelling completes.
