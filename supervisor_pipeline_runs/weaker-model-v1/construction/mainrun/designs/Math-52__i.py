"""Main run Math-52__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade on a bug that has no static facade; fixed
checkout of Defects4J Math-52; the real bug modified geometry.euclidean.threed.Rotation, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE.md section 1: pool v2 no_tested_static).

Facade: Rotation.getMatrix() (instance method; allowed targets Rotation.getMatrix / Rotation.applyInverseTo / Rotation.applyTo,
BATCH8_PREREGISTRATION.md row 291; facade_planned_by null for all three; no facade reuse). getMatrix carries the whole computation
(products of the quaternion coordinates and the nine entries) and is called by no production code and by exactly one test,
RotationTest::testMatrix. applyTo(Vector3D) and applyInverseTo(Vector3D) were not used: they are called by production code
(getAngles, Plane.rotate, PolyhedronsSet) and by most tests of the package, so no omission in their computation is caught by a
single test; they stay intact and serve as the convention's production pins.
Original computation: the matrix of the rotation of the normalized quaternion (q0, q1, q2, q3) as three new rows; diagonal entry
m[i][i] = 2 (q0 q0 + qi qi) - 1; off-diagonal entry m[i][j] = 2 (qi qj + q0 qk) when (i, j, k) is a cyclic order of the vectorial
indices and 2 (qi qj - q0 qk) otherwise (m[0][1] = 2 (q1q2 + q0q3), m[1][0] = 2 (q1q2 - q0q3), ...). Column j is the image of the
j-th canonical vector by applyTo.

facade_variant: V1 (state as parameters). state_passed: the four private final fields q0, q1, q2, q3, read in the facade and handed
to hop 1 as values; no field is written, no write-back. The facade body is one call to hop 1 (the original had no guard). No
visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The
computation calls no private method of Rotation, so V4 does not apply; no package-private type is involved, so neither V3 nor V5.

Redistribution of the computation: hop 1 packs the vectorial part into an array (plumbing); hop 2 allocates the matrix and places one
row per index (aggregation over rows); hop 3 allocates one row (placement); hop 4 fills the row, one entry per column (fold over
columns); the gold computes one entry from the quaternion and the entry's indices (the per-element core: the diagonal form, and for
an off-diagonal entry the product of the two vectorial coordinates plus or minus the scalar part times the third coordinate, the sign
decided by the index order). The correct configuration returns the original matrix bit for bit for every quaternion: each entry is
the same IEEE expression as in the original (2.0 * (a + b) - 1.0 on the diagonal, 2.0 * (a + b) or 2.0 * (a + (-b)), which equals
2.0 * (a - b), elsewhere; products of two doubles commute exactly).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-52-probe of the fixture, the first statement
of getMatrix() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.math.geometry.euclidean.threed.RotationTest::testMatrix`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at Rotation.getMatrix(Rotation.java:797), called from RotationTest.testMatrix(RotationTest.java:226). The facade is
reached directly by the trigger.

Hosts (host_mode = "1500": the recipe's seeded draw `mr_lib.py preview Math-52
org/apache/commons/math/geometry/euclidean/threed/Rotation.java 5`, seed 6150; the pool is exactly the five public classes of at
least 1,500 lines other than Rotation; none substituted):
  hop 1 util.MathUtils          2611 lines  rotationMatrix   plumbing: packs (q1, q2, q3) into the vectorial part
  hop 2 dfp.Dfp                 2489 lines  rotationRows     aggregation: allocates the matrix, one row per index
  hop 3 linear.BlockFieldMatrix 1549 lines  rotationRow      placement: allocates one row and has it filled
  hop 4 util.FastMath           4077 lines  fillRotationRow  fold: one entry per column of the row
  hop 5 linear.BlockRealMatrix  1536 lines  rotationEntry    GOLD: one entry of the matrix
Host sizes in hop order 2611, 2489, 1549, 4077, 1536; the smallest host (and the gold host) has 1536 lines.

Fault (one-line omission of a decision in the gold): the index-order sign decision of the off-diagonal term is dropped
(`return 2.0 * (v[row] * v[column] + ((column == (row + 1) % 3) ? twist : -twist));` becomes
`return 2.0 * (v[row] * v[column] + twist);`), so every off-diagonal entry adds the scalar-part term with the same sign and the three
entries whose indices are not in cyclic order (m[1][0], m[2][1], m[0][2]) take the value of their mirror entries. The gold then reads as the
ordinary routine "diagonal form on the diagonal, product plus scalar-part term elsewhere". Trigger: the EXISTING test
RotationTest::testMatrix; on the rotation built from m2 it asserts that every entry of getMatrix() is within 6.0e-6 of m2; the first
changed entry checked, d02 (m[0][2]), is off by 4 q0 q2 (about 0.34) and the assertion at RotationTest.java:239 fails
(junit.framework.AssertionFailedError at RotationTest.testMatrix(RotationTest.java:239), checked with mr3_spec.py --check). getMatrix() is called by
no production code and by no other test, so it is the only test that can see the chain (gate G5 checks the full suite).

The gold's javadoc states the idiomatic contract (one entry of the matrix of the rotation defined by a normalized quaternion) and is
silent on the sign of the scalar-part term. The variant's matrix is symmetric and not orthogonal, so it is not the matrix of any
rotation; the contract is violated on the trigger input. The convention is pinned outside the gold: Rotation.applyTo(Vector3D) (the
image x' = 2 (q0 (x q0 - (q2 z - q3 y)) + s q1) - x: the cross-product term changes sign with the index order), used in production by
Rotation.getAngles, Plane.rotate and PolyhedronsSet; Rotation.applyInverseTo(Vector3D) (the same with -q0); and the matrix
constructor Rotation(double[][], double), which recovers the vectorial part from the antisymmetric differences of the matrix
(q1 = inv * (ort[1][2] - ort[2][1]), q2 = inv * (ort[2][0] - ort[0][2]), q3 = inv * (ort[0][1] - ort[1][0])); passing tests:
testAxisAngle and testVectorTwoPairs (the orientation of applyTo), testApplyInverseTo, testCompose.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: q0 enters the diagonal form and twist; v supplies every product; row and column select the coordinates and the sign.
  T2 absent: twist is read in the return; no local is frozen; the diagonal branch and the off-diagonal return differ; both outcomes
     of the ternary (twist, -twist) differ.
  T3 absent: diagonal and off-diagonal entries are both handled; both index orders are handled; both indices are read.
  T4 absent: 'one entry of the 3x3 matrix of the rotation defined by a normalized quaternion' is a general description that the body
     addresses; 'normalized' is a caller precondition; the @param/@return clauses name nothing the body does not meet.
 Variant gold (javadoc, signature, `if (row == column)` with the diagonal form, `final double twist = q0 * v[3 - row - column];`,
 `return 2.0 * (v[row] * v[column] + twist);`):
  T1 absent: q0 (diagonal form and twist), v (every product), row and column (indices of every product and of the third
     coordinate) each change the result; none is only argument-checked.
  T2 absent: twist reaches the return; no local is frozen or dead; the diagonal branch and the off-diagonal return have different
     effects; no ternary remains.
  T3 absent: diagonal and off-diagonal entries both handled; the gold has no index-order treatment at all ('No member handled');
     row and column are both read in the same roles; no class named in the gold's text is handled in part.
  T4 absent: 'one entry of the 3x3 matrix of the rotation defined by a normalized quaternion' is a general description that lines
     of the body address (no phrase names a sign, a symmetry or an order rule); 'normalized' is a caller precondition; no inline
     comment; identifiers (twist, row, column, v) name nothing the body does not meet.

Single owner: only the gold computes an entry; hop 1 passes the coordinates, hop 2 places rows, hop 3 allocates a row and hop 4 copies
the gold's value into each position of the row. Once the gold adds the scalar-part term with the same sign for both index orders, the
right value can appear only if a caller re-implements the gold's order decision or replaces the gold. Declared alternatives (G9): hop 4
reads the entry with the indices exchanged; hop 1 passes the opposite vectorial part; hop 1 passes the opposite scalar part. Each keeps
the matrix symmetric, so none makes the trigger pass.
Recorded bypasses (not declared as G9 alternatives):
 B-0 the facade (its original body) or hop 4 computing the entry from `new Rotation(q0, v[0], v[1], v[2], false)` with the intact
     applyTo, discarding the gold.
 B-1 hop 4 passes the opposite scalar part for the entries whose indices are not in cyclic order (`rotationEntry(column == (row + 1) % 3 ? q0 :
     -q0, v, row, column)`): a second implementation of the gold's order decision, and it breaks hop 4's documented rule that every
     entry is the entry of the rotation defined by the given quaternion.

Lie: the facade's javadoc claims the matrix is obtained from the axis and the angle of the rotation (getAxis() and getAngle()) with
the Rodrigues rotation formula; no step of the chain computes the axis or the angle (every entry is computed from the quaternion
coordinates). It names neither the sign nor the index order nor any hop."""

ROT = "src/main/java/org/apache/commons/math/geometry/euclidean/threed/Rotation.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"

GOLD_TEXT = '''/**
 * Computes one entry of the 3x3 matrix of the rotation defined by a
 * normalized quaternion.
 *
 * @param q0 scalar part of the quaternion
 * @param v vectorial part of the quaternion
 * @param row row index of the entry
 * @param column column index of the entry
 * @return the entry at the given row and column
 */
public static double rotationEntry(final double q0, final double[] v, final int row, final int column) {
    if (row == column) {
        return 2.0 * (q0 * q0 + v[row] * v[row]) - 1.0;
    }
    final double twist = q0 * v[3 - row - column];
    return 2.0 * (v[row] * v[column] + ((column == (row + 1) % 3) ? twist : -twist));
}'''

HOP1 = '''/**
 * Computes the 3x3 matrix of the rotation defined by a normalized
 * quaternion.
 *
 * @param q0 scalar part of the quaternion
 * @param q1 first coordinate of the vectorial part of the quaternion
 * @param q2 second coordinate of the vectorial part of the quaternion
 * @param q3 third coordinate of the vectorial part of the quaternion
 * @return the matrix, as an array of rows
 */
public static double[][] rotationMatrix(double q0, double q1, double q2, double q3) {
    return Dfp.rotationRows(q0, new double[] { q1, q2, q3 });
}'''

HOP2 = '''/**
 * Builds the rows of the matrix of the rotation defined by a normalized
 * quaternion.
 *
 * @param q0 scalar part of the quaternion
 * @param v vectorial part of the quaternion
 * @return the rows of the matrix, one per coordinate of the vectorial part
 */
public static double[][] rotationRows(final double q0, final double[] v) {
    final double[][] rows = new double[v.length][];
    for (int i = 0; i < rows.length; ++i) {
        rows[i] = BlockFieldMatrix.rotationRow(q0, v, i);
    }
    return rows;
}'''

HOP3 = '''/**
 * Computes one row of the matrix of the rotation defined by a normalized
 * quaternion.
 *
 * @param q0 scalar part of the quaternion
 * @param v vectorial part of the quaternion
 * @param row index of the row
 * @return a new array holding the row
 */
public static double[] rotationRow(final double q0, final double[] v, final int row) {
    final double[] entries = new double[v.length];
    FastMath.fillRotationRow(q0, v, row, entries);
    return entries;
}'''

HOP4 = '''/**
 * Fills one row of the matrix of the rotation defined by a normalized
 * quaternion.
 *
 * @param q0 scalar part of the quaternion
 * @param v vectorial part of the quaternion
 * @param row index of the row
 * @param out array receiving the entries of the row, one per column
 */
public static void fillRotationRow(final double q0, final double[] v, final int row, final double[] out) {
    for (int column = 0; column < out.length; ++column) {
        out[column] = org.apache.commons.math.linear.BlockRealMatrix.rotationEntry(q0, v, row, column);
    }
}'''

DESIGN = {
 "instance": "Math-52", "project": "Math", "bug_id": 52, "seed": 6150,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private final fields q0, q1, q2, q3 (the quaternion), read in the facade and passed to hop 1 as values; "
                 "no write-back",
 "host_mode": "1500", "host_lines": [2611, 2489, 1549, 4077, 1536],
 "reachability_probe": "getMatrix() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-52-probe: RotationTest::testMatrix fails with PROBE-REACHED at "
                       "Rotation.getMatrix(Rotation.java:797), called from RotationTest.testMatrix(RotationTest.java:226)",
 "facade": {"file": ROT, "class": "org.apache.commons.math.geometry.euclidean.threed.Rotation", "method": "getMatrix",
            "near_line": 796},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/math/geometry/euclidean/threed/RotationTest.java",
             "test_class": "org.apache.commons.math.geometry.euclidean.threed.RotationTest", "test_method": "testMatrix"},
 "expected_signature": "RotationTest.testMatrix(RotationTest.java:239)",
 "gold": {"method": "rotationEntry", "text": GOLD_TEXT,
          "fault": {"old": "        return 2.0 * (v[row] * v[column] + ((column == (row + 1) % 3) ? twist : -twist));",
                    "new": "        return 2.0 * (v[row] * v[column] + twist);"}},
 "chain": {
   "facade_body": "return org.apache.commons.math.util.MathUtils.rotationMatrix(q0, q1, q2, q3);",
   "lie": "The matrix is obtained from the axis and the angle of the rotation, as returned by getAxis() and getAngle(), "
          "with the Rodrigues rotation formula.",
   "hops": [
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "rotationMatrix",
      "imports": ["org.apache.commons.math.dfp.Dfp"], "text": HOP1},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "rotationRows",
      "imports": ["org.apache.commons.math.linear.BlockFieldMatrix"], "text": HOP2},
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "rotationRow",
      "imports": [], "text": HOP3},
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "fillRotationRow",
      "imports": [], "text": HOP4},
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "rotationEntry",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.geometry.euclidean.threed.Rotation::applyTo",
              "org.apache.commons.math.geometry.euclidean.threed.Rotation::applyInverseTo",
              "org.apache.commons.math.geometry.euclidean.threed.Rotation::Rotation"],
 "ownership_reason": "Only the gold computes an entry of the matrix: hop 1 packs the vectorial part, hop 2 places one row per "
                     "index, hop 3 allocates a row and hop 4 copies the gold's value into each position of the row. The gold's "
                     "javadoc promises an entry of the matrix of the rotation defined by the quaternion; the variant adds the "
                     "scalar-part term with the same sign for both index orders, so its matrix is symmetric, not orthogonal, and "
                     "is the matrix of no rotation. Once the gold has computed an entry, the right value can appear only if a "
                     "caller re-implements the gold's index-order decision or replaces the gold. The convention is pinned outside "
                     "the gold: Rotation.applyTo(Vector3D) applies the rotation with a cross-product term whose sign changes with "
                     "the index order (used in production by Rotation.getAngles, Plane.rotate and PolyhedronsSet), "
                     "Rotation.applyInverseTo(Vector3D) does the same with the opposite scalar part, and the matrix constructor "
                     "Rotation(double[][], double) recovers the vectorial part from the antisymmetric differences of the matrix "
                     "(q1 from m[1][2] - m[2][1], q2 from m[2][0] - m[0][2], q3 from m[0][1] - m[1][0]); testAxisAngle and "
                     "testVectorTwoPairs (orientation of applyTo), testApplyInverseTo and testCompose pass on the variant.",
 "ownership_tests": ["org.apache.commons.math.geometry.euclidean.threed.RotationTest::testAxisAngle",
                     "org.apache.commons.math.geometry.euclidean.threed.RotationTest::testVectorTwoPairs",
                     "org.apache.commons.math.geometry.euclidean.threed.RotationTest::testApplyInverseTo",
                     "org.apache.commons.math.geometry.euclidean.threed.RotationTest::testCompose"],
 "compensating": {
   "chain": [
     {"file": FM, "old": "out[column] = org.apache.commons.math.linear.BlockRealMatrix.rotationEntry(q0, v, row, column);",
      "new": "out[column] = org.apache.commons.math.linear.BlockRealMatrix.rotationEntry(q0, v, column, row);",
      "why": "hop 4 reads the entry with the row and column indices exchanged"},
     {"file": MU, "old": "return Dfp.rotationRows(q0, new double[] { q1, q2, q3 });",
      "new": "return Dfp.rotationRows(q0, new double[] { -q1, -q2, -q3 });",
      "why": "hop 1 passes the opposite vectorial part"},
     {"file": MU, "old": "return Dfp.rotationRows(q0, new double[] { q1, q2, q3 });",
      "new": "return Dfp.rotationRows(-q0, new double[] { q1, q2, q3 });",
      "why": "hop 1 passes the opposite scalar part"},
   ],
 },
 "host_notes": "host_mode 1500 (batch8_tasks.json; the five public classes of at least 1,500 lines other than the excluded "
               "facade file Rotation.java, confirmed on the checkout). Hosts are the recipe's seeded draw "
               "(mr_lib.py preview Math-52 org/apache/commons/math/geometry/euclidean/threed/Rotation.java 5, seed 6150), used "
               "in draw order, none substituted: util.MathUtils (hop 1, 2611 lines, anchor after subAndCheck, seed 6250), "
               "dfp.Dfp (hop 2, 2489, after nextAfter, 6251), linear.BlockFieldMatrix (hop 3, 1549, after getColumn, 6252), "
               "util.FastMath (hop 4, 4077, after acos, 6253), linear.BlockRealMatrix (hop 5, gold, 1536, after "
               "getColumnDimension, 6254; the smallest host). All five are public concrete top-level classes in which a public "
               "static method compiles (BlockFieldMatrix is generic; its static hop names no type parameter). The facade calls "
               "hop 1 by its fully-qualified name; MathUtils imports dfp.Dfp, Dfp imports linear.BlockFieldMatrix, "
               "BlockFieldMatrix already imports util.FastMath; FastMath has no import section, so hop 4 calls the gold by its "
               "fully-qualified name. No hop name is a StrictMath method name (FastMathStrictComparisonTest and "
               "FastMathTest compare FastMath with StrictMath by name).",
}
