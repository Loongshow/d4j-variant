"""Main run Lang-27 (C10 recipe on the fixed checkout of Defects4J Lang-27; the real bug modified NumberUtils, the target class).

Facade: NumberUtils.createInteger(String) (allowed target, BATCH5_PREREGISTRATION.md row Lang-27; facade_reuse_of empty). The other
allowed targets were set aside: toInt(String) and toLong(String) only call their default-value overloads, which are a null test
plus one JDK parse inside a try/catch that maps every NumberFormatException to the default. Redistributed, their only
per-element core is the digit loop, and every omission there is either caught by both of their tests (a skipped non-digit
check: "abc" / "1L" in testToIntString / testToLongString and "1234.5" in testToIntStringI / testToLongStringL) or touches only
the single MIN_VALUE string of testToLongString, which a hop can answer in one line by comparing the string with
String.valueOf(Long.MIN_VALUE) (a competing repair). createInteger has a richer computation (Integer.decode: sign, radix
prefix, digits, the int range) and three test callers that see different parts of it.
Original computation of the facade: null gives null; otherwise Integer.decode(str): a zero length string throws; an optional
'-' or '+' sign; a 0x / 0X / # prefix gives radix 16, a leading 0 followed by more characters gives radix 8, else radix 10; a
sign after the prefix throws; the remaining digits are parsed with Integer.parseInt semantics (non-empty, every character a
digit in the radix by Character.digit, the magnitude at most Integer.MAX_VALUE, or Integer.MAX_VALUE + 1 when negative), and the
sign is applied.

Chain (hosts in draw order for seed 7527, mr_lib preview, target org/apache/commons/lang3/math/NumberUtils.java, none skipped):
  hop 1 text.StrBuilder.decodeInteger       decision: a zero length string throws; boxing of the decoded int (placement)
  hop 2 StringUtils.decodeInt               plumbing: reads the optional leading sign (negative flag and index after it)
  hop 3 SystemUtils.toDecodedInt            decision: reads the radix prefix and cuts the digits out of the string
  hop 4 time.FastDateFormat.parseIntDigits  decision: empty digits throw
  hop 5 time.DateUtils.valueOfDigits        GOLD: the loop over the digits (Character.digit in the radix, the per-digit range
                                            decision, the negative accumulation of Integer.parseInt) and the sign
The correct configuration returns exactly Integer.decode's result for every input and throws NumberFormatException exactly when
it does (messages differ; no test reads them): a sign after the prefix is rejected by the gold's digit test (Character.digit of
'-' and '+' is -1 in every radix), the empty remainder by hop 4, and the gold's range decision
`value < ((negative ? Integer.MIN_VALUE : -Integer.MAX_VALUE) + digit) / radix` is Integer.parseInt's bound in one test (exact:
the dividend is never positive and Java division truncates towards zero, so it is the ceiling of the real quotient; the
accumulator never leaves [Integer.MIN_VALUE, 0]); Integer.decode's retry with "-" + digits for Integer.MIN_VALUE is the
negative bound.

Fault (one omission in the gold, a per-digit decision): the range decision before `value = value * radix - digit` is dropped, so
a number that does not fit an int wraps around instead of throwing NumberFormatException. The gold then reads as the ordinary
digit loop of a parser. Trigger: the EXISTING test NumberUtilsTest::testCreateNumber; its assertions 1-4 pass and assertion 5,
createNumber("2147483648") = new Long(2147483648), fails with `expected:<2147483648> but was:<-2147483648>`: createNumber tries
createInteger first and widens to createLong only on NumberFormatException, and the variant returns Integer.MIN_VALUE instead
(assertions 17 and 18, "102147483647" and "10" + Long.MAX_VALUE, would fail the same way). It is the only test in which an
integer string outside the int range reaches the chain: testCreateInteger ("12345", null and blank strings), testIsNumber
(valid and invalid strings of int size, checked only for non-null or an exception) and testLang300 (the 'l' path, createLong)
pass on the variant, and no other test class calls createNumber or createInteger. The gold's javadoc states the idiomatic
contract (the value of the digits of a number in a radix, with a sign) and is silent on the int range; -2147483648 is not the
value of the number 2147483648, so the variant violates that contract on the trigger input.

External pins (convention outside the gold): NumberUtils.createNumber (the production caller of the facade) tries 'successively
larger types from Integer to BigInteger' and relies on createInteger throwing NumberFormatException for a value too big for an
int (try createInteger, catch, createLong, catch, createBigInteger; its 'L' branch has the same step one size up, 'Too big for a
long'); Fraction.getFraction(String) converts a whole number with Integer.parseInt, which rejects a value outside the int range
(FractionTest::testFactory_String_double: getFraction("2147483648") "too big" throws NumberFormatException, passing);
NumberUtils.createLong converts with Long.valueOf, the same rule for long. testCreateInteger and testIsNumber pin the rest of
the conversion convention on the chain (blank and non-digit strings throw; createNumber's fallbacks).

Single owner: only the gold holds the running value together with the next digit and the sign, which is what the range
decision needs; hops 1-4 see the string, the sign, the radix and the digit string, and get back one int, in which a value that
wrapped around cannot be told apart from a value in range (2147483648 comes back as -2147483648, "10" + Long.MAX_VALUE as the
positive 1661992959). Declared alternatives (G9), none absorbs the trigger:
  hop 1 rejects a decoded value whose sign disagrees with the sign of the string (assertion 18 comes back positive);
  hop 4 rejects more than ten digits (2147483648 has ten);
  hop 1 rejects a string longer than eleven characters (the longest int literal; 2147483648 has ten).
Recorded edits above the gold that pass the trigger and the full suite (not repairs of the chain):
 B-0 bypass: the facade restores `return Integer.decode(str);`, or a hop returns Integer.decode / Integer.parseInt of its input,
     discarding the rest of the chain including the gold.
 B-1 bypass (a second implementation of the gold's range decision): hop 4 (or hop 3, which has the same inputs) pre-checks the
     digits with another parser before delegating, e.g. hop 4
     `if (digits.length() == 0 || Long.parseLong(digits, radix) > (negative ? 2147483648L : Integer.MAX_VALUE)) {`
     (or java.math.BigInteger(digits, radix).bitLength()); on the trigger input the gold's output is never used.
 B-2 test-fitted: hop 4 rejects ten or more digits (`digits.length() >= 10`): passes the suite (createNumber then widens every
     ten-digit integer to Long) but rejects valid ints such as "2147483647" and "1234567890", against every hop's documented
     conversion and the facade's contract; a round-trip check of the result at hop 1-4 (Integer.toString(value, radix) compared
     with the digits, plus the sign) likewise rejects valid input with leading zeros ("0x00FF", "007") and non-ASCII digits.
 B-3 bypass above the facade: createNumber's `return createInteger(str);` becomes `return Integer.valueOf(Integer.parseInt(str));`,
     which makes the facade's output dead on createNumber's decimal path and leaves createInteger("2147483648") returning
     -2147483648, against the facade's own contract.
 B-4 test-fitted (decimal only): hop 3's decimal branch compares the digit string with "2147483647" / "2147483648" by length and
     String.compareTo before delegating (the decimal branch never has a leading zero, because a leading 0 with more characters
     goes to the octal branch). It passes the suite, but the hex and octal branches still wrap around (createInteger("0x80000000")
     = -2147483648, createInteger("0100000000000") = 0), against the facade's contract, and a valid ten-digit number in
     non-ASCII digits (Arabic-Indic) is rejected; a second, partial implementation of the gold's decision.
 B-1 to B-4 were each applied to the variant in a scratch copy: trigger passes, defects4j test reports 0 failing tests; the
 behaviour claims above were checked by calling createInteger on the edited builds. The correct configuration was compared with
 Integer.decode on 600,058 inputs (fixed edge cases with every prefix, sign and bound, random strings over digits, prefixes, signs,
 blanks and Arabic-Indic digits, and random longs in decimal, 0x, 0 and # forms): 0 mismatches in value or in throwing.

Lie: the facade's javadoc claims the digits after the sign and the radix prefix are read from the last to the first, each
multiplied by the matching power of the radix and added to the result; the chain reads them from the first to the last and
accumulates by Horner's rule (value * radix - digit). It names neither the int range nor any step that is omitted nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: digits gives the bound and every character, radix the digit test, the range decision and the multiplication,
     negative the bound and the returned sign.
  T2 absent: length is a bound computed before the loop; value is assigned in the loop and returned; digit is read three times;
     both ifs throw or fall through (different effects); the bound ternary and the return ternary have two different outcomes.
  T3 absent: both signs get their own bound (Integer.MIN_VALUE for negative, -Integer.MAX_VALUE otherwise) and both get their
     own return form; the accumulator only moves down from 0, so the range has one open end; no other set.
  T4 absent: the javadoc names the value of the digits of a number in a radix with a sign, a caller precondition ('not null or
     empty') and '@throws NumberFormatException if a character is not a digit in the radix', which the digit test meets; the
     range decision is not described (quiet), and no comment exists. Nothing needed rewriting.
 Variant gold (javadoc, signature, `final int length = digits.length(); int value = 0; for (...) { final int digit =
 Character.digit(digits.charAt(i), radix); if (digit < 0) { throw ...; } value = value * radix - digit; } return negative ? value
 : -value;`):
  T1 absent: digits is read for the bound and every character, radix for Character.digit and the multiplication, negative in
     the return ternary; each changes the result. No parameter is only argument-checked (the gold has no argument check).
  T2 absent: length is a bound computed before the loop (not frozen); value is initialised to 0 and reassigned in the loop on
     every iteration, then returned; i advances in the for header; digit decides the if and feeds value; the if throws or falls
     through; the return ternary gives value or -value. No dead local, no frozen local, no dead decision.
  T3 absent: no range, bound or special value is tested at all ('No member handled'); the only element test is the digit test,
     which covers its class completely (Character.digit < 0 for every character that is not a digit in the radix); both signs
     are handled by the return ternary; no pair halves or range ends of which one is treated; no named class handled in part.
  T4 absent: 'the value of the digits of a number in a radix, with a sign' and '@return the value of the number' are general
     descriptions that the loop and the return address; '@param digits ... not null or empty' is a caller precondition; '@throws
     NumberFormatException if a character is not a digit in the radix' is met by the digit test; no limit, bound, value class or
     case is named; no inline comment; identifiers (length, value, digit, negative) name nothing the body does not meet."""

NU = "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
SY = "src/main/java/org/apache/commons/lang3/SystemUtils.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"

GOLD_TEXT = '''/**
 * <p>Returns the value of the digits of a number in a radix, with a
 * sign.</p>
 *
 * @param digits  the digits of the number, not null or empty
 * @param radix  the radix of the digits
 * @param negative  whether the number is negative
 * @return the value of the number
 * @throws NumberFormatException if a character is not a digit in the radix
 */
public static int valueOfDigits(String digits, int radix, boolean negative) {
    final int length = digits.length();
    int value = 0;
    for (int i = 0; i < length; i++) {
        final int digit = Character.digit(digits.charAt(i), radix);
        if (digit < 0) {
            throw new NumberFormatException("For input string: \\"" + digits + "\\"");
        }
        if (value < ((negative ? Integer.MIN_VALUE : -Integer.MAX_VALUE) + digit) / radix) {
            throw new NumberFormatException("For input string: \\"" + digits + "\\"");
        }
        value = value * radix - digit;
    }
    return negative ? value : -value;
}'''

HOP1 = '''/**
 * <p>Decodes a <code>String</code> into an <code>Integer</code>, handling
 * hex and octal notations.</p>
 *
 * <p>A zero length <code>String</code> is not a number.</p>
 *
 * @param str  the <code>String</code> to decode, not null
 * @return the decoded <code>Integer</code>
 * @throws NumberFormatException if the <code>String</code> cannot be decoded
 */
public static Integer decodeInteger(String str) {
    if (str.length() == 0) {
        throw new NumberFormatException("Zero length string");
    }
    return Integer.valueOf(StringUtils.decodeInt(str));
}'''

HOP2 = '''/**
 * <p>Decodes a non-empty <code>String</code> into an <code>int</code>,
 * reading an optional leading <code>'-'</code> or <code>'+'</code> sign.</p>
 *
 * @param str  the <code>String</code> to decode, not null or empty
 * @return the decoded value
 * @throws NumberFormatException if the <code>String</code> cannot be decoded
 */
public static int decodeInt(String str) {
    final char first = str.charAt(0);
    final boolean negative = first == '-';
    final int index = negative || first == '+' ? 1 : 0;
    return SystemUtils.toDecodedInt(str, index, negative);
}'''

HOP3 = '''/**
 * <p>Decodes the part of a <code>String</code> after its sign into an
 * <code>int</code>.</p>
 *
 * <p>A <code>0x</code>, <code>0X</code> or <code>#</code> prefix gives hex
 * digits, and a leading <code>0</code> followed by more characters gives
 * octal digits; otherwise the digits are decimal.</p>
 *
 * @param str  the <code>String</code> to decode, not null
 * @param index  the index of the first character after the sign
 * @param negative  whether the value is negative
 * @return the decoded value
 * @throws NumberFormatException if the <code>String</code> cannot be decoded
 */
public static int toDecodedInt(String str, int index, boolean negative) {
    if (str.startsWith("0x", index) || str.startsWith("0X", index)) {
        return FastDateFormat.parseIntDigits(str.substring(index + 2), 16, negative);
    }
    if (str.startsWith("#", index)) {
        return FastDateFormat.parseIntDigits(str.substring(index + 1), 16, negative);
    }
    if (str.startsWith("0", index) && str.length() > index + 1) {
        return FastDateFormat.parseIntDigits(str.substring(index + 1), 8, negative);
    }
    return FastDateFormat.parseIntDigits(str.substring(index), 10, negative);
}'''

HOP4 = '''/**
 * <p>Parses the digits of a number in a radix into an <code>int</code>.</p>
 *
 * <p>Empty digits are not a number.</p>
 *
 * @param digits  the digits to parse, not null
 * @param radix  the radix of the digits
 * @param negative  whether the number is negative
 * @return the parsed value
 * @throws NumberFormatException if the digits cannot be parsed
 */
public static int parseIntDigits(String digits, int radix, boolean negative) {
    if (digits.length() == 0) {
        throw new NumberFormatException("No digits to parse");
    }
    return DateUtils.valueOfDigits(digits, radix, negative);
}'''

DESIGN = {
 "instance": "Lang-27", "project": "Lang", "bug_id": 27, "seed": 7527,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": NU, "class": "org.apache.commons.lang3.math.NumberUtils", "method": "createInteger", "near_line": 667},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java",
             "test_class": "org.apache.commons.lang3.math.NumberUtilsTest", "test_method": "testCreateNumber"},
 "expected_signature": "expected:<2147483648> but was:<-2147483648>",
 "gold": {"method": "valueOfDigits", "text": GOLD_TEXT,
          "fault": {"old": "            if (value < ((negative ? Integer.MIN_VALUE : -Integer.MAX_VALUE) + digit) / radix) {\n"
                           "                throw new NumberFormatException(\"For input string: \\\"\" + digits + \"\\\"\");\n"
                           "            }\n"
                           "            value = value * radix - digit;",
                    "new": "            value = value * radix - digit;"}},
 "chain": {
   "facade_body": "if (str == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang3.text.StrBuilder.decodeInteger(str);",
   "lie": "The digits after the sign and the radix prefix are read from the last to the first, and each digit is "
          "multiplied by the matching power of the radix before it is added to the result.",
   "hops": [
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "decodeInteger",
      "imports": ["org.apache.commons.lang3.StringUtils"], "text": HOP1},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "decodeInt",
      "imports": [], "text": HOP2},
     {"file": SY, "class": "org.apache.commons.lang3.SystemUtils", "method": "toDecodedInt",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "parseIntDigits",
      "imports": [], "text": HOP4},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "valueOfDigits", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.math.NumberUtils::createNumber",
              "org.apache.commons.lang3.math.Fraction::getFraction",
              "org.apache.commons.lang3.math.NumberUtils::createLong"],
 "ownership_reason": "Only the gold holds the running value together with the next digit, the radix and the sign, which is what "
                     "the per-digit range decision needs; hops 1-4 read the zero length case, the sign, the radix prefix and "
                     "the empty digit string, and get back one int, in which a value that wrapped around cannot be told apart "
                     "from a value in range (2147483648 comes back as -2147483648; \"10\" + Long.MAX_VALUE comes back as the "
                     "positive 1661992959, so not even the sign betrays it). The convention is pinned outside the gold: "
                     "NumberUtils.createNumber, the production caller of the facade, tries successively larger types from "
                     "Integer to BigInteger and widens to createLong only when createInteger throws NumberFormatException "
                     "(its 'L' branch takes the same step one size up, 'Too big for a long'); Fraction.getFraction(String) "
                     "converts a whole number with Integer.parseInt and rejects 2147483648 as too big "
                     "(FractionTest testFactory_String_double, passing); NumberUtils.createLong converts with Long.valueOf, "
                     "the same rule for long. The gold's javadoc promises the value of the number, which -2147483648 is not "
                     "for the digits 2147483648. A pre-check of the digits with another parser at hop 3 or 4 (Long.parseLong "
                     "or BigInteger) passes the existing tests but is a second implementation of the gold's decision; a "
                     "length limit of ten digits passes them too but rejects valid ints such as 2147483647; a comparison of "
                     "the decimal digit string with \"2147483647\" at hop 3 passes them but leaves hex and octal values "
                     "wrapping around (createInteger(\"0x80000000\") = -2147483648).",
 "ownership_tests": ["org.apache.commons.lang3.math.FractionTest::testFactory_String_double",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testCreateInteger",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testIsNumber",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testLang300"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "    return Integer.valueOf(StringUtils.decodeInt(str));",
      "new": "    final int value = StringUtils.decodeInt(str); if (value != 0 && (value < 0) != (str.charAt(0) == '-')) { "
             "throw new NumberFormatException(\"For input string: \\\"\" + str + \"\\\"\"); } return Integer.valueOf(value);",
      "why": "hop 1 rejects a decoded value whose sign disagrees with the sign of the string"},
     {"file": FDF, "old": "    if (digits.length() == 0) {",
      "new": "    if (digits.length() == 0 || digits.length() > 10) {",
      "why": "hop 4 also rejects more than ten digits"},
     {"file": SB, "old": "    if (str.length() == 0) {",
      "new": "    if (str.length() == 0 || str.length() > 11) {",
      "why": "hop 1 also rejects a string longer than the longest int literal"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 7527 (mr_lib preview, target org/apache/commons/lang3/math/NumberUtils.java): "
               "text.StrBuilder (hop 1), StringUtils (hop 2), SystemUtils (hop 3), time.FastDateFormat (hop 4), time.DateUtils "
               "(hop 5, gold). All five are public top-level classes in which a static method compiles (StrBuilder and "
               "FastDateFormat are instantiable classes, which does not affect a static method); every preview anchor lies in "
               "the outer class (delete, splitByWholeSeparatorPreserveAllTokens, getUserHome, getTimeInstance, "
               "getFragmentInHours), not in a nested one; none was skipped. The facade calls hop 1 by its fully-qualified "
               "name; hop 1 imports StringUtils, hop 3 imports FastDateFormat; hops 2 and 4 call the next host in their own "
               "package.",
}
