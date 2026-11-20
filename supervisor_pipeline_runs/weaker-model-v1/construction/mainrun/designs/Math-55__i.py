"""Main run Math-55__i (cell C10i, batch 7, the paired static/instance bridge: the C10 recipe with an INSTANCE-method facade, on the
fixed checkout of Defects4J Math-55; the real bug modified Vector3D, the facade's class; paired static instance MR-Math-55, whose
facade Vector3D.angle is not used here and whose files were not opened).

Facade: Vector3D.orthogonal() (allowed instance target, BATCH7_PREREGISTRATION.md row 205; no facade reuse). The other allowed target,
Vector3D.normalize(), is a norm, a zero test and one scalarMultiply: it has no per-element iteration or decision to carry a gold, and
any scale omission is recovered by a caller's normalize().
facade_variant: V2 (receiver as parameter). state_passed: the receiver `this` (typed Vector3D) is handed to hop 1, and the hops call
its public methods only (getNorm, getX, getY, getZ); no field is written and nothing is written back (Vector3D is immutable; the facade
returns hop 1's vector). The facade keeps the original guard (a zero norm throws MathArithmeticException(ZERO_NORM); the original
tests 0.6 * getNorm() == 0, which holds exactly when getNorm() == 0) plus the one call to hop 1.
Original computation: threshold = 0.6 * norm; the first of x and y whose coordinate lies in [-threshold, threshold] is the axis, z
otherwise; the result is the cross product of the instance with that canonical axis, scaled by the inverse of the norm of the two
other coordinates: (0, z, -y), (-z, 0, x) or (y, -x, 0) times that inverse.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Math-55-probe/w of the fixture the
first statement of orthogonal() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. defects4j test -t
Vector3DTest::testOrthogonal: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at Vector3D.orthogonal(Vector3D.java:306)
from Vector3DTest.testOrthogonal(Vector3DTest.java:207); Vector3DTest::testAngularSeparation and RotationTest::testVectorOnePair fail
the same way (the latter through Rotation.<init>(Rotation.java:460), the u = -v case). Full suite with the probe: exactly these 3
failing tests. The facade is reached by existing tests directly.

Hosts (host_mode = "1500"; hosts_hop_order of bridge7_tasks.json, the paired static instance's hosts, used in that order, none
substituted; newline counts 1547, 2290, 1532, 2399, 4047; the smallest host has 1532 lines):
  hop 1 linear.BlockFieldMatrix  perpendicularUnitVector   plumbing: the threshold, six tenths of the norm
  hop 2 util.MathUtils           perpendicularTo           decision: the axis (first of x, y within the threshold, else z)
  hop 3 linear.BlockRealMatrix   perpendicularToAxis       placement: the coordinates as an array in, the result array out as a
                                                           Vector3D
  hop 4 dfp.Dfp                  perpendicularCoordinates  pass-through
  hop 5 util.FastMath            unitNormal                GOLD: the inverse of the norm of the coordinates other than the axis,
                                                           then a pass over the three positions deciding per position between the
                                                           axis (left zero), the position after the axis (the following
                                                           coordinate, scaled) and the remaining one (the other, scaled, negated)
The correct configuration returns the original result bit for bit for every input: the same guard and threshold, the same axis
tests, the same sums (0 + a*a + b*b equals a*a + b*b), the same `1 / sqrt(...)` and the same products `inverse * c` and
`-inverse * c`, and a positive zero on the axis.

Fault (one-line omission of a boundary rule in the gold's decision): the wrap of the index after the axis (`if (next == 3) { next =
0; }`) is dropped. For the axis 0 and 1 nothing changes; for the axis 2 (z) the position after the axis is never met, so both other
positions take the negated branch and the gold returns (-inverse * y, -inverse * x, 0), a unit vector in the xy plane that is not
orthogonal to the vector. Trigger: the EXISTING test Vector3DTest::testOrthogonal; its first two vectors (0.1, 2.5, 1.3) and
(2.3, -0.003, 7.6) use the x axis and still pass; the third, v3 = (-1.7, 1.4, 0.2) (threshold 1.327: |x| = 1.7 and |y| = 1.4 lie
outside, so z is used), fails at line 211 with expected:<0.0> but was:<2.16...> (dot product (x * y + y * x) * inverse). It is the
only test that newly fails: testAngularSeparation (k = (2, -1, 4) normalized) uses the x axis, and RotationTest::testVectorOnePair
uses the y axis (u = (3, 2, 1)) and only checks the angle of a rotation whose scalar part is 0. No exception is thrown anywhere: the
gold never indexes the coordinates with the index after the axis (it only compares positions with it), so the failure is a plain
assertion in the test.

The gold's javadoc states the idiomatic contract (the unit vector orthogonal both to a vector and to the canonical axis of the given
index) and is silent on how the position after the axis is found; the variant's result for v3 is not orthogonal to v3 (it is still
orthogonal to the z axis and of unit length). The convention (the
canonical axes taken in the cyclic order x, y, z, x, so that z is followed by x; the result orthogonal to the vector) is pinned
outside the gold: Vector3D.crossProduct, whose components follow the same cyclic order (the y component combines z and x) and whose
cross product of the vector with the axis is the gold's direction, with Vector3DTest::testVectorialProducts and
::testCrossProductCancellation passing; Vector3D.dotProduct with testOrthogonal's own first two assertions and
Vector3DTest::testAngularSeparation (unit and orthogonal on the x axis) passing on the variant; the facade's own javadoc ("a new
normalized vector orthogonal to the instance") and its frame example (i = k.orthogonal(); j = crossProduct(k, i)).

Single owner: only the gold decides what each position of the result holds; hop 1 fixes the threshold, hop 2 picks the axis exactly as
documented (z for v3), hop 3 converts to and from the coordinate array and hop 4 passes along. Once the gold has put a negated value at
the position after the axis, no caller can tell which position that was without redoing the gold's decision. Declared alternatives
(G9, each leaves the trigger failing): hop 1 bases the threshold on the largest coordinate magnitude (getNormInf); hop 2 uses strict
inequalities for the x test; hop 3 normalizes the vector it returns (the variant's result is already unit length).
Recorded one-line edits above the gold that pass the trigger and the full suite, none of them consistent with the documentation on the
path (each checked on the variant in a scratch copy, /private/tmp/d4j-mi-Math-55-alt: trigger passes, defects4j test 0 failing tests):
 R-1 hop 1 raises the threshold factor to 0.8 (z is then never chosen, since |x| and |y| above 0.8 of the norm cannot both hold):
     contradicts hop 1's javadoc (six tenths of the norm).
 R-2 hop 2 falls back to the y axis instead of z: contradicts hop 2's javadoc (the z axis if neither x nor y lies within the
     threshold).
 R-3 hop 3 maps the axis 2 to 1 before the call (`axis == 2 ? 1 : axis`): the result is then orthogonal to the y axis,
     contradicting hop 3's javadoc (the canonical axis of the given index) and hop 2's (the chosen axis).
 R-5 hop 4 passes `axis % 2`: the same remap one hop lower, contradicting hop 4's own javadoc (the canonical axis of the given
     index). R-1 to R-3 and R-5 are numerically sound only because the z axis is chosen solely when |x| and |y| exceed the
     threshold; each changes a documented choice rather than the gold's placement.
 R-4 inverse compensation: hop 3 (or hop 4, by negating the x coordinate it passes for the axis 2) undoes the gold's
     placement for the axis 2 (`axis == 2 ? -normal[0] : normal[0]`): it relies on the gold returning a vector its own javadoc
     excludes, and it breaks the correct configuration.
 B-0 bypass: the facade (its original body) or a hop computes the vector itself, e.g. hop 3
     `return Vector3D.crossProduct(v, axis == 0 ? Vector3D.PLUS_I : axis == 1 ? Vector3D.PLUS_J : Vector3D.PLUS_K).normalize();`,
     discarding hop 4 and the gold.

Lie: the facade's javadoc claims the vector is obtained by removing, from the canonical axis least aligned with the instance, its
component along the instance and normalizing what remains (a Gram-Schmidt step); the chain takes the first axis within the threshold
and returns the normalized cross product of the instance with it, a different vector. It names neither the axis order nor any
position nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (FastMath.unitNormal with the wrap):
  T1 absent: coordinates feed the sum and every written component; axis decides next, both skips and the index 3 - axis - i.
  T2 absent: next is set from axis and reset by the wrap, then read in the placement decision; sum is accumulated in the first loop
     and read for inverse; inverse and normal reach the return; i is advanced by both for headers; the wrap decides next for the
     axis 2; the skip, the next-branch and the other branch have different effects.
  T3 absent: every position of the result has a rule (the axis, the position after it, the remaining one) and the sum skips the same
     axis; the only index that can leave the range is next, and it is wrapped; nothing handles one half of a pair or one end of a
     range only; the gold names no class it handles in part.
  T4 absent: 'unit vector orthogonal both to a vector and to the canonical axis of the given index' (the axis position is never
     written and stays zero), 'the three coordinates of the vector' and
     '@return the three coordinates of the unit vector' are met by lines of the body; '@param axis index of the axis' names no range.
 Variant gold (javadoc, signature, `int next = axis + 1;`, the sum loop with its skip, inverse, the placement loop with its two
 branches, the return):
  T1 absent: coordinates and axis each change the returned values; neither is only argument-checked (the gold has no argument
     check).
  T2 absent: next is computed from axis before the loop and only read inside it (a computed offset, not a literal and not a value the
     loop is meant to move); sum is assigned in its loop and read; inverse and normal reach the return; both loop indices advance;
     the `i == next` branch writes a different value from the `i != axis` branch and is taken for the axis 0 and 1, so no decision
     is dead; no literal-initialised local is left unassigned.
  T3 absent: no index wrap remains anywhere ('No member handled'); the positions still have three rules; the skip of the axis is the
     same in both loops; no pair half, range end or named class is treated in part.
  T4 absent: the javadoc and identifiers (next, sum, inverse, normal) name no limit, value class, case or property the body visibly
     fails to meet; the contract sentence is a general description that the skip, the inverse and the placement address; no inline
     comment."""

V3D = "src/main/java/org/apache/commons/math/geometry/Vector3D.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"

GOLD_TEXT = '''/**
 * Compute the unit vector orthogonal both to a vector and to the
 * canonical axis of the given index.
 * @param coordinates the three coordinates of the vector
 * @param axis index of the axis
 * @return the three coordinates of the unit vector
 */
public static double[] unitNormal(double[] coordinates, int axis) {
    int next = axis + 1;
    if (next == 3) {
        next = 0;
    }
    double sum = 0;
    for (int i = 0; i < 3; i++) {
        if (i != axis) {
            sum += coordinates[i] * coordinates[i];
        }
    }
    double inverse = 1 / sqrt(sum);
    double[] normal = new double[3];
    for (int i = 0; i < 3; i++) {
        if (i == next) {
            normal[i] = inverse * coordinates[3 - axis - i];
        } else if (i != axis) {
            normal[i] = -inverse * coordinates[3 - axis - i];
        }
    }
    return normal;
}'''

HOP1 = '''/**
 * Get a unit vector perpendicular to a non-zero vector.
 * <p>The threshold used to choose the axis is six tenths of the norm of
 * the vector.</p>
 * @param v non-zero vector
 * @return a new unit vector perpendicular to v
 */
public static Vector3D perpendicularUnitVector(final Vector3D v) {
    return MathUtils.perpendicularTo(v, 0.6 * v.getNorm());
}'''

HOP2 = '''/**
 * Returns a unit vector perpendicular to a non-zero vector and to one of
 * the canonical axes: the first of the x and y axes along which the
 * coordinate of the vector lies between {@code -threshold} and
 * {@code threshold}, or the z axis if neither does.
 *
 * @param v non-zero vector
 * @param threshold bound on the coordinate along the axis
 * @return a new unit vector perpendicular to v and to the chosen axis
 */
public static Vector3D perpendicularTo(final Vector3D v, final double threshold) {
    final double x = v.getX();
    if ((x >= -threshold) && (x <= threshold)) {
        return BlockRealMatrix.perpendicularToAxis(v, 0);
    }
    final double y = v.getY();
    if ((y >= -threshold) && (y <= threshold)) {
        return BlockRealMatrix.perpendicularToAxis(v, 1);
    }
    return BlockRealMatrix.perpendicularToAxis(v, 2);
}'''

HOP3 = '''/**
 * Get the unit vector perpendicular both to a vector and to the
 * canonical axis of the given index.
 * @param v vector, not parallel to the axis
 * @param axis index of the axis (0 for x, 1 for y, 2 for z)
 * @return a new unit vector perpendicular to v and to the axis
 */
public static Vector3D perpendicularToAxis(final Vector3D v, final int axis) {
    final double[] normal =
        Dfp.perpendicularCoordinates(new double[] { v.getX(), v.getY(), v.getZ() }, axis);
    return new Vector3D(normal[0], normal[1], normal[2]);
}'''

HOP4 = '''/** Compute the coordinates of the unit vector perpendicular both to a
 * vector and to the canonical axis of the given index.
 * @param coordinates coordinates of the vector
 * @param axis index of the axis
 * @return coordinates of the unit vector
 */
public static double[] perpendicularCoordinates(final double[] coordinates, final int axis) {
    return FastMath.unitNormal(coordinates, axis);
}'''

DESIGN = {
 "instance": "Math-55", "project": "Math", "bug_id": 55, "seed": 3909,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade_variant": "V2",
 "state_passed": "receiver this (Vector3D) to hop 1; no write-back",
 "reachability_probe": "orthogonal() first statement throws IllegalStateException(PROBE-REACHED): Vector3DTest::testOrthogonal, "
                       "Vector3DTest::testAngularSeparation and RotationTest::testVectorOnePair fail with PROBE-REACHED; full suite: "
                       "exactly these 3 failing tests",
 "facade": {"file": V3D, "class": "org.apache.commons.math.geometry.Vector3D", "method": "orthogonal", "near_line": 305},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/geometry/Vector3DTest.java",
             "test_class": "org.apache.commons.math.geometry.Vector3DTest", "test_method": "testOrthogonal"},
 "expected_signature": "expected:<0.0> but was:<2.16",
 "gold": {"method": "unitNormal", "text": GOLD_TEXT,
          "fault": {"old": "        int next = axis + 1;\n"
                           "        if (next == 3) {\n"
                           "            next = 0;\n"
                           "        }\n"
                           "        double sum = 0;",
                    "new": "        int next = axis + 1;\n"
                           "        double sum = 0;"}},
 "chain": {
   "facade_body": "if (getNorm() == 0) {\n"
                  "            throw new MathArithmeticException(LocalizedFormats.ZERO_NORM);\n"
                  "        }\n"
                  "        return org.apache.commons.math.linear.BlockFieldMatrix.perpendicularUnitVector(this);",
   "lie": "The vector is obtained by removing, from the canonical axis least aligned with the instance, its component along "
          "the instance, and normalizing what remains.",
   "hops": [
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "perpendicularUnitVector",
      "imports": ["org.apache.commons.math.geometry.Vector3D", "org.apache.commons.math.util.MathUtils"], "text": HOP1},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "perpendicularTo",
      "imports": ["org.apache.commons.math.geometry.Vector3D", "org.apache.commons.math.linear.BlockRealMatrix"], "text": HOP2},
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "perpendicularToAxis",
      "imports": ["org.apache.commons.math.geometry.Vector3D", "org.apache.commons.math.dfp.Dfp"], "text": HOP3},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "perpendicularCoordinates",
      "imports": ["org.apache.commons.math.util.FastMath"], "text": HOP4},
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "unitNormal", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.geometry.Vector3D::crossProduct",
              "org.apache.commons.math.geometry.Vector3D::dotProduct"],
 "ownership_reason": "Only the gold decides what each position of the result holds: hop 1 fixes the threshold (six tenths of the "
                     "norm), hop 2 picks the axis exactly as its javadoc states (the z axis for (-1.7, 1.4, 0.2), whose x and y "
                     "coordinates lie outside the threshold), hop 3 converts the vector to and from its coordinate array and hop 4 "
                     "passes along. The gold's javadoc promises the unit vector orthogonal both to the vector and to the given "
                     "canonical axis; for the z axis the variant returns (-inverse * y, -inverse * x, 0), which is not orthogonal "
                     "to the vector. The convention is pinned outside the gold: Vector3D.crossProduct takes the axes in the cyclic "
                     "order x, y, z, x (its y component combines z and x), and the cross product of the vector with the chosen "
                     "axis is the gold's direction (Vector3DTest testVectorialProducts and testCrossProductCancellation pass); "
                     "Vector3D.dotProduct with the first two assertions of testOrthogonal and with testAngularSeparation (a unit "
                     "vector orthogonal to the normalized (2, -1, 4)) passing on the variant; the facade's javadoc ('a new "
                     "normalized vector orthogonal to the instance'). An edit above the gold that avoids the z axis (a larger "
                     "threshold factor at hop 1, a y fallback at hop 2, a remapped axis at hop 3) passes the tests but contradicts "
                     "that hop's javadoc; an edit that undoes the gold's placement for the z axis relies on the gold returning a "
                     "vector its javadoc excludes.",
 "ownership_tests": ["org.apache.commons.math.geometry.Vector3DTest::testAngularSeparation",
                     "org.apache.commons.math.geometry.Vector3DTest::testVectorialProducts",
                     "org.apache.commons.math.geometry.Vector3DTest::testCrossProductCancellation",
                     "org.apache.commons.math.geometry.RotationTest::testVectorOnePair"],
 "compensating": {
   "chain": [
     {"file": BFM, "old": "return MathUtils.perpendicularTo(v, 0.6 * v.getNorm());",
      "new": "return MathUtils.perpendicularTo(v, 0.6 * v.getNormInf());",
      "why": "hop 1 bases the threshold on the largest coordinate magnitude"},
     {"file": MU, "old": "if ((x >= -threshold) && (x <= threshold)) {",
      "new": "if ((x > -threshold) && (x < threshold)) {",
      "why": "hop 2 uses strict inequalities for the x coordinate"},
     {"file": BRM, "old": "return new Vector3D(normal[0], normal[1], normal[2]);",
      "new": "return new Vector3D(normal[0], normal[1], normal[2]).normalize();",
      "why": "hop 3 normalizes the vector it returns"},
   ],
 },
 "host_notes": "host_mode 1500 (bridge7_tasks.json). Hosts are hosts_hop_order of the task record, the paired static instance's "
               "hosts, in that order, none substituted: linear.BlockFieldMatrix (hop 1, 1547 lines), util.MathUtils (hop 2, 2290), "
               "linear.BlockRealMatrix (hop 3, 1532; the smallest host), dfp.Dfp (hop 4, 2399), util.FastMath (hop 5, gold, 4047). "
               "All five are public top-level classes in which a static method compiles (BlockFieldMatrix is generic; a static "
               "method does not use its type parameter). Anchors from stageB_lib.pick_insertion_anchor with seed 3909 + 100 + i, "
               "as mr3_spec.py inserts them (pristine line indices): hop 1 after `getEntry` (line idx 1131, seed 4009), hop 2 "
               "after `equalsIncludingNaN` (603, 4010), hop 3 after `createBlocksLayout` (264, 4011), hop 4 after "
               "`getRadixDigits` (640, 4012), hop 5 after `max` (the long overload, 3862, 4013); all in the outer class. The "
               "facade calls hop 1 by its fully-qualified name; each hop imports Vector3D where it names it and the next host. "
               "FastMathStrictComparisonTest reflects over StrictMath's methods only, so the added FastMath method is not "
               "picked up by it.",
}
