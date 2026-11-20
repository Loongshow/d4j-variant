"""Main run Codec-11__i (cell C10i, batch 7, the paired static/instance bridge: the C10 recipe with an INSTANCE-method facade, on the
fixed checkout of Defects4J Codec-11; the real bug modified QuotedPrintableCodec, the facade's class). Paired static instance:
MR-Codec-11 (batch 6, facade QuotedPrintableCodec.decodeQuotedPrintable); none of its files was opened (addendum section 2).

Facade: QuotedPrintableCodec.encode(String) (instance method; allowed targets QuotedPrintableCodec.encode / .decode,
BATCH7_PREREGISTRATION.md row 191; no facade reuse). The String overload is the one that carries object state (the default charset)
and the whole encoding computation, and the one the trigger reaches; encode(byte[]), encode(Object) and encode(String, String) stay
intact, as does the static encodeQuotedPrintable(BitSet, byte[]), the sibling pin below. decode(String) was not used: the decode
behaviours that a single test catches (the rejection of a non-hexadecimal escape, the dropping of raw CR/LF) are either open to a
one-line check or strip above the gold or are codec conventions that no decoding contract states.
Original computation: a null String gives null; otherwise the String is converted to bytes in the default charset (getDefaultCharset(),
the private field charset; an unsupported charset becomes an EncoderException with the same message), encodeQuotedPrintable(
PRINTABLE_CHARS, bytes) writes the quoted-printable form (each byte unsigned; a printable byte as it is, any other byte as '=' and two
upper-case hexadecimal digits; a space or tab that is the last byte escaped; a soft line break '=' CR LF after the byte written once the
column reaches 73, except among the last three bytes, and after the third-last byte when the column then exceeds 71; a space or tab
escaped where a soft line break follows it), and the result is read back as a US-ASCII String.

facade_variant: V1 (state as parameters). state_passed: the String, the default charset read with getDefaultCharset() (the private
field charset; the getter is kept so that an override still applies) and the private static field PRINTABLE_CHARS (BitSet), handed to
hop 1; no field is written, no write-back. The facade body is the original guard plus one call to hop 1. No visibility is widened, no
type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The facade's computation calls no
private method of its class (it calls encode(String, String) and getDefaultCharset()), so V4 does not apply; the chain re-implements the
algorithm of the public static encodeQuotedPrintable(BitSet, byte[]) without calling or copying any private helper of the class: the octet
is taken unsigned with & 0xFF and the escape digits come from the public Hex.encodeHex(byte[], boolean).

Redistribution of the computation: the per-byte core (the written form of each byte, including the end of the data) is in the gold, which
writes the quoted-printable form WITHOUT soft line breaks, one unit per byte; the placement of soft line breaks is a separate step in hop 2,
which splits the gold's output into lines (column rule, the last-three-units rule) and escapes a raw space or tab that a soft line break
follows (the codec's convention for the bytes it places a soft line break after). Hop 2 never places a soft line break after the last
unit, so the end of the gold's output is the end of the final encoded line.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Codec-11-probe3 of the fixture, the first statement of
encode(String) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.codec.net.QuotedPrintableCodecTest::testUltimateSoftBreak`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at QuotedPrintableCodec.encode(QuotedPrintableCodec.java:337), called from QuotedPrintableCodecTest.java:326. The facade is
reached directly by the trigger.

Hosts (host_mode = "largest5"; bridge7_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 language.DoubleMetaphone  1105 lines  printableForm   plumbing: String -> bytes in the charset (unsupported charset ->
                                                              EncoderException), result bytes -> US-ASCII String
  hop 2 binary.Base64              758 lines  printableLines  placement: soft line breaks over the encoded units (a raw space or tab
                                                              that a soft line break follows is escaped)
  hop 3 language.bm.Rule           618 lines  printableRun    aggregation: creates the buffer for the unbroken form and returns its bytes
  hop 4 digest.DigestUtils         582 lines  writePrintable  pass-through
  hop 5 language.bm.PhoneticEngine 511 lines  appendPrintable GOLD: one pass over the bytes deciding, per byte, its written form
Host newline counts 1105, 758, 618, 582, 511; the smallest host (and the gold host) has 511 lines (C10F addendum section 1: hosts under
1500 lines are expected in this regime).
The correct configuration returns the original result for every input of at least three bytes (checked against a Python port of
encodeQuotedPrintable on all test inputs and on 300000 random byte strings of 3 to 170 bytes over an alphabet rich in space, tab, '=',
CR, LF, NUL and high bytes: no difference). For fewer than three bytes the original fails with ArrayIndexOutOfBoundsException
(getUnsignedOctet(bytes.length - 3)); the chain encodes such input. No test encodes such input.

Fault (one-line omission of a special-case step in the gold): the end-of-data rule for a space or tab is dropped from the gold's decision
(`if (printable.get(b) && !(i + 1 == input.length && (b == ' ' || b == '\\t'))) {` becomes `if (printable.get(b)) {`), so a space or tab
that is the last byte is written as it is. The gold then reads as the ordinary routine "write the printable bytes as they are, escape the
others". Trigger: the EXISTING test QuotedPrintableCodecTest::testUltimateSoftBreak; its first assertion, assertEquals("...There is no end
to i=\\r\\nt=09", qpcodec.encode("...There is no end to it\\t")), fails with expected:<...t[=09]> but was:<...t[\\t]> (the trailing tab is
written raw). It is the only test that encodes data ending in a space or tab; the variant's output equals the original's on every other
test input (Python port: only the four inputs of testUltimateSoftBreak differ), and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it writes the bytes "in the quoted-printable form, without soft line breaks": printable
bytes as they are, the others escaped) and is silent on whitespace and on the end of the data. A quoted-printable line must not end in a
space or tab (RFC 1521 rule #3, cited by the class javadoc; RFC 2045 6.7 (3)); the end of the gold's output is the end of the last
encoded line (no soft line break is ever placed after the last unit), so the variant's output "...t\\t" ends the encoded text with a raw
tab and the contract is violated on the trigger input. The convention is pinned outside the gold: the intact sibling
QuotedPrintableCodec.encodeQuotedPrintable(BitSet, byte[]) does the same step ("rule #3: trailing whitespace shall be encoded":
`!printable.get(b) || (i > bytes.length - 2 && isWhitespace(b))`) and is used in production by QCodec.doEncoding and by
QuotedPrintableCodec.encode(byte[]) / encode(String, String); passing tests: testTrailingSpecial (through the chain: a tab before a soft
line break is escaped, "ta=09=\\r\\nbs"), testFinalBytes (through the chain: a space with no line end after it stays as it is),
testUTF8RoundTrip and testEncodeUrlWithNullBitSet (the sibling path).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: input bounds the loop and supplies every byte; printable decides the written form; output receives every write.
  T2 absent: i is the loop cursor; b and digits are read by writes; the raw/escaped branches write different bytes.
  T3 absent: space and tab are both treated at the end of the data, which is the only line end the gold's output has (the gold writes no
     soft line breaks); both escape digits are written; no class named in the gold's text is handled in part.
  T4 absent: 'in the quoted-printable form, without soft line breaks' (no soft line break is written), 'as it is if it may be, and
     otherwise as an equals sign followed by the two hexadecimal digits of its value' and the @param clauses are met by lines of the body.
 Variant gold (javadoc, signature, the loop, `if (printable.get(b))`, the raw/escaped writes):
  T1 absent: input, printable and output each change the output; none is only argument-checked.
  T2 absent: i advances; b and digits reach writes; the if/else has two different effects; no local is frozen or dead.
  T3 absent: the gold has no whitespace, line-end or end-of-data treatment at all ('No member handled' for any such set); the gold names
     no line end besides its own end (it writes no soft line breaks); printable and non-printable bytes are both handled; both escape
     digits are written.
  T4 absent: 'in the quoted-printable form' is a general description; 'without soft line breaks' is met; 'as it is if it may be,
     and otherwise ... two hexadecimal digits of its value' is met ('may be' = in printable, as the @param says); no inline comment;
     identifiers (b, digits, printable) name nothing the body does not meet.

Single owner: only the gold decides the written form of a byte of the data; hops 1, 3 and 4 pass the data along, and hop 2 only places
soft line breaks and escapes a raw space or tab that one of its soft line breaks follows, copying every other unit as it is (it never
places a soft line break after the last unit). The gold writes the last unit, so once it has written a trailing tab as it is, '=09' can
appear only if a caller rewrites the gold's output or replaces the gold. Declared alternatives (G9): hop 1 trims the String before
encoding; hop 2 also allows a soft line break after the last two units; hop 2 counts every third-last unit as an escape. None makes the
trigger pass.
Recorded bypasses (checked on the variant in scratch copies):
 B-0 the facade (its original body) or hop 2 (`return org.apache.commons.codec.net.QuotedPrintableCodec.encodeQuotedPrintable(printable,
     data);`) uses the intact sibling encoder, discarding the rest of the chain including the gold.
 B-1 hop 2 also escapes a raw space or tab that is the last unit (`if (breakAfter && blank)` -> `if ((breakAfter || unit == units - 1) &&
     blank)`): it rewrites the unit the gold wrote (a second implementation of the gold's per-byte decision for the last byte) and breaks
     hop 2's documented rule that every unit other than a space or tab followed by a soft line break is copied as it is.
 B-2 hop 1 or hop 3 rewrites the last character of the gold's output with a regular expression (" \\z" -> "=20", "\\t\\z" -> "=09"),
     overwriting the byte the gold wrote.

Lie: the facade's javadoc claims the encoded length of the string is calculated first, so that the quoted-printable form is written into
an array of exactly that size; no step of the chain calculates the encoded length or sizes an array by it (each step writes into a growing
ByteArrayOutputStream). It names neither whitespace nor the end of the data nor any hop."""

QPC = "src/main/java/org/apache/commons/codec/net/QuotedPrintableCodec.java"
DM = "src/main/java/org/apache/commons/codec/language/DoubleMetaphone.java"
B64 = "src/main/java/org/apache/commons/codec/binary/Base64.java"
RULE = "src/main/java/org/apache/commons/codec/language/bm/Rule.java"
DU = "src/main/java/org/apache/commons/codec/digest/DigestUtils.java"
PE = "src/main/java/org/apache/commons/codec/language/bm/PhoneticEngine.java"

GOLD_TEXT = '''/**
 * Writes bytes to an output stream in the quoted-printable form, without
 * soft line breaks.
 *
 * <p>A byte is written as it is if it may be, and otherwise as an equals
 * sign followed by the two hexadecimal digits of its value.</p>
 *
 * @param input the bytes to write
 * @param printable the bytes that may be written as they are
 * @param output the stream to write to
 */
public static void appendPrintable(final byte[] input, final BitSet printable, final ByteArrayOutputStream output) {
    for (int i = 0; i < input.length; i++) {
        final int b = input[i] & 0xFF;
        if (printable.get(b) && !(i + 1 == input.length && (b == ' ' || b == '\\t'))) {
            output.write(b);
        } else {
            final char[] digits = Hex.encodeHex(new byte[] {(byte) b}, false);
            output.write('=');
            output.write(digits[0]);
            output.write(digits[1]);
        }
    }
}'''

HOP1 = '''/**
 * Encodes a string into its quoted-printable form, using the given
 * charset.
 *
 * <p>The string is read as bytes in the given charset, and the encoded
 * bytes are read back as a US-ASCII string.</p>
 *
 * @param value the string to encode, not null
 * @param charset the charset of the string
 * @param printable the bytes that may be written as they are
 * @return the quoted-printable string
 * @throws EncoderException if the charset is not supported
 */
public static String printableForm(String value, String charset, BitSet printable) throws EncoderException {
    try {
        return StringUtils.newStringUsAscii(Base64.printableLines(value.getBytes(charset), printable));
    } catch (UnsupportedEncodingException e) {
        throw new EncoderException(e.getMessage(), e);
    }
}'''

HOP2 = '''/**
 * Encodes bytes into the quoted-printable form, split into lines by soft
 * line breaks.
 *
 * <p>The bytes are first encoded in the quoted-printable form without soft
 * line breaks, one unit per byte: either the byte as it is, or an equals
 * sign followed by two hexadecimal digits. A soft line break, an equals
 * sign followed by a carriage return and a line feed, is then written after
 * each unit, other than the last three, that starts at column 73 or later,
 * and after the third-last unit if that unit, a space or tab counted as its
 * escape, ends after column 70. A space or tab that a soft line break
 * follows is written as an equals sign followed by its two hexadecimal
 * digits; every other unit is copied as it is.</p>
 *
 * @param data
 *            the bytes to encode, not null
 * @param printable
 *            the bytes that may be written as they are
 * @return a new array holding the quoted-printable bytes
 */
public static byte[] printableLines(byte[] data, BitSet printable) {
    final byte[] text = Rule.printableRun(data, printable);
    final int units = data.length;
    final ByteArrayOutputStream lines = new ByteArrayOutputStream();
    int column = 1;
    for (int j = 0, unit = 0; j < text.length; unit++) {
        final int width = text[j] == '=' ? 3 : 1;
        final boolean blank = text[j] == ' ' || text[j] == '\\t';
        final boolean breakAfter;
        if (unit < units - 3) {
            breakAfter = column >= 73;
        } else if (unit == units - 3) {
            breakAfter = column + (blank ? 3 : width) > 71;
        } else {
            breakAfter = false;
        }
        if (breakAfter && blank) {
            final char[] digits = Hex.encodeHex(new byte[] {text[j]}, false);
            lines.write('=');
            lines.write(digits[0]);
            lines.write(digits[1]);
            column += 3;
        } else {
            lines.write(text, j, width);
            column += width;
        }
        if (breakAfter) {
            lines.write('=');
            lines.write('\\r');
            lines.write('\\n');
            column = 1;
        }
        j += width;
    }
    return lines.toByteArray();
}'''

HOP3 = '''/**
 * Encodes bytes into a new array in the quoted-printable form, without
 * soft line breaks.
 *
 * @param data
 *            the bytes to encode, not null
 * @param printable
 *            the bytes that may be written as they are
 * @return a new array holding the encoded bytes
 */
public static byte[] printableRun(final byte[] data, final BitSet printable) {
    final ByteArrayOutputStream run = new ByteArrayOutputStream();
    DigestUtils.writePrintable(data, printable, run);
    return run.toByteArray();
}'''

HOP4 = '''/**
 * Writes bytes to an output stream in the quoted-printable form, without
 * soft line breaks.
 *
 * @param data
 *            the bytes to write
 * @param printable
 *            the bytes that may be written as they are
 * @param output
 *            the stream to write to
 */
public static void writePrintable(byte[] data, BitSet printable, ByteArrayOutputStream output) {
    PhoneticEngine.appendPrintable(data, printable, output);
}'''

DESIGN = {
 "instance": "Codec-11", "project": "Codec", "bug_id": 11, "seed": 4220,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "pString, the default charset (getDefaultCharset(), i.e. the private field charset) and the private static field "
                 "PRINTABLE_CHARS, passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [1105, 758, 618, 582, 511],
 "reachability_probe": "encode(String) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Codec-11-probe3: QuotedPrintableCodecTest::testUltimateSoftBreak fails with "
                       "PROBE-REACHED at QuotedPrintableCodec.encode(QuotedPrintableCodec.java:337)",
 "facade": {"file": QPC, "class": "org.apache.commons.codec.net.QuotedPrintableCodec", "method": "encode", "near_line": 336},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/codec/net/QuotedPrintableCodecTest.java",
             "test_class": "org.apache.commons.codec.net.QuotedPrintableCodecTest", "test_method": "testUltimateSoftBreak"},
 "expected_signature": "t[=09]> but was:<",
 "gold": {"method": "appendPrintable", "text": GOLD_TEXT,
          "fault": {"old": "            if (printable.get(b) && !(i + 1 == input.length && (b == ' ' || b == '\\t'))) {",
                    "new": "            if (printable.get(b)) {"}},
 "chain": {
   "facade_body": "if (pString == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.codec.language.DoubleMetaphone.printableForm(pString, getDefaultCharset(), "
                  "PRINTABLE_CHARS);",
   "lie": "The encoded length of the string is calculated first, so that the quoted-printable form is written into an array of "
          "exactly that size.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "printableForm",
      "imports": ["java.io.UnsupportedEncodingException", "java.util.BitSet",
                  "org.apache.commons.codec.binary.Base64", "org.apache.commons.codec.binary.StringUtils"], "text": HOP1},
     {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "printableLines",
      "imports": ["java.io.ByteArrayOutputStream", "java.util.BitSet",
                  "org.apache.commons.codec.language.bm.Rule"], "text": HOP2},
     {"file": RULE, "class": "org.apache.commons.codec.language.bm.Rule", "method": "printableRun",
      "imports": ["java.io.ByteArrayOutputStream", "java.util.BitSet",
                  "org.apache.commons.codec.digest.DigestUtils"], "text": HOP3},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "writePrintable",
      "imports": ["java.io.ByteArrayOutputStream", "java.util.BitSet",
                  "org.apache.commons.codec.language.bm.PhoneticEngine"], "text": HOP4},
     {"file": PE, "class": "org.apache.commons.codec.language.bm.PhoneticEngine", "method": "appendPrintable",
      "imports": ["java.io.ByteArrayOutputStream", "java.util.BitSet", "org.apache.commons.codec.binary.Hex"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.net.QuotedPrintableCodec::encodeQuotedPrintable",
              "org.apache.commons.codec.net.QCodec::doEncoding"],
 "ownership_reason": "Only the gold decides the written form of each byte of the data, including the last one: it writes the "
                     "quoted-printable form without soft line breaks, one unit per byte. Hops 1, 3 and 4 pass the data along; hop 2 "
                     "only places soft line breaks over the gold's units (never after the last unit) and escapes a raw space or tab "
                     "that one of its soft line breaks follows, copying every other unit as it is. The end of the gold's output is "
                     "therefore the end of the last encoded line, and once the gold has written the last byte, a tab, as it is, the "
                     "escape '=09' can appear only if a caller rewrites the gold's output or replaces the gold. The gold's javadoc "
                     "promises the quoted-printable form, in which a line must not end in a space or tab (RFC 1521 rule #3, cited by "
                     "the class javadoc); the variant ends the encoded text with a raw tab. The convention is pinned outside the "
                     "gold: the intact sibling QuotedPrintableCodec.encodeQuotedPrintable(BitSet, byte[]) does the same step "
                     "('rule #3: trailing whitespace shall be encoded': a space or tab that is the last byte is escaped) and is used "
                     "in production by QCodec.doEncoding and by QuotedPrintableCodec.encode(byte[]) and encode(String, String); "
                     "testTrailingSpecial (through the chain: a tab followed by a soft line break is escaped) and testFinalBytes "
                     "(through the chain: a space with no line end after it stays as it is) pass, as do testUTF8RoundTrip and "
                     "testEncodeUrlWithNullBitSet on the sibling path.",
 "ownership_tests": ["org.apache.commons.codec.net.QuotedPrintableCodecTest::testTrailingSpecial",
                     "org.apache.commons.codec.net.QuotedPrintableCodecTest::testFinalBytes",
                     "org.apache.commons.codec.net.QuotedPrintableCodecTest::testUTF8RoundTrip",
                     "org.apache.commons.codec.net.QuotedPrintableCodecTest::testEncodeUrlWithNullBitSet"],
 "compensating": {
   "chain": [
     {"file": DM, "old": "return StringUtils.newStringUsAscii(Base64.printableLines(value.getBytes(charset), printable));",
      "new": "return StringUtils.newStringUsAscii(Base64.printableLines(value.trim().getBytes(charset), printable));",
      "why": "hop 1 trims the string before encoding it"},
     {"file": B64, "old": "            breakAfter = false;",
      "new": "            breakAfter = column >= 73;",
      "why": "hop 2 also allows a soft line break after the last two units"},
     {"file": B64, "old": "breakAfter = column + (blank ? 3 : width) > 71;",
      "new": "breakAfter = column + 3 > 71;",
      "why": "hop 2 counts every third-last unit as an escape"},
   ],
 },
 "host_notes": "host_mode largest5 (bridge7_tasks.json: the paired static instance's hosts, hosts_hop_order, in that order; none "
               "substituted, none drawn by this builder): language.DoubleMetaphone (hop 1, 1105 lines), binary.Base64 (hop 2, 758), "
               "language.bm.Rule (hop 3, 618), digest.DigestUtils (hop 4, 582), language.bm.PhoneticEngine (hop 5, gold, 511; the "
               "smallest host). All five are public concrete top-level classes in which a public static method compiles; the facade's "
               "class QuotedPrintableCodec is not a host. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) "
               "with seed 4220 + 100 + i, as mr3_spec.py inserts them: hop 1 after getMaxCodeLen (seed 4320), hop 2 after isBase64 "
               "(4321), hop 3 after getPattern (4322), hop 4 after sha384(String) (4323), hop 5 after encode(String) (4324). The "
               "facade calls hop 1 by its fully-qualified name; each hop imports the next host and java.util.BitSet / "
               "java.io.ByteArrayOutputStream as needed; hop 2 uses binary.Hex from its own package; the gold imports binary.Hex. "
               "Base64's inherited instance field 'buffer' is not used (hop 2's local is named 'lines').",
}
