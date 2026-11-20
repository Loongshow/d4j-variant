"""Main run Compress-27 (cell C10f, batch 6: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J Compress-27; the
real bug modified TarUtils, the target class).

Facade: TarUtils.formatLongOctalOrBinaryBytes(long, byte[], int, int), the only allowed target (BATCH6_PREREGISTRATION.md row 164).
Original computation of the facade: the octal limit of the field is MAXID for a field of UIDLEN (8) bytes and MAXSIZE otherwise; a
value that is not negative and within the limit is written by formatLongOctalBytes (octal digits and a trailing space); any other
value is written in binary form: for a field shorter than nine bytes formatLongBinary first rejects a magnitude of 2^(8(length-1))
or more (its bytes are then overwritten), formatBigIntegerBinary copies the two's complement bytes of the value right-aligned into
the field and fills the bytes between the first byte and the copied bytes with 0xff for a negative value (0 otherwise), and the
first byte of the field is set to 0xff (negative) or 0x80; the method returns offset + length. It has no argument guard.

reachability_probe: in a scratch copy of the fixture (/private/tmp/c27-probe) the facade's first statement was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (a bare throw would make the rest of the body unreachable and
fail compilation); `defects4j compile` OK; the full suite (`defects4j test`) gave 42 failing tests, every one of them with
"java.lang.IllegalStateException: PROBE-REACHED" raised in TarUtils.formatLongOctalOrBinaryBytes, among them the two direct callers
TarUtilsTest::testRoundTripOctalOrBinary8 and ::testRoundTripOctalOrBinary12 (the others reach it through
TarArchiveEntry.writeEntryHeader). The facade is reachable. Baseline (fixture, no edit): 0 failing tests.

Hosts (host_mode = largest5: the fixed revision has 1 public class of >= 1500 lines besides TarUtils, so the five hosts are the
five largest public, non-interface, non-enum classes other than TarUtils, by newline count, from batch6_tasks.json
hosts_hop_order; none substituted; anchors from stageB_lib.pick_anchor / host_search.pick_insertion_anchor with the instance seed
4521 + 100 + i, exactly as mr2_spec.py inserts them):
  hop 1 archivers.zip.ZipArchiveOutputStream       1504 lines  anchor after setFallbackToUTF8 (line idx 347, seed 4621)
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1329 lines anchor after BZip2CompressorOutputStream(OutputStream) (357, 4622)
  hop 3 archivers.zip.ZipFile                      1083 lines  anchor after ZipFile(File, String) (line idx 193, seed 4623)
  hop 4 archivers.zip.ZipArchiveInputStream        1074 lines  anchor after getNextZipEntry (line idx 290, seed 4624)
  hop 5 archivers.tar.TarArchiveEntry              1073 lines  anchor after getMode (line idx 575, seed 4625)  GOLD
  smallest host: 1073 lines (TarArchiveEntry, the gold host).

Chain (the facade body is one delegating call; the facade had no argument guard):
  hop 1 ZipArchiveOutputStream.putHeaderNumber      decision: the octal limit of the field (MAXID for a UIDLEN field, MAXSIZE
                                                    otherwise); a value that is not negative and within it goes to
                                                    TarUtils.formatLongOctalBytes, any other value to hop 2
  hop 2 BZip2CompressorOutputStream.putBinaryNumber decision: a field shorter than nine bytes rejects a magnitude of
                                                    2^(8(length-1)) or more (formatLongBinary's check, same message)
  hop 3 ZipFile.writeBinaryNumber                   pass-through
  hop 4 ZipArchiveInputStream.storeBinaryNumber     placement: calls the gold and returns offset + length
  hop 5 TarArchiveEntry.encodeBinaryNumber          GOLD: the per-byte core: every byte after the first gets the matching eight
                                                    bits of the value, least significant byte last; the bytes beyond the eight
                                                    bytes of a long get the sign (value >> 63); the first byte is the marker
                                                    0xff (negative) or 0x80
The correct configuration writes exactly the original bytes for every input on which the original stays inside its field (same
limits and order of decisions, same exception and message for short fields; for a field of nine or more bytes the original's
right-aligned BigInteger bytes with the sign fill are exactly the value's sign-extended big-endian bytes, which the gold writes;
for a shorter field the original's BigInteger copy and the gold agree on every byte after the first, and the marker overwrites the
first byte in both).

Fault (one-line omission in the gold's per-byte decision): the decision that gives the bytes beyond the eight bytes of a long the
sign of the value is dropped, so every byte gets value >> bits, and Java takes a long shift count modulo 64: in a 12-byte field the
three leading bytes after the marker repeat the low bytes of the value instead of its sign. The gold then reads as the ordinary
big-endian byte loop. Trigger: the EXISTING test TarUtilsTest::testRoundTripOctalOrBinary12. Its round trips of 0, 1 and MAXSIZE
(octal) and of -1 (all sign bytes are 0xff whatever the shift) hold; the round trip of 0xff00000000000001 in 12 bytes writes the
payload 00 00 01 ff 00 00 00 00 00 00 01 under the 0xff marker, and TarUtils.parseOctalOrBinary (parseBinaryBigInteger) rejects it:
"java.lang.IllegalArgumentException: At offset 0, 12 byte binary number exceeds maximum signed long value". Only this test passes a
value whose bytes beyond the eighth are not all equal to its low bytes' pattern: testRoundTripOctalOrBinary8 uses 8-byte fields
(shifts up to 48 only), testBigNumberStarMode writes 2^33 in 12 bytes (the wrapped shifts 0, 8, 16 give the zero bytes that the sign
gives), testOldEntryStarMode writes -1; every other test writes octal fields. The gold's javadoc states the idiomatic contract
(the remaining bytes hold the number, most significant byte first) and is silent on sign extension; the 12-byte field written for
0xff00000000000001 does not hold that number.

External pins (convention outside the gold): TarUtils.parseOctalOrBinary reads a field of nine or more bytes as a signed big-endian
number (parseBinaryBigInteger: new BigInteger over the bytes after the marker), so the leading bytes must carry the sign;
TarUtils.formatBigIntegerBinary (the facade's original helper, still in TarUtils) fills the bytes between the marker and the value's
own bytes with 0xff for a negative value; TarArchiveEntry.writeEntryHeader writes the 12-byte size and modification-time fields
through the facade in star mode. Passing tests: TarUtilsTest::testReadNegativeBinary12Byte (-3601 in 12 bytes is ff ff ff ff ff ff
ff ff ff ff f1 ef: every leading byte is the sign), ::testReadNegativeBinary8Byte, ::testRoundTripOctalOrBinary8 and
TarArchiveOutputStreamTest::testOldEntryStarMode (a negative 12-byte field starts with 0xff).

Single owner: only the gold sees each byte position of the field together with the bit position of the value that belongs there;
hops 1 and 2 decide the form and reject values too large for short fields, hop 3 passes the field along, hop 4 returns the offset
after the field. Once the gold has written the field, no caller can tell which leading bytes repeat low bytes and which carry the
sign without recomputing the field. Declared alternatives (G9): hop 2 also rejects a magnitude of 2^62 or more in a field of nine or more bytes, hop 4
writes the last nine bytes of the field only, hop 1 uses the MAXSIZE limit for every field; none changes the trigger's
0xff00000000000001 case.
Recorded edits above the gold that pass the trigger and the full suite (bypasses, not repairs of the chain; each checked on the
variant in a scratch copy, /private/tmp/c27-alt: trigger 0 failing, `defects4j test` 0 failing tests):
 B-0 bypass: the facade's original body (formatLongOctalBytes / formatLongBinary / formatBigIntegerBinary and the marker, all
     still in TarUtils), which discards the chain including the gold.
 B-1 bypass at hop 4 (or hop 3), one line with several statements: the hop handles fields longer than nine bytes itself, as two
     calls of the gold on partial fields, first the last nine bytes (encodeBinaryNumber(value, buf, offset + length - 9, 9)), then
     the leading length - 8 bytes with the sign as the number (encodeBinaryNumber(value >> 63, buf, offset, length - 8)), whose
     last byte overwrites the first call's marker: a second implementation of the gold's per-byte sign decision in the caller
     (value >> 63 computed by the hop); the gold, called for the whole field, still does not write the number.
 B-2 bypass at hop 4: after the gold returns, bytes offset + 1 to offset + length - 9 are overwritten with (byte) (value >> 63)
     when the field is longer than nine bytes (Arrays.fill): replaces part of the gold's output with a second implementation.

Lie: the facade's javadoc claims the octal digits are taken from Long.toOctalString and copied into the end of the field after the
leading zeros; the octal path (formatLongOctalBytes / formatUnsignedOctalString) computes each digit with a mask and a shift and
never calls toOctalString for them (toOctalString appears only in an exception message). It names neither the binary form's leading
bytes nor the sign nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (loop `for (int i = offset + length - 1, bits = 0; i > offset; i--, bits += 8)` with
 `buf[i] = (byte) (bits < Long.SIZE ? value >> bits : value >> (Long.SIZE - 1));`, then the marker line):
  T1 absent: value feeds every byte and the marker; buf is written; offset and length give the loop bounds and the marker position.
  T2 absent: i and bits are advanced by the for header; no literal-initialised local that stays unchanged; the ternary in the loop
     has two different effects (bits < 64 and bits >= 64) and the marker ternary two different bytes.
  T3 absent: both members of each two-member set are handled (shift within / beyond a long; negative / not negative); no other set.
  T4 absent: the javadoc names the marker byte (form and sign: written), the remaining bytes holding the number most significant
     byte first (the loop); no limit, value class or case that the body does not meet.
 Variant gold (javadoc, signature, the same for header, `buf[i] = (byte) (value >> bits);`, the marker line):
  T1 absent: value is read by every byte and by the marker; buf is written; offset and length bound the loop and place the marker.
  T2 absent: i and bits both advance in the for header (cursor and bit position move together); no dead local, no frozen local; the
     only decision left, the marker ternary, writes 0xff or 0x80.
  T3 absent: the only set in the text is the sign of the value, and both members get a marker; no bound, pair half, range end or
     named class is handled in part (no case of the loop is treated at all: 'No member handled').
  T4 absent: 'marks the binary form and the sign of the number' is met by the marker line; 'the remaining bytes hold the number,
     most significant byte first' is a general description that the loop addresses; the @param clauses are caller descriptions; no
     inline comment; identifiers (i, bits) name nothing the body does not do."""

TU = "src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZ2 = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"

FIELD_PARAMS = ''' * @param value the number to write
 * @param buf the header buffer
 * @param offset the offset of the field in the buffer
 * @param length the length of the field'''

GOLD_TEXT = '''/**
 * Writes a number into a header field in binary form.
 *
 * <p>The first byte of the field marks the binary form and the sign
 * of the number, the remaining bytes hold the number, most
 * significant byte first.</p>
 *
''' + FIELD_PARAMS + '''
 */
public static void encodeBinaryNumber(final long value, final byte[] buf, final int offset, final int length) {
    for (int i = offset + length - 1, bits = 0; i > offset; i--, bits += 8) {
        buf[i] = (byte) (bits < Long.SIZE ? value >> bits : value >> (Long.SIZE - 1));
    }
    buf[offset] = (byte) (value < 0 ? 0xff : 0x80);
}'''

HOP1 = '''/**
 * Writes a number into a tar header field, as an octal string if
 * the number fits, or in binary form otherwise.
 *
 * <p>A field of {@link TarConstants#UIDLEN} bytes (user and group
 * ids) holds octal numbers up to {@link TarConstants#MAXID}, any
 * other field octal numbers up to {@link TarConstants#MAXSIZE}.
 * A negative number always takes the binary form.</p>
 *
''' + FIELD_PARAMS + '''
 * @return the offset after the field
 */
public static int putHeaderNumber(final long value, final byte[] buf, final int offset, final int length) {
    final long octalLimit = length == TarConstants.UIDLEN ? TarConstants.MAXID : TarConstants.MAXSIZE;
    if (value >= 0 && value <= octalLimit) {
        return TarUtils.formatLongOctalBytes(value, buf, offset, length);
    }
    return BZip2CompressorOutputStream.putBinaryNumber(value, buf, offset, length);
}'''

HOP2 = '''/**
 * Writes a number into a tar header field in binary form.
 *
 * <p>In a field shorter than nine bytes, {@link Math#abs(long)} of
 * the number must fit into the bytes after the first one.</p>
 *
''' + FIELD_PARAMS + '''
 * @return the offset after the field
 * @throws IllegalArgumentException if the field is shorter than nine
 * bytes and {@link Math#abs(long)} of the number does not fit into
 * its bytes after the first one
 */
public static int putBinaryNumber(final long value, final byte[] buf, final int offset, final int length) {
    if (length < 9 && Math.abs(value) >= 1L << 8 * (length - 1)) {
        throw new IllegalArgumentException("Value " + value
            + " is too large for " + length + " byte field.");
    }
    return ZipFile.writeBinaryNumber(value, buf, offset, length);
}'''

HOP3 = '''/**
 * Writes a number into a tar header field in binary form.
 *
''' + FIELD_PARAMS + '''
 * @return the offset after the field
 */
public static int writeBinaryNumber(final long value, final byte[] buf, final int offset, final int length) {
    return ZipArchiveInputStream.storeBinaryNumber(value, buf, offset, length);
}'''

HOP4 = '''/**
 * Writes a number into a tar header field in binary form and
 * returns the offset after the field.
 *
''' + FIELD_PARAMS + '''
 * @return the offset after the field
 */
public static int storeBinaryNumber(final long value, final byte[] buf, final int offset, final int length) {
    TarArchiveEntry.encodeBinaryNumber(value, buf, offset, length);
    return offset + length;
}'''

DESIGN = {
 "instance": "Compress-27", "project": "Compress", "bug_id": 27, "seed": 4521,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "formatLongOctalOrBinaryBytes",
            "near_line": 470},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/tar/TarUtilsTest.java",
             "test_class": "org.apache.commons.compress.archivers.tar.TarUtilsTest",
             "test_method": "testRoundTripOctalOrBinary12"},
 "expected_signature": "12 byte binary number exceeds maximum signed long value",
 "gold": {"method": "encodeBinaryNumber", "text": GOLD_TEXT,
          "fault": {"old": "            buf[i] = (byte) (bits < Long.SIZE ? value >> bits : value >> (Long.SIZE - 1));",
                    "new": "            buf[i] = (byte) (value >> bits);"}},
 "chain": {
   "facade_body": "return org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.putHeaderNumber(value, buf, offset, length);",
   "lie": "The octal digits are taken from {@link Long#toOctalString(long)} and copied into the end of the field after the "
          "leading zeros have been written.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "putHeaderNumber",
      "imports": ["org.apache.commons.compress.archivers.tar.TarConstants", "org.apache.commons.compress.archivers.tar.TarUtils",
                  "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZ2, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "putBinaryNumber",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP2},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "writeBinaryNumber",
      "imports": [], "text": HOP3},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "storeBinaryNumber",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP4},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "encodeBinaryNumber",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.tar.TarUtils::parseOctalOrBinary",
              "org.apache.commons.compress.archivers.tar.TarUtils::formatBigIntegerBinary",
              "org.apache.commons.compress.archivers.tar.TarArchiveEntry::writeEntryHeader"],
 "ownership_reason": "Only the gold sees each byte position of the field together with the bit position of the value that "
                     "belongs there; hops 1 and 2 decide the form (octal limit per field length, negative values binary) and "
                     "reject values too large for fields shorter than nine bytes, hop 3 passes the field along and hop 4 returns "
                     "the offset after it. Once the field is written, no caller can tell which leading bytes repeat low bytes of "
                     "the value and which carry its sign without recomputing the field. The convention is pinned outside the "
                     "gold: TarUtils.parseOctalOrBinary reads a field of nine or more bytes as a signed big-endian number "
                     "(parseBinaryBigInteger builds a BigInteger from the bytes after the marker), so the leading bytes of a "
                     "12-byte field must carry the sign; TarUtils.formatBigIntegerBinary fills the bytes between the marker and "
                     "the value's own bytes with 0xff for a negative value; TarUtilsTest testReadNegativeBinary12Byte reads "
                     "-3601 from ff ff ff ff ff ff ff ff ff ff f1 ef, and testOldEntryStarMode expects a negative 12-byte "
                     "modification time to start with 0xff. The gold's javadoc promises that the remaining bytes hold the "
                     "number, which the 12-byte field written for 0xff00000000000001 does not.",
 "ownership_tests": ["org.apache.commons.compress.archivers.tar.TarUtilsTest::testReadNegativeBinary12Byte",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testReadNegativeBinary8Byte",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testRoundTripOctalOrBinary8",
                     "org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testOldEntryStarMode"],
 "compensating": {
   "chain": [
     {"file": BZ2, "old": "if (length < 9 && Math.abs(value) >= 1L << 8 * (length - 1)) {",
      "new": "if (Math.abs(value) >= 1L << Math.min(8 * (length - 1), Long.SIZE - 2)) {",
      "why": "hop 2 also rejects a magnitude of 2^62 or more in a field of nine or more bytes"},
     {"file": ZAIS, "old": "TarArchiveEntry.encodeBinaryNumber(value, buf, offset, length);",
      "new": "TarArchiveEntry.encodeBinaryNumber(value, buf, offset + Math.max(0, length - 9), Math.min(length, 9));",
      "why": "hop 4 writes only the last nine bytes of a longer field"},
     {"file": ZAOS, "old": "final long octalLimit = length == TarConstants.UIDLEN ? TarConstants.MAXID : TarConstants.MAXSIZE;",
      "new": "final long octalLimit = TarConstants.MAXSIZE;",
      "why": "hop 1 uses the MAXSIZE octal limit for every field"},
   ],
 },
 "host_notes": "host_mode largest5 (batch6_tasks.json: 1 other public class of >= 1500 lines). Hosts are exactly hosts_hop_order: "
               "archivers.zip.ZipArchiveOutputStream 1504 lines (hop 1), compressors.bzip2.BZip2CompressorOutputStream 1329 "
               "(hop 2), archivers.zip.ZipFile 1083 (hop 3), archivers.zip.ZipArchiveInputStream 1074 (hop 4), "
               "archivers.tar.TarArchiveEntry 1073 (hop 5, gold); smallest host 1073 lines. All five are public concrete "
               "top-level classes in which a static method compiles; none substituted. Anchors (stageB_lib.pick_anchor, seed "
               "4521 + 100 + i): after setFallbackToUTF8 (line idx 347, seed 4621), after the BZip2CompressorOutputStream(OutputStream) "
               "constructor (357, 4622), after the ZipFile(File, String) constructor (193, 4623), after getNextZipEntry (290, "
               "4624), after getMode (575, 4625); every anchor is an outer-class member. The facade calls hop 1 by its "
               "fully-qualified name; hop 1 imports TarConstants, TarUtils and the next host; hops 2 and 4 import the next host; "
               "hop 3 and hop 4 share the zip package.",
}
