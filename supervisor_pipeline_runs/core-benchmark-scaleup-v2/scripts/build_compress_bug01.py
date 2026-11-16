"""Deterministic construction of CMP-CKSUM-CONTROL-01 / CMP-CKSUM-TREATMENT-01 on a fresh Compress-1f checkout. No LLM.
Usage: build_compress_bug01.py <control|treatment> <work_checkout> <package_dir>. Exact asserted string edits; patches emitted with git diff.
NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
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
B = "src/main/java/org/apache/commons/compress/"; J = lambda *p: os.path.join(work, B, *p)
TU, TB, IO, ZL, EF, AS = J("archivers/tar/TarUtils.java"), J("archivers/tar/TarBuffer.java"), J("utils/IOUtils.java"), J("archivers/zip/ZipLong.java"), J("archivers/zip/ExtraFieldUtils.java"), J("archivers/zip/AsiExtraField.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/compress/archivers/tar/TarArchiveEntryTest.java")
# ---- trigger (identical in both arms) ----
test_src = ('\n    /**\n     * JIRA issue COMPRESS-194\n     *\n     * @see "https://issues.apache.org/jira/browse/COMPRESS-194"\n     */\n'
            '    public void testCompress194() {\n'
            '        final byte[] asciiHeader = new byte[] { \'u\', \'s\', \'t\', \'a\', \'r\', \' \', \' \', 0 };\n'
            '        assertEquals(623L, TarUtils.computeCheckSum(asciiHeader));\n\n'
            '        final byte[] utf8Header = new byte[] { (byte) 0xC3, (byte) 0xA9, \'a\', 0 };\n'
            '        assertEquals(461L, TarUtils.computeCheckSum(utf8Header));\n\n'
            '        final byte[] mixedHeader = new byte[] { \'t\', \'a\', \'r\', (byte) 0x80, (byte) 0xFF, (byte) 0x7F, \'/\', 0 };\n'
            '        assertEquals(884L, TarUtils.computeCheckSum(mixedHeader));\n'
            '    }\n')
t = rd(TEST); k = t.rstrip().rfind("}"); assert t[k:].strip() == "}"
wr(TEST, t[:k].rstrip("\n") + "\n" + test_src + "}" + ("\n" if t.endswith("\n") else ""))
ORIG, BUG = "            sum += BYTE_MASK & buf[i];", "            sum += buf[i];"
if arm == "control":
    edit(TU, ORIG, BUG); files = [B + "archivers/tar/TarUtils.java"]
else:
    # facade: delegate the accumulation to the chain (javadoc untouched)
    edit(TU, ("    public static long computeCheckSum(byte[] buf) {\n        long sum = 0;\n\n        for (int i = 0; i < buf.length; ++i) {\n"
              "            sum += BYTE_MASK & buf[i];\n        }\n\n        return sum;\n    }"),
             ("    public static long computeCheckSum(byte[] buf) {\n        return TarBuffer.tally(buf, 0, buf.length);\n    }"))
    # H1: range segmentation into two-byte strides
    edit(TB, "import java.io.InputStream;", "import java.io.InputStream;\nimport org.apache.commons.compress.utils.IOUtils;")
    append_before_class_end(TB, '\n    /**\n     * Accumulates the checksum of a byte range of a header record, taking the\n     * bytes two at a time.\n     *\n     * @param buf the header bytes\n     * @param offset the first index of the range\n     * @param length the number of bytes in the range\n     * @return the accumulated checksum of the range\n     */\n'
        '    public static long tally(final byte[] buf, final int offset, final int length) {\n        long sum = 0;\n        final int end = offset + length;\n        for (int i = offset; i < end; i += 2) {\n            final int available = end - i;\n            sum += IOUtils.sumPair(buf, i, available);\n        }\n        return sum;\n    }\n')
    # H2: pair accumulation (handles the odd tail)
    edit(IO, "import java.io.IOException;", "import java.io.IOException;\nimport org.apache.commons.compress.archivers.zip.ZipLong;")
    append_before_class_end(IO, '\n    /**\n     * Adds up the two byte values starting at the given index; the second byte\n     * is only added when the range still holds one.\n     *\n     * @param buf the bytes to read\n     * @param index the index of the first byte\n     * @param available the number of bytes left in the range\n     * @return the sum of the byte values of the pair\n     */\n'
        '    public static long sumPair(final byte[] buf, final int index, final int available) {\n        long sum = ZipLong.byteValue(buf, index);\n        if (available > 1) {\n            sum += ZipLong.byteValue(buf, index + 1);\n        }\n        return sum;\n    }\n')
    # H3: element access with bounds validation
    append_before_class_end(ZL, '\n    /**\n     * Returns the numeric value of a single byte of a record.\n     *\n     * @param buf the bytes of the record\n     * @param index the index of the byte\n     * @return the value of the byte\n     */\n'
        '    public static long byteValue(final byte[] buf, final int index) {\n        if (index < 0 || index >= buf.length) {\n            throw new IllegalArgumentException("index out of range: " + index);\n        }\n        return ExtraFieldUtils.widen(buf[index]);\n    }\n')
    # H4: widening of the magnitude to the accumulator type
    append_before_class_end(EF, '\n    /**\n     * Widens the magnitude of a single record byte to the type used by the\n     * checksum accumulator.\n     *\n     * @param raw the byte of the record\n     * @return the widened magnitude of the byte\n     */\n'
        '    public static long widen(final byte raw) {\n        final int magnitude = AsiExtraField.magnitudeOf(raw);\n        final long widened = magnitude;\n        return widened;\n    }\n')
    # H5 (gold): magnitude of a record byte; the BUGGY line lives here
    body = "        final int magnitude = raw & 0xFF;" if True else ""
    append_before_class_end(AS, '\n    /**\n     * Returns the magnitude of a single byte of a record, that is the value it\n     * contributes to a sum over the record.\n     *\n     * @param raw the byte of the record\n     * @return the magnitude of the byte\n     */\n'
        '    public static int magnitudeOf(final byte raw) {\n' + body + '\n        return magnitude;\n    }\n')
    files = [B + x for x in ("archivers/tar/TarUtils.java", "archivers/tar/TarBuffer.java", "utils/IOUtils.java", "archivers/zip/ZipLong.java", "archivers/zip/ExtraFieldUtils.java", "archivers/zip/AsiExtraField.java")]
    edit(AS, "        final int magnitude = raw & 0xFF;", "        final int magnitude = raw;")
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/compress/archivers/tar/TarArchiveEntryTest.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
