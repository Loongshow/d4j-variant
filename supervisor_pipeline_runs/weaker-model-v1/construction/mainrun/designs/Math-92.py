"""Main run Math-92 (cell C10f, batch 6; C10 recipe with fallback hosts on the fixed checkout of Defects4J Math-92; the real bug
modified MathUtils, the target class).

Facade: MathUtils.scalb(double, int) (allowed target, BATCH6_PREREGISTRATION.md row Math-92: MathUtils.gcd / MathUtils.equals /
MathUtils.scalb). No facade reuse.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2), run on scratch copies of construction/fresh-mr/Math-92 with
`if (true) throw new IllegalStateException("PROBE-REACHED");` as the first statement of the facade (the `if (true)` keeps the rest
of the body compilable):
  scalb : defects4j test -t MathUtilsTest::testScalb fails with java.lang.IllegalStateException: PROBE-REACHED at
          MathUtils.scalb(MathUtils.java:820); full suite with the probe: exactly 1 failing test (MathUtilsTest::testScalb).
  gcd   : MathUtilsTest::testGcd fails with PROBE-REACHED; full suite: 48 failing tests (FractionTest, FractionFormatTest,
          the Adams ODE integrator tests, MathUtilsTest testGcd/testLcm/testBinomialCoefficientLarge ...).
  equals: MathUtilsTest::testEquals fails with PROBE-REACHED; full suite: 62 failing tests (the descriptive statistics
          equals/serialization/copy tests, testArrayEquals, ...).
All three are reachable. gcd and equals were set aside: gcd is called on every Fraction operation and equals(double, double) by
every statistic's equals and by equals(double[], double[]), so every omission in their decisions (the NaN clause of equals; the
zero case, the sign normalisation, the power-of-two extraction and the odd-part loop of gcd, all exercised with ordinary inputs
by FractionTest and the statistics tests) is caught by many tests, and no one-line omission leaves exactly one newly failing
test (gate G5). scalb has no production caller; its only caller is MathUtilsTest::testScalb.

Original computation of the facade: if d is 0, NaN or infinite, return d unchanged; otherwise take the raw bits of d, keep the
sign and mantissa bits (mask 0x800fffffffffffff), add scaleFactor << 52 to the exponent bits (mask 0x7ff0000000000000) and
rebuild the double from the bits.

Hosts (host_mode = largest5: the revision has only 2 public classes of >= 1500 lines other than MathUtils, so the hosts are the
five largest public non-interface non-enum classes, task record hosts_hop_order; no substitution):
  hop 1 linear.EigenDecompositionImpl  1832 lines   anchor after getSolver            (line idx 367, anchor seed 3377)
  hop 2 linear.DenseRealMatrix         1621 lines   anchor after walkInOptimizedOrder (line idx 1601, anchor seed 3378)
  hop 3 linear.BigMatrixImpl           1499 lines   anchor after equals               (line idx 1327, anchor seed 3379)
  hop 4 linear.RealVectorImpl          1407 lines   anchor after mapExpm1             (line idx 411, anchor seed 3380)
  hop 5 linear.AbstractRealMatrix      1244 lines   anchor after copySubMatrix        (line idx 359, anchor seed 3381)  GOLD
  smallest host: AbstractRealMatrix, 1244 lines. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with
  the instance seed 3277 + 100 + i, all in the outer class at brace depth 1.

Chain (the facade has no argument guard; its body is one delegating call):
  hop 1 EigenDecompositionImpl.scaledByPowerOfTwo   pass-through
  hop 2 DenseRealMatrix.binaryScaledEntry           pass-through
  hop 3 BigMatrixImpl.exponentScaledValue           pass-through
  hop 4 RealVectorImpl.scaledComponent              placement: a zero scale factor leaves d unchanged; any other scale
                                                    factor is converted into the increment of the exponent bits,
                                                    ((long) scaleFactor) << 52
  hop 5 AbstractRealMatrix.multiplyByPowerOfTwo     GOLD: the per-value core: the special-value decision (0, NaN, infinite
                                                    returned unchanged), the split of d into its raw bits and the addition of
                                                    the increment to the exponent bits
The correct configuration computes exactly the original result for every input (the same special-value test, the same masks, the
same increment scaleFactor << 52 widened to long before the move, the same rebuild; the zero-scale shortcut of hop 4 returns d,
which is what the original returns for a zero scale factor: the special values unchanged, every other value rebuilt from its own
bits).

Fault (one-line omission of a special-case decision in the gold): the `if ((d == 0) || Double.isNaN(d) || Double.isInfinite(d))
{ return d; }` block is dropped, so every value goes through the bit arithmetic. The gold then reads as the textbook bit-level
scaling routine (raw bits, exponent field, sign and mantissa, rebuilt bits). Trigger: the EXISTING test MathUtilsTest::testScalb.
Its first four assertions still hold (scalb(0.0, 5) becomes 2^-1018, within the test's 1e-15 of 0.0; 1.0 * 2^5, 1.0 * 2^-5 and
PI * 2^0 are exact), and line 645 assertTrue(Double.isInfinite(MathUtils.scalb(Double.POSITIVE_INFINITY, 1))) fails with
junit.framework.AssertionFailedError: the exponent bits of +infinity (0x7ff) plus one carry into the sign bit and the result is
-0.0 (the -infinity and NaN assertions would fail the same way: -0.0 and a negative subnormal). No other test reaches the chain.
The gold's javadoc states the idiomatic contract (d multiplied by the power of two) and is silent on special values;
+infinity * 2 = +infinity, so the variant violates that contract on the trigger input.

External pins (convention outside the gold): the facade's own javadoc ('If d is 0 or NaN or Infinite, it is returned
unchanged.'); MathUtils.nextAfter takes the same step at the same place, its 'handling of some important special cases' (NaN or
infinite d returned unchanged) directly before it splits the double in raw components, pinned by
MathUtilsTest::testNextAfterSpecialCases; MathUtils.round(double, int, int) returns infinite values unchanged and NaN as NaN,
pinned by MathUtilsTest::testRoundDouble (and the float overload by testRoundFloat).

Single owner: only the gold looks at the value of d; it is the only method that splits d into raw bits, and the special-value
decision belongs with that split (nextAfter). Hops 1-4 never inspect d: hops 1-3 pass their arguments on, hop 4 tests only the
scale factor and converts it. Once the exponent bits of an infinite or NaN value have been incremented, the carry has overwritten the sign
bit and the exponent field is zero: the returned -0.0 (or a negative subnormal) cannot be told apart from the scaling of an
ordinary value, so no caller can recover infinity or NaN from the gold's result. Declared alternatives (G9): hop 4 forms the
increment by multiplication (scaleFactor * 0x0010000000000000L), hop 1 bounds the scale factor to the span of the exponent field
(+-2098), hop 3 scales the magnitude of d and restores its sign with Math.copySign; each still returns a finite value for
(+infinity, 1), so the trigger still fails.
No caller can pre-filter the input so that the gold's own arithmetic gives the special values back: for an infinite or NaN d the
variant gold returns d only for a zero increment, a zero scale factor never reaches the gold (hop 4 returns d itself), and hop 4 is
documented to pass the increment matching any non-zero scale factor.
Recorded one-line edits above the gold that pass the trigger and the full suite (each checked on the variant in a scratch copy,
defects4j test: 0 failing tests each):
 B-0 bypass: the facade returns Math.scalb(d, scaleFactor) (JDK 6), or a hop returns d * Math.pow(2, scaleFactor) (checked at
     hop 3), discarding the rest of the chain including the gold.
 B-1 bypass: hop 4 widens its shortcut to the special values
     (`if (scaleFactor == 0 || d == 0 || Double.isNaN(d) || Double.isInfinite(d)) {`) and returns d itself for them: on the
     trigger input the gold's output is never used; a second implementation of the gold's decision.
 B-1' bypass: the facade (or hop 1, 2 or 3) passes a zero scale factor for 0, NaN or infinite d
     (`return org.apache.commons.math.linear.EigenDecompositionImpl.scaledByPowerOfTwo(d, (d == 0 || Double.isNaN(d) || Double.isInfinite(d)) ? 0 : scaleFactor);`),
     so hop 4's zero-scale shortcut returns d and the gold is never called for those values (its output dead); again a second
     implementation of the gold's decision above it.
 B-2 not doc-consistent: hop 4 passes a zero increment for NaN or infinite d with a non-zero scale factor
     (`return AbstractRealMatrix.multiplyByPowerOfTwo(d, Double.isNaN(d) || Double.isInfinite(d) ? 0L : ((long) scaleFactor) << 52);`):
     it passes the suite but contradicts hop 4's documented conversion (any non-zero scale factor is converted into the matching
     increment scaleFactor * 2^52), and it too re-implements the gold's decision; the gold itself still returns -0.0 for
     (+infinity, 2^52), an input every javadoc on the path admits.

Lie: the facade's javadoc claims the factor 2^scaleFactor is first evaluated with Math.pow and d is then multiplied by it; the
chain evaluates no power and multiplies nothing (it adds to the exponent bits). It names neither special values nor any omitted
step nor any hop.

No pre-edits. All five hosts and the gold are in org.apache.commons.math.linear, so no import is added; the facade calls hop 1 by
its fully-qualified name.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: d feeds the special-value test, the raw bits and the early return; exponentIncrement feeds the rebuilt bits.
  T2 absent: bits, exponent and rest all reach the return; no literal-initialised or loop-moved local; the if returns d, the
     fall-through returns the rebuilt bits (two different effects).
  T3 absent: the special-value test treats zero (both signs, d == 0), NaN and both infinities; the gold names no class it handles
     in part; no pair half or range end is treated alone (the three bit fields sign, exponent and mantissa are all read: sign and
     mantissa kept by one mask, exponent incremented).
  T4 absent: the javadoc names only 'a power of two', 'd multiplied by the power of two' and the caller's increment ('the scale
     factor times 2^52', a caller precondition); no rule, bound, value class or case is named.
 Variant gold (javadoc, signature, `final long bits = Double.doubleToLongBits(d); final long exponent = bits & 0x7ff0000000000000L;
 final long rest = bits & 0x800fffffffffffffL; return Double.longBitsToDouble(rest | (exponent + exponentIncrement));`):
  T1 absent: d is read by doubleToLongBits and through bits, exponent and rest changes the result; exponentIncrement is added in
     the return; neither is only argument-checked.
  T2 absent: bits feeds exponent and rest, both reach the return; no local is initialised to a literal; no loop, branch, case or
     ternary.
  T3 absent: no special value is handled at all ('No member handled'); no set has a handled and an unhandled member; the three
     bit fields of the double are all read and treated; the gold names no class.
  T4 absent: 'Multiply a number by a power of two' and '@return d multiplied by the power of two' are general descriptions that
     the return line addresses; '@param exponentIncrement ... the scale factor times 2^52' is a caller precondition; no inline
     comment; the identifiers bits, exponent, rest and exponentIncrement name nothing the body does not meet."""

MU = "src/java/org/apache/commons/math/util/MathUtils.java"
EDI = "src/java/org/apache/commons/math/linear/EigenDecompositionImpl.java"
DRM = "src/java/org/apache/commons/math/linear/DenseRealMatrix.java"
BMI = "src/java/org/apache/commons/math/linear/BigMatrixImpl.java"
RVI = "src/java/org/apache/commons/math/linear/RealVectorImpl.java"
ARM = "src/java/org/apache/commons/math/linear/AbstractRealMatrix.java"

GOLD_TEXT = '''/**
 * Multiply a number by a power of two.
 * @param d base number
 * @param exponentIncrement power of two by which d is multiplied, as an
 * increment of the exponent bits (the scale factor times 2<sup>52</sup>)
 * @return d multiplied by the power of two
 */
public static double multiplyByPowerOfTwo(final double d, final long exponentIncrement) {
    if ((d == 0) || Double.isNaN(d) || Double.isInfinite(d)) {
        return d;
    }
    final long bits = Double.doubleToLongBits(d);
    final long exponent = bits & 0x7ff0000000000000L;
    final long rest = bits & 0x800fffffffffffffL;
    return Double.longBitsToDouble(rest | (exponent + exponentIncrement));
}'''

HOP1 = '''/**
 * Scale a number by 2<sup>scaleFactor</sup>.
 * @param d base number
 * @param scaleFactor power of two by which d is multiplied
 * @return d &times; 2<sup>scaleFactor</sup>
 */
public static double scaledByPowerOfTwo(final double d, final int scaleFactor) {
    return DenseRealMatrix.binaryScaledEntry(d, scaleFactor);
}'''

HOP2 = '''/**
 * Scale an entry by 2<sup>scaleFactor</sup>.
 * @param d entry to scale
 * @param scaleFactor power of two by which d is multiplied
 * @return d &times; 2<sup>scaleFactor</sup>
 */
public static double binaryScaledEntry(final double d, final int scaleFactor) {
    return BigMatrixImpl.exponentScaledValue(d, scaleFactor);
}'''

HOP3 = '''/**
 * Scale a value by 2<sup>scaleFactor</sup>.
 * @param d value to scale
 * @param scaleFactor power of two by which d is multiplied
 * @return d &times; 2<sup>scaleFactor</sup>
 */
public static double exponentScaledValue(final double d, final int scaleFactor) {
    return RealVectorImpl.scaledComponent(d, scaleFactor);
}'''

HOP4 = '''/**
 * Scale a vector component by 2<sup>scaleFactor</sup>.
 * <p>A zero scale factor leaves the component unchanged; any other scale
 * factor is converted into the matching increment of the exponent bits,
 * scaleFactor &times; 2<sup>52</sup>.</p>
 * @param d component to scale
 * @param scaleFactor power of two by which d is multiplied
 * @return d &times; 2<sup>scaleFactor</sup>
 */
public static double scaledComponent(final double d, final int scaleFactor) {
    if (scaleFactor == 0) {
        return d;
    }
    return AbstractRealMatrix.multiplyByPowerOfTwo(d, ((long) scaleFactor) << 52);
}'''

DESIGN = {
 "instance": "Math-92", "project": "Math", "bug_id": 92, "seed": 3277,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "scalb", "near_line": 817},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/math/util/MathUtilsTest.java",
             "test_class": "org.apache.commons.math.util.MathUtilsTest", "test_method": "testScalb"},
 "expected_signature": "MathUtilsTest.testScalb(MathUtilsTest.java:645)",
 "gold": {"method": "multiplyByPowerOfTwo", "text": GOLD_TEXT,
          "fault": {"old": "        if ((d == 0) || Double.isNaN(d) || Double.isInfinite(d)) {\n"
                           "            return d;\n"
                           "        }\n"
                           "        final long bits = Double.doubleToLongBits(d);",
                    "new": "        final long bits = Double.doubleToLongBits(d);"}},
 "chain": {
   "facade_body": "return org.apache.commons.math.linear.EigenDecompositionImpl.scaledByPowerOfTwo(d, scaleFactor);",
   "lie": "The factor 2<sup>scaleFactor</sup> is first evaluated with {@link Math#pow(double, double)}, and d is then "
          "multiplied by this factor.",
   "hops": [
     {"file": EDI, "class": "org.apache.commons.math.linear.EigenDecompositionImpl", "method": "scaledByPowerOfTwo",
      "imports": [], "text": HOP1},
     {"file": DRM, "class": "org.apache.commons.math.linear.DenseRealMatrix", "method": "binaryScaledEntry",
      "imports": [], "text": HOP2},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "exponentScaledValue",
      "imports": [], "text": HOP3},
     {"file": RVI, "class": "org.apache.commons.math.linear.RealVectorImpl", "method": "scaledComponent",
      "imports": [], "text": HOP4},
     {"file": ARM, "class": "org.apache.commons.math.linear.AbstractRealMatrix", "method": "multiplyByPowerOfTwo",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.util.MathUtils::scalb",
              "org.apache.commons.math.util.MathUtils::nextAfter",
              "org.apache.commons.math.util.MathUtils::round"],
 "ownership_reason": "Only the gold looks at the value of d: it is the only method on the path that splits d into its raw bits, "
                     "and the special-value decision belongs with that split. Hops 1-4 never inspect d (hops 1-3 pass their "
                     "arguments on; hop 4 tests only the scale factor, returning d for a zero scale factor, and converts any other "
                     "scale factor into the increment of the exponent bits). Once the "
                     "exponent bits of an infinite or NaN value have been incremented, the carry has overwritten the sign bit and "
                     "the exponent field is zero, so the returned -0.0 (or negative subnormal) cannot be told apart from the "
                     "scaling of an ordinary value and no caller can recover infinity or NaN from it. The convention is pinned "
                     "outside the gold: the facade's javadoc ('If d is 0 or NaN or Infinite, it is returned unchanged'); "
                     "MathUtils.nextAfter returns NaN or infinite d unchanged directly before it splits the double in raw "
                     "components (MathUtilsTest testNextAfterSpecialCases); MathUtils.round returns infinite values unchanged and "
                     "NaN as NaN (MathUtilsTest testRoundDouble, testRoundFloat). No caller can make the gold's own arithmetic give "
                     "the special values back: the variant gold returns an infinite or NaN d only for a zero increment, a zero "
                     "scale factor never reaches the gold (hop 4 returns d itself) and hop 4 is documented to pass the increment "
                     "matching any non-zero scale factor; a caller that tests NaN and infinity itself re-implements the gold's "
                     "decision and bypasses the gold. The gold still returns -0.0 for (+infinity, 2^52), an input every javadoc on "
                     "the path admits.",
 "ownership_tests": ["org.apache.commons.math.util.MathUtilsTest::testNextAfterSpecialCases",
                     "org.apache.commons.math.util.MathUtilsTest::testRoundDouble",
                     "org.apache.commons.math.util.MathUtilsTest::testRoundFloat"],
 "compensating": {
   "chain": [
     {"file": RVI, "old": "return AbstractRealMatrix.multiplyByPowerOfTwo(d, ((long) scaleFactor) << 52);",
      "new": "return AbstractRealMatrix.multiplyByPowerOfTwo(d, scaleFactor * 0x0010000000000000L);",
      "why": "hop 4 forms the exponent increment by multiplication"},
     {"file": EDI, "old": "return DenseRealMatrix.binaryScaledEntry(d, scaleFactor);",
      "new": "return DenseRealMatrix.binaryScaledEntry(d, Math.max(-2098, Math.min(2098, scaleFactor)));",
      "why": "hop 1 bounds the scale factor to the span of the exponent field"},
     {"file": BMI, "old": "return RealVectorImpl.scaledComponent(d, scaleFactor);",
      "new": "return Math.copySign(RealVectorImpl.scaledComponent(Math.abs(d), scaleFactor), d);",
      "why": "hop 3 scales the magnitude of d and restores its sign"},
   ],
 },
 "host_notes": "host_mode largest5 (2 other public classes of >= 1500 lines in this revision). Hosts are exactly the task "
               "record's hosts_hop_order, the five largest public non-interface non-enum classes other than MathUtils: "
               "linear.EigenDecompositionImpl 1832 lines (hop 1, anchor after getSolver, line idx 367, seed 3377), "
               "linear.DenseRealMatrix 1621 (hop 2, after walkInOptimizedOrder, 1601, seed 3378), linear.BigMatrixImpl 1499 "
               "(hop 3, after equals, 1327, seed 3379), linear.RealVectorImpl 1407 (hop 4, after mapExpm1, 411, seed 3380), "
               "linear.AbstractRealMatrix 1244 (hop 5, gold, after copySubMatrix, 359, seed 3381); smallest host 1244 lines. "
               "Anchors from stageB_lib.pick_anchor with seed 3277 + 100 + i, all in the outer class at brace depth 1. All five "
               "are public classes in which a static method compiles (AbstractRealMatrix is abstract, which does not affect a "
               "static method; the new names clash with no method of its subclasses DenseRealMatrix, RealMatrixImpl and "
               "SparseRealMatrix); none was skipped or substituted. All hops share the linear package, so no import is added; "
               "the facade calls hop 1 by its fully-qualified name.",
}
