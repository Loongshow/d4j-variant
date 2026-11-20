"""Main run Compress-26 (cell C10f, batch 6: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J Compress-26; the
real bug modified IOUtils, the target class, and its D4J trigger tests are IOUtilsTest::skipUsingRead and ::skipUsingSkipAndRead).

Facade: IOUtils.skip(InputStream, long) (allowed target, BATCH6_PREREGISTRATION.md row Compress-26: IOUtils.readFully /
IOUtils.skip / IOUtils.closeQuietly).
 - closeQuietly is set aside: below its null guard (which the recipe keeps in the facade) it is one close() inside a catch that
   swallows the IOException; nothing iterates or decides, so there is no step to omit.
 - readFully is set aside: its only iteration is the loop that keeps reading after a short read, and a short read can be completed
   by any caller (read again for the rest, or read through a stream that loops on available()), so an omission there has no single
   owner.
 - skip is used: its read fallback consumes bytes from the stream, and bytes read beyond the request cannot be given back by any
   caller.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2): scratch copy of the fixture (/private/tmp/c26r2-probe), first statement
of IOUtils.skip made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; `defects4j test -t` on the candidate
triggers IOUtilsTest::skipUsingSkip, ::skipUsingRead and ::skipUsingSkipAndRead: each fails with
java.lang.IllegalStateException: PROBE-REACHED. Full suite on the same copy: 36 failing tests (baseline 0), all PROBE-REACHED:
IOUtilsTest (3), TarArchiveOutputStreamTest (11), TarArchiveInputStreamTest (6), SevenZFileTest (4), ChangeSetTestCase (4),
ArArchiveInputStreamTest (2), and one each in ArTestCase, TarTestCase, ArArchiveOutputStreamTest, ArjArchiveInputStreamTest,
TarArchiveEntryTest, FramedSnappyCompressorInputStreamTest. The facade is reached by existing tests.

Original computation of the facade: remember the requested count; while bytes remain, call the stream's own skip with the
remaining count and stop at the first call that skips nothing; if bytes remain, read and discard them through a 4096-byte buffer,
each read bounded by min(remaining, 4096), until a read gives fewer than one byte; return requested minus remaining. A count that
is not positive calls nothing and gives 0.

host_mode = largest5 (fewer than five other public classes of >= 1500 lines: n1500_other = 1). Hosts are EXACTLY hosts_hop_order of
the task record (the five largest public, non-interface, non-enum classes other than IOUtils, by newline count), hop i in host i:
  hop 1 archivers.zip.ZipArchiveOutputStream           1501 lines   skipInput     decision: a count that is not positive gives 0
  hop 2 compressors.bzip2.BZip2CompressorOutputStream  1329 lines   skipFrom      pass-through
  hop 3 archivers.zip.ZipFile                          1083 lines   skipStream    pass-through
  hop 4 archivers.zip.ZipArchiveInputStream            1074 lines   skipRaw       the stream's own skip, called until it skips
                                                                                  nothing; hands the request and the bytes skipped
                                                                                  so far on
  hop 5 archivers.tar.TarArchiveEntry                  1073 lines   completeSkip  GOLD: reads and discards bytes through a buffer
                                                                                  until the request is met or the stream ends
 Smallest host: 1073 lines (TarArchiveEntry, the gold host). Anchors: stageB_lib.pick_anchor (host_search.pick_insertion_anchor)
 with the instance seed 7530 (seed + 100 + i), as mr2_spec.py inserts them; recorded in host_notes. No host substituted.

The correct configuration computes exactly the original result for every input, with the same stream calls: hop 1 returns 0 for a
count that is not positive without touching the stream; hop 4 runs the original skip loop (a counter of skipped bytes in place of
the remaining count: skipped < count is remaining > 0, and count - skipped is the request of each skip call); the gold sizes its
buffer min(count, 4096), starts from the bytes already skipped and reads min(count - done, buffer.length) bytes per read, which is
the original's min(remaining, 4096) because count - done <= count; it returns done = count - remaining. When the stream's skip has
covered the request the gold's loop does not run (only the buffer is allocated).

Fault (one-line omission in the gold, in its read loop): the per-read bound is dropped, so each read asks for the whole buffer
(`IOUtils.readFully(in, buffer)` instead of `IOUtils.readFully(in, buffer, 0, (int) Math.min(count - done, buffer.length))`). The
buffer has min(count, 4096) bytes, so the variant differs from the correct gold only when bytes are read while fewer than
buffer.length remain: after a skip that made partial progress, or at the end of a request above 4096 bytes that is not a multiple
of 4096. The reads then consume bytes beyond the request.
Trigger: the EXISTING test IOUtilsTest::skipUsingSkipAndRead (empty test.patch): its stream skips 5 bytes once and then 0, so hop 4
hands (10, 5) to the gold, whose 10-byte read gets the 6 bytes left and skip(sut, 10) returns 11: `expected:<10> but was:<11>`.
skipUsingRead (no skip progress: buffer of 10 bytes = the 10 to read) and skipUsingSkip (no reads) pass; every other test that
reaches the facade either never reads in the gold or reads at the end of the stream, so a full-suite run of the variant has exactly
one failing test, the trigger (gate G5). The over-read bytes are consumed from the stream: no caller can give them back (capping the
returned count still leaves the next read() at -1, compensating edit 1).

Quiet gold: its javadoc states the idiomatic contract (completes a skip of the given number of bytes by reading and discarding bytes;
@return the number of bytes actually skipped) and is silent on how each read is sized; on the trigger the variant skips 11 bytes when
10 were asked for.
External pins (outside the gold's own text):
 - the facade's own javadoc: skip 'the given number of bytes', 'by repeatedly invoking skip on the given input stream', falling
   back to read() when skip returns 0, and 'only skip less than the requested number of bytes if the end of the input stream has
   been reached';
 - ZipArchiveInputStream.skip has the gold's shape (a counter `skipped` up to `value`) and bounds each read by `rem = value -
   skipped`; CpioArchiveInputStream.skip bounds each read by `max - total` (clamped to its buffer); TapeInputStream.skip ('skips the
   full given length unless EOF is reached') advances by at most `len - bytes`;
 - TarArchiveInputStream.skip trims the request to the entry's remaining data and adds the returned count to entryOffset, which
   relies on the count not passing the request;
 - passing tests: IOUtilsTest::skipUsingRead (the read path reads exactly the 10 bytes: the next read() is 11), ::skipUsingSkip,
   TarArchiveInputStreamTest::shouldConsumeArchiveCompletely, ArArchiveInputStreamTest::testReadLongNamesBSD.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, buffer of min(count, 4096) bytes, done = skipped, loop while done < count with the bounded read):
  T1 absent: in feeds every read; count sizes the buffer, bounds the loop and each read; skipped is the start of done, which is
     returned.
  T2 absent: buffer is a call argument of every read; done is assigned in the loop and decides the loop, the read size and the
     return; read is assigned per iteration and decides the break and the update; no literal-initialised local; the if breaks a loop
     that would otherwise continue.
  T3 absent: no enumeration, flag set, pair or special-value class; the read region has both ends (offset 0 and the bounded length);
     nothing to rewrite.
  T4 absent: the javadoc names the given number of bytes, the bytes actually skipped and caller preconditions (count 'positive',
     skipped 'those bytes that are already skipped'); no rule, limit, bound, value class or case that the body does not address; no
     inline comment.
 Variant gold (javadoc, signature, buffer of min(count, 4096) bytes, `long done = skipped;`, loop `while (done < count)` with
 `int read = IOUtils.readFully(in, buffer);`, `if (read < 1) break;`, `done += read;`, `return done;`):
  T1 absent: in is read by readFully; count sizes the buffer and bounds the loop; skipped initialises done, which is returned.
  T2 absent: buffer reaches the readFully call; done is assigned in the loop (`done += read`), decides the loop condition and is
     returned; read is assigned from a call in every iteration and decides the break and the update; no literal-initialised or
     frozen local; `if (read < 1) break;` ends a loop that otherwise goes on, so no dead decision.
  T3 absent: the gold has one loop and one operation (a read of the whole buffer, a single value, no offset or length pair); it
     handles no member of any closed set and names no class that it handles in part; the buffer size min(count, 4096) has no
     lower end to treat because count is positive by the caller's precondition.
  T4 absent: 'Completes a skip of the given number of bytes of a stream by reading and discarding bytes' and '@return the number of
     bytes actually skipped' are general descriptions that the loop and the return address; '@param count the number of bytes to
     skip, positive' and '@param skipped the number of those bytes that are already skipped' are caller preconditions; '@throws
     IOException if the stream cannot be read' matches the call; identifiers (buffer, done, read) name nothing the body visibly
     does not meet.

Single owner: only the gold sizes the reads; hops 1-3 hold the stream and the requested count, hop 4 calls only the stream's skip
and gets back one count from the gold after the bytes are consumed. Declared alternatives (G9), each a one-line edit above the gold
that leaves the over-read in place: hop 4 caps the returned count at the requested count (expected:<11> but was:<-1>: the 11th
byte is gone); hop 1 also skips nothing when the stream reports no available bytes (11 bytes are available); hop 3 skips through a
BufferedInputStream (expected:<10> but was:<11>: the gold's read fills from the 6 bytes left).
Recorded one-line edits above the gold that pass the trigger and the full suite (each applied to the variant in its own scratch
copy: defects4j test, 0 failing tests; then a probe program calling IOUtils.skip on streams that skip 5 bytes once, never, fully,
3 once, 3 then 2, 2-2-2, and on 6000-byte streams with a request of 5000):
 B-0 bypass: the facade (its original body) or any hop skips with another implementation, discarding the gold's result: hop 3
     `return new org.apache.commons.compress.utils.BoundedInputStream(in, count).skip(count);`, or hop 4 `return skipped + new
     org.apache.commons.compress.utils.BoundedInputStream(in, count - skipped).skip(count - skipped);` (InputStream.skip's read
     loop in place of the gold).
 B-1 pre-filter that replaces the documented strategy: hop 3 passes `new org.apache.commons.compress.utils.BoundedInputStream(in,
     count)` down; that wrapper's skip is InputStream.skip, which reads, so the given stream's own skip is never invoked and the
     gold never reads. It contradicts the facade's documentation ('by repeatedly invoking skip on the given input stream ... will
     fall back to using the read() method' when skip returns 0).
 B-2 fitted to one-buffer remainders: hop 4 hands the gold only what is left as a fresh request (`return skipped +
     TarArchiveEntry.completeSkip(in, count - skipped, 0);`); the gold's buffer then has the size of the remainder, which hides the
     over-read only while the remainder fits in one read: with a stream that skips 5 bytes once and then 0 and a request of 5000
     bytes on 6000, it still returns 6000 and the next read() is -1 (the over-read of a request above 4096 does not depend on
     hop 4 at all: with a stream that never skips, a request of 5000 bytes still returns 6000).
 B-3 fitted to the trigger's stream: hop 3 splits the request in two halves (`return ZipArchiveInputStream.skipRaw(in, count / 2)
     + ZipArchiveInputStream.skipRaw(in, count - count / 2);`): it passes because the trigger's stream skips exactly half (5 of 10)
     at its first skip; with a stream that skips 3 bytes once, skip(sut, 10) still returns 11 and the next read() is -1 (and 5005
     for 5000 on the 6000-byte stream that skips 5 once).
 B-4 fitted to the trigger's stream: hop 3 calls the stream's skip once itself and hands the rest on (`long first =
     in.skip(count); return first < count ? first + ZipArchiveInputStream.skipRaw(in, count - first) : first;`): it passes because
     the trigger's stream makes progress only at its first skip; with a stream that skips 3 and then 2 bytes, or 2, 2 and 2,
     skip(sut, 10) still returns 11, and a request of 5000 on 6000 bytes still returns 6000.
 (The correct gold returns the requested count and leaves the next byte in place on every one of these streams.)

Lie: the facade's javadoc claims the stream is first wrapped in a BufferedInputStream so that bytes can be skipped within its
buffer without further calls to the stream; the chain wraps nothing and calls the stream's skip and read directly. It names neither
the read size nor any omitted step nor any hop."""

IO = "src/main/java/org/apache/commons/compress/utils/IOUtils.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZ2 = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"

GOLD_TEXT = '''/**
 * Completes a skip of the given number of bytes of a stream by reading
 * and discarding bytes.
 *
 * @param in stream to read bytes from
 * @param count the number of bytes to skip, positive
 * @param skipped the number of those bytes that are already skipped
 * @return the number of bytes actually skipped
 * @throws IOException if the stream cannot be read
 */
public static long completeSkip(InputStream in, long count, long skipped) throws IOException {
    byte[] buffer = new byte[(int) Math.min(count, 4096)];
    long done = skipped;
    while (done < count) {
        int read = IOUtils.readFully(in, buffer, 0, (int) Math.min(count - done, buffer.length));
        if (read < 1) {
            break;
        }
        done += read;
    }
    return done;
}'''

HOP1 = '''/**
 * Skips bytes of the given stream.
 *
 * <p>A count that is not positive skips nothing and gives 0.</p>
 *
 * @param in stream to skip bytes in
 * @param count the number of bytes to skip
 * @return the number of bytes actually skipped
 * @throws IOException if the stream cannot be skipped or read
 */
public static long skipInput(InputStream in, long count) throws IOException {
    if (count <= 0) {
        return 0;
    }
    return BZip2CompressorOutputStream.skipFrom(in, count);
}'''

HOP2 = '''/**
 * Skips a positive number of bytes of the given stream.
 *
 * @param in stream to skip bytes in
 * @param count the number of bytes to skip, positive
 * @return the number of bytes actually skipped
 * @throws IOException if the stream cannot be skipped or read
 */
public static long skipFrom(InputStream in, long count) throws IOException {
    return ZipFile.skipStream(in, count);
}'''

HOP3 = '''/**
 * Skips the given positive number of bytes of a stream.
 *
 * @param in stream to skip bytes in
 * @param count the number of bytes to skip, positive
 * @return the number of bytes actually skipped
 * @throws IOException if the stream cannot be skipped or read
 */
public static long skipStream(InputStream in, long count) throws IOException {
    return ZipArchiveInputStream.skipRaw(in, count);
}'''

HOP4 = '''/**
 * Skips bytes of the given stream, calling the stream's own skip
 * method for as long as it skips any bytes.
 *
 * @param in stream to skip bytes in
 * @param count the number of bytes to skip, positive
 * @return the number of bytes actually skipped
 * @throws IOException if the stream cannot be skipped or read
 */
public static long skipRaw(InputStream in, long count) throws IOException {
    long skipped = 0;
    while (skipped < count) {
        long n = in.skip(count - skipped);
        if (n == 0) {
            break;
        }
        skipped += n;
    }
    return TarArchiveEntry.completeSkip(in, count, skipped);
}'''

DESIGN = {
 "instance": "Compress-26", "project": "Compress", "bug_id": 26, "seed": 7530,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": IO, "class": "org.apache.commons.compress.utils.IOUtils", "method": "skip", "near_line": 94},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/compress/utils/IOUtilsTest.java",
             "test_class": "org.apache.commons.compress.utils.IOUtilsTest", "test_method": "skipUsingSkipAndRead"},
 "expected_signature": "expected:<10> but was:<11>",
 "gold": {"method": "completeSkip", "text": GOLD_TEXT,
          "fault": {"old": "            int read = IOUtils.readFully(in, buffer, 0, (int) Math.min(count - done, buffer.length));",
                    "new": "            int read = IOUtils.readFully(in, buffer);"}},
 "chain": {
   "facade_body": "return org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.skipInput(input, numToSkip);",
   "lie": "The stream is first wrapped in a BufferedInputStream, so that bytes can be skipped within its buffer without "
          "further calls to the stream.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "skipInput",
      "imports": ["java.io.InputStream", "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZ2, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream", "method": "skipFrom",
      "imports": ["java.io.InputStream", "org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP2},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "skipStream",
      "imports": [], "text": HOP3},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "skipRaw",
      "imports": ["org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP4},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "completeSkip",
      "imports": ["java.io.InputStream", "org.apache.commons.compress.utils.IOUtils"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.zip.ZipArchiveInputStream::skip",
              "org.apache.commons.compress.archivers.cpio.CpioArchiveInputStream::skip",
              "org.apache.commons.compress.archivers.dump.TapeInputStream::skip",
              "org.apache.commons.compress.archivers.tar.TarArchiveInputStream::skip"],
 "ownership_reason": "Only the gold sizes the reads that complete a skip; hops 1-3 hold the stream and the requested count, and hop "
                     "4 calls only the stream's own skip and hands the request and the bytes skipped so far to the gold, getting "
                     "back one count after the bytes are consumed. Bytes read beyond the requested count are gone from the stream, "
                     "so no caller can give them back (capping the returned count leaves the next read() at -1). The convention "
                     "is pinned outside the gold: the facade's javadoc (skips 'the given number of bytes' by invoking the "
                     "stream's skip, falling back to read() when skip returns 0, and skips less only at the end of the stream); "
                     "ZipArchiveInputStream.skip counts `skipped` up to `value` like the gold and bounds each read by `rem = "
                     "value - skipped`; CpioArchiveInputStream.skip and TapeInputStream.skip bound each read or step by the bytes "
                     "still to skip (max - total, len - bytes); TarArchiveInputStream.skip trims the request to the entry's "
                     "remaining data and adds the returned count to its offset; IOUtilsTest skipUsingRead shows the read path "
                     "reading exactly the requested bytes (the next read() is 11). Edits above the gold that pass the trigger and "
                     "the suite either replace the gold's result with another skip implementation, wrap the stream so that its "
                     "own skip is never invoked (contrary to the facade's documented strategy), or are fitted to the trigger: "
                     "hop 4 handing the gold only the remainder as a fresh request hides the over-read only while the remainder "
                     "fits in one read (a stream that skips 5 bytes once, asked for 5000 of 6000 bytes, still gives 6000; a "
                     "stream that never skips gives 6000 for 5000 whatever hop 4 passes), and halving the request or calling "
                     "skip once before delegating still return 11 for a stream that skips 3 bytes once or 3 and then 2 bytes.",
 "ownership_tests": ["org.apache.commons.compress.utils.IOUtilsTest::skipUsingRead",
                     "org.apache.commons.compress.utils.IOUtilsTest::skipUsingSkip",
                     "org.apache.commons.compress.archivers.tar.TarArchiveInputStreamTest::shouldConsumeArchiveCompletely",
                     "org.apache.commons.compress.archivers.ar.ArArchiveInputStreamTest::testReadLongNamesBSD"],
 "compensating": {
   "chain": [
     {"file": ZAIS, "old": "return TarArchiveEntry.completeSkip(in, count, skipped);",
      "new": "return Math.min(count, TarArchiveEntry.completeSkip(in, count, skipped));",
      "why": "hop 4 caps the reported count at the requested count"},
     {"file": ZAOS, "old": "if (count <= 0) {",
      "new": "if (count <= 0 || in.available() == 0) {",
      "why": "hop 1 also skips nothing when the stream reports no available bytes"},
     {"file": ZF, "old": "return ZipArchiveInputStream.skipRaw(in, count);",
      "new": "return ZipArchiveInputStream.skipRaw(new BufferedInputStream(in), count);",
      "why": "hop 3 skips through a buffered view of the stream"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 1): hosts are exactly hosts_hop_order of the batch-6 task record, hop i in "
               "host i: archivers/zip/ZipArchiveOutputStream (1501 lines, hop 1), compressors/bzip2/BZip2CompressorOutputStream "
               "(1329, hop 2), archivers/zip/ZipFile (1083, hop 3), archivers/zip/ZipArchiveInputStream (1074, hop 4), "
               "archivers/tar/TarArchiveEntry (1073, hop 5, gold); smallest host 1073 lines. All five are public concrete "
               "top-level classes in which a static method compiles; none was substituted. Anchors (stageB_lib.pick_anchor -> "
               "host_search.pick_insertion_anchor, instance seed 7530, seeds 7630-7634, all in the outer class): after "
               "setCreateUnicodeExtraFields (line index 337), after the BZip2CompressorOutputStream constructor (357), after "
               "the ZipFile constructor (165), after the ZipArchiveInputStream constructor (185), after isLink (773). The "
               "facade calls hop 1 by its fully-qualified name; hop 1 imports InputStream and BZip2CompressorOutputStream, hop "
               "2 InputStream and ZipFile, hop 3 needs no import (ZipArchiveInputStream is in its package), hop 4 imports "
               "TarArchiveEntry, the gold imports InputStream and IOUtils.",
}
