"""Main run Math-94, cell C10f (batch 6): the C10 recipe with fallback hosts on the fixed checkout of Defects4J Math-94 (the real
bug modified MathUtils, the target class).

Facade: MathUtils.factorialLog(int) (allowed target, BATCH6_PREREGISTRATION.md row Math-94; no facade reuse).
Original computation: throw IllegalArgumentException if n < 0; otherwise return the sum of Math.log(i) for i = 2..n.
Callers: MathUtils.factorialDouble (floor(exp(factorialLog(n)) + 0.5)), hence MathUtils.factorial (Math.round of factorialDouble,
ArithmeticException when that saturates at Long.MAX_VALUE) and PoissonDistributionImpl.probability.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2), on a scratch copy of the fixture, before any design:
  factorialLog's first statement made `throw new IllegalStateException("PROBE-REACHED");`, compiled, and run with
  `defects4j test -t MathUtilsTest::testFactorial` (fails, PROBE-REACHED), `-t MathUtilsTest::testFactorialFail` (fails,
  PROBE-REACHED) and the full suite: exactly 3 failing tests, all with PROBE-REACHED: MathUtilsTest::testFactorial,
  MathUtilsTest::testFactorialFail, PoissonDistributionTest::testDensities. Facade usable.
  The other allowed targets were probed the same way (full suite each): binomialCoefficientLog is reached by 18 tests
  (MathUtilsTest 3, Binomial/Pascal/Hypergeometric distribution tests 15); addAndCheck(int,int) by 15 (MathUtilsTest::testAddAndCheck,
  FractionTest::testAdd, 13 Adams integrator tests through Fraction); addAndCheck(long,long) by 1 (MathUtilsTest::testAddAndCheckLong).
Why not the other targets: binomialCoefficientLog's loops serve the Hypergeometric tests with n up to 26896 at relative tolerance
1e-9 and its degenerate cases with (0,0), so every omission in its loops fails several tests, and its shortcuts (n == k, k == 0,
k == 1, k == n - 1) agree with the loops up to rounding that every test tolerates: no single-trigger fault. addAndCheck(int,int):
its overflow test is exercised by testAddAndCheck and FractionTest::testAdd alike, and dropping one bound leaves a one-of-two range
end (T3b). addAndCheck(long,long): every one-line omission in its sign and overflow case analysis leaves one of the two range ends
checked (T3b) or an asymmetric sign analysis (T3a); dropping the whole check leaves a bare `return a + b` whose one step any hop
could re-add with a and b in hand (no unique owner).

Hosts: host_mode = largest5 (only 2 other public classes reach 1500 lines). The five hosts are exactly hosts_hop_order of the task
record, the five largest public non-interface non-enum classes other than MathUtils, in that order, no substitution:
  hop 1 linear.EigenDecompositionImpl  1832 lines   pass-through
  hop 2 linear.DenseRealMatrix         1621 lines   placement: 0! = 1! = 1, so n < 2 gives 0 (the empty sum of the original)
  hop 3 linear.BigMatrixImpl           1499 lines   pass-through
  hop 4 linear.RealVectorImpl          1407 lines   pass-through
  hop 5 linear.AbstractRealMatrix      1244 lines   GOLD: the per-factor core, the sum of logarithms over the factors 2..n
Smallest host 1244 lines (the gold host). Anchors (stageB_lib.pick_anchor, seed 7228 + 100 + i): see host_notes.

Chain and correct configuration: the facade keeps its argument guard and calls hop 1. The gold forms the original sum of
logarithms with the factors grouped: each factor is multiplied into an exact long partial product, and before the next factor
would take the partial product beyond Long.MAX_VALUE the partial product's logarithm is added to the sum and the product restarts
at 1 (the long range that MathUtils.factorial's own javadoc documents: 20! is the largest factorial below Long.MAX_VALUE). This is
the same logarithmic sum, grouped differently: for n <= 20 it is log((double) n!) exactly (the original rounds once per factor), and
for every n <= 171 it is within 3.4e-13 of the original (relative 5e-16); every test passes on it (G1).

Fault (omission of a state reset inside the gold's iteration): the line `product = 1;` after the partial product has been added to
the sum is dropped. For n <= 20 the restart never happens, so every result is unchanged (testFactorial, n = 0..9, and
PoissonDistributionTest::testDensities, factorials up to 20!, still pass). For n >= 21 the partial product's logarithm is added and
the product keeps growing: 20! * 21 exceeds the long range and wraps to a negative value, so logFactorial(21) is NaN.
factorialDouble(21) is then NaN and factorial(21) = Math.round(NaN) = 0 instead of an ArithmeticException. Trigger: the EXISTING
test MathUtilsTest::testFactorialFail: its first three assertions (negative arguments, all rejected before the chain or by the
facade guard) pass, and `MathUtils.factorial(21); fail("expecting ArithmeticException")` fails with
junit.framework.AssertionFailedError: expecting ArithmeticException (its last assertion, factorialDouble(171) infinite, would fail
too: the variant gives -Infinity there, so factorialDouble(171) = 0). It is the only test that passes an argument above 20 to the
chain (probe above: the other two reaching tests use n <= 9 and n <= 20). The gold's javadoc states the idiomatic contract (the
natural logarithm of n!) and is silent on the long range and the restart; NaN is not log(21!), so the variant violates that contract
on the trigger input.

External pins (convention outside the gold): MathUtils.factorial documents that 21! exceeds the long range ('The largest value of n
for which n! < Long.MAX_VALUE is 20 ... an ArithMeticException is thrown') and factorialDouble that n! up to 170! is finite and above
it is +Infinity; both hold only if the logarithm is right for n > 20. MathUtils.mulAndCheck(long, long) refuses a long product that
leaves the long range instead of wrapping (MathUtilsTest::testMulAndCheckLong). The sibling MathUtils.binomialCoefficientLog sums
the logarithms of the factors of n!/(k!(n-k)!) and stays finite and accurate for large n (MathUtilsTest::testBinomialCoefficientFail:
1030 choose 515 is still +Infinity only after exponentiation, 67 choose 34 still exceeds the long range). Passing tests through
the chain pin the small-argument behaviour (testFactorial, PoissonDistributionTest::testDensities).

Single owner: only the gold sees the individual factors and the partial product; hops 1-4 hold n alone and get one double back.
Once the product has wrapped, the NaN (or, for larger n, -Infinity or a finite value unrelated to n!) cannot be turned back into
log(n!) by any caller, and no argument a hop can pass makes the gold correct for n > 20: the gold is the only use of the factors.
Declared alternatives (G9): hop 4 peels off the last factor (logFactorial(n - 1) + log n), hop 2 maps n > 170 to +Infinity, hop 1
maps a NaN result to +Infinity; each still fails the trigger (checked on the variant in a scratch copy: trigger 1 failing, full
suite only the trigger). Recorded bypasses (one-line edits above the gold that pass the trigger and the full suite by replacing the
gold's result with another implementation; each checked at hop 4 on the variant in a scratch copy: trigger 0 failing, full suite
0 failing):
 B-0 the facade or any of hops 1-4 returns org.apache.commons.math.special.Gamma.logGamma(n + 1.0) (another implementation of
     log n!), discarding the rest of the chain including the gold.
 B-1 a hop sums the logarithms itself, e.g. hop 4
     `double logSum = 0; for (int i = 2; i <= n; i++) { logSum += Math.log((double) i); } return logSum;` (the original body),
     making the gold dead.
 B-2 a hop keeps the gold only for n <= 20 and hands larger arguments to another implementation, e.g. hop 4
     `return n > 20 ? org.apache.commons.math.special.Gamma.logGamma(n + 1.0) : AbstractRealMatrix.logFactorial(n);`: on the
     trigger input the gold's output is not used.
 B-3 a hop adds the logarithm of each factor above a cut-off itself, recursing on n - 1, e.g. hop 4
     `return n > 20 ? logFactorialValue(n - 1) + Math.log((double) n) : AbstractRealMatrix.logFactorial(n);` (also passes with
     cut-off 10). This moves the gold's per-factor sum into the hop: the cut-off is free, and with cut-off 1 the gold contributes
     only log 1! = 0; it is a second implementation of the gold's core, and the gold still returns NaN for log(21!) against its own
     documented contract. A bypass, not a repair of the path.

Lie: the facade's javadoc claims the logarithm is evaluated from Stirling's series for the logarithm of the Gamma function at n + 1,
truncated after its third correction term; nothing on the path evaluates a series or the Gamma function (the chain multiplies and
takes logarithms of exact integers). It names neither the long range nor the restart nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: n is the loop bound, so it decides how many factors enter the sum and the product.
  T2 absent: logSum is reassigned in the loop (+=) and returned; product is reassigned (= 1, *= i) and returned through its
     logarithm; i is advanced by the for header; the if adds to logSum and restarts product, so it decides live statements.
  T3 absent: no enumeration, pair, range end, named class or set of parallel cases; one decision with one treatment.
  T4 absent: the javadoc says 'the natural logarithm of the factorial of an integer' and '@return the natural logarithm of n!'
     (general descriptions the loop and the return address) and '@param n argument, must be non-negative' (a caller
     precondition); no comment; identifiers logSum, product, i name nothing the body does not do.
 Variant gold (javadoc, signature, `double logSum = 0; long product = 1; for (int i = 2; i <= n; i++) { if (product >
 Long.MAX_VALUE / i) { logSum += Math.log((double) product); } product *= i; } return logSum + Math.log((double) product);`):
  T1 absent: n is the loop bound and changes the returned value.
  T2 absent: logSum is assigned inside the loop and reaches the return; product is assigned inside the loop (product *= i) and
     reaches the return; neither is a literal-initialised local that is never reassigned, and no cursor, counter, flag or
     best-so-far is left unassigned; the if decides whether logSum is updated, so it is not a dead decision.
  T3 absent: still no set: no case, pair, range end or named value class has one member treated and a sibling left out.
  T4 absent: unchanged javadoc; it names no limit, bound, value class, case or property that the body visibly fails to meet; the
     precondition on n is a caller precondition; no comment.
"""

MU = "src/java/org/apache/commons/math/util/MathUtils.java"
EDI = "src/java/org/apache/commons/math/linear/EigenDecompositionImpl.java"
DRM = "src/java/org/apache/commons/math/linear/DenseRealMatrix.java"
BMI = "src/java/org/apache/commons/math/linear/BigMatrixImpl.java"
RVI = "src/java/org/apache/commons/math/linear/RealVectorImpl.java"
ARM = "src/java/org/apache/commons/math/linear/AbstractRealMatrix.java"

GOLD_TEXT = '''/**
 * Returns the natural logarithm of the factorial of an integer.
 *
 * @param n argument, must be non-negative
 * @return the natural logarithm of n!
 */
public static double logFactorial(final int n) {
    double logSum = 0;
    long product = 1;
    for (int i = 2; i <= n; i++) {
        if (product > Long.MAX_VALUE / i) {
            logSum += Math.log((double) product);
            product = 1;
        }
        product *= i;
    }
    return logSum + Math.log((double) product);
}'''

HOP1 = '''/**
 * Return the natural logarithm of n!.
 * @param n argument, must be non-negative
 * @return the natural logarithm of n!
 */
public static double factorialLogarithm(final int n) {
    return DenseRealMatrix.logOfFactorial(n);
}'''

HOP2 = '''/**
 * Returns the natural logarithm of the factorial of an integer.
 * <p>0! and 1! are both 1, so their logarithm is 0.</p>
 * @param n argument, must be non-negative
 * @return the natural logarithm of n!
 */
public static double logOfFactorial(final int n) {
    if (n < 2) {
        return 0.0;
    }
    return BigMatrixImpl.lnFactorial(n);
}'''

HOP3 = '''/**
 * Returns the natural logarithm of n!.
 * @param n argument, must be non-negative
 * @return the natural logarithm of n!
 */
public static double lnFactorial(final int n) {
    return RealVectorImpl.logFactorialValue(n);
}'''

HOP4 = '''/**
 * Returns the natural logarithm of the factorial of an integer.
 * @param n argument, must be non-negative
 * @return the natural logarithm of n!
 */
public static double logFactorialValue(final int n) {
    return AbstractRealMatrix.logFactorial(n);
}'''

DESIGN = {
 "instance": "Math-94", "project": "Math", "bug_id": 94, "seed": 7228,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "factorialLog", "near_line": 387},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/math/util/MathUtilsTest.java",
             "test_class": "org.apache.commons.math.util.MathUtilsTest", "test_method": "testFactorialFail"},
 "expected_signature": "AssertionFailedError: expecting ArithmeticException",
 "gold": {"method": "logFactorial", "text": GOLD_TEXT,
          "fault": {"old": "            if (product > Long.MAX_VALUE / i) {\n"
                           "                logSum += Math.log((double) product);\n"
                           "                product = 1;\n"
                           "            }",
                    "new": "            if (product > Long.MAX_VALUE / i) {\n"
                           "                logSum += Math.log((double) product);\n"
                           "            }"}},
 "chain": {
   "facade_body": "if (n < 0) {\n"
                  "            throw new IllegalArgumentException(\"must have n > 0 for n!\");\n"
                  "        }\n"
                  "        return org.apache.commons.math.linear.EigenDecompositionImpl.factorialLogarithm(n);",
   "lie": "The logarithm is evaluated from Stirling's series for the logarithm of the Gamma function at n + 1, "
          "truncated after its third correction term.",
   "hops": [
     {"file": EDI, "class": "org.apache.commons.math.linear.EigenDecompositionImpl", "method": "factorialLogarithm",
      "imports": [], "text": HOP1},
     {"file": DRM, "class": "org.apache.commons.math.linear.DenseRealMatrix", "method": "logOfFactorial",
      "imports": [], "text": HOP2},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "lnFactorial",
      "imports": [], "text": HOP3},
     {"file": RVI, "class": "org.apache.commons.math.linear.RealVectorImpl", "method": "logFactorialValue",
      "imports": [], "text": HOP4},
     {"file": ARM, "class": "org.apache.commons.math.linear.AbstractRealMatrix", "method": "logFactorial",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.util.MathUtils::factorial",
              "org.apache.commons.math.util.MathUtils::mulAndCheck",
              "org.apache.commons.math.util.MathUtils::binomialCoefficientLog"],
 "ownership_reason": "Only the gold sees the individual factors of n! and the partial product it multiplies them into; hops 1-4 "
                     "hold n alone and get one double back. Once the partial product has left the long range it wraps, the "
                     "result is NaN (or -Infinity, or a finite value unrelated to n!), and no caller can turn it back into "
                     "log(n!); no argument a hop can pass makes the gold right for n > 20, since the gold is the only use of the "
                     "factors. The convention is pinned outside the gold: MathUtils.factorial documents that 20! is the largest "
                     "factorial below Long.MAX_VALUE and that a larger result raises an ArithmeticException, and "
                     "factorialDouble that n! is finite up to 170!, both of which hold only if the logarithm is right above 20 "
                     "(they are computed from it); MathUtils.mulAndCheck(long, long) refuses a long product that leaves the "
                     "long range instead of wrapping (testMulAndCheckLong); the sibling MathUtils.binomialCoefficientLog sums "
                     "the logarithms of the factors and stays accurate for large arguments (testBinomialCoefficientFail). "
                     "testFactorial and PoissonDistributionTest.testDensities pass through the chain with factorials up to 20!. "
                     "One-line edits above the gold that pass the suite do so by computing the logarithms of the factors "
                     "themselves (Gamma.logGamma(n + 1.0), the original summation loop, or a hop that adds Math.log(n) and "
                     "recurses on n - 1 down to a cut-off, below which it calls the gold; with cut-off 1 the gold contributes "
                     "only log 1! = 0): each is a second implementation of the gold's per-factor sum and leaves the gold "
                     "returning NaN for log(21!) against its own documented contract, i.e. a bypass, not a repair.",
 "ownership_tests": ["org.apache.commons.math.util.MathUtilsTest::testFactorial",
                     "org.apache.commons.math.distribution.PoissonDistributionTest::testDensities",
                     "org.apache.commons.math.util.MathUtilsTest::testMulAndCheckLong",
                     "org.apache.commons.math.util.MathUtilsTest::testBinomialCoefficientFail"],
 "compensating": {
   "chain": [
     {"file": RVI, "old": "return AbstractRealMatrix.logFactorial(n);",
      "new": "return AbstractRealMatrix.logFactorial(n - 1) + Math.log((double) n);",
      "why": "hop 4 peels off the last factor and adds its logarithm"},
     {"file": DRM, "old": "return BigMatrixImpl.lnFactorial(n);",
      "new": "return n > 170 ? Double.POSITIVE_INFINITY : BigMatrixImpl.lnFactorial(n);",
      "why": "hop 2 maps arguments whose factorial exceeds the double range to infinity"},
     {"file": EDI, "old": "return DenseRealMatrix.logOfFactorial(n);",
      "new": "final double logValue = DenseRealMatrix.logOfFactorial(n); return Double.isNaN(logValue) ? Double.POSITIVE_INFINITY : logValue;",
      "why": "hop 1 maps a NaN logarithm to infinity"},
   ],
 },
 "host_notes": "host_mode largest5 (2 other public classes reach 1500 lines): the five hosts are exactly hosts_hop_order of the "
               "task record, the five largest public non-interface non-enum classes other than MathUtils by newline count: "
               "linear.EigenDecompositionImpl 1832 (hop 1), linear.DenseRealMatrix 1621 (hop 2), linear.BigMatrixImpl 1499 "
               "(hop 3), linear.RealVectorImpl 1407 (hop 4), linear.AbstractRealMatrix 1244 (hop 5, gold; smallest host). "
               "Anchors by stageB_lib.pick_anchor with seed 7228 + 100 + i (as mr2_spec inserts them): after getEigenvector "
               "(line idx 346, seed 7328), after setRowMatrix (940, 7329), after getScale (540, 7330), after mapUlp (768, "
               "7331), after copySubMatrix (359, 7332); every anchor is an outer-class member. All five are public top-level "
               "classes in which a static method compiles (AbstractRealMatrix is abstract, which does not affect a static "
               "method); none was skipped or substituted. All five share the package org.apache.commons.math.linear, so the "
               "hops call each other by simple name with no import; the facade (util.MathUtils) calls hop 1 by its "
               "fully-qualified name.",
}
