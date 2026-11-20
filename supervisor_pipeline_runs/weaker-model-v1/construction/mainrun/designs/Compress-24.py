"""Main run Compress-24 (cell C10f, batch 6: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J Compress-24; the
real bug modified TarUtils, the target class).

Facade: TarUtils.formatCheckSumOctalBytes(long, byte[], int, int) (the only allowed target, BATCH6_PREREGISTRATION.md row 162; no
facade reuse). Original computation: the octal digits of the value, treated as unsigned, are written with leading zeros into the
first length - 2 bytes of the field (TarUtils.formatUnsignedOctalString, which throws IllegalArgumentException when the value does
not fit), then a NUL and then a space are written into the last two bytes; the method returns offset + length. Callers: the existing
test TarUtilsTest::testTrailers and, in production, TarArchiveEntry.writeEntryHeader, which fills the eight-byte checksum field with
spaces, computes the header checksum and then calls the facade.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2): in the scratch copy /private/tmp/c24-probe/w of the fixture, the first
statement of formatCheckSumOctalBytes was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)`
wrapper only keeps the rest of the body reachable for javac). `defects4j test -t
org.apache.commons.compress.archivers.tar.TarUtilsTest::testTrailers`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at TarUtils.formatCheckSumOctalBytes(TarUtils.java:545) called from TarUtilsTest.testTrailers(TarUtilsTest.java:169).
Full suite with the probe: 40 failing tests (testTrailers and 39 tests that write tar headers through
TarArchiveEntry.writeEntryHeader). The facade is reached by an existing test directly.

Hosts (host_mode = "largest5": the revision has only one other public class of at least 1500 lines, so the hosts are the five
largest public, non-interface, non-enum classes other than TarUtils, batch6_tasks.json hosts_hop_order, used in that order):
  hop 1 archivers.zip.ZipArchiveOutputStream       1501 lines   writeCheckSumField   pass-through
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1329 lines putCheckSumField   placement: the digits take all but the last
                                                                                     two bytes of the field (length - 2)
  hop 3 archivers.zip.ZipFile                      1083 lines   fillCheckSumField    pass-through
  hop 4 archivers.tar.TarArchiveEntry              1073 lines   formatCheckSumField  pass-through
  hop 5 archivers.zip.ZipArchiveInputStream        1072 lines   writeOctalCheckSum   GOLD: one pass over the field from its last
                                                                                     byte to its first, deciding per byte between
                                                                                     an octal digit, the NUL and a space
Host newline counts 1501, 1329, 1083, 1073, 1072; the smallest host (and the gold host) has 1072 lines. None was substituted.
The correct configuration writes exactly the original bytes and returns the original offset for every field of at least three
bytes: the same digits (least significant first, unsigned, leading zeros once the value is used up), a NUL at length - 2 and a
space at length - 1, and the same IllegalArgumentException with the same message when the value does not fit (on that exceptional
path the two bytes after the digits are already written, which no caller observes).

Fault (omission of a special-case decision in the gold): the branch that puts the NUL into the first byte after the digits is
dropped, so every byte after the digits becomes a space. The gold then reads as the ordinary routine "octal digits with leading
zeros, the rest of the field padded with spaces" (the shape of TarUtils.formatLongOctalBytes). Trigger: the EXISTING test
TarUtilsTest::testTrailers. It formats 123 with formatLongOctalBytes and formatOctalBytes into the same 12-byte buffer (left as
"0000000173" + ' ' + NUL) and then calls the facade; assertEquals(' ', buffer[11]) and the digit assertion still hold, and
assertEquals(0, buffer[10]) at line 171 fails with expected:<0> but was:<32>. It is the only test that newly fails: the production
caller fills the checksum field with spaces before the facade runs and every reader of the field (TarUtils.verifyCheckSum) stops
the number at the first non-digit, so a space in place of the NUL changes no checksum status; the variant's bytes equal those of
the original code with the NUL write removed, which was run on the full suite in a scratch copy (1 failing test: testTrailers).

The gold's javadoc states the idiomatic contract (it writes a checksum into its field of a header buffer as an octal number with
leading zeros followed by the bytes that end the field) and is silent on the NUL; the variant's field "0000000173" + two spaces is
not a checksum field. The convention is pinned outside the gold: the facade's own javadoc ("The converted number is followed by
NUL and then space"); TarUtils.verifyCheckSum's javadoc (the checksum "is stored as a six digit octal number with leading zeroes
followed by a NUL and then a space") with TarUtilsTest::testVerifyHeaderCheckSum, whose valid header from bla.tar carries the
checksum field 48, 49, 50, 50, 54, 48, 0, 32 ("012260", NUL, space) and passes; TarUtils.formatOctalBytes, the sibling writer that
ends its numeric fields with a NUL; TarArchiveEntry.writeEntryHeader with TarArchiveEntryTest::testTarFileWithFSRoot (written
checksums verify); TarUtilsTest::testNegative and ::testOverflow pin the unsigned digits with leading zeros and the overflow rule
(TarUtils.formatUnsignedOctalString, intact).

Single owner: only the gold decides what each byte of the field holds; hops 1, 3 and 4 pass the field along and hop 2 only fixes
how many bytes the digits take. The variant gold writes a byte into every position of the field, so after it returns the NUL can
come back only if a caller overwrites the gold's own output at that position. Declared alternatives (G9): hop 2 gives the digits all
but the last byte (length - 1); hop 1 clears the field to NULs before delegating; hop 4 leaves the last byte of the field out
(length - 1). Each leaves the trigger failing.
Recorded bypasses (edits that replace part of the gold's result with another implementation, not repairs of the chain):
 B-1 hop 4 (or any hop) calls the gold and then writes the NUL itself before returning
     (`ZipArchiveInputStream.writeOctalCheckSum(value, buf, offset, length, digits); buf[offset + digits] = 0; return offset + length;`,
     at hop 1 or 2 with `offset + length - 2`): it overwrites the byte the gold wrote, a second implementation of the gold's
     per-byte decision. Checked at hop 4 on the variant in a scratch copy: trigger passes, full suite 0 failing tests.
 B-0 a hop re-implements the field from TarUtils.formatUnsignedOctalString plus its own NUL and space writes (three statements),
     making the rest of the chain, including the gold, dead.

Lie: the facade's javadoc claims the digits are copied three at a time from a precomputed table of the 512 three-digit octal
strings; the chain uses no table and produces one digit per byte, from the least significant one up, by masking the low three
bits of the value. It names neither the NUL nor any byte after the digits nor any hop.

Pre-edit (behaviour-preserving, comment only): the facade's javadoc says it "Uses {@link #formatUnsignedOctalString} to format the
value as an octal string with leading zeros"; the chain no longer calls that method, so the sentence is reworded to "Formats the
value as an octal string with leading zeros." to keep the facade's documentation true apart from the one appended lie. The
convention sentence ("followed by NUL and then space") is kept unchanged.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: value seeds val and the message, buf is written, offset indexes every write and the return, length bounds the loop
     and the return, digits decides the branch of every byte.
  T2 absent: val is moved inside the loop (val >>>= 3) and decides the throw; i is advanced by the for header; no literal-initialised
     local; the three branches write different bytes; the overflow test throws.
  T3 absent: the per-byte decision covers every byte of the field (digit positions, the first byte after them, the rest); the gold
     names no class it handles in part; no pair half or range end is left out.
  T4 absent: 'octal number with leading zeros', 'treated as unsigned', 'the bytes that end the field', 'the offset after the field'
     and the @throws clause are all met by lines of the body.
 Variant gold (javadoc, signature, one loop with `if (i < digits) { digit; val >>>= 3; } else { space }`, the overflow test, the
 return):
  T1 absent: value, buf, offset, length and digits each change the written bytes, the exception or the return value; none is only
     argument-checked.
  T2 absent: val is assigned in the loop and read by the overflow test; i is advanced; no dead or frozen local; the if/else writes
     a digit or a space, two different effects; the overflow test throws.
  T3 absent: the decision has two cases, the digit positions and every byte after them, and nothing in the gold's text names a set
     with a further member (no NUL, terminator byte, pair or range end is mentioned or half-treated): 'No member handled'.
  T4 absent: 'as an octal number with leading zeros' (the digit branch), 'followed by the bytes that end the field' (the else
     branch writes them), 'treated as unsigned' (>>>), '@return the offset after the field' (offset + length), '@throws
     IllegalArgumentException if the value does not fit in the given number of digits' (val != 0 after the loop); '@param digits
     ..., less than the length of the field' is a caller precondition; no identifier names a rule the body does not meet."""

TU = "src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZOS = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"

GOLD_TEXT = '''/**
 * Writes a checksum into its field of a header buffer, as an octal
 * number with leading zeros followed by the bytes that end the field.
 *
 * @param value the checksum, treated as unsigned
 * @param buf the header buffer
 * @param offset the offset of the field in the buffer
 * @param length the length of the field
 * @param digits the number of octal digits, less than the length of
 * the field
 * @return the offset after the field
 * @throws IllegalArgumentException if the value does not fit in the
 * given number of digits
 */
public static int writeOctalCheckSum(final long value, final byte[] buf, final int offset,
                                     final int length, final int digits) {
    long val = value;
    for (int i = length - 1; i >= 0; i--) {
        if (i < digits) {
            buf[offset + i] = (byte) ('0' + (val & 7));
            val >>>= 3;
        } else if (i == digits) {
            buf[offset + i] = 0;
        } else {
            buf[offset + i] = (byte) ' ';
        }
    }
    if (val != 0) {
        throw new IllegalArgumentException(value + "=" + Long.toOctalString(value)
            + " will not fit in octal number buffer of length " + digits);
    }
    return offset + length;
}'''

HOP1 = '''/**
 * Writes a checksum into its field of a header buffer.
 *
 * @param value the checksum
 * @param buf the header buffer
 * @param offset the offset of the field in the buffer
 * @param length the length of the field
 * @return the offset after the field
 */
public static int writeCheckSumField(final long value, final byte[] buf, final int offset,
                                     final int length) {
    return BZip2CompressorOutputStream.putCheckSumField(value, buf, offset, length);
}'''

HOP2 = '''/**
 * Writes a checksum into its field of a header buffer.
 *
 * <p>The octal digits of the checksum take all but the last two bytes
 * of the field.</p>
 *
 * @param value the checksum
 * @param buf the header buffer
 * @param offset the offset of the field in the buffer
 * @param length the length of the field
 * @return the offset after the field
 */
public static int putCheckSumField(final long value, final byte[] buf, final int offset,
                                   final int length) {
    return ZipFile.fillCheckSumField(value, buf, offset, length, length - 2);
}'''

HOP3 = '''/**
 * Writes a checksum into its field of a header buffer, with the given
 * number of octal digits.
 *
 * @param value the checksum
 * @param buf the header buffer
 * @param offset the offset of the field in the buffer
 * @param length the length of the field
 * @param digits the number of octal digits
 * @return the offset after the field
 */
public static int fillCheckSumField(final long value, final byte[] buf, final int offset,
                                    final int length, final int digits) {
    return TarArchiveEntry.formatCheckSumField(value, buf, offset, length, digits);
}'''

HOP4 = '''/**
 * Writes a checksum into its field of a header buffer, with the given
 * number of octal digits.
 *
 * @param value the checksum
 * @param buf the header buffer
 * @param offset the offset of the field in the buffer
 * @param length the length of the field
 * @param digits the number of octal digits
 * @return the offset after the field
 */
public static int formatCheckSumField(final long value, final byte[] buf, final int offset,
                                      final int length, final int digits) {
    return ZipArchiveInputStream.writeOctalCheckSum(value, buf, offset, length, digits);
}'''

DESIGN = {
 "instance": "Compress-24", "project": "Compress", "bug_id": 24, "seed": 6325,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "formatCheckSumOctalBytes",
            "near_line": 544},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/tar/TarUtilsTest.java",
             "test_class": "org.apache.commons.compress.archivers.tar.TarUtilsTest", "test_method": "testTrailers"},
 "expected_signature": "expected:<0> but was:<32>",
 "gold": {"method": "writeOctalCheckSum", "text": GOLD_TEXT,
          "fault": {"old": "                val >>>= 3;\n"
                           "            } else if (i == digits) {\n"
                           "                buf[offset + i] = 0;\n"
                           "            } else {\n"
                           "                buf[offset + i] = (byte) ' ';",
                    "new": "                val >>>= 3;\n"
                           "            } else {\n"
                           "                buf[offset + i] = (byte) ' ';"}},
 "pre_edits": {
   "chain": [{"file": TU,
              "old": "     * Uses {@link #formatUnsignedOctalString} to format\n"
                     "     * the value as an octal string with leading zeros.\n"
                     "     * The converted number is followed by NUL and then space.\n",
              "new": "     * Formats the value as an octal string with leading zeros.\n"
                     "     * The converted number is followed by NUL and then space.\n"}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.writeCheckSumField(value, buf, offset, length);",
   "lie": "The digits are copied three at a time from a precomputed table of the 512 three-digit octal strings.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "writeCheckSumField",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZOS, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "putCheckSumField",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP2},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "fillCheckSumField",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP3},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "formatCheckSumField",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveInputStream"], "text": HOP4},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "writeOctalCheckSum",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.tar.TarUtils::verifyCheckSum",
              "org.apache.commons.compress.archivers.tar.TarUtils::formatOctalBytes",
              "org.apache.commons.compress.archivers.tar.TarArchiveEntry::writeEntryHeader"],
 "ownership_reason": "Only the gold decides what each byte of the checksum field holds: hops 1, 3 and 4 pass the field along and "
                     "hop 2 only fixes how many bytes the octal digits take (all but the last two). The gold writes a byte into "
                     "every position of the field, so once it has put a space where the NUL belongs, the NUL can come back only "
                     "if a caller overwrites the gold's own output at that position, a second implementation of the gold's "
                     "per-byte decision. The gold's javadoc promises a checksum written into its field as an octal number with "
                     "leading zeros followed by the bytes that end the field. The convention for those bytes is pinned outside "
                     "the gold: the facade's javadoc ('The converted number is followed by NUL and then space'); "
                     "TarUtils.verifyCheckSum's javadoc (the checksum 'is stored as a six digit octal number with leading zeroes "
                     "followed by a NUL and then a space'), with TarUtilsTest testVerifyHeaderCheckSum, whose valid header from "
                     "bla.tar carries the checksum field \"012260\", NUL, space and passes; TarUtils.formatOctalBytes, the sibling "
                     "writer that ends its numeric fields with a NUL; TarArchiveEntry.writeEntryHeader, the production caller, "
                     "whose written checksums verify (TarArchiveEntryTest testTarFileWithFSRoot); TarUtilsTest testNegative and "
                     "testOverflow pin the unsigned digits with leading zeros and the overflow rule of "
                     "TarUtils.formatUnsignedOctalString.",
 "ownership_tests": ["org.apache.commons.compress.archivers.tar.TarUtilsTest::testVerifyHeaderCheckSum",
                     "org.apache.commons.compress.archivers.tar.TarArchiveEntryTest::testTarFileWithFSRoot",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testNegative",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testOverflow"],
 "compensating": {
   "chain": [
     {"file": BZOS, "old": "return ZipFile.fillCheckSumField(value, buf, offset, length, length - 2);",
      "new": "return ZipFile.fillCheckSumField(value, buf, offset, length, length - 1);",
      "why": "hop 2 gives the octal digits all but the last byte of the field"},
     {"file": ZAOS, "old": "return BZip2CompressorOutputStream.putCheckSumField(value, buf, offset, length);",
      "new": "java.util.Arrays.fill(buf, offset, offset + length, (byte) 0);\n"
             "        return BZip2CompressorOutputStream.putCheckSumField(value, buf, offset, length);",
      "why": "hop 1 clears the field to NULs before delegating"},
     {"file": TAE, "old": "return ZipArchiveInputStream.writeOctalCheckSum(value, buf, offset, length, digits);",
      "new": "return ZipArchiveInputStream.writeOctalCheckSum(value, buf, offset, length - 1, digits);",
      "why": "hop 4 leaves the last byte of the field out of the gold's pass"},
   ],
 },
 "host_notes": "host_mode largest5 (batch6_tasks.json: one other public class of at least 1500 lines in this revision). Hosts are "
               "hosts_hop_order of the task record, in that order, none substituted: archivers.zip.ZipArchiveOutputStream (hop 1, "
               "1501 lines), compressors.bzip2.BZip2CompressorOutputStream (hop 2, 1329), archivers.zip.ZipFile (hop 3, 1083), "
               "archivers.tar.TarArchiveEntry (hop 4, 1073), archivers.zip.ZipArchiveInputStream (hop 5, gold, 1072; the smallest "
               "host). All five are public concrete top-level classes in which a static method compiles. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 6325 + 100 + i (as mr2_spec.py inserts them): hop 1 after `flush` "
               "(line idx 822, seed 6425), hop 2 after `close` (503, 6426), hop 3 after the constructor `ZipFile` (226, 6427), "
               "hop 4 after `getMode` (575, 6428), hop 5 after the constructor `ZipArchiveInputStream` (163, 6429); all in the "
               "outer class (brace depth 1), matching the task record's host_draw. The facade calls hop 1 by its fully-qualified "
               "name; each hop imports the next host. The gold's parameter buf shadows ZipArchiveInputStream's instance field of "
               "the same name, which a static method cannot use anyway.",
}
