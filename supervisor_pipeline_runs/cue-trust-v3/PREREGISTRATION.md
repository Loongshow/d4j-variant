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

## Amendment A1 (2026-10-08, before any GPT-5.6 run): GPT-5.6-first pilot

Appended before the first paid GPT-5.6 call. Nothing above is edited. The instances, the 20 variants, the cue wordings and the
27-slot pilot plan (`plans/pilot.json`) are unchanged.

**Model.** The user moved the pilot to OpenAI GPT-5.6 first; Sonnet and Opus are postponed. Agent profile
`mini-swe-agent-openai-gpt-5-6` from the canonical `benchmark_runs/agents.json` (sha256 `c5dac96e…`), model `gpt-5.6`, provider
`openai`, client litellm 1.98.0 and mini-swe-agent 2.4.6 (both installed 2026-08-26, before the earlier GPT-5.6 runs of 2026-09-21..25).

**Reasoning effort: `medium`, passed explicitly** (`model_kwargs.reasoning_effort`, recorded per run in `prompt.json` and the run's
`mini-swe-agent.config.yaml`). This is the provider default the earlier runs used without sending the parameter:
- OpenAI's reasoning guide states that GPT-5.6 "defaults to `medium` in both modes"; the GPT-5.6 model page lists
  "medium (default)" (developers.openai.com, read 2026-10-08).
- litellm 1.98.0's routing code states that for gpt-5.4+ "unset reasoning_effort means medium server-side".
- Routing is unchanged: for `gpt-5.6` with function tools, litellm sends both the unset-effort request (earlier runs) and the
  explicit-`medium` request (this pilot) to the OpenAI Responses API through its bridge (checked offline with
  `responses_api_bridge_check`). The earlier trajectories carry the same bridge fingerprints (encrypted reasoning items in 1,495 of
  1,549 responses, `chatcmpl-` ids).
- Limitation: the earlier responses do not echo the effort, so the earlier value is established from documentation and code,
  not from the earlier run records.

**Protocol identity with the earlier GPT-5.6 experiments.** Same base prompt (sha256 `845e21e7…`), 50 tool calls, 5 test runs,
300 s, localization-only, the same ranking parser and evaluation. Differences: the explicit effort parameter (same value, same
endpoint); v3 isolation (external workspace, opaque variant IDs); the F1 prompt arm, which is not used in the pilot.

**Pilot arm.** F0 only (normal prompt) for the 27 runs on server root `gptF0`. F1 runs only under the Phase 3 rule below.

**Run statuses: the uniform provider-failure rule** (`scripts/ct_status.py`), taken unchanged from adversarial-break-v1
(`diagnostic/PROVIDER_STALL_RULE.md`). Rule 3's match is widened to OpenAI's wording (`context_length_exceeded`).
- Infrastructure, excluded from all denominators: provider error, provider stall (rules 1 and 2) and start-up failures. Such a
  run may be replaced once per slot; a second infrastructure failure on the same slot halts the block.
- Behavioural, counted and never re-run: completed runs (including invalid or absent rankings, scored as NO_ANSWER), timeouts
  that are agent exhaustion, and context overflow.
- Any other status halts the block for review.

This makes explicit the intention-to-treat rule stated above. The original driver retried every non-completed run, which would
have re-run behavioural timeouts.

**Measures** are defined in the `scripts/ct_metrics.py` docstring and frozen with it. They include the brief's rank-1 categories
GOLD / DECOY / ENTRY_POINT / OTHER / NO_ANSWER; the ENTRY_POINT lists are fixed per instance in that file. Reasoning tokens are
observational only and are never read as laziness on their own.

**Pre-specified pilot contrasts** (per instance, F0; n = 3 per cell):
- CG: delta = Acc@1(C0) − Acc@1(CG).
- CD: delta = decoy-first rate(CD) − decoy-first rate(C0). The Acc@1 change is also reported.
- Classes: STRONG delta ≥ 2/3; WEAK delta = 1/3; NULL delta = 0; INVERTED delta < 0.
- Flags: FLOOR when CG's C0 Acc@1 = 0; CEILING when CD's C0 decoy-first rate = 1.
- Strongest signal reported per run: gold exposed and decoy ranked first.

**Phase 3 (forced inspection) rule.**
- *Trigger:* at least one STRONG contrast in the 27-run pilot.
- *Selection:* up to two instances that have a STRONG contrast. Rank by delta, then the strong-signal count, then the
  gold-exposed-but-misranked count.
- *Runs:* on `gptF1`, for each selected instance, {C0 and each STRONG cue condition} × 3 runs (seed 20261009, wording
  alternation as `ct_plan.py`).
- *Reading:* the effect disappears under F1 → skipping or insufficient verification is plausible; the effect persists → the code
  was inspected and the cue was still trusted.

**Null pilot.** If no contrast on any instance is STRONG, stop. Write `PILOT_NULL_ANALYSIS.md` covering:
- cue strength;
- cue exposure;
- baseline floor or ceiling;
- decoy plausibility;
- ineffective manipulation.

Then propose only a minimal redesigned pilot. No main block is started automatically in either case.

**No mid-block edits.** Cues are not changed during the 27 runs. After them, each manipulation is classified, and only then is
strengthening for a v2 pilot considered (the calibration rule above).

**Smoke run.** One bounded paid smoke run on the diagnostic root `gptDiag` (F0, `CTV-BEE8CB`), never counted. It is preceded by a
free harness proof against a local OpenAI-compatible stand-in (`scripts/stub_openai.py`, roots `gptStub` and `gptStubF1`).

## Amendment A2 (2026-10-08, before any GPT-5.6 run): corrections from the readiness review

An adversarial, read-only readiness review ran before the freeze.
- *Reviewers:* three, one per lens (metrics correctness, harness safety, brief compliance), plus one skeptic per top finding.
- *Result:* nine findings confirmed and none refuted; I triaged the 24 further findings myself.
- *Scope:* every change below is to measurement or harness code. Instances, variants, cues, the pilot plan, the hypotheses and
  the A1 decision rules are unchanged.

1. **Run status** (`scripts/ct_status.py`). The harness labels a non-answer `invalid_ranking` or `agent_protocol_error`, and
   labels any run `provider_error` whose raw output contains "litellm.", which a recovered retry also prints. The fix:
   - mini-swe-agent's recorded exit reason now decides; when it is an agent reason (Submitted, LimitsExceeded, TimeExceeded,
     RepeatedFormatError) and no valid ranking exists, the run is `no_answer`: behavioural, scored NO_ANSWER, never re-run;
   - other exits under those labels halt for review;
   - `protocol_violation` (source changed) is an integrity exclusion;
   - rules 1 to 3 are unchanged.
2. **Inclusion.** A run counts only if the driver's ledger (`diagnostic/block_<server>.jsonl`) records it as `valid` and its
   status is behavioural. Contaminated, integrity-breaking, identity-breaking and unchecked runs are excluded and listed. This
   enforces the pre-registered exclusions in the analysis itself.
3. **Gold exposure** uses the faulty line *as the level shows it*, with that level's gold-method renames applied. In CT-CHART-03
   CG1 and CG2 the cue renames the variable on the faulty line.
4. **Location-aware display matching.** A line of file F counts as displayed only when output attributed to F shows it:
   - with its line number; or
   - with its real neighbouring lines of F.

   Attribution comes from grep's path prefix or from F being named in the command. This applies to method coverage,
   decoy-signature exposure and cue exposure (cue lines are located by the patch hunk headers). Also:
   - more line-prefix formats are parsed;
   - command wrappers are peeled (`bash -c`, `timeout`, `env`);
   - non-answers get their own sufficiency class, `no_answer`;
   - tool-budget and test-budget overruns are recorded.
5. **Isolation.**
   - *P4:* the agent's bash commands see an allowlisted environment, with no keys, no `D4J_*` and no run-tree paths.
   - *Launcher:* it gives the server an allowlisted environment.
   - *Workspace roots:* external roots have neutral names.
   - *Driver:* it checks every run's workspace location.

   The stand-in proof shows zero sensitive variables visible to the agent, and `defects4j test` still runs.

   *Residual:* a process listing still shows the run-tree path of the agent's own process. In 225 earlier GPT-5.6 runs (4,228
   commands) no agent ran `ps`, `env`, a network tool or a checkout. Using that path requires an absolute path outside the
   workspace. The scanner flags such a path; it is contamination if it reaches the Defects4J tree or shows harness content.
6. **Scanner.** Contamination now also covers:
   - a repository checkout or clone;
   - any access to the Defects4J repository tree outside `framework/` (pristine checkouts, project repositories, run trees);
   - a flagged call showing a pristine-only source line;
   - another level's cue comment, now matched by its full text.

   Environment, process and network probes are flagged.
7. **Driver.**
   - The freeze is verified before every health gate and every launch, and each plan is bound to its server.
   - A per-slot ledger (plan hash, slot index) allows one infrastructure replacement per slot, across restarts.
   - A slot with a halting verdict needs operator review.
   - Run directories without a ledger record halt the driver at start-up.
   - One driver per server.
   - A run is identified by directory comparison, so a client-side error cannot orphan it.
   - Analysis servers require `diagnostic/PHASE1_ACCEPTANCE.json` for the current freeze.
   - The server's newest smoke configuration must carry the pinned effort.
8. **Freeze scope.** It also hashes:
   - the launcher, the setup script and P4;
   - every spec;
   - all five level patches of each planned instance.
9. **Budgets, stated exactly** (unchanged from the earlier runs):
   - 50 tool calls is mini-swe-agent's step limit, which counts model calls;
   - the 300 s limit is the harness kill;
   - the 5-test budget is recorded in the manifest, but not stated in the prompt and not enforced;
   - health-gate probes are paid one-call smoke tests.
10. **Known limitation, kept.** The pre-registered stall rule 2 cannot tell a hung provider request from the agent's own long
    command; the trajectory is saved per step. Every rule-2 reclassification is reported individually.

Stand-in proof on the corrected harness (local OpenAI-compatible stand-in, no credential, no cost):
- **A**, normal arm: valid and parsed; gold rank 2 with the decoy first; agent environment clean.
- **B**, forced-inspection arm: the F1 sentence appears exactly once; the source write was detected and the driver halted
  (integrity).
- **C:** the `defects4j checkout` attempt was detected and the driver halted (contamination).

Every request carried `reasoning: {effort: "medium"}` on the Responses route.

## Amendment A3 (2026-10-08, before any GPT-5.6 run): corrections from the second review

A second adversarial, read-only review ran on the corrected harness.
- *Reviewers:* driver/freeze/launcher, metrics/scanner, documents versus code; one skeptic per top finding.
- *Result:* six findings confirmed, none refuted; I triaged the ten further findings myself.
- *Scope:* measurement and harness code, plus the explicit statements below. The scientific design is unchanged.

1. **Exclusion rule, stated plainly.** The original exclusion was "provider failures with no model output". Following the
   user's brief ("provider/network failures may be replaced only under the existing uniform provider-failure rule"), A1 adopted
   the adversarial-break-v1 rule. That rule also excludes provider errors and stalls that occur *after* model output, and it
   allows one replacement per slot. This changes the original wording; it is not just a clarification. Every excluded run and
   its reason is reported by condition.
2. **Credit refusals and crashes.**
   - Halting exclusions (scan failure, contamination, integrity, workspace isolation, protocol identity) are checked before the
     credit test.
   - A credit or quota refusal is now an infrastructure attempt with `halt_reason = provider_credit`. The block still halts, and
     the slot keeps its one replacement after a top-up.
   - A harness `failed` run with no model call is `setup_failure` (infrastructure).
   - A run without a manifest, such as one cut short by a server crash, halts as unknown. After review it can be released only
     through the audited `--release-slot I --reason TEXT`, which appends a release record. Contamination, integrity and
     scan-failure stops can never be released.
   - Slot accounting uses the last record per run.
3. **Orphaned launches.** A pending record is written before each launch, and a restart adopts that run under its true slot and
   attempt. A launch also refuses to start when the external workspace root is not empty.
4. **Scanner.**
   - Pristine-only lines must be absent from every other file of the pristine tree; this removes false contamination from
     generic lines such as `this.x = x;` in sibling classes.
   - Leading `cd` targets are followed, including `~`, `$HOME`, `..` and a bare `cd`, and paths are judged by whether they leave
     the workspace.
   - A narrow marker check runs on every output: gold labels, submissions, manifests, VARIANT_KEY, the experiment name, and paths
     into the Defects4J tree outside `framework/`. For example, a process listing that shows the harness now counts as
     contamination.
   - A scanner failure halts (`STOP_SCAN_FAILED`) instead of reading as clean.
5. **Metrics.**
   - A numbered output line credits only its own line number.
   - The sufficiency classes follow the design definition (`EXPERIMENT_REDESIGN_v3.md` §4.5): *sufficient* = faulty line shown
     AND full decoy body shown AND (failure value shown OR an independent probe run).
   - Contrast classes use the A1 cuts on rates: STRONG means delta ≥ 2/3, WEAK means 0 < delta < 2/3. A cell whose n is not 3 is
     flagged.
6. **Decision rules reconciled.**
   - *Phase 3 trigger and null-pilot stop:* use the A1 contrasts (CG by ΔAcc@1, CD by Δ decoy-first rate). STRONG means the
     effect occurred in at least 2 of 3 runs. WEAK, a single run, does not trigger Phase 3 and does not by itself avoid the null
     stop.
   - *Calibration for a v2 pilot:* the original rule applies (strengthen a cue that moves Acc@1 by less than 1/3), and the CD
     decoy-first change is reported alongside.
   - *Pilot gate:* the cue is shown in at least 80% of CG/CD runs; the cost is at most USD 1.00 per run; behavioural timeouts are
     at most 20% of counted runs; metrics agree with my hand labels on 5 runs. `gpt56_tables.py` computes the first three, and
     the fourth is done by hand.
7. **Freeze and acceptance.**
   - Phase 1 acceptance is bound to a stable digest (common and per-server guards, plus the pilot and smoke plans), so adding a
     Phase 3 plan later does not invalidate it.
   - Acceptance requires the smoke run's ledger record to carry that digest and the smoke plan's hash.
   - The freeze records the final stand-in proof runs from the ledgers.
   - The health-gate description is exact: 3 consecutive passing probes at every driver start and after an infrastructure
     attempt, and 1 after a valid run.
8. **Credential.** The launcher uses one key chosen deterministically (`D4J_OPENAI_API_KEY` preferred). It refuses when the
   caller environment or the env file hold two different keys, and it logs only the variable name.
9. **Phase 3 procedure** (only under the A1 trigger), for each selected instance X with STRONG condition(s) K:
   1. `ct_plan.py plans/phase3_X.json --instances X --levels C0,K --runs 3 --seed 20261009`
   2. `freeze_gpt_pilot.py --add-plan plans/phase3_X.json --server gptF1`
   3. Start gptF1 and run the driver on that plan.

Final stand-in proof on the A3 harness (local stand-in, no credential, no cost; plans `plans/proof_A..E.json`):
- **A** (normal arm): valid; the ranking was parsed (gold rank 2, decoy first).
- **B** (forced-inspection arm, source write): the driver halted with an integrity verdict.
- **C** (`defects4j checkout`): the driver halted with a contamination verdict.
- **D** (the stand-in answered `insufficient_quota` mid-run): after about 4 minutes of client retries the run was recorded as
  an infrastructure attempt and the block halted on credit. After the stand-in "recovered", a restart replaced the slot once,
  and the replacement was valid.
- **E** (driver killed mid-launch): the restart adopted the run under its true slot and attempt, and it was valid.

The audited release command refused a valid slot and a contamination stop.
