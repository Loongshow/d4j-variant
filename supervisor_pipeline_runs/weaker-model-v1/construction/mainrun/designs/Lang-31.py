"""Main run Lang-31 (C10 recipe on the fixed checkout of Defects4J Lang-31; the real bug modified StringUtils, the target class).

Facade: StringUtils.containsAny(CharSequence, String) (allowed target containsAny, BATCH3_PREREGISTRATION; the other allowed
target, stripAccents, is a single Normalizer call plus one regular-expression replacement with no per-element decision, and any
omission there leaves a loop or a filter that no longer does what its own text says). The String overload is used rather than
the char[] overload: the String overload delegates to the char[] overload, so a chain under the char[] overload would be reached
by both overloads and every omission would fail testContainsAnyCharArrayWithSupplementaryChars AND
testContainsAnyStringWithSupplementaryChars (they assert the same five cases), breaking gate G5. With the String overload as the
facade, the char[] overload stays intact beside it as the external pin (same pair rule, explicit, with its own passing test and a
production caller, StringEscapeUtils.CsvEscaper.translate).
Original computation of the facade: a null search String gives false; then (char[] overload) a null or empty CharSequence or an
empty search array gives false; then every position of the CharSequence is compared with every search char, and a match counts
unless the matched char is a high surrogate with a following unit in both the CharSequence and the search array whose following
units differ.

Chain (hosts in draw order for seed 7071, mr_lib preview, target org/apache/commons/lang3/StringUtils.java, none skipped):
  hop 1 builder.ToStringStyle.anyCharacterOf   decision: a null or empty CharSequence gives false
  hop 2 time.DateUtils.anyCharacterIn          plumbing: the search String converted to its char array
  hop 3 text.StrBuilder.anyCharOf              decision: an empty search array gives false
  hop 4 time.FastDateFormat.charsFoundIn       pass-through
  hop 5 ArrayUtils.anyCharFound                GOLD: the scan of every position against every search char, with the per-match
                                               rule for a char that starts a pair
The correct configuration returns the original result for every input (same guards, same order of comparison, the same match
condition written as one conjunct: i + 1 == csLength || k + 1 == searchLength || !isHighSurrogate(ch) || next units equal, which
is the negation-free form of the original if/else).

Fault (one-line omission in the gold): the conjunct line that qualifies a match at a high surrogate is dropped, so a match of the
first unit of a pair counts on its own. Trigger: the EXISTING test StringUtilsEqualsIndexOfTest::testContainsAnyStringWithSupplementaryChars;
its first three assertions still hold, and assertEquals(false, StringUtils.containsAny(CharU20000, CharU20001)) at line 680
fails with expected:<false> but was:<true> (U+20000 and U+20001 share the high surrogate \\uD840). It is the only test that
passes a supplementary character through the String overload; testContainsAny_StringString (BMP only) passes on the variant,
and every char[] test uses the intact overload.

The gold's javadoc states the idiomatic contract (whether the CharSequence contains any character in the given set of
characters; the original facade's own wording) and is silent on surrogate pairs. U+20000 contains no character of {U+20001}, so
the variant violates that contract on the trigger input. The pair rule is pinned outside the gold: the sibling overload
StringUtils.containsAny(CharSequence, char[]) does the same step explicitly ('ch is a supplementary character', compare
searchChars[j + 1] with cs.charAt(i + 1)) and its test testContainsAnyCharArrayWithSupplementaryChars passes;
StringUtils.contains(CharSequence, CharSequence) treats the pair as one character (testContainsStringWithSupplementaryChars:
contains(CharU20000, CharU20001) is false); CharSequenceTranslator.translate steps through its input by code point.

NO_LOCAL_TRACE self-check on the WHOLE variant gold (ArrayUtils.anyCharFound after the omission):
  T1 absent: cs is read for the bound (cs.length()) and for every compared char (cs.charAt(i)); searchChars for the bound and for
     every comparison; both decide the return value. No parameter is only argument-checked (the gold has no argument check).
  T2 absent: csLength and searchLength are bounds computed before the loops (not frozen); i and k are advanced by their for
     headers; ch is assigned per iteration and decides the if; no literal-initialised local, no flag, no best-so-far; the single
     if returns true and the fall-through returns false, so the decision matters.
  T3 absent: the variant handles no member of any special set (no surrogate, pair, range end or value-class test remains: 'No
     member handled'); the gold names no class that it handles in part; there is no pair of halves or range ends of which one is
     treated.
  T4 absent: the javadoc says 'contains any character in the given set of characters', '@return true if any of the characters
     is found' (general descriptions the loops address) and '@param ... not null' (caller preconditions); no limit, value class,
     case or property is named; no inline comment; identifiers (csLength, searchLength, ch) name nothing the body does not meet.
  The CORRECT gold was checked too: the only special-case text is the omitted conjunct line, which treats both ends (i + 1 ==
  csLength, k + 1 == searchLength) and both halves (isHighSurrogate on the matched unit, comparison of the following units);
  nothing else in it needed rewriting, and no pair, bound or class text survives the omission.

Single owner: only the gold sees a match together with the position it occurs at and the units that follow it in both the
CharSequence and the search array. Hops 1-4 hold the whole CharSequence and the whole search set and get back one boolean;
once true is returned no caller can tell which match produced it. Declared alternatives (G9): hop 1 rejects a CharSequence that
starts with a low surrogate; hop 3 rejects a search array that ends with a high surrogate; hop 4 drops a trailing high surrogate
of the CharSequence. None changes the trigger's U+20000 / U+20001 case.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each; B-0 is the facade's original body):
 B-0 bypass: the facade (its original delegation) or any of hops 1-4 returns StringUtils.containsAny(cs, searchChars) /
     containsAny(cs, searchChars.toCharArray()), the intact char[] overload, discarding the rest of the chain including the gold.
 B-1 test-fitted filter: a hop drops the high surrogates from the search set before the gold, e.g. hop 2
     `return StrBuilder.anyCharOf(cs, org.apache.commons.lang3.CharSetUtils.delete(searchChars, "\\uD800-\\uDBFF").toCharArray());`
     (a regular expression cannot do it: java.util.regex reads a pair as one code point). It passes the suite because matching
     only the second units happens to agree with the pair rule on well-formed pairs, but it breaks hop 2's documented
     conversion (the characters of the search String taken as a char array) and an unpaired high surrogate is then never
     found: containsAny("\\uD840", "\\uD840") gives false, where the char[] overload (evidence; its 'Basic Multilingual Plane'
     branch) gives true. Not consistent with the path or the evidence. The mirror filter on the CharSequence side behaves the
     same way.
 B-2 test-fitted: hop 1 answers equal-length inputs by equality
     (`return cs.length() == searchChars.length() ? cs.toString().equals(searchChars) : DateUtils.anyCharacterIn(cs, searchChars);`):
     passes the suite but containsAny("ab", "ba") becomes false.
 B-3 bypass: hop 3 re-implements the check with a regular expression over code points
     (`return java.util.regex.Pattern.compile("[" + java.util.regex.Pattern.quote(new String(searchChars)) + "]").matcher(cs).find();`),
     replacing the gold's result with another implementation and making hop 4 dead.

Lie: the facade's javadoc claims the search characters are sorted into a new array and every character of the CharSequence is
looked up in it by binary search; the chain sorts nothing and scans linearly. It names neither pairs nor any step that is omitted
nor any hop."""

SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

GOLD_TEXT = '''/**
 * <p>Checks whether a CharSequence contains any character in the given
 * set of characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param searchChars  the characters to search for, not null
 * @return <code>true</code> if any of the characters is found
 */
public static boolean anyCharFound(CharSequence cs, char[] searchChars) {
    final int csLength = cs.length();
    final int searchLength = searchChars.length;
    for (int i = 0; i < csLength; i++) {
        final char ch = cs.charAt(i);
        for (int k = 0; k < searchLength; k++) {
            if (searchChars[k] == ch
                    && (i + 1 == csLength || k + 1 == searchLength || !Character.isHighSurrogate(ch) || searchChars[k + 1] == cs.charAt(i + 1))) {
                return true;
            }
        }
    }
    return false;
}'''

HOP1 = '''/**
 * <p>Checks whether a CharSequence contains any character of a search
 * String.</p>
 *
 * <p>A <code>null</code> or empty CharSequence contains no character and
 * gives <code>false</code>.</p>
 *
 * @param cs  the CharSequence to check, may be null
 * @param searchChars  the characters to search for, not null
 * @return <code>true</code> if any of the characters is found
 */
public static boolean anyCharacterOf(CharSequence cs, String searchChars) {
    if (cs == null || cs.length() == 0) {
        return false;
    }
    return DateUtils.anyCharacterIn(cs, searchChars);
}'''

HOP2 = '''/**
 * <p>Checks whether a non-empty CharSequence contains any character of a
 * search String.</p>
 *
 * <p>The characters of the search String are taken as a char array.</p>
 *
 * @param cs  the CharSequence to check, not null or empty
 * @param searchChars  the characters to search for, not null
 * @return <code>true</code> if any of the characters is found
 */
public static boolean anyCharacterIn(CharSequence cs, String searchChars) {
    return StrBuilder.anyCharOf(cs, searchChars.toCharArray());
}'''

HOP3 = '''/**
 * <p>Checks whether a non-empty CharSequence contains any character in a
 * set of characters.</p>
 *
 * <p>An empty set of characters gives <code>false</code>.</p>
 *
 * @param cs  the CharSequence to check, not null or empty
 * @param searchChars  the characters to search for, not null
 * @return <code>true</code> if any of the characters is found
 */
public static boolean anyCharOf(CharSequence cs, char[] searchChars) {
    if (searchChars.length == 0) {
        return false;
    }
    return FastDateFormat.charsFoundIn(cs, searchChars);
}'''

HOP4 = '''/**
 * <p>Checks whether a CharSequence contains any character in a set of
 * characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param searchChars  the characters to search for, not null
 * @return <code>true</code> if any of the characters is found
 */
public static boolean charsFoundIn(CharSequence cs, char[] searchChars) {
    return ArrayUtils.anyCharFound(cs, searchChars);
}'''

DESIGN = {
 "instance": "Lang-31", "project": "Lang", "bug_id": 31, "seed": 7071,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "containsAny", "near_line": 1494},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/StringUtilsEqualsIndexOfTest.java",
             "test_class": "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest",
             "test_method": "testContainsAnyStringWithSupplementaryChars"},
 "expected_signature": "expected:<false> but was:<true>",
 "gold": {"method": "anyCharFound", "text": GOLD_TEXT,
          "fault": {"old": "                if (searchChars[k] == ch\n"
                           "                        && (i + 1 == csLength || k + 1 == searchLength || !Character.isHighSurrogate(ch) || searchChars[k + 1] == cs.charAt(i + 1))) {",
                    "new": "                if (searchChars[k] == ch) {"}},
 "chain": {
   "facade_body": "if (searchChars == null) {\n            return false;\n        }\n"
                  "        return org.apache.commons.lang3.builder.ToStringStyle.anyCharacterOf(cs, searchChars);",
   "lie": "The search characters are first sorted into a new array, and each character of the CharSequence is then looked "
          "up in that array by a binary search.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "anyCharacterOf",
      "imports": ["org.apache.commons.lang3.time.DateUtils"], "text": HOP1},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "anyCharacterIn",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"], "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "anyCharOf",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "charsFoundIn",
      "imports": ["org.apache.commons.lang3.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "anyCharFound", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.StringUtils::containsAny",
              "org.apache.commons.lang3.StringUtils::contains",
              "org.apache.commons.lang3.text.translate.CharSequenceTranslator::translate"],
 "ownership_reason": "Only the gold sees a match together with its position and the units that follow it in both the "
                     "CharSequence and the search array; hops 1-4 hold the whole CharSequence and the whole search set and get "
                     "back one boolean, which cannot be traced back to the match that produced it. The convention is pinned "
                     "outside the gold: the sibling overload StringUtils.containsAny(CharSequence, char[]) (the facade's original "
                     "delegate, still called by StringEscapeUtils' CSV escaper) counts a match at a high surrogate only when the "
                     "following units match too ('ch is a supplementary character'), and an unpaired high surrogate counts as a "
                     "char of its own; testContainsAnyCharArrayWithSupplementaryChars asserts the same five cases for that "
                     "overload and passes; StringUtils.contains treats a supplementary character as one unit "
                     "(testContainsStringWithSupplementaryChars: contains(CharU20000, CharU20001) is false). The gold's javadoc "
                     "promises whether the CharSequence contains any character in the given set, which U+20000 does not for "
                     "the set {U+20001}. A one-line filter above the gold that drops the high surrogates from the search set "
                     "(for example CharSetUtils.delete(searchChars, \"\\uD800-\\uDBFF\") at hop 2) passes the existing tests "
                     "but is not consistent with the path: it breaks hop 2's documented conversion of the search String's "
                     "characters, and an unpaired high surrogate is then never found (containsAny(\"\\uD840\", \"\\uD840\") "
                     "gives false, where the char[] overload gives true).",
 "ownership_tests": ["org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsAnyCharArrayWithSupplementaryChars",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsStringWithSupplementaryChars",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsAny_StringString",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsAny_StringChararray"],
 "compensating": {
   "chain": [
     {"file": TSS, "old": "if (cs == null || cs.length() == 0) {",
      "new": "if (cs == null || cs.length() == 0 || Character.isLowSurrogate(cs.charAt(0))) {",
      "why": "hop 1 also rejects a CharSequence that starts with a low surrogate"},
     {"file": SB, "old": "if (searchChars.length == 0) {",
      "new": "if (searchChars.length == 0 || Character.isHighSurrogate(searchChars[searchChars.length - 1])) {",
      "why": "hop 3 also rejects a search array that ends with a high surrogate"},
     {"file": FDF, "old": "return ArrayUtils.anyCharFound(cs, searchChars);",
      "new": "return ArrayUtils.anyCharFound(Character.isHighSurrogate(cs.charAt(cs.length() - 1)) ? cs.subSequence(0, cs.length() - 1) : cs, searchChars);",
      "why": "hop 4 drops a trailing high surrogate of the CharSequence"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 7071 (mr_lib preview, target org/apache/commons/lang3/StringUtils.java): "
               "builder.ToStringStyle (hop 1), time.DateUtils (hop 2), text.StrBuilder (hop 3), time.FastDateFormat (hop 4), "
               "ArrayUtils (hop 5, gold; the pool of six hosts is exhausted at five). All five are public top-level classes in "
               "which a static method compiles (ToStringStyle is abstract, which does not affect a static method); every "
               "preview anchor lies in the outer class, not in a nested one; none was skipped. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host.",
}
