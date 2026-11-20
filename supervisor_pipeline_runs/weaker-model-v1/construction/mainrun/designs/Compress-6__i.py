"""Main run Compress-6__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Compress-6; the real bug modified ZipArchiveEntry, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE section 1:
pool v2 found no tested static facade in ZipArchiveEntry).

Facade: ZipArchiveEntry.setUnixMode(int) (instance method; allowed targets ZipArchiveEntry.setUnixMode / ZipArchiveEntry.equals,
BATCH9_PREREGISTRATION.md rank 332). Facade reuse: setUnixMode is also the planned facade of Compress-13__i (facade_planned_by); the
distinct candidate equals was preferred but cannot carry the recipe validly, so the planned-elsewhere candidate is used and the reuse is
recorded (B8 note section 3). Why not equals: its computation is the null-safe comparison of the two entry names. Its probe (below)
reaches three tests: testNotEquals ("foo" against "bar", expected false) and ChangeSetTestCase::testAddChangeTwice /
testAddChangeTwiceWithoutReplace (two entries named "test.txt", expected true). Any omission that makes equal names compare unequal is
caught by both ChangeSet tests (gate G5 allows one), and the only single-test behaviour, "foo" reported equal to "bar", needs the chain to
stop comparing the characters of the names, which leaves the name comparison unused, frozen or dead (T1/T2) under any one-line omission.
Original computation of setUnixMode: setExternalAttributes((mode << SHORT_SHIFT) | ((mode & 0200) == 0 ? 1 : 0) | (isDirectory() ? 0x10
: 0)) (SHORT_SHIFT = 16: the Unix mode in the upper sixteen bits, the MS-DOS read-only attribute when the owner-write bit is clear, the
MS-DOS directory attribute for a directory entry), then platform = PLATFORM_UNIX.

facade_variant: V2+V1. V2 (receiver as parameter): the facade passes `this` (typed ZipArchiveEntry, the declaring class) and mode to hop
1; the hops use only the public methods isDirectory() and setExternalAttributes(long) of the receiver. V1 part: the facade keeps the
original's single field write platform = PLATFORM_UNIX after the call (the private field platform has only a protected setter, which a
hop in another package cannot call, and V2 hops call public methods only). The private constant SHORT_SHIFT is the literal 16 in the gold
(a value, not logic). No private method of the class is called (no V4); no package-private type is involved (no V3/V5). No visibility is
widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit.
state_passed: the receiver `this` (as ZipArchiveEntry) and the int mode, handed to hop 1; no value is returned; the facade then writes the
private field platform = PLATFORM_UNIX, as the original did.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Compress-6-probe of the fixture, the first statement of
setUnixMode was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.compress.archivers.zip.ZipArchiveEntryTest::testUnixMode`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at ZipArchiveEntry.setUnixMode(ZipArchiveEntry.java:203), called from ZipArchiveEntryTest.testUnixMode
(ZipArchiveEntryTest.java:171). Full suite with that probe: 1 failing test (testUnixMode only; setUnixMode has no production caller).
The same probe on equals: testNotEquals fails with PROBE-REACHED at ZipArchiveEntry.equals(ZipArchiveEntry.java:457); full suite with
the equals probe: 3 failing tests (testNotEquals, ChangeSetTestCase::testAddChangeTwice, ::testAddChangeTwiceWithoutReplace).

Hosts (host_mode = "largest5"; batch9_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 compressors.bzip2.BZip2CompressorOutputStream 1880 lines  storeUnixMode     pass-through
  hop 2 compressors.bzip2.BZip2CompressorInputStream   968 lines  applyUnixMode     pass-through
  hop 3 archivers.zip.ZipArchiveOutputStream           945 lines  recordUnixMode    pass-through
  hop 4 archivers.cpio.CpioArchiveEntry                805 lines  assignUnixMode    pass-through
  hop 5 archivers.tar.TarArchiveEntry                  700 lines  setUnixAttributes GOLD: the external attributes from the mode and
                                                                                    the entry (upper half, read-only and directory)
Host newline counts 1880, 968, 945, 805, 700; the smallest host (and the gold host) is TarArchiveEntry with 700 lines (C10F addendum
section 1: hosts under 1500 lines are expected in this regime). The computation of setUnixMode is one attribute word; there is no fold or
placement step that a hop could carry without becoming a second place where the low attribute bits are decided, so hops 1-4 are
pass-throughs and the whole per-entry decision is in the gold.
The correct configuration sets exactly the original external attributes for every mode and entry (the same int expression, widened to
long by setExternalAttributes as in the original) and the same platform.

Fault (one-line omission of a special-case decision in the gold): the directory term `| (entry.isDirectory() ? 0x10 : 0)` is dropped
from the gold's attribute word, so a directory entry gets no MS-DOS directory attribute. The gold then reads as the ordinary routine
"the Unix mode in the upper half, a read-only mark when the mode is not writable". Trigger: the EXISTING test
ZipArchiveEntryTest::testUnixMode; its assertions for the file entry "foo" (0755 and 0444) still hold, and for the directory entry
"foo/" with 0777, assertEquals(0x10, ze.getExternalAttributes() & 0xFFFF) fails with expected:<16> but was:<0>. It is the only test
that newly fails: setUnixMode has no production caller and no other test calls it (the probe's full-suite run), and the new hops have no
other caller.

The gold's javadoc states the idiomatic contract (the external attributes of a zip entry from Unix permissions "in a way that is
understood by Info-Zip's unzip command", the facade's own wording; the permissions in the upper sixteen bits) and is silent on the low
attribute bits; in that layout a directory entry carries the MS-DOS directory attribute 0x10 in the low byte, which the variant does not
set for "foo/". The convention that an entry's stored attributes mark it as a directory is pinned outside the gold: AsiExtraField.getMode
(int) ("the file mode for given permissions with the correct file type": DIR_FLAG for a directory entry, the zip Unix extra field's
directory mark, used in production by setMode/setDirectory/parseFromLocalFileData), ZipArchiveEntry.isDirectory (a name ending in '/',
the test of the gold) and ZipArchiveEntry.getUnixMode (reads the permissions back from the upper sixteen bits); passing tests
AsiExtraFieldTest::testModes ("directory" 040123) and AsiExtraFieldTest::testReparse (the directory mark parsed back), and the file-entry
assertions at the start of the trigger.

Single owner: only the gold decides the attribute word; hops 1-4 pass the entry and the mode along unchanged, and the facade only writes
the platform. Every one-line change of the mode above the gold also changes the upper sixteen bits, which the trigger checks (0777 for
"foo/"), and the low byte is computed from the mode only through the owner-write bit. Declared alternatives (G9): hop 4 marks a
directory's mode with the cpio directory type C_ISDIR; hop 1 adds 0x10 to a directory's mode; hop 3 clears the owner-write bit of a
directory's mode. None makes the trigger pass.
Recorded bypasses (edits that redo the gold's work after it, not repairs of the chain):
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.
 B-1 a hop (or the facade) adds a line after its call that sets the attributes again with the directory term
     (`entry.setExternalAttributes(entry.getExternalAttributes() | (entry.isDirectory() ? 0x10 : 0));`): a second implementation of the
     gold's directory decision applied to the word the gold wrote; the gold still writes no directory attribute against its own
     javadoc. Checked on the variant in the scratch copy /private/tmp/d4j-mi-Compress-6-bypass (the line added after hop 4's call):
     trigger passes, full suite 0 failing tests.

Lie: the facade's javadoc claims the external attributes are assembled one byte at a time, starting from the lowest, and written to the
entry once all four bytes are known; the chain computes one int expression and writes it in one call. It names neither directories, the
omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: entry is the target of the write and is tested by isDirectory(); mode is placed in the upper half and decides the
     read-only term; neither is only argument-checked (no argument check).
  T2 absent: no local variable; both ternaries give two different values (1/0, 0x10/0); no loop, cursor, counter, flag or best-so-far.
  T3 absent: no closed set is treated in part: the gold's text names no attribute class ("MS-DOS attributes", "file type"); the
     owner-write bit is the one mode bit tested (exactly one member of the unnamed set of mode bits, which are all placed in the upper
     half); the two halves of the word are both written.
  T4 absent: 'from Unix permissions, in a way that is understood by Info-Zip's unzip command' is a general description that the write
     addresses; 'The permissions are kept in the upper sixteen bits of the attributes' is met by mode << 16; the @param clauses name no
     rule; no inline comment; identifiers (entry, mode, setUnixAttributes) name what they hold.
 Variant gold (javadoc, signature, entry.setExternalAttributes((mode << 16) | ((mode & 0200) == 0 ? 1 : 0))):
  T1 absent: entry is the target of the write (a side effect); mode is placed in the upper half and decides the read-only term.
  T2 absent: no local variable; the ternary gives two different values; no dead or frozen decision.
  T3 absent: the low byte has one term (read-only) and the gold's text names no class of attributes, so 'One member of a larger unnamed
     set' (no sibling attribute is handled and none is named); no directory or file-type treatment remains ('No member handled'); both
     halves of the word are written; no enum or type code is read.
  T4 absent: 'in a way that is understood by Info-Zip's unzip command' is a general description, met by the write; 'kept in the upper
     sixteen bits' is met; the @param clauses ('The zip entry whose attributes are set', 'The Unix permissions') name no rule; no inline
     comment; no identifier names a directory, a type or a bound."""

ZAE = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveEntry.java"
BZO = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
BZI = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorInputStream.java"
ZAO = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
CPIO = "src/main/java/org/apache/commons/compress/archivers/cpio/CpioArchiveEntry.java"
TAR = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"

GOLD_TEXT = '''/**
 * Set the external attributes of a zip entry from Unix permissions,
 * in a way that is understood by Info-Zip's unzip command.
 *
 * <p>The permissions are kept in the upper sixteen bits of the
 * attributes.</p>
 *
 * @param entry The zip entry whose attributes are set.
 * @param mode The Unix permissions.
 */
public static void setUnixAttributes(ZipArchiveEntry entry, int mode) {
    entry.setExternalAttributes((mode << 16)
        | ((mode & 0200) == 0 ? 1 : 0)
        | (entry.isDirectory() ? 0x10 : 0));
}'''

HOP1 = '''/**
 * Sets the external attributes of a zip entry from the given Unix
 * permissions.
 *
 * @param entry
 *            the zip entry whose attributes are set.
 * @param mode
 *            the Unix permissions.
 */
public static void storeUnixMode(ZipArchiveEntry entry, int mode) {
    BZip2CompressorInputStream.applyUnixMode(entry, mode);
}'''

HOP2 = '''/**
 * Sets the external attributes of a zip entry from the given Unix
 * permissions.
 *
 * @param entry
 *            the zip entry whose attributes are set.
 * @param mode
 *            the Unix permissions.
 */
public static void applyUnixMode(ZipArchiveEntry entry, int mode) {
    ZipArchiveOutputStream.recordUnixMode(entry, mode);
}'''

HOP3 = '''/**
 * Sets the external attributes of the given entry from Unix
 * permissions.
 *
 * @param entry the entry whose attributes are set
 * @param mode the Unix permissions
 */
public static void recordUnixMode(ZipArchiveEntry entry, int mode) {
    CpioArchiveEntry.assignUnixMode(entry, mode);
}'''

HOP4 = '''/**
 * Set the external attributes of a zip entry from Unix permissions.
 *
 * @param entry
 *            The zip entry whose attributes are set.
 * @param mode
 *            The Unix permissions.
 */
public static void assignUnixMode(ZipArchiveEntry entry, int mode) {
    TarArchiveEntry.setUnixAttributes(entry, mode);
}'''

DESIGN = {
 "instance": "Compress-6", "project": "Compress", "bug_id": 6, "seed": 8902,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2+V1",
 "state_passed": "the receiver this (as ZipArchiveEntry) and mode, passed to hop 1 (hops call only its public isDirectory() and "
                 "setExternalAttributes(long)); no return value; the facade keeps the field write platform = PLATFORM_UNIX",
 "host_mode": "largest5", "host_lines": [1880, 968, 945, 805, 700],
 "facade_reuse_of": "Compress-13__i (planned facade setUnixMode; the distinct candidate equals cannot carry the recipe)",
 "reachability_probe": "setUnixMode first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Compress-6-probe: ZipArchiveEntryTest::testUnixMode fails with PROBE-REACHED at "
                       "ZipArchiveEntry.setUnixMode(ZipArchiveEntry.java:203); full suite: 1 failing test (testUnixMode only)",
 "facade": {"file": ZAE, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveEntry", "method": "setUnixMode",
            "near_line": 202},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/zip/ZipArchiveEntryTest.java",
             "test_class": "org.apache.commons.compress.archivers.zip.ZipArchiveEntryTest", "test_method": "testUnixMode"},
 "expected_signature": "expected:<16> but was:<0>",
 "gold": {"method": "setUnixAttributes", "text": GOLD_TEXT,
          "fault": {"old": "            | ((mode & 0200) == 0 ? 1 : 0)\n            | (entry.isDirectory() ? 0x10 : 0));",
                    "new": "            | ((mode & 0200) == 0 ? 1 : 0));"}},
 "chain": {
   "facade_body": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream.storeUnixMode(this, mode);\n"
                  "        platform = PLATFORM_UNIX;",
   "lie": "The external attributes are assembled one byte at a time, starting from the lowest, and are written to the entry once "
          "all four bytes are known.",
   "hops": [
     {"file": BZO, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "storeUnixMode",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveEntry"], "text": HOP1},
     {"file": BZI, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream", "method": "applyUnixMode",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveEntry",
                  "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream"], "text": HOP2},
     {"file": ZAO, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "recordUnixMode",
      "imports": ["org.apache.commons.compress.archivers.cpio.CpioArchiveEntry"], "text": HOP3},
     {"file": CPIO, "class": "org.apache.commons.compress.archivers.cpio.CpioArchiveEntry", "method": "assignUnixMode",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry",
                  "org.apache.commons.compress.archivers.zip.ZipArchiveEntry"], "text": HOP4},
     {"file": TAR, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "setUnixAttributes",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveEntry"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.zip.AsiExtraField::getMode",
              "org.apache.commons.compress.archivers.zip.ZipArchiveEntry::isDirectory",
              "org.apache.commons.compress.archivers.zip.ZipArchiveEntry::getUnixMode"],
 "ownership_reason": "Only the gold decides the external attribute word of the entry: the Unix permissions in the upper sixteen bits "
                     "and the low byte (a read-only mark when the owner-write bit is clear, the directory attribute 0x10 for a "
                     "directory entry). Hops 1-4 pass the entry and the mode along unchanged and the facade only writes the platform; "
                     "any change of the mode above the gold also changes the upper sixteen bits, which the trigger checks. The gold's "
                     "javadoc promises the attributes 'in a way that is understood by Info-Zip's unzip command', in which a directory "
                     "entry carries the MS-DOS directory attribute in the low byte; the variant writes 0 there for 'foo/'. The "
                     "convention that an entry's stored attributes mark it as a directory is pinned outside the gold: "
                     "AsiExtraField.getMode(int) gives a directory entry's stored mode the directory type DIR_FLAG ('the file mode "
                     "for given permissions with the correct file type'), ZipArchiveEntry.isDirectory defines a directory entry (a "
                     "name ending in '/') and ZipArchiveEntry.getUnixMode reads the permissions back from the upper sixteen bits; "
                     "AsiExtraFieldTest::testModes and ::testReparse pass, and the trigger's file-entry assertions hold.",
 "ownership_tests": ["org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testModes",
                     "org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testReparse"],
 "compensating": {
   "chain": [
     {"file": CPIO, "old": "TarArchiveEntry.setUnixAttributes(entry, mode);",
      "new": "TarArchiveEntry.setUnixAttributes(entry, entry.isDirectory() ? mode | C_ISDIR : mode);",
      "why": "hop 4 marks a directory's mode with the cpio directory type C_ISDIR"},
     {"file": BZO, "old": "BZip2CompressorInputStream.applyUnixMode(entry, mode);",
      "new": "BZip2CompressorInputStream.applyUnixMode(entry, entry.isDirectory() ? mode | 0x10 : mode);",
      "why": "hop 1 adds 0x10 to a directory's mode"},
     {"file": ZAO, "old": "CpioArchiveEntry.assignUnixMode(entry, mode);",
      "new": "CpioArchiveEntry.assignUnixMode(entry, entry.isDirectory() ? mode & ~0200 : mode);",
      "why": "hop 3 clears the owner-write bit of a directory's mode"},
   ],
 },
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, used in that order; none substituted, none drawn by this "
               "builder): compressors.bzip2.BZip2CompressorOutputStream (hop 1, 1880 lines), compressors.bzip2."
               "BZip2CompressorInputStream (hop 2, 968), archivers.zip.ZipArchiveOutputStream (hop 3, 945), archivers.cpio."
               "CpioArchiveEntry (hop 4, 805), archivers.tar.TarArchiveEntry (hop 5, gold, 700; the smallest host). All five are "
               "public concrete top-level classes in which a public static method compiles; the facade's class ZipArchiveEntry "
               "(facade_files_excluded) is not a host. Anchors from stageB_lib.pick_anchor with seed 8902 + 100 + i, as mr3_spec.py "
               "inserts them (recorded in the spec's stage_b block). The facade calls hop 1 by its fully-qualified name; each hop "
               "imports ZipArchiveEntry (except hop 3, in its package) and the next host (except hop 1, whose next host is in its "
               "package).",
}
