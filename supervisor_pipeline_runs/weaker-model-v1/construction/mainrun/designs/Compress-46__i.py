"""Main run Compress-46__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; the fixed
checkout of Defects4J Compress-46; the real bug modified X5455_ExtendedTimestamp, the facade's class). No static pair exists (B8 note
section 1: pool v2 no_tested_static); paired_* fields of the task record are null.

Facade: X5455_ExtendedTimestamp.getLocalFileDataData() (instance method; allowed candidates hashCode / getLocalFileDataLength /
getLocalFileDataData, BATCH8_PREREGISTRATION.md row 239; facade_planned_by null for all three, so the choice is distinct; no facade
reuse). Why this candidate: hashCode is reached by one test only (testMisc), but that test compares the hash codes of a field and its
shallow clone, so no deterministic change of the hash can fail it; only an exception could, and a null-dereference omission there is
absorbed one-for-one by a caller passing new ZipLong(0) (hash 0) for a missing timestamp. getLocalFileDataLength feeds every zip read
(27 tests reach it) and its only computation the tests distinguish (all three timestamps set, flags 0/1/2/4/7/-1) is shared by
testGettersSetters and testParseReparse through getLocalFileDataData, so no length change is caught by one test only (dropping its
null checks is caught by none). getLocalFileDataData is reached by 26 tests, but a timestamp that is present while its flag bit is
clear only ever reaches it in testParseReparse (setFlags after the three setters; every parse resets the timestamps and reads only the
flagged ones, and the setters keep bit and timestamp in step).
Original computation: an array of getLocalFileDataLength() bytes; byte 0 is built from 0 by OR-ing MODIFY_TIME_BIT, ACCESS_TIME_BIT,
CREATE_TIME_BIT for each timestamp written; the modify time is written when bit0 is set, the access / create time when bit1 / bit2 is set
and the timestamp is not null, each as the four little-endian bytes of the ZipLong, packed in that order after the flags byte.

facade_variant: V1 (state as parameters). state_passed: the private field flags (byte) and the private fields modifyTime, accessTime,
createTime (as one ZipLong[] {modifyTime, accessTime, createTime}), handed to hop 1; no field is written, no write-back. The flags field
carries the same three bits as bit0_modifyTimePresent / bit1_accessTimePresent / bit2_createTimePresent at all times (setFlags sets all
four, each setter updates the bit and flags together, reset goes through setFlags), plus any spurious high bits set through setFlags,
which the chain restricts away as the original does. The facade has no guard (the original had none); its body is one call to hop 1. It
calls no private method (V4 not needed) and no public method of its class (V2 not needed: the chain sizes its own buffer instead of
calling getLocalFileDataLength). No visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no
reflection, no test edit.

Redistribution of the computation: the per-timestamp core (whether a timestamp is written, where, and the flags byte that describes the
written timestamps) is in the gold, one pass over the timestamps; hop 3 is the placement step (a block with room for the flags byte and
every timestamp, cut to the count the writer reports); hop 1 reads the flags byte as an unsigned value; hops 2 and 4 pass along.
The correct configuration returns the original bytes for every state the original can serialise; it differs only where the original
throws NullPointerException (bit0 set with a null modify time), where the chain clears the bit and writes no modify time. No test
reaches that state.

reachability_probe (addendum section 4): three scratch copies /private/tmp/d4j-mi-Compress-46-probe-{hash,len,data} of the fixture, the
first statement of each allowed facade made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
full `defects4j test` (24 s): hashCode -> 1 failing test (X5455_ExtendedTimestampTest::testMisc), getLocalFileDataLength -> 27,
getLocalFileDataData -> 26 failing tests, every one with java.lang.IllegalStateException: PROBE-REACHED, including
X5455_ExtendedTimestampTest::testParseReparse (the trigger) for getLocalFileDataData. The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, in that order, none substituted):
  hop 1 archivers.zip.ZipArchiveOutputStream          1687 lines  timeFieldData  plumbing: the flags byte read as unsigned
  hop 2 archivers.tar.TarArchiveEntry                 1405 lines  packedTimes    pass-through
  hop 3 compressors.bzip2.BZip2CompressorOutputStream 1334 lines  timesBlock     placement: block for flags byte + 4 bytes per
                                                                                  timestamp, cut to the count the writer reports
  hop 4 archivers.zip.ZipFile                         1258 lines  writeTimes     pass-through
  hop 5 archivers.zip.ZipArchiveInputStream           1136 lines  putTimes       GOLD: one pass over the timestamps
Host newline counts 1687, 1405, 1334, 1258, 1136; the smallest host (and the gold host) has 1136 lines (C10F addendum section 1:
hosts under 1500 lines are expected in this regime).

Fault (one-line omission of a decision in the gold): the flag-bit test for a present timestamp is dropped
(`} else if ((head & bit) != 0) {` becomes `} else {`; the edit carries the preceding `head &= ~bit;` line as context so that its new
text is unique in the sources, gate G10), so every timestamp that is not null is written, whether or not its bit is set
in the flags; the flags byte itself is still the flags restricted to the timestamp bits with the bits of missing timestamps cleared. The
gold then reads as the ordinary routine "write the flags byte, clear the bits of missing timestamps, write the timestamps there are".
Trigger: the EXISTING test X5455_ExtendedTimestampTest::testParseReparse; its second call, parseReparse(ZERO_TIME, MOD_ZERO, MOD_ZERO),
sets all three times and then setFlags(1); the variant returns 13 bytes {1, 0 x 12} instead of {1, 0, 0, 0, 0}, and
assertTrue(Arrays.equals(expectedLocal, result)) fails at X5455_ExtendedTimestampTest.java:473 (junit.framework.AssertionFailedError). Fault
experiments on the pristine class (full suite each): the same behaviour change is caught by testParseReparse only; G5 checks the
full suite on the variant.

The gold's javadoc states the idiomatic contract (it writes the flags byte and timestamps "in the local file data layout of the
extended timestamp extra field"; the flags byte is the flags restricted to the timestamp bits with the bits of missing timestamps
cleared; each timestamp written takes the next four bytes) and is silent on which present timestamps are written. In that layout the
flags byte tells which timestamps are present in the data (the class's setFlags/getFlags documentation: "The flags byte tells us which of
the three datestamp fields are present in the data"); the variant's output {1, 0 x 12} announces the modify time only and carries three
timestamps, so the contract is violated on the trigger input. The convention is pinned outside the gold: the intact siblings
X5455_ExtendedTimestamp.getLocalFileDataLength (a timestamp counts only when its bit is set: `bit1_accessTimePresent && accessTime != null
? 4 : 0`), parseFromLocalFileData (reads only the timestamps whose bits are set) and toString (shows a timestamp only when its bit is set
and it is not null); production use of the same data by ExtraFieldUtils.mergeLocalFileDataData (sizes by getLocalFileDataLength).
Passing tests: testGettersSetters (with all three times set, flags 1/2/4 give a local length of 5: a timestamp whose bit is clear is not
counted), testWriteReadRoundtrip and testSampleFile (through the chain), testBitsAreSetWithTime.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: flags initialises head (written to buffer[0] and tested per timestamp); stamps bounds the loop and supplies the bytes;
     buffer receives every write.
  T2 absent: i is the loop cursor; head is reassigned in the loop and written; count advances per timestamp written and is returned;
     bit is read by both branches; the null branch and the bit branch have different effects; nothing frozen or dead.
  T3 absent: every timestamp goes through the same two decisions (missing -> bit cleared; present -> written if its bit is set); the
     flag bits are restricted to the timestamp bits as a whole; no member of a named set is handled in part.
  T4 absent: 'restricted to the bits of the timestamps' (the mask), 'the bit of a missing timestamp cleared' (head &= ~bit), 'Each
     timestamp written takes the next four bytes' (putLong at count, count += 4), 'null where there is none' (null is accepted) and
     '@return the number of bytes written' (count) are met by lines of the body; the layout phrase is a general description.
 Variant gold (javadoc, signature, the mask, the loop, `if (stamps[i] == null) { head &= ~bit; } else { putLong; count += 4; }`,
 buffer[0] = (byte) head, return count):
  T1 absent: flags reaches buffer[0] through head; stamps and buffer as above; no parameter is only argument-checked.
  T2 absent: head is reassigned in the loop (head &= ~bit) and written to buffer[0]; count advances in the loop and is returned; bit is
     read; i advances; the if/else has two different effects; no local is frozen or dead.
  T3 absent: all three timestamps (the loop) get the same treatment; missing and present timestamps are both handled; the gold
     tests no flag bit for writing at all ('No member handled'); no class named in the gold's text is handled in part.
  T4 absent: 'restricted to the bits of the timestamps' is met (mask); 'with the bit of a missing timestamp cleared' is met; 'Each
     timestamp written takes the next four bytes' is met; '@param stamps ..., null where there is none' is accepted without throwing;
     '@param buffer ..., with room for ...' is a caller precondition; '@return the number of bytes written' is met; 'in the local file
     data layout of the extended timestamp extra field' is a general description; no inline comment; identifiers (head, count, bit,
     stamps) name nothing the body does not meet.

Single owner: only the gold decides whether a timestamp is written; hop 1 reads the flags byte as unsigned, hops 2 and 4 pass along,
hop 3 makes room for every timestamp and returns exactly the count the writer reports. Declared alternatives (G9): hop 1 restricts the
flags to the three timestamp bits (the variant still writes unflagged timestamps); hop 3 makes room only for the flagged timestamps (the
variant then overruns the block); hop 3 cuts the block by the number of flag bits instead of the writer's count (passes the trigger
because the trigger's three timestamps are equal, but breaks every zip read whose central data announces a timestamp it does not hold:
the merged local data no longer has getLocalFileDataLength bytes). None absorbs the fault.
Recorded bypasses (doc-inconsistent; reviewers should check them):
 B-0 the facade's original body (or a hop calling the intact computation) discards the chain including the gold.
 B-1 hop 3 cuts the block to `1 + 4 * Integer.bitCount(block[0] & 0xFF)` instead of the writer's count: it makes the gold's returned
     count dead, contradicts hop 3's documented "n being the count the writer reports", and passes the trigger only because the trigger
     sets the three timestamps to one value (for flags 2 it would return the modify time as the access time).
 B-2 hop 1, 2 or 4 rebuilds the timestamp array with null for each timestamp whose bit is clear: it passes null for a timestamp the
     field holds, contradicting the hops' documented "null where the field holds none", and duplicates the gold's per-timestamp
     decision with hard-coded indices in a pass-through. B-1 and B-2 were applied to the variant in scratch copies: each passes the
     trigger and the full suite (0 failing), so both are recorded here for the auditor; neither keeps the path used as documented.

Lie: the facade's javadoc claims the array is sized by getLocalFileDataLength() before the timestamps are copied into it; no step of the
chain calls getLocalFileDataLength or sizes an array by it (hop 3 makes room for every timestamp and cuts the block afterwards). It names
neither the flag bits of present timestamps nor any hop. The facade's javadoc is separated from its header by @Override, so
rewrite_facade finds no adjacent javadoc; a behaviour-preserving pre-edit (pre_edits.chain) inserts the lie where rewrite_facade
inserts it (before the closing */, after the existing '@return get the data' line)."""

X5455 = "src/main/java/org/apache/commons/compress/archivers/zip/X5455_ExtendedTimestamp.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
BZ2 = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"

GOLD_TEXT = '''/**
 * Writes a flags byte and timestamps into a buffer, in the local file
 * data layout of the extended timestamp extra field.
 *
 * <p>The flags byte is the given flags restricted to the bits of the
 * timestamps, {@code 1 << i} being the bit of timestamp {@code i}, with
 * the bit of a missing timestamp cleared. Each timestamp written takes
 * the next four bytes.</p>
 *
 * @param flags the flags
 * @param stamps the timestamps, null where there is none
 * @param buffer the buffer, with room for the flags byte and four bytes
 *               per timestamp
 * @return the number of bytes written
 */
public static int putTimes(final int flags, final ZipLong[] stamps, final byte[] buffer) {
    int head = flags & ((1 << stamps.length) - 1);
    int count = 1;
    for (int i = 0; i < stamps.length; i++) {
        final int bit = 1 << i;
        if (stamps[i] == null) {
            head &= ~bit;
        } else if ((head & bit) != 0) {
            stamps[i].putLong(buffer, count);
            count += 4;
        }
    }
    buffer[0] = (byte) head;
    return count;
}'''

HOP1 = '''/**
 * Creates the local file data of an extended timestamp extra field.
 *
 * @param flags the flags byte of the field
 * @param stamps the modify, access and create times of the field, null
 *               where the field holds none
 * @return the local file data, without Header-ID or length specifier
 */
public static byte[] timeFieldData(final byte flags, final ZipLong[] stamps) {
    return TarArchiveEntry.packedTimes(flags & 0xFF, stamps);
}'''

HOP2 = '''/**
 * Packs timestamps behind a flags byte.
 *
 * @param flags the flags, as an unsigned value
 * @param stamps the timestamps of the field, null where the field holds
 *               none
 * @return the packed bytes
 */
public static byte[] packedTimes(final int flags, final ZipLong[] stamps) {
    return BZip2CompressorOutputStream.timesBlock(flags, stamps);
}'''

HOP3 = '''/**
 * Writes a flags byte and timestamps into a block, and returns the part
 * of the block that was written.
 *
 * <p>The block has room for the flags byte and four bytes per
 * timestamp; the bytes returned are its first {@code n} bytes,
 * {@code n} being the count the writer reports.</p>
 *
 * @param flags the flags
 * @param stamps the timestamps of the field, null where the field holds
 *               none
 * @return the bytes written
 */
public static byte[] timesBlock(final int flags, final ZipLong[] stamps) {
    final byte[] block = new byte[1 + 4 * stamps.length];
    final int n = ZipFile.writeTimes(flags, stamps, block);
    return Arrays.copyOf(block, n);
}'''

HOP4 = '''/**
 * Writes a flags byte and timestamps into a buffer.
 *
 * @param flags the flags
 * @param stamps the timestamps of the field, null where the field holds
 *               none
 * @param buffer the buffer to write to
 * @return the number of bytes written
 */
public static int writeTimes(final int flags, final ZipLong[] stamps, final byte[] buffer) {
    return ZipArchiveInputStream.putTimes(flags, stamps, buffer);
}'''

DESIGN = {
 "instance": "Compress-46", "project": "Compress", "bug_id": 46, "seed": 8650,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field flags (byte) and the private fields modifyTime, accessTime, createTime as one ZipLong[] "
                 "{modifyTime, accessTime, createTime}, passed to hop 1; no field written, no write-back",
 "host_mode": "largest5", "host_lines": [1687, 1405, 1334, 1258, 1136],
 "reachability_probe": "first statement of each allowed facade made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Compress-46-probe-{hash,len,data}; full defects4j test: hashCode 1 failing "
                       "(testMisc), getLocalFileDataLength 27, getLocalFileDataData 26 failing, all with PROBE-REACHED, "
                       "including X5455_ExtendedTimestampTest::testParseReparse for getLocalFileDataData",
 "facade": {"file": X5455, "class": "org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestamp",
            "method": "getLocalFileDataData", "near_line": 173},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/compress/archivers/zip/X5455_ExtendedTimestampTest.java",
             "test_class": "org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestampTest",
             "test_method": "testParseReparse"},
 "expected_signature": "X5455_ExtendedTimestampTest.java:473)",
 "gold": {"method": "putTimes", "text": GOLD_TEXT,
          "fault": {"old": "                head &= ~bit;\n            } else if ((head & bit) != 0) {",
                    "new": "                head &= ~bit;\n            } else {"}},
 "chain": {
   "facade_body": "return ZipArchiveOutputStream.timeFieldData(flags, new ZipLong[] {modifyTime, accessTime, createTime});",
   "lie": "The array is sized by getLocalFileDataLength() before the timestamps are copied into it.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "timeFieldData",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP1},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "packedTimes",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipLong",
                  "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP2},
     {"file": BZ2, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "timesBlock",
      "imports": ["java.util.Arrays", "org.apache.commons.compress.archivers.zip.ZipFile",
                  "org.apache.commons.compress.archivers.zip.ZipLong"], "text": HOP3},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "writeTimes",
      "imports": [], "text": HOP4},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "putTimes",
      "imports": [], "gold": True},
   ],
 },
 # The facade's javadoc is separated from its header by @Override, so the recipe's rewrite_facade finds no adjacent javadoc and
 # appends nothing; this behaviour-preserving pre-edit puts the lie exactly where rewrite_facade puts it (before the closing */).
 "pre_edits": {"chain": [
     {"file": X5455,
      "old": "     * @return get the data\n     */\n    @Override\n    public byte[] getLocalFileDataData() {",
      "new": "     * @return get the data\n       The array is sized by getLocalFileDataLength() before the timestamps are copied "
             "into it.\n     */\n    @Override\n    public byte[] getLocalFileDataData() {"},
 ]},
 "evidence": ["org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestamp::getLocalFileDataLength",
              "org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestamp::parseFromLocalFileData",
              "org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestamp::toString"],
 "ownership_reason": "Only the gold decides, for each timestamp, whether it is written into the local file data and what the flags "
                     "byte says: hop 1 reads the flags byte as unsigned, hops 2 and 4 pass the flags and the timestamps along, and "
                     "hop 3 makes room for every timestamp and returns exactly the count of bytes the gold reports. The gold's "
                     "javadoc promises the local file data layout of the extended timestamp extra field, in which the flags byte "
                     "tells which timestamps are present in the data (X5455_ExtendedTimestamp.setFlags/getFlags documentation); on "
                     "the trigger input (three timestamps set, then setFlags(1)) the variant writes the flags byte 1 followed by "
                     "three timestamps. The convention is pinned outside the gold by the intact siblings "
                     "X5455_ExtendedTimestamp.getLocalFileDataLength (counts a timestamp only when its bit is set), "
                     "parseFromLocalFileData (reads only the timestamps whose bits are set) and toString (shows a timestamp only when "
                     "its bit is set), and by passing tests: testGettersSetters (all three times set, flags 1, 2 and 4 each give a "
                     "local length of 5), testWriteReadRoundtrip and testSampleFile (local data through the chain), "
                     "testBitsAreSetWithTime.",
 "ownership_tests": ["org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestampTest::testGettersSetters",
                     "org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestampTest::testWriteReadRoundtrip",
                     "org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestampTest::testSampleFile",
                     "org.apache.commons.compress.archivers.zip.X5455_ExtendedTimestampTest::testBitsAreSetWithTime"],
 "compensating": {
   "chain": [
     {"file": ZAOS, "old": "    return TarArchiveEntry.packedTimes(flags & 0xFF, stamps);",
      "new": "    return TarArchiveEntry.packedTimes(flags & 0x07, stamps);",
      "why": "hop 1 restricts the flags to the three timestamp bits"},
     {"file": BZ2, "old": "    final byte[] block = new byte[1 + 4 * stamps.length];",
      "new": "    final byte[] block = new byte[1 + 4 * Integer.bitCount(flags & 0x07)];",
      "why": "hop 3 makes room only for the flagged timestamps"},
     {"file": BZ2, "old": "    return Arrays.copyOf(block, n);",
      "new": "    return Arrays.copyOf(block, 1 + 4 * Integer.bitCount(flags & 0x07));",
      "why": "hop 3 cuts the block by the number of flag bits"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder): "
               "archivers.zip.ZipArchiveOutputStream (hop 1, 1687 lines), archivers.tar.TarArchiveEntry (hop 2, 1405), "
               "compressors.bzip2.BZip2CompressorOutputStream (hop 3, 1334), archivers.zip.ZipFile (hop 4, 1258), "
               "archivers.zip.ZipArchiveInputStream (hop 5, gold, 1136; the smallest host). All five are public concrete top-level "
               "classes in which a public static method compiles; the facade's file X5455_ExtendedTimestamp.java is excluded. "
               "Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 8650 + 100 + i, as mr3_spec.py "
               "inserts them: hop 1 after close (seed 8750), hop 2 after a TarArchiveEntry constructor (8751), hop 3 after write "
               "(8752), hop 4 after a ZipFile constructor (8753), hop 5 after canReadEntryData (8754). The facade calls hop 1 by its "
               "simple name (same package); hop 1 imports tar.TarArchiveEntry; hop 2 imports zip.ZipLong and "
               "bzip2.BZip2CompressorOutputStream; hop 3 imports java.util.Arrays, zip.ZipFile and zip.ZipLong; hops 4 and 5 are in "
               "the zip package with ZipLong.",
}
