"""Main run Lang-57 (C10 recipe on the fixed checkout of Defects4J Lang-57; the real bug modified LocaleUtils, the target class).

Facade: LocaleUtils.toLocale(String) (allowed targets: toLocale, localeLookupList, availableLocaleSet). The other two were set
aside. availableLocaleSet caches its set in a private static field (testAvailableLocaleSet asserts the same instance on two
calls), so its body cannot become a guard plus one delegating call: a hop in another class can neither declare nor write that
field. localeLookupList: every omission in its generalisation steps fails both testLocaleLookupList_Locale and
testLocaleLookupList_LocaleLocale (both hold en_US and en_US_ZZZZ cases), and the only single-test step is appending a default
that differs from the locale, whose omission would leave the default parameter unread or its test without effect (T1/T2).
toLocale has two live tests (testToLocale_3Part is emptied in this checkout); the country code is checked only by
testToLocale_2Part.
Original computation: null -> null; length must be 2, 5 or at least 7; the first two characters lowercase; for longer strings
an underscore at index 2 and two uppercase letters at 3-4; for strings of at least 7 an underscore at index 5; the Locale is
built from substring(0, 2), substring(3, 5) and substring(6).

Chain (hosts in draw order for seed 6925, mr_lib preview, target org/apache/commons/lang/LocaleUtils.java, no substitution):
  hop 1 time.FastDateFormat.parseLocale      decision: the length must be 2, 5 or at least 7
  hop 2 text.StrBuilder.readLocale           decision: the language code (first two characters) must be lowercase
  hop 3 builder.ToStringStyle.localeFor      decision: beyond the language code, an underscore and an uppercase country code
  hop 4 math.NumberUtils.createLocale        decision + placement: an underscore before a variant; the characters as an array
  hop 5 ArrayUtils.localeOfChars             GOLD: the per-character pass that collects the codes (language, country, variant;
                                             the third code keeps any further underscores) and creates the Locale
The correct configuration throws the same IllegalArgumentException message for every input the original rejects, in the same
order of checks, and returns an equal Locale for every input it accepts (the codes the gold collects are exactly substring(0,2),
substring(3,5) and substring(6) once hops 1-4 have checked the shape).

Fault (omission of a state reset in the gold): the line `code = "";` after a finished code is stored is dropped, so the running
code keeps the earlier codes and the country code of "us_EN" becomes "usEN" (Locale upper-cases it to "USEN"). Trigger: the
EXISTING test LocaleUtilsTest::testToLocale_2Part; its first assertion assertValidToLocale("us_EN", "us", "EN") sees country
"USEN". testToLocale_1Part passes (no separator in any accepted input; every rejected input is rejected by hops 1-2), and no
other test reaches toLocale.

The gold's javadoc states the idiomatic contract (a Locale created from the characters of a locale String) and is silent on how
a code ends. The convention is pinned outside the gold: the facade's own javadoc ("en_GB" = new Locale("en", "GB")) and
testToLocale_1Part; StringUtils.split restarts each token after a separator (start = ++i; testSplit_StringChar);
StrTokenizer.tokenize clears its work area for every token (readWithQuotes: workArea.clear(); StrTokenizerTest.testBasic1);
StringEscapeUtils.unescapeJava empties its unicode buffer after each escape (unicode.setLength(0)).

Single owner: only the gold sees the characters one by one and collects the codes. No input a hop can hand on makes a gold that
keeps the earlier codes produce ("us", "EN"): its second code is always the first code followed by the second segment. The value
is created inside the gold, so no caller can post-filter the codes; a valid input cannot be pre-filtered. Declared alternatives
(G9): hop 4 hands on the characters without the underscores; hop 4 hands on only the first five characters; hop 3 hands on the
String without its language code. None passes the trigger.
Recorded bypasses (not declared; they discard the gold's result):
 B-0 the facade or any of hops 1-4 returns new Locale(str.substring(0, 2), ...) built from substrings, as the original did,
     discarding hop 5.
 B-1 hop 3 or hop 4 returns new Locale(str.substring(0, 2), str.substring(3)) for a String of length 5 only (one line): passes the
     full suite (testToLocale_3Part is empty; checked at hop 4 on the variant in a scratch copy: 0 failing tests) but still leaves
     every String with a variant to the gold, and replaces the gold's result with another implementation for length 5
     (test-fitted). The same holds for a hop that keeps only the gold's language and rebuilds the country and variant from
     substrings in one expression.
 B-2 re-cutting the gold's Locale after the call (country.substring(language.length())): needs a local and a length test, and
     reads the gold's documented result as something it is not documented to be.

Lie: the facade's javadoc claims the string is matched against a regular expression compiled once for the class and the codes are
read from the groups of the match; the code checks fixed positions in hops 1-4 and collects the codes in a character loop. It
names no step that is omitted and no hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied first to the correct gold (nothing to rewrite) and then to the
WHOLE variant gold:
 T1 absent: the only parameter `chars` is read in the loop condition and in every iteration (separator test, extension); every
    character changes the codes passed to the Locale.
 T2 absent: (a) `codes` reaches the Locale constructor, `count` indexes the stores and the final store, `code` is read by both
    stores, `i` drives the loop; nothing is dead. (b) no local stays frozen: `count` (literal 0) is advanced by count++ inside the
    loop, `code` (literal "") is reassigned inside the loop (code = code + chars[i]), `i` is advanced. (c) the if/else has two
    different effects (store the running code and advance `count`, or extend the running code); no empty, duplicate or
    frozen-local branch.
 T3 absent: the three codes are all stored the same way (codes[...] = code) and all passed to the Locale; no pair, range ends
    or named class is handled in part; the running code is restarted for no code (no member handled, like a word loop with no
    reset).
 T4 absent: the javadoc says only "Creates a Locale from the characters of a locale String" (a general description the body
    addresses) and "not null" (a caller precondition); no comment; identifiers (codes, count, code, chars, localeOfChars) name no
    rule, limit or value class.
"""

FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
NU = "src/java/org/apache/commons/lang/math/NumberUtils.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
LU = "src/java/org/apache/commons/lang/LocaleUtils.java"

GOLD_TEXT = '''/**
 * <p>Creates a Locale from the characters of a locale String.</p>
 *
 * @param chars  the characters of the locale String, not null
 * @return the Locale
 */
public static Locale localeOfChars(char[] chars) {
    String[] codes = new String[] {"", "", ""};
    int count = 0;
    String code = "";
    for (int i = 0; i < chars.length; i++) {
        if (chars[i] == '_' && count < codes.length - 1) {
            codes[count++] = code;
            code = "";
        } else {
            code = code + chars[i];
        }
    }
    codes[count] = code;
    return new Locale(codes[0], codes[1], codes[2]);
}'''

HOP1 = '''/**
 * <p>Converts a locale String to a Locale.</p>
 *
 * <p>The length of the String must be 2, 5 or at least 7.</p>
 *
 * @param str  the locale String to convert, not null
 * @return a Locale
 * @throws IllegalArgumentException if the string is an invalid format
 */
public static Locale parseLocale(String str) {
    int len = str.length();
    if (len != 2 && len != 5 && len < 7) {
        throw new IllegalArgumentException("Invalid locale format: " + str);
    }
    return StrBuilder.readLocale(str);
}'''

HOP2 = '''/**
 * <p>Converts a locale String of length 2, 5 or at least 7 to a Locale.</p>
 *
 * <p>The language code, the first two characters, must be lowercase.</p>
 *
 * @param str  the locale String to convert, not null
 * @return a Locale
 * @throws IllegalArgumentException if the string is an invalid format
 */
public static Locale readLocale(String str) {
    char ch0 = str.charAt(0);
    char ch1 = str.charAt(1);
    if (ch0 < 'a' || ch0 > 'z' || ch1 < 'a' || ch1 > 'z') {
        throw new IllegalArgumentException("Invalid locale format: " + str);
    }
    return ToStringStyle.localeFor(str);
}'''

HOP3 = '''/**
 * <p>Converts a locale String with a valid language code to a Locale.</p>
 *
 * <p>If the String is longer than the language code, the separator must
 * be an underscore and the country code must be uppercase.</p>
 *
 * @param str  the locale String to convert, not null
 * @return a Locale
 * @throws IllegalArgumentException if the string is an invalid format
 */
public static Locale localeFor(String str) {
    if (str.length() > 2) {
        if (str.charAt(2) != '_') {
            throw new IllegalArgumentException("Invalid locale format: " + str);
        }
        char ch3 = str.charAt(3);
        char ch4 = str.charAt(4);
        if (ch3 < 'A' || ch3 > 'Z' || ch4 < 'A' || ch4 > 'Z') {
            throw new IllegalArgumentException("Invalid locale format: " + str);
        }
    }
    return NumberUtils.createLocale(str);
}'''

HOP4 = '''/**
 * <p>Creates a Locale from a locale String whose language code and
 * country code have been checked.</p>
 *
 * <p>If the String is longer than the country code, the separator before
 * the variant must be an underscore.</p>
 *
 * @param str  the locale String to convert, not null
 * @return a Locale
 * @throws IllegalArgumentException if the string is an invalid format
 */
public static Locale createLocale(String str) {
    if (str.length() > 5 && str.charAt(5) != '_') {
        throw new IllegalArgumentException("Invalid locale format: " + str);
    }
    return ArrayUtils.localeOfChars(str.toCharArray());
}'''

DESIGN = {
 "instance": "Lang-57", "project": "Lang", "bug_id": 57, "seed": 6925,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": LU, "class": "org.apache.commons.lang.LocaleUtils", "method": "toLocale", "near_line": 94},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/LocaleUtilsTest.java",
             "test_class": "org.apache.commons.lang.LocaleUtilsTest", "test_method": "testToLocale_2Part"},
 "expected_signature": "expected:<[]EN> but was:<[US]EN>",
 "gold": {"method": "localeOfChars", "text": GOLD_TEXT,
          "fault": {"old": "                codes[count++] = code;\n"
                           "                code = \"\";",
                    "new": "                codes[count++] = code;"}},
 "chain": {
   "facade_body": "if (str == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang.time.FastDateFormat.parseLocale(str);",
   "lie": "The string is matched against a regular expression compiled once for the class, and the language, the country "
          "and the variant are then read from the groups of the match.",
   "hops": [
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "parseLocale",
      "imports": ["org.apache.commons.lang.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "readLocale",
      "imports": ["java.util.Locale", "org.apache.commons.lang.builder.ToStringStyle"], "text": HOP2},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "localeFor",
      "imports": ["java.util.Locale", "org.apache.commons.lang.math.NumberUtils"], "text": HOP3},
     {"file": NU, "class": "org.apache.commons.lang.math.NumberUtils", "method": "createLocale",
      "imports": ["java.util.Locale", "org.apache.commons.lang.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "localeOfChars",
      "imports": ["java.util.Locale"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.LocaleUtils::toLocale",
              "org.apache.commons.lang.StringUtils::split",
              "org.apache.commons.lang.text.StrTokenizer::tokenize",
              "org.apache.commons.lang.StringEscapeUtils::unescapeJava"],
 "ownership_reason": "Only the gold visits the characters one by one and collects the language code, the country code and the "
                     "variant; hops 1-4 check fixed positions of the String and hand it on. Once the gold has created the Locale, "
                     "the country code it was given cannot be cut back without re-reading the String, and no String a hop can "
                     "hand on makes a collector that keeps the earlier codes return ('us', 'EN'). The convention is pinned outside "
                     "the gold: the facade's javadoc (\"en_GB\" = new Locale(\"en\", \"GB\")); StringUtils.split restarts each "
                     "token after a separator (start = ++i, testSplit_StringChar); StrTokenizer.tokenize clears its work area for "
                     "every token (testBasic1); StringEscapeUtils.unescapeJava empties its unicode buffer after each escape "
                     "(unicode.setLength(0)); testToLocale_1Part pins the language-only form through the same chain.",
 "ownership_tests": ["org.apache.commons.lang.LocaleUtilsTest::testToLocale_1Part",
                     "org.apache.commons.lang.StringUtilsTest::testSplit_StringChar",
                     "org.apache.commons.lang.text.StrTokenizerTest::testBasic1",
                     "org.apache.commons.lang.StringEscapeUtilsTest::testUnescapeJava"],
 "compensating": {
   "chain": [
     {"file": NU, "old": "return ArrayUtils.localeOfChars(str.toCharArray());",
      "new": "return ArrayUtils.localeOfChars(StringUtils.remove(str, '_').toCharArray());",
      "why": "hop 4 hands on the characters without the underscores"},
     {"file": NU, "old": "return ArrayUtils.localeOfChars(str.toCharArray());",
      "new": "return ArrayUtils.localeOfChars(str.substring(0, Math.min(str.length(), 5)).toCharArray());",
      "why": "hop 4 hands on only the language code and the country code"},
     {"file": TSS, "old": "return NumberUtils.createLocale(str);",
      "new": "return NumberUtils.createLocale(str.length() > 2 ? str.substring(3) : str);",
      "why": "hop 3 hands on the String without its language code"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 6925 (mr_lib preview, target org/apache/commons/lang/LocaleUtils.java): "
               "time.FastDateFormat (hop 1), text.StrBuilder (hop 2), builder.ToStringStyle (hop 3), math.NumberUtils (hop 4), "
               "ArrayUtils (hop 5, gold). The draw relaxed both package-distinctness constraints for the last pair (pool of six "
               "large classes in this checkout). All five are public top-level classes in which a static method compiles "
               "(ToStringStyle is abstract, which does not affect a static method); none was skipped. The facade calls hop 1 by "
               "its fully-qualified name; each hop imports java.util.Locale (FastDateFormat already does) and the next host.",
}
