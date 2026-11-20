"""Main run Lang-14 (C10 recipe on the fixed checkout of Defects4J Lang-14; the real bug modified StringUtils).

Facade: StringUtils.containsNone(CharSequence, String). The pool candidate is the containsNone family; the char[] overload (the
28-line body) cannot carry a unique trigger, because the String overload delegates to it and every char[] test has an
assertion-for-assertion String mirror (testContainsNone_CharArray* vs testContainsNone_String*), and escapeCsv's two tests are
mirrors too; any fault there fails at least two tests (gate G5). The String overload is the same public static API method, called
by three existing tests and no production code; its body keeps its own guard and delegates to hop 1 instead of the char[] overload,
so the chain now carries the containsNone computation for the String API, and the untouched char[] overload stays beside it as a
sibling implementation of the same convention (external pin).

Chain (hosts in draw order, seed 5652): hop 1 FastDateFormat.excludesAll = the scan over positions (fold: false at the first
position that holds a search char); hop 2 StrBuilder.foundAt = pass-through; hop 3 DateUtils.inSetAt = reads whether the char at
the index is a high surrogate (placement step); hop 4 ToStringStyle.listedAt = pass-through; hop 5 (gold) ArrayUtils.occursAt =
the per-position membership test, with the surrogate-pair convention of the char[] overload: a high surrogate that matches a
search char which is not the last one counts only if the text continues with the search char that follows it.

Fault (omission in the gold): the comparison of the following unit is dropped, so a high surrogate that is in the search set
counts as found whatever low surrogate follows it. Trigger: StringUtilsEqualsIndexOfTest::testContainsNone_StringWithSupplementaryChars
(containsNone(U+20000, U+20001 as String) expected true, got false). The Bad-supplementary String test stays green (the end-of-text
skip and the trailing-high-surrogate rule are untouched), the BMP test is unaffected, and the char[] tests use the intact overload.
The gold's javadoc states only the membership contract (quiet). Pins: StringUtils.containsNone(CharSequence, char...) and
containsAny(CharSequence, char...) carry the explicit pair comparison; indexOfAny too; testContainsNone_CharArrayWithSupplementaryChars
(identical assertions, passing) and testContainsAny_*SupplementaryChars pin it in tests.

Single owner: the trigger input needs a membership verdict that depends on both units and on the position of the match in the
search set; the scan, the pass-throughs and the high-surrogate flag cannot produce it in one line. The declared alternatives
(scan skips pair starts, hop 2 moves a pair start to its low surrogate, hop 4 additionally requires the low surrogate) pass the
trigger but break the trailing-high-surrogate convention (testContainsNone_StringWithBadSupplementaryChars). Bypasses that discard
the chain (facade or hop 1 calling the char[] overload containsNone(cs, chars)) exist and are recorded.

Recorded bypasses found by the builder (both pass the full suite on the variant; checked in a scratch copy):
 B-1 hop 1 (FastDateFormat.excludesAll) overrides the chain's verdict at every pair start:
     `if (StrBuilder.foundAt(cs, i, searchChars) && (!Character.isHighSurrogate(cs.charAt(i)) || i == csLen - 1
      || searchChars[searchChars.length - 1] == cs.charAt(i))) {`
     For a pair start only the trailing-high-surrogate rule survives, so the gold's pair handling is dead (with the correct gold
     too); it relies on the low surrogate of a matching pair being found on its own at the next position, which holds for every
     well-formed text, so no existing test separates it.
 B-2 hop 4 (ToStringStyle.listedAt) re-implements pair membership after the gold:
     `return ArrayUtils.occursAt(cs, index, searchChars, high) && (!high || index == cs.length() - 1
      || searchChars[searchChars.length - 1] == cs.charAt(index) || new String(searchChars).contains(cs.subSequence(index, index + 2)));`
     At a pair start the added clause alone decides, replacing the gold's result with a second implementation.
 B-0 facade: `return containsNone(cs, invalidChars.toCharArray());` (the pre-chain delegation) makes all five hops dead."""

SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

GOLD_TEXT = '''/**
 * <p>Checks whether the character at an index of a CharSequence is one of
 * a set of characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param index  the index of the character to check
 * @param searchChars  the chars to search for, not null
 * @param high  whether the character at the index is a high surrogate
 * @return {@code true} if the character is one of the search chars
 */
public static boolean occursAt(final CharSequence cs, final int index, final char[] searchChars, final boolean high) {
    final char ch = cs.charAt(index);
    final int csLast = cs.length() - 1;
    final int searchLast = searchChars.length - 1;
    for (int j = 0; j <= searchLast; j++) {
        if (searchChars[j] != ch) {
            continue;
        }
        if (high && j < searchLast) {
            if (index == csLast) {
                continue;
            }
            if (searchChars[j + 1] != cs.charAt(index + 1)) {
                continue;
            }
        }
        return true;
    }
    return false;
}'''

AT_DOC = '''/**
 * <p>Checks whether the character at an index of a CharSequence is one of
 * a set of characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param index  the index of the character to check
 * @param searchChars  the chars to search for, not null'''

DESIGN = {
 "instance": "Lang-14", "project": "Lang", "bug_id": 14, "seed": 5652,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "containsNone", "near_line": 1897},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/StringUtilsEqualsIndexOfTest.java",
             "test_class": "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest",
             "test_method": "testContainsNone_StringWithSupplementaryChars"},
 "expected_signature": "expected:<true> but was:<false>",
 "gold": {"method": "occursAt", "text": GOLD_TEXT,
          "fault": {"old": "                if (index == csLast) {\n                    continue;\n                }\n"
                           "                if (searchChars[j + 1] != cs.charAt(index + 1)) {\n                    continue;\n                }",
                    "new": "                if (index == csLast) {\n                    continue;\n                }"}},
 "chain": {
   "facade_body": "if (cs == null || invalidChars == null) {\n            return true;\n        }\n"
                  "        return org.apache.commons.lang3.time.FastDateFormat.excludesAll(cs, invalidChars.toCharArray());",
   "lie": "The invalid characters are first sorted into a lookup table, and the CharSequence is then read from its last "
          "character back to its first, each character being located in that table by a binary search.",
   "hops": [
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "excludesAll",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"],
      "text": '''/**
 * <p>Checks that a CharSequence contains none of a set of characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param searchChars  the chars to search for, not null
 * @return {@code true} if none of the search chars is found
 */
public static boolean excludesAll(final CharSequence cs, final char[] searchChars) {
    final int csLen = cs.length();
    for (int i = 0; i < csLen; i++) {
        if (StrBuilder.foundAt(cs, i, searchChars)) {
            return false;
        }
    }
    return true;
}'''},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "foundAt",
      "imports": ["org.apache.commons.lang3.time.DateUtils"],
      "text": AT_DOC + '''
 * @return {@code true} if the character is one of the search chars
 */
public static boolean foundAt(final CharSequence cs, final int index, final char[] searchChars) {
    return DateUtils.inSetAt(cs, index, searchChars);
}'''},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "inSetAt",
      "imports": ["org.apache.commons.lang3.builder.ToStringStyle"],
      "text": AT_DOC + '''
 * @return {@code true} if the character is one of the search chars
 */
public static boolean inSetAt(final CharSequence cs, final int index, final char[] searchChars) {
    final boolean high = Character.isHighSurrogate(cs.charAt(index));
    return ToStringStyle.listedAt(cs, index, searchChars, high);
}'''},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "listedAt",
      "imports": ["org.apache.commons.lang3.ArrayUtils"],
      "text": AT_DOC + '''
 * @param high  whether the character at the index is a high surrogate
 * @return {@code true} if the character is one of the search chars
 */
public static boolean listedAt(final CharSequence cs, final int index, final char[] searchChars, final boolean high) {
    return ArrayUtils.occursAt(cs, index, searchChars, high);
}'''},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "occursAt", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.StringUtils::containsNone", "org.apache.commons.lang3.StringUtils::containsAny",
              "org.apache.commons.lang3.StringUtils::indexOfAny"],
 "ownership_reason": "Only the per-position membership test sees both units of a surrogate pair together with the search set; "
                     "the scan, the two pass-throughs and the high-surrogate flag pass the position along and cannot turn a "
                     "membership verdict that ignores the following unit into one that depends on it with a one-line change "
                     "without breaking the trailing-high-surrogate rule. The char[] overload containsNone(CharSequence, char...) "
                     "(intact, beside the facade) and containsAny(CharSequence, char...) compare the following unit explicitly "
                     "('if (i < csLast && searchChars[j + 1] == cs.charAt(i + 1))'), indexOfAny does the same, and "
                     "testContainsNone_CharArrayWithSupplementaryChars asserts the identical expectations through that overload.",
 "ownership_tests": ["org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsNone_CharArrayWithSupplementaryChars",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsNone_StringWithBadSupplementaryChars",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsNone_String",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsAny_StringWithSupplementaryChars",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testIndexOfAny_StringCharArrayWithSupplementaryChars"],
 "compensating": {
   "chain": [
     {"file": FDF, "old": "if (StrBuilder.foundAt(cs, i, searchChars)) {",
      "new": "if (!Character.isHighSurrogate(cs.charAt(i)) && StrBuilder.foundAt(cs, i, searchChars)) {",
      "why": "hop 1 scan leaves a pair start to its low surrogate"},
     {"file": SB, "old": "return DateUtils.inSetAt(cs, index, searchChars);",
      "new": "return DateUtils.inSetAt(cs, Character.isHighSurrogate(cs.charAt(index)) && index < cs.length() - 1 ? index + 1 : index, searchChars);",
      "why": "hop 2 checks a pair start by its low surrogate"},
     {"file": TSS, "old": "return ArrayUtils.occursAt(cs, index, searchChars, high);",
      "new": "return ArrayUtils.occursAt(cs, index, searchChars, high) && (!high || index == cs.length() - 1 || ArrayUtils.occursAt(cs, index + 1, searchChars, false));",
      "why": "hop 4 additionally requires the low surrogate of a pair to be a search char"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 5652 (mr_lib preview, n=5): FastDateFormat, StrBuilder, DateUtils, ToStringStyle, "
               "ArrayUtils; all five are public concrete classes and every hop compiles there, so no host was skipped. "
               "Facade is the String overload of the pool's containsNone (see module docstring: the char[] overload has a String "
               "mirror for every test, so no fault in it fails exactly one test).",
}
