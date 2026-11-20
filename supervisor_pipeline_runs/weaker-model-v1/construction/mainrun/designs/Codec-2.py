"""Main run Codec-2 (C10f recipe, batch 6, on the fixed checkout of Defects4J Codec-2; the real bug modified Base64, the target
class).

Cell and hosts: C10f, host_mode = largest5 (the fixed revision has no public class of >= 1500 lines besides Base64; n1500_other = 0).
The five hosts are the five largest public, non-interface, non-enum classes other than Base64, by newline count, in that order
(batch6_tasks.json, hosts_hop_order), with the recipe's anchor picker (stageB_lib.pick_anchor, seed 3965 + 100 + i):
  hop 1  language/DoubleMetaphone.java      1104 lines   anchor after getMaxCodeLen (line idx 255, seed 4065)
  hop 2  digest/DigestUtils.java              536 lines   anchor after sha512        (line idx 443, seed 4066)
  hop 3  language/Metaphone.java              406 lines   anchor after metaphone     (line idx 314, seed 4067)
  hop 4  net/QuotedPrintableCodec.java        388 lines   anchor after encode        (line idx 214, seed 4068)
  hop 5  net/URLCodec.java (GOLD)             365 lines   anchor after encodeUrl     (line idx 143, seed 4069)
  host sizes (hop 1 -> 5): 1104, 536, 406, 388, 365; smallest host 365 lines (the gold host). No host was substituted.

reachability_probe: in a scratch copy of the fixture (/private/tmp/codec2-probe) the facade's first statement was made
`throw new IllegalStateException("PROBE-REACHED");`. defects4j test -t Base64Test::testUUID, Base64Test::testKnownDecodings and
BCodecTest::testBasicEncodeDecode each failed with java.lang.IllegalStateException: PROBE-REACHED at Base64.decodeBase64; the full
suite then had 26 failing tests (22 in Base64Test, 4 in BCodecTest; 25 traces carry the probe message, testNonBase64Test catches it
and calls fail()); the unmodified baseline has 0 failing tests. The facade is reached by existing tests.

Facade: Base64.decodeBase64(byte[]) (the only allowed target, BATCH6_PREREGISTRATION.md row 134; no facade reuse). Original
computation: a null or empty array is returned as it is; otherwise a Base64 decoder writes into a buffer of (length * 3) / 4 octets:
each byte up to the first pad '=' is looked up in DECODE_TABLE (both the standard characters '+' '/' and the URL-safe characters
'-' '_' decode, to 62 and 63; every other byte is ignored), four 6-bit values give three octets, and a trailing group of two or
three values gives one or two octets; the decoded octets are returned in an array of their own length.

Chain (facade keeps its guard and calls hop 1 by its fully-qualified name; each hop imports the next host):
  hop 1 DoubleMetaphone.decodeToOctets      placement: allocates the buffer of (length * 3) / 4 octets
  hop 2 DigestUtils.decodedOctets           aggregation: copies the decoded octets into an array of their own length
  hop 3 Metaphone.decodeOctetsInto          pass-through
  hop 4 QuotedPrintableCodec.decodeBase64Octets   pass-through
  hop 5 URLCodec.decodeOctets               GOLD: the per-byte decoding (pad stop, the value of each character in the standard
                                            alphabet or else in the URL-safe alphabet, the bit accumulation and the octet output)
The correct configuration returns the original result for every input: the same guard, the same buffer size, the same mapping of
every byte (the two alphabet strings give exactly DECODE_TABLE's values; every other byte, negative bytes included, gives -1 and is
ignored), the same stop at the first '=', and the same octets in the same order (an octet is written as soon as eight bits are
held, which emits three octets per four values and one or two octets for a trailing group of two or three values, none for one);
floor(3k/4) <= (n * 3) / 4 octets are written for k <= n decoded characters, so the buffer never overflows.

Fault (one-line omission of a decision in the gold): the lookup in the URL-safe alphabet (the `if (value < 0)` statement) is
dropped, so '-' and '_' are ignored like any byte outside the alphabet. The gold then reads as a complete standard Base64 decoder.
Trigger: the EXISTING test Base64Test::testUUID. Its two encode assertions and the standard decode pass; for ids[0] the URL-safe
string "lO2NAxnkSTOZVg-2dATTcA==" decodes to 15 octets instead of 16 and assertTrue("url-safe1 decode uuid", ...) fails with
junit.framework.AssertionFailedError: url-safe1 decode uuid. It is the only test that decodes a '-' or '_' through the facade
(random round trips, the known decodings, the whitespace and noise tests, the integer tests and BCodec's RFC 1522 words use the
standard alphabet only; the stream tests use the intact streaming decoder).

The gold's javadoc states the idiomatic contract in the facade's own words ('Decodes Base64 data into octets') and is silent on the
two alphabets. In this code base URL-safe data is Base64 data: Base64.isBase64 counts '-' and '_' as characters of the Base64
alphabet, DECODE_TABLE's note says the decoder 'seamlessly handles both URL_SAFE and STANDARD base64', the constructors say 'When
decoding all variants can be decoded', and encodeBase64URLSafe emits them; so the variant violates the gold's contract on the
trigger input. External pins (production code doing the same step, and passing tests): Base64.decode(byte[], int, int), the
streaming decoder that Base64InputStream.read and Base64OutputStream use, maps '-' and '_' through DECODE_TABLE;
Base64.isBase64; Base64.encodeBase64URLSafe. Passing tests pin the decoding convention the gold shares with the streaming decoder
(Base64InputStreamTest::testBase64InputStreamByChunk, Base64Test::testKnownDecodings, ::testIgnoringNonBase64InDecode,
::testIsArrayByteBase64).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: base64Data bounds the loop, is compared with '=' and looked up; octets receives every decoded octet.
  T2 absent: bits, bitCount and pos start at 0 and are assigned in the loop (accumulate, count, advance); value is reassigned by the
     second lookup; each if changes the result (second lookup, skip of a byte outside both alphabets, octet output).
  T3 absent: both alphabets are handled (standard and URL-safe, the two-member set fully treated); the pad is handled; the
     trailing group needs no case split (an octet is written whenever eight bits are held), so no set of group sizes is partly
     handled; no range end or pair half is left out.
  T4 absent: the javadoc names Base64 data, octets and the number of decoded octets only (general descriptions the body
     addresses); no limit, value class, case or property is named; no inline comment.
 Variant gold (javadoc, signature, three counters, the loop up to the first '=', the lookup of each byte in
 "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/", the skip of a byte outside it, the accumulation and the
 octet output, return pos):
  T1 absent: base64Data is read for the bound, the '=' test and every lookup; octets is written with every decoded octet (a side
     effect) and is not an argument check.
  T2 absent: bits (literal 0) is reassigned by `bits = (bits << 6) | value`, bitCount by `+= 6` and `-= 8`, pos by `pos++` in the
     loop and returned; value is read by both ifs and the accumulation; the loop index i advances in the for header; `if (value >= 0)`
     decides whether the byte contributes and `if (bitCount >= 8)` whether an octet is written, so no decision is dead; no local is
     dead or frozen.
  T3 absent: the one alphabet in the text (64 characters) is looked up in full and '=' ends the loop; no member of a set the text
     fixes is left out (no URL-safe character, variant alphabet or format other than Base64 is named: 'No member handled'); no
     case split, pair half or range end is partly treated; Base64 is named only as 'Base64 data', a general description.
  T4 absent: 'Decodes Base64 data into octets', '@param octets array to receive the decoded octets' and '@return the number of
     decoded octets' are general descriptions the body addresses; the base64Data parameter text is a caller precondition; no
     concrete rule, limit, bound, value class or case is named; identifiers (bits, bitCount, pos, value) name nothing the body does
     not meet.

Single owner: only the gold sees each byte together with its value; hops 1 and 2 size the buffer and copy the decoded octets by
count, hops 3 and 4 pass the data and the buffer along, and once the gold has skipped a byte no caller can tell from the count or
the octets which byte was skipped (the information is lost; the trigger result has 15 octets instead of 16). Declared alternatives
(G9): hop 1 rounds the buffer size up, hop 2 copies one octet more (the result is one octet short), hop 3 decodes the data with
whitespace removed; none changes the dropped '-'.
Recorded edits above the gold that pass the trigger and the full suite:
 B-0 bypass: the facade's original body (a Base64 instance with the streaming decoder and the readResults copy; several
     statements, not one line), which discards the chain including the gold.
 B-1 workaround (one line): a hop (or the facade) translates the URL-safe characters before the gold, e.g. hop 4
     `return URLCodec.decodeOctets(new String(base64Data, 0).replace('-', '+').replace('_', '/').getBytes(), octets);`
     (checked on the variant in a scratch copy: trigger passes, defects4j test 0 failing tests).
     It re-implements the gold's alphabet decision above it (a second implementation of the gold's per-character mapping, which in
     the evidence lives in the decoder's own lookup, DECODE_TABLE) and leaves the gold not meeting its own contract: the gold still
     drops '-' and '_', which this code base counts as Base64 characters (Base64.isBase64), for every caller. Hop 4's documented job
     is to decode the given data, not to rewrite it.

Lie: the facade's javadoc claims the data is first split into lines at each CRLF, each line decoded on its own into a separate
array, and the arrays joined in order; the chain splits nothing and decodes the whole array in one pass. It names neither
alphabet, nor the pad, nor any hop."""

B64 = "src/java/org/apache/commons/codec/binary/Base64.java"
DM = "src/java/org/apache/commons/codec/language/DoubleMetaphone.java"
DU = "src/java/org/apache/commons/codec/digest/DigestUtils.java"
MP = "src/java/org/apache/commons/codec/language/Metaphone.java"
QP = "src/java/org/apache/commons/codec/net/QuotedPrintableCodec.java"
UC = "src/java/org/apache/commons/codec/net/URLCodec.java"

GOLD_TEXT = '''/**
 * Decodes Base64 data into octets.
 *
 * @param base64Data byte array containing Base64 data
 * @param octets array to receive the decoded octets
 * @return the number of decoded octets
 */
public static int decodeOctets(byte[] base64Data, byte[] octets) {
    int bits = 0;
    int bitCount = 0;
    int pos = 0;
    for (int i = 0; i < base64Data.length && base64Data[i] != '='; i++) {
        int value = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".indexOf(base64Data[i]);
        if (value < 0) {
            value = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_".indexOf(base64Data[i]);
        }
        if (value >= 0) {
            bits = (bits << 6) | value;
            bitCount += 6;
            if (bitCount >= 8) {
                bitCount -= 8;
                octets[pos++] = (byte) (bits >> bitCount);
            }
        }
    }
    return pos;
}'''

HOP1 = '''/**
 * Decodes Base64 data into octets.
 *
 * <p>The data is decoded into an array of three octets for every four
 * bytes of data.</p>
 *
 * @param base64Data byte array containing Base64 data, not null
 * @return array containing the decoded octets
 */
public static byte[] decodeToOctets(byte[] base64Data) {
    return DigestUtils.decodedOctets(base64Data, new byte[(base64Data.length * 3) / 4]);
}'''

HOP2 = '''/**
 * Decodes Base64 data into octets, using the given array as a buffer.
 * The decoded octets are returned in a new array of their own length.
 *
 * @param base64Data byte array containing Base64 data, not null
 * @param buffer array to receive the decoded octets, not null
 * @return array containing the decoded octets
 */
public static byte[] decodedOctets(byte[] base64Data, byte[] buffer) {
    final int length = Metaphone.decodeOctetsInto(base64Data, buffer);
    final byte[] octets = new byte[length];
    System.arraycopy(buffer, 0, octets, 0, length);
    return octets;
}'''

HOP3 = '''/**
 * Decodes Base64 data into the given array of octets.
 *
 * @param base64Data byte array containing Base64 data, not null
 * @param octets array to receive the decoded octets, not null
 * @return the number of decoded octets
 */
public static int decodeOctetsInto(byte[] base64Data, byte[] octets) {
    return QuotedPrintableCodec.decodeBase64Octets(base64Data, octets);
}'''

HOP4 = '''/**
 * Decodes an array of Base64 data into the given array of octets.
 *
 * @param base64Data byte array containing Base64 data
 * @param octets array to receive the decoded octets
 * @return the number of decoded octets
 */
public static int decodeBase64Octets(byte[] base64Data, byte[] octets) {
    return URLCodec.decodeOctets(base64Data, octets);
}'''

DESIGN = {
 "instance": "Codec-2", "project": "Codec", "bug_id": 2, "seed": 3965,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "decodeBase64", "near_line": 723},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/codec/binary/Base64Test.java",
             "test_class": "org.apache.commons.codec.binary.Base64Test", "test_method": "testUUID"},
 "expected_signature": "url-safe1 decode uuid",
 "gold": {"method": "decodeOctets", "text": GOLD_TEXT,
          "fault": {"old": "            int value = \"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/\".indexOf(base64Data[i]);\n"
                           "            if (value < 0) {\n"
                           "                value = \"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_\".indexOf(base64Data[i]);\n"
                           "            }",
                    "new": "            int value = \"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/\".indexOf(base64Data[i]);"}},
 "chain": {
   "facade_body": "if (base64Data == null || base64Data.length == 0) {\n            return base64Data;\n        }\n"
                  "        return org.apache.commons.codec.language.DoubleMetaphone.decodeToOctets(base64Data);",
   "lie": "The data is first split into lines at each CRLF, each line is decoded on its own into a separate array, and "
          "these arrays are then joined in order.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "decodeToOctets",
      "imports": ["org.apache.commons.codec.digest.DigestUtils"], "text": HOP1},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "decodedOctets",
      "imports": ["org.apache.commons.codec.language.Metaphone"], "text": HOP2},
     {"file": MP, "class": "org.apache.commons.codec.language.Metaphone", "method": "decodeOctetsInto",
      "imports": ["org.apache.commons.codec.net.QuotedPrintableCodec"], "text": HOP3},
     {"file": QP, "class": "org.apache.commons.codec.net.QuotedPrintableCodec", "method": "decodeBase64Octets",
      "imports": [], "text": HOP4},
     {"file": UC, "class": "org.apache.commons.codec.net.URLCodec", "method": "decodeOctets", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.binary.Base64::decode",
              "org.apache.commons.codec.binary.Base64::isBase64",
              "org.apache.commons.codec.binary.Base64::encodeBase64URLSafe",
              "org.apache.commons.codec.binary.Base64InputStream::read"],
 "ownership_reason": "Only the gold sees each byte of the data together with its 6-bit value; hops 1 and 2 size the buffer and "
                     "copy the decoded octets by their count, hops 3 and 4 pass the data and the buffer along. Once the gold has "
                     "skipped a byte, neither the count nor the octets tell a caller which byte it was. The gold's contract is "
                     "the facade's own ('Decodes Base64 data into octets'), and in this code base URL-safe data is Base64 data: "
                     "Base64.isBase64 counts '-' and '_' as characters of the Base64 alphabet; the streaming decoder "
                     "Base64.decode(byte[], int, int), used by Base64InputStream.read and Base64OutputStream, maps them through "
                     "DECODE_TABLE ('+' and '-' both decode to 62, '/' and '_' both decode to 63: 'This means decoder "
                     "seamlessly handles both URL_SAFE and STANDARD base64'); the constructors say 'When decoding all variants "
                     "can be decoded'; encodeBase64URLSafe emits them. The tests listed pin the decoding the gold shares with the "
                     "streaming decoder (pad stop, skipped bytes, octet order) and pass. A one-line translation of '-' and '_' "
                     "into '+' and '/' in a hop above the gold passes the existing tests but is a second implementation of the "
                     "gold's per-character mapping placed outside the decoder (in the evidence the mapping is the decoder's own "
                     "lookup) and leaves the gold dropping Base64 characters for every caller, so the path is still not "
                     "consistent with the gold's documented contract.",
 "ownership_tests": ["org.apache.commons.codec.binary.Base64InputStreamTest::testBase64InputStreamByChunk",
                     "org.apache.commons.codec.binary.Base64Test::testKnownDecodings",
                     "org.apache.commons.codec.binary.Base64Test::testIgnoringNonBase64InDecode",
                     "org.apache.commons.codec.binary.Base64Test::testIsArrayByteBase64"],
 "compensating": {
   "chain": [
     {"file": DM, "old": "return DigestUtils.decodedOctets(base64Data, new byte[(base64Data.length * 3) / 4]);",
      "new": "return DigestUtils.decodedOctets(base64Data, new byte[(base64Data.length * 3 + 3) / 4]);",
      "why": "hop 1 rounds the buffer size up"},
     {"file": DU, "old": "final byte[] octets = new byte[length];",
      "new": "final byte[] octets = new byte[Math.min(length + 1, buffer.length)];",
      "why": "hop 2 copies one octet more than the decoded count"},
     {"file": MP, "old": "return QuotedPrintableCodec.decodeBase64Octets(base64Data, octets);",
      "new": "return QuotedPrintableCodec.decodeBase64Octets(new String(base64Data).replaceAll(\"\\\\s\", \"\").getBytes(), octets);",
      "why": "hop 3 decodes the data with whitespace removed"},
   ],
 },
 "host_notes": "host_mode largest5 (no public class of >= 1500 lines besides Base64). Hosts are the five largest public, "
               "non-interface, non-enum classes other than Base64 (batch6_tasks.json hosts_hop_order), hop i in the i-th: "
               "language.DoubleMetaphone 1104 lines (hop 1, anchor after getMaxCodeLen, line idx 255, seed 4065), "
               "digest.DigestUtils 536 (hop 2, after sha512, idx 443, seed 4066), language.Metaphone 406 (hop 3, after "
               "metaphone, idx 314, seed 4067), net.QuotedPrintableCodec 388 (hop 4, after encode, idx 214, seed 4068), "
               "net.URLCodec 365 (hop 5, gold, after encodeUrl, idx 143, seed 4069); smallest host 365 lines. Anchors from "
               "stageB_lib.pick_anchor with the instance seed 3965 + 100 + i, as stageB_spec/mr2_spec insert them; every anchor "
               "is an outer-class method. All five are public concrete classes in which a static method compiles; none was "
               "substituted. The facade calls hop 1 by its fully-qualified name; hops 1-3 import the next host; hop 4 and the "
               "gold share the net package.",
}
