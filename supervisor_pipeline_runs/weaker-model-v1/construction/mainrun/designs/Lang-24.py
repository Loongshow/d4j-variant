"""Main run Lang-24 (C10 recipe on the fixed checkout of Defects4J Lang-24; the real bug modified NumberUtils, the target class).

Facade: NumberUtils.toByte(String, byte) (allowed target toByte, BATCH5_PREREGISTRATION.md row Lang-24). The other allowed targets
were set aside: toDouble and toFloat are one call to Double.parseDouble / Float.parseFloat, whose full grammar (NaN, Infinity,
hexadecimal significands, type suffixes, surrounding white space, correctly rounded decimal conversion) cannot be redistributed
along a chain without changing the result for some input, so no exact split with a per-element core exists for them. toByte is a
call to Byte.parseByte, i.e. Integer.parseInt(s, 10) followed by the byte range check, which can be written out exactly as a sign
step, a range placement and a digit loop. The two-argument overload is used: it holds the conversion and its argument guard, and
the one-argument overload toByte(String) keeps delegating to it unchanged.
Original computation of the facade: a null String gives the default; otherwise Byte.parseByte(str) and, on NumberFormatException,
the default. Byte.parseByte accepts an optional leading '-' or '+', then one or more characters each of which Character.digit(ch,
10) maps to 0-9 (no white space, no other character), and rejects a value outside [-128, 127].

Chain (hosts in draw order for seed 6186, mr_lib preview, target org/apache/commons/lang3/math/NumberUtils.java, none skipped):
  hop 1 time.DateUtils.parseByte          decision: a NumberFormatException from the conversion gives the default
  hop 2 SystemUtils.toSignedByte          plumbing: the optional sign is read; an empty String or a sign alone holds no number
  hop 3 builder.ToStringStyle.byteValueOf placement: the magnitude limit for the sign (128 negative, 127 positive), narrowing
  hop 4 StringUtils.parseDecimal          pass-through
  hop 5 ArrayUtils.toSignedInt            GOLD: the digit loop (each character decoded with Character.digit, accumulated, a
                                          character that is not a digit or a value above the limit rejected) and the sign
The correct configuration returns the original result for every input: the same null guard, the same sign rule as
Integer.parseInt (a leading '-' or '+'; a sign alone or an empty String is rejected), the same per-character decoding
(Character.digit with radix 10, so the Unicode decimal digits are accepted as Integer.parseInt accepts them), and the same range
[-128, 127] (the magnitude is capped at 128 or 127 while it is accumulated, so no int overflow can occur: before each step the value
is at most 128, after it at most 1289).

Fault (one-line omission in the gold): the disjunct that rejects a character which is not a decimal digit is dropped from the loop's
single check (`if (digit < 0 || value > limit)` becomes `if (value > limit)`), so Character.digit's -1 for such a character is
accumulated as if it were a digit. Trigger: the EXISTING test NumberUtilsTest::testToByteString. Its first assertion ("123" -> 123)
holds; assertTrue("toByte(String) 2 failed", NumberUtils.toByte("abc") == 0) fails: "abc" accumulates -1, -11, -111, which is within
the positive limit, and toByte gives -111. The empty and null assertions still hold (hop 2 and the facade guard). The only other
test that reaches the chain, testToByteStringI, still passes: "123" gives 123, and "12.3" accumulates 1, 12, 119, 1193, which exceeds
the limit 127 and is rejected, so the default 5 is returned. No production code calls toByte.
The gold's javadoc states the idiomatic contract (it parses a String, from an index to its end, as a decimal number with the given
sign, and returns the number) and is silent on the character rule; "abc" is not a decimal number, so a parse that returns -111 for
it violates that contract. The step is pinned outside the gold: NumberUtils.toShort and NumberUtils.toInt are the same conversion
for short and int, and a String with a character that is not a digit gives their default (testToShortString: toShort("abc") = 0;
testToShortStringI: toShort("1234.5", 5) = 5; testToIntString: toInt("abc") = 0); NumberUtils.isDigits rejects a String as soon as
one of its characters is not a digit (testIsDigits: "1ab" and "abc" are not digits); testToByteStringI asserts the default for
"12.3". The facade's own javadoc promises "the byte represented by the string, or the default if conversion fails".

NO_LOCAL_TRACE self-check on the WHOLE variant gold (ArrayUtils.toSignedInt after the omission):
  T1 absent: str is read for the bound (str.length()) and for every decoded character (str.charAt(i)); start is the loop's first
     index; limit is compared with the value in the loop's check; negative decides the returned sign. Each changes the result; no
     parameter is only argument-checked (the gold has no argument check).
  T2 absent: value is initialised to 0 and reassigned in every iteration and returned; i is advanced by the for header; digit is
     assigned per iteration and read in the accumulation; no flag, counter, cursor or best-so-far is left unassigned; the if throws
     and the fall-through continues, the ternary negates or not, so no decision is dead.
  T3 absent: no special set has a handled and an unhandled member. The sign flag is handled both ways; the String is read from the
     start index to its end (both ends of the range used); 'limit' is the only bound the text names ('the largest value accepted
     before the sign is applied'), and it is enforced; no character class is tested at all (no member handled); the text names no
     class (no 'finite', no 'valid', no 'digits only') that is handled in part.
  T4 absent: the javadoc says 'Parses a String, from an index to its end, as a decimal number with the given sign' and '@return the
     number' (general descriptions that the loop, the radix-10 decoding and the sign line address); '@param limit the largest value
     accepted before the sign is applied' is enforced by the throw before the sign is applied; '@param negative whether the number is
     negative' is met by the ternary; '@param str ... not null' is a caller precondition; there is no @throws clause and no inline
     comment; the identifiers (value, digit, limit, negative, start) name nothing the body does not meet.
  The CORRECT gold was checked too: the same items hold, and its only extra text is the disjunct 'digit < 0', a single element-level
  test; the gold names neither the character rule nor any class of rejected input, so no phrase survives the omission.

Single owner: only the gold decodes characters. Hop 1 maps a NumberFormatException to the default; hop 2 reads the sign and rejects
an empty String or a sign alone; hop 3 chooses the magnitude limit for the sign and narrows to byte; hop 4 passes the call on. Once
-1 has been accumulated, the int that comes back is an ordinary value (-111 for "abc", 9 for "1a", 119 for "12a"), so no caller can
recover from it whether a character was rejected. Declared alternatives (G9): hop 1 maps every IllegalArgumentException to the
default; hop 3 uses the positive limit for both signs; hop 4 passes the number on unsigned. None changes the "abc" case.
Recorded one-line edits above the gold that pass the trigger and the full suite (not repairs of the chain):
 B-0 bypass: hop 1 (or hop 2) returns Byte.parseByte(str) inside its try, discarding the rest of the chain including the gold.
 B-1 bypass: hop 2 also rejects a String whose part after the sign is not numeric
     (`if (start == str.length() || !StringUtils.isNumeric(str.substring(start))) {`): a second implementation of the gold's
     per-character decision; on the trigger input the gold's output is never used.
 B-2 test-fitted: hop 2 also rejects a String whose first character after the sign is not a digit
     (`if (start == str.length() || Character.digit(str.charAt(start), 10) < 0) {`): passes the suite, but toByte("1a", (byte) 5)
     still gives 9 and toByte("12a", (byte) 5) 119, where toShort("1a", (short) 5) gives 5 and isDigits("1ab") is false (evidence).
 B-3 test-fitted: hop 3 clamps a non-negative result at zero
     (`return (byte) Math.max(negative ? Integer.MIN_VALUE : 0, StringUtils.parseDecimal(...));`): passes the suite only because the
     trigger's default is 0; toByte("abc", (byte) 5) gives 0 instead of the default 5, and toByte("1a", (byte) 5) still 9.

Lie: the facade's javadoc claims the value is accumulated from the last digit back to the first with a running power of ten; the
chain reads the String from its first character forward and multiplies the running value by ten. It names neither the character
rule nor any step of the chain nor any hop."""

NU = "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
SY = "src/main/java/org/apache/commons/lang3/SystemUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

PARSE_DOC = '''/**
 * <p>Parses a String, from an index to its end, as a decimal number with
 * the given sign.</p>
 *
 * @param str  the String to parse, not null
 * @param start  the index at which the number starts
 * @param negative  whether the number is negative
 * @param limit  the largest value accepted before the sign is applied
 * @return the number
 */'''

GOLD_TEXT = PARSE_DOC + '''
public static int toSignedInt(String str, int start, boolean negative, int limit) {
    int value = 0;
    for (int i = start; i < str.length(); i++) {
        final int digit = Character.digit(str.charAt(i), 10);
        value = value * 10 + digit;
        if (digit < 0 || value > limit) {
            throw new NumberFormatException("For input string: \\"" + str + "\\"");
        }
    }
    return negative ? -value : value;
}'''

HOP1 = '''/**
 * <p>Parses a String to a <code>byte</code>, returning a default value if
 * the String cannot be parsed.</p>
 *
 * @param str  the String to parse, not null
 * @param defaultValue  the default value
 * @return the parsed byte, or the default if the String cannot be parsed
 */
public static byte parseByte(String str, byte defaultValue) {
    try {
        return SystemUtils.toSignedByte(str);
    } catch (NumberFormatException nfe) {
        return defaultValue;
    }
}'''

HOP2 = '''/**
 * <p>
 * Converts a String holding an optionally signed decimal number to a <code>byte</code>.
 * </p>
 *
 * <p>
 * A leading <code>'-'</code> makes the number negative and a leading <code>'+'</code> is skipped. An empty String, or a
 * String that holds a sign alone, is not a number.
 * </p>
 *
 * @param str  the String to convert, not null
 * @return the byte
 */
public static byte toSignedByte(String str) {
    final int start = str.startsWith("-") || str.startsWith("+") ? 1 : 0;
    if (start == str.length()) {
        throw new NumberFormatException("For input string: \\"" + str + "\\"");
    }
    return ToStringStyle.byteValueOf(str, start, str.startsWith("-"));
}'''

HOP3 = '''/**
 * <p>Converts a String, from an index to its end, to a <code>byte</code>
 * with the given sign.</p>
 *
 * <p>The magnitude of a negative <code>byte</code> may be one larger than
 * that of a positive one.</p>
 *
 * @param str  the String to convert, not null
 * @param start  the index at which the number starts
 * @param negative  whether the byte is negative
 * @return the byte
 */
public static byte byteValueOf(String str, int start, boolean negative) {
    return (byte) StringUtils.parseDecimal(str, start, negative, negative ? -Byte.MIN_VALUE : Byte.MAX_VALUE);
}'''

HOP4 = PARSE_DOC + '''
public static int parseDecimal(String str, int start, boolean negative, int limit) {
    return ArrayUtils.toSignedInt(str, start, negative, limit);
}'''

DESIGN = {
 "instance": "Lang-24", "project": "Lang", "bug_id": 24, "seed": 6186,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": NU, "class": "org.apache.commons.lang3.math.NumberUtils", "method": "toByte", "near_line": 330},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java",
             "test_class": "org.apache.commons.lang3.math.NumberUtilsTest", "test_method": "testToByteString"},
 "expected_signature": "toByte(String) 2 failed",
 "gold": {"method": "toSignedInt", "text": GOLD_TEXT,
          "fault": {"old": "            if (digit < 0 || value > limit) {",
                    "new": "            if (value > limit) {"}},
 "chain": {
   "facade_body": "if(str == null) {\n            return defaultValue;\n        }\n"
                  "        return org.apache.commons.lang3.time.DateUtils.parseByte(str, defaultValue);",
   "lie": "The value is accumulated from the last digit back to the first, each digit being multiplied by a running power "
          "of ten.",
   "hops": [
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "parseByte",
      "imports": ["org.apache.commons.lang3.SystemUtils"], "text": HOP1},
     {"file": SY, "class": "org.apache.commons.lang3.SystemUtils", "method": "toSignedByte",
      "imports": ["org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP2},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "byteValueOf",
      "imports": ["org.apache.commons.lang3.StringUtils"], "text": HOP3},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "parseDecimal",
      "imports": [], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "toSignedInt", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.math.NumberUtils::toShort",
              "org.apache.commons.lang3.math.NumberUtils::toInt",
              "org.apache.commons.lang3.math.NumberUtils::isDigits"],
 "ownership_reason": "Only the gold decodes the characters of the String: hop 1 maps a NumberFormatException to the default, hop 2 "
                     "reads the optional sign and rejects an empty String or a sign alone, hop 3 chooses the magnitude limit for "
                     "the sign and narrows the result to byte, and hop 4 passes the call on. The gold accumulates "
                     "Character.digit(ch, 10) for every character and is the only place that can see that a character is not a "
                     "decimal digit (-1); once -1 has been accumulated the int that comes back is an ordinary value (-111 for "
                     "\"abc\", 9 for \"1a\", 119 for \"12a\"), so no caller can recover from it that a character was rejected. "
                     "The gold's javadoc promises to parse the String as a decimal number, which \"abc\" is not. The convention is "
                     "pinned outside the gold: NumberUtils.toShort and NumberUtils.toInt perform the same conversion for short and "
                     "int and give their default for a String with a character that is not a digit (testToShortString: "
                     "toShort(\"abc\") = 0; testToShortStringI: toShort(\"1234.5\", 5) = 5; testToIntString: toInt(\"abc\") = 0); "
                     "NumberUtils.isDigits rejects a String as soon as one character is not a digit (testIsDigits: \"1ab\", "
                     "\"abc\"); testToByteStringI asserts the default for \"12.3\". One-line edits above the gold that pass the "
                     "suite are either bypasses (hop 1 or 2 calling Byte.parseByte; hop 2 rejecting a non-numeric remainder with "
                     "StringUtils.isNumeric before the gold is reached, a second implementation of the gold's per-character "
                     "decision) or test-fitted: hop 2 rejecting only a first character that is not a digit leaves "
                     "toByte(\"1a\", (byte) 5) = 9 where toShort(\"1a\", (short) 5) = 5; hop 3 clamping a non-negative result at "
                     "zero gives 0 instead of the default for toByte(\"abc\", (byte) 5).",
 "ownership_tests": ["org.apache.commons.lang3.math.NumberUtilsTest::testToShortString",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testToShortStringI",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testToIntString",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testIsDigits",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testToByteStringI"],
 "compensating": {
   "chain": [
     {"file": DU, "old": "} catch (NumberFormatException nfe) {",
      "new": "} catch (IllegalArgumentException nfe) {",
      "why": "hop 1 maps every IllegalArgumentException to the default"},
     {"file": TSS, "old": "negative ? -Byte.MIN_VALUE : Byte.MAX_VALUE);",
      "new": "Byte.MAX_VALUE);",
      "why": "hop 3 uses the positive limit for both signs"},
     {"file": SU, "old": "    return ArrayUtils.toSignedInt(str, start, negative, limit);",
      "new": "    return ArrayUtils.toSignedInt(str, start, false, limit);",
      "why": "hop 4 passes the number on unsigned"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 6186 (mr_lib preview, target org/apache/commons/lang3/math/NumberUtils.java): "
               "time.DateUtils (hop 1), SystemUtils (hop 2), builder.ToStringStyle (hop 3), StringUtils (hop 4), ArrayUtils "
               "(hop 5, gold). All five are public top-level classes in which a static method compiles (ToStringStyle is "
               "abstract, which does not affect a static method); every preview anchor lies in the outer class, not in a nested "
               "one; none was skipped. The facade calls hop 1 by its fully-qualified name; hops 1-3 import the next host; hop 4 "
               "and the gold share the org.apache.commons.lang3 package.",
}
