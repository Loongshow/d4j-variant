"""Deterministic construction of MATH-NORM-CONTROL-01 / MATH-NORM-TREATMENT-01 on a fresh Math-1f checkout. No LLM.
Usage: build_math.py <control|treatment> <work_checkout> <package_dir>. Exact, asserted string edits; patches emitted with git diff."""
import os, subprocess, sys, hashlib
arm, work, pkg = sys.argv[1], sys.argv[2], sys.argv[3]
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, t): open(p, "w", encoding="utf-8").write(t)
def edit(path, old, new):
    t = rd(path); assert t.count(old) == 1, f"{os.path.basename(path)}: expected exactly one match for {old[:70]!r}, got {t.count(old)}"; wr(path, t.replace(old, new, 1))
def insert_before(path, anchor, block):
    t = rd(path); assert t.count(anchor) == 1, f"{os.path.basename(path)}: anchor not unique ({t.count(anchor)}): {anchor[:60]!r}"; wr(path, t.replace(anchor, block + anchor, 1))
def insert_after(path, anchor, block):
    t = rd(path); assert t.count(anchor) == 1, f"{os.path.basename(path)}: anchor not unique ({t.count(anchor)}): {anchor[:60]!r}"; wr(path, t.replace(anchor, anchor + block, 1))
def insert_before_javadoc_of(path, decl, block):
    t = rd(path); i = t.find(decl); assert i > 0 and t.count(decl) == 1, decl; j = t.rfind("    /**", 0, i); assert j > 0; wr(path, t[:j] + block + t[j:])
def append_before_class_end(path, block):
    t = rd(path); assert t.endswith("}\n"); k = t.rstrip().rfind("\n}"); wr(path, t[:k + 1] + block + t[k + 1:])
def method_end(t, decl):
    i = t.find(decl); assert i > 0 and t.count(decl) == 1, decl; d = 0; st = False; j = i
    while j < len(t):
        c = t[j]; d += (c == "{") - (c == "}"); st = st or c == "{"
        if st and d == 0: return j + 1
        j += 1
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
B = "src/main/java/org/apache/commons/math3/"; J = lambda *p: os.path.join(work, B, *p)
MA, SU, MU, PR, MX, FM = J("util/MathArrays.java"), J("stat/StatUtils.java"), J("util/MathUtils.java"), J("util/Precision.java"), J("linear/MatrixUtils.java"), J("util/FastMath.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/math3/util/MathArraysTest.java")
# ---- trigger (both arms): appended before the class's closing brace; neutral issue-style name ----
t = rd(TEST); assert "import org.junit.Test;" in t and "import org.junit.Assert;" in t and t.endswith("    }\n}\n")
test_src = ('\n    @Test\n    public void testMath1142() {\n'
            '        Assert.assertEquals(5.0, MathArrays.safeNorm(new double[] { 3.0, 4.0 }), 0d);\n'
            '        Assert.assertEquals(2.0e19, MathArrays.safeNorm(new double[] { 2.0e19, 1.0e10 }), 0d);\n'
            '        Assert.assertEquals(5.0e19, MathArrays.safeNorm(new double[] { -3.0e19, 4.0e19, 5.0e9 }), 0d);\n    }\n}\n')
wr(TEST, t[:-2] + test_src)
ORIG_LINE = "            norm = x1max * Math.sqrt(s1 + (s2 / x1max) / x1max);"; BUG_LINE = "            norm = x1max * Math.sqrt(s1 + s2 / x1max);"
if arm == "control":
    edit(MA, ORIG_LINE, BUG_LINE); files = [B + "util/MathArrays.java"]
else:
    # facade: keep the constants and the threshold derivation; delegate the three magnitude classes to the chain
    t = rd(MA); i = t.find("    public static double safeNorm(double[] v) {\n"); assert i > 0
    body_start = i + len("    public static double safeNorm(double[] v) {\n"); body_end = method_end(t, "    public static double safeNorm(double[] v) {")
    old_body = t[body_start:body_end]; assert ORIG_LINE in old_body and old_body.rstrip().endswith("return norm;\n    }") or old_body.rstrip().endswith("}")
    new_body = ('        double rdwarf = 3.834e-20;\n        double rgiant = 1.304e+19;\n        double floatn = v.length;\n        double agiant = rgiant / floatn;\n'
                '        return StatUtils.survey(v, rdwarf, agiant);\n    }')
    wr(MA, t[:body_start] + new_body + t[body_end:])
    edit(MA, "import org.apache.commons.math3.random.Well19937c;\n", "import org.apache.commons.math3.random.Well19937c;\nimport org.apache.commons.math3.stat.StatUtils;\n")
    # hop 1: StatUtils.survey - the entries above the ceiling, accumulated relative to the largest of them; anchored before sumSq's javadoc
    hop1 = ('    /**\n     * Surveys the entries of an array that lie above a ceiling.\n     *\n'
            '     * @param values the input array\n     * @param floor the smallest magnitude taken into account\n'
            '     * @param ceiling the largest magnitude taken into account\n     * @return the surveyed value of the array\n     */\n'
            '    public static double survey(final double[] values, final double floor, final double ceiling) {\n'
            '        double major = 0;\n        double top = 0;\n        for (int i = 0; i < values.length; i++) {\n            final double x = Math.abs(values[i]);\n'
            '            if (x > ceiling) {\n                if (x > top) {\n                    final double r = top / x;\n                    major = 1 + major * r * r;\n                    top = x;\n'
            '                } else {\n                    final double r = x / top;\n                    major += r * r;\n                }\n            }\n        }\n'
            '        return MathUtils.balance(values, floor, ceiling, major, top);\n    }\n\n')
    insert_before_javadoc_of(SU, "    public static double sumSq(final double[] values) throws MathIllegalArgumentException {", hop1)
    edit(SU, "import org.apache.commons.math3.stat.descriptive.summary.SumOfSquares;\n", "import org.apache.commons.math3.stat.descriptive.summary.SumOfSquares;\nimport org.apache.commons.math3.util.MathUtils;\n")
    # hop 2: MathUtils.balance - the entries between floor and ceiling, squared and summed; anchored before copySign's javadoc block (first copySign overload)
    hop2 = ('    /**\n     * Accumulates the squares of the entries of an array that lie between\n     * a floor and a ceiling.\n     *\n'
            '     * @param values Input array.\n     * @param floor Smallest magnitude taken into account.\n     * @param ceiling Largest magnitude taken into account.\n'
            '     * @param major Contribution of the entries above the ceiling.\n     * @param top Largest magnitude above the ceiling.\n     * @return the balanced value of the array.\n     */\n'
            '    public static double balance(final double[] values, final double floor, final double ceiling,\n                                 final double major, final double top) {\n'
            '        double middle = 0;\n        for (int i = 0; i < values.length; i++) {\n            final double x = Math.abs(values[i]);\n'
            '            if (!(x < floor || x > ceiling)) {\n                middle += x * x;\n            }\n        }\n'
            '        return Precision.residue(values, floor, major, top, middle);\n    }\n\n')
    t = rd(MU); decl = next(l for l in t.split("\n") if "public static byte copySign(byte magnitude, byte sign)" in l or "public static byte copySign(" in l); insert_before_javadoc_of(MU, decl, hop2)
    # hop 3: Precision.residue - the entries below the floor, accumulated relative to the largest of them; appended at the end of the class
    hop3 = ('\n    /**\n     * Accumulates the entries of an array that lie below a floor.\n     *\n'
            '     * @param values Input array.\n     * @param floor Smallest magnitude taken into account by the other sums.\n'
            '     * @param major Contribution of the largest entries.\n     * @param top Largest magnitude among the largest entries.\n'
            '     * @param middle Sum of squares of the intermediate entries.\n     * @return the residual value of the array.\n     */\n'
            '    public static double residue(final double[] values, final double floor, final double major,\n                                 final double top, final double middle) {\n'
            '        double minor = 0;\n        double bottom = 0;\n        for (int i = 0; i < values.length; i++) {\n            final double x = Math.abs(values[i]);\n'
            '            if (x < floor) {\n                if (x > bottom) {\n                    final double r = bottom / x;\n                    minor = 1 + minor * r * r;\n                    bottom = x;\n'
            '                } else if (x != 0) {\n                    final double r = x / bottom;\n                    minor += r * r;\n                }\n            }\n        }\n'
            '        return MatrixUtils.settle(major, top, middle, minor, bottom);\n    }\n')
    append_before_class_end(PR, hop3)
    edit(PR, "import org.apache.commons.math3.exception.util.LocalizedFormats;\n", "import org.apache.commons.math3.exception.util.LocalizedFormats;\nimport org.apache.commons.math3.linear.MatrixUtils;\n")
    # hop 4: MatrixUtils.settle - resolves the three partial sums; appended at the end of the class (after blockInverse)
    hop4 = ('\n    /**\n     * Settles partial sums of squares into a single value.\n     *\n'
            '     * @param major contribution of the largest entries\n     * @param top largest magnitude among the largest entries\n'
            '     * @param middle sum of squares of the intermediate entries\n     * @param minor contribution of the smallest entries\n'
            '     * @param bottom largest magnitude among the smallest entries\n     * @return the settled value\n     */\n'
            '    public static double settle(final double major, final double top, final double middle,\n                                final double minor, final double bottom) {\n'
            '        if (major != 0) {\n            return FastMath.merge(top, major, middle);\n        }\n        if (middle == 0) {\n            return bottom * FastMath.sqrt(minor);\n        }\n'
            '        if (middle >= bottom) {\n            return FastMath.sqrt(middle * (1 + (bottom / middle) * (bottom * minor)));\n        }\n'
            '        return FastMath.sqrt(bottom * ((middle / bottom) + (bottom * minor)));\n    }\n')
    append_before_class_end(MX, hop4)
    # hop 5 (gold): FastMath.merge - merges a plain sum into a scaled sum; the BUGGY line; inserted after hypot
    hop5 = ('\n    /**\n     * Merges a plain sum of squares into a sum of squares expressed\n     * relative to a scale.\n     *\n'
            '     * @param scale the scale of the first sum\n     * @param scaled the sum of squares expressed relative to the scale\n'
            '     * @param plain the plain sum of squares\n     * @return the merged value\n     */\n'
            '    public static double merge(final double scale, final double scaled, final double plain) {\n'
            '        final double relative = plain / scale;\n        return scale * sqrt(scaled + relative);\n    }\n')
    t = rd(FM); e = method_end(t, "    public static double hypot(final double x, final double y) {"); wr(FM, t[:e] + "\n\n" + hop5.strip("\n") + t[e:])
    files = [B + "util/MathArrays.java", B + "stat/StatUtils.java", B + "util/MathUtils.java", B + "util/Precision.java", B + "linear/MatrixUtils.java", B + "util/FastMath.java"]
os.makedirs(pkg, exist_ok=True)
wr(os.path.join(pkg, "variant.patch"), run(["git", "diff", "--"] + files)); wr(os.path.join(pkg, "test.patch"), run(["git", "diff", "--", "src/test/java/org/apache/commons/math3/util/MathArraysTest.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
