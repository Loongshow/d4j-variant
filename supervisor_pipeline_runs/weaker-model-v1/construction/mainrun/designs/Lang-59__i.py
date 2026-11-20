"""Main run Lang-59__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J Lang-59;
the real bug modified StrBuilder, the facade's class). Batch 8: the bug has no static-facade instance (pool v2: no_tested_static), so
there is no paired instance (B8 note section 1).

Facade: StrBuilder.lastIndexOf(StrMatcher, int) (allowed instance target of BATCH8_PREREGISTRATION.md row 279, the 13-line
lastIndexOf candidate; facade_planned_by null, so no facade reuse). The other allowed targets were not used:
 - StrBuilder.lastIndexOf(char, int) (the 11-line candidate, facade_planned_by null): it is also reached through lastIndexOf(char) and
   through lastIndexOf(String, int) for one-character strings, so every behaviour of it is exercised by testLastIndexOf_char,
   testLastIndexOf_char_int, testLastIndexOf_String and testLastIndexOf_String_int together; its only behaviour that one of them alone
   exercises would be the start clamp, which no test can observe (the capacity beyond the characters in use holds '\\0'). No one-line
   omission is caught by exactly one test.
 - StrBuilder.endsWith(String) is planned by Lang-47__i (distinctness preferred, B8 note section 3), and the candidate above carries the
   recipe.
Original computation of the facade: the start index is rounded down to size - 1 when it is at or beyond size; a null matcher or a
negative (rounded) start index gives -1; otherwise the positions from the start index down to 0 are tried in turn with
matcher.isMatch(buffer, i, 0, startIndex + 1) and the first position with a positive match length is returned; -1 if none. The window
end startIndex + 1 means the matcher sees only the text up to and including the start index (testLastIndexOf_StrMatcher_int: "A
matches, 1 is outside bounds").

facade_variant: V1 (state as parameters). The method reads two private fields and writes none: the facade keeps the argument guard
(a null matcher gives -1), reads the private fields buffer (char[]) and size (int) (inside StrBuilder, so no visibility change) and
passes them, with the matcher and the start index, to hop 1, and returns hop 1's result. No public method of the receiver is needed (no
V2), no private method of StrBuilder is called (no V4), StrMatcher is a public type (no V3/V5). No signature, modifier, override or
throws change; no new type; no reflection; no test edit.
state_passed: the private fields buffer (char[]) and size (int) to hop 1, together with the parameters matcher and startIndex; no
field is written, no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Lang-59-probe/w of the fixture, the
first statement of lastIndexOf(StrMatcher, int) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. Full suite
(`defects4j test`): 2 failing tests, both java.lang.IllegalStateException: PROBE-REACHED at StrBuilder.lastIndexOf(StrBuilder.java:1937):
StrBuilderTest::testLastIndexOf_StrMatcher (through lastIndexOf(StrMatcher), StrBuilder.java:1921, from StrBuilderTest.java:1443) and
StrBuilderTest::testLastIndexOf_StrMatcher_int (directly, from StrBuilderTest.java:1460). The facade has no other caller in production
code or tests.

Hosts (host_mode = "1500"; `mr_lib.py preview Lang-59 org/apache/commons/lang/text/StrBuilder.java 5` with the instance seed 8037,
which excludes the facade's file; used in draw order, nothing substituted):
  hop 1 math.NumberUtils         1627 lines  findLastMatch     decision: a negative start index gives -1 (the original's guard)
  hop 2 builder.ToStringStyle    2151 lines  lastMatchOf       pass-through
  hop 3 time.FastDateFormat      1734 lines  searchLastMatch   pass-through
  hop 4 ArrayUtils               4417 lines  lastIndexOfMatch  pass-through
  hop 5 StringUtils              5006 lines  lastMatchIndex    GOLD: the start position (rounded to the last character in use), the
                                                               matcher's window and the backward scan over the positions
Host sizes 1627, 2151, 1734, 4417, 5006; the smallest host is NumberUtils (1627 lines, hop 1); the gold host has 5006 lines.
The correct configuration returns the original result for every input: a null matcher gives -1 in the facade; a negative start index
gives -1 in hop 1 (the original also gives -1: rounding never makes a negative index non-negative); otherwise the gold's
Math.min(startIndex, size - 1) is the original's rounding (and gives -1 for an empty builder), and the window end pos + 1 is the
original's startIndex + 1 after rounding.

Fault (one-line omission in the gold's decision of the matcher's window): the statement `size = pos + 1;`, which ends the matcher's
window just after the start position, is dropped, so the matcher is given every character in use (bufferEnd = size) and a match that
starts at or before the start index but runs past it is accepted. The gold then reads as the ordinary routine "start at the given index
(rounded to the last character in use) and return the first position, going backwards, at which the matcher matches". Trigger: the
EXISTING test StrBuilderTest::testLastIndexOf_StrMatcher_int. Its charMatcher / spaceMatcher / noneMatcher assertions (single-character
matchers, which never look beyond pos) and lastIndexOf(A_NUMBER_MATCHER, 5) still hold; assertEquals(-1, sb.lastIndexOf(A_NUMBER_MATCHER,
6)) at line 1491 ("A matches, 1 is outside bounds") fails with expected:<-1> but was:<6>. It is the only test that newly fails:
testLastIndexOf_StrMatcher reaches the gold only through lastIndexOf(StrMatcher), whose start index (size) is rounded to size - 1, where
the original window end is size as well; no other code calls the facade or the new hops (gate G5 checks the full suite).

The gold's javadoc states the idiomatic contract in the facade's own wording ("to find the last match searching from the given index",
"the last index matched") and the rounding of an index beyond the characters in use; it is silent on the matcher's window. Under the
class's convention a search from an index examines the text up to and including that index and a matcher must not match beyond the
region searched, so 6 is not "the last match searching from" index 6 in "ab bd A1 junction with A2" (the '1' at 7 lies outside); the
contract is violated on the trigger input. The convention is pinned outside the gold: StrBuilder.indexOf(StrMatcher, int) gives the
matcher exactly the region it searches (bufferStart = startIndex, bufferEnd = size), StrBuilder.replace(StrMatcher, String, int, int,
int) (replaceImpl) bounds the matcher by the region [from, to) it replaces in, and StrMatcher.isMatch ("Only values in the buffer between
the specifed indices may be accessed"; the string matcher returns 0 when pos + len > bufferEnd); passing tests:
StrBuilderTest::testReplace_StrMatcher_String_int_int_int_VaryEndIndex (an "aa" that runs past the end index is not replaced: endIndex 4
on "aaxaaaayaa" gives "-xaaaayaa"), StrMatcherTest::testMatcherIndices (stringMatcher("bc") at 1 matches with bufferEnd 3 and not with
bufferEnd 2), and StrBuilderTest::testLastIndexOf_StrMatcher (through the chain).

Single owner: only the gold decides the matcher's window and scans the positions; hops 2-4 pass the four values along unchanged and
hop 1 only answers a negative start index with -1. Every hop documents `size` as the number of characters in use in the buffer, and the
facade hands over the private field size. Declared alternatives (G9): hop 1 passes the position before the start index (startIndex -
1); hop 2 passes size - 1 as the number of characters in use; hop 3 rounds the start index itself (Math.min(startIndex, size - 1)). Each
leaves the trigger failing.
Recorded edits that are not competing repairs (they pass a value that contradicts the documented meaning of a parameter, or replace the
chain):
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.
 B-1 a caller of the gold (hop 4, or any hop or the facade) passes Math.min(size, startIndex + 1) in place of the number of characters
     in use: the trigger and the suite pass, but the value handed over is not "the number of characters in use in the buffer" (every
     hop's @param and the gold's @param; the facade's size field), and the edit is a second implementation, at the caller, of the gold's
     window decision.

Lie: the facade's javadoc claims the characters are first copied in reverse order so that the search can run forwards over the copy; no
step of the chain copies or reverses anything (the gold scans the builder's own buffer backwards). It names neither the matcher's window,
the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: matcher decides every match; buf is the text matched; startIndex seeds pos; size rounds pos and is then the window end
     (read before it is reassigned); none is only argument-checked.
  T2 absent: pos is the cursor and is decremented in the loop; size is reassigned once and read by every isMatch call; no literal-
     initialised local; the if returns pos, the fall-through continues.
  T3 absent: the scanned range [0, pos] has both ends handled (pos rounded to the last character in use, the loop stops below 0); the
     matcher's window has a fixed start 0 and an end set to pos + 1; no enum, type code or named class is handled in part.
  T4 absent: "the last match searching from the given index", "An index beyond the characters in use starts the search at the last
     character in use" (Math.min) and "the last index matched, or -1 if not found" are met by lines of the body.
 Variant gold (javadoc, signature, `int pos = Math.min(startIndex, size - 1);`, the backward while loop with
 `matcher.isMatch(buf, pos, 0, size) > 0`, `return -1`):
  T1 absent: matcher, buf, startIndex (seeds pos) and size (rounds pos and is the matcher's bufferEnd) each change the result; there is
     no argument check.
  T2 absent: pos is decremented in the loop and returned; no local is dead or frozen (no literal-initialised local); the if has an effect
     (return) different from the fall-through.
  T3 absent: the two ends of the scanned range are both handled (the start is rounded to size - 1, the loop ends below 0); the matcher's
     window [0, size) is the characters in use with neither end narrowed ("No member handled"); startIndex and size are not the two ends of
     one range (startIndex is a position, size the number of characters in use); the gold's text names no class it handles in part.
  T4 absent: "to find the last match searching from the given index" is a general description that the backward scan addresses; "An
     index beyond the characters in use starts the search at the last character in use" is met by Math.min(startIndex, size - 1); "@return
     the last index matched, or -1 if not found" is met by `return pos` / `return -1`; the @param clauses are descriptions of the caller's
     values ("not null" is a caller precondition); no inline comment; the identifiers (pos, size) name what they hold."""

SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
NU = "src/java/org/apache/commons/lang/math/NumberUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
SU = "src/java/org/apache/commons/lang/StringUtils.java"

GOLD_TEXT = '''/**
 * <p>Searches the characters in use of a buffer backwards, using a
 * matcher, to find the last match searching from the given index.</p>
 *
 * <p>An index beyond the characters in use starts the search at the
 * last character in use.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param buf  the buffer to search, not null
 * @param startIndex  the index to start at
 * @param size  the number of characters in use in the buffer
 * @return the last index matched, or <code>-1</code> if not found
 */
public static int lastMatchIndex(StrMatcher matcher, char[] buf, int startIndex, int size) {
    int pos = Math.min(startIndex, size - 1);
    size = pos + 1;
    while (pos >= 0) {
        if (matcher.isMatch(buf, pos, 0, size) > 0) {
            return pos;
        }
        pos--;
    }
    return -1;
}'''

HOP1 = '''/**
 * <p>Searches the characters in use of a buffer backwards, using a
 * matcher, to find the last match searching from the given index.</p>
 *
 * <p>A negative start index returns <code>-1</code>.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param buf  the buffer to search, not null
 * @param startIndex  the index to start at
 * @param size  the number of characters in use in the buffer
 * @return the last index matched, or <code>-1</code> if not found
 */
public static int findLastMatch(StrMatcher matcher, char[] buf, int startIndex, int size) {
    if (startIndex < 0) {
        return -1;
    }
    return ToStringStyle.lastMatchOf(matcher, buf, startIndex, size);
}'''

HOP2 = '''/**
 * <p>Searches the characters in use of a buffer backwards, using a
 * matcher, to find the last match searching from the given index.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param buf  the buffer to search, not null
 * @param startIndex  the index to start at
 * @param size  the number of characters in use in the buffer
 * @return the last index matched, or <code>-1</code> if not found
 */
public static int lastMatchOf(StrMatcher matcher, char[] buf, int startIndex, int size) {
    return FastDateFormat.searchLastMatch(matcher, buf, startIndex, size);
}'''

HOP3 = '''/**
 * <p>Searches the characters in use of a buffer backwards, using a
 * matcher, to find the last match searching from the given index.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param buf  the buffer to search, not null
 * @param startIndex  the index to start at
 * @param size  the number of characters in use in the buffer
 * @return the last index matched, or <code>-1</code> if not found
 */
public static int searchLastMatch(StrMatcher matcher, char[] buf, int startIndex, int size) {
    return ArrayUtils.lastIndexOfMatch(matcher, buf, startIndex, size);
}'''

HOP4 = '''/**
 * <p>Finds the last index in the used part of a char array at which a
 * matcher matches, searching backwards from the given index.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param array  the array to search, not null
 * @param startIndex  the index to start at
 * @param size  the number of characters in use in the array
 * @return the last index matched, or <code>-1</code> if not found
 */
public static int lastIndexOfMatch(StrMatcher matcher, char[] array, int startIndex, int size) {
    return StringUtils.lastMatchIndex(matcher, array, startIndex, size);
}'''

DESIGN = {
 "instance": "Lang-59", "project": "Lang", "bug_id": 59, "seed": 8037,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "lastIndexOf", "near_line": 1936},
 "facade_variant": "V1",
 "state_passed": "private fields buffer (char[]) and size (int) to hop 1, with the parameters matcher and startIndex; no write-back",
 "reachability_probe": "full suite with `if (true) { throw new IllegalStateException(\"PROBE-REACHED\"); }` as the first statement of "
                       "lastIndexOf(StrMatcher, int): 2 failing tests, both PROBE-REACHED at StrBuilder.lastIndexOf(StrBuilder.java:1937): "
                       "StrBuilderTest::testLastIndexOf_StrMatcher (via lastIndexOf(StrMatcher), line 1921) and "
                       "StrBuilderTest::testLastIndexOf_StrMatcher_int (directly, StrBuilderTest.java:1460)",
 "host_mode": "1500",
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/text/StrBuilderTest.java",
             "test_class": "org.apache.commons.lang.text.StrBuilderTest", "test_method": "testLastIndexOf_StrMatcher_int"},
 "expected_signature": "expected:<-1> but was:<6>",
 "gold": {"method": "lastMatchIndex", "text": GOLD_TEXT,
          "fault": {"old": "        int pos = Math.min(startIndex, size - 1);\n"
                           "        size = pos + 1;\n",
                    "new": "        int pos = Math.min(startIndex, size - 1);\n"}},
 "chain": {
   "facade_body": "if (matcher == null) {\n"
                  "            return -1;\n"
                  "        }\n"
                  "        return org.apache.commons.lang.math.NumberUtils.findLastMatch(matcher, buffer, startIndex, size);",
   "lie": "The characters are first copied in reverse order, so that the search can run forwards over the copy.",
   "hops": [
     {"file": NU, "class": "org.apache.commons.lang.math.NumberUtils", "method": "findLastMatch",
      "imports": ["org.apache.commons.lang.builder.ToStringStyle", "org.apache.commons.lang.text.StrMatcher"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "lastMatchOf",
      "imports": ["org.apache.commons.lang.time.FastDateFormat", "org.apache.commons.lang.text.StrMatcher"], "text": HOP2},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "searchLastMatch",
      "imports": ["org.apache.commons.lang.ArrayUtils", "org.apache.commons.lang.text.StrMatcher"], "text": HOP3},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "lastIndexOfMatch",
      "imports": ["org.apache.commons.lang.text.StrMatcher"], "text": HOP4},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "lastMatchIndex",
      "imports": ["org.apache.commons.lang.text.StrMatcher"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.text.StrBuilder::indexOf",
              "org.apache.commons.lang.text.StrBuilder::replace",
              "org.apache.commons.lang.text.StrMatcher::isMatch"],
 "ownership_reason": "Only the gold decides the matcher's window and scans the positions backwards; hops 2-4 pass the matcher, the "
                     "buffer, the start index and the number of characters in use along unchanged, and hop 1 only answers a negative "
                     "start index with -1. The gold's javadoc promises, in the facade's own words, the last match searching from the "
                     "given index; under the class's convention a search from an index examines the text up to and including that "
                     "index, and the matcher must not match beyond the region searched, so 6 (an 'A' whose digit lies at 7) is not "
                     "the last match searching from 6. Every hop documents size as the number of characters in use in the buffer and "
                     "the facade hands over the field size, so no caller may narrow it. The convention is pinned outside the gold: "
                     "StrBuilder.indexOf(StrMatcher, int) gives the matcher exactly the region it searches (startIndex to size), "
                     "StrBuilder.replace(StrMatcher, String, int, int, int) bounds the matcher by the region it replaces in, and "
                     "StrMatcher.isMatch allows access only between the given indices (the string matcher returns 0 when the match "
                     "would run past bufferEnd); StrBuilderTest testReplace_StrMatcher_String_int_int_int_VaryEndIndex (an 'aa' running "
                     "past the end index is not replaced) and StrMatcherTest testMatcherIndices (stringMatcher(\"bc\") matches at 1 "
                     "with bufferEnd 3, not with bufferEnd 2) pass, as does testLastIndexOf_StrMatcher through the chain.",
 "ownership_tests": ["org.apache.commons.lang.text.StrBuilderTest::testReplace_StrMatcher_String_int_int_int_VaryEndIndex",
                     "org.apache.commons.lang.text.StrMatcherTest::testMatcherIndices",
                     "org.apache.commons.lang.text.StrBuilderTest::testLastIndexOf_StrMatcher"],
 "compensating": {
   "chain": [
     {"file": NU, "old": "return ToStringStyle.lastMatchOf(matcher, buf, startIndex, size);",
      "new": "return ToStringStyle.lastMatchOf(matcher, buf, startIndex - 1, size);",
      "why": "hop 1 starts the search at the position before the start index"},
     {"file": TSS, "old": "return FastDateFormat.searchLastMatch(matcher, buf, startIndex, size);",
      "new": "return FastDateFormat.searchLastMatch(matcher, buf, startIndex, size - 1);",
      "why": "hop 2 passes one character fewer as the characters in use"},
     {"file": FDF, "old": "return ArrayUtils.lastIndexOfMatch(matcher, buf, startIndex, size);",
      "new": "return ArrayUtils.lastIndexOfMatch(matcher, buf, Math.min(startIndex, size - 1), size);",
      "why": "hop 3 rounds the start index to the last character in use itself"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are the seeded draw `mr_lib.py preview Lang-59 org/apache/commons/lang/text/StrBuilder.java 5` "
               "(instance seed 8037; the facade's file StrBuilder.java, the only allowed candidate file, is excluded), used in draw "
               "order, none substituted: math.NumberUtils (hop 1, 1627 lines; the smallest host), builder.ToStringStyle (hop 2, 2151), "
               "time.FastDateFormat (hop 3, 1734), ArrayUtils (hop 4, 4417), StringUtils (hop 5, gold, 5006). All five are public "
               "top-level classes in which a static method compiles (ToStringStyle is abstract, which does not affect a static "
               "method); StrMatcher is a public class, imported by each host. Anchors from the preview (seed + 100 + i): hop 1 after "
               "`isDigits` (line 1516, seed 8137), hop 2 after `append` (324, 8138), hop 3 after `format` (833, 8139), hop 4 after "
               "`addAll` (3003, 8140), hop 5 after `substring` (1558, 8141). The facade calls hop 1 by its fully-qualified name; each "
               "hop imports the next host (ArrayUtils and StringUtils share a package).",
}
