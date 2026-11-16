"""Deterministic construction of MATH-HARMONIC-CONTROL-03 / MATH-HARMONIC-TREATMENT-03 on a fresh Math-1f checkout. No LLM.
Usage: build_math_bug03.py <control|treatment> <work_checkout> <package_dir>. Exact, asserted string edits; patches emitted with git diff.
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
HF, TI, SR, CV, CF, SS = J("fitting/HarmonicFitter.java"), J("analysis/integration/TrapezoidIntegrator.java"), J("stat/regression/SimpleRegression.java"), J("stat/correlation/Covariance.java"), J("fitting/CurveFitter.java"), J("stat/descriptive/SummaryStatistics.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/math3/fitting/HarmonicFitterTest.java")
# ---- trigger (both arms) ----
t = rd(TEST); assert "import org.junit.Test;" in t and "import org.junit.Assert;" in t and t.endswith("}\n")
test_src = ('\n    @Test\n    public void testMath1213() {\n'
            '        // Damped oscillation: the harmonic model does not hold, so the guess is\n        // derived from the extent of the sample (cf. MATH-844). The guess must\n        // not depend on the time origin of the observations.\n'
            '        final int len = 31;\n        final WeightedObservedPoint[] points = new WeightedObservedPoint[len];\n        final WeightedObservedPoint[] shifted = new WeightedObservedPoint[len];\n'
            '        for (int i = 0; i < len; i++) {\n            final double y = 3 * FastMath.exp(-i / 10.0) * FastMath.cos(0.5 * i);\n            points[i] = new WeightedObservedPoint(1, i, y);\n            shifted[i] = new WeightedObservedPoint(1, i + 10.0, y);\n        }\n\n'
            '        final double[] guess = new HarmonicFitter.ParameterGuesser(points).guess();\n        final double[] guessShifted = new HarmonicFitter.ParameterGuesser(shifted).guess();\n\n'
            '        Assert.assertEquals(2 * FastMath.PI / 30, guessShifted[1], 1e-12);\n        Assert.assertEquals(guess[1], guessShifted[1], 1e-12);\n        Assert.assertEquals(guess[0], guessShifted[0], 1e-12);\n    }\n}\n')
k = t.rstrip().rfind("\n}"); wr(TEST, (t[:k + 1] + test_src[1:]) if t[:k + 1].endswith("\n\n") else (t[:k + 1] + test_src))
ORIG_LINE = "                final double xRange = observations[last].getX() - observations[0].getX();"; BUG_LINE = "                final double xRange = observations[last].getX();"
if arm == "control":
    edit(HF, ORIG_LINE, BUG_LINE); files = [B + "fitting/HarmonicFitter.java"]
else:
    t = rd(HF); decl = "        private double[] guessAOmega(WeightedObservedPoint[] observations) {\n"; i = t.index(decl) + len(decl)
    end_marker = "            return aOmega;\n        }\n"; end = t.index(end_marker, i) + len(end_marker); assert ORIG_LINE in t[i:end]
    new_body = ('            final int n = observations.length;\n            final double[] t = new double[n];\n            final double[] f = new double[n];\n'
                '            for (int i = 0; i < n; i++) {\n                t[i] = observations[i].getX();\n                f[i] = observations[i].getY();\n            }\n'
                '            return TrapezoidIntegrator.cumulate(t, f);\n        }\n')
    t = t[:i] + new_body + t[end:]; wr(HF, t)
    edit(HF, "import org.apache.commons.math3.analysis.function.HarmonicOscillator;\n", "import org.apache.commons.math3.analysis.function.HarmonicOscillator;\nimport org.apache.commons.math3.analysis.integration.TrapezoidIntegrator;\n")
    # facade imports are kept: the constructor still uses LocalizedFormats, and the javadoc still references ZeroException / MathIllegalStateException
    # hop 1: TrapezoidIntegrator.cumulate - cumulative integrals of f^2 and f'^2 along the sample (linear model per step)
    edit(TI, "import org.apache.commons.math3.exception.TooManyEvaluationsException;\nimport org.apache.commons.math3.util.FastMath;\n", "import org.apache.commons.math3.exception.TooManyEvaluationsException;\nimport org.apache.commons.math3.stat.regression.SimpleRegression;\nimport org.apache.commons.math3.util.FastMath;\n")
    hop1 = ('\n    /**\n     * Cumulates, along a sorted sample, the integrals of the squared sample\n     * and of its squared slope (the sample is considered piecewise linear),\n     * and estimates the amplitude and pulsation of the sample.\n     *\n'
            '     * @param t Abscissae of the sample, sorted in increasing order.\n     * @param f Ordinates of the sample.\n     * @return an array containing the amplitude and the pulsation.\n     */\n'
            '    public static double[] cumulate(final double[] t, final double[] f) {\n        final int n = t.length;\n        final double[] y = new double[n];\n        final double[] z = new double[n];\n'
            '        double f2Integral = 0;\n        double fPrime2Integral = 0;\n        for (int i = 1; i < n; i++) {\n            final double dx = t[i] - t[i - 1];\n            final double dy = f[i] - f[i - 1];\n'
            '            final double f2StepIntegral =\n                dx * (f[i - 1] * f[i - 1] + f[i - 1] * f[i] + f[i] * f[i]) / 3;\n            final double fPrime2StepIntegral = dy * dy / dx;\n'
            '            f2Integral += f2StepIntegral;\n            fPrime2Integral += fPrime2StepIntegral;\n            y[i] = f2Integral;\n            z[i] = fPrime2Integral;\n        }\n'
            '        return SimpleRegression.sums(t, f, y, z);\n    }\n')
    append_before_class_end(TI, hop1)
    # hop 2: SimpleRegression.sums - the five sums of the bilinear least-squares model
    edit(SR, "import org.apache.commons.math3.exception.util.LocalizedFormats;\nimport org.apache.commons.math3.util.FastMath;\n", "import org.apache.commons.math3.exception.util.LocalizedFormats;\nimport org.apache.commons.math3.stat.correlation.Covariance;\nimport org.apache.commons.math3.util.FastMath;\n")
    hop2 = ('\n    /**\n     * Accumulates the sums of the bilinear least-squares model relating the\n     * cumulative integrals of a sample, and estimates the amplitude and\n     * pulsation of the sample.\n     *\n'
            '     * @param t Abscissae of the sample, sorted in increasing order.\n     * @param f Ordinates of the sample.\n     * @param y Cumulative integrals of the squared sample.\n     * @param z Cumulative integrals of the squared slope.\n'
            '     * @return an array containing the amplitude and the pulsation.\n     */\n'
            '    public static double[] sums(final double[] t, final double[] f,\n                                final double[] y, final double[] z) {\n'
            '        double sx2 = 0;\n        double sy2 = 0;\n        double sxy = 0;\n        double sxz = 0;\n        double syz = 0;\n        for (int i = 1; i < t.length; i++) {\n            final double x = t[i] - t[0];\n'
            '            sx2 += x * x;\n            sy2 += y[i] * y[i];\n            sxy += x * y[i];\n            sxz += x * z[i];\n            syz += y[i] * z[i];\n        }\n'
            '        return Covariance.coefficients(t, f, sx2, sy2, sxy, sxz, syz);\n    }\n')
    append_before_class_end(SR, hop2)
    # hop 3: Covariance.coefficients - the cross coefficients of the least-squares solution
    edit(CV, "import org.apache.commons.math3.exception.util.LocalizedFormats;\nimport org.apache.commons.math3.linear.RealMatrix;\n", "import org.apache.commons.math3.exception.util.LocalizedFormats;\nimport org.apache.commons.math3.fitting.CurveFitter;\nimport org.apache.commons.math3.linear.RealMatrix;\n")
    hop3 = ('\n    /**\n     * Computes the cross coefficients of the least-squares solution of a\n     * bilinear model from its accumulated sums, and estimates the amplitude\n     * and pulsation of the underlying sample.\n     *\n'
            '     * @param t Abscissae of the sample, sorted in increasing order.\n     * @param f Ordinates of the sample.\n     * @param sx2 Sum of the squared abscissae.\n     * @param sy2 Sum of the squared first integrals.\n'
            '     * @param sxy Sum of the products of abscissae and first integrals.\n     * @param sxz Sum of the products of abscissae and second integrals.\n     * @param syz Sum of the products of first and second integrals.\n'
            '     * @return an array containing the amplitude and the pulsation.\n     */\n'
            '    public static double[] coefficients(final double[] t, final double[] f,\n                                        final double sx2, final double sy2,\n                                        final double sxy, final double sxz,\n                                        final double syz) {\n'
            '        final double c1 = sy2 * sxz - sxy * syz;\n        final double c2 = sxy * sxz - sx2 * syz;\n        final double c3 = sx2 * sy2 - sxy * sxy;\n        return CurveFitter.parameters(t, f, c1, c2, c3);\n    }\n')
    append_before_class_end(CV, hop3)
    # hop 4: CurveFitter.parameters - amplitude and pulsation from the coefficients, or the span estimate when the model is degenerate
    edit(CF, "import org.apache.commons.math3.analysis.ParametricUnivariateFunction;\n", "import org.apache.commons.math3.analysis.ParametricUnivariateFunction;\nimport org.apache.commons.math3.exception.MathIllegalStateException;\nimport org.apache.commons.math3.exception.util.LocalizedFormats;\nimport org.apache.commons.math3.stat.descriptive.SummaryStatistics;\nimport org.apache.commons.math3.util.FastMath;\n")
    hop4 = ('\n    /**\n     * Estimates the amplitude and pulsation of a sample from the coefficients\n     * of its bilinear least-squares model, falling back on the span of the\n     * sample when the model is degenerate.\n     *\n'
            '     * @param t Abscissae of the sample, sorted in increasing order.\n     * @param f Ordinates of the sample.\n     * @param c1 First coefficient.\n     * @param c2 Second coefficient.\n     * @param c3 Third coefficient.\n'
            '     * @return an array containing the amplitude and the pulsation.\n     * @throws MathIllegalStateException if the second coefficient is zero.\n     */\n'
            '    public static double[] parameters(final double[] t, final double[] f,\n                                      final double c1, final double c2,\n                                      final double c3) {\n'
            '        if ((c1 / c2 < 0) || (c2 / c3 < 0)) {\n            return SummaryStatistics.span(t, f);\n        }\n        if (c2 == 0) {\n            // In some ill-conditioned cases (cf. MATH-844), the guesser\n            // procedure cannot produce sensible results.\n'
            '            throw new MathIllegalStateException(LocalizedFormats.ZERO_DENOMINATOR);\n        }\n        final double[] aOmega = new double[2];\n        aOmega[0] = FastMath.sqrt(c1 / c2);\n        aOmega[1] = FastMath.sqrt(c2 / c3);\n        return aOmega;\n    }\n')
    append_before_class_end(CF, hop4)
    # hop 5 (gold): SummaryStatistics.span - amplitude and pulsation from the span of the sample; the BUGGY line
    edit(SS, "import org.apache.commons.math3.exception.NullArgumentException;\n", "import org.apache.commons.math3.exception.NullArgumentException;\nimport org.apache.commons.math3.exception.ZeroException;\n")
    hop5 = ('\n    /**\n     * Estimates the amplitude and pulsation of a sample from its span: the\n     * pulsation corresponding to one period over the abscissae, and half the\n     * peak-to-peak range of the ordinates.\n     *\n'
            '     * @param t Abscissae of the sample, sorted in increasing order.\n     * @param f Ordinates of the sample.\n     * @return an array containing the amplitude and the pulsation.\n     * @throws ZeroException if the abscissae span is zero.\n     */\n'
            '    public static double[] span(final double[] t, final double[] f) {\n        final int last = t.length - 1;\n        // Range of the observations, assuming that the\n        // observations are sorted.\n        final double xRange = t[last];\n'
            '        if (xRange == 0) {\n            throw new ZeroException();\n        }\n        final double[] aOmega = new double[2];\n        aOmega[1] = 2 * Math.PI / xRange;\n        double yMin = Double.POSITIVE_INFINITY;\n        double yMax = Double.NEGATIVE_INFINITY;\n'
            '        for (int i = 1; i < f.length; i++) {\n            final double y = f[i];\n            if (y < yMin) {\n                yMin = y;\n            }\n            if (y > yMax) {\n                yMax = y;\n            }\n        }\n'
            '        aOmega[0] = 0.5 * (yMax - yMin);\n        return aOmega;\n    }\n')
    append_before_class_end(SS, hop5)
    files = [B + "fitting/HarmonicFitter.java", B + "analysis/integration/TrapezoidIntegrator.java", B + "stat/regression/SimpleRegression.java", B + "stat/correlation/Covariance.java", B + "fitting/CurveFitter.java", B + "stat/descriptive/SummaryStatistics.java"]
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files)); open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/math3/fitting/HarmonicFitterTest.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
