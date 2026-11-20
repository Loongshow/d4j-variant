"""Main run Lang-11 (C10 recipe on the fixed checkout of Defects4J Lang-11; the real bug modified RandomStringUtils, and its fix
added the end <= start check to the seven-argument random(int, int, int, boolean, boolean, char[], Random)).

Facade: RandomStringUtils.random(int, int, int, boolean, boolean, char[], Random), the core overload of the pool's `random`
candidate. The two pool entries are the 5-line dispatchers random(int, String) and random(int, char...); neither can carry a
valid instance: their only tests use ASCII sets ("abcdefg", "stuvwxyz") or a null set (length / inequality checks only), so no
per-element omission in a chain behind them fails a test deterministically, and the only remaining failures are guard omissions
(count < 0, empty set), which are not per-element. The seven-argument overload is the same public static API method name, called
directly by three existing tests (testRandomStringUtils, testLANG805, testExceptions) and by every other overload. Its body keeps
its own argument guard (count == 0 / count < 0 / empty chars) and delegates to hop 1.

Chain (hosts in draw order, seed 5957, mr_lib preview n=5, no substitution):
  hop 1 time.DateUtils.drawString        decision: resolves the default range (whole chars set; all values when neither letters
                                         nor numbers; ' '..'z' otherwise) and rejects end <= start (the LANG-807 check)
  hop 2 text.StrBuilder.drawnText        aggregation: turns the drawn array into the String, passes gap = end - start
  hop 3 ArrayUtils.drawnChars            placement: allocates the count-sized buffer and returns it once filled
  hop 4 builder.ToStringStyle.drawInto   pass-through
  hop 5 StringUtils.fillDrawn            GOLD: the per-draw loop (draw at a random offset in the range, decide whether the drawn
                                         character may be used, surrogate pairing, private-high-surrogate skip, write from the
                                         last position to the first)
The chain performs the original computation in the original order and consumes the Random in the same sequence (one nextInt per
draw, one extra nextInt(128) per surrogate partner), so the correct configuration is behaviour-preserving for every caller,
seeded ones included.

Fault (omission in the gold): the digits-only case of the usability decision is dropped (the `else if (numbers)` branch with
Character.isDigit), so a request for digits only falls through to the unrestricted case and every drawn character is used.
Trigger: the EXISTING test RandomStringUtilsTest::testRandomStringUtils; randomNumeric(50) draws from ' '..'z' and the assertion
'r1 contains numeric' (line 84) fails: "r1 contains numeric expected:<true> but was:<false>" (deterministic message and stack;
the chance that 50 unrestricted draws from 91 characters are all digits is about 1e-46). randomAlphabetic and randomAlphanumeric
(checked first in the same test) keep their branches and pass; testLang100, testLANG805, testLANG807 and testExceptions do not use
the digits-only case. No other test class uses RandomStringUtils.

Why not a surrogate omission (the class's most special-case-like step): the only test that exercises surrogates is testLang100,
whose failure message embeds the random index and character ("differs at <i>(<hex>,3f)"), so it can never fail byte-identically
three times (gate G3b); the `count == 1` (no room for a pair) rule fails only when the last draw is a surrogate (about 3% of runs).

The gold's javadoc keeps the facade's own parameter wording ("only allow letters?", "only allow numbers?") and describes the draw,
the fill order and the surrogate handling; it is silent on how the usability decision is split into cases (quiet). Pins outside
the gold: the facade javadoc ('@param numbers only allow numbers?'), randomNumeric's javadoc ('chosen from the set of numeric
characters'), StringUtils.isNumeric (Character.isDigit per character) and isAlphanumeric (Character.isLetterOrDigit) doing the
same classification, with their passing StringUtilsIsTest tests.

Single owner: only the gold sees the drawn characters (the draw loop is inside it, so no caller can pre-filter); hops 1-4 only
resolve the range, allocate the buffer, pass flags along and wrap the result. The usability decision cannot be repaired by a
one-line range change: a digits-only default range needs both of hop 1's default bounds moved ('0' and '9' + 1), and either
bound alone leaves non-digits in the range. Declared alternatives (G9): hop 1 starts the default range at '0' (range '0'..'z'),
hop 1 ends it after '9' (range ' '..'9'), hop 4 asks for letters or digits whenever digits are asked for; all fail the trigger.

Recorded bypasses (each contradicts the facade/hop 1 javadoc, which states that the default range is ' '..'z' and that start/end
are honoured; none repairs an explicit range such as random(n, 32, 127, false, true), which keeps drawing non-digits).
B-1, B-2 and B-3 were each applied to the variant in a scratch copy: all compile and pass the full suite (0 failing tests).
B-1 is the closest to a repair: for the DEFAULT range it yields the same uniform distribution over '0'..'9' as the intact gold
(only the seeded random sequence differs), so a reviewer may read hop 1 as a partial alternative owner for default ranges:
 B-1 hop 1, one line with two statements: `start = numbers && !letters ? '0' : ' '; end = numbers && !letters ? '9' + 1 : end;`
     (default digits-only range '0'..'9'; the gold's missing case is then never exercised by the tests).
 B-2 hop 1 return line routed to a digits array for digits-only requests, discarding start/end:
     `return numbers && !letters && chars == null ? StrBuilder.drawnText(count, 0, 10, false, false, "0123456789".toCharArray(), random) : StrBuilder.drawnText(count, start, end, letters, numbers, chars, random);`
 B-3 hop 2 rewrites the gold's output, replacing every non-digit by '0' for digits-only requests (keeps the length, skews the
     distribution): `return numbers && !letters ? new String(...).replaceAll("[^0-9]", "0") : new String(...);`
 B-0 none at the facade: the original body was the whole computation; restoring it would be a multi-line rewrite.

Lie: the facade's javadoc claims the characters are generated from the first position to the last and concatenated one at a
time; the code fills a char array from its last position to its first and wraps it once. It names neither the usability rule
nor digits nor any hop."""

RSU = "src/main/java/org/apache/commons/lang3/RandomStringUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"

GOLD_TEXT = '''/**
 * <p>Fills a buffer with randomly drawn characters, from its last
 * position to its first.</p>
 *
 * <p>Each character is drawn at a random offset below {@code gap} from
 * {@code start}: it is the character at that index of {@code chars} or,
 * if {@code chars} is {@code null}, the character with that value. A
 * drawn character that is not allowed is discarded and another one is
 * drawn. A surrogate is written together with a randomly chosen partner,
 * so that the buffer only holds complete surrogate pairs; private high
 * surrogates are never written.</p>
 *
 * @param buffer  the buffer to fill, not null
 * @param start  the first index or character value to draw from
 * @param gap  the number of indexes or character values to draw from
 * @param letters  only allow letters?
 * @param numbers  only allow numbers?
 * @param chars  the set of chars to draw from, may be null
 * @param random  the source of randomness, not null
 */
public static void fillDrawn(final char[] buffer, final int start, final int gap, final boolean letters,
        final boolean numbers, final char[] chars, final Random random) {
    int count = buffer.length;
    while (count > 0) {
        final char ch;
        if (chars == null) {
            ch = (char) (random.nextInt(gap) + start);
        } else {
            ch = chars[random.nextInt(gap) + start];
        }
        final boolean usable;
        if (letters && numbers) {
            usable = Character.isLetterOrDigit(ch);
        } else if (letters) {
            usable = Character.isLetter(ch);
        } else if (numbers) {
            usable = Character.isDigit(ch);
        } else {
            usable = true;
        }
        if (!usable || ch >= 56192 && ch <= 56319) {
            continue;
        }
        if (ch >= 56320 && ch <= 57343) {
            if (count == 1) {
                continue;
            }
            buffer[--count] = ch;
            buffer[--count] = (char) (55296 + random.nextInt(128));
        } else if (ch >= 55296 && ch <= 56191) {
            if (count == 1) {
                continue;
            }
            buffer[--count] = (char) (56320 + random.nextInt(128));
            buffer[--count] = ch;
        } else {
            buffer[--count] = ch;
        }
    }
}'''

HOP1 = '''/**
 * <p>Creates a string of randomly drawn characters, first resolving the
 * range to draw from.</p>
 *
 * <p>If start and end are both {@code 0}, the range is the whole of
 * {@code chars} when it is not {@code null}; otherwise it is every
 * character value when letters and numbers are both {@code false}, and
 * the characters from {@code ' '} to {@code 'z'} when they are not.
 * Any other range must end after it starts.</p>
 *
 * @param count  the length of the string to create, greater than zero
 * @param start  the position in the set of chars to start at
 * @param end  the position in the set of chars to end before
 * @param letters  only allow letters?
 * @param numbers  only allow numbers?
 * @param chars  the set of chars to draw from, may be null
 * @param random  the source of randomness, not null
 * @return the string of drawn characters
 * @throws IllegalArgumentException if end is not greater than start
 *  and they are not both {@code 0}
 */
public static String drawString(final int count, int start, int end, final boolean letters, final boolean numbers,
        final char[] chars, final Random random) {
    if (start == 0 && end == 0) {
        if (chars != null) {
            end = chars.length;
        } else if (!letters && !numbers) {
            end = Integer.MAX_VALUE;
        } else {
            end = 'z' + 1;
            start = ' ';
        }
    } else if (end <= start) {
        throw new IllegalArgumentException("Parameter end (" + end + ") must be greater than start (" + start + ")");
    }
    return StrBuilder.drawnText(count, start, end, letters, numbers, chars, random);
}'''

HOP2 = '''/**
 * <p>Creates a string of randomly drawn characters from a resolved
 * range.</p>
 *
 * @param count  the length of the string to create
 * @param start  the first index or character value of the range
 * @param end  the index or character value that ends the range, exclusive
 * @param letters  only allow letters?
 * @param numbers  only allow numbers?
 * @param chars  the set of chars to draw from, may be null
 * @param random  the source of randomness, not null
 * @return the string of drawn characters
 */
public static String drawnText(final int count, final int start, final int end, final boolean letters,
        final boolean numbers, final char[] chars, final Random random) {
    return new String(ArrayUtils.drawnChars(count, start, end - start, letters, numbers, chars, random));
}'''

HOP3 = '''/**
 * <p>Creates an array of randomly drawn characters.</p>
 *
 * @param count  the number of characters to draw
 * @param start  the first index or character value to draw from
 * @param gap  the number of indexes or character values to draw from
 * @param letters  only allow letters?
 * @param numbers  only allow numbers?
 * @param chars  the set of chars to draw from, may be null
 * @param random  the source of randomness, not null
 * @return a new array of {@code count} drawn characters
 */
public static char[] drawnChars(final int count, final int start, final int gap, final boolean letters,
        final boolean numbers, final char[] chars, final Random random) {
    final char[] buffer = new char[count];
    ToStringStyle.drawInto(buffer, start, gap, letters, numbers, chars, random);
    return buffer;
}'''

HOP4 = '''/**
 * <p>Fills an array with randomly drawn characters.</p>
 *
 * @param buffer  the array to fill, not null
 * @param start  the first index or character value to draw from
 * @param gap  the number of indexes or character values to draw from
 * @param letters  only allow letters?
 * @param numbers  only allow numbers?
 * @param chars  the set of chars to draw from, may be null
 * @param random  the source of randomness, not null
 */
public static void drawInto(final char[] buffer, final int start, final int gap, final boolean letters,
        final boolean numbers, final char[] chars, final Random random) {
    StringUtils.fillDrawn(buffer, start, gap, letters, numbers, chars, random);
}'''

DESIGN = {
 "instance": "Lang-11", "project": "Lang", "bug_id": 11, "seed": 5957,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": RSU, "class": "org.apache.commons.lang3.RandomStringUtils", "method": "random", "near_line": 223},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/RandomStringUtilsTest.java",
             "test_class": "org.apache.commons.lang3.RandomStringUtilsTest", "test_method": "testRandomStringUtils"},
 "expected_signature": "r1 contains numeric expected:<true> but was:<false>",
 "gold": {"method": "fillDrawn", "text": GOLD_TEXT,
          "fault": {"old": "                usable = Character.isLetter(ch);\n"
                           "            } else if (numbers) {\n"
                           "                usable = Character.isDigit(ch);\n"
                           "            } else {",
                    "new": "                usable = Character.isLetter(ch);\n"
                           "            } else {"}},
 "chain": {
   "facade_body": "if (count == 0) {\n"
                  "            return \"\";\n"
                  "        } else if (count < 0) {\n"
                  "            throw new IllegalArgumentException(\"Requested random string length \" + count + \" is less than 0.\");\n"
                  "        }\n"
                  "        if (chars != null && chars.length == 0) {\n"
                  "            throw new IllegalArgumentException(\"The chars array must not be empty\");\n"
                  "        }\n"
                  "        return org.apache.commons.lang3.time.DateUtils.drawString(count, start, end, letters, numbers, chars, random);",
   "lie": "The characters are generated in order from the first position of the string to the last, and the string is "
          "assembled by concatenating them one at a time.",
   "hops": [
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "drawString",
      "imports": ["java.util.Random", "org.apache.commons.lang3.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "drawnText",
      "imports": ["java.util.Random"], "text": HOP2},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "drawnChars",
      "imports": ["java.util.Random"], "text": HOP3},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "drawInto",
      "imports": ["java.util.Random", "org.apache.commons.lang3.StringUtils"], "text": HOP4},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "fillDrawn",
      "imports": ["java.util.Random"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.RandomStringUtils::randomNumeric",
              "org.apache.commons.lang3.StringUtils::isNumeric",
              "org.apache.commons.lang3.StringUtils::isAlphanumeric"],
 "ownership_reason": "Only the gold sees the drawn characters: the draw loop, the usability decision and the write into the "
                     "buffer are all inside it, so no caller can pre-filter a draw, and once a non-digit has been written the "
                     "string is complete. Hops 1-4 resolve the default range, allocate the buffer, pass the letters/numbers "
                     "flags along and wrap the result; the documented default range for any letters/numbers request is ' '..'z', "
                     "and moving one of its bounds in one line still leaves non-digits in it. The digits-only convention is "
                     "pinned outside the gold: the facade's javadoc ('@param numbers only allow numbers?'), randomNumeric's "
                     "javadoc ('chosen from the set of numeric characters'), and StringUtils.isNumeric / isAlphanumeric, which "
                     "classify with Character.isDigit / Character.isLetterOrDigit exactly as the gold's other cases do "
                     "(StringUtilsIsTest testIsNumeric / testIsAlphanumeric, passing).",
 "ownership_tests": ["org.apache.commons.lang3.StringUtilsIsTest::testIsNumeric",
                     "org.apache.commons.lang3.StringUtilsIsTest::testIsAlphanumeric",
                     "org.apache.commons.lang3.StringUtilsIsTest::testIsAlpha"],
 "compensating": {
   "chain": [
     {"file": DU, "old": "start = ' ';",
      "new": "start = numbers && !letters ? '0' : ' ';",
      "why": "hop 1 starts the default range of a digits-only request at '0'"},
     {"file": DU, "old": "end = 'z' + 1;",
      "new": "end = numbers && !letters ? '9' + 1 : 'z' + 1;",
      "why": "hop 1 ends the default range of a digits-only request after '9'"},
     {"file": TSS, "old": "StringUtils.fillDrawn(buffer, start, gap, letters, numbers, chars, random);",
      "new": "StringUtils.fillDrawn(buffer, start, gap, letters || numbers, numbers, chars, random);",
      "why": "hop 4 asks for letters or digits whenever digits are asked for"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 5957 (mr_lib preview, n=5, target org/apache/commons/lang3/RandomStringUtils.java): "
               "time.DateUtils (hop 1), text.StrBuilder (hop 2), ArrayUtils (hop 3), builder.ToStringStyle (hop 4), "
               "StringUtils (hop 5, gold). The checkout has exactly five host classes of >= 1500 lines, so the draw relaxed the "
               "'package distinct from the target' rule for hops 3 and 5 (both in org.apache.commons.lang3, like the facade) and "
               "no substitute host exists; all five are public classes (ToStringStyle is abstract, which does not affect a static "
               "method) and every hop compiles there, so none was skipped. java.util.Random is imported in each host.",
}
