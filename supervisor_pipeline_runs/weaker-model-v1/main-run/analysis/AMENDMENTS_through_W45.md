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

## W22 (2026-10-16): the supervisor's new KPI; existing runs re-scored; questions before the next phase

The supervisor set a new main KPI. It counts the Defects4J bug instances on which the gold method can be shifted down the
ranking. Each instance gets 5 runs, and it counts as a success if at least 1 run shifts the gold. The baseline is "just
increasing hops".

- **Re-scoring.** `scripts/kpi_shift_rescore.py` re-scores every existing instance under this KPI and writes
  `kpi-shift/kpi_rescore.json`. A run shifts the gold if it submitted a ranking without the gold first. A gold missing from the
  top 10 counts as a shift; a timeout never does.
  - The script was first written in an earlier session's scratch folder. It was copied here and re-run, and it reproduces
    `kpi_rescore.json` byte for byte.
  - Headline: on GPT-5.6, Stage B C10 succeeds on 0 of 3 bugs and C11 on 2 of 3. On gpt-5.5 both succeed on 3 of 3. The
    September hops-only chains with no extra feature shifted in 0 of 44 runs.
- **Open questions.** `kpi-shift/KPI_PHASE_QUESTIONS_2026-10-16.md` lists 7 questions (EN/中文), each with a proposed default,
  and 3 statements. They cover:
  - what an instance is;
  - which approach and baseline arms to run;
  - the scoring rule;
  - whether the KPI is a count or a rate;
  - which model gives the headline result;
  - the scope, a pilot and the budget;
  - how to build instances at scale.
- **The plan file.** The project memory had said a plan existed at `kpi-shift/KPI_PLAN.md`. It does not; this question file is
  the current record.
- Nothing has been built or run for this phase.


## W23 (2026-10-16): main run started on the supervisor's decisions

**Supervisor decisions (Hong Jin, 16 Oct, relayed by the student).**
- An instance is a real Defects4J bug identity, such as Chart-1, into which a synthetic fault is injected.
- Baselines, hops-only arms, lie on/off arms and the decomposition are not prioritised now.
- KPI: a run counts as a shift whenever the gold is not ranked first. The aim is a count to maximise.
- gpt-5.5 is the primary model.
- Construction methodology is left to the student.

**Plan.** `main-run/MAIN_RUN_PLAN.md`. The verified Stage B **C10** recipe is transferred unchanged: a facade that delegates to five
hops in five drawn host classes of at least 1500 lines, a facade lie, a quiet omission in the hop-5 gold, an existing trigger, and
the same frozen protocol on w55. C10 was chosen over C11 because on gpt-5.5 both shifted 3 of 3 bugs and the odd hop added nothing.

**Candidate pool.** `scripts/mr_candidate_pool.py` writes `main-run/DEFECTS4J_CANDIDATE_POOL.csv`. Of the 854 active bugs, read at
their fixed revisions, 91 are eligible: Lang 41, Closure 25, Math 17, JacksonCore 6 and Chart 2.

**New scripts.** None of them is guarded; they copy the Stage B builders, each change marked MR:
- `mr_lib.py`: per-instance fixtures `construction/fresh-mr/<key>`, real-directory copies of the harness's own `<key>/fixed`
  checkouts, and the per-instance seed;
- `mr_spec.py`, `mr_validate.py`, `mr_harness_check.py`, `mr_package.py` and `mr_key.py`.

No guarded script or server file changed. The frozen freeze library and scanner already take `bug_id` and `fresh` from the key.

**Smoke test.** Stage B's B1 design, re-targeted to the Lang-1 fixture, reached READY on all 16 gates. The record is in
`main-run/smoke/`, and the smoke spec and instance were deleted.

**Batch 1.** Eight instances, each with an existing harness checkout: Chart-2, Lang-22, Lang-39, Lang-14, Lang-45, Lang-1,
Lang-16 and Math-3. Each has its own target and none uses a Stage B target. Every instance is built by one builder agent
(`construction/mainrun/BUILD_BRIEF.md`) and audited by one independent auditor agent (`construction/mainrun/AUDIT_BRIEF.md`).

**Costs.** The estimated run cost is about $18-19 for 40 gpt-5.5 runs. Construction has no OpenAI spend.

## W24 (2026-10-16): main-run batch 1 built, audited, packaged, frozen and launched

**Construction.** Workflow run `wf_11ef36ee-753` had 16 agents: 8 builders and 8 independent auditors, with 0 errors. Results are
in `main-run/batch1_build_audit_results.json`; the records are `main-run/INSTANCE_BUILD_LOG.csv` and
`main-run/INSTANCE_PROVENANCE.csv`, both written by the new unguarded `scripts/mr_build_records.py`.
- All 8 candidates are **ACCEPTED**: READY on 16/16 gates, and each audit CONFIRMED with flags consistent with that verdict. Each
  validation's `spec_sha256` matches its spec.
- No instance was REJECTED, FLAGGED or UNBUILDABLE.
- Every facade is in the class the real bug modified.
- Lang-16 was redesigned once, before its audit and before any run. Its first design omitted `largest = array[i];` and also
  validated READY. The builder then found a one-line hop-3 edit that used the gold's start-index answer as an oracle and passed the
  trigger, so the fault was moved to `index = i;`.

**Lang-1 bypass reviewed.** The builder reported a hop-4 edit that passes the trigger and the full suite. The edit adds a
"1"+24-zeros prefix, so every run takes the gold's BigInteger branch. The auditor classified it as a bypass: after the edit the gold
still returns null for "12345", against its own `@return ... not null`, and the edit is not consistent with the hop docs. The
coordinator agrees. The instance stays ACCEPTED, and the bypass is recorded in the audit.

**Packaging.** `mr_package.py` then `mr_key.py`: Chart-2 CTV-98E197, Lang-22 CTV-1BD08F, Lang-39 CTV-B0C638, Lang-14 CTV-8585FF,
Lang-45 CTV-82A991, Lang-1 CTV-6D85AB, Lang-16 CTV-231992 and Math-3 CTV-BEAA42.
- Each variant is under `new_bug_variants/<P>/bug-<id>/L20/`.
- `review/VARIANT_KEY.json` grew from 30 to 38 entries, and the 30 earlier entries are byte-identical (asserted).
- The w55 server discovered all 8 variants with their own bug ids.

**Plan and freeze.**
- `plans/MR_batch1_gpt55.json` (sha256 `e0173d81…`): `mx_plan.py`, seed 20261016, 5 runs per instance in seeded rounds, 40 slots.
- `mx_freeze.py --add-plan` bound it to w55. The acceptance digest is unchanged (`aa1f32f5…`), and FREEZE.json has sha256
  `9a0d399f…`. Backup: `analysis/verification/backup/FREEZE.before_W24.json`.
- `mx_tmp_audit.py` reported CLEAN, and `ct_driver.py --verify-only` passed.

**Launch.** w55 (gpt-5.5, medium) was started at 12:40Z with pid 87732. `wm_run_chain.sh w55 MR_batch1` began at 12:40:33Z under
`caffeinate`.

## W25 (2026-10-16): main-run batch 1 contamination stop at slot 36 (Lang-39 run-005); continuation

**What happened.** Slot 36 was MR-Lang-39, round 5 (CTV-B0C638/run-005). The run submitted a ranking with the gold at rank 2, and
the frozen scanner then stopped it with `call 17: harness marker, experiment name or repository-tree path in the output`. The
driver halted at 13:34:54Z, before slots 37 to 39.

**Cause.** At call 17 the agent ran, inside its own workspace:

    defects4j info -p Lang -b 1 2>/dev/null | head -50 || true && defects4j export -p classes.modified ... && defects4j export -p dir.src.classes

`defects4j info` prints the tool's configuration: the base dir, `major/`, `project_repos/` and `framework/projects/Lang/...`.
These are paths inside the Defects4J repository tree outside `framework/`, which the pre-registered NARROW rule treats as
contamination.
- The output showed no other variant, no gold label, no manifest and no answer.
- The `-b 1` summary describes real Lang bug 1, not this instance's synthetic fault.
- This is the first `defects4j info` call in the 254 trajectories of this root.

The stop is a true positive of the rule as written. It is not a scanner false positive, and the scanner is not changed.

**Disposition.** This follows the frozen rule and W7: a contamination stop is never released.
- CTV-B0C638/run-005 stays **excluded**, and its gold rank 2 is **not counted** toward the KPI. The KPI report lists it separately.
- The slot gets its single replacement in `plans/MR_batch1_gpt55_cont.json` (sha256 `85d7f50e…`). That plan holds slots 36 to 39
  in the original order, with slot 36 as the replacement. It is frozen to w55, and FREEZE.json now has sha256 `ac2d46ea…`; the
  acceptance digest is unchanged. `mx_tmp_audit` reported CLEAN and `--verify-only` passed.
- The replacement was launched on the same w55 server (pid 87732).

## W26 (2026-10-16): main-run batch 1 result; batch 2 decision and a construction preference

**Batch 1 result.** The run ended at 13:41:32Z. Records: 41, of which 40 are valid and 1 is excluded (W25).
- Every valid run answered, with no timeouts and no provider stalls.
- w55 (pid 87732) was stopped by its recorded PID, and `mx_tmp_audit` reported CLEAN.
- `mx_metrics.py` regenerated `analysis/per_run.json`: the 213 earlier rows are byte-identical and 41 MAIN_RUN rows were added.
- **KPI: 8 validated instances tested; 7 with at least one shift; 21/40 answered runs shifted.**
  - Per project: Chart 1/1, Lang 5/6, Math 1/1.
  - Per instance: Lang-14 5/5, Lang-45 5/5, Math-3 5/5, Chart-2 3/5, Lang-1 1/5, Lang-16 1/5, Lang-22 1/5, Lang-39 0/5.
- All 21 shifts are ENTRY_POINT_BIAS. The facade was ranked first, with the gold displayed, read in full and a test run. The gold
  came 2nd in 17 runs, 3rd in 3 and 4th in 1.
- The report checks against the driver ledger with 0 mismatches on the valid runs.

**Scripts and outputs.** The report comes from the new unguarded `scripts/mr_report.py`. Outputs:
- results: `main-run/MAIN_RUN_RUNS.csv`, `MAIN_RUN_RESULTS.csv`, `SHIFTED_INSTANCES.md`, `FAILED_TO_TRANSFER.md`;
- cost and summary: `main-run/COST_LEDGER.csv`, `main-run/analysis/main_run_summary.json`;
- the progress update: `main-run/SUPERVISOR_PROGRESS_UPDATE.md`.

**Cost.** Runs cost $17.40 (valid $16.85, excluded $0.553), and the 45 probes cost about $0.36 (estimate). The root
`COST_LEDGER.csv` totals are now $81.50 recorded and $84.01 including estimates.

**Diagnosis.** This is a hypothesis drawn from 8 instances and is not tested; it is recorded in `main-run/analysis/diagnosis_notes.json`.
- Shifts concentrate where the omitted step is a special case: a NaN skip, a surrogate-pair check or a word-state reset. Without
  that step the gold still reads as a complete routine.
- Shifts are rare where the omission leaves a visibly broken idiom: a copy index that never advances, an argmax index never
  recorded, a null result on the ordinary path, or a bound stated in the gold's own javadoc.
- No completed instance is changed.

**Batch 2 decision.** Transfer is good (7/8), so batch 2 proceeds under the plan rule: the next candidates by pool rank, with
distinct targets.
- The candidates are the 15 eligible bugs that already have a harness checkout, so the shared workspace store does not change:
  - Lang 30, 15, 7, 5, 26, 63, 32, 11;
  - Chart 11; Math 10, 1;
  - JacksonCore 11, 5, 16;
  - Closure 10.
- The candidate list is `main-run/batch2_tasks.json`. Facades already used, by a main-run instance or by Stage B, are excluded
  from each candidate's allowed targets.

**Construction preference added** to `construction/mainrun/BUILD_BRIEF.md`, from batch 2 on.
- Builders should prefer omitted special-case steps over omissions that leave a visibly broken idiom.
- This is a preference among valid designs only. The gates, the audit, the KPI and the protocol are unchanged.
- Results are reported per batch, so the effect of the change stays visible.
- Construction runs as 4 independent lanes, each a build followed by an audit, so at most 4 heavy jobs run at once.
- No construction runs while paid runs execute, because of CPU contention with the agents' 300 s budget.

**Cost check.** Batch 2 is estimated at about $33–35 for 75 runs (batch-1 mean $0.42 per run, plus replacements and probes),
which takes the experiment to about $118 including estimates.
- The discussed range is read as the KPI-questions default of 16 Oct: $34–84 of new spend for 12–30 instances, about $148
  cumulative. Batch 2 stays inside it, with 23 instances in total.
- A batch 3 would exceed it, so the work stops and is reported before any batch 3.

## W27 (2026-10-16): main-run batch 2 built, audited, packaged, frozen and launched

**Construction.** Workflow `wf_876879ce-878` ran 25 agents: 15 builders and 10 auditors, in 4 sequential lanes, with 0 errors.
Results are in `main-run/batch2_build_audit_results.json`.
- A first launch, `wk5vbpxcw`, received task records without `allowed_targets`. It was stopped within seconds, before any file was
  written, and relaunched with the full records. The script now refuses incomplete records.

**Yield: 10 of 15 ACCEPTED and 5 UNBUILDABLE.**
- **ACCEPTED** (READY on 16/16 gates, audit CONFIRMED with consistent flags, spec hashes matching): Lang-30, Chart-11, Lang-15,
  Lang-7, Lang-26, Lang-63, JacksonCore-5, Lang-32, Lang-11 and Closure-10. Each records its bypasses. Lang-63, Lang-26 and Lang-7
  were each redesigned once before READY.
- **UNBUILDABLE**, under brief step 7. No spec or instance files were left.
  - Lang-5: no omission is both quiet and single-owner and caught by exactly one test.
  - Math-10: no omission in DSCompiler.getCompiler is caught by exactly one test.
  - JacksonCore-16: only two tests reach the facade, and the flattening code is out of reach of every host.
  - JacksonCore-11: the facade is a clock-seeded fold, so no test can fail deterministically.
  - Math-1: every Fraction passes through the public constructor's own reduction, so the single-owner rule cannot be met.

**Fault types.** 9 of the 10 builders chose a special-case step:
- a null skip (Lang-30); a reserved-word exclusion (Closure-10);
- a transient skip (Lang-32); an unbound-variable skip (Lang-15);
- a NaN check (Lang-7); a milliseconds-width rule (Lang-63);
- an escape rule (JacksonCore-5); a segment-type case (Chart-11);
- a digits-only branch (Lang-11).

Lang-26 omits a cache-key component, which the builder records as not the preferred type: it was the only valid omission.

**Trigger caveat.** Lang-11's trigger asserts properties of random strings. On the variant, a digits-only request returns
arbitrary characters, so the trigger fails except with negligible probability. Gate G3 passed.

**Packaging.**

| Instance | Variant id |
|---|---|
| Lang-30 | CTV-20F7D7 |
| Chart-11 | CTV-2A4DC9 |
| Lang-15 | CTV-53F50C |
| Lang-7 | CTV-15AAB2 |
| Lang-26 | CTV-F7BE03 |
| Lang-63 | CTV-DF94AB |
| JacksonCore-5 | CTV-348591 |
| Lang-32 | CTV-AA3A2F |
| Lang-11 | CTV-FCF3C0 |
| Closure-10 | CTV-08A12C |

`review/VARIANT_KEY.json` grew from 38 to 48 entries, with the earlier entries unchanged. `INSTANCE_BUILD_LOG.csv` (23 rows) and
`INSTANCE_PROVENANCE.csv` (18 rows) were regenerated.

**Plan, freeze and launch.**
- `plans/MR_batch2_gpt55.json` (sha256 `a93379cb…`, seed 20261017, 50 slots) is frozen to w55.
- FREEZE.json now has sha256 `14079085…`; the acceptance digest is unchanged. Backup: `FREEZE.before_W27.json`.
- `mx_tmp_audit` reported CLEAN and `--verify-only` passed.
- w55 was started with pid 28564 and discovered all 10 variants with their own bug ids. The chain started at about 15:08Z.

**Cost.** The estimate is about $21–23 for 50 runs, taking the experiment to about $106 including estimates. The total is then
18 instances, inside the range in W26.

## W28 (2026-10-17): main-run batch 2 result; refined hypothesis; stop before batch 3

**Execution.** `plans/MR_batch2_gpt55.json` ran from about 15:08Z to 16:17:59Z.
- Records: 50, all valid and answered. There were no exclusions, no timeouts and no halts.
- w55 (pid 28564) was stopped by its recorded PID, and `mx_tmp_audit` reported CLEAN.
- `mx_metrics.py` added 50 rows; the 254 earlier rows are byte-identical.

**Result.**
- **Batch 2:** 10 validated instances tested; 5 with at least one shift; 17/50 runs shifted.
  - Closure-10 5/5, Lang-7 5/5, Lang-30 3/5, Lang-63 3/5, Lang-15 1/5.
  - 0/5: Chart-11, JacksonCore-5, Lang-11, Lang-26, Lang-32.
- **Cumulative:** 18 tested; 12 with at least one shift; 38/90 runs shifted.
- **Failure modes:** 37 of the 38 shifts are ENTRY_POINT_BIAS. Three of these list the call chain top-down, with the gold 6th. One is
  GOLD_NOT_REACHED (Closure-10 run-003).

**Cost.** Batch 2 cost $21.01 for runs and about $0.42 for probes. The experiment total is $102.51 recorded and $105.44 including
estimates.

**Fixes.** `scripts/mr_report.py` now:
- labels the construction row of each batch with the actual counts of builders, auditors and unbuildable candidates (it had a
  fixed "8 + 8" label);
- appends the per-batch diagnosis notes.

**Refined hypothesis.** This was made after seeing the results and is recorded in `main-run/analysis/diagnosis_notes.json`.
- The W26 preference for special-case omissions did not raise the yield.
- An instance shifts when the omission leaves **no local trace** in the gold. A local trace is any of:
  - an unused or never-updated parameter or variable;
  - a missing sibling case in a visible enumeration;
  - a rule stated in the gold's own javadoc.
- On that reading, 9/9 no-trace instances shifted, against 3/9 traced instances (each at 1/5).
- This must be tested on instances built before any of them is run.

**Stop.** As stated to the user after batch 1, work stops and is reported before a batch 3.
- The premise of that statement no longer holds: batch 2 validated 10, not 15, so a batch 3 of up to 12 instances (about $25–27,
  about $131 cumulative) would stay inside the range.
- Batch 3 would need about 15 new harness checkouts in the shared workspace store. Only Math-5 among the remaining eligible bugs
  has one.
- The proposal, with candidates and a "no local trace" construction checklist, is in `main-run/SUPERVISOR_PROGRESS_UPDATE.md`.
- No batch 3 work has started.

## W29 (2026-10-17): batch 3 authorised; "no local trace" rule pre-specified and frozen; W28 corrected

**Authorisation.** The user wrote on 17 October:

> "Go ahead with Batch 3. Use the 'no local trace' checklist as a pre-specified construction rule before any new behavioural runs.
> You may create the required new Defects4J checkouts. Keep the total spend below approximately $148 and stop before exceeding
> that ceiling. Do not modify any completed Batch 1 or Batch 2 instances or results."

**Correction to W28 and progress update 2.** W28's local-trace reading had three items. Item (3) was "a rule stated in the gold's
own javadoc", and it was applied inconsistently.
- Math-3's gold says "the sum of the finite entries" yet adds NaN. Under item (3) it is therefore traced, and it shifted 5/5.
- Lang-14's gold checks that the second surrogate exists but never compares it, a visibly incomplete pair. It also shifted 5/5.
- The "9/9 against 3/9" split stated in W28 was therefore cleaner than the data supports.

The frozen checklist below is applied blind to the 18 golds, and its classification replaces the coordinator's in reporting.

**The frozen rule.** `construction/mainrun/NO_LOCAL_TRACE_CHECKLIST.md` (sha256 `487a966a…`) states the user-approved rule as four
items, a closure rule and quote-based application:

| Item | Meaning |
|---|---|
| T1 | an input whose value cannot matter |
| T2 | a dead or frozen local, or a dead decision |
| T3 | a visibly incomplete closed set |
| T4 | the gold's own text contradicts its code |

Before freezing, two rounds of independent review (`wf_717b7862-f23`, `wf_6dd27063-878`) found the following, and all of it was
fixed:
- **Round 1.** T4 could not be applied blind; T3 contradicted itself (infinite vs NaN); frozen flags and dead branches had no
  coverage; the "doubt counts as a trace" rule had no quote behind it.
- **Round 2.** Loop bounds could be misread as frozen counts.
- **Minor gaps:** argument checks, caller preconditions, the closure of float special values, and the T1 headline.

**Frozen files.** Every batch-3 rule, brief, script and manifest is hashed in `main-run/analysis/batch3_frozen_hashes.json`
(sha256 `8efeb6ec…`). Among them:
- `TRACE_CHECK_BRIEF.md`, `BUILD_BRIEF.md` (batch-3 rule bullets, the redesign archive, allowed facades) and `AUDIT_BRIEF.md`
  (unchanged);
- `main-run/BATCH3_PREREGISTRATION.md` (`c4f6c94d…`) and `main-run/batch3_tasks.json` (21 candidates);
- the new unguarded scripts `mr_cost_guard.py`, `mr_integrity.py` and `mr_gold_text.py`;
- the revised `mr_build_records.py` (batch-3 statuses from `batch3_dispositions.json`) and `mr_report.py` (every `probe:` line
  counted).

**Pre-registration.**
- **Pipeline.** A builder, then an auditor and a blind trace checker in parallel, then one redesign on REJECTED or TRACE, checked
  by a new auditor and a new checker.
- **Dispositions.** The table is applied top to bottom. A missing verdict is asked for once more, then counts as REJECTED or TRACE.
- **Runs.** Runs start only after every candidate has a final disposition, recorded by amendment.
- **Cost guard.** k is the largest value ≤ 5 with C + 10k·M + (120k + 12)·$0.008 ≤ $147. This is the frozen driver's true worst
  case: at most 2 runs per slot, and 3-probe gates with up to 5 resetting failures. At registration C = $105.437, M = $0.6595 and
  k = 5; about 16 instances are expected, ending near $140.
- **Prediction.**

| Condition | Reading |
|---|---|
| n ≥ 5 and s ≥ 4/5 | SUPPORTED |
| n ≥ 5 and s ≤ 2/3 | NOT SUPPORTED |
| otherwise | INCONCLUSIVE |

- **Retrospective.** Three blind raters rate the 18 golds, one per session, under shuffled labels. The retrospective set's sha256
  is `71b44fa3…`; its label map is `0806a199…`, kept outside the repository until all 54 verdicts are in.

**Checkouts.** 20 new `defects4j checkout` fixed versions were added to the shared workspace store, each at its
`D4J_<P>_<id>_FIXED_VERSION` tag (`main-run/batch3_checkouts.log`). Each went into a new directory, and nothing existing was
touched. Math-5 already had a checkout. All 21 batch-3 fixtures were created.

**Protection of batches 1 and 2.**
- `mr_integrity.py --record` wrote `main-run/analysis/b12_integrity_manifest.json`: 551 entries, sha256 `de51e509…`.
- A full regeneration (`mr_key`, `mr_build_records`, `mx_metrics`, `mr_report`) followed by `--verify` gave 0 mismatches.
- The key preflight passed: no batch-3 key has an existing design, spec, instance or audit.

## W30 (2026-10-17): batch-3 dispositions recorded before any batch-3 run; retrospective blind classification

**Construction.** Workflow `wf_f6d6f335-440` ran 70 agents with 0 errors. The pre-registered pipeline was: builder, then an
auditor and a blind trace checker in parallel, then at most one redesign, followed by a new auditor and a new checker. The
pre-registered disposition table was then applied. Results are in `main-run/batch3_build_audit_results.json`.

**Outcome: 17 ACCEPTED, 4 UNBUILDABLE, 0 REJECTED, 0 FLAGGED.**
- **Redesigns.** 5 of the 17 were redesigned once, before any run, then re-validated, re-audited and re-checked by new agents. The
  first versions are archived in `construction/mainrun/history/<key>/v1/`.
  - The trace checker returned TRACE on 4 first versions: Lang-58 (T3), Lang-35 (T3), Lang-37 (T3) and Lang-51 (T4).
  - The audit REJECTED 1 first version: Lang-40.
  - All 5 redesigned versions are CONFIRMED and NO_TRACE.
- **The other 12** passed both checks on their first version.
- **UNBUILDABLE**, under brief step 7. The builders' reasons are in the build log.
  - Lang-3: createBigDecimal has no per-element core.
  - Lang-54: under JDK 11's locales the facade tests catch no single omission.
  - Math-16: none of log1p, cos or min can carry the recipe validly.
  - Math-5: Complex.valueOf has nothing to split.

**Verification (17/17):**
- READY on 16/16 gates, with each validation's `spec_sha256` equal to its spec;
- audit CONFIRMED with consistent flags;
- facade within its pre-registered allowed targets;
- trigger an existing test;
- `mr_gold_text.py` extracts each final gold.

**Authoritative records.**
- `main-run/analysis/batch3_dispositions.json` (sha256 `af8cc6ebf0e21f2b…`).
- `main-run/analysis/trace_checks_batch3.json` (sha256 `ac02dd0edb63a11d…`).

**Accepted instances, in run order (pool rank):**

| Pool rank | Instance | Variant | Redesigned | Spec sha256 |
|---|---|---|---|---|
| 3 | Lang-44 | CTV-F32718 | no | `3829868b25458ac2…` |
| 4 | Lang-58 | CTV-D3713D | yes | `8aa2276fd0646ca0…` |
| 7 | Lang-49 | CTV-72676E | no | `b336af79cce09e53…` |
| 13 | Lang-31 | CTV-B554D1 | no | `dec41ccb9271e5df…` |
| 14 | Lang-40 | CTV-6DA575 | yes | `7960471173ba851b…` |
| 15 | Lang-35 | CTV-3079A3 | yes | `633241d373e1c2f0…` |
| 16 | Lang-37 | CTV-7BC427 | yes | `810655dc085495b3…` |
| 19 | Lang-20 | CTV-79C97A | no | `d21623bde47c84d3…` |
| 20 | Lang-51 | CTV-16D9F2 | yes | `3f0e7e57e889d6ce…` |
| 21 | Lang-57 | CTV-031745 | no | `43bfc419069ac92b…` |
| 24 | Lang-33 | CTV-C91805 | no | `34462a8e1eaa4682…` |
| 25 | Lang-41 | CTV-F9228F | no | `2a17ee8af9dfc90d…` |
| 30 | Math-15 | CTV-623585 | no | `aead26c76bdece63…` |
| 33 | Lang-46 | CTV-0706ED | no | `b428353a13a385c2…` |
| 34 | Lang-53 | CTV-CA37FA | no | `22a54bf6d32da72f…` |
| 35 | Lang-65 | CTV-2947EF | no | `1f1d1f8e444ddf69…` |
| 37 | Math-55 | CTV-462BE6 | no | `59172e6c03bf1edc…` |

**Tooling fix (pre-run, reporting only).** `scripts/mr_build_records.py` could not read the batch-3 results format (one entry per
version), and it read the dispositions file one level too high. Both were fixed. The script now has sha256 `7e2b1a1d2efb1abb…`; its W29
hash `f7d481e5…` is superseded. No scoring or disposition logic changed. Batch-3 build-log statuses come from the dispositions
file.

**Packaging and integrity.**
- `review/VARIANT_KEY.json` grew from 48 to 65 entries. All 30 pre-main-run entries and all 18 batch-1/2 entries are unchanged.
- `mr_integrity.py --verify` gives 551 entries and 0 mismatches.

**Retrospective blind classification** (pre-registered; descriptive only). It is in
`main-run/analysis/retro_trace_classification.json` (sha256 `5dd68454c9fbbfbc…`). Workflow `wf_8d1cf058-320` ran 54 single-gold sessions
under shuffled labels; the label map was joined only after all 54 verdicts were in. 17 of the 18 golds were unanimous.

| Majority verdict | Instances | With at least one shift | Shifted runs |
|---|---|---|---|
| NO_TRACE | 5 | 5 | 19/25 |
| TRACE | 13 | 7 | 19/65 |

- All 6 instances that never shifted are TRACE.
- The strict rule also classes three 5/5 instances as TRACE: Lang-14 (T3), Math-3 (T3, T4) and Lang-45 (T2, T4).
- The rule's examples were drawn from these golds, so this result does not test the hypothesis.

## W31 (2026-10-17): batch-3 block 1 launched; trace-check robustness; secondary sensitivity analysis fixed before any batch-3 outcome was read

**Block 1 launch.**
- The cost guard (`mr_cost_guard.py --left 17`) gave C = $105.437, M = $0.6595 and k = 5, with a worst case of $143.31.
- `plans/MR_batch3_block1_gpt55.json` (sha256 `8c10ed7b…`, seed 202610171, 25 slots) covers Lang-44, Lang-58, Lang-49, Lang-31
  and Lang-40. It is frozen to w55; FREEZE.json now has sha256 `0de07abe…`, and the acceptance digest is unchanged.
- **Temp leftover.** `mx_tmp_audit` first found one leftover: `/private/tmp/mxm-k2vvzwna`, an empty marker directory (0 files)
  that `mr_validate.py` had created during batch-3 construction. It was removed, the audit then reported CLEAN, and
  `--verify-only` passed.
- w55 started with pid 4449 and discovered all 5 variants. The chain started at about 09:45Z.

**Trace-check robustness** (not pre-registered, and not a decision input). Two more blind raters per accepted gold, 34 sessions
(`wf_7b9ffc93-c20`), rated under shuffled labels. Results: `main-run/analysis/batch3_trace_robustness.json` (sha256 `b144baf7a86550f0…`).

| Group | Instances | Count |
|---|---|---|
| Both extra raters agree with the authoritative NO_TRACE | 13 | 13 |
| 2 of 3 raters NO_TRACE | Lang-44 (one extra rater: T4); Lang-49 (one extra rater: T3) | 2 |
| Both extra raters TRACE | Lang-46 (T3, T3); Lang-65 (T4, T2) | 2 |

Under the pre-registration the single blind checker is authoritative, so no disposition changes.

**Secondary sensitivity analysis**, fixed now, before any batch-3 run outcome has been read. The driver log was not inspected;
only the count of finished slots was. Besides the pre-registered s on n, s is also reported on two subsets of n, with the same
thresholds:

- (a) instances whose majority of 3 raters (the checker plus the 2 extra raters) is NO_TRACE, which drops Lang-46 and Lang-65;
- (b) instances where all 3 raters say NO_TRACE, which also drops Lang-44 and Lang-49.

These are reported as robustness only. The pre-registered reading stays the primary result.

## W32 (2026-10-17): batch 3 executed; pre-registered prediction SUPPORTED; final spend below the ceiling

**Execution.** Seven blocks ran on w55, from about 09:45Z to 11:35:58Z on 17 October. Before each block,
`mr_cost_guard.py` was run, then the plan was frozen, then `mx_tmp_audit` (CLEAN) and `--verify-only` passed.

| Block | Instances | Slots | Guard k | C before block |
|---|---|---|---|---|
| 1 | Lang-44, Lang-58, Lang-49, Lang-31, Lang-40 | 25 | 5 | $105.44 |
| 2 | Lang-35, Lang-37, Lang-20, Lang-51 | 20 | 4 | $114.82 |
| 3 | Lang-57, Lang-33, Lang-41 | 15 | 3 | $121.84 |
| 4 | Math-15, Lang-46 | 10 | 2 | $127.66 |
| 5 | Lang-53 | 5 | 1 | $131.92 |
| 6 | Lang-65 | 5 | 1 | $134.18 |
| 7 | Math-55 | 5 | 1 | $135.50 |

- **Records:** 85, all valid. No exclusions, no replacements, no halts, no timeouts.
- **Integrity:** every response came from model gpt-5.5 at medium effort; contamination 0; the scanner passed every run.
- **Reconciliation:** the gold ranks match the driver ledger on all 85 runs.
- **Server:** w55 (pid 4449) was stopped by its recorded PID, and `mx_tmp_audit` reported CLEAN.
- **Coverage:** all 17 ACCEPTED instances ran, so none was built but not run.
- **Batches 1 and 2:** `mr_integrity.py --verify` gave 0 mismatches after every block and at the end.

**Cost.**
- Batch-3 runs cost $30.84 for 85 records. The highest single run was $0.616, below M = $0.6595. About $0.79 went on the 99
  probes.
- **The experiment total is $133.35 recorded and $137.07 including estimates (guard C = $137.07), below the $148 ceiling.**
- After block 7, k = 0 with no instances left.

**Pre-registered result** (`scripts/mr_batch3_eval.py`, `main-run/analysis/batch3_prediction.json`, sha256 `422dab717d4965d6…`).

| Set | n | With at least one shift | s | Reading |
|---|---|---|---|---|
| **Primary** | 17 | 15 | 0.882 | **SUPPORTED** (threshold 4/5) |
| Secondary (a): majority of 3 raters NO_TRACE | 15 | 14 | 0.933 | SUPPORTED |
| Secondary (b): all 3 raters NO_TRACE | 13 | 12 | 0.923 | SUPPORTED |

- **Primary detail.** 61/85 runs shifted (72%). The two instances without a shift are Math-15 and Lang-65.
- **All 61 shifts are ENTRY_POINT_BIAS** (the facade ranked first). The gold came 2nd in 54 runs, 3rd in 1, 4th in 2 and 6th in 4.

Diagnoses are in `diagnosis_notes.json`.
- **Lang-65.** Its gold reuses one ParsePosition after `setIndex(0)` was omitted, a well-known pitfall. Both extra raters had
  flagged it as a trace.
- **Math-15.** Its trigger is an accuracy failure, and the gold is the only method on the chain that approximates.

**Caveat.** Batch 3 differs from batches 1–2 in its bugs, in its Lang versions and in its construction pipeline, and there is no
control arm. This is therefore a prospective consistency check of the no-local-trace hypothesis, not a causal test.

**Cumulative KPI: 35 validated instances tested; 27 with at least one shift; 99/175 answered runs shifted.**

| Project | Instances tested | With at least one shift |
|---|---|---|
| Lang | 28 | 23 |
| Chart | 2 | 1 |
| Math | 3 | 2 |
| Closure | 1 | 1 |
| JacksonCore | 1 | 0 |

**Reporting fix.** The batch-3 construction row in `main-run/COST_LEDGER.csv` now counts 21 builders, 5 redesigns, 22 audits and
22 trace checks. Only the label changed (`mr_report.py`).

## W33 (2026-10-17): erratum to W32; progress update 3 verified

**Erratum to W32.** W32 says "All 61 shifts are ENTRY_POINT_BIAS". The correct statement is: all 61 batch-3 shifts ranked the
facade first. Of these, 58 are ENTRY_POINT_BIAS, and 3 are GOLD_NOT_REACHED because the frozen display matcher found no display of
the gold's fault line: Lang-41 run-003, Lang-41 run-004 and Lang-58 run-004.

Across all batches, all 99 shifts ranked the facade first: 95 ENTRY_POINT_BIAS and 4 GOLD_NOT_REACHED. W16 records that this
matcher misses some real displays.

**Verification of `main-run/SUPERVISOR_PROGRESS_UPDATE.md` (update 3).** Two independent verifiers checked it (`wf_f930a05c-c9e`).
- The numbers lens recomputed 111 claims and found 0 errors.
- The process lens found 7 errors, all fixed in the update:
  1. Only the 17 READY candidates were audited and trace-checked, in parallel, and redesigns were re-checked by new agents.
  2. The unbuildable reasons understated that the rule itself excluded candidates, a selection effect.
  3. The retrospective table lacked its non-independence caveat.
  4. The cost guard prices runs at the highest observed run cost, so it is not a driver-enforced bound.
  5. "Never displayed" should name the frozen matcher's limitation.
  6. T4's description was narrower than the frozen rule.
  7. The two non-shifting diagnoses are post-hoc readings.

## W34 (2026-10-19): batch 4 authorised (ceiling $200 total), pre-registered, reviewed and frozen

**Authorisation.** The user wrote on 19 October that Hong Jin confirmed the next step:

> "continue expanding the gpt-5.5 study … same frozen main-run methodology and the preregistered no-local-trace construction rule
> … Keep the current scoring unchanged … Do not switch to GPT-5.6 yet, and do not introduce a new baseline or redesign the
> completed batches … cost-controlled batches, preserve all provenance/integrity checks, and stop to report before exceeding the
> new budget ceiling I provide."

The message gave no figure, so the coordinator asked. The user chose **"$200 total"** of cumulative experiment spend, including
estimates.

**Pre-registration.** `main-run/BATCH4_PREREGISTRATION.md` (sha256 `7b630cb0…`) inherits `BATCH3_PREREGISTRATION.md` in full,
except as follows.

**Candidates.** There are 24, in `main-run/batch4_tasks.json`. Facade targets were allocated by maximum bipartite matching in
pool-rank priority, distinct from every earlier facade (main-run or Stage B) and from each other.
- 23 eligible bugs have no distinct target left and are not attempted. With batch 4 the current eligible pool is exhausted, and
  widening it needs the user's approval.

**Cost guard.** `mr_cost_guard.py --cap 199`. At registration: C = $137.0675, M = $0.6595, k = 5, worst case $174.94.

**Reading.** A secondary replication reading uses batch 3's thresholds (REPLICATES / DOES NOT REPLICATE), with a per-project
breakdown. Robustness raters are pre-registered as secondary.

**Disclosed changes to batch-3 files.**
- **BUILD_BRIEF.md** (`42f3a20a…` → `cc565d61…`): one line, so that the facade rule also points at the batch-4 pre-registration.
  Reverting that line in a copy reproduces `42f3a20a…` exactly. Its "(batch 3)" labels on the redesign and archive rules apply to
  batch 4, and builders are told so in their task text.
- **Scripts:**
  - `mr_cost_guard.py`: `--cap`, plus a ledger-set refusal;
  - `mr_integrity.py`: `--batches`, `--manifest`, and `--verify-frozen` with prefix checks;
  - `mr_build_records.py`: reads each batch's dispositions file;
  - `mr_batch3_eval.py`: `--batch`, batch-4 labels and per-project output for batch 4 only;
  - `mr_report.py`: batch-4 notes from their own file, restricted to batch-4 keys.

**Defaults reproduce the earlier output.**
- `batch3_prediction.json` is byte-identical (`422dab71…`, as in W32).
- The batch-1/2 manifest gives 551 entries and 0 mismatches.
- **Incident, corrected.** An interim per-project change briefly rewrote `batch3_prediction.json`. It was restored from the
  pre-change copy and its hash re-confirmed, and the per-project output is now limited to batch 4 onward.

**Integrity: new for batch 4.**
- **Batch-3 manifest.** `main-run/analysis/b3_integrity_manifest.json` (`41e41863…`, 551 entries) covers the batch-3 instances,
  specs, designs, audits, history archives, variants, key entries, plans, ledger lines, per_run rows and CSV rows. Its baseline was
  recorded after the `mr_build_records.py` change, and it is anchored to the 17-October state in two ways:
  - the reconstructed W30 version of that script (sha256 `7e2b1a1d…`, equal to W30's record) reproduces all 44 build-log and 35
    provenance rows exactly;
  - `ct_driver.py --verify-only` passes for all 10 batch-1–3 plans against FREEZE.json's launch-time hashes.
- **Frozen-hash file.** `main-run/analysis/batch4_frozen_hashes.json` (sha256 `11eb66ff…`) pins 53 files and requires
  `AMENDMENTS.md` to begin with `main-run/analysis/AMENDMENTS_through_W33.md` (`bb9057d0…`). The 53 files are:
  - every `mr_*` script, the briefs and the checklist;
  - the batch-3 and batch-4 pre-registrations, `MAIN_RUN_PLAN.md`, the candidate pool and all task files;
  - the batch-3 and batch-4 checkout logs and the batch-1–3 build/audit results;
  - both manifests, the batch-3 analysis files and `diagnosis_notes.json`;
  - the batch-1–3 driver logs and the w50/w56/wmDiag ledgers.

  It gives 54 entries and 0 mismatches.
- **Checkpoints.** The three checks (`--verify`, the batch-3 manifest and `--verify-frozen`) run after construction, after every
  regeneration, after every block and at the end.

**Reviews before freezing.**
- **Round 1** (`wf_5a856bab-c82`). The tooling lens raised:
  - the undisclosed brief change;
  - no batch-4 hash file;
  - batch-3 labels in the evaluation;
  - no per-project reading;
  - overstated manifest coverage;
  - unpinned other ledgers.

  The compliance lens failed when the machine slept.
- **Round 2** (`wf_41831dc1-bd2`, rerun after a network outage). Both lenses raised:
  - batch-3 governing files left unpinned;
  - the "before any checkout" header;
  - minor wording issues (Stage B, FLAGGED in the stop rule, key preflight, the ledger set, note-key restriction, the batch-3
    baseline).

  Both confirmed that the 24 targets are distinct and the 23 skips correct, and that nothing the user forbade is implied. All of
  these points are fixed above.

**Checkouts and fixtures.** 24 new `defects4j checkout` directories were made (`main-run/batch4_checkouts.log`), each at its
`FIXED_VERSION` tag, and 24 fixtures. The key preflight is clean: no batch-4 key appears in the batch-1–3 task files, and no
design, spec, instance, audit, history or variant path exists.

**Construction prompt.** As in batch 3, with two changes:
- the builder text points at `batch4_tasks.json` and `BATCH4_PREREGISTRATION.md`, and says the brief's "batch 3" labels apply;
- the format examples are batch-3 designs built under the checklist (`Lang-31.py`, `Math-55.py`) plus `Closure-10.py` for Closure
  layout, in place of `Lang-30.py`.

Keep-awake was requested for the session.

## W35 (2026-10-19): batch-4 dispositions recorded before any batch-4 run; validator G10 finding

**Construction.** Workflow `wf_ff562da1-80b` ran 51 agents with 0 errors, over 6 lanes, using the batch-3 pipeline unchanged.
Results are in `main-run/batch4_build_audit_results.json`.

**Outcome: 12 ACCEPTED, 12 UNBUILDABLE, 0 REJECTED, 0 FLAGGED.**
- **Closure-60** was redesigned once before any run: its first version's blind trace check found T3. The redesigned version is
  CONFIRMED and NO_TRACE, and v1 is archived. The other 11 passed both checks on their first version.

**UNBUILDABLE.** The builders' reasons are in the build log.

| Instance | Reason |
|---|---|
| Math-79 | the host pool has fewer than five usable classes |
| Lang-50 | the facade's test does not reach a chain |
| JacksonCore-10 | clock-seeded root, so no deterministic single trigger |
| JacksonCore-20 | a uniform enum fold whose omissions fail 60–76 tests |
| Math-46 | Complex.valueOf has no test caller in this checkout |
| Closure-109 | parsing runs on package-private types |
| Closure-107 | CommandLineRunner.main has no caller |
| Closure-122 | private instance state, no splittable chain |
| Closure-27 | no test calls IR.script with statements |
| Closure-37 | not splittable, and no single-test fault |
| Math-59 | see below |
| Lang-56 | see below |

- **Math-59.** The builder returned **FAILED** because it ended before its own validation finished: G2a, G2b and G0 had passed and the
  rest was still running. The first row of the pre-registered table makes this **UNBUILDABLE**. The partial
  `instances/MR-Math-59/validation.json` has no overall verdict and is not used. The builder also recorded a deviation: the
  host pool was exhausted after four draws, so the gold sat in the facade's own class.
- **Lang-56.** The builder returned **FAILED** because validator gate G10 could not pass (next item).

**Validator finding (G10).** `scripts/mr_validate.py` G10 counts occurrences of the gold's new text. It skips any directory whose
path contains "/build", so it also skips source packages named `builder` (for example `org/apache/commons/lang/builder`).
- Lang-56's gold lay in `builder/ToStringStyle.java`, so G10 counted 0 occurrences and failed.
- **Audit of every built instance** (49 specs, read-only). Counting each gold's new text inside the skipped builder-path files
  finds an occurrence only for Lang-56. For every accepted batch-1 to batch-4 instance, G10's uniqueness result is therefore also
  true with the skip removed. The KPI was never affected: G10 only protects the fault-line uniqueness used by a secondary display
  measure.
- The validator is not changed during batch 4. A word-boundary fix should be made, and disclosed, before any future batch.

**Verification of the 12 accepted instances.**
- READY on 16/16 gates, with spec hashes matching their validations;
- audit CONFIRMED with consistent flags;
- facade within the allowed targets;
- five distinct hosts, and the gold never in the facade's class;
- trigger an existing test;
- gold text extractable.

**Authoritative records.**
- `main-run/analysis/batch4_dispositions.json` (sha256 `257ffb5daaa38791…`).
- `main-run/analysis/batch4_trace_checks.json` (sha256 `b47c0e193d62dcec…`).

**Accepted instances, in run order (pool rank):**

| Pool rank | Instance | Variant | Redesigned | Spec sha256 |
|---|---|---|---|---|
| 39 | Math-63 | CTV-DAB673 | no | `ff5dd8b7a0882ef2…` |
| 41 | Lang-13 | CTV-B39570 | no | `5de4c241997e50a4…` |
| 48 | Lang-21 | CTV-19F725 | no | `01f777184ff21f07…` |
| 50 | Lang-52 | CTV-C8A0EC | no | `34892c46c328f0db…` |
| 55 | Lang-38 | CTV-3F7670 | no | `036abbb33915dd9a…` |
| 62 | Closure-174 | CTV-9907BA | no | `da7e4ad3d00b09ad…` |
| 63 | Math-85 | CTV-28AA77 | no | `6c705bf23a012de6…` |
| 65 | Math-36 | CTV-8BFEB5 | no | `1d42298dac65d096…` |
| 68 | Closure-60 | CTV-FBD7A7 | yes | `50bc66057a7557d1…` |
| 69 | Closure-61 | CTV-D3E63B | no | `56f0631401b55d99…` |
| 71 | Closure-9 | CTV-171EBA | no | `4b53c708e5fa8461…` |
| 90 | Closure-137 | CTV-EC9460 | no | `bb3e9cd52e7f8e65…` |

**Packaging and integrity.**
- `review/VARIANT_KEY.json` grew from 65 to 77 entries, and every earlier entry is unchanged.
- `INSTANCE_BUILD_LOG.csv` has 68 rows and `INSTANCE_PROVENANCE.csv` 47.
- The three checkpoints give 0 mismatches: the batch-1/2 manifest (551 entries), the batch-3 manifest (551) and
  `--verify-frozen batch4_frozen_hashes.json` (54).

**Robustness raters.** The pre-registered raters (2 per accepted gold, 24 sessions, under shuffled labels) were launched before
block 1 (`wf_f5fc8e3b-9cd`).

## W36 (2026-10-19): batch-4 robustness ratings (pre-registered secondary); block 1 launched

**Robustness.** Workflow `wf_f5fc8e3b-9cd` ran 24 blind single-gold sessions under shuffled labels. Results:
`main-run/analysis/batch4_trace_robustness.json`.

| Group | Instances | Count |
|---|---|---|
| Both extra raters NO_TRACE | — | 9 of 12 |
| One extra rater TRACE | Lang-52 (T3), Math-36 (T3) | 2 |
| Both extra raters TRACE | Math-85 (T4, T4; both marked it under the doubt rule) | 1 |

- The majority of 3 raters is NO_TRACE for 11 of 12 golds.
- Dispositions are unchanged, as pre-registered.
- Secondary subsets: (a) drops Math-85; (b) also drops Lang-52 and Math-36.

**Block 1.**
- The guard was run with `--cap 199`, then the plan `plans/MR_batch4_block1_gpt55.json` was made and frozen to w55. The FREEZE.json
  backup is `analysis/verification/backup/FREEZE.before_W36_b4block1.json`.
- Before launch, `mx_tmp_audit` and `--verify-only` passed.
- The block covers Math-63, Lang-13, Lang-21, Lang-52 and Lang-38.

**W36 addendum (block 1, before launch).** The first `mx_tmp_audit` found four batch-4 construction leftovers. W36 above had been
appended before that result was read, so its "passed" statement only became true after this cleanup.
- The leftovers were `/private/tmp/mr59`, a Math-59 builder scratch holding a Defects4J checkout, and three empty-work `mxb-*`
  auditor scratches.
- All four were created by this session's agents at about 14:04 on 19 October and had no open handles. They were removed by exact
  path.
- After that, `mx_tmp_audit` reported CLEAN, `--verify-only` passed, and `--verify-frozen` gave 0 mismatches.

## W37 (2026-10-21): batch-4 block 2 halted by clamshell sleep; halt review; continuation

**What happened.** `plans/MR_batch4_block2_gpt55.json` ran slots 0–12 between 05:10 and 05:33Z on 19 October. All 13 runs are
valid.
- Slot 13 (MR-Math-36, round 3) ended at 05:45:33Z as `infrastructure` / `provider_stall`, costing $0.342.
- The driver then needed a 3-probe gate. Six consecutive probes returned `status=timeout`, with wall times of 557 to 2045 s, between
  06:14 and 10:12Z.
- The driver halted with "health gate failed 6 times". Slots 14–24 did not run.

**Halt review.** The system power log (`pmset -g log`) shows "Entering Sleep state due to 'Clamshell Sleep'" at 16:35:04 local
(05:35:04Z), on battery at 47% charge. Repeated maintenance sleeps and dark wakes follow for hours.
- Slot 13 was mid-run when the lid closed. Every later probe spanned sleep periods.
- The stall and the gate failures are therefore artefacts of machine sleep, not of the model or the provider. This is the W3
  situation.
- `caffeinate -i` and the app's keep-awake prevent idle sleep only, not clamshell sleep.
- After waking, `api.openai.com` was reachable (401 without a key), no driver or lock remained, and `mx_tmp_audit` was CLEAN.

**Disposition.** This follows W2/W3 and the batch-3 rule for halted blocks.
- **Continuation.** Slot 13's stall stays an infrastructure attempt. `plans/MR_batch4_block2_gpt55_cont.json` (sha256 `23bda650…`)
  holds slots 13–24 in the original order. Its slot 0 (Math-36, round 3) is that slot's single replacement.
- **Guard before the restart** (`--cap 199`). C = $154.83, which includes the stalled attempt and every probe line, M = $0.7826, and
  k = 5 (worst case $198.86). The 12 remaining slots fit within the k = 3 bound (15 slots), with a worst case of $181.28.
- **Driver caveat.** The frozen driver counts replacements per plan. If the continuation's slot 0 also ends as infrastructure, its
  automatic second attempt would exceed the one-replacement rule; that would be recorded as a deviation.
- **Server.** w55 had run since 19 October through the sleep cycles. It is stopped by its recorded PID and started fresh before
  the continuation.

## W38 (2026-10-21): block-2 continuation stopped; the machine is still in clamshell sleep; paid runs paused

**What happened.** `plans/MR_batch4_block2_gpt55_cont.json` started at 15:50:44Z.
- **Run-004** was its slot 0, the single replacement for Math-36 round 3. It ended at 16:07:33Z as `infrastructure` /
  `provider_stall` (300 s timeout, 9 API calls, $0.172 in the ledger).
- The frozen driver counts attempts per plan, so it passed a 3-probe gate and **launched a third attempt (run-005) at 16:07:49Z**.
  This is the deviation W37 anticipated.
- The coordinator stopped its own driver (pid 20113) about 3 s after that launch, before any further slot. The run had already been
  handed to the server.
- The coordinator then stopped the w55 server (pid 20011) at 16:24:34Z.

**Run-005.** It timed out with 5 API calls.
- Its cost, **$0.0720**, is computed from the run's `info.model_stats.instance_cost`, the same field the driver reads. It is **not in
  the driver ledger**.
- The run is **excluded and never scored**: `mx_metrics` includes only runs with a ledger verdict.
- Its leftover workspace (`/private/tmp/d4jws-w1b2/4f3de347…`, 21 MB) was removed by exact path, and `mx_tmp_audit` then reported
  CLEAN.
- All three integrity checks give 0 mismatches.

**Cause.** `pmset -g log` shows the Mac still in clamshell sleep after the W37 halt: "Clamshell Sleep" at 02:16–02:17 local, then
maintenance sleeps with brief dark wakes about every 15 minutes.
- The restart at 15:50Z fell inside the dark wake of 02:49:53–02:51:17 local, and run-004 stalled when the machine slept at 02:51:17.
- The attempt-2 launch at 16:07:49Z fell inside the 03:07:26–03:08:11 dark wake.
- The "AC Power" reading came from the closed-lid machine.
- Paid runs cannot complete while the lid is closed.

**Spend.** Guard C is $155.17 from the ledger, plus the unledgered $0.0720. Until the root ledger gains a row for run-005, the
coordinator adds that amount to C by hand in every guard decision.

**State.**
- Block 2 is done for slots 0–12: 13 valid runs.
- The Math-36 round-3 slot has two infrastructure attempts in the ledger (run-003, run-004) and one aborted, unledgered attempt
  (run-005). Continuation slots 1–11 have not run, and block 3 (Closure-9, Closure-137) has not run.

**Plan for resuming**, only once the machine is awake with the lid open.
1. Run a new frozen continuation for the 11 remaining slots (rounds 3–5 of Math-85, Closure-60, Closure-174, Closure-61 and Math-36).
2. Following W2's one top-up after a halt review (cause: clamshell sleep, documented above), add a single Math-36 round-3 top-up at
   the **end** of that plan, so that no further automatic retry can follow it.
3. Then run block 3.
4. Run the guard before each step, with C including the unledgered $0.0720.

**W38 erratum.** The spend figure in W38 was written before the guard had run. The guard reports **C = $155.0487 from the
ledger**. With run-005's unledgered $0.0720, spend is **$155.12**, not "$155.17". Headroom to the $199 cap is $43.88.

## W39 (2026-10-21): resume after the lid was opened; run-005 adopted into the ledger; second block-2 continuation

**Machine state.** At 05:10Z `ioreg` showed `AppleClamshellState = No`, and `pmset -g log` showed a wake "due to … lid" at 16:07:31
local. The machine was on battery (100%, about 13 h left). Keep-awake was requested again.

**Adoption of run-005 (frozen driver mechanism).** Killing the driver mid-launch in W38 had left `diagnostic/pending_w55.json`,
bound to the first continuation plan, slot 0, attempt 2. The driver also halts on any run directory without a ledger record.
- The frozen driver was run once on `plans/MR_batch4_block2_gpt55_cont.json` with the w55 server stopped, so no paid call was
  possible.
- It adopted run-005 as `infrastructure` / `provider_stall` (final gap 284.5 s, $0.07195), cleared the pending file, and halted with
  "slot 0 (CTV-8BFEB5) failed twice as infrastructure".
- The ledger now records run-005, so guard C includes it: $155.1206. **The hand-added $0.0720 of W38 is no longer needed.**
- A read-only `ct_status.classify` run beforehand gave the same class for runs 003, 004 and 005: provider_stall, infrastructure.

**Second continuation.** `plans/MR_batch4_block2_gpt55_cont2.json` (sha256 `bb512b4c…`) holds the 11 untouched slots of the first
continuation (its slots 1–11) in the original order. They are followed by **one W2-style top-up for MR-Math-36 round 3, placed
last**.
- Under the frozen driver, the top-up slot gets the usual per-plan attempts, as in W2.
- Math-36's round-3 attempts so far are run-003, run-004 and run-005, all infrastructure caused by clamshell sleep and none scored.

**Guard** (`--cap 199`). C = $155.1206, M = $0.7826, k = 4 (worst case $190.36). The 12 slots fit within the k = 3 bound (15
slots), with a worst case of $181.58. **Before launch,** `pmset` and `ioreg` are checked for the open lid.

## W40 (2026-10-21): batch 4 complete; replication reading REPLICATES; spend below the $200 ceiling

**Execution.**
- Block 1 ran 25 slots on 19 October.
- Block 2 ran slots 0–12 on 19 October, then halted on clamshell sleep (W37). Its first continuation was stopped (W38). Run-005 was
  then adopted, and the second continuation's 12 slots ran (W39).
- Block 3 ran 10 slots on 21 October, 05:35–05:53Z.

**Records.** There are 63 batch-4 records: 60 valid, plus 3 infrastructure attempts on the Math-36 round-3 slot (run-003, run-004,
run-005), all caused by clamshell sleep and none scored. Math-36's five valid runs are run-001, -002, -006, -007 and -008; run-008 is
the W2-style top-up.
- No timeouts and no contamination.
- w55 (pid 23069) was stopped by its recorded PID.
- `mx_tmp_audit` reported CLEAN.
- All three integrity checks give 0 mismatches.
- `batch3_prediction.json` still matches its pinned hash.

**Result** (`mr_batch3_eval.py --batch batch4`, `main-run/analysis/batch4_prediction.json` sha256 `cabfef7e5f4ee7c3…`).

| Set | n | With at least one shift | s | Reading |
|---|---|---|---|---|
| **Primary** | 12 | 11 | 0.917 | **REPLICATES** |
| Secondary (a): majority of 3 NO_TRACE | 11 | 11 | 1.0 | REPLICATES |
| Secondary (b): all 3 NO_TRACE | 9 | 9 | 1.0 | REPLICATES |

- The primary set has 48/60 runs shifted. Robustness ratings: `batch4_trace_robustness.json` (`9456c99cf0865c57…`).
- **Per project:** Closure 5/5 (REPLICATES); Lang 4/4 and Math 2/3, each INCONCLUSIVE because n < 5.
- **The only instance without a shift is Math-85**, the gold whose two extra raters both found a T4 trace. Its omitted
  `fa * fb == 0` exit leaves the gold's `@throws` clause visibly contradicted.
- **All 48 batch-4 shifts ranked the facade first.** Across all batches, all 147 shifted runs did.

**Cumulative KPI: 47 validated instances tested; 38 with at least one shift; 147/235 answered runs shifted.**

| Project | Instances tested | With at least one shift |
|---|---|---|
| Lang | 32 | 27 |
| Math | 6 | 4 |
| Closure | 6 | 6 |
| Chart | 2 | 1 |
| JacksonCore | 1 | 0 |

**Spend.**
- Batch-4 runs cost $26.23 (63 records) and the 81 probes about $0.65.
- **The experiment total is $159.58 recorded and $163.95 including estimates** (guard C = $163.95), below the user's $200
  ceiling.
- The eligible candidate pool is exhausted: every unattempted eligible bug would reuse an existing facade. Going further needs a
  decision on widening the pool, which is the user's.

**Notes.** The batch-4 diagnosis notes are in `main-run/analysis/diagnosis_notes_batch4.json`, kept apart from the frozen
batch-1–3 notes.

## W41 (2026-10-21): verification of progress update 4; errata to W35, W37 and W40; guard records added

**Verification.** Two independent verifiers (`wf_60403baa-5f6`) checked the update.
- The numbers lens recomputed 62 claims. It found no wrong figure in the data tables, but it found two classification and wording
  errors.
- The process lens checked 36 claims and found 9 errors and omissions.
- All of them are fixed in `main-run/SUPERVISOR_PROGRESS_UPDATE.md`.

**Errata.**
- **W35, Lang-50 row.** "the facade's test does not reach a chain" is wrong. No existing test reaches `FastDateFormat.getTimeInstance`
  at all, and the builder also found the host pool too small.
- **W35, Closure-27.** Tests call `IR.script` 953 times, always with zero statements, so the fault site never runs.
- **W35, Closure-37.** It is also unbuildable because no fault is caught by exactly one test.
- **W40, "every unattempted eligible bug would reuse an existing facade".** Wrong for 14 of the 23. Under the simple class + method
  rule used since batch 1:
  - 9 bugs (Lang-24, Lang-27, Lang-36, Lang-12, JacksonCore-6, Math-26, Math-27, Closure-26, Closure-141) offer only methods already
    used as a facade.
  - 14 bugs (Math-37, Math-47, Closure-32/133/68, Closure-42/81/84/157, Closure-83/151/101/158/149) offer only methods that a
    batch-4 builder found unbuildable in a sibling bug's checkout: Complex.valueOf, JsDocInfoParser.parseTypeString,
    IRFactory.transformTree, CommandLineRunner.main.
  - No eligible bug has an unused and untried target.
- **W37, the halt review.** The review took the machine to be awake because the network answered, and the first restart was launched
  without checking the lid. W38 shows the machine was still in clamshell sleep, so the over-limit third attempt followed from that
  launch decision. Since W39, the lid state (`ioreg AppleClamshellState`) is checked before every launch.

**Guard records missing from W36–W40.** These values come from the session record at launch time.
- **Original block-2 launch (19 October, about 05:10Z).** `mr_cost_guard.py --left 7 --cap 199` gave C = $148.3173, M = $0.782629,
  k = 5, worst case $192.3447.
- **Block 3 (21 October, about 05:34Z).** `--left 2 --cap 199` gave C = $159.8951, M = $0.782629, k = 2, worst case $177.5637.
- **Note on M.** Block 1 contained a run costing $0.7826, above the M of $0.6595 in force when block 1 was admitted. Block 1's worst
  case had $24 of headroom to the cap, so the ceiling was never at risk, and from block 2 on the guard used the new M.

## W42 (2026-10-24): the "all Defects4J bugs" extension; batch 5 pre-registered, checkouts and fixtures made, hashes frozen

**Direction.** After meeting the supervisor on 23 October the user wrote that the aim is now to run all Defects4J bugs, that
non-shifting instances are acceptable, that the data set should be as large as possible and that there is no cost limit; where a
revision has fewer than five classes of at least 1500 lines, the repository's largest public classes may serve as hosts ("藏不住就藏不住").
On 24 October the user approved the 13-day plan (`thesis_writeup/supervisor_replies/2026-10-23/run_all_bugs/PLAN_ALL_BUGS_ZH.md`:
batch 5 → C10f → paired static/instance bridge; construction ends 31 October; Mockito, Csv and C10x deferred) and wrote "现在开始运行".
The W34 ceiling of $200 is withdrawn by the user; a $500 sanity cap replaces it (`mr_cost_guard.py --cap 500`, stop-and-report).

**Why the pool changes.** Nine verified analyses (`thesis_writeup/supervisor_replies/2026-10-23/run_all_bugs/`, each adversarially
re-checked) found that 670 of the 763 pool rejections rest on rules, thresholds or recipe implementation, not on the construct. Two
findings bear on batch 5 directly:
- **The slow-suite rule is refuted.** The 959–1001 s suite times of 24 September do not reproduce; re-timed on 23 October from fresh
  checkouts, Time, Collections, JacksonDatabind and Mockito run their full suites in 4–62 s (that session's notes record ~1000 s JVM
  stalls). The rule excluded 202 bugs, 28 by that rule alone (JacksonDatabind 15, Time 13; 16 Time bugs once the next item is fixed).
- **Two pool reading errors.** Time-22..27 were read at the wrong git path (`JodaTime/` prefix, `Time.pm:68-70`); Gson `$Gson$Types`
  never resolved (not in batch 5). The 6-row candidate cap (`mr_candidate_pool.py:128`) hid 11 untried `NumberUtils` targets for
  Lang-24/27/36.

**Pre-registration.** `main-run/BATCH5_PREREGISTRATION.md` (sha256 `e5a4099cd034…`). Batch 5 keeps the C10 recipe, the frozen protocol,
the no-local-trace HARD rule, the audit, the disposition table and the KPI definition unchanged. It changes the pool only: slow-suite rule
dropped; Time-23/25/26 and Lang-24/27/36 candidates recomputed with the pool's own filter (`main-run/batch5_prep/recompute_candidates.py`,
`ac78efc5d2a6…`; output `recomputed_candidates.json`); facade reuse allowed as a recorded alternative (`facade_reuse_of`), with
distinctness kept as the preference and the primary KPI counted over distinct-facade instances. Allocation by maximum bipartite matching
in batch-5 order (`main-run/batch5_prep/make_tasks.py`, `a55a90080895…`), excluding every earlier facade (main run and Stage B, by
fully qualified class and method) and `NumberUtils.createBigDecimal` (unbuildable in Lang-3, W27).

**Candidates.** 37, in `main-run/batch5_tasks.json` (`22779fee2d72…`): JacksonDatabind 14, Time 16, Lang-24/27/36, and four
facade-reuse bugs (JacksonCore-6, Lang-12, Closure-26, Closure-141). 27 have a distinct facade; 10 reuse one (6 within batch 5, 4 of an
earlier instance). Batch-5 ranks are 92–128.

**Checkouts and fixtures.** 27 new fixed checkouts (`scripts/mr_checkouts.py`, `803330607997…`; log `main-run/batch5_checkouts.log`,
`6f958c8c7e21…`; all OK at their `D4J_<P>_<id>_FIXED_VERSION` tag; JacksonDatabind 106–108 MB, Time 21–29 MB, Lang 35 MB, Closure
203–222 MB). Ten keys already had checkouts. 37 fixtures made with `mr_lib.py fixture` (real-directory copies with `.git`;
`construction/fresh-mr` now 105 fixtures, 6.8 GB; 24 GB free on the volume). Key preflight for all 37 keys: clean (no design, spec,
instance, audit, history or variant path; none in the batch-1–4 task files).

**Script changes (pinned files; defaults reproduce earlier output).**
- `mr_integrity.py` `3aa86256cf3d…` → `6dd6fe7be507…`: plan pattern `MR_batch5_*.json`.
- `mr_build_records.py` `c48333d2121f…` → `4a7faf44d4ce…`: batch 5 reads `analysis/batch5_dispositions.json` like batches 3–4.
- `mr_batch3_eval.py` `a28962e55d8e…` → `f4a0dea4906f…`: `--batch batch5` uses the replication labels and names the batch-5
  pre-registration. Re-running the batch-3 and batch-4 evaluations reproduces `batch3_prediction.json` and `batch4_prediction.json`
  byte for byte.
- **Erratum, same day.** A first version of the `mr_batch3_eval.py` edit changed the batch-4 thresholds string too; the check re-run
  overwrote `batch4_prediction.json` with that one-string difference. The file was restored from the pre-run copy (byte-identical,
  verified with `cmp`) and the script corrected before anything else was done.
- New: `scripts/mr_checkouts.py`, `main-run/batch5_prep/` (two scripts and the recomputed candidate records).

**Integrity.** A batch-4 manifest was recorded before any batch-5 row existed: `mr_integrity.py --record --batches batch4 --manifest
b4_integrity_manifest.json` (404 entries, `c8e8edc890cf…`); it verifies with 0 mismatches, as do the batch-1/2 and batch-3 manifests
and `batch4_frozen_hashes.json` (checked before the script edits). `main-run/analysis/AMENDMENTS_through_W41.md` (`9b015d66e36a…`) is
the pinned prefix of this file for `batch5_frozen_hashes.json`, written immediately after this entry.

**Cost guard at registration.** `mr_cost_guard.py --left 37 --cap 500`: C = $163.9474, M = $0.782629, k = 5, worst case after one
block $207.97. Expected batch-5 run cost about $80 (37 × 5 × $0.43), cumulative about $244.

**Next.** Construction workflow (builder → auditor + blind trace checker → one redesign → disposition table), as batch 4
(`wf_ff562da1-80b`'s script with batch-5 names), seven lanes. Dispositions are recorded in W43 before block 1. Runs use
`plans/MR_batch5_block<N>_gpt55.json` on w55 and start only after the user has seen the dispositions and the cost estimate.

## W43 (2026-10-25): batch-5 dispositions recorded before any batch-5 run; packaged, planned and frozen

**Construction.** Workflow `wf_b71eac50-73d` ran 94 agents over 7 lanes with 0 errors (24 Oct 06:20 to 18:20 UTC+11, 12.0 h),
using the batch-3/4 pipeline unchanged (builder → independent auditor + blind trace checker → one redesign → disposition table).
Results: `main-run/batch5_build_audit_results.json` (sha256 `baa4034bbcaa…`), `main-run/analysis/batch5_dispositions.json`
(`fbf70c309356…`, with `facade_reuse_of` and `facade_reuse_effective` per instance), `main-run/analysis/batch5_trace_checks.json`
(`9ba27f1a6f46…`).

**Dispositions: 20 ACCEPTED, 16 UNBUILDABLE, 1 UNBUILDABLE (local trace); 0 REJECTED, 0 FLAGGED.** Four instances were redesigned
once (Time-9, Time-11, JacksonCore-6 ACCEPTED after redesign; JacksonDatabind-75 TRACE again → UNBUILDABLE (local trace)). Every
ACCEPTED instance has validation READY, audit CONFIRMED (all with a recorded bypass, as in batches 1–4) and checker NO_TRACE.

| Rank | Instance | Status | Redesigned | Facade reuse (effective) | Spec sha256 |
|---|---|---|---|---|---|
| 93 | JacksonDatabind-38 | ACCEPTED | no | — | 06d3b6361578 |
| 95 | JacksonDatabind-44 | ACCEPTED | no | — (JacksonDatabind-37 UNBUILDABLE) | 95a2710df0c2 |
| 97 | JacksonDatabind-56 | ACCEPTED | no | — (JacksonDatabind-42 UNBUILDABLE) | 445a70fd37b6 |
| 100 | JacksonDatabind-66 | ACCEPTED | no | — | 23ff5e850cdb |
| 101 | JacksonDatabind-71 | ACCEPTED | no | JacksonDatabind-66 | a513fa939cd9 |
| 105 | JacksonDatabind-105 | ACCEPTED | no | — | a1d5a10efac6 |
| 112 | Time-9 | ACCEPTED | yes | — | ed4676eb991e |
| 113 | Time-11 | ACCEPTED | yes | — | c7879d8bee7b |
| 114 | Time-12 | ACCEPTED | no | — | 24c2eecdfd50 |
| 115 | Time-15 | ACCEPTED | no | — | 12cbd3dc9898 |
| 116 | Time-17 | ACCEPTED | no | — | b0d0d36dc358 |
| 118 | Time-19 | ACCEPTED | no | — | d7fddf249e82 |
| 119 | Time-23 | ACCEPTED | no | — | dad140304621 |
| 121 | Time-26 | ACCEPTED | no | — | 4a2bfe9a6a1e |
| 122 | Lang-24 | ACCEPTED | no | — | 880c0a5c3986 |
| 123 | Lang-27 | ACCEPTED | no | — | c29ddf99103c |
| 125 | JacksonCore-6 | ACCEPTED | yes | JacksonCore-5 | aee3d8b24ba0 |
| 126 | Lang-12 | ACCEPTED | no | Lang-11 | 4625487ca52b |
| 127 | Closure-26 | ACCEPTED | no | Closure-9 | 7be66bc81d0e |
| 128 | Closure-141 | ACCEPTED | no | Closure-137 | 360421316344 |

UNBUILDABLE (builder step 7, no redesign unless noted): JacksonDatabind-37 (no caller of `SimpleType.construct` anywhere; a probe that
makes it throw leaves 0 of 1,517 tests failing), -42, -53, -59, -63, -83, -99; Time-1, -2, -3, -5 (after redesign), -6, -8, -18, -25;
Lang-36. UNBUILDABLE (local trace): JacksonDatabind-75 (TRACE on both versions). Reasons are in the results file; the dominant ones are
"no fault that exactly one existing test catches" and "nothing to split" for the short wrappers that the pre-registration flagged as
likely. Several builders found that the pool's name-based test check (`test_files_calling`) matched unrelated `construct(` /
`getInstance(` calls, so "called by a test" was false for the allowed target: the batch-6 pool must use a qualified or dynamic
reachability check.

Of the 20 ACCEPTED, 15 have a distinct facade and 5 reuse one (JacksonDatabind-71 ↔ -66 within batch 5; JacksonCore-6, Lang-12,
Closure-26, Closure-141 reuse an earlier instance's facade). The primary KPI is counted over the 15; the secondary over all 20.

**Packaging and integrity.**
- `mr_package.py` for the 20 (`main-run/batch5_packaging.log`, `bf080646e686…`). The first pass failed for the 14 JacksonDatabind
  and Time instances because `new_bug_variants/<Project>/` did not exist for these two new projects; the two directories were created
  (new, empty) and the 14 were packaged on the retry. 20 variants, CTV ids in the log.
- `review/VARIANT_KEY.json` grew from 77 to 97 entries (67 MAIN_RUN_C10); every earlier entry is unchanged (manifests below).
- `mr_build_records.py`: `INSTANCE_BUILD_LOG.csv` 105 rows (37 batch-5), `INSTANCE_PROVENANCE.csv` 67 rows (20 batch-5, all with a
  variant id).
- Four checkpoints, 0 mismatches each: batch-1/2 manifest (551), batch-3 manifest, batch-4 manifest (404, recorded in W42),
  `--verify-frozen batch5_frozen_hashes.json` (76).

**Plans and freeze.** Four blocks of 5 in batch-5 order, 5 runs each, seeds 202610251–4:
`plans/MR_batch5_block1_gpt55.json` (`22e334701359…`; JacksonDatabind-38, -44, -56, -66, -71), `block2` (`80536a5581dc…`;
JacksonDatabind-105, Time-9, -11, -12, -15), `block3` (`6de609649d92…`; Time-17, -19, -23, -26, Lang-24), `block4`
(`a8f4e9df8018…`; Lang-27, JacksonCore-6, Lang-12, Closure-26, Closure-141). `FREEZE.json` was backed up to
`analysis/verification/backup/FREEZE.before_W43_b5.json` and the four plans were added, bound to w55 (freeze sha256 `3bfcf071e9db…`).
The driver's `--verify-only` passed for all four plans.

**Cost guard** (`--left 20 --cap 500`): C = $163.9474, M = $0.782629, k = 5; worst case after one block $207.97. Expected batch-5 run
cost about $43 (100 runs × $0.43), cumulative about $207.

**/private/tmp.** `mx_tmp_audit` flagged nine scratch directories of this session's batch-5 builders and auditors (`mxb-*`, `mxm-*`,
24 Oct 17:33–19:44, no open handles) and `jc20-probes` (24 Oct, the exclusion-analysis agents). They were removed by exact path.
Audit after removal: CLEAN.

**Robustness raters.** The pre-registered raters (2 per accepted gold, 40 blind sessions under shuffled labels G01–G20,
`wf_773ad2d8-bff`) were launched before block 1; results go to `main-run/analysis/batch5_trace_robustness.json` (W44). Dispositions
are not changed by them.

**Next.** Block 1 starts only after the user has seen the dispositions and the cost estimate: `start_gpt_server.sh w55`, then
`wm_run_chain.sh w55 MR_batch5 plans/MR_batch5_block1_gpt55.json …`, with the guard re-run before each block.

## W44 (2026-10-25): batch-5 robustness ratings (pre-registered secondary)

**Robustness.** Workflow `wf_773ad2d8-bff` ran 40 blind single-gold sessions (2 extra raters per accepted gold, shuffled labels
G01–G20, the gold text given as a file; 0 errors, 3.4 min). Results: `main-run/analysis/batch5_trace_robustness.json`
(sha256 `4127d673b67e…`).

| Outcome | Instances | Count |
|---|---|---|
| Both extra raters NO_TRACE | — | 19 of 20 |
| One extra rater TRACE | JacksonDatabind-71 (T3, one rater) | 1 |
| Both extra raters TRACE | — | 0 |

- The majority of 3 raters is NO_TRACE for 20 of 20 golds.
- Dispositions are unchanged, as pre-registered. Block 1 has not been launched; it waits for the user's go after the dispositions and
  the cost estimate (W43) were reported.

## W45 (2026-10-25): standing authorisation to run; batch-5 blocks launched under a per-block guard wrapper

**Authorisation.** The user, on 25 October, after seeing the batch-5 dispositions, the robustness ratings and the cost estimate (W43,
W44): "以后不用问我，直接运行，直到遇到不可控困难再停止" (from now on do not ask me; run directly, and stop only on an uncontrollable
difficulty). This covers the batch-5 blocks and the later tiers of the extension (C10f, the paired bridge) under their own
pre-registrations. The $500 sanity cap, the per-block guard, the lid check, the tmp audit, `--verify-only` and the spend report after
each block stay in force; a guard refusal, a halt the driver cannot recover, or a server failure counts as a difficulty that stops the
run and is reported.

**Launch.** `scripts/mr_run_blocks.sh` (new helper) runs the four batch-5 plans one block at a time: before each block it checks the
lid (`AppleClamshellState = No`), waits for w55 to answer `/api/env`, re-runs `mr_cost_guard.py --left <remaining> --cap 500` and
requires k ≥ 5, runs `mx_tmp_audit.py` and the driver's `--verify-only`, then `wm_run_chain.sh w55 MR_batch5_b<N> <plan>`; it stops at
the first failure. Log: `diagnostic/run_blocks_batch5.out`. The server was started with `start_gpt_server.sh w55` (credential from the
authorised env file, never printed; allow-listed environment, P4 on).
