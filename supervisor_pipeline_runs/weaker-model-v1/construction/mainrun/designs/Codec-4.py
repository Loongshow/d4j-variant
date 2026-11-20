"""Main run Codec-4 (cell C10f, batch 6; C10 recipe with fallback hosts on the fixed checkout of Defects4J Codec-4; the real bug
modified Base64, the target class).

Facade: Base64.encodeInteger(BigInteger) (the only allowed target, BATCH6_PREREGISTRATION.md row 135; no facade reuse).
Original computation of the facade: a null BigInteger throws NullPointerException; otherwise toIntegerBytes (the
two's-complement bytes of the value without the sign byte: toByteArray() minus its leading byte when the bit length is a
multiple of 8, i.e. the last (bitLength + 7) / 8 bytes of toByteArray()), then encodeBase64(bytes, false): an empty array is
returned as it is, anything else is encoded with the standard alphabet, unchunked, with '=' padding.

reachability_probe: in a scratch copy of the fixture (/private/tmp/codec4-v2-probe) the facade's first statement was made
`if (true) throw new IllegalStateException("PROBE-REACHED");` (a bare throw would make the remaining body unreachable and not
compile); defects4j compile OK; defects4j test -t Base64Test::testCodeInteger1 / 2 / 3 / 4: each 1 failing test with
java.lang.IllegalStateException: PROBE-REACHED; full suite with the probe: 5 failing tests, testCodeInteger1-4 with
PROBE-REACHED and testCodeIntegerNull with its own 'Incorrect Exception caught' message (it reaches the facade with null).
The facade is reachable; testCodeInteger3 is the trigger chosen below.

host_mode: largest5 (n1500_other = 0). Hosts = hosts_hop_order of the task record, the five largest public non-interface,
non-enum classes other than Base64, by newline count, none substituted:
  hop 1 language.DoubleMetaphone      1105 lines   anchor after `encode` (line idx 206, seed 8377)
  hop 2 digest.DigestUtils             582 lines   anchor after `sha` (line idx 252, seed 8378)
  hop 3 language.Metaphone             407 lines   anchor after `encode` (line idx 371, seed 8379)
  hop 4 net.QuotedPrintableCodec       387 lines   anchor after `encode` (line idx 213, seed 8380)
  hop 5 net.URLCodec (GOLD)            361 lines   anchor after `encode` (line idx 249, seed 8381)
  smallest host: URLCodec, 361 lines (the gold host). Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor)
  with the instance seed 8277 + 100 + i, as mr2_spec.insert_hop uses them; all lie in the outer class (brace depth 1).

Chain (the original computation redistributed):
  hop 1 DoubleMetaphone.encodeMagnitude   placement: the two's-complement bytes without the sign byte (the last
                                          (bitLength + 7) / 8 bytes of toByteArray(); equal to Base64.toIntegerBytes for every
                                          BigInteger, negative ones and zero included)
  hop 2 DigestUtils.base64                decision: an empty array is returned as it is
  hop 3 Metaphone.encodeStandard          plumbing: supplies the standard alphabet (A-Z, a-z, 0-9, '+', '/') as a String
  hop 4 QuotedPrintableCodec.encodePrintable  plumbing: takes the alphabet as US-ASCII bytes (StringUtils.getBytesUsAscii)
  hop 5 URLCodec.encodeGroups             GOLD: the per-group core: every group of three bytes (the final one completed
                                          with zero bytes) gives four characters of the alphabet; `end`, the number of
                                          characters that carry bits of the input, is the character count of the input
                                          bits rounded to the nearest, (4n + 1) / 3, raised by one where it would leave a
                                          single character in the last group (end % 4 == 1: one byte, eight bits, needs two
                                          characters); the characters from `end` on become '='
The correct configuration returns the original result for every input. Checked: the gold's body in a stand-alone harness
(/private/tmp/codec4-v2-proto) against java.util.Base64 for 20,000 random arrays of 0 to 199 bytes: 0 differences; and
Base64.encodeInteger through the whole chain in a scratch copy of the correct configuration (/private/tmp/codec4-v2-correct)
against the untouched Base64.encodeBase64(Base64.toIntegerBytes(v), false) for 12,008 values (6,000 random values of 0 to 300
bits, their negations, and 0, 1, -1, 255, 256, -128, -129, -256; 4,078 / 4,027 / 3,903 of them with n % 3 = 0 / 1 / 2
magnitude bytes): 0 differences.

Fault (omission of a decision in the gold, one guarded statement): the `if (end % 4 == 1) { end++; }` that raises the rounded
count is dropped, so for a final group of one byte `end` stays at 4m + 1 and the second character of that group (the one
holding the byte's last two bits) is overwritten with '='. Final groups of two bytes (end = 4m + 3) and complete groups
(end = 4m) are unchanged. Trigger: the EXISTING test Base64Test::testCodeInteger3. Its BigInteger has 509 bits, i.e. 64
magnitude bytes, 64 % 3 = 1: the only one of the four testCodeInteger values whose final group has one byte
(testCodeInteger1 and 2: 160 bits, 20 bytes; testCodeInteger4: 1023 bits, 128 bytes; all with a final group of two bytes). Its
first assertion fails: expected ...K0Yjg== but was ...K0Yj===. Variant full suite: exactly this test fails (gate G5);
testCodeInteger1, 2, 4 and testCodeIntegerNull pass; no other test reaches the chain (probe above).

The gold's javadoc states the idiomatic contract (encodes the bytes using the base64 algorithm and the given alphabet; the
wording of Base64.encodeBase64's own javadoc, 'using the base64 algorithm') and is silent on how many characters a final group
keeps. The base64 encoding of a final single byte is two characters and "==", so the variant violates that contract on the
trigger input. The convention is pinned outside the gold: Base64.encode(byte[], int, int) (the streaming encoder; its `case 1`
writes two characters and then PAD twice, its `case 2` three characters and PAD once) and Base64.encodeBase64 (static, through
that encoder), used in production by BCodec.doEncoding; passing tests Base64Test::testSingletons ("AA==", "AQ==", ...),
::testKnownEncodings ("...Lg==", "...cw=="), ::testPairs ("AAA="); and the chain itself is pinned on two-byte final groups by
testCodeInteger1 and testCodeInteger4.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: alphabet supplies every character; bytes gives the buffer size, both loop bounds, the presence test, every
     group's bits and `end`.
  T2 absent: buffer (returned), pos (advanced by every write), i, k and j (for headers), group (assigned in the inner loop,
     read by the four writes), end (assigned from bytes.length, raised by end++, start of the '=' loop); `if (k <
     bytes.length)` decides whether a byte enters the group, `if (end % 4 == 1)` moves the start of the '=' run for one left-over
     byte; no literal-initialised local is left unassigned; no else, ternary or case.
  T3 absent: every group writes all four characters; every byte position of a group gets the same presence test; the '='
     treatment is one run from `end` to the end of the buffer, both ends given; the correction treats one value of end % 4, one
     member of a set of four that the gold does not name, the other three needing none; no pair halves, no named class.
  T4 absent: 'using the base64 algorithm and the given alphabet' and '@return array of bytes containing the base64
     characters' are general descriptions the body addresses; '@param alphabet the 64 characters of the alphabet, in order'
     and '@param bytes array of bytes to encode' are caller-side; no inline comment; identifiers (buffer, pos, group, end) name
     nothing the body does not meet.
  Rewritten before the omission was chosen: the usual forms split the final group by its byte count (a `switch` or `if` on
  bytes.length % 3 with a case for one byte and a case for two, or a '=' write per position); an omission in any of them
  leaves a handled sibling case or a handled sibling position. So every group goes through the same four writes after a
  uniform zero-completing read, and the '=' characters are one run from a single computed start; the remainder of the length
  by three is never tested.
 Variant gold (javadoc, signature, body ending `int end = (bytes.length * 4 + 1) / 3; for (int j = end; j < buffer.length;
 j++) { buffer[j] = (byte) '='; } return buffer;`):
  T1 absent: alphabet is read for every written character; bytes for the buffer size, both loop bounds, the presence test,
     every group's bits and `end`; both change the result.
  T2 absent: buffer is returned; pos is advanced by pos++ in each of the four writes; i, k and j advance in their for headers;
     group is assigned in the inner loop (`group << 8`, `group | ...`) and read by the four writes; end is a bound computed
     before the '=' loop from bytes.length and read as its start (not frozen: computed, not a literal, not a loop cursor);
     `if (k < bytes.length)` decides whether a byte enters the group (live for the final group); no else, ternary or case.
  T3 absent: all four characters are written for every group and all three byte positions get the same presence test (no
     member of either set left out); the '=' treatment is a single run from end to buffer.length (both ends of the range
     given); no case, remainder, flag or value class is tested, so no sibling is handled while another is not ('No member
     handled' for any per-case set); the gold names no class it handles in part; no pair halves or range ends are compared or
     clamped.
  T4 absent: 'Encodes an array of bytes into an array of characters using the base64 algorithm and the given alphabet' and
     '@return array of bytes containing the base64 characters' are general descriptions the loops address; '@param alphabet
     the 64 characters of the alphabet, in order' and '@param bytes array of bytes to encode' are caller-side; no inline
     comment; identifiers (buffer, pos, group, end) name nothing the body does not meet.

Single owner: only the gold sees the final group together with the number of bytes it holds and the positions of its
characters; hops 1-4 pass whole arrays (the magnitude bytes, the alphabet) and get back the whole encoded array. No input a
caller can pass makes the variant keep two characters for a final single byte (zero-extending the bytes, padding them on the
left, other alphabets: each changes the characters themselves; one extra zero byte gives ...YjgA=). Declared alternatives
(G9): hop 1 takes the bytes of the absolute value; hop 2 extends data that leaves one byte over with a zero byte; hop 4
appends '=' to the alphabet. None changes the trigger's ...Yj=== ending into ...Yjg==.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in scratch copies,
defects4j test: 0 failing tests each):
 B-0 bypass: the facade (its original body `return encodeBase64(toIntegerBytes(bigInt), false);`) or any of hops 1-4 returns
     org.apache.commons.codec.binary.Base64.encodeBase64(<its bytes>), the intact static encoder, discarding the rest of the
     chain including the gold. Checked at hop 1 (`return org.apache.commons.codec.binary.Base64.encodeBase64(magnitude);`).
 B-1 bypass (post-correction): a hop that holds the input rewrites part of the gold's output, checked at hop 4:
     `byte[] table = StringUtils.getBytesUsAscii(alphabet); byte[] encoded = URLCodec.encodeGroups(table, bytes); if (bytes.length % 3 == 1) { encoded[encoded.length - 3] = table[(bytes[bytes.length - 1] & 3) << 4]; } return encoded;`
     a second implementation of the gold's own final-group character written over the gold's result; the gold's result still
     violates its own contract (it is not the base64 encoding when one byte is left over), so the path is not used as
     documented.

Lie: the facade's javadoc claims the characters are produced by repeated division of the value by 64, least significant first,
each remainder selecting one character; the chain divides nothing and encodes the magnitude bytes three at a time from the most
significant end. It names neither padding nor the final group nor any hop."""

B64 = "src/java/org/apache/commons/codec/binary/Base64.java"
DMP = "src/java/org/apache/commons/codec/language/DoubleMetaphone.java"
DGU = "src/java/org/apache/commons/codec/digest/DigestUtils.java"
MPH = "src/java/org/apache/commons/codec/language/Metaphone.java"
QPC = "src/java/org/apache/commons/codec/net/QuotedPrintableCodec.java"
URL = "src/java/org/apache/commons/codec/net/URLCodec.java"

GOLD_TEXT = '''/**
 * Encodes an array of bytes into an array of characters using the base64 algorithm and the given alphabet.
 *
 * @param alphabet
 *            the 64 characters of the alphabet, in order
 * @param bytes
 *            array of bytes to encode
 * @return array of bytes containing the base64 characters
 */
public static final byte[] encodeGroups(byte[] alphabet, byte[] bytes) {
    byte[] buffer = new byte[(bytes.length + 2) / 3 * 4];
    int pos = 0;
    for (int i = 0; i < bytes.length; i += 3) {
        int group = 0;
        for (int k = i; k < i + 3; k++) {
            group = group << 8;
            if (k < bytes.length) {
                group = group | (bytes[k] & 0xff);
            }
        }
        buffer[pos++] = alphabet[(group >> 18) & 0x3f];
        buffer[pos++] = alphabet[(group >> 12) & 0x3f];
        buffer[pos++] = alphabet[(group >> 6) & 0x3f];
        buffer[pos++] = alphabet[group & 0x3f];
    }
    int end = (bytes.length * 4 + 1) / 3;
    if (end % 4 == 1) {
        end++;
    }
    for (int j = end; j < buffer.length; j++) {
        buffer[j] = (byte) '=';
    }
    return buffer;
}'''

HOP1 = '''/**
 * Encode the magnitude of a BigInteger using the base64 algorithm.
 * The magnitude is the two's-complement representation of the value
 * without its sign byte, in as many bytes as the bit length needs.
 *
 * @param value BigInteger to encode, not null
 * @return a byte array containing base64 characters
 */
public static byte[] encodeMagnitude(BigInteger value) {
    byte[] bytes = value.toByteArray();
    int length = (value.bitLength() + 7) / 8;
    byte[] magnitude = new byte[length];
    System.arraycopy(bytes, bytes.length - length, magnitude, 0, length);
    return DigestUtils.base64(magnitude);
}'''

HOP2 = '''/**
 * Encodes data using the base64 algorithm and returns the value as a <code>byte[]</code>. An empty array is returned
 * as it is.
 *
 * @param data
 *            Data to encode
 * @return base64 characters
 */
public static byte[] base64(byte[] data) {
    if (data.length == 0) {
        return data;
    }
    return Metaphone.encodeStandard(data);
}'''

HOP3 = '''/**
 * Encodes a non-empty byte array using the base64 algorithm with the
 * standard alphabet: the upper case letters, the lower case letters,
 * the digits, then '+' and '/'.
 *
 * @param bytes byte array to encode, not empty
 * @return a byte array containing base64 characters
 */
public static byte[] encodeStandard(byte[] bytes) {
    return QuotedPrintableCodec.encodePrintable("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/", bytes);
}'''

HOP4 = '''/**
 * Encodes an array of bytes into an array of base64 characters of the given alphabet. The alphabet is taken as US-ASCII
 * bytes.
 *
 * @param alphabet
 *                  the 64 characters of the alphabet, in order
 * @param bytes
 *                  array of bytes to be encoded, not empty
 * @return array of bytes containing base64 characters
 */
public static final byte[] encodePrintable(String alphabet, byte[] bytes) {
    return URLCodec.encodeGroups(StringUtils.getBytesUsAscii(alphabet), bytes);
}'''

DESIGN = {
 "instance": "Codec-4", "project": "Codec", "bug_id": 4, "seed": 8277,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "encodeInteger", "near_line": 1005},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/codec/binary/Base64Test.java",
             "test_class": "org.apache.commons.codec.binary.Base64Test", "test_method": "testCodeInteger3"},
 "expected_signature": "but was:<...uWz1itkYMZF0/aKDK0Yj[=]==>",
 "gold": {"method": "encodeGroups", "text": GOLD_TEXT,
          "fault": {"old": "        int end = (bytes.length * 4 + 1) / 3;\n"
                           "        if (end % 4 == 1) {\n"
                           "            end++;\n"
                           "        }",
                    "new": "        int end = (bytes.length * 4 + 1) / 3;"}},
 "chain": {
   "facade_body": "if (bigInt == null) {\n            throw new NullPointerException(\"encodeInteger called with null parameter\");\n        }\n"
                  "        return org.apache.commons.codec.language.DoubleMetaphone.encodeMagnitude(bigInt);",
   "lie": "The characters are produced by repeated division of the value by 64, least significant first, each remainder "
          "selecting one character of the base64 alphabet.",
   "hops": [
     {"file": DMP, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "encodeMagnitude",
      "imports": ["java.math.BigInteger", "org.apache.commons.codec.digest.DigestUtils"], "text": HOP1},
     {"file": DGU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "base64",
      "imports": ["org.apache.commons.codec.language.Metaphone"], "text": HOP2},
     {"file": MPH, "class": "org.apache.commons.codec.language.Metaphone", "method": "encodeStandard",
      "imports": ["org.apache.commons.codec.net.QuotedPrintableCodec"], "text": HOP3},
     {"file": QPC, "class": "org.apache.commons.codec.net.QuotedPrintableCodec", "method": "encodePrintable",
      "imports": [], "text": HOP4},
     {"file": URL, "class": "org.apache.commons.codec.net.URLCodec", "method": "encodeGroups", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.binary.Base64::encode",
              "org.apache.commons.codec.binary.Base64::encodeBase64",
              "org.apache.commons.codec.net.BCodec::doEncoding"],
 "ownership_reason": "Only the gold sees the final group of the magnitude bytes together with the number of bytes it holds and "
                     "the positions of its four characters; hops 1-4 pass whole arrays (the magnitude bytes, the standard "
                     "alphabet) and get back the whole encoded array, and no input they can pass makes a final single-byte group "
                     "keep its two characters (zero-extending or left-padding the bytes, or another alphabet, changes the "
                     "characters themselves). The gold's javadoc promises the encoding of the bytes using the base64 algorithm; "
                     "for 64 magnitude bytes (a final group of one byte) the base64 encoding ends in two characters and \"==\" "
                     "(...Yjg==), which the variant does not produce (...Yj===). The convention is pinned outside the gold: "
                     "Base64.encode(byte[], int, int), the streaming encoder behind Base64.encodeBase64 and BCodec.doEncoding, "
                     "writes two characters and then PAD twice for a final single byte ('case 1') and three characters and PAD "
                     "once for two ('case 2'); Base64Test testSingletons (\"AA==\", \"AQ==\", ...), testKnownEncodings "
                     "(\"...Lg==\", \"...cw==\") and testPairs (\"AAA=\") pass; testCodeInteger1, testCodeInteger2 and "
                     "testCodeInteger4 pass through the same chain with final groups of two bytes.",
 "ownership_tests": ["org.apache.commons.codec.binary.Base64Test::testSingletons",
                     "org.apache.commons.codec.binary.Base64Test::testKnownEncodings",
                     "org.apache.commons.codec.binary.Base64Test::testPairs",
                     "org.apache.commons.codec.binary.Base64Test::testCodeInteger1",
                     "org.apache.commons.codec.binary.Base64Test::testCodeInteger4"],
 "compensating": {
   "chain": [
     {"file": DMP, "old": "byte[] bytes = value.toByteArray();",
      "new": "byte[] bytes = value.abs().toByteArray();",
      "why": "hop 1 takes the bytes of the absolute value"},
     {"file": DGU, "old": "return Metaphone.encodeStandard(data);",
      "new": "return Metaphone.encodeStandard(data.length % 3 == 1 ? java.util.Arrays.copyOf(data, data.length + 1) : data);",
      "why": "hop 2 extends data that leaves one byte over with a zero byte"},
     {"file": QPC, "old": "return URLCodec.encodeGroups(StringUtils.getBytesUsAscii(alphabet), bytes);",
      "new": "return URLCodec.encodeGroups(StringUtils.getBytesUsAscii(alphabet + \"=\"), bytes);",
      "why": "hop 4 appends the pad character to the alphabet"},
   ],
 },
 "host_notes": "host_mode largest5 (no other public class of >= 1500 lines). Hosts = hosts_hop_order of the batch-6 task record, "
               "the five largest public non-interface, non-enum classes other than Base64 by newline count: "
               "language.DoubleMetaphone 1105 (hop 1), digest.DigestUtils 582 (hop 2), language.Metaphone 407 (hop 3), "
               "net.QuotedPrintableCodec 387 (hop 4), net.URLCodec 361 (hop 5, gold; smallest host). None substituted: all "
               "five are public concrete classes in which a static method compiles. Anchors (stageB_lib.pick_anchor = "
               "host_search.pick_insertion_anchor with seed 8277 + 100 + i, as mr2_spec inserts them): after `encode` "
               "(line idx 206, seed 8377), after `sha` (252, 8378), after `encode` (371, 8379), after `encode` (213, 8380), "
               "after `encode` (249, 8381); all in the outer class. The facade calls hop 1 by its fully-qualified name; hop 1 "
               "imports BigInteger and DigestUtils, hop 2 imports Metaphone, hop 3 imports QuotedPrintableCodec; hop 4 and "
               "the gold share the net package (hop 4 uses the existing StringUtils import of QuotedPrintableCodec).",
}
