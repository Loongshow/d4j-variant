"""Main run Math-13__i (cell C10i, batch 9, sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Math-13, a bug with no usable static facade; the real bug modified
org.apache.commons.math3.optimization.general.AbstractLeastSquaresOptimizer, the facade's class). No static pair (B8 note section 1).

Facade: AbstractLeastSquaresOptimizer.guessParametersErrors() (instance method; allowed targets
AbstractLeastSquaresOptimizer.guessParametersErrors / .computeSigma, BATCH9_PREREGISTRATION.md rank 367; facade_planned_by null for
both, no facade reuse). computeSigma was not used: its only test in the general package, AbstractLeastSquaresOptimizerTest::
testComputeSigma, is excluded from the Defects4J run suite (Math.build.xml excludes **/*Abstract*Test.java), so no test of the full
suite reaches it and gate G5 cannot pass with it. guessParametersErrors is reached by LevenbergMarquardtOptimizerTest::
testCircleFitting2 (its value check) and by testTrivial of LevenbergMarquardtOptimizerTest and GaussNewtonOptimizerTest (its argument
check only).
Original computation: if rows <= cols, NumberIsTooSmallException(NO_DEGREES_OF_FREEDOM, rows, cols, false); otherwise
c = sqrt(getChiSquare() / (rows - cols)); covar = computeCovariances(point, 1e-14), i.e. the weighted Jacobian
J = computeWeightedJacobian(point) (protected; it counts one Jacobian evaluation), the normal matrix J^T J = j.transpose().multiply(j)
and its inverse by new QRDecomposition(jTj, 1e-14).getSolver().getInverse(); then errors[i] = sqrt(covar[i][i]) * c for the cols
parameters (cols = point.length, rows = the number of observations = the Jacobian's rows).

facade_variant: V1+V4. V1: the protected fields rows and cols and the value of the public getChiSquare() are read in the facade and
passed to hop 1. V4 (pre-compute the non-public helper): the computation reaches the Jacobian through the protected
computeWeightedJacobian(double[]), which hops in other packages cannot call; the facade calls it once on the protected field point (so
getJacobianEvaluations() counts exactly as before) and passes the resulting RealMatrix down, with the original singularity threshold
1e-14. The facade keeps the original argument check and that much computation, nothing else. state_passed: computeWeightedJacobian(
point), getChiSquare(), rows, cols, 1e-14, handed to hop 1; no field is written, no write-back. No visibility is widened, no type is
added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The chain re-implements the steps of
the public computeCovariances (normal matrix, QR inverse with the threshold) without calling or copying any private code;
computeCovariances, getCovariances and computeSigma stay intact.

Redistribution of the computation: hop 1 multiplies the deviations it receives by the residual factor sqrt(chiSquare / (observations -
parameters)) (the original c); hop 2 passes the Jacobian along; hop 3 forms the normal matrix J^T J exactly as computeCovariances does
(jacobian.transpose().multiply(jacobian)); hop 4 hands its entries to the gold; the gold (hop 5) does the per-parameter core: it
equilibrates the normal matrix (each entry divided by the square roots of the diagonal entries of its row and column, a unit-diagonal
matrix, the usual conditioning step for parameters of very different magnitudes), takes its inverse by QR with the threshold, and
derives each parameter's deviation from the diagonal of the inverse, sqrt(inverse[i][i]) / scale[i]. Since inverse(D^-1 A D^-1) =
D inverse(A) D, this is sqrt(inverse(A)[i][i]), the original value up to rounding (on Kirby2, measured in a scratch copy, relative
differences below 1.3e-8 from the original's ill-conditioned inversion; the original errors of the trigger's circle fit are 6.0466,
4.1722, 3.5135, and the trigger passes on the correct configuration, gate G1). The QR singularity decision is taken on the equilibrated matrix instead of J^T J; guessParametersErrors has no caller
in production code, and the only suite tests that pass its argument check are the trigger's.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-13-probe of the fixture, the first statement of
both allowed facades was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.math3.optimization.general.LevenbergMarquardtOptimizerTest::testCircleFitting2`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at AbstractLeastSquaresOptimizer.guessParametersErrors(AbstractLeastSquaresOptimizer.
java:372); LevenbergMarquardtOptimizerTest::testTrivial fails the same way. (computeSigma: AbstractLeastSquaresOptimizerTest::
testComputeSigma fails with PROBE-REACHED at computeSigma(AbstractLeastSquaresOptimizer.java:403) when run alone, but that class is
not in the run suite.) The facade is reached directly by the trigger.

Hosts (host_mode = "1500"; the recipe's seeded draw `mr_lib.py preview Math-13
org/apache/commons/math3/optimization/general/AbstractLeastSquaresOptimizer.java 5`, seed 5885, used in draw order, none substituted;
both allowed facades are in this file, so the draw is the same for either):
  hop 1 dfp.Dfp                                        2506 lines  parameterErrors       aggregation: residual factor times each deviation
  hop 2 optim.nonlinear.scalar.noderiv.BOBYQAOptimizer 2481 lines  fitDeviations         plumbing: passes the weighted Jacobian along
  hop 3 linear.BlockRealMatrix                         1582 lines  jacobianDeviations    aggregation: forms the normal matrix J^T J
  hop 4 optimization.direct.BOBYQAOptimizer            2487 lines  normalDeviations      placement: hands the normal matrix's entries on
  hop 5 linear.BlockFieldMatrix                        1592 lines  deviationsFromNormal  GOLD: equilibration, QR inverse, per-parameter
                                                                                         deviation
Host sizes 2506, 2481, 1582, 2487, 1592; the smallest host is linear.BlockRealMatrix (1582 lines).

Fault (one-line omission in the gold's per-parameter iteration): the division by the parameter's scale is dropped,
`deviations[i] = FastMath.sqrt(inverse[i][i]) / scale[i];` becomes `deviations[i] = FastMath.sqrt(inverse[i][i]);`, so the gold
returns the square roots of the diagonal of the inverse of the equilibrated matrix (sqrt(A[i][i] * inverse(A)[i][i]), at least 1 and
of the order of 1 for a well-posed fit) instead of the parameters' deviations. The gold still reads as a complete routine: the scales
are computed and used, the inverse is taken, and every deviation is the square root of a diagonal entry of the inverse. Trigger: the
EXISTING test org.apache.commons.math3.optimization.general.LevenbergMarquardtOptimizerTest::testCircleFitting2, which checks that the
fitted centre and radius lie within the asymptotic standard errors of the true ones; the errors shrink from 6.05, 4.17, 3.51 to about
the residual factor 0.80 times sqrt(A[i][i] * inverse(A)[i][i]), below the actual distances 3.19, 2.56, 2.37, and the test fails at its
first assertion with "expected:<123.456> but was:<126.64669415982172>". It is the only test of the run suite that passes the facade's
argument check (testTrivial stops at it); gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract ("Computes the standard deviations of the parameters of a least-squares fit from its
normal matrix"; "@return the standard deviation of each parameter") and is silent on how the deviations are derived from the inverse
beyond "from the diagonal of the inverse". The standard deviation of a fitted parameter is the square root of the diagonal entry of
the covariance matrix inverse(J^T J); the variant returns that of the equilibrated matrix, which is not the covariance of the
parameters. The convention is pinned outside the gold: the facade's own javadoc (sd(a[i]) = sqrt(S / (n - m) * C[i][i]), C the
covariance matrix), the intact computeSigma of the same class (sqrt(cov[i][i])), the intact computeCovariances (C = inverse of J^T J
by QR) and the intact sibling org.apache.commons.math3.optim.nonlinear.vector.jacobian.AbstractLeastSquaresOptimizer.computeSigma (the
same sqrt(cov[i][i]) loop); passing tests: LevenbergMarquardtOptimizerTest::testCircleFitting and GaussNewtonOptimizerTest::
testCircleFitting (computeCovariances entries 1.839, 0.731, 0.786), optim.nonlinear.vector.jacobian.LevenbergMarquardtOptimizerTest::
testCircleFitting2 (the sibling's computeSigma on the same circle problem), AbstractLeastSquaresOptimizerTest::testComputeSigma
(computeSigma on Kirby2, run on its own).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: normal supplies n, the scales and every equilibrated entry; threshold goes to the QR decomposition (it decides
     singularity); neither is only argument-checked.
  T2 absent: n bounds the loops; scale is read by the equilibration and by the deviations; equilibrated is decomposed; inverse is read
     by the deviations; deviations is returned; i and j are loop cursors that advance; no branch.
  T3 absent: each entry is divided by the scales of both its row and its column (both halves of the pair); every parameter gets a
     scale and a deviation; no class named in the gold's text is handled in part.
  T4 absent: 'equilibrated ... each entry is divided by the square roots of the diagonal entries of its row and of its column' is met by
     the double loop; 'The inverse of the equilibrated matrix is computed with a QR decomposition with the given singularity threshold'
     is met; 'derived from the diagonal of the inverse' is met; the @throws clause is the QR solver's SingularMatrixException; 'one row
     and one column per parameter' is a caller precondition.
 Variant gold (javadoc, signature, the three loops, the QR inverse, `deviations[i] = FastMath.sqrt(inverse[i][i]);`):
  T1 absent: normal supplies n, the scales and the equilibrated entries; threshold decides the decomposition; both change the result.
  T2 absent: scale is still read by the equilibration (scale[i] * scale[j]), which reaches the inverse and the returned deviations;
     equilibrated, inverse and deviations are all live; i and j advance; no local is frozen (none is a literal that is tested or
     returned; every cursor moves); no decision exists, so none is dead.
  T3 absent: row and column scales are both applied in the equilibration; every parameter's deviation is written by the same
     statement; the gold names no class (no 'finite', no special values) and handles no member of any set in part.
  T4 absent: every phrase of the javadoc is met by a line of the body ('equilibrated', 'divided by the square roots of the diagonal
     entries of its row and of its column', 'computed with a QR decomposition', 'with the given singularity threshold', 'derived from
     the diagonal of the inverse', the @throws clause); 'the standard deviation of each parameter' is the general description of what
     the method computes, which the final loop addresses; no inline comment; identifiers (n, scale, equilibrated, inverse, deviations)
     name nothing the body does not meet.

Single owner: only the gold turns the normal matrix into deviations; hop 1 applies the residual factor its javadoc states, hop 2 passes
the Jacobian along, hop 3 forms J^T J, hop 4 passes its entries. The variant's output sqrt(A[i][i] * inverse(A)[i][i]) is invariant
under any rescaling of the parameters (equilibration removes it), so no caller can pre-scale the Jacobian or the normal matrix to
recover the deviations; recovering them requires dividing each of the gold's outputs by sqrt(A[i][i]), a second implementation of the
gold's per-parameter scale that no hop's documentation allows (see bypass B-1 below). Because the trigger only checks
that the errors are large enough, an edit that inflates every error would pass it: in hop 1 that means changing the residual factor
its javadoc states (sqrt(chiSquare / (observations - parameters))), in the facade changing the arguments its javadoc's formula fixes
(S, n, m); each contradicts that documentation, and none restores the per-parameter deviations. Declared alternatives (G9): hop 1
normalises the Jacobian by its Frobenius norm; hop 3 hands down the covariance matrix (the QR inverse of J^T J) instead of J^T J; hop 2
drops the singularity threshold to 0. None makes the trigger pass (the first leaves the equilibrated matrix unchanged; the second gives
sqrt(C[i][i] * inverse(C)[i][i]) = the same values; the third changes no decision on this fit).
Recorded bypasses: B-0 the facade's original body (computeCovariances and the sqrt loop), or a multi-line loop in hop 1-4 that computes
sqrt(C[i][i]) itself, discards the gold. B-1 a one-line edit of hop 1's loop, `errors[i] *= factor / jacobian.getColumnVector(i).getNorm();`
(the norm of the Jacobian's i-th column is sqrt(A[i][i])), passes the trigger and the ownership tests on the variant: it contradicts hop
1's javadoc (each deviation is multiplied by the residual factor, nothing else) and hop 2's (hop 1's errors are the deviations it
receives), and it re-computes the gold's per-parameter scale outside the gold, so it is a bypass of the gold's step, not a repair at
another hop; it is not declared in compensating.chain (G9 would correctly report that it absorbs the fault).

Lie: one procedural sentence in the facade's own voice, at the end of the first paragraph of its javadoc, after the definition of
sd(a[i]): "The diagonal entries {@code C[i][i]} are obtained from a Cholesky decomposition of <code>J<sup>T</sup>J</code>." No step of
the chain performs a Cholesky decomposition (the chain takes a QR inverse and square roots of its diagonal). It names neither the
scaling nor any hop nor the gold. Placement: guessParametersErrors carries the annotation @Deprecated between its javadoc and its
header, which stageB_lib.replace_method_body / chain_transform.rewrite_facade does not look past (find_javadoc_start requires only
whitespace between the javadoc's end and the header), so the sentence is added by a documentation-only pre_edit of the chain geometry
(behaviour-preserving, applied before the recipe and folded into the context edits); chain.lie holds the same sentence for the record,
and the recipe's own append finds no adjacent javadoc and adds nothing, so the sentence occurs exactly once (checked in the spec's
context edits). The javadoc's existing text, including the @deprecated note, is unchanged."""

ALSO = "src/main/java/org/apache/commons/math3/optimization/general/AbstractLeastSquaresOptimizer.java"
DFP = "src/main/java/org/apache/commons/math3/dfp/Dfp.java"
BOB2 = "src/main/java/org/apache/commons/math3/optim/nonlinear/scalar/noderiv/BOBYQAOptimizer.java"
BRM = "src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java"
BOB1 = "src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java"
BFM = "src/main/java/org/apache/commons/math3/linear/BlockFieldMatrix.java"

GOLD_TEXT = '''/**
 * Computes the standard deviations of the parameters of a least-squares
 * fit from its normal matrix.
 *
 * <p>The normal matrix is equilibrated before it is decomposed: each entry
 * is divided by the square roots of the diagonal entries of its row and of
 * its column, which keeps the decomposition well conditioned when the
 * parameters have very different magnitudes. The inverse of the
 * equilibrated matrix is computed with a QR decomposition with the given
 * singularity threshold, and the deviations are derived from the diagonal
 * of the inverse.</p>
 *
 * @param normal the normal matrix J<sup>T</sup>J of the fit, one row and
 * one column per parameter
 * @param threshold the singularity threshold of the QR decomposition
 * @return the standard deviation of each parameter
 * @throws SingularMatrixException if the equilibrated matrix is singular
 */
public static double[] deviationsFromNormal(final double[][] normal, final double threshold) {
    final int n = normal.length;
    final double[] scale = new double[n];
    for (int i = 0; i < n; i++) {
        scale[i] = FastMath.sqrt(normal[i][i]);
    }
    final double[][] equilibrated = new double[n][n];
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            equilibrated[i][j] = normal[i][j] / (scale[i] * scale[j]);
        }
    }
    final double[][] inverse =
        new QRDecomposition(MatrixUtils.createRealMatrix(equilibrated), threshold).getSolver().getInverse().getData();
    final double[] deviations = new double[n];
    for (int i = 0; i < n; i++) {
        deviations[i] = FastMath.sqrt(inverse[i][i]) / scale[i];
    }
    return deviations;
}'''

HOP1 = '''/**
 * Computes the asymptotic standard errors of the parameters of a
 * least-squares fit from its weighted Jacobian and its chi-square.
 *
 * <p>The standard deviation of each parameter is multiplied by the
 * residual factor sqrt(chiSquare / (observations - parameters)), the
 * square root of the chi-square per degree of freedom.</p>
 *
 * @param jacobian the weighted Jacobian of the fit, one row per
 * observation and one column per parameter
 * @param chiSquare the chi-square of the fit
 * @param observations the number of observations
 * @param parameters the number of parameters, less than the number of
 * observations
 * @param threshold the singularity threshold of the decomposition
 * @return the asymptotic standard error of each parameter
 * @throws org.apache.commons.math3.linear.SingularMatrixException if the
 * covariance matrix cannot be computed
 */
public static double[] parameterErrors(final RealMatrix jacobian, final double chiSquare,
                                       final int observations, final int parameters,
                                       final double threshold) {
    final double[] errors = BOBYQAOptimizer.fitDeviations(jacobian, threshold);
    final double factor = FastMath.sqrt(chiSquare / (observations - parameters));
    for (int i = 0; i < errors.length; i++) {
        errors[i] *= factor;
    }
    return errors;
}'''

HOP2 = '''/**
 * Computes the standard deviations of the parameters of a least-squares
 * fit from its weighted Jacobian.
 *
 * @param jacobian Weighted Jacobian of the fit (one row per observation,
 * one column per parameter).
 * @param threshold Singularity threshold of the decomposition.
 * @return the standard deviation of each parameter.
 */
public static double[] fitDeviations(RealMatrix jacobian, double threshold) {
    return BlockRealMatrix.jacobianDeviations(jacobian, threshold);
}'''

HOP3 = '''/**
 * Computes the standard deviations of the parameters of a least-squares
 * fit from its weighted Jacobian J, through the normal matrix
 * J<sup>T</sup>J.
 *
 * @param jacobian weighted Jacobian (one row per observation, one column
 * per parameter)
 * @param threshold singularity threshold of the decomposition
 * @return the standard deviation of each parameter
 */
public static double[] jacobianDeviations(final RealMatrix jacobian, final double threshold) {
    final RealMatrix normal = jacobian.transpose().multiply(jacobian);
    return BOBYQAOptimizer.normalDeviations(normal, threshold);
}'''

HOP4 = '''/**
 * Computes the standard deviations of the parameters of a least-squares
 * fit from its normal matrix.
 *
 * @param normal Normal matrix J<sup>T</sup>J of the fit.
 * @param threshold Singularity threshold of the decomposition.
 * @return the standard deviation of each parameter.
 */
public static double[] normalDeviations(RealMatrix normal, double threshold) {
    return BlockFieldMatrix.deviationsFromNormal(normal.getData(), threshold);
}'''

DESIGN = {
 "instance": "Math-13", "project": "Math", "bug_id": 13, "seed": 5885,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1+V4",
 "state_passed": "the weighted Jacobian computeWeightedJacobian(point) (protected helper, called once in the facade), "
                 "getChiSquare(), the protected fields rows and cols and the singularity threshold 1e-14, passed to hop 1; "
                 "no field written, no write-back",
 "host_mode": "1500", "host_lines": [2506, 2481, 1582, 2487, 1592],
 "reachability_probe": "guessParametersErrors first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-13-probe: LevenbergMarquardtOptimizerTest::testCircleFitting2 (and ::testTrivial) "
                       "fail with PROBE-REACHED at AbstractLeastSquaresOptimizer.guessParametersErrors(AbstractLeastSquaresOptimizer.java:372)",
 "facade": {"file": ALSO, "class": "org.apache.commons.math3.optimization.general.AbstractLeastSquaresOptimizer",
            "method": "guessParametersErrors", "near_line": 371},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/math3/optimization/general/LevenbergMarquardtOptimizerTest.java",
             "test_class": "org.apache.commons.math3.optimization.general.LevenbergMarquardtOptimizerTest",
             "test_method": "testCircleFitting2"},
 "expected_signature": "expected:<123.456> but was:<",
 "gold": {"method": "deviationsFromNormal", "text": GOLD_TEXT,
          "fault": {"old": "            deviations[i] = FastMath.sqrt(inverse[i][i]) / scale[i];",
                    "new": "            deviations[i] = FastMath.sqrt(inverse[i][i]);"}},
 "pre_edits": {
   "chain": [{"file": ALSO,
              "old": "     * covariance matrix.\n"
                     "     * </p>\n"
                     "     * <p>\n"
                     "     * See also\n",
              "new": "     * covariance matrix. The diagonal entries {@code C[i][i]} are obtained\n"
                     "     * from a Cholesky decomposition of <code>J<sup>T</sup>J</code>.\n"
                     "     * </p>\n"
                     "     * <p>\n"
                     "     * See also\n"}],
 },
 "chain": {
   "facade_body": "if (rows <= cols) {\n            throw new NumberIsTooSmallException(LocalizedFormats.NO_DEGREES_OF_FREEDOM,\n"
                  "                                                rows, cols, false);\n        }\n"
                  "        return org.apache.commons.math3.dfp.Dfp.parameterErrors(computeWeightedJacobian(point), getChiSquare(), "
                  "rows, cols, 1e-14);",
   "lie": "The diagonal entries {@code C[i][i]} are obtained from a Cholesky decomposition of <code>J<sup>T</sup>J</code>.",
   "hops": [
     {"file": DFP, "class": "org.apache.commons.math3.dfp.Dfp", "method": "parameterErrors",
      "imports": ["org.apache.commons.math3.linear.RealMatrix",
                  "org.apache.commons.math3.optim.nonlinear.scalar.noderiv.BOBYQAOptimizer",
                  "org.apache.commons.math3.util.FastMath"], "text": HOP1},
     {"file": BOB2, "class": "org.apache.commons.math3.optim.nonlinear.scalar.noderiv.BOBYQAOptimizer", "method": "fitDeviations",
      "imports": ["org.apache.commons.math3.linear.BlockRealMatrix", "org.apache.commons.math3.linear.RealMatrix"], "text": HOP2},
     {"file": BRM, "class": "org.apache.commons.math3.linear.BlockRealMatrix", "method": "jacobianDeviations",
      "imports": ["org.apache.commons.math3.optimization.direct.BOBYQAOptimizer"], "text": HOP3},
     {"file": BOB1, "class": "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer", "method": "normalDeviations",
      "imports": ["org.apache.commons.math3.linear.BlockFieldMatrix", "org.apache.commons.math3.linear.RealMatrix"], "text": HOP4},
     {"file": BFM, "class": "org.apache.commons.math3.linear.BlockFieldMatrix", "method": "deviationsFromNormal",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.optimization.general.AbstractLeastSquaresOptimizer::computeSigma",
              "org.apache.commons.math3.optimization.general.AbstractLeastSquaresOptimizer::computeCovariances",
              "org.apache.commons.math3.optim.nonlinear.vector.jacobian.AbstractLeastSquaresOptimizer::computeSigma"],
 "ownership_reason": "Only the gold turns the normal matrix into the parameters' deviations: hop 1 multiplies them by the residual "
                     "factor sqrt(chiSquare / (observations - parameters)) that its javadoc states, hop 2 passes the weighted "
                     "Jacobian along, hop 3 forms J^T J exactly as computeCovariances does, hop 4 passes its entries on. The gold "
                     "equilibrates the normal matrix, takes its inverse by QR and derives each deviation from the diagonal of the "
                     "inverse; the variant omits the division by the parameter's scale, so it returns sqrt(A[i][i] * "
                     "inverse(A)[i][i]), which is invariant under any rescaling of the parameters: no caller can pre-scale its "
                     "input to recover the deviations, and recovering them afterwards needs a second, per-parameter implementation "
                     "of the gold's step. The gold's javadoc promises the standard deviation of each parameter, the square root of "
                     "the diagonal entry of the covariance matrix inverse(J^T J). The convention is pinned outside the gold: the "
                     "facade's javadoc (sd(a[i]) = sqrt(S / (n - m) * C[i][i]), C the covariance matrix), the intact computeSigma of "
                     "the same class (sqrt(cov[i][i])), the intact computeCovariances (C = QR inverse of J^T J) and the intact "
                     "sibling optim.nonlinear.vector.jacobian.AbstractLeastSquaresOptimizer.computeSigma; the testCircleFitting "
                     "covariance checks, the sibling's testCircleFitting2 (computeSigma on the same circle problem) and "
                     "testComputeSigma (Kirby2, NIST certified deviations) pass.",
 "ownership_tests": ["org.apache.commons.math3.optimization.general.LevenbergMarquardtOptimizerTest::testCircleFitting",
                     "org.apache.commons.math3.optimization.general.GaussNewtonOptimizerTest::testCircleFitting",
                     "org.apache.commons.math3.optim.nonlinear.vector.jacobian.LevenbergMarquardtOptimizerTest::testCircleFitting2",
                     "org.apache.commons.math3.optimization.general.AbstractLeastSquaresOptimizerTest::testComputeSigma"],
 "compensating": {
   "chain": [
     {"file": DFP, "old": "        final double[] errors = BOBYQAOptimizer.fitDeviations(jacobian, threshold);",
      "new": "        final double[] errors = BOBYQAOptimizer.fitDeviations(jacobian.scalarMultiply(1.0 / jacobian.getFrobeniusNorm()), threshold);",
      "why": "hop 1 normalises the Jacobian by its Frobenius norm"},
     {"file": BRM, "old": "        final RealMatrix normal = jacobian.transpose().multiply(jacobian);",
      "new": "        final RealMatrix normal = new QRDecomposition(jacobian.transpose().multiply(jacobian), threshold).getSolver().getInverse();",
      "why": "hop 3 hands down the covariance matrix instead of the normal matrix"},
     {"file": BOB2, "old": "        return BlockRealMatrix.jacobianDeviations(jacobian, threshold);",
      "new": "        return BlockRealMatrix.jacobianDeviations(jacobian, 0);",
      "why": "hop 2 drops the singularity threshold"},
   ],
 },
 "host_notes": "host_mode 1500: hosts from the recipe's seeded draw (mr_lib.py preview Math-13 "
               "org/apache/commons/math3/optimization/general/AbstractLeastSquaresOptimizer.java 5, seed 5885; the facade's file "
               "is excluded; FastMathLiteralArrays is marked unusable by the pool), in draw order, none substituted: dfp.Dfp (hop 1, "
               "2506 lines), optim.nonlinear.scalar.noderiv.BOBYQAOptimizer (hop 2, 2481), linear.BlockRealMatrix (hop 3, 1582, the "
               "smallest host), optimization.direct.BOBYQAOptimizer (hop 4, 2487), linear.BlockFieldMatrix (hop 5, gold, 1592). "
               "Anchors (seed 5885 + 100 + i, as mr3_spec.py inserts them): hop 1 after newInstance (5985), hop 2 after the "
               "BOBYQAOptimizer constructor (5986), hop 3 after getRow (5987), hop 4 after the BOBYQAOptimizer constructor (5988), "
               "hop 5 after scalarMultiply (5989). The two BOBYQAOptimizer classes share a simple name; each hop imports only the one "
               "it calls (hop 1 the optim.nonlinear one, hop 3 the optimization.direct one). The gold is a static, non-generic method "
               "in the generic BlockFieldMatrix and uses QRDecomposition and MatrixUtils from its own package and the imported "
               "FastMath. The facade calls hop 1 by its fully-qualified name.",
}
