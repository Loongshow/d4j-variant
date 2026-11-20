# Main run, batch 9 (cell C10i, the remaining tier: V2-best bugs and Closure): pre-registration

Written before any batch-9 design, build or run, after the batch-9 checkouts and host confirmation. The sha256 of this file is recorded in
`AMENDMENTS.md` (W61). Batch 9 is the fifth and last tier of the "all Defects4J bugs" extension (W42, W45): the C10i recipe (instance-method
facade, batches 7–8) applied to the remaining bugs that **have no usable static facade** in their modified classes (pool v2 `facade_class_basis = no_tested_static`
or no strictly tested static target). These instances are reported in the C10i cell (`mr3_report.py`, tier `MAIN_RUN_C10I`), with batch
`batch9`, and are never pooled with C10/C10f in a headline without the composition (W42).

## Authorisation

W45 (the user's standing instruction of 25 October: "以后不用问我，直接运行，直到遇到不可控困难再停止"), the 23-October goal of running every
Defects4J bug ("我倒是希望我跑所有的defect4j bug ... 希望数据量足够大"), the instruction of 27 October to resume ("resume the work"), and the instruction of 26 October to continue toward about 200 instances
("充值好了，继续跑试验", given in reply to the 200-instance projection of the same day, which projected a cumulative of about $490 and
recommended raising the guard cap to $550–600), and the 23-October instruction that cost is not a limit ("不需要考虑 cost limit"). **The
guard cap stays $600** (raised from $500 for batch 8, W56); the per-block checks of W45 are unchanged. The cap stays a sanity stop:
if the guard's worst case exceeds it, the launcher stops and the coordinator reports.

## Everything from batches 3 to 8, unchanged

`BATCH3_…BATCH8_PREREGISTRATION.md` apply unless this document says otherwise: the C10 recipe (`BUILD_BRIEF.md`, sha256
`cc565d61c221…`), the C10i addendum (`BUILD_BRIEF_C10I_ADDENDUM.md`, `3be3eafbfcd8…`),
the C10f host section (`BUILD_BRIEF_C10F_ADDENDUM.md`, `f50c479a7abe…`), the no-local-trace
HARD rule (`NO_LOCAL_TRACE_CHECKLIST.md`, `487a966a09f9…`), `TRACE_CHECK_BRIEF.md` and `AUDIT_BRIEF.md`
(with the batch-7 audit item `g_c10i_rules`), the pipeline (builder → auditor + blind checker → one redesign → disposition table), the frozen
protocol on w55 (gpt-5.5, medium, 50 tool calls, 5 tests, 300 s; 5 runs per instance), the KPI (SHIFT = gold rank > 1; INSTANCE_SUCCESS =
at least one shift in 5 valid runs), the 16 gates, packaging and the key, the robustness raters (secondary), facade reuse as a recorded
alternative with distinctness preferred, the per-block launcher `scripts/mr_run_blocks.sh` (cap $600 since batch 8, see Authorisation). No completed instance is redesigned, rebuilt or re-run.

## What defines batch 9

**1. Unit.** The last attempted tier of the 23-October instance-method profile: every bug not used in batches 1–8 whose modified classes offer
a strictly tested public instance method (same candidate filter as batch 8) and whose best candidate is **V2** (the receiver passed as a
parameter), plus the **13 Closure bugs** with any qualifying candidate, which batch 8 deferred only for disk (33 GB free on 27 October).
Mockito (unscorable on the frozen server) and Csv (package-private hosts) stay deferred; after batch 9 no other bug of the profile is left
unattempted. Selection script `main-run/batch9_prep/make_tasks.py` (`58e9d18dd7ed…`; batch 8's with this filter, ranks
from 307, and facade reuse checked against batches 7 and 8). Batch 8 found V2 facades shifting less (4 of 11) than V1 (32 of 48); batch 9 is
the V2 tier at scale, read descriptively.

**2. Facade and hosts.** `construction/mainrun/BUILD_BRIEF_C10I_B8_NOTE.md` (`b993d4bee1ea…`): no static pair
(addendum §2 void); hosts by `host_mode` with every allowed candidate's file excluded — `1500`: the recipe's seeded draw at build time;
`largest5`: the five largest public classes confirmed on the checkout (`batch9_prep/confirm_hosts.py`, `74051e3ccf98…`;
a 1500-regime task with fewer than five such classes on the checkout is moved to largest5 and marked); distinctness preferred via
`facade_planned_by`. Reachability probe mandatory. Labels and paths are batch 7's (`mr3_spec.py`, `MI-<key>`, `designs/<key>__i.py`).

**3. Records.** `scripts/mr3_build_records.py` (`d271ebc2a775…`) now also reads `batch9_tasks.json` and
`analysis/batch9_dispositions.json`; `scripts/mr_integrity.py` (`570df0971e15…`) resolves C10i ids by `fixture_key` and
knows `MR_batch9_*` plans; `scripts/mr3_report.py` (`e7e1fd85af27…`) reports the cell with a `batch` column.
Dispositions, robustness and host confirmation by `batch9_prep/*.py` (copies of batch 8's with the batch-9 file names).

**4. KPI and reading (descriptive; the batch-3 thresholds are reported as a secondary reading as in batches 4–6).** Primary: ACCEPTED
batch-9 instances with at least one shift in 5 valid runs, over instances with a distinct facade (effective reuse recorded on the facade
chosen). Secondary: all ACCEPTED; per project; per host regime; per facade variant; and the C10i cell as a whole (batches 7–9) beside
C10 and C10f. Comparison with the static cells is descriptive (different bugs); the paired comparison stays batch 7's.

## Candidates (75)

**Order (W62, the user's instruction of 27 October "按 9a/9b 调整").** Batch 9 is built and run in two sub-batches. **9a** = the projects whose
C10i cell is empty or thin (Closure, Cli, Collections, Compress, Codec, JacksonCore, JacksonXml; 30 candidates), ranks first;
**9b** = Math, Jsoup, JacksonDatabind, Chart, Lang (45 candidates). 9a is constructed, rated, packaged and run before 9b
is constructed (no construction during paid runs). Everything else in this document applies to both; the original W61 ranks are kept as
`pool_rank_W61`.

Batch-9 order = ranks 307–381, by project and bug id. 51 have a planned-distinct facade; 24 plan a facade already planned by an
earlier task (recorded; the builder may choose another allowed candidate). Best-candidate variants: {'V2': 69, 'V0': 1, 'V1': 5}. Host regimes:
{'1500': 39, 'largest5': 36}; the smallest largest5 fifth host has 276 lines, the median 725. Task file `main-run/batch9_tasks.json`
(sha256 `300290ec89e4…`); construction in two interleaved halves (`half` a/b) only if disk requires it.

| Project | Candidates | of which largest5 |
|---|---|---|
| Chart | 6 | 0 |
| Cli | 8 | 8 |
| Closure | 13 | 0 |
| Codec | 1 | 1 |
| Collections | 4 | 4 |
| Compress | 2 | 2 |
| JacksonCore | 1 | 0 |
| JacksonDatabind | 9 | 6 |
| JacksonXml | 1 | 1 |
| Jsoup | 9 | 9 |
| Lang | 4 | 0 |
| Math | 17 | 5 |

| Rank | Sub | Task | Regime | Host lines (hop 1 → 5) | Allowed instance facades | Planned reuse of |
|---|---|---|---|---|---|---|
| 307 | 9a | Closure-18__i | 1500 | seeded draw | Compiler.init (V2, 10 lines) / Compiler.getReverseAbstractInterpreter (V2, 13 lines) | — |
| 308 | 9a | Closure-31__i | 1500 | seeded draw | Compiler.init (V2, 10 lines) / Compiler.getReverseAbstractInterpreter (V2, 13 lines) | Closure-18__i |
| 309 | 9a | Closure-57__i | 1500 | seeded draw | ClosureCodingConvention.getAssertionFunctions (V0, 18 lines) | — |
| 310 | 9a | Closure-82__i | 1500 | seeded draw | JSType.getTypesUnderEquality (V2, 19 lines) | — |
| 311 | 9a | Closure-104__i | 1500 | seeded draw | UnionType.matchesNumberContext (V1, 8 lines) / UnionType.matchesStringContext (V1, 8 lines) / UnionType.matchesObjectContext (V1, 8 lines) | — |
| 312 | 9a | Closure-110__i | 1500 | seeded draw | Node.getQualifiedName (V2, 15 lines) / Node.getSourceOffset (V2, 10 lines) / Node.isQualifiedName (V2, 11 lines) | — |
| 313 | 9a | Closure-146__i | 1500 | seeded draw | JSType.getTypesUnderEquality (V2, 19 lines) | Closure-82__i |
| 314 | 9a | Closure-149__i | 1500 | seeded draw | CompilerOptions.getDefineReplacements (V1, 18 lines) | — |
| 315 | 9a | Closure-155__i | 1500 | seeded draw | Scope.getVar (V1, 9 lines) | — |
| 316 | 9a | Closure-162__i | 1500 | seeded draw | Scope.getVar (V1, 9 lines) | Closure-155__i |
| 317 | 9a | Closure-165__i | 1500 | seeded draw | ObjectType.isUnknownType (V2, 19 lines) | — |
| 318 | 9a | Closure-167__i | 1500 | seeded draw | JSType.isNominalConstructor (V2, 18 lines) / JSType.getTypesUnderShallowInequality (V2, 16 lines) / JSType.canTestForShallowEqualityWith (V2, 12 lines) | — |
| 319 | 9a | Closure-169__i | 1500 | seeded draw | UnionType.isSubtype (V1, 15 lines) / UnionType.matchesNumberContext (V1, 8 lines) / UnionType.matchesStringContext (V1, 8 lines) | — |
| 320 | 9a | Cli-8__i | largest5 | 680, 417, 372, 320, 311 | HelpFormatter.printHelp (V2, 29 lines) | — |
| 321 | 9a | Cli-11__i | largest5 | 680, 432, 372, 320, 311 | HelpFormatter.printHelp (V2, 29 lines) | Cli-8__i |
| 322 | 9a | Cli-23__i | largest5 | 674, 399, 385, 366, 276 | HelpFormatter.printHelp (V2, 29 lines) | Cli-8__i |
| 323 | 9a | Cli-24__i | largest5 | 674, 399, 385, 366, 276 | HelpFormatter.printHelp (V2, 29 lines) | Cli-8__i |
| 324 | 9a | Cli-25__i | largest5 | 674, 399, 385, 366, 276 | HelpFormatter.printHelp (V2, 29 lines) | Cli-8__i |
| 325 | 9a | Cli-32__i | largest5 | 705, 689, 430, 388, 375 | HelpFormatter.printHelp (V2, 29 lines) | Cli-8__i |
| 326 | 9a | Cli-33__i | largest5 | 705, 689, 430, 388, 375 | HelpFormatter.printHelp (V2, 29 lines) | Cli-8__i |
| 327 | 9a | Cli-36__i | largest5 | 1094, 1006, 694, 430, 396 | OptionGroup.toString (V2, 38 lines) | — |
| 328 | 9a | Collections-4__i | largest5 | 2084, 1994, 1716, 1644, 1467 | MultiValueMap.remove (V2, 13 lines) | — |
| 329 | 9a | Collections-10__i | largest5 | 2085, 1995, 1776, 1645, 1468 | MultiValueMap.remove (V2, 13 lines) | Collections-4__i |
| 330 | 9a | Collections-22__i | largest5 | 2172, 1779, 1762, 1389, 1249 | ListOrderedMap.putAll (V2, 15 lines) | — |
| 331 | 9a | Collections-27__i | largest5 | 2228, 1892, 1797, 1523, 1389 | MultiValueMap.putAll (V2, 10 lines) / MultiValueMap.removeMapping (V2, 13 lines) | — |
| 332 | 9a | Compress-6__i | largest5 | 1880, 968, 945, 805, 700 | ZipArchiveEntry.setUnixMode (V2, 9 lines) / ZipArchiveEntry.equals (V2, 18 lines) | Compress-13__i |
| 333 | 9a | Compress-38__i | largest5 | 1621, 1330, 1149, 1112, 1014 | TarArchiveEntry.isDirectory (V2, 14 lines) / TarArchiveEntry.isFile (V2, 8 lines) / TarArchiveEntry.writeEntryHeader (V2, 11 lines) | — |
| 334 | 9a | Codec-6__i | largest5 | 1105, 1071, 582, 492, 407 | Base64InputStream.read (V2, 9 lines) | — |
| 335 | 9a | JacksonCore-18__i | 1500 | seeded draw | UTF8JsonGenerator.writeRaw (V2, 9 lines) | — |
| 336 | 9a | JacksonXml-6__i | largest5 | 1030, 823, 580, 537, 395 | ToXmlGenerator.initGenerator (V2, 24 lines) | — |
| 337 | 9b | Chart-1__i | 1500 | seeded draw | AbstractCategoryItemRenderer.getLegendItems (V2, 32 lines) / AbstractCategoryItemRenderer.addAnnotation (V2, 16 lines) | — |
| 338 | 9b | Chart-3__i | 1500 | seeded draw | TimeSeries.setMaximumItemCount (V2, 9 lines) / TimeSeries.update (V2, 8 lines) / TimeSeries.getDataItem (V2, 8 lines) | — |
| 339 | 9b | Chart-4__i | 1500 | seeded draw | XYPlot.getLegendItems (V2, 29 lines) / XYPlot.getDomainAxisForDataset (V2, 18 lines) / XYPlot.getRangeAxisForDataset (V2, 18 lines) | Chart-14__i |
| 340 | 9b | Chart-9__i | 1500 | seeded draw | TimeSeries.addOrUpdate (V2, 35 lines) / TimeSeries.removeAgedItems (V2, 15 lines) / TimeSeries.delete (V2, 8 lines) | — |
| 341 | 9b | Chart-15__i | 1500 | seeded draw | PiePlot.setInteriorGap (V2, 12 lines) / PiePlot.setExplodePercent (V2, 9 lines) | — |
| 342 | 9b | Chart-17__i | 1500 | seeded draw | TimeSeries.addOrUpdate (V2, 35 lines) / TimeSeries.removeAgedItems (V2, 15 lines) / TimeSeries.delete (V2, 8 lines) | Chart-9__i |
| 343 | 9b | JacksonDatabind-2__i | largest5 | 3176, 1622, 1585, 1474, 1125 | TokenBuffer.writeBinary (V2, 12 lines) | — |
| 344 | 9b | JacksonDatabind-6__i | largest5 | 3174, 1778, 1622, 1585, 1478 | StdDateFormat.parse (V2, 22 lines) | — |
| 345 | 9b | JacksonDatabind-7__i | largest5 | 3190, 1622, 1585, 1486, 1125 | TokenBuffer.deserialize (V2, 20 lines) / TokenBuffer.writeBinary (V2, 12 lines) | — |
| 346 | 9b | JacksonDatabind-15__i | 1500 | seeded draw | StdSerializer.getSchema (V2, 8 lines) | — |
| 347 | 9b | JacksonDatabind-30__i | largest5 | 1918, 1820, 1532, 1390, 1311 | ObjectMapper.enableDefaultTyping (V2, 14 lines) / TokenBuffer.deserialize (V2, 20 lines) / TokenBuffer.writeBinary (V2, 11 lines) | — |
| 348 | 9b | JacksonDatabind-31__i | largest5 | 3858, 1918, 1820, 1532, 1390 | TokenBuffer.deserialize (V2, 20 lines) / TokenBuffer.writeBinary (V2, 11 lines) | JacksonDatabind-7__i |
| 349 | 9b | JacksonDatabind-57__i | largest5 | 3929, 1931, 1893, 1568, 1431 | ObjectReader.treeToValue (V2, 9 lines) | — |
| 350 | 9b | JacksonDatabind-73__i | 1500 | seeded draw | POJOPropertyBuilder.getMutator (V2, 10 lines) | — |
| 351 | 9b | JacksonDatabind-108__i | 1500 | seeded draw | ObjectReader.treeToValue (V2, 9 lines) | JacksonDatabind-57__i |
| 352 | 9b | Jsoup-1__i | largest5 | 828, 420, 374, 371, 348 | Document.title (V2, 8 lines) | — |
| 353 | 9b | Jsoup-7__i | largest5 | 2274, 1044, 543, 504, 455 | Document.title (V2, 8 lines) | Jsoup-1__i |
| 354 | 9b | Jsoup-29__i | largest5 | 1119, 661, 617, 536, 454 | Document.title (V2, 8 lines) | Jsoup-1__i |
| 355 | 9b | Jsoup-49__i | largest5 | 1223, 977, 707, 703, 635 | Node.absUrl (V2, 8 lines) | — |
| 356 | 9b | Jsoup-54__i | largest5 | 1237, 1024, 728, 702, 694 | W3CDom.fromJsoup (V2, 13 lines) | — |
| 357 | 9b | Jsoup-73__i | largest5 | 1435, 1249, 778, 734, 725 | W3CDom.fromJsoup (V2, 13 lines) | Jsoup-54__i |
| 358 | 9b | Jsoup-75__i | largest5 | 1464, 1254, 778, 739, 725 | Attributes.asList (V2, 9 lines) | — |
| 359 | 9b | Jsoup-84__i | largest5 | 1458, 1186, 778, 733, 725 | W3CDom.fromJsoup (V2, 13 lines) | Jsoup-54__i |
| 360 | 9b | Jsoup-92__i | largest5 | 1524, 1205, 778, 741, 725 | Attributes.asList (V2, 9 lines) | Jsoup-75__i |
| 361 | 9b | Lang-6__i | 1500 | seeded draw | CharSequenceTranslator.translate (V2, 23 lines) / CharSequenceTranslator.translate (V2, 12 lines) | — |
| 362 | 9b | Lang-8__i | 1500 | seeded draw | FastDatePrinter.format (V2, 11 lines) | — |
| 363 | 9b | Lang-9__i | 1500 | seeded draw | FastDateParser.parse (V2, 12 lines) | — |
| 364 | 9b | Lang-10__i | 1500 | seeded draw | FastDateParser.parse (V2, 12 lines) | Lang-9__i |
| 365 | 9b | Math-7__i | 1500 | seeded draw | AbstractIntegrator.integrate (V2, 24 lines) | — |
| 366 | 9b | Math-11__i | 1500 | seeded draw | MultivariateNormalDistribution.sample (V2, 15 lines) | — |
| 367 | 9b | Math-13__i | 1500 | seeded draw | AbstractLeastSquaresOptimizer.guessParametersErrors (V2, 12 lines) / AbstractLeastSquaresOptimizer.computeSigma (V2, 9 lines) | — |
| 368 | 9b | Math-14__i | 1500 | seeded draw | AbstractLeastSquaresOptimizer.computeSigma (V2, 9 lines) | — |
| 369 | 9b | Math-29__i | 1500 | seeded draw | OpenMapRealVector.mapAddToSelf (V2, 5 lines) | — |
| 370 | 9b | Math-35__i | 1500 | seeded draw | ElitisticListPopulation.nextGeneration (V2, 13 lines) | — |
| 371 | 9b | Math-37__i | 1500 | seeded draw | Complex.abs (V2, 20 lines) | — |
| 372 | 9b | Math-44__i | 1500 | seeded draw | AbstractIntegrator.integrate (V2, 23 lines) | — |
| 373 | 9b | Math-45__i | 1500 | seeded draw | OpenMapRealMatrix.multiply (V2, 23 lines) | — |
| 374 | 9b | Math-47__i | 1500 | seeded draw | Complex.abs (V2, 20 lines) | Math-37__i |
| 375 | 9b | Math-53__i | 1500 | seeded draw | Complex.abs (V2, 22 lines) | Math-37__i |
| 376 | 9b | Math-58__i | 1500 | seeded draw | GaussianFitter.fit (V2, 28 lines) | — |
| 377 | 9b | Math-95__i | largest5 | 1466, 1343, 1294, 1059, 1057 | FDistributionImpl.cumulativeProbability (V2, 13 lines) | — |
| 378 | 9b | Math-96__i | largest5 | 1466, 1345, 1295, 1059, 1057 | Complex.abs (V2, 22 lines) | Math-37__i |
| 379 | 9b | Math-101__i | largest5 | 1320, 1069, 1041, 1037, 1035 | ComplexFormat.parse (V2, 8 lines) / ComplexFormat.format (V2, 16 lines) | — |
| 380 | 9b | Math-102__i | largest5 | 1319, 1069, 1036, 1033, 1006 | ChiSquareTestImpl.chiSquareTest (V2, 7 lines) / ChiSquareTestImpl.chiSquareTestDataSetsComparison (V2, 7 lines) / ChiSquareTestImpl.chiSquareTest (V2, 6 lines) | — |
| 381 | 9b | Math-106__i | largest5 | 1318, 1053, 1035, 740, 688 | ProperFractionFormat.format (V2, 22 lines) | — |

Expected: UNBUILDABLE outcomes of the batch-5/6/7 kinds (no single-trigger omission; no existing test reaches the facade despite the strict
name check, the overload false positive of Lang-38; nothing to split); JacksonXml and the non-harness Chart bugs are first attempts in
those projects, and a staging failure (G13/G14) is recorded as UNBUILDABLE with its reason.

**Key preflight.** Before any batch-9 builder starts, the coordinator asserts for all 75 keys that no `designs/<key>__i.py`,
`specs/MI-<key>.json`, `instances/MI-<key>/`, `audits/MI-<key>.json` or `history/<key>__i/` exists, that every fixture exists with `.git`, and
that none of the keys appears in the batch-1 to batch-9 task files.

## Cost guard

`mr_cost_guard.py --cap 600`, re-run before every block by `mr_run_blocks.sh`; blocks of at most 5 in batch-9 order; plans
`plans/MR_batch9_block<N>_gpt55.json`. Expected run cost about 75 × 5 × $0.42 ≈ $158 if every candidate were built; with the
batch-9 yield (60 of 97) about $97; with the batch-6 yield (38 of 62) about $97.

## Integrity

1. The batch-1/2 to batch-7 manifests as before; the batch-9 manifest (`b8_integrity_manifest.json`, W60) recorded after the batch-9
   runs and before any batch-9 row.
2. `mr_integrity.py --verify-frozen batch9_frozen_hashes.json`, written before any batch-9 build: every `mr_*`, `mr2_*` and `mr3_*` script,
   the briefs, the checklist, the addenda and this note, this document, `batch9_tasks.json`, `batch9_checkouts.log`, the batch-1–8 task
   files and dispositions, the pool files, the manifests, the other servers' ledgers, and `AMENDMENTS.md` through W61 as a pinned prefix. Mutable outputs (`FREEZE.json`, the key, the C10i record CSVs) are not pinned (W57).

## Outputs

`main-run/batch9_tasks.json`, `batch9_checkouts.log`, `batch9_build_audit_results.json`; `analysis/batch9_dispositions.json`,
`batch9_trace_checks.json`, `batch9_trace_robustness.json`, `batch9_prediction.json` (`mr_batch3_eval.py --batch batch9`, reading the C10i
results file), `batch9_frozen_hashes.json`; rows in `INSTANCE_BUILD_LOG_C10I.csv` / `INSTANCE_PROVENANCE_C10I.csv`; the `mr3_report.py`
files; `SUPERVISOR_PROGRESS_UPDATE.md` as update 9.
