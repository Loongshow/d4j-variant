"""Deterministic construction of JKC-OFFSET-CONTROL-05 / JKC-OFFSET-TREATMENT-05 on a fresh JacksonCore-1f checkout. No LLM.
Usage: build_jacksoncore_bug05.py <control|treatment> <work> <pkg>. NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
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
PB, IC, MS, IN, SS, RC = J("base/ParserBase.java"), J("io/IOContext.java"), J("io/MergedStream.java"), J("util/InternCache.java"), J("io/SerializedString.java"), J("json/JsonReadContext.java")
TEST = os.path.join(work, "src/test/java/com/fasterxml/jackson/core/json/TestJsonParser.java")
test_src = ('\n    // [JACKSON-488]\n    public void testJackson488() throws Exception\n    {\n'
            '        JsonFactory f = new JsonFactory();\n        JsonParser jp = f.createJsonParser("{\\"a\\":1,\\"bb\\":true}");\n\n'
            '        assertToken(JsonToken.START_OBJECT, jp.nextToken());\n'
            '        assertEquals(0L, jp.getTokenLocation().getCharOffset());\n'
            '        assertEquals(0L, jp.getCurrentLocation().getCharOffset());\n\n'
            '        assertToken(JsonToken.FIELD_NAME, jp.nextToken());\n        assertEquals("a", jp.getCurrentName());\n'
            '        assertEquals(5L, jp.getCurrentLocation().getCharOffset());\n\n'
            '        assertToken(JsonToken.VALUE_NUMBER_INT, jp.nextToken());\n'
            '        assertToken(JsonToken.FIELD_NAME, jp.nextToken());\n        assertEquals(15L, jp.getCurrentLocation().getCharOffset());\n\n'
            '        assertToken(JsonToken.VALUE_TRUE, jp.nextToken());\n'
            '        assertToken(JsonToken.END_OBJECT, jp.nextToken());\n        assertEquals(16L, jp.getCurrentLocation().getCharOffset());\n'
            '        jp.close();\n    }\n')
t = rd(TEST); k = t.rstrip().rfind("}"); assert t[k:].strip() == "}"
wr(TEST, t[:k].rstrip("\n") + "\n" + test_src + "}" + ("\n" if t.endswith("\n") else ""))
ORIG = "                                _currInputProcessed + _inputPtr - 1,"
BUG = "                                _currInputProcessed + _inputPtr,"
if arm == "control":
    edit(PB, ORIG, BUG); files = [B + "base/ParserBase.java"]
else:
    edit(PB, ("        int col = _inputPtr - _currInputRowStart + 1; // 1-based\n        return new JsonLocation(_ioContext.getSourceReference(),\n"
              "                                _currInputProcessed + _inputPtr - 1,\n                                _currInputRow, col);"),
             ("        int col = _inputPtr - _currInputRowStart + 1; // 1-based\n        final long charOffset = IOContext.charOffset(_currInputProcessed, _inputPtr);\n"
              "        return new JsonLocation(_ioContext.getSourceReference(),\n                                charOffset,\n                                _currInputRow, col);"))
    append_before_class_end(IC, '\n    /**\n     * Returns the offset of the last processed character of the input, given the\n     * number of characters of earlier buffers and the pointer into the current one.\n     *\n     * @param processed number of characters processed before the current buffer\n     * @param ptr pointer into the current buffer\n     * @return the offset of the last processed character\n     */\n'
        '    public static long charOffset(final long processed, final int ptr) {\n        final long consumed = processed + ptr;\n        final long offset = MergedStream.streamOffset(consumed);\n        return offset;\n    }\n')
    append_before_class_end(MS, '\n    /**\n     * Returns the offset of the last processed character for a number of consumed\n     * characters, or -1 when the amount consumed is not known.\n     *\n     * @param consumed number of characters consumed from the input\n     * @return the offset of the last processed character\n     */\n'
        '    public static long streamOffset(final long consumed) {\n        if (consumed < 0L) {\n            return -1L;\n        }\n        return InternCache.zeroBased(consumed);\n    }\n')
    edit(MS, "package com.fasterxml.jackson.core.io;", "package com.fasterxml.jackson.core.io;\n\nimport com.fasterxml.jackson.core.util.InternCache;")
    append_before_class_end(IN, '\n    /**\n     * Returns the offset of the last processed character relative to the start of\n     * the input.\n     *\n     * @param consumed number of characters consumed from the input\n     * @return the offset of the last processed character\n     */\n'
        '    public static long zeroBased(final long consumed) {\n        final int origin = 0;\n        final long position = SerializedString.positionOf(consumed, origin);\n        return position;\n    }\n')
    edit(IN, "package com.fasterxml.jackson.core.util;", "package com.fasterxml.jackson.core.util;\n\nimport com.fasterxml.jackson.core.io.SerializedString;")
    append_before_class_end(SS, '\n    /**\n     * Returns the offset of the last processed character relative to the given\n     * origin of the input.\n     *\n     * @param consumed number of characters consumed from the input\n     * @param origin offset the input starts at\n     * @return the offset of the last processed character\n     */\n'
        '    public static long positionOf(final long consumed, final int origin) {\n        final long relative = consumed - origin;\n        final long position = JsonReadContext.lastProcessed(relative);\n        return position;\n    }\n')
    edit(SS, "package com.fasterxml.jackson.core.io;", "package com.fasterxml.jackson.core.io;\n\nimport com.fasterxml.jackson.core.json.JsonReadContext;")
    append_before_class_end(RC, '\n    /**\n     * Returns the position of the last processed character of the input for the\n     * position the input is about to read next.\n     *\n     * @param nextPosition position the input reads next\n     * @return position of the last processed character\n     */\n'
        '    public static long lastProcessed(final long nextPosition) {\n        final int back = 1;\n        return nextPosition - back;\n    }\n')
    files = [B + x for x in ("base/ParserBase.java", "io/IOContext.java", "io/MergedStream.java", "util/InternCache.java", "io/SerializedString.java", "json/JsonReadContext.java")]
    edit(RC, "        final int back = 1;", "        final int back = 0;")
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/com/fasterxml/jackson/core/json/TestJsonParser.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " ")[:250])
