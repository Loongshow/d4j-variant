"""Main run Codec-8__i (cell C10i, batch 7: the paired static/instance bridge; the C10 recipe with an INSTANCE-method facade, on the
fixed checkout of Defects4J Codec-8; the real bug modified Base64 and Base64InputStream, and the facade is in Base64). The paired
static-facade instance is MR-Codec-8 (facade Base64.encodeBase64); none of its files were opened (addendum section 2).

Facade: Base64.decode(byte[]) (instance method, public, line 725; allowed target of bridge7_tasks.json, BATCH7_PREREGISTRATION.md
row 192; facade_reuse_of = null; not the paired static facade, and Base64 is not one of the five hosts).
Original computation: reset() clears the object's streaming state; a null or empty array is returned as is; the package-private
streaming decoder decode(byte[], int, int) is run over the whole array and once more with -1 (end of data), and the octets it
buffered are copied out with readResults into an array of their exact length. The streaming decoder stops at the first pad
character '=', skips every byte that is not a Base64 character (`if (b >= 0 && b < DECODE_TABLE.length)` and then
`DECODE_TABLE[b] >= 0`), turns each group of four characters into three octets and a final group of two or three characters into
one or two octets. Production callers: decode(String), decode(Object), decodeBase64(String), decodeBase64(byte[]), decodeInteger,
and net.BCodec (through decodeBase64).

facade_variant: V1 (state as parameters). The computation needs no public method of the receiver (its helpers reset, the streaming
decode(byte[], int, int) and readResults are private or package-private, so V2 would carry nothing), and it reads no instance field
that depends on the object's configuration: decoding is the same in every mode. The only state the chain needs is the class's
private static lookup table DECODE_TABLE (Base64 characters to six-bit values, -1 for the other codes in its bounds), which the
facade reads inside its class and passes to hop 1.
state_passed: DECODE_TABLE (private static final byte[] of Base64) as the second argument of hop 1, next to the caller's array; no
write-back. The streaming fields (buffer, pos, readPos, modulus, x, eof) that the original reset and then consumed are not used by
the chain and are no longer written by this method; they are read only by the streaming methods, which Base64InputStream and
Base64OutputStream call on Base64 objects of their own (never after decode(byte[])). No visibility is widened, no type is added,
the facade's signature and modifiers are unchanged.
Facade body: the original guard (`if (pArray == null || pArray.length == 0) { return pArray; }`) plus one call
`return org.apache.commons.codec.language.DoubleMetaphone.decodeBase64Text(pArray, DECODE_TABLE);`.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Codec-8-probe/w of the fixture,
the first statement of Base64.decode(byte[]) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t org.apache.commons.codec.binary.Base64Test::testBase64`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at Base64.decode(Base64.java:726) called from Base64.decode(Base64.java:715) (decode(String)) from
Base64Test.testBase64(Base64Test.java:79). Full suite with the probe: 37 failing tests (36 with PROBE-REACHED in the trace, and
Base64Test::testNonBase64Test, which catches the probe's exception and fails its own assertion). The facade is reached by existing
tests directly and through decodeBase64.

Hosts (host_mode = "largest5"; the paired static instance's hosts, bridge7_tasks.json hosts_hop_order, used in that order; none
substituted):
  hop 1 language.DoubleMetaphone      1105 lines  decodeBase64Text        pass-through
  hop 2 digest.DigestUtils             582 lines  decodeBase64Octets      placement: a buffer with room for three octets per group
                                                                          of four characters and two more, then the octets copied
                                                                          into an array of their exact length
  hop 3 language.ColognePhonetic       492 lines  decodeBase64Into        pass-through
  hop 4 language.Metaphone             407 lines  fillBase64Octets        pass-through
  hop 5 net.QuotedPrintableCodec       387 lines  decodeBase64Characters  GOLD: one pass over the bytes, deciding per byte between
                                                                          the end of the data (pad), a Base64 character (six more
                                                                          bits, an octet whenever eight bits are held) and any
                                                                          other byte (passed over)
Host newline counts 1105, 582, 492, 407, 387; the smallest host (and the gold host) has 387 lines (below 1500, expected under
largest5, BUILD_BRIEF_C10F_ADDENDUM section 1). The correct configuration returns exactly the original octets for every input: the
bit accumulator emits an octet at the 2nd, 3rd and 4th character of each group, the same octets in the same order as the original
three-octet write, and a final group of two or three characters leaves 12 or 18 bits, which give the same one or two octets as the
original final step (checked against a transcription of the original decoder on 200000 random inputs with Base64 characters, pads,
negative bytes and bytes above the table).

Fault (omission of a decision step in the gold): the bound test that sends codes outside the lookup table to -1 is dropped, so the
gold indexes the table with every byte it reads (`int sextet = c >= 0 && c < table.length ? table[c] : -1;` becomes
`int sextet = table[c];`). For codes 0-122 nothing changes (the table marks the non-Base64 ones with -1), but a byte above 122 or a
negative byte (any non-ASCII octet) raises ArrayIndexOutOfBoundsException instead of being passed over, unless a pad character comes
first. Trigger: the EXISTING test Base64Test::testBase64, which decodes "SGVsbG{eeeeee}8gV29ybGQ=" (six e-acute, UTF-8, "bogus
characters to decode (to skip actually)") with decode(String): '{' (123) is the first byte outside the table and the test fails with
java.lang.ArrayIndexOutOfBoundsException (Index 123 out of bounds for length 123). It is the only test that newly fails: every other
input the suite decodes through the facade holds only codes 0-122 before its first pad (Base64Test::testCodec68 decodes
{'n', 'A', '=', '=', 0x9c}, where the pad ends the data before 0x9c); the streaming decoder used by Base64InputStream is untouched.

The gold's javadoc states the idiomatic contract (it decodes the Base64 characters found in an array of bytes, six bits per
character, an octet per eight bits, up to the first pad) and is silent on codes outside the table; the variant throws instead of
decoding the Base64 characters of the trigger's input. The convention (bytes that are not Base64 characters, in or out of the
table's bounds, are skipped and never throw) is pinned outside the gold: Base64.isBase64 (`octet >= 0 && octet <
DECODE_TABLE.length && DECODE_TABLE[octet] != -1`) with Base64Test::testIsArrayByteBase64 (Byte.MIN_VALUE, -125, -10 and
Byte.MAX_VALUE are rejected without an exception); the streaming decoder Base64.decode(byte[], int, int), whose javadoc says it
"Ignores all non-base64 characters" and whose code makes the same bound test before the lookup, used in production by
Base64InputStream.read(byte[], int, int); DECODE_TABLE's javadoc ("Characters that are not in the Base64 alphabet but fall within the
bounds of the array are translated to -1"); Base64Test::testNonBase64Test ("RFC 2045 requires that all non base64 character be
discarded, an exception should not have been thrown"), ::testIgnoringNonBase64InDecode and ::testCodec68 (CODEC-68: no
ArrayIndexOutOfBoundsException on non-Base64 bytes), all passing on the variant.

Single owner: only the gold reads the bytes of the text and decides, per byte, whether it ends the data, adds six bits or is passed
over; hops 1, 3 and 4 pass the text, the table and the buffer along unchanged and hop 2 only sizes the buffer and trims the result.
Once the gold indexes the table with a code outside it, the exception is raised inside the gold, before any caller sees a result, so
no caller can recover the octets; a caller can only avoid it by removing or rewriting the bytes before the gold reads them.
Declared alternatives (G9): hop 2 gives the buffer one octet per character; hop 1 widens the table to 256 entries
(Arrays.copyOf pads with zeros, so '{' would decode as 'A', and negative bytes still fall outside); hop 4 reduces the text to
US-ASCII first (non-ASCII bytes become '?', which the table marks with -1, but '{' stays). Each leaves the trigger failing.
Recorded bypasses (edits that move the gold's per-byte decision into another implementation, not repairs of the chain):
 B-1 a hop rewrites the text so that only Base64 characters and the pad remain, with a second copy of the alphabet as a regular
     expression, e.g. at hop 4 `return QuotedPrintableCodec.decodeBase64Characters(org.apache.commons.codec.binary.StringUtils
     .getBytesUtf8(org.apache.commons.codec.binary.StringUtils.newStringUtf8(text).replaceAll("[^A-Za-z0-9+/=_-]", "")), table,
     buffer);`: the gold then never sees a byte it would pass over, so its table test for such bytes becomes dead; the alphabet is
     decided twice. Checked at hop 4 on the variant in a scratch copy (/private/tmp/d4j-mi-Codec-8-byp): trigger passes, full
     suite 0 failing tests.
 B-0 a hop decodes the text itself (a second decoding loop), making the rest of the chain, including the gold, dead.

Lie: the facade's javadoc claims the length of the result is computed in advance from the input length and the number of pad
characters at its end, and the octets are written directly into an array of exactly that length; the chain counts no pad characters,
writes into a buffer with spare room and copies the octets out afterwards. It names neither the table, nor its bounds, nor any byte
class, nor any hop.

No pre-edit: the facade's original javadoc ("Decodes a byte[] containing characters in the Base64 alphabet.") stays true of the
chain.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, locals bits/held/count, one loop with the pad test, the bounded lookup, the -1 test and the
 eight-bit emission, the return):
  T1 absent: text is iterated and read, table is read by the lookup and its length bounds it, buffer receives every octet; none is
     only argument-checked.
  T2 absent: bits, held and count are assigned inside the loop and read (bits and held by the octet write, count as the write
     position and the return); c and sextet are read; the pad test breaks, the ternary has two live outcomes, the -1 test and the
     eight-bit test decide live statements.
  T3 absent: both ends of the table's index range are tested (c >= 0 and c < table.length); the three per-byte cases (pad, Base64
     character, other entry) are all treated; the gold names no class it handles in part.
  T4 absent: 'the Base64 characters found in an array of bytes', 'Each Base64 character gives six bits', 'every eight bits collected
     give one octet', 'four characters give three octets', 'Decoding ends at the first pad character' and '@return the number of
     octets written' are each met by lines of the body; the @param table phrase is a caller precondition the facade's DECODE_TABLE
     meets.
 Variant gold (the same text with `int sextet = table[c];`):
  T1 absent: text, table and buffer each change the result (table by the lookup, now without its length); none is only
     argument-checked.
  T2 absent: no dead or frozen local (bits, held, count are moved in the loop and read; c is read by the pad test and the lookup;
     sextet is read); no dead decision (pad break, -1 test and eight-bit test each decide live statements).
  T3 absent: the variant tests no end of the table's index range at all ('No member handled', not one of two); the per-byte cases
     the gold's text names (the pad, a Base64 character, an entry of -1) are all treated; no pair half, range end or named class is
     left half-treated.
  T4 absent: every phrase above is still met by a line of the body; the text names no rule about codes outside the table, no
     'any byte', 'skipped' or 'never throws' clause, and no bound; the @param table phrase ('holding the six-bit value of each
     Base64 character and -1 in every other entry') is a caller precondition, not a statement of what the gold checks."""

B64 = "src/java/org/apache/commons/codec/binary/Base64.java"
DM = "src/java/org/apache/commons/codec/language/DoubleMetaphone.java"
DU = "src/java/org/apache/commons/codec/digest/DigestUtils.java"
CP = "src/java/org/apache/commons/codec/language/ColognePhonetic.java"
MP = "src/java/org/apache/commons/codec/language/Metaphone.java"
QP = "src/java/org/apache/commons/codec/net/QuotedPrintableCodec.java"

GOLD_TEXT = '''/**
 * Decodes the Base64 characters found in an array of bytes into octets. Each Base64 character gives six bits, and every
 * eight bits collected give one octet, so four characters give three octets. Decoding ends at the first pad character.
 *
 * @param text
 *                  array of bytes to decode
 * @param table
 *                  lookup table indexed by character code, holding the six-bit value of each Base64 character and -1
 *                  in every other entry
 * @param buffer
 *                  the buffer that receives the octets
 * @return the number of octets written
 */
public static int decodeBase64Characters(byte[] text, byte[] table, byte[] buffer) {
    int bits = 0;
    int held = 0;
    int count = 0;
    for (int i = 0; i < text.length; i++) {
        int c = text[i];
        if (c == '=') {
            break;
        }
        int sextet = c >= 0 && c < table.length ? table[c] : -1;
        if (sextet != -1) {
            bits = (bits << 6) | sextet;
            held += 6;
            if (held >= 8) {
                held -= 8;
                buffer[count++] = (byte) (bits >> held);
            }
        }
    }
    return count;
}'''

HOP1 = '''/**
 * Decodes Base64 text into octets.
 * @param text The bytes to decode
 * @param table The lookup table indexed by character code, holding the six-bit value
 *        of each Base64 character and -1 in every other entry
 * @return The decoded octets
 */
public static byte[] decodeBase64Text(byte[] text, byte[] table) {
    return DigestUtils.decodeBase64Octets(text, table);
}'''

HOP2 = '''/**
 * Decodes Base64 text into octets.
 * <p>
 * The octets are first written into a buffer with room for three octets per group of four characters and two more for
 * a final shorter group, and are then copied into an array of their exact length.
 * </p>
 *
 * @param text
 *            The bytes to decode
 * @param table
 *            The lookup table indexed by character code, holding the six-bit value of each Base64 character and -1
 *            in every other entry
 * @return The decoded octets
 */
public static byte[] decodeBase64Octets(byte[] text, byte[] table) {
    byte[] buffer = new byte[text.length / 4 * 3 + 2];
    int length = ColognePhonetic.decodeBase64Into(text, table, buffer);
    byte[] octets = new byte[length];
    System.arraycopy(buffer, 0, octets, 0, length);
    return octets;
}'''

HOP3 = '''/**
 * Decodes Base64 text into the given buffer.
 *
 * @param text the bytes to decode
 * @param table the lookup table indexed by character code, holding the six-bit
 *        value of each Base64 character and -1 in every other entry
 * @param buffer the buffer that receives the octets
 * @return the number of octets written
 */
public static int decodeBase64Into(byte[] text, byte[] table, byte[] buffer) {
    return Metaphone.fillBase64Octets(text, table, buffer);
}'''

HOP4 = '''/**
 * Decodes Base64 text into the given buffer.
 *
 * @param text the bytes to decode
 * @param table the lookup table indexed by character code, holding the six-bit
 *        value of each Base64 character and -1 in every other entry
 * @param buffer the buffer that receives the octets
 * @return the number of octets written
 */
public static int fillBase64Octets(byte[] text, byte[] table, byte[] buffer) {
    return QuotedPrintableCodec.decodeBase64Characters(text, table, buffer);
}'''

DESIGN = {
 "instance": "Codec-8", "project": "Codec", "bug_id": 8, "seed": 6049,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "decode", "near_line": 725},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/codec/binary/Base64Test.java",
             "test_class": "org.apache.commons.codec.binary.Base64Test", "test_method": "testBase64"},
 "expected_signature": "java.lang.ArrayIndexOutOfBoundsException",
 "gold": {"method": "decodeBase64Characters", "text": GOLD_TEXT,
          "fault": {"old": "            int sextet = c >= 0 && c < table.length ? table[c] : -1;",
                    "new": "            int sextet = table[c];"}},
 "chain": {
   "facade_body": "if (pArray == null || pArray.length == 0) {\n"
                  "            return pArray;\n"
                  "        }\n"
                  "        return org.apache.commons.codec.language.DoubleMetaphone.decodeBase64Text(pArray, DECODE_TABLE);",
   "lie": "The length of the result is computed in advance from the length of the input and the number of pad characters at "
          "its end, and the octets are written directly into an array of exactly that length.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "decodeBase64Text",
      "imports": ["org.apache.commons.codec.digest.DigestUtils"], "text": HOP1},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "decodeBase64Octets",
      "imports": ["org.apache.commons.codec.language.ColognePhonetic"], "text": HOP2},
     {"file": CP, "class": "org.apache.commons.codec.language.ColognePhonetic", "method": "decodeBase64Into",
      "imports": [], "text": HOP3},
     {"file": MP, "class": "org.apache.commons.codec.language.Metaphone", "method": "fillBase64Octets",
      "imports": ["org.apache.commons.codec.net.QuotedPrintableCodec"], "text": HOP4},
     {"file": QP, "class": "org.apache.commons.codec.net.QuotedPrintableCodec", "method": "decodeBase64Characters",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.binary.Base64::isBase64",
              "org.apache.commons.codec.binary.Base64::isArrayByteBase64",
              "org.apache.commons.codec.binary.Base64InputStream::read"],
 "ownership_reason": "Only the gold reads the bytes of the text and decides, per byte, whether it ends the data (the pad), adds "
                     "six bits (a Base64 character) or is passed over: hops 1, 3 and 4 pass the text, the lookup table and the "
                     "buffer along unchanged and hop 2 only sizes the buffer and trims the result to the octets written. The "
                     "gold's javadoc promises to decode the Base64 characters found in an array of bytes; on the trigger's "
                     "input ('{' and UTF-8 e-acute among Base64 characters) the gold indexes the lookup table with a code "
                     "beyond it and throws ArrayIndexOutOfBoundsException inside itself, before any caller sees a result. The "
                     "convention that bytes which are not Base64 characters are skipped whether or not they fall within the "
                     "table's bounds, and never cause an exception, is pinned outside the gold: Base64.isBase64 tests "
                     "'octet >= 0 && octet < DECODE_TABLE.length' before the lookup and Base64Test testIsArrayByteBase64 "
                     "rejects Byte.MIN_VALUE, -125, -10 and Byte.MAX_VALUE without an exception; the streaming decoder "
                     "Base64.decode(byte[], int, int), used in production by Base64InputStream.read(byte[], int, int), makes "
                     "the same bound test before its lookup and documents that it 'Ignores all non-base64 characters'; "
                     "DECODE_TABLE's javadoc says only characters 'within the bounds of the array' are translated to -1; "
                     "Base64Test testNonBase64Test ('RFC 2045 requires that all non base64 character be discarded, an "
                     "exception should not have been thrown'), testIgnoringNonBase64InDecode and testCodec68 (CODEC-68, no "
                     "ArrayIndexOutOfBoundsException on non-Base64 bytes) pass.",
 "ownership_tests": ["org.apache.commons.codec.binary.Base64Test::testIsArrayByteBase64",
                     "org.apache.commons.codec.binary.Base64Test::testNonBase64Test",
                     "org.apache.commons.codec.binary.Base64Test::testIgnoringNonBase64InDecode",
                     "org.apache.commons.codec.binary.Base64Test::testCodec68"],
 "compensating": {
   "chain": [
     {"file": DU, "old": "byte[] buffer = new byte[text.length / 4 * 3 + 2];",
      "new": "byte[] buffer = new byte[text.length];",
      "why": "hop 2 gives the buffer room for one octet per character"},
     {"file": DM, "old": "return DigestUtils.decodeBase64Octets(text, table);",
      "new": "return DigestUtils.decodeBase64Octets(text, java.util.Arrays.copyOf(table, 256));",
      "why": "hop 1 widens the lookup table to 256 entries"},
     {"file": MP, "old": "return QuotedPrintableCodec.decodeBase64Characters(text, table, buffer);",
      "new": "return QuotedPrintableCodec.decodeBase64Characters(org.apache.commons.codec.binary.StringUtils.getBytesUsAscii("
             "org.apache.commons.codec.binary.StringUtils.newStringUsAscii(text)), table, buffer);",
      "why": "hop 4 reduces the text to US-ASCII before the gold reads it"},
   ],
 },
 "host_notes": "host_mode largest5 (bridge7_tasks.json; the paired static instance's hosts, hosts_hop_order, used in that order, "
               "none substituted): language.DoubleMetaphone (hop 1, 1105 lines), digest.DigestUtils (hop 2, 582), "
               "language.ColognePhonetic (hop 3, 492), language.Metaphone (hop 4, 407), net.QuotedPrintableCodec (hop 5, gold, "
               "387; the smallest host). All five are public concrete top-level classes in which a public static method "
               "compiles. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 6049 + 100 + i, as "
               "mr3_spec.py inserts them: hop 1 after `setMaxCodeLen` (line idx 263, seed 6149), hop 2 after `md5` (the "
               "md5(String) overload, 191, 6150), hop 3 after `encode` (the encode(String) overload, 341, 6151), hop 4 after "
               "`encode` (the encode(String) overload, 381, 6152), hop 5 after the constructor `QuotedPrintableCodec(String)` "
               "(108, 6153); all in the outer class. The facade calls hop 1 by its fully-qualified name; hops 1, 2 and 4 import "
               "the next host, hop 3 calls Metaphone in its own package. The facade passes Base64's private static "
               "DECODE_TABLE as an argument (V1); no modifier changes.",
}
