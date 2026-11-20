"""Main run Codec-13 (cell C10f, batch 6: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J Codec-13; the real
bug modified StringUtils, the target class, together with CharSequenceUtils and DoubleMetaphone).

Facade: StringUtils.getBytesUnchecked(String, String) (the only allowed target, BATCH6_PREREGISTRATION.md row 141; no facade reuse).
Original computation: a null String gives null; otherwise String.getBytes(charsetName), an UnsupportedEncodingException for an
unknown name being rethrown as IllegalStateException("<name>: <exception>"). String.getBytes looks the charset up by name and
encodes the characters with a new encoder of that charset that replaces malformed input and unmappable characters.

Reachability probe (BUILD_BRIEF_C10F_ADDENDUM section 2), run before designing on a scratch copy of the fixture
(/private/tmp/codec13-builder/probe): the facade's first statement was made `if (true) { throw new
IllegalStateException("PROBE-REACHED"); }` (a bare throw would make the rest of the body unreachable and not compile); defects4j
compile OK, then the FULL suite (defects4j test, 609 tests): 7 failing tests, all with java.lang.IllegalStateException:
PROBE-REACHED: StringUtilsTest::testGetBytesIso8859_1, testGetBytesUsAscii, testGetBytesUtf16, testGetBytesUtf16Be,
testGetBytesUtf16Le, testGetBytesUtf8 (all through the private helper testGetBytesUnchecked) and testGetBytesUncheckedNullInput.
testGetBytesUncheckedBadName expects an IllegalStateException and therefore passed under the probe; it reaches the facade too.
No other test and no production code calls getBytesUnchecked. Result: REACHED.

Hosts: host_mode = largest5 (the fixed revision has no other public class of 1500 lines or more). The five hosts are exactly
hosts_hop_order of the task record, in that order, none substituted (all five are public concrete top-level classes in which a
static method compiles):
  hop 1 language.DoubleMetaphone   1009 lines
  hop 2 digest.DigestUtils          819 lines
  hop 3 binary.Base64               775 lines
  hop 4 language.bm.Rule            697 lines
  hop 5 digest.Sha2Crypt            545 lines (gold; the smallest host, 545 lines)
Anchors: the recipe's stageB_lib.pick_insertion_anchor through insert_hop with the instance seed 3172 (anchor seed 3172 + 100 + i):
after DoubleMetaphone.getMaxCodeLen, DigestUtils.sha256, Base64.isBase64, Rule.getInstance and Sha2Crypt.sha512Crypt (the spec's
stage_b record holds the anchors actually used).

Chain:
  facade StringUtils.getBytesUnchecked      argument guard (a null String gives null), then one call to hop 1
  hop 1 DoubleMetaphone.valueBytes         lookup: the charset resolved by name; an unsupported name gives IllegalStateException
  hop 2 DigestUtils.dataBytes              decision: an empty String gives an empty array
  hop 3 Base64.toOctets                    pass-through
  hop 4 Rule.inputBytes                    pass-through (the String handed on as a CharSequence)
  hop 5 Sha2Crypt.encodeKey                GOLD: the encoding itself; a new encoder of the charset that replaces malformed input
                                           and unmappable characters, an output buffer sized by the encoder's average bytes per
                                           char, and the encode-and-flush loop that enlarges the buffer whenever the encoder
                                           reports an overflow
The correct configuration returns the original result for every String and every supported charset name (checked in a scratch
Java program against String.getBytes for every available charset that can encode, on 14 samples including the empty String,
lone and paired surrogates, CJK text, 5000 non-ASCII chars and stateful encodings: 2394 cases, 0 mismatches). An unsupported
name still gives IllegalStateException("<name>: <exception>"), the exception in the message now being the
UnsupportedCharsetException of Charset.forName; an illegal name gives the same IllegalCharsetNameException as before.

Fault (omission of the iteration in the gold): the overflow loop is dropped; the encode and flush calls remain as plain
statements, so the gold encodes once into the buffer sized by the average bytes per char and returns what fits. Trigger: the
EXISTING test StringUtilsTest::testGetBytesUtf16. "UTF-16" writes a byte-order mark before the characters, so "ABC" needs 8 bytes
while the estimate is 3 x 2.0 = 6: the variant returns FE FF 00 41 00 42 and assertTrue(Arrays.equals(expected, actual)) in the
helper testGetBytesUnchecked (StringUtilsTest.java:64) fails. The other five charset tests fit their estimate exactly
(ISO-8859-1, US-ASCII 3 x 1.0; UTF-8 (int) (3 x 1.1) = 3; UTF-16BE, UTF-16LE 3 x 2.0, no mark) and pass; the null and bad-name
tests never reach the gold. No other test reaches the chain. The gold's javadoc states the idiomatic contract (the characters
of the key encoded into a new byte array using the given charset) and is silent on buffer sizes and overflow; the variant
violates that contract on the trigger input (the last character is missing). The omission is not specific to UTF-16: any text
whose encoding exceeds the estimate is cut short (for example "\\u00e9" in UTF-8 gives an empty array), which no existing test
checks.

External pins (the convention that the result holds the encoding of every character, never cut at an initial capacity):
StringUtils.getBytesUtf16, the facade's sibling, encodes to UTF-16 with the byte-order mark and every character through
String.getBytes(Charset); Hex.encode(byte[]) encodes its hex String with the codec's charset the same way, and
HexTest::testRequiredCharset (UTF-16 included) and HexTest::testCustomCharset (every available charset) assert that these bytes
equal String.getBytes(name); BaseNCodec.ensureBufferSize takes the same step for Base64 and Base32 output (the buffer is enlarged
whenever the next output would not fit, output is never dropped). StringUtilsTest::testGetBytesUtf16Be and ::testGetBytesUtf16Le
assert that the chain's own result equals String.getBytes(name) and pass on the variant.

Single owner: only the gold creates the encoder and the buffers, sees the encoder's overflow result and can enlarge the buffer;
hops 1-4 hand on the String and the Charset and get back one finished array. A caller cannot change the estimate (the gold wraps
the characters itself and takes the average from an encoder it creates), and no JDK charset other than UTF-16 itself produces the
UTF-16 output with a larger estimate. Declared alternatives (G9): hop 1 resolves "UTF-16" to its big-endian form; hop 3 hands on a
CharBuffer over a copy of the characters; hop 4 hands on a String copy and the charset re-resolved by its canonical name. None
changes the trigger's result.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in scratch copies,
defects4j test: 0 failing tests each; B-0 at hop 4 as `return input.toString().getBytes(charset);`, B-1 at hop 2 as below):
 B-0 bypass: the facade (its original body) or any of hops 1-4 returns value.getBytes(charset) / String.getBytes(charsetName),
     the JDK's own encoding, discarding the rest of the chain including the gold.
 B-1 test-fitted: a hop rewrites UTF-16 as UTF-16BE with an explicit U+FEFF first char, e.g. hop 2
     `return Base64.toOctets(Charsets.UTF_16.equals(charset) ? "\\uFEFF" + data : data, Charsets.UTF_16.equals(charset) ? Charsets.UTF_16BE : charset);`
     The UTF-16BE estimate for n + 1 chars (2n + 2) happens to be exact, so the trigger passes, but every other text whose
     encoding exceeds its estimate is still cut short (getBytesUnchecked("\\u00e9", "UTF-8") gives an empty array where
     String.getBytes gives C3 A9, contradicting the facade's contract and the pins; confirmed on the B-1 build), and the hop no
     longer encodes with the given charset as its javadoc says.
Side note: hop 4 lives in Rule, so the first call through the chain runs Rule's static initializer, which loads the
Beider-Morse rule resources from the class path; the resources are on the defects4j test class path and every gate passed.

Lie: the facade's javadoc claims the string is first normalized to Unicode Normalization Form C so that canonically equivalent
strings are encoded to the same bytes; no hop normalizes anything. It names neither buffers, sizes, overflow, the byte-order mark,
the omitted step nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: key is wrapped and encoded; charset gives the encoder; both decide the returned bytes.
  T2 absent: encoder, in and bytes all reach the return; out is enlarged inside the loop it serves; the loop runs its body exactly
     when the encoder reports an overflow; no literal-initialised local, flag, counter or best-so-far.
  T3 absent: both coder calls (encode and flush) are tested for overflow in the one loop condition; both error actions (malformed,
     unmappable) are set to REPLACE, so no error result can occur and none is tested; no other set, pair or range end.
  T4 absent: the javadoc names only the encoding of the key's characters with the given charset into a new byte array;
     '@param ... not null' are caller preconditions; no rule, bound, value class or case is named.
  Nothing needed rewriting; the gold was written without final on its locals (the host mixes final and non-final locals) so that
  the variant's buffer local does not stand out as a non-final local that is never reassigned.
 Variant gold (javadoc, signature, encoder set-up, `CharBuffer in = CharBuffer.wrap(key);`, `ByteBuffer out =
 ByteBuffer.allocate((int) (in.remaining() * encoder.averageBytesPerChar()));`, `encoder.encode(in, out, true);`,
 `encoder.flush(out);`, flip, copy into bytes, return):
  T1 absent: key is read by CharBuffer.wrap and its chars are encoded; charset creates the encoder; each changes the result.
  T2 absent: encoder is read by the size estimate, encode and flush; in is a call argument of encode; out is a call argument of
     encode and flush and is read by remaining() and get(); bytes is returned; out is initialised by an allocation, not a
     literal, and there is no loop, branch, case or ternary left.
  T3 absent: no case, branch or check remains (no coder result is tested: 'No member handled'); malformed input and unmappable
     characters both keep their REPLACE action; the gold names no class it handles in part; no pair half or range end is
     treated.
  T4 absent: 'Encodes the characters of a key into a new byte array using the given charset' and '@return the encoded key
     bytes' are general descriptions that the encode lines address; '@param ... not null' are caller preconditions; no inline
     comment; the identifiers (encodeKey, encoder, in, out, bytes) name nothing the body does not meet."""

SU = "src/main/java/org/apache/commons/codec/binary/StringUtils.java"
DM = "src/main/java/org/apache/commons/codec/language/DoubleMetaphone.java"
DU = "src/main/java/org/apache/commons/codec/digest/DigestUtils.java"
B64 = "src/main/java/org/apache/commons/codec/binary/Base64.java"
RULE = "src/main/java/org/apache/commons/codec/language/bm/Rule.java"
SHA = "src/main/java/org/apache/commons/codec/digest/Sha2Crypt.java"

GOLD_TEXT = '''/**
 * Encodes the characters of a key into a new byte array using the given charset.
 *
 * @param key
 *            the characters of the key, not null
 * @param charset
 *            the charset to encode the key with, not null
 * @return the encoded key bytes
 */
public static byte[] encodeKey(final CharSequence key, final Charset charset) {
    CharsetEncoder encoder = charset.newEncoder().onMalformedInput(CodingErrorAction.REPLACE)
            .onUnmappableCharacter(CodingErrorAction.REPLACE);
    CharBuffer in = CharBuffer.wrap(key);
    ByteBuffer out = ByteBuffer.allocate((int) (in.remaining() * encoder.averageBytesPerChar()));
    while (encoder.encode(in, out, true).isOverflow() || encoder.flush(out).isOverflow()) {
        out.flip();
        out = ByteBuffer.allocate(2 * out.capacity() + 1).put(out);
    }
    out.flip();
    byte[] bytes = new byte[out.remaining()];
    out.get(bytes);
    return bytes;
}'''

HOP1 = '''/**
 * Encodes a String value into a sequence of bytes using the named charset.
 *
 * @param value
 *            the String value to encode, not null
 * @param charsetName
 *            the name of a required {@link Charset}
 * @return the encoded bytes
 * @throws IllegalStateException
 *             if the named charset is not supported, which should never happen for a required charset name
 */
public static byte[] valueBytes(final String value, final String charsetName) {
    try {
        return DigestUtils.dataBytes(value, Charset.forName(charsetName));
    } catch (final UnsupportedCharsetException e) {
        throw new IllegalStateException(charsetName + ": " + e);
    }
}'''

HOP2 = '''/**
 * Encodes String data into bytes using the given charset.
 * <p>
 * Empty data gives an empty array.
 * </p>
 *
 * @param data
 *            the data to encode, not null
 * @param charset
 *            the charset to encode the data with
 * @return the encoded bytes
 */
public static byte[] dataBytes(final String data, final Charset charset) {
    if (data.length() == 0) {
        return new byte[0];
    }
    return Base64.toOctets(data, charset);
}'''

HOP3 = '''/**
 * Encodes the characters of a non-empty String into octets using the given charset.
 *
 * @param str
 *            the String to encode, not null or empty
 * @param charset
 *            the charset to encode the String with
 * @return the encoded octets
 */
public static byte[] toOctets(final String str, final Charset charset) {
    return Rule.inputBytes(str, charset);
}'''

HOP4 = '''/**
 * Encodes a sequence of input characters into bytes using the given charset.
 *
 * @param input
 *            the characters to encode, not null or empty
 * @param charset
 *            the charset to encode the characters with
 * @return the encoded bytes
 */
public static byte[] inputBytes(final CharSequence input, final Charset charset) {
    return Sha2Crypt.encodeKey(input, charset);
}'''

DESIGN = {
 "instance": "Codec-13", "project": "Codec", "bug_id": 13, "seed": 3172,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SU, "class": "org.apache.commons.codec.binary.StringUtils", "method": "getBytesUnchecked", "near_line": 137},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/codec/binary/StringUtilsTest.java",
             "test_class": "org.apache.commons.codec.binary.StringUtilsTest", "test_method": "testGetBytesUtf16"},
 "expected_signature": "StringUtilsTest.testGetBytesUnchecked(StringUtilsTest.java:64)",
 "gold": {"method": "encodeKey", "text": GOLD_TEXT,
          "fault": {"old": "        while (encoder.encode(in, out, true).isOverflow() || encoder.flush(out).isOverflow()) {\n"
                           "            out.flip();\n"
                           "            out = ByteBuffer.allocate(2 * out.capacity() + 1).put(out);\n"
                           "        }",
                    "new": "        encoder.encode(in, out, true);\n"
                           "        encoder.flush(out);"}},
 "chain": {
   "facade_body": "if (string == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.codec.language.DoubleMetaphone.valueBytes(string, charsetName);",
   "lie": "The string is first normalized to Unicode Normalization Form C, so that canonically equivalent strings are "
          "encoded to the same bytes.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "valueBytes",
      "imports": ["java.nio.charset.Charset", "java.nio.charset.UnsupportedCharsetException",
                  "org.apache.commons.codec.digest.DigestUtils"], "text": HOP1},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "dataBytes",
      "imports": ["java.nio.charset.Charset", "org.apache.commons.codec.binary.Base64"], "text": HOP2},
     {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "toOctets",
      "imports": ["java.nio.charset.Charset", "org.apache.commons.codec.language.bm.Rule"], "text": HOP3},
     {"file": RULE, "class": "org.apache.commons.codec.language.bm.Rule", "method": "inputBytes",
      "imports": ["java.nio.charset.Charset", "org.apache.commons.codec.digest.Sha2Crypt"], "text": HOP4},
     {"file": SHA, "class": "org.apache.commons.codec.digest.Sha2Crypt", "method": "encodeKey",
      "imports": ["java.nio.ByteBuffer", "java.nio.CharBuffer", "java.nio.charset.Charset", "java.nio.charset.CharsetEncoder",
                  "java.nio.charset.CodingErrorAction"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.binary.StringUtils::getBytesUtf16",
              "org.apache.commons.codec.binary.Hex::encode",
              "org.apache.commons.codec.binary.BaseNCodec::ensureBufferSize"],
 "ownership_reason": "Only the gold creates the encoder and the output buffer, sees the encoder's overflow result and can enlarge "
                     "the buffer; hops 1-4 hand on the String and the Charset and get back one finished array, and none of them "
                     "can change the gold's size estimate (the gold wraps the characters and takes the average bytes per char "
                     "from an encoder it creates itself). Once the gold has returned the bytes that fit, the rest of the "
                     "encoding is lost to every caller. The convention that the result holds the encoding of every character "
                     "is pinned outside the gold: StringUtils.getBytesUtf16, the facade's sibling, returns the UTF-16 encoding "
                     "with the byte-order mark and every character (String.getBytes(Charset)); Hex.encode(byte[]) encodes its "
                     "hex String with the codec's charset the same way, and HexTest testRequiredCharset (UTF-16 included) and "
                     "testCustomCharset (every available charset) assert that these bytes equal String.getBytes(name); "
                     "BaseNCodec.ensureBufferSize enlarges the Base64/Base32 output buffer whenever the next output would not "
                     "fit instead of dropping output; StringUtilsTest testGetBytesUtf16Be and testGetBytesUtf16Le assert that "
                     "the chain's own result equals String.getBytes(name). The gold's javadoc promises the characters of the "
                     "key encoded with the given charset, which FE FF 00 41 00 42 is not for \"ABC\" in UTF-16. A one-line hop "
                     "edit that rewrites UTF-16 as UTF-16BE with an explicit U+FEFF first char passes the existing tests only "
                     "because that estimate happens to be exact; it leaves every other text whose encoding exceeds its estimate "
                     "cut short (getBytesUnchecked(\"\\u00e9\", \"UTF-8\") gives an empty array) and no longer encodes with "
                     "the given charset as the hop's javadoc says.",
 "ownership_tests": ["org.apache.commons.codec.binary.HexTest::testRequiredCharset",
                     "org.apache.commons.codec.binary.HexTest::testCustomCharset",
                     "org.apache.commons.codec.binary.StringUtilsTest::testGetBytesUtf16Be",
                     "org.apache.commons.codec.binary.StringUtilsTest::testGetBytesUtf16Le"],
 "compensating": {
   "chain": [
     {"file": DM, "old": "return DigestUtils.dataBytes(value, Charset.forName(charsetName));",
      "new": "return DigestUtils.dataBytes(value, Charset.forName(\"UTF-16\".equalsIgnoreCase(charsetName) ? \"UTF-16BE\" : charsetName));",
      "why": "hop 1 resolves UTF-16 to its big-endian form"},
     {"file": B64, "old": "return Rule.inputBytes(str, charset);",
      "new": "return Rule.inputBytes(java.nio.CharBuffer.wrap(str.toCharArray()), charset);",
      "why": "hop 3 hands on a CharBuffer over a copy of the characters"},
     {"file": RULE, "old": "return Sha2Crypt.encodeKey(input, charset);",
      "new": "return Sha2Crypt.encodeKey(input.toString(), Charset.forName(charset.name()));",
      "why": "hop 4 hands on a String copy and the charset re-resolved by its canonical name"},
   ],
 },
 "host_notes": "host_mode largest5 (no other public class of >= 1500 lines in the fixed revision). Hosts exactly as "
               "hosts_hop_order of the task record (five largest public non-interface non-enum classes other than StringUtils, "
               "by newline count): language.DoubleMetaphone 1009 (hop 1), digest.DigestUtils 819 (hop 2), binary.Base64 775 "
               "(hop 3), language.bm.Rule 697 (hop 4), digest.Sha2Crypt 545 (hop 5, gold; smallest host 545). None substituted: "
               "all five are public concrete top-level classes in which a static method compiles (Base64 extends BaseNCodec "
               "and DoubleMetaphone implements StringEncoder, which does not affect a static method; Rule's nested types are "
               "untouched). Anchors by stageB_lib.pick_insertion_anchor through insert_hop with seed 3172 + 100 + i: after "
               "DoubleMetaphone.getMaxCodeLen, DigestUtils.sha256, Base64.isBase64, Rule.getInstance, Sha2Crypt.sha512Crypt, "
               "all at class-body depth 1 (see the spec's stage_b record). The facade calls hop 1 by its fully-qualified name; "
               "each hop imports Charset and the next host; hop 1 also imports UnsupportedCharsetException and the gold the "
               "java.nio buffer and encoder types.",
}
