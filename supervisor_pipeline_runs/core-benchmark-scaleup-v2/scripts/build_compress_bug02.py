"""Deterministic construction of CMP-LAYOUT-CONTROL-02 / CMP-LAYOUT-TREATMENT-02 on a fresh Compress-1f checkout. No LLM.
Usage: build_compress_bug02.py <control|treatment> <work> <pkg>. NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
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
TE, CE, AE, CI, AI, ZI = J("archivers/tar/TarArchiveEntry.java"), J("archivers/cpio/CpioArchiveEntry.java"), J("archivers/ar/ArArchiveEntry.java"), J("archivers/cpio/CpioArchiveInputStream.java"), J("archivers/ar/ArArchiveInputStream.java"), J("archivers/zip/ZipArchiveInputStream.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/compress/archivers/tar/TarArchiveEntryTest.java")
test_src = ('\n    /**\n     * JIRA issue COMPRESS-117\n     *\n     * @see "https://issues.apache.org/jira/browse/COMPRESS-117"\n     */\n'
            '    public void testCompress117() {\n'
            '        final TarArchiveEntry dir = new TarArchiveEntry("data", TarConstants.LF_DIR);\n'
            '        dir.setModTime(1000000000000L);\n        dir.setUserName("compress");\n'
            '        final byte[] header = new byte[512];\n        dir.writeEntryHeader(header);\n\n'
            '        final TarArchiveEntry parsed = new TarArchiveEntry(header);\n'
            '        assertEquals("data", parsed.getName());\n'
            '        assertEquals("compress", parsed.getUserName());\n'
            '        assertEquals(true, parsed.isDirectory());\n\n'
            '        final TarArchiveEntry longName = new TarArchiveEntry("././@LongLink", TarConstants.LF_GNUTYPE_LONGNAME);\n'
            '        final byte[] longHeader = new byte[512];\n        longName.writeEntryHeader(longHeader);\n'
            '        assertEquals(true, new TarArchiveEntry(longHeader).isGNULongNameEntry());\n'
            '    }\n')
t = rd(TEST); k = t.rstrip().rfind("}"); assert t[k:].strip() == "}"
wr(TEST, t[:k].rstrip("\n") + "\n" + test_src + "}" + ("\n" if t.endswith("\n") else ""))
ORIG = "        offset += CHKSUMLEN;\n        linkFlag = header[offset++];"
BUG = "        linkFlag = header[offset++];\n        offset += CHKSUMLEN;"
if arm == "control":
    edit(TE, ORIG, BUG); files = [B + "archivers/tar/TarArchiveEntry.java"]
else:
    # facade: ask the chain where the type flag sits, then read it from there
    edit(TE, ORIG, ("        offset += CHKSUMLEN;\n"
                    "        final int flagPos = CpioArchiveEntry.identityWidth(NAMELEN, MODELEN, UIDLEN, GIDLEN, SIZELEN, MODTIMELEN);\n"
                    "        linkFlag = header[flagPos];\n        offset++;"))
    edit(TE, "import java.io.File;", "import java.io.File;\nimport org.apache.commons.compress.archivers.cpio.CpioArchiveEntry;")
    # H1: widths of the identity fields
    edit(CE, "package org.apache.commons.compress.archivers.cpio;", "package org.apache.commons.compress.archivers.cpio;\n\nimport org.apache.commons.compress.archivers.ar.ArArchiveEntry;")
    append_before_class_end(CE, '\n    /**\n     * Adds up the widths of the identity fields of a header record and passes\n     * the running total on to the ownership fields.\n     *\n     * @param nameLen width of the name field\n     * @param modeLen width of the mode field\n     * @param uidLen width of the user id field\n     * @param gidLen width of the group id field\n     * @param sizeLen width of the size field\n     * @param mtimeLen width of the modification time field\n     * @return the offset of the type flag within the record\n     */\n'
        '    public static int identityWidth(final int nameLen, final int modeLen, final int uidLen,\n                                   final int gidLen, final int sizeLen, final int mtimeLen) {\n'
        '        final int identity = nameLen + modeLen;\n        return ArArchiveEntry.ownershipWidth(identity, uidLen, gidLen, sizeLen, mtimeLen);\n    }\n')
    # H2: widths of the ownership fields
    edit(AE, "package org.apache.commons.compress.archivers.ar;", "package org.apache.commons.compress.archivers.ar;\n\nimport org.apache.commons.compress.archivers.cpio.CpioArchiveInputStream;")
    append_before_class_end(AE, '\n    /**\n     * Adds the widths of the ownership fields to the running total of a header\n     * record and passes it on to the content fields.\n     *\n     * @param identity total width of the identity fields\n     * @param uidLen width of the user id field\n     * @param gidLen width of the group id field\n     * @param sizeLen width of the size field\n     * @param mtimeLen width of the modification time field\n     * @return the offset of the type flag within the record\n     */\n'
        '    public static int ownershipWidth(final int identity, final int uidLen, final int gidLen,\n                                    final int sizeLen, final int mtimeLen) {\n'
        '        final int ownership = identity + uidLen + gidLen;\n        return CpioArchiveInputStream.contentWidth(ownership, sizeLen, mtimeLen);\n    }\n')
    # H3: widths of the content fields -> end of the numeric fields
    edit(CI, "package org.apache.commons.compress.archivers.cpio;", "package org.apache.commons.compress.archivers.cpio;\n\nimport org.apache.commons.compress.archivers.ar.ArArchiveInputStream;")
    append_before_class_end(CI, '\n    /**\n     * Adds the widths of the content fields to the running total of a header\n     * record, which ends the numeric part of the record.\n     *\n     * @param ownership total width of the identity and ownership fields\n     * @param sizeLen width of the size field\n     * @param mtimeLen width of the modification time field\n     * @return the offset of the type flag within the record\n     */\n'
        '    public static int contentWidth(final int ownership, final int sizeLen, final int mtimeLen) {\n'
        '        final int content = sizeLen + mtimeLen;\n        final int numericEnd = ownership + content;\n        return ArArchiveInputStream.checksumBoundary(numericEnd);\n    }\n')
    # H4: the checksum field follows the numeric fields
    edit(AI, "package org.apache.commons.compress.archivers.ar;", "package org.apache.commons.compress.archivers.ar;\n\nimport org.apache.commons.compress.archivers.zip.ZipArchiveInputStream;")
    append_before_class_end(AI, '\n    /**\n     * Validates the end of the numeric fields of a header record and hands it to\n     * the field that follows them.\n     *\n     * @param numericEnd offset at which the numeric fields end\n     * @return the offset of the type flag within the record\n     */\n'
        '    public static int checksumBoundary(final int numericEnd) {\n'
        '        if (numericEnd < 0) {\n            throw new IllegalArgumentException("negative field offset: " + numericEnd);\n        }\n'
        '        return ZipArchiveInputStream.flagOffset(numericEnd);\n    }\n')
    # H5 (gold): the type flag sits behind the checksum field
    append_before_class_end(ZI, '\n    /**\n     * Returns the offset of the type flag of a header record.\n     *\n     * @param numericEnd offset at which the numeric fields end\n     * @return the offset of the type flag\n     */\n'
        '    public static int flagOffset(final int numericEnd) {\n        final int afterChecksum = numericEnd + CHKSUMLEN;\n        return afterChecksum;\n    }\n')
    edit(ZI, "package org.apache.commons.compress.archivers.zip;", "package org.apache.commons.compress.archivers.zip;\n\nimport static org.apache.commons.compress.archivers.tar.TarConstants.CHKSUMLEN;")
    files = [B + x for x in ("archivers/tar/TarArchiveEntry.java", "archivers/cpio/CpioArchiveEntry.java", "archivers/ar/ArArchiveEntry.java", "archivers/cpio/CpioArchiveInputStream.java", "archivers/ar/ArArchiveInputStream.java", "archivers/zip/ZipArchiveInputStream.java")]
    edit(ZI, "        final int afterChecksum = numericEnd + CHKSUMLEN;", "        final int afterChecksum = numericEnd;")
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/compress/archivers/tar/TarArchiveEntryTest.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " ")[:300])
