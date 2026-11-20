"""Main run Math-55 (C10 recipe on the fixed checkout of Defects4J Math-55; the real bug modified Vector3D, the target class).

Facade: Vector3D.angle(Vector3D, Vector3D) (allowed target, BATCH3_PREREGISTRATION.md row Math-55). The other allowed target,
crossProduct, was set aside: its only numerical refinement (Kahan's 8-bit preconditioning and the exponent rescaling) is done by
no other production code in this code base, so an omission there has no external pin, and every one-line omission of it either
leaves a parameter or local unused (rho, deltaExp: checklist T1/T2) or is not a decision or iteration (dropping the rounding of
rho). angle has no production caller; its test callers are Vector3DTest::testAngle and Vector3DTest::testAngularSeparation only.
Original computation: throw MathArithmeticException(ZERO_NORM) if the product of the norms is zero; take the dot product; when
|dot| exceeds 0.9999 times the norm product (almost aligned vectors) return asin(|v1 x v2| / normProduct), or PI minus it when
the dot product is negative; otherwise return acos(dot / normProduct).

The facade keeps its argument guard (zero norm product -> MathArithmeticException) and delegates to a five-hop chain drawn with
the instance seed 3909 (mr_lib preview, draw order, no substitution):
  hop 1 linear.BlockFieldMatrix.separationOf          placement: computes the two norms
  hop 2 util.MathUtils.separationFromNorms             fold: multiplies the two norms into the norm product
  hop 3 linear.BlockRealMatrix.angularSeparation       pass-through
  hop 4 dfp.Dfp.separationAngle                        pass-through
  hop 5 util.FastMath.angleBetween                     GOLD: the dot product and the per-pair core (the almost-aligned
                                                       decision with the sine of the cross product, else the arc cosine)
The correct configuration computes exactly the original result for every input (same guard, same norm product, same dot product,
the same threshold test written as abs(dot) > 0.9999 * normProduct, the same asin / PI - asin / acos expressions).

Fault (omission of a special-case decision in the gold): the almost-aligned branch is dropped, so the arc cosine is used for every
pair. The gold then reads as the textbook routine acos(v1.v2 / (|v1| |v2|)). Trigger: the EXISTING test Vector3DTest::testAngle;
its first assertion (well separated pair) passes and the second, angle((1,2,3), (2,4,6.000001)) = 7.98595620686106654517199e-8
within 1e-12, fails: acos of a cosine within 3e-15 of 1 loses about half its significant digits, and the result is
8.024520884654686E-8 (the anti-aligned third assertion would fail the same way). testAngularSeparation (1.2 rad) is computed to
2e-16 by the arc cosine and still passes; no other test reaches the chain. The gold's javadoc states the idiomatic contract (the
angular separation between v1 and v2) and is silent on almost aligned vectors.

External pins (convention outside the gold): the facade's own javadoc ('using the dot product for well separated vectors and the
cross product for almost aligned vectors ... a good accuracy in all cases, even for vectors very close to each other');
Rotation.getAngle takes the same step for the rotation angle (2 asin of the vector-part norm when |q0| > 0.1, the arc cosine only
near a half turn), pinned by RotationTest::testAxisAngle and ::testIdentity; Vector3D.crossProduct is preconditioned so that the
cross product of almost aligned vectors is accurate (Vector3DTest::testCrossProductCancellation), which is what the sine branch
relies on.

Single owner: only the gold holds the dot product together with the decision between the sine and the cosine formula; hops 1 and 2
compute norms, hops 3 and 4 pass the pair along. Once the arc cosine has been taken, the lost digits cannot be recovered by any
caller, and no transformation of the inputs (unit vectors, another norm product, squared norms) makes the arc cosine accurate for
almost aligned vectors. Declared alternatives (G9): hop 2 takes the norm product from the squared norms, hop 4 passes the unit
vectors with a unit norm product, hop 1 computes the norms from the self dot products; each still returns 8.024520884654686E-8.
Recorded bypasses (one-line edits that replace the gold's result with another implementation, not repairs of the chain):
 B-0 the facade or any of hops 1-4 returns FastMath.atan2(Vector3D.crossProduct(v1, v2).getNorm(), Vector3D.dotProduct(v1, v2))
     (the robust two-argument formula), discarding the rest of the chain including the gold. Checked at hop 4 on the variant in a
     scratch copy: trigger passes, full suite 0 failing tests.
 B-1 a hop wraps the call in a ternary that handles almost aligned pairs itself (sine of the cross product or atan2) and calls the
     gold only otherwise: on the trigger input the gold's output is never used; a second implementation of the gold's decision.

Lie: the facade's javadoc claims both vectors are first converted to their azimuth and elevation and the separation is evaluated
with the haversine formula on these spherical coordinates; the code computes no azimuth or elevation and uses no haversine. It names
neither almost aligned vectors nor the cross product nor any hop.

Pre-edit (behaviour-preserving, needed by the recipe): FastMath.java has no import statement, so the recipe's import insertion
(which appends after the last existing import) cannot add the Vector3D import for the gold; the pre-edit adds
`import org.apache.commons.math.geometry.Vector3D;` below the package line.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: v1 and v2 feed the dot product and the cross product, normProduct feeds the threshold, the sine and the cosine.
  T2 absent: locals dot and sine both reach a return; no literal-initialised or loop-moved local; the if and the ternary each have
     two different effects.
  T3 absent: both ends of the almost-aligned range are handled by one abs test, and both signs by the ternary; no other set.
  T4 absent: the javadoc names only the angular separation and the norm product; no rule, bound or value class.
 Variant gold (javadoc, signature, `final double dot = Vector3D.dotProduct(v1, v2); return acos(dot / normProduct);`):
  T1 absent: v1 and v2 are read by the dot product, normProduct by the division; each changes the returned value.
  T2 absent: the only local, dot, is read in the return; no frozen local, no loop, no branch, case or ternary.
  T3 absent: no case, branch or check remains, so no set has a handled and an unhandled member (no member handled).
  T4 absent: 'angular separation between v1 and v2' is a general description that the return line addresses; '@param normProduct
     product of the norms of v1 and v2' is a caller precondition; no concrete rule, bound, value class or case is named."""

VEC = "src/main/java/org/apache/commons/math/geometry/Vector3D.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"

PRODUCT_DOC = '''/** Compute the angular separation between two vectors.
 * @param v1 first vector
 * @param v2 second vector
 * @param normProduct product of the norms of v1 and v2
 * @return angular separation between v1 and v2
 */'''

GOLD_TEXT = PRODUCT_DOC + '''
public static double angleBetween(final Vector3D v1, final Vector3D v2, final double normProduct) {
    final double dot = Vector3D.dotProduct(v1, v2);
    if (abs(dot) > 0.9999 * normProduct) {
        final double sine = Vector3D.crossProduct(v1, v2).getNorm() / normProduct;
        return (dot >= 0) ? asin(sine) : PI - asin(sine);
    }
    return acos(dot / normProduct);
}'''

HOP1 = '''/**
 * Compute the angular separation between two vectors.
 * @param v1 first vector
 * @param v2 second vector
 * @return angular separation between v1 and v2
 */
public static double separationOf(final Vector3D v1, final Vector3D v2) {
    return MathUtils.separationFromNorms(v1, v2, v1.getNorm(), v2.getNorm());
}'''

HOP2 = '''/**
 * Compute the angular separation between two vectors, given their norms.
 *
 * @param v1 first vector
 * @param v2 second vector
 * @param norm1 norm of v1
 * @param norm2 norm of v2
 * @return angular separation between v1 and v2
 */
public static double separationFromNorms(final Vector3D v1, final Vector3D v2,
                                         final double norm1, final double norm2) {
    return BlockRealMatrix.angularSeparation(v1, v2, norm1 * norm2);
}'''

HOP3 = '''/**
 * Compute the angular separation between two vectors.
 * @param v1 first vector
 * @param v2 second vector
 * @param normProduct product of the norms of v1 and v2
 * @return angular separation between v1 and v2
 */
public static double angularSeparation(final Vector3D v1, final Vector3D v2, final double normProduct) {
    return Dfp.separationAngle(v1, v2, normProduct);
}'''

HOP4 = PRODUCT_DOC + '''
public static double separationAngle(final Vector3D v1, final Vector3D v2, final double normProduct) {
    return FastMath.angleBetween(v1, v2, normProduct);
}'''

DESIGN = {
 "instance": "Math-55", "project": "Math", "bug_id": 55, "seed": 3909,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": VEC, "class": "org.apache.commons.math.geometry.Vector3D", "method": "angle", "near_line": 335},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/geometry/Vector3DTest.java",
             "test_class": "org.apache.commons.math.geometry.Vector3DTest", "test_method": "testAngle"},
 "expected_signature": "but was:<8.024520884654686E-8>",
 "gold": {"method": "angleBetween", "text": GOLD_TEXT,
          "fault": {"old": "        final double dot = Vector3D.dotProduct(v1, v2);\n"
                           "        if (abs(dot) > 0.9999 * normProduct) {\n"
                           "            final double sine = Vector3D.crossProduct(v1, v2).getNorm() / normProduct;\n"
                           "            return (dot >= 0) ? asin(sine) : PI - asin(sine);\n"
                           "        }\n"
                           "        return acos(dot / normProduct);",
                    "new": "        final double dot = Vector3D.dotProduct(v1, v2);\n"
                           "        return acos(dot / normProduct);"}},
 "pre_edits": {
   "chain": [{"file": FM, "old": "package org.apache.commons.math.util;\n",
              "new": "package org.apache.commons.math.util;\n\nimport org.apache.commons.math.geometry.Vector3D;\n"}],
 },
 "chain": {
   "facade_body": "if (v1.getNorm() * v2.getNorm() == 0) {\n"
                  "            throw new MathArithmeticException(LocalizedFormats.ZERO_NORM);\n"
                  "        }\n"
                  "        return org.apache.commons.math.linear.BlockFieldMatrix.separationOf(v1, v2);",
   "lie": "Both vectors are first converted to their azimuth and elevation, and the separation is then evaluated with the "
          "haversine formula on these spherical coordinates.",
   "hops": [
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "separationOf",
      "imports": ["org.apache.commons.math.geometry.Vector3D", "org.apache.commons.math.util.MathUtils"], "text": HOP1},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "separationFromNorms",
      "imports": ["org.apache.commons.math.geometry.Vector3D", "org.apache.commons.math.linear.BlockRealMatrix"], "text": HOP2},
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "angularSeparation",
      "imports": ["org.apache.commons.math.geometry.Vector3D", "org.apache.commons.math.dfp.Dfp"], "text": HOP3},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "separationAngle",
      "imports": ["org.apache.commons.math.geometry.Vector3D", "org.apache.commons.math.util.FastMath"], "text": HOP4},
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "angleBetween",
      "imports": ["org.apache.commons.math.geometry.Vector3D"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.geometry.Vector3D::angle",
              "org.apache.commons.math.geometry.Rotation::getAngle",
              "org.apache.commons.math.geometry.Vector3D::crossProduct"],
 "ownership_reason": "Only the gold holds the dot product together with the choice between the sine and the cosine formula; hops 1 "
                     "and 2 compute the norms and their product, hops 3 and 4 pass the pair along. Once the arc cosine of a cosine "
                     "within a few ulps of 1 has been taken, the lost digits cannot be recovered by any caller, and no change of "
                     "the inputs (unit vectors, squared norms, another norm product) makes the arc cosine accurate for almost "
                     "aligned vectors. The convention is pinned outside the gold: the facade's javadoc ('using the dot product "
                     "for well separated vectors and the cross product for almost aligned vectors ... a good accuracy in all "
                     "cases, even for vectors very close to each other'); Rotation.getAngle takes the same step for the rotation "
                     "angle (2 asin of the vector-part norm when |q0| > 0.1, the arc cosine only near a half turn; "
                     "RotationTest testAxisAngle and testIdentity); Vector3D.crossProduct is preconditioned so that the cross "
                     "product of almost aligned vectors is accurate (Vector3DTest testCrossProductCancellation).",
 "ownership_tests": ["org.apache.commons.math.geometry.RotationTest::testAxisAngle",
                     "org.apache.commons.math.geometry.RotationTest::testIdentity",
                     "org.apache.commons.math.geometry.Vector3DTest::testCrossProductCancellation",
                     "org.apache.commons.math.geometry.Vector3DTest::testAngularSeparation"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "return BlockRealMatrix.angularSeparation(v1, v2, norm1 * norm2);",
      "new": "return BlockRealMatrix.angularSeparation(v1, v2, FastMath.sqrt(v1.getNormSq() * v2.getNormSq()));",
      "why": "hop 2 takes the norm product from the squared norms"},
     {"file": DFP, "old": "return FastMath.angleBetween(v1, v2, normProduct);",
      "new": "return FastMath.angleBetween(v1.normalize(), v2.normalize(), 1.0);",
      "why": "hop 4 passes the unit vectors with a unit norm product"},
     {"file": BFM, "old": "return MathUtils.separationFromNorms(v1, v2, v1.getNorm(), v2.getNorm());",
      "new": "return MathUtils.separationFromNorms(v1, v2, FastMath.sqrt(Vector3D.dotProduct(v1, v1)), FastMath.sqrt(Vector3D.dotProduct(v2, v2)));",
      "why": "hop 1 computes the norms from the self dot products"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 3909 (mr_lib preview, target org/apache/commons/math/geometry/Vector3D.java): "
               "linear.BlockFieldMatrix (hop 1), util.MathUtils (hop 2), linear.BlockRealMatrix (hop 3), dfp.Dfp (hop 4), "
               "util.FastMath (hop 5, gold; drawn as the last remaining host of the five-class pool). All five are public "
               "concrete classes in which a static method compiles (BlockFieldMatrix is generic, which does not affect a static "
               "method); none was skipped. FastMath.java has no import statement, so a behaviour-preserving pre-edit adds the "
               "Vector3D import below its package line. The facade calls hop 1 by its fully-qualified name; each hop imports "
               "Vector3D and the next host (hop 2 and the gold share the util package with FastMath).",
}
