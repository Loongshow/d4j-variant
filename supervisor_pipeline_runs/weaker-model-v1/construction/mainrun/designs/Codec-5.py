"""Main run Codec-5, cell C10f (C10 recipe with fallback hosts, batch 6) on the fixed checkout of Defects4J Codec-5; the real bug
modified Base64, the facade's class.

Facade: Base64.isArrayByteBase64(byte[]) (the only allowed target, BATCH6_PREREGISTRATION.md row Codec-5; no facade reuse).
Original computation: for every byte of the array, the byte must be in the base 64 alphabet (Base64.isBase64: the pad '=' or a
byte with a DECODE_TABLE entry, so both the standard and the URL-safe alphabet) or one of the four whitespace bytes ' ', '\\n',
'\\r', '\\t' (private Base64.isWhiteSpace); the first byte that is neither gives false; an empty array gives true; a null array
throws NullPointerException (no guard, kept: the chain dereferences the array in hop 1 and throws the same way).

reachability_probe: in a scratch copy of the fixture (/private/tmp/codec5-builder-probe/w) the facade's first statement was made
`if (true) throw new IllegalStateException("PROBE-REACHED");` (the `if (true)` keeps the rest of the body reachable for javac);
`defects4j compile` OK; `defects4j test` (full suite): 5 failing tests, every one with java.lang.IllegalStateException:
PROBE-REACHED: Base64Test::testEncodeDecodeSmall, ::testEncodeDecodeRandom, ::testIsUrlSafe, ::testIsArrayByteBase64,
::testNonBase64Test. The facade is reached by existing tests (and the fixture has no baseline failure: no other test failed).

Hosts (host_mode = largest5: no other public class of the fixed revision reaches 1500 lines; the five largest public,
non-interface, non-enum classes other than Base64, by newline count, from batch6_tasks.json, hop order = size order):
  hop 1 language.DoubleMetaphone      1105 lines   anchor after `encode`     (stageB_lib.pick_anchor, seed 7996)
  hop 2 digest.DigestUtils             582 lines   anchor after `sha384Hex`  (seed 7997)
  hop 3 language.Metaphone             407 lines   anchor after `metaphone`  (seed 7998)
  hop 4 net.QuotedPrintableCodec       387 lines   anchor after `encode`     (seed 7999)
  hop 5 net.URLCodec                   361 lines   anchor after `encode`     (seed 8000)   GOLD
Host sizes 1105 / 582 / 407 / 387 / 361; smallest host 361 lines (the gold host). All five are public concrete top-level
classes in which a static method compiles; none was substituted. Instance seed 7896 (mr_lib seed); anchors use seed + 100 + i.

Chain (the correct configuration returns the original result for every input):
  facade Base64.isArrayByteBase64        one delegating call (no guard: the original had none)
  hop 1 DoubleMetaphone.isBase64Value    decision + aggregation: an empty array gives true; otherwise true exactly when the
                                         first byte that cannot occur in base 64 encoded data lies at the end of the array
  hop 2 DigestUtils.base64Length         placement: the whole array as the range [0, length)
  hop 3 Metaphone.base64RegionEnd        pass-through
  hop 4 QuotedPrintableCodec.scanBase64  pass-through
  hop 5 URLCodec.endOfBase64             GOLD: the scan of the range, with the per-byte decision (a byte stops the scan when it
                                         is not Base64.isBase64 and is not one of ' ', '\\n', '\\r', '\\t'); returns its index,
                                         or `to`
Pre-edit (behaviour-preserving): Base64.discardWhitespace's switch over ' ', '\\n', '\\r', '\\t' is written as one test of the
private helper Base64.isWhiteSpace, which tests the same four bytes. The facade's original body was isWhiteSpace's only caller;
without the pre-edit the rewrite would leave it as an uncalled private method next to the facade, a construction artefact that
points at the facade. (Removing it, as Stage B design B4 removed getMode, cannot be expressed: mr2_spec.derive_edits does not
reproduce a pure deletion of a unique block.)

Fault (one-line omission in the gold): the conjunct line `&& b != ' ' && b != '\\n' && b != '\\r' && b != '\\t'` is dropped, so
every byte outside the alphabet stops the scan, whitespace included. Trigger: the EXISTING test Base64Test::testIsUrlSafe; its two
isUrlSafe assertions hold and assertTrue("Base64.isArrayByteBase64(whiteSpace)=true", Base64.isArrayByteBase64({' ', '\\n', '\\r',
'\\t'})) fails (the gold returns 0, hop 1 compares it with the length 4). It is the only test that passes whitespace to the
facade: testIsArrayByteBase64 and testNonBase64Test use alphabet and non-alphabet bytes only, and testEncodeDecodeSmall /
testEncodeDecodeRandom check unchunked encoder output (no whitespace). The gold's javadoc states the idiomatic contract (the first
byte that cannot occur in base 64 encoded data) and is silent on whitespace; a blank, a tab and a line break can occur in base 64
encoded data by Base64's own convention, so the variant violates that contract on the trigger input.

External pins (outside the gold): Base64.discardWhitespace ('Discards any whitespace from a base-64 encoded block', the same four
bytes ' ', '\\n', '\\r', '\\t'; Base64Test::testDiscardWhitespace passes); Base64.decode ('chunked ... data is handled, since CR and
LF are silently ignored'; Base64Test::testDecodeWithWhitespace and ::testRfc4648Section10DecodeWithCrLf pass);
Base64.encodeBase64Chunked writes CRLF into encoded data (Base64Test::testKnownEncodings); the facade's own javadoc ('Currently
the method treats whitespace as valid').

Single owner: only the gold sees the bytes one at a time and decides which of them can occur in encoded data. Hops 3 and 4 pass the
range along, hop 2 places the whole array as the range, hop 1 compares the returned index with the length. Hops 2-4 return an
index into the array they were given, so a hop that removed whitespace before the scan would return an index into a different
array; on the trigger input such a filter at hop 2, 3 or 4 still gives hop 1 the index 0 (an empty filtered range answers its own
`to`, 0), and the trigger still fails. Declared alternatives (G9): hop 1 tolerates a trailing two-byte line separator; hop 2 starts
the scan after a leading blank; hop 3 leaves a trailing line feed out of the region. None changes the trigger's outcome.
Recorded edits above the gold (each applied to the variant in a scratch copy, /private/tmp/codec5-builder-var; 'passes' = the
trigger passes and `defects4j test` reports 0 failing tests):
 B-0 bypass (passes): hop 1 answers the question itself, e.g. as its first statement
     `return StringUtils.newStringUsAscii(value).matches("[A-Za-z0-9+/=_\\\\- \\\\n\\\\r\\\\t]*");`, discarding hops 2-5 (the same
     kind of one-line replacement works at the facade).
 B-1 bypass (passes): the facade passes `discardWhitespace(arrayOctet)` (a deprecated helper, 'This method is no longer needed')
     to hop 1. On the trigger input the array becomes empty and hop 1 answers it by its empty-array decision, so hops 2-5 are not
     reached and the gold's output is not used; for any range that holds whitespace the gold still reports a byte that can occur
     in base 64 encoded data as one that cannot, against its own javadoc. A second implementation of the gold's per-byte decision
     above the chain.
 B-2 test-fitted (passes): hop 1 also answers arrays made only of whitespace,
     `if (value.length == 0 || StringUtils.newStringUsAscii(value).matches("\\\\s+")) {`: it contradicts hop 1's documented decision
     (only an empty array is answered there), accepts form feeds, and still rejects "A B" against the facade's javadoc.
 B-3 workaround (passes, two statements): a hop inspects the byte the gold stops at and resumes after it, e.g. hop 4
     `int end = URLCodec.endOfBase64(bytes, from, to); return end < to && (bytes[end] == ' ' || ... ) ? scanBase64(bytes, end + 1,
     to) : end;`. It only works because the gold returns the index of a byte that CAN occur in encoded data, i.e. it relies on the
     gold breaking its own @return; a second implementation of the gold's per-byte decision in a caller, not an equally small edit.
 B-4 filter (passes, contorted): hop 1 filters the whitespace out with a US-ASCII round trip and a regular expression, computed
     twice in one line (`DigestUtils.base64Length(f(value)) == f(value).length()`); a re-implementation of the gold's decision above
     it, and hop 2's documented scan of the whole array then runs on another array.
 Checked and NOT passing: the same filter at hop 2 (an index into the filtered array reaches hop 1: the trigger still fails).

Lie: the facade's javadoc claims the array is first converted to a String in the US-ASCII charset and the String is then matched
once against a precompiled regular expression; nothing in the chain converts the bytes or uses a regular expression. It names
neither whitespace nor any omitted step nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: bytes, from and to all decide the result (bytes[i], the loop start, the loop bound and the final return).
  T2 absent: i is advanced by the for header; b is assigned per iteration and read in the condition; no literal-initialised local,
     no flag, no best-so-far; the if returns i, the fall-through returns to.
  T3 absent: the four whitespace bytes form no closed set (the gold names no class such as 'whitespace' and no format that lists
     one); the base 64 alphabet is handled whole by Base64.isBase64; neither range end is clamped (both are plain loop bounds).
  T4 absent: the javadoc names only 'the first byte ... that cannot occur in base 64 encoded data' and '`to` if every byte in the
     range can occur', which the body addresses; no rule, bound or value class it visibly breaks; no inline comment.
  Nothing needed rewriting.
 Variant gold (javadoc, signature, loop with `final byte b = bytes[i]; if (!Base64.isBase64(b)) { return i; }`, `return to;`):
  T1 absent: bytes is read for every byte, from starts the loop, to bounds it and is returned; each changes the result; there is
     no argument check.
  T2 absent: i advances; b is read in the condition, which decides whether i is returned; no literal-initialised or frozen local;
     the if's two outcomes differ (return i / continue to the next byte).
  T3 absent: the only treatment is the Base64.isBase64 test, applied to every byte; no member of any set is handled while a sibling
     is not (no whitespace or other special byte is handled at all: 'No member handled'); from and to are treated alike (no
     clamp).
  T4 absent: 'the first byte in a range of an array of bytes that cannot occur in base 64 encoded data' is a general description
     that the isBase64 line addresses; '@return ... or <code>to</code> if every byte in the range can occur' is met by `return
     to`; the @param clauses describe the arguments; the identifiers (endOfBase64, bytes, from, to, b) name nothing the body does
     not meet."""

B64 = "src/java/org/apache/commons/codec/binary/Base64.java"
DM = "src/java/org/apache/commons/codec/language/DoubleMetaphone.java"
DU = "src/java/org/apache/commons/codec/digest/DigestUtils.java"
MP = "src/java/org/apache/commons/codec/language/Metaphone.java"
QP = "src/java/org/apache/commons/codec/net/QuotedPrintableCodec.java"
UC = "src/java/org/apache/commons/codec/net/URLCodec.java"

GOLD_TEXT = '''/**
 * Finds the first byte in a range of an array of bytes that cannot occur in base 64 encoded data.
 *
 * @param bytes
 *            array of bytes to scan
 * @param from
 *            index of the first byte to scan
 * @param to
 *            index after the last byte to scan
 * @return index of the first such byte, or <code>to</code> if every byte in the range can occur in base 64 encoded
 *         data
 */
public static final int endOfBase64(byte[] bytes, int from, int to) {
    for (int i = from; i < to; i++) {
        final byte b = bytes[i];
        if (!Base64.isBase64(b)
                && b != ' ' && b != '\\n' && b != '\\r' && b != '\\t') {
            return i;
        }
    }
    return to;
}'''

HOP1 = '''/**
 * Check if an array of bytes holds only base 64 encoded data. An empty
 * array gives <code>true</code>.
 *
 * @param value array of bytes to check
 * @return <code>true</code> if every byte of the array can occur in base 64
 *          encoded data; <code>false</code> otherwise.
 */
public static boolean isBase64Value(byte[] value) {
    if (value.length == 0) {
        return true;
    }
    return DigestUtils.base64Length(value) == value.length;
}'''

HOP2 = '''/**
 * Calculates the length of the leading base 64 encoded data in an array of bytes.
 * <p>
 * The whole array is scanned, from its first byte to its last.
 * </p>
 *
 * @param data
 *            Data to scan
 * @return index of the first byte that cannot occur in base 64 encoded data, or the length of the array if there is
 *         none
 */
public static int base64Length(byte[] data) {
    return Metaphone.base64RegionEnd(data, 0, data.length);
}'''

HOP3 = '''/**
 * Find the first byte in a region of an array of bytes that cannot
 * occur in base 64 encoded data.
 *
 * @param bytes array of bytes to scan
 * @param from index of the first byte of the region
 * @param to index after the last byte of the region
 * @return index of the first such byte, or <code>to</code> if there is none
 */
public static int base64RegionEnd(byte[] bytes, int from, int to) {
    return QuotedPrintableCodec.scanBase64(bytes, from, to);
}'''

HOP4 = '''/**
 * Scans a range of an array of bytes for the first byte that cannot occur in base 64 encoded data.
 *
 * @param bytes
 *                  array of bytes to scan
 * @param from
 *                  index of the first byte to scan
 * @param to
 *                  index after the last byte to scan
 * @return index of the first such byte, or <code>to</code> if there is none
 */
public static final int scanBase64(byte[] bytes, int from, int to) {
    return URLCodec.endOfBase64(bytes, from, to);
}'''

DISCARD_OLD = """            switch (data[i]) {
                case ' ' :
                case '\\n' :
                case '\\r' :
                case '\\t' :
                    break;
                default :
                    groomedData[bytesCopied++] = data[i];
            }"""

DISCARD_NEW = """            if (!isWhiteSpace(data[i])) {
                groomedData[bytesCopied++] = data[i];
            }"""

DESIGN = {
 "instance": "Codec-5", "project": "Codec", "bug_id": 5, "seed": 7896,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "isArrayByteBase64", "near_line": 625},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/codec/binary/Base64Test.java",
             "test_class": "org.apache.commons.codec.binary.Base64Test", "test_method": "testIsUrlSafe"},
 "expected_signature": "Base64.isArrayByteBase64(whiteSpace)=true",
 "gold": {"method": "endOfBase64", "text": GOLD_TEXT,
          "fault": {"old": "            if (!Base64.isBase64(b)\n"
                           "                    && b != ' ' && b != '\\n' && b != '\\r' && b != '\\t') {",
                    "new": "            if (!Base64.isBase64(b)) {"}},
 "pre_edits": {
   "chain": [{"file": B64, "old": DISCARD_OLD, "new": DISCARD_NEW}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.codec.language.DoubleMetaphone.isBase64Value(arrayOctet);",
   "lie": "The array is first converted to a String in the US-ASCII charset, and that String is then matched once against "
          "a precompiled regular expression.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "isBase64Value",
      "imports": ["org.apache.commons.codec.digest.DigestUtils"], "text": HOP1},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "base64Length",
      "imports": ["org.apache.commons.codec.language.Metaphone"], "text": HOP2},
     {"file": MP, "class": "org.apache.commons.codec.language.Metaphone", "method": "base64RegionEnd",
      "imports": ["org.apache.commons.codec.net.QuotedPrintableCodec"], "text": HOP3},
     {"file": QP, "class": "org.apache.commons.codec.net.QuotedPrintableCodec", "method": "scanBase64",
      "imports": [], "text": HOP4},
     {"file": UC, "class": "org.apache.commons.codec.net.URLCodec", "method": "endOfBase64",
      "imports": ["org.apache.commons.codec.binary.Base64"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.binary.Base64::discardWhitespace",
              "org.apache.commons.codec.binary.Base64::decode",
              "org.apache.commons.codec.binary.Base64::encodeBase64Chunked"],
 "ownership_reason": "Only the gold sees the bytes one at a time and decides which of them can occur in base 64 encoded data; "
                     "hops 3 and 4 pass the range along, hop 2 places the whole array as the range [0, length), and hop 1 "
                     "compares the returned index with the length (an empty array gives true there). Hops 2-4 return an index "
                     "into the array they were given, so no one-line filter at those hops can keep their documented result. "
                     "The convention is pinned outside the gold: Base64.discardWhitespace 'Discards any whitespace from a "
                     "base-64 encoded block' and removes exactly ' ', '\\n', '\\r' and '\\t' (Base64Test testDiscardWhitespace); "
                     "Base64.decode handles chunked data 'since CR and LF are silently ignored' (testDecodeWithWhitespace, "
                     "testRfc4648Section10DecodeWithCrLf); Base64.encodeBase64Chunked writes CRLF into the encoded data "
                     "(testKnownEncodings); the facade's own javadoc says the method treats whitespace as valid. The gold's "
                     "javadoc promises the first byte that cannot occur in base 64 encoded data, which a blank, a tab or a line "
                     "break is not. Passing the array through discardWhitespace (deprecated: 'This method is no longer needed') "
                     "at the facade makes the trigger's array empty, so hop 1 answers it and hops 2-5 are never reached: the "
                     "gold's output is not used, and the gold still reports whitespace as a byte that cannot occur in encoded "
                     "data for any range that holds it.",
 "ownership_tests": ["org.apache.commons.codec.binary.Base64Test::testDiscardWhitespace",
                     "org.apache.commons.codec.binary.Base64Test::testDecodeWithWhitespace",
                     "org.apache.commons.codec.binary.Base64Test::testRfc4648Section10DecodeWithCrLf",
                     "org.apache.commons.codec.binary.Base64Test::testKnownEncodings"],
 "compensating": {
   "chain": [
     {"file": DM, "old": "return DigestUtils.base64Length(value) == value.length;",
      "new": "return DigestUtils.base64Length(value) >= value.length - 2;",
      "why": "hop 1 tolerates a trailing two-byte line separator"},
     {"file": DU, "old": "return Metaphone.base64RegionEnd(data, 0, data.length);",
      "new": "return Metaphone.base64RegionEnd(data, data[0] == ' ' ? 1 : 0, data.length);",
      "why": "hop 2 starts the scan after a leading blank"},
     {"file": MP, "old": "return QuotedPrintableCodec.scanBase64(bytes, from, to);",
      "new": "return QuotedPrintableCodec.scanBase64(bytes, from, bytes[to - 1] == '\\n' ? to - 1 : to);",
      "why": "hop 3 leaves a trailing line feed out of the region"},
   ],
 },
 "host_notes": "host_mode largest5 (no other public class reaches 1500 lines): the hosts are exactly hosts_hop_order of "
               "batch6_tasks.json, in size order: language.DoubleMetaphone 1105 lines (hop 1, anchor after `encode`, seed 7996), "
               "digest.DigestUtils 582 (hop 2, after `sha384Hex`, seed 7997), language.Metaphone 407 (hop 3, after `metaphone`, "
               "seed 7998), net.QuotedPrintableCodec 387 (hop 4, after `encode`, seed 7999), net.URLCodec 361 (hop 5, gold, "
               "after `encode`, seed 8000); anchors from stageB_lib.pick_anchor with the instance seed 7896 + 100 + i, all in "
               "the outer class. Smallest host 361 lines. All five are public concrete classes in which a static method "
               "compiles; none was substituted. The facade calls hop 1 by its fully-qualified name; hops 1-3 import the next "
               "host, hop 4 shares the net package with URLCodec, and the gold imports Base64. Behaviour-preserving pre-edit: "
               "Base64.discardWhitespace's switch over the four whitespace bytes is written as a call of the private Base64.isWhiteSpace "
               "(same four bytes), whose only caller was the facade's original body.",
}
