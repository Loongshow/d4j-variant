"""Main run Compress-34__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade;
the fixed checkout of Defects4J Compress-34; the real bug modified X7875_NewUnix, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE section 1; pool v2: no_tested_static).

Facade: X7875_NewUnix.hashCode() (the only allowed instance target of BATCH8_PREREGISTRATION.md row 237; facade_planned_by null,
no facade reuse).
Original computation: hc = -1234567 * version; hc ^= Integer.rotateLeft(uid.hashCode(), 16); hc ^= gid.hashCode() (uid and gid are
non-negative BigIntegers: reset() gives 1000, setUID/setGID go through ZipUtil.longToBig, parseFromLocalFileData builds
new BigInteger(1, bytes) from up to 255 bytes; version is 1 or a byte read by parseFromLocalFileData, so 0..255).
Why the chain reads the local file data: the only test that reaches hashCode (probe below) is X7875_NewUnixTest::testMisc, which
asserts that a clone has the same hash code as the original. Any deterministic hash passes it, so an omission that only changes the
value cannot be caught; an omission must make the method throw on the default field (version 1, UID 1000, GID 1000), and the three
BigInteger.hashCode() calls and two XORs have no iteration or decision for such an omission. The chain therefore computes the same
value from the field's own wire form, its local file data (version byte, then the UID and the GID, each as a size byte followed by
the unsigned value least significant byte first, as getLocalFileDataData() writes it and parseFromLocalFileData reads it): the
starting hash is -1234567 * version; for each number the hash is rotated left by 16 bits and the number's BigInteger hash code is
XORed in. For two numbers this is rotl(rotl(s, 16) ^ U, 16) ^ G = s ^ rotl(U, 16) ^ G, the original value. The per-number hash is
computed from the value's bytes: they are copied out, zero-padded at the most significant end to whole 4-byte words, and the words,
read little-endian with ZipLong.getValue, are summed with weights 1, 31, 31^2, ... from the least significant word up; this is
BigInteger.hashCode()'s Horner fold over the big-endian magnitude, mod 2^32 (leading zero words add 0). Checked in Java on 200000
random states (version 0..255, UID/GID up to 250 random bits plus 0, 1, 255, 256, 1000, 2^31, 2^32 - 2, 2^32, 2^63 - 1 and the
2039-bit all-ones value, i.e. a 255-byte number), with the gold, the trimming of getLocalFileDataData and the original formula
side by side: no difference. The correct configuration therefore returns the original result for every reachable state, and never
throws (the data always has the version byte and two numbers).

facade_variant: V2 (receiver as parameter). The facade passes `this` (typed as its declaring class X7875_NewUnix, a public class) to
hop 1, and hop 1 calls only the public method getLocalFileDataData() of the receiver. V1 does not carry this computation: the local
file data's size trimming is the package-private static helper trimLeadingZeroesForceMinLength (V3 needs same_pkg_hosts, which the
task record does not list; copying it into a hop is not allowed), and getLocalFileDataData() is public. No private method is called
(no V4), no package-private type passes through a hop (no V5).
state_passed: the receiver `this` to hop 1 (which reads version, UID and GID through getLocalFileDataData()); no field is written,
no write-back.
The facade body is one call to hop 1 (the original has no guard). No visibility is widened, no type is added, no signature,
modifier, override or throws clause changes (the @Override annotation stays), no reflection, no test edit. The facade had no javadoc;
a one-sentence javadoc in the class's voice is added first (pre_edits, behaviour-preserving). The recipe's rewrite_facade appends the
lie to the javadoc that immediately precedes the `public int hashCode()` line, so the javadoc sits between @Override and the
declaration; its last line is an asterisk line so that the appended lie also starts with an asterisk.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Compress-34-probe of the fixture, the first
statement of hashCode() was made `if (version != Integer.MIN_VALUE) { throw new IllegalStateException("PROBE-REACHED"); }` (the
condition is always true; it only keeps the rest of the body reachable for javac). `defects4j test -t
org.apache.commons.compress.archivers.zip.X7875_NewUnixTest::testMisc`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at X7875_NewUnix.hashCode(X7875_NewUnix.java:270), called from X7875_NewUnixTest.testMisc(X7875_NewUnixTest.java:101).
`defects4j test` (full suite): 1 failing test, the same one. The facade is reached by an existing test directly, and by no other test.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted; all five are public
concrete top-level classes in which a public static method compiles):
  hop 1 archivers.zip.ZipArchiveOutputStream          1623 lines  extraDataHash      plumbing: the receiver's local file data
  hop 2 compressors.bzip2.BZip2CompressorOutputStream 1329 lines  versionedDataHash  aggregation: the starting hash from the
                                                                                      version byte (-1234567 * unsigned version)
  hop 3 archivers.tar.TarArchiveEntry                 1129 lines  foldOwnerIds       pass-through
  hop 4 archivers.zip.ZipFile                         1124 lines  foldExtraNumbers   pass-through
  hop 5 archivers.zip.ZipArchiveInputStream           1104 lines  foldSizedNumbers   GOLD: the walk over the size-prefixed numbers
                                                                                      and the per-number core (the value's
                                                                                      BigInteger hash and the rotate/XOR fold)
Host newline counts 1623, 1329, 1129, 1124, 1104; the smallest host (and the gold host) is ZipArchiveInputStream, 1104 lines
(C10F addendum section 1: hosts under 1500 lines are expected in this regime). Anchors: stageB_lib.pick_insertion_anchor with seed
6931 + 100 + i, as mr3_spec.py inserts them (recorded in host_notes).

Fault (one-line omission in the gold): the step that zero-pads a number's value to whole 4-byte words,
`value = Arrays.copyOf(value, (size + 3) & ~3);`, is dropped. The value is still copied out exactly, still read as little-endian
32-bit words and still folded, so the variant is an ordinary word-wise hash for values whose size is a multiple of four (InfoZip's
own 4-byte UIDs and GIDs); but getLocalFileDataData() trims each number to its significant bytes (MIN_LENGTH = 1), so its sizes are
1..n, and a value of 1, 2 or 3 bytes over the last whole word is read past its end. On the default field (data
{1, 2, -24, 3, 2, -24, 3}) the UID's value is the 2-byte array {-24, 3} and ZipLong.getValue(value, 0) reads value[3]: hashCode()
throws ArrayIndexOutOfBoundsException. Trigger: the EXISTING test X7875_NewUnixTest::testMisc; `assertEquals(o.hashCode(),
xf.hashCode())` fails with java.lang.ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 2. It is the only test that
reaches hashCode (probe, full suite), and gate G5 checks the full suite.
The gold's javadoc states the idiomatic contract (it folds the size-prefixed numbers of the data into a hash, each value hashed as
BigInteger.hashCode() hashes it, with a 16-bit rotation) and is silent on word padding; the variant does not hash a value whose size
is not a multiple of four (it throws on the trigger's data). The convention that a number's value has any byte length is pinned
outside the gold: X7875_NewUnix.getLocalFileDataData writes each number trimmed to its significant bytes through
trimLeadingZeroesForceMinLength (minimum length 1, no rounding to a word), and X7875_NewUnix.parseFromLocalFileData reads a value of
any size (uidSize bytes into new BigInteger(1, reverse(uidBytes))); passing tests: X7875_NewUnixTest::testParseReparse (sizes 1, 2,
4, 5 and 8 written and read), ::testTrimLeadingZeroesForceMinLength4 (trimmed lengths 1, 3, 4 and 6) and ::testSampleFile.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: data supplies every size and value byte and bounds the walk; offset is the walk's start; seed is the starting hash.
  T2 absent: hash, pos, size, value, valueHash, factor and i all reach the return value; pos advances by pos++ and pos += size;
     value is read by the padding copy and then by ZipLong.getValue; factor is multiplied by 31 in the word loop; no branch.
  T3 absent: no enumeration and no closed set handled in part; the copy uses both ends of the value's range (pos, pos + size);
     every number gets the same treatment; the javadoc names no value class.
  T4 absent: 'size-prefixed numbers', 'unsigned', 'least significant byte first', 'rotated left by 16 bits', 'XORed', 'as
     BigInteger#hashCode() computes it' and the @param/@return clauses are general descriptions that lines of the body address;
     no inline comment; identifiers name nothing the body does not do.
 Variant gold (javadoc, signature, the while loop, `int size = data[pos++] & 0xFF;`, `byte[] value = Arrays.copyOfRange(data, pos,
 pos + size);`, `pos += size;`, the word loop over value with ZipLong.getValue and factor, the rotate/XOR, return hash):
  T1 absent: data, offset and seed each change the result (data: sizes, values and the bound; offset: the start; seed: the start
     hash); none is only argument-checked.
  T2 absent: pos is the walk's cursor and is assigned in the loop (pos++, pos += size); value is read by ZipLong.getValue and
     bounds the word loop (not literal-initialised); i, factor (factor *= 31) and valueHash are assigned in the word loop and reach
     the return value; size bounds the copy and the cursor step; no literal-initialised local stays unassigned while it is used as a
     cursor, count or flag; there is no branch, case or ternary at all.
  T3 absent: no enumeration, no pair handled one-sidedly (the copy uses both pos and pos + size; the walk reads the size byte and the
     value of every number), no named class handled in part, no member read but left untreated.
  T4 absent: no phrase names a bound, limit, value class or case the body visibly does not meet: 'size-prefixed' (a size byte is read
     at the cursor), 'starting at the given offset' (pos = offset), 'unsigned' and 'least significant byte first' (ZipLong.getValue
     reads unsigned little-endian words), 'rotated left by 16 bits' and 'XORed' (they are), 'as BigInteger#hashCode() computes it'
     (a weighted fold with factor 31: a general description the word loop addresses); no inline comment; identifiers (hash, pos,
     size, value, valueHash, factor) name nothing the body does not meet.

Single owner: only the gold reads the values of the numbers and turns them into words; hop 1 only reads the receiver's local file
data, hop 2 only computes the starting hash from the version byte and gives the offset of the first size byte (1), hops 3 and 4 pass
the data, the offset and the seed along unchanged. Whatever a caller passes, the variant gold reads a value of size not divisible by
four past its end, and getLocalFileDataData() (the only data a caller here has) trims every number to its significant bytes; a caller
can avoid the throw only by not handing the gold the UID and GID as they are: an offset at or past the end, or one that lands on a
value byte whose "size" happens to be a multiple of four (offsets 2 and 5 on the trigger's data, where 0xE8 = 232 is read as a size
and the copy runs past the data), or not calling the gold; each drops or garbles the UID and GID and breaks hop 2's and hop 3's
documented behaviour. Declared alternatives (G9): hop 2 reads the version byte signed; hop 1 hashes the central directory data;
hop 3 rotates the seed before passing it on. None makes the trigger pass.
Recorded bypasses (each discards or garbles the gold's input):
 B-0 the facade's original body (rotate/XOR of uid.hashCode() and gid.hashCode()), discarding the whole chain.
 B-1 hop 1 returns java.util.Arrays.hashCode(field.getLocalFileDataData()), discarding hops 2-5 (a different hash, consistent with
     equals; breaks hop 1's documented hash of version, UID and GID as folded by the chain).
 B-2 hop 2 passes data.length as the offset: the gold folds no number and the hash is the version's starting hash alone (UID and
     GID ignored; breaks hop 2's documented "the UID and GID that follow it are folded").
 B-3 hop 2 (or hop 3/4 by offset + 1) starts the walk at offset 2: the gold reads the UID's first value byte 0xE8 as a size of 232,
     copies 232 bytes (the 4 bytes left in the data, the rest zero), and folds that one bogus number (breaks hop 2's and hop 3's documented UID/GID fold;
     hop 3's @param offset is the user id's size byte). Offset 5 does the same on the GID's first value byte.

Lie: the facade's javadoc claims the UID and GID are written out together as one decimal string whose hash code is then mixed with
the version; no step of the chain forms a decimal string or hashes a String (the chain hashes the field's local file data bytes).
It names neither the walk, the words, the padding, the size bytes nor any hop."""

X78 = "src/main/java/org/apache/commons/compress/archivers/zip/X7875_NewUnix.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZ2 = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
TAR = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"

GOLD_TEXT = '''/**
 * Folds the size-prefixed numbers of extra field data, starting at the
 * given offset, into a hash.
 *
 * <p>Each number is a size byte followed by its unsigned value, least
 * significant byte first. The hash is rotated left by 16 bits and the
 * value's hash, computed as {@link java.math.BigInteger#hashCode()}
 * computes it, is XORed into it.</p>
 *
 * @param data the extra field data
 * @param offset the position of the first number's size byte
 * @param seed the hash to start from
 * @return the hash with the numbers folded in
 */
public static int foldSizedNumbers(final byte[] data, final int offset, final int seed) {
    int hash = seed;
    int pos = offset;
    while (pos < data.length) {
        int size = data[pos++] & 0xFF;
        byte[] value = Arrays.copyOfRange(data, pos, pos + size);
        value = Arrays.copyOf(value, (size + 3) & ~3);
        pos += size;
        int valueHash = 0;
        int factor = 1;
        for (int i = 0; i < value.length; i += WORD) {
            valueHash += factor * (int) ZipLong.getValue(value, i);
            factor *= 31;
        }
        hash = Integer.rotateLeft(hash, 16) ^ valueHash;
    }
    return hash;
}'''

HOP1 = '''/**
 * Computes the hash of a UNIX UID/GID extra field from its local file
 * data.
 *
 * @param field the extra field, not null
 * @return the hash of the field's version, UID and GID
 */
public static int extraDataHash(final X7875_NewUnix field) {
    return BZip2CompressorOutputStream.versionedDataHash(field.getLocalFileDataData());
}'''

HOP2 = '''/**
 * Hashes the local file data of a UNIX UID/GID extra field: a version
 * byte followed by the size-prefixed UID and GID.
 *
 * <p>The version, read as an unsigned byte, is multiplied by -1234567 to
 * give the starting hash, into which the UID and GID that follow it are
 * folded.</p>
 *
 * @param data the local file data of the extra field, not null
 * @return the hash of the data
 */
public static int versionedDataHash(final byte[] data) {
    final int version = data[0] & 0xFF;
    return TarArchiveEntry.foldOwnerIds(data, 1, -1234567 * version);
}'''

HOP3 = '''/**
 * Folds the size-prefixed user and group ids of extra field data into a
 * hash.
 *
 * @param data the extra field data
 * @param offset the position of the user id's size byte
 * @param seed the hash to start from
 * @return the hash with both ids folded in
 */
public static int foldOwnerIds(final byte[] data, final int offset, final int seed) {
    return ZipFile.foldExtraNumbers(data, offset, seed);
}'''

HOP4 = '''/**
 * Folds the size-prefixed numbers of extra field data, starting at the
 * given offset, into a hash.
 *
 * @param data the extra field data
 * @param offset the position of the first number's size byte
 * @param seed the hash to start from
 * @return the hash with the numbers folded in
 */
public static int foldExtraNumbers(final byte[] data, final int offset, final int seed) {
    return ZipArchiveInputStream.foldSizedNumbers(data, offset, seed);
}'''

DESIGN = {
 "instance": "Compress-34", "project": "Compress", "bug_id": 34, "seed": 6931,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (X7875_NewUnix) to hop 1, which reads version, UID and GID through the public "
                 "getLocalFileDataData(); no field written, no write-back",
 "host_mode": "largest5", "host_lines": [1623, 1329, 1129, 1124, 1104],
 "reachability_probe": "hashCode() first statement made `if (version != Integer.MIN_VALUE) { throw new "
                       "IllegalStateException(\"PROBE-REACHED\"); }` in /private/tmp/d4j-mi-Compress-34-probe: "
                       "defects4j test -t X7875_NewUnixTest::testMisc and the full suite each give 1 failing test, "
                       "X7875_NewUnixTest::testMisc with PROBE-REACHED at X7875_NewUnix.hashCode(X7875_NewUnix.java:270), "
                       "called from X7875_NewUnixTest.java:101",
 "facade": {"file": X78, "class": "org.apache.commons.compress.archivers.zip.X7875_NewUnix", "method": "hashCode", "near_line": 269},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/archivers/zip/X7875_NewUnixTest.java",
             "test_class": "org.apache.commons.compress.archivers.zip.X7875_NewUnixTest", "test_method": "testMisc"},
 "expected_signature": "ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 2",
 "gold": {"method": "foldSizedNumbers", "text": GOLD_TEXT,
          "fault": {"old": "            byte[] value = Arrays.copyOfRange(data, pos, pos + size);\n"
                           "            value = Arrays.copyOf(value, (size + 3) & ~3);\n",
                    "new": "            byte[] value = Arrays.copyOfRange(data, pos, pos + size);\n"}},
 "pre_edits": {"chain": [
   {"file": X78,
    "old": "    @Override\n    public int hashCode() {\n        int hc = -1234567 * version;",
    "new": "    @Override\n    /**\n     * Returns a hash code built from the version, UID and GID of this extra field.\n     * */\n"
           "    public int hashCode() {\n        int hc = -1234567 * version;"},
 ]},
 "chain": {
   "facade_body": "return ZipArchiveOutputStream.extraDataHash(this);",
   "lie": "The UID and GID are written out together as one decimal string, and the hash code of that string is then "
          "mixed with the version.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "extraDataHash",
      "imports": ["org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZ2, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream",
      "method": "versionedDataHash",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP2},
     {"file": TAR, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "foldOwnerIds",
      "imports": ["org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP3},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "foldExtraNumbers",
      "imports": [], "text": HOP4},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "foldSizedNumbers",
      "imports": ["java.util.Arrays"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.zip.X7875_NewUnix::getLocalFileDataData",
              "org.apache.commons.compress.archivers.zip.X7875_NewUnix::trimLeadingZeroesForceMinLength",
              "org.apache.commons.compress.archivers.zip.X7875_NewUnix::parseFromLocalFileData"],
 "ownership_reason": "Only the gold reads the values of the size-prefixed numbers and turns them into words: hop 1 only reads "
                     "the receiver's local file data, hop 2 only computes the starting hash from the version byte and gives the "
                     "offset of the first size byte, hops 3 and 4 pass the data, offset and seed along unchanged. The variant gold "
                     "copies each value out exactly and reads it as whole 4-byte little-endian words, so it reads any value whose "
                     "size is not a multiple of four past its end; the data every caller here has comes from "
                     "getLocalFileDataData(), which trims each number to its significant bytes. A caller can avoid the throw only "
                     "by not handing the gold the UID and GID as they are (an offset past the end, or one landing on a value byte "
                     "read as a size), which drops or garbles them and breaks hop 2's and hop 3's documented fold. The gold's "
                     "javadoc promises each value's BigInteger hash; on the trigger's data (the default field, version 1, UID "
                     "1000, GID 1000, each a 2-byte value) the variant throws ArrayIndexOutOfBoundsException instead, so "
                     "hashCode() violates its contract. That a number's value has any byte length is pinned outside the gold: "
                     "X7875_NewUnix.getLocalFileDataData writes each number trimmed by trimLeadingZeroesForceMinLength (minimum "
                     "length 1, no rounding to a word) and X7875_NewUnix.parseFromLocalFileData reads a value of any size into "
                     "new BigInteger(1, reverse(bytes)); X7875_NewUnixTest::testParseReparse (sizes 1, 2, 4, 5, 8), "
                     "::testTrimLeadingZeroesForceMinLength4 and ::testSampleFile pass.",
 "ownership_tests": ["org.apache.commons.compress.archivers.zip.X7875_NewUnixTest::testParseReparse",
                     "org.apache.commons.compress.archivers.zip.X7875_NewUnixTest::testTrimLeadingZeroesForceMinLength4",
                     "org.apache.commons.compress.archivers.zip.X7875_NewUnixTest::testSampleFile"],
 "compensating": {
   "chain": [
     {"file": BZ2, "old": "    final int version = data[0] & 0xFF;",
      "new": "    final int version = data[0];",
      "why": "hop 2 reads the version byte signed"},
     {"file": ZAOS, "old": "return BZip2CompressorOutputStream.versionedDataHash(field.getLocalFileDataData());",
      "new": "return BZip2CompressorOutputStream.versionedDataHash(field.getCentralDirectoryData());",
      "why": "hop 1 hashes the central directory data"},
     {"file": TAR, "old": "return ZipFile.foldExtraNumbers(data, offset, seed);",
      "new": "return ZipFile.foldExtraNumbers(data, offset, Integer.rotateLeft(seed, 16));",
      "why": "hop 3 rotates the seed before folding the ids"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this "
               "builder; the facade file X7875_NewUnix.java is excluded): archivers.zip.ZipArchiveOutputStream (hop 1, 1623 lines), "
               "compressors.bzip2.BZip2CompressorOutputStream (hop 2, 1329), archivers.tar.TarArchiveEntry (hop 3, 1129), "
               "archivers.zip.ZipFile (hop 4, 1124), archivers.zip.ZipArchiveInputStream (hop 5, gold, 1104; the smallest host). "
               "All five are public concrete top-level classes in which a public static method compiles. Anchors from "
               "stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 6931 + 100 + i, as mr3_spec.py inserts them: "
               "hop 1 after addRawArchiveEntry (seed 7031), hop 2 after finish (7032), hop 3 after isGlobalPaxHeader (7033), "
               "hop 4 after copyRawEntries (7034), hop 5 after matches (7035). The facade calls hop 1 by its simple name (same "
               "package); hop 1 imports BZip2CompressorOutputStream, hop 2 imports TarArchiveEntry, hop 3 imports "
               "archivers.zip.ZipFile; hops 4 and 5 are in the facade's package; hop 5 imports java.util.Arrays and uses the "
               "host's existing static import ZipConstants.WORD and the same-package ZipLong.",
}
