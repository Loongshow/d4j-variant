"""Main-run instance Lang-16 (C10 recipe on the fixed checkout of Defects4J Lang-16; target class NumberUtils, the class the real
bug modified). Facade: NumberUtils.max(long[]), one of the min/max array overloads allowed for this instance (createBigInteger and
createBigDecimal are reserved for Lang-1). Its argument guard (null, empty) stays; the rest of its computation is redistributed
along five hops in the drawn hosts (seed 3614, draw order, no substitution):
  hop 1 ArrayUtils.largestElement        placement: reads the value at the index of the largest element
  hop 2 FastDateFormat.largestPosition   placement: the whole array as the range [0, length)
  hop 3 StringUtils.indexOfLargest       pass-through over the range
  hop 4 ToStringStyle.largestIndex       pass-through over the range
  hop 5 DateUtils.locateLargest          GOLD: the scan of the range (per-element core) keeping the largest value met so far
                                         and its index (first occurrence on ties, strict comparison)
The correct configuration computes exactly what the original max(long[]) computed (running maximum, strict '>').

Fault: inside the scan the gold omits recording the index of a larger element (`index = i;`); it still tracks the largest value,
but the index it returns is always the start of the range, so hop 1 reads the first element. Trigger: NumberUtilsTest::testMaxLong,
first multi-element assertion max({6, 9}) ("max(long[]) failed for array length 2 expected:<9> but was:<6>"). It is the only test
that newly fails: no production code calls max(long[]), the _nullArray/_emptyArray tests stop at the facade guard, and the sibling
overloads (int/short/byte/double/float) are untouched.
Pins outside the gold: the sibling overloads NumberUtils.max(int[]/short[]/byte[]/double[]/float[]) and the min overloads all keep a
running extreme replaced by each larger (smaller) element and return it; ObjectUtils.max(T...) does the same and documents the
first-on-ties rule; their passing tests testMaxInt/testMaxShort/testMaxByte/testMaxDouble/testMaxFloat (identical inputs, e.g.
{6, 9} -> 9 and {-5, 0, 10, 5, -10} -> 10) and ObjectUtilsTest.testMax pin the result. The gold javadoc states the contract (the
index of the largest value, first occurrence on ties) and is silent on the step that records the position.
Ownership: with the omission the gold's output is the start of the range whatever the elements are, so it carries no information
about the position of the largest value: no caller can recover that position from it, and no re-parameterisation of the range at
hops 2-4 helps (any range returns its own start). Any one-line hop edit that passes the trigger must therefore compute the maximum
without the gold. (Redesign 1: the first design omitted `largest = array[i];` instead; its gold still answered "is the first element
the largest", and a one-line recursive edit at hop 3 used that as an oracle and passed the trigger, so it was replaced.)
Bypasses (recorded, not competing repairs under W13; both checked on a scratch variant): hop 1 can return
ObjectUtils.max(toObject(array)), hop 2 can return ArrayUtils.indexOf(array, ObjectUtils.max(ArrayUtils.toObject(array))) (fully
qualified); both discard hops 2-5 / 3-5.
Lie: the facade's documentation claims a pairwise knockout (tournament) over the elements; the code scans linearly with a running
maximum."""

HOP1 = '''/**
 * <p>Gets the largest value in an array of <code>long</code>.</p>
 *
 * @param array  the array to search, not null or empty
 * @return the largest value in the array
 */
public static long largestElement(long[] array) {
    return array[FastDateFormat.largestPosition(array)];
}'''

HOP2 = '''/**
 * <p>Gets the index of the largest value in an array of <code>long</code>.
 * If the largest value occurs more than once, the index of its first
 * occurrence is returned.</p>
 *
 * @param array  the array to search, not null or empty
 * @return the index of the largest value in the array
 */
public static int largestPosition(long[] array) {
    return StringUtils.indexOfLargest(array, 0, array.length);
}'''

HOP3 = '''/**
 * <p>Finds the index of the largest value in a range of an array of
 * <code>long</code>. If the largest value occurs more than once in the
 * range, the index of its first occurrence is returned.</p>
 *
 * @param array  the array to search, not null
 * @param startIndex  the index of the first element of the range
 * @param endIndex  the index after the last element of the range,
 *  greater than <code>startIndex</code>
 * @return the index of the largest value in the range
 */
public static int indexOfLargest(long[] array, int startIndex, int endIndex) {
    return ToStringStyle.largestIndex(array, startIndex, endIndex);
}'''

HOP4 = '''/**
 * <p>Gets the index of the largest value in a range of an array of
 * <code>long</code>. If the largest value occurs more than once in the
 * range, the index of its first occurrence is returned.</p>
 *
 * @param array  the array to search, not null
 * @param startIndex  the index of the first element of the range
 * @param endIndex  the index after the last element of the range,
 *  greater than <code>startIndex</code>
 * @return the index of the largest value in the range
 */
public static int largestIndex(long[] array, int startIndex, int endIndex) {
    return DateUtils.locateLargest(array, startIndex, endIndex);
}'''

GOLD_TEXT = '''/**
 * <p>Finds the index of the largest value in a range of an array of
 * <code>long</code>, examining the elements of the range in order.</p>
 *
 * <p>If the largest value occurs more than once in the range, the index
 * of its first occurrence is returned.</p>
 *
 * @param array  the array to search, not null
 * @param startIndex  the index of the first element of the range
 * @param endIndex  the index after the last element of the range,
 *  greater than <code>startIndex</code>
 * @return the index of the largest value in the range
 */
public static int locateLargest(long[] array, int startIndex, int endIndex) {
    int index = startIndex;
    long largest = array[startIndex];
    for (int i = startIndex + 1; i < endIndex; i++) {
        if (array[i] > largest) {
            largest = array[i];
            index = i;
        }
    }
    return index;
}'''

DESIGN = {
 "instance": "Lang-16", "project": "Lang", "bug_id": 16, "seed": 3614,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": "src/main/java/org/apache/commons/lang3/math/NumberUtils.java", "class": "org.apache.commons.lang3.math.NumberUtils",
            "method": "max", "near_line": 901},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java",
             "test_class": "org.apache.commons.lang3.math.NumberUtilsTest", "test_method": "testMaxLong"},
 "expected_signature": "expected:<9> but was:<6>",
 "gold": {"method": "locateLargest", "text": GOLD_TEXT,
          "fault": {"old": "            if (array[i] > largest) {\n                largest = array[i];\n                index = i;\n            }",
                    "new": "            if (array[i] > largest) {\n                largest = array[i];\n            }"}},
 "chain": {
   "facade_body": "if (array == null) {\n            throw new IllegalArgumentException(\"The Array must not be null\");\n        } else if (array.length == 0) {\n            throw new IllegalArgumentException(\"Array cannot be empty.\");\n        }\n        return org.apache.commons.lang3.ArrayUtils.largestElement(array);",
   "lie": "The elements are compared in pairs, the larger of each pair going on to the next round, until a single element remains.",
   "hops": [
     {"file": "src/main/java/org/apache/commons/lang3/ArrayUtils.java", "class": "org.apache.commons.lang3.ArrayUtils", "method": "largestElement",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP1},
     {"file": "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java", "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "largestPosition",
      "imports": ["org.apache.commons.lang3.StringUtils"], "text": HOP2},
     {"file": "src/main/java/org/apache/commons/lang3/StringUtils.java", "class": "org.apache.commons.lang3.StringUtils", "method": "indexOfLargest",
      "imports": ["org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP3},
     {"file": "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java", "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "largestIndex",
      "imports": ["org.apache.commons.lang3.time.DateUtils"], "text": HOP4},
     {"file": "src/main/java/org/apache/commons/lang3/time/DateUtils.java", "class": "org.apache.commons.lang3.time.DateUtils", "method": "locateLargest",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.math.NumberUtils::max", "org.apache.commons.lang3.ObjectUtils::max",
              "org.apache.commons.lang3.math.IEEE754rUtils::max"],
 "ownership_reason": "Only the scan in the gold sees the individual elements; when it meets a larger element it has to record both the "
                     "value and its position. Without the position step the gold returns the start of the range whatever the elements "
                     "are, so its output carries no information about where the largest value is: hop 1 can only read the value at the "
                     "index it is given, and no one-line change of the range at hops 2-4 (shorter, shifted, or a rescan from the "
                     "returned index) recovers it, because every range yields its own start. The sibling overloads "
                     "NumberUtils.max(int[]/short[]/byte[]/double[]/float[]) keep a running maximum replaced by each larger element, as does "
                     "ObjectUtils.max (first on ties, documented); testMaxInt/testMaxShort/testMaxByte/testMaxDouble (passing) feed the same "
                     "inputs ({6, 9} -> 9, {-5, 0, 10, 5, -10} -> 10). Known bypasses (W13, not competing repairs): hop 1 returning "
                     "ObjectUtils.max(toObject(array)) or hop 2 returning ArrayUtils.indexOf(array, ObjectUtils.max(ArrayUtils.toObject(array))), "
                     "which discard hops 2-5 or 3-5.",
 "ownership_tests": ["org.apache.commons.lang3.math.NumberUtilsTest::testMaxInt",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testMaxShort",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testMaxByte",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testMaxDouble",
                     "org.apache.commons.lang3.ObjectUtilsTest::testMax"],
 "compensating": {
   "chain": [
     {"file": "src/main/java/org/apache/commons/lang3/ArrayUtils.java", "old": "        return array[FastDateFormat.largestPosition(array)];",
      "new": "        return Math.max(array[FastDateFormat.largestPosition(array)], array[array.length - 1]);",
      "why": "hop 1 also weighs the last element of the array"},
     {"file": "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java", "old": "        return DateUtils.locateLargest(array, startIndex, endIndex);",
      "new": "        return DateUtils.locateLargest(array, DateUtils.locateLargest(array, startIndex, endIndex), endIndex);",
      "why": "hop 4 rescans the range from the index found"},
     {"file": "src/main/java/org/apache/commons/lang3/StringUtils.java", "old": "        return ToStringStyle.largestIndex(array, startIndex, endIndex);",
      "new": "        return array[ToStringStyle.largestIndex(array, startIndex, endIndex)] < array[startIndex] ? startIndex : ToStringStyle.largestIndex(array, startIndex, endIndex);",
      "why": "hop 3 keeps the first element of the range when it is larger than the element found"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 3614 (mr_lib.py preview Lang-16 org/apache/commons/lang3/math/NumberUtils.java): ArrayUtils, "
               "FastDateFormat, StringUtils, ToStringStyle, DateUtils. All five are public concrete classes and compile with a public "
               "static hop; no host substituted.",
}
