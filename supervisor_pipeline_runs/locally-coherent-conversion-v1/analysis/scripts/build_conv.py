"""Deterministic construction of CONVERSION-CONTROL-01 / CONVERSION-TREATMENT-01 on a fresh Lang-1f checkout. No LLM.
Usage: build_conv.py <control|treatment> <work_checkout>. Exact, asserted string edits; emits patches with git diff."""
import os, subprocess, sys
LC = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/locally-coherent-conversion-v1"
arm, work = sys.argv[1], sys.argv[2]; pkg = os.path.join(LC, "CONVERSION-CONTROL-01" if arm == "control" else "CONVERSION-TREATMENT-01")
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def edit(path, reps):
    t = open(path, encoding="utf-8").read()
    for old, new in reps:
        assert t.count(old) == 1, f"{os.path.basename(path)}: expected exactly one match for {old[:70]!r}, got {t.count(old)}"
        t = t.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(t)
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
CONV = os.path.join(work, "src/main/java/org/apache/commons/lang3/Conversion.java"); AU = os.path.join(work, "src/main/java/org/apache/commons/lang3/ArrayUtils.java"); FR = os.path.join(work, "src/main/java/org/apache/commons/lang3/math/Fraction.java"); TEST = os.path.join(work, "src/test/java/org/apache/commons/lang3/ConversionTest.java")
# ---- trigger (both arms): appended before the class's closing brace, one blank line, no comments ----
test_src = ('\n    @Test\n    public void testLang1112() {\n        final int[] src = new int[]{0xCDF1F0C1, 0x0F123456, 0x78000000};\n'
            '        assertEquals(0x0000000F12345600L, Conversion.intArrayToLong(src, 1, 0L, 8, 1));\n'
            '        assertEquals(0x1234CDF1F0C1DEF0L, Conversion.intArrayToLong(src, 0, 0x123456789ABCDEF0L, 16, 1));\n    }\n}\n')
t = open(TEST).read(); assert t.endswith("    }\n}\n"); open(TEST, "w").write(t[:-2] + test_src)
LOOP = ('        long out = dstInit;\n        int shift = 0;\n        for (int i = 0; i < nInts; i++ ) {\n            shift = i * 32 + dstPos;\n'
        '            final long bits = ((0xffffffffL & src[i + srcPos]) << shift);\n            final long mask = 0xffffffffL << shift;\n            out = (out & ~mask) | bits;\n        }\n        return out;\n    }\n')
if arm == "control":
    edit(CONV, [("            shift = i * 32 + dstPos;\n            final long bits = ((0xffffffffL & src[i + srcPos]) << shift);",
                 "            shift = (i + dstPos) * 32;\n            final long bits = ((0xffffffffL & src[i + srcPos]) << shift);")])
    files = ["src/main/java/org/apache/commons/lang3/Conversion.java"]
else:
    # facade: keep both guards verbatim, delegate the loop
    edit(CONV, [(LOOP, "        return ArrayUtils.foldValues(src, srcPos, dstInit, dstPos, nInts);\n    }\n")])
    # hop1 in ArrayUtils after subarray(int[]); import for Fraction
    hop1 = ('\n    /**\n     * <p>Folds a run of {@code int} values into a {@code long}.</p>\n     *\n     * @param values  the values to fold\n'
            '     * @param from  the index of the first value to use\n     * @param initial  the starting value of the result\n'
            '     * @param at  the position in the result at which the first value is placed\n     * @param count  the number of values to fold\n'
            '     * @return the folded value\n     * @since 3.2\n     */\n    public static long foldValues(final int[] values, final int from, final long initial, final int at, final int count) {\n'
            '        return Fraction.assemble(values, from, initial, at, count);\n    }\n')
    anchor1 = ('        final int[] subarray = new int[newSize];\n        System.arraycopy(array, startIndexInclusive, subarray, 0, newSize);\n        return subarray;\n    }\n')
    t = open(AU).read(); i = t.find("public static int[] subarray(final int[] array"); j = t.find(anchor1, i); assert i > 0 and j > 0
    t = t[:j + len(anchor1)] + hop1 + t[j + len(anchor1):]; open(AU, "w").write(t)
    edit(AU, [("import org.apache.commons.lang3.builder.ToStringStyle;\n", "import org.apache.commons.lang3.builder.ToStringStyle;\nimport org.apache.commons.lang3.math.Fraction;\n")])
    # hop2 in Fraction after subAndCheck: the loop with renamed parameters and the BUGGY line
    hop2 = ('    \n    /**\n     * Assemble a run of ints into a long.\n     *\n     * @param values the values to assemble\n     * @param from the index of the first value to use\n'
            '     * @param initial the starting value of the result\n     * @param at the position in the result at which the first value is placed\n'
            '     * @param count the number of values to assemble\n     * @return the assembled value\n     */\n'
            '    public static long assemble(final int[] values, final int from, final long initial, final int at, final int count) {\n'
            '        long out = initial;\n        int shift = 0;\n        for (int i = 0; i < count; i++ ) {\n            shift = (i + at) * 32;\n'
            '            final long bits = ((0xffffffffL & values[i + from]) << shift);\n            final long mask = 0xffffffffL << shift;\n            out = (out & ~mask) | bits;\n        }\n        return out;\n    }\n')
    anchor2 = ('    private static int subAndCheck(final int x, final int y) {\n        final long s = (long)x-(long)y;\n        if (s < Integer.MIN_VALUE ||\n            s > Integer.MAX_VALUE) {\n            throw new ArithmeticException("overflow: add");\n        }\n        return (int)s;\n    }\n')
    t = open(FR).read(); assert t.count(anchor2) == 1; t = t.replace(anchor2, anchor2 + hop2, 1); open(FR, "w").write(t)
    files = ["src/main/java/org/apache/commons/lang3/ArrayUtils.java", "src/main/java/org/apache/commons/lang3/math/Fraction.java", "src/main/java/org/apache/commons/lang3/Conversion.java"]
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/lang3/ConversionTest.java"]))
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
