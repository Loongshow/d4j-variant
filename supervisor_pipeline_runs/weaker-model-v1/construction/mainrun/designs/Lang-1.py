"""Main-run instance Lang-1 (C10 recipe on the fixed checkout of Defects4J Lang-1; target class NumberUtils, the class the real
bug modified). Facade = NumberUtils.createBigInteger(String) (pool candidate, allowed target). Its null guard stays; the rest of
its computation is redistributed along five hops in the drawn hosts (seed 7673, draw order, no substitution):
  hop 1 ToStringStyle.integerValue          sign placement: a leading '-' is stepped over and the value negated at the end
  hop 2 Conversion.prefixedToBigInteger     radix decision: '0x' or '#' -> 16, '0' followed by more digits -> 8, else 10
                                            (the original prefix rules, unchanged)
  hop 3 ArrayUtils.digitRunValue            leading zeros of the digit run are skipped, the last digit kept (plumbing)
  hop 4 StrBuilder.valueOfDigits            pass-through
  hop 5 DateUtils.parseDigits               GOLD: the per-digit conversion of the digit run. Digits are accumulated in a long
                                            while the value is below Long.MAX_VALUE / radix, and in a BigInteger from the
                                            digit at which the long would overflow; the result is the BigInteger, or the
                                            long when the value never left the long range.
The correct configuration computes what new BigInteger(str.substring(pos), radix) computed for every digit string (a sign
character after the prefix, accepted by the BigInteger constructor, is now rejected like any non-digit, as Long.decode does).
Fault: the final decision omits the long-range result (`return value == null ? BigInteger.valueOf(head) : value;` becomes
`return value;`), so every value below Long.MAX_VALUE / radix comes back null. Trigger: NumberUtilsTest::testCreateBigInteger
(first assertion createBigInteger("12345"): expected:<12345> but was:<null>). It is the only test that newly fails: the facade's
only production caller, NumberUtils.createNumber, calls createBigInteger only after createLong has failed (values of 2^63 and
more, which leave the long range inside the gold), and invalid strings still throw. testCreateNumber, TestLang747 and
testCreateNumberMagnitude (BigInteger results in radix 10, 16 and 8) stay green on the variant.
The gold's javadoc states the contract (the value of the digits, not null) and is silent on the two accumulation ranges.
Pins outside the gold: createLong and createInteger (Long.decode / Integer.decode, the same prefixes, the value of a small digit
string), createNumber's ladder Integer -> Long -> BigInteger, and their passing tests.
Single owner: for a value inside the long range the gold returns null, which carries no information, so no hop can recover the
value from it; padding the digits with zeros does not leave the long range (the value is unchanged), and no hop can feed the gold
a digit string that reaches the BigInteger range without changing its value. Passing one-line edits at hops replace the gold's
result with another implementation (bypasses, recorded): hop 4 or hop 3 calling new BigInteger(str.substring(start), radix) or
Long.parseLong for short runs, and the facade restoring its original body (hop-4 versions of the first two checked by the
builder: full suite clean on the variant).
Recorded for the auditor (W13 reading left to the audit): one further passing one-line edit keeps the gold in use. Hop 4
re-encodes the run as "1" + 24 zeros + digits and subtracts radix^(24 + n), with an empty-run guard so that "", "#" and "0x"
still throw (`return start >= str.length() ? DateUtils.parseDigits(str, start, radix) : DateUtils.parseDigits("1" +
StringUtils.repeat('0', 24) + str.substring(start), 0, radix).subtract(BigInteger.valueOf(radix).pow(24 + str.length() - start));`).
It steers every value into the gold's BigInteger range by an offset that has no role in the conversion; checked by the builder:
trigger and full suite pass on the variant. This is the pre-scaling pattern of W14; no conversion of a digit string to a number
is immune to it, because the gold is correct on the large values that createNumber's tests need.
Lie: the facade's documentation claims a block-wise Integer.parseInt conversion from the last block to the first; the code
converts digit by digit from the first digit, with no blocks and no Integer.parseInt."""

NUMBER_UTILS = "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"

HOP1 = '''/**
 * <p>Converts a <code>String</code> to a <code>BigInteger</code>. A leading
 * minus sign is stepped over and the value of the rest of the
 * <code>String</code> is negated.</p>
 *
 * @param str  the <code>String</code> to convert, not null
 * @return the <code>BigInteger</code> value of the <code>String</code>
 * @throws NumberFormatException if the value cannot be converted
 */
public static BigInteger integerValue(final String str) {
    final boolean negative = str.startsWith("-");
    final BigInteger value = Conversion.prefixedToBigInteger(str, negative ? 1 : 0);
    return negative ? value.negate() : value;
}'''

HOP2 = '''/**
 * <p>Converts the number that starts at an index of a <code>String</code>
 * to a non-negative <code>BigInteger</code>. A <code>0x</code> or
 * <code>#</code> prefix marks a hexadecimal number, a leading <code>0</code>
 * followed by further digits an octal number, and any other number is
 * decimal.</p>
 *
 * @param str  the <code>String</code> to convert, not null
 * @param pos  the index at which the number starts
 * @return the value of the number
 * @throws NumberFormatException if the value cannot be converted
 */
public static BigInteger prefixedToBigInteger(final String str, final int pos) {
    if (str.startsWith("0x", pos)) {
        return ArrayUtils.digitRunValue(str, pos + 2, 16);
    }
    if (str.startsWith("#", pos)) {
        return ArrayUtils.digitRunValue(str, pos + 1, 16);
    }
    if (str.startsWith("0", pos) && str.length() > pos + 1) {
        return ArrayUtils.digitRunValue(str, pos + 1, 8);
    }
    return ArrayUtils.digitRunValue(str, pos, 10);
}'''

HOP3 = '''/**
 * <p>Gets the value of the digits of a <code>String</code>, from an index
 * to the end of the <code>String</code>, in a radix. Leading zeros are
 * skipped, the last digit being always kept.</p>
 *
 * @param str  the <code>String</code> to read, not null
 * @param start  the index of the first digit
 * @param radix  the radix of the digits
 * @return the value of the digits
 * @throws NumberFormatException if there are no digits, or if a character
 *  is not a digit in the radix
 */
public static BigInteger digitRunValue(final String str, final int start, final int radix) {
    int first = start;
    while (first < str.length() - 1 && str.charAt(first) == '0') {
        first++;
    }
    return StrBuilder.valueOfDigits(str, first, radix);
}'''

HOP4 = '''/**
 * <p>Gets the value of the digits of a <code>String</code>, from an index
 * to the end of the <code>String</code>, in a radix.</p>
 *
 * @param str  the <code>String</code> to read, not null
 * @param start  the index of the first digit
 * @param radix  the radix of the digits
 * @return the value of the digits
 * @throws NumberFormatException if there are no digits, or if a character
 *  is not a digit in the radix
 */
public static BigInteger valueOfDigits(final String str, final int start, final int radix) {
    return DateUtils.parseDigits(str, start, radix);
}'''

GOLD_TEXT = '''/**
 * <p>Parses the digits of a <code>String</code>, from an index to the end
 * of the <code>String</code>, as a non-negative number in a radix.</p>
 *
 * @param str  the <code>String</code> to parse, not null
 * @param start  the index of the first digit
 * @param radix  the radix of the digits, from 2 to 36
 * @return the value of the digits, not null
 * @throws NumberFormatException if there are no digits, or if a character
 *  is not a digit in the radix
 */
public static BigInteger parseDigits(final String str, final int start, final int radix) {
    final int end = str.length();
    if (start >= end) {
        throw new NumberFormatException("Zero length BigInteger");
    }
    final long limit = Long.MAX_VALUE / radix;
    long head = 0;
    BigInteger value = null;
    for (int i = start; i < end; i++) {
        final int digit = Character.digit(str.charAt(i), radix);
        if (digit < 0) {
            throw new NumberFormatException("For input string: \\"" + str + "\\"");
        }
        if (value == null && head < limit) {
            head = head * radix + digit;
        } else {
            if (value == null) {
                value = BigInteger.valueOf(head);
            }
            value = value.multiply(BigInteger.valueOf(radix)).add(BigInteger.valueOf(digit));
        }
    }
    return value == null ? BigInteger.valueOf(head) : value;
}'''

DESIGN = {
 "instance": "Lang-1", "project": "Lang", "bug_id": 1, "seed": 7673,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": NUMBER_UTILS, "class": "org.apache.commons.lang3.math.NumberUtils", "method": "createBigInteger", "near_line": 723},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java",
             "test_class": "org.apache.commons.lang3.math.NumberUtilsTest", "test_method": "testCreateBigInteger"},
 "expected_signature": "expected:<12345> but was:<null>",
 "gold": {"method": "parseDigits", "text": GOLD_TEXT,
          "fault": {"old": "                value = value.multiply(BigInteger.valueOf(radix)).add(BigInteger.valueOf(digit));\n            }\n        }\n        return value == null ? BigInteger.valueOf(head) : value;",
                    "new": "                value = value.multiply(BigInteger.valueOf(radix)).add(BigInteger.valueOf(digit));\n            }\n        }\n        return value;"}},
 "chain": {
   "facade_body": "if (str == null) {\n            return null;\n        }\n        return org.apache.commons.lang3.builder.ToStringStyle.integerValue(str);",
   "lie": "The digits are converted in blocks of nine with {@link Integer#parseInt(String, int)}, from the last block to the first, and each block is multiplied by the power of the radix that matches its position before the blocks are added up.",
   "hops": [
     {"file": "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java", "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "integerValue",
      "imports": ["java.math.BigInteger", "org.apache.commons.lang3.Conversion"], "text": HOP1},
     {"file": "src/main/java/org/apache/commons/lang3/Conversion.java", "class": "org.apache.commons.lang3.Conversion", "method": "prefixedToBigInteger",
      "imports": ["java.math.BigInteger"], "text": HOP2},
     {"file": "src/main/java/org/apache/commons/lang3/ArrayUtils.java", "class": "org.apache.commons.lang3.ArrayUtils", "method": "digitRunValue",
      "imports": ["java.math.BigInteger", "org.apache.commons.lang3.text.StrBuilder"], "text": HOP3},
     {"file": "src/main/java/org/apache/commons/lang3/text/StrBuilder.java", "class": "org.apache.commons.lang3.text.StrBuilder", "method": "valueOfDigits",
      "imports": ["java.math.BigInteger", "org.apache.commons.lang3.time.DateUtils"], "text": HOP4},
     {"file": "src/main/java/org/apache/commons/lang3/time/DateUtils.java", "class": "org.apache.commons.lang3.time.DateUtils", "method": "parseDigits",
      "imports": ["java.math.BigInteger"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.math.NumberUtils::createLong", "org.apache.commons.lang3.math.NumberUtils::createInteger",
              "org.apache.commons.lang3.math.NumberUtils::createNumber"],
 "ownership_reason": "Only the digit conversion reads the digits; for a value that stays inside the long range it holds the value in its "
                     "long accumulator and must return that as a BigInteger. Once it has returned null the value is gone: no hop can "
                     "recover 12345 from null, padding the digits with zeros leaves the value (and so the accumulation range) unchanged, "
                     "and the sign, prefix and leading-zero hops never see a value. The same prefixes and digit strings give their plain "
                     "numeric value through the sibling factories createLong and createInteger (Long.decode / Integer.decode; "
                     "testCreateLong, testCreateInteger, the Integer and Long cases of TestLang747), and createNumber's ladder hands "
                     "createBigInteger the values beyond the long range, whose BigInteger results stay correct on the variant "
                     "(testCreateNumber, TestLang747, testCreateNumberMagnitude). Known bypasses (W13, not competing repairs): hop 3 or "
                     "hop 4 calling new BigInteger(str.substring(start), radix) or Long.parseLong for a short run, and the facade "
                     "restoring its original body, discard the gold's result. Recorded for the audit: a hop-4 one-liner that "
                     "re-encodes the run as '1' + 24 zeros + digits and subtracts radix^(24 + n) (guarded for an empty run) keeps "
                     "the gold in use and passes the trigger and the full suite; it steers every value into the gold's BigInteger "
                     "range by an offset with no role in the conversion (the pre-scaling pattern of W14).",
 "ownership_tests": ["org.apache.commons.lang3.math.NumberUtilsTest::testCreateLong",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testCreateInteger",
                     "org.apache.commons.lang3.math.NumberUtilsTest::TestLang747",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumberMagnitude",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumber"],
 "compensating": {
   "chain": [
     {"file": "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java", "old": "        return negative ? value.negate() : value;",
      "new": "        return value == null ? BigInteger.ZERO : negative ? value.negate() : value;", "why": "hop 1 maps a missing value to zero"},
     {"file": "src/main/java/org/apache/commons/lang3/ArrayUtils.java", "old": "        while (first < str.length() - 1 && str.charAt(first) == '0') {",
      "new": "        while (first < str.length() && str.charAt(first) == '0') {", "why": "hop 3 skips every leading zero"},
     {"file": "src/main/java/org/apache/commons/lang3/text/StrBuilder.java", "old": "        return DateUtils.parseDigits(str, start, radix);",
      "new": "        return DateUtils.parseDigits(org.apache.commons.lang3.StringUtils.leftPad(str.substring(start), 40, '0'), 0, radix);",
      "why": "hop 4 pads the digit run with zeros to forty digits"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 7673 (mr_lib.py preview Lang-1 org/apache/commons/lang3/math/NumberUtils.java): ToStringStyle, "
               "Conversion, ArrayUtils, StrBuilder, DateUtils. All five usable public classes; no host substituted.",
}
