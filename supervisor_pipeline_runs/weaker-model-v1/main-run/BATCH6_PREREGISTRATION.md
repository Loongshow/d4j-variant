# Main run, batch 6 (cell C10f): pre-registration

Written on 25 October 2026, after the batch-6 checkouts and host confirmation and before any batch-6 design, build or run. The sha256
of this file is recorded in `AMENDMENTS.md` (W46). Batch 6 is the second tier of the "all Defects4J bugs" extension (W42, W45): the
C10 recipe with **fallback hosts**. It is a new cell, **C10f**, kept apart from the 67 C10 instances by its labels.

## Authorisation

W45: the user's standing instruction of 25 October ("以后不用问我，直接运行，直到遇到不可控困难再停止") and the 23-October host rule
("没有 '≥1500 行' 就找 repo 里面的 largest file 就好了，藏不住就藏不住"). The $500 sanity cap and the per-block checks of W45 remain.

## Everything from batches 3 to 5, unchanged

`BATCH3_PREREGISTRATION.md`, `BATCH4_PREREGISTRATION.md` and `BATCH5_PREREGISTRATION.md` apply unless this document says otherwise:
the C10 recipe (`BUILD_BRIEF.md`, sha256 `cc565d61c221…`, not edited), the no-local-trace HARD rule
(`NO_LOCAL_TRACE_CHECKLIST.md`, `487a966a09f9…`), `TRACE_CHECK_BRIEF.md` and `AUDIT_BRIEF.md`,
the pipeline (builder → auditor + blind checker → one redesign → disposition table), the frozen protocol on w55 (gpt-5.5, medium, 50
tool calls, 5 tests, 300 s; 5 runs per instance), the KPI definition (SHIFT = gold rank > 1; INSTANCE_SUCCESS = at least one shift in 5
valid runs), the 16 gates, packaging and the key, the robustness raters (secondary), the replication reading with batch 3's thresholds
(`mr_batch3_eval.py --batch batch6`), facade reuse as a recorded alternative with distinctness preferred (batch 5, §3), the $500 cap and
the per-block launcher (`scripts/mr_run_blocks.sh`). No completed batch-1 to batch-5 instance is redesigned, rebuilt or re-run.

## What defines C10f

**1. Host rule.** Hosts are five distinct public, non-interface, non-enum classes other than the facade's own class. Where at least five
such classes have ≥ 1,500 lines, they are drawn by the recipe's seeded draw as before (`host_mode = 1500`). Otherwise
(`host_mode = largest5`) the hosts are the **five largest** such classes by newline count (ties by path), hop 1 in the largest and hop 5
(the gold) in the fifth largest. Host sizes are recorded per instance as covariates (`host_lines`); the smallest host in this batch has
276 lines and the median fifth host 890 lines (C10 hosts had 1,237–7,104, median
2,269). The builder addendum `construction/mainrun/BUILD_BRIEF_C10F_ADDENDUM.md` (sha256 `f50c479a7abe…`)
gives the procedure; a listed host that cannot carry a static method is replaced by the next-largest public class and the substitution
recorded.

**2. Cell label.** `scripts/mr2_spec.py` (sha256 `42611b664a23…`) is `mr_spec.py` with one changed line:
`mechanism MAIN_RUN_C10F, tier MAIN_RUN_C10F`. The frozen `mx_metrics.py` copies these fields into every row; `mr_report.py` (tier
`MAIN_RUN`) therefore keeps reporting only the 67 C10 instances, and `scripts/mr2_report.py` (sha256 `810f6e92108d…`,
a copy that reads tier `MAIN_RUN_C10F`) writes `MAIN_RUN_C10F_RUNS.csv`, `MAIN_RUN_C10F_RESULTS.csv`, `SHIFTED_INSTANCES_C10F.md`,
`FAILED_TO_TRANSFER_C10F.md`, `COST_LEDGER_C10F.csv` and `analysis/main_run_c10f_summary.json`. Instance ids keep the `MR-<key>` prefix
(no batch-6 bug was attempted before), so `mr_build_records.py`, `mr_key.py`, `mr_package.py`, the driver, the scanner and the freeze
library are unchanged.

**3. Pool v2 and the strict test-caller check.** `main-run/batch6_prep/mr2_candidate_pool.py` (output `main-run/CANDIDATE_POOL_V2.csv`,
`candidate_pool_v2.json`; report `batch6_prep/POOL_V2_REPORT.md`) re-reads all 854 bugs with the pool's candidate filter and a stricter
test-caller check (STRICT1: a test file names the method followed by `(` and the declaring class's simple name, comments and string
literals blanked). It reproduces the original pool (91 eligible, 0 field mismatches) and the verified 23-October recount (SUP-static 213
LOOSE / 173 STRICT1, 0 mismatches). ELIGIBLE_C10F = 166 bugs (101 in the 1500 regime, 65 largest5); 93 of them are already in batches
1–5. Mockito and Csv are deferred (W42 decisions).

**4. Reachability probe (new, mandatory).** Before designing, the builder makes the facade throw and runs its candidate trigger tests;
the facade is usable only if an existing test fails with the probe message (addendum §2). This answers the batch-5 finding that the
pool's name-based check gave false "called by a test" verdicts.

**5. KPI for the cell.** Primary: ACCEPTED C10f instances with at least one shift in 5 valid runs, over instances with a distinct facade.
Secondary: all ACCEPTED C10f instances; per project; per host regime; and, descriptively, shift against the smallest host size and the
gold host size. C10f is never pooled with C10 in a headline without its composition being shown (toolchain plan, W42).

## Candidates (62)

Batch-6 order = ranks 129–190. 53 have a distinct facade; 9 reuse one (recorded). Targets exclude every earlier
facade (main run through batch 5, Stage B) and every target found UNBUILDABLE in a sibling revision (41 targets; list in
`POOL_V2_REPORT.md` §5). Eleven otherwise-eligible bugs were dropped because every target was excluded (Closure-32, -42, -68, -81, -84,
-133, -157; Math-26, -27, -37, -47). Hosts were confirmed on the real checkouts (`batch6_prep/confirm_hosts.py`); source file
`main-run/batch6_tasks.json` (sha256 `b96210ac621f…`).

| Project | Candidates | of which largest5 |
|---|---|---|
| Cli | 4 | 4 |
| Codec | 11 | 11 |
| Collections | 12 | 12 |
| Compress | 13 | 13 |
| Gson | 4 | 4 |
| JacksonCore | 1 | 1 |
| JacksonDatabind | 2 | 1 |
| Jsoup | 8 | 8 |
| JxPath | 1 | 1 |
| Math | 6 | 6 |

| Rank | Bug | Regime | Host lines (hop 1 → 5) | Allowed facade targets | Facade reuse of | Builder warning |
|---|---|---|---|---|---|---|
| 129 | JacksonDatabind-103 | 1500 | 1777, 1756, 4211, 2177, 1949 | ClassUtil.isLocalType / ClassUtil.wrapperType / ClassUtil.primitiveType | — | — |
| 130 | Cli-26 | largest5 | 984, 674, 399, 385, 276 | OptionBuilder.create | — | — |
| 131 | Cli-31 | largest5 | 1020, 705, 689, 430, 388 | OptionBuilder.create | Cli-26 | — |
| 132 | Cli-34 | largest5 | 1042, 705, 689, 430, 386 | OptionBuilder.create | Cli-26 | — |
| 133 | Cli-40 | largest5 | 1092, 1012, 781, 546, 429 | TypeHandler.createValue | — | — |
| 134 | Codec-2 | largest5 | 1104, 536, 406, 388, 365 | Base64.decodeBase64 | — | — |
| 135 | Codec-4 | largest5 | 1105, 582, 407, 387, 361 | Base64.encodeInteger | — | — |
| 136 | Codec-5 | largest5 | 1105, 582, 407, 387, 361 | Base64.isArrayByteBase64 | — | — |
| 137 | Codec-7 | largest5 | 1105, 582, 492, 407, 387 | Base64.encodeBase64 | — | — |
| 138 | Codec-8 | largest5 | 1105, 582, 492, 407, 387 | Base64.encodeBase64 / Base64.isArrayByteBase64 / Base64.encodeInteger | Codec-4, Codec-5, Codec-7 | — |
| 139 | Codec-9 | largest5 | 1105, 750, 582, 428, 407 | Base64.isBase64 | — | — |
| 140 | Codec-11 | largest5 | 1105, 758, 618, 582, 511 | QuotedPrintableCodec.encodeQuotedPrintable / QuotedPrintableCodec.decodeQuotedPrintable | — | — |
| 141 | Codec-13 | largest5 | 1009, 819, 775, 697, 545 | StringUtils.getBytesUnchecked | — | — |
| 142 | Codec-14 | largest5 | 1009, 819, 775, 545, 539 | Rule.getInstance | — | — |
| 143 | Codec-17 | largest5 | 1142, 1088, 1009, 785, 728 | StringUtils.newString | — | — |
| 144 | Codec-18 | largest5 | 1142, 1088, 1009, 785, 728 | StringUtils.equals | — | — |
| 145 | Collections-3 | largest5 | 2084, 1994, 1716, 1644, 1467 | CollectionUtils.get / CollectionUtils.index / CollectionUtils.size | — | — |
| 146 | Collections-5 | largest5 | 2085, 1995, 1717, 1645, 1468 | SetUniqueList.decorate | — | — |
| 147 | Collections-13 | largest5 | 2085, 1995, 1678, 1468, 1333 | ExtendedProperties.convertProperties | — | — |
| 148 | Collections-15 | largest5 | 2085, 1995, 1784, 1678, 1468 | SetUniqueList.decorate | Collections-5 | — |
| 149 | Collections-16 | largest5 | 2085, 1995, 1784, 1678, 1468 | SetUniqueList.decorate | Collections-5 | — |
| 150 | Collections-17 | largest5 | 2144, 1764, 1666, 1447, 1384 | EqualPredicate.equalPredicate | — | — |
| 151 | Collections-18 | largest5 | 2138, 1764, 1666, 1447, 1384 | ListOrderedSet.listOrderedSet | — | — |
| 152 | Collections-19 | largest5 | 2138, 1761, 1744, 1486, 1447 | SetUniqueList.setUniqueList | — | — |
| 153 | Collections-21 | largest5 | 2172, 1805, 1779, 1447, 1389 | SetUniqueList.setUniqueList | — | — |
| 154 | Collections-23 | largest5 | 2171, 1789, 1779, 1389, 1249 | UnmodifiableTrie.unmodifiableTrie | — | — |
| 155 | Collections-24 | largest5 | 2171, 1789, 1779, 1389, 1249 | UnmodifiableBoundedCollection.unmodifiableBoundedCollection | — | — |
| 156 | Collections-25 | largest5 | 2171, 2062, 1791, 1389, 1249 | IteratorUtils.toString / IteratorUtils.collatedIterator / IteratorUtils.filteredIterator | — | — |
| 157 | Compress-7 | largest5 | 1881, 995, 969, 888, 745 | TarUtils.formatNameBytes / TarUtils.formatLongOctalBytes | — | — |
| 158 | Compress-8 | largest5 | 1881, 995, 969, 888, 745 | TarUtils.parseName | — | — |
| 159 | Compress-10 | largest5 | 1886, 1495, 1048, 901, 890 | ZipFile.closeQuietly | — | — |
| 160 | Compress-14 | largest5 | 1886, 1495, 1048, 969, 926 | TarUtils.parseOctalOrBinary | — | — |
| 161 | Compress-17 | largest5 | 1495, 1340, 1071, 1053, 972 | TarUtils.formatOctalBytes | — | — |
| 162 | Compress-24 | largest5 | 1501, 1329, 1083, 1073, 1072 | TarUtils.formatCheckSumOctalBytes | — | — |
| 163 | Compress-26 | largest5 | 1501, 1329, 1083, 1074, 1073 | IOUtils.readFully / IOUtils.skip / IOUtils.closeQuietly | — | — |
| 164 | Compress-27 | largest5 | 1504, 1329, 1083, 1074, 1073 | TarUtils.formatLongOctalOrBinaryBytes | — | — |
| 165 | Compress-31 | largest5 | 1613, 1329, 1121, 1082, 1073 | TarUtils.verifyCheckSum | — | — |
| 166 | Compress-35 | largest5 | 1623, 1329, 1132, 1131, 1108 | TarUtils.formatUnsignedOctalString | — | — |
| 167 | Compress-36 | largest5 | 1621, 1330, 1253, 1149, 1126 | SevenZFile.matches | — | — |
| 168 | Compress-39 | largest5 | 1621, 1330, 1253, 1149, 1112 | ArchiveUtils.isEqual / ArchiveUtils.sanitize / ArchiveUtils.toAsciiString | — | — |
| 169 | Compress-45 | largest5 | 1686, 1334, 1259, 1258, 1136 | TarUtils.parseOctal | — | — |
| 170 | Gson-1 | largest5 | 1118, 570, 566, 553, 387 | TypeInfoFactory.getTypeInfoForField | — | — |
| 171 | Gson-14 | largest5 | 1617, 989, 906, 864, 659 | $Gson$Types.subtypeOf / $Gson$Types.supertypeOf | — | — |
| 172 | Gson-16 | largest5 | 1617, 989, 906, 864, 659 | $Gson$Types.canonicalize | — | — |
| 173 | Gson-18 | largest5 | 1617, 1024, 906, 864, 659 | $Gson$Types.getRawType | — | — |
| 174 | JacksonCore-1 | largest5 | 3157, 2006, 1913, 1853, 1482 | NumberInput.parseInt / NumberInput.inLongRange / NumberInput.parseLong | — | — |
| 175 | JacksonDatabind-5 | largest5 | 3174, 1778, 1622, 1585, 1478 | AnnotatedClass.constructWithoutSuperTypes | — | — |
| 176 | Jsoup-3 | largest5 | 844, 420, 383, 355, 348 | Tag.valueOf | — | — |
| 177 | Jsoup-25 | largest5 | 1119, 658, 615, 536, 454 | Tag.valueOf | Jsoup-3 | — |
| 178 | Jsoup-28 | largest5 | 1119, 661, 617, 536, 454 | Parser.parseBodyFragment | — | — |
| 179 | Jsoup-53 | largest5 | 1237, 1016, 706, 702, 694 | TokenQueue.unescape | — | — |
| 180 | Jsoup-58 | largest5 | 1290, 1114, 750, 706, 703 | Parser.parseBodyFragment | Jsoup-28 | — |
| 181 | Jsoup-60 | largest5 | 1290, 1114, 750, 706, 703 | TokenQueue.unescape | Jsoup-53 | — |
| 182 | Jsoup-74 | largest5 | 1435, 1249, 778, 734, 725 | StringUtil.resolve / StringUtil.padding / StringUtil.isBlank | — | — |
| 183 | Jsoup-87 | largest5 | 1497, 1192, 778, 733, 725 | Tag.valueOf | Jsoup-3 | — |
| 184 | JxPath-5 | largest5 | 3775, 1875, 863, 820, 757 | NodePointer.newNodePointer | — | — |
| 185 | Math-91 | largest5 | 1836, 1597, 1511, 1408, 1273 | Fraction.getReducedFraction | — | sibling-package analogue org.apache.commons.math3.fraction.Fraction::getReducedFraction was UNBUILDABLE in Math-1 (W27): every Fraction ends in the public Fraction(int,int) constructor, which itself does the sign move with the MIN_VALUE overflow check and the gcd reduction, so the single-owner rule and the fault rule cannot both be met (omitting the zero shortcut, the sign move or the reduction fails no test). Not excluded: rule (b) is by exact FQN and this FQN has no UNBUILDABLE record; counter-precedent: Math-36 (ACCEPTED, batch 4): org.apache.commons.math.fraction.BigFraction::getReducedFraction, whose body is identical to Math-1's UNBUILDABLE math3 BigFraction target and whose constructor also normalises (reduce plus sign); its builder found a valid fault with 3 recorded bypasses. Builder: check the single-owner and fault rules for this target first and stop early with UNBUILDABLE if they cannot both be met (likely reason: no single owner) |
| 186 | Math-92 | largest5 | 1832, 1621, 1499, 1407, 1244 | MathUtils.gcd / MathUtils.equals / MathUtils.scalb | — | this exact FQN was an allowed target of Math-79, which was UNBUILDABLE for a reason that is not a property of the target (fewer than five usable >=1500-line hosts in that revision: the pool's five included MathUtils, the target class, and the draw stopped at four (validate_MR-Math-79.log); a host-pool property, which C10f's largest-5 rule addresses; the targets themselves were not evaluated there); not excluded, but no build with it has succeeded yet |
| 187 | Math-93 | largest5 | 1832, 1621, 1499, 1407, 1244 | MathUtils.nextAfter / MathUtils.binomialCoefficient / MathUtils.subAndCheck | — | this exact FQN was an allowed target of Math-79, which was UNBUILDABLE for a reason that is not a property of the target (fewer than five usable >=1500-line hosts in that revision: the pool's five included MathUtils, the target class, and the draw stopped at four (validate_MR-Math-79.log); a host-pool property, which C10f's largest-5 rule addresses; the targets themselves were not evaluated there); not excluded, but no build with it has succeeded yet |
| 188 | Math-94 | largest5 | 1832, 1621, 1499, 1407, 1244 | MathUtils.binomialCoefficientLog / MathUtils.factorialLog / MathUtils.addAndCheck | — | this exact FQN was an allowed target of Math-79, which was UNBUILDABLE for a reason that is not a property of the target (fewer than five usable >=1500-line hosts in that revision: the pool's five included MathUtils, the target class, and the draw stopped at four (validate_MR-Math-79.log); a host-pool property, which C10f's largest-5 rule addresses; the targets themselves were not evaluated there); not excluded, but no build with it has succeeded yet |
| 189 | Math-99 | largest5 | 1840, 1621, 1501, 1407, 1264 | MathUtils.binomialCoefficientDouble / MathUtils.lcm / MathUtils.factorial | — | — |
| 190 | Math-104 | largest5 | 1319, 1069, 1036, 1019, 1016 | Gamma.regularizedGammaP / Gamma.regularizedGammaQ / Gamma.logGamma | — | — |

Many largest5 targets are short factories or wrappers; the pre-registration expects UNBUILDABLE outcomes of the batch-5 kinds and records
them. Several largest5 hosts are small, abstract or generated code; substitutions are recorded per instance.

**Key preflight.** Before any batch-6 builder starts, the coordinator asserts for all 62 keys that no design, spec, instance, audit,
history or variant path exists apart from the fixtures, and that none of the keys appears in the batch-1 to batch-5 task files.

## Cost guard

`mr_cost_guard.py --cap 500`, re-run before every block by `mr_run_blocks.sh`; blocks of at most 5 in batch-6 order; plans
`plans/MR_batch6_block<N>_gpt55.json`. Expected run cost about 62 × 5 × $0.43 ≈ $133 if every candidate were built;
with the batch-5 yield (20 of 37) about $72.

## Integrity

1. The batch-1/2, batch-3 and batch-4 manifests, as before; a batch-5 manifest (`b5_integrity_manifest.json`) recorded after the batch-5
   runs and before any batch-6 row.
2. `mr_integrity.py --verify-frozen batch6_frozen_hashes.json`, written before any batch-6 build: every `mr_*` and `mr2_*` script, the
   briefs, the checklist and the addendum, this document, `batch6_tasks.json`, `batch6_checkouts.log`, the pool v2 files, the governing
   records and completed-batch artefacts (1–5), the manifests, the driver logs, the other servers' ledgers, and `AMENDMENTS.md` through
   W45 as a pinned prefix.

## Outputs

Rows added to the four CSVs (batch `batch6`), regenerated by the pinned scripts; `main-run/batch6_tasks.json`, `batch6_checkouts.log`,
`batch6_build_audit_results.json`; `analysis/batch6_dispositions.json` (with `facade_reuse_of`, `host_mode`, `host_lines`),
`batch6_trace_checks.json`, `batch6_trace_robustness.json`, `batch6_prediction.json`, `batch6_frozen_hashes.json`; the C10f report files
of `mr2_report.py`; `SUPERVISOR_PROGRESS_UPDATE.md` as update 6.
