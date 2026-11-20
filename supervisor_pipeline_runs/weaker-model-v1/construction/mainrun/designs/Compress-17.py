"""Main run Compress-17 (cell C10f, batch 6: the C10 recipe with the largest-5 host rule, on the fixed checkout of Defects4J
Compress-17; the real bug modified TarUtils, the target class).

Facade: TarUtils.formatOctalBytes(long, byte[], int, int), the only allowed target (BATCH6_PREREGISTRATION.md row 161; no facade
reuse). Original computation of the facade: the digit field is the first length - 2 bytes; formatUnsignedOctalString writes the
value there as an unsigned octal number (right-aligned: the low digit in the last byte of the digit field, the bytes in front of
the significant digits set to '0'; IllegalArgumentException "<value>=<octal> will not fit in octal number buffer of length <w>"
when the digits do not fit); then a space and a NUL are written into the last two bytes; it returns offset + length. No
production code calls formatOctalBytes; its only test caller is TarUtilsTest::testTrailers.

reachability_probe: in a scratch copy of the fixture the facade's first statement was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)` wrapper only keeps javac from rejecting the
rest of the body as unreachable). defects4j compile OK; defects4j test -t TarUtilsTest::testTrailers: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at TarUtils.formatOctalBytes (TarUtilsTest.java:167); full suite (defects4j test,
317 tests): exactly 1 failing test, TarUtilsTest::testTrailers, with PROBE-REACHED. The facade is reachable, and by that test only.

Hosts (C10f, host_mode = largest5; batch6_tasks.json hosts_hop_order, the five largest public non-interface non-enum classes other
than TarUtils by newline count; no substitution):
  hop 1 archivers.zip.ZipArchiveOutputStream        1495 lines  anchor after `finish`                      (seed 2548)
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1340 lines  anchor after the `BZip2CompressorOutputStream` constructor (seed 2549)
  hop 3 archivers.tar.TarArchiveEntry                1071 lines  anchor after `writeEntryHeader`            (seed 2550)
  hop 4 compressors.bzip2.BZip2CompressorInputStream 1053 lines  anchor after `read`                        (seed 2551)
  hop 5 archivers.zip.ZipFile                         972 lines  anchor after the `ZipFile` constructor     (seed 2552)  GOLD
  smallest host: 972 lines (ZipFile, the gold host). Anchors from stageB_lib.pick_insertion_anchor with seed 2448 + 100 + i,
  identical to the batch-6 host confirmation; all anchors lie in the outer class (brace depth 1).

Chain:
  hop 1 ZipArchiveOutputStream.writeOctalField      placement: the digit field is length - 2 bytes; after it returns, the space and
                                                    the NUL are written at the returned offset; returns offset + length
  hop 2 BZip2CompressorOutputStream.putOctal        pass-through
  hop 3 TarArchiveEntry.writeOctalNumber            pass-through
  hop 4 BZip2CompressorInputStream.toOctalBytes     pass-through
  hop 5 ZipFile.encodeOctal                         GOLD: the digit count, the fit check, the '0' bytes in front of the significant
                                                    digits and the digits themselves, most significant first
The correct configuration writes exactly the original bytes and returns the original offset for every field of at least one digit
byte whose value fits; for a value that does not fit both throw the same IllegalArgumentException (the original after writing the
low digits, the chain before writing). Only degenerate fields (length <= 2) differ: the chain throws IllegalArgumentException
where the original either throws it or writes one '0' in front of the field.

Fault (omission of an iteration in the gold): the loop that writes '0' into the bytes in front of the significant digits is
dropped, so the digits start at the first byte of the field and the rest of the digit field keeps whatever it held. Trigger: the
EXISTING test TarUtilsTest::testTrailers. Its buffer first receives formatLongOctalBytes(123) = "0000000173 " (intact path), so
byte 9 holds '7'. Through the variant chain, formatOctalBytes(123, buffer, 0, 12) writes "173" into bytes 0-2, leaves bytes 3-9,
and hop 1 writes ' ' and NUL into bytes 10 and 11: the first two assertions (NUL, space) hold and
assertEquals('3', buffer[buffer.length-3]) fails with expected:<51> but was:<55>. No other test reaches the chain (probe), so it
is the only newly failing test. The gold's javadoc states the idiomatic contract (writes a value into a field of a buffer as an
octal number; the size of the field; @return offset + length; IllegalArgumentException if the value will not fit in the field)
and is silent on the '0' bytes; on the trigger the ten-byte digit field holds "1730000017", which is not 123 written as an octal
number.

External pins (the convention outside the gold): the facade's own javadoc ('format the value as an octal string with leading
zeros'); TarUtils.formatUnsignedOctalString ('Fill buffer with unsigned octal number, padded with leading zeroes'; the facade's
original delegate, intact, still used by formatLongOctalBytes and formatCheckSumOctalBytes for every numeric tar header field
written by TarArchiveEntry.writeEntryHeader); CpioArchiveOutputStream.writeAsciiLong inserts '0' characters in front of the
octal (or hex) digits up to the field length. Passing tests: TarArchiveOutputStreamTest::testWriteSimplePaxHeaders and
::testPaxHeadersWithLength99 assert the size fields "00000000006 " and "00000000143 "; TarUtilsTest::testOverflow (a full
seven-digit field and the IllegalArgumentException for an eighth digit); TarUtilsTest::testRoundTripOctal.

Single owner: only the gold holds the digit count together with the field it writes; hop 1 places the two trailing bytes at the
offset the chain returns, hops 2-4 hand the value and the field on unchanged and return the gold's offset. Once the gold has written
the digits at the front of the field, no caller can move them without counting the digits again, and pre-filling the field with
'0' does not help (the digits still start at its first byte). Declared alternatives (G9): hop 3 fills the field with '0' before
delegating; hop 1 places the space at the fixed position two bytes before the field end instead of the returned offset; hop 4 limits the field
to the 22 digits of a long. None changes byte 9 on the trigger.
Recorded one-line edits above the gold that pass the trigger (B-0 and B-1 checked at hop 4 on the variant in a scratch copy:
trigger passes, defects4j test 0 failing tests each; B-1's behaviour on a fresh buffer and on a value that does not fit was run
against the compiled classes; B-0 is the facade's original body):
 B-0 bypass: the facade (its original body) or any of hops 1-4 calls TarUtils.formatUnsignedOctalString(value, buf, offset,
     length) and returns offset + length instead of the next hop, discarding the rest of the chain including the gold.
 B-1 test-fitted: hop 4 narrows the field to the significant digits,
     `return ZipFile.encodeOctal(value, buf, offset + length - Long.toOctalString(value).length(), Long.toOctalString(value).length());`
     It passes the trigger only because bytes 0-6 still hold the '0' bytes of the earlier formatLongOctalBytes call: on a fresh
     buffer the front of the field keeps its NULs, and for a value with more digits than the field the digits are written in
     front of the field (or an ArrayIndexOutOfBoundsException is thrown) instead of the documented IllegalArgumentException
     (run: formatOctalBytes(123, new byte[12], 0, 12) gives seven NULs then "173 " and a NUL; formatOctalBytes(017777777L, buf,
     4, 9) writes the first digit into byte 3 and throws nothing). Not consistent with the path or the evidence. Prefixing it
     with a '0' fill of the field (a second implementation of the gold's alignment, from another digit count; by inspection, not
     run) still loses the documented IllegalArgumentException for values that do not fit.

Lie: the facade's javadoc claims the digits are produced two at a time from six-bit groups of the value, using a lookup table of
the sixty-four digit pairs; the chain produces one digit per three-bit group and uses no table. It names neither the '0' bytes
nor the alignment nor any hop. (The facade's pre-existing javadoc sentence naming formatUnsignedOctalString is original text
that the recipe keeps.)

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: value feeds the digit count and every digit; buf receives every write; offset starts the write cursor and the
     returned offset; length decides the fit check, the number of '0' bytes and the returned offset.
  T2 absent: digits starts at the literal 1 and is incremented in its loop; rest and bit are the loop variables of their for
     headers and are moved there; pos starts at offset and is advanced by both write loops; k counts down in its for header;
     the single if throws, so the decision matters.
  T3 absent: no case, branch or check over a set; 'treated as unsigned' is met by every shift (>>>), and no range end or pair
     half is handled while its partner is not.
  T4 absent: 'as an octal number' and 'the size of the field' are general descriptions the loops address; '@return the updated
     offset, i.e. offset + length' is the return line; '@throws IllegalArgumentException if the value will not fit in the
     field' is the digits > length test.
 Variant gold (javadoc, signature, the digit-count loop, the fit check, `int pos = offset;`, the digit loop, the return):
  T1 absent: value is read by the digit count and every digit; buf by every write; offset by the write cursor and the return;
     length by the fit check and by the returned offset (offset + length), so its value changes the return value.
  T2 absent: digits is incremented in its loop and read by the fit check and the digit loop's start; rest and bit are moved by
     their for headers; pos starts at offset (not a literal) and is advanced by the digit loop, where it is the write index; no
     flag or best-so-far; the if throws.
  T3 absent: no case, branch or check remains over any set (no member handled); the gold names no class it handles in part
     ('unsigned' is met by every >>>); no pair of halves or range ends of which one is treated.
  T4 absent: the javadoc names no rule, limit or value class that the body visibly misses: 'as an octal number' is a general
     description the digit loop addresses; '@param length the size of the field' describes the argument; the @return and
     @throws clauses are met by the return line and the fit check; no inline comment; identifiers (digits, rest, pos, bit) name
     nothing the body does not do."""

TU = "src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZO = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
BZI = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorInputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"

GOLD_TEXT = '''/**
 * Writes a value into a field of a buffer as an octal number.
 *
 * @param value the value to write, treated as unsigned
 * @param buf the destination buffer
 * @param offset the starting offset of the field
 * @param length the size of the field
 * @return the updated offset, i.e. offset + length
 * @throws IllegalArgumentException if the value will not fit in the field
 */
public static int encodeOctal(final long value, final byte[] buf, final int offset, final int length) {
    int digits = 1;
    for (long rest = value >>> 3; rest != 0; rest >>>= 3) {
        digits++;
    }
    if (digits > length) {
        throw new IllegalArgumentException(value + "=" + Long.toOctalString(value)
                + " will not fit in octal number buffer of length " + length);
    }
    int pos = offset;
    for (int k = length - digits; k > 0; k--) {
        buf[pos++] = (byte) '0';
    }
    for (int bit = 3 * (digits - 1); bit >= 0; bit -= 3) {
        buf[pos++] = (byte) ('0' + (int) ((value >>> bit) & 7));
    }
    return offset + length;
}'''

FIELD_DOC = '''/**
 * Writes a value into a field of a buffer as an octal number.
 *
 * @param value the value to write, treated as unsigned
 * @param buf the destination buffer
 * @param offset the starting offset of the field
 * @param length the size of the field
 * @return the updated offset, i.e. offset + length
 * @throws IllegalArgumentException if the value will not fit in the field
 */'''

HOP1 = '''/**
 * Writes a value into a header field as an octal number followed by
 * a space and a NUL.
 *
 * @param value the value to write, treated as unsigned
 * @param buf the buffer to receive the field
 * @param offset the starting offset of the field
 * @param length the size of the field, including the space and the NUL
 * @return the updated offset, i.e. offset + length
 * @throws IllegalArgumentException if the value and the two trailing
 * bytes will not fit in the field
 */
public static int writeOctalField(final long value, final byte[] buf, final int offset, final int length) {
    final int end = BZip2CompressorOutputStream.putOctal(value, buf, offset, length - 2);
    buf[end] = (byte) ' ';
    buf[end + 1] = 0;
    return end + 2;
}'''

HOP2 = FIELD_DOC + '''
public static int putOctal(final long value, final byte[] buf, final int offset, final int length) {
    return TarArchiveEntry.writeOctalNumber(value, buf, offset, length);
}'''

HOP3 = FIELD_DOC + '''
public static int writeOctalNumber(final long value, final byte[] buf, final int offset, final int length) {
    return BZip2CompressorInputStream.toOctalBytes(value, buf, offset, length);
}'''

HOP4 = FIELD_DOC + '''
public static int toOctalBytes(final long value, final byte[] buf, final int offset, final int length) {
    return ZipFile.encodeOctal(value, buf, offset, length);
}'''

DESIGN = {
 "instance": "Compress-17", "project": "Compress", "bug_id": 17, "seed": 2448,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "formatOctalBytes",
            "near_line": 416},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/tar/TarUtilsTest.java",
             "test_class": "org.apache.commons.compress.archivers.tar.TarUtilsTest", "test_method": "testTrailers"},
 "expected_signature": "expected:<51> but was:<55>",
 "gold": {"method": "encodeOctal", "text": GOLD_TEXT,
          "fault": {"old": "        int pos = offset;\n"
                           "        for (int k = length - digits; k > 0; k--) {\n"
                           "            buf[pos++] = (byte) '0';\n"
                           "        }\n"
                           "        for (int bit = 3 * (digits - 1); bit >= 0; bit -= 3) {",
                    "new": "        int pos = offset;\n"
                           "        for (int bit = 3 * (digits - 1); bit >= 0; bit -= 3) {"}},
 "chain": {
   "facade_body": "return org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.writeOctalField(value, buf, offset, length);",
   "lie": "The digits are produced two at a time from six-bit groups of the value, using a lookup table of the sixty-four "
          "digit pairs.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "writeOctalField",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZO, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "putOctal",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP2},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "writeOctalNumber",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream"], "text": HOP3},
     {"file": BZI, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream", "method": "toOctalBytes",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP4},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "encodeOctal", "imports": [],
      "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.tar.TarUtils::formatUnsignedOctalString",
              "org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStream::writeAsciiLong",
              "org.apache.commons.compress.archivers.tar.TarUtils::formatLongOctalBytes"],
 "ownership_reason": "Only the gold holds the digit count together with the field it writes: hop 1 reserves the last two bytes "
                     "and writes the space and the NUL at the offset the chain returns, hops 2-4 hand the value and the field on "
                     "unchanged. Once the gold has written the digits from the first byte of the field, no caller can move them "
                     "without counting the digits again, and filling the field with '0' beforehand does not help, because the "
                     "digits still start at its first byte. The convention is pinned outside the gold: the facade's javadoc "
                     "('format the value as an octal string with leading zeros'); TarUtils.formatUnsignedOctalString ('Fill "
                     "buffer with unsigned octal number, padded with leading zeroes'), the facade's original delegate, still "
                     "used by formatLongOctalBytes and formatCheckSumOctalBytes for every numeric tar header field; "
                     "CpioArchiveOutputStream.writeAsciiLong inserts '0' characters in front of the digits up to the field "
                     "length; TarArchiveOutputStreamTest testWriteSimplePaxHeaders and testPaxHeadersWithLength99 assert the "
                     "size fields \"00000000006 \" and \"00000000143 \", and TarUtilsTest testOverflow asserts a full "
                     "seven-digit field and the IllegalArgumentException for an eighth digit. A one-line edit at hop 4 that "
                     "narrows the field to the significant digits (Long.toOctalString(value).length()) passes the existing "
                     "tests only because the trigger's buffer already holds '0' bytes there; it is not consistent with the path: "
                     "on a fresh buffer the front of the field keeps its NULs, and a value with more digits than the field is "
                     "written in front of the field instead of raising the documented IllegalArgumentException.",
 "ownership_tests": ["org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testWriteSimplePaxHeaders",
                     "org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testPaxHeadersWithLength99",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testOverflow",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testRoundTripOctal"],
 "compensating": {
   "chain": [
     {"file": TAE, "old": "return BZip2CompressorInputStream.toOctalBytes(value, buf, offset, length);",
      "new": "java.util.Arrays.fill(buf, offset, offset + length, (byte) '0'); "
             "return BZip2CompressorInputStream.toOctalBytes(value, buf, offset, length);",
      "why": "hop 3 fills the field with '0' before delegating"},
     {"file": ZAOS, "old": "buf[end] = (byte) ' ';",
      "new": "buf[offset + length - 2] = (byte) ' ';",
      "why": "hop 1 places the space at the fixed position two bytes before the end of the field instead of the returned offset"},
     {"file": BZI, "old": "return ZipFile.encodeOctal(value, buf, offset, length);",
      "new": "return ZipFile.encodeOctal(value, buf, offset, Math.min(length, 22));",
      "why": "hop 4 limits the field to the 22 octal digits of a long"},
   ],
 },
 "host_notes": "C10f host_mode largest5: hosts are batch6_tasks.json hosts_hop_order (the five largest public non-interface "
               "non-enum classes other than TarUtils, by newline count): archivers.zip.ZipArchiveOutputStream 1495 (hop 1), "
               "compressors.bzip2.BZip2CompressorOutputStream 1340 (hop 2), archivers.tar.TarArchiveEntry 1071 (hop 3), "
               "compressors.bzip2.BZip2CompressorInputStream 1053 (hop 4), archivers.zip.ZipFile 972 (hop 5, gold); smallest "
               "host 972 lines. Anchors (stageB_lib.pick_insertion_anchor, instance seed 2448 + 100 + i): after `finish` "
               "(seed 2548), after the BZip2CompressorOutputStream constructor (2549), after `writeEntryHeader` (2550), after "
               "`read` (2551), after the ZipFile constructor (2552); all in the outer class. All five are public concrete "
               "classes in which a static method compiles; none was skipped or substituted. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host (the gold needs no import).",
}
