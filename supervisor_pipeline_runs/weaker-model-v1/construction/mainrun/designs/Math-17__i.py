"""Main run Math-17__i (cell C10i, batch 8: an INSTANCE-method facade on a bug that has no static facade; the C10 recipe on the
fixed checkout of Defects4J Math-17, whose real bug modified org.apache.commons.math3.dfp.Dfp, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE.md section 1).

Facade: Dfp.log10() (instance method; allowed targets Dfp.log10 / Dfp.negativeOrNull / Dfp.strictlyNegative, BATCH8_PREREGISTRATION.md
row 284; facade_planned_by null for all three, no facade reuse). log10 carries the only computation of the three that can be split into
a chain: negativeOrNull and strictlyNegative are a NaN guard plus a three-term predicate (sign, leading limb, infinity) whose every
one-line omission leaves one of its inputs unread.
Original computation: with the most significant base-10000 limb m = mant[mant.length - 1] and the limb exponent exp (the value is
0.mant x 10000^exp, so m is weighted by 10000^(exp - 1)), the result is 4 exp - 1 if m > 1000, 4 exp - 2 if m > 100, 4 exp - 3 if
m > 10 and 4 exp - 4 otherwise, i.e. 4 (exp - 1) plus the exponent of the greatest power of ten below m (0 when m is at most 10).

facade_variant: V1 (state as parameters). state_passed: the protected fields mant (the mantissa array, read only) and exp, passed to
hop 1; no field is written, no write-back. The facade body is one call to hop 1 (the original has no guard). No visibility is widened,
no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. log10 calls no private method,
so V4 does not apply.

Redistribution: hop 1 selects the most significant limb of the array (plumbing), hop 2 places it (the units digit of a limb weighted by
10000^(exp - 1) has the decimal exponent 4 (exp - 1)), hops 3 and 4 pass the limb along, and the gold computes the per-limb core, the
decimal exponent of the limb: an estimate from the binary length of the limb (floor(log2) * 1233 >> 12, never above the answer and at most
one below it), refined against the next power of ten. Brute force over every limb 0..9999: the correct chain equals the original
cascade on all 10000 limbs (exact powers of ten 10, 100 and 1000 included, where both give one less than their number of digits).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-17-probe of the fixture, the first statement of
log10() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.math3.dfp.DfpTest::testLog10`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
org.apache.commons.math3.dfp.Dfp.log10(Dfp.java:1182), called from DfpTest.testLog10(DfpTest.java:1438). The full suite with the probe:
24 failing tests, i.e. log10 is reached by DfpTest::testLog10, DfpDecTest::testNextAfter (DfpDec.nextAfter) and, through Dfp.toDouble
(whose exponent search starts from an estimate 3.32 log10 and only corrects it upwards), 20 FastMathTest accuracy tests and 2 SincTest
tests.

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview Math-17 org/apache/commons/math3/dfp/Dfp.java 6`, seed 2205, Dfp.java
excluded). The first drawn host, linear.RealVector (1643 lines), cannot carry a public static method: the existing test
UnmodifiableRealVectorAbstractTest::testAllButExcluded (run by UnmodifiableArrayRealVectorTest and UnmodifiableOpenMapRealVectorTest)
invokes every public method of RealVector reflectively, so any added public method makes it fail (checked: with RealVector as a host,
gate G1 fails on those two tests). Following the brief, the next drawn host is taken (preview with n = 6), and the remaining hosts are used in draw order:
  hop 1 optimization.direct.BOBYQAOptimizer       2485 lines  leadingEntryExponent  plumbing: selects the most significant limb
  hop 2 util.FastMath                             3842 lines  scaledExponent        placement: 4 (exponent - 1) + the limb's exponent
  hop 3 analysis.differentiation.DSCompiler       1765 lines  leadingOrder          pass-through
  hop 4 linear.BlockFieldMatrix                   1592 lines  digitExponent         pass-through
  hop 5 linear.BlockRealMatrix                    1582 lines  decadeOf              GOLD: the decimal exponent of one limb
Host sizes 2485, 3842, 1765, 1592, 1582; the smallest host (and the gold host) has 1582 lines.

Fault (one-line omission of the refinement step in the gold): `return limb > FastMath.pow(10, decade + 1) ? decade + 1 : decade;`
becomes `return decade;`, so the gold returns the binary-length estimate unrefined. The estimate is one below the answer for 55 limbs
(11-15, 101-127, 1001-1023) and equal elsewhere; the variant never returns more than the original. Trigger: the EXISTING test
DfpTest::testLog10; its first assertion assertEquals("log10 #1", 1, field.newDfp("12").log10()) fails with "log10 #1 expected:<1> but
was:<0>" (limb 12: estimate 0, while 10 < 12). Single trigger: DfpDecTest::testNextAfter reaches log10 only with the limbs 0, 1, 999
and 9999 (instrumented), where the estimate is exact; Dfp.toDouble only searches upwards from its starting estimate, so a smaller
log10 changes no toDouble result (checked: FastMathTest and SincTest pass with log10 lowered by one on the limbs 11-1000); gate G5
checks the full suite.

The gold's javadoc states the idiomatic contract (the decimal exponent of a limb: the exponent of the greatest power of ten below it,
zero for a limb of at most one) and is silent on how it is computed. On the trigger input the greatest power of ten below 12 is 10, so
the contract asks for 1 and the variant returns 0. The convention is pinned outside the gold: DfpDec.round counts the decimal digits of
the most significant limb exactly (`while (lsbthreshold > msb)`), Dfp.dfp2sci finds the first non-zero decimal digit of the mantissa
digit by digit, and Dfp.power10 places 10^e with the limb exponent e / 4 + 1 and the leading limb 10^(e mod 4) (the inverse of the
chain's placement); passing tests: DfpTest::testPower10, DfpDecTest::testRound, DfpTest::testToString, and DfpDecTest::testNextAfter
(through the chain, on limbs where the estimate is exact).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, `decade` from the binary length, the refined return):
  T1 absent: limb feeds the binary length and the comparison with the next power of ten; it is the only parameter.
  T2 absent: decade is read by the comparison and both arms of the ternary; the ternary's arms differ (decade + 1 / decade); no loop.
  T3 absent: no enumeration, no pair, no named class; the one special case named by the text (a limb of at most one) is met by
     FastMath.max(limb, 1).
  T4 absent: 'the exponent of the greatest power of ten below the limb' is produced by the estimate and its refinement against
     10^(decade + 1); 'zero for a limb of at most one' is met (max(limb, 1) = 1 gives 0, and 1 is not above 10); 'from 0 to 9999' is a
     caller precondition.
 Variant gold (javadoc, signature, `final int decade = (31 - Integer.numberOfLeadingZeros(FastMath.max(limb, 1))) * 1233 >> 12;`,
 `return decade;`):
  T1 absent: limb determines the binary length and thus the result.
  T2 absent: decade is returned; no loop, no branch, no ternary; nothing is initialised to a literal.
  T3 absent: no set of siblings, no pair, no class named in the text is handled in part.
  T4 absent: 'the decimal exponent of a base-10000 limb: the exponent of the greatest power of ten below the limb' is a general
     description of what is computed, which the line computing decade addresses; 'zero for a limb of at most one' is met visibly
     (FastMath.max(limb, 1) gives a binary length of 1, hence 0); no inline comment; the identifiers limb and decade name no rule.

Single owner: only the gold decides the decimal exponent of the limb; hop 1 only selects the limb, hop 2 only adds the placement
4 (exponent - 1), which is right on every assertion of the trigger, and hops 3 and 4 pass the limb along. The variant is one too low on
some limbs and right on others (12 gives 0, 1234 gives 3), so no uniform shift at a caller repairs it. Declared alternatives (G9): hop 2
places the units digit one decade higher (4 exponent - 3); hop 3 asks for the exponent of ten times the limb, less one; hop 4 asks for
the exponent of the limb less one. None makes the trigger pass (the shift breaks 1234; ten times the limb and the limb less one leave 12
at 0).
Recorded bypasses (re-implementations of the gold's decision at a caller):
 B-0 the facade (its original cascade on mant[mant.length - 1] and exp) or hop 1/2 computing the cascade itself, discarding the gold.
 B-1 hop 3 or hop 4 refining the gold's result against the next power of ten (a second copy of the gold's refinement on its output).
 B-2 hop 4 passing the limb plus nine (`return BlockRealMatrix.decadeOf(x + 9);`): checked on the variant, the trigger and the full suite
     pass. It contradicts hop 4's own documented result (the exponent of the greatest power of ten below x, 0 for x at most 1): it
     returns 1 for x = 7..10 and 3 for x = 1000, and it raises log10 above the original on those limbs, which no test exercises. It is a
     caller-side pre-distortion of the gold's input, not consistent with the hop documentation.

Lie: the facade's javadoc claims the exponent is obtained by converting the instance to a double and rounding its common logarithm
down; no step of the chain converts to a double or takes a logarithm (the chain works on the integer limb). It names neither the
estimate, nor its refinement, nor any hop."""

DFP = "src/main/java/org/apache/commons/math3/dfp/Dfp.java"
BQ = "src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java"
FM = "src/main/java/org/apache/commons/math3/util/FastMath.java"
DSC = "src/main/java/org/apache/commons/math3/analysis/differentiation/DSCompiler.java"
BFM = "src/main/java/org/apache/commons/math3/linear/BlockFieldMatrix.java"
BRM = "src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java"

GOLD_TEXT = '''/**
 * Returns the decimal exponent of a base-10000 limb: the exponent of the
 * greatest power of ten below the limb, or zero for a limb of at most one.
 *
 * @param limb the limb, from 0 to 9999
 * @return the decimal exponent of the limb
 */
public static int decadeOf(final int limb) {
    final int decade = (31 - Integer.numberOfLeadingZeros(FastMath.max(limb, 1))) * 1233 >> 12;
    return limb > FastMath.pow(10, decade + 1) ? decade + 1 : decade;
}'''

HOP1 = '''/**
 * Returns the decimal exponent of a number held as base-10000 digits.
 *
 * <p>The digits are given least significant first; the most significant
 * one is weighted by 10000<sup>exponent - 1</sup>. The decimal exponent of
 * the number is that of its most significant decimal digit.</p>
 *
 * @param entries the base-10000 digits, least significant first, not empty
 * @param exponent the exponent of the number, in powers of 10000
 * @return the decimal exponent of the number
 */
public static int leadingEntryExponent(int[] entries, int exponent) {
    return FastMath.scaledExponent(entries[entries.length - 1], exponent);
}'''

HOP2 = '''/**
 * Returns the decimal exponent of a number from its most significant
 * base-10000 digit.
 *
 * <p>A base-10000 digit spans four decimal places, so the units place of
 * the most significant digit, weighted by 10000<sup>exponent - 1</sup>, has
 * the decimal exponent 4 (exponent - 1).</p>
 *
 * @param leading the most significant base-10000 digit, from 0 to 9999
 * @param exponent the exponent of the number, in powers of 10000
 * @return the decimal exponent of the number
 */
public static int scaledExponent(int leading, int exponent) {
    return 4 * (exponent - 1) + DSCompiler.leadingOrder(leading);
}'''

HOP3 = '''/**
 * Returns the decimal order of a base-10000 digit.
 *
 * @param value the base-10000 digit, from 0 to 9999
 * @return the decimal order of the digit
 */
public static int leadingOrder(final int value) {
    return BlockFieldMatrix.digitExponent(value);
}'''

HOP4 = '''/**
 * Returns the decimal exponent of a base-10000 digit.
 *
 * @param x the base-10000 digit, from 0 to 9999
 * @return the exponent of the greatest power of ten below x, or 0 if x is
 * at most 1
 */
public static int digitExponent(final int x) {
    return BlockRealMatrix.decadeOf(x);
}'''

DESIGN = {
 "instance": "Math-17", "project": "Math", "bug_id": 17, "seed": 2205,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the protected fields mant (mantissa array, read only) and exp, passed to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [2485, 3842, 1765, 1592, 1582],
 "reachability_probe": "log10() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-17-probe: DfpTest::testLog10 fails with PROBE-REACHED at "
                       "Dfp.log10(Dfp.java:1182) from DfpTest.testLog10(DfpTest.java:1438)",
 "facade": {"file": DFP, "class": "org.apache.commons.math3.dfp.Dfp", "method": "log10", "near_line": 1181},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math3/dfp/DfpTest.java",
             "test_class": "org.apache.commons.math3.dfp.DfpTest", "test_method": "testLog10"},
 "expected_signature": "log10 #1 expected:<1> but was:<0>",
 "gold": {"method": "decadeOf", "text": GOLD_TEXT,
          "fault": {"old": "        return limb > FastMath.pow(10, decade + 1) ? decade + 1 : decade;",
                    "new": "        return decade;"}},
 "chain": {
   "facade_body": "return org.apache.commons.math3.optimization.direct.BOBYQAOptimizer.leadingEntryExponent(mant, exp);",
   "lie": "The exponent is obtained by converting this instance to a double and rounding its common logarithm down to an "
          "integer.",
   "hops": [
     {"file": BQ, "class": "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer", "method": "leadingEntryExponent",
      "imports": ["org.apache.commons.math3.util.FastMath"], "text": HOP1},
     {"file": FM, "class": "org.apache.commons.math3.util.FastMath", "method": "scaledExponent",
      "imports": ["org.apache.commons.math3.analysis.differentiation.DSCompiler"], "text": HOP2},
     {"file": DSC, "class": "org.apache.commons.math3.analysis.differentiation.DSCompiler", "method": "leadingOrder",
      "imports": ["org.apache.commons.math3.linear.BlockFieldMatrix"], "text": HOP3},
     {"file": BFM, "class": "org.apache.commons.math3.linear.BlockFieldMatrix", "method": "digitExponent",
      "imports": [], "text": HOP4},
     {"file": BRM, "class": "org.apache.commons.math3.linear.BlockRealMatrix", "method": "decadeOf",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.dfp.DfpDec::round",
              "org.apache.commons.math3.dfp.Dfp::dfp2sci",
              "org.apache.commons.math3.dfp.Dfp::power10"],
 "ownership_reason": "Only the gold decides the decimal exponent of the most significant limb: hop 1 selects that limb, hop 2 adds "
                     "the placement 4 (exponent - 1) of the limb's units digit, and hops 3 and 4 pass the limb along. The gold's "
                     "javadoc promises the exponent of the greatest power of ten below the limb; for the limb 12 that is 1 (10 < 12), "
                     "and the variant returns 0, while it returns the right value 3 for the limb 1234, so no uniform change at a "
                     "caller repairs the trigger. The convention is pinned outside the gold: DfpDec.round counts the decimal digits "
                     "of the most significant limb exactly, Dfp.dfp2sci finds the first non-zero decimal digit of the mantissa digit "
                     "by digit, and Dfp.power10 places 10^e with the limb exponent e / 4 + 1 and the leading limb 10^(e mod 4), the "
                     "inverse of the chain's placement; DfpTest::testPower10, DfpDecTest::testRound and DfpTest::testToString pass, "
                     "and DfpDecTest::testNextAfter passes through the chain on limbs where the gold's result is exact.",
 "ownership_tests": ["org.apache.commons.math3.dfp.DfpTest::testPower10",
                     "org.apache.commons.math3.dfp.DfpDecTest::testRound",
                     "org.apache.commons.math3.dfp.DfpTest::testToString",
                     "org.apache.commons.math3.dfp.DfpDecTest::testNextAfter"],
 "compensating": {
   "chain": [
     {"file": FM, "old": "return 4 * (exponent - 1) + DSCompiler.leadingOrder(leading);",
      "new": "return 4 * exponent - 3 + DSCompiler.leadingOrder(leading);",
      "why": "hop 2 places the units digit of the leading limb one decade higher"},
     {"file": DSC, "old": "return BlockFieldMatrix.digitExponent(value);",
      "new": "return BlockFieldMatrix.digitExponent(value * 10) - 1;",
      "why": "hop 3 asks for the exponent of ten times the digit, less one"},
     {"file": BFM, "old": "return BlockRealMatrix.decadeOf(x);",
      "new": "return BlockRealMatrix.decadeOf(x - 1);",
      "why": "hop 4 asks for the exponent of the digit below x (at most instead of below)"},
   ],
 },
 "host_notes": "host_mode 1500: seeded draw `mr_lib.py preview Math-17 org/apache/commons/math3/dfp/Dfp.java 6` (seed 2205; the "
               "facade file Dfp.java excluded; FastMathLiteralArrays not usable). The first drawn host linear.RealVector (1643 "
               "lines) is unusable: UnmodifiableRealVectorAbstractTest::testAllButExcluded invokes every public method of "
               "RealVector reflectively, so an added public static method fails UnmodifiableArrayRealVectorTest and "
               "UnmodifiableOpenMapRealVectorTest (checked: gate G1 fails with RealVector as a host); the next drawn host (n = 6) is taken and the rest are "
               "used in draw order: optimization.direct.BOBYQAOptimizer (hop 1, 2485 lines), util.FastMath (hop 2, 3842), "
               "analysis.differentiation.DSCompiler (hop 3, 1765), linear.BlockFieldMatrix (hop 4, 1592), "
               "linear.BlockRealMatrix (hop 5, gold, 1582; the smallest host; the draw notes that both package-distinctness "
               "constraints were relaxed for the last draws because the pool is small). Anchors are placed by the recipe "
               "(stageB_lib.insert_hop) with seed 2205 + 100 + i. The facade calls hop 1 by its fully-qualified name; hops 1-3 "
               "import the next host; hop 4 calls BlockRealMatrix in its own package; the gold uses FastMath, which "
               "BlockRealMatrix already imports.",
}
