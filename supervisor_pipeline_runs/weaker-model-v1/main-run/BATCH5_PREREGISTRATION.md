# Main run, batch 5: pre-registration

Written on 24 October 2026, after the batch-5 checkouts and before any batch-5 design, build or run. The sha256 of this file is
recorded in `AMENDMENTS.md` (W42). Batch 5 is the first batch of the "all Defects4J bugs" extension that the supervisor asked for
on 23 October; it is the tier of that extension that changes the recipe least: the C10 recipe, the frozen protocol, the no-local-trace
rule, the audit and the disposition table are all unchanged. What changes is the pool: the slow-suite rule is dropped, the pool's
reading errors are corrected, hidden candidates are no longer capped, and a facade may be reused when it is recorded.

## Authorisation

The user, after meeting the supervisor, on 23 October:

> "我倒是希望我跑所有的 defect4j bug，尽管有些可能不会发生 shift，但是希望数据量足够大，不需要考虑 cost limit"
> (I would like to run all Defects4J bugs; some may not shift, but the data set should be large; no need to consider a cost limit.)

and, on the host rule: "没有 '≥1500 行' 就找 repo 里面的 largest file 就好了，藏不住就藏不住" (where there are no ≥1500-line classes, use
the repository's largest files; if the fault cannot be hidden, so be it). On 24 October the user chose the 13-day plan
(`thesis_writeup/supervisor_replies/2026-10-23/run_all_bugs/PLAN_ALL_BUGS_ZH.md`) and wrote "现在开始运行" (start now).

The $200 ceiling of W34 is therefore withdrawn by the user. A sanity cap replaces it (see "Cost guard").

## Everything from batches 3 and 4, unchanged

`main-run/BATCH3_PREREGISTRATION.md` and `main-run/BATCH4_PREREGISTRATION.md` apply in full unless this document says otherwise.
In particular, unchanged:

- the C10 recipe (`construction/mainrun/BUILD_BRIEF.md`, sha256 `cc565d61…`, not edited for batch 5; its "batch 3" labels and its
  facade-choice line, which names the batch-3 and batch-4 pre-registrations, apply to batch 5 and to this document, and builders are
  told so in their task text);
- the **no-local-trace HARD rule** (`NO_LOCAL_TRACE_CHECKLIST.md`, sha256 `487a966a…`), `TRACE_CHECK_BRIEF.md` (`e1ff2aeb…`) and
  `AUDIT_BRIEF.md` (`2d3527cd…`);
- the pipeline: builder, then an independent auditor and a blind trace checker in parallel; one pre-run redesign on REJECTED or
  TRACE, checked by a new auditor and a new checker; the v1 archive before a redesign; the missing-verdict rule;
- the disposition table, applied top to bottom: checker TRACE → UNBUILDABLE (local trace); audit REJECTED → REJECTED; audit
  FLAG_AMBIGUOUS → FLAGGED (run after all ACCEPTED instances, reported separately, never counted); audit CONFIRMED → ACCEPTED;
- the frozen protocol on w55: gpt-5.5, medium effort, 50 tool calls, 5 tests, 300 s; the frozen driver with its health gate, stall
  rules and one replacement per slot; the exclusion rules; 5 runs per instance in seeded rounds;
- the KPI: SHIFT = gold rank > 1 (absent from the top 10 = 11); INSTANCE_SUCCESS = at least one shift in the first 5 valid runs;
  scoring with the frozen `mx_metrics.py` and `scripts/mr_report.py`;
- the robustness raters (two extra blind raters per ACCEPTED gold, secondary) and the replication reading with batch 3's thresholds,
  per project (`mr_batch3_eval.py --batch batch5`);
- no completed batch-1 to batch-4 instance is redesigned, rebuilt or re-run.

## What changes in batch 5

### 1. The slow-suite rule is dropped

`mr_candidate_pool.py` rejected every bug of Time, Collections, JacksonDatabind and Mockito because their full suites were recorded at
959–1,001 s on 24 September (`core-benchmark-scaleup-v2/PROJECT_SELECTION.md`). Those timings do not reproduce. Re-timed on 23
October from fresh `defects4j checkout`s, the full suites ran in 4–62 s (Time-1 4 s, and 35–41 s in an independent re-run;
Collections-1 8–9 s; JacksonDatabind-1 13–19 s; Mockito-1 45–62 s); the 24-September session's own notes record JVM stalls of
about 1,000 s. The record of this re-timing is `thesis_writeup/supervisor_replies/2026-10-23/run_all_bugs/exclusion_reasons_oct23/`
(`provenance.md` §2.3 (xii), `fix_provenance/retime_results.txt`; `proto_D/REPORT.md`). The user has in any case removed the time
constraint. Mockito's 978 s was its compile time.

With that rule gone, 30 bugs pass every other pool rule unchanged (at least 5 public host classes of ≥ 1,500 lines besides the
target's own class; a public static 4–50-line self-contained target in the bug's modified classes that an existing test names):
JacksonDatabind 14 and Time 16. Collections and Mockito gain nothing: every one of their bugs also fails the host rule.

### 2. Two pool reading errors are corrected

- **Time-22 to Time-27.** Their git trees keep the `JodaTime/` directory that Defects4J strips at checkout (`Time.pm:68–70`), so the
  pool read no source at all and reported "0 hosts, no static target". Read at the right path, Time-23, -25 and -26 have 9 hosts and
  7–9 tested static candidates (`main-run/batch5_prep/recompute_candidates.py`, output `recomputed_candidates.json`). Time-22, -24
  and -27 still fail another rule and are not in batch 5.
- **The 6-row candidate cap.** The pool stored only the 6 highest-scoring tested candidates per bug (`mr_candidate_pool.py:128`).
  Lang-24, Lang-27 and Lang-36 were skipped in batch 4 as "facade reuse only" because the visible rows were `NumberUtils.min/max`,
  the facades of Lang-7 and Lang-16 (W41). Uncapped, the class has 13 more tested static methods, 11 never used or tried as a facade.
  The three bugs receive three disjoint sets of them.

The candidate records for these bugs use the pool's own filter and fields (`score_candidate_methods(require_static=True)`, 4–50
lines, self-containedness > 0, name-based test check). For the other 27 bugs the records are copied from the pool CSV's
`candidates` column.

### 3. Facade reuse is allowed, and recorded

From batch 3 on, a facade had to be distinct from every earlier facade and from every other candidate of the batch (W41 lists the
9 bugs this excluded). Batch 5 keeps distinctness as the **preference** and allows reuse as a **recorded** alternative:

- targets are allocated by maximum bipartite matching in batch-5 order, over targets that are not an earlier facade (main run or
  Stage B, matched by fully qualified class and method) and were not found unbuildable in a sibling revision
  (`NumberUtils.createBigDecimal`, Lang-3, W27); a matched bug may also receive up to two unmatched leftover targets of its own, each
  given to at most one bug;
- a bug with no unused target left gets its shared target with `facade_reuse_of` = the instance(s) whose facade it is (an earlier
  instance, or the batch-5 candidate matched to it);
- `facade_reuse_of` is recorded in `main-run/batch5_tasks.json` and in `main-run/analysis/batch5_dispositions.json`, not in the
  CSVs (their schema is protected by the integrity manifests).

Why: 456 of the 854 Defects4J bugs share their modified-class set with another bug (548 distinct sets), so "all bugs" is not reachable
without reuse. A reused facade is the same construction on a different fixed revision, so these instances are not independent of
their group; they are reported as such.

### 4. KPI: primary and secondary counts

- **Primary (unchanged definition, new scope):** the count of ACCEPTED instances with at least one shift in 5 valid runs, over the
  instances whose facade is distinct (`facade_reuse_of` empty).
- **Secondary:** the same count over all ACCEPTED batch-5 instances, with the reuse groups listed; and the KPI per project.
- The 47 batch-1 to batch-4 instances are reported exactly as before (`mr_report.py` filters on batch).

### 5. Cost guard: the ceiling is withdrawn; a sanity cap of $500 remains

The inequality and the definitions of C and M are those of batch 3:

    C + 10k × M + (120k + 12) × $0.008  ≤  $500.00     (scripts/mr_cost_guard.py --cap 500)

- The guard is re-run before every block and before any restart; the spend is reported to the user after every block.
- Plans are `plans/MR_batch5_block<N>_gpt55.json`, driver logs `diagnostic/run_MR_batch5_block<N>_gpt55.out`.
- ACCEPTED instances run first, in batch-5 order, in blocks of at most 5; FLAGGED instances follow.
- Expected run cost of batch 5: about 37 × 5 × $0.43 ≈ $80 (projection from the main-run mean), bringing the cumulative total to
  about $244; the $500 cap is a stop-and-report, not a budget.

At registration (`mr_cost_guard.py --left 37 --cap 500`): C = $163.9474, M = $0.782629, k = 5, worst case after one block $207.97.

### 6. New projects and new checkouts

- Time and JacksonDatabind have never had a main-run instance. The evaluation server's method catalog covers them (Time-1: 4,165
  entries; JacksonDatabind-104: 6,851; `toolchain.md` §1.7), so their golds and entry points are scorable on w55 unchanged.
- 27 new fixed checkouts were made on 24 October with `defects4j checkout -p <P> -v <id>f -w <store>/defects4j/<P>-<id>/fixed`
  into directories that did not exist (`scripts/mr_checkouts.py`, log `main-run/batch5_checkouts.log`; each line gives the git
  head, the `D4J_<P>_<id>_FIXED_VERSION` tag and the size). Ten keys already had a checkout. Fixtures are real-directory copies with
  `.git`, as before (`mr_lib.py fixture`).

## Candidates (37)

Batch-5 order = rank 92 onward (the pool's 91 eligible bugs hold ranks 1–91). "Allowed facade targets" are the only methods a builder
may use as the facade; if none can carry the recipe validly, the instance is UNBUILDABLE. Source: `main-run/batch5_tasks.json`
(sha256 `22779fee…`), produced by `main-run/batch5_prep/make_tasks.py`.

| Rank | Bug | Allowed facade targets | Facade reuse of |
|---|---|---|---|
| 92 | JacksonDatabind-37 | SimpleType.construct | — |
| 93 | JacksonDatabind-38 | CollectionType.construct / MapType.construct | — |
| 94 | JacksonDatabind-42 | FromStringDeserializer.types | — |
| 95 | JacksonDatabind-44 | SimpleType.construct | JacksonDatabind-37 |
| 96 | JacksonDatabind-53 | TypeBindings.create | — |
| 97 | JacksonDatabind-56 | FromStringDeserializer.types | JacksonDatabind-42 |
| 98 | JacksonDatabind-59 | MapLikeType.upgradeFrom / CollectionLikeType.construct / MapLikeType.construct | — |
| 99 | JacksonDatabind-63 | JsonMappingException.from | — |
| 100 | JacksonDatabind-66 | StdKeyDeserializer.forType | — |
| 101 | JacksonDatabind-71 | StdKeyDeserializer.forType | JacksonDatabind-66 |
| 102 | JacksonDatabind-75 | EnumSerializer.construct | — |
| 103 | JacksonDatabind-83 | FromStringDeserializer.types | JacksonDatabind-42 |
| 104 | JacksonDatabind-99 | ReferenceType.upgradeFrom / ReferenceType.construct | — |
| 105 | JacksonDatabind-105 | JdkDeserializers.find | — |
| 106 | Time-1 | UnsupportedDurationField.getInstance | — |
| 107 | Time-2 | UnsupportedDurationField.getInstance | Time-1 |
| 108 | Time-3 | MutableDateTime.now | — |
| 109 | Time-5 | Period.fieldDifference | — |
| 110 | Time-6 | GJChronology.getInstance | — |
| 111 | Time-8 | DateTimeZone.setDefault | — |
| 112 | Time-9 | DateTimeZone.forOffsetMillis | — |
| 113 | Time-11 | ZoneInfoCompiler.main | — |
| 114 | Time-12 | LocalDateTime.fromDateFields / LocalDate.fromDateFields / LocalDate.fromCalendarFields | — |
| 115 | Time-15 | FieldUtils.safeMultiply / FieldUtils.getWrappedValue / FieldUtils.safeAdd | — |
| 116 | Time-17 | DateTimeZone.setProvider | — |
| 117 | Time-18 | GJChronology.getInstance | Time-6 |
| 118 | Time-19 | DateTimeZone.forOffsetHoursMinutes | — |
| 119 | Time-23 | DateTimeZone.forID / DateTimeZone.setNameProvider | — |
| 120 | Time-25 | DateTimeZone.getDefault | — |
| 121 | Time-26 | DateTimeZone.forTimeZone / ZonedChronology.getInstance / LenientDateTimeField.getInstance | — |
| 122 | Lang-24 | NumberUtils.toByte / toDouble / toFloat (lang3.math) | — |
| 123 | Lang-27 | NumberUtils.createInteger / toInt / toLong (lang3.math) | — |
| 124 | Lang-36 | NumberUtils.isDigits / toShort / createDouble (lang3.math) | — |
| 125 | JacksonCore-6 | JsonPointer.compile | JacksonCore-5 |
| 126 | Lang-12 | RandomStringUtils.random | Lang-11 |
| 127 | Closure-26 | ProcessCommonJSModules.toModuleName | Closure-9 |
| 128 | Closure-141 | NodeUtil.getVarsDeclaredInBranch | Closure-137 |

27 candidates have a distinct facade; 10 reuse one. Several allowed targets are short wrappers with little computation of their own
(the `NumberUtils.toX` and `DateTimeZone.setX` methods); the brief's step 7 (UNBUILDABLE when nothing can be split into a chain) is
expected to remove some of them, and that outcome is recorded, not forced.

**Key preflight.** Before any batch-5 builder starts, the coordinator asserts once, for all 37 keys, that no design, spec, instance,
audit, history or variant path exists apart from the fixtures, and that none of the keys appears in the batch-1 to batch-4 task files.

## Integrity

These checks run after construction, after every regeneration of shared outputs, after every block and at the end:

1. `mr_integrity.py --verify` (batches 1–2) and `--verify --batches batch3 --manifest b3_integrity_manifest.json`, as before;
2. `mr_integrity.py --verify --batches batch4 --manifest b4_integrity_manifest.json`: a new manifest of the batch-4 rows and
   artefacts, recorded on 24 October before any batch-5 row existed (404 entries; sha256 `c8e8edc8…`);
3. `mr_integrity.py --verify-frozen batch5_frozen_hashes.json`, written before any batch-5 build. It pins every `mr_*` script, the
   briefs and the checklist, this document, `batch5_tasks.json`, `batch5_checkouts.log`, the governing records
   (`BATCH3/4_PREREGISTRATION.md`, `MAIN_RUN_PLAN.md`, `DEFECTS4J_CANDIDATE_POOL.csv`), the batch-1 to batch-4 task files, checkout
   logs and build-audit results, the batch-3 and batch-4 dispositions and analysis files, all three manifests, the driver logs and
   the other servers' ledgers, and `AMENDMENTS.md` through W41 as a pinned prefix (`main-run/analysis/AMENDMENTS_through_W41.md`).

Any mismatch stops batch 5 until it is restored and recorded.

**Disclosed changes to pinned files** (defaults reproduce the earlier output; checked by re-running the batch-3 and batch-4
evaluations, whose output files are byte-identical):

- `mr_integrity.py` (`3aa86256…` → `6dd6fe7b…`): plan pattern for batch 5;
- `mr_build_records.py` (`c48333d2…` → `4a7faf44…`): batch 5 reads its dispositions file like batches 3–4;
- `mr_batch3_eval.py` (`a28962e5…` → see W42): `--batch batch5` uses the replication labels and names this document in its
  thresholds string; batch-3 and batch-4 output unchanged;
- new scripts: `scripts/mr_checkouts.py` (checkouts), `main-run/batch5_prep/recompute_candidates.py` and `make_tasks.py` (candidate
  records and allocation).

**Pre-existing deviation, disclosed here.** The recipe's anchor picker accepts only 4-space-indented methods
(`scripts/generator/host_search.py:149–154`). In the six Closure instances of batches 2–4, 14 of 30 hops were therefore inserted
into nested classes and 9 at the end of a file. No completed result is changed; the two Closure candidates of batch 5 (Closure-26,
Closure-141) are built with the same unchanged recipe, so the deviation applies to them too and is recorded per hop
(`toolchain.md` §6, P1).

## Outputs

**Rows added** to `INSTANCE_BUILD_LOG.csv`, `INSTANCE_PROVENANCE.csv`, `MAIN_RUN_RUNS.csv`, `MAIN_RUN_RESULTS.csv`, the `.md` reports
and both cost ledgers, regenerated by the pinned scripts from manifest-protected rows.

**New:** `main-run/batch5_tasks.json`, `batch5_checkouts.log`, `batch5_build_audit_results.json`;
`main-run/analysis/batch5_dispositions.json` (with `facade_reuse_of` per instance), `batch5_trace_checks.json`,
`batch5_trace_robustness.json`, `batch5_prediction.json`, `batch5_frozen_hashes.json`, `diagnosis_notes_batch5.json`;
`main-run/batch5_prep/`.

**Rewritten:** `SUPERVISOR_PROGRESS_UPDATE.md`, as update 5, with the primary and secondary KPI, per project and per reuse group.

## What comes after batch 5 (not part of this registration)

Later tiers of the extension change the recipe and are registered separately before their first build: C10f (static facade with the
five largest public classes as hosts when fewer than five reach 1,500 lines), C10i (instance-method facades, variants V0–V5) and the
paired static/instance bridge. Their instances will carry their own cell id so that the frozen metrics keep them apart from C10.
