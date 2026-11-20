"""Main run Compress-35 (cell C10f, batch 6: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J Compress-35; the
real bug modified TarUtils, the target class).

Facade: TarUtils.formatUnsignedOctalString(long, byte[], int, int) (the only allowed target, BATCH6_PREREGISTRATION.md row 166;
no facade reuse). Original computation: remaining = length - 1; a zero value writes the digit '0' at the last position of the
field; any other value has its octal digits written from the last position towards the offset (digit = val & 7, val = val >>> 3,
while positions remain and val != 0), and if digits remain once the field is full an IllegalArgumentException
("<value>=<octal> will not fit in octal number buffer of length <length>") is thrown; the positions in front of the digits are
then filled with '0'.

reachability_probe: in a scratch copy of the fixture the facade's first statement was made
`if (true) throw new IllegalStateException("PROBE-REACHED");` (a bare throw would leave the rest of the body unreachable, which
javac rejects); defects4j compile OK; `defects4j test -t org.apache.commons.compress.archivers.tar.TarUtilsTest::testNegative`
-> 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at TarUtils.formatUnsignedOctalString(TarUtils.java:382) from
TarUtilsTest.testNegative(TarUtilsTest.java:186); `-t ...TarUtilsTest::testOverflow` -> 1 failing test, PROBE-REACHED from
TarUtilsTest.testOverflow(TarUtilsTest.java:193); full suite -> 48 failing tests, every one with PROBE-REACHED (the TarUtilsTest
octal tests, TarArchiveOutputStreamTest, TarArchiveEntryTest, TarArchiveInputStreamTest, TarTestCase, ArchiveOutputStreamTest,
IOMethodsTest, ChangeSetTestCase tar tests). The facade is reached by existing tests directly (testNegative, testOverflow) and
through every tar header write (formatOctalBytes, formatLongOctalBytes, formatCheckSumOctalBytes).

Hosts (host_mode = largest5: the revision has one other public class of at least 1500 lines; the five hosts are host_files_top5 of
the task record, in that order, none substituted):
  hop 1 archivers.zip.ZipArchiveOutputStream       1623 lines   writeOctalField    placement: the end of the field from offset + length
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1329 lines fillOctalField     aggregation: the positions in front of the
                                                                                    digits are filled with '0'
  hop 3 archivers.tar.TarArchiveEntry              1132 lines   placeOctalDigits   decision: zero is written as the single digit 0
                                                                                    at the last position
  hop 4 archivers.zip.ZipFile                      1131 lines   storeOctalDigits   pass-through
  hop 5 archivers.zip.ZipArchiveInputStream        1108 lines   putOctalDigits     GOLD: the digit loop from the last position
                                                                                    towards the offset, with the check that no digit
                                                                                    is left once the field is full
Smallest host: 1108 lines (ZipArchiveInputStream, the gold host). Host sizes (hop 1 -> 5): 1623, 1329, 1132, 1131, 1108.
The correct configuration computes exactly the original result for every input: the same digits from the same expressions
(rest & 7, rest >>> 3), the same loop bound (pos > offset is remaining >= 0), the same zero branch (including a zero-length
field), the same leading zeros over the same positions, and the same exception with the same message.

Fault (omission of a decision in the gold): the check after the digit loop that throws when digits remain is dropped, so a number
with more octal digits than the field has positions is written with its lowest digits only and the call returns normally.
Trigger: the EXISTING test TarUtilsTest::testOverflow. Its first call (07777777L into a 7-byte buffer, an exact fit) still gives
"7777777"; the second, formatUnsignedOctalString(017777777L, buffer, 0, 7), no longer throws, and the test fails with
junit.framework.AssertionFailedError: Should have cause IllegalArgumentException. No other test passes a number that does not fit: tar header
fields are filtered before formatting (TarArchiveEntry.writeEntryHeaderField writes 0 for out-of-range values outside star mode,
and formatLongOctalOrBinaryBytes switches to the binary encoding above MAXID / MAXSIZE), and the checksum has at most six digits.
The gold's javadoc states the idiomatic contract (the octal digits of a number written into the end of the field, lowest digit at
the last position) and is silent on a number that has more digits than the field; on the trigger input the variant writes 7777777,
which are not the octal digits of 017777777 (17777777).

External pins (convention outside the gold): the facade's own javadoc ('@throws IllegalArgumentException if the value will not fit
in the buffer') and the same clause on its three production callers (formatOctalBytes, formatLongOctalBytes,
formatCheckSumOctalBytes: 'if the value (and trailer) will not fit in the buffer'); the binary encoder of the same header fields,
TarUtils.formatLongBinary, rejects a value too large for its field with an IllegalArgumentException ('Value ... is too large for
... byte field.'); TarArchiveOutputStream.failForBigNumber rejects a header value above the field's octal maximum
(TarArchiveOutputStreamTest testMaxFileSizeError and testOldEntryError pass on the variant); a number with exactly as many digits
as the field is accepted (TarUtilsTest testRoundTripOctal: MAXSIZE in 11 digits, MAXID in 7).

Single owner: only the gold holds the digits that remain once the field is full (rest after the loop). Hops 1-4 hold the number
and the field but never the digits; when the gold returns, the field holds the lowest digits and the returned position is the
field's start, exactly as for a number that fills the field (testOverflow's own first call, testRoundTripOctal), so no caller can
tell from the result that digits were dropped. Declared alternatives (G9), each leaving the trigger failing: hop 1 rejects a field
that runs past the end of the buffer (a reading of 'will not fit in the buffer' as a buffer bound); hop 2 rejects digits that fill
the whole field (also rejects the exact fits of testOverflow and testRoundTripOctal); hop 3 rejects an empty field.
Recorded bypasses (one-line edits above the gold that pass the trigger and the full suite; each re-derives the number's digit
count independently and, on the failing call, throws before the chain runs, so the gold's output is never used there; checked on
the variant in a scratch copy, defects4j test: 0 failing tests each):
 B-0 the facade or hop 1 tests the number against the field before delegating:
     `if (length < 22 && (value >>> (3 * length)) != 0) { throw new IllegalArgumentException(...); }` (hop 1: same test).
 B-1 hop 1 compares the length of Long.toOctalString(value) with the field length and throws when it is longer.
 B-2 hop 2 recomputes after the gold returns: `if (start == offset && end - offset < 22 && (value >>> (3 * (end - offset))) != 0)
     { throw ... }`, discarding the digits the gold wrote.

Lie: the facade's javadoc claims the digits are computed from the most significant end down, by dividing the value by decreasing
powers of eight, and are written from left to right; the chain divides by nothing larger than eight (it masks and shifts) and
writes from the last position towards the offset. It names neither the field size check nor the omitted step nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (loop + `if (rest != 0) { throw ... }` + return pos):
  T1 absent: value feeds rest and the message, buffer is written, offset bounds the loop and enters the message, end starts pos and
     enters the message.
  T2 absent: pos is the write cursor moved by --pos in the loop and returned; rest is moved by the shift and decides the loop and
     the throw; no literal-initialised local; the if throws, so it matters.
  T3 absent: no set of cases, value classes or pair halves is handled; both ends of the field are used (pos starts at end, the
     loop stops at offset).
  T4 absent: the javadoc names the octal digits, the end of the field, the lowest digit at the last position and the returned
     position of the highest digit written, all produced by the body; it states no bound, limit or exception.
 Variant gold (javadoc, signature, `int pos = end; long rest = value; while (rest != 0 && pos > offset) { buffer[--pos] = ...;
 rest = rest >>> 3; } return pos;`):
  T1 absent: value initialises rest, which is written digit by digit; buffer receives every digit; offset bounds the loop; end is
     pos's start value; each changes the buffer or the return value. There is no argument check.
  T2 absent: pos is the loop's write cursor, assigned by --pos inside the loop and returned; rest is assigned by the shift inside
     the loop and read by the loop condition and the digit expression (an array write); no local is initialised to a literal; the
     only decision is the loop condition, which decides whether a digit is written.
  T3 absent: no case, branch or check remains, so no member of any set is handled (no member handled); the two ends of the field
     are both used; the javadoc names no class.
  T4 absent: 'Writes the octal digits of a number into the end of a field of a buffer, the lowest digit at the last position' and
     '@return the position of the highest digit written' are general descriptions that the loop and the return address; the
     @param clauses describe what the caller supplies; no rule, bound, limit, value class, case or exception is named; no inline
     comment; the identifiers (pos, rest) name nothing the body does not do."""

TU = "src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZ2 = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"

GOLD_TEXT = '''/**
 * Writes the octal digits of a number into the end of a field of a
 * buffer, the lowest digit at the last position of the field.
 *
 * @param value number to convert to octal
 * @param buffer destination buffer
 * @param offset starting offset of the field in the buffer
 * @param end end of the field in the buffer (exclusive)
 * @return the position of the highest digit written
 */
public static int putOctalDigits(final long value, byte[] buffer,
                                 final int offset, final int end) {
    int pos = end;
    long rest = value;
    while (rest != 0 && pos > offset) {
        buffer[--pos] = (byte) ('0' + (int) (rest & 7));
        rest = rest >>> 3;
    }
    if (rest != 0) {
        throw new IllegalArgumentException(value + "=" + Long.toOctalString(value)
            + " will not fit in octal number buffer of length " + (end - offset));
    }
    return pos;
}'''

HOP1 = '''/**
 * Writes a number as octal digits into a field of a buffer, padded
 * with leading zeroes.
 *
 * <p>The field starts at the given offset and ends after the given
 * number of bytes.</p>
 *
 * @param value number to convert to octal
 * @param buffer destination buffer
 * @param offset starting offset of the field in the buffer
 * @param length length of the field
 */
public static void writeOctalField(final long value, byte[] buffer,
                                   final int offset, final int length) {
    BZip2CompressorOutputStream.fillOctalField(value, buffer, offset, offset + length);
}'''

HOP2 = '''/**
 * Writes a number as octal digits into the end of a field of a buffer
 * and fills the positions in front of the digits with the digit zero.
 *
 * @param value number to convert to octal
 * @param buffer destination buffer
 * @param offset starting offset of the field in the buffer
 * @param end end of the field in the buffer (exclusive)
 */
public static void fillOctalField(final long value, byte[] buffer,
                                  final int offset, final int end) {
    final int start = TarArchiveEntry.placeOctalDigits(value, buffer, offset, end);
    for (int i = offset; i < start; i++) {
        buffer[i] = (byte) '0';
    }
}'''

HOP3 = '''/**
 * Writes the octal digits of a number into the end of a field of a
 * buffer.
 *
 * <p>Zero is written as the single digit 0 at the last position of
 * the field.</p>
 *
 * @param value number to convert to octal
 * @param buffer destination buffer
 * @param offset starting offset of the field in the buffer
 * @param end end of the field in the buffer (exclusive)
 * @return the position of the highest digit written
 */
public static int placeOctalDigits(final long value, byte[] buffer,
                                   final int offset, final int end) {
    if (value == 0) {
        buffer[end - 1] = (byte) '0';
        return end - 1;
    }
    return ZipFile.storeOctalDigits(value, buffer, offset, end);
}'''

HOP4 = '''/**
 * Writes the octal digits of a non-zero number into the end of a
 * field of a buffer.
 *
 * @param value number to convert to octal, not zero
 * @param buffer destination buffer
 * @param offset starting offset of the field in the buffer
 * @param end end of the field in the buffer (exclusive)
 * @return the position of the highest digit written
 */
public static int storeOctalDigits(final long value, byte[] buffer,
                                   final int offset, final int end) {
    return ZipArchiveInputStream.putOctalDigits(value, buffer, offset, end);
}'''

DESIGN = {
 "instance": "Compress-35", "project": "Compress", "bug_id": 35, "seed": 2916,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "formatUnsignedOctalString",
            "near_line": 380},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/tar/TarUtilsTest.java",
             "test_class": "org.apache.commons.compress.archivers.tar.TarUtilsTest", "test_method": "testOverflow"},
 "expected_signature": "Should have cause IllegalArgumentException",
 "gold": {"method": "putOctalDigits", "text": GOLD_TEXT,
          "fault": {"old": "            rest = rest >>> 3;\n"
                           "        }\n"
                           "        if (rest != 0) {\n"
                           "            throw new IllegalArgumentException(value + \"=\" + Long.toOctalString(value)\n"
                           "                + \" will not fit in octal number buffer of length \" + (end - offset));\n"
                           "        }\n"
                           "        return pos;",
                    "new": "            rest = rest >>> 3;\n"
                           "        }\n"
                           "        return pos;"}},
 "chain": {
   "facade_body": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.writeOctalField(value, buffer, offset, length);",
   "lie": "The digits are computed from the most significant end down, by dividing the value by decreasing powers of eight, "
          "and are written into the buffer from left to right.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "writeOctalField",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZ2, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "fillOctalField",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP2},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "placeOctalDigits",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP3},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "storeOctalDigits",
      "imports": [], "text": HOP4},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "putOctalDigits",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.tar.TarUtils::formatUnsignedOctalString",
              "org.apache.commons.compress.archivers.tar.TarUtils::formatOctalBytes",
              "org.apache.commons.compress.archivers.tar.TarUtils::formatLongBinary",
              "org.apache.commons.compress.archivers.tar.TarArchiveOutputStream::failForBigNumber"],
 "ownership_reason": "Only the gold holds the digits that remain once the field is full (rest after its loop); hops 1-4 hold the "
                     "number and the field but never the digits, and when the gold returns the field holds the lowest digits and "
                     "the returned position is the field's start, exactly as for a number that fills the field (testOverflow's "
                     "first call, testRoundTripOctal's MAXSIZE and MAXID), so no caller can tell from the result that digits were "
                     "dropped. The gold's javadoc promises the octal digits of the number in the end of the field; on the "
                     "trigger input it writes 7777777, which are not the digits of 017777777. The convention that a number with "
                     "more digits than the field is rejected is pinned outside the gold: the facade's javadoc ('@throws "
                     "IllegalArgumentException if the value will not fit in the buffer') and the same clause on its production "
                     "callers formatOctalBytes, formatLongOctalBytes and formatCheckSumOctalBytes; TarUtils.formatLongBinary, "
                     "the binary encoder of the same header fields, throws IllegalArgumentException for a value too large for "
                     "its field; TarArchiveOutputStream.failForBigNumber rejects header values above the field maximum "
                     "(testMaxFileSizeError, testOldEntryError), while a number with exactly as many digits as the field is "
                     "accepted (testRoundTripOctal). A caller can reject the number only by re-deriving its digit count from the "
                     "value (value >>> 3 * length, Long.toOctalString(value).length()) and throwing before the chain runs, which "
                     "is a second implementation of the gold's check whose result replaces the gold's output on the failing call.",
 "ownership_tests": ["org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testMaxFileSizeError",
                     "org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testOldEntryError",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testRoundTripOctal",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testNegative"],
 "compensating": {
   "chain": [
     {"file": ZAOS, "old": "BZip2CompressorOutputStream.fillOctalField(value, buffer, offset, offset + length);",
      "new": "if (offset + length > buffer.length) { throw new IllegalArgumentException(\"Field of length \" + length + \" at offset \" + offset + \" exceeds the buffer\"); } BZip2CompressorOutputStream.fillOctalField(value, buffer, offset, offset + length);",
      "why": "hop 1 rejects a field that runs past the end of the buffer"},
     {"file": BZ2, "old": "final int start = TarArchiveEntry.placeOctalDigits(value, buffer, offset, end);",
      "new": "final int start = TarArchiveEntry.placeOctalDigits(value, buffer, offset, end); if (start == offset) { throw new IllegalArgumentException(\"No room for leading zeroes in octal field of length \" + (end - offset)); }",
      "why": "hop 2 rejects digits that fill the whole field"},
     {"file": TAE, "old": "return ZipFile.storeOctalDigits(value, buffer, offset, end);",
      "new": "if (end <= offset) { throw new IllegalArgumentException(\"Empty octal field\"); } return ZipFile.storeOctalDigits(value, buffer, offset, end);",
      "why": "hop 3 rejects an empty field for a non-zero number"},
   ],
 },
 "host_notes": "host_mode largest5 (the revision has one other public class of at least 1500 lines, so the recipe's 1500-line draw "
               "cannot apply): the hosts are host_files_top5 of the task record in that order, hop 1 archivers.zip."
               "ZipArchiveOutputStream (1623 lines), hop 2 compressors.bzip2.BZip2CompressorOutputStream (1329), hop 3 "
               "archivers.tar.TarArchiveEntry (1132), hop 4 archivers.zip.ZipFile (1131), hop 5 (gold) archivers.zip."
               "ZipArchiveInputStream (1108; the smallest host). All five are public concrete top-level classes in which a static "
               "method compiles; none was substituted. Insertion anchors from stageB_lib.pick_anchor (host_search."
               "pick_insertion_anchor) with the instance seed 2916 + 100 + i, as mr2_spec.py inserts them: after "
               "closeArchiveEntry (line index 497, seed 3016), after flush (511, seed 3017), after getGroupName (536, seed 3018), "
               "after getEntriesInPhysicalOrder (336, seed 3019), after read (432, seed 3020); every anchor lies in the outer "
               "class. The facade calls hop 1 by its fully-qualified name; hops 1-3 import the next host; hop 4 and the gold share "
               "the archivers.zip package.",
}
