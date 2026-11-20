# Main run, batch 4: pre-registration

First written on 19 October 2026, before any batch-4 checkout. It was revised the same day, after the 24 checkouts
(`main-run/batch4_checkouts.log`, DONE) and two rounds of independent review. Every version predates any batch-4 design, build or
run. The sha256 of the final version is recorded in `AMENDMENTS.md` (W34).

## Authorisation

The user, on 19 October:

> "Hong Jin confirmed that the next step is to continue expanding the gpt-5.5 study. Please proceed with additional Defects4J bug
> instances using the same frozen main-run methodology and the preregistered no-local-trace construction rule. Keep the current
> scoring unchanged: a shift occurs whenever the gold method is not ranked first. Do not switch to GPT-5.6 yet, and do not introduce
> a new baseline or redesign the completed batches. Continue in cost-controlled batches, preserve all provenance/integrity checks,
> and stop to report before exceeding the new budget ceiling I provide."

Asked for the ceiling, the user chose: **"$200 total"** of cumulative experiment spend, including estimates.

## Everything from batch 3, unchanged

`main-run/BATCH3_PREREGISTRATION.md` applies in full unless this document says otherwise.

**Construction rule.** `construction/mainrun/NO_LOCAL_TRACE_CHECKLIST.md` is byte-identical to the batch-3 file (sha256
`487a966a…`), and `TRACE_CHECK_BRIEF.md` and `AUDIT_BRIEF.md` are unchanged.

**The one change to a frozen batch-3 file.** In `construction/mainrun/BUILD_BRIEF.md` (sha256 `42f3a20a…` → `cc565d61…`), one
line changed so that the facade rule also points at this document:

> was: "**Facade choice (batch 3).** Your facade MUST be one of your instance's allowed targets in `main-run/BATCH3_PREREGISTRATION.md`."
>
> now: "**Facade choice (batch 3 on).** Your facade MUST be one of your instance's allowed targets in your batch's pre-registration
> (`main-run/BATCH3_PREREGISTRATION.md` or `main-run/BATCH4_PREREGISTRATION.md`)."

Reverting that one line in a copy reproduces the W29 hash `42f3a20a…` exactly, so nothing else in the brief changed.

**Batch-3 labels in the brief.** The brief's "Pre-run checks and the single redesign (batch 3)" bullet and its "batch-3 redesign
archive" allowed write apply to batch 4 as written. Batch-4 builders are told so in their task text, and the brief is not edited
again.

**Script changes.** Four scripts gained batch-4 options; their defaults reproduce the batch-1–3 behaviour exactly:

- `mr_cost_guard.py`: `--cap`, and a refusal (exit 2) if the set of server ledgers `diagnostic/block_*.jsonl` is anything other
  than w50, w55, w56 and wmDiag;
- `mr_integrity.py`: `--batches`, `--manifest` and `--verify-frozen`;
- `mr_build_records.py`: reads each batch's dispositions file;
- `mr_batch3_eval.py`: `--batch`, the replication labels and a per-project breakdown for batch 4.

`mr_report.py` reads batch-4 diagnosis notes from `analysis/diagnosis_notes_batch4.json`, so the batch-1–3 notes file is never
edited. It accepts only `_batch4` and keys of batch-4 instances, and raises on any other key.

Checks that the defaults reproduce earlier output:

- re-running the batch-3 evaluation reproduces `batch3_prediction.json` byte for byte (sha256 `422dab71…`, as in W32);
- the batch-1/2 manifest still verifies with 0 mismatches.

**Batch-3 manifest baseline.** It was recorded on 19 October after the `mr_build_records.py` change. It is anchored to the
17-October state in two ways:
- The W30 version of that script (sha256 `7e2b1a1d…`, as recorded in W30) was reconstructed by undoing the W34 edits. Run into a
  scratch folder, it reproduces all 44 build-log rows and all 35 provenance rows of today's files exactly.
- The frozen driver's `--verify-only` passes for all 10 batch-1–3 plans against FREEZE.json's launch-time hashes of their
  instances, variants and key entries.

**Protocol and scoring.**
- the C10 recipe;
- the frozen protocol on w55: gpt-5.5, medium effort, 50 tool calls, 5 tests, 300 s;
- the frozen driver, with its health gate, its stall rules and one replacement per slot;
- the exclusion rules;
- the KPI: SHIFT means gold rank > 1, with absent from the top 10 counted as 11; an instance succeeds with at least one shift in 5
  valid runs;
- scoring with the frozen `mx_metrics.py` and `scripts/mr_report.py`.

**Pipeline and dispositions.**
- builder, then an auditor and a blind trace checker in parallel;
- one pre-run redesign on REJECTED or TRACE, checked by a new auditor and a new checker;
- the disposition table, applied top to bottom;
- the missing-verdict rule and the v1 archive before a redesign.

**Before any run.** Runs start only after every batch-4 candidate has a final disposition. That disposition is recorded, with
`main-run/analysis/batch4_dispositions.json` and every spec's sha256, in an amendment before block 1. No completed batch-1, batch-2
or batch-3 instance is redesigned, rebuilt or re-run.

## Candidates (24)

These are the eligible pool bugs not yet attempted that still have a facade target distinct from every facade already used, by
an earlier main-run instance or by Stage B, and from every other batch-4 candidate. Targets were allocated by maximum bipartite matching in pool-rank priority: a candidate gets its own
matched target, then up to two leftover targets of its own.

A builder must choose its facade from its row. If none can carry the recipe validly, the instance is UNBUILDABLE.

| Pool rank | Bug | Allowed facade targets |
|---|---|---|
| 38 | Math-59 | FastMath.atanh / cosh / log1p |
| 39 | Math-63 | MathUtils.mulAndCheck / binomialCoefficientDouble / checkOrder |
| 40 | Math-79 | MathUtils.binomialCoefficientLog / nextAfter / equals |
| 41 | Lang-13 | SerializationUtils.clone / serialize / deserialize |
| 48 | Lang-21 | DateUtils.round / iterator / ceiling |
| 50 | Lang-52 | StringEscapeUtils.escapeHtml / unescapeHtml / escapeXml |
| 51 | Lang-50 | FastDateFormat.getTimeInstance |
| 54 | JacksonCore-10 | ByteQuadsCanonicalizer.createRoot |
| 55 | Lang-38 | FastDateFormat.getInstance |
| 56 | Lang-56 | FastDateFormat.getDateInstance |
| 58 | JacksonCore-20 | JsonGenerator.collectDefaults |
| 62 | Closure-174 | NodeUtil.verifyScopeChanges / newQualifiedNameNode / mapMainToClone |
| 63 | Math-85 | UnivariateRealSolverUtils.bracket |
| 65 | Math-36 | BigFraction.getReducedFraction |
| 66 | Math-46 | Complex.valueOf |
| 68 | Closure-60 | NodeUtil.getSourceName |
| 69 | Closure-61 | NodeUtil.getNearestFunctionName |
| 71 | Closure-9 | ProcessCommonJSModules.toModuleName |
| 73 | Closure-109 | JsDocInfoParser.parseTypeString |
| 75 | Closure-107 | CommandLineRunner.main |
| 76 | Closure-122 | IRFactory.transformTree |
| 78 | Closure-27 | IR.script |
| 81 | Closure-37 | NodeTraversal.traverseRoots |
| 90 | Closure-137 | NodeUtil.getVarsDeclaredInBranch |

**Not attempted: 23 eligible bugs**, because every one of their targets is already an earlier facade or matched to a
higher-ranked batch-4 candidate. Building them would give near-duplicate instances.

| Project | Bugs |
|---|---|
| Lang | 24, 27, 36, 12 |
| JacksonCore | 6 |
| Math | 26, 27, 47, 37 |
| Closure | 26, 32, 133, 42, 68, 81, 84, 83, 151, 101, 157, 158, 149, 141 |

With batch 4, the current eligible pool is exhausted. Widening the pool (its rules are in `MAIN_RUN_PLAN.md`) would change the
methodology, and is not done without the user's approval.

**Checkouts.** The 24 new checkouts were made on 19 October, each with `defects4j checkout -p <P> -v <id>f -w
<store>/defects4j/<P>-<id>/fixed` into a directory that did not exist. Each is at its `D4J_<P>_<id>_FIXED_VERSION` tag. The log is
`main-run/batch4_checkouts.log`. The fixtures are real-directory copies, as before.

**Key preflight.** Before any batch-4 builder starts, the coordinator asserts once, for all 24 keys, that:
- no design, spec, instance, audit, history or variant path exists, apart from the fixtures;
- none of the keys appears in the batch-1, batch-2 or batch-3 task files.

## Cost guard: ceiling $200

The inequality and the definitions of C and M are those of batch 3. Only the cap changes, to **$199.00**, keeping the $1 margin of
batch 3:

    C + 10k × M + (120k + 12) × $0.008  ≤  $199.00     (scripts/mr_cost_guard.py --cap 199)

- The guard is re-run before every block and before any restart of a halted block.
- Plans are `plans/MR_batch4_block<N>_gpt55.json`, and their driver logs are `diagnostic/run_MR_batch4_block<N>_gpt55.out`.
- ACCEPTED instances run first, in pool-rank order, in blocks of at most 5. FLAGGED instances follow, only while the guard allows.
- If k = 0, batch 4 stops and the coordinator reports. Any ACCEPTED or FLAGGED instances left are reported as built but not run.

At registration, C = $137.07, M = $0.6595 and k = 5.

## Integrity

These three checks run after construction, after every regeneration of shared outputs, after every block and at the end:

1. `mr_integrity.py --verify`: batches 1–2, 551 entries.
2. `mr_integrity.py --verify --batches batch3 --manifest b3_integrity_manifest.json`: batch 3, 551 entries, recorded on 19 October.
3. `mr_integrity.py --verify-frozen batch4_frozen_hashes.json`, which is written before any batch-4 build. Its sha256 is in W34. It
   pins:
   - every `mr_*` script and the briefs, the checklist, this document, `batch4_tasks.json` and `batch4_checkouts.log`;
   - the governing and completed-batch records:
     - `BATCH3_PREREGISTRATION.md`, `MAIN_RUN_PLAN.md` and `DEFECTS4J_CANDIDATE_POOL.csv`;
     - `batch1/2/3_tasks.json`, `batch3_checkouts.log` and `batch1/2/3_build_audit_results.json`;
     - `AMENDMENTS.md` through W33, as a pinned snapshot that the live file must still begin with;
   - both integrity manifests;
   - the batch-3 analysis files (dispositions, trace checks, robustness, prediction, retrospective classification and frozen hashes);
   - `diagnosis_notes.json`;
   - the batch-1–3 driver logs (`diagnostic/run_MR_batch1*`, `run_MR_batch2*` and `run_MR_batch3*`), whose probe lines feed the
     guard's C;
   - the ledgers of the other servers (`diagnostic/block_w50.jsonl`, `block_w56.jsonl` and `block_wmDiag.jsonl`). Together with
     the guard's ledger-set check, any spend recorded for a server other than w55, or in a new ledger file, stops batch 4 instead
     of escaping C.
- Any mismatch stops batch 4 until it is restored and recorded.
- The key preflight is the same as batch 3: no design, spec, instance, audit or variant path may exist for a batch-4 key before its
  builder starts.

## Robustness raters (pre-registered here; secondary)

After every disposition is final and before block 1, two additional blind raters per ACCEPTED batch-4 gold apply the frozen
checklist under shuffled labels, as in batch 3. They never change a disposition.

## Reading (secondary; a replication of batch 3)

The KPI stays the count of instances with at least one shift. In addition, batch 4 is read with batch 3's thresholds, as a
replication of the batch-3 result:

| Condition | Reading |
|---|---|
| n < 5 | INCONCLUSIVE |
| s ≥ 4/5 | REPLICATES |
| s ≤ 2/3 | DOES NOT REPLICATE |
| otherwise | INCONCLUSIVE |

- n counts ACCEPTED batch-4 instances with 5 valid runs.
- s is the share of n with at least one shift.
- Subsets: (a) majority of 3 raters NO_TRACE; (b) all 3 raters NO_TRACE.

Batch 4 is Closure-heavy (10 of 24 candidates), so `mr_batch3_eval.py --batch batch4` also reports the reading per project.

## Outputs

**Rows added.** The manifests protect batch-1, batch-2 and batch-3 rows at field level in the four CSVs, in `per_run.json` and in
the driver ledger. The `.md` files and the cost ledgers are regenerated from those verified rows by the pinned scripts. Their
aggregate lines change, and their batch-1–3 inputs are pinned as above.

- `INSTANCE_BUILD_LOG.csv` and `INSTANCE_PROVENANCE.csv`;
- `MAIN_RUN_RUNS.csv` and `MAIN_RUN_RESULTS.csv`;
- `SHIFTED_INSTANCES.md` and `FAILED_TO_TRANSFER.md`;
- both cost ledgers;
- amendments W34 onward.

**New:**

- `main-run/batch4_tasks.json`, `main-run/batch4_checkouts.log` and `main-run/batch4_build_audit_results.json`;
- `main-run/analysis/batch4_dispositions.json`, `batch4_trace_checks.json`, `batch4_trace_robustness.json`,
  `batch4_prediction.json`, `batch4_frozen_hashes.json` and `diagnosis_notes_batch4.json`.

**Rewritten:** `SUPERVISOR_PROGRESS_UPDATE.md`, as update 4.
