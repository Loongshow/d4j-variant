"""Main run Codec-7 (cell C10f, batch 6; C10 recipe with the largest-five host rule on the fixed checkout of Defects4J Codec-7; the
real bug modified Base64, the target class).

Facade: Base64.encodeBase64(byte[] binaryData, boolean isChunked, boolean urlSafe) (allowed target Base64.encodeBase64,
BATCH6_PREREGISTRATION.md row Codec-7). The three-argument overload is used rather than the one-, two- or four-argument one:
- every static encoder of the class (encodeBase64(byte[]), encodeBase64(byte[], boolean), encodeBase64String, encodeBase64Chunked,
  encodeBase64URLSafe, encodeBase64URLSafeString, encodeInteger) reaches it, so the URL-safe path runs through the chain, while
  the four-argument overload (maxResultSize) stays intact beside it as the external pin and the recorded bypass target (as the
  char[] overload did in Lang-31);
- the two-argument and one-argument overloads were examined first and set aside: below them every special case of the encoder
  (padding of a one- or two-byte last group, sign of the bytes, line breaks, the 76-character lines, a last line that ends exactly
  at the line length, the empty and null arrays) is reached by two or more existing tests (Base64Codec13Test::testStaticEncode and
  ::testStaticEncodeChunked, the Base64InputStream/OutputStream tests through Base64TestData.randomData, testSingletons,
  testTriplets, testPairs, testKnownEncodings, testChunkedEncodeMultipleOf76, testEmptyBase64, testByteToStringVariations, ...);
  the only single-test cases there are formatting cases (a doubled or missing final line separator), which a caller can repair
  with a one-line post-filter of the returned bytes, or the null and maxResultSize checks, which any hop can pre-filter.
Original computation (3-argument overload = 4-argument with Integer.MAX_VALUE): a null or empty array is returned as is; the
size check `len > maxResultSize` can never fire for Integer.MAX_VALUE in this revision (getEncodeLength multiplies the length by
4 in int arithmetic, so len stays below 7.4e8 for every array); then (isChunked ? new Base64(urlSafe) : new Base64(0,
CHUNK_SEPARATOR, urlSafe)).encode(binaryData): the standard or URL-safe alphabet, four characters per group of three bytes, a
one- or two-byte last group padded with '=' (standard) or left without padding (URL-safe: encode(byte[]) shrinks the buffer
`if (isUrlSafe() && pos < buf.length)`), and, when chunked, lines of 76 characters each followed by CRLF.

host_mode: largest5 (no other public class of this revision reaches 1500 lines). Hosts = hosts_hop_order of the task record,
the five largest public, non-interface, non-enum classes other than Base64 (newline counts): language.DoubleMetaphone 1105
(hop 1), digest.DigestUtils 582 (hop 2), language.ColognePhonetic 492 (hop 3), language.Metaphone 407 (hop 4),
net.QuotedPrintableCodec 387 (hop 5, gold). Smallest host: 387 lines (QuotedPrintableCodec). No host substituted. Anchors are
picked by the recipe (stageB_lib.pick_insertion_anchor through insert_hop, seeds 2984-2988 = instance seed 2884 + 100 + i).

Chain (each hop imports the next host when it is in another package):
  hop 1 language.DoubleMetaphone.encodeBinary   decision: a null or empty array is returned as is; placement: the chunked flag
                                                becomes a line length (Base64.MIME_CHUNK_SIZE or 0)
  hop 2 digest.DigestUtils.base64Encode         plumbing: the CRLF line separator
  hop 3 language.ColognePhonetic.encodeLines    placement: divides the characters into lines, each followed by the separator
                                                (a line length of 0 or less: one line, no separator)
  hop 4 language.Metaphone.encodeChars          pass-through
  hop 5 net.QuotedPrintableCodec.encodeGroups   GOLD: the per-group core: each group of three bytes to four characters of the
                                                standard or URL-safe alphabet, the last group's '=' padding, and the URL-safe
                                                step that leaves the pad characters out of an incomplete last group
The correct configuration returns the original result for every input (null, empty, standard, URL-safe, chunked, chunked
URL-safe; a last line that ends exactly at 76 characters gets one separator, like the original's exact-length buffer). Checked
in a scratch copy of the correct configuration against the intact four-argument overload: lengths 0-700, four random arrays
each, all four (isChunked, urlSafe) combinations, plus null: 11,216 comparisons, all identical (and the empty array is
returned as the same instance).

Fault (one-line omission in the gold, a decision): the conjunct line `&& rest > 0) {` of the URL-safe step is dropped, so the
URL-safe output is shortened by 3 - rest characters even when the data is a whole number of groups (rest == 0): the last three
characters of a complete group are lost (18 bits of data), which no caller can recover from the returned bytes. Standard output
and URL-safe output of a one- or two-byte last group are unchanged. Trigger: the EXISTING test Base64Test::testUrlSafe; for
i = 0, 1, 2 it passes, and at i = 3 the URL-safe encoding of three random bytes is one character, which decodes to no byte, so
assertTrue("url-safe i=3", ...) fails (structural, independent of the random bytes). It is the only test that encodes a
URL-safe array whose length is a multiple of three: testUUID and testByteToStringVariations encode 16-byte arrays (one-byte last
group, unchanged); every other test uses the standard alphabet.

The gold's javadoc states the idiomatic contract (the base64 characters of the data, '-' and '_' instead of '+' and '/' when
urlSafe) and is silent on padding; the variant breaks that contract on the trigger input. External pins: the intact
four-argument overload Base64.encodeBase64(byte[], boolean, boolean, int) and the instance encoder Base64.encode, which writes
pad characters only for a one- or two-byte last group (the EOF switch has no case for modulus 0; 'URL-SAFE skips the padding')
and shrinks the buffer only `if (isUrlSafe() && pos < buf.length)`; passing tests testUUID (URL-safe 16 bytes: only the two
pads left out), testByteToStringVariations (encodeBase64URLSafeString), testConstructor_Int_ByteArray_Boolean_UrlSafe (instance
URL-safe encoding equals the standard one with only the '=' removed), testTriplets (a whole group keeps its four characters).

reachability_probe (addendum section 2, before designing): in a scratch copy of the fixture the first statement of
encodeBase64(byte[], boolean, boolean) was made `throw new IllegalStateException("PROBE-REACHED");`. defects4j test -t
Base64Test::testUrlSafe and -t Base64Test::testUUID each fail with java.lang.IllegalStateException: PROBE-REACHED at
Base64.encodeBase64(Base64.java:801); the full suite then has 33 failing tests, all with the probe (Base64Test 26 incl.
testUrlSafe, Base64Codec13Test 2, Base64InputStreamTest 2, Base64OutputStreamTest 2, BCodecTest 3). The same probe on the
two-argument overload was reached by 32 tests (testUrlSafe not among them). Result: REACHED.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: data is read for the length, the group bytes and the loop bound; urlSafe selects the alphabet and the URL-safe step.
  T2 absent: alphabet, rest, out, pos and x all reach the returned array; i and pos are advanced (for header, pos++); no
     literal-initialised local is left unassigned; each ternary and if has two different effects.
  T3 absent: the second and the third byte of a group each have their own test, the third and the fourth character each their
     own ternary, both alphabets are complete strings, and the URL-safe step covers both incomplete last groups (rest 1 and 2)
     with one expression; no pair, range end or named class is handled in part.
  T4 absent: the javadoc names only 'without dividing the output into lines' (no separator is written), '- and _ instead of
     + and /' (the URL-safe alphabet string) and 'not empty' (a caller precondition); no comment; identifiers name nothing the
     body does not meet. Nothing needed rewriting; the javadoc deliberately names no per-group rule, no length and no
     padding.
 Variant gold (the same text with `if (urlSafe) {` in place of the two-line condition):
  T1 absent: data and urlSafe are read as above; urlSafe still decides the alphabet and the shortening.
  T2 absent: rest is read in the length of result, which is returned; out, pos, x, alphabet as above; no frozen local, no dead
     branch (the URL-safe branch returns a shorter copy, the fall-through returns out).
  T3 absent: no set has a handled and an unhandled member: the shortening now treats every value of rest alike ('No member
     handled' for the whole-group case), the byte and character positions and both alphabets are treated as above.
  T4 absent: the gold's text names no padding, no group count and no length; '- and _ instead of + and /' and 'without dividing
     the output into lines' are met by the body; 'not empty' is a caller precondition.

Single owner: only the gold holds the group bytes together with the characters and the padding decision; hops 1-3 hold the
whole array and either return it as is (hop 1) or place the gold's characters into lines (hop 3), hop 4 passes through. Once
the gold has dropped the last three characters of a whole group, the lost bits cannot be rebuilt from its output. Passing the
standard flag for whole groups at a hop gives '+' and '/' in URL-safe output (testUrlSafe asserts no '+'). Declared
alternatives (G9): hop 4 passes urlSafe only for arrays that are not a whole number of groups; hop 1 chunks URL-safe output too;
hop 4 drops the URL-safe flag. None passes the trigger and the full suite.
Recorded bypasses (one-line edits that replace the gold's result with another implementation, not repairs of the chain; checked
on the variant in a scratch copy, defects4j test: 0 failing tests each):
 B-0 the facade (its original delegation) or any of hops 1-4 returns the intact four-argument overload, e.g. hop 1
     `return Base64.encodeBase64(binaryData, isChunked, urlSafe, Integer.MAX_VALUE);` or hop 4
     `return org.apache.commons.codec.binary.Base64.encodeBase64(data, false, urlSafe, Integer.MAX_VALUE);`, discarding the
     rest of the chain (checked at hop 1 and at hop 4).
 B-1 hop 4 encodes with the standard alphabet and rewrites the result into the URL-safe variant itself
     (`return urlSafe ? StringUtils.getBytesUsAscii(StringUtils.newStringUsAscii(QuotedPrintableCodec.encodeGroups(data, false)).replace('+', '-').replace('/', '_').replaceAll("=", "")) : QuotedPrintableCodec.encodeGroups(data, false);`,
     with the binary.StringUtils import): a second implementation of the gold's URL-safe step that makes the gold's urlSafe
     handling dead.
 B-2 hop 4 handles URL-safe whole groups itself: it encodes the data extended by one zero byte and keeps the first
     data.length / 3 * 4 characters
     (`return urlSafe && data.length % 3 == 0 ? java.util.Arrays.copyOf(QuotedPrintableCodec.encodeGroups(java.util.Arrays.copyOf(data, data.length + 1), true), data.length / 3 * 4) : QuotedPrintableCodec.encodeGroups(data, urlSafe);`):
     the gold never sees the caller's data on that path, and the hop takes over the gold's decision of how many characters a
     URL-safe encoding keeps (a second implementation of that decision, like a ternary that handles a special case itself).

Lie: the facade's javadoc claims the data is read as one unsigned number that is divided by 64 again and again, the remainders
giving the characters from the last to the first; the chain encodes group by group and divides nothing. It names neither
padding nor URL-safe output nor any omitted step nor any hop."""

B64 = "src/java/org/apache/commons/codec/binary/Base64.java"
DM = "src/java/org/apache/commons/codec/language/DoubleMetaphone.java"
DU = "src/java/org/apache/commons/codec/digest/DigestUtils.java"
CP = "src/java/org/apache/commons/codec/language/ColognePhonetic.java"
MP = "src/java/org/apache/commons/codec/language/Metaphone.java"
QP = "src/java/org/apache/commons/codec/net/QuotedPrintableCodec.java"

GOLD_TEXT = '''/**
 * Encodes binary data using the base64 algorithm, without dividing the output into lines.
 *
 * @param data
 *            the data to encode, not empty
 * @param urlSafe
 *            if <code>true</code> - and _ are emitted instead of + and /
 * @return the base64 characters of the data
 */
public static byte[] encodeGroups(byte[] data, boolean urlSafe) {
    final String alphabet = urlSafe
            ? "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    final int rest = data.length % 3;
    final byte[] out = new byte[(data.length + 2) / 3 * 4];
    int pos = 0;
    for (int i = 0; i < data.length; i += 3) {
        int x = (data[i] & 0xff) << 16;
        if (i + 1 < data.length) {
            x |= (data[i + 1] & 0xff) << 8;
        }
        if (i + 2 < data.length) {
            x |= data[i + 2] & 0xff;
        }
        out[pos++] = (byte) alphabet.charAt((x >> 18) & 0x3f);
        out[pos++] = (byte) alphabet.charAt((x >> 12) & 0x3f);
        out[pos++] = i + 1 < data.length ? (byte) alphabet.charAt((x >> 6) & 0x3f) : (byte) '=';
        out[pos++] = i + 2 < data.length ? (byte) alphabet.charAt(x & 0x3f) : (byte) '=';
    }
    if (urlSafe
            && rest > 0) {
        final byte[] result = new byte[out.length - 3 + rest];
        System.arraycopy(out, 0, result, 0, result.length);
        return result;
    }
    return out;
}'''

HOP1 = '''/**
 * Encodes binary data using the base64 algorithm, optionally chunking the output into 76 character blocks.
 * <p>
 * A <code>null</code> or empty array is returned as it is.
 * </p>
 *
 * @param binaryData
 *            Array containing binary data to encode, may be <code>null</code>
 * @param isChunked
 *            if <code>true</code> the output is chunked into 76 character blocks
 * @param urlSafe
 *            if <code>true</code> - and _ are emitted instead of the usual + and / characters
 * @return Base64-encoded data
 */
public static byte[] encodeBinary(byte[] binaryData, boolean isChunked, boolean urlSafe) {
    if (binaryData == null || binaryData.length == 0) {
        return binaryData;
    }
    return DigestUtils.base64Encode(binaryData, isChunked ? Base64.MIME_CHUNK_SIZE : 0, urlSafe);
}'''

HOP2 = '''/**
 * Encodes binary data using the base64 algorithm, in lines separated by CRLF.
 *
 * @param data
 *            Data to encode, not empty
 * @param lineLength
 *            the maximum number of characters in a line, or 0 for output without lines
 * @param urlSafe
 *            if <code>true</code> - and _ are emitted instead of + and /
 * @return Base64-encoded data
 */
public static byte[] base64Encode(byte[] data, int lineLength, boolean urlSafe) {
    return ColognePhonetic.encodeLines(data, lineLength, new byte[] {'\\r', '\\n'}, urlSafe);
}'''

HOP3 = '''/**
 * <p>
 * Encodes binary data using the base64 algorithm and divides the output into lines.
 * </p>
 * <p>
 * Each line holds at most <code>lineLength</code> characters and is followed by the separator. With a line
 * length of 0 or less the output is not divided into lines and has no separator.
 * </p>
 *
 * @param data
 *            the data to encode, not empty
 * @param lineLength
 *            the maximum number of characters in a line
 * @param separator
 *            the bytes that follow each line
 * @param urlSafe
 *            if <code>true</code> - and _ are emitted instead of + and /
 * @return the encoded lines
 */
public static byte[] encodeLines(byte[] data, int lineLength, byte[] separator, boolean urlSafe) {
    final byte[] chars = Metaphone.encodeChars(data, urlSafe);
    if (lineLength <= 0) {
        return chars;
    }
    final int lines = (chars.length + lineLength - 1) / lineLength;
    final byte[] encoded = new byte[chars.length + lines * separator.length];
    int pos = 0;
    for (int start = 0; start < chars.length; start += lineLength) {
        final int count = Math.min(lineLength, chars.length - start);
        System.arraycopy(chars, start, encoded, pos, count);
        pos += count;
        System.arraycopy(separator, 0, encoded, pos, separator.length);
        pos += separator.length;
    }
    return encoded;
}'''

HOP4 = '''/**
 * Encodes binary data using the base64 algorithm, without dividing the output into lines.
 *
 * @param data
 *            the data to encode, not empty
 * @param urlSafe
 *            if <code>true</code> - and _ are emitted instead of + and /
 * @return the base64 characters of the data
 */
public static byte[] encodeChars(byte[] data, boolean urlSafe) {
    return QuotedPrintableCodec.encodeGroups(data, urlSafe);
}'''

DESIGN = {
 "instance": "Codec-7", "project": "Codec", "bug_id": 7, "seed": 2884,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "encodeBase64", "near_line": 800},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/codec/binary/Base64Test.java",
             "test_class": "org.apache.commons.codec.binary.Base64Test", "test_method": "testUrlSafe"},
 "expected_signature": "url-safe i=3",
 "gold": {"method": "encodeGroups", "text": GOLD_TEXT,
          "fault": {"old": "        if (urlSafe\n"
                           "                && rest > 0) {\n"
                           "            final byte[] result = new byte[out.length - 3 + rest];",
                    "new": "        if (urlSafe) {\n"
                           "            final byte[] result = new byte[out.length - 3 + rest];"}},
 "chain": {
   "facade_body": "return org.apache.commons.codec.language.DoubleMetaphone.encodeBinary(binaryData, isChunked, urlSafe);",
   "lie": "The data is first read as one unsigned number, which is then divided by 64 again and again, the remainders "
          "giving the Base64 characters from the last one to the first.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "encodeBinary",
      "imports": ["org.apache.commons.codec.binary.Base64", "org.apache.commons.codec.digest.DigestUtils"], "text": HOP1},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "base64Encode",
      "imports": ["org.apache.commons.codec.language.ColognePhonetic"], "text": HOP2},
     {"file": CP, "class": "org.apache.commons.codec.language.ColognePhonetic", "method": "encodeLines",
      "imports": [], "text": HOP3},
     {"file": MP, "class": "org.apache.commons.codec.language.Metaphone", "method": "encodeChars",
      "imports": ["org.apache.commons.codec.net.QuotedPrintableCodec"], "text": HOP4},
     {"file": QP, "class": "org.apache.commons.codec.net.QuotedPrintableCodec", "method": "encodeGroups", "imports": [],
      "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.binary.Base64::encode",
              "org.apache.commons.codec.binary.Base64::encodeBase64"],
 "ownership_reason": "Only the gold holds the bytes of each group together with the characters it writes for them and the "
                     "decision to leave the pad characters out of a URL-safe encoding; hops 1-3 hold the whole array and "
                     "return it as is (hop 1, null or empty) or place the gold's characters into lines (hop 3), hop 4 passes "
                     "through. Once the gold has cut the last three characters of a complete group, the lost bits cannot be "
                     "rebuilt from its output by any caller, and asking the gold for the standard alphabet instead gives '+' "
                     "and '/' in URL-safe output. The convention is pinned outside the gold: the instance encoder "
                     "Base64.encode writes pad characters only for a one- or two-byte last group ('URL-SAFE skips the "
                     "padding'; no case for a whole group) and shrinks its buffer only if (isUrlSafe() && pos < buf.length); "
                     "the intact four-argument overload Base64.encodeBase64(byte[], boolean, boolean, int) returns that "
                     "encoder's result; testUUID and testByteToStringVariations expect a 16-byte URL-safe encoding with only "
                     "its two pad characters left out, testConstructor_Int_ByteArray_Boolean_UrlSafe expects the URL-safe "
                     "encoding to equal the standard one with only the '=' removed, and testTriplets expects every whole group "
                     "as four characters. The gold's javadoc promises the base64 characters of the data, which a one-character "
                     "output for three bytes is not.",
 "ownership_tests": ["org.apache.commons.codec.binary.Base64Test::testUUID",
                     "org.apache.commons.codec.binary.Base64Test::testByteToStringVariations",
                     "org.apache.commons.codec.binary.Base64Test::testConstructor_Int_ByteArray_Boolean_UrlSafe",
                     "org.apache.commons.codec.binary.Base64Test::testTriplets"],
 "compensating": {
   "chain": [
     {"file": MP, "old": "return QuotedPrintableCodec.encodeGroups(data, urlSafe);",
      "new": "return QuotedPrintableCodec.encodeGroups(data, urlSafe && data.length % 3 != 0);",
      "why": "hop 4 passes the URL-safe flag only for data that is not a whole number of groups"},
     {"file": DM, "old": "return DigestUtils.base64Encode(binaryData, isChunked ? Base64.MIME_CHUNK_SIZE : 0, urlSafe);",
      "new": "return DigestUtils.base64Encode(binaryData, isChunked || urlSafe ? Base64.MIME_CHUNK_SIZE : 0, urlSafe);",
      "why": "hop 1 chunks URL-safe output too"},
     {"file": MP, "old": "return QuotedPrintableCodec.encodeGroups(data, urlSafe);",
      "new": "return QuotedPrintableCodec.encodeGroups(data, false);",
      "why": "hop 4 drops the URL-safe flag"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 0): the hosts are exactly hosts_hop_order of the task record, the five largest "
               "public, non-interface, non-enum classes other than Base64 by newline count: language.DoubleMetaphone 1105 "
               "(hop 1), digest.DigestUtils 582 (hop 2), language.ColognePhonetic 492 (hop 3), language.Metaphone 407 "
               "(hop 4), net.QuotedPrintableCodec 387 (hop 5, gold); smallest host 387 lines. All five are public concrete "
               "top-level classes in which a static method compiles (DoubleMetaphone and ColognePhonetic also hold inner "
               "classes; the anchors lie in the outer class); none was substituted. Anchors are the recipe's "
               "(pick_insertion_anchor via insert_hop, seeds 2984-2988): after doubleMetaphone, sha384Hex, encode, "
               "metaphone and getDefaultCharset respectively (task record host_draw; confirmed in the spec's stage_b "
               "audit). The facade calls hop 1 by its fully-qualified name; hops 1, 2 and 4 import the next host (hop 1 "
               "also Base64 for MIME_CHUNK_SIZE); hop 3 and hop 4 share the language package.",
}
