# Held-out confirmation results (Phase 5)

**Result: none of the three held-out recipes brought GPT-5.6's pooled Acc@1 down to the preregistered ≤ 0.60 threshold on fresh held-out instances.**

| Recipe | Valid runs | Correct | Pooled Acc@1 (Wilson 95%) | Label |
|---|---|---|---|---|
| HA entry-point ranking | 15 | 14 | 0.933 (0.702 to 0.988) | NOT_SUPPORTED |
| HB sink blame | 14 | 14 | 1.000 (0.785 to 1.000) | NOT_SUPPORTED |
| HC convention attribution | 15 | 15 | 1.000 (0.796 to 1.000) | NOT_SUPPORTED |
| **All** | **44** | **43** | **0.977** | |

- **Every answered held-out run ranked the gold first** (43/43).
- **The only miss is a no-answer run:** a 300 s budget timeout (HA-COMPRESS run-003). Its only model call returned about 5 s into
  the run, and the budget ran out before the results of the three commands it issued were recorded, so the time was lost in
  that tool step, not in waiting for a model response.
- **Behaviour across all 44 valid runs:** every run ran a test, and every answered run displayed the gold's fault line and read
  the gold in full.

The global stop rule's condition **B** is met, as the frozen held-out plan operationalises it:

- 17 families were screened, against a requirement of at least 12;
- held-out confirmation is complete for three failure-mode recipes (HA, HB, HC) that the plan derived from the S1 misses of
  the three strongest screened families (M19, M3, M5). The recipes are coded M10, M19 and M3: M5 is carried only through the
  HA and HB failure modes, and M10 itself screened NULL (NEW-R7-M10, 3/3). One HB cell, HO-HB-COMPRESS-01, has 4 valid runs
  rather than the preregistered 5 (X11);
- none reaches pooled Acc@1 ≤ 0.60.

Under rule B's preregistered wording, GPT-5.6 is therefore robust under the tested manipulations. This is scoped to GPT-5.6 at
effort medium in mini-swe-agent (300 s) on these 9 synthetic single-fault instances, and the per-recipe Wilson 95% lower
bounds (0.702, 0.785, 0.796) do not exclude moderate reductions.

## Design

The recipes, the nine instances as first frozen (HO-HC-MATH-01 at r0) and `plans/HO.json` were frozen before any held-out run.
Gate G14, HO-HC-MATH-01 r1, `plans/HO_cont.json` and `plans/HO_top.json` were added after held-out runs had begun (X10, X11),
each before its own first call.

- **Recipes.** HA, HB and HC are specified in HELDOUT_CONFIRMATION_PLAN.md. The recipe text was frozen at
  2026-10-10T04:01Z, before any Phase 4 result existed (`construction/heldout/RECIPES_FROZEN.json`).
- **Instances.** 9 fresh instances, 3 per recipe, each recipe across 3 projects. Each was built by a separate builder agent that
  was instructed not to read model output, trajectories or metrics (`construction/heldout/BUILDER_BRIEF.md`). The plan the
  builders read also summarises S1 outcomes and states the pre-run predictions, and at least two builder reports
  (HO-HB-COMPRESS-01, HO-HC-JACKSONCORE-01) cite those predictions.
- **Validation.**
  - Every instance is READY on builder gates G0 to G13. G14, harness compatibility, was added in X10. It is recorded as passed in the
    validation of HO-HC-MATH-01 r1. For all nine held-out and both Phase 4 variants, the retro check was re-run and archived on
    2026-10-12 (`analysis/verification/g14_retro_check.json`: 11/11 PASS). All nine instances were
    staged by the harness in their valid runs.
  - Every instance is fresh against all 134 previously used methods.
  - Each gold was **CONFIRMED** by an auditor that did not build the instance (`instances/<iid>/audit.json`, which records the
    auditor only as "independent agent").
- **Pre-run revisions.**
  - HO-HB-LANG-01 r0 was rejected for leakage (X6).
  - HO-HC-MATH-01 r0 could not be staged by the harness (X10).
  - Both were revised before any agent saw them and re-audited.
  - No instance was modified after an agent step.
- **Protocol.** The same frozen GPT-5.6 protocol as screening: effort medium, 50 steps, 300 s, external workspace, scanner.
- **Plans.**
  - `plans/HO.json`: 45 slots, seed 20261014.
  - `plans/HO_cont.json`: slots 8 to 44, after the X10 setup failure.
  - `plans/HO_top.json`: one top-up after the slot-36 halt review.
  - Each plan was frozen before its first call.

## Per instance

| Instance | Project | Valid runs | Acc@1 | Gold ranks | Infrastructure attempts (excluded, replaced) | Audit |
|---|---|---|---|---|---|---|
| HO-HA-COMPRESS-01 | Compress | 5 | 0.80 | 1, —, 1, 1, 1 (— = no answer, timeout) | 1 provider stall | CONFIRMED |
| HO-HA-MATH-01 | Math | 5 | 1.00 | 1 ×5 | 0 | CONFIRMED |
| HO-HA-JACKSONCORE-01 | JacksonCore | 5 | 1.00 | 1 ×5 | 0 | CONFIRMED |
| HO-HB-COMPRESS-01 | Compress | 4 | 1.00 | 1 ×4 | 4 provider stalls on round 5; cell left unfilled (X11) | CONFIRMED |
| HO-HB-LANG-01 | Lang | 5 | 1.00 | 1 ×5 | 0 | CONFIRMED (r1) |
| HO-HB-MATH-01 | Math | 5 | 1.00 | 1 ×5 | 0 | CONFIRMED |
| HO-HC-MATH-01 | Math | 5 | 1.00 | 1 ×5 | 1 setup failure on r0 (STOP_INTEGRITY; no agent step) | CONFIRMED (r1) |
| HO-HC-JACKSONCORE-01 | JacksonCore | 5 | 1.00 | 1 ×5 | 0 | CONFIRMED |
| HO-HC-LANG-01 | Lang | 5 | 1.00 | 1 ×5 | 0 | CONFIRMED |

The cost of the valid held-out runs was USD 7.64. The held-out blocks cost USD 8.42 in total, including infrastructure
attempts and estimated health-probe costs (COST_LEDGER.csv).

## STABLE criteria (PREREGISTRATION.md; operationalised in AMENDMENTS X8 before any held-out run)

| Criterion | HA | HB | HC |
|---|---|---|---|
| C1 pooled Acc@1 ≤ 0.60 | no (0.933) | no (1.000) | no (1.000) |
| C2 at least 2 of 3 instances ≤ 0.60 | no (0 of 3) | no (0 of 3) | no (0 of 3) |
| C3 no-answers under half of the misses | no (the 1 miss is a no-answer) | no (computed false; no misses) | no (computed false; no misses) |
| C4 at least half of the wrong answered runs exposed the gold | no (computed false; no wrong answered runs) | no (computed false; none) | no (computed false; none) |
| C5 scanner clean, instances valid | yes | yes | no: the HO-HC-MATH-01 r0 setup-failure STOP_INTEGRITY counts under X8 (no agent step ran; no leakage; X11) |
| C6 independent audits confirmed | yes | yes | yes |
| **STABLE** | **no** | **no** | **no** |
| **Label** (X8) | **NOT_SUPPORTED** | **NOT_SUPPORTED** | **NOT_SUPPORTED** |

PARTIALLY_SUPPORTED would have required pooled Acc@1 ≤ 0.80, or at least one instance at Acc@1 ≤ 0.60. Neither holds for any
recipe.

## How this compares with the predictions recorded before the runs

| Recipe | Prediction | Observed | Assessment |
|---|---|---|---|
| HA | 0.4 to 1.0, direction uncertain | 0.93; no misranking | consistent with the upper end |
| HB | ≥ 0.6 | 1.00 | consistent |
| HC | ≥ 0.8 | 1.00 | consistent |

The Phase 4 diagnostics are consistent with this, but they are exploratory (X4) and small. The two 0/3 screening effects
became 3/3 each after validity repairs (n = 3 per arm; 0/3 against 3/3 gives a two-sided Fisher p of 0.10). The DEPTH-01
revision made two javadoc edits, removing the decoy's doc contradiction and pinning the gold's own contract, so which edit
mattered is not identified. The COMPRESS-07 revision removed the correct sibling that offered an alternative entry-point
repair, together with its test. The held-out instances, whose documentation makes the gold the single defensible owner, were
also at or near ceiling. No held-out arm varied that property, and 8 of the 9 builder reports had already flagged the gold as
easy to spot or the instance as at ceiling risk. The held-out null therefore cannot be credited specifically to single-owner
documentation, and it does not show robustness to stronger forms of these mechanisms.

## Infrastructure events and one scored timeout (details in AMENDMENTS)

The X10 setup failure and the five provider stalls were excluded and never scored. HA-COMPRESS run-003 is not an
infrastructure event: it is a valid run, scored as a no-answer.

- **X10.** A setup failure on HO-HC-MATH-01 r0: its patch touched a `*.bak` file that the harness drops from workspaces. The
  instance was revised and gate G14 was added.
- **X11.**
  - Provider stalls: one on HO-HA-COMPRESS-01 (replaced) and four on HO-HB-COMPRESS-01 round 5. A replay of the stalled state
    returned in 8.3 s; one top-up was run and both of its attempts stalled. The cell was left unfilled because the outcome
    could not change the verdict.
  - One scored timeout (HA-COMPRESS run-003), counted as a no-answer under the frozen rule. Its only model call returned about
    5 s into the run; the results of the three commands it issued were recorded at about 305 s, after the 300 s budget, and no
    second model call was made (api_calls = 1). The budget was therefore spent in that tool step, not in waiting for the
    provider; X11's description of a second model call that did not return is not borne out by the trajectory. The run (12:16
    to 12:21Z) followed the HO-HA-COMPRESS-01 run-002 provider stall and a 574 s health probe, about 35 minutes before the
    HO-HB-COMPRESS-01 stalls.
