# Failed mechanisms: screened, no accuracy reduction for GPT-5.6

Each instance in the S2 and S1 tables below was screened under the frozen GPT-5.6 protocol with 3 valid runs per instance
(MECHANISM_SCREENING_REPORT.md) and scored NULL: every run ranked the gold first. The M3 rows there are the NULL instances
of a family that was PROMISING overall (15/21). The held-out section uses 5 runs per instance (4 for HO-HB-COMPRESS-01) and
has one miss, and the last section summarises earlier, non-screening data. The agent ran a test in every screening run, and
it read the gold method in full in all of them except one run of RH-ADV-REGISTRY-01, where the gold was read in full in 2 of
3 runs. In held-out, HO-HA-COMPRESS-01 run-003 (a no-answer timeout) also did not read the gold. Design summaries come from each instance's builder report or original
validation. They describe the construction, not the model's behaviour.

## New prototypes built for this study (S2): 12 families, 36/36 gold at rank 1

| Family | Instance (project) | What the instance tests |
|---|---|---|
| M1 + M6 local oddness | NEW-R1-M1 (Lang) | A correct competitor on the trigger path uses a valid but hacky-looking sentinel-digit trick (`DurationFormatUtils.format`). The gold (`formatPeriod`) has a quiet fault. |
| M2 pure omission | NEW-R2-M2 (Compress) | The gold (`CpioArchiveInputStream.readOldBinaryEntry`) has lost its final padding step. Its remaining body has exactly the shape of the correct sibling `readOldAsciiEntry`. |
| M3 definer/adapter | NEW-R3-M3 (Math) | A definer with an unusual-looking deviance convention, pinned by its javadoc and a passing test. The gold is the adapter that consumes it (`SaddlePointExpansion.logBinomialProbability`). |
| M7 inverse pair | NEW-R5-M7 (Compress) | DOS-time encode/decode. The correct encoder has a legitimately asymmetric `>> 1`. The decoder (gold) omits the doubling. The round-trip failure fits either side. |
| M8 cross-caller convention | NEW-R6-M8 (Lang) | A callee whose javadoc reads like a boolean but returns a match length. The gold caller (`StrSubstitutor.substitute`) misreads it; two other callers (`StrBuilder.replaceImpl`, `StrTokenizer.readWithQuotes`) read it as a length under passing tests. |
| M9 test-evidence ambiguity | NEW-R13-M9 (Lang) | A bare `assertTrue(a && b)` failure, with no message or values, compatible with several suspects. |
| M10 entry-point blame | NEW-R7-M10 (Math) | The trigger calls only `NaturalRanking.rank`, which has visible validation and branching. The fault is in the private guard `containsNaNs`: two calls below on the REMOVED path (`rank` → `removeNaNs` → `containsNaNs`) and one call below on the FAILED path; the trigger exercises both. |
| M12 same-file competition | NEW-R8-M12 (Lang) | The gold `StrTokenizer.readNextToken` and three correct competitors, all in one 1,114-line file and all executed by the trigger. |
| M13 cross-file competition | NEW-R9-M13 (Compress) | The test calls the long `writeEntryHeader` directly and reaches the long `parseTarHeader` through the `TarArchiveEntry(byte[])` constructor. The gold (`TarUtils.getLongOctalBytes`) is one call away. |
| M14 state propagation | NEW-R10-M14 (Compress) | The gold (`ZipArchiveOutputStream.write`) updates the CRC accumulator over the wrong range. The failure surfaces later, in the more complex `closeEntry`. |
| M15 fallback path | NEW-R11-M15 (Math) | Only the overflow fallback of `BigFraction.doubleValue` is faulty. The prominent normal branch is correct. |
| M17 type semantics | NEW-R12-M17 (JacksonCore) | A column field that can hold a 0-based index or a 1-based number. The gold (`ReaderBasedJsonParser.nextToken`) stores the wrong one. |

**Invalid:** M4 (multiple plausible owners), NEW-R4-M4 (Math). The harness validator rejects its gold because the class name
ends in `Test`, so the instance is uninformative (AMENDMENTS X1). M4 therefore has **no valid screening result**.

## Re-hosted instances (S1) that scored NULL

| Family | Instance | Note |
|---|---|---|
| M11 lexical/semantic match | RH-ADV-LEX-01 (Lang) | |
| M16 overload/dispatch ambiguity | RH-ADV-OVERLOAD-01, RH-ADV-REGISTRY-01 (Lang) | |
| M7 symmetry / round trip | RH-ADV-OWNER-01 (Lang) | |
| M20 evidence competition | RH-ADV-COMPOSITE-01 (Chart) | |
| M3 adapter, Level B conventions (offset units, case folding, scale units) | RH-LB-LANG-03, RH-LB-LANG-04, RH-LB-MATH-05 ADAPTER | 3 of the 7 M3 instances. NEW-R3-M3 (S2 table) is also NULL; the other three (LB-COMPRESS-07-ADAPTER, LB-CHART-01-ADAPTER, ADV-DEFINER-01) are in PROMISING_MECHANISMS.md, and the M3 family is PROMISING overall (15/21) |
| controls: M3 with explicit contract | RH-OCFLB-CHART-01-ADAPTER, RH-CF-V3 (Chart) | explicit-contract controls, not single-factor twins. OCFLB-CHART-01-ADAPTER states contracts at the definer and the gold but also differs from LB-CHART-01-ADAPTER in several other features; CF-V3 differs from ADV-DEFINER-01 only in an explicit javadoc on the definer `drift` (the gold is unchanged) |
| controls | RH-LB-CHART-01-DEFINER (M3 definer arm), RH-CF-V5 (M1, visible operator at the gold) | |

## Held-out NOT_SUPPORTED: three failure-mode recipes from the strongest screening families (Phase 5)

By screening label the strongest families were M19, M3 and M5 (HELDOUT_CONFIRMATION_PLAN.md). Each recipe carries a failure
mode seen in their S1 misses, in a validity-repaired form; the recipes do not replicate the families. HA's M10 label names
the entry-point failure mode, not a strong screening family (NEW-R7-M10 scored 3/3), and no held-out instance carries an M5
tag.

| Recipe | Carries | Held-out | Instances |
|---|---|---|---|
| HA entry-point ranking | M10 failure mode from S1 (COMPRESS-07, MASK-01, CF-V1) | 14/15 (0.933); the only miss is a no-answer timeout, with no misranking | Compress 4/5, Math 5/5, JacksonCore 5/5 |
| HB sink blame | M19 + M6 + M2 (DEPTH-01, MASK-01) | 14/14 (1.000) | Compress 4/4, Lang 5/5, Math 5/5 |
| HC convention attribution with a second production caller | M3 (CHART-01-ADAPTER, DEFINER-01) | 15/15 (1.000) | Lang 5/5, Math 5/5, JacksonCore 5/5 |

All nine instances were built by builders who had built no screening instance and saw no GPT-5.6 output, and an auditor who
had not built the instance confirmed each final gold. Two were revised before any agent step: HO-HB-LANG-01 after its first
audit rejected it for leakage (revised by its original builder rather than rebuilt fresh, as the plan's audit rule requires;
AMENDMENTS X6), and HO-HC-MATH-01 after a harness setup failure (AMENDMENTS X10). None meets any
STABLE criterion on accuracy (HELDOUT_CONFIRMATION_RESULTS.md).

Phase 4 (exploratory, n = 3 per arm, AMENDMENTS X4) revised only the two 0/3 instances, and both became 3/3 after their
flagged features were changed. P4-COMPRESS07-r1 removed the correct sibling; P4-DEPTH-01-r1 changed two javadocs at once (the
decoy's contradiction and the gold's contract), so its two repairs are not separable. This is consistent with, but does not
establish, those two effects depending on validity problems. The other reductions (MASK-01 1/3, CHART-01-ADAPTER 1/3,
DEFINER-01 2/3, CF-V1 2/3) were not revised, so Phase 4 does not explain the held-out result as a whole
(PROMISING_MECHANISMS.md).

## Also not reducing accuracy in earlier frozen GPT-5.6 data (MECHANISM_MINING.md)

- **M0, structural displacement** (depth, hops): tag-level Acc@1 0.97 (168 runs, 67 instances); the displacement families
  score 0.90 to 1.00 on valid behavioural runs. The earlier displacement studies, as summarised in
  mining/annotations/diagnostic-noncanonical-v3.json, report that displacement delays first exposure of the gold while rank 1
  usually holds. The answered misses in these families include CHART-PIE-TREATMENT-03 (0/5), which MECHANISM_MINING.md
  attributes to a locally odd definer rather than to displacement.
- **Cue-trust pilot** (misleading identifier names and comments in the source code, gold-excusing or decoy-blaming, with
  behaviour unchanged; frozen F0 prompt): 27/27 gold at rank 1. Every cue was refuted by co-visible code or by the failing
  test source in the prompt, so the pilot's own null analysis judges it undecidable whether identifier cues can move GPT-5.6
  (PILOT_NULL_ANALYSIS.md in cue-trust-v3).

## Why these failed (cross-cutting observations)

1. **GPT-5.6 inspects and tests under this protocol** (effort medium, failing-test source in the prompt, runnable tests, 50
   calls and 300 s). Every screening run ran a test, and the gold was read in full in 89 of the 90 valid runs. In the single
   exploratory prototypes of mechanisms meant to draw attention away from the gold (M10, M12, M13, M14, M15), the gold was
   read and ranked first in every run (3/3 each; n = 3 cannot rule out a moderate reduction), and M0 was near ceiling in
   frozen data (0.97).
2. **A gold that violates something visible locally is found.** That can be an omitted step next to a correct sibling, a wrong
   range, or a misread return value. The S2 recipes for M2, M3, M7, M8 and M17 deliberately provide decisive evidence of this kind (a sibling, an inverse, a
   second caller or a passing test) so that the task stays solvable. The correct runs were not systematically coded. In the
   evidence chains, the M2 runs cite the writer (and, in 2 of 3, the new-format reader `readNewEntry`) and the M7 runs cite
   the encoder, but the M8 runs resolved the fault from the callee's own return contract without displaying the second
   callers' bodies. M5 (distant decisive evidence) has no S2 recipe and was PROMISING in screening (3/6;
   PROMISING_MECHANISMS.md). In the held-out recipes a locally visible violation was required by construction (plan rule 4:
   the gold's javadoc states a postcondition its code violates), so the held-out null tests only that validity-repaired form.
3. **Odd-looking correct code with nearby pinning evidence did not mislead in the two S2 prototypes built to test it**
   (NEW-R1-M1 and NEW-R3-M3, 3/3 each, exploratory). This is not a general protection. In RH-ADV-DEFINER-01 the definer
   `drift`, which reads backwards but is pinned by a passing unit test, was blamed in 1 of 3 runs, and in frozen GPT-5.6 data a
   quiet gold beside a locally odd correct competitor is the strongest predictor of a miss (Acc@1 0.38, MECHANISM_MINING.md).
   Accuracy fell on 6 S1 instances (12 wrong runs). The blind labellers judged only the 3 DEPTH-01 answers defensible and the
   other 9 not defensible (COMPRESS-07, CHART-01-ADAPTER, DEFINER-01, MASK-01, CF-V1). The coordinator review also judged the
   DEPTH-01 answers defensible, agreed that MASK-01 run 1 and CF-V1 run 2 were not, judged the two CHART-01-ADAPTER answers
   defensible, and judged the COMPRESS-07, DEFINER-01 and MASK-01 run 3 answers partly defensible (PROMISING_MECHANISMS.md).
