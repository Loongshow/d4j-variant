"""Main run Lang-7 (C10 recipe on the fixed checkout of Defects4J Lang-7; the real bug modified NumberUtils, the target class here).

Facade: NumberUtils.min(double[]) (pool candidate `min`, the 20-line double[] overload; line 847). createBigDecimal, the other
allowed candidate, was set aside: on the harness JDK every guard in it (null, blank, leading "--") is redundant with
java.math.BigDecimal's own parsing, so no omission there fails an existing test, and its single `new BigDecimal(str)` has no
per-element core to put at hop 5. The other `min` overloads are not usable either: none of their tests contains a special value,
so a fault there could only be a visibly broken comparison. NumberUtils.max is excluded (used elsewhere).
The facade keeps its argument guard (null array, empty array: IllegalArgumentException) and delegates to a five-hop chain drawn
with the instance seed 5829 (mr_lib preview, draw order; hop 5 takes drawn host 6, see host_notes):
  hop 1 StringUtils.lowestOf            placement: the whole array as the range [0, length)
  hop 2 text.StrBuilder.lowestInRange   placement: the first value of the range is the starting value, the rest of the range
                                        is scanned
  hop 3 Conversion.minimumFrom          pass-through
  hop 4 time.DateUtils.minAcross        pass-through
  hop 5 ArrayUtils.leastFrom            GOLD: the per-value scan (a NaN value makes the result NaN; a smaller value replaces
                                        the running minimum)
The chain performs exactly the original computation (min = array[0]; scan from index 1; NaN check, then `<`), so the correct
configuration is behaviour-preserving for every caller (only tests call min(double[]); no production caller exists).

Fault (omission in the gold, special-value step): the NaN check inside the scan is dropped, so a NaN value after the first one is
passed over by the `<` comparison and the scan returns the minimum of the other values. The gold still reads as a complete,
ordinary minimum scan. Trigger: the EXISTING test NumberUtilsTest::testLang381, whose array
a = {1.2, NaN, 3.7, 27.0, 42.0, NaN} must give NaN (line 1286, assertTrue(Double.isNaN(NumberUtils.min(a)))); the variant
returns 1.2. It is the only test that feeds NaN to min(double[]): testMinDouble uses finite values only, the null/empty tests stop
at the facade guard, and IEEE754rUtilsTest exercises IEEE754rUtils (NaN-ignoring by design). Array b of the same test starts with
NaN, which the starting value carries through, so it passes either way.

The gold's javadoc states the idiomatic contract (the minimum of a starting value and the values of a range) and is silent on
NaN. External pins: NumberUtils.min(double, double, double) documents 'If any value is NaN, NaN is returned' (Math.min);
the sibling overloads NumberUtils.min(float[]) and NumberUtils.max(double[]) perform the same NaN step in their scans; the
facade's own javadoc points to IEEE754rUtils.min(double[]) as 'a version of this method that handles NaN differently', and
IEEE754rUtilsTest::testLang381 (passing) asserts that the IEEE754r version ignores NaN on the very same arrays.

Single owner: only the gold looks at the individual values of the range; once a NaN value has been passed over, the running
minimum (1.2) carries no trace of it, so the placement hops and pass-throughs cannot recover it with a one-line change.
Declared alternatives (G9): hop 2 returns NaN when the first value of the range is NaN (the trigger's NaN is the second value);
hop 2 starts the scan from NaN (the trigger passes but every finite array gives NaN, testMinDouble fails); hop 4 combines the
starting value with Math.min (no effect on a NaN inside the range).
Recorded bypasses (not declared; B-1 and B-2 each passed the trigger, testMinDouble and the full suite on the variant in a
builder scratch copy, checked on the redesign-0 build whose chain code is identical):
 B-1 a second NaN test outside the gold through a sibling, e.g. hop 1
     `return Double.isNaN(NumberUtils.max(array)) ? Double.NaN : StrBuilder.lowestInRange(array, 0, array.length);`
     (max(double[]) is NaN whenever any value is NaN), or
     `java.util.Arrays.asList(ArrayUtils.toObject(array)).contains(Double.NaN)` (Double.equals matches NaN); both re-implement
     the step above the gold.
 B-2 last-value overfits: both trigger arrays end with NaN, so hop 2 seeding from the last value of the range
     (`array[begin + length - 1]`, scanning [begin, begin + length - 1)) or a hop returning
     `Math.min(<result>, array[begin + length - 1])` pass the trigger; both leave {1, NaN, 2} at 1 and the first contradicts
     hop 2's javadoc ('taking the first value of the range as the starting value').
 B-0 facade: restoring the original inline loop discards all five hops.

Lie: the facade's javadoc claims a pairwise halving reduction (front half against mirrored back half, lesser kept, repeated);
the code scans once from the front. It names neither NaN nor any hop."""

NU = "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
CV = "src/main/java/org/apache/commons/lang3/Conversion.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

GOLD_TEXT = '''/**
 * <p>Returns the minimum of a starting value and the values in a range
 * of an array.</p>
 *
 * @param start  the starting value
 * @param array  an array, not null
 * @param begin  the index of the first value in the range
 * @param length  the number of values in the range
 * @return the minimum value
 */
public static double leastFrom(final double start, final double[] array, final int begin, final int length) {
    double least = start;
    final int end = begin + length;
    for (int i = begin; i < end; i++) {
        final double value = array[i];
        if (Double.isNaN(value)) {
            return Double.NaN;
        }
        if (value < least) {
            least = value;
        }
    }
    return least;
}'''

FROM_DOC = '''/**
 * <p>Returns the minimum of a starting value and the values in a range
 * of an array.</p>
 *
 * @param start  the starting value
 * @param array  an array, not null
 * @param begin  the index of the first value in the range
 * @param length  the number of values in the range
 * @return the minimum value
 */'''

HOP1 = '''/**
 * <p>Returns the minimum value in an array.</p>
 *
 * @param array  an array, not null or empty
 * @return the minimum value in the array
 */
public static double lowestOf(final double[] array) {
    return StrBuilder.lowestInRange(array, 0, array.length);
}'''

HOP2 = '''/**
 * <p>Returns the minimum value in a range of an array, taking the first
 * value of the range as the starting value.</p>
 *
 * @param array  an array, not null
 * @param begin  the index of the first value in the range
 * @param length  the number of values in the range, at least one
 * @return the minimum value in the range
 */
public static double lowestInRange(final double[] array, final int begin, final int length) {
    return Conversion.minimumFrom(array[begin], array, begin + 1, length - 1);
}'''

HOP3 = FROM_DOC + '''
public static double minimumFrom(final double start, final double[] array, final int begin, final int length) {
    return DateUtils.minAcross(start, array, begin, length);
}'''

HOP4 = FROM_DOC + '''
public static double minAcross(final double start, final double[] array, final int begin, final int length) {
    return ArrayUtils.leastFrom(start, array, begin, length);
}'''

DESIGN = {
 "instance": "Lang-7", "project": "Lang", "bug_id": 7, "seed": 5829,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": NU, "class": "org.apache.commons.lang3.math.NumberUtils", "method": "min", "near_line": 847},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java",
             "test_class": "org.apache.commons.lang3.math.NumberUtilsTest", "test_method": "testLang381"},
 "expected_signature": "NumberUtilsTest.testLang381(NumberUtilsTest.java:1286)",
 "gold": {"method": "leastFrom", "text": GOLD_TEXT,
          "fault": {"old": "            final double value = array[i];\n"
                           "            if (Double.isNaN(value)) {\n"
                           "                return Double.NaN;\n"
                           "            }\n"
                           "            if (value < least) {",
                    "new": "            final double value = array[i];\n"
                           "            if (value < least) {"}},
 "chain": {
   "facade_body": "if (array == null) {\n"
                  "            throw new IllegalArgumentException(\"The Array must not be null\");\n"
                  "        } else if (array.length == 0) {\n"
                  "            throw new IllegalArgumentException(\"Array cannot be empty.\");\n"
                  "        }\n"
                  "        return StringUtils.lowestOf(array);",
   "lie": "The values are reduced pairwise, each round comparing every value in the front half of the remaining values with "
          "the value at the mirrored position in the back half and keeping the lesser of the two, until a single value remains.",
   "hops": [
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "lowestOf",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "lowestInRange",
      "imports": ["org.apache.commons.lang3.Conversion"], "text": HOP2},
     {"file": CV, "class": "org.apache.commons.lang3.Conversion", "method": "minimumFrom",
      "imports": ["org.apache.commons.lang3.time.DateUtils"], "text": HOP3},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "minAcross",
      "imports": ["org.apache.commons.lang3.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "leastFrom", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.math.NumberUtils::min",
              "org.apache.commons.lang3.math.NumberUtils::max",
              "org.apache.commons.lang3.math.IEEE754rUtils::min"],
 "ownership_reason": "Only the scan in the gold looks at the individual values of the range; once a NaN value has been passed "
                     "over by the `<` comparison the running minimum (1.2 for {1.2, NaN, 3.7, 27.0, 42.0, NaN}) carries no trace "
                     "of it, so the range placement, the starting-value placement and the two pass-throughs cannot recover it with "
                     "a one-line change. The convention is pinned outside the gold: NumberUtils.min(double, double, double) "
                     "documents 'If any value is NaN, NaN is returned'; the sibling scans NumberUtils.min(float[]) and "
                     "NumberUtils.max(double[]) return NaN as soon as they meet a NaN value; the facade's javadoc names "
                     "IEEE754rUtils.min(double[]) as the version that handles NaN differently, and IEEE754rUtilsTest.testLang381 "
                     "(passing) shows that version ignoring NaN on the same arrays.",
 "ownership_tests": ["org.apache.commons.lang3.math.IEEE754rUtilsTest::testLang381",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testMinDouble",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testMinimumDouble",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testMaxDouble"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "    return Conversion.minimumFrom(array[begin], array, begin + 1, length - 1);",
      "new": "    return Double.isNaN(array[begin]) ? Double.NaN : Conversion.minimumFrom(array[begin], array, begin + 1, length - 1);",
      "why": "hop 2 returns NaN when the first value of the range is NaN"},
     {"file": SB, "old": "    return Conversion.minimumFrom(array[begin], array, begin + 1, length - 1);",
      "new": "    return Conversion.minimumFrom(Double.NaN, array, begin, length);",
      "why": "hop 2 starts the scan from NaN so that NaN carries through"},
     {"file": DU, "old": "    return ArrayUtils.leastFrom(start, array, begin, length);",
      "new": "    return Math.min(start, ArrayUtils.leastFrom(start, array, begin, length));",
      "why": "hop 4 combines the starting value with Math.min, which keeps NaN"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 5829 (mr_lib preview, target org/apache/commons/lang3/math/NumberUtils.java): "
               "StringUtils (hop 1), text.StrBuilder (hop 2), Conversion (hop 3), time.DateUtils (hop 4), builder.ToStringStyle "
               "(drawn 5th), ArrayUtils (drawn 6th, preview n=6). Drawn host 5, ToStringStyle, is unusable for the gold: it lives "
               "in the package directory org/apache/commons/lang3/builder, and the validator's G10 source walk skips every "
               "directory whose path contains '/build' (meant for build output), which also matches '/builder'; the first "
               "build (redesign 0) passed every other gate but G10 counted the gold's edited text 0 times. Hop 5 therefore takes "
               "the next drawn host, ArrayUtils (anchor seeded by hop position as usual). All hosts are public classes and every "
               "hop compiles there. NumberUtils already imports StringUtils, so the facade calls hop 1 by its simple name.",
}
