# Deviations and amendments (mechanism-search-v1)

PREREGISTRATION.md is frozen: it is hashed into every plan in FREEZE.json, so it is left unchanged. Every deviation from it,
and every protocol addition made after the first paid run, is recorded here with the date (UTC), the reason, and the effect on
the data.

## X1 (2026-10-10): NEW-R4-M4 is invalid because the harness cannot accept its gold

- **What happened.** The submission validator, `agents/mini_swe_fault_localization.py::_looks_like_test_method` in the frozen
  server tree, rejects any method whose class name ends in `Test` or `Tests`, whose package contains `.junit.` or `.test.`, or
  whose method name starts with `test`. The gold of NEW-R4-M4, `MannWhitneyUTest::mannWhitneyU`, matches the first rule.
- **Evidence.** In S2 run CTV-15AB64/run-001, the agent's first submission ranked the gold first. It was rejected with
  `test_method` errors. The agent then resubmitted without any `MannWhitneyUTest` method, so the scored rank is None.
- **Decision.** The instance is invalid, a gold-validity failure decided on validity rather than outcome. It is excluded
  from every screening class and from family conclusions. Its two remaining S2 slots were dropped from the continuation plan.
- **Prevention.** The builder (`scripts/mx_build_validate.py`) has a new gate, G13: the gold and every decoy must be
  submittable. `mx_derive.py` has the same gate as D5. A retro check of every instance in the key found no other affected
  instance.

## X2 (2026-10-10): STOP_CONTAMINATION at S2 slot 15, followed by a continuation plan

- **What happened.** In run CTV-065313/run-002 (NEW-R7-M10, round 2), the agent ran
  `find /private/tmp /usr /opt -name 'junit-4*.jar'` while looking for a JUnit jar. The output was one path inside a stale
  cue-trust-v3 workspace (`/private/tmp/ct3ws-diagF1/.../CTV-BEE8CB/lib/junit.jar`). The scanner stopped the block, which is
  correct.
- **Effect on the data.** The variant shown, CTV-BEE8CB, is an unrelated Chart cue-trust instance. No source or answer
  content was shown. The run had ranked the gold first. Under the frozen rule the run is excluded: contamination can never be
  released.
- **Continuation.** `plans/S2_cont.json` contains S2 slots 15 to 38 in the original order. Slot 15 is its replacement. The
  NEW-R4-M4 slots are dropped (X1). The plan was frozen with `mx_freeze.py --add-plan` before any paid call.
- **Root cause and environment.**
  - Stale directories under `/private/tmp` survived from earlier work: one cue-trust workspace and empty builder marker
    directories whose names carried instance IDs and role words.
  - My cleanup of those shared `/private/tmp` entries was refused by the session's permission policy, so they are left for
    the user to remove.
  - Validity is protected by the scanner, which stops any run that displays another variant ID or out-of-workspace source.
    The stale Chart workspace cannot help with the non-Chart instances in the next blocks.
  - The builder now gives its marker directory a neutral name (`mxm-*`) and removes it at the end of every build.
  - No construction runs while a paid block is running.

## X3 (2026-10-10): collateral failure in the re-hosted RH-ADV-DEPTH-01

- **Finding.** In this harness the parent variant also fails `ConversionTest::testIntArrayToLong`, not only the trigger.
  The original validation recorded only the trigger. The re-host reproduction (apply, compile, trigger) did not run the full
  suite, so this was missed. It was found while deriving P4-DEPTH-01-r1, and confirmed directly on a fresh copy.
- **Effect.** An agent that runs the full suite sees two failing tests instead of one. The gold and the failure mechanism
  are unchanged. The S1 result for RH-ADV-DEPTH-01 is reported with this caveat.
- **Derived revision.** P4-DEPTH-01-r1 changes only documentation, so `mx_derive.py` checks it with a parent-matching gate
  (D3: the full-suite failure set must equal the parent's).

## X4 (2026-10-10): Phase 4 derived revisions

`scripts/mx_derive.py` builds EXPLORATORY revisions of an existing instance.

- **What a revision carries.** The parent IID, the revision number and the edits are recorded in `instances/<iid>/spec.json`
  and in INSTANCE_PROVENANCE.csv.
- **Gates.** D1 apply and compile; D2 the trigger fails three times byte-identically with the parent's assertion; D3 the
  full suite; D4 fault vocabulary; D5 submittability.
- **Use.** Revisions are diagnostics (does an effect survive a validity repair?). They are never confirmation evidence.

## X5 (2026-10-10): builder tool fixes after the recipe freeze (the recipe text is unchanged)

- **G11 guard.** `mx_build_validate.py` G11 (decoys unchanged) compared every decoy with its pristine version before checking
  whether a context edit touched its file. A decoy created by a context edit, which all three held-out recipes need, has no
  pristine version, so the builder would crash. The check now skips context-edited files first. G1 already proves those
  edits behaviour-preserving, so the semantics are unchanged.
- **Neutral temporary names.** Builder temporary directories are now named neutrally (`mxb-*`, `mxm-*`) and removed after
  each build (X2).
- **Freeze record.** `construction/heldout/RECIPES_FROZEN.json` records the builder hash at the recipe freeze. The hash after
  these fixes is recorded with each held-out validation.

## X6 (2026-10-10): pre-run revision of a held-out instance rejected by audit

- **Rejection.** The first audit rejected HO-HB-LANG-01 on leakage (item d) only. The trigger's zone literal appeared in the
  gold's javadoc example, so a grep for the literal landed on the gold. Items a, b, c and e passed.
- **Revision.** No run had used the instance, so its original builder revised it before any run: neutral javadoc examples,
  the same contract and fault, a second validator attempt, and re-packaging under the same id.
- **Re-audit.** A different, independent auditor audits the revision. The original verdict is kept as
  `instances/HO-HB-LANG-01/audit_r0.json`.
- **Consistency with the plan.** This keeps the plan's rule that an instance is never modified after its first behavioural
  run.

## X7 (2026-10-10): more stale scratch found in /private/tmp; cleanup required before paid runs resume

- **Finding.** The S2 builder agents left scratch checkouts under `/private/tmp`: `nr1m1` and `r2m2` to `r13m9` (about 1 GB),
  plus `r5m7_c.log`. They hold Defects4J source trees from the construction of the NEW-R* instances, which may include pristine
  or correct copies next to variants.
- **Risk.** An agent running a remaining S2_cont slot could reach them with `find /private/tmp`. The scanner would stop such a
  run, so the data stay valid, but every stop costs a run.
- **Action.**
  - These, together with the X2 leftovers (`mxmark-*`, `mxchk-1Cyp`, `ct3ws-*`), must be removed before S2_cont resumes.
  - The session policy refuses my sweep of shared `/private/tmp`, so the user is asked to remove them.
  - Held-out builders and auditors used `mktemp /private/tmp/mxb-*` and delete their own scratch on completion. Before any
    paid block, the coordinator checks that no `mxb-*` remains.

## X8 (2026-10-11T04:26:30Z): operational definition of PARTIALLY_SUPPORTED, fixed before any held-out run

- **Why.** PREREGISTRATION.md defines PARTIALLY_SUPPORTED only as "some held-out reduction but not all six criteria". This is
  fixed now, while S2_cont is running and no held-out (HO) run directory exists. Pooled held-out Acc@1 is referred to below
  as "pooled".
- **The classes.**
  - **SUPPORTED** = STABLE, meaning all six criteria hold.
  - **PARTIALLY_SUPPORTED** = not STABLE, and either (pooled ≤ 0.80) or (at least one held-out instance has Acc@1 ≤ 0.60).
  - **NOT_SUPPORTED** = otherwise.
- **Operational criteria.**
  - Criterion 3: no-answers (rank-1 category NO_ANSWER) make up under half of the misses. Infrastructure attempts are excluded
    and replaced under the frozen driver rule, and they are reported separately.
  - Criterion 5: no STOP_CONTAMINATION, STOP_INTEGRITY or STOP_SCAN_FAILED record on any held-out run of the mechanism, and
    every instance READY.
- **Reporting.** `scripts/mx_heldout_report.py` implements this, with Wilson 95% intervals.

## X9 (2026-10-11): residual exposure, the coordinator session's own files under /private/tmp/claude-501

- **What is exposed.** The coordinating Claude session keeps its scratchpad and its subagent transcripts under
  `/private/tmp/claude-501/`. That includes builders and auditors, which read gold names.
- **Why it cannot be removed.** These are session infrastructure, so they cannot be moved while the session runs.
  `mx_tmp_audit.py` therefore skips `claude-*`.
- **What protects the data.** An evaluated agent could reach these files only by searching `/private/tmp` outside its
  workspace. The frozen scanner stops any run that displays out-of-workspace harness content or another variant id
  (X2 showed that it does), and such a run is excluded.
- **Conclusion.** This is a disclosed residual risk to cost, not to data validity.

## X10 (2026-10-11): held-out setup failure on HO-HC-MATH-01; gate G14 added; continuation plan

- **What happened.** HO slot 8 (HO-HC-MATH-01, round 1) stopped with STOP_INTEGRITY. The run status was
  `failed`/`setup_failure` ("Could not apply variant patches"), so no agent config existed and the effort field was empty.
- **Cause.** The builder had mirrored its edits into the tracked `StorelessBivariateCovariance.java.bak`. The server stages
  agent workspaces with a filtered copy that drops `*.bak`, `*.orig` and `*.rej` (`agentAdapter.mjs`), then applies patches
  with `patch -p1 --forward --batch`. The `.bak` hunks therefore had no target file. The builder validator and the auditors
  used `git apply` on unfiltered copies, so they could not see this.
- **Effect.** No agent step ran, so the instance had **no behavioural run**. The 8 held-out runs completed before the stop
  (slots 0 to 7) are unaffected.
- **Fix.**
  - New gate **G14** (`scripts/mx_harness_check.py`, called by `mx_build_validate.py`). It stages a copy with the server's own
    `copyDirectoryFiltered` and `stripHistoryDirs`, imported read-only, and dry-runs both patches with the server's exact
    `patch` command.
  - A retro check of all 11 new variants passed except HO-HC-MATH-01. The builder checkouts are byte-identical to the server
    checkouts (`diff -rq`, 0 lines, all five projects).
  - HO-HC-MATH-01 is revised by its original builder: the `.bak` edits are removed and nothing else changes. It is then
    re-validated with G0 to G14 and re-audited. The r0 records are kept (`*_r0.json`, `build_r0/`).
  - `plans/HO_cont.json` holds HO slots 8 to 44 in the original order; slot 8 is the replacement. It is frozen before any
    further call.

## X11 (2026-10-11): held-out completion; one cell left unfilled after four provider stalls; one agent-side timeout

- **HO-HB-COMPRESS-01, round 5.** The slot stalled four times in a row, every attempt classified `provider_stall`:
  - HO_cont run-005 (5 calls, final gap 272 s);
  - HO_cont run-006 (4 calls, 281 s);
  - HO_top run-007 (no recorded calls);
  - HO_top run-008 (3 calls, 283 s).
- **Halt review.** After the first halt, a replay of run-006's exact state returned in 8.3 s (`diagnostic/HALT_REVIEW_HO_slot36.md`).
  One top-up (HO_top, 2 attempts) was run under the preregistered top-up rule, and both attempts stalled.
- **Decision.** The cell stays unfilled. The second top-up that the rule allows was **not** used, because the outcome cannot
  change any verdict. HB stands at 14/14 valid runs; a wrong 15th run would give 14/15 = 0.93, still far above the 0.60
  threshold. Further attempts risked more 30-minute stalls for no information. HO-HB-COMPRESS-01 is reported with n = 4.
  Its four valid runs ranked the gold first.
- **HO-HA-COMPRESS-01 run-003.** The frozen classifier counts this as a valid behavioural `timeout` (NO_ANSWER).
  - The agent's first model call issued three commands, which completed. The second model call did not return within the
    300 s budget (`TimeExceeded`).
  - Stall rule 2 did not apply, because less than 60 s of budget remained after the last tool result.
  - It occurred at 12:16Z, in the same window as a provider stall (run-002 at 12:05Z) and a 574-second health probe (12:15Z).
  - It is kept as classified, with no post-hoc reclassification, and counts as HA's only miss. Held-out STABLE criterion 3
    therefore fails for HA, because the only miss is a no-answer.
- **HC and criterion C5.** The criterion is computed as "n" for HC because the setup-failure STOP_INTEGRITY record of
  HO-HC-MATH-01 r0 (X10) counts against it. No agent step ran in that run; the stop reflects harness compatibility, not
  leakage. Every other held-out run is scanner-clean.

## X12 (2026-10-12): corrigenda from the independent report verification

The final reports were checked by independent verifier agents (a numbers lens and an inference lens per report, plus a
cross-report check). Each finding was then adjudicated against the primary data before any change was made
(`analysis/verification/`). Earlier entries are left as written. These corrections take precedence over them.

1. **X11, HO-HA-COMPRESS-01 run-003. Corrects the description of the timeout.**
   - The run made **one** model call (api_calls = 1). It returned 5.5 s after the timer started and issued three commands:
     grep, `defects4j test` and find. All three exited 0, but their results were recorded only at about 304.9 s, after the
     300 s budget, so the agent stopped (`TimeExceeded`). No second model call was made.
   - The budget was spent in that tool step, not in waiting for the provider. The link drawn in X11 to the provider-degradation
     window is not supported.
   - Neither stall rule applied:
     - rule 1 requires at most 2 commands, and this run issued 3;
     - rule 2 requires more than 60 s left after the last tool result, and the final gap was about −4.9 s.
   - The classification (valid run, NO_ANSWER) stands.
2. **X2.** The command the agent actually ran was
   `find /private/tmp /usr /opt -type f \( -name 'junit-4*.jar' -o -name 'junit.jar' \) 2>/dev/null | head -20` (call 10). The
   `junit.jar` pattern matched the stale path.
3. **X2 continuation.** No frozen rule covers replacing an excluded behavioural run. PREREGISTRATION.md provides replacement
   for infrastructure failures, and screening asks for 3 valid runs per instance. Giving slot 15 a replacement in S2_cont was
   an operator decision taken to complete 3 valid runs.
4. **X3.**
   - The re-host reproduction ran no full suite for any of the 18 re-hosted instances.
   - Only RH-ADV-DEPTH-01's parent was later checked on the full suite, by P4 gate D3.
   - Whether the other 17 re-hosted instances fail extra tests in this harness is therefore unknown.
5. **X5.**
   - The builder's hash after the fixes is **not** recorded. The packaged held-out validation records name the validator only
     by path (`validator_version`), and FREEZE.json does not hash the builder.
   - G1 gives test-level evidence that context edits preserve behaviour, not proof. Builders and auditors noted, for example,
     that the HO-HC-MATH-01 and HO-HA-MATH-01 context edits are mathematically identical to upstream but not bit-identical.
6. **X6.**
   - HELDOUT_CONFIRMATION_PLAN.md says that a rejected instance "is replaced by a fresh build from the same recipe before any
     run". HO-HB-LANG-01 was instead **revised in place** before any run (javadoc example only; same contract, fault and id),
     then re-validated and re-audited. That is a deviation from the plan's wording.
   - Both audit records name the auditor only as "independent agent". The records therefore do not themselves show that the r1
     auditor differed from the r0 auditor. Each audit was a newly launched agent.
7. **X7.**
   - The "about 1 GB" for the S2 builder scratch was measured with `du` in the coordinating session before the directories were
     removed (about 996 MB in total). That measurement was not archived.
   - The directories were removed on 2026-10-11 with the user's explicit authorisation.
8. **X9.**
   - The scanner stops a run whose output shows a foreign variant id, a harness marker (for example `gold_rank`,
     `structured_submission`, `variant_manifest` or `VARIANT_KEY`), an experiment name or the repository path. After an
     out-of-workspace call it also stops on a pristine-only source line.
   - It does not match gold method names. A display of coordinator files that carried none of these markers would not be
     caught. The residual risk is therefore small but not limited to cost.
9. **X10.**
   - The retro check of the 11 new variants was not archived when it was run.
   - It was re-run and archived on 2026-10-12 (`analysis/verification/g14_retro_check.json`), and all 11 variants PASS,
     including HO-HC-MATH-01 r1.
   - The builder checkouts are identical to the server checkouts only when VCS metadata is excluded
     (`diff -rq -x .git -x .svn`, 0 lines, all five projects). A plain `diff -rq` lists only `.git` and `.svn` differences.
10. **X11, scanner status.** Two held-out runs each had one flagged call that wrote a scratch Java file under `/tmp`:
    HO-HA-JACKSONCORE-01 run-001 and HO-HC-LANG-01 run-002. The scanner did not judge either contaminating, and both runs are
    valid. No other held-out run has a STOP_CONTAMINATION, STOP_INTEGRITY or STOP_SCAN_FAILED record, apart from the r0 setup
    failure in X10.
11. **Phase 7 label set (not previously recorded).**
    - PREREGISTRATION.md fixes the Phase 7 failure-mode labels: SEARCH_FAILURE, DISCOVERY_WITHOUT_INSPECTION,
      ATTRIBUTION_FAILURE, EVIDENCE_RETRIEVAL_FAILURE, EVIDENCE_INTEGRATION_FAILURE, CONVENTION_PRIOR, LOCAL_ODDNESS_BIAS,
      ENTRY_POINT_BIAS, LEXICAL_SHORTCUT and OTHER.
    - The blind labelling (FAILURE_MODE_ANALYSIS.md) used a finer post-hoc set instead.
    - **Coordinator mapping onto the preregistered set:**

      | Post-hoc label | Preregistered label |
      |---|---|
      | ENTRY_POINT_RANKING | ENTRY_POINT_BIAS |
      | CONVENTION_ATTRIBUTION | CONVENTION_PRIOR |
      | CALLER_ARGUMENT_BLAME | CONVENTION_PRIOR (its secondary label is convention attribution) |
      | DECOY_DOC_CONTRADICTION | ATTRIBUTION_FAILURE |
      | MASK_PLACEMENT_ATTRIBUTION | ATTRIBUTION_FAILURE |
      | held-out no-answer timeout | OTHER |

    - **Preregistered counts over the 13 wrong runs:** ENTRY_POINT_BIAS 5, ATTRIBUTION_FAILURE 4, CONVENTION_PRIOR 3, OTHER 1.
      No run is SEARCH_FAILURE or DISCOVERY_WITHOUT_INSPECTION: the gold was read in every wrong answered run.
