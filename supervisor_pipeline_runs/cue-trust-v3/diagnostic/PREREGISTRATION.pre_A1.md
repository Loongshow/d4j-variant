# cue-trust-v3 pre-registration

Written 2026-10-08, before any cue-trust-v3 model run. Design source:
`/Users/shawnli/Desktop/Honours/thesis_writeup/EXPERIMENT_REDESIGN_v3.md`.
This file is frozen before the pilot. Any later change is appended as a dated
amendment, never edited in place.

## Question

When identifiers and comments misdescribe code whose behaviour is unchanged,
do repository-level LLM fault-localization agents blame the method the cue
points to rather than the method the code convicts? If so, do they commit
without checking the code (premature commitment) or after checking it (cue
override)?

## Instances and conditions

- **Instances.** One injected one-line semantic value fault in an existing
  long method of an existing large Defects4J file; a new deterministic
  trigger; one or more correct decoys on the executed path. Every instance
  passes `scripts/ct_validate.py` (READY) before any run.
- **Cue conditions (within instance, bytecode-identical):**
  - **C0:** neutral.
  - **CG:** gold-rationalising, two wordings CG1/CG2.
  - **CD:** decoy-incriminating, two wordings CD1/CD2.
  - Wordings alternate across runs (`scripts/ct_plan.py`).
- **Prompt factor F:**
  - **F0:** the frozen prompt.
  - **F1:** the frozen prompt plus one sentence: "Before you submit, display
    the complete source body of every method you rank in your top three."
  - Each F level runs on its own server root.
- **Primary model:** `claude-sonnet-4-6` (the only provider with an
  authorized key). `claude-opus-5-5` is a conditional replication on C0 and
  CD only.
- **Protocol:** frozen base prompt sha256 `845e21e7…`; 50 tool calls; 5 test
  runs; 300 s; localization-only; exact `Class::method` scoring.
- **Variant identity:** variant IDs are opaque (`CTV-xxxxxx`); the key is in
  `review/VARIANT_KEY.json`.

## Stages

1. **Pilot** (calibration only, excluded from confirmatory analysis): 3
   instances × {C0, CG, CD} × F0 × 3 runs = 27 runs.
   - *Gate:* manipulation and parser checks only. The cue is displayed in at
     least 80% of CG/CD runs, `ct_metrics.py` agrees with hand labels on 5
     runs, cost per run is at most USD 1.00, and the timeout rate is at most
     20%.
   - *Calibration rule:* if a cue moves Acc@1 by less than 1/3 on an
     instance, strengthen it along the name–body lever, i.e. identifiers that
     make correct code look wrong. Do not add hint comments. The modified
     instance is re-validated and gets new variant IDs.
2. **Main** (confirmatory): fresh instances, not the pilot ones; target 11
   instances × 3 C × 2 F × 3 runs = 198 runs on the primary model.
3. **Iteration after the main block** is exploratory and labelled as such.

## Hypotheses (directional)

- **H1:** CD raises decoy-at-1 and lowers Acc@1 relative to C0.
- **H2:** CG lowers Acc@1 relative to C0.
- **H3 (mechanism, secondary):** the CD and CG effects shrink under F1. A
  persisting effect under F1 is read as cue override; a vanishing effect as
  premature commitment. Both outcomes are reported.

## Analysis

- **Unit and outcome.** The unit is the instance. The primary outcome is
  per-instance Acc@1 (and decoy-at-1 for CD).
- **Primary contrasts (F0, two, Holm-corrected).** CD vs C0 and CG vs C0.
  Each uses an exact sign-flip permutation test on the instance-level
  differences, plus a bootstrap 95% CI over instances. A mixed-effects
  logistic model with a random intercept per instance is a sensitivity
  check.
- **Secondary.** F and C×F are estimation-only; depth stratum is an
  exploratory moderator.
- **Process measures (descriptive).** Fault-line, decoy, cue and
  failure-value exposure; verification; effort and tokens; and the
  evidence-sufficiency classes (efficient, cue override, premature, guess).
- **Non-answers.** Timeouts and invalid rankings count as not correct
  (intention to treat), with a sensitivity analysis that excludes them; their
  rates are reported by condition.
- **Exclusions (pre-registered):**
  - runs flagged contaminated by `scan_v3.py`, which also halts the driver;
  - runs breaking protocol identity or source integrity;
  - provider failures with no model output.
- **No pooling** across models or with earlier experiment families in any
  confirmatory test. Comparisons with earlier families are descriptive.

## Stop rules

The driver halts on:
- an exhausted provider credit balance;
- a failing health gate;
- contamination;
- an integrity break;
- a slot failing twice as infrastructure.

Halts are reported with the run state at the time. No paid run is launched
outside a written plan file.
