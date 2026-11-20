"""Main run Codec-11 (C10f recipe, batch 6, on the fixed checkout of Defects4J Codec-11; the real bug modified
QuotedPrintableCodec, the target class).

Cell and hosts: C10f, host_mode = largest5 (n1500_other = 0: no other public class of the fixed revision reaches 1500 lines).
The five hosts are exactly hosts_hop_order of the batch-6 task record (the five largest public, non-interface, non-enum classes
other than QuotedPrintableCodec, by newline count), hop i in the i-th largest:
  hop 1 language.DoubleMetaphone   1105 lines
  hop 2 binary.Base64               758 lines
  hop 3 language.bm.Rule            618 lines
  hop 4 digest.DigestUtils          582 lines
  hop 5 language.bm.PhoneticEngine  511 lines (GOLD; the smallest host, 511 lines)
No substitution: all five are public concrete top-level classes in which a static method compiles. Anchors (recipe anchor picker,
stageB_lib.pick_anchor / host_search.pick_insertion_anchor with seed 4220 + 100 + i, as mr2_spec.py inserts them): DoubleMetaphone
after getMaxCodeLen (seed 4320), Base64 after isBase64 (4321), Rule after getPattern (4322), DigestUtils after sha384 (4323),
PhoneticEngine after encode (4324); every anchor is an outer-class member.

reachability_probe: in scratch copies of the fixture, the first statement of each allowed facade was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }`, the copy compiled and the full suite was run (defects4j test,
about 4 s). encodeQuotedPrintable(BitSet, byte[]): 19 failing tests, all 19 with PROBE-REACHED (14 QuotedPrintableCodecTest
methods and 5 QCodecTest methods). decodeQuotedPrintable(byte[]): 18 failing tests, all 18 with PROBE-REACHED, among them
QuotedPrintableCodecTest::testDecodeInvalid, testSoftLineBreakDecode, testSkipNotEncodedCRLF, testDecodeWithNullArray and five
QCodecTest methods. Baseline: 0 failing tests. Both facades are reached by existing tests.

Facade: QuotedPrintableCodec.decodeQuotedPrintable(byte[]) (allowed target, BATCH6_PREREGISTRATION.md row Codec-11). The other
allowed target, encodeQuotedPrintable(BitSet, byte[]), was screened and set aside. Its only omissions that exactly one test
catches are the whitespace step before a soft line break (testTrailingSpecial), the whitespace step for the third-to-last
octet, the soft line break before the last two octets and the whitespace step for the last octet (testUltimateSoftBreak). The
first three leave output that is still valid quoted-printable (RFC 1521 allows white space before a soft-break '='; the last
encoded line stays within 76 characters: 74, 75 and 76 characters on the trigger's inputs), so no contract is violated on
the trigger; the fourth is recoverable by a one-statement rewrite of the final output octet at any caller; and in the single
encoder routine each of them leaves a line-end rule (the whitespace escape or the soft line break) applied at some line ends
but not at others (checklist T3).
Original computation of the facade: a null array gives null; then every octet is scanned: '=' followed by CR is a soft line
break and is skipped; '=' followed by two characters is decoded with Utils.digit16 (which throws DecoderException for a
character that is not a hexadecimal digit) into one octet; an index past the end is reported as
DecoderException("Invalid quoted-printable encoding"); a CR or LF anywhere else is skipped; every other octet is copied.

Chain (the facade keeps its null guard and delegates; the facade calls hop 1 by its fully-qualified name):
  hop 1 DoubleMetaphone.decodeQuotedText    placement: creates the buffer, returns its contents
  hop 2 Base64.decodeQuotedChars            pass-through
  hop 3 Rule.unquoteOctets                  pass-through
  hop 4 DigestUtils.writeQuotedOctets       pass-through
  hop 5 PhoneticEngine.appendDecodedOctets  GOLD: the scan of every octet (line breaks skipped, ordinary octets copied, an
                                            escape character followed by a line break skipped, an escape character followed
                                            by two characters decoded into one octet, both characters checked as hexadecimal
                                            digits, an escape cut short by the end of the array reported as DecoderException)
The gold uses Character.digit with its own check because Utils (net package) is package-private and not visible from
language.bm. The correct configuration returns the original result and throws DecoderException in the same cases for every
input, with one difference on input that the original rejected: an escape character followed by a lone LF is skipped as a soft
line break (the original sent the LF to digit16 and threw). The soft-break test covers both line-break characters so that the
gold treats CR and LF alike in both of its line-break tests.

Fault (one omission in the gold): the hexadecimal-digit check of the two characters after an escape character is dropped, so
Character.digit's -1 for a non-digit is folded into an octet: "=WW" is written as the octet 0xEF instead of being rejected.
Trigger: the EXISTING test QuotedPrintableCodecTest::testDecodeInvalid; its first two blocks ("=" and "=A", cut short by the end
of the array) still get DecoderException from the gold's catch; the third block, decode("=WW"), returns normally and the test
fails with "DecoderException should have been thrown". It is the only test that decodes a non-hexadecimal escape through the
facade (the probe-reached decode tests, QCodecTest and RFC1522CodecTest pass on the variant).

Quiet gold: its javadoc states the idiomatic contract (writes the octets represented by an array of quoted-printable
characters) and is silent on the digit check. "=WW" represents no octet, so writing 0xEF violates that contract on the trigger
input; the facade's own javadoc promises DecoderException when quoted-printable decoding is unsuccessful.
External pins (convention outside the gold): URLCodec.decodeUrl decodes its '%' escapes the same way and passes both characters
through Utils.digit16, which throws DecoderException for a character that is not a hexadecimal digit
(URLCodecTest::testDecodeInvalid: "%WW" bad first character and "%0W" bad second character both throw); Hex.decodeHex /
Hex.toDigit do the same check per character (HexTest::testDecodeBadCharacterPos0 / Pos1: "q0" and "0q" throw). Utils.digit16 is
also what the facade's original body used.

Single owner: only the gold sees an escape sequence and its two characters; hops 1-4 hold the whole array and the buffer, never
an individual escape. Once the gold has written 0xEF for "=WW", no caller can tell it from a genuine "=EF", so the effect cannot
be recovered after the gold, and no rearrangement of the input or of the buffer by a hop makes the gold reject it. Declared
alternatives (G9): hop 2 rejects an array whose last character is the escape character; hop 3 reports an
IllegalArgumentException of the decoding as DecoderException; hop 4 upper-cases the characters before decoding. None changes
the trigger's "=WW" case.
Recorded bypass (checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests):
 B-0 the facade or any of hops 1-4 pre-validates the whole array with a regular expression before delegating, e.g. hop 4
     `if (java.util.regex.Pattern.compile("(?s)=(?![\\r\\n]|[0-9A-Fa-f]{2}|.?\\z)").matcher(StringUtils.newStringIso8859_1(bytes)).find()) { throw new DecoderException("Not a hexadecimal escape"); }`
     placed before the delegating call: a second implementation of the gold's per-escape digit decision at a level that never
     sees an escape, which re-parses the whole array with a different grammar; not a repair of the chain.

Lie: the facade's javadoc claims the data is first split into lines at each soft line break and each line decoded on its own
before the decoded lines are joined; the chain splits nothing and decodes the array in one pass into one buffer. It names
neither hexadecimal digits nor any check nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold: the original's soft-break test looked at CR only while the line-break skip treats CR and LF (a one-of-two pattern
  under T3(b)); it was rewritten so that both tests treat CR and LF. The original catch message "Invalid quoted-printable
  encoding" would name a class that the variant handles only in part (T3(c)); the gold's message names only the case its catch
  handles ("Incomplete escape sequence"). The digit check tests both characters (u == -1 || l == -1). No @throws clause states a
  class of rejected input. Nothing else needed rewriting.
 Variant gold (javadoc, signature, loop; the digit check removed):
  T1 absent: bytes is read for the bound, every octet and both characters of each escape; buffer receives every written octet;
     both change the result. Neither is used only in an argument check.
  T2 absent: b is read by the line-break test, the escape test and the copy; u and l are read in the written octet; e is the
     cause of the thrown exception; i is advanced by the for header and by the two reads of an escape; no literal-initialised
     local, no flag, counter or best-so-far; each if changes what is written or skipped, and the catch throws.
  T3 absent: CR and LF are treated alike in both line-break tests; the two characters of an escape get the same treatment
     (Character.digit, both folded into the octet); no case, member or range end is handled while a sibling is not; no class is
     named that is handled in part.
  T4 absent: the javadoc says 'Writes the octets represented by an array of quoted-printable characters to a buffer' (a general
     description that the loop addresses), '@param bytes array of quoted-printable characters' and '@param buffer the buffer to
     write the octets to' (caller inputs); the only message, 'Incomplete escape sequence', is thrown exactly when an escape runs
     past the end of the array; no comment; identifiers (b, u, l, i, e, appendDecodedOctets) name nothing the body does not meet."""

QPC = "src/main/java/org/apache/commons/codec/net/QuotedPrintableCodec.java"
DM = "src/main/java/org/apache/commons/codec/language/DoubleMetaphone.java"
B64 = "src/main/java/org/apache/commons/codec/binary/Base64.java"
RULE = "src/main/java/org/apache/commons/codec/language/bm/Rule.java"
DU = "src/main/java/org/apache/commons/codec/digest/DigestUtils.java"
PE = "src/main/java/org/apache/commons/codec/language/bm/PhoneticEngine.java"

GOLD_TEXT = '''/**
 * Writes the octets represented by an array of quoted-printable characters to a buffer.
 *
 * @param bytes
 *            array of quoted-printable characters
 * @param buffer
 *            the buffer to write the octets to
 */
public static void appendDecodedOctets(byte[] bytes, ByteArrayOutputStream buffer) throws DecoderException {
    for (int i = 0; i < bytes.length; i++) {
        final int b = bytes[i];
        if (b == '\\r' || b == '\\n') {
            continue;
        }
        if (b != '=') {
            buffer.write(b);
            continue;
        }
        try {
            if (bytes[i + 1] == '\\r' || bytes[i + 1] == '\\n') {
                continue;
            }
            final int u = Character.digit((char) bytes[++i], 16);
            final int l = Character.digit((char) bytes[++i], 16);
            if (u == -1 || l == -1) {
                throw new DecoderException("Not a hexadecimal digit after the escape character");
            }
            buffer.write((u << 4) + l);
        } catch (ArrayIndexOutOfBoundsException e) {
            throw new DecoderException("Incomplete escape sequence", e);
        }
    }
}'''

HOP1 = '''/**
 * Decodes an array of quoted-printable characters into the octets they represent.
 *
 * @param bytes array of quoted-printable characters
 * @return array of decoded octets
 */
public static byte[] decodeQuotedText(byte[] bytes) throws DecoderException {
    ByteArrayOutputStream buffer = new ByteArrayOutputStream();
    Base64.decodeQuotedChars(bytes, buffer);
    return buffer.toByteArray();
}'''

HOP2 = '''/**
 * Decodes an array of quoted-printable characters into the octets they represent, writing the octets to a buffer.
 *
 * @param bytes
 *            array of quoted-printable characters
 * @param buffer
 *            the buffer to write the decoded octets to
 */
public static void decodeQuotedChars(byte[] bytes, ByteArrayOutputStream buffer) throws DecoderException {
    Rule.unquoteOctets(bytes, buffer);
}'''

HOP3 = '''/**
 * Writes the octets represented by an array of quoted-printable characters to a buffer.
 *
 * @param bytes
 *            the quoted-printable characters
 * @param buffer
 *            the buffer to write the octets to
 */
public static void unquoteOctets(byte[] bytes, ByteArrayOutputStream buffer) throws DecoderException {
    DigestUtils.writeQuotedOctets(bytes, buffer);
}'''

HOP4 = '''/**
 * Writes the octets represented by an array of quoted-printable characters to a buffer.
 *
 * @param bytes
 *            Quoted-printable characters
 * @param buffer
 *            Buffer to write the octets to
 */
public static void writeQuotedOctets(byte[] bytes, ByteArrayOutputStream buffer) throws DecoderException {
    PhoneticEngine.appendDecodedOctets(bytes, buffer);
}'''

DESIGN = {
 "instance": "Codec-11", "project": "Codec", "bug_id": 11, "seed": 4220,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "host_mode": "largest5", "host_lines": [1105, 758, 618, 582, 511], "smallest_host_lines": 511,
 "reachability_probe": "decodeQuotedPrintable: probe throw as first statement, full suite: 18 failing, all with PROBE-REACHED "
                       "(incl. QuotedPrintableCodecTest::testDecodeInvalid); encodeQuotedPrintable: 19 failing, all with "
                       "PROBE-REACHED; baseline 0 failing",
 "facade": {"file": QPC, "class": "org.apache.commons.codec.net.QuotedPrintableCodec", "method": "decodeQuotedPrintable",
            "near_line": 257},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/codec/net/QuotedPrintableCodecTest.java",
             "test_class": "org.apache.commons.codec.net.QuotedPrintableCodecTest", "test_method": "testDecodeInvalid"},
 "expected_signature": "DecoderException should have been thrown",
 "gold": {"method": "appendDecodedOctets", "text": GOLD_TEXT,
          "fault": {"old": "                final int l = Character.digit((char) bytes[++i], 16);\n"
                           "                if (u == -1 || l == -1) {\n"
                           "                    throw new DecoderException(\"Not a hexadecimal digit after the escape character\");\n"
                           "                }\n"
                           "                buffer.write((u << 4) + l);",
                    "new": "                final int l = Character.digit((char) bytes[++i], 16);\n"
                           "                buffer.write((u << 4) + l);"}},
 "chain": {
   "facade_body": "if (bytes == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.codec.language.DoubleMetaphone.decodeQuotedText(bytes);",
   "lie": "The data is first split into lines at each soft line break, and every line is then decoded on its own before "
          "the decoded lines are joined.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "decodeQuotedText",
      "imports": ["java.io.ByteArrayOutputStream", "org.apache.commons.codec.DecoderException",
                  "org.apache.commons.codec.binary.Base64"], "text": HOP1},
     {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "decodeQuotedChars",
      "imports": ["java.io.ByteArrayOutputStream", "org.apache.commons.codec.DecoderException",
                  "org.apache.commons.codec.language.bm.Rule"], "text": HOP2},
     {"file": RULE, "class": "org.apache.commons.codec.language.bm.Rule", "method": "unquoteOctets",
      "imports": ["java.io.ByteArrayOutputStream", "org.apache.commons.codec.DecoderException",
                  "org.apache.commons.codec.digest.DigestUtils"], "text": HOP3},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "writeQuotedOctets",
      "imports": ["java.io.ByteArrayOutputStream", "org.apache.commons.codec.DecoderException",
                  "org.apache.commons.codec.language.bm.PhoneticEngine"], "text": HOP4},
     {"file": PE, "class": "org.apache.commons.codec.language.bm.PhoneticEngine", "method": "appendDecodedOctets",
      "imports": ["java.io.ByteArrayOutputStream", "org.apache.commons.codec.DecoderException"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.net.URLCodec::decodeUrl",
              "org.apache.commons.codec.net.Utils::digit16",
              "org.apache.commons.codec.binary.Hex::toDigit"],
 "ownership_reason": "Only the gold sees an escape sequence and the two characters that follow the escape character; hops 1-4 "
                     "hold the whole array and the buffer and never an individual escape. Once the gold has folded "
                     "Character.digit's -1 into an octet (\"=WW\" written as 0xEF), no caller can tell it from a genuine "
                     "\"=EF\", so the effect cannot be recovered after the gold. The convention is pinned outside the gold: "
                     "URLCodec.decodeUrl decodes its escapes the same way and sends both characters through Utils.digit16, "
                     "which throws DecoderException for a character that is not a hexadecimal digit "
                     "(URLCodecTest::testDecodeInvalid: \"%WW\" and \"%0W\" throw); Hex.decodeHex checks every character with "
                     "Hex.toDigit (HexTest::testDecodeBadCharacterPos0 / Pos1: \"q0\" and \"0q\" throw); Utils.digit16 is what "
                     "the facade's original body used. The gold's javadoc promises the octets represented by the "
                     "quoted-printable characters, which \"=WW\" does not have, and the facade's javadoc promises "
                     "DecoderException when quoted-printable decoding is unsuccessful. A hop that pre-validates the whole "
                     "array with a regular expression passes the existing tests but is a second implementation of the "
                     "gold's per-escape decision at a level that never sees an escape (recorded bypass).",
 "ownership_tests": ["org.apache.commons.codec.net.URLCodecTest::testDecodeInvalid",
                     "org.apache.commons.codec.binary.HexTest::testDecodeBadCharacterPos0",
                     "org.apache.commons.codec.binary.HexTest::testDecodeBadCharacterPos1",
                     "org.apache.commons.codec.net.QuotedPrintableCodecTest::testSoftLineBreakDecode"],
 "compensating": {
   "chain": [
     {"file": B64, "old": "Rule.unquoteOctets(bytes, buffer);",
      "new": "if (bytes.length > 0 && bytes[bytes.length - 1] == '=') { throw new DecoderException(\"Incomplete escape sequence\"); } Rule.unquoteOctets(bytes, buffer);",
      "why": "hop 2 also rejects an array whose last character is the escape character"},
     {"file": RULE, "old": "DigestUtils.writeQuotedOctets(bytes, buffer);",
      "new": "try { DigestUtils.writeQuotedOctets(bytes, buffer); } catch (IllegalArgumentException e) { throw new DecoderException(e.getMessage(), e); }",
      "why": "hop 3 reports an IllegalArgumentException of the decoding as a DecoderException"},
     {"file": DU, "old": "PhoneticEngine.appendDecodedOctets(bytes, buffer);",
      "new": "PhoneticEngine.appendDecodedOctets(StringUtils.getBytesUsAscii(StringUtils.newStringUsAscii(bytes).toUpperCase()), buffer);",
      "why": "hop 4 upper-cases the characters before decoding"},
   ],
 },
 "host_notes": "host_mode largest5 (no other public class reaches 1500 lines): hosts are hosts_hop_order of the batch-6 task "
               "record, the five largest public non-interface non-enum classes other than QuotedPrintableCodec by newline "
               "count: language.DoubleMetaphone 1105 (hop 1), binary.Base64 758 (hop 2), language.bm.Rule 618 (hop 3), "
               "digest.DigestUtils 582 (hop 4), language.bm.PhoneticEngine 511 (hop 5, gold; smallest host 511). No "
               "substitution: each is a public concrete top-level class in which a static method compiles. Anchors from the "
               "recipe's picker with seed 4220 + 100 + i (as mr2_spec.py inserts): after DoubleMetaphone.getMaxCodeLen "
               "(seed 4320), Base64.isBase64 (4321), Rule.getPattern (4322), DigestUtils.sha384 (4323), "
               "PhoneticEngine.encode (4324); all outer-class members. The facade calls hop 1 by its fully-qualified name; "
               "each hop imports ByteArrayOutputStream, DecoderException and the next host (Rule and PhoneticEngine share "
               "the language.bm package).",
}
