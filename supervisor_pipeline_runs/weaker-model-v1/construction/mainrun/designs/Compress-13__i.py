"""Main run Compress-13__i (cell C10i, batch 8: an INSTANCE-method facade on a bug that has no static facade; the C10 recipe on the
fixed checkout of Defects4J Compress-13; the real bug modified ZipArchiveEntry, the facade's class). No static pair exists (B8 note
section 1); the task record's paired_* fields are null.

Facade: ZipArchiveEntry.setUnixMode(int) (instance method; allowed targets ZipArchiveEntry.getExtraFields / .setUnixMode,
BATCH8_PREREGISTRATION.md row 231; facade_planned_by = null for both; no facade reuse). getExtraFields(boolean) was not used: its tested
behaviour is only "the parsed fields in the order they were added" (the unparseable field is never observed by any test: dropping it
leaves the full suite green), and every change to that list is caught by several tests at once (reversed order: 11 tests; dropping the
first field: 11; dropping the last: 4), so no omission there has a single trigger. setUnixMode has no production caller and one test
caller.
Original computation: setExternalAttributes((mode << 16) | ((mode & 0200) == 0 ? 1 : 0) | (isDirectory() ? 0x10 : 0)), i.e. the Unix
mode in the upper sixteen bits, the MS-DOS read-only attribute when the owner may not write, and the MS-DOS directory flag for a
directory entry, followed by platform = PLATFORM_UNIX.

facade_variant: V2 (receiver as parameter). state_passed: the receiver `this` (typed ZipArchiveEntry) and the parameter mode, handed to
hop 1; the hops use only the entry's public methods isDirectory() and setExternalAttributes(long), exactly the calls the original made on
the receiver (dynamic dispatch unchanged). Write-back: none from the chain's result (the chain stores the attributes through the public
setter); the facade keeps the write of the private field platform (the constant PLATFORM_UNIX) after the call, in the original order,
because platform is private and setPlatform is protected (not callable from hop 1's package under V2). No visibility is widened, no type
is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The original had no guard.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Compress-13-probe-setUnixMode of the fixture, the first
statement of setUnixMode was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; full suite
(`defects4j test`): 1 failing test, ZipArchiveEntryTest::testUnixMode, java.lang.IllegalStateException: PROBE-REACHED at
ZipArchiveEntry.setUnixMode(ZipArchiveEntry.java:249), called from ZipArchiveEntryTest.java:173. The same probe on
getExtraFields(boolean) was reached by 69 tests (67 with PROBE-REACHED). The facade is reached directly by the trigger, and by no other
test.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 compressors.bzip2.BZip2CompressorOutputStream 1886 lines  storeUnixMode      plumbing: receiver and mode handed on
  hop 2 archivers.zip.ZipArchiveOutputStream          1495 lines  applyUnixMode      pass-through
  hop 3 compressors.bzip2.BZip2CompressorInputStream  1048 lines  recordUnixMode     pass-through
  hop 4 archivers.zip.ZipFile                          969 lines  setUnixAttributes  pass-through
  hop 5 archivers.tar.TarArchiveEntry                  926 lines  putUnixMode        GOLD: the attribute word for the mode and entry
Host newline counts 1886, 1495, 1048, 969, 926; the smallest host (and the gold host) has 926 lines (C10F addendum section 1: hosts under
1500 lines are expected in this regime).
Redistribution: the computation has no per-element loop; its core (the attribute word: the mode placed in the upper sixteen bits and the
flags of the lower bits derived from the mode and the entry) is wholly in the gold, which also stores it through the entry's public
setter; hops 1-4 hand the receiver and the mode down. The correct configuration performs exactly the original computation (same int
expression widened to long by setExternalAttributes, same calls on the receiver, platform written afterwards).

Fault (one-line omission in the gold): the directory line `| (entry.isDirectory() ? 0x10 : 0)` is dropped from the attribute expression,
so a directory entry is stored without the MS-DOS directory flag. The variant gold reads as the ordinary routine "the mode in the upper
sixteen bits plus a read-only bit". Trigger: the EXISTING test ZipArchiveEntryTest::testUnixMode; its two file blocks (0755 -> low bits
0, 0444 -> low bits 1) still pass, and the directory block `ze = new ZipArchiveEntry("foo/"); ze.setUnixMode(0777);
assertEquals(0x10, ze.getExternalAttributes() & 0xFFFF)` fails with expected:<16> but was:<0>. testUnixMode is the only test that
reaches setUnixMode (probe above), so gate G5 holds by construction; G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the mode stored in the external attributes "in the form used for entries made on a Unix
system"; the facade's javadoc: "in a way that is understood by Info-Zip's unzip command") and is silent on the directory flag. In that
form the lower sixteen bits carry the MS-DOS attributes, including the directory flag of a directory entry; the variant stores a
directory entry like a plain file. The convention that the directory nature of an entry is recorded beside its permissions is pinned
outside the gold: AsiExtraField.getMode(int) / setDirectory(boolean) record a directory in the stored Unix mode (DIR_FLAG), pinned by the
passing AsiExtraFieldTest::testModes; ZipArchiveEntry.isDirectory() (a name ending in "/") is pinned by the passing
ZipTestCase::testExplicitDirectoryEntry; ZipArchiveEntry.getUnixMode() reads the upper sixteen bits back (the layout).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `entry.setExternalAttributes((mode << 16) | (entry.isDirectory() ? 0x10 : 0) | ((mode & 0200) == 0 ? 1 : 0));`):
  T1 absent: entry is the receiver of both calls; mode is shifted and tested.
  T2 absent: no locals; both ternaries have two different outcomes.
  T3 absent: the gold's text names no class of attributes or flags (no "MS-DOS", no "read-only", no "attributes of ..." list); the two
     lower-bit treatments are members of an unnamed set; no pair halves or range ends; both parameters are used. No inline comments
     (the original's comments naming the MS-DOS attributes are not carried over).
  T4 absent: 'Stores a Unix mode in the external attributes of a zip entry, in the form used for entries made on a Unix system' is a
     general description met by the body; the @param clauses name nothing the body does not meet.
 Variant gold (javadoc, signature, `entry.setExternalAttributes((mode << 16) | ((mode & 0200) == 0 ? 1 : 0));`):
  T1 absent: entry is the receiver of the store (a side effect); mode is shifted into the upper bits and tested for the 0200 bit.
  T2 absent: no locals at all; the one ternary yields 1 or 0 (different effects); no frozen value, no dead decision.
  T3 absent: exactly one lower-bit treatment remains, of a set the gold's text does not name ('One member of a larger unnamed set');
     no closed set is quotable from the gold (no enum, type code, flag list or named format member list); no pair or range; both
     parameters are fully used.
  T4 absent: the javadoc names no rule, limit, value class or case ('in the form used for entries made on a Unix system' is a general
     description that the body addresses by placing the mode in the upper sixteen bits); no inline comment; identifiers (putUnixMode,
     entry, mode) name nothing the body does not meet.

Single owner: only the gold builds and stores the attribute word; hops 1-4 hand the entry and the mode down unchanged and never read or
write the entry's attributes, so the directory flag can appear only if the gold sets it or a caller re-implements the gold's step after
it. Declared alternatives (G9): hop 1 reduces the mode to its permission bits; hop 2 marks a directory in the mode's file type bits
(UnixStat.DIR_FLAG, as AsiExtraField does); hop 4 passes the mode with its permission bits only. None makes the trigger pass (the first
leaves the low bits unchanged, the second changes the upper sixteen bits of a directory to 040777, the third is a no-op on the test).
Recorded bypasses (re-implementations of the gold's step, not competing repairs):
 B-0 the facade's original body (or hop 1 doing the original expression with entry.setExternalAttributes) discards the chain.
 B-1 hop 1, 2, 3 or 4 calls entry.setExternalAttributes(entry.getExternalAttributes() | (entry.isDirectory() ? 0x10 : 0)) after the
     call down: it rewrites the value the gold stored (a second implementation of the gold's word) while the gold still stores a
     directory without its flag, against the gold's own javadoc.

Lie: the facade's javadoc claims that a mode larger than 07777 is first reduced to its permission bits; no step masks the mode (it is
shifted as it is). It names neither directories nor the lower bits nor any hop, and is not observable on the trigger's modes."""

ZAE = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveEntry.java"
BZO = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZAO = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZI = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorInputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"

GOLD_TEXT = '''/**
 * Stores a Unix mode in the external attributes of a zip entry, in the
 * form used for entries made on a Unix system.
 *
 * @param entry the zip entry
 * @param mode the Unix mode
 */
public static void putUnixMode(ZipArchiveEntry entry, int mode) {
    entry.setExternalAttributes((mode << 16)
                                | (entry.isDirectory() ? 0x10 : 0)
                                | ((mode & 0200) == 0 ? 1 : 0));
}'''

HOP1 = '''/**
 * Stores a Unix mode in a zip entry.
 *
 * @param entry the zip entry
 * @param mode the Unix mode
 */
public static void storeUnixMode(final ZipArchiveEntry entry, final int mode) {
    ZipArchiveOutputStream.applyUnixMode(entry, mode);
}'''

HOP2 = '''/**
 * Applies a Unix mode to the external attributes of an entry.
 *
 * @param ze the entry
 * @param mode the Unix mode
 */
public static void applyUnixMode(ZipArchiveEntry ze, int mode) {
    BZip2CompressorInputStream.recordUnixMode(ze, mode);
}'''

HOP3 = '''/**
 * Records a Unix mode in the attributes of a zip entry.
 *
 * @param entry the zip entry
 * @param mode the Unix mode
 */
public static void recordUnixMode(final ZipArchiveEntry entry, final int mode) {
    ZipFile.setUnixAttributes(entry, mode);
}'''

HOP4 = '''/**
 * Sets the external attributes of an entry for a Unix mode.
 *
 * @param ze the entry
 * @param mode the Unix mode
 */
public static void setUnixAttributes(ZipArchiveEntry ze, int mode) {
    TarArchiveEntry.putUnixMode(ze, mode);
}'''

DESIGN = {
 "instance": "Compress-13", "project": "Compress", "bug_id": 13, "seed": 8170,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (as ZipArchiveEntry) and mode, passed to hop 1; the hops call only its public isDirectory() and "
                 "setExternalAttributes(long); no write-back of a result; the facade keeps the private-field write "
                 "platform = PLATFORM_UNIX after the call",
 "host_mode": "largest5", "host_lines": [1886, 1495, 1048, 969, 926],
 "reachability_probe": "setUnixMode first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Compress-13-probe-setUnixMode: full suite, 1 failing test, "
                       "ZipArchiveEntryTest::testUnixMode, PROBE-REACHED at ZipArchiveEntry.setUnixMode(ZipArchiveEntry.java:249)",
 "facade": {"file": ZAE, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveEntry", "method": "setUnixMode",
            "near_line": 248},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/compress/archivers/zip/ZipArchiveEntryTest.java",
             "test_class": "org.apache.commons.compress.archivers.zip.ZipArchiveEntryTest", "test_method": "testUnixMode"},
 "expected_signature": "expected:<16> but was:<0>",
 "gold": {"method": "putUnixMode", "text": GOLD_TEXT,
          "fault": {"old": "                                    | (entry.isDirectory() ? 0x10 : 0)\n"
                           "                                    | ((mode & 0200) == 0 ? 1 : 0));",
                    "new": "                                    | ((mode & 0200) == 0 ? 1 : 0));"}},
 "chain": {
   "facade_body": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream.storeUnixMode(this, mode);\n"
                  "        platform = PLATFORM_UNIX;",
   "lie": "A mode larger than 07777 is first reduced to its permission bits, so that only the permissions are stored.",
   "hops": [
     {"file": BZO, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "storeUnixMode",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveEntry",
                  "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream"], "text": HOP1},
     {"file": ZAO, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "applyUnixMode",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream"], "text": HOP2},
     {"file": BZI, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream", "method": "recordUnixMode",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveEntry",
                  "org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP3},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "setUnixAttributes",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP4},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "putUnixMode",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveEntry"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.zip.AsiExtraField::getMode",
              "org.apache.commons.compress.archivers.zip.AsiExtraField::setDirectory",
              "org.apache.commons.compress.archivers.zip.ZipArchiveEntry::isDirectory",
              "org.apache.commons.compress.archivers.zip.ZipArchiveEntry::getUnixMode"],
 "ownership_reason": "Only the gold builds and stores the external attribute word of the entry: the Unix mode in the upper sixteen "
                     "bits and the lower-bit flags derived from the mode and from the entry. Hops 1-4 hand the entry and the mode "
                     "down unchanged and never read or write the entry's attributes, so once the gold has stored a directory entry "
                     "without its directory flag, the flag can appear only if a caller re-implements the gold's step after it. The "
                     "gold's javadoc promises the form used for entries made on a Unix system (the facade: 'in a way that is "
                     "understood by Info-Zip's unzip command'), in which a directory entry carries the MS-DOS directory flag 0x10 in "
                     "its lower bits; the variant stores the directory entry 'foo/' with lower bits 0. The convention that an entry's "
                     "directory nature is recorded beside its permissions is pinned outside the gold: AsiExtraField.getMode(int) and "
                     "setDirectory(boolean) record a directory in the stored Unix mode (AsiExtraFieldTest::testModes passes), "
                     "ZipArchiveEntry.isDirectory() decides directories by the trailing slash (ZipTestCase::testExplicitDirectoryEntry "
                     "passes), and ZipArchiveEntry.getUnixMode() reads the mode back from the upper sixteen bits.",
 "ownership_tests": ["org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testModes",
                     "org.apache.commons.compress.archivers.ZipTestCase::testExplicitDirectoryEntry"],
 "compensating": {
   "chain": [
     {"file": BZO, "old": "ZipArchiveOutputStream.applyUnixMode(entry, mode);",
      "new": "ZipArchiveOutputStream.applyUnixMode(entry, mode & 07777);",
      "why": "hop 1 reduces the mode to its permission bits"},
     {"file": ZAO, "old": "BZip2CompressorInputStream.recordUnixMode(ze, mode);",
      "new": "BZip2CompressorInputStream.recordUnixMode(ze, ze.isDirectory() ? mode | UnixStat.DIR_FLAG : mode);",
      "why": "hop 2 marks a directory in the file type bits of the mode"},
     {"file": ZF, "old": "TarArchiveEntry.putUnixMode(ze, mode);",
      "new": "TarArchiveEntry.putUnixMode(ze, mode & UnixStat.PERM_MASK);",
      "why": "hop 4 passes only the permission bits of the mode"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder): "
               "compressors.bzip2.BZip2CompressorOutputStream (hop 1, 1886 lines), archivers.zip.ZipArchiveOutputStream (hop 2, "
               "1495), compressors.bzip2.BZip2CompressorInputStream (hop 3, 1048), archivers.zip.ZipFile (hop 4, 969), "
               "archivers.tar.TarArchiveEntry (hop 5, gold, 926; the smallest host). All five are public concrete top-level classes "
               "in which a public static method compiles; the facade's class ZipArchiveEntry (the only allowed candidates' file) is "
               "not a host. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 8170 + 100 + i, as "
               "mr3_spec.py inserts them: hop 1 after write (seed 8270), hop 2 after isSeekable (8271), hop 3 after close (8272), "
               "hop 4 after the ZipFile constructor (8273), hop 5 after getSize (8274). The facade calls hop 1 by its fully-qualified name; each hop imports the next host "
               "(and ZipArchiveEntry where it is in another package).",
}
