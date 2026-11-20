"""Main run Compress-15__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; the
fixed checkout of Defects4J Compress-15, whose real bug modified ZipArchiveEntry, the facade's class). No static pair exists (B8 note
section 1).

Facade: ZipArchiveEntry.setUnixMode(int) (instance method; allowed candidates ZipArchiveEntry.getExtraFields / .setUnixMode,
BATCH8_PREREGISTRATION.md row 232). setUnixMode has facade_planned_by = null and is preferred (B8 note section 3); it is used, so
there is no effective facade reuse (the record's facade_reuse_of, Compress-13__i, concerns getExtraFields only). getExtraFields(boolean)
was not used: it is called by setExtra() on every change of the extra fields and by every archive write, so no omission in it is
caught by exactly one existing test.
Original computation: the external attributes become (mode << 16) | (the mode lacks the owner-write bit 0200 ? 1 : 0) |
(isDirectory() ? 0x10 : 0) (an int, widened to long by setExternalAttributes), set with the public setExternalAttributes(long); then the
private field platform is set to PLATFORM_UNIX.

facade_variant: V2 (receiver as parameter). state_passed: the receiver `this` (typed ZipArchiveEntry) and the parameter mode, handed to
hop 1; the hops call only the receiver's public methods isDirectory() and setExternalAttributes(long). The facade keeps the original
assignment `platform = PLATFORM_UNIX;` of its private field after the call (a constant; the only setter, setPlatform, is protected, so
no hop calls it). No value is returned. The facade body is one call to hop 1 plus that original field write; setUnixMode has no
argument guard. No visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no
reflection, no test edit. setUnixMode calls no private method (V4 does not apply) and needs no package-private type (V3/V5 do not
apply).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Compress-15-probe of the fixture, the first statement
of setUnixMode was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.compress.archivers.zip.ZipArchiveEntryTest::testUnixMode`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at ZipArchiveEntry.setUnixMode(ZipArchiveEntry.java:249), called from ZipArchiveEntryTest.java:175. The full suite
with the probe: testUnixMode is the only failing test, so it is the only existing test that reaches setUnixMode.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 archivers.zip.ZipArchiveOutputStream          1495 lines  applyUnixMode         pass-through
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1340 lines  recordUnixMode        pass-through
  hop 3 archivers.tar.TarArchiveEntry                 1056 lines  storeMode             pass-through
  hop 4 compressors.bzip2.BZip2CompressorInputStream  1053 lines  transferMode          pass-through
  hop 5 archivers.zip.ZipFile                          972 lines  assignUnixAttributes  GOLD: builds the attribute word from the mode
                                                                                         and the entry, and sets it on the entry
Host newline counts 1495, 1340, 1056, 1053, 972; the smallest host (and the gold host) has 972 lines (C10F addendum section 1: hosts
under 1500 lines are expected in this regime).
The correct configuration computes exactly the original value (same int expression, same order of the receiver calls) for every
mode and every entry.

Fault (one-line omission of a special-case step in the gold): the directory step `attributes |= entry.isDirectory() ? 0x10 : 0;` is
dropped, so a directory entry gets the same attributes as a plain file with the same mode. The gold then reads as the ordinary routine
"place the mode in the upper two bytes, mark a mode without owner write, set the attributes". Trigger: the EXISTING test
ZipArchiveEntryTest::testUnixMode; for the entry "foo/" with mode 0777 its assertion assertEquals(0x10, ze.getExternalAttributes() &
0xFFFF) fails with expected:<16> but was:<0>. It is the only test that reaches setUnixMode (probe above), and gate G5 checks the full
suite.

The gold's javadoc states the idiomatic contract (it sets the external attributes of the entry from its Unix mode, the mode in the
upper two bytes) and is silent on directories and on the lower bytes. The external attributes are those the facade's own javadoc
describes (understood by Info-Zip's unzip), in which a directory entry carries the directory attribute 0x10 in the lower byte; the
variant leaves it out for the entry "foo/". The convention that a directory entry's Unix attributes record that it is a directory is
pinned outside the gold: AsiExtraField.getMode(int) (production: the mode stored for a directory entry carries the directory type
DIR_FLAG), ZipArchiveEntry.isDirectory() (a name ending in "/" is a directory) and ZipArchiveEntry.getUnixMode() (the mode is read back
from the upper two bytes); passing tests AsiExtraFieldTest::testModes and ::testReparse (a directory's mode carries the directory type)
and ZipTestCase::testExplicitDirectoryEntry (the entry "foo/" is a directory).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: mode is shifted into the attributes and tested for 0200; entry is asked isDirectory() and receives the attributes.
  T2 absent: attributes is assigned from mode, updated twice and passed to setExternalAttributes; each ternary has two different
     outcomes; no literal-initialised or loop variable.
  T3 absent: no class of attributes, flags or bits is named in the gold's text; the two lower-byte marks it sets belong to no closed
     set fixed by the gold's text, a Java type or a named format; upper and lower halves are both written.
  T4 absent: 'Sets the external attributes of an entry from its Unix mode' and 'The mode is held in the upper two bytes of the
     attributes' are met by `mode << 16` and setExternalAttributes; the @param clauses are met.
 Variant gold (javadoc, signature, `int attributes = mode << 16;`, `attributes |= (mode & 0200) == 0 ? 1 : 0;`,
 `entry.setExternalAttributes(attributes);`):
  T1 absent: mode is read twice (shift, 0200 test) and changes the result; entry receives the attributes (a side effect); neither is
     only argument-checked.
  T2 absent: attributes is not initialised to a literal, is updated and reaches the setter; the ternary has two different outcomes;
     no loop; no dead local.
  T3 absent: exactly one lower-byte mark (the one derived from 0200) is set, and the gold names no class of marks ('One member of a
     larger unnamed set'); the gold tests no other flag and reads no other member; the upper half (mode) and the lower half (the mark)
     are both written.
  T4 absent: 'from its Unix mode' and 'held in the upper two bytes' are met; 'the entry whose attributes are set' is met by
     setExternalAttributes; no inline comment; identifiers (attributes, entry, mode, assignUnixAttributes) name nothing the body does
     not meet.

Single owner: only the gold builds the attribute word; hops 1-4 pass the entry and the mode along unchanged and set nothing themselves,
and the facade adds only the platform. No input a caller can pass makes the variant set 0x10 in the lower bytes (the lower bytes hold
only the 0200 mark), so the omission cannot be pre-filtered above the gold. Declared alternatives (G9): hop 1 adds the Unix directory
type DIR_FLAG to the mode of a directory entry; hop 3 keeps only the permission bits (07777) of the mode; hop 4 ORs 0x10 into the mode
of a directory entry. None makes the trigger pass (the first changes the upper half; the others leave the lower bytes as they are).
Recorded bypasses (one-line edits that overwrite the gold's result):
 B-0 the facade's original body sets the attributes itself, discarding the chain including the gold.
 B-1 a hop (1-4), after its call, adds `entry.setExternalAttributes(entry.getExternalAttributes() | (entry.isDirectory() ? 0x10 :
     0));`: a second implementation of the gold's directory step that rewrites the attributes the gold set, against the hop's
     documentation that it only passes the entry and the mode on.

Lie: the facade's javadoc claims the set-user-ID, set-group-ID and sticky bits are cleared from the mode before it is stored; no step of
the chain masks the mode (it is shifted as it is). It names neither directories nor the lower bytes nor any hop."""

ZAE = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveEntry.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZO = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
BZI = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorInputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"

GOLD_TEXT = '''/**
 * Sets the external attributes of an entry from its Unix mode.
 *
 * <p>The mode is held in the upper two bytes of the attributes.</p>
 *
 * @param entry the entry whose attributes are set
 * @param mode the Unix mode of the entry
 */
public static void assignUnixAttributes(ZipArchiveEntry entry, int mode) {
    int attributes = mode << 16;
    attributes |= (mode & 0200) == 0 ? 1 : 0;
    attributes |= entry.isDirectory() ? 0x10 : 0;
    entry.setExternalAttributes(attributes);
}'''

HOP1 = '''/**
 * Sets the external attributes of an entry, as they are written to
 * the central directory, from its Unix mode.
 *
 * <p>The entry and the mode are passed on unchanged.</p>
 *
 * @param entry the entry whose attributes are set
 * @param mode the Unix mode of the entry
 */
public static void applyUnixMode(ZipArchiveEntry entry, int mode) {
    BZip2CompressorOutputStream.recordUnixMode(entry, mode);
}'''

HOP2 = '''/**
 * Records the Unix mode of an archive entry in its external
 * attributes.
 *
 * <p>The entry and the mode are passed on unchanged.</p>
 *
 * @param entry the entry whose attributes are set
 * @param mode the Unix mode of the entry
 */
public static void recordUnixMode(ZipArchiveEntry entry, int mode) {
    TarArchiveEntry.storeMode(entry, mode);
}'''

HOP3 = '''/**
 * Stores the Unix mode of a zip entry in its external attributes.
 *
 * <p>The entry and the mode are passed on unchanged.</p>
 *
 * @param entry the entry whose attributes are set
 * @param mode the Unix mode of the entry
 */
public static void storeMode(ZipArchiveEntry entry, int mode) {
    BZip2CompressorInputStream.transferMode(entry, mode);
}'''

HOP4 = '''/**
 * Transfers the Unix mode of an archive entry into its external
 * attributes.
 *
 * <p>The entry and the mode are passed on unchanged.</p>
 *
 * @param entry the entry whose attributes are set
 * @param mode the Unix mode of the entry
 */
public static void transferMode(ZipArchiveEntry entry, int mode) {
    ZipFile.assignUnixAttributes(entry, mode);
}'''

DESIGN = {
 "instance": "Compress-15", "project": "Compress", "bug_id": 15, "seed": 8644,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (typed ZipArchiveEntry) and mode, passed to hop 1; hops call its public isDirectory() and "
                 "setExternalAttributes(long); the facade keeps the original write platform = PLATFORM_UNIX after the call; no return value",
 "host_mode": "largest5", "host_lines": [1495, 1340, 1056, 1053, 972],
 "reachability_probe": "setUnixMode first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Compress-15-probe: ZipArchiveEntryTest::testUnixMode fails with PROBE-REACHED at "
                       "ZipArchiveEntry.setUnixMode(ZipArchiveEntry.java:249); full suite: it is the only failing test",
 "facade": {"file": ZAE, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveEntry", "method": "setUnixMode", "near_line": 248},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/zip/ZipArchiveEntryTest.java",
             "test_class": "org.apache.commons.compress.archivers.zip.ZipArchiveEntryTest", "test_method": "testUnixMode"},
 "expected_signature": "expected:<16> but was:<0>",
 "gold": {"method": "assignUnixAttributes", "text": GOLD_TEXT,
          "fault": {"old": "        attributes |= (mode & 0200) == 0 ? 1 : 0;\n        attributes |= entry.isDirectory() ? 0x10 : 0;",
                    "new": "        attributes |= (mode & 0200) == 0 ? 1 : 0;"}},
 "chain": {
   "facade_body": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.applyUnixMode(this, mode);\n"
                  "        platform = PLATFORM_UNIX;",
   "lie": "The set-user-ID, set-group-ID and sticky bits are cleared from the mode before it is stored, since unzip ignores them.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "applyUnixMode",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZO, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "recordUnixMode",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry",
                  "org.apache.commons.compress.archivers.zip.ZipArchiveEntry"], "text": HOP2},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "storeMode",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveEntry",
                  "org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream"], "text": HOP3},
     {"file": BZI, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream", "method": "transferMode",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipArchiveEntry",
                  "org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP4},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "assignUnixAttributes",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.zip.AsiExtraField::getMode",
              "org.apache.commons.compress.archivers.zip.ZipArchiveEntry::isDirectory",
              "org.apache.commons.compress.archivers.zip.ZipArchiveEntry::getUnixMode"],
 "ownership_reason": "Only the gold builds the external attribute word of the entry: it places the Unix mode in the upper two bytes, "
                     "sets the lower-byte marks and sets the word on the entry. Hops 1-4 pass the entry and the mode on unchanged and "
                     "set nothing themselves; the facade adds only the platform. The lower bytes of the variant's word hold only the "
                     "mark derived from the owner-write bit, so no mode a caller passes makes a directory entry carry the directory "
                     "attribute 0x10; once the gold has set the word without it, it can appear only if a caller rewrites the "
                     "attributes the gold set or replaces the gold. The gold promises the external attributes of the entry from its "
                     "Unix mode; the facade documents them as those understood by Info-Zip's unzip, in which a directory carries the "
                     "directory attribute, and the variant leaves it out for the directory entry foo/. The convention that a "
                     "directory entry's Unix attributes record that it is a directory is pinned outside the gold: AsiExtraField."
                     "getMode(int) stores the directory type DIR_FLAG with the mode of a directory entry, ZipArchiveEntry."
                     "isDirectory() makes a name ending in '/' a directory and ZipArchiveEntry.getUnixMode() reads the mode back from "
                     "the upper two bytes; AsiExtraFieldTest::testModes and ::testReparse (a directory's mode carries the directory "
                     "type) and ZipTestCase::testExplicitDirectoryEntry (the entry foo/ is a directory) pass.",
 "ownership_tests": ["org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testModes",
                     "org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testReparse",
                     "org.apache.commons.compress.archivers.ZipTestCase::testExplicitDirectoryEntry"],
 "compensating": {
   "chain": [
     {"file": ZAOS, "old": "    BZip2CompressorOutputStream.recordUnixMode(entry, mode);",
      "new": "    BZip2CompressorOutputStream.recordUnixMode(entry, entry.isDirectory() ? mode | UnixStat.DIR_FLAG : mode);",
      "why": "hop 1 adds the Unix directory type to the mode of a directory entry"},
     {"file": TAE, "old": "    BZip2CompressorInputStream.transferMode(entry, mode);",
      "new": "    BZip2CompressorInputStream.transferMode(entry, mode & 07777);",
      "why": "hop 3 keeps only the permission bits of the mode"},
     {"file": BZI, "old": "    ZipFile.assignUnixAttributes(entry, mode);",
      "new": "    ZipFile.assignUnixAttributes(entry, entry.isDirectory() ? mode | 0x10 : mode);",
      "why": "hop 4 marks the mode of a directory entry with 0x10"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder): "
               "archivers.zip.ZipArchiveOutputStream (hop 1, 1495 lines), compressors.bzip2.BZip2CompressorOutputStream (hop 2, 1340), "
               "archivers.tar.TarArchiveEntry (hop 3, 1056), compressors.bzip2.BZip2CompressorInputStream (hop 4, 1053), "
               "archivers.zip.ZipFile (hop 5, gold, 972; the smallest host). All five are public concrete top-level classes in which a "
               "public static method compiles; the facade's class ZipArchiveEntry (the excluded allowed-candidate file) is not a host. "
               "Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 8644 + 100 + i, as mr3_spec.py "
               "inserts them: hop 1 after isSeekable (seed 8744), hop 2 after write (8745), hop 3 after setGroupName (8746), hop 4 "
               "after close (8747), hop 5 after getEncoding (8748). The facade calls hop 1 by its fully-qualified name; hops 2-4 "
               "import ZipArchiveEntry and the next host; hop 1 and the gold are in ZipArchiveEntry's own package.",
}
