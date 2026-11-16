"""Deterministic construction of MATH-BICUBIC-CONTROL-02 / MATH-BICUBIC-TREATMENT-02 on a fresh Math-1f checkout. No LLM.
Usage: build_math_bug02.py <control|treatment> <work_checkout> <package_dir>. Exact, asserted string edits; patches emitted with git diff.
NON-CANONICAL / CORE BENCHMARK SCALE-UP / NO GPT-5.6 RUNS PERFORMED."""
import os, subprocess, sys, hashlib
arm, work, pkg = sys.argv[1], sys.argv[2], sys.argv[3]
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, t): open(p, "w", encoding="utf-8").write(t)
def edit(path, old, new):
    t = rd(path); assert t.count(old) == 1, f"{os.path.basename(path)}: expected exactly one match for {old[:70]!r}, got {t.count(old)}"; wr(path, t.replace(old, new, 1))
def append_before_class_end(path, block):
    t = rd(path); assert t.endswith("}\n"); k = t.rstrip().rfind("\n}")
    if t[:k + 1].endswith("\n\n") and block.startswith("\n"): block = block[1:]
    wr(path, t[:k + 1] + block + t[k + 1:])
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
B = "src/main/java/org/apache/commons/math3/"; J = lambda *p: os.path.join(work, B, *p)
BI, SI, PS, FU, PU, DD = J("analysis/interpolation/BicubicSplineInterpolator.java"), J("analysis/interpolation/SplineInterpolator.java"), J("analysis/polynomials/PolynomialSplineFunction.java"), J("analysis/FunctionUtils.java"), J("analysis/polynomials/PolynomialsUtils.java"), J("analysis/interpolation/DividedDifferenceInterpolator.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/math3/analysis/interpolation/BicubicSplineInterpolatorTest.java")
# ---- trigger (both arms): appended before the class's closing brace; neutral issue-style name ----
t = rd(TEST); assert "import org.junit.Test;" in t and "import org.junit.Assert;" in t and t.endswith("}\n")
test_src = ('\n    /**\n     * Test of the interpolation of a bilinear sample.\n     */\n    @Test\n    public void testMath1181() {\n'
            '        final double[] xval = new double[] {0, 1, 2};\n        final double[] yval = new double[] {0, 1, 2};\n'
            '        final double[][] fval = new double[xval.length][yval.length];\n        for (int i = 0; i < xval.length; i++) {\n            for (int j = 0; j < yval.length; j++) {\n'
            '                fval[i][j] = xval[i] * yval[j];\n            }\n        }\n\n'
            '        final BicubicSplineInterpolator interpolator = new BicubicSplineInterpolator();\n        final BicubicSplineInterpolatingFunction p = interpolator.interpolate(xval, yval, fval);\n\n'
            '        Assert.assertEquals(1.0, p.partialDerivativeXY(1.0, 1.0), 1e-12);\n        Assert.assertEquals(0.25, p.value(0.5, 0.5), 1e-12);\n        Assert.assertEquals(2.25, p.value(1.5, 1.5), 1e-12);\n    }\n}\n')
k = t.rstrip().rfind("\n}"); wr(TEST, t[:k + 1] + test_src[1:] if t[:k + 1].endswith("\n\n") else t[:k + 1] + test_src)
ORIG_LINE = "                    ((xval[nI] - xval[pI]) * (yval[nJ] - yval[pJ]));"; BUG_LINE = "                    (4 * (xval[nI] - xval[pI]) * (yval[nJ] - yval[pJ]));"
if arm == "control":
    edit(BI, ORIG_LINE, BUG_LINE); files = [B + "analysis/interpolation/BicubicSplineInterpolator.java"]
else:
    # facade: keep the argument checks and the transposition of the sample; delegate the spline construction to hop 1
    t = rd(BI); start = t.index("        final SplineInterpolator spInterpolator = new SplineInterpolator();\n"); end_marker = "                                                      dFdX, dFdY, d2FdXdY);\n    }\n"
    end = t.index(end_marker) + len(end_marker); assert ORIG_LINE in t[start:end]
    t = t[:start] + "        final double[][][] partials = SplineInterpolator.lace(xval, yval, fval, fX);\n\n        // Create the interpolating splines\n        return new BicubicSplineInterpolatingFunction(xval, yval, fval,\n                                                      partials[0], partials[1],\n                                                      partials[2]);\n    }\n" + t[end:]
    h1 = t.index("    /**\n     * Computes the next index of an array, clipping if necessary.\n"); h2 = t.index("        return index >= 0 ? index : 0;\n    }\n") + len("        return index >= 0 ? index : 0;\n    }\n")
    t = t[:h1].rstrip("\n") + "\n" + t[h2:]; wr(BI, t)
    edit(BI, "import org.apache.commons.math3.analysis.UnivariateFunction;\nimport org.apache.commons.math3.analysis.polynomials.PolynomialSplineFunction;\n", "")
    # hop 1: SplineInterpolator.lace - the splines along the first variable
    assert "import org.apache.commons.math3.analysis.polynomials.PolynomialSplineFunction;" in rd(SI)
    hop1 = ('\n    /**\n     * Laces a bivariate sample with splines along the first variable and\n     * gathers the partial derivatives at the grid knots.\n     *\n'
            '     * @param xval All the x-coordinates of the interpolation points, sorted\n     * in increasing order.\n     * @param yval All the y-coordinates of the interpolation points, sorted\n     * in increasing order.\n'
            '     * @param fval The values of the interpolation points on all the grid knots:\n     * {@code fval[i][j] = f(xval[i], yval[j])}.\n     * @param fX The transposed sample: {@code fX[j][i] = fval[i][j]}.\n'
            '     * @return the partial derivatives at the grid knots.\n     */\n'
            '    public static double[][][] lace(final double[] xval,\n                                                          final double[] yval,\n                                                          final double[][] fval,\n                                                          final double[][] fX) {\n'
            '        final int yLen = yval.length;\n        final SplineInterpolator spInterpolator = new SplineInterpolator();\n\n'
            '        // For each line y[j] (0 <= j < yLen), construct a 1D spline with\n        // respect to variable x\n        final PolynomialSplineFunction[] ySplineX = new PolynomialSplineFunction[yLen];\n'
            '        for (int j = 0; j < yLen; j++) {\n            ySplineX[j] = spInterpolator.interpolate(xval, fX[j]);\n        }\n\n'
            '        return PolynomialSplineFunction.weave(xval, yval, fval, ySplineX);\n    }\n')
    append_before_class_end(SI, hop1)
    # hop 2: PolynomialSplineFunction.weave - the splines along the second variable
    edit(PS, "import org.apache.commons.math3.analysis.differentiation.UnivariateDifferentiableFunction;\n", "import org.apache.commons.math3.analysis.differentiation.UnivariateDifferentiableFunction;\nimport org.apache.commons.math3.analysis.interpolation.SplineInterpolator;\n")
    hop2 = ('\n    /**\n     * Weaves a bivariate sample with splines along the second variable and\n     * gathers the partial derivatives at the grid knots.\n     *\n'
            '     * @param xval All the x-coordinates of the interpolation points, sorted\n     * in increasing order.\n     * @param yval All the y-coordinates of the interpolation points, sorted\n     * in increasing order.\n'
            '     * @param fval The values of the interpolation points on all the grid knots.\n     * @param ySplineX The splines along the first variable, one per {@code yval}.\n'
            '     * @return the partial derivatives at the grid knots.\n     */\n'
            '    public static double[][][] weave(final double[] xval,\n                                                           final double[] yval,\n                                                           final double[][] fval,\n                                                           final PolynomialSplineFunction[] ySplineX) {\n'
            '        final int xLen = xval.length;\n        final SplineInterpolator spInterpolator = new SplineInterpolator();\n\n'
            '        // For each line x[i] (0 <= i < xLen), construct a 1D spline with\n        // respect to variable y generated by array fY_1[i]\n        final PolynomialSplineFunction[] xSplineY = new PolynomialSplineFunction[xLen];\n'
            '        for (int i = 0; i < xLen; i++) {\n            xSplineY[i] = spInterpolator.interpolate(yval, fval[i]);\n        }\n\n'
            '        return FunctionUtils.slope(xval, yval, fval, ySplineX, xSplineY);\n    }\n')
    append_before_class_end(PS, hop2)
    edit(PS, "import org.apache.commons.math3.analysis.DifferentiableUnivariateFunction;\n", "import org.apache.commons.math3.analysis.DifferentiableUnivariateFunction;\nimport org.apache.commons.math3.analysis.FunctionUtils;\n")
    # hop 3: FunctionUtils.slope - partial derivatives with respect to x at the grid knots
    edit(FU, "import org.apache.commons.math3.analysis.function.Identity;\n", "import org.apache.commons.math3.analysis.function.Identity;\nimport org.apache.commons.math3.analysis.polynomials.PolynomialSplineFunction;\nimport org.apache.commons.math3.analysis.polynomials.PolynomialsUtils;\n")
    hop3 = ('\n    /**\n     * Evaluates the slopes of a woven bivariate sample along the first\n     * variable at the grid knots and gathers the partial derivatives at the\n     * grid knots.\n     *\n'
            '     * @param xval All the x-coordinates of the interpolation points.\n     * @param yval All the y-coordinates of the interpolation points.\n     * @param fval The values of the interpolation points on all the grid knots.\n'
            '     * @param ySplineX The splines along the first variable, one per {@code yval}.\n     * @param xSplineY The splines along the second variable, one per {@code xval}.\n'
            '     * @return the partial derivatives at the grid knots.\n     */\n'
            '    public static double[][][] slope(final double[] xval,\n                                                           final double[] yval,\n                                                           final double[][] fval,\n                                                           final PolynomialSplineFunction[] ySplineX,\n                                                           final PolynomialSplineFunction[] xSplineY) {\n'
            '        final int xLen = xval.length;\n        final int yLen = yval.length;\n\n'
            '        // Partial derivatives with respect to x at the grid knots\n        final double[][] dFdX = new double[xLen][yLen];\n        for (int j = 0; j < yLen; j++) {\n            final UnivariateFunction f = ySplineX[j].derivative();\n'
            '            for (int i = 0; i < xLen; i++) {\n                dFdX[i][j] = f.value(xval[i]);\n            }\n        }\n\n'
            '        return PolynomialsUtils.rise(xval, yval, fval, xSplineY, dFdX);\n    }\n')
    append_before_class_end(FU, hop3)
    # hop 4: PolynomialsUtils.rise - partial derivatives with respect to y at the grid knots
    edit(PU, "import org.apache.commons.math3.fraction.BigFraction;\n", "import org.apache.commons.math3.analysis.UnivariateFunction;\nimport org.apache.commons.math3.analysis.interpolation.DividedDifferenceInterpolator;\nimport org.apache.commons.math3.fraction.BigFraction;\n")
    hop4 = ('\n    /**\n     * Evaluates the rises of a woven bivariate sample along the second\n     * variable at the grid knots and gathers the partial derivatives at the\n     * grid knots.\n     *\n'
            '     * @param xval All the x-coordinates of the interpolation points.\n     * @param yval All the y-coordinates of the interpolation points.\n     * @param fval The values of the interpolation points on all the grid knots.\n'
            '     * @param xSplineY The splines along the second variable, one per {@code xval}.\n     * @param dFdX The partial derivatives with respect to x at the grid knots.\n'
            '     * @return the partial derivatives at the grid knots.\n     */\n'
            '    public static double[][][] rise(final double[] xval,\n                                                          final double[] yval,\n                                                          final double[][] fval,\n                                                          final PolynomialSplineFunction[] xSplineY,\n                                                          final double[][] dFdX) {\n'
            '        final int xLen = xval.length;\n        final int yLen = yval.length;\n\n'
            '        // Partial derivatives with respect to y at the grid knots\n        final double[][] dFdY = new double[xLen][yLen];\n        for (int i = 0; i < xLen; i++) {\n            final UnivariateFunction f = xSplineY[i].derivative();\n'
            '            for (int j = 0; j < yLen; j++) {\n                dFdY[i][j] = f.value(yval[j]);\n            }\n        }\n\n'
            '        return DividedDifferenceInterpolator.warp(xval, yval, fval, dFdX, dFdY);\n    }\n')
    append_before_class_end(PU, hop4)
    # hop 5 (gold): DividedDifferenceInterpolator.warp - the mixed partial derivatives by central differences; the BUGGY line
    hop5 = ('\n    /**\n     * Estimates the mixed partial derivatives of a bivariate sample at the\n     * grid knots by central differences and gathers all partial derivatives.\n     *\n'
            '     * @param xval All the x-coordinates of the interpolation points.\n     * @param yval All the y-coordinates of the interpolation points.\n     * @param fval The values of the interpolation points on all the grid knots.\n'
            '     * @param dFdX The partial derivatives with respect to x at the grid knots.\n     * @param dFdY The partial derivatives with respect to y at the grid knots.\n'
            '     * @return the partial derivatives at the grid knots.\n     */\n'
            '    public static double[][][] warp(final double[] xval,\n                                                           final double[] yval,\n                                                           final double[][] fval,\n                                                           final double[][] dFdX,\n                                                           final double[][] dFdY) {\n'
            '        final int xLen = xval.length;\n        final int yLen = yval.length;\n\n'
            '        // Mixed partial derivatives\n        final double[][] d2FdXdY = new double[xLen][yLen];\n        for (int i = 0; i < xLen ; i++) {\n            final int nI = after(i, xLen);\n            final int pI = before(i);\n'
            '            for (int j = 0; j < yLen; j++) {\n                final int nJ = after(j, yLen);\n                final int pJ = before(j);\n'
            '                final double dx = xval[nI] - xval[pI];\n                final double dy = yval[nJ] - yval[pJ];\n'
            '                d2FdXdY[i][j] = (fval[nI][nJ] - fval[nI][pJ] -\n                                 fval[pI][nJ] + fval[pI][pJ]) / (4 * dx * dy);\n            }\n        }\n\n'
            '        return new double[][][] {dFdX, dFdY, d2FdXdY};\n    }\n\n'
            '    /**\n     * Computes the next index of an array, clipping if necessary.\n     * It is assumed (but not checked) that {@code i >= 0}.\n     *\n     * @param i Index.\n     * @param max Upper limit of the array.\n     * @return the next index.\n     */\n'
            '    private static int after(int i, int max) {\n        final int index = i + 1;\n        return index < max ? index : index - 1;\n    }\n\n'
            '    /**\n     * Computes the previous index of an array, clipping if necessary.\n     * It is assumed (but not checked) that {@code i} is smaller than the size\n     * of the array.\n     *\n     * @param i Index.\n     * @return the previous index.\n     */\n'
            '    private static int before(int i) {\n        final int index = i - 1;\n        return index >= 0 ? index : 0;\n    }\n')
    append_before_class_end(DD, hop5)
    files = [B + "analysis/interpolation/BicubicSplineInterpolator.java", B + "analysis/interpolation/SplineInterpolator.java", B + "analysis/polynomials/PolynomialSplineFunction.java", B + "analysis/FunctionUtils.java", B + "analysis/polynomials/PolynomialsUtils.java", B + "analysis/interpolation/DividedDifferenceInterpolator.java"]
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files)); open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/math3/analysis/interpolation/BicubicSplineInterpolatorTest.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
