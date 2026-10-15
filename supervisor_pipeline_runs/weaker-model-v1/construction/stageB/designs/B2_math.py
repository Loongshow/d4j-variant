"""Stage B bug B2 (Math): FastMath.atanh(double). Gold = the Taylor-series evaluation for small non-negative arguments; the
fault omits the tier for 0.031 < a <= 0.087 (that band falls to the 5-term series). Trigger: FastMathTest::testHyperbolicInverses
(atanh round trip over [-1, 1] step 1e-4, tolerance 2 ulp) fails as a value mismatch; asinh's four-tier series, the class's
0.5-ulp contract and DSCompiler.atanh / DfpTest.testAtanh (passing) pin the correct behaviour. Odd hop = sign restoration
written as a raw-bits XOR (the idiom of FastMath.copySign) instead of copySign itself."""
GOLD_TEXT = '''/** Inverse hyperbolic tangent of a small non-negative number, from the
 * Taylor series of the function truncated according to the magnitude of
 * the argument.
 * @param a number on which evaluation is done, between 0 and 0.15
 * @return inverse hyperbolic tangent of a
 */
public static double smallArgumentSeries(final double a) {
    final double a2 = a * a;
    if (a > 0.087) {
        return a * (1 + a2 * (1d / 3d + a2 * (1d / 5d + a2 * (1d / 7d + a2 * (1d / 9d + a2 * (1d / 11d + a2 * (1d / 13d + a2 * (1d / 15d + a2 * (1d / 17d)))))))));
    } else if (a > 0.031) {
        return a * (1 + a2 * (1d / 3d + a2 * (1d / 5d + a2 * (1d / 7d + a2 * (1d / 9d + a2 * (1d / 11d + a2 * (1d / 13d)))))));
    } else if (a > 0.003) {
        return a * (1 + a2 * (1d / 3d + a2 * (1d / 5d + a2 * (1d / 7d + a2 * (1d / 9d)))));
    } else {
        return a * (1 + a2 * (1d / 3d + a2 * (1d / 5d)));
    }
}'''
SIGN_DOC = '''/** Attach the sign of a number to a non-negative magnitude.
 * @param magnitude non-negative magnitude
 * @param x number whose sign is used
 * @return magnitude carrying the sign of x
 */'''
SIB_PLAIN = SIGN_DOC + '''
public static double attachSign(final double magnitude, final double x) {
    return FastMath.copySign(magnitude, x);
}'''
SIB_ODD = SIGN_DOC + '''
public static double attachSign(final double magnitude, final double x) {
    final long m = Double.doubleToRawLongBits(magnitude);
    final long s = Double.doubleToRawLongBits(x) & Long.MIN_VALUE;
    return Double.longBitsToDouble(m ^ s);
}'''
H3_DOC = '''/** Evaluate the inverse hyperbolic tangent of a number from the
 * evaluation of its magnitude.
 * @param a number on which evaluation is done
 * @return inverse hyperbolic tangent of a
 */'''
DESIGN = {
 "bug": "B2", "project": "Math", "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": "src/main/java/org/apache/commons/math3/util/FastMath.java", "class": "org.apache.commons.math3.util.FastMath",
            "method": "atanh", "near_line": 748},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math3/util/FastMathTest.java",
             "test_class": "org.apache.commons.math3.util.FastMathTest", "test_method": "testHyperbolicInverses"},
 "expected_signature": "expected:<0.0> but was:<7071.0>",
 "gold": {"method": "smallArgumentSeries", "text": GOLD_TEXT,
          "fault": {"old": "        } else if (a > 0.031) {\n            return a * (1 + a2 * (1d / 3d + a2 * (1d / 5d + a2 * (1d / 7d + a2 * (1d / 9d + a2 * (1d / 11d + a2 * (1d / 13d)))))));\n        } else if (a > 0.003) {",
                    "new": "        } else if (a > 0.003) {"}},
 "one_hop": {
   "facade_old": '''        boolean negative = false;
        if (a < 0) {
            negative = true;
            a = -a;
        }

        double absAtanh;
        if (a > 0.15) {
            absAtanh = 0.5 * FastMath.log((1 + a) / (1 - a));
        } else {
            final double a2 = a * a;
            if (a > 0.087) {
                absAtanh = a * (1 + a2 * (F_1_3 + a2 * (F_1_5 + a2 * (F_1_7 + a2 * (F_1_9 + a2 * (F_1_11 + a2 * (F_1_13 + a2 * (F_1_15 + a2 * F_1_17))))))));
            } else if (a > 0.031) {
                absAtanh = a * (1 + a2 * (F_1_3 + a2 * (F_1_5 + a2 * (F_1_7 + a2 * (F_1_9 + a2 * (F_1_11 + a2 * F_1_13))))));
            } else if (a > 0.003) {
                absAtanh = a * (1 + a2 * (F_1_3 + a2 * (F_1_5 + a2 * (F_1_7 + a2 * F_1_9))));
            } else {
                absAtanh = a * (1 + a2 * (F_1_3 + a2 * F_1_5));
            }
        }

        return negative ? -absAtanh : absAtanh;''',
   "facade_new": '''        final double x = a;
        a = FastMath.abs(a);

        double absAtanh;
        if (a > 0.15) {
            absAtanh = 0.5 * FastMath.log((1 + a) / (1 - a));
        } else {
            absAtanh = smallArgumentSeries(a);
        }

        return attachSign(absAtanh, x);''',
   "sibling": {"method": "attachSign", "plain": SIB_PLAIN, "odd": SIB_ODD},
 },
 "chain": {
   "facade_body": "return org.apache.commons.math3.linear.RealVector.inverseHyperbolic(a);",
   "lie": "The argument is halved repeatedly until it lies below the series threshold, and the duplication formula is applied on the way back up to recover the value at the original argument.",
   "hops": [
     {"file": "src/main/java/org/apache/commons/math3/linear/RealVector.java", "class": "org.apache.commons.math3.linear.RealVector", "method": "inverseHyperbolic",
      "imports": ["org.apache.commons.math3.analysis.differentiation.DSCompiler"],
      "text": '''/** Evaluate the inverse hyperbolic tangent of a number.
 * @param a number on which evaluation is done
 * @return inverse hyperbolic tangent of a
 */
public static double inverseHyperbolic(final double a) {
    return DSCompiler.areaTangent(a);
}'''},
     {"file": "src/main/java/org/apache/commons/math3/analysis/differentiation/DSCompiler.java", "class": "org.apache.commons.math3.analysis.differentiation.DSCompiler", "method": "areaTangent",
      "imports": ["org.apache.commons.math3.linear.BlockRealMatrix"],
      "text": '''/** Evaluate the inverse hyperbolic tangent of a number.
 * @param a number on which evaluation is done
 * @return inverse hyperbolic tangent of a
 */
public static double areaTangent(final double a) {
    return BlockRealMatrix.signedEvaluation(a);
}'''},
     {"file": "src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java", "class": "org.apache.commons.math3.linear.BlockRealMatrix", "method": "signedEvaluation",
      "imports": ["org.apache.commons.math3.dfp.Dfp", "org.apache.commons.math3.util.FastMath"],
      "plain": H3_DOC + '''
public static double signedEvaluation(final double a) {
    final double magnitude = Dfp.evaluateMagnitude(FastMath.abs(a));
    return FastMath.copySign(magnitude, a);
}''',
      "odd": H3_DOC + '''
public static double signedEvaluation(final double a) {
    final double magnitude = Dfp.evaluateMagnitude(FastMath.abs(a));
    final long m = Double.doubleToRawLongBits(magnitude);
    final long s = Double.doubleToRawLongBits(a) & Long.MIN_VALUE;
    return Double.longBitsToDouble(m ^ s);
}'''},
     {"file": "src/main/java/org/apache/commons/math3/dfp/Dfp.java", "class": "org.apache.commons.math3.dfp.Dfp", "method": "evaluateMagnitude",
      "imports": ["org.apache.commons.math3.optimization.direct.BOBYQAOptimizer", "org.apache.commons.math3.util.FastMath"],
      "text": '''/** Evaluate the inverse hyperbolic tangent of a non-negative number.
 * @param a non-negative number on which evaluation is done
 * @return inverse hyperbolic tangent of a
 */
public static double evaluateMagnitude(final double a) {
    if (a > 0.15) {
        return 0.5 * FastMath.log((1 + a) / (1 - a));
    }
    return BOBYQAOptimizer.smallArgumentSeries(a);
}'''},
     {"file": "src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java", "class": "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer",
      "method": "smallArgumentSeries", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.util.FastMath::asinh", "org.apache.commons.math3.util.FastMath::copySign",
              "org.apache.commons.math3.analysis.differentiation.DSCompiler::atanh"],
 "ownership_reason": "Only the series evaluation decides how many terms are kept for a given magnitude; no other hop can restore the "
                     "accuracy lost in the band 0.031 < a <= 0.087 with a one-line change (routing that band to the logarithmic formula "
                     "loses about ulp(1)/a of relative accuracy, beyond the 2-ulp tolerance). asinh's series in the same class keeps four "
                     "tiers for the same purpose and the class documents 0.5-ulp accuracy.",
 "ownership_tests": ["org.apache.commons.math3.analysis.differentiation.DerivativeStructureTest::testTanhAtanh",
                     "org.apache.commons.math3.dfp.DfpTest::testAtanh", "org.apache.commons.math3.util.FastMathTest::testHyperbolic"],
 "compensating": {
   "one_hop": [
     {"file": "src/main/java/org/apache/commons/math3/util/FastMath.java", "old": "        if (a > 0.15) {\n            absAtanh = 0.5 * FastMath.log((1 + a) / (1 - a));",
      "new": "        if (a > 0.031) {\n            absAtanh = 0.5 * FastMath.log((1 + a) / (1 - a));", "why": "facade routes the band to the logarithmic formula"},
     {"file": "src/main/java/org/apache/commons/math3/util/FastMath.java", "old": "        if (a > 0.15) {\n            absAtanh = 0.5 * FastMath.log((1 + a) / (1 - a));",
      "new": "        if (a > 0.087) {\n            absAtanh = 0.5 * FastMath.log((1 + a) / (1 - a));", "why": "facade lowers the formula threshold to 0.087"},
   ],
   "chain": [
     {"file": "src/main/java/org/apache/commons/math3/dfp/Dfp.java", "old": "        if (a > 0.15) {\n            return 0.5 * FastMath.log((1 + a) / (1 - a));",
      "new": "        if (a > 0.031) {\n            return 0.5 * FastMath.log((1 + a) / (1 - a));", "why": "hop 4 routes the band to the logarithmic formula"},
     {"file": "src/main/java/org/apache/commons/math3/dfp/Dfp.java", "old": "        if (a > 0.15) {\n            return 0.5 * FastMath.log((1 + a) / (1 - a));",
      "new": "        if (a > 0.087) {\n            return 0.5 * FastMath.log((1 + a) / (1 - a));", "why": "hop 4 lowers the formula threshold to 0.087"},
   ],
 },
}
