"""Main run Codec-9 (C10f recipe on the fixed checkout of Defects4J Codec-9; the real bug modified Base64, the target class).

Cell C10f, batch 6. host_mode = largest5 (no other public class of the revision reaches 1500 lines), so the five hosts are the five
largest public non-interface, non-enum classes other than Base64, by newline count, in that order (batch6_tasks.json
hosts_hop_order): language.DoubleMetaphone 1105 lines (hop 1), binary.Base32 750 (hop 2), digest.DigestUtils 582 (hop 3),
language.ColognePhonetic 428 (hop 4), language.Metaphone 407 (hop 5, gold). Smallest host: 407 lines (Metaphone, the gold host).

Facade: Base64.isBase64(String) (allowed target Base64.isBase64, BATCH6_PREREGISTRATION.md row Codec-9). Base64 has three public
static isBase64 overloads; the String overload is used. Its original body converts the String to its UTF-8 bytes and delegates to
the byte[] overload, which stays intact beside it as the external pin (the same per-byte rule, with its own passing tests). The
byte[] overload is reached by six tests and the byte overload by 77, so a chain under either of them would have every
per-byte omission caught by several tests at once (gate G5): an omission that admits a control byte fails both
testIsArrayByteBase64 ({0}) and testIsStringBase64, and the only single-test omissions there (space or tab not admitted, only
testIsUrlSafe) reject a valid byte, which a caller can always undo by deleting that byte before the check.
Original computation of the facade: the UTF-8 bytes of the String (a null String gives null, and the byte loop then throws a
NullPointerException); every byte must be in the Base64 alphabet or the pad (Base64.isBase64(byte)) or one of space, tab, CR, LF
(Base64.isWhiteSpace), otherwise false; true when every byte passes (so true for the empty String).

reachability_probe (addendum section 2; scratch copies of the fixture, defects4j compile + full suite, 331 tests):
  isBase64(String) body replaced by `throw new IllegalStateException("PROBE-REACHED");` -> exactly 1 failing test,
    Base64Test::testIsStringBase64, java.lang.IllegalStateException: PROBE-REACHED at Base64.isBase64(Base64.java:607). REACHED.
  isBase64(byte[]) body replaced the same way -> 6 failing tests, all with PROBE-REACHED: testEncodeDecodeSmall,
    testEncodeDecodeRandom, testIsUrlSafe, testIsArrayByteBase64, testNonBase64Test, testIsStringBase64.
  isBase64(byte) body replaced the same way -> 77 failing tests, all with PROBE-REACHED.

Chain (hosts = hosts_hop_order of the task record, anchors from stageB_lib.pick_insertion_anchor with the instance seed 5488 + 100 + i):
  hop 1 language.DoubleMetaphone.isBase64Value   conversion: the String taken as its UTF-8 bytes
  hop 2 binary.Base32.isBase64Octets            placement: the whole array as the range (offset 0, its length)
  hop 3 digest.DigestUtils.isBase64Data         decision: an empty range gives true
  hop 4 language.ColognePhonetic.isBase64Text   pass-through
  hop 5 language.Metaphone.isBase64Region       GOLD: the scan of every byte of the range, with the per-byte rule: a byte at or
                                                below the space character must be space, tab, LF or CR; any other byte must be a
                                                Base64 character or the pad (Base64.isBase64(byte))
The correct configuration returns the original result for every input: the same UTF-8 conversion; a null String still throws a
NullPointerException (hop 2 reads the array's length); for a byte at or below ' ' Base64.isBase64(byte) is always false (the pad
is '=', the alphabet starts at '+', negative bytes are outside the table), so the original rule reduces there to the four
whitespace bytes; above ' ' isWhiteSpace is always false, so it reduces to Base64.isBase64(byte).

Fault (one-line omission of a special-case decision in the gold): the check that admits only space, tab, LF and CR among the
bytes at or below the space character is dropped, so every such byte (a control byte, and also a negative byte) is passed over.
The gold then reads as the common lenient idiom 'skip blanks, check the rest'. Trigger: the EXISTING test
Base64Test::testIsStringBase64. Its null, empty and valid-string assertions still hold (validString has only letters, digits, '=',
LF and CR), and assertFalse("Base64.isStringBase64(invalid-string) is false", Base64.isBase64(invalidString)) at line 76 fails:
invalidString is validString followed by the NUL character, and NUL (byte 0) is now passed over, so the result is true. It is the
only test that reaches the String overload (probe above); every other isBase64 test calls the intact byte[] overload.

The gold's javadoc states the idiomatic contract in general form (whether the range holds valid Base64 data, true for an empty
range) and is silent on control bytes and on how whitespace is told apart. In this code base valid Base64 data means only
characters of the Base64 alphabet or the pad, with whitespace treated as valid (the facade's own javadoc, the byte[] overload);
NUL is neither, so the variant violates that contract on the trigger input. The convention is pinned outside the gold: the intact
sibling overload Base64.isBase64(byte[])
admits a byte only if it is a Base64 character or Base64.isWhiteSpace (space, LF, CR, tab), and its tests pass:
testIsArrayByteBase64 asserts isBase64(new byte[]{0}) is false and that negative bytes are rejected, testIsUrlSafe asserts that
{' ', '\\n', '\\r', '\\t'} is accepted, testNonBase64Test rejects '%'; BaseNCodec.isWhiteSpace documents 'Whitespace is taken to
mean: space, tab, CR, LF'; Base32.isBase32(byte[]) applies the same rule to the Base32 alphabet.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: data is read for every byte (data[i]); offset starts the scan and, with length, fixes its end; each changes the result.
  T2 absent: end is a bound computed before the loop; i is advanced by the for header; octet is assigned per iteration and read in
     every decision; no literal-initialised local, flag, counter or best-so-far; each if has its own effect (return false,
     continue past the alphabet check, return false).
  T3 absent: the whitespace bytes the gold tests (space, tab, LF, CR) are its own literals and all four get the same treatment;
     the range has both ends (offset, end) treated; no pair, no parallel case list with a missing member; the named format
     (Base64) is checked through Base64.isBase64 for every byte above space, and no alphabet byte lies at or below space.
  T4 absent: 'holds valid Base64 data' is a general description that the per-byte checks address; 'or is empty' is met (the loop
     is not entered and true is returned); the @param texts describe the arguments; no limit, bound or value class is named.
 Variant gold (javadoc, signature, `final int end = offset + length; for (int i = offset; i < end; i++) { final byte octet =
 data[i]; if (octet <= ' ') { continue; } if (!Base64.isBase64(octet)) { return false; } } return true;`):
  T1 absent: data is read per byte, offset is the loop start, length fixes end; each changes the returned value. No parameter is
     only argument-checked (the gold has no argument check).
  T2 absent: end is a bound computed before the loop (not frozen); i is advanced by the for header; octet is assigned per
     iteration and read in both conditions; no literal-initialised local; the first if (continue) decides whether the alphabet
     check runs, which changes the result for every byte at or below space, so neither decision is dead.
  T3 absent: no whitespace member, control byte or pad is tested by name any more (no member handled); both ends of the range are
     used; no pair half; the gold's text names no class (no 'whitespace', 'alphabet' or 'finite'-like class), and the one named
     format, Base64, is not handled in part: every byte above space reaches Base64.isBase64, and no alphabet byte lies at or
     below space.
  T4 absent: 'Tests whether a range of a byte array holds valid Base64 data' and '@return true if the range holds valid Base64
     data or is empty; false otherwise' are general descriptions of what the method computes, which the per-byte checks address
     (like 'a valid variable name'); 'or is empty' is met (no iteration, true); the @param texts describe the arguments; no
     limit, bound, value class or case is named; no inline comment; identifiers (end, octet) name nothing the body does not
     meet.

Single owner: only the gold looks at individual bytes; hops 1-4 hold the whole String or array (or its range) and get back one
boolean, which cannot be traced back to the byte that produced it. Removing or adding bytes above the gold cannot help: the
admitted NUL is itself the reason for false, and deleting it would make the true answer correct only for the trimmed input.
Declared alternatives (G9): hop 1 trims the value before the conversion (String.trim drops the trailing NUL, and the trimmed
validString is true, so the result stays true); hop 1 converts with US-ASCII instead of UTF-8 (NUL is still byte 0); hop 4 skips a
leading UTF-8 byte order mark. None changes the trigger's result.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each, B-0 at hop 2, B-1 at hop 4 and at hop 1, B-2 and B-3 as written):
 B-0 bypass: the facade (its original body) or any of hops 1-4 returns the intact byte[] overload, e.g. hop 2
     `return Base64.isBase64(arrayOctet);`, discarding the rest of the chain including the gold.
 B-1 bypass (second implementation of the gold's decision): a hop scans the range itself before the gold, e.g. at hop 4
     `for (int i = offset; i < offset + length; i++) { if (data[i] < ' ' && data[i] != '\\t' && data[i] != '\\n' && data[i] != '\\r') { return false; } }`;
     on the trigger input the gold's result is then never used. The same holds for a regular expression at hop 1 that maps every
     character outside printable ASCII, tab, LF and CR to '$' before the conversion; that edit also breaks hop 1's documented
     conversion (the value tested as its UTF-8 bytes).
 B-2 test-fitted: hop 4 also requires the last byte of the range to be a Base64 character
     (`return Metaphone.isBase64Region(data, offset, length) && Base64.isBase64(data[offset + length - 1]);`): passes the suite
     but isBase64("abc\\n") becomes false, against every hop's documentation and the byte[] overload.
 B-3 test-fitted: hop 1 replaces NUL before the conversion (`value.replace('\\0', '$')`): passes the suite, but "\\u0001" or
     a String with a non-ASCII character is still accepted, against hop 1's documented conversion and contract.

Lie: the facade's javadoc claims the String is matched in a single pass against a precompiled regular expression of the Base64
alphabet; the chain uses no regular expression. It names neither control characters nor whitespace handling nor any hop.

host_notes: see the DESIGN key. The facade calls hop 1 by its fully-qualified name. Base32.java has no import statement, so hop 2
calls DigestUtils by its fully-qualified name (no import added there); hop 1 imports Base32 and StringUtils, hop 3 imports
ColognePhonetic, hop 4 calls Metaphone in its own package, the gold imports Base64."""

B64 = "src/java/org/apache/commons/codec/binary/Base64.java"
DM = "src/java/org/apache/commons/codec/language/DoubleMetaphone.java"
B32 = "src/java/org/apache/commons/codec/binary/Base32.java"
DU = "src/java/org/apache/commons/codec/digest/DigestUtils.java"
CP = "src/java/org/apache/commons/codec/language/ColognePhonetic.java"
MP = "src/java/org/apache/commons/codec/language/Metaphone.java"

GOLD_TEXT = r'''/**
 * Tests whether a range of a byte array holds valid Base64 data.
 *
 * @param data the bytes to test
 * @param offset the index of the first byte of the range
 * @param length the number of bytes in the range
 * @return <code>true</code> if the range holds valid Base64 data or is empty;
 *         <code>false</code> otherwise
 */
public static boolean isBase64Region(byte[] data, int offset, int length) {
    final int end = offset + length;
    for (int i = offset; i < end; i++) {
        final byte octet = data[i];
        if (octet <= ' ') {
            if (octet != ' ' && octet != '\t' && octet != '\n' && octet != '\r') {
                return false;
            }
            continue;
        }
        if (!Base64.isBase64(octet)) {
            return false;
        }
    }
    return true;
}'''

FAULT_OLD = "\n".join([
    r"            if (octet <= ' ') {",
    r"                if (octet != ' ' && octet != '\t' && octet != '\n' && octet != '\r') {",
    r"                    return false;",
    r"                }",
    r"                continue;",
    r"            }",
])
FAULT_NEW = "\n".join([
    r"            if (octet <= ' ') {",
    r"                continue;",
    r"            }",
])

HOP1 = r'''/**
 * Check if a <code>String</code> value contains only valid characters
 * within the Base64 alphabet, treating whitespace as valid. The value is
 * tested as its UTF-8 bytes.
 *
 * @param value String to test
 * @return <code>true</code> if all characters are valid characters in the
 *          Base64 alphabet or if the value is empty;
 *          <code>false</code> otherwise.
 */
public static boolean isBase64Value(String value) {
    return Base32.isBase64Octets(StringUtils.getBytesUtf8(value));
}'''

HOP2 = r'''/**
 * Tests a given byte array to see if it contains only valid characters within the Base64 alphabet. The whole array is
 * tested. Currently the method treats whitespace as valid.
 *
 * @param arrayOctet
 *            byte array to test
 * @return <code>true</code> if all bytes are valid characters in the Base64 alphabet or if the byte array is empty;
 *         <code>false</code>, otherwise
 */
public static boolean isBase64Octets(byte[] arrayOctet) {
    return org.apache.commons.codec.digest.DigestUtils.isBase64Data(arrayOctet, 0, arrayOctet.length);
}'''

HOP3 = r'''/**
 * Checks whether a range of data contains only valid characters within the Base64 alphabet, treating whitespace as
 * valid. An empty range gives <code>true</code>.
 *
 * @param data
 *            Data to check
 * @param offset
 *            Index of the first byte of the range
 * @param length
 *            Number of bytes in the range
 * @return <code>true</code> if all bytes of the range are valid characters in the Base64 alphabet or if the range is
 *         empty
 */
public static boolean isBase64Data(byte[] data, int offset, int length) {
    if (length == 0) {
        return true;
    }
    return ColognePhonetic.isBase64Text(data, offset, length);
}'''

HOP4 = r'''/**
 * Checks whether a non-empty range of bytes contains only valid characters
 * within the Base64 alphabet, treating whitespace as valid.
 *
 * @param data the bytes to check
 * @param offset the index of the first byte of the range
 * @param length the number of bytes in the range, at least one
 * @return <code>true</code> if all bytes of the range are valid characters
 *         in the Base64 alphabet
 */
public static boolean isBase64Text(byte[] data, int offset, int length) {
    return Metaphone.isBase64Region(data, offset, length);
}'''

DESIGN = {
 "instance": "Codec-9", "project": "Codec", "bug_id": 9, "seed": 5488,
 "src_root": "src/java", "test_root": "src/test",
 "host_mode": "largest5",
 "host_lines": [1105, 750, 582, 428, 407],
 "smallest_host_lines": 407,
 "reachability_probe": "scratch copies, full suite (331 tests): isBase64(String) throwing IllegalStateException(\"PROBE-REACHED\") "
                       "-> 1 failing test, Base64Test::testIsStringBase64, with that message (REACHED); isBase64(byte[]) -> 6 "
                       "failing tests with the message; isBase64(byte) -> 77 failing tests with the message.",
 "facade": {"file": B64, "class": "org.apache.commons.codec.binary.Base64", "method": "isBase64", "near_line": 606},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/codec/binary/Base64Test.java",
             "test_class": "org.apache.commons.codec.binary.Base64Test", "test_method": "testIsStringBase64"},
 "expected_signature": "Base64.isStringBase64(invalid-string) is false",
 "gold": {"method": "isBase64Region", "text": GOLD_TEXT, "fault": {"old": FAULT_OLD, "new": FAULT_NEW}},
 "chain": {
   "facade_body": "return org.apache.commons.codec.language.DoubleMetaphone.isBase64Value(base64);",
   "lie": "The String is matched in a single pass against a precompiled regular expression of the Base64 alphabet.",
   "hops": [
     {"file": DM, "class": "org.apache.commons.codec.language.DoubleMetaphone", "method": "isBase64Value",
      "imports": ["org.apache.commons.codec.binary.Base32", "org.apache.commons.codec.binary.StringUtils"], "text": HOP1},
     {"file": B32, "class": "org.apache.commons.codec.binary.Base32", "method": "isBase64Octets",
      "imports": [], "text": HOP2},
     {"file": DU, "class": "org.apache.commons.codec.digest.DigestUtils", "method": "isBase64Data",
      "imports": ["org.apache.commons.codec.language.ColognePhonetic"], "text": HOP3},
     {"file": CP, "class": "org.apache.commons.codec.language.ColognePhonetic", "method": "isBase64Text",
      "imports": [], "text": HOP4},
     {"file": MP, "class": "org.apache.commons.codec.language.Metaphone", "method": "isBase64Region",
      "imports": ["org.apache.commons.codec.binary.Base64"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.codec.binary.Base64::isBase64",
              "org.apache.commons.codec.binary.BaseNCodec::isWhiteSpace",
              "org.apache.commons.codec.binary.Base32::isBase32"],
 "ownership_reason": "Only the gold looks at individual bytes and decides, for each byte at or below the space character, "
                     "whether it is one of the whitespace bytes; hops 1-4 hold the whole String or array and get back one "
                     "boolean, which cannot be traced back to the byte that produced it, and no change of the input above the "
                     "gold (trimming, another charset, a narrower range) turns an admitted NUL into a rejection. The convention "
                     "is pinned outside the gold: the intact sibling overload Base64.isBase64(byte[]) (the facade's original "
                     "delegate) admits a byte only if it is a Base64 character or one of space, LF, CR and tab "
                     "(Base64.isWhiteSpace); testIsArrayByteBase64 asserts that {0} and negative bytes are rejected, "
                     "testIsUrlSafe that {' ', '\\n', '\\r', '\\t'} is accepted, testNonBase64Test that '%' is rejected, and "
                     "all pass; BaseNCodec.isWhiteSpace documents 'Whitespace is taken to mean: space, tab, CR, LF'; "
                     "Base32.isBase32(byte[]) applies the same rule; the facade's own javadoc says the String must contain only "
                     "valid characters within the Base64 alphabet, whitespace being treated as valid. The gold's javadoc "
                     "promises whether the range holds valid Base64 data, which a range holding the NUL byte does not. A one-line "
                     "edit above the gold that passes the existing tests either discards the gold's result (returning the "
                     "intact byte[] overload), re-implements the gold's per-byte decision before it, or is fitted to the "
                     "trigger (requiring a Base64 last byte, or replacing NUL) and breaks the documented contract on other "
                     "input (isBase64(\"abc\\n\") false, or \"\\u0001\" accepted).",
 "ownership_tests": ["org.apache.commons.codec.binary.Base64Test::testIsArrayByteBase64",
                     "org.apache.commons.codec.binary.Base64Test::testIsUrlSafe",
                     "org.apache.commons.codec.binary.Base64Test::testNonBase64Test",
                     "org.apache.commons.codec.binary.Base64Test::testEncodeDecodeSmall"],
 "compensating": {
   "chain": [
     {"file": DM, "old": "return Base32.isBase64Octets(StringUtils.getBytesUtf8(value));",
      "new": "return Base32.isBase64Octets(StringUtils.getBytesUtf8(value.trim()));",
      "why": "hop 1 drops leading and trailing blanks and control characters before the conversion"},
     {"file": DM, "old": "return Base32.isBase64Octets(StringUtils.getBytesUtf8(value));",
      "new": "return Base32.isBase64Octets(StringUtils.getBytesUsAscii(value));",
      "why": "hop 1 converts the value with US-ASCII instead of UTF-8"},
     {"file": CP, "old": "return Metaphone.isBase64Region(data, offset, length);",
      "new": "return length >= 3 && data[offset] == (byte) 0xEF && data[offset + 1] == (byte) 0xBB && data[offset + 2] == (byte) 0xBF ? Metaphone.isBase64Region(data, offset + 3, length - 3) : Metaphone.isBase64Region(data, offset, length);",
      "why": "hop 4 skips a leading UTF-8 byte order mark"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 0): hosts are exactly hosts_hop_order of batch6_tasks.json, the five largest "
               "public non-interface, non-enum classes other than Base64 by newline count: language.DoubleMetaphone 1105 (hop 1), "
               "binary.Base32 750 (hop 2), digest.DigestUtils 582 (hop 3), language.ColognePhonetic 428 (hop 4), "
               "language.Metaphone 407 (hop 5, gold); smallest host 407 lines. All five are public concrete top-level classes "
               "in which a static method compiles; none was substituted. Anchors (stageB_lib.pick_insertion_anchor via "
               "pick_anchor, seed 5488 + 100 + i): after isDoubleMetaphoneEqual (line index 247, seed 5588), after "
               "decodeBase32Hex (501, 5589), after sha384 (389, 5590), after isCologneEqual (402, 5591), after encode(String) "
               "(381, 5592); each anchor lies in the outer class. The facade calls hop 1 by its fully-qualified name; Base32.java "
               "has no import statement, so hop 2 calls DigestUtils by its fully-qualified name; hop 1 imports Base32 and "
               "StringUtils, hop 3 imports ColognePhonetic, hop 4 calls Metaphone in its own package, the gold imports Base64.",
}
