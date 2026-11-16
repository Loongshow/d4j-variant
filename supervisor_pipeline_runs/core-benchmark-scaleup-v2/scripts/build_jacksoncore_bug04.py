"""Deterministic construction of JKC-SURR-CONTROL-04 / JKC-SURR-TREATMENT-04 on a fresh JacksonCore-1f checkout. No LLM.
Usage: build_jacksoncore_bug04.py <control|treatment> <work> <pkg>. NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
import os, subprocess, sys, hashlib
arm, work, pkg = sys.argv[1], sys.argv[2], sys.argv[3]
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, t): open(p, "w", encoding="utf-8").write(t)
def edit(path, old, new):
    t = rd(path); assert t.count(old) == 1, f"{os.path.basename(path)}: {t.count(old)} matches for {old[:60]!r}"; wr(path, t.replace(old, new, 1))
def append_before_class_end(path, block):
    t = rd(path); k = t.rstrip().rfind("}"); assert t[k:].strip() == "}"
    wr(path, t[:k].rstrip("\n") + "\n" + block + "}" + ("\n" if t.endswith("\n") else ""))
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
B = "src/main/java/com/fasterxml/jackson/core/"; J = lambda *p: os.path.join(work, B, *p)
UW, CT, NI, NO, JE, TB = J("io/UTF8Writer.java"), J("io/CharTypes.java"), J("io/NumberInput.java"), J("io/NumberOutput.java"), J("io/JsonStringEncoder.java"), J("util/TextBuffer.java")
TEST = os.path.join(work, "src/test/java/com/fasterxml/jackson/core/io/TestUTF8Writer.java")
test_src = ('\n    // [JACKSON-417]\n    public void testJackson417() throws Exception\n    {\n'
            '        BufferRecycler rec = new BufferRecycler();\n        IOContext ctxt = new IOContext(rec, null, false);\n'
            '        ByteArrayOutputStream out = new ByteArrayOutputStream();\n        UTF8Writer w = new UTF8Writer(ctxt, out);\n'
            '        w.write("a\\u00e9\\uD83D\\uDE00");\n        w.close();\n\n'
            '        byte[] b = out.toByteArray();\n        assertEquals(7, b.length);\n'
            '        assertEquals(0x61, b[0] & 0xFF);\n        assertEquals(0xC3, b[1] & 0xFF);\n        assertEquals(0xA9, b[2] & 0xFF);\n'
            '        assertEquals(0xF0, b[3] & 0xFF);\n        assertEquals(0x9F, b[4] & 0xFF);\n        assertEquals(0x98, b[5] & 0xFF);\n        assertEquals(0x80, b[6] & 0xFF);\n'
            '    }\n')
t = rd(TEST); k = t.rstrip().rfind("}"); assert t[k:].strip() == "}"
wr(TEST, t[:k].rstrip("\n") + "\n" + test_src + "}" + ("\n" if t.endswith("\n") else ""))
ORIG = "        return 0x10000 + ((firstPart - SURR1_FIRST) << 10) + (secondPart - SURR2_FIRST);"
BUG = "        return 0x10000 + ((firstPart - SURR1_FIRST) << 11) + (secondPart - SURR2_FIRST);"
if arm == "control":
    edit(UW, ORIG, BUG); files = [B + "io/UTF8Writer.java"]
else:
    edit(UW, ORIG, "        return CharTypes.codePointOf(firstPart, secondPart);")
    append_before_class_end(CT, '\n    /**\n     * Returns the code point that a surrogate pair stands for.\n     *\n     * @param hi the first (high) surrogate\n     * @param lo the second (low) surrogate\n     * @return the code point of the pair\n     */\n'
        '    public static int codePointOf(final int hi, final int lo) {\n        final int hiOffset = hi - 0xD800;\n        final int loOffset = lo - 0xDC00;\n        return NumberInput.plane(hiOffset, loOffset);\n    }\n')
    append_before_class_end(NI, '\n    /**\n     * Returns the code point of a surrogate pair, which lies above the basic\n     * multilingual plane.\n     *\n     * @param hiOffset offset of the high surrogate within its block\n     * @param loOffset offset of the low surrogate within its block\n     * @return the code point of the pair\n     */\n'
        '    public static int plane(final int hiOffset, final int loOffset) {\n        final int base = 0x10000;\n        final int combined = NumberOutput.assemble(base, hiOffset, loOffset);\n        return combined;\n    }\n')
    append_before_class_end(NO, '\n    /**\n     * Combines the contributions of the two surrogates of a pair with the base\n     * of the supplementary planes.\n     *\n     * @param base first code point above the basic multilingual plane\n     * @param hiOffset offset of the high surrogate within its block\n     * @param loOffset offset of the low surrogate within its block\n     * @return the code point of the pair\n     */\n'
        '    public static int assemble(final int base, final int hiOffset, final int loOffset) {\n        final int high = JsonStringEncoder.weight(hiOffset);\n        final int combined = base + high + loOffset;\n        return combined;\n    }\n')
    append_before_class_end(JE, '\n    /**\n     * Returns the contribution of the high surrogate of a pair to the code point.\n     *\n     * @param hiOffset offset of the high surrogate within its block\n     * @return the contribution of the high surrogate\n     */\n'
        '    public static int weight(final int hiOffset) {\n        if (hiOffset < 0 || hiOffset > 0x3FF) {\n            throw new IllegalArgumentException("surrogate offset out of range: " + hiOffset);\n        }\n        return TextBuffer.highSurrogateWeight(hiOffset);\n    }\n')
    edit(JE, "package com.fasterxml.jackson.core.io;", "package com.fasterxml.jackson.core.io;\n\nimport com.fasterxml.jackson.core.util.TextBuffer;")
    append_before_class_end(TB, '\n    /**\n     * Returns the contribution of the high surrogate of a pair to the code point,\n     * that is its offset shifted by the number of bits the low surrogate holds.\n     *\n     * @param hiOffset offset of the high surrogate within its block\n     * @return the contribution of the high surrogate\n     */\n'
        '    public static int highSurrogateWeight(final int hiOffset) {\n        final int bits = 10;\n        return hiOffset << bits;\n    }\n')
    files = [B + x for x in ("io/UTF8Writer.java", "io/CharTypes.java", "io/NumberInput.java", "io/NumberOutput.java", "io/JsonStringEncoder.java", "util/TextBuffer.java")]
    edit(TB, "        final int bits = 10;", "        final int bits = 11;")
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/com/fasterxml/jackson/core/io/TestUTF8Writer.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " ")[:250])
