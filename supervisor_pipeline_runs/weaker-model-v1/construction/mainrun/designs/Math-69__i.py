"""Main run Math-69__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Math-69; the real bug modified PearsonsCorrelation, the facade's class). No static pair (pool v2: no_tested_static).

Facade: PearsonsCorrelation.getCorrelationStandardErrors() (allowed instance target of BATCH8_PREREGISTRATION.md row 296,
facade_planned_by null, no facade reuse). The other two allowed targets were not used:
 - PearsonsCorrelation.correlation(double[], double[]) is called by computeCorrelationMatrix, i.e. by every constructor that takes
   data, by SpearmansCorrelation and by most tests of both correlation test classes; no omission in its computation is caught by a
   single test.
 - PearsonsCorrelation.getCorrelationPValues() is reached by testLongly, testSwissFertility, testPValueNearZero and
   testStdErrorConsistency of PearsonsCorrelationTest, and SpearmansRankCorrelationTest inherits testSwissFertility and
   testPValueNearZero (both of which build a PearsonsCorrelation), so an off-diagonal change fails several tests and a change that
   only shows for vanishing p-values fails two (one per class).
getCorrelationStandardErrors is reached by exactly two tests (probe below); testCovarianceConsistency compares two PearsonsCorrelation
instances built from the same data, so a deterministic change of the per-entry computation cancels there, and
testStdErrorConsistency, which checks the standard errors against the independently computed p-values, is the only test that sees
it.
Original computation of the facade: nVars = correlationMatrix.getColumnDimension(); out[i][j] = sqrt((1 - r * r) / (nObs - 2))
with r = correlationMatrix.getEntry(i, j), for every i, j; returned as new BlockRealMatrix(out).

facade_variant: V1 (state as parameters). The method reads two private final fields (correlationMatrix, a RealMatrix, and nObs, an
int) and writes none; the facade passes both values to hop 1 and returns hop 1's result. RealMatrix is a public interface of the
public package org.apache.commons.math.linear, visible from every host; the chain uses only its public methods getRowDimension and
getRow, so V2 is not needed; no private method of PearsonsCorrelation is called (no V4); no package-private type is involved (no
V3/V5). No signature, modifier, override or throws change; no new type; no reflection; no test edit. The facade calls hop 1 by its
fully-qualified name (no import added to PearsonsCorrelation).
state_passed: the private fields correlationMatrix (RealMatrix) and nObs (int) to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Math-69-probe/w of the fixture,
the first statement of getCorrelationStandardErrors was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
Full suite (defects4j test) with the probe: 2 failing tests, PearsonsCorrelationTest::testStdErrorConsistency
(java.lang.IllegalStateException: PROBE-REACHED at PearsonsCorrelation.getCorrelationStandardErrors(PearsonsCorrelation.java:136)
from PearsonsCorrelationTest.java:227) and PearsonsCorrelationTest::testCovarianceConsistency (same, from line 250). The facade
has no production caller; SpearmansRankCorrelationTest overrides both tests with empty bodies.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of batch8_tasks.json, in that order, none substituted):
  hop 1 util.MathUtils            1833 lines  correlationErrors           degrees of freedom: sample size - 2
  hop 2 linear.BlockRealMatrix    1687 lines  createErrorMatrix           aggregation: one row of errors per row, matrix built
  hop 3 linear.BlockFieldMatrix   1667 lines  rowErrors                   placement: fetches row i of the correlation matrix
  hop 4 linear.BigMatrixImpl      1506 lines  errorsOfCoefficients        pass-through
  hop 5 linear.ArrayRealVector    1239 lines  coefficientStandardErrors   GOLD: the per-coefficient standard error loop
Host newline counts 1833, 1687, 1667, 1506, 1239; the smallest host is ArrayRealVector (1239 lines), which is also the gold host.
The correct configuration returns the original matrix: the correlation matrix is square, so iterating its rows (getRowDimension)
covers the same entries as the original's nVars x nVars loop, row i of the matrix is (getEntry(i, 0), ..., getEntry(i, nVars - 1)),
and (1 - r) * (1 + r) is 1 - r * r written as a product (equal up to rounding in the last place; the same form on both sides of
testCovarianceConsistency; testStdErrorConsistency's tolerance is 1e-14 on p-values).

Fault (one-line omission inside the gold's iteration): the statement that multiplies the running value by (1 + r) is dropped, so
each standard error is computed as sqrt((1 - r) / dof) instead of sqrt((1 - r) (1 + r) / dof). The gold then reads as an ordinary
loop that turns each coefficient into a value and divides it by the degrees of freedom before taking the square root.
Trigger: the EXISTING test PearsonsCorrelationTest::testStdErrorConsistency (Swiss fertility data, 47 observations, 5 variables): for
each entry below the diagonal it forms t = |r| / se and compares 2 (1 - T45(t)) with getCorrelationPValues(); with the variant
errors t is wrong for every coefficient other than 0 and the first comparison fails (expected_signature below). It is the only test
that newly fails: the facade's only other test caller, testCovarianceConsistency, compares two instances whose correlation matrices
agree to 1e-14, so the same per-entry computation gives the same errors on both sides; the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the standard error of each coefficient estimated with the given degrees of
freedom) and is silent on how the value is formed; sqrt((1 - r) / dof) is not the standard error of a correlation coefficient. The
convention is pinned outside the gold: the facade's own javadoc keeps the formula SE_r = ((1 - r^2) / (n - 2))^(1/2);
PearsonsCorrelation.getCorrelationPValues forms t = |r| ((n - 2) / (1 - r^2))^(1/2) (pinned by PearsonsCorrelationTest testLongly
and testSwissFertility against R); SimpleRegression.getMeanSquareError (SSE / (n - 2), SSE = SYY - SXY^2 / SXX = SYY (1 - r^2)) and
SimpleRegression.getSlopeStdErr (pinned by SimpleRegressionTest testNorris against NIST) use the same residual fraction and degrees
of freedom.

Single owner: only the gold turns a coefficient into its error; hop 1 forms the degrees of freedom, hop 2 assembles rows, hop 3
fetches a row and hop 4 passes it on. A scalar change of the degrees of freedom cannot turn (1 - r) into (1 - r)(1 + r) for every
coefficient at once (the missing factor differs per entry), and fetching a column instead of a row, or transposing the result, gives
the same values (the matrix is symmetric). Declared alternatives (G9): hop 1 uses sampleSize - 1; hop 3 fetches column i; hop 2
transposes the assembled matrix. Each leaves the trigger failing.
Recorded bypasses (edits that replace or pre-transform the gold's data against the documentation, not repairs of the chain):
 B-1 hop 4 passes the squared coefficients (e.g. new ArrayRealVector(coefficients).ebeMultiply(coefficients).getData()); the variant
     gold then returns the original values, but hop 4 and the gold document their argument as the correlation coefficients, and the
     gold still mis-computes the error of a coefficient it is given.
 B-2 hop 4 multiplies the gold's result entry by entry by sqrt(1 + r) (one line with ArrayRealVector operations): a second
     implementation of the missing factor applied to the gold's output; the gold still returns values that are not standard errors.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims only the entries below the diagonal are computed and each is then copied to its mirror position
above the diagonal; the chain computes every entry of every row and copies nothing. It names neither the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: coefficients gives r for every entry and its length sizes the result and bounds the loop; degreesOfFreedom divides v in
     every entry; there is no argument check.
  T2 absent: errors is written per entry and returned; r is read by both factor statements; v is initialised from r, reassigned by
     the product and read by the square root; the cursor i advances in the loop header; no literal-initialised local; no branch.
  T3 absent: no enum, type code, flag or named format; the two factors (1 - r) and (1 + r) are both present, so even read as a
     pair nothing is left out; no named class of values.
  T4 absent: 'Computes the standard errors of correlation coefficients', 'the standard error of the coefficient at index i' and
     '@return a new array holding the standard error of each coefficient' describe the computation in general and the loop
     addresses them; '@param degreesOfFreedom number of degrees of freedom of the estimates' is met by the division; no inline
     comment; identifiers errors, r, v, i name what they hold.
 Variant gold (javadoc, signature, errors array, loop: r = coefficients[i]; v = 1 - r; errors[i] = sqrt(v / degreesOfFreedom);
 return errors):
  T1 absent: coefficients gives r (read by v) and sizes/bounds the loop; degreesOfFreedom divides v; both change every result entry.
  T2 absent: r is read by v; v (initialised to 1 - r, an expression, not a literal) is read by the square root; errors is written
     and returned; i advances in the loop header; there is no decision.
  T3 absent: no enum, type code, flag, parameter set or named format whose member is missing; no two-member pair or range is named
     by the gold's text (the javadoc names no bound or interval of the coefficients), 1 - r is a single arithmetic step and has no
     visible sibling treatment ('No member handled'); no class of values ('finite', 'positive', ...) is named.
  T4 absent: the javadoc phrases are general descriptions of the computation that the loop addresses (like 'the reduced
     fraction'); '@param coefficients correlation coefficients' and '@param degreesOfFreedom number of degrees of freedom of the
     estimates' name no rule the body breaks (the division uses it); no inline comment; no identifier names a property."""

PC = "src/main/java/org/apache/commons/math/stat/correlation/PearsonsCorrelation.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
BMI = "src/main/java/org/apache/commons/math/linear/BigMatrixImpl.java"
ARV = "src/main/java/org/apache/commons/math/linear/ArrayRealVector.java"

GOLD_TEXT = '''/**
 * Computes the standard errors of correlation coefficients.
 * <p>The entry at index i of the returned array is the standard error of
 * the coefficient at index i of <code>coefficients</code>, each coefficient
 * having been estimated with <code>degreesOfFreedom</code> degrees of
 * freedom.</p>
 * @param coefficients correlation coefficients
 * @param degreesOfFreedom number of degrees of freedom of the estimates
 * @return a new array holding the standard error of each coefficient
 */
public static double[] coefficientStandardErrors(double[] coefficients, int degreesOfFreedom) {
    double[] errors = new double[coefficients.length];
    for (int i = 0; i < coefficients.length; ++i) {
        double r = coefficients[i];
        double v = 1 - r;
        v *= 1 + r;
        errors[i] = Math.sqrt(v / degreesOfFreedom);
    }
    return errors;
}'''

HOP1 = '''/**
 * Returns the matrix of standard errors associated with a matrix of
 * correlation coefficients.
 * <p>Entry (i, j) of the result is the standard error of entry (i, j) of
 * <code>correlations</code>, the coefficients having been estimated from
 * <code>sampleSize</code> observations, i.e. with
 * <code>sampleSize - 2</code> degrees of freedom.</p>
 *
 * @param correlations matrix of correlation coefficients
 * @param sampleSize number of observations the coefficients were estimated from
 * @return matrix of standard errors
 */
public static RealMatrix correlationErrors(RealMatrix correlations, int sampleSize) {
    return BlockRealMatrix.createErrorMatrix(correlations, sampleSize - 2);
}'''

HOP2 = '''/**
 * Create a new matrix holding the standard errors of a matrix of
 * correlation coefficients.
 * <p>
 * Row i of the new matrix holds the standard errors of the coefficients
 * in row i of <code>correlations</code>.
 * </p>
 * @param correlations matrix of correlation coefficients
 * @param degreesOfFreedom number of degrees of freedom of the estimates
 * @return a new matrix of standard errors
 */
public static BlockRealMatrix createErrorMatrix(final RealMatrix correlations,
                                                final int degreesOfFreedom) {
    final int rows = correlations.getRowDimension();
    final double[][] errors = new double[rows][];
    for (int i = 0; i < rows; ++i) {
        errors[i] = BlockFieldMatrix.rowErrors(correlations, i, degreesOfFreedom);
    }
    return new BlockRealMatrix(errors);
}'''

HOP3 = '''/**
 * Get the standard errors of the correlation coefficients in one row of
 * a correlation matrix.
 * @param correlations matrix of correlation coefficients
 * @param row index of the row
 * @param degreesOfFreedom number of degrees of freedom of the estimates
 * @return standard errors of the coefficients in the row
 */
public static double[] rowErrors(final RealMatrix correlations, final int row,
                                 final int degreesOfFreedom) {
    return BigMatrixImpl.errorsOfCoefficients(correlations.getRow(row), degreesOfFreedom);
}'''

HOP4 = '''/**
 * Returns the standard errors of an array of correlation coefficients.
 *
 * @param coefficients correlation coefficients
 * @param degreesOfFreedom number of degrees of freedom of the estimates
 * @return array of standard errors, one per coefficient
 */
public static double[] errorsOfCoefficients(double[] coefficients, int degreesOfFreedom) {
    return ArrayRealVector.coefficientStandardErrors(coefficients, degreesOfFreedom);
}'''

DESIGN = {
 "instance": "Math-69", "project": "Math", "bug_id": 69, "seed": 6063,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "private fields correlationMatrix (RealMatrix) and nObs (int), passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [1833, 1687, 1667, 1506, 1239],
 "reachability_probe": "getCorrelationStandardErrors first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-69-probe/w; full suite: 2 failing tests, "
                       "PearsonsCorrelationTest::testStdErrorConsistency (PROBE-REACHED at "
                       "PearsonsCorrelation.getCorrelationStandardErrors(PearsonsCorrelation.java:136) from "
                       "PearsonsCorrelationTest.java:227) and PearsonsCorrelationTest::testCovarianceConsistency (from line 250)",
 "facade": {"file": PC, "class": "org.apache.commons.math.stat.correlation.PearsonsCorrelation",
            "method": "getCorrelationStandardErrors", "near_line": 135},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/math/stat/correlation/PearsonsCorrelationTest.java",
             "test_class": "org.apache.commons.math.stat.correlation.PearsonsCorrelationTest",
             "test_method": "testStdErrorConsistency"},
 "expected_signature": "expected:<0.00509966911319415> but was:<0.01491720061472634>",
 "gold": {"method": "coefficientStandardErrors", "text": GOLD_TEXT,
          "fault": {"old": "            double v = 1 - r;\n"
                           "            v *= 1 + r;\n"
                           "            errors[i] = Math.sqrt(v / degreesOfFreedom);\n",
                    "new": "            double v = 1 - r;\n"
                           "            errors[i] = Math.sqrt(v / degreesOfFreedom);\n"}},
 "chain": {
   "facade_body": "return org.apache.commons.math.util.MathUtils.correlationErrors(correlationMatrix, nObs);",
   "lie": "Only the entries below the diagonal are computed; each of them is then copied to its mirror position above the "
          "diagonal.",
   "hops": [
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "correlationErrors",
      "imports": ["org.apache.commons.math.linear.BlockRealMatrix", "org.apache.commons.math.linear.RealMatrix"], "text": HOP1},
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "createErrorMatrix",
      "imports": [], "text": HOP2},
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "rowErrors",
      "imports": [], "text": HOP3},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "errorsOfCoefficients",
      "imports": [], "text": HOP4},
     {"file": ARV, "class": "org.apache.commons.math.linear.ArrayRealVector", "method": "coefficientStandardErrors",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.stat.correlation.PearsonsCorrelation::getCorrelationPValues",
              "org.apache.commons.math.stat.regression.SimpleRegression::getMeanSquareError",
              "org.apache.commons.math.stat.regression.SimpleRegression::getSlopeStdErr"],
 "ownership_reason": "Only the gold turns a correlation coefficient into its standard error; hop 1 forms the degrees of freedom "
                     "(sample size - 2), hop 2 assembles one row of errors per row of the correlation matrix, hop 3 fetches a row "
                     "and hop 4 passes it on unchanged. The gold's javadoc promises the standard error of each coefficient "
                     "estimated with the given degrees of freedom, which sqrt((1 - r) / dof) is not. No one-line change above the "
                     "gold that keeps the hops' documentation restores the errors: the degrees of freedom are one scalar for all "
                     "entries while the missing factor (1 + r) differs per coefficient, and a column instead of a row or a "
                     "transposed result gives the same values for the symmetric correlation matrix. The convention is pinned "
                     "outside the gold: the facade's javadoc formula SE_r = ((1 - r^2) / (n - 2))^(1/2); "
                     "PearsonsCorrelation.getCorrelationPValues, whose t = |r| ((n - 2) / (1 - r^2))^(1/2) is checked against R "
                     "by PearsonsCorrelationTest testLongly and testSwissFertility; SimpleRegression.getMeanSquareError "
                     "(SSE / (n - 2) with SSE = SYY (1 - r^2)) and getSlopeStdErr, checked against NIST by SimpleRegressionTest "
                     "testNorris.",
 "ownership_tests": ["org.apache.commons.math.stat.correlation.PearsonsCorrelationTest::testLongly",
                     "org.apache.commons.math.stat.correlation.PearsonsCorrelationTest::testSwissFertility",
                     "org.apache.commons.math.stat.regression.SimpleRegressionTest::testNorris"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "return BlockRealMatrix.createErrorMatrix(correlations, sampleSize - 2);",
      "new": "return BlockRealMatrix.createErrorMatrix(correlations, sampleSize - 1);",
      "why": "hop 1 uses one degree of freedom fewer in the estimate"},
     {"file": BFM, "old": "return BigMatrixImpl.errorsOfCoefficients(correlations.getRow(row), degreesOfFreedom);",
      "new": "return BigMatrixImpl.errorsOfCoefficients(correlations.getColumn(row), degreesOfFreedom);",
      "why": "hop 3 reads the coefficients of column i instead of row i"},
     {"file": BRM, "old": "return new BlockRealMatrix(errors);",
      "new": "return new BlockRealMatrix(errors).transpose();",
      "why": "hop 2 places the rows of errors as columns of the result"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch8_tasks.json), in that order, "
               "none substituted: util.MathUtils (hop 1, 1833 lines), linear.BlockRealMatrix (hop 2, 1687), "
               "linear.BlockFieldMatrix (hop 3, 1667; a generic class, the static method uses no type parameter), "
               "linear.BigMatrixImpl (hop 4, 1506), linear.ArrayRealVector (hop 5, gold, 1239; the smallest host). All five "
               "are public top-level classes in which a static method compiles. Anchors from stageB_lib.pick_insertion_anchor "
               "with seed 6063 + 100 + i (as mr3_spec.py inserts them): hop 1 after `lcm` (seed 6163), hop 2 after the "
               "constructor `BlockRealMatrix` (6164), hop 3 after `getRowDimension` (6165), hop 4 after `solve` (6166), hop 5 "
               "after the constructor `ArrayRealVector` (6167); all in the outer class. The facade's class "
               "PearsonsCorrelation (the only allowed-candidate file) is not a host. MathUtils imports RealMatrix and "
               "BlockRealMatrix; hops 2-5 share the package org.apache.commons.math.linear and need no import.",
}
