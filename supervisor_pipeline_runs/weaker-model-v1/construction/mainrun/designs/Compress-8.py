"""Main run Compress-8 (cell C10f, batch 6; C10 recipe on the fixed checkout of Defects4J Compress-8; the real bug modified
TarUtils, the target class).

Facade: TarUtils.parseName(byte[], int, int), the only allowed target (BATCH6_PREREGISTRATION.md row 158). Original computation:
a StringBuffer of capacity `length`; for every position from `offset` up to `offset + length`, a NUL byte ends the name, any other
byte is appended as the character (char) (b & 0xFF); the String of the buffer is returned. Its javadoc: 'Parsing stops when a NUL
is found or the buffer length is reached.'

host_mode: largest5 (one other public class of at least 1500 lines in this revision). Hosts are the five largest public classes other
than TarUtils, in task-record order (hosts_hop_order), none substituted:
  hop 1 compressors.bzip2.BZip2CompressorOutputStream  1881 lines  nameOfField      pass-through
  hop 2 compressors.bzip2.BZip2CompressorInputStream    995 lines  nameInField      pass-through
  hop 3 archivers.zip.ZipArchiveOutputStream             969 lines  fieldName        aggregation: creates the StringBuffer that
                                                                                   collects the name, with the length of the
                                                                                   field as its capacity, and returns its String
  hop 4 archivers.cpio.CpioArchiveEntry                  888 lines  appendFieldName  pass-through of the receiving buffer, the
                                                                                   byte buffer and the offset
  hop 5 archivers.tar.TarArchiveEntry                    745 lines  appendEntryName  GOLD: the per-byte scan (a NUL ends the name,
                                                                                   a full receiving buffer ends the scan) with
                                                                                   the unsigned byte-to-char step
Host sizes 1881 / 995 / 969 / 888 / 745 newlines; smallest host 745 lines (TarArchiveEntry, the gold host). Anchors
(stageB_lib.pick_insertion_anchor through pick_anchor, instance seed 2715, seed + 100 + i, as mr2_spec.py inserts them): after flush
(seed 2815), after read(byte[], int, int) (seed 2816), after flush (seed 2817), after the CpioArchiveEntry(File, String)
constructor (seed 2818), after getUserId (seed 2819), all at brace depth 1 in the outer class.
The correct configuration returns the original result for every input: hop 3 creates the same StringBuffer(length) (the same
NegativeArraySizeException for a negative length), and the gold appends while the buffer holds fewer characters than its capacity
(= length, so at most `length` bytes from `offset` are read, as in the original bound i < offset + length) and the byte is not NUL,
with the same mask.

reachability_probe: in a scratch copy of the fixture the first statement of TarUtils.parseName was made
`if (true) throw new IllegalStateException("PROBE-REACHED");` (a bare throw as the first statement makes the rest of the body
unreachable, which javac rejects); defects4j compile OK; `defects4j test -t TarUtilsTest::testName`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at TarUtils.parseName; full suite (defects4j test): 12 failing tests, each with
PROBE-REACHED: TarUtilsTest::testName, ::testRoundTripNames, TarTestCase::testTarUnarchive, ::testFileEntryFromFile,
::testDirectoryEntryFromFile, ::testExplicitDirectoryEntry, ::testCOMPRESS114, ::testExplicitFileEntry,
TarArchiveEntryTest::testTarFileWithFSRoot, IOMethodsTest::testReadTar, ChangeSetTestCase::testDeleteFromTar,
::testDeleteFromAndAddToTar. The facade is reached (directly by TarUtilsTest, and through TarArchiveEntry.parseTarHeader by every
tar-reading test).

Fault (one-line omission of the stopping rule in the gold's iteration): the conjunct `entryName.length() < entryName.capacity()` is
dropped from the scan's condition, so the scan runs on to the next NUL wherever it lies. For a name that fills its field (no NUL
inside the field) the scan reads past the field. Trigger: the EXISTING test TarUtilsTest::testName; its first call
parseName(buff, 1, 10) reads a field filled by 'abcdefghij' in a 20-byte buffer whose later bytes are letters too, so the scan
reaches the end of the buffer and fails with java.lang.ArrayIndexOutOfBoundsException: Index 20 out of bounds for length 20. It is
the only test that newly fails: every other reaching test parses NUL-terminated names, or full fields that a NUL soon follows (the
GNU magic 'ustar ' is followed by the version ' \0'; the POSIX version '00' fills its 2-byte field and is followed by the user
name and its NUL), and TarArchiveEntry.writeEntryHeader writes such values back cut to their field length, so the round trips and
the magic re-detection of ChangeSetTestCase::testDeleteFromTar still pass. The gold's javadoc states the idiomatic contract (the
characters of the entry name held in a header buffer, collected in the buffer created for that name) and is silent on full
fields; on the trigger input the variant appends characters that are not part of the name and then reads outside the header
buffer, so it violates that contract.

Faults set aside (each checked on parseName in a scratch copy, full suite): dropping the NUL rule fails 11 of the 12 reaching
tests (all but IOMethodsTest::testReadTar); dropping the 0xFF mask fails testRoundTripNames AND testCOMPRESS114 (both decode the
byte 0xB1). A scan bounded by the end of the
header buffer instead of the receiving buffer's capacity would end in an assertion instead of an exception, and then hop 3, which
knows the field length, could keep at most `length` characters of the result and repair every input; the gold would not be the
unique owner. The field length is therefore not a parameter of the gold: it reaches the gold only as the capacity of the buffer
created for the name.

External pins (convention outside the gold): the facade's own javadoc ('Parsing stops when a NUL is found or the buffer length is
reached'); hop 3's javadoc (the receiving buffer is created with the length of the field as its initial capacity);
TarUtils.formatNameBytes, the writing side, fills the whole field without a NUL when the name is as long as the field ('If the
name is longer than the buffer, the output is truncated'); TarArchiveEntry.writeEntryHeader writes the POSIX version '00' and the
GNU magic 'ustar ' as full, NUL-free fields that parseTarHeader reads back through the facade; ArchiveUtils.isEqual treats trailing
NULs as optional (ArchiveUtilsTest::testCompareBA). Passing tests on the variant: testCompareBA, testRoundTripNames,
testCOMPRESS114, testDeleteFromTar.

Single owner: only the gold reads the bytes of the field; hops 1 and 2 pass the buffer, the offset and the length on unchanged,
hop 3 only creates the receiving StringBuffer and returns its String, hop 4 passes the receiving buffer, the byte buffer and the
offset on unchanged. No hop can stop a scan it does not perform: once the gold has read outside the header buffer and thrown, no
caller can recover the name. Declared alternatives (G9): hop 3 keeps at most `length` characters of the collected name; hop 2
clamps the length to the bytes left in the buffer; hop 1 answers an empty field, or one that starts with a NUL, directly. None
changes the trigger's exception (the variant scan consults neither the length nor the capacity).
Recorded edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy, defects4j test):
 B-0 bypass: the facade (its original body) or any of hops 1-3 returns another implementation of the parse, e.g. hop 2
     `return new String(buf, 0, offset, length).split("\\0", 2)[0];` (the ISO-8859-1 String constructor, cut at the first NUL),
     discarding the rest of the chain including the gold.
 B-1 pre-filter: a hop passes a NUL-terminated copy of the field instead of the buffer, e.g. hop 1
     `return BZip2CompressorInputStream.nameInField(java.util.Arrays.copyOf(java.util.Arrays.copyOfRange(buf, offset, offset + length), length + 1), 0, length);`.
     It contradicts the edited hop's own documentation (the buffer is passed on without being copied, and the offset is the
     field's offset in that buffer), and every hop below it then reads a different array.
 B-2 test-fitted masking: hop 3 catches the exception the gold's scan raises and then cuts the collected characters to the
     field length, `try { CpioArchiveEntry.appendFieldName(name, buf, offset); } catch (ArrayIndexOutOfBoundsException e) { name.setLength(Math.min(name.length(), length)); }`.
     It repairs only the inputs on which the overrun reaches the end of the buffer: whenever a NUL follows the field inside the
     buffer no exception is raised and the gold's characters past the field are returned (parseName({'a','b',' ',0}, 0, 2)
     gives "ab " instead of "ab"; a parsed GNU magic keeps seven characters for its six-byte field), so hop 3 then contradicts
     its own documentation (the name held in the field) and the facade's.
 B-3 masking bypass: the same catch with the cut moved after it, so it also applies on the normal path
     (`try { ... } catch (ArrayIndexOutOfBoundsException e) { } name.setLength(Math.min(name.length(), length));`, two
     statements). It swallows the exception the gold raises and re-implements the field bound in hop 3 as a cut of the gold's
     output, relying on the gold appending characters that are not part of the name; the gold is no longer used as
     documented, and its stopping rule is replaced, not repaired.

Lie: the facade's javadoc claims each byte is mapped to its character through a 256-entry ISO-8859-1 lookup table; no table exists,
the character is computed from the byte. It names neither the field end nor full fields nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, `for (int i = offset; entryName.length() < entryName.capacity() && header[i] != 0; ++i) {
 entryName.append((char) (header[i] & 0xFF)); }`):
  T1 absent: entryName receives the characters and its fill level decides the scan, header is read, offset starts the scan.
  T2 absent: the only local, i, is advanced by the for header; the loop condition decides every append; no branch, case or ternary.
  T3 absent: the NUL test is the only per-byte special case and the mask applies to every byte; the gold receives no range (no end
     index or length parameter), so no range end is treated while the other is not; no class is named.
  T4 absent: the javadoc names the characters of the entry name held in a header buffer, the buffer created for the name and the
     offset of the name; no limit, bound, value class or case is named; there is no inline comment.
  Rewritten before choosing the omission: the field length is not given to the gold as a parameter (a start offset and a length
  would form a range of which the variant would bound only the start), and the original's 'Trailing null' and 'Allow for
  sign-extension' comments are not carried into the gold.
 Variant gold (javadoc, signature, `for (int i = offset; header[i] != 0; ++i) { entryName.append((char) (header[i] & 0xFF)); }`):
  T1 absent: entryName is appended to (side effect), header decides the scan and the characters, offset starts the scan; each
     changes the result or the side effect; no parameter is only argument-checked.
  T2 absent: i is the cursor, advanced by ++i in the for header and used as the index of every read; there are no other locals, no
     literal-initialised variable and no branch, case or ternary; the loop condition decides whether each append runs.
  T3 absent: the NUL test is the only per-byte special case (one member of an unnamed set; the mask applies to every byte); the
     only position in the text is a start offset, with no end index, length or bound beside it, so there is no pair of range ends
     of which one is handled; the gold names no class that it handles in part.
  T4 absent: 'Appends the characters of the entry name held in a header buffer' is a general description the loop addresses; the
     @param clauses say what the caller supplies (the buffer created for the entry name, the header buffer, the offset of the
     name); no rule, limit, value class or case is named; identifiers (entryName, header, offset, i) name nothing the body does
     not meet."""

TU = "src/main/java/org/apache/commons/compress/archivers/tar/TarUtils.java"
BZO = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
BZI = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorInputStream.java"
ZAO = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
CAE = "src/main/java/org/apache/commons/compress/archivers/cpio/CpioArchiveEntry.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"

GOLD_TEXT = '''/**
 * Appends the characters of the entry name held in a header buffer.
 *
 * @param entryName the buffer created for the entry name, which
 *                  receives its characters
 * @param header the header buffer
 * @param offset the offset of the entry name in the header buffer
 */
public static void appendEntryName(final StringBuffer entryName, final byte[] header,
                                   final int offset) {
    for (int i = offset; entryName.length() < entryName.capacity() && header[i] != 0; ++i) {
        entryName.append((char) (header[i] & 0xFF));
    }
}'''

FIELD_DOC = '''/**
 * Reads the name held in a field of a byte buffer.
 *
 * @param buf the buffer that holds the field; it is passed on without
 *            being copied
 * @param offset the offset of the field in the buffer
 * @param length the length of the field
 * @return the name held in the field
 */'''

HOP1 = FIELD_DOC + '''
public static String nameOfField(final byte[] buf, final int offset, final int length) {
    return BZip2CompressorInputStream.nameInField(buf, offset, length);
}'''

HOP2 = FIELD_DOC + '''
public static String nameInField(final byte[] buf, final int offset, final int length) {
    return ZipArchiveOutputStream.fieldName(buf, offset, length);
}'''

HOP3 = '''/**
 * Reads the name held in a field of a byte buffer.
 *
 * <p>The characters of the name are collected in a new buffer whose
 * initial capacity is the length of the field.</p>
 *
 * @param buf the buffer that holds the field; it is passed on without
 *            being copied
 * @param offset the offset of the field in the buffer
 * @param length the length of the field
 * @return the name held in the field
 */
public static String fieldName(final byte[] buf, final int offset, final int length) {
    final StringBuffer name = new StringBuffer(length);
    CpioArchiveEntry.appendFieldName(name, buf, offset);
    return name.toString();
}'''

HOP4 = '''/**
 * Appends the name held in a field of a byte buffer to the buffer
 * created for that field.
 *
 * @param name the buffer created for the field, which receives the
 *             characters of the name
 * @param buf the buffer that holds the field; it is passed on without
 *            being copied
 * @param offset the offset of the field in buf
 */
public static void appendFieldName(final StringBuffer name, final byte[] buf, final int offset) {
    TarArchiveEntry.appendEntryName(name, buf, offset);
}'''

DESIGN = {
 "instance": "Compress-8", "project": "Compress", "bug_id": 8, "seed": 2715,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "parseName", "near_line": 128},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/tar/TarUtilsTest.java",
             "test_class": "org.apache.commons.compress.archivers.tar.TarUtilsTest", "test_method": "testName"},
 "expected_signature": "java.lang.ArrayIndexOutOfBoundsException: Index 20 out of bounds for length 20",
 "gold": {"method": "appendEntryName", "text": GOLD_TEXT,
          "fault": {"old": "        for (int i = offset; entryName.length() < entryName.capacity() && header[i] != 0; ++i) {",
                    "new": "        for (int i = offset; header[i] != 0; ++i) {"}},
 "chain": {
   "facade_body": "return org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream.nameOfField(buffer, offset, length);",
   "lie": "Each byte is mapped to its character through a 256-entry ISO-8859-1 lookup table.",
   "hops": [
     {"file": BZO, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "nameOfField",
      "imports": [], "text": HOP1},
     {"file": BZI, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream", "method": "nameInField",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream"], "text": HOP2},
     {"file": ZAO, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "fieldName",
      "imports": ["org.apache.commons.compress.archivers.cpio.CpioArchiveEntry"], "text": HOP3},
     {"file": CAE, "class": "org.apache.commons.compress.archivers.cpio.CpioArchiveEntry", "method": "appendFieldName",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP4},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "appendEntryName",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.tar.TarUtils::formatNameBytes",
              "org.apache.commons.compress.archivers.tar.TarArchiveEntry::writeEntryHeader",
              "org.apache.commons.compress.utils.ArchiveUtils::isEqual"],
 "ownership_reason": "Only the gold reads the bytes of the field: it scans the header buffer from the offset, ends the name at a "
                     "NUL, stops when the buffer created for the name is full and decodes each byte; hops 1 and 2 pass the "
                     "buffer, the offset and the length on unchanged (each documents that the buffer is passed on without "
                     "being copied), hop 3 only creates the receiving StringBuffer with the length of the field as its "
                     "initial capacity (as its javadoc says) and returns its String, and hop 4 passes the receiving buffer, "
                     "the byte buffer and the offset on unchanged. The scan has to stop at the end of the field as well as at "
                     "a NUL, because a name may fill its field: the facade's javadoc says parsing stops when a NUL is found or "
                     "the buffer length is reached; TarUtils.formatNameBytes, the writing side, fills the whole field "
                     "without a NUL when the name is as long as the field ('If the name is longer than the buffer, the "
                     "output is truncated'); TarArchiveEntry.writeEntryHeader writes the POSIX version '00' and the GNU magic "
                     "'ustar ' as full NUL-free fields that parseTarHeader reads back through the facade; ArchiveUtils.isEqual "
                     "treats trailing NULs as optional (ArchiveUtilsTest testCompareBA). The gold's javadoc promises the "
                     "characters of the entry name, collected in the buffer created for it; on the trigger input (a field "
                     "filled by 'abcdefghij' at offset 1) the scan appends the bytes after the field and reads past the end "
                     "of the header buffer, and once it has thrown no caller can recover the name. Hop edits that do not "
                     "perform the scan (truncating the collected name, clamping the length, answering empty fields) do not "
                     "change the exception; passing a NUL-terminated copy of the field instead of the buffer contradicts the "
                     "documentation of the hop that makes it (the buffer is passed on without being copied, the offset is the "
                     "field's offset in that buffer). A hop that catches the exception the scan raises and cuts the collected "
                     "characters to the field length uses the gold outside its documented behaviour: cutting only after the "
                     "exception still returns the characters the gold appends past the field whenever a NUL follows inside "
                     "the buffer (parseName of {'a','b',' ',0} with length 2 gives \"ab \"), and cutting on every path "
                     "re-implements the field bound in that hop as a cut of the gold's output while the gold keeps appending "
                     "characters that are not part of the name.",
 "ownership_tests": ["org.apache.commons.compress.ArchiveUtilsTest::testCompareBA",
                     "org.apache.commons.compress.changes.ChangeSetTestCase::testDeleteFromTar",
                     "org.apache.commons.compress.archivers.tar.TarUtilsTest::testRoundTripNames",
                     "org.apache.commons.compress.archivers.TarTestCase::testCOMPRESS114"],
 "compensating": {
   "chain": [
     {"file": ZAO, "old": "return name.toString();",
      "new": "return name.length() > length ? name.substring(0, length) : name.toString();",
      "why": "hop 3 keeps at most `length` characters of the collected name"},
     {"file": BZI, "old": "return ZipArchiveOutputStream.fieldName(buf, offset, length);",
      "new": "return ZipArchiveOutputStream.fieldName(buf, offset, Math.min(length, buf.length - offset));",
      "why": "hop 2 clamps the field length to the bytes left in the buffer"},
     {"file": BZO, "old": "return BZip2CompressorInputStream.nameInField(buf, offset, length);",
      "new": "return length == 0 || buf[offset] == 0 ? \"\" : BZip2CompressorInputStream.nameInField(buf, offset, length);",
      "why": "hop 1 answers an empty field, or one that starts with a NUL, directly"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 1). Hosts = hosts_hop_order of the task record in order, the five largest public "
               "non-interface non-enum classes other than TarUtils by newline count: compressors.bzip2.BZip2CompressorOutputStream "
               "(1881, hop 1), compressors.bzip2.BZip2CompressorInputStream (995, hop 2), archivers.zip.ZipArchiveOutputStream "
               "(969, hop 3), archivers.cpio.CpioArchiveEntry (888, hop 4), archivers.tar.TarArchiveEntry (745, hop 5, gold); "
               "smallest host 745 lines. All five are public concrete top-level classes in which a static method compiles; "
               "none was substituted. Anchors from stageB_lib.pick_anchor (pick_insertion_anchor) with the instance seed 2715 "
               "(seed + 100 + i, as mr2_spec.py inserts them): after flush (seed 2815), after read (seed 2816), after flush "
               "(seed 2817), after the CpioArchiveEntry(File, String) constructor (seed 2818), after getUserId (seed 2819), all "
               "at brace depth 1 in the outer class, identical to the task record's host_draw. The facade calls hop 1 by its "
               "fully-qualified name; hop 1 and hop 2 share a package; hops 2-4 import the next host. The static parameter "
               "names entryName (gold) and name (hop 4) do not touch the instance fields of the same hosts.",
}
