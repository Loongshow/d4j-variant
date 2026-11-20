"""Main run Lang-44 (C10 recipe on the fixed checkout of Defects4J Lang-44; the real bug modified org.apache.commons.lang.NumberUtils).

Facade: NumberUtils.minimum(long, long, long) (allowed batch-3 targets: isDigits, minimum, maximum). isDigits cannot carry the
recipe without a local trace: its whole computation is one per-character predicate, so any omission in a per-character gold
removes the only read of the string (T1) or freezes the cursor (T2); its ASCII-visible behaviour has no second step to omit.
maximum cannot be triggered by the chosen fault (all its test values are positive, so a running maximum that starts from zero
still passes). minimum(long, long, long) is called only by NumberUtilsTest::testMinimumLong (no production caller), so a fault on
its chain has exactly one catching test. The facade has no argument guard; its body becomes one delegating call into a five-hop
chain drawn with the instance seed 4438 (mr_lib preview, draw order, no substitution):
  hop 1 time.FastDateFormat.lowestOf        placement: the three values are packed into an array
  hop 2 text.StrBuilder.lowestElement       placement: the whole array is taken as the range [0, length)
  hop 3 time.DateUtils.lowestBetween        pass-through of the range
  hop 4 builder.ToStringStyle.lowestInRange pass-through of the range
  hop 5 ArrayUtils.lowestValue              GOLD: the per-element pass over the range (the first element of the range seeds
                                            the running lowest value; each later element replaces it when it is lower)
The correct chain returns the smallest of a, b, c for every input (same comparisons as the original), so the correct
configuration is behaviour-preserving.

Fault (omission in a decision of the gold): the seeding disjunct `i == startIndexInclusive ||` is dropped, so the running lowest
value keeps its placeholder start 0 unless an element is lower than 0. Trigger: the EXISTING test NumberUtilsTest::testMinimumLong,
first assertion minimum(12345, 12346, 12347) expects 12345 and gets 0. No other test reaches the facade; the int overload, the
maximum overloads and math.NumberUtils keep their own bodies.

The gold's javadoc states the idiomatic contract (the lowest value in the range) and is silent on how the running value is seeded.
The convention that the result is one of the values of the range (seeded from the first element, never from an outside constant)
is pinned outside the gold: the sibling overload NumberUtils.minimum(int, int, int) starts from its first argument (passing
testMinimumInt); math.NumberUtils.min(long[]) seeds with array[0] and math.NumberUtils.min(long, long, long) starts from a (passing
math NumberUtilsTest::testMinLong, which expects min({5}) = 5 and min({6, 9}) = 6, and ::testMinimumLong).

Single owner: only the gold visits the elements one by one. Once the running value has been seeded with 0, the lowest of an
all-positive range is lost (the result is 0 whatever the values), so no hop can recover it by post-processing, and no one-line
change of the packed values or of the range bounds makes the start value harmless for every input. Declared alternatives (G9):
hop 2 starts the range at the second element, hop 4 folds the first element of the range in again with Math.min, hop 1 packs
the values in the opposite order; none passes the trigger. Recorded bypasses (not repairs): any hop (or the facade) replacing
its delegation by a direct computation, for example hop 1 returning org.apache.commons.lang.math.NumberUtils.min(a, b, c) or
hop 4 returning org.apache.commons.lang.math.NumberUtils.min(ArrayUtils.subarray(array, startIndexInclusive, endIndexExclusive)),
discards the gold's output. A workaround that packs offsets at hop 1 (a + lowestElement({0, b - a, c - a})) passes the tests
but overflows for widely separated values, so it breaks hop 1's own contract (the lowest of any three long values).

Lie: the facade's javadoc claims the values are sorted by a three-step exchange network and the value in front is returned; the
code packs them into an array and scans it once. It names no hop, no seeding and no start value.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first, then to the VARIANT gold:
  correct gold: T1 absent (array, startIndexInclusive, endIndexExclusive all decide the result); T2 absent (lowest is reassigned
  in the loop and returned; value and i are live; the if decides a live assignment); T3 absent (no enumeration or special-value
  set; both range ends bound the loop); T4 absent (the javadoc names only the general result and caller preconditions).
  variant gold:
  T1 absent - array is read as array[i], startIndexInclusive starts the loop, endIndexExclusive bounds it; each changes the result.
  T2 absent - lowest (initialised 0) is reassigned inside the loop (`lowest = value;`) and returned, so neither dead nor frozen
     (b)(i)/(ii); value feeds the condition and the assignment; i is the advancing cursor; the single if guards a live assignment.
  T3 absent - no closed set is enumerated: no special values, cases, flags or pair halves; both range ends are used only as loop
     bounds, neither is clamped or checked.
  T4 absent - the javadoc phrases are the general result ("the lowest value in the range", addressed by the comparison lines)
     and caller preconditions ("not null", "greater than startIndexInclusive"); no concrete limit, value class or case is named.
"""

SU = "src/java/org/apache/commons/lang/NumberUtils.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
DU = "src/java/org/apache/commons/lang/time/DateUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"

RANGE_DOC = '''/**
 * <p>Gets the lowest value in a range of a <code>long</code> array.</p>
 *
 * <p>The range runs from <code>startIndexInclusive</code> up to, but not
 * including, <code>endIndexExclusive</code>.</p>
 *
 * @param array  the array to search, not null
 * @param startIndexInclusive  the first index of the range
 * @param endIndexExclusive  the index after the last index of the range,
 *  greater than startIndexInclusive
 * @return the lowest value in the range
 */'''

GOLD_TEXT = RANGE_DOC + '''
public static long lowestValue(long[] array, int startIndexInclusive, int endIndexExclusive) {
    long lowest = 0;
    for (int i = startIndexInclusive; i < endIndexExclusive; i++) {
        final long value = array[i];
        if (i == startIndexInclusive || value < lowest) {
            lowest = value;
        }
    }
    return lowest;
}'''

HOP1 = '''/**
 * <p>Gets the lowest of three <code>long</code> values.</p>
 *
 * @param a  value 1
 * @param b  value 2
 * @param c  value 3
 * @return the lowest of the values
 */
public static long lowestOf(long a, long b, long c) {
    return StrBuilder.lowestElement(new long[] {a, b, c});
}'''

HOP2 = '''/**
 * <p>Gets the lowest element of a <code>long</code> array.</p>
 *
 * @param array  the array to search, not null or empty
 * @return the lowest element of the array
 */
public static long lowestElement(long[] array) {
    return DateUtils.lowestBetween(array, 0, array.length);
}'''

HOP3 = RANGE_DOC + '''
public static long lowestBetween(long[] array, int startIndexInclusive, int endIndexExclusive) {
    return ToStringStyle.lowestInRange(array, startIndexInclusive, endIndexExclusive);
}'''

HOP4 = RANGE_DOC + '''
public static long lowestInRange(long[] array, int startIndexInclusive, int endIndexExclusive) {
    return ArrayUtils.lowestValue(array, startIndexInclusive, endIndexExclusive);
}'''

DESIGN = {
 "instance": "Lang-44", "project": "Lang", "bug_id": 44, "seed": 4438,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SU, "class": "org.apache.commons.lang.NumberUtils", "method": "minimum", "near_line": 393},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/NumberUtilsTest.java",
             "test_class": "org.apache.commons.lang.NumberUtilsTest", "test_method": "testMinimumLong"},
 "expected_signature": "expected:<12345> but was:<0>",
 "gold": {"method": "lowestValue", "text": GOLD_TEXT,
          "fault": {"old": "            final long value = array[i];\n"
                           "            if (i == startIndexInclusive || value < lowest) {\n"
                           "                lowest = value;",
                    "new": "            final long value = array[i];\n"
                           "            if (value < lowest) {\n"
                           "                lowest = value;"}},
 "chain": {
   "facade_body": "return org.apache.commons.lang.time.FastDateFormat.lowestOf(a, b, c);",
   "lie": "The values are sorted into ascending order by a three-step exchange network, and the value that ends up in front "
          "is returned.",
   "hops": [
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "lowestOf",
      "imports": ["org.apache.commons.lang.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "lowestElement",
      "imports": ["org.apache.commons.lang.time.DateUtils"], "text": HOP2},
     {"file": DU, "class": "org.apache.commons.lang.time.DateUtils", "method": "lowestBetween",
      "imports": ["org.apache.commons.lang.builder.ToStringStyle"], "text": HOP3},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "lowestInRange",
      "imports": ["org.apache.commons.lang.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "lowestValue", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.NumberUtils::minimum",
              "org.apache.commons.lang.math.NumberUtils::min"],
 "ownership_reason": "Only the gold visits the elements of the range one by one; hop 1 packs the three values, hop 2 takes the "
                     "whole array as the range, hops 3 and 4 pass the range along. Once the running lowest value has been seeded "
                     "with 0 instead of the first element of the range, the lowest of an all-positive range is lost (the result "
                     "is 0 whatever the values), so no hop can recover it and no one-line change of the packed values or the "
                     "range bounds makes the start value harmless for every input. The convention that the result is one of the "
                     "values, seeded from the first one, is pinned outside the gold: the sibling overload "
                     "NumberUtils.minimum(int, int, int) starts from its first argument (testMinimumInt); math.NumberUtils.min(long[]) "
                     "seeds with array[0] and math.NumberUtils.min(long, long, long) starts from a (math NumberUtilsTest "
                     "testMinLong expects min({5}) = 5 and min({6, 9}) = 6; testMinimumLong expects 12345).",
 "ownership_tests": ["org.apache.commons.lang.NumberUtilsTest::testMinimumInt",
                     "org.apache.commons.lang.math.NumberUtilsTest::testMinLong",
                     "org.apache.commons.lang.math.NumberUtilsTest::testMinimumLong"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "return DateUtils.lowestBetween(array, 0, array.length);",
      "new": "return DateUtils.lowestBetween(array, 1, array.length);",
      "why": "hop 2 starts the range at the second element"},
     {"file": TSS, "old": "return ArrayUtils.lowestValue(array, startIndexInclusive, endIndexExclusive);",
      "new": "return Math.min(array[startIndexInclusive], ArrayUtils.lowestValue(array, startIndexInclusive, endIndexExclusive));",
      "why": "hop 4 folds the first element of the range in again"},
     {"file": FDF, "old": "return StrBuilder.lowestElement(new long[] {a, b, c});",
      "new": "return StrBuilder.lowestElement(new long[] {c, b, a});",
      "why": "hop 1 packs the values in the opposite order"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4438 (mr_lib preview, target org/apache/commons/lang/NumberUtils.java): "
               "time.FastDateFormat (hop 1), text.StrBuilder (hop 2), time.DateUtils (hop 3), builder.ToStringStyle (hop 4), "
               "ArrayUtils (hop 5, gold). All five are public classes in which a static method compiles (ToStringStyle is "
               "abstract, which does not affect a static method); none was skipped. The preview notes that the draw relaxed "
               "package distinctness for the hop-5 pair (pool of 2 candidates left). The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host.",
}
