"""Main-run instance Lang-45 (C10 recipe on the fixed checkout of Defects4J Lang-45; target class WordUtils, the class the real
bug modified). Facade: WordUtils.initials(String), the whitespace overload of the pool candidate `initials` (allowed target).

Why this facade. abbreviate (pool rank 1) has no per-element core beyond a single space search: every omission in that search is
either recoverable by a caller (a clamp to the upper limit, a re-parameterised lower limit or a suffix call) or removes the search
outright, so it cannot carry a single-owner gold. The char[] overload initials(String, char[]) is reached by both initials tests
(initials(String) delegates to it with null delimiters, and testInitials_String_charArray's null block repeats testInitials_String
assertion for assertion), so every whitespace-path fault fails two tests (G5); its explicit-delimiter path has no omission-shaped
per-element step (only the empty-array rule, a guard any caller can restore). capitalize(String, char[]) is reached by four tests.
initials(String) is a public static API method called by exactly one existing test (testInitials_String) and by no production code;
its body (originally `return initials(str, null);`) now carries the whitespace initials computation along the chain, and the
untouched char[] overload stays beside it as a sibling implementation of the same convention (external pin).

Computation redistributed along the chain (hosts in draw order, seed 8633, no substitution):
  facade  WordUtils.initials(String)          one delegating call to hop 1 (the original body had no guard of its own)
  hop 1   ToStringStyle.leadingChars          null/empty guard of the original, allocates the half-length buffer and builds the
                                              String from the reported count (aggregation)
  hop 2   DateUtils.fillLeadingChars          pass-through: String -> char[]
  hop 3   StrBuilder.getWordChars             placement: the whole array as the range [0, length)
  hop 4   FastDateFormat.parseWordStarts      pass-through
  gold    StringUtils.copyWordStarts          per-element core: the scan that copies the first character of each whitespace
                                              separated word in the range into the destination and returns the count
Fault (one-line omission in the gold): the whitespace branch no longer leaves the current word (`inWord = false;` dropped; the
branch keeps its `continue`, so it reads as a plain whitespace skip). After the first word every character counts as inside a word,
so only the first word's first character is copied. Trigger: WordUtilsTest::testInitials_String,
initials("Ben John Lee") expected "BJL", got "B" (the earlier assertions null, "", "  ", "I", "i" are unaffected).
It is the only test that newly fails: the chain is reached only through initials(String).
Single owner: the gold's output (one character and a count of 1) carries nothing about the later words; no caller can pre-filter
the input so that one scan yields several word starts (the scan never leaves its first word whatever follows), and no one-line
change at hops 1-4 rebuilds the missing characters. Recorded bypasses (discard the chain): the facade restoring
`return initials(str, null);`, or hop 1 returning WordUtils.initials(str, null). Feeding the gold the initials themselves does not
help (they form one word). Declared alternatives (G9): hop 1 allocates a slot per character, hop 2 trims the String, hop 4 takes
the count from the number of whitespace separated words; none passes the trigger.
Pins outside the gold's javadoc: initials(String, char[]) (null delimiters: lastWasGap = true at every whitespace), capitalize and
uncapitalize (capitalizeNext / uncapitalizeNext = true at every delimiter), swapCase (whitespace flag recomputed per character);
testInitials_String_charArray (null block: "BJL", "BJ", "BJ.L", "iah1"), testCapitalize_String, testUncapitalize_String and
testCapitalizeWithDelimiters_String pass on the variant.
Lie: the facade's documentation claims a two-pass algorithm (count the words, then fill a StringBuffer of that size); the code
makes a single scan into a half-length char buffer."""

HOP1 = '''/**
 * <p>Gets the first character of each word in a String, in order.
 * Words are separated by whitespace, as defined by
 * {@link Character#isWhitespace(char)}.</p>
 *
 * @param str  the String to read, may be null
 * @return the String of first characters, <code>null</code> if null
 *  String input
 */
public static String leadingChars(String str) {
    if (str == null || str.length() == 0) {
        return str;
    }
    char[] buffer = new char[str.length() / 2 + 1];
    int count = DateUtils.fillLeadingChars(str, buffer);
    return new String(buffer, 0, count);
}'''

HOP2 = '''/**
 * <p>Fills a buffer with the first character of each word in a String,
 * in order. Words are separated by whitespace.</p>
 *
 * @param str  the String to read, not null
 * @param buffer  the buffer to fill, large enough for every word
 * @return the number of characters placed in the buffer
 */
public static int fillLeadingChars(String str, char[] buffer) {
    return StrBuilder.getWordChars(str.toCharArray(), buffer);
}'''

HOP3 = '''/**
 * Copies the first character of each word in a character array into a
 * destination array, in order. Words are separated by whitespace.
 *
 * @param chars  the characters to read, not null
 * @param destination  the destination array, large enough for every word
 * @return the number of characters copied
 */
public static int getWordChars(char[] chars, char[] destination) {
    return FastDateFormat.parseWordStarts(chars, 0, chars.length, destination);
}'''

HOP4 = '''/**
 * <p>Copies the first character of each word in a range of a character
 * array into a destination array, in order.</p>
 *
 * @param chars  the characters to read, not null
 * @param start  the index of the first character to read
 * @param end  the index after the last character to read
 * @param destination  the destination array, large enough for every word
 * @return the number of characters copied
 */
public static int parseWordStarts(char[] chars, int start, int end, char[] destination) {
    return StringUtils.copyWordStarts(chars, start, end, destination);
}'''

GOLD_TEXT = '''/**
 * <p>Copies the first character of each word in a range of a character
 * array into a destination array, in order. Words are separated by
 * whitespace, as defined by {@link Character#isWhitespace(char)}.</p>
 *
 * @param chars  the characters to read, not null
 * @param start  the index of the first character to read
 * @param end  the index after the last character to read
 * @param destination  the destination array, large enough for every word
 * @return the number of characters copied
 */
public static int copyWordStarts(char[] chars, int start, int end, char[] destination) {
    int count = 0;
    boolean inWord = false;
    for (int i = start; i < end; i++) {
        char ch = chars[i];
        if (Character.isWhitespace(ch)) {
            inWord = false;
            continue;
        }
        if (!inWord) {
            destination[count++] = ch;
            inWord = true;
        }
    }
    return count;
}'''

SRC = "src/java/org/apache/commons/lang"

DESIGN = {
 "instance": "Lang-45", "project": "Lang", "bug_id": 45, "seed": 8633,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": f"{SRC}/WordUtils.java", "class": "org.apache.commons.lang.WordUtils", "method": "initials", "near_line": 507},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/WordUtilsTest.java",
             "test_class": "org.apache.commons.lang.WordUtilsTest", "test_method": "testInitials_String"},
 "expected_signature": "expected:<B[JL]> but was:<B[]>",
 "gold": {"method": "copyWordStarts", "text": GOLD_TEXT,
          "fault": {"old": "            char ch = chars[i];\n            if (Character.isWhitespace(ch)) {\n                inWord = false;\n                continue;\n            }",
                    "new": "            char ch = chars[i];\n            if (Character.isWhitespace(ch)) {\n                continue;\n            }"}},
 "chain": {
   "facade_body": "return org.apache.commons.lang.builder.ToStringStyle.leadingChars(str);",
   "lie": "The words are counted in a first pass over the String, and a <code>StringBuffer</code> of that size is then filled with the first letter of each word in a second pass.",
   "hops": [
     {"file": f"{SRC}/builder/ToStringStyle.java", "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "leadingChars",
      "imports": ["org.apache.commons.lang.time.DateUtils"], "text": HOP1},
     {"file": f"{SRC}/time/DateUtils.java", "class": "org.apache.commons.lang.time.DateUtils", "method": "fillLeadingChars",
      "imports": ["org.apache.commons.lang.text.StrBuilder"], "text": HOP2},
     {"file": f"{SRC}/text/StrBuilder.java", "class": "org.apache.commons.lang.text.StrBuilder", "method": "getWordChars",
      "imports": ["org.apache.commons.lang.time.FastDateFormat"], "text": HOP3},
     {"file": f"{SRC}/time/FastDateFormat.java", "class": "org.apache.commons.lang.time.FastDateFormat", "method": "parseWordStarts",
      "imports": ["org.apache.commons.lang.StringUtils"], "text": HOP4},
     {"file": f"{SRC}/StringUtils.java", "class": "org.apache.commons.lang.StringUtils", "method": "copyWordStarts", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.WordUtils::initials", "org.apache.commons.lang.WordUtils::capitalize",
              "org.apache.commons.lang.WordUtils::uncapitalize", "org.apache.commons.lang.WordUtils::swapCase"],
 "ownership_reason": "Only the scan in copyWordStarts sees the individual characters and decides where a word starts; every caller sees "
                     "only the copied characters and their count. Once the scan stops leaving a word at whitespace it copies the first "
                     "character of the first word and nothing else, so the starts of the later words are gone: no caller can rebuild them "
                     "from 'B' and a count of 1, and no pre-filtering of the input lets one scan report several word starts. The same "
                     "convention (a whitespace character ends the current word, the next non-whitespace character starts one) is carried "
                     "by the sibling overload initials(String, char[]) with null delimiters (lastWasGap = true at every whitespace), by "
                     "capitalize/uncapitalize (capitalizeNext/uncapitalizeNext = true at every delimiter) and by swapCase; "
                     "testInitials_String_charArray's null block (BJL, BJ, BJ.L, iah1) pins it through the intact overload. Known bypasses "
                     "(W13, not competing repairs): the facade restoring `return initials(str, null);` or hop 1 returning "
                     "WordUtils.initials(str, null), each discarding the chain.",
 "ownership_tests": ["org.apache.commons.lang.WordUtilsTest::testInitials_String_charArray",
                     "org.apache.commons.lang.WordUtilsTest::testCapitalize_String",
                     "org.apache.commons.lang.WordUtilsTest::testUncapitalize_String",
                     "org.apache.commons.lang.WordUtilsTest::testCapitalizeWithDelimiters_String"],
 "compensating": {
   "chain": [
     {"file": f"{SRC}/builder/ToStringStyle.java", "old": "        char[] buffer = new char[str.length() / 2 + 1];",
      "new": "        char[] buffer = new char[str.length()];", "why": "hop 1 allocates a buffer slot for every character"},
     {"file": f"{SRC}/time/DateUtils.java", "old": "        return StrBuilder.getWordChars(str.toCharArray(), buffer);",
      "new": "        return StrBuilder.getWordChars(str.trim().toCharArray(), buffer);", "why": "hop 2 trims the String before reading it"},
     {"file": f"{SRC}/time/FastDateFormat.java", "old": "        return StringUtils.copyWordStarts(chars, start, end, destination);",
      "new": "        return Math.max(StringUtils.copyWordStarts(chars, start, end, destination), StringUtils.split(new String(chars, start, end - start)).length);",
      "why": "hop 4 takes the count from the number of whitespace separated words"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 8633 (mr_lib.py preview Lang-45 org/apache/commons/lang/WordUtils.java): ToStringStyle, "
               "DateUtils, StrBuilder, FastDateFormat, StringUtils. All five are public concrete classes and compile with a public "
               "static hop; no host substituted. The draw notes that hop 5 relaxed the package-distinctness heuristic (pool of 6 "
               "large classes); StringUtils shares the target's package.",
}
