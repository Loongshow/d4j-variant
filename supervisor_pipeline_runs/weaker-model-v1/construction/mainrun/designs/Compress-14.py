"""Main run Compress-14 (cell C10f: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J Compress-14; the real
bug modified TarUtils, the target class).

Facade: TarUtils.parseOctalOrBinary(byte[], int, int) (the only allowed target, BATCH6_PREREGISTRATION.md row 160; no facade
reuse). Production callers: TarArchiveEntry.parseTarHeader (user id, group id and size fields). Test callers: TarUtilsTest
(checkRoundTripOctalOrBinary) directly, and every test that reads a tar header indirectly.
Original computation of the facade: if the most significant bit of the first byte is clear, the field is an octal number and is
parsed by TarUtils.parseOctal; otherwise the marker bit is ignored, the low seven bits of the first byte are the leading value,
and every following byte is appended (val = (val << 8) + (byte & 0xff)), with an IllegalArgumentException when the value would
exceed a signed long (checked before each shift).

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2), run before designing: in a scratch copy of the fixture
(/private/tmp/cmp14-probe) the facade's first statement was made `throw new IllegalStateException("PROBE-REACHED");` (the
original body moved to a private method so the file compiles); defects4j compile OK;
`defects4j test -t org.apache.commons.compress.archivers.tar.TarUtilsTest::testRoundTripOctalOrBinary` -> Failing tests: 1,
java.lang.IllegalStateException: PROBE-REACHED at TarUtils.parseOctalOrBinary(TarUtils.java:126) <- TarUtilsTest.java:135.
The full suite with the probe: 20 failing tests, all through the facade (the trigger, plus 19 tar-reading tests through
TarArchiveEntry.parseTarHeader, among them TarArchiveOutputStreamTest::testBigFileStarMode, the only other test that takes the
binary branch). The facade is reached by existing tests: usable.

Hosts (host_mode = "largest5": the fixed revision has only 1 other public class of >= 1500 lines, so the hosts are the five
largest public, non-interface, non-enum classes other than TarUtils, hosts_hop_order of batch6_tasks.json, in that order; anchors
by stageB_lib.pick_insertion_anchor with seed 3817 + 100 + i, as mr2_spec.py inserts them; none substituted):
  hop 1 compressors.bzip2.BZip2CompressorOutputStream (1886 lines; anchor after getBlockSize, line idx 644, seed 3917)
        valueOfNumber        decision: a clear marker bit means an octal field (TarUtils.parseOctal), else the binary branch
  hop 2 archivers.zip.ZipArchiveOutputStream (1495 lines; anchor after setMethod, line idx 730, seed 3918)
        binaryNumberValue    placement: the marker bit is dropped; the low seven bits of the first byte become the leading value
  hop 3 compressors.bzip2.BZip2CompressorInputStream (1048 lines; anchor after close, line idx 374, seed 3919)
        valueOfBinary        pass-through
  hop 4 archivers.zip.ZipFile (969 lines; anchor after getEntriesInPhysicalOrder, line idx 285, seed 3920)
        binaryValue          pass-through
  hop 5 archivers.tar.TarArchiveEntry (926 lines; anchor after the TarArchiveEntry constructor ending at line idx 255, seed 3921)
        binaryValueOf        GOLD: the per-byte fold of the bytes after the first, with the per-step size check
Host sizes (covariates): 1886, 1495, 1048, 969, 926; smallest host = gold host = 926 lines.
The correct configuration returns the original result for every input: the same octal/binary decision, the same leading value
(buffer[offset] & 0x7f), the same fold (val << 8) + (byte & 0xff) over bytes 1 .. length-1, and the same exception with the same
message. The size check is written as (val >>> (63 - 8)) != 0 instead of val >= (1L << (63 - 8)); the two are equal for every
val >= 0, and val is never negative in the correct configuration (a leading value in 0..127 plus masked bytes).

Fault (one-line omission in the gold, inside its iteration): the unsigned mask of each appended byte is dropped,
`val = (val << 8) + (buffer[offset + i] & 0xff);` -> `val = (val << 8) + buffer[offset + i];`, so a byte of 0x80 or more is
added as a negative number. The gold then reads as an ordinary shift-and-add fold. Trigger: the EXISTING test
TarUtilsTest::testRoundTripOctalOrBinary. Its first two cases (0 and 1) take the octal branch and pass; the third,
checkRoundTripOctalOrBinary(Long.MAX_VALUE, 8) (bytes ff ff ff ff ff ff ff ff after formatLongOctalOrBinaryBytes), fails with
expected:<9223372036854775807> but was:<9151031864016699135> (0x7efefefefefefeff). It is the only test whose binary field has a
byte of 0x80 or more after the first: testBigFileStarMode writes the size 2^33 into a 12-byte field (80 00 00 00 00 00 00 02 00 00
00 00) and still passes; every other tar test has octal fields. The gold's javadoc states the idiomatic contract (the value of a
binary number, given the value of its first byte) and is silent on the sign of the bytes; ff ff ff ff ff ff ff ff with the marker
bit dropped is the binary number 0x7fffffffffffffff, so the variant violates that contract on the trigger input.

External pins (the convention that each byte of a binary number is taken as an unsigned 8-bit value, outside the gold):
CpioUtil.byteArray2long does the same big-endian fold (ret <<= 8; ret |= tmp_number[pos] & 0xFF), pinned by
CpioUtilTest::oldBinMagicFromByteArrayNotSwapped (byte 0xc7 after the first byte); ZipLong.getValue masks every byte, pinned by
ZipLongTest::testSign (ff ff ff ff is 0xFFFFFFFF); TarUtils.parseName masks each byte ("Allow for sign-extension"), pinned by
TarUtilsTest::testRoundTripNames (bytes 0xb1); TarUtils.formatLongOctalOrBinaryBytes writes the binary form as the 8-bit bytes
of the value with the marker bit set, which the facade must invert, and TarArchiveOutputStreamTest::testBigFileStarMode pins that
format end to end through the chain (it passes on the variant). The facade's own javadoc says the rest of the buffer "is
interpreted as a binary number".

Single owner: only the gold reads the bytes after the first one and folds them into the value. Hop 1 reads only the marker bit,
hop 2 only the first byte, hops 3 and 4 pass the buffer along; all four get back one long. A Java byte cannot carry a value of
0x80 or more as a positive number, so no caller can pre-filter the buffer so that the gold's unmasked addition comes out right,
and the gold's result is the only place the bytes are combined. Declared alternatives (G9): hop 2 keeps the marker bit in the
leading value; hop 3 masks the leading value to seven bits; hop 4 reads at most eight bytes of the number. None changes the
trigger's eight 0xff bytes.
Recorded one-line edits above the gold that pass the trigger and the full suite (each checked on the variant in a scratch copy,
defects4j test: 0 failing tests each; classification given):
 B-0 bypass: the facade or hop 1, 2, 3 or 4 computes the value itself, e.g. hop 4
     `return new java.math.BigInteger(1, java.util.Arrays.copyOfRange(buffer, offset + 1, offset + length)).add(java.math.BigInteger.valueOf(lead).shiftLeft(8 * (length - 1))).longValue();`,
     discarding the gold's result (it also drops the size check).
 B-1 test-fitted post-correction: hop 4 rewrites the gold's result with a bit trick that only undoes the unmasked addition,
     `return (TarArchiveEntry.binaryValueOf(buffer, offset, length, lead) + (0x8080808080808080L >>> (8 * (9 - length)))) ^ (0x8080808080808080L >>> (8 * (9 - length)));`
     (adding 0x80 to every appended byte position and flipping those bits back turns signed byte values into unsigned ones).
     It leaves the gold violating its own documented result and only works because of it: with the gold as documented it turns
     a correct value such as 0x7fffffffffffffff into 0x80000000000000ff; and its mask is meaningless for fields of more than
     nine bytes (Java reduces the negative shift count). Not consistent with the path: the gold is not used as documented.

Lie: the facade's javadoc claims the binary form is decoded by wrapping the buffer in a java.nio.ByteBuffer and reading the
number with a single getLong call; the chain uses no ByteBuffer and folds the bytes one at a time. It names neither the sign of a
byte, nor masking, nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold.
 Correct gold (TarArchiveEntry.binaryValueOf with the mask):
  T1 absent: buffer is read for every appended byte, offset for the index and the message, length for the bound and the message,
     lead as the initial value; each changes the returned value or the thrown exception.
  T2 absent: val starts at the parameter lead (not a literal), is assigned in the loop and returned; i is advanced by the for
     header; no flag, counter or best-so-far; the if throws or lets the fold continue, so the decision matters.
  T3 absent: every byte the gold reads gets the same treatment (masked and appended); the first byte is not read by the gold (its
     value arrives as lead); the size check is a test of the bits above the low 55, not one end of a pair of bounds (the form
     val >= (1L << 55) was rewritten to the bit test so that no one-sided bound can be quoted); no case, enum or named class.
  T4 absent: 'the value of a binary number in a byte buffer, given the value of its first byte' and '@return The long value of
     the binary number' are general descriptions that the fold addresses; '@throws IllegalArgumentException if the binary number
     would exceed the size of a signed long 64-bit integer' is met by the check before each shift; @param lines are caller
     descriptions; identifiers (val, lead, i) name nothing the body does not meet.
 Variant gold (the same text with `val = (val << 8) + buffer[offset + i];`):
  T1 absent: all four parameters are still read in the computation (buffer in the addition, offset in the index and message,
     length in the bound and message, lead as the initial value).
  T2 absent: val is assigned in the loop and returned, i advances, no literal-initialised or loop-moved local is left unassigned;
     the if is live (it throws when the value has bits above the low 55, otherwise the fold continues).
  T3 absent: no member of any set is treated while a sibling is not: no byte is masked, so 'no member handled'; there is no
     case, branch per value class, pair of halves or range ends; the gold names no class it handles in part.
  T4 absent: no phrase names a concrete rule, bound, value class or case that the body visibly does not meet: the size rule is
     checked before every shift; nothing in the javadoc mentions signed or unsigned bytes, eight bits per byte or a range of byte
     values; no inline comment."""

SRC = "src/main/java/org/apache/commons/compress/"
TU = SRC + "archivers/tar/TarUtils.java"
BZO = SRC + "compressors/bzip2/BZip2CompressorOutputStream.java"
ZAO = SRC + "archivers/zip/ZipArchiveOutputStream.java"
BZI = SRC + "compressors/bzip2/BZip2CompressorInputStream.java"
ZF = SRC + "archivers/zip/ZipFile.java"
TAE = SRC + "archivers/tar/TarArchiveEntry.java"

GOLD_TEXT = '''/**
 * Compute the value of a binary number in a byte buffer, given the
 * value of its first byte.
 *
 * @param buffer The buffer from which to parse.
 * @param offset The offset into the buffer from which to parse.
 * @param length The number of bytes to parse.
 * @param lead The value of the first byte of the number.
 * @return The long value of the binary number.
 * @throws IllegalArgumentException if the binary number would exceed
 * the size of a signed long 64-bit integer.
 */
public static long binaryValueOf(final byte[] buffer, final int offset,
                                 final int length, final long lead) {
    long val = lead;
    for (int i = 1; i < length; i++) {
        if ((val >>> (63 - 8)) != 0) {
            throw new IllegalArgumentException(
                "At offset " + offset + ", " + length + " byte " +
                "binary number exceeds maximum signed long value");
        }
        val = (val << 8) + (buffer[offset + i] & 0xff);
    }
    return val;
}'''

HOP1 = '''/**
 * Compute the value contained in a byte buffer.  If the most
 * significant bit of the first byte in the buffer is set, the
 * buffer holds a binary number.  Otherwise it holds an octal
 * number, which is parsed by {@link TarUtils#parseOctal}.
 *
 * @param buffer The buffer from which to parse.
 * @param offset The offset into the buffer from which to parse.
 * @param length The maximum number of bytes to parse.
 * @return The long value of the octal or binary string.
 */
public static long valueOfNumber(final byte[] buffer, final int offset,
                                 final int length) {
    if ((buffer[offset] & 0x80) == 0) {
        return TarUtils.parseOctal(buffer, offset, length);
    }
    return ZipArchiveOutputStream.binaryNumberValue(buffer, offset, length);
}'''

HOP2 = '''/**
 * Compute the value of a binary number in a byte buffer.  The most
 * significant bit of the first byte marks the binary form and is
 * ignored; the remaining seven bits are the value of the first byte.
 *
 * @param buffer The buffer from which to parse.
 * @param offset The offset into the buffer from which to parse.
 * @param length The number of bytes to parse.
 * @return The long value of the binary number.
 */
public static long binaryNumberValue(final byte[] buffer, final int offset,
                                     final int length) {
    return BZip2CompressorInputStream.valueOfBinary(buffer, offset, length,
                                                    buffer[offset] & 0x7f);
}'''

HOP3 = '''/**
 * Compute the value of a binary number in a byte buffer, given the
 * value of its first byte.
 *
 * @param buffer The buffer from which to parse.
 * @param offset The offset into the buffer from which to parse.
 * @param length The number of bytes to parse.
 * @param lead The value of the first byte of the number.
 * @return The long value of the binary number.
 */
public static long valueOfBinary(final byte[] buffer, final int offset,
                                 final int length, final long lead) {
    return ZipFile.binaryValue(buffer, offset, length, lead);
}'''

HOP4 = '''/**
 * Compute the value of a binary number in a byte buffer, given the
 * value of its first byte.
 *
 * @param buffer The buffer from which to parse.
 * @param offset The offset into the buffer from which to parse.
 * @param length The number of bytes to parse.
 * @param lead The value of the first byte of the number.
 * @return The long value of the binary number.
 */
public static long binaryValue(final byte[] buffer, final int offset,
                               final int length, final long lead) {
    return TarArchiveEntry.binaryValueOf(buffer, offset, length, lead);
}'''

DESIGN = {
 "instance": "Compress-14", "project": "Compress", "bug_id": 14, "seed": 3817,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "parseOctalOrBinary",
            "near_line": 124},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/tar/TarUtilsTest.java",
             "test_class": "org.apache.commons.compress.archivers.tar.TarUtilsTest",
             "test_method": "testRoundTripOctalOrBinary"},
 "expected_signature": "expected:<9223372036854775807> but was:<9151031864016699135>",
 "gold": {"method": "binaryValueOf", "text": GOLD_TEXT,
          "fault": {"old": "            val = (val << 8) + (buffer[offset + i] & 0xff);",
                    "new": "            val = (val << 8) + buffer[offset + i];"}},
 "chain": {
   "facade_body": "return org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream.valueOfNumber(buffer, offset, length);",
   "lie": "The binary form is decoded by wrapping the buffer in a java.nio.ByteBuffer and reading the number with a "
          "single getLong call.",
   "hops": [
     {"file": BZO, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream",
      "method": "valueOfNumber",
      "imports": ["org.apache.commons.compress.archivers.tar.TarUtils",
                  "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream"], "text": HOP1},
     {"file": ZAO, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream",
      "method": "binaryNumberValue",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream"], "text": HOP2},
     {"file": BZI, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream",
      "method": "valueOfBinary",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP3},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "binaryValue",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP4},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "binaryValueOf",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.cpio.CpioUtil::byteArray2long",
              "org.apache.commons.compress.archivers.zip.ZipLong::getValue",
              "org.apache.commons.compress.archivers.tar.TarUtils::parseName",
              "org.apache.commons.compress.archivers.tar.TarUtils::formatLongOctalOrBinaryBytes"],
 "ownership_reason": "Only the gold reads the bytes that follow the first byte of a binary field and folds them into the value; "
                     "hop 1 reads only the marker bit, hop 2 only the first byte (its low seven bits become the leading value), "
                     "hops 3 and 4 pass the buffer along, and all four get back one long. A Java byte cannot hold 0x80 or more "
                     "as a positive number, so no caller can prepare the buffer so that an unmasked addition of the bytes "
                     "comes out right, and the gold's result is the only place the bytes are combined. The convention that "
                     "each byte of a binary number is an unsigned 8-bit value is pinned outside the gold: CpioUtil."
                     "byteArray2long does the same big-endian fold with every byte masked (ret <<= 8; ret |= b & 0xFF; "
                     "CpioUtilTest oldBinMagicFromByteArrayNotSwapped, byte 0xc7 after the first, passes); ZipLong.getValue "
                     "masks every byte (ZipLongTest testSign: ff ff ff ff is 0xFFFFFFFF); TarUtils.parseName masks each byte "
                     "to allow for sign extension (TarUtilsTest testRoundTripNames, bytes 0xb1); TarUtils."
                     "formatLongOctalOrBinaryBytes writes the binary form as the 8-bit bytes of the value with the marker bit "
                     "set, and TarArchiveOutputStreamTest testBigFileStarMode reads such a field back through the chain. The "
                     "facade's javadoc says the rest of the buffer is interpreted as a binary number, and the gold's javadoc "
                     "promises the value of that binary number, which for ff ff ff ff ff ff ff ff with the marker bit dropped "
                     "is 0x7fffffffffffffff.",
 "ownership_tests": ["org.apache.commons.compress.archivers.cpio.CpioUtilTest::oldBinMagicFromByteArrayNotSwapped",
                     "org.apache.commons.compress.archivers.zip.ZipLongTest::testSign",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testRoundTripNames",
                     "org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testBigFileStarMode"],
 "compensating": {
   "chain": [
     {"file": ZAO, "old": "buffer[offset] & 0x7f);",
      "new": "buffer[offset] & 0xff);",
      "why": "hop 2 keeps the marker bit in the value of the first byte"},
     {"file": BZI, "old": "return ZipFile.binaryValue(buffer, offset, length, lead);",
      "new": "return ZipFile.binaryValue(buffer, offset, length, lead & 0x7f);",
      "why": "hop 3 masks the value of the first byte to seven bits"},
     {"file": ZF, "old": "return TarArchiveEntry.binaryValueOf(buffer, offset, length, lead);",
      "new": "return TarArchiveEntry.binaryValueOf(buffer, offset, Math.min(length, 8), lead);",
      "why": "hop 4 reads at most eight bytes of the number"},
   ],
 },
 "host_notes": "host_mode largest5 (1 other public class of >= 1500 lines in the fixed revision): the hosts are hosts_hop_order "
               "of batch6_tasks.json, in order, none substituted: compressors.bzip2.BZip2CompressorOutputStream (hop 1, 1886 "
               "lines, anchor after getBlockSize, line idx 644, seed 3917), archivers.zip.ZipArchiveOutputStream (hop 2, 1495, "
               "after setMethod, 730, seed 3918), compressors.bzip2.BZip2CompressorInputStream (hop 3, 1048, after close, 374, "
               "seed 3919), archivers.zip.ZipFile (hop 4, 969, after getEntriesInPhysicalOrder, 285, seed 3920), "
               "archivers.tar.TarArchiveEntry (hop 5, gold, 926, after the TarArchiveEntry constructor, 255, seed 3921); "
               "anchors from stageB_lib.pick_insertion_anchor with the instance seed 3817 + 100 + i (the values mr2_spec.py "
               "inserts at), all in the outer class. Smallest host 926 lines (the gold host). All five are public concrete "
               "classes in which a static method compiles. The facade calls hop 1 by its fully-qualified name; each hop "
               "imports the next host (hop 1 also TarUtils); in ZipArchiveOutputStream and ZipFile the new import follows the "
               "existing static imports.",
}
