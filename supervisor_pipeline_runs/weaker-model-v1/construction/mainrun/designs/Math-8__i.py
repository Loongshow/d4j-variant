"""Main run Math-8__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; the fixed
checkout of Defects4J Math-8, fixed revision 0d057fc6dc9fac9e16c01e3647c2201281310a6a; the real bug modified
distribution.DiscreteDistribution, the facade's class). No static pair exists (pool v2: no_tested_static; B8 note section 1).

Facade: DiscreteDistribution.sample() (instance method; allowed candidates DiscreteDistribution.sample() (V1) and
DiscreteDistribution.sample(int) (V2), BATCH8_PREREGISTRATION.md row 283; facade_planned_by null for both; no facade reuse).
sample() carries the whole sampling computation; sample(int) only allocates an array and calls sample() once per slot, so its chain
would hold no per-element computation that a single existing test could catch (the one test that calls it checks only the length of
the returned array). sample(int) stays intact and is the trigger's way into the facade.
Original computation of sample(): one uniform deviate u = random.nextDouble(); the probabilities are summed in order and the first
value whose running sum exceeds u is returned; if none does (floating-point residue), the last value is returned.

facade_variant: V1 (state as parameters). state_passed: the fields random (RandomGenerator), probabilities (double[], normalised) and
singletons (List<T>), read in the facade and passed to hop 1; no field is written, no write-back. The facade body is one call to hop 1
(the original has no argument guard). No visibility is widened, no type is added, no signature, modifier, override or throws clause
changes, no reflection, no test edit. The facade calls no private method, so V4 does not apply; the hops are generic only in hop 1
(List<T> of the public type parameter), no package-private type crosses a package (V3/V5 not needed).

Redistribution of the computation: hop 1 maps the drawn index to its value; hop 2 draws the deviate (the one nextDouble() call, as in
the original); hop 3 passes through; hop 4 is the fold: it lays the weights out one after another from zero and records the start of
each entry (starts[i] = running sum of the weights before i, accumulated in the original order); hop 5, the gold, is the per-point
core: it walks the starts in order, moving on to the next interval while its start is at or below the point, and stops at the last
interval. The correct chain returns bit for bit what the original returns for every deviate: starts[i + 1] is the original's running
sum after entry i, so the walk stops at the first i with u < sum_i, and at the last entry when no running sum exceeds u (the original
fallback).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-8-probe of the fixture, the first statement of
sample() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; defects4j test -t on
DiscreteRealDistributionTest::testIssue942, DiscreteRealDistributionTest::testSample and DiscreteIntegerDistributionTest::testSample:
each 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at DiscreteDistribution.sample(DiscreteDistribution.java:157).
testIssue942 reaches the facade through DiscreteDistribution.sample(int); the two testSample tests through DiscreteRealDistribution
.sample() / DiscreteIntegerDistribution.sample() (innerDistribution.sample()).

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview Math-8 org/apache/commons/math3/distribution/DiscreteDistribution.java 5`,
seed 7643, used in draw order, none substituted):
  hop 1 analysis.differentiation.DSCompiler                    1763 lines  drawValue        plumbing: drawn index -> value
  hop 2 linear.BlockFieldMatrix                                1593 lines  drawIndex        placement: draws the deviate
  hop 3 optimization.direct.BOBYQAOptimizer                    2487 lines  weightedIndex    pass-through
  hop 4 linear.BlockRealMatrix                                 1582 lines  indexForWeights  aggregation: the fold of weights into starts
  hop 5 linear.RealVector                                      1651 lines  intervalOf       GOLD: the walk over the starts
Host sizes 1763, 1593, 2487, 1582, 1651; the smallest host is BlockRealMatrix (1582 lines); the gold host has 1651 lines.

Fault (one-line omission in the gold's iteration): the walk's stop at the last interval is dropped
(`while (index + 1 < starts.length && starts[index + 1] <= point) {` becomes `while (starts[index + 1] <= point) {`), so the walk
moves on past the last interval when the point lies at or above the last start, reading a start that does not exist. Trigger: the
EXISTING test DiscreteRealDistributionTest::testIssue942 (values {a: 0, b: 1}, sample(1)); for every deviate u in [0, 1) the starts
are {0, 0}, the walk passes the empty first interval and then reads starts[2]: java.lang.ArrayIndexOutOfBoundsException: Index 2 out of bounds for length 2. Under
the two testSample tests (weights 0.2, 0.2, 0.3, 0.3, 0, 0; starts 0, 0.2, 0.4, 0.7, 1.0, 1.0) the point never reaches the last start
(1.0 > every deviate), so the walk stops inside the array and every draw equals the original's; no other test reaches sample().
Gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract ("the index of the interval that holds the point"; intervals visited in order,
moving on to the next while its start is at or below the point) and is silent on the last interval. The convention that the last
interval holds every point at or above its start is pinned outside the gold: StepFunction.value (a point at or past the last abscissa
takes the last ordinate; f.value(30) and f.value(+inf) give the last step in StepFunctionTest::testSomeValues) and
PolynomialSplineFunction.value (the last knot is taken by the last piece) do the same step; DiscreteRealDistributionTest::testSample
and DiscreteIntegerDistributionTest::testSample pass through the chain.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: starts supplies the walk's bound and every compared start; point decides where the walk stops.
  T2 absent: index is the walk's cursor, advanced in the loop and returned; the loop condition decides every step.
  T3 absent: the gold handles no enumerated set; it reads only starts (an interval's end is the next start) and point.
  T4 absent: 'the index of the interval that holds a point', 'visited in order, moving on to the next interval while its start is at
     or below the point' and the @param clauses are met by the loop; 'in ascending order' and 'the first one at or below the point'
     are caller preconditions.
 Variant gold (javadoc, signature, `int index = 0;`, `while (starts[index + 1] <= point) {`, `index++;`, `return index;`):
  T1 absent: starts and point both decide the returned index; neither is only argument-checked.
  T2 absent: index is advanced inside the loop and returned; it is not frozen; the loop condition is live; no dead local or decision.
  T3 absent: no set is enumerated; the gold has no bound test at all ('No member handled'), and no clamp of a start or end parameter;
     an interval's two ends are both read (its own start through the walk, its end as the next start).
  T4 absent: 'moving on to the next interval while its start is at or below the point' is what the loop does; 'the index of the
     interval that holds the point' is a general description of the result that the loop addresses; no inline comment; identifiers
     (starts, point, index) name nothing the body does not meet.

Single owner: only the gold decides where the walk stops; hop 4 records one start per entry, hops 1 to 3 pass the index or the point
along. Once the gold reads past the last start the exception is raised inside the gold, so no caller can take its result and recover;
a caller can avoid it only by not calling the gold. Declared alternatives (G9): hop 4 makes room for one more start (the extra start is
0.0, so the walk passes it as well); hop 4 records starts only for entries with a positive weight (the starts of {0, 1} stay {0, 0});
hop 2 keeps the point strictly below the drawn deviate. None makes the trigger pass.
Recorded bypasses: B-0 the facade's original body (the in-place running-sum loop) discards the chain including the gold; B-1 hop 4
returns the position from java.util.Arrays.binarySearch over its starts (`int at = Arrays.binarySearch(starts, point); return at >= 0 ?
at : -at - 2;`) instead of calling the gold, discarding the gold's walk; B-2 hop 4 sizes its starts one longer and stores the total as
the last start (two statements), which gives the walk a start it was not documented to receive (hop 4's javadoc: one start per entry).

Lie: the facade's javadoc claims the value is located by a binary search over the cumulative probabilities; no step of the chain
searches by bisection (hop 5 walks the starts one by one). It names neither the last interval nor any hop."""

DD = "src/main/java/org/apache/commons/math3/distribution/DiscreteDistribution.java"
DSC = "src/main/java/org/apache/commons/math3/analysis/differentiation/DSCompiler.java"
BFM = "src/main/java/org/apache/commons/math3/linear/BlockFieldMatrix.java"
BOB = "src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java"
BRM = "src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java"
RV = "src/main/java/org/apache/commons/math3/linear/RealVector.java"

GOLD_TEXT = '''/**
 * Returns the index of the interval that holds a point, given the start
 * of each interval.
 * <p>
 * The intervals are visited in order, moving on to the next interval
 * while its start is at or below the point.
 * </p>
 *
 * @param starts the start of each interval, in ascending order, the
 * first one at or below the point
 * @param point the point to locate
 * @return the index of the interval that holds the point
 */
public static int intervalOf(final double[] starts, final double point) {
    int index = 0;
    while (index + 1 < starts.length && starts[index + 1] <= point) {
        index++;
    }
    return index;
}'''

HOP1 = '''/**
 * Draws one of the given values, each with the probability given at the
 * same position.
 *
 * @param <T> the type of the values
 * @param generator the generator to draw with
 * @param probabilities the probability of each value, summing to one
 * @param values the values to draw from, as many as the probabilities
 * @return the drawn value
 */
public static <T> T drawValue(final RandomGenerator generator, final double[] probabilities,
                              final List<T> values) {
    return values.get(BlockFieldMatrix.drawIndex(generator, probabilities));
}'''

HOP2 = '''/**
 * Draws the index of an entry, each entry with a chance equal to its
 * weight.
 * <p>
 * One uniform deviate in [0, 1) is drawn from the generator and placed
 * among the weighted entries.
 * </p>
 *
 * @param generator the generator of the uniform deviate
 * @param weights the weight of each entry, summing to one
 * @return the index of the drawn entry
 */
public static int drawIndex(final RandomGenerator generator, final double[] weights) {
    return BOBYQAOptimizer.weightedIndex(weights, generator.nextDouble());
}'''

HOP3 = '''/**
 * Returns the index of the entry that a point selects among weighted
 * entries laid out one after another from zero.
 *
 * @param weights the weight of each entry
 * @param point the point, at or above zero
 * @return the index of the selected entry
 */
public static int weightedIndex(final double[] weights, final double point) {
    return BlockRealMatrix.indexForWeights(weights, point);
}'''

HOP4 = '''/**
 * Returns the index of the entry that a point selects among weighted
 * entries.
 * <p>
 * The entries are laid out one after another from zero, each over a
 * length equal to its weight, and the start of each entry is recorded,
 * one start per entry; the entry laid over the point is selected.
 * </p>
 *
 * @param weights the weight of each entry, not negative
 * @param point the point, at or above zero
 * @return the index of the selected entry
 */
public static int indexForWeights(final double[] weights, final double point) {
    final double[] starts = new double[weights.length];
    double sum = 0;
    for (int i = 0; i < weights.length; i++) {
        starts[i] = sum;
        sum += weights[i];
    }
    return RealVector.intervalOf(starts, point);
}'''

DESIGN = {
 "instance": "Math-8", "project": "Math", "bug_id": 8, "seed": 7643,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the fields random (RandomGenerator), probabilities (double[]) and singletons (List<T>), passed to hop 1; "
                 "no write-back",
 "host_mode": "1500", "host_lines": [1763, 1593, 2487, 1582, 1651],
 "reachability_probe": "sample() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-8-probe: DiscreteRealDistributionTest::testIssue942, "
                       "DiscreteRealDistributionTest::testSample and DiscreteIntegerDistributionTest::testSample each fail with "
                       "PROBE-REACHED at DiscreteDistribution.sample(DiscreteDistribution.java:157)",
 "facade": {"file": DD, "class": "org.apache.commons.math3.distribution.DiscreteDistribution", "method": "sample", "near_line": 156},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/math3/distribution/DiscreteRealDistributionTest.java",
             "test_class": "org.apache.commons.math3.distribution.DiscreteRealDistributionTest", "test_method": "testIssue942"},
 "expected_signature": "java.lang.ArrayIndexOutOfBoundsException: Index 2 out of bounds for length 2",
 "gold": {"method": "intervalOf", "text": GOLD_TEXT,
          "fault": {"old": "        while (index + 1 < starts.length && starts[index + 1] <= point) {",
                    "new": "        while (starts[index + 1] <= point) {"}},
 "chain": {
   "facade_body": "return org.apache.commons.math3.analysis.differentiation.DSCompiler.drawValue(random, probabilities, "
                  "singletons);",
   "lie": "The value is located by a binary search over the cumulative probabilities.",
   "hops": [
     {"file": DSC, "class": "org.apache.commons.math3.analysis.differentiation.DSCompiler", "method": "drawValue",
      "imports": ["org.apache.commons.math3.linear.BlockFieldMatrix", "org.apache.commons.math3.random.RandomGenerator"],
      "text": HOP1},
     {"file": BFM, "class": "org.apache.commons.math3.linear.BlockFieldMatrix", "method": "drawIndex",
      "imports": ["org.apache.commons.math3.optimization.direct.BOBYQAOptimizer",
                  "org.apache.commons.math3.random.RandomGenerator"], "text": HOP2},
     {"file": BOB, "class": "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer", "method": "weightedIndex",
      "imports": ["org.apache.commons.math3.linear.BlockRealMatrix"], "text": HOP3},
     {"file": BRM, "class": "org.apache.commons.math3.linear.BlockRealMatrix", "method": "indexForWeights",
      "imports": [], "text": HOP4},
     {"file": RV, "class": "org.apache.commons.math3.linear.RealVector", "method": "intervalOf",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.analysis.function.StepFunction::value",
              "org.apache.commons.math3.analysis.polynomials.PolynomialSplineFunction::value"],
 "ownership_reason": "Only the gold decides where the walk over the starts stops: hop 4 lays the weights out from zero and records "
                     "one start per entry, hops 1 to 3 pass the index or the point along (hop 2 draws the single deviate). The "
                     "gold's contract is the index of the interval that holds the point; the last interval holds every point at or "
                     "above its start, because there is no next interval to move on to. The variant walks past the last interval "
                     "and reads a start that does not exist, raising inside the gold, so no caller can take its result and recover "
                     "it. The convention is pinned outside the gold: StepFunction.value gives a point at or past the last abscissa "
                     "the last ordinate (StepFunctionTest::testSomeValues: f.value(30) and f.value(+inf) give the last step; "
                     "testEndpointBehavior), PolynomialSplineFunction.value gives the last knot to the last piece; "
                     "DiscreteRealDistributionTest::testSample and DiscreteIntegerDistributionTest::testSample pass through the "
                     "chain (every draw inside the starts).",
 "ownership_tests": ["org.apache.commons.math3.analysis.function.StepFunctionTest::testSomeValues",
                     "org.apache.commons.math3.analysis.function.StepFunctionTest::testEndpointBehavior",
                     "org.apache.commons.math3.distribution.DiscreteRealDistributionTest::testSample",
                     "org.apache.commons.math3.distribution.DiscreteIntegerDistributionTest::testSample"],
 "compensating": {
   "chain": [
     {"file": BRM, "old": "        final double[] starts = new double[weights.length];",
      "new": "        final double[] starts = new double[weights.length + 1];",
      "why": "hop 4 makes room for one more start"},
     {"file": BRM, "old": "            starts[i] = sum;",
      "new": "            starts[i] = weights[i] > 0 ? sum : starts[i];",
      "why": "hop 4 records starts only for entries with a positive weight"},
     {"file": BFM, "old": "        return BOBYQAOptimizer.weightedIndex(weights, generator.nextDouble());",
      "new": "        return BOBYQAOptimizer.weightedIndex(weights, FastMath.nextAfter(generator.nextDouble(), 0.0));",
      "why": "hop 2 keeps the point strictly below the drawn deviate"},
   ],
 },
 "host_notes": "host_mode 1500: seeded draw `mr_lib.py preview Math-8 org/apache/commons/math3/distribution/DiscreteDistribution.java "
               "5` (seed 7643; the facade file is excluded by the draw; FastMathLiteralArrays is not usable), used in draw order, "
               "none substituted: analysis.differentiation.DSCompiler (hop 1, 1763 lines), linear.BlockFieldMatrix (hop 2, 1593), "
               "optimization.direct.BOBYQAOptimizer (hop 3, 2487), linear.BlockRealMatrix (hop 4, 1582, the smallest host), "
               "linear.RealVector (hop 5, gold, 1651). All five are public top-level classes in which a public static method "
               "compiles (RealVector is abstract; BlockFieldMatrix's type parameter is not used by the static hop). Anchors "
               "(preview, seed 7643 + 100 + i): hop 1 after cosh (7743), hop 2 after scalarAdd (7744), hop 3 after the "
               "BOBYQAOptimizer constructor (7745), hop 4 after createBlocksLayout (7746), hop 5 after getMaxValue (7747). The "
               "facade calls hop 1 by its fully-qualified name; hops 1 to 3 import the next host and RandomGenerator as needed; "
               "hop 4 and the gold are in the same package; BlockFieldMatrix already imports FastMath.",
}
