"""Main run Compress-45, cell C10f (C10 recipe with fallback hosts) on the fixed checkout of Defects4J Compress-45; the real bug
modified TarUtils, the target class.

Facade: TarUtils.parseOctal(byte[], int, int) (the only allowed target, BATCH6_PREREGISTRATION.md row 169).
Original computation of the facade: a length below 2 gives IllegalArgumentException; a field whose first byte is a NUL gives 0;
leading spaces are skipped; trailing NULs and spaces are trimmed from the end; every remaining byte must be '0'..'7' (otherwise
IllegalArgumentException, which also catches a NUL or space embedded in the number) and is accumulated as an octal digit.

reachability_probe: in a scratch copy of the fixture the first statement of parseOctal became
`if (buffer != null) { throw new IllegalStateException("PROBE-REACHED"); }` (a bare throw would make the rest of the body an
unreachable statement, which javac rejects); defects4j compile OK; `defects4j test -t
org.apache.commons.compress.archivers.tar.TarUtilsTest::testParseOctal` -> 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at TarUtils.parseOctal(TarUtils.java:105) called from TarUtilsTest.testParseOctal(TarUtilsTest.java:59). The full
suite on the probe copy has 61 failing tests (every tar reader test reaches the facade through TarArchiveEntry.parseTarHeader,
parseOctalOrBinary and verifyCheckSum); the pristine fixture has 0 failing tests. Reachability confirmed.

Hosts (host_mode = largest5: the fixed revision has only one other public class of at least 1500 lines, so the hosts are the five
largest public non-interface non-enum classes other than TarUtils, by newline count, hop 1 in the largest), exactly
hosts_hop_order of the task record, none substituted:
  hop 1 archivers.zip.ZipArchiveOutputStream       1686 lines  decision: a field that starts with a NUL gives 0; computes the
                                                                field end (offset + length)
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1334 lines placement: skips the leading spaces
  hop 3 archivers.tar.TarArchiveEntry              1259 lines  placement: the number ends at the first NUL or space of the field
  hop 4 archivers.zip.ZipFile                      1258 lines  decision: only NULs and spaces may follow the number (any other
                                                                byte there gives IllegalArgumentException)
  hop 5 archivers.zip.ZipArchiveInputStream        1136 lines  GOLD: the per-byte core, every byte of the number checked to be
                                                                an octal digit and accumulated
host_lines = [1686, 1334, 1259, 1258, 1136]; smallest host 1136 lines (the gold host).
The correct configuration returns the original value for every input and throws IllegalArgumentException on exactly the inputs
the original rejects: a byte that is not '0'..'7' before the first NUL or space is rejected by the gold, and a NUL or space
embedded in the number (the original's other invalid-byte case) is equivalent to a non-separator byte after the first NUL or
space, which hop 4 rejects. Only the wording of the exception message differs from the original's private exceptionMessage
helper (no test reads it); that helper is left in TarUtils unused. Checked by a differential run in a scratch copy of the
correct configuration: 4,000,000 random (buffer, offset, length) cases over digit, NUL, space, letter, sign and 0xff bytes,
comparing the original algorithm with the chain (value, or exception class): 0 differences.

Fault (one-line omission in the gold, the per-byte digit check): the `if (currentByte < '0' || currentByte > '7') { throw ... }`
step is dropped, so a byte that is not an octal digit is accumulated as if it were one. The gold then reads as the textbook
octal accumulation loop. Trigger: the EXISTING test TarUtilsTest::testParseOctalInvalid. Its two length checks still throw in
the facade guard; its third case, "abcdef " (letters followed by a space), is no longer rejected, and the test fails at
fail("Expected IllegalArgumentException") with junit.framework.AssertionFailedError: Expected IllegalArgumentException. Its
embedded-space and embedded-NUL cases (and COMPRESS-178.tar, whose gid field "00\\0" + "0765\\0" has an embedded NUL) are still
rejected by hop 4, so TarTestCase::testCOMPRESS178 passes and the trigger is the only newly failing test. Mutation screening on
the original method showed why the check is split this way: dropping the whole original check fails testParseOctalInvalid and
testCOMPRESS178; the leading-NUL rule, the leading-space skip and the trailer trim each fail 3 to 55 tests.

The gold's javadoc states the idiomatic contract (parses the octal number held in the bytes from start to end) and is silent on
the digit check; "abcdef" holds no octal number, so the variant violates that contract on the trigger input. External pins: the
facade's own javadoc ('@throws IllegalArgumentException if ... a invalid byte is detected'); the sibling
TarUtils.parseOctalOrBinary ('an invalid byte is detected in an octal number'); the other archive formats' octal header fields:
CpioArchiveInputStream.readAsciiLong reads the old ASCII cpio fields with Long.parseLong(..., 8) and ArArchiveInputStream.asInt
reads the ar file mode with Integer.parseInt(..., 8), both of which reject a non-octal digit with NumberFormatException, an
IllegalArgumentException; passing tests: TarTestCase::testCOMPRESS178 (an invalid byte in a tar header field surfaces as an
IllegalArgumentException cause), TarUtilsTest::testParseOctal, ::testParseOctalCompress330, ::testRoundTripOctal,
ArTestCase::testArUnarchive.

Single owner: only the gold looks at the bytes of the number one by one; hop 1 tests one byte (the first), hop 2 moves past
spaces, hop 3 locates the first NUL or space, hop 4 tests only the bytes after the number. Once the gold has folded a letter into
the value no caller can tell, since every byte pattern of the number yields some long. Declared alternatives (G9): hop 2 also
skips leading NULs; hop 3 ends the number at any control byte or space; hop 4 also requires the trailing NUL or space that the
facade's javadoc mentions. None changes the trigger's "abcdef " case.
Recorded one-line edits above the gold (each applied to the variant in a scratch copy: trigger passes, defects4j test reports
0 failing tests; a further hop-1 alternative, a first byte above '7' giving 0, and the declared hop-2 alternative were also
screened there and leave the trigger failing):
 B-0 bypass: hop 4 returns `stop == start ? 0L : Long.parseLong(new String(buffer, start, stop - start,
     java.nio.charset.StandardCharsets.US_ASCII), 8)` instead of calling the gold, replacing the gold's result with another
     implementation (and accepting a leading sign the original rejects).
 B-1 second implementation: hop 4 checks the bytes of the number itself before calling the gold
     (`for (int k = start; k < stop; k++) { if (buffer[k] < '0' || buffer[k] > '7') { throw new IllegalArgumentException(...); } }`);
     on the trigger input the gold is never reached; it duplicates the gold's per-byte step at a hop whose documented role is
     the bytes after the number.
 B-2 not doc-consistent: hop 3 ends the number at the first byte that is not an octal digit
     (`while (stop < end && buffer[stop] >= '0' && buffer[stop] <= '7') {`), so hop 4 then rejects the letters as bytes after
     the number. It contradicts hop 3's documented rule (the number ends at the first NUL or space of the field: for "abcdef "
     that is index 6, the edit ends it at index 0) and hop 4's documented input (the number followed by its trailer).

Lie: the facade's javadoc claims the digits are read from the last one towards the first and each digit is multiplied by the
matching power of eight before it is added to the result; the chain reads the digits first to last and shifts the running value.
It names neither the digit check nor invalid bytes nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: buffer is read for every byte; start and end bound the loop; all three decide the return value.
  T2 absent: result is reassigned in the loop and returned; i is advanced by the for header; currentByte is assigned per
     iteration and read by the check and the accumulation; the single if throws, so it matters.
  T3 absent: the check covers both ends of the digit range ('0' and '7'); no other set, pair or named class.
  T4 absent: the javadoc names only the octal number held in the bytes from start to end; no limit, case or value class.
 Variant gold (javadoc, signature, `long result = 0; for (int i = start; i < end; i++) { final byte currentByte = buffer[i];
 result = (result << 3) + (currentByte - '0'); } return result;`):
  T1 absent: buffer is read for every byte, start and end bound the loop; each changes the returned value; there is no argument
     check.
  T2 absent: result is literal-initialised but reassigned in every iteration and returned; i is advanced by the for header;
     currentByte is assigned per iteration and read by the accumulation; no flag, cursor or best-so-far; no branch, case or
     ternary remains.
  T3 absent: no byte class is tested at all (no member handled); no pair of halves or range ends of which one is treated; the
     gold's text names no class that it handles in part.
  T4 absent: 'Parses the octal number held in the bytes from start to end of a buffer' and '@return the value of the number'
     are general descriptions that the loop addresses; the @param clauses describe what the caller supplies; no inline comment;
     the identifiers (result, currentByte, i) name nothing the body does not meet."""

TU = "src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZ2 = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"

GOLD_TEXT = '''/**
 * Parses the octal number held in the bytes from start to end of a
 * buffer.
 *
 * @param buffer the buffer holding the number
 * @param start the index of the first byte of the number
 * @param end the index after the last byte of the number
 * @return the value of the number
 */
public static long octalNumberValue(final byte[] buffer, final int start, final int end) {
    long result = 0;
    for (int i = start; i < end; i++) {
        final byte currentByte = buffer[i];
        if (currentByte < '0' || currentByte > '7') {
            throw new IllegalArgumentException("Invalid byte " + currentByte + " at index " + i);
        }
        result = (result << 3) + (currentByte - '0');
    }
    return result;
}'''

HOP1 = '''/**
 * Parses the octal number held in a header field.
 *
 * <p>A field whose first byte is a NUL holds no number and gives
 * 0.</p>
 *
 * @param buffer the buffer holding the field
 * @param offset the offset of the field in the buffer
 * @param length the length of the field
 * @return the value of the field
 */
public static long valueOfOctalField(final byte[] buffer, final int offset, final int length) {
    if (buffer[offset] == 0) {
        return 0L;
    }
    return BZip2CompressorOutputStream.valueAfterLeadingSpaces(buffer, offset, offset + length);
}'''

HOP2 = '''/**
 * Parses the octal number held in the bytes from start to end of a
 * buffer, after any leading spaces.
 *
 * <p>Leading spaces are skipped.</p>
 *
 * @param buffer the buffer holding the field
 * @param start the index of the first byte of the field
 * @param end the index after the last byte of the field
 * @return the value of the field
 */
public static long valueAfterLeadingSpaces(final byte[] buffer, final int start, final int end) {
    int first = start;
    while (first < end && buffer[first] == ' ') {
        first++;
    }
    return TarArchiveEntry.valueOfLeadingNumber(buffer, first, end);
}'''

HOP3 = '''/**
 * Parses the octal number at the start of a field.
 *
 * <p>The number ends at the first NUL or space of the field, or at
 * the end of the field if the field holds neither.</p>
 *
 * @param buffer the buffer holding the field
 * @param start the index of the first byte of the number
 * @param end the index after the last byte of the field
 * @return the value of the number
 */
public static long valueOfLeadingNumber(final byte[] buffer, final int start, final int end) {
    int stop = start;
    while (stop < end && buffer[stop] != 0 && buffer[stop] != ' ') {
        stop++;
    }
    return ZipFile.valueBeforeTrailer(buffer, start, stop, end);
}'''

HOP4 = '''/**
 * Parses the octal number of a field in which the number is followed
 * by its trailing NULs and spaces.
 *
 * <p>Only NULs and spaces may follow the number; any other byte
 * between the number and the end of the field gives an
 * IllegalArgumentException.</p>
 *
 * @param buffer the buffer holding the field
 * @param start the index of the first byte of the number
 * @param stop the index after the last byte of the number
 * @param end the index after the last byte of the field
 * @return the value of the number
 */
public static long valueBeforeTrailer(final byte[] buffer, final int start, final int stop, final int end) {
    for (int i = stop; i < end; i++) {
        if (buffer[i] != 0 && buffer[i] != ' ') {
            throw new IllegalArgumentException("Invalid byte " + buffer[i] + " at index " + i);
        }
    }
    return ZipArchiveInputStream.octalNumberValue(buffer, start, stop);
}'''

DESIGN = {
 "instance": "Compress-45", "project": "Compress", "bug_id": 45, "seed": 3395,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "parseOctal", "near_line": 104},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/tar/TarUtilsTest.java",
             "test_class": "org.apache.commons.compress.archivers.tar.TarUtilsTest",
             "test_method": "testParseOctalInvalid"},
 "expected_signature": "AssertionFailedError: Expected IllegalArgumentException",
 "gold": {"method": "octalNumberValue", "text": GOLD_TEXT,
          "fault": {"old": "            final byte currentByte = buffer[i];\n"
                           "            if (currentByte < '0' || currentByte > '7') {\n"
                           "                throw new IllegalArgumentException(\"Invalid byte \" + currentByte + \" at index \" + i);\n"
                           "            }\n"
                           "            result = (result << 3) + (currentByte - '0');",
                    "new": "            final byte currentByte = buffer[i];\n"
                           "            result = (result << 3) + (currentByte - '0');"}},
 "chain": {
   "facade_body": "if (length < 2){\n"
                  "            throw new IllegalArgumentException(\"Length \"+length+\" must be at least 2\");\n"
                  "        }\n"
                  "        return org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.valueOfOctalField(buffer, offset, length);",
   "lie": "The digits are read from the last one towards the first, and each digit is multiplied by the matching power of "
          "eight before it is added to the result.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "valueOfOctalField",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZ2, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream",
      "method": "valueAfterLeadingSpaces",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP2},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "valueOfLeadingNumber",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP3},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "valueBeforeTrailer",
      "imports": [], "text": HOP4},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "octalNumberValue",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.tar.TarUtils::parseOctalOrBinary",
              "org.apache.commons.compress.archivers.cpio.CpioArchiveInputStream::readAsciiLong",
              "org.apache.commons.compress.archivers.ar.ArArchiveInputStream::asInt"],
 "ownership_reason": "Only the gold looks at the bytes of the number one by one: hop 1 tests the first byte of the field for a "
                     "NUL, hop 2 moves past the leading spaces, hop 3 locates the first NUL or space, and hop 4 tests only the "
                     "bytes after the number; once the gold has folded a byte that is not an octal digit into the value, no "
                     "caller can tell, since every byte pattern yields some long. The convention is pinned outside the gold: "
                     "the facade's javadoc ('@throws IllegalArgumentException if ... a invalid byte is detected') and the "
                     "sibling TarUtils.parseOctalOrBinary ('an invalid byte is detected in an octal number'); the octal header "
                     "fields of the other archive formats are read with radix-8 parsers that reject a non-octal digit with "
                     "NumberFormatException, an IllegalArgumentException (CpioArchiveInputStream.readAsciiLong for the old "
                     "ASCII cpio fields, ArArchiveInputStream.asInt for the ar file mode); TarTestCase testCOMPRESS178 passes "
                     "and requires an invalid byte in a tar header field to surface as an IllegalArgumentException cause. The "
                     "gold's javadoc promises the octal number held in the bytes, which \"abcdef\" is not. A hop above the gold "
                     "can only re-do the digit check itself (a second implementation of the gold's step, on the trigger input "
                     "the gold is then never reached) or end the number at the first non-digit at hop 3, which contradicts "
                     "hop 3's documented rule that the number ends at the first NUL or space of the field.",
 "ownership_tests": ["org.apache.commons.compress.archivers.TarTestCase::testCOMPRESS178",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testParseOctal",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testParseOctalCompress330",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testRoundTripOctal",
                     "org.apache.commons.compress.archivers.ArTestCase::testArUnarchive"],
 "compensating": {
   "chain": [
     {"file": BZ2, "old": "        while (first < end && buffer[first] == ' ') {",
      "new": "        while (first < end && (buffer[first] == ' ' || buffer[first] == 0)) {",
      "why": "hop 2 also skips leading NULs"},
     {"file": TAE, "old": "        while (stop < end && buffer[stop] != 0 && buffer[stop] != ' ') {",
      "new": "        while (stop < end && buffer[stop] > ' ') {",
      "why": "hop 3 ends the number at any control byte or space"},
     {"file": ZF, "old": "        for (int i = stop; i < end; i++) {\n            if (buffer[i] != 0 && buffer[i] != ' ') {",
      "new": "        if (stop == end) { throw new IllegalArgumentException(\"Missing trailer at index \" + end); }\n"
             "        for (int i = stop; i < end; i++) {\n            if (buffer[i] != 0 && buffer[i] != ' ') {",
      "why": "hop 4 also requires the trailing NUL or space that the facade's javadoc mentions"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 1): the hosts are hosts_hop_order of the task record, the five largest public "
               "non-interface non-enum classes other than TarUtils, in that order, none substituted: "
               "archivers.zip.ZipArchiveOutputStream (hop 1, 1686 lines), compressors.bzip2.BZip2CompressorOutputStream (hop 2, "
               "1334), archivers.tar.TarArchiveEntry (hop 3, 1259), archivers.zip.ZipFile (hop 4, 1258), "
               "archivers.zip.ZipArchiveInputStream (hop 5, gold, 1136); smallest host 1136 lines. All five are public concrete "
               "classes in which a static method compiles. Anchors (stageB_lib.pick_insertion_anchor via pick_anchor, seeds "
               "3395 + 100 + i, matching the task record): after putArchiveEntry (line 728, seed 3495), after the "
               "BZip2CompressorOutputStream constructor (line 392, seed 3496), after isGlobalPaxHeader (line 845, seed 3497), "
               "after getEntriesInPhysicalOrder (line 409, seed 3498), after the ZipArchiveInputStream constructor (line 192, "
               "seed 3499); all in the outer class. The facade calls hop 1 by its fully-qualified name; hops 1-3 import the next "
               "host; hop 4 and the gold share the zip package. The facade's private exceptionMessage helper in TarUtils is "
               "left in place, unused.",
}
