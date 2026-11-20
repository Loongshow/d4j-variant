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

## W46 (2026-10-25): batch 6 (cell C10f, fallback hosts) pre-registered; pool v2; checkouts, fixtures and hashes

**Pre-registration.** `main-run/BATCH6_PREREGISTRATION.md` (sha256 `1d9bf9939335…`), generated by
`main-run/batch6_prep/write_prereg.py` (`fc7e5a3be1bd…`) from the confirmed task file. C10f = the C10 recipe with
fallback hosts: where fewer than five public non-interface non-enum classes of ≥ 1500 lines exist besides the facade's class, the hosts
are the five largest such classes (hop 1 in the largest, hop 5 in the fifth). Everything else is unchanged (W45 authorisation; batches
3–5 rules). New cell labels keep C10f apart from the 67 C10 instances: `scripts/mr2_spec.py` (`42611b664a23…`, one changed
line: mechanism and tier `MAIN_RUN_C10F`) and `scripts/mr2_report.py` (`810f6e92108d…`, tier filter and `*_C10F` output
files). Builder addendum `construction/mainrun/BUILD_BRIEF_C10F_ADDENDUM.md` (`f50c479a7abe…`): host
procedure by `host_mode`, a mandatory reachability probe before designing (batch-5 lesson: the pool's name-based test check gave false
"called by a test" verdicts), `mr2_spec.py` in place of `mr_spec.py`.

**Pool v2.** `main-run/batch6_prep/mr2_candidate_pool.py` (`4f66596f3708…`; workflow `wf_ef458ce4-69b`,
built, adversarially verified and corrected) → `main-run/CANDIDATE_POOL_V2.csv` (`dc04c530d07d…`),
`candidate_pool_v2.json`, `batch6_candidates.json`, `batch6_tasks_draft.json`; report `batch6_prep/POOL_V2_REPORT.md`. Sanity: the original
pool's 91 eligible bugs reproduced with 0 field mismatches; the 23-October recount (SUP-static 213 LOOSE / 173 STRICT1) reproduced with 0
mismatches; the emulated name grep agrees with real `git grep` on 1,427 checks. ELIGIBLE_C10F = 166 (101 in the 1500 regime, 65 largest5),
93 already in batches 1–5; Mockito and Csv deferred. Targets exclude 66 used facades and 41 targets found UNBUILDABLE in a sibling revision
(25 named in the brief, 16 added by the pool builder with their reasons; the math3 `Fraction.getReducedFraction` exclusion from Math-1
removed the only target of Math-26 and Math-27). Eleven otherwise-eligible bugs were dropped for lack of a target.

**Candidates.** 62 (`main-run/batch6_tasks.json`, `b96210ac621f…`): Compress 13, Collections 12, Codec 11, Jsoup 8, Math 6,
Cli 4, Gson 4, JacksonDatabind 2, JacksonCore 1, JxPath 1; one in the 1500 regime (JacksonDatabind-103), 61 largest5; 53 distinct facades,
9 recorded reuses; ranks 129–190. Four tasks carry a builder warning (Math-91 target structure; Math-92/93/94 inherit Math-79's FQNs, which
failed there for host reasons). The fifth host ranges from 276 lines (Cli) to 1,273 (Math), median 926.

**Checkouts, hosts, fixtures.** 37 new fixed checkouts (`main-run/batch6_checkouts.log`, `400e90bacca0…`, all OK at
their `FIXED_VERSION` tags); 25 keys already had one. Hosts were confirmed on the real checkouts by `batch6_prep/confirm_hosts.py`
(`bd51ff1d289b…`): 58 of 61 largest5 lists equal the pool's git-snapshot lists; for Collections-13, -15 and
-16 the checkout differs (the snapshot listed `ExtendedProperties`/`FastArrayList` that the Defects4J checkout lays out differently) and
the checkout list is the one recorded in `batch6_tasks.json`. 62 fixtures made with `mr_lib.py fixture`. Key preflight: 62 keys, 1 problems: JacksonCore-1: variant path exists.

**Integrity.** `main-run/analysis/AMENDMENTS_through_W45.md` (`99fb3b39ecea…`) is the pinned prefix for
`batch6_frozen_hashes.json`, written immediately after this entry. The batch-5 manifest is recorded after the batch-5 runs finish and
before any batch-6 row (W47).

**Order of work.** Batch-6 construction starts after the batch-5 runs have finished (no construction during paid runs); its runs follow
under `mr_run_blocks.sh` with cap $500. Batch-5 scoring and the progress update are recorded in W47.

**W46 addendum (preflight item).** The one preflight finding, "JacksonCore-1: variant path exists", is `new_bug_variants/JacksonCore/bug-1/L20/`
with CTV-7CE456 (mechanism M3) and CTV-E04F64 (M10): mechanism-search held-out instances validated on 10 October on the same fixed
revision, touching `JsonStringEncoder`, `CharTypes`, `Base64Variant(s)` and `ByteArrayBuilder`. Neither touches the batch-6 facade class
`NumberInput`, and neither is a main-run or Stage B instance, so the facade-distinctness rule is unaffected. JacksonCore-1 stays in
batch 6; `mr_package.py` will add its C10f variant as a third CTV directory under the same bug directory, as the layout allows. The other
61 keys have no variant path. Verified before any batch-6 build.

## W47 (2026-10-25): batch-5 runs complete and scored; batch-5 manifest recorded; batch-6 construction launched

**Runs.** `scripts/mr_run_blocks.sh w55 MR_batch5 500` ran the four blocks between 01:33Z and 03:53Z (2 h 20 min; log
`diagnostic/run_blocks_MR_batch5.out`). Guard before each block: C = $163.95 / $177.50 / $186.73 / $197.01, k = 5 each time; lid open,
`mx_tmp_audit` CLEAN and `--verify-only` passed each time. 101 records (100 valid runs; 1 record excluded by a frozen driver rule and replaced
in block 4), 0 halts, 0 timeouts, median wall time 67 s. Batch-5 run cost $41.87; cumulative recorded $201.45, including
estimates $206.7 (guard after the batch: C = $206.71, M = $0.9527).

**Scoring.** Frozen `mx_metrics.py`, then `mr_report.py` (`MAIN_RUN_RUNS.csv`, `MAIN_RUN_RESULTS.csv`, `SHIFTED_INSTANCES.md`,
`FAILED_TO_TRANSFER.md`, `COST_LEDGER.csv`, `analysis/main_run_summary.json`) and `mr_batch3_eval.py --batch batch5`
(`analysis/batch5_prediction.json`).

**Batch-5 result (KPI unchanged: a shift is gold rank > 1; an instance succeeds with at least one shift in 5 valid runs).**

| Scope | Instances | With ≥ 1 shift | Shifted / answered runs |
|---|---|---|---|
| Primary: distinct facade | 15 | **8** | 34/75 |
| Secondary: recorded facade reuse | 5 | 4 | 13/25 |
| All batch 5 | 20 | **12** | 47/100 |

Per project (all 20): Closure 2/2, JacksonCore 1/1, JacksonDatabind 1/6, Lang 3/3, Time 5/8. Every shifted run but one ranked the facade (entry point) first; the one exception
is an upstream hop (Time-9).

| Rank | Instance | Project | Shifted/answered | Gold ranks | ≥ 1 shift | Facade reuse of |
|---|---|---|---|---|---|---|
| 93 | JacksonDatabind-38 | JacksonDatabind | 5/5 | 2 2 2 6 2 | yes | — |
| 95 | JacksonDatabind-44 | JacksonDatabind | 0/5 | 1 1 1 1 1 | no | — |
| 97 | JacksonDatabind-56 | JacksonDatabind | 0/5 | 1 1 1 1 1 | no | — |
| 100 | JacksonDatabind-66 | JacksonDatabind | 0/5 | 1 1 1 1 1 | no | — |
| 101 | JacksonDatabind-71 | JacksonDatabind | 0/5 | 1 1 1 1 1 | no | JacksonDatabind-66 |
| 105 | JacksonDatabind-105 | JacksonDatabind | 0/5 | 1 1 1 1 1 | no | — |
| 112 | Time-9 | Time | 4/5 | 3 6 4 1 4 | yes | — |
| 113 | Time-11 | Time | 0/5 | 1 1 1 1 1 | no | — |
| 114 | Time-12 | Time | 0/5 | 1 1 1 1 1 | no | — |
| 115 | Time-15 | Time | 5/5 | 2 2 2 2 2 | yes | — |
| 116 | Time-17 | Time | 5/5 | 3 3 3 3 2 | yes | — |
| 118 | Time-19 | Time | 4/5 | 1 2 2 2 2 | yes | — |
| 119 | Time-23 | Time | 0/5 | 1 1 1 1 1 | no | — |
| 121 | Time-26 | Time | 1/5 | 2 1 1 1 1 | yes | — |
| 122 | Lang-24 | Lang | 5/5 | 2 2 6 3 2 | yes | — |
| 123 | Lang-27 | Lang | 5/5 | 3 3 3 3 3 | yes | — |
| 125 | JacksonCore-6 | JacksonCore | 1/5 | 1 1 2 1 1 | yes | JacksonCore-5 |
| 126 | Lang-12 | Lang | 2/5 | 2 2 1 1 1 | yes | Lang-11 |
| 127 | Closure-26 | Closure | 5/5 | 2 3 3 2 5 | yes | Closure-9 |
| 128 | Closure-141 | Closure | 5/5 | 2 2 2 2 2 | yes | Closure-137 |

**Replication reading (secondary; batch-3 thresholds, `mr_batch3_eval.py --batch batch5`):** None. Per project:
Closure: INCONCLUSIVE (n < 5) (2/2); JacksonCore: INCONCLUSIVE (n < 5) (1/1); JacksonDatabind: DOES NOT REPLICATE (1/6); Lang: INCONCLUSIVE (n < 5) (3/3); Time: DOES NOT REPLICATE (5/8).
The two projects new to the main run differ: JacksonDatabind 1 of 6 instances shifted, Time 5 of 8; Lang 3 of 3 and the two Closure
reuses 2 of 2 shifted as in batches 1–4. This is the first main-run batch whose per-project readings diverge; the thesis must report it
as such (no causal reading; the project, the facade kind and the host sizes are confounded here).

**Programme total after batch 5:** 67 validated instances tested, 50 with at least one shift
(194/335 answered runs shifted); per project {'Chart': {'tested': 2, 'with_shift': 1}, 'Closure': {'tested': 8, 'with_shift': 8}, 'JacksonCore': {'tested': 2, 'with_shift': 1}, 'JacksonDatabind': {'tested': 6, 'with_shift': 1}, 'Lang': {'tested': 35, 'with_shift': 30}, 'Math': {'tested': 6, 'with_shift': 4}, 'Time': {'tested': 8, 'with_shift': 5}}.

**Integrity.** After scoring: batch-1/2, batch-3 and batch-4 manifests 0 mismatches; `batch5_frozen_hashes.json` and
`batch6_frozen_hashes.json` 0 mismatches. A batch-5 manifest was then recorded: `mr_integrity.py --record --batches batch5 --manifest
b5_integrity_manifest.json` (668 entries, sha256 `f4f9c8f9f747…`), verified 0 mismatches.

**Batch 6.** Construction of the 62 C10f candidates (W46) was launched immediately after the runs ended (no construction during paid
runs), with the batch-5 pipeline, the C10f addendum, `mr2_spec.py` and the reachability probe; eight lanes. Dispositions will be
recorded in W48 before any batch-6 run.

**W47 addendum (the reading line above printed "None" because the coordinator read the wrong key of `batch5_prediction.json`; the file is
correct).** Replication reading, batch-3 thresholds (`mr_batch3_eval.py --batch batch5`): primary n = 20, 12 with a shift, s = 0.60 →
**DOES NOT REPLICATE** (instances without a shift: JacksonDatabind-44, -56, -66, -71, -105; Time-11, -12, -23). Subset (a), majority of 3
raters NO_TRACE: the same 20, s = 0.60, DOES NOT REPLICATE. Subset (b), all 3 raters NO_TRACE: n = 19 (JacksonDatabind-71 drops out),
12 with a shift, s = 0.63, DOES NOT REPLICATE. Per project: JacksonDatabind 1 of 6 (s = 0.17, DOES NOT REPLICATE); Time 5 of 8
(s = 0.63, DOES NOT REPLICATE); Lang 3 of 3, Closure 2 of 2 and JacksonCore 1 of 1 (INCONCLUSIVE, n < 5). The batch-3/4 reading (SUPPORTED
15/17, REPLICATES 11/12) was on Lang, Math, Closure and Chart; batch 5 is the first evidence from JacksonDatabind and Time, and it does not
carry the rule over to those projects. No causal reading is drawn: project, facade kind and host sizes are confounded.

## W48 (2026-10-26): batch-6 (C10f) dispositions recorded before any batch-6 run; packaged, planned and frozen

**Construction.** Workflow `wf_dc4c62df-3b9` ran 172 agents over 8 lanes with 0 errors (25 Oct 15:40 to 26 Oct 05:15 local, 5.6 h),
with the batch-5 pipeline plus the C10f addendum (host rule by `host_mode`, mandatory reachability probe, `mr2_spec.py`). Results:
`main-run/batch6_build_audit_results.json` (`3da07ae468bb…`), `analysis/batch6_dispositions.json`
(`cc0ce9f6ff47…`; with `facade_reuse_of`, `host_mode`, task and builder `host_lines`, probe summary),
`analysis/batch6_trace_checks.json` (`e77e7532cabc…`).

**Dispositions: 38 ACCEPTED, 22 UNBUILDABLE, 2 UNBUILDABLE (local trace); 0 REJECTED, 0 FLAGGED.**
ACCEPTED by project: Cli 4, Codec 8, Collections 7, Compress 9, Gson 3, JacksonCore 1, JacksonDatabind 1, Jsoup 2, Math 3; 37 in the largest5 regime and 1 (JacksonDatabind-103) in the 1500
regime; 32 distinct facades, 6 recorded reuses. Every ACCEPTED instance has validation READY (16 gates),
audit CONFIRMED, checker NO_TRACE, mechanism and tier `MAIN_RUN_C10F`, and a recorded reachability probe (an existing test reached the facade).
Redesigned once: JacksonDatabind-103, Codec-4, Codec-8, Compress-8, Compress-26, Gson-14, Gson-16. Host sizes (hop 1 → 5) are recorded per instance; the smallest accepted host is 276
lines (Cli-26), the largest5 fifth hosts range 276–1,468.

| Rank | Instance | Regime | Host lines | Redesigned | Facade reuse of | Spec sha256 |
|---|---|---|---|---|---|---|
| 129 | JacksonDatabind-103 | 1500 | 1777,1756,4211,2177,1949 | yes | — | d78b9781389c |
| 130 | Cli-26 | largest5 | 984,674,399,385,276 | no | — | 96e366558d36 |
| 131 | Cli-31 | largest5 | 1020,705,689,430,388 | no | Cli-26 | ef1edf4137a0 |
| 132 | Cli-34 | largest5 | 1042,705,689,430,386 | no | Cli-26 | 8b3d57dab3fd |
| 133 | Cli-40 | largest5 | 1092,1012,781,546,429 | no | — | 5916597e4bd2 |
| 134 | Codec-2 | largest5 | 1104,536,406,388,365 | no | — | b51b09656305 |
| 135 | Codec-4 | largest5 | 1105,582,407,387,361 | yes | — | 8bf345dde400 |
| 136 | Codec-5 | largest5 | 1105,582,407,387,361 | no | — | 6fd740faf7cc |
| 137 | Codec-7 | largest5 | 1105,582,492,407,387 | no | — | b3ac88073e7d |
| 138 | Codec-8 | largest5 | 1105,582,492,407,387 | yes | Codec-4, Codec-5, Codec-7 | be32af79cd04 |
| 139 | Codec-9 | largest5 | 1105,750,582,428,407 | no | — | f9f5d4e8347e |
| 140 | Codec-11 | largest5 | 1105,758,618,582,511 | no | — | 55cd7e5ea537 |
| 141 | Codec-13 | largest5 | 1009,819,775,697,545 | no | — | 49c2a043737d |
| 145 | Collections-3 | largest5 | 2084,1994,1716,1644,1467 | no | — | cdb0da584c1d |
| 146 | Collections-5 | largest5 | 2085,1995,1717,1645,1468 | no | — | 44fefd3df8b3 |
| 147 | Collections-13 | largest5 | 2085,1995,1678,1468,1333 | no | — | f12e8004fa98 |
| 148 | Collections-15 | largest5 | 2085,1995,1784,1678,1468 | no | Collections-5 | d26ae5bc650e |
| 149 | Collections-16 | largest5 | 2085,1995,1784,1678,1468 | no | Collections-5 | b7ed622c4a35 |
| 152 | Collections-19 | largest5 | 2138,1761,1744,1486,1447 | no | — | a20ef616b583 |
| 153 | Collections-21 | largest5 | 2172,1805,1779,1447,1389 | no | — | 31990fd3c910 |
| 158 | Compress-8 | largest5 | 1881,995,969,888,745 | yes | — | eaef433742f4 |
| 160 | Compress-14 | largest5 | 1886,1495,1048,969,926 | no | — | 53b7c3932104 |
| 161 | Compress-17 | largest5 | 1495,1340,1071,1053,972 | no | — | 8f04e0cd42f5 |
| 162 | Compress-24 | largest5 | 1501,1329,1083,1073,1072 | no | — | aef7f8abd480 |
| 163 | Compress-26 | largest5 | 1501,1329,1083,1074,1073 | yes | — | 43a7663c9587 |
| 164 | Compress-27 | largest5 | 1504,1329,1083,1074,1073 | no | — | 8e78dd69d2fc |
| 165 | Compress-31 | largest5 | 1613,1329,1121,1082,1073 | no | — | 7ae32a40b43d |
| 166 | Compress-35 | largest5 | 1623,1329,1132,1131,1108 | no | — | 7068c441ef11 |
| 169 | Compress-45 | largest5 | 1686,1334,1259,1258,1136 | no | — | 7f2beb1ec016 |
| 170 | Gson-1 | largest5 | 1118,570,566,553,387 | no | — | 5127be527f77 |
| 171 | Gson-14 | largest5 | 1617,989,590,380,659 | yes | — | bb694e50ef5a |
| 172 | Gson-16 | largest5 | 1617,989,597,384,659 | yes | — | 4cd6742558d7 |
| 174 | JacksonCore-1 | largest5 | 3157,2006,1913,1853,1482 | no | — | ef685a69f349 |
| 179 | Jsoup-53 | largest5 | 1237,1016,706,702,694 | no | — | 8b3edb045c0c |
| 181 | Jsoup-60 | largest5 | 1290,1114,750,706,703 | no | Jsoup-53 | 1757913b59c8 |
| 186 | Math-92 | largest5 | 1832,1621,1499,1407,1244 | no | — | 8af19abdde16 |
| 187 | Math-93 | largest5 | 1832,1621,1499,1407,1244 | no | — | 2a870b992d29 |
| 188 | Math-94 | largest5 | 1832,1621,1499,1407,1244 | no | — | 94710806f2fa |

UNBUILDABLE (24): Codec-14, Codec-17, Codec-18, Collections-17, Collections-18, Collections-23, Collections-24, Collections-25, Compress-7, Compress-10, Compress-36, Compress-39, Gson-18, JacksonDatabind-5, Jsoup-3, Jsoup-25, Jsoup-28, Jsoup-58, Jsoup-74, Jsoup-87, JxPath-5, Math-91, Math-99, Math-104. Reasons are the brief's step 7 (no fault that exactly one existing
test catches; nothing to split; no unique owner), as the pre-registration expected for short factory and wrapper facades; Collections-25 and
Gson-18 were TRACE on both versions. Every reachability probe found at least one existing test reaching the facade, so the pool v2 strict check
held; the batch-5 false-positive cause did not recur.

**Packaging and integrity.** `new_bug_variants/<P>/` directories were created for Cli, Codec, Collections, Compress, Gson and Jsoup (new, empty)
before `mr_package.py` ran for the 38 (`main-run/batch6_packaging.log`, `e39cde321ba8…`). `review/VARIANT_KEY.json`
grew from 97 to 135 entries (67 MAIN_RUN_C10 + 38 MAIN_RUN_C10F). `mr_build_records.py`: `INSTANCE_BUILD_LOG.csv` 167 rows (62 batch-6),
`INSTANCE_PROVENANCE.csv` 108 rows (38 batch-6). Checkpoints after packaging: batch-1/2, batch-3, batch-4 and batch-5 manifests and the batch-5
and batch-6 frozen-hash files all 0 mismatches (see the console record of this entry's commands). `/private/tmp`: the builders' scratch
(`c36v2-probe`, `codec4-v2-probe`, `c5alt-viewhop4`, `codec4-v2-correct`; this session's agents, no open handles) was removed by exact path;
`mx_tmp_audit` CLEAN.

**Plans and freeze.** Eight blocks in batch-6 order (5,5,5,5,5,5,5,3), 5 runs each, seeds 202610261–8: block1 `a8ec500902ac…` (JacksonDatabind-103, Cli-26, Cli-31, Cli-34, Cli-40); block2 `7f519e1b1bc5…` (Codec-2, Codec-4, Codec-5, Codec-7, Codec-8); block3 `956b3e7234d6…` (Codec-9, Codec-11, Codec-13, Collections-3, Collections-5); block4 `b1276d657acb…` (Collections-13, Collections-15, Collections-16, Collections-19, Collections-21); block5 `14c2287fed63…` (Compress-8, Compress-14, Compress-17, Compress-24, Compress-26); block6 `a68117e5598e…` (Compress-27, Compress-31, Compress-35, Compress-45, Gson-1); block7 `c079ad832db8…` (Gson-14, Gson-16, JacksonCore-1, Jsoup-53, Jsoup-60); block8 `72b264150994…` (Math-92, Math-93, Math-94).
`FREEZE.json` backed up to `analysis/verification/backup/FREEZE.before_W48_b6.json`; the eight plans were added, bound to w55 (freeze sha256
`31f422cbb9e7…`). The driver's `--verify-only` passed for all eight.

**Cost guard** (`--left 38 --cap 500`): see the console record; C ≈ $206.71 before batch 6. Expected batch-6 run cost about 190 × $0.43 ≈ $82,
cumulative about $289.

**Robustness raters.** Launched before block 1 (2 per accepted gold, 76 blind sessions, labels H01–H38); results in
`analysis/batch6_trace_robustness.json` (W49). Dispositions are not changed by them.

**Launch.** Under W45, `scripts/mr_run_blocks.sh w55 MR_batch6 500 plans/MR_batch6_block1..8_gpt55.json` starts immediately after this entry.

## W49 (2026-10-26): batch-6 robustness ratings (pre-registered secondary)

**Robustness.** Workflow `wf_be94bb02-de7` ran 76 blind single-gold sessions (2 extra raters per accepted C10f gold, shuffled labels
H01–H38, gold text given as a file; 0 errors, 5.5 min). Results: `main-run/analysis/batch6_trace_robustness.json` (sha256 `ad7f74cd2708…`).

| Outcome | Instances | Count |
|---|---|---|
| Both extra raters NO_TRACE | — | 34 of 38 |
| One extra rater TRACE | Collections-15 (T4), Collections-16 (T4), Collections-21 (T4) | 3 |
| Both extra raters TRACE | JacksonCore-1 (T3; T3) | 1 |

- The majority of 3 raters is NO_TRACE for 37 of 38 golds.
- Dispositions are unchanged, as pre-registered. The batch-6 runs had already started under W45/W48 when the ratings completed; the
  pre-registration places the raters before block 1 as a secondary record, and the ratings do not gate the runs.

## W50 (2026-10-26): batch 7 (cell C10i, the paired static/instance bridge) pre-registered; tooling and hashes

**Pre-registration.** `main-run/BATCH7_PREREGISTRATION.md` (sha256 `8116593a1e21…`). 19 bugs that already have
an ACCEPTED static-facade instance (batches 1, 3, 4, 5, 6) receive a second instance with an **instance-method facade** on the same fixed
revision and the same five hosts (`main-run/bridge7_tasks.json`, `abedf91782c0…`; selection in
`main-run/batch7_prep/selection.md`). 15 distinct instance facades, 4 recorded reuses. Primary reading: the within-bug paired difference
in shifted runs; everything else descriptive.

**Tooling (copies; the pinned originals are unchanged).** `construction/mainrun/BUILD_BRIEF_C10I_ADDENDUM.md`
(`3be3eafbfcd8…`: variants V1–V5, the not-allowed list, independence from the static instance, MI- paths,
reachability probe); `scripts/mr3_spec.py` (`f4e673bd7697…`: iid `MI-<key>`, mechanism and tier `MAIN_RUN_C10I`);
`scripts/mr3_build_records.py` (`b09afad8f564…`: reads `bridge*_tasks.json`, writes `*_C10I.csv`); `scripts/mr3_report.py`
(`5266ddd6c3bf…`: tier `MAIN_RUN_C10I`, `MAIN_RUN_C10I_*` files). Key preflight for the 19: clean.

**Integrity.** `main-run/analysis/AMENDMENTS_through_W49.md` (`cbbdbf29bce1…`) is the pinned prefix for
`batch7_frozen_hashes.json`, written immediately after this entry. Construction starts after the batch-6 runs finish (no construction during
paid runs); the batch-6 manifest is recorded before any batch-7 row.

**W50 addendum (errata, 2026-10-25 evening +1100).**
- **Dates.** The headers of W48, W49, W50 and of `BATCH7_PREREGISTRATION.md` say 26 October; the entries were written on 25 October between
  20:31 and 20:50 local time (+1100), after the batch-6 runs had started at 09:34Z (= 20:34 local). W43's "24 Oct 06:20 to 18:20 UTC+11" for
  the batch-5 construction also conflates zones: the workflow ran from about 04:20Z on 24 October for 12.0 h. Timestamps inside the record
  files (UTC, suffixed Z) are authoritative; the entry headers are not corrected in place.
- **Record-writer defect, corrected.** `mr_build_records.py` applied the disposition table only to batches 3–5 (an explicit tuple), so three
  batch-6 rows whose last version had validation READY and audit CONFIRMED but a disposition of UNBUILDABLE were written as ACCEPTED:
  Collections-25 and Gson-18 (UNBUILDABLE, local trace) and Compress-36 (redesign UNBUILDABLE). `INSTANCE_PROVENANCE.csv` therefore had 108
  rows. The script now applies the table to every batch that has a dispositions file (`4a7faf44d4ce…` → `ae770b410e23…`);
  regenerated: build log 167 rows with 38 batch-6 ACCEPTED, provenance 105 rows. The batch-1/2, 3, 4 and 5 manifests still verify (0 mismatches).
  `batch5_frozen_hashes.json` and `batch6_frozen_hashes.json` now report exactly one mismatch each, this script; they are not rewritten
  (they document the state at those builds). No packaged variant, key entry or plan was affected: packaging used the dispositions file.
- **Consequence for batch 7.** The selection in `BATCH7_PREREGISTRATION.md` said "Of the 108 ACCEPTED bugs"; corrected to 105 (none of the 19
  pairs involves the three instances). New sha256 `0832640a129e…`; `batch7_frozen_hashes.json` rewritten before any
  batch-7 build (0 mismatches), now also pinning `analysis/diagnosis_notes_batch5.json` (the batch-5 output promised in its pre-registration,
  written today; descriptive coordinator notes only, read by `mr_report.py` without error).
- Found by the E16 evidence-card verifier (`wf_f68304fb-419`), whose card `thesis_writeup/_draft_v3/evidence/E16_all-bugs-extension-batches5-7.md`
  records these items in its S12.

## W51 (2026-10-26, 00:55 +1100 = 2026-10-25 13:55Z): batch-6 (C10f) runs complete; results, reading, records

**Runs.** `scripts/mr_run_blocks.sh w55 MR_batch6 500 plans/MR_batch6_block1..8_gpt55.json` ran the eight blocks from 09:34:32Z to
13:45:19Z on 25 October (4 h 11 min); log `diagnostic/run_blocks_MR_batch6.out` (sha256 `60170704d206…`). The guard ran before every block
(C = 206.71, 215.49, 229.52, 240.59, 251.48, 260.44, 271.70, 280.94; k = 5 at blocks 1–7 and k = 3 at block 8, which has 3 instances); the
tmp audit was CLEAN and the driver's `--verify-only` passed at every block; 0 halts. 190 records, 190 valid, 0 excluded, 0 timeouts, 0 runs
without an answer. Run cost $78.39 (median run 70 s, median 16.5 tool calls); cumulative recorded $279.84, including estimates $286.74
(`mr_cost_guard.py --left 0 --cap 500`: C = 286.7417).

**Scoring.** Frozen `mx_metrics.py` (`analysis/per_run.json` `b1b5fb2c9e79…`), then `scripts/mr2_report.py`: `MAIN_RUN_C10F_RUNS.csv`
(`fc4d5dc3b215…`, 190 rows), `MAIN_RUN_C10F_RESULTS.csv` (`fb8503438c2e…`, 38 rows), `SHIFTED_INSTANCES_C10F.md`,
`FAILED_TO_TRANSFER_C10F.md`, `COST_LEDGER_C10F.csv`, `analysis/main_run_c10f_summary.json` (`e582ba663f24…`). `mr_report.py` was not
re-run: no C10 row changed, and the batch-5 manifest verifies.

**Result: 38 C10f instances tested, 30 with at least one shift; 108 of 190 answered runs shifted.**

| Scope (BATCH6_PREREGISTRATION.md §5) | n | With ≥ 1 shift | s | Shifted / answered | Reading (batch-3 thresholds) |
|---|---|---|---|---|---|
| Primary: distinct facade | 32 | 26 | 0.8125 | 99/160 | REPLICATES |
| Secondary: recorded facade reuse | 6 | 4 | 0.667 | 9/30 | DOES NOT REPLICATE (n = 6) |
| All ACCEPTED | 38 | 30 | 0.789 | 108/190 | INCONCLUSIVE (between 2/3 and 4/5) |
| Host regime largest5 | 37 | 30 | 0.811 | 108/185 | REPLICATES |
| Host regime 1500 | 1 | 0 | — | 0/5 | INCONCLUSIVE (n < 5) |
| Majority of 3 raters NO_TRACE | 37 | 29 | 0.784 | 107/185 | INCONCLUSIVE |
| All 3 raters NO_TRACE | 34 | 26 | 0.765 | 100/170 | INCONCLUSIVE |

Per project (tested, with a shift, shifted/answered): Cli 4, 2, 4/20; Codec 8, 6, 26/40; Collections 7, 6, 22/35 (REPLICATES); Compress 9, 8,
32/45 (REPLICATES); Gson 3, 3, 10/15; JacksonCore 1, 1, 1/5; JacksonDatabind 1, 0, 0/5; Jsoup 2, 2, 7/10; Math 3, 2, 7/15 (the others n < 5
or between the thresholds). Instances without a shift (all five runs gold-first): JacksonDatabind-103, Cli-26, Cli-31, Codec-7, Codec-8,
Collections-13, Compress-31, Math-93.

Failure modes (190 valid runs, mechanical labels): GOLD_FIRST 82, ENTRY_POINT_BIAS 99, GOLD_NOT_REACHED 8, UPSTREAM_HOP_FIRST 1; rank-1
category ENTRY_POINT 107, GOLD 82, DECOY 1. The dominant wrong answer is again the facade.

Host size (descriptive, as pre-registered). By gold-host tercile: 276–511 lines, 8 of 12 instances with a shift (26/60 runs); 545–1,108
lines, 12 of 13 (48/65); 1,136–1,949 lines, 10 of 13 (34/65). By smallest-host tercile: 276–407, 8 of 12 (28/60); 429–1,108, 12 of 13
(46/65); 1,136–1,756, 10 of 13 (34/65). Small hosts did not lower the shift rate; the relation is not monotone. (From
`analysis/batch6_prediction.json` `per_instance.host_lines`.)

**Reading script.** `scripts/mr_batch3_eval.py` (`f4a0dea4906f…` → `5054fc8a89c7…`): for `--batch batch6` it reads
`MAIN_RUN_C10F_RESULTS.csv` (the C10f rows are not in `MAIN_RUN_RESULTS.csv`), uses the replication labels, and adds the C10f scopes of the
pre-registration (`c10f_primary_distinct_facade`, `c10f_secondary_recorded_reuse`, `c10f_per_host_regime`) and the host covariates per
instance. The batch-3, 4 and 5 outputs were regenerated after the edit and compared byte for byte with copies taken before it: identical.
Output `analysis/batch6_prediction.json` (`a403abe377ec…`). Its `primary` key is the script's generic scope (all ACCEPTED with 5 valid runs,
n = 38); the cell's pre-registered primary is `c10f_primary_distinct_facade` (n = 32).

**Integrity.** `scripts/mr_integrity.py` (`6dd6fe7be507…` → `a034203ed79d…`): plan patterns for batches 6 and 7; the two C10f CSVs are
covered where they exist (no batch-1–5 instance has a row there). Batch-1/2, 3, 4 and 5 manifests: 0 mismatches before and after the edit
(551, 551, 404, 668 entries). `main-run/analysis/b6_integrity_manifest.json` recorded (`cd17d89a66a7…`; 1,255 entries: 164 instance files,
185 construction files, 152 variant files, 38 key entries, 8 plans, 190 ledger lines, 190 per-run rows, 190 + 38 C10f CSV rows, 62 + 38
build-log and provenance rows) and verified with 0 mismatches, before any batch-7 row (W50). `batch5_frozen_hashes.json` and
`batch6_frozen_hashes.json` now report two documented mismatches each (`mr_build_records.py`, W50 addendum; `mr_batch3_eval.py`, this entry)
and are not rewritten. `batch7_frozen_hashes.json` is rewritten immediately after this entry, with `main-run/analysis/AMENDMENTS_through_W51.md`
as the pinned prefix, now also pinning the batch-6 run outputs (the C10f files, `batch6_prediction.json`, `b6_integrity_manifest.json`, the
eight batch-6 plans, the block logs) and the two edited scripts.

**Programme.** C10: 67 tested, 50 with a shift (194/335). C10f: 38 tested, 30 with a shift (108/190). Reported by cell, never pooled in a
headline without the composition (W42). Batch 7 (C10i) construction starts after the frozen-hash rewrite (W50: after the batch-6 runs and
the batch-6 manifest). `SUPERVISOR_PROGRESS_UPDATE.md` is rewritten as update 6. Thesis integration is deferred at the user's instruction
of 26 October ("do not modify thesis yet"); results stay in these records.

**W51 addendum (launch).** `batch7_frozen_hashes.json` rewritten at 2026-10-25T13:57:12Z (sha256 `d27cfead4b0c…`; 137 files + the
prefix `AMENDMENTS_through_W51.md` `bd7154f68ad4…`; verify 0 mismatches). Key preflight for the 19 pairs re-checked (no `designs/<key>__i.py`,
`specs/MI-<key>.json`, `instances/MI-<key>/`; all 19 fixtures with `.git`); `mx_tmp_audit` CLEAN; no `/private/tmp/d4j-mi-*`. One allowed
candidate sits in a host class and is excluded by the facade-class rule: JacksonDatabind-103's `DeserializationContext.isEnabled`
(DeserializationContext is a host); its two other candidates stand. Batch-7 construction workflow `wf_46793795-700` launched at
2026-10-25T14:0xZ (26 Oct 01:0x +1100): 19 tasks in 7 lanes, builder → auditor + blind checker → one redesign, model opus, with the C10I
addendum, `mr3_spec.py`, `mr_gold_text.py MI-<key>` and an added audit item `g_c10i_rules` (the addendum's not-allowed list).
`SUPERVISOR_PROGRESS_UPDATE.md` rewritten as update 6.

## W52 (2026-10-26, 03:5x +1100 = 2026-10-25 16:5xZ): batch-7 (C10i) dispositions recorded before any batch-7 run; packaged, planned and frozen

**Construction.** Workflow `wf_46793795-700` ran 62 agents over 7 lanes with 0 errors (2026-10-25 14:03Z to 16:47Z, 2 h 47 min), with the
batch-6 pipeline plus the C10I addendum (instance-method facade, variants V1–V5, same hosts as the static pair, independence from the static
instance, reachability probe, `mr3_spec.py`, `mr_gold_text.py MI-<key>`) and an added audit item `g_c10i_rules` (the addendum's not-allowed
list). Results: `main-run/bridge7_build_audit_results.json` (`6affa8f140aa…`), `analysis/bridge7_dispositions.json` (`dca9edd4d6d9…`),
`analysis/bridge7_trace_checks.json` (`f0a9a18865d7…`), written by `main-run/batch7_prep/make_dispositions.py` (`e0cca25c9c78…`), which
re-applies the pre-registered table to the last version built and agrees with the workflow's own status for all 19.

**Dispositions: 17 ACCEPTED, 2 UNBUILDABLE; 0 REJECTED, 0 FLAGGED, 0 local trace.** Every ACCEPTED instance has validation READY (16 gates),
audit CONFIRMED with `g_c10i_rules = true`, checker NO_TRACE, mechanism and tier `MAIN_RUN_C10I`, an existing trigger, a facade in a
real-bug modified class, a recorded reachability probe (an existing test reached the facade), and **hosts identical, in hop order, to its
static pair** (checked spec against task record for all 17). Facade variants: V2 (receiver) 9, V1 (state as parameters) 6, V1+V2 2; no V3–V5
was needed. Host regimes: 1500 for 9, largest5 for 8. Redesigned once: Codec-11 (v1 TRACE, T3), Collections-13 (v1 audit REJECTED: the gold
sat in a host other than the fifth listed; v2 uses the listed hosts), Time-12 (v1 TRACE, T3).

| Rank | Task | Static facade (pair) | Instance facade | Variant | Gold | Hosts | Redesigned | Reuse of | Variant id | Spec sha256 |
|---|---|---|---|---|---|---|---|---|---|---|
| 191 | Codec-11__i | QuotedPrintableCodec.decodeQuotedPrintable | QuotedPrintableCodec.encode | V1 | PhoneticEngine.appendPrintable | largest5 | yes | — | CTV-F612F3 | e7438607c7e8 |
| 192 | Codec-8__i | Base64.encodeBase64 | Base64.decode | V1 | QuotedPrintableCodec.decodeBase64Characters | largest5 | no | — | CTV-1AFDA3 | 1145d4a395b6 |
| 193 | Collections-13__i | ExtendedProperties.convertProperties | ExtendedProperties.getInclude | V1 | FastArrayList.effectiveKey | largest5 | yes | — | CTV-8550A0 | 89887b4164ae |
| 194 | Collections-5__i | SetUniqueList.decorate | SetUniqueList.addAll | V2 | CursorableLinkedList.insertInOrder | largest5 | no | — | CTV-3118F2 | bd3ad493a9f8 |
| 195 | Collections-15__i | SetUniqueList.decorate | SetUniqueList.addAll | V2 | CursorableLinkedList.insertEachAt | largest5 | no | Collections-5__i | CTV-9FE0C5 | 1d817503921b |
| 196 | Collections-16__i | SetUniqueList.decorate | SetUniqueList.addAll | V2 | CursorableSubList.insertSequence | largest5 | no | Collections-5__i, Collections-15__i | CTV-2570C4 | fe029d4e16cb |
| 197 | Collections-19__i | SetUniqueList.setUniqueList | SetUniqueList.retainAll | V1+V2 | PatriciaTrie.removeElementsNotIn | largest5 | no | — | CTV-D1784E | a84fc157edb1 |
| 198 | Collections-21__i | SetUniqueList.setUniqueList | SetUniqueList.retainAll | V1+V2 | AbstractHashedMap.removeAllBut | largest5 | no | — | CTV-720302 | 6e4ed24d63d6 |
| 199 | JacksonCore-1__i | NumberInput.inLongRange | — | — | UNBUILDABLE | — | — | — | — | — |
| 200 | JacksonDatabind-103__i | ClassUtil.isLocalType | BasicBeanDescription.findAnySetterAccessor | V1 | ObjectReader.isUsableAnySetter | 1500 | no | — | CTV-A80261 | abd7ddeea7ff |
| 201 | Lang-22__i | Fraction.getFraction | Fraction.toProperString | V1 | DateUtils.properFractionString | 1500 | no | — | CTV-060A2D | 6723255d966a |
| 202 | Lang-49__i | Fraction.getReducedFraction | Fraction.pow | V2 | FastDateFormat.raisedFraction | 1500 | no | — | CTV-CA9E24 | 40b8cd807e38 |
| 203 | Lang-38__i | FastDateFormat.getInstance | — | — | UNBUILDABLE | — | — | — | — | — |
| 204 | Math-36__i | BigFraction.getReducedFraction | BigFraction.floatValue | V1 | BOBYQAOptimizer.floatQuotient | 1500 | no | — | CTV-E05BD9 | 90d97a2e712b |
| 205 | Math-55__i | Vector3D.angle | Vector3D.orthogonal | V2 | FastMath.unitNormal | 1500 | no | — | CTV-15ED2F | 5063a23646b6 |
| 206 | Time-12__i | LocalDateTime.fromDateFields | LocalDate.toDate | V2 | DateTimeFormatterBuilder.javaDayStart | 1500 | yes | — | CTV-4BBE98 | 86becdb450c2 |
| 207 | Time-9__i | DateTimeZone.forOffsetMillis | DateTimeZone.getOffsetFromLocal | V2 | LocalTime.localMillisOffset | 1500 | no | — | CTV-89F873 | 8dda3aaa1f6a |
| 208 | Time-17__i | DateTimeZone.setProvider | DateTimeZone.getOffsetFromLocal | V2 | Period.wallOffsetAt | 1500 | no | Time-9__i | CTV-0E70C3 | 5263f26876d3 |
| 209 | Time-19__i | DateTimeZone.forOffsetHoursMinutes | DateTimeZone.getMillisKeepLocal | V2 | LocalDate.millisAtSameLocal | 1500 | no | — | CTV-D0852E | 5af456725cfe |

UNBUILDABLE (2). JacksonCore-1: all three allowed facades are reached by tests, but none admits a quiet omission that exactly one existing
test catches (`expandCurrentSegment` is asserted non-null only; `size` and `contentsAsString` states are each caught by 0, 2 or more tests;
18 omissions screened on the full suite). Lang-38: the single allowed candidate, `FastDateFormat.format(Object, StringBuffer, FieldPosition)`,
is reached by no existing test (full-suite probe: 0 of 1,624 tests fail); the pool's strict name check had matched `format(` calls of the other
overloads, an overload false positive of the kind the reachability probe exists to catch. Both pairs leave the analysis (the pre-registration
expected UNBUILDABLE outcomes for short methods).

**Facade reuse, recorded on the facade actually chosen.** The task file's `facade_reuse_of` was computed on each bug's best-ranked candidate
(4 planned reuses). The builders chose: Collections-15 and -16 `addAll` (reuse of Collections-5, as planned); Time-17 `getOffsetFromLocal`
(reuse of Time-9, as planned); Time-19 `getMillisKeepLocal` (distinct; the plan had it reusing Time-9/-17). `make_dispositions.py` therefore
records `facade_reuse_planned` and `facade_reuse_effective` separately; effective reuse = an earlier ACCEPTED batch-7 instance with the
identical facade. **14 distinct instance facades, 3 effective reuses.** The pre-registered primary (pairs with a distinct instance facade) has
n = 14 if all 17 run cleanly.

**Packaging and records.** `mr_package.py` for the 17 (`main-run/bridge7_packaging.log`, `fd91ff90498f…`); `review/VARIANT_KEY.json` 135 → 152
entries (`4ce942a1f88b…`; all 135 earlier entries byte-identical; 17 × `MAIN_RUN_C10I`). `mr3_build_records.py`: `INSTANCE_BUILD_LOG_C10I.csv`
19 rows (`fe5313172c4d…`), `INSTANCE_PROVENANCE_C10I.csv` 17 rows (`fc18d822797e…`; facade in a real-bug class 17/17, existing trigger 17/17).
The C10/C10f files are untouched. Checkpoints after packaging and the key: batch-1/2, 3, 4, 5 and 6 manifests and `batch7_frozen_hashes.json`
all 0 mismatches. `/private/tmp`: no `d4j-mi-*` scratch left by the builders; `mx_tmp_audit` CLEAN.

**Plans and freeze.** Four blocks in batch-7 order (5, 5, 5, 2), 5 runs each, seeds 202610271–4: block1 `847754dbd177…` (MI-Codec-11,
MI-Codec-8, MI-Collections-13, MI-Collections-5, MI-Collections-15); block2 `ab0f4b75a10d…` (MI-Collections-16, MI-Collections-19,
MI-Collections-21, MI-JacksonDatabind-103, MI-Lang-22); block3 `dc43b53f0242…` (MI-Lang-49, MI-Math-36, MI-Math-55, MI-Time-12, MI-Time-9);
block4 `0c0f0db2a207…` (MI-Time-17, MI-Time-19). `mx_plan.py` labelled every slot condition and level `MAIN_RUN_C10I`. `FREEZE.json` backed
up to `analysis/verification/backup/FREEZE.before_W52_b7.json`; the four plans added, bound to w55 (freeze sha256 `41056649843d…`).

**Cost guard** (`--left 17 --cap 500`): C = 286.74, k = 5, worst case after a block $339.27. Expected batch-7 run cost about 85 × $0.43 ≈ $37.

**Paired analysis tool.** `main-run/batch7_prep/pairs.py` (`12681dfab610…`) implements the pre-registered reading (per-pair difference
instance minus static, mean and exact sign test, 2×2 of instance vs static success; primary over distinct instance facades; by variant, by
host regime; the C10i cell alone). Tested on the static side before any batch-7 run: all 19 static rows resolve to the paired variant ids;
15 of the 19 static instances had a shift (Codec-8, Collections-13, JacksonDatabind-103 and Time-12 did not).

**Robustness raters.** Launched before block 1 (2 per accepted gold, 34 blind sessions, labels I01–I17 shuffled with seed 20261027, gold text
given as a file); results to `analysis/bridge7_trace_robustness.json` (W53). Dispositions are not changed by them.

**Launch.** Under W45, `scripts/mr_run_blocks.sh w55 MR_batch7 500 plans/MR_batch7_block1..4_gpt55.json` starts immediately after this entry
(lid check, server check, guard, tmp audit and `--verify-only` before every block). The batch-6 manifest (W51) precedes every batch-7 row.

## W53 (2026-10-26, 03:56 +1100 = 2026-10-25 16:56Z): batch-7 robustness ratings (pre-registered secondary)

**Robustness.** Workflow `wf_2bce32e5-095` ran 34 blind single-gold sessions (2 extra raters per accepted C10i gold, shuffled labels
I01–I17 with seed 20261027, gold text given as a file; 0 errors, 2.4 min). Results: `main-run/analysis/bridge7_trace_robustness.json`
(sha256 `6bdb32cc4f8c…`), written by `main-run/batch7_prep/make_robustness.py` from the workflow output and the label map.

| Outcome | Instances | Count |
|---|---|---|
| Both extra raters NO_TRACE | — | 16 of 17 |
| One extra rater TRACE | Time-17__i (T4, one rater) | 1 |
| Both extra raters TRACE | — | 0 |

- The majority of 3 raters is NO_TRACE for 17 of 17 golds.
- Dispositions are unchanged, as pre-registered. The batch-7 runs had started under W45/W52 (block 1 at 16:52:48Z) when the ratings
  completed at 16:55Z; the pre-registration places the raters before block 1 as a secondary record, and the ratings do not gate the runs.

## W54 (2026-10-26, 04:4x +1100 = 2026-10-25 17:4xZ): batch-7 runs halted by the provider's credit balance; block 1 complete, block 2 partial; continuation frozen; paid runs paused

**What happened.** `mr_run_blocks.sh w55 MR_batch7 500 …` started block 1 at 16:52:48Z (guard C = 286.74, k = 5). Block 1 ended at
17:24:36Z: 25 records, 25 valid. Block 2 started at 17:24:37Z (guard C = 296.46, k = 5) and completed slots 0–5 (6 valid runs). At 17:33:23Z
the frozen driver's gate probe before slot 6 returned `credit_error=True` and the driver halted with **HALT_PROVIDER_CREDIT** ("the provider
reports an exhausted credit balance; no run launched"); `mr_run_blocks.sh` stopped on the chain's exit 1 (blocks 3 and 4 not started). Logs:
`diagnostic/run_blocks_MR_batch7.out` (`9b36b968e896…`), `run_MR_batch7_block1_gpt55.out` (`1087626fecce…`), `run_MR_batch7_block2_gpt55.out`
(`580460320838…`). 0 timeouts, 0 excluded records, no pending run (`diagnostic/pending_w55.json` absent), `mx_tmp_audit` CLEAN. The lid was
open and the server answered throughout; the stop is the OpenAI account's balance, which the coordinator cannot change. This is the
"uncontrollable difficulty" of W45: **paid runs are paused until the user restores the credit.** The w55 server is left running idle.

**Cost.** 31 batch-7 runs, $12.14 (median run about 60–90 s). Cumulative recorded $291.98; including estimates $299.17
(`mr_cost_guard.py --left 0 --cap 500`: C = 299.1734). Remaining batch-7 runs: 54 (19 + 25 + 10), about $23 at the batch-7 rate.

**Scored so far (frozen `mx_metrics.py`, `mr3_report.py`; not the pre-registered reading, which needs all 17 pairs).**

| Instance | Static pair (shifted/answered) | Instance facade (shifted/answered) | Instance gold ranks |
|---|---|---|---|
| Codec-11 | 4/5 | 5/5 | 9 7 7 9 7 |
| Codec-8 | 0/5 | 1/5 | 1 1 1 1 2 |
| Collections-13 | 0/5 | 4/5 | 3 1 3 3 3 |
| Collections-5 | 5/5 | 5/5 | 2 2 2 2 2 |
| Collections-15 | 2/5 | 5/5 | 2 2 2 2 2 |
| Collections-16 | 2/5 | 1/1 (partial) | 2 |
| Collections-19 | 5/5 | 0/1 (partial) | 1 |
| Collections-21 | 3/5 | 0/1 (partial) | 1 |
| JacksonDatabind-103 | 0/5 | 0/1 (partial) | 1 |
| Lang-22 | 1/5 | 0/2 (partial) | 1 1 |

Over the five complete pairs (`main-run/batch7_prep/pairs.py`, `analysis/bridge7_pairs.json`, descriptive): instance facades 20/25 shifted
runs against 11/25 for the static pairs; the four distinct-facade pairs have a mean within-bug difference of +0.30 (sign test 3 positive,
0 negative, p = 0.25); the 2×2 is 3 both-shift, 2 instance-only (Codec-8, Collections-13), 0 static-only. In Codec-11 the gold fell to ranks
7–9 (the facade first, four hops ranked above the gold). These are interim figures and are superseded by the full reading once the 17 pairs
have run.

**Scripts (C10i copies; the pinned originals are unchanged).** `scripts/mr3_report.py` (`5266ddd6c3bf…` → `e7e1fd85af27…`): the C10i build
log's `instance` is the task key `<key>__i`, so the report now keys build rows by `<key>` (before, batch and build/audit columns of
`MAIN_RUN_C10I_RESULTS.csv` were empty) and reads only `diagnosis_notes_bridge*.json` (the batch-4/5 notes files made the copy's key assertion
fail). `main-run/batch7_prep/pairs.py` (`12681dfab610…` → `9a76247c88d9…`): C10i rows matched by `instance_id`. `scripts/mr_integrity.py`
(`a034203ed79d…` → `2adcdf5aea02…`, edited before the runs): batch-7 support (`bridge7_tasks.json`, `MI-<key>` ids, the C10i CSVs); the
batch-1/2, 3, 4, 5 and 6 manifests verify with 0 mismatches before and after. `batch7_frozen_hashes.json` therefore reports two documented
mismatches (`mr3_report.py`, `mr_integrity.py`) and is not rewritten.

**Continuation (W37/W39 rule: untouched slots in the original order).** `plans/MR_batch7_block2_gpt55_cont.json` (`5a2774548efc…`) holds slots
6–24 of block 2 (19 slots: Collections-16 ×4, Collections-19 ×4, Collections-21 ×4, JacksonDatabind-103 ×4, Lang-22 ×3) with a
`continuation_of` record; no replacement slot is needed (the halt was at the gate, before any launch). `FREEZE.json` backed up to
`analysis/verification/backup/FREEZE.before_W54_b7cont.json`; the plan added, bound to w55 (freeze sha256 `c84bf9a9fcff…`). Driver
`--verify-only` on the continuation and on blocks 3 and 4: OK OK OK. Resume command, to be run only after the credit is restored:
`scripts/mr_run_blocks.sh w55 MR_batch7cont 500 plans/MR_batch7_block2_gpt55_cont.json plans/MR_batch7_block3_gpt55.json plans/MR_batch7_block4_gpt55.json`
(lid, server, guard, tmp audit and verify-only before every block, as before). The batch-7 manifest is recorded after the last block.

**W54 addendum (resume).** The user restored the OpenAI credit and instructed "充值好了，继续跑试验" (2026-10-25 12:14Z). Pre-checks: lid open,
server w55 answering, `mx_tmp_audit` CLEAN, no pending run. `scripts/mr_run_blocks.sh w55 MR_batch7cont 500 plans/MR_batch7_block2_gpt55_cont.json
plans/MR_batch7_block3_gpt55.json plans/MR_batch7_block4_gpt55.json` starts immediately after this addendum (guard, tmp audit and verify-only before
every block, as before).

## W55 (2026-10-27, 00:4x +1100 = 2026-10-26 13:4xZ): batch-7 (C10i) runs complete; paired reading; records

**Runs.** After the credit was restored (W54 addendum), `mr_run_blocks.sh w55 MR_batch7cont 500 …` ran the block-2 continuation (19 slots,
12:14:11Z–12:42:58Z), block 3 (12:42:59Z–13:19:16Z) and block 4 (13:19:17Z–13:36:49Z); guard before each: C = 299.17, 307.70, 318.78
(k = 5, 5, 2); tmp audit CLEAN and `--verify-only` passed at every block; 0 halts. With block 1 and block-2 slots 0–5 (W54): **85 records,
85 valid, 0 excluded, 0 timeouts, 0 without an answer.** Batch-7 run cost $36.70; cumulative recorded about $316.54, including estimates
$324.21 (`mr_cost_guard.py --left 0 --cap 500`). Log `diagnostic/run_blocks_MR_batch7cont.out` (`f8bbd9d41dd2…`).

**Scoring.** Frozen `mx_metrics.py` (`analysis/per_run.json` `2afaba23c480…`), `scripts/mr3_report.py` (W54 version): `MAIN_RUN_C10I_RUNS.csv`
(`3604db38933a…`, 85 rows), `MAIN_RUN_C10I_RESULTS.csv` (`f5b731f6e523…`, 17 rows, batch `bridge7`), `analysis/main_run_c10i_summary.json`
(`59d0bc0e63a0…`), the C10i markdown and cost files. **C10i cell: 17 tested, 12 with at least one shift, 40 of 85 runs shifted.** Failure
modes: GOLD_FIRST 45, ENTRY_POINT_BIAS 38, GOLD_NOT_REACHED 1, UPSTREAM_HOP_FIRST 1.

**Pre-registered paired reading** (`main-run/batch7_prep/pairs.py`, `analysis/bridge7_pairs.json` `b6b438311afd…`; descriptive):

| Scope | Pairs | Instance facade shifted/answered | Static facade shifted/answered | Mean diff (instance − static) | Sign test (+/−, p) | 2×2 (both / instance only / static only / neither) |
|---|---|---|---|---|---|---|
| **Primary: distinct instance facade** | 14 | 30/70 | 40/70 | −0.14 | 6/5, p = 1.00 | 7 / 3 / 3 / 1 |
| All pairs | 17 | 40/85 | 49/85 | −0.11 | 8/6, p = 0.79 | 9 / 3 / 4 / 1 |
| Host regime 1500 | 9 | 13/45 | 28/45 | −0.33 | 3/4, p = 1.00 | 4 / 1 / 3 / 1 |
| Host regime largest5 | 8 | 27/40 | 21/40 | +0.15 | 5/2, p = 0.45 | 5 / 2 / 1 / 0 |
| Variant V1 (state as parameters) | 6 | 16/30 | 9/30 | +0.23 | — | 3 / 2 / 0 / 1 |
| Variant V2 (receiver) | 9 | 22/45 | 32/45 | −0.22 | — | 5 / 1 / 3 / 0 |
| Variant V1+V2 | 2 | 2/10 | 8/10 | −0.60 | — | 1 / 0 / 1 / 0 |

**Reading.** The facade's kind does not change the result in a consistent direction: as many pairs moved up as down (6 vs 5), the
counts of instances with a shift are equal (10 vs 10 in the primary), and the mean difference is small and of uncertain sign. The
per-pair differences are large in both directions (Collections-13 +0.8; Collections-19, Lang-49, Time-17 −1.0; Math-55, Time-9 −0.8), so
**within-bug variation from the construction (which method, which gold, which lie) is as large as any facade-kind effect.** The
1500/largest5 split and the V1/V2 split point in opposite directions and are confounded with project (all Time, Lang and Math pairs are
1500 and V2-heavy; all Collections and Codec pairs are largest5); they are reported, not interpreted. Per project in the cell: Codec 2/2,
Collections 5/6, Math 2/2, Lang 1/2, Time 2/4, JacksonDatabind 0/1. Codec-11 is the deepest displacement in the programme (gold ranks 7–9).

**Consequence for the extension.** C10i instances on bugs without a static facade (batch 8) can be reported in the same cell as batch 7's:
the bridge found no systematic static/instance difference that would make them a different kind of instance. They stay a separate cell in
every table (W42).

**Integrity.** `main-run/analysis/b7_integrity_manifest.json` recorded (`ec128af5439e…`; 538 entries: 68 instance files, 72 construction
files, 68 variant files, 17 key entries, 5 plans, 85 ledger lines, 85 per-run rows, 85 + 17 C10i run/result rows, 19 + 17 build/provenance
rows) and verified, 0 mismatches. Batch-1/2, 3, 4, 5 and 6 manifests: 0 mismatches. `mx_tmp_audit` CLEAN.

**Programme after batch 7** (by cell; never pooled without the composition): C10 67 tested / 50 with a shift (194/335 runs); C10f 38 / 30
(108/190); C10i 17 / 12 (40/85). **122 instances, 92 with a shift, 342 of 610 runs.**

## W56 (2026-10-27, 00:5x +1100 = 2026-10-26 13:5xZ): batch 8 (C10i on bugs without a static facade) pre-registered; checkouts, fixtures, tooling, cap

**Authorisation.** W45 and the user's instruction of 26 October ("充值好了，继续跑试验"), given in reply to the projection for about 200
instances (which said the remaining instances must come from instance-method facades on unused bugs and recommended a –600 cap), with the
23-October "不需要考虑 cost limit". **The guard cap is  from batch 8 on** (was ); everything else in W45 is unchanged.

**Pre-registration.** `main-run/BATCH8_PREREGISTRATION.md` (sha256 `45c2d0585913…`), generated by `main-run/batch8_prep/write_prereg.py`
(`cf34a5e2a1e7…`). 97 bugs not used in batches 1–7, with no static facade, whose best strictly tested public instance
candidate is V0 or V1 (`batch8_prep/make_tasks.py` `dd6acb068cd5…` over the 23-October profile; deferred list
`batch8_prep/deferred.json`: 62 V2-best bugs and 6 Closure bugs; Mockito and Csv as before). Projects: Math 24, Jsoup 14, JacksonDatabind 13,
Compress 10, Chart 8, Collections 7, Lang 7, Cli 5, Gson 3, JacksonCore 3, JacksonXml 2, Time 1; regimes 1500 48, largest5 49 (smallest fifth
host 286 lines, median 725); 62 planned-distinct facades, 35 planned reuses (the builder may pick another allowed candidate; effective reuse
is recorded on the facade chosen). Ranks 210–306.

**Checkouts and fixtures.** `scripts/mr_checkouts.py batch8_checkouts.log …`: 77 new fixed checkouts, all OK (2–5 s each; log
`main-run/batch8_checkouts.log` `a165e068b5cd…`), 20 already present. 97 fixtures `construction/fresh-mr/<key>` created by
`mr_lib.py fixture` (with `.git`). Disk 19 → 13 GB free. Hosts confirmed on the checkouts (`batch8_prep/confirm_hosts.py`
`8cc77d85eceb…`; every allowed candidate's file excluded): 7 largest5 lists differed from the pool snapshot and use the
checkout's; no task changed regime. Task file `main-run/batch8_tasks.json` (`2057de7498a5…`).

**Builder note.** `construction/mainrun/BUILD_BRIEF_C10I_B8_NOTE.md` (`b993d4bee1ea…`): no static pair (addendum §2 void);
hosts by regime (1500: the recipe's seeded draw excluding the chosen facade's file; largest5: exactly the confirmed list); distinctness
preferred through `facade_planned_by`; C10i paths. The pinned briefs and addenda are not edited.

**Tooling edits (recorded, regression-checked).** `scripts/mr3_build_records.py` (`b09afad8f564…` → `1170d9a68eea…`): also reads
`batch8_tasks.json` and `analysis/batch8_dispositions.json`; the C10i CSVs regenerate byte-identical. `scripts/mr_integrity.py`
(`2adcdf5aea02…` → `9419bfdbdb89…`): C10i ids by `fixture_key`, `MR_batch8_*` plans; the batch-1/2, 3, 4, 5, 6 and 7 manifests verify with 0
mismatches. `scripts/mr_batch3_eval.py` (`5054fc8a89c7…` → `3d4b6c02bf30…`): `--batch batch8` reads the C10i results file and adds the
C10i scopes (distinct facade, reuse, host regime, facade variant); batch-3, 4, 5 and 6 outputs byte-identical. New:
`main-run/batch8_prep/make_dispositions.py` (`ef779d473d1a…`).

**Key preflight**: clean for all 97 (no design, spec, instance, audit or history path; fixtures with `.git`; no key in batches 1–7).
`batch8_frozen_hashes.json` is written immediately after this entry, with `AMENDMENTS_through_W56.md` as the pinned prefix; construction
(workflow, model opus, 8 lanes) starts after it. No paid run takes place during construction.

**W56 addendum (launch).** `batch8_frozen_hashes.json` written at 2026-10-26T13:46:21Z (sha256 `1647e65a91b0…`; 177 files + the prefix
`AMENDMENTS_through_W56.md`; verify 0 mismatches). Batch-8 construction workflow `wf_0ddca1ab-3d6` launched at about 13:48Z (26 Oct 00:48 +1100... i.e.
27 Oct 00:48 local): 97 tasks in 8 round-robin lanes, builder → auditor + blind checker → one redesign, model opus, with the C10I addendum, the
batch-8 note, `mr3_spec.py`, `mr_gold_text.py MI-<key>` and the audit item `g_c10i_rules`.
- Erratum to the line above: the launch time is 2026-10-26 ~13:48Z = 27 October 00:48 local (+1100).
- Precision on "no static facade": 93 of the 97 bugs have no tested public static candidate (pool v2 `no_tested_static`). Four have one but
  no usable static facade: Math-26 and Math-27 (strictly tested static targets, all excluded as used elsewhere or UNBUILDABLE in a sibling
  revision; the two were among the eleven bugs dropped from batch 6 for that reason) and Compress-29 and Compress-33 (loosely tested static
  candidates only). All four are built with an instance facade like the rest; the field `static_facade_status` records the case.

## W57 (2026-10-27, ~10:0x +1100 = 2026-10-26 23:0xZ): batch-8 dispositions recorded before any batch-8 run; packaged, planned and frozen

**Construction.** Workflow `wf_0ddca1ab-3d6` ran 310 agents over 8 lanes with 0 errors (2026-10-26 ~13:48Z to 22:53Z, 9.1 h). Results
`main-run/batch8_build_audit_results.json` (`217ea85e5424…`); `analysis/batch8_dispositions.json` (`9aec7a4ed9e8…`) and
`analysis/batch8_trace_checks.json` (`28ba6d1c858b…`) by `batch8_prep/make_dispositions.py`; 0 disagreements with the workflow's status.

**Dispositions: 60 ACCEPTED, 31 UNBUILDABLE, 5 UNBUILDABLE (local trace), 1 REJECTED; 0 FLAGGED.** ACCEPTED by project: Math 15, JacksonDatabind 10,
Jsoup 9, Chart 6, Compress 6, Collections 5, Lang 5, JacksonCore 3, Time 1 (Cli, Gson and JacksonXml 0). 45 distinct facades, 15 effective
reuses; variants V1 48, V2 11, V1+V2 1; regimes 1500 35, largest5 25; redesigned once 16. Every ACCEPTED instance: validation READY, audit
CONFIRMED with `g_c10i_rules = true`, checker NO_TRACE, an allowed facade, an existing trigger, a recorded reachability probe.
- UNBUILDABLE: Chart-18, Chart-21, Cli-13, Cli-14, Cli-15, Cli-21, Compress-11, Compress-16, Compress-42, Gson-4, Gson-9, Gson-15, JacksonDatabind-41, JacksonDatabind-86, JacksonDatabind-97, JacksonXml-1, JacksonXml-3, Jsoup-22, Jsoup-41, Jsoup-57, Jsoup-90, Lang-4, Math-22, Math-27, Math-43, Math-60, Math-75, Math-76, Math-89, Math-90, Math-105. The reasons are the pre-registered kinds (no quiet omission that exactly one existing test catches; nothing to split in
  1–3-statement facades). Two new ones: Cli-13/14/15/21 — the fixed largest5 hosts create a Java package dependency cycle (util ↔ option) or
  make every chain fail an existing test on the correct configuration; and **Math-76 — an infrastructure stop**: the builder's structured
  result was forced while `mr_validate.py` was still running (G0–G3c had passed; `validation.json` has no overall verdict). It is recorded as
  UNBUILDABLE under the table and not retried.
- UNBUILDABLE (local trace): Collections-8, Collections-9, Compress-33, Jsoup-61, Lang-47. REJECTED: Cli-16.
- **Host deviations among the ACCEPTED, all recorded by the builder and confirmed by the auditor (item e):** (i) Collections-2, -7, -12: the
  listed fifth host FastArrayList is Serializable without a declared serialVersionUID, so any added method changes its computed UID and the
  pristine serialisation-compatibility tests fail (G1 on the correct configuration); replaced by the next-largest public class,
  map.AbstractHashedMap (1,328–1,329 lines), as the B8 note's substitution rule says. (ii) Ten instances (Collections-1, -2, -6, -7, -12; Jsoup-37,
  -42, -43, -48, -66, -69, -70, -93) have a hop whose seeded anchor lies in a nested class of the listed host file (Jsoup `Evaluator.*`) or in the
  package-private second class `CursorableSubList` of `CursorableLinkedList.java`: the pre-existing anchor quirk of W42, now also in C10i; the
  host files are the listed ones.

**Scratch.** `mx_tmp_audit` listed four validator scratch directories left by this session's builders (`/private/tmp/mxm-4zjrbr5n`,
`mxm-9x9wcju6`, `mxm-dqqrl4e2`, `mxb-ysl9jg86`, `mxb-yn1508e0`; created 27 Oct 03:11–09:20 local during construction; 0 open handles, no
validation running); removed by exact path; CLEAN.

**Packaging and records.** `mr_package.py` for the 60 (`main-run/batch8_packaging.log` `8c64709f2b56…`); new project dirs created first.
`review/VARIANT_KEY.json` 152 → 212 entries (`5b58a2fa1dbe…`; the 152 earlier entries byte-identical; C10i 77). `mr3_build_records.py`:
`INSTANCE_BUILD_LOG_C10I.csv` 116 rows, `INSTANCE_PROVENANCE_C10I.csv` 77 rows. Batch-1/2, 3, 4, 5, 6 and 7 manifests: 0 mismatches.
`batch8_frozen_hashes.json` now reports four mismatches: `FREEZE.json`, `review/VARIANT_KEY.json` and the two C10i record CSVs, which packaging,
the key and the plan freeze are meant to update; pinning them in W56 was an error of the coordinator (they are mutable outputs, not rules).
Every rule, brief, script and task file still verifies.

**Plans and freeze.** Twelve blocks of 5 in batch-8 order, 5 runs each, seeds 202610301–312: block1 `37c35b1e2999…`; block2 `e167ed7ce67d…`; block3 `8a984bef90b7…`; block4 `663b1773362f…`; block5 `27eb0c36d1d1…`; block6 `257a9f9e7488…`; block7 `4ba6d1049107…`; block8 `9a880efbc964…`; block9 `7d083f1db785…`; block10 `0f28dfe5dbcc…`; block11 `6afec628218a…`; block12 `d38ba6e1d55b…`;. `FREEZE.json` backed up to
`analysis/verification/backup/FREEZE.before_W57_b8.json`; the 12 plans added, bound to w55 (freeze sha256 `85eb0a47a39e…`); `--verify-only` passed for all 12.

**Cost guard** (`--left 60 --cap 600`): C = 324.21, k = 5, worst case after a block .74. Expected batch-8 run cost about 300 × /bin/zsh.43 ≈ ;
cumulative about .

**Robustness raters** launched with the runs (2 per accepted gold, 120 blind sessions, labels J01–J60); results in W58. They do not gate the runs.

**Launch.** `scripts/mr_run_blocks.sh w55 MR_batch8 600 plans/MR_batch8_block1..12_gpt55.json` starts immediately after this entry.
- **W57 correction (scratch).** The tmp audit's output was read truncated: the builders had left **20** validator scratch directories, not 5
  (`/private/tmp/mxm-*` 3 and `mxb-*` 17, all created 27 Oct 03:11–09:20 local during construction, each with 0 open handles and no validation
  running). All were removed by exact path; `mx_tmp_audit` CLEAN before launch.

## W58 (2026-10-27, ~10:1x +1100 = 2026-10-26 23:1xZ): batch-8 robustness ratings (pre-registered secondary)

**Robustness.** Workflow `wf_d2c0ab50-613` ran 120 blind single-gold sessions (2 extra raters per accepted batch-8 gold, shuffled labels
J01–J60 with seed 20261028, gold text as a file; 0 errors, 5.7 min). (A first launch, `wf_9cf48684-be3`, reused batch 7's script by mistake
and stopped at its input check with 0 agents.) Results `main-run/analysis/batch8_trace_robustness.json` (sha256 `6f553a88d3b6…`), written by
`main-run/batch8_prep/make_robustness.py` (`47cd39c89098…`; batch 7's writer with the batch-8 file names and seed).

| Outcome | Instances | Count |
|---|---|---|
| Both extra raters NO_TRACE | — | 51 of 60 |
| One extra rater TRACE | Compress-19 (T4), JacksonDatabind-95 (T3), Math-34 (T3) | 3 |
| Both extra raters TRACE | Compress-46 (T3, T3), JacksonCore-8 (T4, T4), JacksonDatabind-11 (T3, T3), Jsoup-48 (T4, T4), Math-49 (T3, T3), Math-86 (T3, T4) | 6 |

- The majority of 3 raters is NO_TRACE for 54 of 60 golds — a lower agreement than batches 3–7 (batch 6: 37 of 38; batch 7: 17 of 17).
- Dispositions are unchanged, as pre-registered. The six majority-TRACE instances stay ACCEPTED and are run; the secondary reading
  "majority of 3 raters NO_TRACE" (`mr_batch3_eval.py --batch batch8`) excludes them, and both readings are reported.

## W59 (2026-10-27, 14:0x +1100 = 2026-10-27 03:0xZ): batch-8 runs halted by the provider's credit balance after block 6; continuation frozen; paid runs paused

**What happened.** `mr_run_blocks.sh w55 MR_batch8 600 …` ran blocks 1–6 (22:55:55Z 26 Oct – 02:36:11Z 27 Oct; guard C = 324.21, 335.02, 345.50,
356.05, 366.05, 378.12; k = 5 each; 0 halts). Block 7 (guard C = 388.78) completed slots 0–9 (10 valid runs); slot 10 (MI-Jsoup-42 round 3,
run-003) ended `infrastructure` / `provider_error` ($0.06) and the driver halted with **HALT_PROVIDER_CREDIT** ("the provider refused for
credit/quota during the run"); the launcher stopped (blocks 8–12 not started). No pending run; `mx_tmp_audit` CLEAN; lid open; server up.
One earlier infrastructure record (MI-Chart-19 run-001, `provider_stall`, block 1) was replaced within its block by the frozen driver.
Log `diagnostic/run_blocks_MR_batch8.out` (`9901aaba791f…`). **This is again the W45 "uncontrollable difficulty": paid runs are paused until the
user restores the OpenAI credit.**

**Cost.** Batch-8 runs so far $103.81 (2 excluded records included); cumulative incl. estimates $392.74 (`mr_cost_guard.py --left 0 --cap 600`).
Remaining: 140 runs (15 + 5 × 25), about $58; projected cumulative about $451.

**Interim (30 instances with 5 valid runs, 5 partial, 25 not run; not the pre-registered reading).** 19 of 30 shifted (71/150 runs); distinct
facade 15 of 22; JacksonDatabind 3 of 10. Superseded by W60 when all 60 have run.

**Continuation (W37/W39 rule).** `plans/MR_batch8_block7_gpt55_cont.json` (`605a73ffd552…`) holds slots 10–24 of block 7 in the original order; its
slot 0 (Jsoup-42 round 3) is the single replacement for the infrastructure attempt. `FREEZE.json` backed up to
`analysis/verification/backup/FREEZE.before_W59_b8cont.json`; the plan added, bound to w55 (`f0214eeda5c6…`). `--verify-only` passed for the
continuation and blocks 8–12. Resume after the credit is restored:
`scripts/mr_run_blocks.sh w55 MR_batch8cont 600 plans/MR_batch8_block7_gpt55_cont.json plans/MR_batch8_block8_gpt55.json … plans/MR_batch8_block12_gpt55.json`.

**W59 addendum (resume).** The user wrote "how many instance we have run, resume the work" (2026-10-27 05:15Z). Pre-checks: lid open, no pending run, `mx_tmp_audit` CLEAN, guard C = 392.74 (k = 5, cap 600); w55 server was down and is restarted by the launch command. `mr_run_blocks.sh w55 MR_batch8cont 600 …` (continuation + blocks 8–12) starts immediately after this addendum.

## W60 (2026-10-27, 19:4x +1100 = 2026-10-27 08:4xZ): batch-8 runs complete; results, reading, records

**Runs.** After the second credit top-up, `mr_run_blocks.sh w55 MR_batch8cont 600 …` ran the block-7 continuation (05:15:55Z–05:36:59Z) and
blocks 8–12 (to 08:41:27Z); guard before each: C = 392.74, 398.90, 409.55, 419.77, 430.54, 441.79 (k = 5); tmp audit CLEAN and `--verify-only`
passed at every block; 0 halts. Batch 8 in total: **300 valid runs for 60 instances, 2 infrastructure records (MI-Chart-19 run-001
provider_stall; MI-Jsoup-42 run-003 provider_error at the credit halt), each replaced once, 0 timeouts.** Batch-8 run cost $127.22 (median run
75 s); cumulative including estimates **$454.07** (`mr_cost_guard.py --left 0 --cap 600`). Log `diagnostic/run_blocks_MR_batch8cont.out`
(`ea794b75b3d1…`).

**Scoring.** Frozen `mx_metrics.py` (`analysis/per_run.json` `e42ebe91d2fc…`), `mr3_report.py` (`MAIN_RUN_C10I_RESULTS.csv` `8259ad833e6a…`,
`MAIN_RUN_C10I_RUNS.csv` `c5987bb40050…`, `analysis/main_run_c10i_summary.json` `3a90f38b20db…`), `mr_batch3_eval.py --batch batch8`
(`analysis/batch8_prediction.json` `dc2db98fe209…`).

**Result: 60 batch-8 instances tested, 37 with at least one shift; 121 of 300 runs shifted.**

| Scope (BATCH8_PREREGISTRATION.md §4) | n | With ≥ 1 shift | s | Shifted / answered | Batch-3 thresholds (secondary) |
|---|---|---|---|---|---|
| **Primary: distinct facade** | 45 | 29 | 0.64 | 96/225 | DOES NOT REPLICATE |
| Recorded facade reuse | 15 | 8 | 0.53 | 25/75 | DOES NOT REPLICATE |
| All ACCEPTED | 60 | 37 | 0.62 | 121/300 | DOES NOT REPLICATE |
| Majority of 3 raters NO_TRACE | 54 | 35 | 0.65 | 116/270 | DOES NOT REPLICATE |
| All 3 raters NO_TRACE | 51 | 33 | 0.65 | 111/255 | DOES NOT REPLICATE |
| Hosts ≥ 1,500 lines | 35 | 23 | 0.66 | 79/175 | DOES NOT REPLICATE |
| Five largest classes | 25 | 14 | 0.56 | 42/125 | DOES NOT REPLICATE |
| Variant V1 (state as parameters) | 48 | 32 | 0.67 | 103/240 | — |
| Variant V2 (receiver) | 11 | 4 | 0.36 | 13/55 | — |

Per project (tested, with a shift, shifted/answered): Math 15, 11, 28/75; JacksonDatabind 10, 3, 13/50; Jsoup 9, 2, 2/45; Chart 6, 4, 15/30;
Compress 6, 4, 11/30; Collections 5, 5, 20/25; Lang 5, 4, 17/25; JacksonCore 3, 3, 12/15; Time 1, 1, 3/5. Failure modes (300 runs): GOLD_FIRST 179,
ENTRY_POINT_BIAS 116, GOLD_NOT_REACHED 5; rank-1 category ENTRY_POINT 121, GOLD 179. Deepest displacements: Math-103 (ranks 4 6 4 5 4), Math-61
(5 6 2 2 5).

**Reading.** On bugs that never had a static facade, the shift rate is lower than in C10/C10f (instances 0.62 vs 0.75–0.79; runs 0.40 vs
0.57–0.58), and the batch-3 reading does not replicate in any scope. The drop is concentrated: **Jsoup 2 of 9 (2 of 45 runs) and
JacksonDatabind 3 of 10** account for 14 of the 23 instances without a shift, while Collections, Lang, JacksonCore and Math behave as before.
V2 (receiver) facades shifted far less than V1 (4 of 11 vs 32 of 48), which agrees in direction with the batch-7 V1/V2 split (+0.23 vs −0.22)
but is confounded with project (the V2 instances are mostly Jsoup and JacksonDatabind). Reported, not interpreted causally.

**Integrity.** `main-run/analysis/b8_integrity_manifest.json` recorded (`47c997d53c5e…`; 2,082 entries) and verified, 0 mismatches; batch-1/2,
3, 4, 5, 6 and 7 manifests 0 mismatches; `mx_tmp_audit` CLEAN.

**Programme after batch 8** (by cell; never pooled without the composition): C10 67 / 50 (194/335 runs); C10f 38 / 30 (108/190); C10i 77 / 49
(161/385; batch 7 17 / 12, batch 8 60 / 37). **182 instances, 129 with a shift, 463 of 910 runs.**

## W61 (2026-10-27, ~20:3x +1100 = 2026-10-27 09:3xZ): batch 9 (C10i, the remaining tier) pre-registered; checkouts, fixtures, tooling

**Authorisation.** W45, the 23-October goal of running every Defects4J bug, the 26-October "继续跑试验" and the 27-October "resume the work".
Cap stays  (W56).

**Pre-registration.** `main-run/BATCH9_PREREGISTRATION.md` (sha256 `f815692da23f…`), from `main-run/batch9_prep/write_prereg.py`
(`9d412e085c59…`). 75 bugs: the 62 not-yet-used bugs whose best instance candidate is V2, and the 13 Closure bugs with any
qualifying candidate (deferred in batch 8 for disk only). Projects: Math 17, Closure 13, JacksonDatabind 9, Jsoup 9, Cli 8, Chart 6, Collections 4,
Lang 4, Compress 2, Codec 1, JacksonCore 1, JacksonXml 1. Best variants V2 69, V1 5, V0 1; regimes 1500 39, largest5 36; 51 planned-distinct, 24
planned reuses; ranks 307–381. Four bugs had a static candidate but no usable static facade: Closure-149, JacksonXml-6, Math-37, Math-47 (recorded in `static_facade_status`).
After batch 9, only Mockito and Csv remain unattempted in the profile. Selection `batch9_prep/make_tasks.py` (`58e9d18dd7ed…`);
the first draft listed the batch-8 bugs as left over because batch 8's task keys are `<key>__i` — the used-bug check now reads `fixture_key`;
no batch-9 task overlaps batches 1–8 (checked).

**Checkouts and fixtures.** 49 new checkouts, all OK (`main-run/batch9_checkouts.log` `017831647225…`); 75 fixtures; disk 33 → 27 GB
free. Hosts confirmed on the checkouts (`batch9_prep/confirm_hosts.py` `74051e3ccf98…`): 2 largest5 lists differed from the pool
snapshot; no regime change. `main-run/batch9_tasks.json` (`b8c15d03363c…`). Key preflight clean.

**Tooling (copies and small edits, regression-checked).** `batch9_prep/make_dispositions.py` (`d5b6ad6edf0a…`) and
`make_robustness.py` (`9c89e9fa3c44…`): batch 8's with batch-9 names (reuse also against batch-8 facades). `scripts/mr3_build_records.py`
(`1170d9a68eea…` → `d271ebc2a775…`), `scripts/mr_integrity.py` (`9419bfdbdb89…` → `570df0971e15…`) and `scripts/mr_batch3_eval.py`
(`3d4b6c02bf30…` → `6ee6fae20b16…`): batch-9 file names, plan pattern and reading. Batch-3, 4, 5, 6 and 8 readings and the C10i
records regenerate byte-identical; batch-1/2 to 8 manifests 0 mismatches. The builder note `BUILD_BRIEF_C10I_B8_NOTE.md` applies unchanged.

`batch9_frozen_hashes.json` is written immediately after this entry (prefix `AMENDMENTS_through_W61.md`; mutable outputs not pinned, W57).
- W61 time erratum: the entry was written at about 08:50Z (19:50 +1100), not 09:3xZ; `batch9_frozen_hashes.json` frozen_at 2026-10-27T08:50:34Z (sha256 `98308d93dd21…`, 203 files + prefix, 0 mismatches). Construction waits for the user to opt into the multi-agent workflow (the session's standing workflow opt-in has lapsed).

## W62 (2026-10-27, ~20:2x +1100): batch 9 reordered into 9a / 9b before any batch-9 build; workflow opt-in

**Instruction.** The user wrote "按 9a/9b 调整，用 workflow 建造" (27 October), accepting the coordinator's proposal: build and run first the
projects whose C10i cell is empty or thin, and launch construction as a multi-agent workflow.

**Change (no batch-9 design, spec or run exists).** `main-run/batch9_tasks.json` (`b8c15d03363c…` → `300290ec89e4…`): the same 75 tasks, hosts and
allowed candidates; new field `sub` and new ranks — **9a** (ranks 307–336, 30 tasks: Closure 13, Cli 8, Collections 4, Compress 2, Codec 1,
JacksonCore 1, JacksonXml 1) then **9b** (ranks 337–381, 45 tasks: Chart 6, JacksonDatabind 9, Jsoup 9, Lang 4, Math 17); the W61 rank is kept as
`pool_rank_W61`. `facade_reuse_of` and `facade_planned_by` were computed in the W61 order and are not recomputed (they are hints;
effective reuse is decided on the facade chosen, in the new rank order, by `make_dispositions.py`). `BATCH9_PREREGISTRATION.md`
(`f815692da23f…` → `650b0899b8b4…`) regenerated with an "Order (W62)" paragraph and a Sub column
(`write_prereg.py` → `f055962dfac0…`). **Sequence:** 9a construction → 9a dispositions, raters, packaging, plans
`MR_batch9a_block<N>`, runs → 9b construction → 9b likewise. No construction during paid runs.

`batch9_frozen_hashes.json` is rewritten after this entry with `AMENDMENTS_through_W62.md` as the prefix. 9a construction (30 tasks, 8 lanes,
model opus) starts immediately after.
