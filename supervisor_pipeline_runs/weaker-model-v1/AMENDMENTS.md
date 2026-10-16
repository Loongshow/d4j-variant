# Deviations and amendments (weaker-model-v1)

PREREGISTRATION.md is frozen (hashed into every plan). Deviations and operational decisions are recorded here.

## W1 (2026-10-12): plan additions while a driver was running

- **What happened.** At 11:34Z, while the L1 (gpt-5.5) pilot driver was running, all later ladder plans and extensions were
  generated and frozen with `mx_freeze.py --add-plan`. That tool writes FREEZE.json non-atomically. A driver reading the file
  mid-write could have failed to parse it.
- **Effect.** None:
  - the L1 driver kept running and finished all 27 slots;
  - FREEZE.json parses;
  - each driver verifies only its own plan's hashes.
- **The stray log line.** A verify-only call made at the same time was refused by the driver lock. It wrote one harmless line,
  `HALT: another driver … holds …`, into `driver_w55.log`. It did not come from the running driver.
- **Rule from here on.** No freeze edits while a paid block is running.

## W2 (2026-10-12): L2 (gpt-5) slot-0 halt review and continuation

- **The halt.** L2 pilot slot 0 (HO-HA-JACKSONCORE-01) ended twice as `provider_stall`, under stall rule 2 of the frozen
  classifier. The driver halted with "failed twice as infrastructure".

| Attempt | API calls | Last tool result | Model reply before the 300 s kill | Cost (USD) |
|---|---|---|---|---|
| run-001 | 23 | at 168.8 s | none | 0.167 |
| run-002 | 26 | at 212.5 s | none | 0.186 |

- **Halt review.** `scripts/replay_stall_gpt.py` replayed each run's exact final state with a 240 s cap. The replays returned in
  **24.4 s** (run-002, with 87.5 s of budget remaining) and **62.9 s** (run-001, with 131.2 s remaining), both with tool calls.
  The calls that hung were therefore transient provider stalls, not model latency longer than the budget, so the classification
  stands.
- **Continuation.** Following the top-up rule (one top-up after a halt review), `plans/L2_gpt5_cont.json` holds all 27 L2 pilot
  slots in the original order; slot 0 is its replacement. It is frozen before its first call.
- **Observation.** gpt-5 makes many more calls per run than GPT-5.6 (23 to 26 against a median of 16). Its cost per run (about
  $0.18) is above the audit estimate.

## W3 (2026-10-13): L2 continuation halted by machine sleep, not by the model or provider

- **What happened.** L2_gpt5_cont ran slots 0 to 6 normally (7 valid runs). Slot 7 (HO-HB-MATH-01, run-001) was then
  classified `provider_stall`, and the health gate failed six times (probe walls 1,060 s to 6,001 s), so the driver halted
  at 2026-10-13T00:43Z.
- **Cause.** The macOS power log shows the machine in deep idle from 2026-10-12T13:12Z, waking only for 15-minute
  maintenance cycles until after the halt. The six probes and the slot-7 run all fall inside that window: slot 7 started at
  12:50Z and its process ran 2,373 s of wall time for a 300 s budget. The coordinator's keep-awake hold expires when the
  session is idle, and the session was idle while the block ran.
- **Effect on the data.** None of the seven valid runs is affected (normal durations, all answered). Slot 7's run-001 stays
  an excluded infrastructure attempt and is replaced. gpt-5 itself did not fail: the replays of its two earlier stalls
  returned in 24 s and 63 s (W2).
- **Resumption.** The same frozen plan is resumed; the driver continues at slot 7, attempt 2, from its ledger. From this
  block on, every driver is started under `caffeinate -i -w <driver pid>`, which holds the machine awake for the driver's
  lifetime regardless of session activity.

## W4 (2026-10-13): L2 (gpt-5) pilot result and decision

- **Result.** 27 valid runs: 17 answered, all 17 gold at rank 1; 10 behavioural timeouts (300 s budget exhausted while the
  agent was still working). Pooled Acc@1 0.63 (Wilson 0.44 to 0.79); answered rate 0.63; HA 5/9, HB 7/9, HC 5/9; no misranking.
- **Timeouts.** In 9 of the 10 the agent had already displayed and fully read the gold; 7 had run a test. Median answered run:
  22 model calls, 238 s, 8,064 reasoning tokens (GPT-5.6 median: 16 calls). gpt-5 is slower per step, not lost.
- **Decision (PREREGISTRATION, stage step 2).** Answered rate < 0.70 → OPERATIONALLY TOO WEAK at the frozen 300 s budget.
  Its accuracy loss is entirely no-answer, so it is not the attribution regime sought. Per step 4 the untried intermediate
  gpt-5.4 (I12) would be next on this ladder.
- **Machine-sleep check.** Runs proceeded every 5 to 6 minutes with caffeinate holding the machine awake (W3); no sleep gaps.

## W5 (2026-10-14): direction change, Stage A pre-registration (written before any Stage A paid call)

- **Change.** The user redirected the study: the goal is a stable accuracy drop that demonstrates degradation under long
  reasoning chains, gpt-5.5 is the model to test first, and ineffective earlier mechanisms are to be dropped. The weaker-model
  ladder (PREREGISTRATION.md) is paused after L1 (gpt-5.5, 27/27) and L2 (gpt-5, TOO_WEAK, W4). Nothing frozen is modified.
- **Evidence reviewed before this design** (sources: mechanism-search-v1 mining and reports, camouflage-model-comparison-v1,
  anthropic-pilot-v1, ocflb-differential-analysis-v1, the supervisor-recipe source audit):
  - the chain recipe alone (two-file-crossing 5-hop chains through ≥1500-line hosts) left GPT-5.6 at 0.94 to 1.00 over about
    230 runs and Claude Opus at 3/3 on both odd-hop-free TREATMENT arms; it raised search cost only;
  - host-file size was never measured on GPT-5.6 (the camouflage block stopped at 2 of 30 slots); Claude was 3/3 on both arms
    of its one pair;
  - the instances that broke both models share one shape: a quiet terminal gold plus a correct mid-chain hop whose arithmetic
    reads backwards against loosely worded documentation (CHART-PIE-TREATMENT-03: GPT-5.6 0/5, Claude 0/3), or an ownership
    split with an omission gold (CLOSURE-12-OWN-001 0.20, CLOSURE-131-OWN-001 0.33 for GPT-5.6).
- **Stage A (this entry).** Re-host, unchanged, the frozen instances GPT-5.6 missed and run gpt-5.5 on them:
  - FZ-CHART-PIE-TREATMENT-03 and its control FZ-CHART-PIE-CONTROL-03 (same fault, 5-hop chain vs none);
  - FZ-CLOSURE-12-OWN-001 and FZ-CLOSURE-131-OWN-001;
  - the four S1 instances GPT-5.6 missed, copied byte-identically from mechanism-search-v1: RH-LB-COMPRESS-07-ADAPTER (0/3),
    RH-ADV-DEPTH-01 (0/3), RH-LB-CHART-01-ADAPTER (1/3), RH-ADV-MASK-01 (1/3).
  - 5 valid runs each for the four FZ instances, 3 each for the four RH instances (matching their GPT-5.6 n): 32 runs, about
    $11 at gpt-5.5's observed $0.34 per run. Protocol, scoring and measures unchanged; the server tree is byte-identical to
    mxF0; the scanner and freeze apply.
  - Read-outs: per-instance Acc@1 against the GPT-5.6 reference; treatment vs control for CHART-PIE-03; for every wrong run,
    the mechanical split (NO_ANSWER / SEARCH_FAILURE / DISCOVERY_WITHOUT_INSPECTION / ATTRIBUTION_FAILURE) and the
    preregistered Phase 7 label.
  - Prediction recorded now: gpt-5.5 at or below GPT-5.6 on each instance; CHART-PIE-TREATMENT-03 ≤ 0.2 with the control at
    1.0; the CHART pair is the one that isolates the chain.
- **Stage B (conditional, not yet designed in detail).** If Stage A transfers, build fresh instances in Lang/Math/Compress as a
  2×2 (5-hop chain through large hosts yes/no × odd-looking correct hop yes/no), with the "externally pinned, locally
  under-specified" rule from ocflb-differential-analysis-v1 so each gold stays objectively owned. This measures the chain's own
  contribution instead of assuming it. It waits for the user's script, which may add to the recipe.
- **Validity note for the record.** CHART-PIE-TREATMENT-03's gold rests partly on its label: one-line repairs at hops 3, 4 or 5
  are behaviourally equivalent (mining annotation). Any claim built on it needs the Stage B instances, where the gold is pinned
  externally.

## W6 (2026-10-14): freeze and scanner made bug-id aware; freeze digest refreshed; Phase 1 re-accepted with one new smoke run

- **Why.** The Closure instances live under `new_bug_variants/Closure/bug-12` and `bug-131` (validated bases Closure-12f
  and Closure-131f). `freeze_lib.variant_files()` and `scan_v3.vpatch()` hard-coded `bug-1/L20`, so such a plan could not
  be frozen, verified or scanned.
- **Change.** One line in each: the variant path takes the bug id from the key entry (default 1, so every existing entry
  resolves to the same path as before). sha256: freeze_lib.py eafa41b244ff0aac → 258a2bfda81d72ba; scan_v3.py 656cc79a8be27601 → 749c5521c4028b2e.
- **Consequence.** The guarded-common hash set and the acceptance digest change. The completed blocks (smoke, L1, L2) keep the
  digest they ran under in their ledger records; nothing about them is altered. FREEZE.json's guarded_common is refreshed and
  Phase 1 acceptance is re-established with one bounded paid smoke run on wmDiag under the new digest before any Stage A call.
  The unrun ladder plans stay frozen under their own per-plan hashes.

## W6c (2026-10-14): Closure re-hosts relabelled to the L20 namespace; plan A1 re-frozen; Phase 1 re-accepted

- **Discovery failure.** The harness drops a variant whose manifest `reasoning.level` differs from its directory namespace
  (`variantLibrary.mjs`, `discoverRecordsInNamespace`). The canonical Closure manifests carry `L10`; re-hosted copies live under
  `L20`, so FZ-CLOSURE-12-OWN-001 and FZ-CLOSURE-131-OWN-001 were invisible to the server while every Chart and S1 variant was
  found.
- **Fix (data, not server).** `wm_rehost.py` now sets `reasoning.level` to `L20` in the re-hosted copy, keeps the original
  under `reasoning.original_level`, and lists only the artifacts actually shipped. The patches, the gold and every other field
  are unchanged; the server tree stays byte-identical to mxF0. The two Closure entries were re-hosted (and re-reproduced) with
  this fix.
- **Freeze.** Because the manifests changed, plan A1 is removed from FREEZE.json and added again before any A1 call. The
  acceptance script change (optional smoke-plan argument) is covered by the W6b digest refresh.
- **Phase 1.** Re-accepted on 2026-10-14T04:46Z with smoke run CTV-68B9DE/run-002 on wmDiag (gpt-5.5), 13/13 PASS under the
  new digest. The first attempt that day made no paid call: the original smoke plan's slot already held a valid run and was
  skipped by the driver.

## W7 (2026-10-14): Stage A halt at A1 slot 2 was a scanner false positive; scanner precision fix; continuation

- **What happened.** A1 slot 2 (FZ-CHART-PIE-CONTROL-03, run-001) ranked the gold first and was then stopped:
  `cross-level cue tokens displayed ['double angle, double extent, double explodePercent) {', 'explodePercent);']`.
- **Cause.** At call 2 the agent printed its own test file (`tests/.../PiePlotTests.java` lines 650–710). The `ArcProbe` test
  added by the control's own `test.patch` contains those two lines; the treatment's `variant.patch` re-uses the same parameter
  list for its new `ring` hop. The scanner subtracted this variant's own `variant.patch` lines and the pristine tree from the
  sibling token set, but not its own `test.patch` lines or the files that patch touches, so text from the run's own workspace
  counted as foreign. The text is not in the pristine `PiePlot.java` (its signature is split across lines).
- **Fix (precision only).** `scan_v3.py` now treats the run's own `test.patch` like its own `variant.patch`: its added lines and
  touched files are never foreign. Nothing is removed from the protections against sibling-variant text, harness content,
  out-of-workspace access or pristine-source display. sha256 749c5521c402… → 28e617af1827….
- **Re-scan under the fix (read-only).** CTV-CB7F8F/run-001: contaminated=false, 0 flagged calls. The two valid runs of the
  block (CTV-5376D5/run-001, CTV-71ABF3/run-001) are unchanged (contaminated=false).
- **Disposition.** Under the frozen rule a contamination stop is never released, so run-001 of the control stays excluded and
  its slot was replaced in `plans/A1_gpt55_cont.json` (slots 2 to 19 of A1 in the original order), as in mechanism-search X2.
  Because a guarded script changed, the freeze digest was refreshed (FREEZE.json amendment "W7", 1f719a5c… → dcc0a163…) and
  Phase 1 re-accepted with smoke run CTV-68B9DE/run-003 on `plans/smoke3.json` (13/13 PASS) before any further paid call.
- **Note on numbering.** FREEZE.json also carries an amendment "W6b" (the acceptance-script change that made the smoke plan
  path an argument); it is covered by the W6 text and has no separate entry here.

## W8 (2026-10-14): Stage A complete; pre-registered prediction met

- **Runs.** 32 valid (A1: 20, A2: 12). One excluded contamination stop (W7, replaced). No provider failures, no timeouts.
- **Result.** gpt-5.5 on the eight breaker instances: 1/27. Matched CHART pair: treatment 0/5 (gold ranks 6, 6, 6, 6, >10),
  control 5/5. CLOSURE-12 1/5, CLOSURE-131 0/5, ADV-DEPTH-01 0/3, ADV-MASK-01 0/3, LB-CHART-01-ADAPTER 0/3,
  LB-COMPRESS-07-ADAPTER 0/3. Pooled over the 32 runs including the control: 6/32 = 0.188 (Wilson 0.09 to 0.35).
- **Failure type.** All 26 misses are answered runs in which the gold's fault line was displayed, the gold read in full and a
  test executed (mechanical split: ATTRIBUTION_FAILURE 26/26). Rank-1 categories: declared decoy 18, entry point 8.
- **Against the W5 prediction.** "gpt-5.5 at or below GPT-5.6 on each instance; CHART treatment ≤ 0.2 with control 1.0": met
  on every instance; gpt-5.5 is below GPT-5.6 on three of eight (CLOSURE-131, ADV-MASK-01, LB-CHART-01-ADAPTER) and equal on
  the other five.
- **Reading.** On a current model the chain-isolated drop exists (CHART pair) and the attribution failures GPT-5.6 showed in
  screening recur and deepen. The Closure signature caveat (W-rehost: first assertion line only) affects only the
  failure-values-seen process measure.
- **Cost.** Run cost in this root $28.90 plus health probes (L1 $9.29, L2 $6.06, Stage A $12.60, smokes $0.95).

## W9 (2026-10-14): Stage A failure-mode labelling complete

- 26 wrong gpt-5.5 runs, two blind labellers each with the preregistered Phase 7 label set, 11 adjudicated (agreement: 15
  full, 2 primary-only, 9 none). Records in `analysis/failure_modes/labels_stageA_blind.json`; comparison with GPT-5.6 in
  FAILURE_MODE_COMPARISON.md.
- Primary labels: ENTRY_POINT_BIAS 12, EVIDENCE_INTEGRATION_FAILURE 6, CONVENTION_PRIOR 5, LOCAL_ODDNESS_BIAS 1,
  EVIDENCE_RETRIEVAL_FAILURE 1, ATTRIBUTION_FAILURE 1. Defensible rank-1 answers: 4 (3 CHART treatment runs ranking `drift`,
  1 DEPTH-01 run citing the decoy's doc contradiction), partly 5, no 17.
- Mechanical split unchanged: 26/26 gold exposed, read in full, test executed.

## W10 (2026-10-14): corrigenda from the independent verification of the Stage A documents

Four result documents (WEAKER_MODEL_RESULTS, MECHANISM_BY_MODEL, FAILURE_MODE_COMPARISON, SUPERVISOR_UPDATE) were checked by
nine verifier agents and every finding adjudicated against the primary data before edits (`analysis/verification/`): 72
confirmed, 29 partly, 3 rejected. The documents are corrected in place. Earlier amendment text stays as written; these
corrections take precedence over it.

1. **W5 and W8, "the CHART pair isolates the chain".** It does not. The treatment arm adds the 5-hop decomposition together
   with a correct hop whose arithmetic reads backwards and an ownership split in which hops 3 to 5 are behaviourally
   equivalent repair sites, and the control's gold (`PiePlot::getArcBounds`) is the method the test calls. The pair contrasts
   that bundle against the undecomposed method; chain length, the odd hop and gold-at-entry-point are not separated.
2. **W5, "0.94 to 1.00 over about 230 runs".** The traceable figures (mechanism-search-v1 `mining/run_data.json`, GPT-5.6):
   odd-hop-free September treatment arms 43/44 pooled on the nine 5-hop arms and 37/42 on the six 6-hop arms (three of those
   five misses timeouts), 0.80 to 1.00 per arm on answered runs. 0.94 is the family-wide pool including controls and PIE-03.
3. **W5, "the facade lie was never tested on GPT-5.x".** It was tested once: NUMBERUTILS-TREATMENT-01 (the generator's own
   two-hop chain, Lang), GPT-5.6 5/5 at rank 1 with the lie read in every run. Untested beside a 5-hop chain on a hard instance.
4. **W8, "eight breaker instances" and "pre-registered prediction met".** Seven breakers plus the CHART control make eight
   instances; the 1/27 is over the seven. The W5 expectation was written after the direction change and restated GPT-5.6's
   and Claude's known results on the same instances; it is an exploratory expectation, not a preregistered prediction.
5. **Reference protocol.** The GPT-5.6 references for the CHART pair and the Closure instances are September runs made before
   the P1 external-workspace and P3 explicit-effort patches, with reasoning effort unset. For those four comparisons "only
   the model differs" is not documented; it holds for the four RH instances (mxF0, same frozen protocol).
6. **Scope.** Stage A is exploratory (outside PREREGISTRATION.md's question), its instances were selected on GPT-5.6's misses,
   and per-instance gaps between the models are one or two runs at n = 3 to 6 (Fisher two-sided p ≥ 0.19 everywhere).
   MATH-NORM-TREATMENT-01, a September instance of the chain-plus-odd-hop shape, was solved by GPT-5.6 in 4/4 answered runs,
   so the shape is not uniformly breaking.

## W11 (2026-10-14): Stage B construction tooling and deviations from the supervisor's recipe

Decisions (user, 2026-10-14): the facade lie stays inside the chain arm; gpt-5.5 only; third project Chart `DatasetUtilities`.
Design: STAGE_B_DESIGN.md and STAGE_B_PREREGISTRATION.md; construction records under `construction/stageB/`.

Tooling (none of it guarded; FREEZE unchanged until plans are added):
- `scripts/generator/`: the supervisor's generator modules vendored from `thesis/` with sha256s in `PROVENANCE.json`
  (`host_search`, `chain_transform`, `extract_transform`, `candidate_search`, `validate`, `package_variant`) plus the Claude-written
  `callgraph.py` shim; `generate_chain.py`/`chain_design.py` (the claude-opus-5 design step) are deliberately not used.
- `scripts/stageB_lib.py`: wraps `pick_two_hosts` (seeded host draw over classes >= 1500 lines), `pick_insertion_anchor`
  (seeded interior public method), `rewrite_facade` (body replacement + lie inside the existing javadoc).
- `scripts/stageB_spec.py`: builds a cell on a scratch copy with those functions, derives unique old/new context edits that
  reproduce the recipe output byte for byte (asserted), and writes a spec for the validator.
- `scripts/stageB_validate.py` = `mx_build_validate.py` with SB1 (an EXISTING trigger test; empty test.patch), SB2 (G7 applies
  test.patch only when non-empty), SB3 (spec sha and cell in the record). All 16 gate checks otherwise unchanged.
- `scripts/stageB_harness_check.py` = `mx_harness_check.py` staging with this root's evaluation server `models/w55` (SB4; the MX
  copy imports `models/mxF0`, absent here, which made G14 fail on the first validation attempt of 2026-10-14 for a path reason only;
  the two affected cells passed every other gate and pass G14 directly after the fix; all twelve cells were re-validated from scratch).
- `scripts/stageB_package.py` = `mx_package_new.py` with id namespace `weaker-model-v1:<iid>`, Stage B manifest extension, hop
  count and cell recorded; `scripts/stageB_key.py` merges entries into the existing key.

Deviations from the recipe as code, each recorded per cell in the spec's `stage_b` block:
1. Five hops over five distinct hosts (the recipe inserts two hops in two hosts): hosts are drawn with `pick_two_hosts` called
   with seed 1014, 1015, 1016 and growing exclusions (`construction/stageB/designs/host_draws.json`), so the draw is the recipe's.
2. Anchors never land on a hop inserted earlier (the recipe can anchor on its own hop); interfaces and enums are skipped as
   hosts (a static method in a 1.4-era interface does not compile); for Chart, `org/jfree/chart/plot/*` is excluded (the
   CHART-PIE-03 neighbourhood).
3. Hops reference their types and callees through added imports (the recipe has no import mechanism and would need
   fully-qualified names); the facade keeps the recipe's fully-qualified call into hop 1.
4. The fault is a hand-authored omission applied with the recipe's exact-once replacement semantics; no LLM anywhere.
5. One-hop cells place the gold and the sibling helper directly below the facade (natural code), not at anonymous anchors.
6. B3's facade guard `if (minimum <= maximum)` is rewritten to the equivalent `if (categoryCount > 0)` in every cell so the
   fault surfaces as `Range(NaN, 8)` (a value mismatch) rather than a null range (an NPE at the test line); G1 proves the rewrite
   behaviour-preserving on the suite.
7. The gold's javadoc does not state the omitted step (MX held-out rule 4 required it and produced ceiling instances); the
   convention is pinned by second callers, sibling implementations and passing tests named in `evidence`/`ownership_tests`.
Smoke checks (2026-10-14, `stageB_spec.py --check`): all twelve cells compile and fail only on the trigger's assertion with one
signature per bug (B1 `expected:<2> but was:<0>`, B2 `expected:<0.0> but was:<7071.0>`, B3 `expected:<2.0> but was:<NaN>`).
Baseline full suites of the three fixtures: zero failures (construction/stageB/validation/baseline_*.json).

## W12 (2026-10-14, incident): VCS metadata of three shared mechanism-search-v1 fixtures deleted by the G14 staging check

What happened. This root's `construction/fresh/{Lang,Math,Chart}` were symlinks to `mechanism-search-v1/construction/fresh/<P>`.
The G14 check (`stageB_harness_check.py`, a copy of `mx_harness_check.py`) hands the fixture path to the server's own
`copyDirectoryFiltered`; given a symlink, that function creates the destination as a symlink to the source, and the following
`stripHistoryDirs(destination)` deletes `.git` (and `.svn`) THROUGH the link, in the real fixture. Verified on a scratch tree.
Two direct checks (Lang, Chart, about 20:40) and the Math chain's first G14 (about 20:55) removed `.git` from the MX fixtures
Lang, Math and Chart and `.svn` from Chart. No tracked file was changed: a fresh `defects4j checkout -p <P> -v 1f` of each
project is byte-identical to the MX fixtures across all tracked files (Lang 312, Math 1456, Chart 1212; zero differences).
Compress and JacksonCore were not involved.

Effect. The MX fixtures still serve any read-only use; MX's own builders (which rely on `git diff`/`git apply` inside copies)
would fail until `.git` is restored. Restoring from the server's checkouts (`workspaces/defects4j/<P>-1/fixed/.git`, clean,
identical content) was proposed and left to the user (the action modifies a shared resource outside this root).

Response. (1) All validator chains were stopped. (2) `stageB_harness_check.py` now copies from the REAL path and aborts if the
destination is a symbolic link (SB5), checked on scratch and on this root's own fixture. (3) This root's fixtures are now its own
fresh checkouts (`construction/fresh/{Lang,Math,Chart}`, real directories, content-identical to MX's), so Stage B no longer
touches the shared fixtures at all. (4) Every Stage B cell is re-validated from scratch on these fixtures; the G0-G13 results
recorded before the incident are discarded. The Stage B specs are unchanged (they were derived from identical content).

Validation outcome (2026-10-14, third attempt, on this root's own fixtures): all twelve cells READY on the 16 gates
(`instances/SB-*/validation.json`, logs in `construction/stageB/logs/`); in every cell both declared compensating edits left the
trigger failing (G9 absorbed = false). Validator hardening after the fact: SB6 aborts a build whose variant.patch is empty (the
silent symptom of a fixture without `.git` seen during W12). SB6 was added after the twelve validations; it changes no gate.

## W13 (2026-10-14, before any Stage B run): refinement of the single-owner rule after the first audit

The Chart auditor (bug B3) found that one line at the facade (C00/C01) or hop 1 (C10/C11),
`minimum = Math.min(minimum, base + findMinimumStackedRangeValue(dataset).doubleValue())`, passes the trigger, the ownership
tests and the full suite. Every other item was in order (a true, b false, d false, e true, f true). The edit does not repair the
data path: it discards the gold's output (`limits[0]` becomes dead) and recomputes the quantity with an unrelated existing method.
Such a bypass exists wherever a fixture holds a redundant implementation (Lang's `indexOfAnyBut` has a CharSequence overload; the
original facades themselves could always have been "repaired" this way) and it does not point at a fault location, which is what
the single-owner rule is for (CHART-PIE-03 failed it because three hops shared the convention and any of them could carry the
arithmetic).

Rule as refined (applies to all three bugs, uniformly, and is recorded in STAGE_B_PREREGISTRATION.md and AUDIT_BRIEF.md):
- (c) **competing repair**: a one-line edit at a non-gold method that makes the trigger pass with the ownership tests and the suite
  green AND keeps every method on the trigger path used as its documentation describes (no hop's documented output becomes dead,
  no hop is removed from the path). A bug with any such edit is REJECTED.
- (c-bypass) **bypass**: a passing one-line edit that replaces the gold's result with another implementation or makes a hop's
  output dead. Recorded per bug with the exact edit; it does not reject the bug, and it is reported as a limitation in the results
  (an agent ranking the edited method first for that reason is labelled ENTRY_POINT_BIAS or OTHER by the blind labellers, not
  credited).
The three auditors re-evaluate (c) under both readings and record `c_competing_repair` and `c_bypass` separately. Verdicts are
CONFIRMED only with a = true, b = false, c_competing_repair = false, d = false, e = true, f = true.

## W14 (2026-10-14, before any Stage B run): B2 (Math, atanh series tier) withdrawn after audit

The independent auditor REJECTED B2 under the W13 rule: a one-line half-angle argument reduction at the facade (C00/C01) or hop 4
(C10/C11), evaluating `4 * series(h(h(a)))` with `h(a) = a / (1 + sqrt(1 - a*a))`, keeps the gold in use, passes the trigger
(round-trip metric 2.00 against the tolerance 2) and every ownership test in all four cells: a competing repair, not a bypass
(42 trials logged in `construction/stageB/audits/SB-B2.json`; items a, b, d, e, f were all in order, and log1p/Dfp closed forms
were additionally recorded as bypasses). This is the upstream pre-scaling ambiguity already seen in MATH-NORM-TREATMENT-01: an
accuracy fault in a numeric kernel can always be avoided by a caller that reduces the argument first. B2's four READY cells are
not packaged and never run. A Math replacement is sought with the shape that survived audit in B1 and B3: an omission inside
an iteration over data whose effect no caller can pre-filter or recover in one line. If none is ready when the confirmed bugs
launch, the block runs with the confirmed bugs and the replacement runs as a second block under the same plan rules (recorded).

## W15 (2026-10-14): B4 = the Math replacement for B2 (StatUtils.mode, NaN skip inside the frequency tally)

Design (`construction/stageB/designs/B4_math.py`, ids SB-B4-C*): facade `StatUtils.mode(double[])` (the 3-arg overload enters the
same path); gold `tabulate(values, begin, length)` builds the `Frequency` table and skips NaN inside its loop; the fault removes
the skip, NaN (4 occurrences) becomes the mode, and `StatUtilsTest::testMode` fails at its nanInfested block with
`expected:<0.0> but was:<NaN>` (smoke-checked in all four cells). Pins: both facade javadocs ("NaN values are ignored when
computing the mode"), `FrequencyTest.testModeDoubleNan` (Frequency keeps NaN keys, so the skip cannot move downstream), the
NaN-skip idiom of `MathArrays.normalizeArray`. The original private `getMode` is removed in every cell (it held the skip). The
odd element is the mode extraction written with indices computed from the end (C01 sibling, C11 hop 3).
Deviations recorded: (1) `StatUtils` (about 900 lines) is below the recipe's 1800-line TARGET gate; the facade file is common to
all four cells and is not a factor of the 2x2. (2) Hosts must now be PUBLIC classes (the seeded draw for this target first produced
the package-private `FastMathLiteralArrays`, whose hop could not be called from another package; the generator does not check
this); the redraw with the same seed gives RealVector, DSCompiler, MathArrays (hop 3), BlockRealMatrix, FastMath (gold host),
recorded in `designs/host_draws.json` under `Math-B4`. (3) The generator gained `pre_edits` (edits shared by a geometry, used to
remove `getMode` and to reroute the 3-arg overload) and an explicit insertion anchor for the one-hop helpers. B4 goes through the
same validation, independent audit (W13 rule) and packaging as B1/B3 and runs as block 2 (`plans/B_stageB_gpt55_block2.json`,
20 slots) after block 1, under the same server, freeze and driver rules.
W15 addendum (same day): the first B4 chain cells failed G1 only: `UnmodifiableArrayRealVectorTest::testAllButExcluded` and
`UnmodifiableOpenMapRealVectorTest::testAllButExcluded` enumerate `RealVector`'s public methods by reflection, and a public static
hop with a `double[]` parameter there breaks them (B2's `double` hop had passed). `RealVector` is excluded from the B4 host pool
for that reason and the seeded draw was repeated: hosts BlockFieldMatrix (hop 1), DSCompiler, MathArrays (hop 3), Dfp, FastMath
(gold host). C00/C01 (READY on the first attempt) are unchanged; C10/C11 were regenerated and re-validated from scratch.

## W16 (2026-10-14): block-1 blind labels, and one measurement limitation of the frozen `gold_exposed`

Block 1 (B1 Lang, B3 Chart; 40 runs) ended 2026-10-14 11:31Z with 14 misses, all gold rank 2 behind the facade. Two blind
labellers per miss (process lens, argument lens; 28 label files in `analysis/failure_modes/labels_block1/`, task files in
`tasks_block1/`, aggregate in `labels_block1_raw.json`): primary ENTRY_POINT_BIAS in 28 of 28; `gold_named_in_chain` and
`divergence_located_at_gold` yes in 28 of 28; defensibility no 20 / partly 8; secondaries EVIDENCE_INTEGRATION_FAILURE 4,
LOCAL_ODDNESS_BIAS 4, CONVENTION_PRIOR 1. Six runs split between the lenses on defensibility or secondary and were sent to a
third-lens adjudicator (`adjudication_block1_tasks.json` -> `labels_block1_adjudicated.json`).

Measurement limitation. The frozen measures code CTV-4D1CCD/run-002 (SB-B3-C10) as `gold_exposed = false` (mechanical split
SEARCH_FAILURE), but the run's tool output does contain the gold's fault line: call 8 ran `nl -ba <file> | grep -n signedSums
-A100 -B30`, whose doubly numbered lines (`524-   524\t...`) the frozen display matcher does not attribute to the file. The
extended view (`analysis/traj_views/CTV-4D1CCD/run-002.max8000.txt`, line 840) shows `below = below + v;` displayed before the
submission, and both labellers describe the agent's chain as locating the NaN at that branch. Under the freeze the measure is
not changed; this run is reported with both readings (frozen: SEARCH_FAILURE; labelled: ATTRIBUTION after display). No other
run in Stage B so far is affected (all other misses have `gold_exposed = true` and `full_gold_read = true`).
W16 addendum (block 2): the same limitation affects two B4 runs, CTV-7C06F2/run-005 (SB-B4-C11) and CTV-CCA96B/run-002 (SB-B4-C10),
both frozen `gold_exposed = false`; their extended views (`analysis/traj_views/<vid>/<run>.max12000.txt`, lines 628 and 782) show
`1141-  1141\t            freq.addValue(Double.valueOf(value));` displayed in an `nl -ba | grep -n -A` window before the submission.
Across Stage B, 3 of 24 misses carry this code; all three are reported with both readings. The frozen definition is unchanged.
Block 2 blind labels (20 lens-labels over 10 misses, `labels_block2/`): CONVENTION_PRIOR 10, ENTRY_POINT_BIAS 8,
ATTRIBUTION_FAILURE 1, DISCOVERY_WITHOUT_INSPECTION 1; defensibility "partly" in 20 of 20 (the facade's own javadoc states the
NaN rule in B4, unlike B1/B3 where no method on the path stated the convention); 4 runs agreed on all fields, 6 adjudicated
(`labels_block2_adjudicated.json`).

## W17 (2026-10-15 00:15): Stage B closed

Final: 60 runs (block 1 B1+B3 40, block 2 B4 20), all answered, none contaminated, $21.91. Cells C00 15/15, C01 14/15, C10 3/15,
C11 4/15; chain effect -0.73 (Fisher p 3.4e-9), odd hop 0.00, interaction +0.13. Blind labels over 24 misses (two lenses each,
12 adjudicated): ENTRY_POINT_BIAS 17, CONVENTION_PRIOR 6, ATTRIBUTION_FAILURE 1; gold named in chain 24/24; divergence located at
the gold 22/24; defensible no 14 / partly 10 / yes 0. STAGE_B_RESULTS.md holds the tables; analysis/stageB_cells.json the numbers;
analysis/failure_modes/labels_block{1,2}_final.json the labels. Server w55 stopped 12:06Z; /private/tmp audited clean. No further
paid run is scheduled; the next design (separating hop count from cross-class dispersal, host size and the lie) is a user decision.

## W18 (2026-10-15 03:50Z): GPT-5.6 Stage B replication set up (server w56), before any GPT-5.6 Stage B call

Brief (user, 2026-10-15): run the exact Stage B design on GPT-5.6; analyse the 10 gpt-5 timeouts retrospectively. Preregistration:
`stageB-gpt56/GPT56_STAGE_B_PREREGISTRATION.md` (sha256 41ce1903b2253015..., written before this amendment's changes).
- Server `w56` added to `models/servers.json`: model `gpt-5.6`, `reasoning_effort: medium`, agent `mini-swe-agent-openai-gpt-5-6`,
  port 8862, external workspace `/private/tmp/d4jws-w6c3`, role analysis. Built with the guarded `scripts/setup_server.py`:
  server tree sha256 b62f0a2fbfed69b3 (byte-identical to w55 and mxF0); agents.json = the canonical file (c5dac96ed40c405e); the
  GPT-5.6 profile differs from w55's gpt-5.5 profile only in agent_id, model, display_name (defaults 50 / 5 / 300 s).
- FREEZE.json: w56 added to `guarded_by_server` and `models`; no guarded script changed (asserted); acceptance digest
  dcc0a1638e885d9b -> aa1f32f54aa08e64 (FREEZE amendments entry W18). Backup: `analysis/verification/backup/FREEZE.before_W18.json`.
- Re-acceptance: `plans/smoke4.json` (SELFTEST on wmDiag, gpt-5.5) frozen and run: CTV-68B9DE/run-004 valid, $0.255;
  `diagnostic/PHASE1_ACCEPTANCE.json` ALL PASS for digest aa1f32f5. (Corrected in W20: the wmDiag server, gpt-5.5, was
  started fresh for this smoke at 03:47:30Z, pid 1069, and stopped at 03:48:59Z; it had not been left running since W7, per
  `diagnostic/server_lifecycle.log`.)
- Plans: `plans/B_stageB_gpt56_block1.json` (sha256 94e481dc21f2b712...) and `..._block2.json` (e2bc07efa0fb7edc...) generated by
  `mx_plan.py` with the gpt-5.5 instance lists and seed 1014; their slot sequences, instance lists, seed and runs per instance are
  identical to `B_stageB_gpt55_block1/2.json` (asserted). Both frozen to w56.
- Cost estimate reported to the user before launch: about $11-13 for 60 runs (cap about $30; pause at $25).

## W19 (2026-10-15): Study 1, retrospective analysis of the 10 gpt-5 timeouts (no benchmark run)

Retrospective only: no gpt-5 block was rerun.

**Replays.** Three bounded next-action replays (brief section 8) were made with `scripts/gpt5_replay_next_action.py`.
- Each was one request from the exact pre-timeout state, for runs selected by a rule fixed before any call
  (`gpt5-timeouts/replays/SELECTION.md`).
- They are diagnostic only and never scored.
- Recorded usage was 62,275 prompt and 5,207 completion tokens, about $0.13 at gpt-5 list prices without cache discounts.

**Outputs** are in `gpt5-timeouts/`; `GPT5_TIMEOUT_ANALYSIS.md` is the report.

**Verdict on the ambiguity hypothesis: NOT SUPPORTED, as an explanation of why these 10 runs timed out rather than completed.**
- gpt-5's completed runs used a median of 238 s of the 300 s budget.
- **Slow serving: 6 timeouts.** These fall in a slow-serving period defined by measured speed: slots 15 to 25, 14:05 to 15:05Z on
  2026-10-13, where every measurable run ran below 50 tok/s against 69.4 before. On the six timeout instances, 6 of 6 runs in that
  period timed out, against 4 of 12 outside it.
- **Normal speed: 4 timeouts.**
  - One had committed, and the validator rejected its ranking for a duplicate method name.
  - Three spent 168 to 193 s in heavy post-gold reasoning, against 117 to 150 s for their comparators. Two of those three were also
    in malformed-command loops.
- **INCONCLUSIVE for the three.** Their behaviour is compatible with non-commitment, but whether ambiguity caused it cannot be
  tested: there is no unambiguous control and the reasoning is hidden.
- **No ambiguity behaviour seen.** The coders observed no competing-owner or convention behaviour.

**Revision.** The first version of the documents was revised the same day after two rounds of two-lens verification
(`analysis/verification/gpt5_timeout_docs_round1.json`, `gpt5_timeout_docs_round2.md`; originals in
`analysis/verification/backup/*.v1.md`). Round 2 replaced the 13:47Z window, which had been set by the first late timeout, with a
period defined by measured speed. It also read two runs of the same shape the same way. The first version had:
- an order-dependent time attribution;
- no provider-speed confound, although all 8 comparators ran before the slowdown;
- miscounts of tests, slow calls and pending requests.

**Harness interactions recorded.** Three interactions between gpt-5 and the harness are recorded. They are not changed, because the
protocol is frozen.

1. **Login-shell tests fail.** `defects4j test` run through a login shell (`bash -lc`) failed with "Failed to parse Java version"
   in all 15 such commands. The frozen classifier counts 32 test steps in all.
   - gpt-5 used this form; gpt-5.5 used it in none of its 27 held-out test commands.
   - 7 of 10 gpt-5 timeouts and 11 of 17 completed runs never had a successful test. 3 of those timeouts ran no test.
2. **Malformed commands.** gpt-5 often ended a command string with a stray `}`: 16 of 27 runs, 217 commands. Most such commands
   fail (197 of 217), but not all.
3. **Duplicate-overload rejection.** The submission validator rejects a ranking that lists two overloads of the same method (3
   gpt-5 runs). One of these is a timeout that had submitted a correct ranking.

**Effect on W4.** These interactions, and the provider's speed in the window, make W4's "operationally too weak at the frozen
budget" partly a property of the harness, of the provider on that day, and of gpt-5's command style. W4's accuracy figures are
unchanged.

**New scripts**, none of them guarded:
- `gpt5_timeline.py` (also used for the Stage B models);
- `gpt5_timeout_compare.py`, revised so after-gold medians skip the run that never reached the gold;
- `gpt5_traj_view.py`, a copy of `mx_traj_view.py` that tolerates runs without a submission;
- `gpt5_replay_next_action.py`;
- `gpt5_workload_speed.py`;
- `gpt5_timeout_facts.py`.

## W20 (2026-10-15): Study 2, Stage B re-run on GPT-5.6 (execution, result, analysis additions)

**Execution.** Plans `B_stageB_gpt56_block1` (`94e481dc…`) and `B_stageB_gpt56_block2` (`e2bc07ef…`) ran back to back on w56
through `scripts/wm_run_chain.sh` under `caffeinate`, 03:49:58 to 05:05:42Z, with freeze digest `aa1f32f5…`.
- 61 records: 60 valid, all answered, none timed out.
- One exclusion: CTV-7C06F2/run-003 (SB-B4-C11, slot 10) was classified `provider_stall` under frozen rule 2, with a request
  pending for 268.8 s after its last tool result. The slot's single replacement, run-004, was valid.
- No halt rule fired. All 67 health probes passed.
- Identity and integrity were clean in 61 of 61: response model `gpt-5.6`, effort medium, protocol identity, source integrity,
  workspace isolation and scanner all ok; contamination 0.
- Cost: $13.03 for the 61 records. The 60 valid runs cost $12.92, inside the preregistered estimate of $11 to $13 "for the 60
  runs". The total including the excluded run is $0.03 above that range and well under the $25 pause point.
- The w56 server was stopped by its recorded PID at 05:14:14Z, and `mx_tmp_audit.py` reported CLEAN.

**Result**, against `stageB-gpt56/GPT56_STAGE_B_PREREGISTRATION.md` (sha256 `41ce1903…`, unchanged since it was written).

| Cell | Acc@1 |
|---|---|
| C00 | 15/15 |
| C01 | 15/15 |
| C10 | 15/15 |
| C11 | 11/15 |

- P3: 1-hop pooled 30/30 against 5-hop + lie pooled 26/30, difference -0.13, p = 0.11.
- Classification **ATTENUATED**, at the boundary: ELIMINATED needed 27/30. No BASELINE_SHIFT.
- All 4 misses are in C11, with blind primary ENTRY_POINT_BIAS 4 of 4. In each, the gold was read in full, named in the evidence
  chain and identified as the divergence, and the facade was ranked first.
- Documents: `stageB-gpt56/GPT56_STAGE_B_RESULTS.md`, `GPT55_VS_GPT56_ANALYSIS.md`, `CROSS_MODEL_FAILURE_MODES.md`,
  `SUPERVISOR_UPDATE_STAGE_B_GPT56.md`.
- The gpt-5.5 records are unchanged. `analysis/stageB_cells.json` regenerates byte-identically (sha256 `ccea0911…`; backup in
  `analysis/verification/backup/`).

**Script changes and additions.** None of these scripts is guarded; the frozen measures and the frozen protocol are unchanged.
- `stageB_report.py` now writes `analysis/stageB_cells_<server>.json` for any server other than w55, so that the gpt-5.5 file
  cannot be overwritten. The w55 output is unchanged.
- `stageB_label_prep.py` writes non-w55 views to `analysis/traj_views_set2/`. This was recorded at setup.
- New scripts:
  - `stageB_model_compare.py`: per-cell and per-project tables, contrasts, process measures;
  - `stageB_process_extra.py`;
  - `stageB_label_compare.py`: the final-label rule as for gpt-5.5, plus the cross-model tally;
  - `stageB_lie_scan.py`: a keyword scan of the chain-cell evidence chains for each bug's lie sentence. It found 0 of 60 runs across
    both models.

**Labelling.**
- `LABEL_BRIEF.md` was unchanged.
- The labelling workflow asked one extra field, `lie_cited`. It was not asked for gpt-5.5, whose "no chain cites the lie" came from
  the rationales; the phrase scan now covers both models.
- The labellers were told neither the model nor the cell. The views carry no model identifier; this was checked by grep.

**Decision, under the preregistered rule.** ATTENUATED means the decomposition is recommended. It is proposed, not launched.
- The rule does not name a model. The documents add an interpretation, marked as such:
  - only one of the decomposition's four cells, dispersed hops with the lie, is the C10 condition, which scored 15/15 on GPT-5.6;
  - the other three cells are untested on GPT-5.6, and are expected but not shown to be near ceiling;
  - running the decomposition on gpt-5.5, if it is run at all, would show which component drives that model's -0.73 drop.
- The model choice and the go/no-go are left to the supervisor.

**Cost ledger.** `COST_LEDGER.csv` was created for this root: $64.10 recorded run cost, and about $66.25 including the estimates
for replays and the 253 health probes.

**Errata found by the round-3 numbers verification** (`analysis/verification/stageB_gpt56_docs_round3.md`):
- W18 said the wmDiag server had been left running since W7. It had not: it was started fresh for smoke4 and stopped afterwards.
  The W18 text now says so.
- `COST_LEDGER.csv` first labelled the smoke runs as GPT-5.6. The wmDiag smokes run gpt-5.5.
- The round-3 inference verification led to these corrections:
  - the lie finding is now "not cited", rather than "ignored, not rejected";
  - gpt-5's held-out losses are no longer called purely operational, because 3 of its runs are INCONCLUSIVE;
  - the comparison of wrong and correct runs now uses the same-instance runs;
  - reasoning tokens are reported as a model-level offset;
  - the labellers' blinding is now stated as weaker, because the variant patch shows each run's cell structure.

## W21 (2026-10-16): report sent to the supervisor; open questions recorded

- The report on Studies 1 and 2 was sent to the supervisor as a web page. Its Markdown copy is
  `stageB-gpt56/SUPERVISOR_REPORT_2026-10-16.md`. It supersedes `SUPERVISOR_UPDATE_STAGE_B_GPT56.md` as the letter actually sent;
  the earlier draft is kept.
- Before sending, four reviewer agents checked the report (numbers, faithfulness, readability, completeness), and a second round
  re-checked the revised page. All figures match the verified study documents. Figures computed only for the report are marked
  as such: the GPT-5.6 decomposition estimate of about $16–17, the per-project intervals, and the cost totals.
- `stageB-gpt56/SUPERVISOR_QUESTIONS_2026-10-16.md` lists the 14 questions still open for the supervisor, in English and Chinese,
  with sources. They were found by two independent sweeps of all documents and merged after a check against the sources.
  - Items 1–3 block the next paid experiment: the decomposition's go/no-go and model, its factor set, and the budget ceiling after
    the passed $40 check-in.
- No experiment was run and no frozen file was changed.

