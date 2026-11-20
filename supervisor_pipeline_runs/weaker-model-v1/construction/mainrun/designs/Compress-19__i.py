"""Main run Compress-19__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; the
fixed checkout of Defects4J Compress-19; the real bug modified Zip64ExtendedInformationExtraField, the facade's class). No static pair
(B8 note section 1).

Facade: Zip64ExtendedInformationExtraField.getCentralDirectoryLength() (the only allowed candidate of the task record,
BATCH8_PREREGISTRATION.md row 234; facade_planned_by null, no facade reuse). Original computation: the length of the central
directory data of the ZIP64 extra field is the sum of the widths of the values that are present, in the fixed order of the
APPNOTE layout quoted by the class javadoc: the original size (8 bytes), the compressed size (8), the relative header offset (8) and
the disk start number (4); an absent (null) value does not appear in the data. It is returned as a ZipShort.

facade_variant: V1 (state as parameters). state_passed: the four private fields size, compressedSize, relativeHeaderOffset and
diskStart, in the layout order, as one Object[] handed to hop 1, whose ZipShort result the facade returns. No field is written, no
write-back. The facade body is state gathering plus one call to hop 1 (the original has no guard). No visibility is widened, no type is
added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The method calls no private helper, so
V4 does not apply; ZipShort is public and the fields travel as Object, so no generic hop (V5) is needed. The javadoc of the facade is
the one-line {@inheritDoc}; the lie is appended to it by the recipe.

Redistribution of the computation: the per-element core, the room each field takes at its place in the layout and where it ends, is
in the gold (the place-dependent widths 8, 8, 8, 4 live in the gold, not in any caller); hop 3 aggregates the gold's per-field ends
into the length of the record (the end of its last present field); hop 1 wraps the length in a ZipShort; hops 2 and 4 pass the fields
along. The correct configuration returns the original length for all 16 combinations of present and absent fields (checked by hand:
the end of the last present field equals the sum of the widths of the present fields).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Compress-19-probe of the fixture, the first statement
of getCentralDirectoryLength was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; full
suite (`defects4j test`): 4 failing tests, each with java.lang.IllegalStateException: PROBE-REACHED:
Zip64ExtendedInformationExtraFieldTest::testWriteCDOnlySizes, ::testWriteCDSizeAndOffset, ::testWriteCDSizeOffsetAndDisk,
::testWriteCDSizeAndDisk. No other test of the suite reaches the facade. The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 archivers.zip.ZipArchiveOutputStream          1503 lines  extendedDataLength  plumbing: wraps the length in a ZipShort
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1340 lines  layoutLength        pass-through
  hop 3 archivers.zip.ZipFile                         1092 lines  lastFieldEnd        aggregation: the end of the last present field
  hop 4 archivers.tar.TarArchiveEntry                 1064 lines  fieldEnds           pass-through
  hop 5 compressors.bzip2.BZip2CompressorInputStream  1053 lines  endPositions        GOLD: one pass over the fields deciding, per
                                                                                      field, the room it takes and where it ends
Host newline counts 1503, 1340, 1092, 1064, 1053; the smallest host (and the gold host) has 1053 lines (C10F addendum section 1:
hosts under 1500 lines are expected in this regime).

Fault (one-line omission of a special-case step in the gold): the rule that an absent field takes no room is dropped from the advance
of the running end (`end += present ? (i < 3 ? 8 : 4) : 0;` becomes `end += i < 3 ? 8 : 4;`); absent fields are still given the end
-1. The gold then reads as the ordinary routine "each field ends at its place in the layout, an absent one marked -1". Trigger: the
EXISTING test Zip64ExtendedInformationExtraFieldTest::testWriteCDSizeAndDisk (size, compressed size and disk start present, relative
header offset absent); its first assertion, assertEquals(new ZipShort(20), f.getCentralDirectoryLength()), fails with
expected:<ZipShort value: 20> but was:<ZipShort value: 28> (the disk start is made to end at 28 instead of 20). It is the only test with
an absent field followed by a present one: when the absent fields are all at the end (testWriteCDOnlySizes, testWriteCDSizeAndOffset)
or there is none (testWriteCDSizeOffsetAndDisk), the end of the last present field is unchanged; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (where each field ends in a record that holds the given fields in the given order;
the width of a field by its place; -1 for an absent field) and is silent on the room an absent field takes. A record that holds the
fields (S, C, D) holds D from 16 to 20; the variant gives 28, so the contract is violated on the trigger input. The convention (the
fields of the ZIP64 extra field are packed, an absent one does not appear) is pinned outside the gold: the class javadoc ("the fields
will only appear if the corresponding Local or Central directory record field is set"), the intact siblings
Zip64ExtendedInformationExtraField.getCentralDirectoryData (the write offset advances only past a present value),
reparseCentralDirectoryData and parseFromLocalFileData (the read offset advances only past a present value), and the passing tests
testReadLFHSizesAndDisk (the disk start is read at offset 16 when the relative header offset is absent), testReadCDSomethingAndDisk
(the disk start is read at offset 8 of 12 bytes), and, through the chain, testWriteCDSizeAndOffset and testWriteCDOnlySizes.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: fields decides present for every place (the advance and the mark) and its length bounds the loop and sizes the result.
  T2 absent: i is the loop cursor; end is advanced in the loop and read into ends; present is read by both lines; ends is returned;
     every ternary has two different outcomes (8 vs 4 by place; the width vs 0; end vs -1).
  T3 absent: present and absent fields are both treated in the advance and in the mark; both place classes the javadoc names (the
     first three places, the later places) get their width; no enum, type code or named format is enumerated.
  T4 absent: 'eight bytes ... four bytes' by place is met by `i < 3 ? 8 : 4`; '-1 for an absent field' is met by
     `present ? end : -1`; 'where each field ends in a record that holds the given fields in the given order' is a general
     description met by the running end; the @param clause is a caller description.
 Variant gold (javadoc, signature, the loop with `final boolean present = fields[i] != null;`, `end += i < 3 ? 8 : 4;`,
 `ends[i] = present ? end : -1;`, `return ends;`):
  T1 absent: fields changes the result (present decides -1 or the end of each place; fields.length bounds the loop and sizes ends).
  T2 absent: i advances; end is assigned in every iteration and read into ends; present is read by the mark; ends is returned; both
     ternaries have two different outcomes; no local is dead or frozen.
  T3 absent: the gold enumerates no closed set; present/absent is a property tested once and both outcomes are given; both place
     classes named by the javadoc get their width; the gold names no class (no 'packed', 'contiguous', 'no room') that it handles in
     part; no pair half or range end is involved.
  T4 absent: the width by place is met; '-1 for an absent field' is met; the summary sentence is a general description that the
     running end addresses; 'null where a field is absent' is a caller description; no inline comment; identifiers (ends, end,
     present, fields, endPositions) name nothing the body does not meet.

Single owner: only the gold knows how much room a field takes and decides where each field ends; hop 3 reads the gold's ends (the
last one that is not -1), hops 1, 2 and 4 pass fields and lengths along, and no caller holds a width it could adjust. Once the gold
has advanced past the absent relative header offset, the disk start ends at 28 and the length 28 follows; 20 can come out of the
chain only if a caller recomputes the widths itself (discarding the gold's ends). Re-ordering or dropping fields at the facade moves
the disk start to an eight-byte place (24). Declared alternatives (G9): hop 3 takes an end of 0 as absent; hop 3 scans the ends from
the first field; the facade puts the disk start before the relative header offset. None absorbs the fault.
Recorded bypasses: B-0 hop 3 (or hop 2, or hop 1) sums the widths of the non-null fields itself, discarding the gold's ends; B-1 hop 4
re-implements the placement instead of calling the gold. Both throw away the gold's output.

Lie: the facade's javadoc claims that, for a field parsed from central directory data, the length of the stored raw data is returned;
no step of the chain reads the raw data (the length is always computed from the four values). It names neither absent values nor the
room a value takes nor any hop."""

ZEF = "src/main/java/org/apache/commons/compress/archivers/zip/Zip64ExtendedInformationExtraField.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZO = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
BZI = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorInputStream.java"

GOLD_TEXT = '''/**
 * Computes where each field ends in a record that holds the given fields
 * in the given order. A field in one of the first three places is eight
 * bytes long, a field in a later place four bytes.
 *
 * @param fields the fields, null where a field is absent
 * @return the end in bytes of each field, -1 for an absent field
 */
public static int[] endPositions(final Object[] fields) {
    final int[] ends = new int[fields.length];
    int end = 0;
    for (int i = 0; i < fields.length; i++) {
        final boolean present = fields[i] != null;
        end += present ? (i < 3 ? 8 : 4) : 0;
        ends[i] = present ? end : -1;
    }
    return ends;
}'''

HOP1 = '''/**
 * Returns the length of the data of an extra field that holds the given
 * fields in the given order.
 *
 * @param fields the fields, null where a field is absent
 * @return the length of the data
 */
public static ZipShort extendedDataLength(Object[] fields) {
    return new ZipShort(BZip2CompressorOutputStream.layoutLength(fields));
}'''

HOP2 = '''/**
 * Returns the number of bytes needed to hold the given fields in the given
 * order.
 *
 * @param fields
 *            the fields, null where a field is absent
 * @return the number of bytes
 */
public static int layoutLength(final Object[] fields) {
    return ZipFile.lastFieldEnd(fields);
}'''

HOP3 = '''/**
 * Returns the length of a record that holds the given fields in the given
 * order, that is the end of its last field.
 *
 * @param fields the fields, null where a field is absent
 * @return the length of the record in bytes, 0 if it holds no field
 */
public static int lastFieldEnd(Object[] fields) {
    final int[] ends = TarArchiveEntry.fieldEnds(fields);
    for (int i = ends.length - 1; i >= 0; i--) {
        if (ends[i] >= 0) {
            return ends[i];
        }
    }
    return 0;
}'''

HOP4 = '''/**
 * Get where each field ends in a record that holds the given fields in the
 * given order.
 *
 * @param fields the fields, null where a field is absent
 * @return the end in bytes of each field, -1 for an absent field
 */
public static int[] fieldEnds(Object[] fields) {
    return BZip2CompressorInputStream.endPositions(fields);
}'''

FACADE_CALL = ("return ZipArchiveOutputStream.extendedDataLength(new Object[] {size, compressedSize, relativeHeaderOffset, "
               "diskStart});")

DESIGN = {
 "instance": "Compress-19", "project": "Compress", "bug_id": 19, "seed": 4277,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private fields size, compressedSize, relativeHeaderOffset, diskStart, in the layout order, as one Object[] "
                 "passed to hop 1; hop 1's ZipShort is returned; no write-back",
 "host_mode": "largest5", "host_lines": [1503, 1340, 1092, 1064, 1053],
 "reachability_probe": "getCentralDirectoryLength first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Compress-19-probe; full suite: 4 failing tests, all PROBE-REACHED: "
                       "Zip64ExtendedInformationExtraFieldTest::testWriteCDOnlySizes, testWriteCDSizeAndOffset, "
                       "testWriteCDSizeOffsetAndDisk, testWriteCDSizeAndDisk",
 "facade": {"file": ZEF, "class": "org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraField",
            "method": "getCentralDirectoryLength", "near_line": 148},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/compress/archivers/zip/Zip64ExtendedInformationExtraFieldTest.java",
             "test_class": "org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraFieldTest",
             "test_method": "testWriteCDSizeAndDisk"},
 "expected_signature": "expected:<ZipShort value: 20> but was:<ZipShort value: 28>",
 "gold": {"method": "endPositions", "text": GOLD_TEXT,
          "fault": {"old": "        end += present ? (i < 3 ? 8 : 4) : 0;",
                    "new": "        end += i < 3 ? 8 : 4;"}},
 "chain": {
   "facade_body": FACADE_CALL,
   "lie": "For a field parsed from central directory data, the length of the stored raw data is returned.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "extendedDataLength",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZO, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "layoutLength",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP2},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "lastFieldEnd",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP3},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "fieldEnds",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream"], "text": HOP4},
     {"file": BZI, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream", "method": "endPositions",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraField::getCentralDirectoryData",
              "org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraField::reparseCentralDirectoryData",
              "org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraField::parseFromLocalFileData"],
 "ownership_reason": "Only the gold knows how much room each field of the record takes and decides where it ends: it gives every "
                     "field its end (-1 for an absent one) from a running end that advances by the field's place-dependent width. "
                     "Hop 3 reads the gold's ends and returns the last one that is not -1; hops 1, 2 and 4 pass the fields and the "
                     "length along; no caller holds a width. Once the gold has advanced the running end past the absent relative "
                     "header offset, the disk start ends at 28 and the length 28 follows; 20 can come out of the chain only if a "
                     "caller recomputes the widths itself, and re-ordering or dropping fields at the facade puts the disk start at an "
                     "eight-byte place. The gold's javadoc promises where each field ends in a record that holds the given fields in "
                     "the given order; a record holding the original size, the compressed size and the disk start holds the disk "
                     "start from 16 to 20. The convention that an absent field of the ZIP64 extended information extra field does "
                     "not appear is pinned outside the gold: the class javadoc (the fields only appear if the corresponding directory "
                     "field is set), the intact siblings getCentralDirectoryData (the write offset advances only past a present "
                     "value), reparseCentralDirectoryData and parseFromLocalFileData (the read offset advances only past a present "
                     "value), and the passing tests testReadLFHSizesAndDisk (disk start read at 16 without a relative header offset), "
                     "testReadCDSomethingAndDisk (disk start read at 8 of 12 bytes), and, through the chain, "
                     "testWriteCDSizeAndOffset and testWriteCDOnlySizes.",
 "ownership_tests": ["org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraFieldTest::testReadLFHSizesAndDisk",
                     "org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraFieldTest::testReadCDSomethingAndDisk",
                     "org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraFieldTest::testWriteCDSizeAndOffset",
                     "org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraFieldTest::testWriteCDOnlySizes"],
 "compensating": {
   "chain": [
     {"file": ZF, "old": "        if (ends[i] >= 0) {",
      "new": "        if (ends[i] > 0) {",
      "why": "hop 3 takes an end of 0 as absent"},
     {"file": ZF, "old": "    for (int i = ends.length - 1; i >= 0; i--) {",
      "new": "    for (int i = 0; i < ends.length; i++) {",
      "why": "hop 3 scans the ends from the first field"},
     {"file": ZEF, "old": "new Object[] {size, compressedSize, relativeHeaderOffset, diskStart}",
      "new": "new Object[] {size, compressedSize, diskStart, relativeHeaderOffset}",
      "why": "the facade puts the disk start before the relative header offset"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder): "
               "archivers.zip.ZipArchiveOutputStream (hop 1, 1503 lines), compressors.bzip2.BZip2CompressorOutputStream (hop 2, 1340), "
               "archivers.zip.ZipFile (hop 3, 1092), archivers.tar.TarArchiveEntry (hop 4, 1064), "
               "compressors.bzip2.BZip2CompressorInputStream (hop 5, gold, 1053; the smallest host). All five are public concrete "
               "top-level classes in which a public static method compiles; the facade's class Zip64ExtendedInformationExtraField "
               "(the only allowed candidate's file) is not a host. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) "
               "with seed 4277 + 100 + i, as mr3_spec.py inserts them: hop 1 after setCreateUnicodeExtraFields (seed 4377), hop 2 after "
               "finish (4378), hop 3 after getEntriesInPhysicalOrder (4379), hop 4 after getMode (4380), hop 5 after close (4381). The "
               "facade calls hop 1 by its simple name (same package); hops 1-4 each import the next host.",
}
