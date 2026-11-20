"""Main run Math-61__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J Math-61,
a bug without a static facade; the real bug modified PoissonDistributionImpl, the facade's class). No static pair (B8 note section 1).

Facade: PoissonDistributionImpl.cumulativeProbability(int) (the only allowed candidate of batch8_tasks.json, BATCH8_PREREGISTRATION.md
row 295; facade_planned_by null, no facade reuse). Original computation: x < 0 gives 0; x == Integer.MAX_VALUE gives 1; otherwise
Gamma.regularizedGammaQ((double) x + 1, mean, epsilon, maxIterations), i.e. the regularized upper incomplete gamma function
Q(a, x') at a = x + 1, x' = mean, which Gamma computes as 1 - P(a, x') from the series of regularizedGammaP when x' < a + 1, and
otherwise as exp(-x' + a log x' - logGamma(a)) divided by the continued fraction with partial denominators 2n + 1 - a + x' and partial
numerators n(a - n) (evaluated by ContinuedFraction.evaluate, which rescales its intermediate results when they overflow).

facade_variant: V1 (state as parameters). The method reads three private fields (mean, epsilon, maxIterations) and writes none: the
facade keeps the original two guards, reads the fields inside its own class and passes the values with x to hop 1; there is no
write-back. The chain needs no method of the receiver (no V2), no private method of PoissonDistributionImpl is called (no V4), and no
package-private type is involved (no V3/V5). No signature, modifier, override or throws change; no new type (no anonymous
ContinuedFraction subclass either: the gold evaluates the fraction's recurrence itself); no reflection; no test edit.
state_passed: x and the private fields mean, epsilon, maxIterations (double, double, int values) to hop 1; no write-back.

Redistribution of the computation (one level below the facade's single call, the algorithm of Gamma.regularizedGammaQ): hop 1 turns
the count into the shape a = x + 1; hop 2 makes Gamma's regime decision (the series of P below a + 1 via the public
Gamma.regularizedGammaP, the continued fraction from a + 1 on); hop 3 applies the factor exp(-x + a log x - logGamma(a)) to the
fraction; hop 4 passes the arguments on; hop 5, the gold, evaluates the continued fraction (the per-term core: the partial numerators
and denominators, the convergent recurrence, the renormalisation of the recurrence terms, the convergence test).

reachability_probe (addendum section 4): in scratch copies of the fixture (/private/tmp/d4j-mi-Math-61-probe*/w) the first statement of
cumulativeProbability(int) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. `defects4j test -t
org.apache.commons.math.distribution.PoissonDistributionTest::testCumulativeProbabilities`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at PoissonDistributionImpl.cumulativeProbability(PoissonDistributionImpl.java:165) from
IntegerDistributionAbstractTest.verifyCumulativeProbabilities(IntegerDistributionAbstractTest.java:160).
`defects4j test -t org.apache.commons.math.distribution.PoissonDistributionTest::testCumulativeProbabilitySpecial`: 1 failing test,
PROBE-REACHED at PoissonDistributionImpl.java:165 from AbstractIntegerDistribution.cumulativeProbability(AbstractIntegerDistribution.java:71)
and PoissonDistributionTest.checkProbability(PoissonDistributionTest.java:193). Full suite with the probe
(defects4j test, 2218 tests): 7 failing tests, all in PoissonDistributionTest (testDegenerateInverseCumulativeProbability,
testCumulativeProbabilitySpecial, testLargeMeanInverseCumulativeProbability, testLargeMeanCumulativeProbability,
testInverseCumulativeProbabilities, testCumulativeProbabilities, testFloatingPointArguments); the random package tests are not in the
harness's test list. The trigger testCumulativeProbabilitySpecial reaches the facade directly (dist.cumulativeProbability(double) ->
AbstractIntegerDistribution.cumulativeProbability(double) -> cumulativeProbability(int)).

Hosts (host_mode = "1500"; `mr_lib.py preview Math-61 org/apache/commons/math/distribution/PoissonDistributionImpl.java 5`, seed 6838,
the seeded draw used in draw order, none substituted):
  hop 1 linear.BlockFieldMatrix 1636 lines  cumulativeCount         plumbing: the count becomes the shape a = x + 1
  hop 2 util.FastMath           3263 lines  regularizedUpperGamma   decision: 1 - P(a, x) from Gamma's series below a + 1, else hop 3
  hop 3 linear.BigMatrixImpl    1505 lines  upperGammaFromFraction  aggregation: exp(-x + a log x - logGamma(a)) / fraction
  hop 4 dfp.Dfp                 2398 lines  gammaFractionTerms      pass-through
  hop 5 util.MathUtils          1986 lines  evaluateGammaFraction   GOLD: the continued fraction of Q(a, x)
Host sizes 1636, 3263, 1505, 2398, 1986; the smallest host is BigMatrixImpl (1505 lines); the gold host has 1986 lines.

Correct configuration: equal to the original on every input the suite uses where the fraction needs no renormalisation (the same
recurrence, the same coefficients, the same factor; the convergence test stops at the same or an adjacent convergent within 1e-12
relative), so the mean-4 values of testCumulativeProbabilities / testFloatingPointArguments / testInverseCumulativeProbabilities
(tolerance 1e-12) are unchanged; where renormalisation is needed (a and mean of several thousand and above, x' - a below a few hundred)
the gold's renormalisation keeps the convergents exact up to rounding (the library's ContinuedFraction rescales p2/q2 against
unscaled p1/q1), e.g. Q's fraction at (9103, 9120) is 87.5399513 versus 87.5399508 in the library; the suite only requires those values
to be positive and not NaN. Checked in a scratch build: PoissonDistributionTest 12/12 passing.

Fault (one-step omission inside the gold's loop): the renormalisation of the recurrence terms is dropped. Without it the convergent
numerators and denominators overflow after about 110 terms whenever the fraction needs more terms than that (a and mean of several
thousand and above, close to each other); the numerator overflows first (the convergents are about 50-300), the next convergent is
+infinity, the relative test `|next - value| <= epsilon |next|` holds (inf <= inf) and the gold returns +infinity, so hop 3 returns
Q = 0. Trigger: the EXISTING test PoissonDistributionTest::testCumulativeProbabilitySpecial (JIRA MATH-282): for mean 9120 and
x = 9075 (a = 9076) the gold returns +infinity instead of 106.42, cumulativeProbability returns 0, and checkProbability's
assertTrue(p > 0) fails with "Zero cum probability returned for mean = 9120.0 x = 9075.0". It is the only test that newly fails:
the mean-4 tests and testLargeMeanCumulativeProbability (fractions of at most 20 terms) never reach the renormalisation;
testLargeMeanInverseCumulativeProbability does reach it (means 1e4 and 1e5), and the variant then gives 0 (overflow of the numerator)
or the last convergent (numerator and denominator overflowing together give a convergent that is not a number, and the gold returns the
convergent before it, as its javadoc states), never NaN and no exception, and that test asserts only the bisection's own invariant (p >= F(ret), p < F(ret + 1)) and the absence of a
MathException, which holds for any value the variant returns. Checked in a scratch build: PoissonDistributionTest 11 pass,
testCumulativeProbabilitySpecial fails with the signature above.

The gold's javadoc states the idiomatic contract (the value of the continued fraction of Q(a, x) with the stated partial numerators and
denominators, from the recurrence of its convergents, stopping when two successive convergents agree within epsilon or when a convergent
is not a number, returning the convergent before it in that case) and is silent on renormalisation; +infinity is not the value of a fraction that converges to 106.42. The convention is pinned outside the gold:
ContinuedFraction.evaluate (javadoc: the recurrence "can result in very large intermediate results which can result in numerical
overflow. As a means to combat these overflow conditions, the intermediate results are scaled whenever they threaten to become
numerically unstable"), which Gamma.regularizedGammaQ uses for exactly this fraction (getA = 2n + 1 - a + x, getB = n(a - n)) and
Beta.regularizedBeta uses for its own; passing tests ContinuedFractionTest::testGoldenRatio, GammaTest::testRegularizedGammaPositivePositive
and PoissonDistributionTest::testCumulativeProbabilities (the fraction's values at a = 1, 2, 3, x = 4 through this chain).

Single owner: only the gold builds the convergents; hops 1-4 never see a partial numerator or denominator, and the gold returns one
number. No one-line edit above the gold that keeps every hop's documentation restores the fraction's value: at the documented tolerance
(the field epsilon, 1e-12 by default) the overflow comes at term 108-113 on the four trigger inputs while two convergents first agree at
term 117-146 (a scratch simulation of the gold's recurrence); a caller cannot recover the value from +infinity, and maxIterations only
bounds the loop. Recorded non-repair (tolerance): an upper hop that passes a looser tolerance than it is given (e.g. hop 4 passing
epsilon * 1.0e6, i.e. 1e-6) makes the fraction stop at term 66-90, before the overflow, so the trigger and the suite pass; that edit
contradicts hop 4's javadoc ("to the relative tolerance epsilon", "@param epsilon the relative tolerance of the fraction") and the
facade's epsilon field (every Poisson probability then carries a relative error of order 1e-6 instead of 1e-12), and it hides the
omission rather than removing it: the gold still overflows whenever the fraction needs more than about 110 terms at that tolerance
(larger a and mean, e.g. a = x of order 1e6). Declared alternatives (G9): hop 2 moves the regime boundary to x <= a + 1; hop 4 passes a tighter tolerance; hop 3
computes the factor as exp(-x) x^a / Gamma(a) in three parts. Each leaves the trigger failing.
Recorded bypasses (replace the gold's result with another implementation, or make it dead): hop 2 (or hop 3) returning
Gamma.regularizedGammaQ(a, x, epsilon, maxIterations) (or 1 - Gamma.regularizedGammaP) for x >= a + 1, which makes hops 3-5 dead;
the facade's original body. Not repairs: an edit that only forces a positive result (e.g. hop 3 dividing by FastMath.min(fraction,
Double.MAX_VALUE), about 1e-311) satisfies the trigger's p > 0 but leaves Q off by some 300 orders of magnitude, against hop 3's and the
facade's documented values.

Lie: the facade's javadoc claims that the probabilities P(X = 0), ..., P(X = x) are computed one after another from exp(-mean) and
added up; the chain sums no probability masses (it evaluates the regularized gamma function by a series or a continued fraction). It
names neither renormalisation, overflow, the fraction, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: a and x set the first denominator x + 1 - a and every partial numerator/denominator; epsilon is the tolerance of the
     convergence test; maxIterations bounds the loop and is the exception's argument; no argument check exists.
  T2 absent: previousNumerator/previousDenominator are read by the recurrence and reassigned every term; numerator/denominator are read
     by the recurrence, the renormalisation and the convergent; value is read by the convergence test and returned on the undefined
     convergent; next is returned or becomes value; an, bn feed the recurrence; previousDenominator = 0.0 and denominator = 1.0 are
     reassigned every term; the loop index n advances; each decision returns a different value or changes all four terms.
  T3 absent: the renormalisation tests and scales both numerator and denominator and both previous terms (no pair half left out); the
     only special-value test is a NaN test of the convergent (one member of an unnamed set; the gold names no class such as "finite").
  T4 absent: the coefficients 2n + 1 - a + x and n(a - n) are the body's an and bn; "stops when two successive convergents agree within
     the relative tolerance epsilon" is the `|next - value| <= epsilon * |next|` return; "or when a convergent is not a number, in which
     case the convergent before it is returned" is `if (Double.isNaN(next)) { return value; }` (value holds the previous convergent);
     "@throws MaxIterationsExceededException if neither happens within maxIterations terms" is the throw after the loop, reached only when
     neither return was taken; "x at least a + 1" is a caller precondition.
 Variant gold (javadoc, signature, the recurrence over n = 1..maxIterations, the shift of the four terms, next = numerator / denominator,
 the NaN return of the last convergent, the convergence return, the throw):
  T1 absent: a and x enter numerator = x + 1 - a, an and bn; epsilon is the convergence tolerance; maxIterations bounds the loop and is
     thrown; all decide the return value.
  T2 absent: every local is read by the recurrence, a decision or a return and reassigned each term (previousNumerator,
     previousDenominator, numerator, denominator, value) or recomputed (an, bn, nextNumerator, nextDenominator, next); no literal-
     initialised local stays unassigned (previousDenominator = 0.0 and denominator = 1.0 are reassigned at n = 1); n advances; the NaN
     decision returns value, the convergence decision returns next, the fall-through continues.
  T3 absent: numerator and denominator get the same treatment everywhere (the same recurrence, the same shift, both enter next); no
     magnitude, sign or range treatment remains for either ("No member handled"); the only special-value test is NaN on the convergent,
     and the class the javadoc names ("not a number") is exactly that test, handled in full; the javadoc names no wider class (no
     "finite"); no enum, type code or named format.
  T4 absent: the javadoc names the coefficients (met by an, bn), the recurrence of the convergents (met), the two stopping rules (the
     relative test returns next; a convergent that is not a number returns value, the convergent before it), the throw "if neither
     happens within maxIterations terms" (met: the throw follows the loop and is reached only when neither return was taken), "@return the value of the continued fraction" (a general description, addressed by the returns);
     x "at least a + 1" and a "the a parameter" are caller preconditions; no inline comment; identifiers numerator, denominator,
     previous*, next, value name what they hold."""

PDI = "src/main/java/org/apache/commons/math/distribution/PoissonDistributionImpl.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"
BMI = "src/main/java/org/apache/commons/math/linear/BigMatrixImpl.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"

GOLD_TEXT = '''/**
 * Evaluates the continued fraction of the regularized upper incomplete
 * gamma function Q(a, x), whose n-th partial denominator is
 * <code>2n + 1 - a + x</code> and whose n-th partial numerator is
 * <code>n(a - n)</code>, from the recurrence of its convergents.
 * <p>
 * The evaluation stops when two successive convergents agree within the
 * relative tolerance <code>epsilon</code>, or when a convergent is not a
 * number, in which case the convergent before it is returned.</p>
 *
 * @param a the a parameter of the gamma function
 * @param x the value, at least <code>a + 1</code>
 * @param epsilon the relative tolerance between successive convergents
 * @param maxIterations the maximum number of terms of the fraction
 * @return the value of the continued fraction
 * @throws MaxIterationsExceededException if neither happens within
 * <code>maxIterations</code> terms
 */
public static double evaluateGammaFraction(double a, double x, double epsilon, int maxIterations)
    throws MaxIterationsExceededException {
    double previousNumerator = 1.0;
    double previousDenominator = 0.0;
    double numerator = x + 1.0 - a;
    double denominator = 1.0;
    double value = numerator;
    for (int n = 1; n <= maxIterations; n++) {
        final double an = 2.0 * n + 1.0 - a + x;
        final double bn = n * (a - n);
        final double nextNumerator = an * numerator + bn * previousNumerator;
        final double nextDenominator = an * denominator + bn * previousDenominator;
        previousNumerator = numerator;
        previousDenominator = denominator;
        numerator = nextNumerator;
        denominator = nextDenominator;
        if (FastMath.abs(numerator) > 1.0e150 || FastMath.abs(denominator) > 1.0e150) {
            previousNumerator *= 1.0e-150;
            previousDenominator *= 1.0e-150;
            numerator *= 1.0e-150;
            denominator *= 1.0e-150;
        }
        final double next = numerator / denominator;
        if (Double.isNaN(next)) {
            return value;
        }
        if (FastMath.abs(next - value) <= epsilon * FastMath.abs(next)) {
            return next;
        }
        value = next;
    }
    throw new MaxIterationsExceededException(maxIterations);
}'''

HOP1 = '''/**
 * Returns the probability P(X &le; x) of a Poisson count X with the given
 * mean, as the regularized upper incomplete gamma function Q(x + 1, mean).
 *
 * @param x the count
 * @param mean the Poisson mean
 * @param epsilon the convergence criterion of the gamma function
 * @param maxIterations the maximum number of iterations of the gamma function
 * @return P(X &le; x)
 * @throws MathException if the gamma function cannot be computed
 */
public static double cumulativeCount(int x, double mean, double epsilon, int maxIterations)
    throws MathException {
    return FastMath.regularizedUpperGamma((double) x + 1, mean, epsilon, maxIterations);
}'''

HOP2 = '''/**
 * Compute the regularized upper incomplete gamma function Q(a, x).
 * <p>
 * For x &lt; a + 1, Q(a, x) is computed as 1 - P(a, x) from the series of
 * the regularized gamma function P; otherwise it is computed from its
 * continued fraction.
 * </p>
 * @param a the a parameter
 * @param x the value
 * @param epsilon the convergence criterion of the series or the fraction
 * @param maxIterations the maximum number of iterations
 * @return Q(a, x)
 * @throws org.apache.commons.math.MathException if the series or the fraction cannot be computed
 */
public static double regularizedUpperGamma(double a, double x, double epsilon, int maxIterations)
    throws org.apache.commons.math.MathException {
    if (x < a + 1.0) {
        return 1.0 - org.apache.commons.math.special.Gamma.regularizedGammaP(a, x, epsilon, maxIterations);
    }
    return org.apache.commons.math.linear.BigMatrixImpl.upperGammaFromFraction(a, x, epsilon, maxIterations);
}'''

HOP3 = '''/**
 * Returns the regularized upper incomplete gamma function Q(a, x) from its
 * continued fraction: <code>exp(-x) x<sup>a</sup> / &Gamma;(a)</code>
 * divided by the value of the fraction.
 *
 * @param a the a parameter
 * @param x the value, at least <code>a + 1</code>
 * @param epsilon the convergence criterion of the fraction
 * @param maxIterations the maximum number of terms of the fraction
 * @return Q(a, x)
 * @throws MathException if the fraction cannot be evaluated
 */
public static double upperGammaFromFraction(double a, double x, double epsilon, int maxIterations)
    throws MathException {
    return FastMath.exp(-x + a * FastMath.log(x) - Gamma.logGamma(a)) /
           Dfp.gammaFractionTerms(a, x, epsilon, maxIterations);
}'''

HOP4 = '''/** Evaluate the continued fraction of the regularized upper incomplete
 * gamma function Q(a, x) to the relative tolerance epsilon.
 * @param a the a parameter
 * @param x the value, at least a + 1
 * @param epsilon the relative tolerance of the fraction
 * @param maxIterations the maximum number of terms of the fraction
 * @return the value of the continued fraction
 * @exception MathException if the fraction cannot be evaluated
 */
public static double gammaFractionTerms(double a, double x, double epsilon, int maxIterations)
    throws MathException {
    return MathUtils.evaluateGammaFraction(a, x, epsilon, maxIterations);
}'''

FAULT_OLD = ("            denominator = nextDenominator;\n"
             "            if (FastMath.abs(numerator) > 1.0e150 || FastMath.abs(denominator) > 1.0e150) {\n"
             "                previousNumerator *= 1.0e-150;\n"
             "                previousDenominator *= 1.0e-150;\n"
             "                numerator *= 1.0e-150;\n"
             "                denominator *= 1.0e-150;\n"
             "            }\n"
             "            final double next = numerator / denominator;\n")
FAULT_NEW = ("            denominator = nextDenominator;\n"
             "            final double next = numerator / denominator;\n")

DESIGN = {
 "instance": "Math-61", "project": "Math", "bug_id": 61, "seed": 6838,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": PDI, "class": "org.apache.commons.math.distribution.PoissonDistributionImpl", "method": "cumulativeProbability",
            "near_line": 164},
 "facade_variant": "V1",
 "state_passed": "x and the private fields mean, epsilon, maxIterations (double, double, int values) to hop 1; no field written, "
                 "no write-back",
 "host_mode": "1500",
 "reachability_probe": "testCumulativeProbabilities fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "PoissonDistributionImpl.cumulativeProbability(PoissonDistributionImpl.java:165) from "
                       "IntegerDistributionAbstractTest.java:160; full suite with the probe: 7 failing tests, all in "
                       "PoissonDistributionTest, including the trigger testCumulativeProbabilitySpecial",
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/distribution/PoissonDistributionTest.java",
             "test_class": "org.apache.commons.math.distribution.PoissonDistributionTest",
             "test_method": "testCumulativeProbabilitySpecial"},
 "expected_signature": "Zero cum probability returned for mean = 9120.0 x = 9075.0",
 "gold": {"method": "evaluateGammaFraction", "text": GOLD_TEXT, "fault": {"old": FAULT_OLD, "new": FAULT_NEW}},
 "chain": {
   "facade_body": "if (x < 0) {\n"
                  "            return 0;\n"
                  "        }\n"
                  "        if (x == Integer.MAX_VALUE) {\n"
                  "            return 1;\n"
                  "        }\n"
                  "        return org.apache.commons.math.linear.BlockFieldMatrix.cumulativeCount(x, mean, epsilon, maxIterations);",
   "lie": "The probabilities P(X = 0), P(X = 1), ..., P(X = x) are computed one after another, starting from "
          "P(X = 0) = exp(-mean), and added up in that order.",
   "hops": [
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "cumulativeCount",
      "imports": ["org.apache.commons.math.MathException"], "text": HOP1},
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "regularizedUpperGamma",
      "imports": [], "text": HOP2},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "upperGammaFromFraction",
      "imports": ["org.apache.commons.math.MathException", "org.apache.commons.math.dfp.Dfp",
                  "org.apache.commons.math.special.Gamma", "org.apache.commons.math.util.FastMath"], "text": HOP3},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "gammaFractionTerms",
      "imports": ["org.apache.commons.math.MathException", "org.apache.commons.math.util.MathUtils"], "text": HOP4},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "evaluateGammaFraction",
      "imports": ["org.apache.commons.math.MaxIterationsExceededException"], "gold": True},
   ],
 },
 "pre_edits": {"chain": [
   {"file": PDI, "old": "     * The probability distribution function P(X <= x) for a Poisson\n     * distribution.\n",
    "new": "     * The probability distribution function P(X <= x) for a Poisson\n"
           "     * distribution. The probabilities P(X = 0), P(X = 1), ..., P(X = x) are\n"
           "     * computed one after another, starting from P(X = 0) = exp(-mean), and\n"
           "     * added up in that order.\n"},
 ]},
 "evidence": ["org.apache.commons.math.util.ContinuedFraction::evaluate",
              "org.apache.commons.math.special.Gamma::regularizedGammaQ",
              "org.apache.commons.math.special.Beta::regularizedBeta"],
 "ownership_reason": "Only the gold builds the convergents of the continued fraction of Q(a, x); hops 1-4 never see a partial "
                     "numerator or denominator (hop 1 forms the shape x + 1, hop 2 chooses between the series of P and the "
                     "fraction at a + 1, hop 3 divides exp(-x + a log x - logGamma(a)) by the fraction's value, hop 4 passes "
                     "the arguments on). The gold's javadoc promises the value of the continued fraction from the recurrence of "
                     "its convergents; on the trigger input (a = 9076, x = 9120) the fraction's value is 106.42 and the gold "
                     "returns +infinity, because the recurrence terms overflow after about 110 terms while the convergents need "
                     "117-146 to agree at the documented tolerance (the field epsilon, 1e-12 by default); a looser tolerance "
                     "passed by an upper hop would contradict that hop's and the facade's documented tolerance and only hides "
                     "the omission for larger arguments, and no caller can recover the value from +infinity. The convention that the recurrence's "
                     "intermediate results are rescaled is pinned outside the gold by ContinuedFraction.evaluate (its javadoc: "
                     "the intermediate results 'are scaled whenever they threaten to become numerically unstable'), which "
                     "Gamma.regularizedGammaQ uses for exactly this fraction (getA = 2n + 1 - a + x, getB = n(a - n)) and "
                     "Beta.regularizedBeta for its own; ContinuedFractionTest testGoldenRatio, GammaTest "
                     "testRegularizedGammaPositivePositive and PoissonDistributionTest testCumulativeProbabilities (the fraction's "
                     "values at a = 1, 2, 3 and x = 4 through this chain) pass.",
 "ownership_tests": ["org.apache.commons.math.util.ContinuedFractionTest::testGoldenRatio",
                     "org.apache.commons.math.special.GammaTest::testRegularizedGammaPositivePositive",
                     "org.apache.commons.math.distribution.PoissonDistributionTest::testCumulativeProbabilities"],
 "compensating": {
   "chain": [
     {"file": FM, "old": "if (x < a + 1.0) {",
      "new": "if (x <= a + 1.0) {",
      "why": "hop 2 moves the regime boundary so that x == a + 1 uses the series"},
     {"file": DFP, "old": "return MathUtils.evaluateGammaFraction(a, x, epsilon, maxIterations);",
      "new": "return MathUtils.evaluateGammaFraction(a, x, epsilon * 1.0e-3, maxIterations);",
      "why": "hop 4 passes a tighter tolerance to the fraction"},
     {"file": BMI, "old": "return FastMath.exp(-x + a * FastMath.log(x) - Gamma.logGamma(a)) /",
      "new": "return FastMath.exp(-x) * FastMath.pow(x, a) / FastMath.exp(Gamma.logGamma(a)) /",
      "why": "hop 3 computes the factor exp(-x) x^a / Gamma(a) in three parts"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are the recipe's seeded draw `mr_lib.py preview Math-61 "
               "org/apache/commons/math/distribution/PoissonDistributionImpl.java 5` (seed 6838; the facade's file is excluded), "
               "used in draw order, none substituted: linear.BlockFieldMatrix (hop 1, 1636 lines), util.FastMath (hop 2, 3263), "
               "linear.BigMatrixImpl (hop 3, 1505; the smallest host), dfp.Dfp (hop 4, 2398), util.MathUtils (hop 5, gold, 1986). "
               "All five are public top-level classes in which a public static method compiles (BlockFieldMatrix is generic: the "
               "facade calls the static hop through the raw class name; BigMatrixImpl is deprecated, which does not affect a static "
               "method). Anchors from the preview (stageB_lib.pick_insertion_anchor, seed 6838 + 100 + i): hop 1 after "
               "`setRowMatrix` (line 941), hop 2 after `cosh` (228), hop 3 after `getScale` (558), hop 4 after `newInstance` "
               "(576), hop 5 after `addAndCheck` (107). FastMath has no import statements, so hop 2 names Gamma, BigMatrixImpl "
               "and MathException by their fully-qualified names; the facade calls hop 1 by its fully-qualified name; the other "
               "hops import what they call. The facade's class PoissonDistributionImpl is not a host. The facade carries "
               "@Override between its javadoc and its header, so the recipe's rewrite_facade finds no adjacent javadoc and "
               "appends nothing; the lie (the same sentence as chain.lie) is therefore placed by a behaviour-preserving pre_edit "
               "as the second sentence of the facade's javadoc description. The facade's file keeps its import of Gamma "
               "(still named in the javadoc of the field maxIterations).",
}
