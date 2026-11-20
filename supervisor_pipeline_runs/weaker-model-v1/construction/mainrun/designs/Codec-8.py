"""Main run Codec-8 (cell C10f, batch 6; the C10 recipe with fallback hosts on the fixed checkout of Defects4J Codec-8; the real
bug modified Base64 and Base64InputStream, and Base64 is the target class).

Facade: Base64.encodeBase64(byte[], boolean, boolean, int), an allowed target of BATCH6_PREREGISTRATION row 138 (encodeBase64);
facade_reuse_of Codec-4, Codec-5, Codec-7 is recorded (the same method is the facade of Codec-7). It is the pool's 15-line candidate
and the overload in which every other static encode method of Base64 ends. The two other allowed targets were set aside:
 - encodeInteger: its only own step is the sign-byte removal of toIntegerBytes, which testCodeInteger1 and testCodeInteger2 both
   exercise (both integers have 160 bits, a multiple of 8), so an omission there fails two tests (gate G5); every other step is
   the shared base64 encoding, reached by all four testCodeInteger tests.
 - isArrayByteBase64: its per-byte rule (alphabet, pad or whitespace) has one decision reached by a single test (the whitespace
   acceptance, testIsUrlSafe); a quiet gold cannot state a contract that covers whitespace without naming it, and any caller
   that strips whitespace before the check undoes the omission.
Original computation of the facade: a null or empty array is returned as is; an encoded length (estimated with the MIME chunk
size) above maxResultSize throws IllegalArgumentException; otherwise a Base64 codec with line length 76 and CRLF (chunked) or
without line division (not chunked), in the standard or the URL-safe alphabet, encodes the array with the streaming encoder
Base64.encode(byte[], int, int): every group of three bytes becomes four characters; a final group of one or two bytes becomes two
or three characters, completed with '=' in the standard alphabet only; in chunked output CRLF follows every full line of 76
characters and, at the end, the last line, unless the output already ends with CRLF ("Don't want to append the CRLF two times in
a row").

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2): scratch copies of the fixture under /private/tmp/codec8-v2, the facade's
first statement made `throw new IllegalStateException("PROBE-REACHED")`, compiled, then
 - defects4j test -t Base64Codec13Test::testStaticEncodeChunked: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED;
 - defects4j test (full suite): 34 failing tests, all 34 with PROBE-REACHED (25 Base64Test, 2 Base64Codec13Test, 2
   Base64InputStreamTest, 2 Base64OutputStreamTest, 3 BCodecTest). REACHED.
 The same probe on the two other allowed targets: isArrayByteBase64 5 failing, all with PROBE-REACHED; encodeInteger 5 failing,
 4 with PROBE-REACHED (testCodeIntegerNull catches the exception and fails with its own message). Both reached, both set aside
 for the reasons above.

Hosts: host_mode = largest5 (the fixed revision has no other public class of 1500 lines, n1500_other = 0). The five hosts are
hosts_hop_order of the task record, the five largest public non-interface non-enum classes other than Base64 by newline count,
in that order; anchors from stageB_lib.pick_anchor / host_search.pick_insertion_anchor with seed 6049 + 100 + i, as mr2_spec.py
inserts them:
  hop 1 language.DoubleMetaphone     1105 lines   anchor after setMaxCodeLen (seed 6149)
  hop 2 digest.DigestUtils            582 lines   anchor after md5 (seed 6150)
  hop 3 language.ColognePhonetic      492 lines   anchor after encode (seed 6151)
  hop 4 language.Metaphone            407 lines   anchor after encode (seed 6152)
  hop 5 net.QuotedPrintableCodec      387 lines   anchor after the QuotedPrintableCodec(String) constructor (seed 6153); GOLD
host_lines = [1105, 582, 492, 407, 387]; smallest host (and gold host): 387 lines. No host substituted.

Chain:
  hop 1 DoubleMetaphone.toBase64                decision: chunked output gets the MIME line length 76, otherwise 0
  hop 2 DigestUtils.base64Encode                placement: the line separator CRLF
  hop 3 ColognePhonetic.base64Of                placement: the standard or the URL-safe alphabet as 64 bytes
  hop 4 Metaphone.base64Bytes                   decision: URL-safe output is not padded
  hop 5 QuotedPrintableCodec.encodeBase64Bytes  GOLD: the per-group core (three bytes to four characters, then the final group
                                                of one or two bytes with its padding) and the division of the characters into
                                                lines with the separator
The correct configuration returns the original bytes for every input that reaches the chain (non-empty arrays), in the order of
the streaming encoder: the full groups, a line ended inside the loop as soon as it holds lineLength characters; then the final
group of one or two bytes, if any, with the same characters and padding rule; then the closing separator, written when lines are
divided and the last line is not empty (characters of full groups after the last separator, or a final partial group), which is
the streaming encoder's test that the output does not already end with the separator. Same alphabets, same line length (76 is a
multiple of 4), same separator.

Gold's own contract (quiet): the javadoc says the bytes are encoded with the base64 algorithm and the alphabet, that each group of
three bytes becomes four characters, and that with a positive line length the output is divided into lines the way
Base64.encode(byte[]) divides it for a codec of that line length and separator; it says nothing about a line that ends exactly at
the end of the data.

Fault (omission of a decision in the gold): the closing separator is written whenever lines are divided (`if (lineLength > 0)`);
the condition that the last line is not empty (`&& (column > 0 || count > 0)`) is dropped. When the input is a whole number of
full lines (a multiple of 57 bytes for 76-character lines: 19 groups per line, no final partial group), the last line already got
its separator inside the loop and gets a second one, which Base64.encode(byte[]) never writes. Trigger: the EXISTING test
Base64Codec13Test::testStaticEncodeChunked, which compares Base64.encodeBase64Chunked with the output of commons-codec 1.3 for its
vectors (sizes 0-16, 63-82 and 121-180); the only multiple of 57 among them is the 171-byte vector (57 groups, 228 characters,
exactly three lines), which ends in "\\r\\n\\r\\n": assertTrue("static Base64.encodeBase64Chunked() test-171", false). The 169- and
170-byte vectors also end exactly at a line end, but with a final partial group, after which the closing separator is the first
one, as in the correct configuration; so does testChunkedEncodeMultipleOf76 (its last 76-character line ends in 'u2A='). Every
other chunked static encode in the suite ends in a shorter last line (testKnownEncodings, testSingletonsChunked,
testTripletsChunked, the other Codec13 vectors); the stream tests use the streaming encoder (intact) or unchunked static encoding,
so no other test newly fails.

External pins (outside the gold's javadoc): Base64.encode(byte[], int, int), the streaming encoder of the same class, writes the
final separator only if the previous character is not the end of the separator ("Don't want to append the CRLF two times in a
row"); Base64.getEncodeLength sizes chunked output with one separator per line and no extra one when the length chunks perfectly
(lenChunksPerfectly); Base64OutputStream.close ends a chunked stream through the streaming encoder. Passing tests show one
separator after the last line: Base64Test testChunkedEncodeMultipleOf76 (76-character lines against ENCODED_76_CHARS_PER_LINE,
last line exactly full), testKnownEncodings ("...bGFoIGJsYWg=\\r\\n"), testSingletonsChunked ("AA==\\r\\n"), and
Base64OutputStreamTest testBase64OutputStreamByChunk (the streaming encoder with line length 76 and CRLF).

Single owner: only the gold sees the encoded characters together with the position reached in the current line; hops 1-4 choose
the line length, the separator, the alphabet and the padding, and get back the finished bytes. No choice of those inputs removes
the second separator while keeping 76-character lines ended by CRLF. Declared alternatives (G9): hop 1 rounds the line length
down to a multiple of 4 (as the Base64 constructor does), hop 2 passes LF alone as the separator, hop 4 asks for padding only
when a final partial group exists; none removes the second separator.
Recorded one-line edits above the gold that pass the trigger and the full suite (bypasses, not repairs of the chain):
 B-0 the facade's original body (`Base64 b64 = isChunked ? new Base64(urlSafe) : new Base64(0, CHUNK_SEPARATOR, urlSafe);
     return b64.encode(binaryData);`), or any of hops 1-4 returning `new org.apache.commons.codec.binary.Base64(lineLength,
     separator, urlSafe).encode(data)` (the streaming encoder through Base64's public constructor), discarding the rest of the
     chain including the gold.
 B-1 a hop re-decides the line end itself and cuts the gold's output, e.g. hop 4
     `final byte[] out = QuotedPrintableCodec.encodeBase64Bytes(data, lineLength, separator, alphabet, !urlSafe); return lineLength
     > 0 && data.length % (lineLength / 4 * 3) == 0 ? java.util.Arrays.copyOf(out, out.length - separator.length) : out;`: a second
     implementation, outside the gold, of the gold's decision whether the last line has already been ended; it overwrites the
     gold's result instead of using it as documented (hop 4's own step is the padding choice), and with it in place the gold still
     writes, on the trigger input, a separator that Base64.encode(byte[]) does not write.
 Both checked at hop 4 on the variant in a scratch copy (/private/tmp/codec8-v2): trigger passes, full suite 0 failing tests.

Lie: the facade's javadoc claims each 12-bit half of a three-byte group is translated at once into two characters through a
4096-entry table; the chain uses no such table and looks up one 6-bit value per character. It names neither lines, separators,
padding, nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: data feeds every group, lineLength the in-loop line end and the closing separator, separator both writes, alphabet
     every character, pad the '=' loop; no argument check.
  T2 absent: buffer is returned; column is advanced and reset in the loop and read in both line-end tests; i (initialised to 0)
     is advanced by the loop header and read for count; count and both bits are assigned and read; no dead branch (the ternary
     takes the second byte or zero, the if on count writes the final group or nothing, both separator ifs write or not).
  T3 absent: the closing test covers both ways a last line can be non-empty (characters of full groups, a final partial group);
     the final group treats one and two bytes alike (k up to count, padding from count to 3); no named class handled in part.
  T4 absent: 'Each group of three bytes is written as four characters of the alphabet', '0 for no line division' and the pad
     clause are met; the line division is that of Base64.encode(byte[]) for the same line length and separator (one separator
     after every full line and one after a non-empty last line); 'a multiple of 4' and 'not null' are caller preconditions.
 Variant gold (the closing test reads `if (lineLength > 0) {`):
  T1 absent: every parameter still changes the result: data (groups), lineLength (the loop test and the closing test),
     separator (both writes), alphabet (every character), pad (the '=' loop).
  T2 absent: column is advanced, reset and read in the loop test that decides the in-loop separator write; i is advanced by the
     loop header and read for count; count decides whether and how the final group is written; buffer is returned; no local is
     initialised to a literal and left unassigned, and no loop cursor, counter or flag stays unmoved; the closing if still
     decides whether a separator is written (lineLength 0 writes none), so no decision is dead.
  T3 absent: no set with a handled and an unhandled member: the final group treats one and two bytes alike; the four characters
     of a group are all written; lineLength 0 and positive both decide both separator writes; no pair, range end or named class.
     The final group is not added to column, which nothing after it reads: a line ends inside the loop only after full groups,
     and the line holding the final group is ended by the closing separator, so no group goes without a line end.
  T4 absent: the javadoc names no count of separators, no rule for a line that ends at the end of the data and no other
     concrete rule the body visibly breaks: groups become four characters, lineLength 0 writes no separator, the pad clause is
     met, and the line division is stated only by reference to Base64.encode(byte[]); 'a multiple of 4' and 'not null' are caller
     preconditions; identifiers (column, count, bits, buffer) name nothing the body does not do."""

B64 = "src/java/org/apache/commons/codec/binary/Base64.java"
DM = "src/java/org/apache/commons/codec/language/DoubleMetaphone.java"
DU = "src/java/org/apache/commons/codec/digest/DigestUtils.java"
CP = "src/java/org/apache/commons/codec/language/ColognePhonetic.java"
MP = "src/java/org/apache/commons/codec/language/Metaphone.java"
QP = "src/java/org/apache/commons/codec/net/QuotedPrintableCodec.java"

GOLD_TEXT = '''/**
 * Encodes binary data using the base64 algorithm with the given alphabet.
 * <p>
 * Each group of three bytes is written as four characters of the alphabet. When the line length is positive, the
 * output is divided into lines the way {@link org.apache.commons.codec.binary.Base64#encode(byte[])} divides it for a
 * codec with that line length and line separator.
 * </p>
 *
 * @param data
 *            binary data to encode, not null
 * @param lineLength
 *            the line length, a multiple of 4, or 0 for no line division
 * @param separator
 *            the line separator
 * @param alphabet
 *            the 64 characters of the encoding alphabet, in the order of their 6-bit values
 * @param pad
 *            if <code>true</code>, a final group of fewer than three bytes is completed with '=' characters
 * @return the encoded data
 */
public static byte[] encodeBase64Bytes(byte[] data, int lineLength, byte[] separator, byte[] alphabet, boolean pad) {
    ByteArrayOutputStream buffer = new ByteArrayOutputStream();
    int column = 0;
    int i = 0;
    for (; i + 3 <= data.length; i += 3) {
        int bits = ((data[i] & 0xff) << 16) | ((data[i + 1] & 0xff) << 8) | (data[i + 2] & 0xff);
        for (int k = 0; k < 4; k++) {
            buffer.write(alphabet[(bits >> (18 - 6 * k)) & 0x3f]);
        }
        column += 4;
        if (lineLength > 0 && column >= lineLength) {
            buffer.write(separator, 0, separator.length);
            column = 0;
        }
    }
    int count = data.length - i;
    if (count > 0) {
        int bits = ((data[i] & 0xff) << 16) | (count > 1 ? (data[i + 1] & 0xff) << 8 : 0);
        for (int k = 0; k <= count; k++) {
            buffer.write(alphabet[(bits >> (18 - 6 * k)) & 0x3f]);
        }
        for (int k = count; pad && k < 3; k++) {
            buffer.write('=');
        }
    }
    if (lineLength > 0 && (column > 0 || count > 0)) {
        buffer.write(separator, 0, separator.length);
    }
    return buffer.toByteArray();
}'''

HOP1 = '''/**
 * Encodes binary data using the base64 algorithm, optionally chunking the output into 76 character blocks.
 *
 * @param binaryData
 *            binary data to encode, not null
 * @param isChunked
 *            if <code>true</code> the output is chunked into blocks of {@link Base64#MIME_CHUNK_SIZE} characters
 * @param urlSafe
 *            if <code>true</code> - and _ are emitted instead of the usual + and / characters
 * @return Base64-encoded data
 */
public static byte[] toBase64(byte[] binaryData, boolean isChunked, boolean urlSafe) {
    return DigestUtils.base64Encode(binaryData, isChunked ? Base64.MIME_CHUNK_SIZE : 0, urlSafe);
}'''

HOP2 = '''/**
 * Encodes binary data using the base64 algorithm, dividing the output into lines of the given length.
 * <p>
 * The line separator is CRLF.
 * </p>
 *
 * @param data
 *            binary data to encode, not null
 * @param lineLength
 *            number of characters per line, or 0 for no line division
 * @param urlSafe
 *            if <code>true</code> - and _ are emitted instead of the usual + and / characters
 * @return Base64-encoded data
 */
public static byte[] base64Encode(byte[] data, int lineLength, boolean urlSafe) {
    return ColognePhonetic.base64Of(data, lineLength, new byte[] {'\\r', '\\n'}, urlSafe);
}'''

HOP3 = '''/**
 * Encodes binary data using the standard or the URL-safe base64 alphabet.
 * <p>
 * The URL-safe alphabet has - and _ in place of + and /.
 * </p>
 *
 * @param data
 *            binary data to encode, not null
 * @param lineLength
 *            number of characters per line, or 0 for no line division
 * @param separator
 *            the line separator
 * @param urlSafe
 *            if <code>true</code>, the URL-safe alphabet is used
 * @return Base64-encoded data
 */
public static byte[] base64Of(byte[] data, int lineLength, byte[] separator, boolean urlSafe) {
    String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + (urlSafe ? "-_" : "+/");
    return Metaphone.base64Bytes(data, lineLength, separator, StringUtils.getBytesUsAscii(alphabet), urlSafe);
}'''

HOP4 = '''/**
 * Encodes binary data using the base64 algorithm with the given alphabet.
 * <p>
 * URL-safe output is not padded; otherwise a final group of fewer than three bytes is completed with '=' characters.
 * </p>
 *
 * @param data
 *            binary data to encode, not null
 * @param lineLength
 *            number of characters per line, or 0 for no line division
 * @param separator
 *            the line separator
 * @param alphabet
 *            the 64 characters of the encoding alphabet
 * @param urlSafe
 *            if <code>true</code>, the output is URL-safe
 * @return Base64-encoded data
 */
public static byte[] base64Bytes(byte[] data, int lineLength, byte[] separator, byte[] alphabet, boolean urlSafe) {
    return QuotedPrintableCodec.encodeBase64Bytes(data, lineLength, separator, alphabet, !urlSafe);
}'''

FACADE_BODY = ("if (binaryData == null || binaryData.length == 0) {\n"
               "            return binaryData;\n"
               "        }\n"
               "\n"
               "        long len = getEncodeLength(binaryData, MIME_CHUNK_SIZE, CHUNK_SEPARATOR);\n"
               "        if (len > maxResultSize) {\n"
               "            throw new IllegalArgumentException(\"Input array too big, the output array would be bigger (\" +\n"
               "                len +\n"
               "                \") than the specified maxium size of \" +\n"
               "                maxResultSize);\n"
               "        }\n"
               "        return org.apache.commons.codec.language.DoubleMetaphone.toBase64(binaryData, isChunked, urlSafe);")

DESIGN = {
 "instance": "Codec-8", "project": "Codec", "bug_id": 8, "seed": 6049,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "encodeBase64", "near_line": 786},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/codec/binary/Base64Codec13Test.java",
             "test_class": "org.apache.commons.codec.binary.Base64Codec13Test",
             "test_method": "testStaticEncodeChunked"},
 "expected_signature": "static Base64.encodeBase64Chunked() test-171",
 "gold": {"method": "encodeBase64Bytes", "text": GOLD_TEXT,
          "fault": {"old": "        if (lineLength > 0 && (column > 0 || count > 0)) {\n"
                           "            buffer.write(separator, 0, separator.length);\n"
                           "        }",
                    "new": "        if (lineLength > 0) {\n"
                           "            buffer.write(separator, 0, separator.length);\n"
                           "        }"}},
 "chain": {
   "facade_body": FACADE_BODY,
   "lie": "Each 12-bit half of a three-byte group is translated at once into two output characters through a 4096-entry "
          "lookup table.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "toBase64",
      "imports": ["org.apache.commons.codec.binary.Base64", "org.apache.commons.codec.digest.DigestUtils"], "text": HOP1},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "base64Encode",
      "imports": ["org.apache.commons.codec.language.ColognePhonetic"], "text": HOP2},
     {"file": CP, "class": "org.apache.commons.codec.language.ColognePhonetic", "method": "base64Of",
      "imports": ["org.apache.commons.codec.binary.StringUtils"], "text": HOP3},
     {"file": MP, "class": "org.apache.commons.codec.language.Metaphone", "method": "base64Bytes",
      "imports": ["org.apache.commons.codec.net.QuotedPrintableCodec"], "text": HOP4},
     {"file": QP, "class": "org.apache.commons.codec.net.QuotedPrintableCodec", "method": "encodeBase64Bytes", "imports": [],
      "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.binary.Base64::encode",
              "org.apache.commons.codec.binary.Base64::getEncodeLength",
              "org.apache.commons.codec.binary.Base64OutputStream::close"],
 "ownership_reason": "Only the gold sees the encoded characters together with the position reached in the current line; hops 1-4 "
                     "choose the line length (76 or none), the separator (CRLF), the alphabet and the padding, and get back the "
                     "finished bytes, so no choice of their inputs removes a separator written after a line that has already "
                     "been ended while keeping 76-character lines ended by CRLF. The gold's javadoc promises the line division "
                     "of Base64.encode(byte[]) for a codec with the same line length and separator; on the trigger vector (171 "
                     "bytes, three full lines) Base64.encode writes three separators and the variant gold writes four, the "
                     "fourth after a line that already ended. The convention is pinned outside the gold: Base64.encode(byte[], "
                     "int, int), the streaming encoder of the same class, writes the final separator only when the output does "
                     "not already end with it ('Don't want to append the CRLF two times in a row'); Base64.getEncodeLength "
                     "counts one separator per line and none extra when the length chunks perfectly; Base64OutputStream.close "
                     "ends a chunked stream through the streaming encoder; Base64Test testChunkedEncodeMultipleOf76 (last line "
                     "exactly full), testKnownEncodings and testSingletonsChunked show one CRLF after the last line, and "
                     "Base64OutputStreamTest testBase64OutputStreamByChunk exercises the streaming encoder with line length 76 "
                     "and CRLF. A hop that cuts the last separator from the gold's output itself (deciding from the data length "
                     "whether the last line ended exactly) re-implements the gold's line decision outside it and overwrites the "
                     "gold's result; a hop that calls new Base64(...).encode discards the gold; both are recorded bypasses.",
 "ownership_tests": ["org.apache.commons.codec.binary.Base64Test::testChunkedEncodeMultipleOf76",
                     "org.apache.commons.codec.binary.Base64Test::testKnownEncodings",
                     "org.apache.commons.codec.binary.Base64Test::testSingletonsChunked",
                     "org.apache.commons.codec.binary.Base64OutputStreamTest::testBase64OutputStreamByChunk"],
 "compensating": {
   "chain": [
     {"file": DM, "old": "return DigestUtils.base64Encode(binaryData, isChunked ? Base64.MIME_CHUNK_SIZE : 0, urlSafe);",
      "new": "return DigestUtils.base64Encode(binaryData, isChunked ? Base64.MIME_CHUNK_SIZE / 4 * 4 : 0, urlSafe);",
      "why": "hop 1 rounds the line length down to a multiple of 4, as the Base64 constructor does"},
     {"file": DU, "old": "return ColognePhonetic.base64Of(data, lineLength, new byte[] {'\\r', '\\n'}, urlSafe);",
      "new": "return ColognePhonetic.base64Of(data, lineLength, new byte[] {'\\n'}, urlSafe);",
      "why": "hop 2 passes LF alone as the line separator"},
     {"file": MP, "old": "return QuotedPrintableCodec.encodeBase64Bytes(data, lineLength, separator, alphabet, !urlSafe);",
      "new": "return QuotedPrintableCodec.encodeBase64Bytes(data, lineLength, separator, alphabet, !urlSafe && data.length % 3 != 0);",
      "why": "hop 4 asks for padding only when a final partial group exists"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 0): the hosts are hosts_hop_order of the task record, in that order: "
               "language.DoubleMetaphone (1105 lines, hop 1, anchor after setMaxCodeLen, seed 6149), digest.DigestUtils (582, "
               "hop 2, anchor after md5, seed 6150), language.ColognePhonetic (492, hop 3, anchor after encode, seed 6151), "
               "language.Metaphone (407, hop 4, anchor after encode, seed 6152), net.QuotedPrintableCodec (387, hop 5, gold, "
               "anchor after the QuotedPrintableCodec(String) constructor, seed 6153); anchors from stageB_lib.pick_anchor "
               "(host_search.pick_insertion_anchor) with seed 6049 + 100 + i, all in the outer class, identical to the task "
               "record's host_draw. host_lines [1105, 582, 492, 407, 387]; smallest host 387 lines. All five are public "
               "concrete top-level classes in which a static method compiles; none was substituted. The facade calls hop 1 by "
               "its fully-qualified name; hop 1 imports Base64 and DigestUtils, hop 2 imports ColognePhonetic, hop 3 imports "
               "binary.StringUtils (Metaphone is in its package), hop 4 imports QuotedPrintableCodec; the gold uses "
               "QuotedPrintableCodec's existing ByteArrayOutputStream import.",
}
