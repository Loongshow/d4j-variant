"""Main run Compress-38__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Compress-38; the real bug modified TarArchiveEntry, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE.md section 1:
pool v2 found no tested static target); paired_* fields of the task record are null.

Facade: TarArchiveEntry.isDirectory() (instance method, @Override of ArchiveEntry.isDirectory; allowed targets TarArchiveEntry.isDirectory /
.isFile / .writeEntryHeader, BATCH9_PREREGISTRATION.md rank 333; facade_planned_by null for all three; no facade reuse). isDirectory was
chosen because it carries a decision with several parts (a file-backed entry, the directory link flag, the header kinds, the name) that can
be split along a chain, and an existing test reaches it. isFile was not used: its only decisions are a pair of normal-file flags and a
negated name test, so every one-line omission there either leaves a parameter unused or one of the two normal-file flags handled alone.
writeEntryHeader(byte[]) was not used: its own computation is only the choice between the default and the fallback encoding; the header
layout is in the private writeEntryHeaderField and the three-argument overload, which a hop may not copy.
Original computation: an entry created from a file is a directory if that file is one (file.isDirectory()); otherwise an entry whose link
flag is LF_DIR is a directory; otherwise an entry whose name ends with '/' is a directory unless it is a PAX extended header or a PAX global
extended header (isPaxHeader(), isGlobalPaxHeader()); every other entry is not a directory.

facade_variant: V2+V1 (receiver as parameter, plus one private field as a value). state_passed: the receiver `this` (typed TarArchiveEntry;
the hops call only its public methods getFile(), getName(), isPaxHeader(), isGlobalPaxHeader()) and the private field linkFlag (byte),
which has no public getter, handed to hop 1; no field is written, no write-back. The facade body is one call to hop 1 (the original has no
argument guard). No visibility is widened, no type is added, no signature, modifier, override (@Override kept) or throws clause changes, no
reflection, no test edit. The original calls no private method, so V4 does not apply; the public calls isPaxHeader()/isGlobalPaxHeader()/
getName() are kept as calls on the receiver, so an override still applies.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Compress-38-probe of the fixture, the first statement of
isDirectory() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.compress.archivers.tar.TarArchiveInputStreamTest::survivesPaxHeaderWithNameEndingInSlash`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at TarArchiveEntry.isDirectory(TarArchiveEntry.java:851), called from
TarArchiveEntry.parseTarHeader(TarArchiveEntry.java:1159). The facade is reached by the trigger (and, through TarArchiveInputStream and
TarArchiveOutputStream, by most tar tests).

Hosts (host_mode = "largest5"; batch9_tasks.json hosts_hop_order, used in that order, none substituted, none drawn by this builder):
  hop 1 archivers.zip.ZipArchiveOutputStream          1621 lines  isDirectoryEntry     plumbing: an entry created from a file is judged by
                                                                                       that file; any other entry goes on down the chain
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1330 lines  entryIsDirectory     pass-through
  hop 3 archivers.zip.ZipFile                         1149 lines  denotesDirectory     pass-through
  hop 4 archivers.zip.ZipArchiveInputStream           1112 lines  readsAsDirectory     pass-through
  hop 5 archivers.sevenz.SevenZFile                   1014 lines  isDirectoryByHeader  GOLD: the header decision (link flag, header kind,
                                                                                       name)
Host newline counts 1621, 1330, 1149, 1112, 1014; the smallest host (and the gold host) has 1014 lines (C10F addendum section 1: hosts
under 1500 lines are expected in this regime).
The correct configuration returns the original result for every entry: hop 1 reads getFile() (which returns the field file) where the
original read the field, and the gold makes the original's three header tests in the original order.

Fault (one-line omission of a special-case step in the gold): the exclusion of the two PAX header kinds is dropped from the gold's name
test (`return !entry.isPaxHeader() && !entry.isGlobalPaxHeader() && entry.getName().endsWith("/");` becomes `return
entry.getName().endsWith("/");`). The gold then reads as the ordinary routine "an entry is a directory if its link flag says so or its
name ends with a slash". Trigger: the EXISTING test TarArchiveInputStreamTest::survivesPaxHeaderWithNameEndingInSlash (COMPRESS-356.tar:
a PAX extended header, link flag 'x', named "PaxHeader/package/package.jso/", followed by the entry package/package.json). On the variant
the PAX header is taken for a directory, so TarArchiveInputStream reads none of its data (read/skip return nothing for a directory) and
parses the PAX records as the next header: java.io.IOException "Error detected parsing the header". Only this test newly fails (full
suite on a scratch copy with the same omission: 1 failing test; gate G5 checks the variant itself).
Note for reviewers: this omission re-creates, inside the chain's gold, the behaviour that the real Defects4J bug Compress-38 had in
TarArchiveEntry.isDirectory, and the trigger is that bug's trigger test. The alternative omission (the LF_DIR test, caught only by
TarArchiveOutputStreamTest::testWriteLongDirectoryNameTruncateMode) was rejected because it leaves the gold's flag parameter unused (T1).

The gold's javadoc states the idiomatic contract (it tells "whether a tar entry represents a directory, judging by the link flag and the
name") and is silent on header kinds. A PAX extended header is not a directory: it is a header entry whose data are the records that apply
to the next entry; the variant reports it as a directory. The convention is pinned outside the gold: TarArchiveInputStream.getNextTarEntry
reads a PAX header entry's data as PAX records (paxHeaders / readGlobalPaxHeaders), which only works if the PAX entry is not a directory;
TarArchiveOutputStream.writePaxHeaders names its PAX entries with stripTo7Bits, whose shouldBeReplaced replaces '/' because "when used as
last character TAE will consider the PAX header a directory", and writes the PAX data with a size that putArchiveEntry honours only for a
non-directory. Passing tests: TarArchiveInputStreamTest::survivesBlankLinesInPaxHeader (a PAX header read through the chain),
TarArchiveOutputStreamTest::testWriteNonAsciiDirectoryNamePosixMode and ::testWriteSimplePaxHeaders (PAX headers written and read back
through the chain), TarArchiveOutputStreamTest::testWriteLongDirectoryNameTruncateMode (the LF_DIR side of the decision through the chain).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: flag decides the first return; entry supplies the header kind and the name of the second.
  T2 absent: no locals; the if returns true, the fall-through returns a computed value (two different effects).
  T3 absent: both PAX header kinds (extended and global) are treated; no other header kind is named; no class named in the text is
     handled in part.
  T4 absent: 'whether a tar entry represents a directory, judging by the link flag and the name' is a general description met by the
     body (both are read); the @param/@return clauses name nothing the body does not meet.
 Variant gold (javadoc, signature, `if (flag == TarConstants.LF_DIR) { return true; }`, `return entry.getName().endsWith("/");`):
  T1 absent: flag decides the first return; entry's name decides the second; neither is only argument-checked.
  T2 absent: no locals at all; the if branch (true) and the fall-through (the name test) have different effects; nothing frozen or dead.
  T3 absent: no header kind is handled at all ('No member handled'); of the link-flag codes exactly one (LF_DIR) is tested and the gold
     names no class of them ('One member of a larger unnamed set'); no pair half or range end is involved.
  T4 absent: 'represents a directory' and 'judging by the link flag and the name' are general descriptions addressed by the two lines;
     no inline comment; identifiers (entry, flag, isDirectoryByHeader) name nothing the body does not meet.

Single owner: only the gold makes the header decision (link flag, header kind, name); hop 1 only answers for an entry created from a file
(a PAX header read from an archive never is) and hops 2-4 hand the entry and its flag on unchanged. Once the gold reports a PAX header as
a directory, the stream skips its data whatever a caller does with the answer, unless a caller replaces the gold's answer for that entry.
Declared alternatives (G9): hop 2 leaves out the PAX global extended header; hop 3 leaves out the GNU long-name entry; hop 1 answers from
the file only if the file exists. None makes the trigger pass (the trigger's header is a PAX extended header, 'x', read from a stream).
Recorded bypasses (not repairs of the chain):
 B-0 the facade's original body, or any hop re-deriving the answer, replaces the chain including the gold.
 B-1 a hop answers false for a PAX header before calling down (`!entry.isPaxHeader() && !entry.isGlobalPaxHeader() && ...`): a second
     copy of the gold's header decision in a hop documented as handing the entry on, which then decides header kinds that the gold also
     decides.
 B-2 outside the chain, TarArchiveInputStream's private isDirectory() (or read/skip) could ignore the answer for a PAX header; that
     leaves TarArchiveEntry.isDirectory() reporting a PAX header as a directory to every other caller (TarArchiveOutputStream,
     parseTarHeader).

Lie placement: the facade carries @Override between its javadoc and its declaration, so the recipe's javadoc finder
(extract_transform.find_javadoc_start, which requires only whitespace between the javadoc and the header) finds no javadoc and
rewrite_facade appends nothing. The behaviour-preserving pre-edit (pre_edits.chain) therefore inserts the lie sentence into isDirectory's
own javadoc exactly where and in the form rewrite_facade puts it (two spaces, the sentence, a new line, before the closing */); the
recipe call then leaves the javadoc unchanged, so the sentence appears once.
Lie: the facade's javadoc claims the entry's mode is examined first and an entry whose mode has the directory bit set is reported as a
directory; no step of the chain reads the mode. It names neither header kinds nor the name test nor any hop."""

TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZOS = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"
SZF = "src/main/java/org/apache/commons/compress/archivers/sevenz/SevenZFile.java"
TAE_IMP = "org.apache.commons.compress.archivers.tar.TarArchiveEntry"
LIE = "The entry's mode is examined first, and an entry whose mode has the directory bit set is reported as a directory."

GOLD_TEXT = '''/**
 * Tells whether a tar entry represents a directory, judging by the link
 * flag and the name it was read or created with.
 *
 * @param entry the entry to examine
 * @param flag the link flag of the entry
 * @return whether the entry represents a directory
 */
public static boolean isDirectoryByHeader(final TarArchiveEntry entry, final byte flag) {
    if (flag == TarConstants.LF_DIR) {
        return true;
    }
    return !entry.isPaxHeader() && !entry.isGlobalPaxHeader() && entry.getName().endsWith("/");
}'''

HOP1 = '''/**
 * Tells whether a tar entry represents a directory.
 *
 * <p>An entry that was created from a file represents a directory if
 * that file is a directory; any other entry is judged by its link flag
 * and its name.</p>
 *
 * @param entry the entry to examine
 * @param flag the link flag of the entry
 * @return whether the entry represents a directory
 */
public static boolean isDirectoryEntry(final TarArchiveEntry entry, final byte flag) {
    final File source = entry.getFile();
    if (source != null) {
        return source.isDirectory();
    }
    return BZip2CompressorOutputStream.entryIsDirectory(entry, flag);
}'''

HOP2 = '''/**
 * Tells whether a tar entry that was not created from a file represents
 * a directory.
 *
 * @param entry the entry to examine
 * @param flag the link flag of the entry
 * @return whether the entry represents a directory
 */
public static boolean entryIsDirectory(final TarArchiveEntry entry, final byte flag) {
    return ZipFile.denotesDirectory(entry, flag);
}'''

HOP3 = '''/**
 * Tells whether a tar entry represents a directory, judging by its link
 * flag and its name.
 *
 * @param entry the entry to examine
 * @param flag the link flag of the entry
 * @return whether the entry represents a directory
 */
public static boolean denotesDirectory(final TarArchiveEntry entry, final byte flag) {
    return ZipArchiveInputStream.readsAsDirectory(entry, flag);
}'''

HOP4 = '''/**
 * Tells whether a tar entry read from an archive or created by name
 * represents a directory.
 *
 * @param entry the entry to examine
 * @param flag the link flag of the entry
 * @return whether the entry represents a directory
 */
public static boolean readsAsDirectory(final TarArchiveEntry entry, final byte flag) {
    return SevenZFile.isDirectoryByHeader(entry, flag);
}'''

DESIGN = {
 "instance": "Compress-38", "project": "Compress", "bug_id": 38, "seed": 2627,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2+V1",
 "state_passed": "the receiver this (TarArchiveEntry; hops call only getFile(), getName(), isPaxHeader(), isGlobalPaxHeader()) and the "
                 "private field linkFlag (byte value), passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [1621, 1330, 1149, 1112, 1014],
 "reachability_probe": "isDirectory() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Compress-38-probe: TarArchiveInputStreamTest::survivesPaxHeaderWithNameEndingInSlash fails "
                       "with PROBE-REACHED at TarArchiveEntry.isDirectory(TarArchiveEntry.java:851), called from "
                       "TarArchiveEntry.parseTarHeader(TarArchiveEntry.java:1159)",
 "facade": {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "isDirectory", "near_line": 850},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/compress/archivers/tar/TarArchiveInputStreamTest.java",
             "test_class": "org.apache.commons.compress.archivers.tar.TarArchiveInputStreamTest",
             "test_method": "survivesPaxHeaderWithNameEndingInSlash"},
 "expected_signature": "Error detected parsing the header",
 "gold": {"method": "isDirectoryByHeader", "text": GOLD_TEXT,
          "fault": {"old": "        return !entry.isPaxHeader() && !entry.isGlobalPaxHeader() && entry.getName().endsWith(\"/\");",
                    "new": "        return entry.getName().endsWith(\"/\");"}},
 "chain": {
   "facade_body": "return org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.isDirectoryEntry(this, linkFlag);",
   "lie": LIE,
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "isDirectoryEntry",
      "imports": [TAE_IMP, "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZOS, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "entryIsDirectory",
      "imports": [TAE_IMP, "org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP2},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "denotesDirectory",
      "imports": [TAE_IMP], "text": HOP3},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "readsAsDirectory",
      "imports": [TAE_IMP, "org.apache.commons.compress.archivers.sevenz.SevenZFile"], "text": HOP4},
     {"file": SZF, "class": "org.apache.commons.compress.archivers.sevenz.SevenZFile", "method": "isDirectoryByHeader",
      "imports": [TAE_IMP, "org.apache.commons.compress.archivers.tar.TarConstants"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.tar.TarArchiveInputStream::getNextTarEntry",
              "org.apache.commons.compress.archivers.tar.TarArchiveOutputStream::writePaxHeaders",
              "org.apache.commons.compress.archivers.tar.TarArchiveOutputStream::putArchiveEntry"],
 "ownership_reason": "Only the gold makes the header decision for an entry that was not created from a file: the directory link flag, "
                     "the header kinds and the name. Hop 1 only answers for an entry created from a file (an entry read from an archive "
                     "never is one) and hops 2-4 hand the entry and its link flag on unchanged, so once the gold reports a PAX extended "
                     "header whose name ends with a slash as a directory, TarArchiveInputStream reads none of its data and parses its "
                     "records as the next header. The gold's javadoc promises whether the entry represents a directory; a PAX header "
                     "is a header entry whose data are records for the next entry, not a directory. The convention is pinned outside "
                     "the gold: TarArchiveInputStream.getNextTarEntry reads a PAX header entry's data as PAX records (paxHeaders, "
                     "readGlobalPaxHeaders); TarArchiveOutputStream.writePaxHeaders names its PAX entries through stripTo7Bits, whose "
                     "shouldBeReplaced replaces '/' so that the PAX header is not considered a directory, and writes the PAX data with "
                     "a size that putArchiveEntry honours only for a non-directory. survivesBlankLinesInPaxHeader, "
                     "testWriteNonAsciiDirectoryNamePosixMode and testWriteSimplePaxHeaders (PAX headers through the chain) and "
                     "testWriteLongDirectoryNameTruncateMode (the link-flag side through the chain) pass.",
 "ownership_tests": ["org.apache.commons.compress.archivers.tar.TarArchiveInputStreamTest::survivesBlankLinesInPaxHeader",
                     "org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testWriteNonAsciiDirectoryNamePosixMode",
                     "org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testWriteSimplePaxHeaders",
                     "org.apache.commons.compress.archivers.tar.TarArchiveOutputStreamTest::testWriteLongDirectoryNameTruncateMode"],
 "compensating": {
   "chain": [
     {"file": BZOS, "old": "    return ZipFile.denotesDirectory(entry, flag);",
      "new": "    return !entry.isGlobalPaxHeader() && ZipFile.denotesDirectory(entry, flag);",
      "why": "hop 2 leaves out the PAX global extended header"},
     {"file": ZF, "old": "    return ZipArchiveInputStream.readsAsDirectory(entry, flag);",
      "new": "    return !entry.isGNULongNameEntry() && ZipArchiveInputStream.readsAsDirectory(entry, flag);",
      "why": "hop 3 leaves out the GNU long-name entry"},
     {"file": ZAOS, "old": "    if (source != null) {\n            return source.isDirectory();",
      "new": "    if (source != null && source.exists()) {\n            return source.isDirectory();",
      "why": "hop 1 answers from the file only if the file exists"},
   ],
 },
 "pre_edits": {"chain": [
   {"file": TAE,
    "old": "     * @return True if this entry is a directory.\n     */\n    @Override\n    public boolean isDirectory() {",
    "new": "     * @return True if this entry is a directory.\n       " + LIE + "\n     */\n    @Override\n    public boolean isDirectory() {"},
 ]},
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder; the "
               "facade's file TarArchiveEntry.java is excluded): archivers.zip.ZipArchiveOutputStream (hop 1, 1621 lines), "
               "compressors.bzip2.BZip2CompressorOutputStream (hop 2, 1330), archivers.zip.ZipFile (hop 3, 1149), "
               "archivers.zip.ZipArchiveInputStream (hop 4, 1112), archivers.sevenz.SevenZFile (hop 5, gold, 1014; the smallest "
               "host). All five are public concrete top-level classes in which a public static method compiles. Anchors from "
               "stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 2627 + 100 + i, as mr3_spec.py inserts them: "
               "hop 1 after closeArchiveEntry (seed 2727), hop 2 after chooseBlockSize (2728), hop 3 after getEncoding (2729), hop 4 "
               "after the ZipArchiveInputStream constructor (2730), hop 5 after close (2731). The facade calls hop 1 by its "
               "fully-qualified name (no import added to TarArchiveEntry); each hop imports TarArchiveEntry and the next host where "
               "it is in another package; hop 1 uses java.io.File, already imported by ZipArchiveOutputStream; the gold imports "
               "TarConstants.",
}
