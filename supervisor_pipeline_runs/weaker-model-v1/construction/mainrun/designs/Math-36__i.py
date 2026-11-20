"""Main run Math-36__i (cell C10i, batch 7, the paired static/instance bridge: the C10 recipe with an INSTANCE-METHOD facade, on the
fixed checkout of Defects4J Math-36; the real bug modified BigFraction, the facade's class). Paired static instance: MR-Math-36
(batch 4, static facade BigFraction.getReducedFraction; not opened, BUILD_BRIEF_C10I_ADDENDUM section 2).

Facade: BigFraction.floatValue() (allowed target, BATCH7_PREREGISTRATION.md row 204; no facade reuse). It is an instance method
(an @Override of Number.floatValue) that reads the two private fields numerator and denominator and writes none.
  facade_variant = V1 (state as parameters): the facade reads the fields numerator and denominator (it is inside the class) and
  passes their values to hop 1; the chain computes the float; the facade returns it. state_passed = the fields numerator and
  denominator (BigInteger values), no write-back. No guard (the original has none). No visibility, signature, modifier,
  annotation or thrown-type change; no new type; no reflection; no test edit.
Original computation of the facade: the float value of the numerator divided by the float value of the denominator; when that
quotient is NaN (both parts beyond the float range), both parts are shifted right by the same number of bits, the larger bit
length minus Float.MAX_EXPONENT, and the shifted parts are divided instead.
Why not the other allowed targets: BigFraction.doubleValue is reached by 39 existing tests through many production callers
(PolynomialsUtils, the Adams/Nordsieck ODE transformer, MatrixUtils' converter, KolmogorovSmirnovDistribution, percentageValue),
so its intact body is kept beside the facade as the external pin instead; BigFraction.pow(int) carries only the sign decision of
the exponent (a reciprocal), which any caller can take over in one line, and the probe shows it is also reached by
KolmogorovSmirnovDistributionTest.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in three scratch copies of the fixture
(/private/tmp/d4j-mi-Math-36-probe-{dv,fv,pw}) the first statement of doubleValue(), floatValue() and pow(int) respectively was
made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)` wrapper only keeps the rest of the body
reachable for javac), and the full suite was run (defects4j test). floatValue: 2 failing tests, both with
java.lang.IllegalStateException: PROBE-REACHED at BigFraction.floatValue(BigFraction.java:738):
BigFractionTest::testFloatValue (called at BigFractionTest.java:230) and BigFractionTest::testFloatValueForLargeNumeratorAndDenominator.
doubleValue: 39 failing tests with PROBE-REACHED (BigFractionTest x5, BigFractionFormatTest::testParseBig, MatrixUtilsTest,
PolynomialsUtilsTest x17, KolmogorovSmirnovDistributionTest, Adams* and NordsieckStepInterpolatorTest). pow(int): 2 failing
tests with PROBE-REACHED (BigFractionTest::testPow, KolmogorovSmirnovDistributionTest::testCumulativeDensityFunction). The
chosen facade is reached by an existing test directly.

Hosts (host_mode = "1500": the revision has five usable public classes of at least 1500 lines other than BigFraction; they are
hosts_hop_order of the task record, used in that order; mr_lib preview with the instance seed 2706 draws the same five in the same
order):
  hop 1 linear.BlockRealMatrix                 1536 lines  ratioToFloat    pass-through
  hop 2 util.FastMath                          3810 lines  floatRatio      pass-through
  hop 3 linear.BlockFieldMatrix                1549 lines  ratioAsFloat    pass-through
  hop 4 dfp.Dfp                                2494 lines  floatOfRatio    pass-through
  hop 5 optimization.direct.BOBYQAOptimizer    2482 lines  floatQuotient   GOLD: the float value of the fraction from its two
                                                                           parts, with the decision that rescales both parts
                                                                           when their float quotient is NaN
Host newline counts 1536, 3810, 1549, 2494, 2482; the smallest host has 1536 lines (BlockRealMatrix); the gold host has 2482.
None was substituted.
The correct configuration returns the original result for every input: the same float quotient, the same NaN test (Float.isNaN
on the float, as the original's Double.isNaN on the widened float), the same common shift (the larger bit length minus
Float.MAX_EXPONENT) and the same division of the shifted parts.

Fault (omission of a special-case decision in the gold): the if statement that rescales both parts when their float quotient is
NaN is dropped, so the gold divides the two float values and returns the quotient as it is. The gold then reads as the ordinary
routine "numerator divided by denominator in float arithmetic". Trigger: the EXISTING test
BigFractionTest::testFloatValueForLargeNumeratorAndDenominator: the fraction (10^401 + 1) / (2 * 10^400) has both parts beyond the
float range, both float values are Infinity, and assertEquals(5, large.floatValue(), 1e-15) fails with expected:<5.0> but
was:<NaN>. It is the only test that newly fails: floatValue is reached by exactly two tests (probe above), and
BigFractionTest::testFloatValue (1/2 and 1/3, whose parts are in range) passes on the variant.
Relation to the real bug: the omitted step is the rescaling that the real Math-36 fix (MATH-744) added to floatValue and
doubleValue; the injected fault removes it from the gold in BOBYQAOptimizer only, and the facade's own body no longer computes
anything. The trigger is the test that came with that fix, which is the only existing test whose float parts leave the range.

The gold's javadoc states the idiomatic contract (it computes the value of a fraction as a float) and is silent on parts beyond
the float range; NaN is not the value of (10^401 + 1) / (2 * 10^400), so the variant violates that contract on the trigger input.
The convention is pinned outside the gold: the sibling BigFraction.doubleValue, intact beside the facade, does the same step for
double (a NaN quotient of the double values is replaced by the quotient of both parts shifted right by the larger bit length minus
Double.MAX_EXPONENT), and BigFractionTest::testDoubleValueForLargeNumeratorAndDenominator, which asserts 5 for the same fraction
through doubleValue, passes on the variant; BigFraction.bigDecimalValue computes the value of a fraction from its parts whatever
their size (BigFractionTest::testBigDecimalValue passes); BigFractionTest::testFloatValue and ::testDoubleValue pin the ordinary
quotients.

Single owner: only the gold divides the parts and decides, from the quotient it has just computed, whether both parts must be
rescaled; hops 1-4 pass the two parts along unchanged and return the gold's float. Once the gold has returned NaN, the value of the
fraction cannot be recovered from it. Declared alternatives (G9): hop 4 reduces the fraction to lowest terms before delegating;
hop 2 removes the common powers of two of the parts; hop 3 divides the parts in double precision and narrows the result. None
changes the trigger's outcome (the fraction is already in lowest terms with an odd numerator, and both parts are beyond the double
range too).
The three declared alternatives were also run on the variant in scratch copies before validation: the trigger still fails
with expected:<5.0> but was:<NaN> for each.
Recorded bypasses (edits that replace the gold's result, or its rescaling step, with another implementation; each was checked on
the variant in a scratch copy with defects4j test: trigger passes, full suite 0 failing tests):
 B-0 the facade returns `(float) doubleValue();`, the intact double sibling, discarding the chain including the gold; any hop can
     do the same with `(float) new org.apache.commons.math.fraction.BigFraction(numerator, denominator).doubleValue()`.
 B-1 pre-scaling at hop 4: `return BOBYQAOptimizer.floatQuotient(numerator.shiftRight(Math.max(numerator.bitLength(),
     denominator.bitLength()) - Float.MAX_EXPONENT), denominator.shiftRight(<the same>));` (one long statement). This is the
     gold's own rescaling step implemented a second time in a caller and applied unconditionally: it changes the fraction handed
     to the gold for every input (a left shift for parts in range, a truncation for large parts), and for a fraction whose
     numerator is far larger than its denominator (for example 2^200 / 3, shift 74) it hands the gold a zero denominator, which
     the documentation of every hop and of the gold excludes ("not zero"); the gold's own rescaling happens only after its NaN
     test and stays inside the gold. Not consistent with the path.
 B-2 hop 4 calls the gold and, when the result is NaN, calls it again with both parts shifted
     (`final float q = BOBYQAOptimizer.floatQuotient(numerator, denominator); final int e = <the excess>; return Float.isNaN(q) ?
     BOBYQAOptimizer.floatQuotient(numerator.shiftRight(e), denominator.shiftRight(e)) : q;`): a second implementation of the
     gold's rescaling decision that replaces the gold's result.

Lie: the facade's javadoc claims the numerator and the denominator are first converted to BigDecimal values and divided to eight
significant digits, the decimal quotient then being narrowed to a float; the chain uses no BigDecimal and divides two float values.
It names neither the range of the parts nor any rescaling nor any hop.
Pre-edit (comment only, places the lie): the facade's javadoc is separated from its header by the @Override annotation, and the
recipe's rewrite_facade only appends the lie to a javadoc followed by whitespace alone (extract_transform.find_javadoc_start), so
it would silently leave the lie out. The pre-edit puts the same sentence exactly where rewrite_facade puts it in every other
instance: on its own line immediately before the closing */ of the facade's javadoc. The annotation, the header and the rest of
the javadoc are unchanged, and rewrite_facade then replaces only the body (it finds no adjacent javadoc, so the lie is not added
twice).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; quotient of the float values; if Float.isNaN(quotient) { excess = max bit length - Float.MAX_EXPONENT;
 quotient = quotient of the shifted parts }; return quotient):
  T1 absent: numerator and denominator are each converted and divided, and each is shifted and divided in the rescaled branch;
     neither is only argument-checked.
  T2 absent: quotient is computed, possibly reassigned in the branch, and returned; excess is computed in the branch and used by
     both shifts; no literal-initialised local, cursor, flag or best-so-far; the NaN test decides whether the rescaled quotient
     replaces the first one, a different result.
  T3 absent: the special-value treatment is a NaN test only, one member of the unnamed set of float special values, and the gold's
     text names no class ("finite", "infinite" or similar); the pair numerator/denominator is treated alike everywhere (both
     converted, both bit lengths in the max, both shifted by the same excess).
  T4 absent: 'the value of a fraction as a float' and '@return the value of the fraction, as a float' are general descriptions
     the body addresses; '(not zero)' is a caller precondition; identifiers (quotient, excess) name nothing the body does not do.
 Variant gold (javadoc, signature, `float quotient = numerator.floatValue() / denominator.floatValue();`, `return quotient;`):
  T1 absent: both parameters are converted and divided, and the quotient is returned; no argument check.
  T2 absent: quotient is initialised by the division (not a literal) and returned; no other local; no loop; no branch, case or
     ternary.
  T3 absent: no member of any special set is handled ('No member handled'); the pair numerator/denominator is treated alike;
     the gold names no class it handles in part.
  T4 absent: the javadoc names no limit, range, value class, case or property; '(not zero)' is a caller precondition; no inline
     comment; the identifiers quotient, numerator and denominator name nothing the body does not meet."""

BF = "src/main/java/org/apache/commons/math/fraction/BigFraction.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
BOB = "src/main/java/org/apache/commons/math/optimization/direct/BOBYQAOptimizer.java"

LIE = ("The numerator and the denominator are first converted to {@code BigDecimal} values and divided to eight "
       "significant digits, and that decimal quotient is then narrowed to a {@code float}.")

GOLD_TEXT = '''/**
 * Computes the value of a fraction as a {@code float}.
 *
 * @param numerator Numerator of the fraction.
 * @param denominator Denominator of the fraction (not zero).
 * @return the value of the fraction, as a {@code float}.
 */
public static float floatQuotient(final BigInteger numerator, final BigInteger denominator) {
    float quotient = numerator.floatValue() / denominator.floatValue();
    if (Float.isNaN(quotient)) {
        final int excess = Math.max(numerator.bitLength(), denominator.bitLength()) - Float.MAX_EXPONENT;
        quotient = numerator.shiftRight(excess).floatValue() / denominator.shiftRight(excess).floatValue();
    }
    return quotient;
}'''

HOP1 = '''/**
 * Get the value of a fraction as a float.
 *
 * @param numerator  the numerator of the fraction
 * @param denominator  the denominator of the fraction, not zero
 * @return the value of the fraction as a float
 */
public static float ratioToFloat(final BigInteger numerator, final BigInteger denominator) {
    return FastMath.floatRatio(numerator, denominator);
}'''

HOP2 = '''/**
 * Compute the value of a fraction as a float.
 * @param numerator numerator of the fraction
 * @param denominator denominator of the fraction, not zero
 * @return the value of the fraction as a float
 */
public static float floatRatio(final BigInteger numerator, final BigInteger denominator) {
    return BlockFieldMatrix.ratioAsFloat(numerator, denominator);
}'''

HOP3 = '''/**
 * Get the value of a fraction as a float.
 *
 * @param numerator  the numerator of the fraction
 * @param denominator  the denominator of the fraction, not zero
 * @return the value of the fraction as a float
 */
public static float ratioAsFloat(final BigInteger numerator, final BigInteger denominator) {
    return Dfp.floatOfRatio(numerator, denominator);
}'''

HOP4 = '''/** Convert a fraction to a float.
 * @param numerator numerator of the fraction
 * @param denominator denominator of the fraction, not zero
 * @return the value of the fraction as a float
 */
public static float floatOfRatio(final BigInteger numerator, final BigInteger denominator) {
    return BOBYQAOptimizer.floatQuotient(numerator, denominator);
}'''

DESIGN = {
 "instance": "Math-36", "project": "Math", "bug_id": 36, "seed": 2706,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": BF, "class": "org.apache.commons.math.fraction.BigFraction", "method": "floatValue", "near_line": 737},
 "facade_variant": "V1",
 "state_passed": "fields numerator and denominator (BigInteger values) passed to hop 1; no write-back",
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/fraction/BigFractionTest.java",
             "test_class": "org.apache.commons.math.fraction.BigFractionTest",
             "test_method": "testFloatValueForLargeNumeratorAndDenominator"},
 "expected_signature": "expected:<5.0> but was:<NaN>",
 "gold": {"method": "floatQuotient", "text": GOLD_TEXT,
          "fault": {"old": "        float quotient = numerator.floatValue() / denominator.floatValue();\n"
                           "        if (Float.isNaN(quotient)) {\n"
                           "            final int excess = Math.max(numerator.bitLength(), denominator.bitLength()) - Float.MAX_EXPONENT;\n"
                           "            quotient = numerator.shiftRight(excess).floatValue() / denominator.shiftRight(excess).floatValue();\n"
                           "        }\n"
                           "        return quotient;",
                    "new": "        float quotient = numerator.floatValue() / denominator.floatValue();\n"
                           "        return quotient;"}},
 "pre_edits": {
   "chain": [{"file": BF,
              "old": "     * @see java.lang.Number#floatValue()\n"
                     "     */\n"
                     "    @Override\n"
                     "    public float floatValue() {",
              "new": "     * @see java.lang.Number#floatValue()\n"
                     "       " + LIE + "\n"
                     "     */\n"
                     "    @Override\n"
                     "    public float floatValue() {"}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.math.linear.BlockRealMatrix.ratioToFloat(numerator, denominator);",
   "lie": LIE,
   "hops": [
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "ratioToFloat",
      "imports": ["java.math.BigInteger"], "text": HOP1},
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "floatRatio",
      "imports": ["java.math.BigInteger", "org.apache.commons.math.linear.BlockFieldMatrix"], "text": HOP2},
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "ratioAsFloat",
      "imports": ["java.math.BigInteger", "org.apache.commons.math.dfp.Dfp"], "text": HOP3},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "floatOfRatio",
      "imports": ["java.math.BigInteger", "org.apache.commons.math.optimization.direct.BOBYQAOptimizer"], "text": HOP4},
     {"file": BOB, "class": "org.apache.commons.math.optimization.direct.BOBYQAOptimizer", "method": "floatQuotient",
      "imports": ["java.math.BigInteger"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.fraction.BigFraction::doubleValue",
              "org.apache.commons.math.fraction.BigFraction::bigDecimalValue"],
 "ownership_reason": "Only the gold divides the two parts of the fraction and decides, from the float quotient it has just "
                     "computed, whether both parts must first be brought into the float range; hops 1-4 pass the numerator and "
                     "the denominator along unchanged and return the gold's float, and once the gold has returned NaN the value "
                     "of the fraction cannot be recovered from it. The gold's javadoc promises the value of the fraction as a "
                     "float, which for (10^401 + 1) / (2 * 10^400) is 5, not NaN. The convention is pinned outside the gold: the "
                     "sibling BigFraction.doubleValue, intact beside the facade, replaces a NaN quotient of the double values by "
                     "the quotient of both parts shifted right by the larger bit length minus Double.MAX_EXPONENT, and "
                     "BigFractionTest testDoubleValueForLargeNumeratorAndDenominator, which asserts 5 for the same fraction, "
                     "passes; BigFraction.bigDecimalValue computes the value of a fraction from its parts whatever their size "
                     "(testBigDecimalValue passes); testFloatValue and testDoubleValue pin the ordinary quotients. Shifting both "
                     "parts in a caller before the gold is a second implementation of the gold's own rescaling step: applied "
                     "unconditionally it changes the fraction handed to the gold for every input and, for a numerator far "
                     "larger than the denominator (2^200 / 3), hands the gold a zero denominator, which the documentation of "
                     "every hop and of the gold excludes.",
 "ownership_tests": ["org.apache.commons.math.fraction.BigFractionTest::testDoubleValueForLargeNumeratorAndDenominator",
                     "org.apache.commons.math.fraction.BigFractionTest::testFloatValue",
                     "org.apache.commons.math.fraction.BigFractionTest::testDoubleValue",
                     "org.apache.commons.math.fraction.BigFractionTest::testBigDecimalValue"],
 "compensating": {
   "chain": [
     {"file": DFP, "old": "return BOBYQAOptimizer.floatQuotient(numerator, denominator);",
      "new": "final BigInteger gcd = numerator.gcd(denominator);\n"
             "        return BOBYQAOptimizer.floatQuotient(numerator.divide(gcd), denominator.divide(gcd));",
      "why": "hop 4 reduces the fraction to lowest terms before delegating"},
     {"file": FM, "old": "return BlockFieldMatrix.ratioAsFloat(numerator, denominator);",
      "new": "final int twos = min(numerator.getLowestSetBit(), denominator.getLowestSetBit());\n"
             "        return BlockFieldMatrix.ratioAsFloat(numerator.shiftRight(twos), denominator.shiftRight(twos));",
      "why": "hop 2 removes the common powers of two of the numerator and the denominator"},
     {"file": BFM, "old": "return Dfp.floatOfRatio(numerator, denominator);",
      "new": "return (float) (numerator.doubleValue() / denominator.doubleValue());",
      "why": "hop 3 divides the parts in double precision and narrows the quotient to float"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are hosts_hop_order of the task record, in that order, none substituted: "
               "linear.BlockRealMatrix (hop 1, 1536 lines), util.FastMath (hop 2, 3810), linear.BlockFieldMatrix (hop 3, 1549), "
               "dfp.Dfp (hop 4, 2494), optimization.direct.BOBYQAOptimizer (hop 5, gold, 2482); smallest host 1536 lines. "
               "mr_lib preview (seed 2706, target org/apache/commons/math/fraction/BigFraction.java) draws the same five in the "
               "same order (FastMathLiteralArrays is package-private and not usable). All five are public concrete top-level "
               "classes in which a static method compiles (BlockFieldMatrix is generic; the static hop uses no type parameter). "
               "Anchors from stageB_lib.pick_insertion_anchor with seed 2706 + 100 + i (as mr3_spec.py inserts them): hop 1 after "
               "`getColumnDimension` (seed 2806), hop 2 after `scalb` (2807), hop 3 after `scalarMultiply` (2808), hop 4 after "
               "`divide` (the divide(int) overload, 2809), hop 5 after the constructor `BOBYQAOptimizer` (2810); all in the outer "
               "class. The facade calls hop 1 by its fully-qualified name; each hop imports java.math.BigInteger and the next "
               "host (BlockRealMatrix already imports FastMath).",
}
