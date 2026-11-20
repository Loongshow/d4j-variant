"""Main run Lang-12 (C10 recipe on the fixed checkout of Defects4J Lang-12; the real bug modified RandomStringUtils, the target class).

Facade: RandomStringUtils.random(int count, boolean letters, boolean numbers) (allowed target RandomStringUtils.random,
BATCH5_PREREGISTRATION.md row Lang-12; facade reuse of Lang-11, recorded by the coordinator in batch5_tasks.json). The method
identity Class::method is the same for every overload of random; the overload is chosen as follows. The pool records name the two
five-line overloads random(int, String) and random(int, char...). Every test that reaches them (testRandomStringUtils with the
sets "abcdefg" and "stuvwxyz", testExceptions) checks only the length, membership in a set of BMP letters, the inequality of two
draws and the argument errors; on those overloads letters and numbers are always false and the set never holds a surrogate, so
no per-element step of the generation is exercised deterministically, and the only deterministic checks left (count < 0, an
empty set) are argument checks that any hop can pre-filter. They cannot carry the recipe validly. The three-argument overload
is reached by random(int), randomAlphabetic, randomAlphanumeric and randomNumeric (testRandomStringUtils, testLang100,
testExceptions), so its chain carries the per-element character filter; the seven-argument overload stays intact beside it as
the external pin (it runs the same loop for random(int, int, int, boolean, boolean), randomAscii, the char[] and String
overloads and testLANG805).
Original computation of the facade (through the five- and seven-argument overloads with chars == null): a count of 0 gives "";
a negative count throws IllegalArgumentException; the code range is ' ' to 'z' when letters or numbers are requested, else 0 to
Integer.MAX_VALUE; then the buffer is filled from its last position to its first: a code is drawn, a code the letters/numbers
filter rejects is drawn again, a code in the private high-surrogate block 56192-56319 is drawn again, a surrogate drawn for
the first position (no room for a pair) is drawn again, a low surrogate is placed after a random high surrogate, a high
surrogate before a random low surrogate, and any other code is placed as it is.

The facade body is one delegating call (the original had no guard) to a five-hop chain drawn with the instance seed 4927
(mr_lib preview, draw order, none skipped):
  hop 1 text.StrBuilder.randomText          decision: count 0 gives "", a negative count throws IllegalArgumentException
  hop 2 builder.ToStringStyle.randomFromRange placement: the code range (' ' to 'z' for letters or numbers, else 0 to MAX)
  hop 3 StringUtils.randomBetween           plumbing: the width of the range, end - start
  hop 4 time.DateUtils.randomSpan           pass-through
  hop 5 ArrayUtils.randomChars              GOLD: the per-position loop (draw, filter, private block, room for a pair,
                                            the two pair placements, the plain placement, and drawing again)
The correct configuration returns the original result for every input and leaves the Random in the same state (checked in a
scratch harness against the original loop: 112,000 seeded cases over all four flag combinations and counts 0-300, plus the
negative-count exception). The three conditions under which the original draws again (filter rejection, private block, no room
for a pair) are written as one acceptance condition, with one 'draw again' branch.

Fault (one-line omission in the gold): the 'draw again' branch (`} else { count++; }`) is dropped. A rejected code then uses up
its position, which keeps its initial value '\\u0000'. Trigger: the EXISTING test RandomStringUtilsTest::testRandomStringUtils.
Its random(50) and randomAscii blocks pass (random(50) rejects only the rare private-block codes and leaves its length at 50;
randomAscii goes through the intact five- and seven-argument overloads). randomAlphabetic(50) draws from ' '..'z', where 39 of 91
codes are not letters, so a string with no rejected code has probability (52/91)^50 < 1e-12; the first assertion of the loop
at line 68 fails with "r1 contains alphabetic expected:<true> but was:<false>" (fixed message, fixed line). testLang100
(random(5000), no filter) still passes: an unused position holds '\\u0000', which survives the UTF-8 round trip, and a pair is
never split. testLANG805 and the set overloads use the intact seven-argument overload. No other test class uses
RandomStringUtils.

The gold's javadoc states the idiomatic contract in the facade's own words (a random string whose length is the number of
characters specified; characters chosen as indicated by the arguments; letters/numbers: "generated string will include
alphabetic / numeric characters") and is silent on drawing again. On the trigger input the variant returns NUL characters that
were never chosen, and randomAlphabetic's contract ("Characters will be chosen from the set of alphabetic characters") fails.
External pins: the seven-argument overload RandomStringUtils.random(int, int, int, boolean, boolean, char[], Random) runs the
same loop and draws again on rejection (`} else { count++; }`), with its passing test testLANG805 (every position holds a drawn
character of the set); randomAlphabetic, randomNumeric and randomAlphanumeric are production callers of the facade whose
javadocs restrict every character to the class; testLang100 passes through the facade and the gold and pins that the gold places
every position (5,000 positions, pairs intact).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (as written below; the original's three separate 'count++' retries were already folded into one acceptance
 condition and one 'draw again' branch, and its comments were not carried over, so no sibling retry pattern can remain):
  T1 absent: count sizes the buffer and drives the loop; start and gap give every drawn code; letters and numbers decide
     acceptance; random gives every code and pair partner.
  T2 absent: buffer is returned; count is the loop's cursor, assigned in the loop header, in both pair branches and in the
     'draw again' branch; ch, low and high are computed per iteration and decide live statements; no literal-initialised local;
     every branch has its own effect.
  T3 absent: both pair halves (low, high) are placed; both ends of each code block are tested (56320/57343, 55296/56191,
     56192/56319); both flags letters and numbers have their test, and the neither-flag case is handled.
  T4 absent: the javadoc names only the length ("the number of characters specified"), the choice "as indicated by the
     arguments", the inclusive letters/numbers wording and caller preconditions ("positive"); no limit, value class or case.
 Variant gold (the same text without `} else {` / `count++;`):
  T1 absent: every parameter is still read in the main computation and changes the returned string (letters and numbers
     decide which positions are written).
  T2 absent: buffer is returned; count is assigned in the loop header and in both pair branches; ch, low, high decide live
     writes; the outer if writes or does not write, the inner if/else-if/else make three different writes; no frozen local,
     no dead decision.
  T3 absent: no draw-again treatment remains for any case (no member handled); low and high, both ends of every block and both
     flags are treated exactly as in the correct gold.
  T4 absent: "Creates a random string whose length is the number of characters specified" is met (buffer of count);
     "Characters will be chosen as indicated by the arguments" names no class or rule; "if {@code true}, generated string will
     include alphabetic characters" (and numeric) is met when the flag is set; "positive" on count and gap are caller
     preconditions; no inline comment; identifiers (buffer, ch, low, high) name nothing the body does not do.

Single owner: only the gold sees each drawn code and decides, position by position, whether it is used. Hops 1-4 hold the count,
the flags, the range and the Random and get back a finished string; once a position has been used up by a rejected code, no
caller can draw for it again, and no change of the range or the flags removes the rejections (every range that holds both
letters and digits also holds other codes). Declared alternatives (G9): hop 2 starts the range of the requested classes at '0';
hop 1 drops the unused positions from the result; hop 3 counts the end code into the range. Each still fails the trigger.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy):
 B-0 bypass: the facade (its original body) or any of hops 1-4 returns RandomStringUtils.random(count, 0, 0, letters, numbers,
     null, random), the intact seven-argument overload, discarding the rest of the chain including the gold.
 B-1 test-fitted: a hop overwrites every unused position with one constant
     (`StringUtils.replaceChars(<result>, (char) 0, letters ? 'a' : '0')`): every alphabetic string then holds about 21 'a's
     at the positions the gold left, and in the unfiltered mode a drawn '\\u0000' becomes '0', so random(int) can no longer
     give that character ('Characters will be chosen from the set of all characters'); not consistent with the path or with
     the seven-argument overload, which draws again.
 B-2 test-fitted: hop 2 shrinks the range to letters only ('A'-'Z') for letters alone and to digits ('0'-'9') otherwise: it
     contradicts hop 2's documented range (' ' to 'z', the ASCII printable characters), randomAlphanumeric then never gives a
     letter (the facade: 'generated string will include alphabetic characters'), and randomAlphabetic never a lower-case one.

Lie: the facade's javadoc claims the string is filled from its first position to its last, each character cut from the low
sixteen bits of one random long; the chain fills from the last position to the first and draws each code with nextInt. It names
neither the filter nor drawing again nor any hop."""

RSU = "src/main/java/org/apache/commons/lang3/RandomStringUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

FLAG_DOCS = ''' * @param letters  if {@code true}, generated string will include
 *  alphabetic characters
 * @param numbers  if {@code true}, generated string will include
 *  numeric characters
 * @param random  a source of randomness'''

GOLD_TEXT = '''/**
 * <p>Creates a random string whose length is the number of characters
 * specified.</p>
 *
 * <p>Characters will be chosen as indicated by the arguments.</p>
 *
 * @param count  the length of random string to create, positive
 * @param start  the first character code to choose from
 * @param gap  the number of character codes to choose from, positive
''' + FLAG_DOCS + '''
 * @return the random string
 */
public static String randomChars(int count, int start, int gap, boolean letters, boolean numbers, Random random) {
    final char[] buffer = new char[count];
    while (count-- != 0) {
        final char ch = (char) (random.nextInt(gap) + start);
        final boolean low = ch >= 56320 && ch <= 57343;
        final boolean high = ch >= 55296 && ch <= 56191;
        if ((letters && Character.isLetter(ch) || numbers && Character.isDigit(ch) || !letters && !numbers)
                && (ch < 56192 || ch > 56319) && (count > 0 || !low && !high)) {
            if (low) {
                buffer[count] = ch;
                count--;
                buffer[count] = (char) (55296 + random.nextInt(128));
            } else if (high) {
                buffer[count] = (char) (56320 + random.nextInt(128));
                count--;
                buffer[count] = ch;
            } else {
                buffer[count] = ch;
            }
        } else {
            count++;
        }
    }
    return new String(buffer);
}'''

HOP1 = '''/**
 * <p>Creates a random string whose length is the number of characters
 * specified.</p>
 *
 * <p>A length of zero gives the empty string.</p>
 *
 * @param count  the length of random string to create
''' + FLAG_DOCS + '''
 * @return the random string
 * @throws IllegalArgumentException if {@code count} &lt; 0
 */
public static String randomText(int count, boolean letters, boolean numbers, Random random) {
    if (count == 0) {
        return "";
    } else if (count < 0) {
        throw new IllegalArgumentException("Requested random string length " + count + " is less than 0.");
    }
    return ToStringStyle.randomFromRange(count, letters, numbers, random);
}'''

HOP2 = '''/**
 * <p>Creates a random string of a positive length from a range of
 * character codes.</p>
 *
 * <p>When letters or numbers are requested, the range runs from
 * {@code ' '} to {@code 'z'}, the ASCII printable characters; otherwise
 * it runs from {@code 0} up to {@code Integer.MAX_VALUE}.</p>
 *
 * @param count  the length of random string to create, positive
''' + FLAG_DOCS + '''
 * @return the random string
 */
public static String randomFromRange(int count, boolean letters, boolean numbers, Random random) {
    final int start = letters || numbers ? ' ' : 0;
    final int end = letters || numbers ? 'z' + 1 : Integer.MAX_VALUE;
    return StringUtils.randomBetween(count, start, end, letters, numbers, random);
}'''

HOP3 = '''/**
 * <p>Creates a random string of a positive length, choosing from the
 * character codes from {@code start} up to, but not including,
 * {@code end}.</p>
 *
 * @param count  the length of random string to create, positive
 * @param start  the first character code to choose from
 * @param end  the character code to end before, greater than start
''' + FLAG_DOCS + '''
 * @return the random string
 */
public static String randomBetween(int count, int start, int end, boolean letters, boolean numbers, Random random) {
    return DateUtils.randomSpan(count, start, end - start, letters, numbers, random);
}'''

HOP4 = '''/**
 * <p>Creates a random string of a positive length, choosing from a
 * range of character codes given by its first code and its width.</p>
 *
 * @param count  the length of random string to create, positive
 * @param start  the first character code to choose from
 * @param gap  the number of character codes to choose from, positive
''' + FLAG_DOCS + '''
 * @return the random string
 */
public static String randomSpan(int count, int start, int gap, boolean letters, boolean numbers, Random random) {
    return ArrayUtils.randomChars(count, start, gap, letters, numbers, random);
}'''

DESIGN = {
 "instance": "Lang-12", "project": "Lang", "bug_id": 12, "seed": 4927,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": RSU, "class": "org.apache.commons.lang3.RandomStringUtils", "method": "random", "near_line": 142},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/RandomStringUtilsTest.java",
             "test_class": "org.apache.commons.lang3.RandomStringUtilsTest", "test_method": "testRandomStringUtils"},
 "expected_signature": "r1 contains alphabetic expected:<true> but was:<false>",
 "gold": {"method": "randomChars", "text": GOLD_TEXT,
          "fault": {"old": "                    buffer[count] = ch;\n"
                           "                }\n"
                           "            } else {\n"
                           "                count++;\n"
                           "            }\n"
                           "        }\n"
                           "        return new String(buffer);",
                    "new": "                    buffer[count] = ch;\n"
                           "                }\n"
                           "            }\n"
                           "        }\n"
                           "        return new String(buffer);"}},
 "chain": {
   "facade_body": "return org.apache.commons.lang3.text.StrBuilder.randomText(count, letters, numbers, RANDOM);",
   "lie": "The string is filled from its first position to its last, each character being cut from the low sixteen bits "
          "of a single random long.",
   "hops": [
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "randomText",
      "imports": ["java.util.Random", "org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "randomFromRange",
      "imports": ["java.util.Random", "org.apache.commons.lang3.StringUtils"], "text": HOP2},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "randomBetween",
      "imports": ["java.util.Random", "org.apache.commons.lang3.time.DateUtils"], "text": HOP3},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "randomSpan",
      "imports": ["java.util.Random", "org.apache.commons.lang3.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "randomChars",
      "imports": ["java.util.Random"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.RandomStringUtils::random",
              "org.apache.commons.lang3.RandomStringUtils::randomAlphabetic",
              "org.apache.commons.lang3.RandomStringUtils::randomNumeric",
              "org.apache.commons.lang3.RandomStringUtils::randomAlphanumeric"],
 "ownership_reason": "Only the gold sees each drawn character code and decides, position by position, whether it is used; hops "
                     "1-4 hold the count, the letters/numbers flags, the code range and the Random and get back a finished "
                     "string. Once a rejected code has used up a position (which keeps its initial value), no caller can draw "
                     "for that position again, and no change of the range or the flags removes the rejections: every range "
                     "that holds both letters and digits also holds other codes. The convention is pinned outside the gold: "
                     "the seven-argument overload RandomStringUtils.random(int, int, int, boolean, boolean, char[], Random), "
                     "kept intact beside the facade and used by randomAscii, the char[] and String overloads and testLANG805, "
                     "runs the same loop and draws again whenever the letters/numbers filter rejects a code "
                     "('} else { count++; }'); randomAlphabetic, randomNumeric and randomAlphanumeric, the production callers "
                     "of the facade, document that every character is chosen from their class ('Characters will be chosen "
                     "from the set of alphabetic characters'); testLang100 passes 5,000 positions through the facade and the "
                     "gold and pins that the gold places every position, pairs intact; testExceptions pins the count guard "
                     "of hop 1. A one-line edit above the gold that passes the existing tests either discards the gold "
                     "(returning the seven-argument overload), overwrites the unused positions with a constant (the string "
                     "is then no longer chosen at random there, and a drawn '\\u0000' in the unfiltered mode is lost), or "
                     "shrinks the documented range so that randomAlphanumeric never gives a letter.",
 "ownership_tests": ["org.apache.commons.lang3.RandomStringUtilsTest::testLANG805",
                     "org.apache.commons.lang3.RandomStringUtilsTest::testLang100",
                     "org.apache.commons.lang3.RandomStringUtilsTest::testExceptions"],
 "compensating": {
   "chain": [
     {"file": TSS, "old": "final int start = letters || numbers ? ' ' : 0;",
      "new": "final int start = letters || numbers ? '0' : 0;",
      "why": "hop 2 starts the range of the requested classes at '0'"},
     {"file": SB, "old": "return ToStringStyle.randomFromRange(count, letters, numbers, random);",
      "new": "return org.apache.commons.lang3.StringUtils.remove(ToStringStyle.randomFromRange(count, letters, numbers, random), (char) 0);",
      "why": "hop 1 drops the unused positions from the result"},
     {"file": SU, "old": "return DateUtils.randomSpan(count, start, end - start, letters, numbers, random);",
      "new": "return DateUtils.randomSpan(count, start, end - start + 1, letters, numbers, random);",
      "why": "hop 3 counts the end code into the range"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4927 (mr_lib preview, target org/apache/commons/lang3/RandomStringUtils.java): "
               "text.StrBuilder (hop 1), builder.ToStringStyle (hop 2), StringUtils (hop 3), time.DateUtils (hop 4), "
               "ArrayUtils (hop 5, gold; drawn as the last remaining host: the pool has exactly five classes of >= 1,500 lines, "
               "so preview with n=6 gives the same five). The draw relaxed the 'distinct from the target package' preference "
               "for hops 3 and 5 (StringUtils and ArrayUtils share the lang3 package with RandomStringUtils). All five are "
               "public top-level classes in which a static method compiles (ToStringStyle is abstract, which does not affect "
               "a static method); none was skipped. The facade calls hop 1 by its fully-qualified name and passes the class's "
               "private RANDOM instance; each hop imports java.util.Random and the next host.",
}
