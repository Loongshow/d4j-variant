"""Main run Lang-61__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug without a static facade; fixed
checkout of Defects4J Lang-61, whose real bug modified org.apache.commons.lang.text.StrBuilder, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE section 1).

Facade: StrBuilder.lastIndexOf(StrMatcher matcher, int startIndex) (instance method, allowed candidate "StrBuilder.lastIndexOf" of
BATCH8_PREREGISTRATION.md row 281, facade_planned_by = null, so no facade reuse; near_line 1936). Of the allowed candidates,
StrBuilder.endsWith is planned by Lang-47__i (distinctness preferred) and lastIndexOf(char, int) is reached by four tests through
lastIndexOf(char), lastIndexOf(String) and lastIndexOf(String, int), none of whose behaviours a single existing test isolates. The
matcher overload is reached by exactly two tests (testLastIndexOf_StrMatcher through lastIndexOf(StrMatcher), which passes size,
and testLastIndexOf_StrMatcher_int directly).
Original computation: startIndex >= size is rounded to size - 1; a null matcher or a (rounded) negative index gives -1; otherwise
the index i runs from startIndex down to 0 and the first i with matcher.isMatch(buffer, i, 0, startIndex + 1) > 0 is returned, so
the matcher sees the characters up to and including startIndex as the active area; -1 if none matches.

facade_variant: V1 (state as parameters). The method reads two fields and writes none: the facade keeps the null-matcher part of
the original guard, reads the protected fields buffer (char[]) and size (int) inside StrBuilder (no visibility change) and passes
them with the matcher and startIndex to hop 1, then returns hop 1's result. The chain needs no method of the receiver (V2 not
needed), no private method of StrBuilder (no V4) and no package-private type (StrMatcher is a public abstract class; no V3/V5). No
signature, modifier, override or throws change; no new type; no reflection; no test edit.
state_passed: the fields buffer (char[]) and size (int), with the parameters matcher and startIndex, to hop 1; no field is written,
no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Lang-61-probe of the fixture, the
first statement of lastIndexOf(StrMatcher, int) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`;
defects4j compile OK; full suite (defects4j test): 2 failing tests, both java.lang.IllegalStateException: PROBE-REACHED:
StrBuilderTest::testLastIndexOf_StrMatcher_int (direct call, StrBuilderTest.java:1460) and StrBuilderTest::testLastIndexOf_StrMatcher
(through lastIndexOf(StrMatcher), StrBuilderTest.java:1443). The facade has no other production caller. The facade is reached by an
existing test directly.

Hosts (host_mode = "1500"; `mr_lib.py preview Lang-61 org/apache/commons/lang/text/StrBuilder.java 5`, instance seed 5368; the draw
excludes the facade's file StrBuilder.java, the only facade_files_excluded entry; used in draw order, nothing substituted):
  hop 1 builder.ToStringStyle  2151 lines  lastMatchedIndex   pass-through
  hop 2 ArrayUtils             4417 lines  lastIndexOfMatch   pass-through
  hop 3 math.NumberUtils       1628 lines  lastMatchPosition  pass-through
  hop 4 StringUtils            5008 lines  lastIndexOfMatcher pass-through
  hop 5 time.FastDateFormat    1734 lines  lastMatchIndex     GOLD: rounds an index beyond the characters in use, hands the
                                                              matcher its active area and scans backwards
Host newline counts 2151, 4417, 1628, 5008, 1734; the smallest host is math.NumberUtils (1628 lines); the gold host has 1734 lines.
The correct configuration returns the original result for every input: a null matcher gives -1 in the facade; the correct gold
rounds startIndex >= size to size - 1 as the original, narrows the active area to the characters up to and including the (rounded)
index, and scans from the index down to 0, so a negative index (including the rounded index -1 of an empty builder) runs no
iteration and gives -1, as the original's early return does.

Fault (one-line omission in the gold): the statement `size = startIndex + 1;` that narrows the active area to the characters up to
and including the index is dropped, so the matcher is applied with all the characters in use as its active area and a match
starting at or before the index may run past it. The gold then reads as the ordinary routine "round the index into the characters
in use, scan backwards, apply the matcher within the characters in use". Trigger: the EXISTING test
StrBuilderTest::testLastIndexOf_StrMatcher_int. Its single-character matcher assertions (charMatcher, spaceMatcher, noneMatcher,
null) and assertEquals(-1, sb.lastIndexOf(A_NUMBER_MATCHER, 5)) still hold, and assertEquals(-1, sb.lastIndexOf(A_NUMBER_MATCHER,
6)) on "ab bd A1 junction with A2" (the test's comment: "A matches, 1 is outside bounds") fails with expected:<-1> but was:<6>.
testLastIndexOf_StrMatcher passes on the variant: lastIndexOf(StrMatcher) passes size, the gold rounds it to size - 1, and the
narrowed area startIndex + 1 = size is the variant's area anyway. No other test reaches the facade (probe) and the new hops have no
other caller.

The gold's javadoc states the idiomatic contract in the facade's own words ("to find the last match, searching backwards from the
given index") and is silent on the active area the matcher is given. The convention that a search from an index only sees the
characters up to that index, and that a matcher never matches past the bound it is given, is pinned outside the gold:
StrBuilder.replace(StrMatcher, String, int, int, int) (through replaceImpl, isMatch(buf, i, from, to): matches must lie within
[startIndex, endIndex)), with StrBuilderTest::testReplace_StrMatcher_String_int_int_int_VaryEndIndex passing (replace("aa" matcher,
0, 4) on "aaxaaaayaa" leaves the "aa" at 3..4 alone: "-xaaaayaa"); StrBuilder.lastIndexOf(String, int) starts its scan at
startIndex - strLen + 1, so a found string ends at or before startIndex (StrBuilderTest::testLastIndexOf_String_int passing);
StrBuilder.indexOf(StrMatcher, int), the forward sibling, hands the matcher the bounds of the searched region (isMatch(buf, i,
startIndex, len); StrBuilderTest::testIndexOf_StrMatcher_int passing); StrMatcher.isMatch's contract ("Only values in the buffer
between the specifed indices may be accessed"); the facade's own javadoc ("find the last match searching from the given index") is
kept unchanged apart from the lie.

Single owner: only the gold rounds the index, hands the matcher its active area and scans; the facade only answers a null matcher,
and hops 1-4 pass the four values along. Each hop documents size as the number of characters in use, and every hop passes exactly
that. Declared alternatives (G9), each leaving the trigger failing: hop 1 starts the search one index lower (startIndex - 1: the
match at 0 for index 0 is lost); hop 2 passes size - 1 (the "A1" at 6..7 stays inside the area); hop 3 rounds the index down to
at most size - 2 (the index 6 is unchanged).
Recorded edit that is not consistent with the hops' documentation (and so not an alternative repair): any hop passing
Math.min(size, startIndex + 1) in place of size makes the variant gold behave like the correct one (the gold's rounding then
leaves an index below size unchanged and rounds a larger one exactly as before), but every hop's and the gold's javadoc document
that argument as "the number of characters in use in the buffer", which a narrowed area is not; the edit moves the gold's own step
into a caller under a wrong description. Recorded bypass: B-0, the facade's original body (or any hop re-implementing the scan with
isMatch(buf, i, 0, startIndex + 1)) makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the search runs forwards from the start of the builder, applying the matcher at each index and
keeping the most recent match until the start index is passed; the chain scans backwards from the start index and stops at the first
match. It names neither the matcher's active area, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (startIndex rounded by `startIndex >= size ? size - 1 : startIndex`; `size = startIndex + 1;`; backward loop;
 isMatch(buf, i, 0, size); return -1):
  T1 absent: matcher decides the return; buf is handed to the matcher; size is read by the rounding before it is reassigned, so
     its value moves the start of the scan; startIndex is rounded and starts the loop and gives the area end.
  T2 absent: the reassigned parameters startIndex and size are read by the loop and by every isMatch call; i is the loop cursor
     and is decremented; no literal-initialised local; the ternary has two different outcomes; the one if returns i or continues.
  T3 absent: both ends of the index range are treated (an index at or beyond the characters in use is rounded to the last one,
     and the loop ends below 0, so a negative index finds nothing); no enumeration, case set or pair half is left out.
  T4 absent: "rounded to the last character in use" is the ternary; "A negative index finds nothing" is the loop guard and the
     final return; "the last match, searching backwards from the given index" the loop from startIndex down with the first-match
     return; "-1 if not found" the final return; no inline comment; identifiers name what they hold.
 Variant gold (javadoc, signature, `startIndex = (startIndex >= size ? size - 1 : startIndex);`, then `for (int i = startIndex;
 i >= 0; i--)` with `matcher.isMatch(buf, i, 0, size) > 0` returning i, then `return -1`):
  T1 absent: matcher's result decides the return; buf and size are passed to every isMatch call and size also rounds the index;
     startIndex is rounded and starts the loop; no parameter is only argument-checked (there is no argument check).
  T2 absent: the reassigned parameter startIndex is read by the loop initialiser; the only local, the cursor i, is initialised
     from it and decremented by the loop; no literal-initialised local; the ternary gives size - 1 or the index (different
     values); the single if returns i or lets the scan continue (different effects).
  T3 absent: the index range has both ends treated (the upper end by the rounding to size - 1, the lower end by the loop guard
     i >= 0, which the javadoc states as "A negative index finds nothing"); the matcher is given 0 and size, the two ends of the
     characters in use, for every index, with neither end given a treatment the other lacks; the gold has no branch over kinds of
     characters and its text names no class it would handle in part.
  T4 absent: "An index beyond the characters in use is rounded to the last character in use" is the ternary; "A negative index
     finds nothing" is met by the loop guard and `return -1`; "Searches a character buffer using a matcher to find the last
     match, searching backwards from the given index" is a general description that the loop from startIndex down and the
     first-match return address; "@return the last index matched, or -1 if not found" is met by the two returns; "@param size  the
     number of characters in use in the buffer" describes what the caller supplies; no inline comment; the name lastMatchIndex
     names what is returned."""

SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
NU = "src/java/org/apache/commons/lang/math/NumberUtils.java"
SU = "src/java/org/apache/commons/lang/StringUtils.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
SM = "org.apache.commons.lang.text.StrMatcher"

GOLD_TEXT = '''/**
 * <p>Searches a character buffer using a matcher to find the last match,
 * searching backwards from the given index.</p>
 *
 * <p>An index beyond the characters in use is rounded to the last
 * character in use. A negative index finds nothing.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param buf  the character buffer
 * @param size  the number of characters in use in the buffer
 * @param startIndex  the index to search backwards from
 * @return the last index matched, or -1 if not found
 */
public static int lastMatchIndex(StrMatcher matcher, char[] buf, int size, int startIndex) {
    startIndex = (startIndex >= size ? size - 1 : startIndex);
    size = startIndex + 1;
    for (int i = startIndex; i >= 0; i--) {
        if (matcher.isMatch(buf, i, 0, size) > 0) {
            return i;
        }
    }
    return -1;
}'''

HOP1 = '''/**
 * <p>Searches the characters of a buffer using a matcher to find the
 * last match, searching backwards from the given index.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param buf  the character buffer
 * @param size  the number of characters in use in the buffer
 * @param startIndex  the index to start at
 * @return the last index matched, or -1 if not found
 */
public static int lastMatchedIndex(StrMatcher matcher, char[] buf, int size, int startIndex) {
    return ArrayUtils.lastIndexOfMatch(matcher, buf, size, startIndex);
}'''

HOP2 = '''/**
 * <p>Finds the last index in the given character array at which the
 * matcher matches, searching backwards from the given index.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param array  the character array to search through
 * @param size  the number of characters in use in the array
 * @param startIndex  the index to search backwards from
 * @return the last index matched, or <code>-1</code> if not found
 */
public static int lastIndexOfMatch(StrMatcher matcher, char[] array, int size, int startIndex) {
    return NumberUtils.lastMatchPosition(matcher, array, size, startIndex);
}'''

HOP3 = '''/**
 * <p>Finds the position of the last match of a matcher in a character
 * array, searching backwards from the given position.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param chars  the characters to search
 * @param size  the number of characters in use
 * @param startIndex  the position to search backwards from
 * @return the position of the last match, or -1 if not found
 */
public static int lastMatchPosition(StrMatcher matcher, char[] chars, int size, int startIndex) {
    return StringUtils.lastIndexOfMatcher(matcher, chars, size, startIndex);
}'''

HOP4 = '''/**
 * <p>Finds the last index within a character array at which the matcher
 * matches, searching backwards from the given index.</p>
 *
 * @param matcher  the matcher to use, not null
 * @param chars  the characters to search
 * @param size  the number of characters in use
 * @param startIndex  the index to search backwards from
 * @return the last index matched, -1 if no match
 */
public static int lastIndexOfMatcher(StrMatcher matcher, char[] chars, int size, int startIndex) {
    return FastDateFormat.lastMatchIndex(matcher, chars, size, startIndex);
}'''

DESIGN = {
 "instance": "Lang-61", "project": "Lang", "bug_id": 61, "seed": 5368,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "lastIndexOf", "near_line": 1936},
 "facade_variant": "V1",
 "state_passed": "fields buffer (char[]) and size (int), with the parameters matcher and startIndex, to hop 1; no write-back",
 "host_mode": "1500",
 "reachability_probe": "full suite with the probe: 2 failing tests, both java.lang.IllegalStateException: PROBE-REACHED: "
                       "testLastIndexOf_StrMatcher_int (direct, StrBuilderTest.java:1460) and testLastIndexOf_StrMatcher "
                       "(through lastIndexOf(StrMatcher), StrBuilderTest.java:1443)",
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/text/StrBuilderTest.java",
             "test_class": "org.apache.commons.lang.text.StrBuilderTest", "test_method": "testLastIndexOf_StrMatcher_int"},
 "expected_signature": "expected:<-1> but was:<6>",
 "gold": {"method": "lastMatchIndex", "text": GOLD_TEXT,
          "fault": {"old": "    public static int lastMatchIndex(StrMatcher matcher, char[] buf, int size, int startIndex) {\n"
                           "        startIndex = (startIndex >= size ? size - 1 : startIndex);\n"
                           "        size = startIndex + 1;\n",
                    "new": "    public static int lastMatchIndex(StrMatcher matcher, char[] buf, int size, int startIndex) {\n"
                           "        startIndex = (startIndex >= size ? size - 1 : startIndex);\n"}},
 "chain": {
   "facade_body": "if (matcher == null) {\n"
                  "            return -1;\n"
                  "        }\n"
                  "        return org.apache.commons.lang.builder.ToStringStyle.lastMatchedIndex(matcher, buffer, size, startIndex);",
   "lie": "The search runs forwards from the start of the builder, applying the matcher at each index and keeping the most "
          "recent match until the start index is passed.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "lastMatchedIndex",
      "imports": ["org.apache.commons.lang.ArrayUtils", SM], "text": HOP1},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "lastIndexOfMatch",
      "imports": ["org.apache.commons.lang.math.NumberUtils", SM], "text": HOP2},
     {"file": NU, "class": "org.apache.commons.lang.math.NumberUtils", "method": "lastMatchPosition",
      "imports": [SM], "text": HOP3},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "lastIndexOfMatcher",
      "imports": ["org.apache.commons.lang.time.FastDateFormat", SM], "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "lastMatchIndex",
      "imports": [SM], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.text.StrBuilder::replace",
              "org.apache.commons.lang.text.StrBuilder::lastIndexOf",
              "org.apache.commons.lang.text.StrBuilder::indexOf"],
 "ownership_reason": "Only the gold rounds the index, hands the matcher its active area and scans: the facade "
                     "answers a null matcher, and hops 1-4 pass the matcher, the buffer, the number of characters in use and the index along unchanged; "
                     "every hop documents and passes size as the number of characters in use in the buffer. The gold promises "
                     "the last match searching backwards from the given index, in the facade's own words; StrBuilder's "
                     "convention is that such a search only sees the characters up to and including the index (the trigger's "
                     "own comment: 'A matches, 1 is outside bounds'), so returning the 'A1' that starts at 6 and runs to 7 for "
                     "index 6 breaks the gold's contract while every caller passes documented values. The convention is pinned "
                     "outside the gold: StrBuilder.replace(StrMatcher, String, int, int, int) gives the matcher the bounds of "
                     "the replaced region (replaceImpl: isMatch(buf, i, from, to)), so a match running past the end index is "
                     "not taken (StrBuilderTest testReplace_StrMatcher_String_int_int_int_VaryEndIndex: replacing \"aa\" in "
                     "\"aaxaaaayaa\" up to index 4 gives \"-xaaaayaa\"); StrBuilder.lastIndexOf(String, int) starts at "
                     "startIndex - strLen + 1 so that a found string ends at or before the index (testLastIndexOf_String_int); "
                     "the forward sibling StrBuilder.indexOf(StrMatcher, int) hands the matcher the bounds of the searched "
                     "region (testIndexOf_StrMatcher_int); StrMatcher.isMatch allows access only between the given indices. "
                     "Narrowing the area in a caller would need a hop to pass something other than the documented number of "
                     "characters in use.",
 "ownership_tests": ["org.apache.commons.lang.text.StrBuilderTest::testReplace_StrMatcher_String_int_int_int_VaryEndIndex",
                     "org.apache.commons.lang.text.StrBuilderTest::testLastIndexOf_String_int",
                     "org.apache.commons.lang.text.StrBuilderTest::testIndexOf_StrMatcher_int"],
 "compensating": {
   "chain": [
     {"file": TSS, "old": "return ArrayUtils.lastIndexOfMatch(matcher, buf, size, startIndex);",
      "new": "return ArrayUtils.lastIndexOfMatch(matcher, buf, size, startIndex - 1);",
      "why": "hop 1 starts the search one index below the given index"},
     {"file": AU, "old": "return NumberUtils.lastMatchPosition(matcher, array, size, startIndex);",
      "new": "return NumberUtils.lastMatchPosition(matcher, array, size - 1, startIndex);",
      "why": "hop 2 leaves the last character in use out of the area"},
     {"file": NU, "old": "return StringUtils.lastIndexOfMatcher(matcher, chars, size, startIndex);",
      "new": "return StringUtils.lastIndexOfMatcher(matcher, chars, size, Math.min(startIndex, size - 2));",
      "why": "hop 3 rounds the index down to at most two below the number of characters in use"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts from the recipe's seeded draw, mr_lib.py preview Lang-61 "
               "org/apache/commons/lang/text/StrBuilder.java 5 with the instance seed 5368 (the facade's file StrBuilder.java is "
               "excluded), used in draw order, none substituted: builder.ToStringStyle (hop 1, 2151 lines), ArrayUtils (hop 2, "
               "4417), math.NumberUtils (hop 3, 1628; the smallest host), StringUtils (hop 4, 5008), time.FastDateFormat (hop "
               "5, gold, 1734). All five are public top-level classes in which a static method compiles (ToStringStyle is "
               "abstract, which does not affect a static method). Anchors from stageB_lib.pick_insertion_anchor with seed 5368 "
               "+ 100 + i (as mr3_spec.py inserts them): hop 1 after `append` (line 586, seed 5468), hop 2 after `toObject` "
               "(2473, 5469), hop 3 after `stringToInt` (153, 5470), hop 4 after `split` (2040, 5471), hop 5 after "
               "`getDateInstance` (264, 5472); all in the outer class. The facade calls hop 1 by its fully-qualified name; each "
               "hop imports the next host and the public type org.apache.commons.lang.text.StrMatcher.",
}
