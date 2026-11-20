"""Main run Math-63 (C10 recipe on the fixed checkout of Defects4J Math-63; the real bug modified MathUtils, the target class).

Facade: MathUtils.mulAndCheck(long, long) (allowed target mulAndCheck, BATCH4_PREREGISTRATION.md row Math-63). The other allowed
targets were set aside:
 - binomialCoefficientDouble: its only special-case steps (the exact long path for n < 67, the final rounding, the symmetry) are
   each recoverable by a one-line change at a caller hop (round the returned value, dispatch small n to binomialCoefficient,
   pass n - k), so no omission there has a single owner;
 - checkOrder: its per-element core is an enumeration over two closed sets (OrderDirection INCREASING/DECREASING and the strict
   flag); every omission inside it leaves a member of one of them untreated while its sibling is treated (checklist T3), or
   leaves the flag unread (T1), or freezes the running `previous` (T2).
The long overload is used rather than the int one: the int overload is a widened product with a two-sided range test, and any
omission in it leaves one range end untreated (T3).
Original computation of the facade: if a > b, recurse with (b, a) ("use symmetry to reduce boundary cases"); then, with a <= b,
a sign-by-sign case analysis that compares a against Long.MAX_VALUE / b or Long.MIN_VALUE / b, multiplies when the product fits
and throws ArithmeticException("overflow: multiply") otherwise; a zero factor gives 0.

The facade has no argument guard; its body becomes one delegating call to a five-hop chain:
  hop 1 linear.BlockFieldMatrix.exactProduct    placement: passes the two factors on with the smaller one first (the original's
                                                symmetry step)
  hop 2 util.FastMath.multiplyExact             pass-through
  hop 3 linear.BigMatrixImpl.longProduct        pass-through
  hop 4 linear.BlockRealMatrix.productOf        pass-through
  hop 5 linear.ArrayRealVector.entryProduct     GOLD: the overflow-checked product of two ordered factors (zero factors give 0;
                                                otherwise the product is computed and divided back by b, and the pair
                                                (Long.MIN_VALUE, -1), whose quotient wraps, is rejected as well)
The correct configuration returns exactly the original result, or throws exactly when the original throws, for every input:
checked against the original method on 2,785,561 operand pairs (edge values around 0, +-1, +-2, +-3, +-2^31, +-2^32,
+-3037000500, Long.MIN_VALUE, Long.MAX_VALUE and their halves, plus seeded random values), 0 differences, and both agree with an
exact BigInteger product on every pair.

Fault (omission of a special-case step in the gold): the disjunct that rejects the pair (Long.MIN_VALUE, -1) is dropped from the
overflow test, so the gold reads as the textbook divide-back check `product / b != a`. For a = Long.MIN_VALUE, b = -1 the product
wraps to Long.MIN_VALUE and Long.MIN_VALUE / -1 wraps to Long.MIN_VALUE again, so the test passes and Long.MIN_VALUE is returned
instead of an ArithmeticException (2^63 is not a long). Hop 1 orders (-1, Long.MIN_VALUE) into the same pair, so both orders
reach the gold as (Long.MIN_VALUE, -1). Trigger: the EXISTING test MathUtilsTest::testMulAndCheckLong; its ten value assertions
and its first four failure cases still hold, and testMulAndCheckLongFailure(min, -1L) fails with
"junit.framework.AssertionFailedError: Expecting ArithmeticException". No other test multiplies Long.MIN_VALUE by -1: the other
callers of the facade (binomialCoefficient for n > 66, lcm(long, long)) pass non-negative factors or factors other than -1, and
testBinomialCoefficient, testBinomialCoefficientLarge, testBinomialCoefficientFail and testLcmLong pass on the variant.
The gold's javadoc states the idiomatic contract (multiply two long integers, checking for overflow; @throws ArithmeticException
if the result can not be represented as a long, the facade's own wording) and is silent on Long.MIN_VALUE and on -1; on the
trigger input the result 2^63 cannot be represented as a long and nothing is thrown, so the variant violates that contract.

External pins (convention outside the gold): the facade's javadoc (@throws ArithmeticException if the result can not be
represented as a long); MathUtils.subAndCheck(long, long) treats a subtrahend of Long.MIN_VALUE as its own case because its
negation wraps (testSubAndCheckLong: subAndCheck(0L, Long.MIN_VALUE) must throw); MathUtils.lcm(long, long) rejects a result whose
absolute value wraps to Long.MIN_VALUE, i.e. 2^63 (testLcmLong: lcm(Long.MIN_VALUE, 1) must throw); the int overload
MathUtils.mulAndCheck(int, int) widens the product and rejects anything outside the int range, Integer.MIN_VALUE * -1 included
(testMulAndCheck).

Single owner: only the gold forms the product and decides whether it fits. Hop 1 orders the factors, hops 2-4 pass them on, and
all of them receive a long back; Long.MIN_VALUE is also the correct product of (Long.MIN_VALUE, 1) and of (Long.MIN_VALUE / 2, 2),
both asserted by the trigger, so no caller can tell a wrapped product from a valid one. Every hop from 2 to 5 documents the
ordering it receives (first factor not greater than the second), so the pair always reaches the gold as (Long.MIN_VALUE, -1).
Declared alternatives (G9): hop 1 orders the factors by magnitude (FastMath.abs of Long.MIN_VALUE is negative, so the pair is
unchanged); hop 2 passes the negated factors (same product; -Long.MIN_VALUE wraps, and the gold receives (1, Long.MIN_VALUE),
whose quotient matches); hop 3 returns -a for a second factor of -1 (the negation wraps to Long.MIN_VALUE). None changes the
trigger's outcome.
Recorded one-line edits above the gold that pass the trigger and the full suite (each checked on the variant in a scratch copy:
trigger passes, defects4j test 0 failing tests; B-1 at hop 4, B-2 at hop 3, B-3 at hop 1 and at hop 2):
 B-1 bypass: a hop (or the facade) rejects the pair itself before calling down,
     `if (a == Long.MIN_VALUE && b == -1) { throw new ArithmeticException("overflow: multiply"); }`: on the trigger input the
     gold's result is never used; a second implementation of the gold's overflow decision.
 B-2 bypass: hop 3 routes a second factor of -1 through the checked negation,
     `return (b == -1) ? org.apache.commons.math.util.MathUtils.subAndCheck(0L, a) : BlockRealMatrix.productOf(a, b);`: another
     implementation of the product for every b == -1, discarding the gold's result there.
 B-3 not consistent with the path: hop 1 orders the other way (`a < b`), or one of hops 2-4 passes (b, a): the gold then receives
     (-1, Long.MIN_VALUE), whose divide-back test detects the wrap. Both break the documented ordering (hop 1's own javadoc: the
     smaller factor first; the @param of hops 2-5: first factor not greater than the second).

Lie: the facade's javadoc claims each factor is split into its high and low 32-bit words and the product is assembled from the
four partial products, an overflow being reported when a partial product carries past 64 bits; the chain splits nothing and
divides the product back. It names neither Long.MIN_VALUE nor -1 nor any omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold: the only bound or special-value text is the omitted disjunct `(a == Long.MIN_VALUE && b == -1)` (Long.MIN_VALUE
  without Long.MAX_VALUE would read as one range end); it is exactly the omitted text, so it does not survive into the variant.
  Nothing else needed rewriting: both factors get the same zero test, both feed the product and the divide-back comparison,
  `product` is live, both decisions have two different effects, and the javadoc names no rule the body does not meet.
 Variant gold (javadoc, signature, `if (a == 0 || b == 0) { return 0L; } final long product = a * b;
  if (product / b != a) { throw new ArithmeticException("overflow: multiply"); } return product;`):
  T1 absent: a is read by the zero test, the product and the comparison; b by the zero test, the product and the division; each
     changes the returned value or whether the exception is thrown; neither is read only in an argument check.
  T2 absent: the only local, product, is returned and compared; it is not literal-initialised and there is no loop; the zero
     test returns 0 where the division would otherwise throw (b == 0), and the overflow test chooses between a throw and a
     return, so neither decision is dead.
  T3 absent: the two parameters get the same zero treatment and both take part in the product and the check; no range end
     (neither Long.MIN_VALUE nor Long.MAX_VALUE), no sign case and no value class is handled, so no set has a handled and an
     unhandled member ('No member handled'); the gold names no class that it handles only in part.
  T4 absent: 'Multiply two long integers, checking for overflow' and '@return the product a * b' are general descriptions that
     the body addresses; '@throws ArithmeticException if the result can not be represented as a long' is met by a line that
     tests it (the divide-back comparison) for the case the phrase names; '@param a first factor, not greater than b' is a
     caller precondition; no inline comment; the identifiers (entryProduct, product, a, b) name nothing the body does not
     meet."""

MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"
ARV = "src/main/java/org/apache/commons/math/linear/ArrayRealVector.java"
BMI = "src/main/java/org/apache/commons/math/linear/BigMatrixImpl.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"

ORDERED_DOC = '''/**
 * Multiply two long integers, checking for overflow.
 *
 * @param a first factor, not greater than b
 * @param b second factor
 * @return the product <code>a * b</code>
 * @throws ArithmeticException if the result can not be represented as a
 *         long
 */'''

GOLD_TEXT = ORDERED_DOC + '''
public static long entryProduct(final long a, final long b) {
    if (a == 0 || b == 0) {
        return 0L;
    }
    final long product = a * b;
    if (product / b != a || (a == Long.MIN_VALUE && b == -1)) {
        throw new ArithmeticException("overflow: multiply");
    }
    return product;
}'''

HOP1 = '''/**
 * Multiply two long integers, checking for overflow.
 * <p>The two factors are passed on with the smaller one first.</p>
 *
 * @param a first factor
 * @param b second factor
 * @return the product <code>a * b</code>
 * @throws ArithmeticException if the result can not be represented as a
 *         long
 */
public static long exactProduct(final long a, final long b) {
    return (a > b) ? FastMath.multiplyExact(b, a) : FastMath.multiplyExact(a, b);
}'''

HOP2 = ORDERED_DOC + '''
public static long multiplyExact(final long a, final long b) {
    return org.apache.commons.math.linear.BigMatrixImpl.longProduct(a, b);
}'''

HOP3 = ORDERED_DOC + '''
public static long longProduct(final long a, final long b) {
    return BlockRealMatrix.productOf(a, b);
}'''

HOP4 = ORDERED_DOC + '''
public static long productOf(final long a, final long b) {
    return ArrayRealVector.entryProduct(a, b);
}'''

DESIGN = {
 "instance": "Math-63", "project": "Math", "bug_id": 63, "seed": 5851,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "mulAndCheck", "near_line": 1047},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/util/MathUtilsTest.java",
             "test_class": "org.apache.commons.math.util.MathUtilsTest", "test_method": "testMulAndCheckLong"},
 "expected_signature": "AssertionFailedError: Expecting ArithmeticException",
 "gold": {"method": "entryProduct", "text": GOLD_TEXT,
          "fault": {"old": "        if (product / b != a || (a == Long.MIN_VALUE && b == -1)) {",
                    "new": "        if (product / b != a) {"}},
 "chain": {
   "facade_body": "return org.apache.commons.math.linear.BlockFieldMatrix.exactProduct(a, b);",
   "lie": "Each factor is split into its high and low 32-bit words, and the product is assembled from the four partial "
          "products, an overflow being reported as soon as a partial product carries past the 64th bit.",
   "hops": [
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "exactProduct",
      "imports": ["org.apache.commons.math.util.FastMath"], "text": HOP1},
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "multiplyExact",
      "imports": [], "text": HOP2},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "longProduct",
      "imports": [], "text": HOP3},
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "productOf",
      "imports": [], "text": HOP4},
     {"file": ARV, "class": "org.apache.commons.math.linear.ArrayRealVector", "method": "entryProduct",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.util.MathUtils::subAndCheck",
              "org.apache.commons.math.util.MathUtils::lcm",
              "org.apache.commons.math.util.MathUtils::mulAndCheck"],
 "ownership_reason": "Only the gold forms the product and decides whether it fits in a long; hop 1 orders the two factors "
                     "(smaller first, the original's symmetry step) and hops 2-4 pass them on, each receiving a long back. "
                     "Long.MIN_VALUE is also the correct product of (Long.MIN_VALUE, 1) and of (Long.MIN_VALUE / 2, 2), both "
                     "asserted by the trigger, so no caller can tell the wrapped product of (Long.MIN_VALUE, -1) from a valid "
                     "one. Hops 2-5 document the ordering they receive (first factor not greater than the second), so the pair "
                     "always reaches the gold as (Long.MIN_VALUE, -1); passing it the other way round breaks that documented "
                     "ordering. The gold's javadoc promises an ArithmeticException when the result can not be represented as a "
                     "long, which 2^63 cannot. The convention is pinned outside the gold: the facade's javadoc; "
                     "MathUtils.subAndCheck(long, long) treats a subtrahend of Long.MIN_VALUE as its own case because its "
                     "negation wraps (testSubAndCheckLong: subAndCheck(0L, Long.MIN_VALUE) throws); MathUtils.lcm(long, long) "
                     "rejects a result whose absolute value wraps to Long.MIN_VALUE, i.e. 2^63 (testLcmLong: "
                     "lcm(Long.MIN_VALUE, 1) throws); the int overload mulAndCheck(int, int) widens the product and rejects "
                     "anything outside the int range, Integer.MIN_VALUE * -1 included (testMulAndCheck).",
 "ownership_tests": ["org.apache.commons.math.util.MathUtilsTest::testSubAndCheckLong",
                     "org.apache.commons.math.util.MathUtilsTest::testLcmLong",
                     "org.apache.commons.math.util.MathUtilsTest::testMulAndCheck",
                     "org.apache.commons.math.util.MathUtilsTest::testAddAndCheckLong"],
 "compensating": {
   "chain": [
     {"file": BFM, "old": "return (a > b) ? FastMath.multiplyExact(b, a) : FastMath.multiplyExact(a, b);",
      "new": "return (FastMath.abs(a) > FastMath.abs(b)) ? FastMath.multiplyExact(b, a) : FastMath.multiplyExact(a, b);",
      "why": "hop 1 orders the factors by magnitude"},
     {"file": FM, "old": "return org.apache.commons.math.linear.BigMatrixImpl.longProduct(a, b);",
      "new": "return org.apache.commons.math.linear.BigMatrixImpl.longProduct(-b, -a);",
      "why": "hop 2 passes the negated factors, which have the same product"},
     {"file": BMI, "old": "return BlockRealMatrix.productOf(a, b);",
      "new": "return (b == -1) ? -a : BlockRealMatrix.productOf(a, b);",
      "why": "hop 3 negates the first factor directly when the second is -1"},
   ],
 },
 "host_notes": "The recipe's host pool for this checkout (classes of at least 1500 lines) is FastMath, MathUtils, "
               "BlockRealMatrix, BlockFieldMatrix and BigMatrixImpl. MathUtils is the target, so mr_lib preview (seed 5851, "
               "target org/apache/commons/math/util/MathUtils.java, n=5 and n=6) draws four hosts and stops with the pool "
               "exhausted: linear.BlockFieldMatrix (hop 1), util.FastMath (hop 2), linear.BigMatrixImpl (hop 3), "
               "linear.BlockRealMatrix (hop 4). Hops 1-4 use these hosts in that draw order. No fifth host exists at 1500 "
               "lines; the vendored generator's own remedy for a pool that is too small is to lower the minimum host size "
               "(host_search.pick_two_hosts: 'lower --min-host-lines'). The threshold was lowered to the largest value at which "
               "a fifth usable non-target class exists, 1237 lines, and the recipe's draw (stageB_lib.draw_hosts, seed 5851, "
               "the four drawn hosts excluded) returns linear.ArrayRealVector as the last remaining host: hop 5, the gold "
               "(1237 lines, the only host below 1500). Its anchor is the recipe's (seed 5955). None was skipped: all five are "
               "public concrete classes in which a static method compiles (BlockFieldMatrix is generic and BigMatrixImpl is "
               "deprecated; neither affects a static method). FastMath.java has no import statement, so hop 2 calls hop 3 by "
               "its fully-qualified name; the facade calls hop 1 by its fully-qualified name; hop 1 uses BlockFieldMatrix's "
               "existing FastMath import; hops 3, 4 and 5 share the linear package.",
}
