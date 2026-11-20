"""Main run Math-93, cell C10f (C10 recipe with fallback hosts, BATCH6_PREREGISTRATION.md) on the fixed checkout of Defects4J
Math-93; the real bug modified MathUtils, the target class.

Facade: MathUtils.nextAfter(double, double) (allowed target, BATCH6_PREREGISTRATION.md row Math-93; builder warning recorded: the
same FQN was an allowed target of Math-79, UNBUILDABLE there for a host-pool reason only). The other allowed targets were set
aside. binomialCoefficient delegates its whole computation to binomialCoefficientDouble / binomialCoefficientLog, which stay
public production methods (distributions, tests); its own steps are two argument checks, two shortcut returns that the log sum
reproduces exactly (omitting either fails no test) and a final Long.MAX_VALUE check on the returned value, which every caller
can see and recover. subAndCheck: the long overload's own step is the Long.MIN_VALUE case of the negation, an input-level test
that any hop can pre-filter, and the addition it delegates to has paired positive and negative overflow checks (omitting one is
checklist T3(b)) and a symmetry swap that a hop can absorb by passing the operands in order; the int overload is one widened
subtraction with one two-ended range test.
nextAfter has one production caller, MathUtils.roundUnscaled (the float round(..) overloads: floor/ceil of nextAfter(unscaled,
+-infinity)); its test callers are MathUtilsTest::testNextAfter, ::testNextAfterSpecialCases, ::testArrayEquals,
::testArrayHash and, through roundUnscaled, ::testRoundFloat.
Original computation: NaN or infinite d is returned unchanged; d == 0 gives Double.MIN_VALUE, or -Double.MIN_VALUE when
direction < 0; otherwise the raw bits are split into sign, exponent and mantissa, the magnitude moves up when
d * (direction - d) >= 0 and down otherwise, with an explicit carry into the exponent when the mantissa is all ones and an
explicit borrow from it when the mantissa is zero.

reachability_probe: in a scratch copy of the fixture (/private/tmp/mr-Math-93-probe) the first statement of nextAfter was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (a bare throw would make the rest of the body unreachable,
which javac rejects); defects4j compile OK; defects4j test -t on MathUtilsTest::testNextAfter, ::testNextAfterSpecialCases,
::testArrayEquals and ::testArrayHash: each fails with java.lang.IllegalStateException: PROBE-REACHED at
MathUtils.nextAfter(MathUtils.java:692). Full suite on the probe copy: exactly 5 failing tests, all with PROBE-REACHED
(those four and MathUtilsTest::testRoundFloat, via roundUnscaled); no other test reaches the facade. Facade usable.

Hosts (host_mode = largest5: the revision has only 2 other public classes of >= 1500 lines, so the five hosts are the five largest
public non-interface non-enum classes other than MathUtils, hosts_hop_order of batch6_tasks.json, used as listed, none
substituted). Newline counts: EigenDecompositionImpl 1832, DenseRealMatrix 1621, BigMatrixImpl 1499, RealVectorImpl 1407,
AbstractRealMatrix 1244; smallest host 1244 lines (the gold host). Anchors from stageB_lib.pick_insertion_anchor with the instance
seed 8420 (+100+i): after getD (seed 8520), getColumn (8521), setRoundingMode (8522), the RealVectorImpl(Double[]) constructor
(8523), walkInRowOrder (8524).

The facade keeps its first special case (NaN or infinite d is returned unchanged) as its guard and delegates to a five-hop chain:
  hop 1 linear.EigenDecompositionImpl.nextRepresentable   decision: a zero d gives +-Double.MIN_VALUE by the sign of direction
  hop 2 linear.DenseRealMatrix.adjacentEntry              decision: the side, larger magnitude when d * (direction - d) >= 0
  hop 3 linear.BigMatrixImpl.adjacentValue                placement: works on Math.abs(d) and restores the sign with
                                                          MathUtils.indicator(d)
  hop 4 linear.RealVectorImpl.representableMagnitude      pass-through
  hop 5 linear.AbstractRealMatrix.adjacentMagnitude       GOLD: the adjacent representable magnitude: Math.ulp(magnitude) above;
                                                          below, the same gap, except half of it when the magnitude is a
                                                          normal power of two above MathUtils.SAFE_MIN
The correct configuration returns the original result for every input: checked bit for bit (doubleToRawLongBits, so the signs
of zero included) against the original body on 2e7 random and special (d, direction) pairs (0, -0.0, +-MIN_VALUE, +-MAX_VALUE,
+-SAFE_MIN, subnormals, powers of two, all-ones mantissas, NaN and infinite directions): 0 differences.

Fault (omission of a special-case decision in the gold): the power-of-two branch is dropped, so the magnitude below is always
magnitude - Math.ulp(magnitude). The gold then reads as the plain "plus or minus one ulp" routine. Trigger: the EXISTING test
MathUtilsTest::testNextAfter; its first five assertions hold and the sixth, nextAfter(-8.0, 34.27555555555555) =
-7.999999999999999, fails with expected:<-7.999999999999999> but was:<-7.999999999999998> (8.0 is a power of two: the number
below it is 2^-50 away, half of Math.ulp(8.0); the variant goes two representable numbers down). testNextAfterSpecialCases
(MIN_VALUE -> 0 is subnormal, MAX_VALUE -> infinity is the larger side), testArrayEquals and testArrayHash (nextAfter(1, 2),
larger side) and testRoundFloat (no unscaled value is a power of two; zero is hop 1's) pass on the variant. The gold's javadoc
states the idiomatic contract (the next smaller representable magnitude) and is silent on powers of two; 7.999999999999998 is
not the next smaller representable magnitude below 8.0, so the omission violates that contract on the trigger input.

External pins (convention outside the gold): the facade's own javadoc ('the smallest machine representable number strictly
greater than d is returned; otherwise the largest representable number strictly less than d'); MathUtils.EPSILON = 0x1.0p-53, documented as the smallest positive number such that 1 - EPSILON is not
numerically equal to 1, i.e. the number below the power of two 1.0 is half of Math.ulp(1.0) = 2^-52 away; the production caller
MathUtils.roundUnscaled, which takes floor or ceil of nextAfter(unscaled, +-infinity) as the immediate neighbour of the unscaled
value; tests testNextAfterSpecialCases (MIN_VALUE -> 0 and MAX_VALUE -> infinity, one representable step each), testArrayEquals and
testArrayHash (nextAfter(1, 2) is a different number), testRoundFloat (the production caller through the whole chain).

Single owner: only the gold holds a magnitude together with its gap to the adjacent representable magnitude; hop 1 sees only
whether d is zero, hop 2 only the side, hop 3 only the sign, hop 4 passes the pair along. Whether the gap below is the full or
half ulp depends on the mantissa bits of the magnitude, which no caller inspects, and once two representable steps have been
taken no caller can tell from the returned value that a binade boundary was crossed. Declared alternatives (G9): hop 2 decides
the side from the sign of d and a comparison with direction; hop 3 restores the sign with Math.copySign; hop 3 takes the
magnitude by clearing the sign bit. Each still returns -7.999999999999998 on the trigger input.
Recorded bypasses (one-line edits above the gold that replace the gold's result with another implementation, not repairs of the
chain; checked on the variant in a scratch copy where marked):
 B-0 the facade's original body, or any of hops 2-4 computing the neighbour from the raw bits, e.g. hop 3
     `return Double.longBitsToDouble(Double.doubleToLongBits(d) + (larger ? 1 : -1));` (sign-magnitude bits: +1 moves to the
     larger magnitude, -1 to the smaller), discarding hops 4-5 including the gold. Checked at hop 3 on the variant in a scratch
     copy: trigger passes, full suite 0 failing tests.
 B-1 a hop that answers the smaller side itself and calls the gold only for the larger side, e.g. hop 3
     `return larger ? MathUtils.indicator(d) * RealVectorImpl.representableMagnitude(Math.abs(d), true) : Math.nextAfter(d, 0.0);`
     (java.lang.Math.nextAfter toward zero), or a hop that tests for a power of two itself: on the trigger input the gold's
     output is never used; a second implementation of the gold's decision. Checked (the Math.nextAfter form at hop 3) on the
     variant in a scratch copy: trigger passes, full suite 0 failing tests.

Lie: the facade's javadoc claims d is converted to a BigDecimal through its shortest decimal representation, whose last decimal
digit is moved by one toward direction before the result is converted back to a double (the house style of MathUtils.round);
the chain uses no BigDecimal and no decimal digits. It names neither powers of two nor any gap nor any hop.

No pre-edits. BigMatrixImpl gets the MathUtils import; the other hosts already import it or need nothing (same package).

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: magnitude feeds Math.ulp, the power-of-two test and every return; larger decides which return is taken.
  T2 absent: the only local, ulp, is read in all three returns; no literal-initialised or loop-moved local; the `if (larger)` and
     the power-of-two `if` each choose between different results.
  T3 absent: both sides get a gap from ulp; the extra case exists only on the smaller side because Math.ulp is by definition the
     gap to the next larger magnitude, so no member of {larger, smaller} is left without its treatment; no class is named.
  T4 absent: the javadoc names the adjacent representable magnitude on the requested side and a caller precondition (positive
     finite magnitude); no limit, bound, value class or case.
 Variant gold (javadoc, signature, `final double ulp = Math.ulp(magnitude); if (larger) { return magnitude + ulp; }
 return magnitude - ulp;`):
  T1 absent: magnitude is read by Math.ulp and both returns, larger by the if; each changes the returned value.
  T2 absent: ulp is read in both returns; no frozen local, no loop; the if returns magnitude + ulp, the fall-through
     magnitude - ulp, two different effects.
  T3 absent: the two sides (larger, smaller) both get the same treatment (plus or minus ulp); no special case, branch or check
     remains for any value class (no member handled); the gold names no class it handles in part.
  T4 absent: 'the next larger representable magnitude ... otherwise the next smaller one' and 'the representable magnitude
     adjacent to the given one' are general descriptions that the two returns address; '@param magnitude positive finite
     magnitude' is a caller precondition; no inline comment; identifiers (ulp, magnitude, larger) name nothing the body does not
     meet."""

MU = "src/java/org/apache/commons/math/util/MathUtils.java"
EDI = "src/java/org/apache/commons/math/linear/EigenDecompositionImpl.java"
DRM = "src/java/org/apache/commons/math/linear/DenseRealMatrix.java"
BMI = "src/java/org/apache/commons/math/linear/BigMatrixImpl.java"
RVI = "src/java/org/apache/commons/math/linear/RealVectorImpl.java"
ARM = "src/java/org/apache/commons/math/linear/AbstractRealMatrix.java"

MAGNITUDE_DOC = '''/**
 * Get the representable magnitude adjacent to a positive magnitude.
 * @param magnitude positive finite magnitude
 * @param larger if true, the next larger representable magnitude is
 * returned, otherwise the next smaller one
 * @return the representable magnitude adjacent to the given one
 */'''

GOLD_TEXT = MAGNITUDE_DOC + '''
public static double adjacentMagnitude(final double magnitude, final boolean larger) {
    final double ulp = Math.ulp(magnitude);
    if (larger) {
        return magnitude + ulp;
    }
    if ((magnitude > MathUtils.SAFE_MIN) &&
        ((Double.doubleToLongBits(magnitude) & 0x000fffffffffffffL) == 0L)) {
        return magnitude - 0.5 * ulp;
    }
    return magnitude - ulp;
}'''

HOP1 = '''/**
 * Get the next machine representable number after a finite number,
 * moving in the direction of another number.
 * <p>
 * If <code>d</code> is zero, the smallest positive number is returned
 * when <code>direction</code> is not negative, and the largest negative
 * number otherwise.</p>
 * @param d base number (finite)
 * @param direction direction of the move
 * @return the next machine representable number in the specified direction
 */
public static double nextRepresentable(final double d, final double direction) {
    if (d == 0) {
        return (direction < 0) ? -Double.MIN_VALUE : Double.MIN_VALUE;
    }
    return DenseRealMatrix.adjacentEntry(d, direction);
}'''

HOP2 = '''/**
 * Get the representable number adjacent to a non-zero finite number, on
 * the side of another number.
 * <p>
 * The magnitude increases when <code>direction</code> lies beyond
 * <code>d</code> as seen from zero, or is equal to <code>d</code>, and
 * decreases otherwise.</p>
 * @param d base number (finite, non-zero)
 * @param direction direction of the move
 * @return the representable number adjacent to d on the side of direction
 */
public static double adjacentEntry(final double d, final double direction) {
    return BigMatrixImpl.adjacentValue(d, d * (direction - d) >= 0);
}'''

HOP3 = '''/**
 * Get the representable number adjacent to a non-zero finite number,
 * with a larger or a smaller magnitude.
 * <p>
 * The adjacent magnitude is computed for the absolute value of
 * <code>d</code>, and the sign of <code>d</code> is then restored.</p>
 * @param d base number (finite, non-zero)
 * @param larger if true, the adjacent number with a larger magnitude is
 * returned, otherwise the adjacent number with a smaller magnitude
 * @return the representable number adjacent to d
 */
public static double adjacentValue(final double d, final boolean larger) {
    return MathUtils.indicator(d) * RealVectorImpl.representableMagnitude(Math.abs(d), larger);
}'''

HOP4 = MAGNITUDE_DOC + '''
public static double representableMagnitude(final double magnitude, final boolean larger) {
    return AbstractRealMatrix.adjacentMagnitude(magnitude, larger);
}'''

DESIGN = {
 "instance": "Math-93", "project": "Math", "bug_id": 93, "seed": 8420,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "nextAfter", "near_line": 691},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/math/util/MathUtilsTest.java",
             "test_class": "org.apache.commons.math.util.MathUtilsTest", "test_method": "testNextAfter"},
 "expected_signature": "expected:<-7.999999999999999> but was:<-7.999999999999998>",
 "gold": {"method": "adjacentMagnitude", "text": GOLD_TEXT,
          "fault": {"old": "        if ((magnitude > MathUtils.SAFE_MIN) &&\n"
                           "            ((Double.doubleToLongBits(magnitude) & 0x000fffffffffffffL) == 0L)) {\n"
                           "            return magnitude - 0.5 * ulp;\n"
                           "        }\n"
                           "        return magnitude - ulp;",
                    "new": "        return magnitude - ulp;"}},
 "chain": {
   "facade_body": "// handling of some important special cases\n"
                  "        if (Double.isNaN(d) || Double.isInfinite(d)) {\n"
                  "            return d;\n"
                  "        }\n"
                  "        return org.apache.commons.math.linear.EigenDecompositionImpl.nextRepresentable(d, direction);",
   "lie": "The value of d is converted to a BigDecimal through its shortest decimal representation, whose last decimal digit "
          "is moved by one toward direction before the result is converted back to a double.",
   "hops": [
     {"file": EDI, "class": "org.apache.commons.math.linear.EigenDecompositionImpl", "method": "nextRepresentable",
      "imports": [], "text": HOP1},
     {"file": DRM, "class": "org.apache.commons.math.linear.DenseRealMatrix", "method": "adjacentEntry",
      "imports": [], "text": HOP2},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "adjacentValue",
      "imports": ["org.apache.commons.math.util.MathUtils"], "text": HOP3},
     {"file": RVI, "class": "org.apache.commons.math.linear.RealVectorImpl", "method": "representableMagnitude",
      "imports": [], "text": HOP4},
     {"file": ARM, "class": "org.apache.commons.math.linear.AbstractRealMatrix", "method": "adjacentMagnitude",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.util.MathUtils::nextAfter",
              "org.apache.commons.math.util.MathUtils::roundUnscaled",
              "org.apache.commons.math.util.MathUtils::scalb"],
 "ownership_reason": "Only the gold holds a magnitude together with its gap to the adjacent representable magnitude; hop 1 sees "
                     "only whether d is zero, hop 2 only the side of the move, hop 3 only the sign, hop 4 passes the pair "
                     "along. Whether the gap below is the full or half ulp depends on the mantissa bits of the magnitude, which "
                     "no caller inspects, and once two representable steps have been taken no caller can tell from the "
                     "returned value that a binade boundary was crossed. The convention is pinned outside the gold: the "
                     "facade's javadoc ('the smallest machine representable number strictly greater than d is returned; otherwise "
                     "the largest representable number strictly less than d'); "
                     "MathUtils.EPSILON = 0x1.0p-53, the smallest positive number such that 1 - EPSILON is not numerically "
                     "equal to 1, so the number below the power of two 1.0 is half of Math.ulp(1.0) away; MathUtils.scalb "
                     "moves the exponent field of a double in whole steps of 2^52 in its raw bits; the production caller "
                     "MathUtils.roundUnscaled takes floor or ceil of nextAfter(unscaled, +-infinity) as the immediate "
                     "neighbour of the unscaled value (MathUtilsTest testRoundFloat); testNextAfterSpecialCases pins one "
                     "representable step at both ends of the range (MIN_VALUE -> 0, MAX_VALUE -> infinity), testArrayEquals "
                     "and testArrayHash that nextAfter(1, 2) is a different number.",
 "ownership_tests": ["org.apache.commons.math.util.MathUtilsTest::testNextAfterSpecialCases",
                     "org.apache.commons.math.util.MathUtilsTest::testArrayEquals",
                     "org.apache.commons.math.util.MathUtilsTest::testArrayHash",
                     "org.apache.commons.math.util.MathUtilsTest::testRoundFloat"],
 "compensating": {
   "chain": [
     {"file": DRM, "old": "return BigMatrixImpl.adjacentValue(d, d * (direction - d) >= 0);",
      "new": "return BigMatrixImpl.adjacentValue(d, (d > 0) ? (direction >= d) : (direction <= d));",
      "why": "hop 2 decides the side from the sign of d and a comparison with direction"},
     {"file": BMI, "old": "return MathUtils.indicator(d) * RealVectorImpl.representableMagnitude(Math.abs(d), larger);",
      "new": "return Math.copySign(RealVectorImpl.representableMagnitude(Math.abs(d), larger), d);",
      "why": "hop 3 restores the sign with Math.copySign"},
     {"file": BMI, "old": "return MathUtils.indicator(d) * RealVectorImpl.representableMagnitude(Math.abs(d), larger);",
      "new": "return MathUtils.indicator(d) * RealVectorImpl.representableMagnitude(Double.longBitsToDouble(Double.doubleToLongBits(d) & 0x7fffffffffffffffL), larger);",
      "why": "hop 3 takes the magnitude by clearing the sign bit"},
   ],
 },
 "host_notes": "host_mode largest5 (2 other public classes of >= 1500 lines in this revision). Hosts exactly as hosts_hop_order "
               "in batch6_tasks.json, hop i in the i-th largest: linear.EigenDecompositionImpl (1832 lines, hop 1), "
               "linear.DenseRealMatrix (1621, hop 2), linear.BigMatrixImpl (1499, hop 3), linear.RealVectorImpl (1407, hop 4), "
               "linear.AbstractRealMatrix (1244, hop 5, gold); smallest host 1244 lines. All five are public top-level classes "
               "in which a static method compiles (AbstractRealMatrix is abstract and DenseRealMatrix extends it; the hop "
               "names differ, so no static method is hidden); none was substituted. Anchors (stageB_lib.pick_insertion_anchor, "
               "instance seed 8420 + 100 + i): after getD (8520), getColumn (8521), setRoundingMode (8522), the "
               "RealVectorImpl(Double[]) constructor (8523), walkInRowOrder (8524); every anchor is an outer-class member. "
               "The facade calls hop 1 by its fully-qualified name; hops 1-4 call the next host in the same package; "
               "BigMatrixImpl gets the MathUtils import, the other hosts already import it or need nothing.",
}
