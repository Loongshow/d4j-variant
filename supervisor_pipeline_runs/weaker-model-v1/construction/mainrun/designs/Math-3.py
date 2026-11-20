"""Main-run instance Math-3 (C10 recipe on the fixed checkout of Defects4J Math-3; target class MathArrays, the class the real bug
modified). Facade = MathArrays.normalizeArray(double[], double) (pool candidate 2; convolve, candidate 1, was set aside: every
omission in its convolution sum is an out-of-range index, which a hop can absorb by zero-padding the input, so its gold could not
be the unique owner). The facade keeps its argument guard (infinite or NaN target sum) and delegates to a five-hop chain drawn
with the instance seed 8219 (mr_lib preview, draw order, no substitution):
  hop 1 optim...noderiv.BOBYQAOptimizer.rescaledEntries   placement: the output copy (NaN entries copied, others x * total / sum)
  hop 2 linear.BlockFieldMatrix.normalizingSum            decision: rejects a zero sum (ARRAY_SUMS_TO_ZERO)
  hop 3 dfp.Dfp.sumOfEntries                              pass-through: the whole array as the slice [0, length)
  hop 4 linear.BlockRealMatrix.blockTotal                 pass-through
  hop 5 optimization.direct.BOBYQAOptimizer.rangeSum      GOLD: the per-entry pass (infinite entries rejected, the finite
                                                          entries summed)
The chain performs exactly the original computation in the original order (target-sum guard, per-entry infinite check and sum,
zero-sum check, output loop with the same arithmetic `values[i] * total / sum`), so the correct configuration is
behaviour-preserving for every caller (EnumeratedDistribution, FuzzyKMeansClusterer, the Variance/MathArrays tests).

Fault (omission in the gold): the NaN skip around the accumulation is dropped, so a NaN entry enters the sum and the sum becomes
NaN; every rescaled entry is then NaN. Trigger: the EXISTING test MathArraysTest::testNormalizeArray, whose 'Ignore NaNs' block
normalizes {-1, -1, NaN, 1, NaN} and expects {1, 1, NaN, -1, NaN} (TestUtils reports 'expected = 1.0 observed = NaN'). It is the
only test that feeds a NaN entry to normalizeArray: EnumeratedDistribution rejects NaN probabilities before normalizing,
FuzzyKMeansClusterer normalizes random values in [0, 1), VarianceTest uses identical finite weights.

The gold's javadoc states the contract (the sum of the finite entries of the slice; an infinite entry is rejected) and is silent
on the skipping step. External pins: the facade's own javadoc ('sum is the sum of the non-NaN entries', 'Ignores ... NaNs');
Max.evaluate and Min.evaluate, reductions over an array slice that leave NaN entries out (`if (!Double.isNaN(values[i]))`), with
their passing testNaNs tests; inside the chain, hop 1 copies NaN entries unchanged.

Single owner: only the gold inspects individual entries for the sum. Once a NaN has entered the sum the finite total (-1 on the
trigger) is gone, so hop 2's zero check, hop 1's output loop and the pass-throughs cannot recover it with a one-line change, and
there is no NaN-removing array utility for a one-line pre-filter at hops 2-4. Declared alternatives (G9): hop 2 also rejects a
NaN sum (the trigger then throws), hop 4 shortens the slice (NaN at index 2 stays in), hop 1 leaves entries unscaled under a NaN
sum (signs come out reversed). Recorded bypasses: hop 1 can compute its own NaN-skipping sum with an inline loop, discarding
hops 2-5; a hop above the gold can pass the gold a copy with NaN entries replaced by zero (a second implementation of the skip
outside the gold, multi-statement).

Lie: the facade's javadoc claims compensated summation in order of increasing magnitude and an in-place rescale of the input
array; the code does a plain left-to-right sum and returns a new array. It names neither NaN nor skipping nor any hop."""

MA = "src/main/java/org/apache/commons/math3/util/MathArrays.java"
BQ1 = "src/main/java/org/apache/commons/math3/optim/nonlinear/scalar/noderiv/BOBYQAOptimizer.java"
BFM = "src/main/java/org/apache/commons/math3/linear/BlockFieldMatrix.java"
DFP = "src/main/java/org/apache/commons/math3/dfp/Dfp.java"
BRM = "src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java"
BQ5 = "src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java"

GOLD_TEXT = '''/**
 * Returns the sum of the finite entries in the slice
 * {@code [begin, begin + length)} of an array.
 *
 * @param values the array
 * @param begin index (0-based) of the first entry of the slice
 * @param length the number of entries in the slice
 * @return the sum of the finite entries of the slice
 * @throws MathIllegalArgumentException if an entry of the slice is infinite
 */
public static double rangeSum(final double[] values, final int begin, final int length) {
    double sum = 0d;
    for (int i = begin; i < begin + length; i++) {
        final double entry = values[i];
        if (Double.isInfinite(entry)) {
            throw new MathIllegalArgumentException(LocalizedFormats.INFINITE_ARRAY_ELEMENT, entry, i);
        }
        if (!Double.isNaN(entry)) {
            sum += entry;
        }
    }
    return sum;
}'''

HOP1 = '''/**
 * Returns a copy of an array in which each entry x that is not NaN is
 * replaced by {@code x * total / sum}, where sum is the sum of the finite
 * entries of the array. NaN entries are copied unchanged.
 *
 * @param values the array to rescale
 * @param total the target sum of the rescaled entries
 * @return the rescaled copy of the array
 * @throws MathIllegalArgumentException if an entry is infinite
 * @throws MathArithmeticException if the finite entries sum to zero
 */
public static double[] rescaledEntries(double[] values, double total) {
    final double sum = BlockFieldMatrix.normalizingSum(values);
    final int len = values.length;
    final double[] out = new double[len];
    for (int i = 0; i < len; i++) {
        if (Double.isNaN(values[i])) {
            out[i] = Double.NaN;
        } else {
            out[i] = values[i] * total / sum;
        }
    }
    return out;
}'''

HOP2 = '''/**
 * Returns the sum of the finite entries of an array, the divisor of a
 * normalization of the array, which therefore must not be zero.
 *
 * @param values the array
 * @return the sum of the finite entries
 * @throws MathIllegalArgumentException if an entry is infinite
 * @throws MathArithmeticException if the sum is zero
 */
public static double normalizingSum(double[] values) {
    final double sum = Dfp.sumOfEntries(values);
    if (sum == 0) {
        throw new MathArithmeticException(LocalizedFormats.ARRAY_SUMS_TO_ZERO);
    }
    return sum;
}'''

HOP3 = '''/**
 * Returns the sum of the finite entries of an array.
 *
 * @param values the array
 * @return the sum of the finite entries
 * @throws MathIllegalArgumentException if an entry is infinite
 */
public static double sumOfEntries(double[] values) {
    return BlockRealMatrix.blockTotal(values, 0, values.length);
}'''

HOP4 = '''/**
 * Returns the sum of the finite entries in the slice
 * {@code [begin, begin + length)} of an array.
 *
 * @param values the array
 * @param begin index (0-based) of the first entry of the slice
 * @param length the number of entries in the slice
 * @return the sum of the finite entries of the slice
 * @throws MathIllegalArgumentException if an entry of the slice is infinite
 */
public static double blockTotal(double[] values, int begin, int length) {
    return BOBYQAOptimizer.rangeSum(values, begin, length);
}'''

DESIGN = {
 "instance": "Math-3", "project": "Math", "bug_id": 3, "seed": 8219,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": MA, "class": "org.apache.commons.math3.util.MathArrays", "method": "normalizeArray", "near_line": 1294},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math3/util/MathArraysTest.java",
             "test_class": "org.apache.commons.math3.util.MathArraysTest", "test_method": "testNormalizeArray"},
 "expected_signature": "expected = 1.0 observed = NaN",
 "gold": {"method": "rangeSum", "text": GOLD_TEXT,
          "fault": {"old": "            if (!Double.isNaN(entry)) {\n"
                           "                sum += entry;\n"
                           "            }",
                    "new": "            sum += entry;"}},
 "chain": {
   "facade_body": "if (Double.isInfinite(normalizedSum)) {\n"
                  "            throw new MathIllegalArgumentException(LocalizedFormats.NORMALIZE_INFINITE);\n"
                  "        }\n"
                  "        if (Double.isNaN(normalizedSum)) {\n"
                  "            throw new MathIllegalArgumentException(LocalizedFormats.NORMALIZE_NAN);\n"
                  "        }\n"
                  "        return org.apache.commons.math3.optim.nonlinear.scalar.noderiv.BOBYQAOptimizer.rescaledEntries(values, normalizedSum);",
   "lie": "The entries are accumulated with compensated summation in order of increasing magnitude, and the input array is "
          "then rescaled in place and returned.",
   "hops": [
     {"file": BQ1, "class": "org.apache.commons.math3.optim.nonlinear.scalar.noderiv.BOBYQAOptimizer", "method": "rescaledEntries",
      "imports": ["org.apache.commons.math3.linear.BlockFieldMatrix"], "text": HOP1},
     {"file": BFM, "class": "org.apache.commons.math3.linear.BlockFieldMatrix", "method": "normalizingSum",
      "imports": ["org.apache.commons.math3.dfp.Dfp", "org.apache.commons.math3.exception.MathArithmeticException"], "text": HOP2},
     {"file": DFP, "class": "org.apache.commons.math3.dfp.Dfp", "method": "sumOfEntries",
      "imports": ["org.apache.commons.math3.linear.BlockRealMatrix"], "text": HOP3},
     {"file": BRM, "class": "org.apache.commons.math3.linear.BlockRealMatrix", "method": "blockTotal",
      "imports": ["org.apache.commons.math3.optimization.direct.BOBYQAOptimizer"], "text": HOP4},
     {"file": BQ5, "class": "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer", "method": "rangeSum",
      "imports": ["org.apache.commons.math3.exception.MathIllegalArgumentException"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.util.MathArrays::normalizeArray",
              "org.apache.commons.math3.stat.descriptive.rank.Max::evaluate",
              "org.apache.commons.math3.stat.descriptive.rank.Min::evaluate"],
 "ownership_reason": "Only the gold inspects the individual entries that make up the sum; once a NaN entry has entered the sum, "
                     "the finite total (-1 for {-1, -1, NaN, 1, NaN}) is lost, so the zero-sum check, the output loop and the "
                     "pass-throughs cannot recover it with a one-line change, and no NaN-removing array utility exists for a "
                     "one-line pre-filter. The convention is pinned outside the gold: the facade's javadoc defines sum as 'the sum "
                     "of the non-NaN entries' and says NaNs are ignored; Max.evaluate and Min.evaluate leave NaN entries out of "
                     "their reduction over a slice (MaxTest/MinTest testNaNs, passing); hop 1 copies NaN entries unchanged. The "
                     "gold's javadoc promises the sum of the finite entries, which NaN violates.",
 "ownership_tests": ["org.apache.commons.math3.stat.descriptive.rank.MaxTest::testNaNs",
                     "org.apache.commons.math3.stat.descriptive.rank.MinTest::testNaNs",
                     "org.apache.commons.math3.stat.descriptive.moment.VarianceTest::testWeightedVariance"],
 "compensating": {
   "chain": [
     {"file": BFM, "old": "        final double sum = Dfp.sumOfEntries(values);\n        if (sum == 0) {",
      "new": "        final double sum = Dfp.sumOfEntries(values);\n        if (sum == 0 || Double.isNaN(sum)) {",
      "why": "hop 2 rejects a sum that is not a number as it rejects a zero sum"},
     {"file": BRM, "old": "        return BOBYQAOptimizer.rangeSum(values, begin, length);",
      "new": "        return BOBYQAOptimizer.rangeSum(values, begin, length - 1);",
      "why": "hop 4 leaves the last entry out of the slice"},
     {"file": BQ1, "old": "                out[i] = values[i] * total / sum;",
      "new": "                out[i] = Double.isNaN(sum) ? values[i] : values[i] * total / sum;",
      "why": "hop 1 leaves the entries unscaled when the sum is not a number"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 8219 (mr_lib preview, n=5, target org/apache/commons/math3/util/MathArrays.java): "
               "optim.nonlinear.scalar.noderiv.BOBYQAOptimizer (hop 1), linear.BlockFieldMatrix (hop 2), dfp.Dfp (hop 3), "
               "linear.BlockRealMatrix (hop 4), optimization.direct.BOBYQAOptimizer (hop 5, gold). All five are public concrete "
               "classes in which a static method compiles; none was skipped. Hop 5's class is @Deprecated (since 3.1), which only "
               "adds a deprecation note at compile time. Hops 1 and 5 share the simple name BOBYQAOptimizer: the facade calls hop 1 "
               "by its fully-qualified name and hop 4 imports the optimization.direct class. BlockFieldMatrix is generic; the "
               "static hop uses no type parameter.",
}
