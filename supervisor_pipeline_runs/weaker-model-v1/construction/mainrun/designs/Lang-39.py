"""Main-run instance Lang-39 (C10 recipe on the fixed checkout of Defects4J Lang-39; target class StringUtils, the class the real
bug modified). Facade: StringUtils.repeat(String, String, int), the separator overload of the pool candidate `repeat` (allowed
target). Its only caller is the existing test StringUtilsTest::testRepeat_StringStringInt; the plain overload repeat(String, int)
is left untouched and stays a sibling pin. The overload with the separator is used because every input shape of the plain
overload's tests also reaches the plain overload through the separator overload (("abc", 3) vs ("?, ", 3), ("a", 3) vs ("x", 3)),
so a fault in a chain behind repeat(String, int) is always caught by both repeat tests (gate G5).

Computation redistributed along the chain (the original body was repeat(str + separator, n) followed by removeEnd):
  facade  StringUtils.repeat(str, sep, n)   original null guard (delegates to repeat(str, n)) + one call to hop 1
  hop 1   DateUtils.joinCopies              count <= 0 gives "" (negative treated as zero), otherwise passes on
  hop 2   StrBuilder.separatedCopies        placement: unit = str + separator, copies of the unit, trailing separator removed
  hop 3   ToStringStyle.copiesOf            aggregation: allocates the char buffer, asks hop 4 to fill it, builds the String
                                            from the reported end index
  hop 4   FastDateFormat.writeCopies        pass-through: String -> char[] and the buffer handed to the gold
  gold    ArrayUtils.replicate              per-element core: copies the source array into the target `count` times, laid end
                                            to end, and returns the index after the last element copied
Fault: the gold omits advancing the write index after each copy (`index += source.length;`), so every copy lands on index 0 and
the reported end stays 0; hop 3 therefore builds "" and the trigger's first non-trivial assertion fails
(repeat("", "x", 3): expected "xx", got ""). The output carries no information about the copies, so no caller can recover it with
a one-line change, and no re-parameterisation of the gold avoids the omission (every count >= 1 call returns end index 0).
Any passing one-line edit at a hop must discard the gold's output (bypass: StringUtils.repeat at hop 2/3, or the original body at
the facade).
Pins outside the gold's javadoc: StrBuilder.append(char[]) (arraycopy at the current end, then size += length), ArrayUtils.addAll
(char overload places the second array at array1.length), the plain repeat overload (copies laid end to end) and rightPad
(cyclic copies of the pad String); their passing tests are the ownership tests.
Hosts: the seeded draw for target org/apache/commons/lang3/StringUtils.java with the instance seed 7696, in draw order; all five
are public classes and compile with a public static hop (no host replaced)."""

GOLD_TEXT = '''/**
 * <p>Copies the elements of an array into another array a number of
 * times, the copies laid end to end from the start of the target
 * array.</p>
 *
 * @param source  the array to copy, not null
 * @param target  the array to copy into, large enough for all the copies
 * @param count  the number of copies, zero or more
 * @return the index in the target array that follows the last element
 *  copied
 */
public static int replicate(char[] source, char[] target, int count) {
    int index = 0;
    for (int i = 0; i < count; i++) {
        System.arraycopy(source, 0, target, index, source.length);
        index += source.length;
    }
    return index;
}'''

HOP1 = '''/**
 * <p>Returns a String made of copies of a String, with a separator
 * between each copy and the next.</p>
 *
 * @param str  the String to copy, not null
 * @param separator  the String to place between the copies, not null
 * @param count  the number of copies, zero or less gives an empty String
 * @return the copies joined by the separator, not null
 */
public static String joinCopies(String str, String separator, int count) {
    if (count <= 0) {
        return "";
    }
    return StrBuilder.separatedCopies(str, separator, count);
}'''

HOP2 = '''/**
 * <p>Returns a String made of copies of a String, with a separator
 * between each copy and the next.</p>
 *
 * <p>Each copy is taken together with the separator that follows it, and
 * the separator that follows the last copy is removed from the end.</p>
 *
 * @param str  the String to copy, not null
 * @param separator  the String to place between the copies, not null
 * @param count  the number of copies, at least one
 * @return the copies joined by the separator, not null
 */
public static String separatedCopies(String str, String separator, int count) {
    return StringUtils.removeEnd(ToStringStyle.copiesOf(str + separator, count), separator);
}'''

HOP3 = '''/**
 * <p>Returns a String made of copies of a String laid end to end.</p>
 *
 * @param str  the String to copy, not null
 * @param count  the number of copies, zero or more
 * @return the copies laid end to end, not null
 */
public static String copiesOf(String str, int count) {
    final char[] buffer = new char[str.length() * count];
    final int end = FastDateFormat.writeCopies(buffer, str, count);
    return new String(buffer, 0, end);
}'''

HOP4 = '''/**
 * <p>Writes copies of the characters of a String into a buffer, laid end
 * to end from the start of the buffer.</p>
 *
 * @param buffer  the buffer to write to, large enough for all the copies
 * @param str  the String to copy, not null
 * @param count  the number of copies, zero or more
 * @return the index in the buffer that follows the last character written
 */
public static int writeCopies(char[] buffer, String str, int count) {
    return ArrayUtils.replicate(str.toCharArray(), buffer, count);
}'''

SRC = "src/java/org/apache/commons/lang3"
DESIGN = {
 "instance": "Lang-39", "project": "Lang", "bug_id": 39, "seed": 7696, "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": f"{SRC}/StringUtils.java", "class": "org.apache.commons.lang3.StringUtils", "method": "repeat", "near_line": 4112},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang3/StringUtilsTest.java",
             "test_class": "org.apache.commons.lang3.StringUtilsTest", "test_method": "testRepeat_StringStringInt"},
 "expected_signature": "expected:<[xx]> but was:<[]>",
 "gold": {"method": "replicate", "text": GOLD_TEXT,
          "fault": {"old": "            System.arraycopy(source, 0, target, index, source.length);\n            index += source.length;\n        }",
                    "new": "            System.arraycopy(source, 0, target, index, source.length);\n        }"}},
 "chain": {
   "facade_body": "if (str == null || separator == null) {\n            return repeat(str, repeat);\n        }\n        return org.apache.commons.lang3.time.DateUtils.joinCopies(str, separator, repeat);",
   "lie": "The result is assembled by halving the count recursively, the copies for each half being built separately and joined with a single separator between the two halves.",
   "hops": [
     {"file": f"{SRC}/time/DateUtils.java", "class": "org.apache.commons.lang3.time.DateUtils", "method": "joinCopies",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"], "text": HOP1},
     {"file": f"{SRC}/text/StrBuilder.java", "class": "org.apache.commons.lang3.text.StrBuilder", "method": "separatedCopies",
      "imports": ["org.apache.commons.lang3.StringUtils", "org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP2},
     {"file": f"{SRC}/builder/ToStringStyle.java", "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "copiesOf",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP3},
     {"file": f"{SRC}/time/FastDateFormat.java", "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "writeCopies",
      "imports": ["org.apache.commons.lang3.ArrayUtils"], "text": HOP4},
     {"file": f"{SRC}/ArrayUtils.java", "class": "org.apache.commons.lang3.ArrayUtils", "method": "replicate", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.text.StrBuilder::append", "org.apache.commons.lang3.ArrayUtils::addAll",
              "org.apache.commons.lang3.StringUtils::repeat", "org.apache.commons.lang3.StringUtils::rightPad"],
 "ownership_reason": "Only the gold writes the copies into the buffer and reports where they end; the facade, the count guard, the "
                     "separator placement, the buffer allocation and the pass-through only hand on the String, the separator, the "
                     "count and the buffer. Once the copies have been written over each other at index 0 and the end index is 0, the "
                     "String built from the buffer is empty and no caller can recover the copies from it with a one-line change; no "
                     "re-parameterisation avoids the omission (every call with a count of one or more reports 0). The convention of "
                     "copying at the current end and then advancing it is the one of StrBuilder.append(char[]) (arraycopy at the end, "
                     "then size += length) and ArrayUtils.addAll (second array placed at array1.length); the plain repeat overload "
                     "and rightPad lay copies end to end, and their passing tests pin the result lengths and contents.",
 "ownership_tests": ["org.apache.commons.lang3.StringUtilsTest::testRepeat_StringInt",
                     "org.apache.commons.lang3.StringUtilsTest::testRightPad_StringIntString",
                     "org.apache.commons.lang3.text.StrBuilderAppendInsertTest::testAppend_CharArray",
                     "org.apache.commons.lang3.text.StrBuilderAppendInsertTest::testAppendPadding",
                     "org.apache.commons.lang3.ArrayUtilsAddTest::testAddObjectArrayToObjectArray"],
 "compensating": {
   "chain": [
     {"file": f"{SRC}/builder/ToStringStyle.java", "old": "        return new String(buffer, 0, end);",
      "new": "        return new String(buffer);", "why": "hop 3 builds the String from the whole buffer instead of the reported end"},
     {"file": f"{SRC}/time/FastDateFormat.java", "old": "        return ArrayUtils.replicate(str.toCharArray(), buffer, count);",
      "new": "        return Math.max(ArrayUtils.replicate(str.toCharArray(), buffer, count), str.length() * count);",
      "why": "hop 4 reports at least the full length of the copies"},
     {"file": f"{SRC}/text/StrBuilder.java", "old": "        return StringUtils.removeEnd(ToStringStyle.copiesOf(str + separator, count), separator);",
      "new": "        return str + ToStringStyle.copiesOf(separator + str, count - 1);",
      "why": "hop 2 writes the first copy and then a separator in front of each further copy"},
   ],
 },
 "host_notes": "Seeded draw (seed 7696, target org/apache/commons/lang3/StringUtils.java, n=5) used in draw order: hop1 "
               "time/DateUtils, hop2 text/StrBuilder, hop3 builder/ToStringStyle, hop4 time/FastDateFormat, hop5 (gold) ArrayUtils. "
               "All five are public top-level classes; no host was unusable and none was replaced.",
}
