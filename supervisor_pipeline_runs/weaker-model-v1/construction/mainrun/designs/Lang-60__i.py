"""Main run Lang-60__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Lang-60; the real bug modified org.apache.commons.lang.text.StrBuilder, the target class). Batch 8: the bug has no static-facade
instance (pool v2: no_tested_static), so there is no pair.

Facade: StrBuilder.lastIndexOf(StrMatcher matcher, int startIndex) (allowed instance target of BATCH8_PREREGISTRATION.md row 280,
the 13-line lastIndexOf; facade_planned_by = null, so no facade reuse). The other allowed targets were not used: StrBuilder.endsWith
is planned by Lang-47__i (distinctness preferred), and StrBuilder.lastIndexOf(char, int) (the 11-line overload) is reached by four
tests (testLastIndexOf_char, testLastIndexOf_char_int, testLastIndexOf_String, testLastIndexOf_String_int, through lastIndexOf(char)
and the one-character path of lastIndexOf(String, int)); its only one-line omission that leaves a working loop is the clamp of a too
large start index, which no test catches (the characters past the content are '\\0' within the capacity), so no single trigger exists.
Original computation of the facade: a start index at or beyond size is rounded down to size - 1; a null matcher or a (rounded)
negative start index gives -1; otherwise the builder is searched backwards from the start index, and at each position i the matcher
is asked matcher.isMatch(buffer, i, 0, startIndex + 1), i.e. the matcher's active area ends just after the start index, so a match
that would need a character after the start index does not count; the first position matched is returned, -1 if none.

facade_variant: V1 (state as parameters). The method reads two private fields and writes none: the facade reads the private fields
buffer (char[]) and size (int) (inside StrBuilder, so no visibility change) and passes them, with the two parameters matcher and
startIndex, to hop 1, and returns hop 1's result. The chain needs no method of the receiver (V2 not needed), no private method of
StrBuilder (no V4), and StrMatcher is a public top-level class with a public abstract isMatch (no V3/V5). The original guard (null
matcher or negative start) is redistributed: the null matcher check sits in hop 1, the negative start check and the rounding of the
start index in the gold. No signature, modifier, override or throws change; no new type; no reflection; no test edit.
state_passed: the private fields buffer (char[] reference) and size (int value), with the parameters matcher and startIndex, to
hop 1; no write-back (the method writes no field).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Lang-60-probe/w of the fixture, the
first statement of lastIndexOf(StrMatcher, int) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. Full
suite (`defects4j test`): 2 failing tests, both java.lang.IllegalStateException: PROBE-REACHED at StrBuilder.lastIndexOf
(StrBuilder.java:1937): StrBuilderTest::testLastIndexOf_StrMatcher (via lastIndexOf(StrMatcher) at StrBuilder.java:1921, test line
1443) and StrBuilderTest::testLastIndexOf_StrMatcher_int (directly, test line 1460). No production caller reaches the facade except
lastIndexOf(StrMatcher), which no other test calls.

Hosts (host_mode = "1500"; `mr_lib.py preview Lang-60 org/apache/commons/lang/text/StrBuilder.java 5` with the instance seed 2488,
the facade file StrBuilder.java excluded by the draw; used in draw order, nothing substituted):
  hop 1 math.NumberUtils          1628 lines  lastMatchIndex      decision: a null matcher matches nothing (-1)
  hop 2 StringUtils               5008 lines  lastIndexOfMatcher  pass-through
  hop 3 builder.ToStringStyle     2151 lines  lastMatchingIndex   pass-through
  hop 4 time.FastDateFormat       1734 lines  findLastMatch       pass-through
  hop 5 ArrayUtils                4417 lines  lastIndexOfMatch    GOLD: the negative start check, the rounding of a too large start
                                                                  index, the end of the matcher's active area and the backwards
                                                                  scan (the per-position core)
Host newline counts 1628, 5008, 2151, 1734, 4417; the smallest host is NumberUtils (1628 lines, hop 1); the gold host has 4417 lines.
The correct configuration returns the original value for every call: a null matcher gives -1 at hop 1 (the original returns -1 for
it whatever the start index); a negative start index gives -1 in the gold before rounding, and a start index >= length is rounded to
length - 1, which is -1 for an empty builder and then the loop does not run (the original's 'startIndex < 0 after rounding' case);
the active area ends at startIndex + 1 after rounding, as in the original.

Fault (one-line omission in the gold): the statement that ends the matcher's active area just after the (rounded) start index,
`endIndex = startIndex + 1;`, is dropped, so the matcher is given the whole content [0, length) and a match at a position at or
before the start index may use characters after it. The gold then reads as the ordinary routine "round the start index into the
content, scan backwards, ask the matcher against the content". Trigger: the EXISTING test
StrBuilderTest::testLastIndexOf_StrMatcher_int. Its asserts with charMatcher, spaceMatcher, noneMatcher and null still hold
(single-character matchers do not look at the active area), and assertEquals(-1, sb.lastIndexOf(A_NUMBER_MATCHER, 6)) at line 1491
("A matches, 1 is outside bounds") fails with expected:<-1> but was:<6>. It is the only test that newly fails: the other test that
reaches the facade, testLastIndexOf_StrMatcher, only calls lastIndexOf(StrMatcher), whose start index is size, so the rounded start
index is size - 1 and startIndex + 1 == length there; the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the last index at which the matcher matches, searching backwards from the given
index; only the first length characters are searched; the ArrayUtils rules for a negative and a too large start index) and is silent
on the active area. The convention that a backwards search from an index does not let a match use characters after that index is
pinned outside the gold: StrBuilder.lastIndexOf(String, int) starts its loop at startIndex - strLen + 1, so the whole match lies at
or before the start index; StrBuilder.indexOf(StrMatcher, int) bounds the matcher's active area by the searched range
(isMatch(buf, i, startIndex, len)); StrMatcher.isMatch documents bufferStart/bufferEnd as the active area ("Only values in the buffer
between the specifed indices may be accessed"), and StrMatcherTest::testMatcherIndices pins that a match is cut off at bufferEnd
(isMatch(BUFFER2, 1, 0, 2) == 0); passing tests StrBuilderTest::testIndexOf_StrMatcher_int, StrBuilderTest::testLastIndexOf_String_int
and StrMatcherTest::testMatcherIndices.

Single owner: only the gold decides the matcher's active area and runs the matcher; hops 2-4 pass the four values along unchanged
and hop 1 only answers a null matcher. Every hop documents `length` as "the number of characters of the array in use" and the gold
documents that only the first length characters are searched, so a hop cannot narrow the active area without passing a value that
is not the documented length. Declared alternatives (G9), each leaving the trigger failing: hop 1 passes length - 1 (the last
character in use left out; A1 still lies inside the content); hop 2 searches from startIndex - 1 (strictly before the start index;
lastIndexOf(charMatcher('a'), 0) gives -1); hop 4 passes startIndex as the length (the start position itself is rounded away).
Recorded bypass (an edit that redefines a documented argument, not a repair of the chain): a hop passing
Math.min(length, startIndex + 1) as the length makes the trigger pass, but hands the gold a value that is not the number of
characters in use against every hop's and the gold's @param length. Checked on the variant in a scratch copy (at hop 4): trigger
passes, full suite 0 failing tests.

Lie: the facade's javadoc claims the search steps back through the builder a block of characters at a time, testing each block
from its last character before moving to the previous block; the chain tests one position at a time and has no blocks. It names
neither the active area, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: array and matcher are read by isMatch; length seeds endIndex, which bounds the rounding of startIndex; startIndex is
     tested, rounded, ends the active area and starts the loop; none is only argument-checked.
  T2 absent: endIndex is read by the rounding decision, reassigned from the rounded startIndex and read by isMatch; i is the loop
     cursor and is decremented; no literal-initialised local; the negative check returns, the rounding changes startIndex.
  T3 absent: both ends of the start index are treated (negative gives -1, at or beyond length is rounded down); the active area is
     given both ends (0 and endIndex); no enum, type code or named format.
  T4 absent: 'Only the first length characters ... are searched', 'A negative startIndex will return INDEX_NOT_FOUND (-1)', 'A
     startIndex at or beyond length will search from the last character in use' and the @return clause are each met by a line.
 Variant gold (javadoc, signature, `int endIndex = length;`, negative start returns INDEX_NOT_FOUND, start at or beyond endIndex
 rounded to endIndex - 1, backwards loop asking matcher.isMatch(array, i, 0, endIndex), INDEX_NOT_FOUND at the end):
  T1 absent: array and matcher are read by isMatch; length seeds endIndex, which bounds the rounding and is the end of the active
     area; startIndex is tested, rounded and starts the loop; all four change the result.
  T2 absent: endIndex is initialised from the parameter length (not a literal) and read twice; it is a bound computed before the
     loop, not a value the loop moves; i is decremented; no flag, counter or best-so-far; both decisions have effects (return, a
     new startIndex).
  T3 absent: both ends of the start index are treated (negative, at or beyond length); the matcher's active area has both ends
     given (0 and endIndex); the gold names no class it would handle in part.
  T4 absent: 'searching backwards from the given index' is a general description that the loop addresses; 'Only the first length
     characters of the array are searched' is met (the scan starts at most at length - 1 and the active area ends at length); the
     negative and too large start index sentences are met by the two decisions; '@return the last index matched, INDEX_NOT_FOUND
     (-1) if there is no match' is met; the @param clauses name no rule; no inline comment; endIndex holds the end of the
     characters given to the matcher."""

SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
NU = "src/java/org/apache/commons/lang/math/NumberUtils.java"
SU = "src/java/org/apache/commons/lang/StringUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
SM = "org.apache.commons.lang.text.StrMatcher"

GOLD_TEXT = '''/**
 * <p>Finds the last index in the given <code>char</code> array at which the
 * matcher matches, searching backwards from the given index.</p>
 *
 * <p>Only the first <code>length</code> characters of the array are searched.
 * A negative startIndex will return {@link #INDEX_NOT_FOUND} (<code>-1</code>).
 * A startIndex at or beyond <code>length</code> will search from the last
 * character in use.</p>
 *
 * @param array  the array holding the characters to search
 * @param length  the number of characters of the array in use
 * @param matcher  the matcher to use
 * @param startIndex  the start index to traverse backwards from
 * @return the last index matched,
 *  {@link #INDEX_NOT_FOUND} (<code>-1</code>) if there is no match
 */
public static int lastIndexOfMatch(char[] array, int length, StrMatcher matcher, int startIndex) {
    int endIndex = length;
    if (startIndex < 0) {
        return INDEX_NOT_FOUND;
    } else if (startIndex >= endIndex) {
        startIndex = endIndex - 1;
    }
    endIndex = startIndex + 1;
    for (int i = startIndex; i >= 0; i--) {
        if (matcher.isMatch(array, i, 0, endIndex) > 0) {
            return i;
        }
    }
    return INDEX_NOT_FOUND;
}'''

HOP1 = '''/**
 * <p>Finds the last index in a <code>char</code> array at which a matcher
 * matches, searching backwards from the given index.</p>
 *
 * <p>A <code>null</code> matcher matches nothing and returns <code>-1</code>.</p>
 *
 * @param array  the array holding the characters to search
 * @param length  the number of characters of the array in use
 * @param matcher  the matcher to use, may be null
 * @param startIndex  the index to start searching back from
 * @return the last index matched, or <code>-1</code> if there is no match
 */
public static int lastMatchIndex(char[] array, int length, StrMatcher matcher, int startIndex) {
    if (matcher == null) {
        return -1;
    }
    return StringUtils.lastIndexOfMatcher(array, length, matcher, startIndex);
}'''

HOP2 = '''/**
 * <p>Finds the last index in a <code>char</code> array at which a
 * matcher matches, searching backwards from the given index.</p>
 *
 * @param array  the array holding the characters to search
 * @param length  the number of characters of the array in use
 * @param matcher  the matcher to use
 * @param startIndex  the index to start searching back from
 * @return the last index matched, <code>-1</code> if there is no match
 */
public static int lastIndexOfMatcher(char[] array, int length, StrMatcher matcher, int startIndex) {
    return ToStringStyle.lastMatchingIndex(array, length, matcher, startIndex);
}'''

HOP3 = '''/**
 * <p>Finds the last index in a <code>char</code> array at which a
 * matcher matches, searching backwards from the given index.</p>
 *
 * @param array  the array holding the characters to search
 * @param length  the number of characters of the array in use
 * @param matcher  the matcher to use
 * @param startIndex  the index to start searching back from
 * @return the last index matched, <code>-1</code> if there is no match
 */
public static int lastMatchingIndex(char[] array, int length, StrMatcher matcher, int startIndex) {
    return FastDateFormat.findLastMatch(array, length, matcher, startIndex);
}'''

HOP4 = '''/**
 * <p>Finds the last index in a <code>char</code> array at which a
 * matcher matches, searching backwards from the given index.</p>
 *
 * @param array  the array holding the characters to search
 * @param length  the number of characters of the array in use
 * @param matcher  the matcher to use
 * @param startIndex  the index to start searching back from
 * @return the last index matched, <code>-1</code> if there is no match
 */
public static int findLastMatch(char[] array, int length, StrMatcher matcher, int startIndex) {
    return ArrayUtils.lastIndexOfMatch(array, length, matcher, startIndex);
}'''

DESIGN = {
 "instance": "Lang-60", "project": "Lang", "bug_id": 60, "seed": 2488,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "lastIndexOf", "near_line": 1936},
 "facade_variant": "V1",
 "state_passed": "private fields buffer (char[] reference) and size (int value), with the parameters matcher and startIndex, to "
                 "hop 1; no write-back (the method writes no field)",
 "reachability_probe": "full suite with the probe: 2 failing tests, both java.lang.IllegalStateException: PROBE-REACHED at "
                       "StrBuilder.lastIndexOf(StrBuilder.java:1937): StrBuilderTest::testLastIndexOf_StrMatcher (via "
                       "lastIndexOf(StrMatcher), StrBuilder.java:1921) and StrBuilderTest::testLastIndexOf_StrMatcher_int (direct)",
 "host_mode": "1500",
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/text/StrBuilderTest.java",
             "test_class": "org.apache.commons.lang.text.StrBuilderTest", "test_method": "testLastIndexOf_StrMatcher_int"},
 "expected_signature": "expected:<-1> but was:<6>",
 "gold": {"method": "lastIndexOfMatch", "text": GOLD_TEXT,
          "fault": {"old": "            startIndex = endIndex - 1;\n"
                           "        }\n"
                           "        endIndex = startIndex + 1;\n",
                    "new": "            startIndex = endIndex - 1;\n"
                           "        }\n"}},
 "chain": {
   "facade_body": "return org.apache.commons.lang.math.NumberUtils.lastMatchIndex(buffer, size, matcher, startIndex);",
   "lie": "The search steps back through the builder a block of characters at a time, testing each block from its last "
          "character before moving to the previous block.",
   "hops": [
     {"file": NU, "class": "org.apache.commons.lang.math.NumberUtils", "method": "lastMatchIndex",
      "imports": [SM], "text": HOP1},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "lastIndexOfMatcher",
      "imports": ["org.apache.commons.lang.builder.ToStringStyle", SM], "text": HOP2},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "lastMatchingIndex",
      "imports": ["org.apache.commons.lang.time.FastDateFormat", SM], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "findLastMatch",
      "imports": ["org.apache.commons.lang.ArrayUtils", SM], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "lastIndexOfMatch", "imports": [SM], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.text.StrBuilder::lastIndexOf",
              "org.apache.commons.lang.text.StrBuilder::indexOf",
              "org.apache.commons.lang.text.StrMatcher::isMatch"],
 "ownership_reason": "Only the gold decides the matcher's active area and runs the matcher: it rounds the start index into the "
                     "content, ends the active area just after the rounded start index and scans backwards; hops 2-4 pass the "
                     "array, the length in use, the matcher and the start index along unchanged and hop 1 only answers a null "
                     "matcher with -1. Every hop and the gold document length as the number of characters of the array in use, "
                     "so no caller can narrow the active area without passing a value that is not that length. The convention "
                     "that a backwards search from an index does not let a match use characters after that index is pinned "
                     "outside the gold: StrBuilder.lastIndexOf(String, int) starts at startIndex - strLen + 1, so the whole match "
                     "lies at or before the start index; StrBuilder.indexOf(StrMatcher, int) bounds the matcher's active area by "
                     "the searched range (isMatch(buf, i, startIndex, len)); StrMatcher.isMatch documents bufferStart and "
                     "bufferEnd as the active area ('Only values in the buffer between the specifed indices may be accessed'), "
                     "and StrMatcherTest testMatcherIndices pins that a match is cut off at bufferEnd.",
 "ownership_tests": ["org.apache.commons.lang.text.StrMatcherTest::testMatcherIndices",
                     "org.apache.commons.lang.text.StrBuilderTest::testIndexOf_StrMatcher_int",
                     "org.apache.commons.lang.text.StrBuilderTest::testLastIndexOf_String_int"],
 "compensating": {
   "chain": [
     {"file": NU, "old": "return StringUtils.lastIndexOfMatcher(array, length, matcher, startIndex);",
      "new": "return StringUtils.lastIndexOfMatcher(array, length - 1, matcher, startIndex);",
      "why": "hop 1 leaves the last character in use out of the search"},
     {"file": SU, "old": "return ToStringStyle.lastMatchingIndex(array, length, matcher, startIndex);",
      "new": "return ToStringStyle.lastMatchingIndex(array, length, matcher, startIndex - 1);",
      "why": "hop 2 searches strictly before the start index"},
     {"file": FDF, "old": "return ArrayUtils.lastIndexOfMatch(array, length, matcher, startIndex);",
      "new": "return ArrayUtils.lastIndexOfMatch(array, startIndex, matcher, startIndex);",
      "why": "hop 4 passes the start index as the number of characters in use"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts from `mr_lib.py preview Lang-60 org/apache/commons/lang/text/StrBuilder.java 5` with the "
               "instance seed 2488 (the facade file StrBuilder.java is excluded by the draw), used in draw order, none "
               "substituted: math.NumberUtils (hop 1, 1628 lines; the smallest host), StringUtils (hop 2, 5008), "
               "builder.ToStringStyle (hop 3, 2151), time.FastDateFormat (hop 4, 1734), ArrayUtils (hop 5, gold, 4417). All "
               "five are public top-level classes in which a static method compiles (ToStringStyle is abstract, which does not "
               "affect a static method) and that can import the public org.apache.commons.lang.text.StrMatcher. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 2488 + 100 + i (as mr3_spec.py inserts them): hop 1 after `min` "
               "(line 1199, seed 2588), hop 2 after `lastIndexOf` (981, 2589), hop 3 after `appendEnd` (275, 2590), hop 4 after "
               "`getTimeInstance` (389, 2591), hop 5 after `add` (3371, 2592); all in the outer class. The facade calls hop 1 "
               "by its fully-qualified name; each hop imports the next host and StrMatcher. Recorded bypass: a hop passing "
               "Math.min(length, startIndex + 1) as the length passes the trigger but hands on a value that is not the number "
               "of characters in use (checked on the variant at hop 4: trigger passes, full suite 0 failing tests).",
}
