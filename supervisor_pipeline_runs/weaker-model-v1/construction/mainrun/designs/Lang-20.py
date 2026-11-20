"""Main run Lang-20 (C10 recipe on the fixed checkout of Defects4J Lang-20; the real bug modified StringUtils, the target class).

Facade: StringUtils.substring(String, int, int) (batch-3 allowed targets: abbreviate / substring). abbreviate was set aside: every
decision that only testAbbreviate_StringIntInt observes (the pull-back of the offset so the window is full, the width-7 check,
the middle window with two markers) acts on the scalars (str, offset, maxWidth) that every hop holds, so a hop repairs it in one
line (a Math.min clamp of the offset, a guard, or a truncation of the returned String), or the variant gold reads the offset only
in a range test. substring(String, int) was set aside for the same reason (each of its steps is a monotone adjustment of one
position that a hop pre-filters with one Math.min / Math.max). substring(String, int, int) has no production caller and exactly
one test caller, StringUtilsSubstringTest::testSubstring_StringIntInt, so a change of its result fails only that test (G5).
Original computation: null String -> null; a negative position counts back from the end; the end is moved down to the length;
a start after the end gives ""; both positions are moved up to 0; str.substring(start, end).

Chain (hosts in draw order for seed 2415, mr_lib preview of org/apache/commons/lang3/StringUtils.java, none skipped):
  hop 1 time.DateUtils.clippedText          decision: an empty String is returned as it is, else delegates
  hop 2 builder.ToStringStyle.textWithin     pass-through
  hop 3 text.StrBuilder.midText              pass-through
  hop 4 time.FastDateFormat.partOf           pass-through
  hop 5 ArrayUtils.regionOf                  GOLD: resolves both positions (count back from the end, move inside the String),
                                             gives "" when the start lies after the end, else takes the characters between them
The correct configuration returns exactly the original result for every input (proof: the clamp to [0, length] is monotone, so
the resolved start exceeds the resolved end only when the original returned "" and every other input yields the same pair of
positions), so it is behaviour-preserving for every caller.

Fault (omission of a decision in the gold): the three-line block `if (start > end) { return ""; }` is dropped, so a start that
lies after the end reaches String.substring, which throws. Trigger: the EXISTING test StringUtilsSubstringTest::
testSubstring_StringIntInt, whose first non-trivial assertion substring("foo bar baz", 8, 6) expects "" and gets
java.lang.StringIndexOutOfBoundsException (begin 8, end 6, length 11). No other test reaches the facade.
The gold's javadoc states the idiomatic contract (the characters from the start position up to the end position, positions
resolved leniently: counted back from the end, moved inside the String) and is silent on the empty-range rule; from 8 up to 6
there are no characters, yet the variant throws instead of returning.

External pins (convention outside the gold): the facade's own javadoc ('If start is not strictly to the left of end, "" is
returned', example substring("abc", 2, 0) = ""); ArrayUtils.subarray, in the gold's own host class, gives the empty array for
an end before the start ('Undervalue (< startIndex) produces empty array', newSize <= 0) and ArrayUtilsTest::
testSubarrayObject asserts "start > end" -> ""; StringUtils.mid returns "" for a position past the end and a negative length
(testMid_String: mid(FOOBAR, 9, 3) = ""); substring(String, int) returns "" for a start past the end (testSubstring_StringInt:
substring("abc", 4) = "").

Single owner: only the gold holds the resolved positions. Above it, the hops hold the raw positions, and the order of the raw
positions is not the order of the resolved ones (the trigger's own (0, -8): raw start after end, resolved 0 before 3), so no
one-line comparison or Math.min / Math.max of the raw positions is a repair. Declared one-line alternatives (G9): hop 1 also
returns "" when start > end (gives "" for (0, -8), expected "foo"); hop 3 passes Math.min(start, end) as the start (resolves
(-8, -8) for (0, -8): ""); hop 4 passes Math.max(start, end) as the end ((0, 0) for (0, -8): ""). None passes the trigger.
Recorded bypasses (not declared; B-1 at hop 1 and B-2 at hop 4 were checked on the variant in a scratch copy: trigger passes,
full suite 0 failing tests):
 B-0 the facade restores the original resolve-and-compare body, discarding all five hops.
 B-1 a test-fitted one-line guard on non-negative raw positions, e.g. hop 1
     `return start > end && end >= 0 ? "" : ToStringStyle.textWithin(str, start, end);`: it passes testSubstring_StringIntInt (its only start-after-end
     case, (8, 6), has non-negative positions) but still throws for (-1, 5) on "foo bar baz" (resolved 10 after 5), so it breaks
     the facade's documented rule; not a repair.
 B-2 a one-line re-implementation of the gold's position resolution at a hop, e.g. hop 4
     `return (start < 0 ? str.length() + start : start) > (end < 0 ? str.length() + end : end) ? "" : ArrayUtils.regionOf(str, start, end);`
     a second implementation of the count-back rule for both positions, far larger than the one-line gold repair.
 B-3 a hop that catches StringIndexOutOfBoundsException from the gold and returns "" (try/catch, multi-statement, swallows the
     gold's failure).

Lie: the facade's javadoc claims the characters are collected by walking from the end position back towards the start position,
each character placed in front of those already collected; the code delegates and takes one String.substring. It names neither
the empty-range rule nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first (no pattern found, nothing rewritten),
then to the WHOLE variant gold:
 T1 absent: str is read for its length and the final substring; start and end are each resolved and passed to str.substring;
    no parameter is unused, overwritten before use, or read only in an argument check.
 T2 absent: len is read by both count-back lines and both moves; start and end are reassigned and read by str.substring; no local
    is initialised to a literal; there is no loop; both `if (... < 0)` decisions change the substring taken.
 T3 absent: the closed sets in the gold's text are the two range ends {start, end} and the two sides of the String {before 0,
    past the length}; both ends get the count-back step and the same two-sided move (Math.max(0, Math.min(x, len))), so no
    member is left out.
 T4 absent: 'a negative position counts back from the end' is met by the two count-back lines; 'a position that then lies
    outside the String is moved to the nearer end of it' is met by the two Math.max/Math.min lines; '(exclusive)' is met by
    str.substring(start, end); 'not null' is a caller precondition; '@return the characters from the start position up to the
    end position' is a general description that str.substring(start, end) addresses."""

SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

GOLD_TEXT = '''/**
 * <p>Gets the characters of a String from a start position up to an end
 * position.</p>
 *
 * <p>A negative position counts back from the end of the String, and a
 * position that then lies outside the String is moved to the nearer end
 * of it.</p>
 *
 * @param str  the String to get the characters from, not null
 * @param start  the position to start from
 * @param end  the position to end at (exclusive)
 * @return the characters from the start position up to the end position
 */
public static String regionOf(String str, int start, int end) {
    final int len = str.length();
    if (start < 0) {
        start = len + start;
    }
    if (end < 0) {
        end = len + end;
    }
    start = Math.max(0, Math.min(start, len));
    end = Math.max(0, Math.min(end, len));
    if (start > end) {
        return "";
    }
    return str.substring(start, end);
}'''

HOP_DOC = '''/**
 * <p>Gets the characters of a String from a start position up to an end
 * position.</p>
 *
 * @param str  the String to get the characters from, not null
 * @param start  the position to start from, negative means count back
 *  from the end of the String by this many characters
 * @param end  the position to end at (exclusive), negative means count
 *  back from the end of the String by this many characters
 * @return the characters from the start position up to the end position
 */'''

HOP1 = '''/**
 * <p>Gets the characters of a String from a start position up to an end
 * position.</p>
 *
 * <p>An empty String is returned as it is.</p>
 *
 * @param str  the String to get the characters from, not null
 * @param start  the position to start from, negative means count back
 *  from the end of the String by this many characters
 * @param end  the position to end at (exclusive), negative means count
 *  back from the end of the String by this many characters
 * @return the characters from the start position up to the end position
 */
public static String clippedText(String str, int start, int end) {
    if (str.length() == 0) {
        return str;
    }
    return ToStringStyle.textWithin(str, start, end);
}'''

HOP2 = HOP_DOC + '''
public static String textWithin(String str, int start, int end) {
    return StrBuilder.midText(str, start, end);
}'''

HOP3 = HOP_DOC + '''
public static String midText(String str, int start, int end) {
    return FastDateFormat.partOf(str, start, end);
}'''

HOP4 = HOP_DOC + '''
public static String partOf(String str, int start, int end) {
    return ArrayUtils.regionOf(str, start, end);
}'''

DESIGN = {
 "instance": "Lang-20", "project": "Lang", "bug_id": 20, "seed": 2415,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "substring", "near_line": 2070},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/StringUtilsSubstringTest.java",
             "test_class": "org.apache.commons.lang3.StringUtilsSubstringTest", "test_method": "testSubstring_StringIntInt"},
 "expected_signature": "java.lang.StringIndexOutOfBoundsException: begin 8, end 6, length 11",
 "gold": {"method": "regionOf", "text": GOLD_TEXT,
          "fault": {"old": "        end = Math.max(0, Math.min(end, len));\n"
                           "        if (start > end) {\n"
                           "            return \"\";\n"
                           "        }\n"
                           "        return str.substring(start, end);",
                    "new": "        end = Math.max(0, Math.min(end, len));\n"
                           "        return str.substring(start, end);"}},
 "chain": {
   "facade_body": "if (str == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang3.time.DateUtils.clippedText(str, start, end);",
   "lie": "The characters are collected by walking from the end position back towards the start position, each character "
          "being placed in front of the characters already collected.",
   "hops": [
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "clippedText",
      "imports": ["org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "textWithin",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"], "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "midText",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "partOf",
      "imports": ["org.apache.commons.lang3.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "regionOf", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.ArrayUtils::subarray",
              "org.apache.commons.lang3.StringUtils::mid",
              "org.apache.commons.lang3.StringUtils::right"],
 "ownership_reason": "Only the gold resolves the two positions (a negative position counted back from the end, then moved inside "
                     "the String) and so only the gold can compare them; the facade and hops 1-4 pass the raw positions, whose "
                     "order is not the order of the resolved ones (the trigger's own (0, -8): raw start after end, resolved 0 "
                     "before 3), so no one-line comparison or Math.min/Math.max of raw positions repairs it, and once the gold "
                     "has thrown no caller can recover the result in one line. The convention is pinned outside the gold: the "
                     "facade's javadoc ('If start is not strictly to the left of end, \"\" is returned', substring(\"abc\", 2, 0) "
                     "= \"\"); ArrayUtils.subarray, in the gold's own class, returns the empty array for an end before the start "
                     "('Undervalue (< startIndex) produces empty array') and ArrayUtilsTest.testSubarrayObject asserts "
                     "'start > end' -> \"\"; StringUtils.mid and StringUtils.right return \"\" for an empty or negative span "
                     "(testMid_String: mid(FOOBAR, 9, 3) = \"\", testRight_String: right(FOOBAR, -1) = \"\"); "
                     "substring(String, int) returns \"\" for a start past the end (testSubstring_StringInt).",
 "ownership_tests": ["org.apache.commons.lang3.ArrayUtilsTest::testSubarrayObject",
                     "org.apache.commons.lang3.StringUtilsSubstringTest::testMid_String",
                     "org.apache.commons.lang3.StringUtilsSubstringTest::testRight_String",
                     "org.apache.commons.lang3.StringUtilsSubstringTest::testSubstring_StringInt"],
 "compensating": {
   "chain": [
     {"file": DU, "old": "return ToStringStyle.textWithin(str, start, end);",
      "new": "return start > end ? \"\" : ToStringStyle.textWithin(str, start, end);",
      "why": "hop 1 gives the empty String when the start lies after the end"},
     {"file": SB, "old": "return FastDateFormat.partOf(str, start, end);",
      "new": "return FastDateFormat.partOf(str, Math.min(start, end), end);",
      "why": "hop 3 never passes a start after the end"},
     {"file": FDF, "old": "return ArrayUtils.regionOf(str, start, end);",
      "new": "return ArrayUtils.regionOf(str, start, Math.max(start, end));",
      "why": "hop 4 never passes an end before the start"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2415 (mr_lib preview, target org/apache/commons/lang3/StringUtils.java): "
               "time.DateUtils (hop 1), builder.ToStringStyle (hop 2), text.StrBuilder (hop 3), time.FastDateFormat (hop 4), "
               "ArrayUtils (hop 5, gold). The Lang host pool has exactly these five classes besides the target, so n=8 draws "
               "the same five. All are public classes in which a static method compiles (ToStringStyle is abstract, which does "
               "not affect a static method); none was skipped. The facade calls hop 1 by its fully-qualified name; each hop "
               "imports the next host.",
}
