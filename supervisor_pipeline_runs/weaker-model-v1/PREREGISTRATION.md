# Pre-registration: weaker-model-v1

Written on 2026-10-12, before the first paid call in this root. This file is hashed into every plan in FREEZE.json.

## Question

Do the controlled mechanisms that GPT-5.6 resisted become effective when the only change is a weaker model?

**Target:** a stable reduction in method-level Acc@1 relative to GPT-5.6, ideally through repeated gold-read-but-misranked
failures, with the benchmark held fixed.

## What is frozen (identical to mechanism-search-v1 held-out)

- **Instances.** The 9 held-out instances:
  - HO-HA-COMPRESS-01, HO-HA-JACKSONCORE-01 and HO-HA-MATH-01, recipe HA (entry-point ranking);
  - HO-HB-COMPRESS-01, HO-HB-LANG-01 and HO-HB-MATH-01, recipe HB (sink blame);
  - HO-HC-JACKSONCORE-01, HO-HC-LANG-01 and HO-HC-MATH-01, recipe HC (convention attribution).
- **Copies.** Variant patches, tests, manifests, golds, decoys, entry points and audits are byte-identical copies, recorded with
  their hashes in `review/BENCHMARK_COPY.json`.
- **Protocol.**
  - base prompt sha256 `845e21e7…`;
  - 50 tool calls, 5 test runs, 300 s;
  - external workspace (P1) and agent environment allowlist (P4);
  - the same tools and submission validator, and the same scoring and measures (`scripts/mx_metrics.py`);
  - the contamination scanner, with this root's name added as a marker.
- **Server code.** Every server tree is byte-identical to the GPT-5.6 server mxF0 (checked).
- **Reasoning setting.** Every run config carries `reasoning_effort: medium`, as for GPT-5.6. litellm (`drop_params: true`)
  drops it for models without a reasoning control.
- **What changes:** only the model id and its agent-profile label. Each profile is a copy of the GPT-5.6 profile with
  `agent_id`, `model` and `display_name` changed and identical defaults.
- **Reference:** GPT-5.6 is **not** re-run. Its held-out results are the reference: HA 14/15, HB 14/14, HC 15/15 (43/44
  valid runs, with no gold-read-but-misranked failure).

## Ladder (MODEL_SELECTION_AUDIT.md)

- **Primary rungs:** L1 gpt-5.5 → L2 gpt-5 → L3 gpt-5-mini → L4 gpt-5-nano → L5 gpt-4.1-mini → L6 gpt-4o-mini.
- **Intermediates:** gpt-5.4 (L1–L2), gpt-5.4-mini (L2–L3) and gpt-5.4-nano (L3–L4). These are used only as described under
  Stage procedure, step 4.

## Stage procedure (per model)

1. **Pilot.** 27 valid runs, 9 instances × 3 rounds, in a seeded interleaved plan frozen before its first call. Provider and
   infrastructure failures are replaced under the frozen driver rule and never scored.
2. **Operational viability.**
   - A model is **OPERATIONALLY TOO WEAK** if fewer than 70% of its valid runs end in a submitted ranking of ten.
   - Failures that count against a model: timeouts, malformed or rejected submissions, tool misuse, context failure, or an
     inability to run tests.
3. **Decision on a viable model:**
   - pooled pilot Acc@1 ≥ 0.90 → stop this model and move to the next primary rung;
   - pooled pilot Acc@1 < 0.90 **and** at least one genuine misranking (an answered run with gold rank ≠ 1) → extend to 5
     rounds (45 valid runs) and evaluate the success criteria.

   The brief steps down at ≥ 0.95. The gap between 0.90 and 0.95 is resolved here as "step down", because ≤ 0.80 is not
   reachable from ≥ 0.90 in practice.
4. **Operationally too weak.**
   - If an intermediate lies between the last viable rung and this one and has not been tried, run its pilot next.
   - Otherwise stop under rule B.
5. **A 45-run result that fails the success criteria** (for example 0.80 < Acc@1 < 0.90) → move to the next rung.

## Success: a useful weaker-model regime (evaluated on 45 valid runs)

All five must hold:

1. pooled Acc@1 ≤ 0.80;
2. at least 2 of the 3 recipes (HA, HB, HC) have repeated errors, meaning at least 2 wrong runs each;
3. at least 70% of valid runs are answered;
4. no-answers make up less than half of the misses, and provider failures stay excluded;
5. at least one wrong answered run shows the gold exposed, the gold read in full and the gold misranked.

**Preferred:** pooled Acc@1 between 0.40 and 0.70, with repeated attribution failures.

## Stop rules

- **A.** The first model meeting the success criteria becomes the primary weaker-model condition. Model search stops; no
  search for a weaker model just to lower accuracy further.
- **B.** Models become operationally too weak and no untried intermediate remains. Report the last viable model.
- **C.** Every viable model on the ladder stays at Acc@1 ≥ 0.90. Report that the benchmark is too easy across the tested
  capability range. Only then would a benchmark redesign be considered.

## Measures and failure modes

- **Per-run measures** are the frozen definitions in `scripts/mx_metrics.py`: included, answered, gold rank, Acc@1, rank-1
  category, gold exposed, gold read in full, decoy exposed, tests executed, decisive evidence displayed, tool calls, tokens,
  cost and wall time.
- **Mechanical split for every wrong run:**
  - NO_ANSWER: no submitted ranking of ten;
  - SEARCH_FAILURE: the gold's fault line was never displayed;
  - DISCOVERY_WITHOUT_INSPECTION: displayed, but not read in full;
  - ATTRIBUTION_FAILURE: displayed, read in full and still misranked.
- **Labels for answered wrong runs.** Two independent labellers each assign the preregistered mechanism-search Phase 7 label:
  SEARCH_FAILURE, DISCOVERY_WITHOUT_INSPECTION, ATTRIBUTION_FAILURE, EVIDENCE_RETRIEVAL_FAILURE, EVIDENCE_INTEGRATION_FAILURE,
  CONVENTION_PRIOR, LOCAL_ODDNESS_BIAS, ENTRY_POINT_BIAS, LEXICAL_SHORTCUT or OTHER.
  - The labellers see only the safe trajectory view and the patches.
  - A third labeller adjudicates any disagreement.
- **Per model:** HA, HB and HC Acc@1, pooled Acc@1 with Wilson 95% intervals, the gold-read-but-misranked rate, and the
  answered rate.

## Integrity

- **Frozen driver.** Freeze verification runs before every gate and launch, and a plan is frozen before its first call.
- **Scanner.** The contamination scanner runs on every run.
- **Clean environment.** `scripts/mx_tmp_audit.py` runs before every block, and nothing is built during paid blocks.
- **No tuning to the model.** No benchmark element is changed after seeing any result: bugs, decoys, tests, evidence, prompts,
  budgets and timeouts stay as they are.

## Cost

- **Estimates.** About $0.22 per gpt-5.5 run, falling to about $0.002 for gpt-5-nano (MODEL_SELECTION_AUDIT.md).
- **Staged total.** The whole ladder of pilots plus one 45-run confirmation should stay under about $20.
- **Check-in.** Stop and ask if the cumulative spend in this root exceeds $40.
