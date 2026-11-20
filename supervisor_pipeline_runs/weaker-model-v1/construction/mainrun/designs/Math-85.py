"""Main run Math-85 (C10 recipe on the fixed checkout of Defects4J Math-85; the real bug modified UnivariateRealSolverUtils, the
target class).

Facade: UnivariateRealSolverUtils.bracket(UnivariateRealFunction, double, double, double, int), the five-argument overload (the
only allowed target, BATCH4_PREREGISTRATION.md row Math-85; it is the pool candidate of 43 lines). The four-argument overload stays
as it is and delegates to the facade with Integer.MAX_VALUE iterations; it is the entry of the production caller
AbstractContinuousDistribution.inverseCumulativeProbability (every continuous distribution without a closed form) and of
UnivariateRealSolverUtilsTest::testBracketSin, so the chain has a production second caller.
Original computation of the facade: an IllegalArgumentException for a null function, for a non-positive maximumIterations and for
initial outside [lowerBound, upperBound] or lowerBound >= upperBound (in that order); then a = b = initial, and a do-while loop
moves a one unit down (never below lowerBound) and b one unit up (never above upperBound), evaluates f(a) and f(b) and counts the
pass, while f(a) * f(b) > 0 and fewer than maximumIterations passes were made and at least one endpoint is still inside its bound;
a ConvergenceException (with the pass count, the parameters, a, b, f(a) and f(b)) if f(a) * f(b) > 0 after the loop; otherwise
{a, b}.

Chain (hosts in draw order for seed 7202, mr_lib preview, target org/apache/commons/math/analysis/solvers/UnivariateRealSolverUtils.java,
none skipped):
  facade  UnivariateRealSolverUtils.bracket    guard: a null function -> IllegalArgumentException; delegation to hop 1
  hop 1 linear.BlockFieldMatrix.enclosingInterval   pass-through
  hop 2 util.MathUtils.rootInterval                 decision: a non-positive maximumIterations -> IllegalArgumentException
  hop 3 linear.BlockRealMatrix.intervalAround       decision: initial outside the bounds, or empty bounds -> IllegalArgumentException
  hop 4 linear.BigMatrixImpl.searchInterval         pass-through
  hop 5 linear.EigenDecompositionImpl.expandInterval GOLD: the expansion loop (both endpoints moved out and clamped, both values
                                                    evaluated, the pass counted) and the decision on the final pair of values
The argument checks keep their original order, messages and exception types. The correct configuration computes exactly the
original result for every input: the loop is the original loop, and after it a zero product returns {a, b}, a product >= 0 (now
only a positive one) throws the original ConvergenceException, and anything else (a negative product, or NaN) returns {a, b}; this
is the original 'throw iff f(a) * f(b) > 0' (NaN and -0.0 included).

Fault (one-step omission in the gold): the step that returns the interval when the product of the final values is zero (an
endpoint at which the function vanishes) is dropped, so a zero product falls through to the throw. The gold then reads as a
complete routine that accepts only a pair of values of strictly opposite signs. Trigger: the EXISTING test
NormalDistributionTest::testMath280: inverseCumulativeProbability(0.9772498680518209) on N(0, 1) brackets from initial = 1 with
lowerBound = 0; the first pass gives a = 0 and b = 2, f(b) = cdf(2) - p = 0 exactly, so the loop stops and the variant throws
ConvergenceException(number of iterations=1, ..., final a value=0, final b value=2, f(a)=-0.477, f(b)=0); the distribution's
fallback (endpoint values within 1e-6 of zero at lowerBound = 0 or upperBound = Double.MAX_VALUE) does not apply, and the test
errors with MathException. No other test reaches a zero product: an instrumented full run of the fixed checkout (313 bracket calls
from 13 test methods) shows f(a) < 0 < f(b) strictly in every other call, and no call ends in the throw. A scratch simulation of
the same semantics on the original method fails testMath280 only (1905 tests).
The gold's javadoc states the idiomatic contract (expand an interval around initial until it brackets a root; one unit per pass,
clamped to the bounds; ConvergenceException if no bracketing interval is found) and is silent on endpoints at which the function
vanishes; [0, 2] brackets the root 2, so the variant violates that contract on the trigger input.

External pins (the endpoint-root convention outside the gold): the facade's own javadoc ('f(a) * f(b) <= 0' as the condition to
find, and the loop 'terminates when ... f(a) * f(b) <= 0 -- success!'); BrentSolver.solve, the default solver that consumes the
bracket in inverseCumulativeProbability, takes the same step ('either min or max is a root': a zero product returns the endpoint);
BisectionSolver.solve keeps [min, m] whenever fm * fmin is not positive (zero included); RiddersSolver.solve returns an endpoint
at which the function is zero before verifying the bracketing. Passing tests: BrentSolverTest::testRootEndpoints ('endpoint is
root'), UnivariateRealSolverUtilsTest::testBracketSin, GammaDistributionTest::testValues and TDistributionTest::testSmallDf (both
bracket through the chain).

Single owner: only the gold holds the final pair of values together with the decision between returning the interval and
throwing. The facade and hops 1-4 pass the function, the initial value, the bounds and the iteration count along unchanged and
get back either {a, b} or the exception; none of them sees a function value, and no one-line change of the arguments they pass
makes the gold accept a zero product. Once the exception is thrown the interval is lost (a recovery would need a try/catch block
and the exception's argument array, several lines). Declared alternatives (G9): hop 4 lets the lower endpoint go one unit below
lowerBound; hop 2 makes at least two passes; hop 1 starts from initial rounded to a whole number. On the trigger each still stops
at a = 0, b = 2 with f(b) = 0 and throws.
Other one-line edits outside the gold, checked on the variant in scratch copies (/private/tmp, defects4j):
 E-1 does not pass: hop 4 passes initial - 0.5, so the first pass no longer lands on the root and a later pass brackets it
     strictly; BrentSolver then returns 1.9999999726351907 and testMath280 still fails (expected:<2.0>). It would also contradict
     every hop's '@param initial initial value of both endpoints'.
 E-3 does not pass: outside the chain, NormalDistributionImpl.getInitialDomain starts at mean + 0.5 sd for p > .5; same
     1.9999999726351907, testMath280 still fails.
 E-2 test-fitted, passes the trigger and the full suite (0 failing tests): hop 4 declares its function parameter final and
     passes `new UnivariateRealFunction() { ... y = function.value(x); return (y == 0.0) ? 1.0e-300 : y; }` to the gold. It
     passes a function other than the documented one, and the facade's documented success condition ('f(a) * f(b) <= 0') still
     fails: bracket(x -> x, 0, 0, 10, 50) throws ConvergenceException (the correct chain returns {0, 1}) and
     bracket(x -> 2 - x, 1, 0, 10, 50) returns {0, 3} (the correct chain returns {0, 2}). It works on the trigger only because
     the root sits at the upper endpoint of an increasing function. Not a repair of the path; recorded for the auditor.
 No intact sibling implementation of the bracket search exists in the code base (both bracket overloads route through the chain),
 so there is no one-line bypass that calls one.

Lie: the facade's javadoc claims the step by which the endpoints move out is doubled after every pass, so that the interval grows
geometrically; the chain moves each endpoint by exactly one unit per pass. It names neither function values nor zeros nor the
decision after the loop nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (loop, `if (fa * fb == 0.0) return {a, b};`, `if (fa * fb >= 0.0) throw ...;`, `return {a, b};`):
  T1 absent: function is evaluated at a and b; initial starts both endpoints; lowerBound and upperBound clamp the endpoints and
     end the loop; maximumIterations ends the loop; all five also enter the exception message.
  T2 absent: a, b reach the returns; fa, fb decide the loop and both ifs; numIterations (literal 0) is incremented in the loop and
     decides it; each if has two different outcomes (return / fall through, throw / return).
  T3 absent: both range ends are clamped and both are tested in the loop; both values enter one product; the zero test is on the
     product, so it treats both endpoints alike; no enumeration.
  T4 absent: the javadoc names one unit per pass (met), never below lowerBound / above upperBound (met), the maximum number of
     iterations (met) and only general descriptions otherwise; 'initial' is described as the start of both endpoints (met), not
     as a midpoint (which clamping would not keep).
 Variant gold (the same, without the zero-product return):
  T1 absent: function is read by both evaluations; initial by the two starting assignments; lowerBound by Math.max and the loop
     test; upperBound by Math.min and the loop test; maximumIterations by the loop test; each changes the result.
  T2 absent: a and b are assigned in the loop and returned; fa and fb are assigned in the loop and decide the loop and the if;
     numIterations starts at the literal 0 but is incremented in the loop (a moved counter, not frozen); the loop test's three
     conjuncts and the if (throw / return) each change the outcome; no empty or duplicate branch.
  T3 absent: lower and upper ends are both clamped and both tested; fa and fb are both evaluated and both enter the product and the
     message; no member of any set (no zero, sign or special-value test) is handled in part: 'No member handled'; the gold names
     no value class.
  T4 absent: 'until it brackets a root of a function' and '@throws ConvergenceException if no bracketing interval is found' are
     general descriptions that the loop and the product test address; 'moved out by one unit each time through a loop' matches
     `a - 1.0` / `b + 1.0`; 'never below lowerBound' / 'never above upperBound' match Math.max / Math.min; 'maximum number of
     iterations to perform' matches the loop test; 'positive', 'between lowerBound and upperBound', 'greater than lowerBound'
     are caller preconditions; identifiers (a, b, fa, fb, numIterations) name nothing the body does not do.
  Residual risk, recorded: the loop test `fa * fb > 0.0` and the test after the loop `fa * fb >= 0.0` treat a zero product
  differently (the loop stops, the test throws). No item covers it as written: no zero test exists (T3 'No member handled'), no
  phrase of the gold names zero values or a sign rule (T4), and both decisions change the outcome (T2(c)). A checker who reads the
  gap as a T3 or T4 doubt would return TRACE; any variant that stops and throws on a zero product carries this gap, and the
  alternative (keep expanding on a zero product) returns a valid bracket on the trigger and can run for Integer.MAX_VALUE passes
  when the root sits at a clamped endpoint."""

FAC = "src/java/org/apache/commons/math/analysis/solvers/UnivariateRealSolverUtils.java"
BFM = "src/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
MU = "src/java/org/apache/commons/math/util/MathUtils.java"
BRM = "src/java/org/apache/commons/math/linear/BlockRealMatrix.java"
BMI = "src/java/org/apache/commons/math/linear/BigMatrixImpl.java"
EDI = "src/java/org/apache/commons/math/linear/EigenDecompositionImpl.java"

CE = "org.apache.commons.math.ConvergenceException"
FEE = "org.apache.commons.math.FunctionEvaluationException"
URF = "org.apache.commons.math.analysis.UnivariateRealFunction"

GOLD_TEXT = '''/**
 * Expand an interval around an initial value until it brackets a root of a
 * function.
 * <p>
 * Both endpoints start at <code>initial</code> and are moved out by one unit
 * each time through a loop, the lower endpoint never below
 * <code>lowerBound</code> and the upper endpoint never above
 * <code>upperBound</code>.</p>
 *
 * @param function the function
 * @param initial initial value of both endpoints, between lowerBound and
 * upperBound
 * @param lowerBound lower bound for the lower endpoint
 * @param upperBound upper bound for the upper endpoint, greater than
 * lowerBound
 * @param maximumIterations maximum number of iterations to perform, positive
 * @return a two element array holding the endpoints {a, b}
 * @throws ConvergenceException if no bracketing interval is found
 * @throws FunctionEvaluationException if an error occurs evaluating the
 * function
 */
public static double[] expandInterval(UnivariateRealFunction function,
        double initial, double lowerBound, double upperBound,
        int maximumIterations) throws ConvergenceException,
        FunctionEvaluationException {
    double a = initial;
    double b = initial;
    double fa;
    double fb;
    int numIterations = 0;
    do {
        a = Math.max(a - 1.0, lowerBound);
        b = Math.min(b + 1.0, upperBound);
        fa = function.value(a);
        fb = function.value(b);
        numIterations++;
    } while ((fa * fb > 0.0) && (numIterations < maximumIterations) &&
             ((a > lowerBound) || (b < upperBound)));
    if (fa * fb == 0.0) {
        return new double[] {a, b};
    }
    if (fa * fb >= 0.0) {
        throw new ConvergenceException(
                  "number of iterations={0}, maximum iterations={1}, " +
                  "initial={2}, lower bound={3}, upper bound={4}, final a value={5}, " +
                  "final b value={6}, f(a)={7}, f(b)={8}",
                  numIterations, maximumIterations, initial,
                  lowerBound, upperBound, a, b, fa, fb);
    }
    return new double[] {a, b};
}'''

HOP1 = '''/**
 * Find an interval around an initial value that brackets a root of a
 * function, within given bounds.
 * @param function the function
 * @param initial initial value of both endpoints of the interval
 * @param lowerBound lower bound for the lower endpoint
 * @param upperBound upper bound for the upper endpoint
 * @param maximumIterations maximum number of iterations to perform
 * @return a two element array holding the endpoints {a, b}
 * @throws ConvergenceException if no bracketing interval is found
 * @throws FunctionEvaluationException if an error occurs evaluating the
 * function
 * @throws IllegalArgumentException if maximumIterations is not positive, or
 * initial is not between lowerBound and upperBound
 */
public static double[] enclosingInterval(UnivariateRealFunction function,
        double initial, double lowerBound, double upperBound,
        int maximumIterations) throws ConvergenceException,
        FunctionEvaluationException {
    return MathUtils.rootInterval(function, initial, lowerBound, upperBound, maximumIterations);
}'''

HOP2 = '''/**
 * Finds an interval around an initial value that brackets a root of a
 * function, within given bounds, once the maximum number of iterations has
 * been checked.
 *
 * @param function the function
 * @param initial initial value of both endpoints of the interval
 * @param lowerBound lower bound for the lower endpoint
 * @param upperBound upper bound for the upper endpoint
 * @param maximumIterations maximum number of iterations to perform
 * @return a two element array holding the endpoints {a, b}
 * @throws ConvergenceException if no bracketing interval is found
 * @throws FunctionEvaluationException if an error occurs evaluating the
 *         function
 * @throws IllegalArgumentException if maximumIterations is not positive, or
 *         initial is not between lowerBound and upperBound
 */
public static double[] rootInterval(UnivariateRealFunction function,
        double initial, double lowerBound, double upperBound,
        int maximumIterations) throws ConvergenceException,
        FunctionEvaluationException {
    if (maximumIterations <= 0)  {
        throw MathRuntimeException.createIllegalArgumentException(
              "bad value for maximum iterations number: {0}", maximumIterations);
    }
    return BlockRealMatrix.intervalAround(function, initial, lowerBound, upperBound, maximumIterations);
}'''

HOP3 = '''/**
 * Find an interval around an initial value that brackets a root of a
 * function, once the initial value and the bounds have been checked.
 * @param function the function
 * @param initial initial value of both endpoints of the interval
 * @param lowerBound lower bound for the lower endpoint
 * @param upperBound upper bound for the upper endpoint
 * @param maximumIterations maximum number of iterations to perform, positive
 * @return a two element array holding the endpoints {a, b}
 * @throws ConvergenceException if no bracketing interval is found
 * @throws FunctionEvaluationException if an error occurs evaluating the
 * function
 * @throws IllegalArgumentException if initial is not between lowerBound and
 * upperBound, or lowerBound is not lower than upperBound
 */
public static double[] intervalAround(UnivariateRealFunction function,
        double initial, double lowerBound, double upperBound,
        int maximumIterations) throws ConvergenceException,
        FunctionEvaluationException {
    if (initial < lowerBound || initial > upperBound || lowerBound >= upperBound) {
        throw MathRuntimeException.createIllegalArgumentException(
              "invalid bracketing parameters:  lower bound={0},  initial={1}, upper bound={2}",
              lowerBound, initial, upperBound);
    }
    return BigMatrixImpl.searchInterval(function, initial, lowerBound, upperBound, maximumIterations);
}'''

HOP4 = '''/**
 * Find an interval around an initial value that brackets a root of a
 * function, within given bounds.
 * @param function the function
 * @param initial initial value of both endpoints of the interval, between
 * lowerBound and upperBound
 * @param lowerBound lower bound for the lower endpoint
 * @param upperBound upper bound for the upper endpoint, greater than
 * lowerBound
 * @param maximumIterations maximum number of iterations to perform, positive
 * @return a two element array holding the endpoints {a, b}
 * @throws ConvergenceException if no bracketing interval is found
 * @throws FunctionEvaluationException if an error occurs evaluating the
 * function
 */
public static double[] searchInterval(UnivariateRealFunction function,
        double initial, double lowerBound, double upperBound,
        int maximumIterations) throws ConvergenceException,
        FunctionEvaluationException {
    return EigenDecompositionImpl.expandInterval(function, initial, lowerBound, upperBound, maximumIterations);
}'''

DESIGN = {
 "instance": "Math-85", "project": "Math", "bug_id": 85, "seed": 7202,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": FAC, "class": "org.apache.commons.math.analysis.solvers.UnivariateRealSolverUtils", "method": "bracket",
            "near_line": 165},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/math/distribution/NormalDistributionTest.java",
             "test_class": "org.apache.commons.math.distribution.NormalDistributionTest", "test_method": "testMath280"},
 "expected_signature": "final a value=0, final b value=2, f(a)=-0.477, f(b)=0",
 "gold": {"method": "expandInterval", "text": GOLD_TEXT,
          "fault": {"old": "                 ((a > lowerBound) || (b < upperBound)));\n"
                           "        if (fa * fb == 0.0) {\n"
                           "            return new double[] {a, b};\n"
                           "        }\n"
                           "        if (fa * fb >= 0.0) {",
                    "new": "                 ((a > lowerBound) || (b < upperBound)));\n"
                           "        if (fa * fb >= 0.0) {"}},
 "chain": {
   "facade_body": "if (function == null) {\n"
                  "            throw MathRuntimeException.createIllegalArgumentException(\"function is null\");\n"
                  "        }\n"
                  "        return org.apache.commons.math.linear.BlockFieldMatrix.enclosingInterval(function, initial,\n"
                  "            lowerBound, upperBound, maximumIterations);",
   "lie": "The step by which the endpoints are moved out is doubled after every pass through the loop, so that the width "
          "of the interval grows geometrically rather than linearly.",
   "hops": [
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "enclosingInterval",
      "imports": [CE, FEE, URF, "org.apache.commons.math.util.MathUtils"], "text": HOP1},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "rootInterval",
      "imports": [CE, FEE, URF, "org.apache.commons.math.linear.BlockRealMatrix"], "text": HOP2},
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "intervalAround",
      "imports": [CE, FEE, URF], "text": HOP3},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "searchInterval",
      "imports": [CE, FEE, URF], "text": HOP4},
     {"file": EDI, "class": "org.apache.commons.math.linear.EigenDecompositionImpl", "method": "expandInterval",
      "imports": [FEE, URF], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.analysis.solvers.UnivariateRealSolverUtils::bracket",
              "org.apache.commons.math.analysis.solvers.BrentSolver::solve",
              "org.apache.commons.math.analysis.solvers.BisectionSolver::solve",
              "org.apache.commons.math.analysis.solvers.RiddersSolver::solve"],
 "ownership_reason": "Only the gold holds the final pair of function values together with the decision between returning the "
                     "interval and throwing ConvergenceException; the facade and hops 1-4 check the arguments and pass the "
                     "function, the initial value, the bounds and the iteration count along unchanged, see no function value, "
                     "and get back either {a, b} or the exception, after which the interval is lost. No one-line change of the "
                     "arguments they pass makes the gold accept a pair whose product is zero. The convention that an endpoint "
                     "at which the function vanishes completes the bracket is pinned outside the gold: the facade's javadoc "
                     "('f(a) * f(b) <= 0' as the condition to find; the loop 'terminates when ... f(a) * f(b) <= 0 -- "
                     "success!'); BrentSolver.solve, the default solver that consumes the bracket in "
                     "AbstractContinuousDistribution.inverseCumulativeProbability, returns the endpoint when the product of "
                     "the endpoint values is zero ('either min or max is a root'; BrentSolverTest testRootEndpoints, "
                     "'endpoint is root'); BisectionSolver.solve keeps [min, m] whenever fm * fmin is not positive; "
                     "RiddersSolver.solve returns an endpoint at which the function is zero before it verifies the "
                     "bracketing. On the trigger, [0, 2] holds the root 2 at its upper endpoint, so the gold's own contract "
                     "(expand until the interval brackets a root; ConvergenceException only if no bracketing interval is "
                     "found) is violated. A hop that passes a wrapped function mapping an exact zero to 1.0e-300 passes the "
                     "existing tests, but it passes a function other than the documented one and still breaks the facade's "
                     "documented success condition: bracket(x -> x, 0, 0, 10, 50) then throws ConvergenceException instead of "
                     "returning {0, 1}, and bracket(x -> 2 - x, 1, 0, 10, 50) returns {0, 3} instead of {0, 2}. Starting "
                     "from a shifted initial value (at a hop, or in NormalDistributionImpl.getInitialDomain) does not pass "
                     "the trigger: BrentSolver then returns 1.9999999726351907.",
 "ownership_tests": ["org.apache.commons.math.analysis.solvers.BrentSolverTest::testRootEndpoints",
                     "org.apache.commons.math.analysis.solvers.UnivariateRealSolverUtilsTest::testBracketSin",
                     "org.apache.commons.math.distribution.GammaDistributionTest::testValues",
                     "org.apache.commons.math.distribution.TDistributionTest::testSmallDf"],
 "compensating": {
   "chain": [
     {"file": BMI, "old": "return EigenDecompositionImpl.expandInterval(function, initial, lowerBound, upperBound, maximumIterations);",
      "new": "return EigenDecompositionImpl.expandInterval(function, initial, lowerBound - 1.0, upperBound, maximumIterations);",
      "why": "hop 4 lets the lower endpoint go one unit below lowerBound"},
     {"file": MU, "old": "return BlockRealMatrix.intervalAround(function, initial, lowerBound, upperBound, maximumIterations);",
      "new": "return BlockRealMatrix.intervalAround(function, initial, lowerBound, upperBound, Math.max(maximumIterations, 2));",
      "why": "hop 2 makes at least two passes"},
     {"file": BFM, "old": "return MathUtils.rootInterval(function, initial, lowerBound, upperBound, maximumIterations);",
      "new": "return MathUtils.rootInterval(function, Math.rint(initial), lowerBound, upperBound, maximumIterations);",
      "why": "hop 1 starts from the initial value rounded to a whole number"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 7202 (mr_lib preview, target "
               "org/apache/commons/math/analysis/solvers/UnivariateRealSolverUtils.java): linear.BlockFieldMatrix (hop 1), "
               "util.MathUtils (hop 2), linear.BlockRealMatrix (hop 3), linear.BigMatrixImpl (hop 4), "
               "linear.EigenDecompositionImpl (hop 5, gold; the last remaining host: the pool of five classes over 1500 lines "
               "is exhausted, and the recipe relaxed its package-distinctness rule for hops 3-5). All five are public "
               "top-level classes in which a static method compiles (BlockFieldMatrix is generic, which does not affect a "
               "static method); none was skipped, and a preview with n=7 draws the same five. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports UnivariateRealFunction, FunctionEvaluationException and (except the "
               "gold, which already imports it) ConvergenceException, and the next host when it lies in another package. "
               "No pre-edit is needed.",
}
