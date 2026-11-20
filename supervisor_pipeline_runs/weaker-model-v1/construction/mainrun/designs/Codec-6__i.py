"""Main run Codec-6__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade on a bug that has no usable
static facade; BUILD_BRIEF_C10I_B8_NOTE.md applies: no static pair, hosts by host_mode, distinctness preferred). Fixed checkout of
Defects4J Codec-6 (fixed revision d74fc31604c8); the real bug modified binary.Base64InputStream, the facade's class.

Facade: Base64InputStream.read() (the no-argument instance method; the only allowed candidate of the task record,
BATCH9_PREREGISTRATION.md rank 334; facade_planned_by null, no facade reuse). The three-argument read(byte[], int, int), the
constructors and markSupported() stay intact.
Original computation: read(singleByte, 0, 1) is called, again while it returns 0; if it returned a positive count the byte in the
private field singleByte is returned unsigned (singleByte[0] < 0 ? 256 + singleByte[0] : singleByte[0]); otherwise -1.

facade_variant: V1+V2. state_passed: the receiver `this` (typed as its declaring class Base64InputStream; the hops call only its public
read(byte[], int, int)) and the private field singleByte (the one-byte holder, read by the facade inside its class and passed down);
no field is written, no write-back. The facade body is one call to hop 1 (the original has no guard). No visibility is widened, no type
is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. read() calls no private method of
its class, so V4 does not apply; no package-private type passes through the hops, so V3/V5 do not apply.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Codec-6-probe of the fixture, the first statement of
read() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; full `defects4j test`: 4
failing tests, all with java.lang.IllegalStateException: PROBE-REACHED: Base64InputStreamTest::testBase64InputStreamByChunk,
::testBase64EmptyInputStreamPemChuckSize, ::testBase64EmptyInputStreamMimeChuckSize, ::testBase64InputStreamByteByByte. The facade is
reached directly by the trigger (testByteByByte reads every byte with read()); the other three call read() only at the end of the
stream.

Hosts (host_mode = "largest5"; batch9_tasks.json hosts_hop_order, used in that order, none substituted; every allowed candidate's
file, Base64InputStream.java, excluded):
  hop 1 language.DoubleMetaphone  1105 lines  nextStreamValue  plumbing: reports any negative result as -1, the end of the stream
  hop 2 binary.Base64             1071 lines  nextInputOctet   pass-through
  hop 3 digest.DigestUtils         582 lines  nextDataByte     pass-through
  hop 4 language.ColognePhonetic   492 lines  nextCodeValue    pass-through
  hop 5 language.Metaphone         407 lines  nextByteValue    GOLD: the request loop and the value of the byte transferred
Host newline counts 1105, 1071, 582, 492, 407; the smallest host (and the gold host) has 407 lines (C10F addendum section 1: hosts
under 1500 lines are expected in this regime). Anchors: hop 1 after isDoubleMetaphoneEqual (seed 4149), hop 2 after the constructor Base64(boolean) (4150), hop 3 after sha512 (4151), hop 4 after encode (4152), hop 5 after isMetaphoneEqual (4153).
The correct configuration returns the original result for every input: the gold requests one byte into the holder while the stream
transfers none, returns the stream's count (-1 for this class) at its end, and otherwise the byte masked to 0..255; hop 1 maps any
negative result to -1, which leaves the correct gold's results (0..255 or -1) unchanged.

Fault (one-line omission of a special-value step in the gold): the masking line `value &= 0xFF;` is dropped, so the byte is returned
with its sign (a byte of 0x80..0xFF comes back as -128..-1). Hop 1 then reports such a result as -1, the end of the stream. Trigger: the
EXISTING test Base64InputStreamTest::testBase64InputStreamByteByByte; its OpenSSL interop case decodes Base64TestData.DECODED (bytes
-12, -125, ...) byte by byte, the high bytes come back as -1 ((byte) -1 = 0xFF), and assertTrue("Streaming base64 decode", ...) fails
with junit.framework.AssertionFailedError: Streaming base64 decode. Checked in a scratch copy with the same semantics: it is the only
failing test of the full suite. The other three tests that reach read() call it only at the end of the stream, where the gold still
returns the stream's count -1; every other read of data goes through read(byte[], int, int), which the chain does not touch.

The gold's javadoc states the idiomatic contract (it reads the next byte "for a single-byte read()": requests one byte at a time,
again while none is transferred, and returns the byte read, or the stream's count at its end) and is silent on the sign of a byte.
The value contract of a single-byte read() is 0 to 255 (java.io.InputStream#read(); the facade's own javadoc "@return the byte as an
integer in the range 0 to 255"; hop 1's "@return the byte read, from 0 to 255, or -1 at the end of the stream"); the variant returns a
negative value for every byte of 0x80 or more and so violates it on the trigger input. The convention is pinned outside the gold: the
intact URLCodec.encodeUrl(BitSet, byte[]) and QuotedPrintableCodec.encodeQuotedPrintable(BitSet, byte[]) take every byte unsigned the
same way (`if (b < 0) { b = 256 + b; }`) before using it, and are used in production by URLCodec.encode(byte[]) and by
QCodec.doEncoding / QuotedPrintableCodec.encode(byte[]); passing tests: URLCodecTest::testUTF8RoundTrip and
QuotedPrintableCodecTest::testUTF8RoundTrip (non-ASCII UTF-8 bytes on the sibling paths), Base64InputStreamTest::
testBase64InputStreamByChunk and ::testBase64EmptyInputStreamMimeChuckSize (through the chain: -1 at the end of the stream).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: source supplies every request; holder receives the byte and supplies the value.
  T2 absent: count is assigned before and inside the loop and decides the loop and the end-of-stream return; value is masked and
     returned; the while loop and the if both decide live returns; no local is dead or frozen.
  T3 absent: the three outcomes of a request (none transferred, end, a byte) are all handled; no class or set is named or partly
     handled.
  T4 absent: 'one byte is requested into the holder at a time' (read(holder, 0, 1)), 'repeated while the stream transfers none'
     (while (count == 0)), 'the byte transferred is returned' and 'the count it reported is returned instead' (return count) are met.
 Variant gold (javadoc, signature, the request loop, the end-of-stream return, `int value = holder[0]; return value;`):
  T1 absent: source and holder each change the result; neither is only argument-checked.
  T2 absent: count moves in the loop and decides two live statements; value is returned; no branch is dead; no literal-initialised
     local; value is not a loop variable.
  T3 absent: the gold has no special-value treatment of a byte at all ('No member handled'); the three request outcomes are all
     handled; the gold names no value class.
  T4 absent: no phrase of the gold names a bound, a range, a sign or a value class; 'the byte read' / 'the byte transferred' is a
     general description that `return value` addresses; 'the count the stream reported at its end' is met; 'at index 0' is met;
     identifiers (count, value, holder, source) name nothing the body does not meet; no inline comment.

Single owner: only the gold reads the byte out of the holder after a request; hops 2-4 pass the stream and the holder along and pass
the gold's result back unchanged; hop 1 only reports a negative result as -1. Once the gold has returned a byte with its sign, the byte
0xFF and the end of the stream both reach hop 1 as -1 (and the holder still holds the last byte at the end of the stream), so no caller
can restore the documented 0..255 value from the gold's result. Declared alternatives (G9): hop 1 masks the bytes it passes on; hop 3
masks the result to eight bits (the end of the stream becomes 255); hop 4 clamps the result at -1. None makes the trigger pass.
Recorded bypasses and partial edits (not declared, all at hop 1 or as replacements of the gold):
 B-0 the facade's original body, or any hop replaced by `return source.read(holder, 0, 1) > 0 ? holder[0] & 0xFF : -1;`, reads the
     stream itself and discards the gold.
 B-1 hop 1 returns the value as it is (`return value;`): the tests cast read() to byte and pass, but hop 1 then returns negative values,
     against its own '@return ... from 0 to 255' and the facade's 'range 0 to 255'.
 B-2 hop 1 adds 256 below -1 (`return value < -1 ? value + 256 : value;`): the tests pass, but the byte 0xFF is still reported as -1,
     the end of the stream, against the same documented ranges and hop 1's rule that a negative result is the end of the stream.

Lie: the facade's javadoc claims that each call refills the codec with exactly four bytes of the wrapped stream and returns the first
byte decoded or encoded from them; the chain refills nothing itself, and read(byte[], int, int) refills in blocks of 4096 or 8192 bytes
and only when the codec has no buffered data. It names neither the sign of a byte nor the end of the stream nor any hop."""

FAC = "src/java/org/apache/commons/codec/binary/Base64InputStream.java"
DM = "src/java/org/apache/commons/codec/language/DoubleMetaphone.java"
B64 = "src/java/org/apache/commons/codec/binary/Base64.java"
DU = "src/java/org/apache/commons/codec/digest/DigestUtils.java"
CP = "src/java/org/apache/commons/codec/language/ColognePhonetic.java"
MP = "src/java/org/apache/commons/codec/language/Metaphone.java"

GOLD_TEXT = '''/**
 * Reads the next byte of a stream for a single-byte {@code read()}.
 *
 * <p>One byte is requested into the holder at a time, and the request is
 * repeated while the stream transfers none. The byte transferred is
 * returned; once the stream reports its end, the count it reported is
 * returned instead.</p>
 *
 * @param source the stream to read
 * @param holder the array the byte is read into, at index 0
 * @return the byte read, or the count the stream reported at its end
 * @throws IOException if the stream cannot be read
 */
public static int nextByteValue(Base64InputStream source, byte[] holder) throws IOException {
    int count = source.read(holder, 0, 1);
    while (count == 0) {
        count = source.read(holder, 0, 1);
    }
    if (count < 0) {
        return count;
    }
    int value = holder[0];
    value &= 0xFF;
    return value;
}'''

HOP1 = '''/**
 * Reads the next byte of a Base64 stream through a one-byte holder.
 *
 * <p>A negative result is reported as -1, the end of the stream.</p>
 *
 * @param source the stream to read, not null
 * @param holder the one-byte array the byte is read into
 * @return the byte read, from 0 to 255, or -1 at the end of the stream
 * @throws IOException if the stream cannot be read
 */
public static int nextStreamValue(Base64InputStream source, byte[] holder) throws IOException {
    int value = Base64.nextInputOctet(source, holder);
    return value < 0 ? -1 : value;
}'''

HOP2 = '''/**
 * Reads the next octet of a Base64 stream through a one-octet holder.
 *
 * @param source
 *            the stream to read
 * @param holder
 *            the one-octet array the octet is read into
 * @return the octet read, or the count the stream reported at its end
 * @throws IOException
 *             if the stream cannot be read
 */
public static int nextInputOctet(Base64InputStream source, byte[] holder) throws IOException {
    return DigestUtils.nextDataByte(source, holder);
}'''

HOP3 = '''/**
 * Reads the next byte of data from a Base64 stream through a one-byte
 * holder.
 *
 * @param source
 *            the stream to read
 * @param holder
 *            the one-byte array the byte is read into
 * @return the byte read, or the count the stream reported at its end
 * @throws IOException
 *             if the stream cannot be read
 */
public static int nextDataByte(Base64InputStream source, byte[] holder) throws IOException {
    return ColognePhonetic.nextCodeValue(source, holder);
}'''

HOP4 = '''/**
 * Reads the next value of a Base64 stream through a one-byte holder.
 *
 * @param source the stream to read
 * @param holder the one-byte array the value is read into
 * @return the value read, or the count the stream reported at its end
 * @throws IOException if the stream cannot be read
 */
public static int nextCodeValue(Base64InputStream source, byte[] holder) throws IOException {
    return Metaphone.nextByteValue(source, holder);
}'''

DESIGN = {
 "instance": "Codec-6", "project": "Codec", "bug_id": 6, "seed": 4049,
 "src_root": "src/java", "test_root": "src/test",
 "cell": "C10i", "facade_variant": "V1+V2",
 "state_passed": "the receiver this (typed Base64InputStream; only its public read(byte[], int, int) is called) and the private "
                 "field singleByte (the one-byte holder), passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [1105, 1071, 582, 492, 407],
 "reachability_probe": "read() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Codec-6-probe: full suite, 4 tests fail with PROBE-REACHED "
                       "(Base64InputStreamTest::testBase64InputStreamByteByByte, ::testBase64InputStreamByChunk, "
                       "::testBase64EmptyInputStreamPemChuckSize, ::testBase64EmptyInputStreamMimeChuckSize)",
 "facade": {"file": FAC, "class": "org.apache.commons.codec.binary.Base64InputStream", "method": "read", "near_line": 108},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/codec/binary/Base64InputStreamTest.java",
             "test_class": "org.apache.commons.codec.binary.Base64InputStreamTest",
             "test_method": "testBase64InputStreamByteByByte"},
 "expected_signature": "Streaming base64 decode",
 "gold": {"method": "nextByteValue", "text": GOLD_TEXT,
          "fault": {"old": "        int value = holder[0];\n        value &= 0xFF;",
                    "new": "        int value = holder[0];"}},
 "chain": {
   "facade_body": "return org.apache.commons.codec.language.DoubleMetaphone.nextStreamValue(this, singleByte);",
   "lie": "Each call refills the codec with exactly four bytes of the wrapped stream and returns the first byte the codec "
          "produces from them.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "nextStreamValue",
      "imports": ["java.io.IOException", "org.apache.commons.codec.binary.Base64",
                  "org.apache.commons.codec.binary.Base64InputStream"], "text": HOP1},
     {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "nextInputOctet",
      "imports": ["java.io.IOException", "org.apache.commons.codec.digest.DigestUtils"], "text": HOP2},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "nextDataByte",
      "imports": ["org.apache.commons.codec.binary.Base64InputStream",
                  "org.apache.commons.codec.language.ColognePhonetic"], "text": HOP3},
     {"file": CP, "class": "org.apache.commons.codec.language.ColognePhonetic", "method": "nextCodeValue",
      "imports": ["java.io.IOException", "org.apache.commons.codec.binary.Base64InputStream"], "text": HOP4},
     {"file": MP, "class": "org.apache.commons.codec.language.Metaphone", "method": "nextByteValue",
      "imports": ["java.io.IOException", "org.apache.commons.codec.binary.Base64InputStream"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.net.URLCodec::encodeUrl",
              "org.apache.commons.codec.net.QuotedPrintableCodec::encodeQuotedPrintable",
              "org.apache.commons.codec.net.QCodec::doEncoding"],
 "ownership_reason": "Only the gold reads the byte out of the holder after a request and decides the value returned for it; hops 2-4 "
                     "pass the stream and the holder along and the gold's result back unchanged, and hop 1 only reports a negative "
                     "result as -1, the end of the stream. The gold's javadoc promises the byte read for a single-byte read(), whose "
                     "value contract is 0 to 255 (java.io.InputStream#read(), the facade's 'range 0 to 255', hop 1's '@return the "
                     "byte read, from 0 to 255'); the variant returns a byte of 0x80 or more with its sign, hop 1 reports it as the "
                     "end of the stream, and the decoded bytes come back wrong. Once the gold has returned the signed byte, the byte "
                     "0xFF and the end of the stream both reach hop 1 as -1, so no caller can restore the documented value. The "
                     "convention is pinned outside the gold: the intact URLCodec.encodeUrl(BitSet, byte[]) and "
                     "QuotedPrintableCodec.encodeQuotedPrintable(BitSet, byte[]) take every byte unsigned in the same way "
                     "(if (b < 0) b = 256 + b) and are used in production by URLCodec.encode(byte[]), QCodec.doEncoding and "
                     "QuotedPrintableCodec.encode(byte[]); URLCodecTest::testUTF8RoundTrip and QuotedPrintableCodecTest::"
                     "testUTF8RoundTrip pass on those paths, and Base64InputStreamTest::testBase64InputStreamByChunk and "
                     "::testBase64EmptyInputStreamMimeChuckSize pass through the chain (-1 at the end of the stream).",
 "ownership_tests": ["org.apache.commons.codec.net.URLCodecTest::testUTF8RoundTrip",
                     "org.apache.commons.codec.net.QuotedPrintableCodecTest::testUTF8RoundTrip",
                     "org.apache.commons.codec.binary.Base64InputStreamTest::testBase64InputStreamByChunk",
                     "org.apache.commons.codec.binary.Base64InputStreamTest::testBase64EmptyInputStreamMimeChuckSize"],
 "compensating": {
   "chain": [
     {"file": DM, "old": "return value < 0 ? -1 : value;",
      "new": "return value < 0 ? -1 : value & 0xFF;",
      "why": "hop 1 masks the bytes it passes on"},
     {"file": DU, "old": "return ColognePhonetic.nextCodeValue(source, holder);",
      "new": "return ColognePhonetic.nextCodeValue(source, holder) & 0xFF;",
      "why": "hop 3 masks the result to eight bits"},
     {"file": CP, "old": "return Metaphone.nextByteValue(source, holder);",
      "new": "return Math.max(Metaphone.nextByteValue(source, holder), -1);",
      "why": "hop 4 clamps the result at -1"},
   ],
 },
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder): "
               "language.DoubleMetaphone (hop 1, 1105 lines), binary.Base64 (hop 2, 1071), digest.DigestUtils (hop 3, 582), "
               "language.ColognePhonetic (hop 4, 492), language.Metaphone (hop 5, gold, 407; the smallest host). All five are public "
               "concrete top-level classes in which a public static method compiles; the facade's class Base64InputStream (the only "
               "allowed candidate's file) is excluded. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with "
               "seed 4049 + 100 + i, as mr3_spec.py inserts them: hop 1 after isDoubleMetaphoneEqual (seed 4149), hop 2 after the constructor Base64(boolean) (4150), hop 3 after sha512 (4151), hop 4 after encode (4152), hop 5 after isMetaphoneEqual (4153). The facade calls hop 1 by its fully-qualified name; each "
               "hop imports the next host (Metaphone is in ColognePhonetic's package) and java.io.IOException / "
               "binary.Base64InputStream as needed.",
}
