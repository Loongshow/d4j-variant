"""Deterministic construction of CONVERSION-DISPATCH-CONTROL-01 / CONVERSION-DISPATCH-TREATMENT-01 on a fresh Lang-1f checkout. No LLM.
Usage: build_dispatch.py <control|treatment> <work_checkout>. Same five-stage chain as conversion-long-chain-v1, with the hop3 -> hop4 call
replaced by indirect dispatch through org.apache.commons.lang3.builder.Folding (binding Folding.STANDARD -> StandardFolding -> ObjectUtils.combine).
NON-CANONICAL / INDIRECT-DISPATCH DIAGNOSTIC / GPT-5.6."""
import os, subprocess, sys, hashlib
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/conversion-dispatch-v1"
arm, work = sys.argv[1], sys.argv[2]; pkg = os.path.join(R, "CONVERSION-DISPATCH-CONTROL-01" if arm == "control" else "CONVERSION-DISPATCH-TREATMENT-01")
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def edit(path, reps):
    t = open(path, encoding="utf-8").read()
    for old, new in reps:
        assert t.count(old) == 1, f"{os.path.basename(path)}: expected exactly one match for {old[:70]!r}, got {t.count(old)}"
        t = t.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(t)
def insert_after(path, anchor, block):
    t = open(path, encoding="utf-8").read(); assert t.count(anchor) == 1, f"{os.path.basename(path)}: anchor not unique ({t.count(anchor)}): {anchor[:60]!r}"
    open(path, "w", encoding="utf-8").write(t.replace(anchor, anchor + block, 1))
def insert_before(path, anchor, block):
    t = open(path, encoding="utf-8").read(); assert t.count(anchor) == 1, f"{os.path.basename(path)}: anchor not unique ({t.count(anchor)}): {anchor[:60]!r}"
    open(path, "w", encoding="utf-8").write(t.replace(anchor, block + anchor, 1))
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
J = lambda *p: os.path.join(work, "src/main/java/org/apache/commons/lang3", *p)
CONV, AU, EU, BF, OU, NU = J("Conversion.java"), J("ArrayUtils.java"), J("EnumUtils.java"), J("BitField.java"), J("ObjectUtils.java"), J("math", "NumberUtils.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/lang3/ConversionTest.java")
# ---- trigger (both arms, identical to the validated pair): appended before the class's closing brace ----
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
    # facade: keep both guards verbatim, delegate the loop to hop 1
    edit(CONV, [(LOOP, "        return ArrayUtils.gather(src, srcPos, dstInit, dstPos, nInts);\n    }\n")])
    # hop 1: ArrayUtils.gather — bounds-checked copy of the run; anchored after subarray(int[])
    hop1 = ('\n    /**\n     * <p>Gathers a run of elements of an {@code int} array into a {@code long}.</p>\n     *\n'
            '     * @param array  the array to gather from\n     * @param startIndex  the index of the first element to gather\n'
            '     * @param initial  the starting value of the result\n     * @param at  the position in the result at which the first element is placed\n'
            '     * @param count  the number of elements to gather\n     * @return the gathered value\n     * @since 3.2\n     */\n'
            '    public static long gather(final int[] array, final int startIndex, final long initial, final int at, final int count) {\n'
            '        final int[] run = new int[count];\n        System.arraycopy(array, startIndex, run, 0, count);\n        return EnumUtils.compose(run, initial, at);\n    }\n')
    anchor1 = ('        final int[] subarray = new int[newSize];\n        System.arraycopy(array, startIndexInclusive, subarray, 0, newSize);\n        return subarray;\n    }\n')
    t = open(AU).read(); i = t.find("public static int[] subarray(final int[] array"); j = t.find(anchor1, i); assert i > 0 and j > 0
    t = t[:j + len(anchor1)] + hop1 + t[j + len(anchor1):]; open(AU, "w").write(t)
    # hop 2: EnumUtils.compose — derives the word width and the one-word field; anchored before checkBitVectorable's javadoc
    hop2 = ('    /**\n     * <p>Composes a run of {@code int} values into a {@code long}.</p>\n     *\n'
            '     * @param run the values to compose\n     * @param initial the starting value of the result\n'
            '     * @param at the position in the result at which the first value is placed\n     * @return the composed value\n     * @since 3.2\n     */\n'
            '    public static long compose(final int[] run, final long initial, final int at) {\n'
            '        final int width = Integer.SIZE;\n        final long field = (1L << width) - 1;\n        return BitField.widen(run, initial, at, width, field);\n    }\n\n')
    insert_before(EU, '    /**\n     * Validate that {@code enumClass} is compatible with representation in a {@code long}.\n', hop2)
    # hop 3: BitField.widen — widens each value with the field; appended after setByteBoolean
    hop3 = ('\n    /**\n     * <p>Widens the values of a run to the given field.</p>\n     *\n'
            '     * @param run the values to widen\n     * @param initial the starting value of the result\n'
            '     * @param at the position in the result at which the first value is placed\n     * @param width the width of a value\n'
            '     * @param field the field covering one value\n     * @return the widened values combined into the result\n     */\n'
            '    public static long widen(final int[] run, final long initial, final int at, final int width, final long field) {\n'
            '        final long[] words = new long[run.length];\n        for (int i = 0; i < run.length; i++) {\n            words[i] = run[i] & field;\n        }\n'
            '        return Folding.STANDARD.fold(words, initial, at, width, field);\n    }\n')
    insert_after(BF, '    public byte setByteBoolean(final byte holder, final boolean flag) {\n        return flag ? setByte(holder) : clearByte(holder);\n    }\n', hop3)
    edit(BF, [('package org.apache.commons.lang3;\n\n/**', 'package org.apache.commons.lang3;\n\nimport org.apache.commons.lang3.builder.Folding;\n\n/**')])
    # dispatch abstraction + binding (ToStringStyle idiom) and the implementation (StandardToStringStyle idiom): two new files in builder
    BD = os.path.join(work, 'src/main/java/org/apache/commons/lang3/builder'); FOLD = os.path.join(BD, 'Folding.java'); SF = os.path.join(BD, 'StandardFolding.java')
    assert not os.path.exists(FOLD) and not os.path.exists(SF)
    LIC = open(os.path.join(BD, 'Builder.java')).read().split('package org.apache.commons.lang3.builder;')[0]
    open(FOLD, 'w').write(LIC + 'package org.apache.commons.lang3.builder;\n\n/**\n * <p>Folds a run of values into a single value.</p>\n *\n * <p>This class is intended to be used as a singleton. Use {@link #STANDARD} or subclass this class\n * to provide a different folding.</p>\n *\n * @since 3.2\n * @version $Id$\n */\npublic abstract class Folding {\n\n    /**\n     * The standard folding.\n     */\n    public static final Folding STANDARD = new StandardFolding();\n\n    /**\n     * <p>Constructor.</p>\n     */\n    protected Folding() {\n        super();\n    }\n\n    /**\n     * <p>Folds the values into the result.</p>\n     *\n     * @param values  the values to fold\n     * @param initial  the starting value of the result\n     * @param at  the position in the result at which the first value is placed\n     * @param width  the width of a value\n     * @param field  the field covering one value\n     * @return the folded value\n     */\n    public abstract long fold(long[] values, long initial, int at, int width, long field);\n\n}\n')
    open(SF, 'w').write(LIC + 'package org.apache.commons.lang3.builder;\n\nimport org.apache.commons.lang3.ObjectUtils;\n\n/**\n * <p>The standard {@link Folding}.</p>\n *\n * @since 3.2\n * @version $Id$\n */\npublic class StandardFolding extends Folding {\n\n    /**\n     * <p>Constructor.</p>\n     */\n    public StandardFolding() {\n        super();\n    }\n\n    /**\n     * {@inheritDoc}\n     */\n    @Override\n    public long fold(final long[] values, final long initial, final int at, final int width, final long field) {\n        return ObjectUtils.combine(values, initial, at, width, field);\n    }\n\n}\n')
    run(['git', 'add', '-N', 'src/main/java/org/apache/commons/lang3/builder/Folding.java', 'src/main/java/org/apache/commons/lang3/builder/StandardFolding.java'])
    # hop 4: ObjectUtils.combine — the accumulation loop; anchored after mode(); one new import (blends with the existing lang3 sub-package imports)
    hop4 = ('    // Combine\n    //-----------------------------------------------------------------------\n    /**\n     * Combine a run of values into a single value.\n     *\n'
            '     * @param words the values to combine\n     * @param initial the starting value of the result\n'
            '     * @param at the position in the result at which the first value is placed\n     * @param width the width of a value\n'
            '     * @param field the field covering one value\n     * @return the combined value\n     * @since 3.2\n     */\n'
            '    public static long combine(final long[] words, final long initial, final int at, final int width, final long field) {\n'
            '        long total = initial;\n        for (int i = 0; i < words.length; i++) {\n            total = NumberUtils.overlay(total, words[i], i, at, width, field);\n        }\n        return total;\n    }\n\n')
    insert_before(OU, '    // cloning\n    //-----------------------------------------------------------------------\n', hop4)
    edit(OU, [("import org.apache.commons.lang3.exception.CloneFailedException;\n", "import org.apache.commons.lang3.exception.CloneFailedException;\nimport org.apache.commons.lang3.math.NumberUtils;\n")])
    # hop 5 (gold): NumberUtils.overlay — places one value; the BUGGY line; anchored after max(float,float,float)
    hop5 = ('\n    /**\n     * <p>Overlays a value onto a holder at the position given by its index.</p>\n     *\n'
            '     * @param holder  the value to overlay onto\n     * @param word  the value to place\n     * @param index  the index of the value within its run\n'
            '     * @param at  the position in the holder at which the first value of the run is placed\n     * @param width  the width of a value\n'
            '     * @param field  the field covering one value\n     * @return the holder with the value placed\n     */\n'
            '    public static long overlay(final long holder, final long word, final int index, final int at, final int width, final long field) {\n'
            '        final int shift = (index + at) * width;\n        return (holder & ~(field << shift)) | (word << shift);\n    }\n')
    insert_after(NU, '    public static float max(final float a, final float b, final float c) {\n        return Math.max(Math.max(a, b), c);\n    }\n', hop5)
    files = [f"src/main/java/org/apache/commons/lang3/{x}" for x in ("ArrayUtils.java", "BitField.java", "Conversion.java", "EnumUtils.java", "ObjectUtils.java", "builder/Folding.java", "builder/StandardFolding.java", "math/NumberUtils.java")]
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/lang3/ConversionTest.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16])
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
