"""Main run Math-86__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; fixed
checkout of Defects4J Math-86; the real bug modified CholeskyDecompositionImpl, the facade's class). No static pair (B8 note
section 1: pool v2 no_tested_static).

Facade: CholeskyDecompositionImpl.getDeterminant() (instance method; allowed targets CholeskyDecompositionImpl.getDeterminant /
.getLT, BATCH8_PREREGISTRATION.md row 300; facade_planned_by null, no facade reuse). getLT was not used: it is reached by
testDimensions, testAEqualLLT, testLTTransposed, testMatricesValues and (through getL) testLLowerTriangular, so any omission in the
matrix it builds is caught by several tests, and its only other decision (the cache) has no quiet one-line omission that leaves
both of its inputs live (an omitted cache check leaves the cached value unread).
Original computation: the product, over the rows i of the row-oriented storage lTData of L^T, of lTData[i][i] * lTData[i][i] (the
determinant of A = L L^T is the product of the squared diagonal elements of the factor).

facade_variant: V1 (state as parameters). state_passed: the private field lTData (double[][]), handed to hop 1; no field is
written, no write-back. The facade body is one call to hop 1 (the original has no guard). No visibility is widened, no type is
added, no signature, modifier, override or throws change, no reflection, no test edit; the facade calls no private method (no V4)
and no package-private type is involved (no V3/V5).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-86-probe of the fixture, the first statement
of getDeterminant was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.math.linear.CholeskySolverTest::testDeterminant`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at CholeskyDecompositionImpl.getDeterminant(CholeskyDecompositionImpl.java:176),
called from CholeskySolverTest.getDeterminant(CholeskySolverTest.java:135) / testDeterminant(CholeskySolverTest.java:131). (The same
probe on getLT was reached by testDimensions, testAEqualLLT and testMatricesValues.) getDeterminant has no production caller.

Hosts (host_mode = "1500": exactly five other public classes of >= 1500 lines exist; seeded draw `mr_lib.py preview Math-86
org/apache/commons/math/linear/CholeskyDecompositionImpl.java 5`, seed 3492, used in draw order, nothing substituted):
  hop 1 linear.EigenDecompositionImpl 1825 lines  choleskyDeterminant  placement: the diagonal of the factor into an array
  hop 2 util.MathUtils                1598 lines  productOfSquares     pass-through
  hop 3 linear.BigMatrixImpl          1505 lines  squaresProduct       pass-through
  hop 4 linear.DenseFieldMatrix       1621 lines  multiplySquares      pass-through
  hop 5 linear.DenseRealMatrix        1638 lines  squaredProduct       GOLD: one pass over the entries, squaring each and
                                                                       multiplying it into a product held with a separate binary
                                                                       exponent
Host sizes 1825, 1598, 1505, 1621, 1638; the smallest host is BigMatrixImpl (1505 lines); the gold host has 1638 lines.
The correct configuration returns the original's value for every matrix whose running products stay in the normal double range
(scaling by powers of two is exact, so each rounded multiplication gives the same significand as the original's); outside that
range it avoids the original's overflow/underflow. On the trigger matrix it returns exactly 7290000.0 (1 * 9 * 36 * 100 * 225).

Fault (one-line omission inside the gold's iteration): the statement that rescales the running product by its binary exponent
(`product = MathUtils.scalb(product, -e);`) is dropped, while the exponent is still accumulated, so the result is the product
multiplied by 2 to the sum of the running products' exponents. Trigger: the EXISTING test CholeskySolverTest::testDeterminant,
assertEquals(7290000.0, ..., 1.0e-15), fails with expected:<7290000.0> but was:<1.0259762901103411E21> (2^47 times the
determinant: running exponents 0, 3, 8, 14, 22). It is the only test that reaches getDeterminant (the probe), the facade has no
production caller and the new hops have no other caller, so it is the only test that newly fails (gate G5 checks the full suite).
No caller can pre-filter the input (any input with a non-trivial running exponent is affected) or recover the result (the
exponent sum depends on every running product inside the gold).

The gold's javadoc states the idiomatic contract ("the product of the squares of the entries") and is silent on how the product is
held; the variant returns 2^47 times that product on the trigger input. The convention is pinned outside the gold: the intact
siblings LUDecompositionImpl.getDeterminant (the plain product of the factor's diagonal, with the permutation sign) and
EigenDecompositionImpl.getDeterminant (the plain product of the eigenvalues) give the determinant as the product with no extra
factor, and MathUtils.scalb ("d x 2^scaleFactor") fixes that scaling by -e and later by the accumulated exponent cancel; passing
tests LUSolverTest::testDeterminant (determinants -1, -10, 0 through LU), MathUtilsTest::testScalb and
CholeskyDecompositionImplTest::testMatricesValues (the factor's diagonal 1, 3, 6, 10, 15, whose squared product is 7290000).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: values bounds the loop and supplies every factor.
  T2 absent: i is the loop cursor; product is multiplied and rescaled in the loop and returned; e is read by the rescale and by
     the exponent update; exponent is updated in the loop and returned; no branch.
  T3 absent: no enumeration, no pair or range, no named value class; every entry gets the same treatment.
  T4 absent: 'the product of the squares of the entries' and the @param/@return clauses are met by the body; no inline comment;
     identifiers (values, product, exponent, e) name nothing the body does not meet.
 Variant gold (javadoc, signature, the loop with `product *= values[i] * values[i]; final int e = Math.getExponent(product);
 exponent += e;`, `return MathUtils.scalb(product, exponent);`):
  T1 absent: values bounds the loop and supplies every factor; it is not only argument-checked.
  T2 absent: i advances; product is assigned in the loop and returned; e reaches exponent, which is assigned in the loop and
     reaches the return value; no local is dead or frozen; no branch, case or ternary.
  T3 absent: no closed set is involved (no special-value, sign, pair or range treatment at all: 'No member handled').
  T4 absent: the javadoc is a general description ('the product of the squares of the entries') that lines of the body address;
     no rule, limit, bound, value class or case is named; no inline comment; no identifier names a property (no 'scaled',
     'normalised', 'finite').

Single owner: only the gold multiplies the factors and holds the product's exponent; hop 1 only copies the diagonal of the factor
into an array, and hops 2-4 pass the array along and return the gold's value unchanged. Once the gold has returned 2^47 times the
product, no one-line edit of a non-gold hop can remove the factor (it depends on the gold's running products) without
recomputing the product itself. Declared alternatives (G9): hop 1 takes the magnitude of each diagonal element; hop 1 squares the
diagonal elements itself; hop 2 passes a sorted copy of the array. None makes the trigger pass.
Recorded bypasses (each discards the gold's output): B-0 the facade's original body (its own product loop); B-1 hop 1 returns
`Math.pow(new LUDecompositionImpl(MatrixUtils.createRealMatrix(lT)).getDeterminant(), 2)` (the intact LU sibling on the factor).

Lie: the facade's javadoc claims the diagonal elements of L and of L^T are multiplied in two separate passes and the two results
multiplied together; the chain makes one pass over one diagonal and squares each element. It names neither the binary exponent nor
the rescaling nor any hop."""

CDI = "src/java/org/apache/commons/math/linear/CholeskyDecompositionImpl.java"
EDI = "src/java/org/apache/commons/math/linear/EigenDecompositionImpl.java"
MU = "src/java/org/apache/commons/math/util/MathUtils.java"
BMI = "src/java/org/apache/commons/math/linear/BigMatrixImpl.java"
DFM = "src/java/org/apache/commons/math/linear/DenseFieldMatrix.java"
DRM = "src/java/org/apache/commons/math/linear/DenseRealMatrix.java"

GOLD_TEXT = '''/**
 * Returns the product of the squares of the entries of an array.
 * @param values the entries to square and multiply
 * @return the product of the squares of the entries
 */
public static double squaredProduct(final double[] values) {
    double product = 1.0;
    int exponent = 0;
    for (int i = 0; i < values.length; ++i) {
        product *= values[i] * values[i];
        final int e = Math.getExponent(product);
        product = MathUtils.scalb(product, -e);
        exponent += e;
    }
    return MathUtils.scalb(product, exponent);
}'''

HOP1 = '''/**
 * Compute the determinant of a symmetric positive definite matrix from
 * its Cholesky factor.
 * <p>The determinant of A = LL<sup>T</sup> is the product of the squares
 * of the diagonal elements of L<sup>T</sup>.</p>
 * @param lT row-oriented storage for L<sup>T</sup> matrix data
 * @return determinant of the decomposed matrix
 */
public static double choleskyDeterminant(final double[][] lT) {
    final double[] diagonal = new double[lT.length];
    for (int i = 0; i < lT.length; ++i) {
        diagonal[i] = lT[i][i];
    }
    return MathUtils.productOfSquares(diagonal);
}'''

HOP2 = '''/**
 * Returns the product of the squares of the entries of an array.
 *
 * @param values the entries
 * @return the product of the squares of the entries
 */
public static double productOfSquares(final double[] values) {
    return BigMatrixImpl.squaresProduct(values);
}'''

HOP3 = '''/**
 * Returns the product of the squares of the entries of an array.
 *
 * @param values the entries
 * @return the product of the squares of the entries
 */
public static double squaresProduct(final double[] values) {
    return DenseFieldMatrix.multiplySquares(values);
}'''

HOP4 = '''/**
 * Returns the product of the squares of the entries of an array.
 * @param values the entries
 * @return the product of the squares of the entries
 */
public static double multiplySquares(final double[] values) {
    return DenseRealMatrix.squaredProduct(values);
}'''

DESIGN = {
 "instance": "Math-86", "project": "Math", "bug_id": 86, "seed": 3492,
 "src_root": "src/java", "test_root": "src/test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field lTData (double[][]) passed to hop 1; no field written, no write-back",
 "host_mode": "1500", "host_lines": [1825, 1598, 1505, 1621, 1638],
 "reachability_probe": "getDeterminant first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-86-probe: CholeskySolverTest::testDeterminant fails with PROBE-REACHED at "
                       "CholeskyDecompositionImpl.getDeterminant(CholeskyDecompositionImpl.java:176)",
 "facade": {"file": CDI, "class": "org.apache.commons.math.linear.CholeskyDecompositionImpl", "method": "getDeterminant",
            "near_line": 174},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/math/linear/CholeskySolverTest.java",
             "test_class": "org.apache.commons.math.linear.CholeskySolverTest", "test_method": "testDeterminant"},
 "expected_signature": "expected:<7290000.0> but was:<1.02597",
 "gold": {"method": "squaredProduct", "text": GOLD_TEXT,
          "fault": {"old": "            product = MathUtils.scalb(product, -e);\n            exponent += e;",
                    "new": "            exponent += e;"}},
 "chain": {
   "facade_body": "return EigenDecompositionImpl.choleskyDeterminant(lTData);",
   "lie": "The diagonal elements of L and of L<sup>T</sup> are multiplied in two separate passes, and the determinant is the "
          "product of the two results.",
   "hops": [
     {"file": EDI, "class": "org.apache.commons.math.linear.EigenDecompositionImpl", "method": "choleskyDeterminant",
      "imports": ["org.apache.commons.math.util.MathUtils"], "text": HOP1},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "productOfSquares",
      "imports": ["org.apache.commons.math.linear.BigMatrixImpl"], "text": HOP2},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "squaresProduct",
      "imports": [], "text": HOP3},
     {"file": DFM, "class": "org.apache.commons.math.linear.DenseFieldMatrix", "method": "multiplySquares",
      "imports": [], "text": HOP4},
     {"file": DRM, "class": "org.apache.commons.math.linear.DenseRealMatrix", "method": "squaredProduct",
      "imports": ["org.apache.commons.math.util.MathUtils"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.linear.LUDecompositionImpl::getDeterminant",
              "org.apache.commons.math.linear.EigenDecompositionImpl::getDeterminant",
              "org.apache.commons.math.util.MathUtils::scalb"],
 "ownership_reason": "Only the gold multiplies the factors and holds the product's binary exponent: hop 1 copies the diagonal of "
                     "the Cholesky factor L^T into an array, and hops 2-4 pass the array along and return the gold's value "
                     "unchanged. The gold's javadoc promises the product of the squares of the entries; the variant returns that "
                     "product times 2 to the sum of its running exponents (2^47 on the trigger matrix), a factor that depends on "
                     "every running product inside the gold, so no caller can pre-filter the entries or recover the product without "
                     "recomputing it. The convention is pinned outside the gold: the intact siblings LUDecompositionImpl."
                     "getDeterminant and EigenDecompositionImpl.getDeterminant give a determinant as the plain product of a "
                     "factor's diagonal or of the eigenvalues, with no extra factor, and MathUtils.scalb (d x 2^scaleFactor) fixes "
                     "that scaling by -e and later by the accumulated exponent cancel; LUSolverTest::testDeterminant, "
                     "MathUtilsTest::testScalb and CholeskyDecompositionImplTest::testMatricesValues (the factor's diagonal 1, 3, "
                     "6, 10, 15) pass.",
 "ownership_tests": ["org.apache.commons.math.linear.LUSolverTest::testDeterminant",
                     "org.apache.commons.math.util.MathUtilsTest::testScalb",
                     "org.apache.commons.math.linear.CholeskyDecompositionImplTest::testMatricesValues"],
 "compensating": {
   "chain": [
     {"file": EDI, "old": "diagonal[i] = lT[i][i];",
      "new": "diagonal[i] = Math.abs(lT[i][i]);",
      "why": "hop 1 takes the magnitude of each diagonal element"},
     {"file": EDI, "old": "diagonal[i] = lT[i][i];",
      "new": "diagonal[i] = lT[i][i] * lT[i][i];",
      "why": "hop 1 squares the diagonal elements itself"},
     {"file": MU, "old": "return BigMatrixImpl.squaresProduct(values);",
      "new": "final double[] sorted = values.clone(); Arrays.sort(sorted); return BigMatrixImpl.squaresProduct(sorted);",
      "why": "hop 2 passes a sorted copy of the entries"},
   ],
 },
 "host_notes": "host_mode 1500 (batch8_tasks.json; exactly five other public classes of >= 1500 lines on the checkout). Hosts are "
               "the recipe's seeded draw `mr_lib.py preview Math-86 org/apache/commons/math/linear/CholeskyDecompositionImpl.java 5` "
               "(seed 3492), used in draw order, none substituted: linear.EigenDecompositionImpl (hop 1, 1825 lines, anchor after "
               "getSolver, seed 3592), util.MathUtils (hop 2, 1598, after equals, 3593), linear.BigMatrixImpl (hop 3, 1505, after "
               "subtract, 3594; the smallest host), linear.DenseFieldMatrix (hop 4, 1621, after getColumnVector, 3595), "
               "linear.DenseRealMatrix (hop 5, gold, 1638, after getColumnVector, 3596). The draw notes that the package-"
               "distinctness constraints were relaxed (pool of exactly five). All five are public concrete top-level classes in "
               "which a public static method compiles (DenseFieldMatrix is generic; the static hop uses only double[]). The facade "
               "calls hop 1 by its simple name (same package); hop 2 imports linear.BigMatrixImpl; hops 3 and 4 call classes of "
               "their own package; the gold imports util.MathUtils (hop 1's host already imports it).",
}
