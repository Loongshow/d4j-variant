"""Main run Lang-40 (C10 recipe on the fixed checkout of Defects4J Lang-40; the real bug modified StringUtils, the target class).

Facade: StringUtils.indexOfAny(String, String[]) (allowed batch-3 target "StringUtils.indexOfAny"; pool candidate indexOfAny,
26 lines). The other allowed target, leftPad, was set aside: every step of leftPad(String, int, String) is a function of its
scalar arguments (the null/empty pad normalisation, the "no padding needed" decision, the cyclic copy of the pad String), so any
caller can redo or pre-shape it in one statement (normalise the pad, return early, or pass the pad String already repeated to the
needed length), and the String-pad overload is reached by three tests (testLeftPad_StringIntString, testLeftPad_StringIntChar
through the PAD_LIMIT redirect, testCenter_StringIntString through center). The String[] overload of indexOfAny has no production
caller and exactly one test caller, StringUtilsEqualsIndexOfTest::testIndexOfAny_StringStringarray, so a change of its result
fails only that test (gate G5).
Original computation: return -1 for a null String or a null array; otherwise, over the array, skip a null entry, take
str.indexOf(entry), skip -1, keep the smallest index (initial Integer.MAX_VALUE), and map Integer.MAX_VALUE to -1.

Chain (hosts in draw order for seed 8361, mr_lib preview, target org/apache/commons/lang/StringUtils.java; no substitution):
  facade StringUtils.indexOfAny            guard (null String or null array -> -1), then one call to hop 1
  hop 1 text.StrBuilder.positionOfAny       decision: an empty array gives -1
  hop 2 time.FastDateFormat.findFirst       plumbing: maps the "none" value Integer.MAX_VALUE to -1
  hop 3 builder.ToStringStyle.earliestOf    pass-through
  hop 4 time.DateUtils.earliestMatch        aggregation: the fold over the array in array order (a null entry skipped), each
                                            entry looked for only before the earliest index found so far
  hop 5 ArrayUtils.indexBefore              GOLD: the per-entry search: the first index at which one String occurs in str when
                                            that index is lower than a limit, otherwise the limit; it walks the occurrences of
                                            the entry's first character below the limit and tests each with startsWith
The correct configuration computes exactly the original result for every input: the fold returns the smallest index at which any
non-null entry occurs (indexBefore returns the entry's first index when it is below the running earliest, else the running
earliest, so the fold is a running minimum) and Integer.MAX_VALUE if none occurs; hop 2 maps that to -1; an empty array gives -1
at hop 1 instead of through the sentinel, which is the same value. The first occurrence of a non-empty entry starts with its first
character, so the ascending walk over that character's positions below the limit meets it first; an empty entry occurs at index 0.

Fault (omission in the gold, a special-value step): the empty-String step `if (search.length() == 0) { return 0; }` is dropped,
so an empty entry reaches search.charAt(0). Trigger: the EXISTING test StringUtilsEqualsIndexOfTest::testIndexOfAny_StringStringarray.
Its first eight assertions pass (the three guards, {"ob","ba"} on "foobar" -> 2, the three empty arrays, {"llll"} -> -1); the
assertion indexOfAny("foobar", new String[] {""}) == 0 at StringUtilsEqualsIndexOfTest.java:360 then fails with
java.lang.StringIndexOutOfBoundsException thrown by String.charAt inside the gold. The gold's javadoc states the idiomatic contract
(the first index of search in str if it is lower than limit, otherwise limit; search not null, limit not negative) and is silent on
empty Strings; the empty String occurs at index 0, so the contract requires 0 for limit > 0, and the variant throws instead.

External pins (the convention outside the gold): the facade's own javadoc ("a search array containing "" will return 0 if str is
not null", with the examples indexOfAny("zzabyycdxx", [""]) = 0 and indexOfAny("", [""]) = 0); StringUtils.indexOf(String, String)
delegates to String.indexOf, under which an empty String occurs at index 0 (testIndexOf_String: indexOf("", "") == 0 and
indexOf("aabaabaa", "") == 0); the sibling StringUtils.lastIndexOfAny(String, String[]) treats an empty entry as occurring
(testLastIndexOfAny_StringStringarray: {""} gives 6 on "foobar" and 0 on ""); StringUtils.contains(String, String) reports an
empty String as contained (testContainsString: contains("", "") == true).

Single owner: only the gold looks at the characters of an entry. No caller can pre-shape the input so that the gold never meets
an empty entry and still yields the documented answer: removing an empty entry changes the answer (indexOfAny(s, [""]) is 0, not
-1), and no non-empty String occurs at index 0 of every String (for str = "" only the empty String occurs, so indexOfAny("", [""])
== 0 at line 361 can come from the gold only when the gold gets the empty String). The exception cannot be undone by a caller in
one line (a catch needs a block). Declared alternatives (G9): hop 4 also skips an empty entry (gives -1 for [""] instead of 0);
hop 1 also treats an empty String as having no occurrence (the trigger still throws at line 360); hop 3 passes
StringUtils.stripAll(searchStrs) (an empty entry stays empty).
Recorded bypasses (each answers the empty entry itself, so the gold's result for that entry is never computed; the gold still
breaks its own contract):
 B-1 the facade short-circuits after its guard: `if (ArrayUtils.contains(searchStrs, "")) { return 0; }` - the chain is not run
     at all for any array holding an empty String.
 B-2 hop 4 answers an empty entry itself: `earliest = searchStrs[i].length() == 0 ? 0 : ArrayUtils.indexBefore(...)` - the gold
     is not called for that entry.
 B-3 hop 4 replaces the gold call by its own lookup with String.indexOf (the gold becomes dead).
 B-1 and B-2 were checked on the variant in a scratch copy: the trigger passes and the full suite has 0 failing tests, as
 expected for edits that compute the empty-String answer outside the gold.

Failure form: the variant fails with java.lang.StringIndexOutOfBoundsException thrown by String.charAt, so the trigger's stack trace
lists the whole path (facade, hops 1-4) with the gold as the deepest project frame (ArrayUtils.indexBefore). The gold runs before the
failure as well, on the {"ob","ba"} and {"llll"} assertions, and returns the right values there.

Lie: the facade's javadoc claims the String is read once from its last character back to its first, every search String being
tried at each position, and the position of the last match met is returned; the code instead takes the search Strings one by one in
array order and walks forward through the occurrences of each one's first character below the earliest index found so far. It
names neither empty Strings, nor the omitted step, nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the gold as it reads in the VARIANT and to the correct gold:
 T1 absent: str is the receiver of indexOf and startsWith; search is read by charAt(0) and is the startsWith argument; limit bounds
    the walk and is the value returned when no occurrence is met; every parameter changes the result, none is read only in an
    argument check.
 T2 absent: first feeds both indexOf calls; the cursor pos starts from str.indexOf(first) (not a literal) and is advanced by the
    loop's update clause; the one decision (startsWith) returns the live cursor; both loop conjuncts can end the walk; no empty
    branch, no branches with equal effects, no constant test (the correct gold's empty-String test returns 0 where the variant
    throws, so it is live).
 T3 absent: the two ends of the walked range are both tested (pos >= 0 and pos < limit); the variant has no element-level
    special-value test at all ("no member handled"); the gold's text names no value class.
 T4 absent: "not null" and "not negative" are caller preconditions; "the first index of search in str if it is lower than limit"
    is produced by the ascending walk over the first character's positions below limit with startsWith; "otherwise limit" by the
    final return; the identifiers first, pos and limit match their use."""

SU = "src/java/org/apache/commons/lang/StringUtils.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
DU = "src/java/org/apache/commons/lang/time/DateUtils.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"

GOLD_TEXT = '''/**
 * <p>Finds the first index at which a String occurs in another String,
 * when that index is lower than a limit.</p>
 *
 * @param str  the String to search in, not null
 * @param search  the String to search for, not null
 * @param limit  the index before which the occurrence must start, not negative
 * @return the first index of <code>search</code> in <code>str</code> if it is
 *  lower than <code>limit</code>, otherwise <code>limit</code>
 */
public static int indexBefore(String str, String search, int limit) {
    if (search.length() == 0) {
        return 0;
    }
    final char first = search.charAt(0);
    for (int pos = str.indexOf(first); pos >= 0 && pos < limit; pos = str.indexOf(first, pos + 1)) {
        if (str.startsWith(search, pos)) {
            return pos;
        }
    }
    return limit;
}'''

ARR = ''' * @param str  the String to search in, not null
 * @param searchStrs  the Strings to search for, not null'''

HOP1 = '''/**
 * <p>Finds the first index in a String of any of the Strings in an
 * array.</p>
 *
 * <p>An empty array gives <code>-1</code>.</p>
 *
''' + ARR + '''
 * @return the first index of any of the Strings, -1 if none of them occurs
 */
public static int positionOfAny(String str, String[] searchStrs) {
    if (searchStrs.length == 0) {
        return -1;
    }
    return FastDateFormat.findFirst(str, searchStrs);
}'''

HOP2 = '''/**
 * <p>Finds the first index in a String of any of the Strings in a
 * non-empty array.</p>
 *
 * @param str  the String to search in, not null
 * @param searchStrs  the Strings to search for, not null or empty
 * @return the first index of any of the Strings, -1 if none of them occurs
 */
public static int findFirst(String str, String[] searchStrs) {
    final int index = ToStringStyle.earliestOf(str, searchStrs);
    return index == Integer.MAX_VALUE ? -1 : index;
}'''

HOP3 = '''/**
 * <p>Finds the earliest index in a String at which any of the Strings in
 * an array occurs.</p>
 *
''' + ARR + '''
 * @return the earliest index of any of the Strings,
 *  <code>Integer.MAX_VALUE</code> if none of them occurs
 */
public static int earliestOf(String str, String[] searchStrs) {
    return DateUtils.earliestMatch(str, searchStrs);
}'''

HOP4 = '''/**
 * <p>Finds the earliest index in a String at which any of the Strings in
 * an array occurs.</p>
 *
 * <p>The Strings are taken in array order, each one being looked for
 * only before the earliest index found so far. A <code>null</code>
 * entry is skipped.</p>
 *
''' + ARR + '''
 * @return the earliest index of any of the Strings,
 *  <code>Integer.MAX_VALUE</code> if none of them occurs
 */
public static int earliestMatch(String str, String[] searchStrs) {
    int earliest = Integer.MAX_VALUE;
    for (int i = 0; i < searchStrs.length; i++) {
        if (searchStrs[i] != null) {
            earliest = ArrayUtils.indexBefore(str, searchStrs[i], earliest);
        }
    }
    return earliest;
}'''

DESIGN = {
 "instance": "Lang-40", "project": "Lang", "bug_id": 40, "seed": 8361,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "indexOfAny", "near_line": 1438},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/StringUtilsEqualsIndexOfTest.java",
             "test_class": "org.apache.commons.lang.StringUtilsEqualsIndexOfTest", "test_method": "testIndexOfAny_StringStringarray"},
 "expected_signature": "java.lang.StringIndexOutOfBoundsException",
 "gold": {"method": "indexBefore", "text": GOLD_TEXT,
          "fault": {"old": "        if (search.length() == 0) {\n"
                           "            return 0;\n"
                           "        }\n"
                           "        final char first = search.charAt(0);",
                    "new": "        final char first = search.charAt(0);"}},
 "chain": {
   "facade_body": "if ((str == null) || (searchStrs == null)) {\n            return -1;\n        }\n"
                  "        return org.apache.commons.lang.text.StrBuilder.positionOfAny(str, searchStrs);",
   "lie": "The String is read once from its last character back to its first, every search String being tried at each "
          "position, and the position of the last match met on the way is returned.",
   "hops": [
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "positionOfAny",
      "imports": ["org.apache.commons.lang.time.FastDateFormat"], "text": HOP1},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "findFirst",
      "imports": ["org.apache.commons.lang.builder.ToStringStyle"], "text": HOP2},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "earliestOf",
      "imports": ["org.apache.commons.lang.time.DateUtils"], "text": HOP3},
     {"file": DU, "class": "org.apache.commons.lang.time.DateUtils", "method": "earliestMatch",
      "imports": ["org.apache.commons.lang.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "indexBefore", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.StringUtils::indexOf",
              "org.apache.commons.lang.StringUtils::lastIndexOfAny",
              "org.apache.commons.lang.StringUtils::contains",
              "org.apache.commons.lang.StringUtils::indexOfAny"],
 "ownership_reason": "Only the gold looks at the characters of a search String; the facade guards the null String and array, "
                     "hop 1 decides the empty array, hop 2 maps the 'none' value Integer.MAX_VALUE to -1, hop 3 passes the "
                     "array on and hop 4 folds the entries in array order (a null entry skipped), handing each one with the "
                     "earliest index found so far to the gold. The gold's contract (the first index of search in str if it is "
                     "lower than limit, otherwise limit; search not null) covers the empty String, which occurs at index 0, so "
                     "the gold owes 0 for indexOfAny(\"foobar\", [\"\"]) and throws instead. No caller can pre-shape the input "
                     "so that the gold never meets an empty entry: dropping the entry changes the answer from 0 to -1, and no "
                     "non-empty String occurs at index 0 of every String (for str = \"\" only the empty String does, so "
                     "indexOfAny(\"\", [\"\"]) == 0 can come from the gold only when the gold gets the empty String). An edit "
                     "that answers the empty entry outside the gold (a facade or hop-4 short-circuit returning 0) computes "
                     "that entry's result in place of the gold and is a bypass. The convention is pinned outside the gold: "
                     "the facade's javadoc ('a search array containing \"\" will return 0 if str is not null', with the "
                     "examples [\"\"] -> 0 on \"zzabyycdxx\" and on \"\"); StringUtils.indexOf(String, String) delegates to "
                     "String.indexOf and testIndexOf_String expects indexOf(\"\", \"\") == 0 and indexOf(\"aabaabaa\", \"\") "
                     "== 0; the sibling lastIndexOfAny(String, String[]) treats an empty entry as occurring and "
                     "testLastIndexOfAny_StringStringarray expects 6 for [\"\"] on \"foobar\" and 0 on \"\"; "
                     "StringUtils.contains(String, String) reports an empty String as contained (testContainsString: "
                     "contains(\"\", \"\") == true).",
 "ownership_tests": ["org.apache.commons.lang.StringUtilsEqualsIndexOfTest::testIndexOf_String",
                     "org.apache.commons.lang.StringUtilsEqualsIndexOfTest::testLastIndexOfAny_StringStringarray",
                     "org.apache.commons.lang.StringUtilsEqualsIndexOfTest::testContainsString"],
 "compensating": {
   "chain": [
     {"file": DU, "old": "        if (searchStrs[i] != null) {",
      "new": "        if (searchStrs[i] != null && searchStrs[i].length() > 0) {",
      "why": "hop 4 also skips an empty entry"},
     {"file": SB, "old": "    if (searchStrs.length == 0) {",
      "new": "    if (searchStrs.length == 0 || str.length() == 0) {",
      "why": "hop 1 also treats an empty String as having no occurrence"},
     {"file": TSS, "old": "    return DateUtils.earliestMatch(str, searchStrs);",
      "new": "    return DateUtils.earliestMatch(str, org.apache.commons.lang.StringUtils.stripAll(searchStrs));",
      "why": "hop 3 passes the search Strings through StringUtils.stripAll"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 8361 (mr_lib preview, target org/apache/commons/lang/StringUtils.java): "
               "text.StrBuilder (hop 1, anchor after appendln), time.FastDateFormat (hop 2, after getTimeZone), "
               "builder.ToStringStyle (hop 3, after append), time.DateUtils (hop 4, after round), ArrayUtils (hop 5, gold, "
               "after toPrimitive; last remaining host, the Lang-40 pool has exactly five non-target classes of at least 1500 "
               "lines). All five are public top-level classes in which a public static method compiles (ToStringStyle is "
               "abstract, which does not affect a static method); none was skipped. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host.",
}
