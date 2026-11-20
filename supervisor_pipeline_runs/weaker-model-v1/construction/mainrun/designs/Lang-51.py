"""Main run Lang-51 (C10 recipe on the fixed checkout of Defects4J Lang-51; the real bug modified BooleanUtils, the target class).

Facade: BooleanUtils.toBoolean(String) (allowed targets for this instance: BooleanUtils.xor / toBooleanObject / toBoolean).
The other allowed targets were set aside:
  - xor(boolean[]) is also reached through xor(Boolean[]), so any change of its result fails a primitive and an object test
    together (gate G5); a chain behind xor(Boolean[]) can only carry an "exactly one true" step, and an omission there (the
    second-true exit, which leaves a parity xor) is undone by a one-line pre-filter at any hop
    (ArrayUtils.indexOf(array, TRUE) != ArrayUtils.lastIndexOf(array, TRUE)), and the null-element step by
    ArrayUtils.contains(array, null): neither leaves the gold as the single owner.
  - toBooleanObject(String): its test feeds only the six words, their upper-case forms, "", "oof" and null, so an omission in
    a matching step shows only on "" or on "oof", which a one-line check at any hop (an emptiness test, or a test of the
    second letter) absorbs.
  - the int/Integer/String "specified value" overloads of toBoolean and toBooleanObject are three-way decision cascades with
    no per-element core; any omission there leaves one of the true/false/null siblings untreated (checklist T3).
toBoolean(String) has no production caller and exactly one test caller, BooleanUtilsTest::test_toBoolean_String, so a change
of its result fails only that test (gate G5).

Original computation: an identity fast path for the interned literal "true"; null gives false; a switch on the length (2, 3,
4, otherwise false); per length, an ASCII case-insensitive comparison of the characters with "on", "yes" or "true".

Chain (hosts in draw order for seed 2732, mr_lib preview, target org/apache/commons/lang/BooleanUtils.java, no substitution):
  hop 1 builder.ToStringStyle.isTrueValue      decision: a String of fewer than two or more than four characters is none of
                                               the words (the switch's default branch)
  hop 2 text.StrBuilder.isTrueText             pass-through
  hop 3 ArrayUtils.isTrueLiteral               pass-through
  hop 4 time.FastDateFormat.isTrueToken        pass-through
  hop 5 StringUtils.isTrueWord                 GOLD: a two-cursor scan over the words "true", "on" and "yes": cursor i
                                               names the word being tried, cursor j the character; a matching character
                                               (both folded with Character.toLowerCase) advances j, a mismatch or the end
                                               of either String moves to the next word and restarts j at the first
                                               character; the String is accepted when j has reached the end of both the
                                               word and the String
The facade keeps the null guard (null -> false) and delegates to hop 1. The identity fast path is dropped: "true" is matched
by the scan anyway. The correct configuration gives the original result for every input: Character.toLowerCase maps a
character to one of t, r, u, e, o, n, y, s only from that letter or its ASCII upper case, so the folding equals the
original's ch == 'x' || ch == 'X' tests, and a word is accepted only when the String has its length.

Fault (omission in the gold, a state reset): when the scan moves on to the next word it no longer restarts the character
cursor (the line j = 0 in the mismatch branch is dropped), so the next word is compared only from the position the previous
word reached. The gold still reads as an ordinary scan whose acceptance test requires the end of both the word and the
String. Every word itself is still accepted ("true" is tried first from position 0; "on" and "yes" differ from every earlier
word at the first character, so the cursor is still 0 when they are reached), as is every case variant. A String that shares
a beginning with an earlier word and has the length of a later one is accepted: "tru" reaches position 3 on "true", and
"yes" is then accepted at position 3. Trigger: the EXISTING test BooleanUtilsTest::test_toBoolean_String; every assertion
up to line 333 passes ("yes?", "trux", "yep", "oof", "off" are still rejected), and
assertEquals(false, BooleanUtils.toBoolean("tru")) at BooleanUtilsTest.java:334 fails with "expected:<false> but was:<true>".
The gold's javadoc states the idiomatic contract (the String is one of the words "true", "on" and "yes", ignoring case) and
is silent on how the scan is organised.

External pins (convention outside the gold): the facade's own javadoc ("'true', 'on' or 'yes' (case insensitive) will return
true. Otherwise, false is returned"); the String overload BooleanUtils.toBooleanObject(String) compares the String with each
word as a whole, from its first character, with String.equalsIgnoreCase (BooleanUtilsTest::test_toBooleanObject_String:
"oof" and "" -> null); StrBuilder.equalsIgnoreCase does the same per-character case-insensitive comparison over the whole
content and returns false when the sizes differ (StrBuilderTest::testEqualsIgnoreCase); StrBuilder.indexOf(String, int)
restarts its character cursor at 0 for every candidate position (for (int j = 0; j < strLen; j++) inside the candidate loop;
StrBuilderTest::testIndexOf_String_int).

Single owner: only the gold pairs the String with each word; hop 1 sees the length alone and hops 2-4 pass the String along.
After the gold the answer is a boolean, so nothing can be recovered. A repair above the gold must tell "tru" from "yes":
both have three letters, so no length test at a hop separates them, and a hop has no word table. Declared alternatives
(G9): hop 1 also rejects a String that does not end with a letter, hop 2 passes on only Strings made of letters
(StringUtils.isAlpha), hop 3 lower-cases the String first; each still accepts "tru" (line 334).
Recorded bypasses (one-line edits that pass the full suite but discard or duplicate the gold's matching; B-1 at hop 4 and
B-2 at hop 2, in its "three-character String must start with 'y'" form, were checked on the variant in a scratch copy:
trigger and full suite, 0 failing tests):
 B-0 the facade or any of hops 1-4 returns Boolean.TRUE.equals(BooleanUtils.toBooleanObject(str)), or
     "true".equalsIgnoreCase(str) || "on".equalsIgnoreCase(str) || "yes".equalsIgnoreCase(str), discarding the rest of the
     chain including the gold.
 B-1 a hop pre-filters with the sibling, BooleanUtils.toBooleanObject(str) == Boolean.TRUE && <next hop>(str): the
     whole-String match is then done by the second implementation, and once the conjunct holds the answer is already known,
     so the gold's output carries nothing the pre-filter has not computed.
 B-2 a hop re-encodes part of the word table, for example "a three-character String must start with 'y'"
     (str.length() != 3 || Character.toLowerCase(str.charAt(0)) == 'y'), "a String starting with 't' has four characters",
     or "the last letter is e, n or s": a second copy of the gold's word list (letters and lengths) inside the hop, valid for
     this table only.

Lie: the facade's javadoc claims a case-insensitive hash code of the String is looked up in a precomputed table of the hash
codes of the accepted words; the code scans characters word by word, with no hash. It names neither the cursor nor any
omitted step nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the WHOLE variant gold (the correct gold differs only
by the line j = 0 in the mismatch branch and shows none of the patterns either):
 T1 absent: the only parameter, str, is read in j == str.length(), j < str.length() and str.charAt(j); all of them decide
    the return value.
 T2 absent: words (read for words.length and words[i]), i (initialised 0, advanced by i++ inside the loop, bounds the
    loop), j (initialised 0, advanced by j++ inside the loop, tested and used as the index), word (read in both tests) are
    all live; no local is frozen (i and j are both assigned inside the loop); the acceptance if returns true and the
    if/else has two different effects (advance j, or advance i), so no decision is dead.
 T3 absent: the closed set named in the gold's text ("true", "on", "yes") is in the table and every member is treated by
    the same scan; both Strings get the same Character.toLowerCase folding; both lengths appear in both the bound test
    (j < word.length() && j < str.length()) and the acceptance test (j == word.length() && j == str.length()); there are no
    pair halves or range ends handled on one side only.
 T4 absent: "one of the words "true", "on" and "yes"" and "@return true if the String is one of the words" describe the
    computation and the scan addresses them; for the words the phrase names, each is accepted (case variants too);
    "ignoring case" is met by the folding of both characters; "not null" is a caller precondition."""

SU = "src/java/org/apache/commons/lang/StringUtils.java"
BU = "src/java/org/apache/commons/lang/BooleanUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"

WORDS_DOC = '''/**
 * <p>Checks whether a String is one of the words <code>"true"</code>,
 * <code>"on"</code> and <code>"yes"</code>, ignoring case.</p>
 *
 * @param str  the String to check, not null
 * @return <code>true</code> if the String is one of the words
 */'''

SHORT_DOC = '''/**
 * <p>Checks whether a String of two to four characters is one of the
 * words <code>"true"</code>, <code>"on"</code> and <code>"yes"</code>,
 * ignoring case.</p>
 *
 * @param str  the String to check, not null
 * @return <code>true</code> if the String is one of the words
 */'''

GOLD_TEXT = WORDS_DOC + '''
public static boolean isTrueWord(String str) {
    String[] words = new String[] {"true", "on", "yes"};
    int i = 0;
    int j = 0;
    while (i < words.length) {
        String word = words[i];
        if (j == word.length() && j == str.length()) {
            return true;
        }
        if (j < word.length() && j < str.length()
                && Character.toLowerCase(str.charAt(j)) == Character.toLowerCase(word.charAt(j))) {
            j++;
        } else {
            i++;
            j = 0;
        }
    }
    return false;
}'''

HOP1 = '''/**
 * <p>Checks whether a String is one of the words <code>"true"</code>,
 * <code>"on"</code> and <code>"yes"</code>, ignoring case.</p>
 *
 * <p>A String of fewer than two or more than four characters is none of
 * the words.</p>
 *
 * @param str  the String to check, not null
 * @return <code>true</code> if the String is one of the words
 */
public static boolean isTrueValue(String str) {
    int length = str.length();
    if (length < 2 || length > 4) {
        return false;
    }
    return StrBuilder.isTrueText(str);
}'''

HOP2 = SHORT_DOC + '''
public static boolean isTrueText(String str) {
    return ArrayUtils.isTrueLiteral(str);
}'''

HOP3 = SHORT_DOC + '''
public static boolean isTrueLiteral(String str) {
    return FastDateFormat.isTrueToken(str);
}'''

HOP4 = SHORT_DOC + '''
public static boolean isTrueToken(String str) {
    return StringUtils.isTrueWord(str);
}'''

DESIGN = {
 "instance": "Lang-51", "project": "Lang", "bug_id": 51, "seed": 2732,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": BU, "class": "org.apache.commons.lang.BooleanUtils", "method": "toBoolean", "near_line": 649},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/BooleanUtilsTest.java",
             "test_class": "org.apache.commons.lang.BooleanUtilsTest", "test_method": "test_toBoolean_String"},
 "expected_signature": "expected:<false> but was:<true>",
 "gold": {"method": "isTrueWord", "text": GOLD_TEXT,
          "fault": {"old": "                j++;\n"
                           "            } else {\n"
                           "                i++;\n"
                           "                j = 0;\n"
                           "            }",
                    "new": "                j++;\n"
                           "            } else {\n"
                           "                i++;\n"
                           "            }"}},
 "chain": {
   "facade_body": "if (str == null) {\n            return false;\n        }\n"
                  "        return org.apache.commons.lang.builder.ToStringStyle.isTrueValue(str);",
   "lie": "A case-insensitive hash code of the String is computed first and looked up in a precomputed table of the "
          "hash codes of the accepted words.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "isTrueValue",
      "imports": ["org.apache.commons.lang.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "isTrueText",
      "imports": ["org.apache.commons.lang.ArrayUtils"], "text": HOP2},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "isTrueLiteral",
      "imports": ["org.apache.commons.lang.time.FastDateFormat"], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "isTrueToken",
      "imports": ["org.apache.commons.lang.StringUtils"], "text": HOP4},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "isTrueWord", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.BooleanUtils::toBooleanObject",
              "org.apache.commons.lang.text.StrBuilder::equalsIgnoreCase",
              "org.apache.commons.lang.text.StrBuilder::indexOf"],
 "ownership_reason": "Only the gold pairs the String with each of the words 'true', 'on' and 'yes'; hop 1 sees the length "
                     "alone (and rightly passes on a three-character String such as 'tru', which has the length of 'yes') "
                     "and hops 2-4 pass the String along, so no hop knows the words, and after the gold the answer is a "
                     "boolean. A word matches only as a whole String, compared from its first character: the facade's "
                     "javadoc says 'true', 'on' or 'yes' (case insensitive) give true and anything else false; the String "
                     "overload toBooleanObject(String) compares the String with each word separately using "
                     "String.equalsIgnoreCase (test_toBooleanObject_String: 'oof' and \"\" -> null); "
                     "StrBuilder.equalsIgnoreCase compares the whole content case-insensitively and returns false when the "
                     "sizes differ (testEqualsIgnoreCase); StrBuilder.indexOf(String, int) restarts its character cursor at "
                     "0 for every candidate position (testIndexOf_String_int).",
 "ownership_tests": ["org.apache.commons.lang.BooleanUtilsTest::test_toBooleanObject_String",
                     "org.apache.commons.lang.text.StrBuilderTest::testEqualsIgnoreCase",
                     "org.apache.commons.lang.text.StrBuilderTest::testIndexOf_String_int"],
 "compensating": {
   "chain": [
     {"file": TSS, "old": "if (length < 2 || length > 4) {",
      "new": "if (length < 2 || length > 4 || !Character.isLetter(str.charAt(length - 1))) {",
      "why": "hop 1 also rejects a String that does not end with a letter"},
     {"file": SB, "old": "return ArrayUtils.isTrueLiteral(str);",
      "new": "return org.apache.commons.lang.StringUtils.isAlpha(str) && ArrayUtils.isTrueLiteral(str);",
      "why": "hop 2 passes on only Strings made of letters"},
     {"file": AU, "old": "return FastDateFormat.isTrueToken(str);",
      "new": "return FastDateFormat.isTrueToken(str.toLowerCase());",
      "why": "hop 3 lower-cases the String first"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2732 (mr_lib preview, target org/apache/commons/lang/BooleanUtils.java): "
               "builder.ToStringStyle (hop 1), text.StrBuilder (hop 2), ArrayUtils (hop 3), time.FastDateFormat (hop 4), "
               "StringUtils (hop 5, gold). The Lang-51 host pool holds exactly these five classes above 1500 lines, so "
               "the draw relaxed the distinct-package preference for hops 3-5 (recorded by the draw itself) and n=6 "
               "offers no further host. All five are public classes in which a static method compiles (ToStringStyle "
               "is abstract, which does not affect a static method); none was skipped. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host (StrBuilder already imports ArrayUtils).",
}
