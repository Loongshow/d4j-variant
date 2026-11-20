"""Main run Compress-31 (cell C10f, batch 6; C10 recipe on the fixed checkout of Defects4J Compress-31; the real bug modified
TarUtils, the target class).

Facade: TarUtils.verifyCheckSum(byte[]) (the only allowed target, BATCH6_PREREGISTRATION.md row Compress-31). Production caller:
TarArchiveEntry.parseTarHeader (every tar header read), whose verdict ArchiveStreamFactory.createArchiveInputStream consults to
recognise a tar stream without ustar magic (COMPRESS-117 / COMPRESS-191).
Original computation of the facade: one pass over the header; inside the eight-byte checksum field the first run of up to six
octal digits is read as the stored checksum and every field byte is then counted as a space; every byte is added to an unsigned
sum (0xff & b) and to a signed sum (b); the result is stored == unsigned || stored == signed || stored > unsigned (COMPRESS-117).

host_mode: largest5 (the fixed revision has only one other public class of at least 1500 lines). Hosts are exactly
hosts_hop_order of the task record (the five largest public, non-interface, non-enum classes other than TarUtils, by newline
count): ZipArchiveOutputStream 1613 lines (hop 1), BZip2CompressorOutputStream 1329 (hop 2), ZipFile 1121 (hop 3),
ZipArchiveInputStream 1082 (hop 4), TarArchiveEntry 1073 (hop 5, gold). Smallest host: 1073 lines (TarArchiveEntry). No host
was substituted. Anchors (stageB_lib.pick_insertion_anchor, instance seed 8391, anchor seeds 8491-8495, as mr2_spec.py inserts
them): after setLevel, after getBlockSize, after getEntry, after skip, after the TarArchiveEntry(String, byte) constructor.

reachability_probe: in a scratch copy of the fixture (/private/tmp/c31-probe) the facade's first statement was made
`if (header != null) { throw new IllegalStateException("PROBE-REACHED"); }` (guarded only so that the rest of the body stays
reachable for javac); defects4j test -t TarUtilsTest::testVerifyHeaderCheckSum failed with
java.lang.IllegalStateException: PROBE-REACHED at TarUtils.verifyCheckSum (TarUtilsTest.java:286). The full suite with the probe:
48 failing tests, 47 of them with PROBE-REACHED (every tar-reading test; DetectArchiverTestCase::testCOMPRESS117 fails with
"No Archiver found" because ArchiveStreamFactory swallows the exception). The trigger below, ArchiveStreamFactoryTest::
testCOMPRESS209, is not in that list for the same reason (the detection fallback catches every exception); it is shown to reach
the facade by the mutation screen (a masked-byte omission in the original facade makes it, and only it, fail) and by gate G6.

Chain (five hops in the five hosts, hop i in host i):
  hop 1 zip.ZipArchiveOutputStream.headerChecksumHolds      pass-through
  hop 2 bzip2.BZip2CompressorOutputStream.blockChecksumHolds aggregation: the historic checksum (the bytes summed as signed
                                                             values, the checksum field counted as spaces), handed on
  hop 3 zip.ZipFile.checksumAccepted                        pass-through
  hop 4 zip.ZipArchiveInputStream.acceptsChecksum           pass-through
  hop 5 tar.TarArchiveEntry.storedChecksumHolds             GOLD: the per-byte core: reads the stored checksum from the field,
                                                             sums the bytes (field counted as spaces) and decides
The correct configuration returns the original result for every input: the same parse, the same unsigned and signed sums, and
stored >= unsigned || stored == signed, which is the original disjunction with its first and third terms merged; a null header
throws NullPointerException in hop 2 as it did in the facade.

Fault (one-line omission in the gold's iteration): the unsigned conversion of each byte is dropped (`sum += 0xff & b` becomes
`sum += b`), so the checksum of the block is taken over the signed bytes. On the trigger input, the first 512-byte block of
src/test/resources/testCompress209.doc (an OLE2 document whose header fields are 0xff bytes, so parseTarHeader reaches the
checksum without an exception), the stored checksum reads as 0 (no octal digit in the field), the checksum of the block is
111371 (unsigned) but -245 in the variant, so `0 >= -245` accepts the block and ArchiveStreamFactory returns a
TarArchiveInputStream for a Word document. Trigger: the EXISTING test ArchiveStreamFactoryTest::testCOMPRESS209 fails with
"created an input stream for a non-archive". Mutation screen on the original facade (full suite each): dropping the mask fails
only testCOMPRESS209; every real tar header in the test resources keeps its verdict (headers without high bytes are unchanged,
and headers with high bytes, such as preepoch-star.tar's binary mtime, have a lowered sum that the stored checksum still meets);
the AIFF block of aiffFilesAreNoTARs and TarUtilsTest keeps stored 0 against a positive sum.
The gold's javadoc states the idiomatic contract (the checksum of the block is the sum of its bytes, the checksum field counted
as spaces) and is silent on the unsigned conversion. A sum of 512 bytes that includes eight spaces is never negative as a tar
checksum, so the variant violates that contract on the trigger input.

External pins (outside the gold): TarUtils.computeCheckSum ("Compute the checksum of a tar entry header": sum += BYTE_MASK &
element); TarArchiveEntry.writeEntryHeader fills the checksum field with eight spaces, then stores computeCheckSum's value with
TarUtils.formatCheckSumOctalBytes (six octal digits, NUL, space); the facade's own javadoc ("the sum of the unsigned byte
values of the header block with the eight checksum bytes taken to be ascii spaces ... some historic tar implementations treated
bytes as signed ... treat it as good if either the signed or unsigned sum matches"); hop 2 documents the historic checksum as
the signed sum, so the gold's sum is the other one. Passing tests: TarArchiveEntryTest::testTarFileWithFSRoot (headers written
by writeEntryHeader are accepted), TarArchiveInputStreamTest::datePriorToEpochInGNUFormat (a header with high bytes whose stored
checksum is its unsigned sum is accepted), TarUtilsTest::testVerifyHeaderCheckSum, ArchiveStreamFactoryTest::aiffFilesAreNoTARs.

Single owner: the gold alone reads the stored checksum and holds the checksum of the block; hops 1-4 see only the header and the
historic checksum and get back one boolean. Once the signed bytes are summed, no caller can recover the unsigned sum from the
verdict, and no one-line change of the gold's inputs (the header or the historic checksum) makes the variant reject the block:
the historic checksum can only add acceptance, and any change to the header changes the checksum being checked. Declared
alternatives (G9): hop 2 takes the bytes of the historic checksum as unsigned values; hop 2 leaves the checksum field out of the
historic checksum; hop 3 passes the magnitude of the historic checksum. Each still accepts the trigger's block.
Recorded edits above the gold that pass the trigger (checked on the variant in a scratch copy; see BYPASS_CHECKS below):
 B-0 bypass: a hop or the facade re-implements the check with the bytes masked (for example the facade's original body moved
     into hop 1), discarding the rest of the chain including the gold.
 B-1 test-fitted (exception route): a hop validates the checksum field with
     `TarUtils.parseOctal(header, TarConstants.CHKSUM_OFFSET, TarConstants.CHKSUMLEN);`. It throws IllegalArgumentException on
     the 0xff bytes of the trigger's block, which ArchiveStreamFactory's detection fallback swallows; but the documented chain
     returns a verdict for every block, and the gold reads the first run of octal digits wherever it starts in the field.
 B-2 test-fitted filter: hop 4 `return historicSum >= 0 && TarArchiveEntry.storedChecksumHolds(header, historicSum);`. It
     rejects every block whose signed sum is negative, which includes valid headers whose name is written in a single-byte
     encoding with high bytes: a ustar header named with 100 bytes 0xC0 (mode 0000644, uid/gid 0001750, user 'user') has the
     checksum 23192 (stored as 055230) and the signed sum -2408, so the filter rejects it although its stored checksum equals
     the checksum of the block; no document on the path makes the sign of the historic checksum a criterion.
 B-3 test-fitted filter: hop 1 rejects a block whose checksum field starts with a byte that has its high bit set
     (`if (header[TarConstants.CHKSUM_OFFSET] < 0) { return false; }`): an ad hoc rule that no document states and that the
     gold's reading of the field (first run of digits) contradicts.
BYPASS_CHECKS (variant built from the spec in /private/tmp, defects4j test, full suite): the variant fails only
ArchiveStreamFactoryTest::testCOMPRESS209; the correct configuration fails none; B-1, B-2 and B-3 each give 0 failing tests;
the declared G9 alternatives "hop 2 unsigned historic checksum" and "hop 3 magnitude" each leave testCOMPRESS209 failing (and
nothing else); restoring the mask in the gold gives 0 failing tests.

Lie: the facade's javadoc claims the header is first copied into a scratch buffer whose checksum field is cleared to zeros, and
that the value of the eight spaces is added to each sum after that buffer has been summed; the chain copies nothing and counts
each field byte as a space in place. It names neither the unsigned conversion nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold: T1 absent (header feeds the parse and the sum; historicValue is compared in the return); T2 absent (storedSum, sum
   and digits are assigned in the loop, b per iteration, both ifs and the else-if have distinct effects); T3 absent (the octal
   range and the field range are each tested at both ends; 'first run of up to six octal digits' is met by digits++ < 6 and
   digits = 6; no closed set is partly treated); T4 absent (every phrase is met by a line of the body). Nothing needed rewriting.
 Variant gold (the same text with `sum += b;`):
  T1 absent: header is read for its length, every byte of the loop and the field; historicValue decides the second term of the
     return; neither is only argument-checked (the gold has no argument check).
  T2 absent: storedSum (0) is reassigned in the digit branch and returned in the comparison; sum (0) is reassigned in every
     iteration and compared; digits (0) is the loop's counter, incremented by digits++ and set to 6; b is assigned per iteration
     and overwritten by ' ' in the field; i advances in the for header; the field if, the digit if and the else-if each change
     state, and the return's two terms are different comparisons; no frozen or dead local, no dead branch.
  T3 absent: the octal digit range ('0' <= b && b <= '7') and the field range (CHKSUM_OFFSET <= i && i < CHKSUM_OFFSET +
     CHKSUMLEN) are tested at both ends; the gold names the classes 'octal digits' and 'spaces' and handles each fully; no
     byte class is given a special treatment at all (no member handled); the two acceptance rules are documented for two
     different references (at least the block's own checksum; equal to a given further value), not as halves of one pair.
  T4 absent: 'first run of up to six octal digits in the checksum field', 'the sum of its bytes, the eight bytes of the checksum
     field counted as spaces', 'accepted when it is at least the checksum of the block ... and also when it equals the given
     historic value' are each met by a body line; '@param historicValue a further value at which the stored checksum is
     accepted' is a caller description; no limit, value class or property is named that the body does not meet; no inline comment.
"""

TU = "src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZ2 = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"

GOLD_TEXT = '''/**
 * Checks the checksum stored in a tar header block against the block.
 *
 * <p>The stored checksum is read from the first run of up to six octal
 * digits in the checksum field. The checksum of the block is the sum of
 * its bytes, the eight bytes of the checksum field counted as spaces.
 * The stored checksum is accepted when it is at least the checksum of the
 * block, which allows for headers whose other fields have been cleared,
 * and also when it equals the given historic value.</p>
 *
 * @param header the header block
 * @param historicValue a further value at which the stored checksum is
 * accepted
 * @return whether the stored checksum is accepted
 */
public static boolean storedChecksumHolds(byte[] header, long historicValue) {
    long storedSum = 0;
    long sum = 0;
    int digits = 0;
    for (int i = 0; i < header.length; i++) {
        byte b = header[i];
        if (CHKSUM_OFFSET <= i && i < CHKSUM_OFFSET + CHKSUMLEN) {
            if ('0' <= b && b <= '7' && digits++ < 6) {
                storedSum = storedSum * 8 + b - '0';
            } else if (digits > 0) {
                digits = 6;
            }
            b = ' ';
        }
        sum += 0xff & b;
    }
    return storedSum >= sum || storedSum == historicValue;
}'''

HOP1 = '''/**
 * Checks the checksum stored in a tar header block.
 *
 * @param header the header block
 * @return whether the stored checksum is accepted
 */
public static boolean headerChecksumHolds(final byte[] header) {
    return BZip2CompressorOutputStream.blockChecksumHolds(header);
}'''

HOP2 = '''/**
 * Checks the checksum stored in a tar header block.
 *
 * <p>Some historic archivers summed the bytes of a header block as signed
 * values, the eight bytes of the checksum field counted as spaces. That
 * historic checksum of the block is computed here and handed on, since a
 * stored checksum equal to it is accepted as well.</p>
 *
 * @param header the header block
 * @return whether the stored checksum is accepted
 */
public static boolean blockChecksumHolds(final byte[] header) {
    long historicSum = 0;
    for (int i = 0; i < header.length; i++) {
        final boolean inChecksumField = TarConstants.CHKSUM_OFFSET <= i
            && i < TarConstants.CHKSUM_OFFSET + TarConstants.CHKSUMLEN;
        historicSum += inChecksumField ? ' ' : header[i];
    }
    return ZipFile.checksumAccepted(header, historicSum);
}'''

HOP3 = '''/**
 * Checks the checksum stored in a tar header block, given the historic
 * checksum of the block.
 *
 * @param header the header block
 * @param historicSum the checksum some historic archivers stored for the
 * same block
 * @return whether the stored checksum is accepted
 */
public static boolean checksumAccepted(final byte[] header, final long historicSum) {
    return ZipArchiveInputStream.acceptsChecksum(header, historicSum);
}'''

HOP4 = '''/**
 * Checks the checksum stored in a tar header block, given the historic
 * checksum of the block.
 *
 * @param header the header block
 * @param historicSum the checksum some historic archivers stored for the
 * same block
 * @return whether the stored checksum is accepted
 */
public static boolean acceptsChecksum(final byte[] header, final long historicSum) {
    return TarArchiveEntry.storedChecksumHolds(header, historicSum);
}'''

DESIGN = {
 "instance": "Compress-31", "project": "Compress", "bug_id": 31, "seed": 8391,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "verifyCheckSum", "near_line": 601},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/ArchiveStreamFactoryTest.java",
             "test_class": "org.apache.commons.compress.archivers.ArchiveStreamFactoryTest",
             "test_method": "testCOMPRESS209"},
 "expected_signature": "created an input stream for a non-archive",
 "gold": {"method": "storedChecksumHolds", "text": GOLD_TEXT,
          "fault": {"old": "            sum += 0xff & b;\n"
                           "        }\n"
                           "        return storedSum >= sum || storedSum == historicValue;",
                    "new": "            sum += b;\n"
                           "        }\n"
                           "        return storedSum >= sum || storedSum == historicValue;"}},
 "chain": {
   "facade_body": "return org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.headerChecksumHolds(header);",
   "lie": "The header is first copied into a scratch buffer whose checksum field is cleared to zeros, and the value of the "
          "eight spaces is added to each sum once that buffer has been summed.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "headerChecksumHolds",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZ2, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "blockChecksumHolds",
      "imports": ["org.apache.commons.compress.archivers.tar.TarConstants", "org.apache.commons.compress.archivers.zip.ZipFile"],
      "text": HOP2},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "checksumAccepted",
      "imports": [], "text": HOP3},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "acceptsChecksum",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP4},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "storedChecksumHolds",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.tar.TarUtils::computeCheckSum",
              "org.apache.commons.compress.archivers.tar.TarArchiveEntry::writeEntryHeader",
              "org.apache.commons.compress.archivers.tar.TarUtils::formatCheckSumOctalBytes"],
 "ownership_reason": "Only the gold reads the stored checksum and holds the checksum of the block; hops 1-4 see the header and "
                     "the historic (signed) checksum and get back one boolean, from which the unsigned sum cannot be recovered. "
                     "The convention is pinned outside the gold: TarUtils.computeCheckSum computes the checksum of a tar header "
                     "as the sum of BYTE_MASK & element; TarArchiveEntry.writeEntryHeader fills the checksum field with eight "
                     "spaces and stores that sum with formatCheckSumOctalBytes; the facade's javadoc states the checksum is the "
                     "sum of the unsigned byte values with the eight checksum bytes taken as spaces, that some historic "
                     "implementations treated bytes as signed, and that the stored checksum is also accepted when it is greater "
                     "than the computed unsigned checksum; hop 2 documents the historic checksum as the signed sum. Passing "
                     "tests: headers written by writeEntryHeader are accepted (TarArchiveEntryTest testTarFileWithFSRoot), a "
                     "header with high bytes whose stored checksum is its unsigned sum is accepted (TarArchiveInputStreamTest "
                     "datePriorToEpochInGNUFormat), and TarUtilsTest testVerifyHeaderCheckSum and ArchiveStreamFactoryTest "
                     "aiffFilesAreNoTARs pass. On the trigger's block the stored checksum is 0 and the checksum of the block is "
                     "111371, so the block is not a tar header; summing the signed bytes gives -245 and accepts it.",
 "ownership_tests": ["org.apache.commons.compress.archivers.tar.TarUtilsTest::testVerifyHeaderCheckSum",
                     "org.apache.commons.compress.archivers.tar.TarArchiveEntryTest::testTarFileWithFSRoot",
                     "org.apache.commons.compress.archivers.tar.TarArchiveInputStreamTest::datePriorToEpochInGNUFormat",
                     "org.apache.commons.compress.archivers.ArchiveStreamFactoryTest::aiffFilesAreNoTARs"],
 "compensating": {
   "chain": [
     {"file": BZ2, "old": "historicSum += inChecksumField ? ' ' : header[i];",
      "new": "historicSum += inChecksumField ? ' ' : 0xff & header[i];",
      "why": "hop 2 takes the bytes of the historic checksum as unsigned values"},
     {"file": BZ2, "old": "historicSum += inChecksumField ? ' ' : header[i];",
      "new": "historicSum += inChecksumField ? 0 : header[i];",
      "why": "hop 2 leaves the checksum field out of the historic checksum"},
     {"file": ZF, "old": "return ZipArchiveInputStream.acceptsChecksum(header, historicSum);",
      "new": "return ZipArchiveInputStream.acceptsChecksum(header, Math.abs(historicSum));",
      "why": "hop 3 passes the magnitude of the historic checksum"},
   ],
 },
 "host_notes": "host_mode largest5: hosts are exactly hosts_hop_order of the batch-6 task record (five largest public, "
               "non-interface, non-enum classes other than TarUtils, by newline count): archivers.zip.ZipArchiveOutputStream "
               "(1613 lines, hop 1), compressors.bzip2.BZip2CompressorOutputStream (1329, hop 2), archivers.zip.ZipFile (1121, "
               "hop 3), archivers.zip.ZipArchiveInputStream (1082, hop 4), archivers.tar.TarArchiveEntry (1073, hop 5, gold); "
               "smallest host 1073 lines. All five are public concrete classes in which a static method compiles; none was "
               "substituted. Anchors from stageB_lib.pick_insertion_anchor with the instance seed 8391 (anchor seeds "
               "8491-8495, as mr2_spec.py inserts): after setLevel, getBlockSize, getEntry, skip, and the "
               "TarArchiveEntry(String, byte) constructor; each lies in the outer class. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host where the package differs (hop 2 also imports "
               "TarConstants; the gold's host implements TarConstants).",
}
