"""Deterministic construction of HA-LOW-01 / HA-HIGH-01 on a fresh Lang-1f checkout. No LLM. Usage: build_ha.py <low|high> <work_checkout>
Exact, asserted string edits; patches captured with git diff. NON-CANONICAL / HYPOTHESIS-AMBIGUITY EXPERIMENT / GPT-5.6."""
import os, subprocess, sys, hashlib
R = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/hypothesis-ambiguity-v1"
arm, work = sys.argv[1], sys.argv[2]; assert arm in ("low", "high"); VID = "HA-LOW-01" if arm == "low" else "HA-HIGH-01"; pkg = os.path.join(R, "packages", VID)
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, t): open(p, "w", encoding="utf-8").write(t)
def edit(path, old, new):
    t = rd(path); assert t.count(old) == 1, f"{os.path.basename(path)}: expected one match for {old[:60]!r}, got {t.count(old)}"; wr(path, t.replace(old, new, 1))
def insert_after(path, anchor, block):
    t = rd(path); assert t.count(anchor) == 1, f"{os.path.basename(path)}: anchor not unique ({t.count(anchor)})"; wr(path, t.replace(anchor, anchor + block, 1))
def absent(path, *names):
    t = rd(path)
    for n in names: assert (n + "(") not in t, f"{os.path.basename(path)} already declares {n}"
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
J = lambda *p: os.path.join(work, "src/main/java/org/apache/commons/lang3", *p)
CONV, AU, BF, NU = J("Conversion.java"), J("ArrayUtils.java"), J("BitField.java"), J("math", "NumberUtils.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/lang3/ConversionTest.java")
absent(AU, "pack", "advance", "gather"); absent(BF, "lane", "offset", "widen"); absent(NU, "deposit", "merge")
# ---- trigger (identical in both arms) ----
test_src = ('\n    @Test\n    public void testLang1140() {\n        final int[] src = new int[]{0x1CDF1F0C, 0x00123456, 0x78000000};\n'
            '        assertEquals(0x0000000012345600L, Conversion.intArrayToLong(src, 1, 0L, 8, 1));\n'
            '        assertEquals(0x0012345600000000L, Conversion.intArrayToLong(src, 1, 0L, 32, 1));\n    }\n}\n')
t = rd(TEST); assert t.endswith("    }\n}\n"); wr(TEST, t[:-2] + test_src)
# ---- facade: keep both guards, delegate the loop (identical in both arms) ----
LOOP = ('        long out = dstInit;\n        int shift = 0;\n        for (int i = 0; i < nInts; i++ ) {\n            shift = i * 32 + dstPos;\n'
        '            final long bits = ((0xffffffffL & src[i + srcPos]) << shift);\n            final long mask = 0xffffffffL << shift;\n            out = (out & ~mask) | bits;\n        }\n        return out;\n    }\n')
edit(CONV, LOOP, "        return ArrayUtils.pack(src, srcPos, nInts, dstInit, dstPos);\n    }\n")
# ---- gold (identical in both arms): BitField.lane, appended after setByteBoolean ----
BF_ANCHOR = '    public byte setByteBoolean(final byte holder, final boolean flag) {\n        return flag ? setByte(holder) : clearByte(holder);\n    }\n'
lane = ('\n    /**\n     * <p>Returns the lane of a position. Positions are counted in bits and grouped\n     * into lanes of {@link Integer#SIZE} bits.</p>\n     *\n'
        '     * @param at  the position, in bits\n     * @return the lane for {@code at}\n     */\n'
        '    public static int lane(final int at) {\n        return (at + Integer.SIZE - 1) / Integer.SIZE;\n    }\n')
if arm == "high":
    helper_bf = ('\n    /**\n     * <p>Returns the offset of a position inside its lane.</p>\n     *\n'
                 '     * @param at  the position, in bits\n     * @return the offset of {@code at} inside its lane\n     */\n'
                 '    public static int offset(final int at) {\n        return at % Integer.SIZE;\n    }\n')
    pack = ('\n    /**\n     * <p>Packs a run of elements of an {@code int} array into a {@code long}.</p>\n     *\n'
            '     * @param array  the array to pack from\n     * @param startIndex  the index of the first element to pack\n'
            '     * @param count  the number of elements to pack\n     * @param initial  the starting value of the result\n'
            '     * @param at  the position in the result at which the first element is placed\n     * @return the packed value\n     * @since 3.2\n     */\n'
            '    public static long pack(final int[] array, final int startIndex, final int count, final long initial, final int at) {\n'
            '        final int lane = BitField.lane(at);\n        final int offset = BitField.offset(at);\n        long out = initial;\n'
            '        for (int index = 0; index < count; index++) {\n            out = NumberUtils.deposit(out, array[startIndex + index], advance(lane, index), offset);\n        }\n        return out;\n    }\n'
            '\n    /**\n     * <p>Returns the lane of the element with the given index in a run that starts at the given lane.</p>\n     *\n'
            '     * @param lane  the lane of the first element of the run\n     * @param index  the index of the element within the run\n'
            '     * @return the lane of the element\n     * @since 3.2\n     */\n'
            '    public static int advance(final int lane, final int index) {\n        return lane + index;\n    }\n')
    helper_nu = ('\n    /**\n     * <p>Deposits a value into a holder at the given lane and offset.</p>\n     *\n'
                 '     * @param holder  the value to deposit into\n     * @param value  the value to deposit\n     * @param lane  the lane of the value\n'
                 '     * @param offset  the offset of the value inside its lane\n     * @return the holder with the value deposited\n     */\n'
                 '    public static long deposit(final long holder, final int value, final int lane, final int offset) {\n'
                 '        final int shift = lane * Integer.SIZE + offset;\n        final long field = 0xffffffffL << shift;\n'
                 '        return (holder & ~field) | ((0xffffffffL & value) << shift);\n    }\n')
else:
    helper_bf = ('\n    /**\n     * <p>Widens an {@code int} value to a {@code long}, keeping its low 32 bits.</p>\n     *\n'
                 '     * @param value  the value to widen\n     * @return the widened value\n     */\n'
                 '    public static long widen(final int value) {\n        return 0xffffffffL & value;\n    }\n')
    pack = ('\n    /**\n     * <p>Packs a run of elements of an {@code int} array into a {@code long}.</p>\n     *\n'
            '     * @param array  the array to pack from\n     * @param startIndex  the index of the first element to pack\n'
            '     * @param count  the number of elements to pack\n     * @param initial  the starting value of the result\n'
            '     * @param at  the position in the result at which the first element is placed\n     * @return the packed value\n     * @since 3.2\n     */\n'
            '    public static long pack(final int[] array, final int startIndex, final int count, final long initial, final int at) {\n'
            '        final int[] run = gather(array, startIndex, count);\n        final int lane = BitField.lane(at);\n        final int offset = at % Integer.SIZE;\n        long out = initial;\n'
            '        for (int index = 0; index < count; index++) {\n            final int shift = (lane + index) * Integer.SIZE + offset;\n'
            '            out = NumberUtils.merge(out, BitField.widen(run[index]), shift);\n        }\n        return out;\n    }\n'
            '\n    /**\n     * <p>Gathers a run of elements of an {@code int} array into a new array.</p>\n     *\n'
            '     * @param array  the array to gather from\n     * @param startIndex  the index of the first element to gather\n'
            '     * @param count  the number of elements to gather\n     * @return the gathered run\n     * @since 3.2\n     */\n'
            '    public static int[] gather(final int[] array, final int startIndex, final int count) {\n'
            '        final int[] run = new int[count];\n        System.arraycopy(array, startIndex, run, 0, count);\n        return run;\n    }\n')
    helper_nu = ('\n    /**\n     * <p>Merges a value into a holder at the given shift.</p>\n     *\n'
                 '     * @param holder  the value to merge into\n     * @param value  the value to merge\n     * @param shift  the shift at which the value is merged\n'
                 '     * @return the holder with the value merged\n     */\n'
                 '    public static long merge(final long holder, final long value, final int shift) {\n'
                 '        final long field = 0xffffffffL << shift;\n        return (holder & ~field) | (value << shift);\n    }\n')
insert_after(BF, BF_ANCHOR, lane + helper_bf)
# ArrayUtils: pack (+ advance | gather) after subarray(int[]); import of math.NumberUtils next to the other lang3 sub-package imports
AU_ANCHOR = '        final int[] subarray = new int[newSize];\n        System.arraycopy(array, startIndexInclusive, subarray, 0, newSize);\n        return subarray;\n    }\n'
t = rd(AU); i = t.find("public static int[] subarray(final int[] array"); j = t.find(AU_ANCHOR, i); assert i > 0 and j > 0; wr(AU, t[:j + len(AU_ANCHOR)] + pack + t[j + len(AU_ANCHOR):])
edit(AU, "import org.apache.commons.lang3.builder.ToStringStyle;\nimport org.apache.commons.lang3.mutable.MutableInt;\n", "import org.apache.commons.lang3.builder.ToStringStyle;\nimport org.apache.commons.lang3.math.NumberUtils;\nimport org.apache.commons.lang3.mutable.MutableInt;\n")
insert_after(NU, '    public static float max(final float a, final float b, final float c) {\n        return Math.max(Math.max(a, b), c);\n    }\n', helper_nu)
files = ["src/main/java/org/apache/commons/lang3/" + x for x in ("ArrayUtils.java", "BitField.java", "Conversion.java", "math/NumberUtils.java")]
os.makedirs(pkg, exist_ok=True)
wr(os.path.join(pkg, "variant.patch"), run(["git", "diff", "--"] + files)); wr(os.path.join(pkg, "test.patch"), run(["git", "diff", "--", "src/test/java/org/apache/commons/lang3/ConversionTest.java"]))
for f in ("variant.patch", "test.patch"): print(VID, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(VID, "built:", run(["git", "status", "--short"]).replace("\n", " "))
