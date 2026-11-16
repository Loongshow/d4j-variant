"""Deterministic construction of CMP-OCTAL-CONTROL-03 / CMP-OCTAL-TREATMENT-03 on a fresh Compress-1f checkout. No LLM.
Usage: build_compress_bug03.py <control|treatment> <work> <pkg>. NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
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
TU, ZS, JM, UP, UE, TO = J("archivers/tar/TarUtils.java"), J("archivers/zip/ZipShort.java"), J("archivers/zip/JarMarker.java"), J("archivers/zip/UnicodePathExtraField.java"), J("archivers/zip/UnrecognizedExtraField.java"), J("archivers/tar/TarArchiveOutputStream.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/compress/archivers/tar/TarArchiveEntryTest.java")
test_src = ('\n    /**\n     * JIRA issue COMPRESS-130\n     *\n     * @see "https://issues.apache.org/jira/browse/COMPRESS-130"\n     */\n'
            '    public void testCompress130() {\n'
            '        final byte[] small = new byte[8];\n        TarUtils.getOctalBytes(7L, small, 0, 8);\n'
            '        assertEquals(7L, TarUtils.parseOctal(small, 0, 8));\n\n'
            '        final byte[] mode = new byte[8];\n        TarUtils.getOctalBytes(493L, mode, 0, 8);\n'
            '        assertEquals(493L, TarUtils.parseOctal(mode, 0, 8));\n'
            '        assertEquals(\'7\', (char) mode[3]);\n        assertEquals(\'5\', (char) mode[4]);\n        assertEquals(\'5\', (char) mode[5]);\n'
            '    }\n')
t = rd(TEST); k = t.rstrip().rfind("}"); assert t[k:].strip() == "}"
wr(TEST, t[:k].rstrip("\n") + "\n" + test_src + "}" + ("\n" if t.endswith("\n") else ""))
ORIG = "                buf[offset + idx] = (byte) ((byte) '0' + (byte) (val & 7));"
BUG = "                buf[offset + idx] = (byte) ((byte) '0' + (byte) (val & 15));"
if arm == "control":
    edit(TU, ORIG, BUG); files = [B + "archivers/tar/TarUtils.java"]
else:
    edit(TU, ORIG, "                buf[offset + idx] = ZipShort.digitOf(val);")
    edit(TU, "package org.apache.commons.compress.archivers.tar;", "package org.apache.commons.compress.archivers.tar;\n\nimport org.apache.commons.compress.archivers.zip.ZipShort;")
    append_before_class_end(ZS, '\n    /**\n     * Returns the character that represents the lowest digit of a numeric field\n     * value.\n     *\n     * @param val the remaining field value\n     * @return the digit character\n     */\n'
        '    public static byte digitOf(final long val) {\n        final int digit = JarMarker.digitValue(val);\n        final byte encoded = (byte) ((byte) \'0\' + (byte) digit);\n        return encoded;\n    }\n')
    append_before_class_end(JM, '\n    /**\n     * Returns the lowest digit of a numeric field value, independent of its sign.\n     *\n     * @param val the remaining field value\n     * @return the value of the lowest digit\n     */\n'
        '    public static int digitValue(final long val) {\n        final int sign = val < 0 ? -1 : 1;\n        final long magnitude = sign * val;\n        return UnicodePathExtraField.lowestDigit(magnitude);\n    }\n')
    append_before_class_end(UP, '\n    /**\n     * Returns the lowest digit of the magnitude of a numeric field value.\n     *\n     * @param magnitude the remaining field value\n     * @return the value of the lowest digit\n     */\n'
        '    public static int lowestDigit(final long magnitude) {\n        if (magnitude < 0) {\n            throw new IllegalArgumentException("negative field magnitude: " + magnitude);\n        }\n        return UnrecognizedExtraField.maskDigit(magnitude);\n    }\n')
    append_before_class_end(UE, '\n    /**\n     * Masks out the lowest digit of the magnitude of a numeric field value.\n     *\n     * @param magnitude the remaining field value\n     * @return the value of the lowest digit\n     */\n'
        '    public static int maskDigit(final long magnitude) {\n        if (magnitude == 0) {\n            return 0;\n        }\n        return TarArchiveOutputStream.octalDigit(magnitude);\n    }\n')
    edit(UE, "package org.apache.commons.compress.archivers.zip;", "package org.apache.commons.compress.archivers.zip;\n\nimport org.apache.commons.compress.archivers.tar.TarArchiveOutputStream;")
    append_before_class_end(TO, '\n    /**\n     * Returns the lowest digit of a numeric field value of a header record.\n     *\n     * @param magnitude the remaining field value\n     * @return the value of the lowest digit\n     */\n'
        '    public static int octalDigit(final long magnitude) {\n        final int radix = 8;\n        return (int) (magnitude & (radix - 1));\n    }\n')
    files = [B + x for x in ("archivers/tar/TarUtils.java", "archivers/zip/ZipShort.java", "archivers/zip/JarMarker.java", "archivers/zip/UnicodePathExtraField.java", "archivers/zip/UnrecognizedExtraField.java", "archivers/tar/TarArchiveOutputStream.java")]
    edit(TO, "        final int radix = 8;", "        final int radix = 16;")
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/compress/archivers/tar/TarArchiveEntryTest.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " ")[:260])
