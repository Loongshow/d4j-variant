"""Main run Math-103__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade; the
fixed checkout of Defects4J Math-103, whose real bug modified NormalDistributionImpl, the facade's class). No static pair (B8 note
section 1).

Facade: NormalDistributionImpl.cumulativeProbability(double) (the only allowed candidate of the task record, BATCH8_PREREGISTRATION.md
row 304; facade_planned_by = Math-60__i, so this is a recorded facade reuse: no other candidate exists; nothing of that task was
opened). Original computation: P(X < x) = 0.5 * (1 + erf((x - mean) / (standardDeviation * sqrt 2))) with Erf.erf; if Erf.erf throws
MaxIterationsExceededException (its series overflows for a standard score beyond about 37.7), the value is top-coded: 0 when x is more
than 20 standard deviations below the mean, 1 when more than 20 above, and the exception is rethrown otherwise.

facade_variant: V1 (state as parameters). state_passed: the argument x (as a one-element array) and the private fields mean and
standardDeviation (read directly, as the original body does), handed to hop 1; no field is written, no write-back. The facade body
is one call to hop 1 (the original has no argument guard) and takes element 0 of the returned array. No visibility is widened, no
type is added, no signature, modifier, override or throws clause changes (it still declares MathException), no reflection, no test
edit. No private method of the class is called by the original body (no V4); no package-private type is involved (no V3/V5).

Redistribution of the computation: the chain evaluates the normal distribution function at each point of an array (the facade passes
one point). Hop 1 expresses each point as its standard score (point - mean) / sd; hop 2 creates the array of probabilities; hops 3
and 4 pass the scores and the array along; the gold (hop 5) computes, for each standard score, the standard normal probability
0.5 * (1 + erf(z / sqrt 2)), giving a score beyond 20 in magnitude the probability 0 (below) or 1 (above) without evaluating the error
function. The correct configuration equals the original on every test input: within 20 standard deviations both evaluate the same
formula (the score is formed as ((x - mean) / sd) / sqrt 2 instead of (x - mean) / (sd * sqrt 2), a difference of an ulp or so);
beyond 37.7 both top-code; between 20 and 37.7 the original evaluates the formula, whose series result lies within 6e-14 of 0 or 1
(checked at every half step from 20 to 37.5; it even falls slightly below 0 or above 1 there), where the chain writes 0 or 1. No test
evaluates that range except testExtremeValues, whose bounds (< 1e-5, > 0.99999) both satisfy.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-103-probe of the fixture, the first statement
of cumulativeProbability(double) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.math.distribution.NormalDistributionTest::testExtremeValues`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at NormalDistributionImpl.cumulativeProbability(NormalDistributionImpl.java:109),
called from NormalDistributionTest.testExtremeValues(NormalDistributionTest.java:133). Full suite with the probe: 8 failing tests
(NormalDistributionTest testExtremeValues, testSetStandardDeviation, testQuantiles, testSetMean, testInverseCumulativeProbabilities,
testCumulativeProbabilities, testConsistency; PoissonDistributionTest testNormalApproximateProbability). The facade is reached directly.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 linear.BigMatrixImpl                 1319 lines  normalCumulative  placement: each point -> its standard score
  hop 2 stat.inference.TTestImpl             1069 lines  standardCumulative aggregation: creates the probability array
  hop 3 linear.RealMatrixImpl                1036 lines  fillCumulative    pass-through
  hop 4 ode.GraggBulirschStoerIntegrator     1019 lines  cumulativeInto    pass-through
  hop 5 geometry.Rotation                    1016 lines  writeCumulative   GOLD: per score, the standard normal probability
Host newline counts 1319, 1069, 1036, 1019, 1016; the smallest host (and the gold host) has 1016 lines (C10F addendum section 1).

Fault (one-line omission of a special-case step in the gold): the gold's far-tail decision is dropped (the if/else that gives a score
beyond 20 in magnitude the probability 0 or 1 becomes the plain assignment of the formula), so the gold evaluates the error function at
every score. Trigger: the EXISTING test NormalDistributionTest::testExtremeValues; at i = 40 cumulativeProbability(-40.0) reaches the
gold with z = -40, Erf.erf(-28.28) overflows its series and the test errors with
org.apache.commons.math.MaxIterationsExceededException (maximal number of iterations exceeded). It is the only test that evaluates the
distribution function more than 37.7 standard deviations from the mean; every other test input stays within 6 standard deviations, and
gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (for each standard score, the probability that a standard normal variable is less
than it) and is silent on far scores and on the error function's convergence; P(Z < -40) is a probability (0 to double precision), yet
the variant gold throws instead of writing it. The convention is pinned outside the gold: the facade's own javadoc (the convergence
exception is caught and 0 or 1 returned beyond 20 standard deviations), Erf.erf ("@throws MathException if the algorithm fails to
converge": the error function itself cannot be evaluated far out), NormalDistributionImpl.getDomainLowerBound /
getDomainUpperBound (the bracketing domain of the inverse runs to -Double.MAX_VALUE / Double.MAX_VALUE) and
AbstractContinuousDistribution.inverseCumulativeProbability (production code that evaluates cumulativeProbability at those domain
bounds when bracketing fails); passing tests through the chain: testQuantiles, testCumulativeProbabilities,
testInverseCumulativeProbabilities and PoissonDistributionTest::testNormalApproximateProbability (the distribution function, to 1e-10).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: scores bounds the loop and supplies every score; probabilities receives every write.
  T2 absent: i is the loop cursor and advances; z is read by the decision and by both writes; the if/else writes different values
     (0 or 1 vs the formula) and the ternary's two arms are both reachable (negative and positive far scores).
  T3 absent: both far tails are handled by the one decision (below: 0, above: 1); no class named in the gold's text is handled in part.
  T4 absent: 'the probability that a standard normal random variable takes a value less than the score' and the @param clauses are met
     by lines of the body; no inline comment; the identifiers (z, scores, probabilities) name nothing the body does not meet.
 Variant gold (javadoc, signature, the loop, `final double z = scores[i];`, the formula write):
  T1 absent: scores and probabilities each change the output; neither is only argument-checked.
  T2 absent: i advances; z reaches the write; no local is dead or frozen; no decision at all.
  T3 absent: the gold has no special-score treatment at all ('No member handled' for tails or special values); it names no class
     of scores (no "finite", no range).
  T4 absent: the javadoc is a general description of what the method computes, addressed by the formula line; @param clauses are
     met (each score's probability is written at its index); no comment; identifiers name nothing unmet.

Single owner: only the gold decides the probability of a score; hop 1 forms the standard scores (documented as exactly
(point - mean) / sd), hop 2 creates the array and returns it, hops 3 and 4 pass the scores and the array along. Once the gold has
called Erf.erf at a far score the exception has already escaped; no caller can pre-filter the scores in one line without changing
them (hop 1's documented scores) and recovering needs a try/catch around the whole array plus a second evaluation. Declared
alternatives (G9): hop 1 standardises by the magnitude of the standard deviation; hop 1 forms the score as point / sd - mean / sd;
hop 2 pre-fills the probability array with 0.5. None makes the trigger pass.
Recorded bypasses / doc-inconsistent edits (not declared, since they absorb the omission):
 B-0 the facade's original body (or any hop computing the probabilities itself with Erf.erf and a top-coding try/catch) discards
     the rest of the chain including the gold.
 B-1 hop 1 clamps each standard score to [-20, 20] (`scores[i] = Math.max(-20.0, Math.min(20.0, (points[i] - mean) / sd));`): the
     gold then evaluates the formula at +-20 (within 1e-14 of 0 and 1), so the trigger passes; it breaks hop 1's documented rule that each score is the
     difference between the point and the mean divided by the standard deviation.
 B-2 hop 2, 3 or 4 replaces each far score by +-20 or writes 0/1 for it before or instead of calling the next hop: a loop of its own
     (more than one line) and a second implementation of the gold's per-score decision.

Lie: the facade's javadoc claims the probability is computed by integrating the density from the mean to x with Simpson's rule and
adding one half; no step of the chain integrates anything (the gold evaluates the error function). It names neither the tails nor
convergence nor any hop."""

NDI = "src/java/org/apache/commons/math/distribution/NormalDistributionImpl.java"
BMI = "src/java/org/apache/commons/math/linear/BigMatrixImpl.java"
TTI = "src/java/org/apache/commons/math/stat/inference/TTestImpl.java"
RMI = "src/java/org/apache/commons/math/linear/RealMatrixImpl.java"
GBS = "src/java/org/apache/commons/math/ode/GraggBulirschStoerIntegrator.java"
ROT = "src/java/org/apache/commons/math/geometry/Rotation.java"

GOLD_TEXT = '''/** Compute, for each standard score, the probability that a standard
 * normal random variable takes a value less than the score.
 * @param scores the standard scores
 * @param probabilities the array receiving the probabilities, at the
 * same indices as the scores
 */
public static void writeCumulative(double[] scores, double[] probabilities)
    throws MathException {
  for (int i = 0; i < scores.length; i++) {
    final double z = scores[i];
    if (Math.abs(z) > 20.0) {
      probabilities[i] = (z < 0.0) ? 0.0 : 1.0;
    } else {
      probabilities[i] = 0.5 * (1.0 + Erf.erf(z / Math.sqrt(2.0)));
    }
  }
}'''

HOP1 = '''/**
 * Returns, for each point, the probability that a normal random variable
 * with the given mean and standard deviation takes a value less than the
 * point.
 * <p>
 * Each point is expressed as its standard score, the difference between
 * the point and the mean divided by the standard deviation, and the
 * probabilities are those of the standard scores under the standard
 * normal distribution.</p>
 *
 * @param points the points at which the probabilities are computed
 * @param mean the mean of the distribution
 * @param sd the standard deviation of the distribution, positive
 * @return the probabilities, at the same indices as the points
 * @throws MathException if a probability can not be computed
 */
public static double[] normalCumulative(double[] points, double mean, double sd)
    throws MathException {
    final double[] scores = new double[points.length];
    for (int i = 0; i < points.length; i++) {
        scores[i] = (points[i] - mean) / sd;
    }
    return TTestImpl.standardCumulative(scores);
}'''

HOP2 = '''/**
 * Returns, for each standard score, the probability that a standard
 * normal random variable takes a value less than the score.
 *
 * @param scores the standard scores
 * @return a new array holding the probabilities, at the same indices as
 * the scores
 * @throws MathException if a probability can not be computed
 */
public static double[] standardCumulative(double[] scores)
    throws MathException {
    final double[] probabilities = new double[scores.length];
    RealMatrixImpl.fillCumulative(scores, probabilities);
    return probabilities;
}'''

HOP3 = '''/**
 * Stores, for each standard score, the probability that a standard normal
 * random variable takes a value less than the score.
 *
 * @param scores the standard scores
 * @param probabilities the array receiving the probabilities, at the same
 * indices as the scores
 * @throws MathException if a probability can not be computed
 */
public static void fillCumulative(double[] scores, double[] probabilities)
    throws MathException {
    GraggBulirschStoerIntegrator.cumulativeInto(scores, probabilities);
}'''

HOP4 = '''/** Store, for each standard score, the probability that a standard
 * normal random variable takes a value less than the score.
 * @param scores the standard scores
 * @param probabilities the array receiving the probabilities, at the
 * same indices as the scores
 * @exception org.apache.commons.math.MathException if a probability can
 * not be computed
 */
public static void cumulativeInto(double[] scores, double[] probabilities)
    throws org.apache.commons.math.MathException {
  org.apache.commons.math.geometry.Rotation.writeCumulative(scores, probabilities);
}'''

DESIGN = {
 "instance": "Math-103", "project": "Math", "bug_id": 103, "seed": 8619,
 "src_root": "src/java", "test_root": "src/test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the argument x (as a one-element array) and the private fields mean and standardDeviation, passed to hop 1; "
                 "element 0 of the returned array is returned; no write-back",
 "host_mode": "largest5", "host_lines": [1319, 1069, 1036, 1019, 1016],
 "reachability_probe": "cumulativeProbability(double) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-103-probe: NormalDistributionTest::testExtremeValues fails with PROBE-REACHED at "
                       "NormalDistributionImpl.cumulativeProbability(NormalDistributionImpl.java:109) from "
                       "NormalDistributionTest.java:133; full suite with the probe: 8 failing tests (7 NormalDistributionTest, "
                       "PoissonDistributionTest::testNormalApproximateProbability)",
 "facade": {"file": NDI, "class": "org.apache.commons.math.distribution.NormalDistributionImpl", "method": "cumulativeProbability",
            "near_line": 108},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/math/distribution/NormalDistributionTest.java",
             "test_class": "org.apache.commons.math.distribution.NormalDistributionTest", "test_method": "testExtremeValues"},
 "expected_signature": "org.apache.commons.math.MaxIterationsExceededException",
 "gold": {"method": "writeCumulative", "text": GOLD_TEXT,
          "fault": {"old": "        if (Math.abs(z) > 20.0) {\n"
                           "          probabilities[i] = (z < 0.0) ? 0.0 : 1.0;\n"
                           "        } else {\n"
                           "          probabilities[i] = 0.5 * (1.0 + Erf.erf(z / Math.sqrt(2.0)));\n"
                           "        }",
                    "new": "        probabilities[i] = 0.5 * (1.0 + Erf.erf(z / Math.sqrt(2.0)));"}},
 "chain": {
   "facade_body": "return org.apache.commons.math.linear.BigMatrixImpl.normalCumulative(new double[] {x}, mean,\n"
                  "                standardDeviation)[0];",
   "lie": "The probability is computed by integrating the density from the mean to <code>x</code> with Simpson's rule and "
          "adding one half.",
   "hops": [
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "normalCumulative",
      "imports": ["org.apache.commons.math.MathException", "org.apache.commons.math.stat.inference.TTestImpl"], "text": HOP1},
     {"file": TTI, "class": "org.apache.commons.math.stat.inference.TTestImpl", "method": "standardCumulative",
      "imports": ["org.apache.commons.math.linear.RealMatrixImpl"], "text": HOP2},
     {"file": RMI, "class": "org.apache.commons.math.linear.RealMatrixImpl", "method": "fillCumulative",
      "imports": ["org.apache.commons.math.MathException", "org.apache.commons.math.ode.GraggBulirschStoerIntegrator"],
      "text": HOP3},
     {"file": GBS, "class": "org.apache.commons.math.ode.GraggBulirschStoerIntegrator", "method": "cumulativeInto",
      "imports": [], "text": HOP4},
     {"file": ROT, "class": "org.apache.commons.math.geometry.Rotation", "method": "writeCumulative",
      "imports": ["org.apache.commons.math.MathException", "org.apache.commons.math.special.Erf"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.special.Erf::erf",
              "org.apache.commons.math.distribution.AbstractContinuousDistribution::inverseCumulativeProbability",
              "org.apache.commons.math.distribution.NormalDistributionImpl::getDomainLowerBound"],
 "ownership_reason": "Only the gold decides the probability of a standard score: hop 1 forms the standard scores, documented as "
                     "exactly the difference between the point and the mean divided by the standard deviation; hop 2 creates the "
                     "probability array and returns it; hops 3 and 4 pass the scores and the array along. The gold's javadoc "
                     "promises, for each standard score, the probability that a standard normal variable is less than it; at the "
                     "score -40 the variant gold calls Erf.erf, whose series cannot converge there (Erf.erf: '@throws "
                     "MathException if the algorithm fails to converge'), and throws MaxIterationsExceededException instead of "
                     "writing the probability (0 to double precision). The exception escapes before any caller sees a result, so "
                     "no later hop can recover the value without a try/catch and a second evaluation, and no earlier hop can keep "
                     "the score from the gold in one line without breaking its documented scores. The convention that a far score "
                     "has probability 0 or 1 is pinned outside the gold: the facade's javadoc (beyond 20 standard deviations the "
                     "convergence exception is caught and 0 or 1 returned), NormalDistributionImpl.getDomainLowerBound / "
                     "getDomainUpperBound (the inverse's bracketing domain runs to -Double.MAX_VALUE / Double.MAX_VALUE) and "
                     "AbstractContinuousDistribution.inverseCumulativeProbability (which evaluates the distribution function at "
                     "those bounds when bracketing fails); testQuantiles, testCumulativeProbabilities, "
                     "testInverseCumulativeProbabilities and PoissonDistributionTest.testNormalApproximateProbability pass through "
                     "the chain.",
 "ownership_tests": ["org.apache.commons.math.distribution.NormalDistributionTest::testQuantiles",
                     "org.apache.commons.math.distribution.NormalDistributionTest::testCumulativeProbabilities",
                     "org.apache.commons.math.distribution.NormalDistributionTest::testInverseCumulativeProbabilities",
                     "org.apache.commons.math.distribution.PoissonDistributionTest::testNormalApproximateProbability"],
 "compensating": {
   "chain": [
     {"file": BMI, "old": "            scores[i] = (points[i] - mean) / sd;",
      "new": "            scores[i] = (points[i] - mean) / Math.abs(sd);",
      "why": "hop 1 standardises by the magnitude of the standard deviation"},
     {"file": BMI, "old": "            scores[i] = (points[i] - mean) / sd;",
      "new": "            scores[i] = points[i] / sd - mean / sd;",
      "why": "hop 1 forms each score as point / sd - mean / sd"},
     {"file": TTI, "old": "        final double[] probabilities = new double[scores.length];",
      "new": "        final double[] probabilities = new double[scores.length]; java.util.Arrays.fill(probabilities, 0.5);",
      "why": "hop 2 pre-fills the probability array with one half"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder): "
               "linear.BigMatrixImpl (hop 1, 1319 lines), stat.inference.TTestImpl (hop 2, 1069), linear.RealMatrixImpl (hop 3, "
               "1036), ode.GraggBulirschStoerIntegrator (hop 4, 1019), geometry.Rotation (hop 5, gold, 1016; the smallest host). "
               "All five are public concrete top-level classes in which a public static method compiles; the facade's class "
               "NormalDistributionImpl is excluded. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with "
               "seed 8619 + 100 + i, as mr3_spec.py inserts them: hop 1 after preMultiply (seed 8719), hop 2 after t (8720), hop 3 "
               "after operate (8721); GraggBulirschStoerIntegrator (8722) and Rotation (8723) have no 4-space-indented members (both "
               "files use 2-space indentation), so the picker returns no anchor and the recipe inserts the hop before the class's "
               "closing brace; hops 4 and 5 are written in those files' 2-space style and javadoc voice. GraggBulirschStoerIntegrator "
               "has no import section, so hop 4 names MathException and Rotation by their fully-qualified names; the other hops "
               "import what they need.",
}
