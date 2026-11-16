"""Deterministic construction of CMP-ALIGN-CONTROL-06 / CMP-ALIGN-TREATMENT-06 on a fresh Compress-1f checkout. No LLM.
Usage: build_compress_bug06.py <control|treatment> <work> <pkg>. NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
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
AO, ZO, JO, TI, ZE, CO = J("archivers/ar/ArArchiveOutputStream.java"), J("archivers/zip/ZipArchiveOutputStream.java"), J("archivers/jar/JarArchiveOutputStream.java"), J("archivers/tar/TarArchiveInputStream.java"), J("archivers/zip/ZipArchiveEntry.java"), J("archivers/cpio/CpioArchiveOutputStream.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/compress/archivers/ArTestCase.java")
test_src = ('\n    /**\n     * JIRA issue COMPRESS-145\n     *\n     * @see "https://issues.apache.org/jira/browse/COMPRESS-145"\n     */\n'
            '    public void testCompress145() throws Exception {\n'
            '        final java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();\n'
            '        final org.apache.commons.compress.archivers.ar.ArArchiveOutputStream os =\n            new org.apache.commons.compress.archivers.ar.ArArchiveOutputStream(bos);\n'
            '        os.putArchiveEntry(new org.apache.commons.compress.archivers.ar.ArArchiveEntry("odd.txt", 3));\n'
            '        os.write(new byte[] { \'a\', \'b\', \'c\' });\n'
            '        os.putArchiveEntry(new org.apache.commons.compress.archivers.ar.ArArchiveEntry("even.txt", 2));\n'
            '        os.write(new byte[] { \'d\', \'e\' });\n        os.closeArchiveEntry();\n        os.close();\n\n'
            '        final byte[] archive = bos.toByteArray();\n'
            '        assertEquals(\'!\', (char) archive[0]);\n'
            '        assertEquals(\'c\', (char) archive[70]);\n'
            '        assertEquals(10, archive[71] & 0xFF);\n'
            '        assertEquals(\'e\', (char) archive[72]);\n'
            '    }\n')
t = rd(TEST); k = t.rstrip().rfind("}"); assert t[k:].strip() == "}"
wr(TEST, t[:k].rstrip("\n") + "\n" + test_src + "}" + ("\n" if t.endswith("\n") else ""))
ORIG, BUG = "        if ((entryOffset % 2) != 0) {", "        if ((entryOffset % 2) == 0) {"
if arm == "control":
    edit(AO, ORIG, BUG); files = [B + "archivers/ar/ArArchiveOutputStream.java"]
else:
    edit(AO, ("    public void closeArchiveEntry() throws IOException {\n        if ((entryOffset % 2) != 0) {\n            out.write('\\n');\n            archiveOffset++;\n        }\n    }"),
             ("    public void closeArchiveEntry() throws IOException {\n        final int pad = ZipArchiveOutputStream.memberEnd(entryOffset);\n"
              "        for (int i = 0; i < pad; i++) {\n            out.write('\\n');\n            archiveOffset++;\n        }\n    }"))
    edit(AO, "import java.io.IOException;", "import java.io.IOException;\nimport org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream;")
    append_before_class_end(ZO, '\n    /**\n     * Returns the number of pad bytes that must follow a member of the given\n     * length so that the next header starts at an aligned offset.\n     *\n     * @param memberLength number of bytes written for the member\n     * @return the number of pad bytes to write\n     */\n'
        '    public static int memberEnd(final long memberLength) {\n        if (memberLength < 0) {\n            throw new IllegalArgumentException(\"negative member length: \" + memberLength);\n        }\n        return JarArchiveOutputStream.alignmentBoundary(memberLength);\n    }\n')
    edit(ZO, "package org.apache.commons.compress.archivers.zip;", "package org.apache.commons.compress.archivers.zip;\n\nimport org.apache.commons.compress.archivers.jar.JarArchiveOutputStream;")
    append_before_class_end(JO, '\n    /**\n     * Returns the number of pad bytes needed at the given offset for the\n     * alignment the format requires.\n     *\n     * @param end offset the member ends at\n     * @return the number of pad bytes to write\n     */\n'
        '    public static int alignmentBoundary(final long end) {\n        final int boundary = 2;\n        final int count = TarArchiveInputStream.remainder(end, boundary);\n        return count;\n    }\n')
    edit(JO, "package org.apache.commons.compress.archivers.jar;", "package org.apache.commons.compress.archivers.jar;\n\nimport org.apache.commons.compress.archivers.tar.TarArchiveInputStream;")
    append_before_class_end(TI, '\n    /**\n     * Returns the number of pad bytes needed at the given offset, from how far\n     * the offset lies past the last alignment boundary.\n     *\n     * @param end offset the member ends at\n     * @param boundary the alignment the format requires\n     * @return the number of pad bytes to write\n     */\n'
        '    public static int remainder(final long end, final int boundary) {\n        final long remainder = end % boundary;\n        final int count = ZipArchiveEntry.padCount(remainder, boundary);\n        return count;\n    }\n')
    edit(TI, "package org.apache.commons.compress.archivers.tar;", "package org.apache.commons.compress.archivers.tar;\n\nimport org.apache.commons.compress.archivers.zip.ZipArchiveEntry;")
    append_before_class_end(ZE, '\n    /**\n     * Returns the number of pad bytes needed for the given distance past the last\n     * alignment boundary.\n     *\n     * @param remainder distance past the last alignment boundary\n     * @param boundary the alignment the format requires\n     * @return the number of pad bytes to write\n     */\n'
        '    public static int padCount(final long remainder, final int boundary) {\n        if (boundary != 2) {\n            throw new IllegalArgumentException("unsupported alignment boundary: " + boundary);\n        }\n        return CpioArchiveOutputStream.padNeeded(remainder);\n    }\n')
    edit(ZE, "package org.apache.commons.compress.archivers.zip;", "package org.apache.commons.compress.archivers.zip;\n\nimport org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStream;")
    append_before_class_end(CO, '\n    /**\n     * Returns the number of pad bytes needed for a member that ends the given\n     * distance past the last alignment boundary of a two-byte aligned format.\n     *\n     * @param remainder distance past the last alignment boundary\n     * @return the number of pad bytes to write\n     */\n'
        '    public static int padNeeded(final long remainder) {\n        final boolean unaligned = remainder != 0;\n        return unaligned ? 1 : 0;\n    }\n')
    files = [B + x for x in ("archivers/ar/ArArchiveOutputStream.java", "archivers/zip/ZipArchiveOutputStream.java", "archivers/jar/JarArchiveOutputStream.java", "archivers/tar/TarArchiveInputStream.java", "archivers/zip/ZipArchiveEntry.java", "archivers/cpio/CpioArchiveOutputStream.java")]
    edit(CO, "        final boolean unaligned = remainder != 0;", "        final boolean unaligned = remainder == 0;")
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/compress/archivers/ArTestCase.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " ")[:250])
