# Main run, batch 3: pre-registration

Written on 17 October 2026, before any batch-3 design, build or run. It was revised once, after an independent review (W29), and
before freezing. Its sha256 is recorded in `AMENDMENTS.md` (W29).

## Authorisation

The user, on 17 October:

> "Go ahead with Batch 3. Use the 'no local trace' checklist as a pre-specified construction rule before any new behavioural runs.
> You may create the required new Defects4J checkouts. Keep the total spend below approximately $148 and stop before exceeding
> that ceiling. Do not modify any completed Batch 1 or Batch 2 instances or results."

## Unchanged from batches 1 and 2

- the C10 recipe;
- the frozen protocol on w55: gpt-5.5, medium effort, 50 tool calls, 5 tests, 300 s;
- the frozen driver, with its health gate, its stall rules and one replacement per slot;
- the KPI: SHIFT means gold rank > 1, with absent from the top 10 counted as 11; an instance succeeds with at least one shift in 5
  valid runs;
- the 16 validation gates and the independent ownership audit (`AUDIT_BRIEF.md`);
- the exclusion rules;
- scoring with the frozen `mx_metrics.py` and `scripts/mr_report.py`.

## The new construction rule

`construction/mainrun/NO_LOCAL_TRACE_CHECKLIST.md` is a **hard** rule; its sha256 is in W29. After the omission, the whole gold
must show none of the following.

| Item | Meaning |
|---|---|
| T1 | a parameter whose value cannot change the result |
| T2 | a dead or frozen local, or a dead decision |
| T3 | a visibly incomplete closed set |
| T4 | a concrete phrase in its own javadoc, comments or identifiers that the body visibly does not meet |

The checklist's text governs. The builder brief's summary is only a pointer to it.

## Protecting batches 1 and 2

**Integrity manifest.** Before any batch-3 build, `scripts/mr_integrity.py --record` writes the sha256 of every batch-1 and batch-2
artefact to `main-run/analysis/b12_integrity_manifest.json`. The artefacts are:

- the instance directories, specs, designs, audits and variants;
- the variant-key entries and the plans;
- the driver-ledger records;
- the `per_run.json` rows;
- the rows of `MAIN_RUN_RUNS.csv`, `MAIN_RUN_RESULTS.csv`, `INSTANCE_BUILD_LOG.csv` and `INSTANCE_PROVENANCE.csv`.

`--verify` runs after construction, after every run block and at the end. Any mismatch stops batch 3 until it is restored and
recorded.

**Output files.** Batch-3 rows and sections are added to the shared output files, and no batch-1 or batch-2 row is edited or
removed. `mr_report.py` and `mr_build_records.py` rewrite whole files, so `--verify` checks field-level identity of each batch-1 or
batch-2 row in the four CSVs, in `per_run.json` and in the driver ledger, after every regeneration of shared outputs. Row order is
not checked, because the files sort by instance id. The `.md` files, `main-run/COST_LEDGER.csv` and `main_run_summary.json` are
deterministic renderings of those verified rows by the same scripts. Their aggregate lines, such as headline counts and cost
totals, are recomputed and are not batch-1 or batch-2 results.

A full regeneration (`mr_key`, `mr_build_records`, `mx_metrics`, `mr_report`) followed by `--verify` gave 0 mismatches on
17 October, before any batch-3 build, so regeneration is idempotent.

**Key preflight.** Batch-3 instance keys are `<Project>-<bugId>`, as before; `mr_lib.py` needs this form. None of the 21 keys was
used by batch 1 or 2.

- Before any builder starts, the coordinator asserts that no design, spec, instance, audit or variant path exists for any batch-3
  key. The batch-3 fixtures, created on 17 October, are the only exception.
- `mr_package.py` keeps its variant-id collision assert.

## Candidates (21)

These are the next eligible pool ranks that still have an unused target.

- **Checkouts.** The 20 new checkouts were created on 17 October, each with `defects4j checkout -p <P> -v <id>f -w
  <store>/defects4j/<P>-<id>/fixed` into a directory that did not exist. Math-5 already had one. The log is
  `main-run/batch3_checkouts.log`.
- **Facade choice.** A builder must choose its facade from its row's allowed targets. If none can carry the recipe, the instance
  is UNBUILDABLE. This keeps facades distinct within batch 3 and from every earlier facade.

| Pool rank | Bug | Allowed facade targets |
|---|---|---|
| 3 | Lang-44 | NumberUtils.isDigits / minimum / maximum |
| 4 | Lang-58 | NumberUtils.compare |
| 7 | Lang-49 | Fraction.getReducedFraction |
| 13 | Lang-31 | StringUtils.containsAny / stripAccents |
| 14 | Lang-40 | StringUtils.indexOfAny / leftPad |
| 15 | Lang-35 | ArrayUtils.toMap / addAll / subarray |
| 16 | Lang-37 | ArrayUtils.indexOf / lastIndexOf |
| 19 | Lang-20 | StringUtils.abbreviate / substring |
| 20 | Lang-51 | BooleanUtils.xor / toBooleanObject / toBoolean |
| 21 | Lang-57 | LocaleUtils.toLocale / localeLookupList / availableLocaleSet |
| 22 | Lang-3 | NumberUtils.createBigDecimal |
| 23 | Lang-54 | LocaleUtils.countriesByLanguage / languagesByCountry |
| 24 | Lang-33 | ClassUtils.getShortClassName / getAllInterfaces / getAllSuperclasses |
| 25 | Lang-41 | ClassUtils.getPackageName / isAssignable / getPublicMethod |
| 30 | Math-15 | FastMath.asinh / atanh |
| 31 | Math-16 | FastMath.log1p / cos / min |
| 33 | Lang-46 | StringEscapeUtils.unescapeCsv / escapeCsv |
| 34 | Lang-53 | DateUtils.round / truncate |
| 35 | Lang-65 | DateUtils.parseDate / iterator / isSameDay |
| 37 | Math-55 | Vector3D.crossProduct / angle |
| 64 | Math-5 | Complex.valueOf |

## Construction pipeline (per candidate)

1. **Builder.** Follows `BUILD_BRIEF.md`, including the hard checklist, its self-check and the allowed facades. It works until the
   instance is READY on all 16 gates (at most 4 gate iterations, as before), or until it returns UNBUILDABLE or FAILED.
2. **Two independent checks, in parallel, on a READY instance:**
   - an **auditor** following `AUDIT_BRIEF.md`;
   - a **trace checker** following `TRACE_CHECK_BRIEF.md`. It sees only the variant gold text that `scripts/mr_gold_text.py` prints.
3. **One redesign.** If the audit is REJECTED or the checker returns TRACE, a builder receives both sets of reasons and makes ONE
   redesign.
   - Sending a REJECTED audit back once was already the rule in batches 1 and 2 (`MAIN_RUN_PLAN.md`), though it never happened.
   - The redesigned version is re-validated on the 16 gates, then checked by a **new** auditor and a **new** checker. Neither has
     seen the earlier version or its findings.
4. **Disposition.** It is decided on the last version built: the first version if no redesign was triggered, otherwise the
   redesigned one. Both versions' verdicts are recorded. Rows apply top to bottom, and the first match wins.

| Condition on the last version | Status |
|---|---|
| The builder returned UNBUILDABLE or FAILED, or the version is not READY on all 16 gates | UNBUILDABLE |
| Checker verdict TRACE (any audit verdict) | UNBUILDABLE (local trace) |
| Checker NO_TRACE, audit REJECTED | REJECTED |
| Checker NO_TRACE, audit FLAG_AMBIGUOUS | FLAGGED: run after all ACCEPTED instances, reported separately, never counted |
| Checker NO_TRACE, audit CONFIRMED | **ACCEPTED** |

**Missing verdicts.** A missing or invalid verdict (no result, or a value outside the allowed set) is requested once more from a
new agent. If it is still missing, it counts as REJECTED for the audit and TRACE for the checker.

**Archive before a redesign.** Before redesigning, the builder archives version 1's design, spec, validation, audit and trace
verdict in `construction/mainrun/history/<key>/v1/`. Nothing in the new design, spec or code refers to the earlier findings.

5. **Before any run.** Runs start only after all 21 candidates have a final disposition. The dispositions go in
   `main-run/analysis/batch3_dispositions.json`, which is authoritative for `INSTANCE_BUILD_LOG.csv`, for planning and for n. That
   file's sha256, and the sha256 of every batch-3 spec, are recorded in an amendment before block 1. No batch-3 instance is designed, redesigned or dispositioned after any
   batch-3 run exists.

## Run order and cost guard (ceiling $148)

**Order.** ACCEPTED instances run first, in pool-rank order, in blocks. FLAGGED instances follow in pool-rank order, only while the
guard allows. Within a block, runs are interleaved in seeded rounds, as before. Each block is planned, frozen and verified like the
earlier batches.

**Names.** Block plans are named `plans/MR_batch3_block<N>_gpt55.json`, and their driver logs are
`diagnostic/run_MR_batch3_block<N>_gpt55.out`. The guard fails if any ledger record after the main run began belongs to no
`plans/MR_*.json` plan, because that spend would be missing from C.

**Guard.** The block size `k` is the largest integer, at most min(5, instances left), such that

    C + 10k × M + (120k + 12) × $0.008  ≤  $147.00

| Term | Meaning |
|---|---|
| C | the experiment's cumulative spend, recomputed from the raw sources by `scripts/mr_cost_guard.py`: the pre-main-run total including estimates ($66.25), plus every main-run driver-ledger record's `cost_usd`, plus $0.008 × the health probes counted in the main-run driver logs. It is computed only after the previous block's chain has ended, so every run is in the ledger. Every `probe:` line counts, including hung probes. |
| M | the highest single-run cost seen in any main-run record so far, batch 3 included. It is $0.6595 at registration. |
| 10k | the worst-case number of runs: 5k slots, each with at most one replacement under the frozen driver. |
| 120k + 12 | the worst-case number of probes under the frozen driver. A 3-probe gate runs at start and after every non-valid attempt, and each gate tolerates up to 5 resetting probe failures. |

**Why it holds.** Under these terms, spend after a block can pass $147 only if some run costs more than M. The gap between $147 and
$148, and the distance between the worst case and the expected case (about $2.15 per instance against a reserve of $7.56), cover
that.

**Halted blocks.** If a block halts, the guard is re-run on the slots that remain before any restart, and each restart is a new,
frozen continuation plan. If k = 0, batch 3 stops, and any ACCEPTED or FLAGGED instances left are reported as built but not run.

**Expected use.** At the means of batches 1 and 2, the guard admits blocks of about 5, 4, 2, 2, 1, 1 and 1: about 16 instances,
ending near $140.

**The ceiling.** Spend is expected to reach at most $147 at the moment of stopping, below the user's ceiling of about $148.

## Prediction (descriptive; no statistical test, per the supervisor)

**Hypothesis (from batches 1–2).** gpt-5.5 shifts the gold on instances whose omission leaves no local trace.

**Denominator.** n is the number of ACCEPTED batch-3 instances whose 5 valid runs were scored under the unchanged exclusion rules,
counted exactly as the 18 earlier instances were. n and s are computed from the `MAIN_RUN_RESULTS.csv` rows with batch = batch3,
an ACCEPTED status in `batch3_dispositions.json`, and valid_runs = 5. They are not taken from the report's headline counts. Reported separately and left out of n:

- FLAGGED instances;
- instances built but not run;
- any instance with fewer than 5 valid runs.

Let s = (instances in n with at least one shift) / n.

| Condition | Reading |
|---|---|
| n < 5, including n = 0 | INCONCLUSIVE (too few; s is reported if n > 0) |
| n ≥ 5 and s ≥ 4/5 | **SUPPORTED** |
| n ≥ 5 and s ≤ 2/3 (12/18, the batch-1–2 rate) | **NOT SUPPORTED** |
| n ≥ 5 and 2/3 < s < 4/5 | **INCONCLUSIVE** |

Shifted runs over answered runs are reported alongside.

## Retrospective classification (reported, never used to change anything)

Three independent raters apply the frozen checklist under `TRACE_CHECK_BRIEF.md`, one gold per session: 18 golds × 3 raters = 54
sessions.

- Each session gets the variant gold text under a shuffled anonymous label, and no results.
- No rater is a batch-3 builder, auditor or checker.
- The majority verdict per gold is cross-tabulated with that instance's KPI outcome. The mapping file is joined only after all 54
  verdicts are in.

The checklist's examples were drawn from those golds after their results were known, so this cross-tabulation is descriptive only.
The prospective test is batch 3.

## Outputs

**Rows added** (batch-1 and batch-2 rows protected as above):

- `INSTANCE_BUILD_LOG.csv` and `INSTANCE_PROVENANCE.csv`;
- `MAIN_RUN_RUNS.csv` and `MAIN_RUN_RESULTS.csv`;
- `SHIFTED_INSTANCES.md` and `FAILED_TO_TRANSFER.md`;
- both cost ledgers;
- the amendments, W29 onward.

**Rewritten:** `SUPERVISOR_PROGRESS_UPDATE.md`, as update 3.

**New:**

- `main-run/analysis/trace_checks_batch3.json`;
- `main-run/analysis/retro_trace_classification.json`;
- `main-run/analysis/b12_integrity_manifest.json`;
- `main-run/batch3_build_audit_results.json`.
