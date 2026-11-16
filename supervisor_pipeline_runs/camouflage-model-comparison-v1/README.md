# camouflage-model-comparison-v1

One continuous research task with three experiments, run on 2026-09-25 against the frozen Variant Lab
server `diagnostic-noncanonical-v3` (port 8792) with the frozen GPT-5.6 localization protocol.

| Experiment | Question | Status |
|---|---|---|
| **A** controlled large-file camouflage | does the gold's host environment change localization behaviour when structural distance and the semantic fault are held fixed? | **built and validated in full; paid block BLOCKED_PROVIDER_QUOTA after 2 of 30 slots** (1 of 2 attempted slots completed, 0.3212 USD) |
| **B** GPT model strength | is the benchmark's difficulty specific to GPT-5.6? | **BLOCKED_MODEL_AVAILABILITY** (the harness pins the OpenAI model to the server environment) |
| **C** Anthropic replication | does a Claude model behave the same way? | **BLOCKED_ADAPTER_SUPPORT** (credential present, adapter declares anthropic unsupported) |

## Start here

- `supervisor-recipe-audit/SUPERVISOR_RECIPE_AUDIT.md` - what the supervisor generator actually does, read
  from source, including the settled answer on "similar surrounding method names" (it is **not** in the recipe).
- `experiment-a-camouflage/review/CAMOUFLAGE_METRICS.md` - the metric definitions and the measured LOW/HIGH separation.
- `experiment-a-camouflage/review/CAMOUFLAGE_AUDIT.md` - proof that the arms differ only in the gold's host.
- `experiment-a-camouflage/review/OWNERSHIP_AUDIT.md` - behavioural and contractual ownership.
- `experiment-a-camouflage/review/READINESS.md` - A-R1..A-R13.
- `experiment-a-camouflage/results/CAMOUFLAGE_RESULTS.md` - the run results and Master Table 1.
- `combined-analysis/` - MASTER_RESULTS, CROSS_MODEL_TABLES, SEARCH_STRATEGY_AUDIT, DEPTH_PRIOR_ANALYSIS,
  THESIS_IMPLICATIONS, NEXT_EXPERIMENT_DECISION, and the two blocked-experiment records.

## The manipulation in one sentence

For each of three well-understood semantic faults, the same five-hop chain with the same trigger, the same
failure and a byte-identical gold method body was built twice, differing only in which existing production
class hosts the gold: a small sparse class (LOW) or a large method-dense class (HIGH) that clears the
supervisor recipe's own >= 1500-line host threshold.

## Reproduction

Construction is deterministic: `scripts/build_camouflage_variant.py` re-derives each arm from the
already-validated historical patch of the same fault. Validation, fresh reproduction, the five-state
equivalence probe, the camouflage audit and the ownership counterfactual all run from the scripts in
`scripts/`; `MASTER_MANIFEST.json` records their hashes and the six package hashes.
