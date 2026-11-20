"""Main run Lang-65 (C10 recipe on the fixed checkout of Defects4J Lang-65; the real bug modified DateUtils, the target class).

Facade: DateUtils.parseDate(String, String[]) (allowed target, BATCH3_PREREGISTRATION.md row 35). The other allowed targets were
set aside: every computation in iterator(Calendar, int) is an enumeration (the range-style switch, the start/end pair, the four
cutoff wrap tests, the two weekday walks), so each one-line omission there leaves a visibly incomplete closed set (T3), an empty
branch (T2c) or an endless walk; isSameDay(Calendar, Calendar) is a three-field comparison (ERA, YEAR, DAY_OF_YEAR) whose only
test-visible omission (DAY_OF_YEAR) fails both isSameDay tests and leaves a 'same year' check under a 'same day' contract.
parseDate is a loop over patterns with a per-pattern core. Original computation: reject a null string or pattern array; one
SimpleDateFormat, created from the first pattern and re-patterned for each later one; one ParsePosition, set back to index 0
before each pattern; the first pattern whose parse is non-null and ends at the end of the string gives the date; otherwise a
ParseException("Unable to parse the date: " + str).

Chain (hosts in draw order for seed 4195, mr_lib preview, no host skipped):
  hop 1 builder.ToStringStyle.parseDateText       decision: an empty pattern array gives the ParseException without a parse
  hop 2 StringUtils.parseByPatterns               placement: the whole array as the pattern range [0, length)
  hop 3 text.StrBuilder.parsePatternRange         pass-through
  hop 4 ArrayUtils.dateOfPatternRange             pass-through
  hop 5 time.FastDateFormat.parseInTurn           GOLD: the per-pattern loop (parser created for the first pattern of the range
                                                  and re-patterned for each later one, the parse position set to the start of
                                                  the string, the whole-string acceptance test, the ParseException when no
                                                  pattern of the range parses the whole string)
The correct configuration performs the original computation in the original order (same guard, same parser reuse, same
position reset, same acceptance test, same exception and message; hop 1's empty-array exception is the one the loop throws for
zero patterns), so it is behaviour-preserving for every caller.

Fault (omission in the gold, a state reset): the line `pos.setIndex(0);` at the top of each pattern's turn is dropped, so after a
pattern that parses only a prefix of the string (non-null date, index short of the end) the next pattern starts parsing where the
previous one stopped instead of at the start of the string. Trigger: the EXISTING test DateUtilsTest::testParseDate, first
assertion: parseDate("1972-12-03", {"yyyy'-'DDD", "yyyy'-'MM'-'dd", "yyyyMMdd"}). The first pattern parses "1972-12" (day 12 of
1972) and stops at index 7; the second pattern, which parses the whole string from index 0, now starts at index 7 and fails, the
third fails too, and the method throws java.text.ParseException "Unable to parse the date: 1972-12-03" (expected Dec 3 1972).
The later assertions do not depend on the reset (a failed parse restores the index; "1972-338" and "19721203" are taken by a
pattern whose predecessors failed outright). testParseDate is the only test that reaches parseDate, and parseDate has no
production caller, so no other test can change (G5).

The gold's javadoc states the contract (each pattern of the range tried in turn; the date of the first pattern that parses the
whole of the string; a ParseException if none does) and is silent on the position reset. The omission violates that contract on
the trigger input: "yyyy'-'MM'-'dd" parses the whole of "1972-12-03", yet the gold throws. The convention is pinned outside the
gold: the facade's own javadoc ('The parse will try each parse pattern in turn. A parse is only deemed sucessful if it parses
the whole of the input string.'); java.text.DateFormat.parse(String) and java.text.Format.parseObject(String) parse each string
'from the beginning' with a new ParsePosition(0); in this code base CompositeFormat.reformat parses its input through
Format.parseObject(String), and CompositeFormatTest::testUsage (passing) parses the whole of "01032005" with a SimpleDateFormat
that way.

Single owner: only the gold holds the ParsePosition and the parser; they are locals of the gold, created afresh on every call.
The facade and hops 1-4 see only the string, the pattern array and the range, and the gold reports failure by throwing, so no
hop can test the result and try again without a try/catch block (several statements). A one-line edit above the gold can only
reorder, shorten or shift the pattern range; each such edit still meets a prefix-parsing pattern first or loses a pattern the
test needs. Declared alternatives (G9): hop 2 starts the range at the second pattern when there are several (then "1972-338" is
taken by "yyyyMMdd" as 8 Oct 1971); hop 1 tries a reversed copy of the patterns ("yyyyMMdd" parses only "1972-12" of
"1972-12-03", same failure, and "1972-338" goes wrong); hop 4 starts its range one pattern later when it holds several (as hop 2).
None passes the trigger (checked on a probe of the variant loop before building; G9 re-checks on the build).
Recorded bypasses (not repairs of a hop, they discard the gold or re-implement its loop):
 B-0 the facade's original body (the guard plus the whole pattern loop) restored in place of the delegating call: discards all
     five hops including the gold (multi-statement).
 B-1 a hop above the gold wraps its call in try/catch and, on a ParseException, calls the chain again for each remaining pattern
     on its own, or loops over single-pattern ranges itself: a second implementation of the per-pattern loop (multi-statement).

Lie: the facade's javadoc claims each pattern is compiled into a format only once, with already compiled formats taken from a
cache shared between calls; the code compiles a SimpleDateFormat on every call and keeps no cache. It names neither the parse
position, nor the position reset, nor any hop.

Note for reviewers: the ParseException is thrown by the gold itself (as the original parseDate threw it from its own loop), so
the trigger's stack trace shows the whole chain with FastDateFormat.parseInTurn as the top frame. Moving the throw to a hop (gold
returns null) was rejected because any hop holding the array could then retry the remaining patterns in one line (a competing
one-line edit), which the exception rules out.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), on the WHOLE gold as it reads in the variant, item by item:
 T1 absent: str is parsed, measured and quoted in the exception; parsePatterns supplies every pattern; startIndex starts the loop
    and decides where the parser is created; endIndex bounds the loop; none is used only in an argument check.
 T2 absent: parser (null, then assigned a new SimpleDateFormat on the first turn) is read by applyPattern and parse; pos (a new
    ParsePosition, not a literal) is passed to parse, which moves it, and its index is tested; date is tested and returned; i
    advances; the if/else on i == startIndex has two different effects; the acceptance if returns or continues; no dead local,
    no frozen local, no dead decision.
 T3 absent: no enumeration in the gold; every pattern of the range gets the same treatment; both range ends are used (start and
    bound of the loop); the gold names no value class.
 T4 absent: 'each of the date patterns in a range ... in turn' (the for loop over [startIndex, endIndex)); 'the first pattern
    that parses the whole of the string' (date != null && pos.getIndex() == str.length() returns at the first such pattern);
    '@throws ParseException if no pattern in the range parses the whole of the string' (the throw after the loop); 'not null'
    on str and parsePatterns are caller preconditions.
 The CORRECT gold was checked the same way before choosing the omission (it differs only by the reset line, which is a
 statement on pos) and shows none of T1-T4."""

DU = "src/java/org/apache/commons/lang/time/DateUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
SU = "src/java/org/apache/commons/lang/StringUtils.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"

RANGE_DOC = '''/**
 * <p>Parses a string representing a date by trying each of the date
 * patterns in a range of an array in turn, and returns the date given by
 * the first pattern that parses the whole of the string.</p>
 *
 * @param str  the date to parse, not null
 * @param parsePatterns  the date format patterns to use, see SimpleDateFormat, not null
 * @param startIndex  the index of the first pattern to try
 * @param endIndex  the index after the last pattern to try
 * @return the parsed date
 * @throws ParseException if no pattern in the range parses the whole of
 *  the string
 */'''

GOLD_TEXT = RANGE_DOC + '''
public static Date parseInTurn(String str, String[] parsePatterns, int startIndex, int endIndex) throws ParseException {
    SimpleDateFormat parser = null;
    ParsePosition pos = new ParsePosition(0);
    for (int i = startIndex; i < endIndex; i++) {
        if (i == startIndex) {
            parser = new SimpleDateFormat(parsePatterns[i]);
        } else {
            parser.applyPattern(parsePatterns[i]);
        }
        pos.setIndex(0);
        Date date = parser.parse(str, pos);
        if (date != null && pos.getIndex() == str.length()) {
            return date;
        }
    }
    throw new ParseException("Unable to parse the date: " + str, -1);
}'''

HOP1 = '''/**
 * <p>Parses a string representing a date by trying each of an array of
 * date patterns in turn, and returns the date given by the first pattern
 * that parses the whole of the string.</p>
 *
 * <p>An empty array of patterns gives a ParseException without any parse
 * being tried.</p>
 *
 * @param str  the date to parse, not null
 * @param parsePatterns  the date format patterns to use, see SimpleDateFormat, not null
 * @return the parsed date
 * @throws ParseException if none of the patterns parses the whole of the
 *  string
 */
public static Date parseDateText(String str, String[] parsePatterns) throws ParseException {
    if (parsePatterns.length == 0) {
        throw new ParseException("Unable to parse the date: " + str, -1);
    }
    return StringUtils.parseByPatterns(str, parsePatterns);
}'''

HOP2 = '''/**
 * <p>Parses a string representing a date by trying each of a non-empty
 * array of date patterns in turn, and returns the date given by the first
 * pattern that parses the whole of the string.</p>
 *
 * <p>The patterns are tried over the whole array, from its first pattern
 * to its last.</p>
 *
 * @param str  the date to parse, not null
 * @param parsePatterns  the date format patterns to use, see SimpleDateFormat, not null or empty
 * @return the parsed date
 * @throws ParseException if none of the patterns parses the whole of the
 *  string
 */
public static Date parseByPatterns(String str, String[] parsePatterns) throws ParseException {
    return StrBuilder.parsePatternRange(str, parsePatterns, 0, parsePatterns.length);
}'''

HOP3 = RANGE_DOC + '''
public static Date parsePatternRange(String str, String[] parsePatterns, int startIndex, int endIndex) throws ParseException {
    return ArrayUtils.dateOfPatternRange(str, parsePatterns, startIndex, endIndex);
}'''

HOP4 = RANGE_DOC + '''
public static Date dateOfPatternRange(String str, String[] parsePatterns, int startIndex, int endIndex) throws ParseException {
    return FastDateFormat.parseInTurn(str, parsePatterns, startIndex, endIndex);
}'''

DESIGN = {
 "instance": "Lang-65", "project": "Lang", "bug_id": 65, "seed": 4195,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": DU, "class": "org.apache.commons.lang.time.DateUtils", "method": "parseDate", "near_line": 251},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/time/DateUtilsTest.java",
             "test_class": "org.apache.commons.lang.time.DateUtilsTest", "test_method": "testParseDate"},
 "expected_signature": "Unable to parse the date: 1972-12-03",
 "gold": {"method": "parseInTurn", "text": GOLD_TEXT,
          "fault": {"old": "                parser.applyPattern(parsePatterns[i]);\n"
                           "            }\n"
                           "            pos.setIndex(0);\n"
                           "            Date date = parser.parse(str, pos);",
                    "new": "                parser.applyPattern(parsePatterns[i]);\n"
                           "            }\n"
                           "            Date date = parser.parse(str, pos);"}},
 "chain": {
   "facade_body": "if (str == null || parsePatterns == null) {\n"
                  "            throw new IllegalArgumentException(\"Date and Patterns must not be null\");\n"
                  "        }\n"
                  "        return org.apache.commons.lang.builder.ToStringStyle.parseDateText(str, parsePatterns);",
   "lie": "Each pattern is compiled into a format only once, and a format already compiled by an earlier call is taken "
          "from a cache shared between calls instead of being compiled again.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "parseDateText",
      "imports": ["java.text.ParseException", "java.util.Date", "org.apache.commons.lang.StringUtils"], "text": HOP1},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "parseByPatterns",
      "imports": ["java.text.ParseException", "java.util.Date", "org.apache.commons.lang.text.StrBuilder"], "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "parsePatternRange",
      "imports": ["java.text.ParseException", "java.util.Date"], "text": HOP3},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "dateOfPatternRange",
      "imports": ["java.text.ParseException", "java.util.Date", "org.apache.commons.lang.time.FastDateFormat"], "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "parseInTurn",
      "imports": ["java.text.ParseException"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.time.DateUtils::parseDate",
              "java.text.DateFormat::parse",
              "java.text.Format::parseObject",
              "org.apache.commons.lang.text.CompositeFormat::reformat"],
 "ownership_reason": "Only the gold holds the parse position and the parser: both are locals of the gold, created afresh on "
                     "every call, and the gold alone runs the per-pattern loop and decides acceptance. The facade and hops 1-4 "
                     "see only the string, the pattern array and the pattern range, and the gold reports a failed parse by "
                     "throwing, so no hop can test the outcome and try the remaining patterns again without a try/catch block; "
                     "a one-line reordering, shortening or shifting of the range still meets a prefix-parsing pattern first or "
                     "loses a pattern that the test needs. The convention that every pattern is applied to the whole string from "
                     "its start is pinned outside the gold: the facade's javadoc ('The parse will try each parse pattern in "
                     "turn. A parse is only deemed sucessful if it parses the whole of the input string.'); "
                     "java.text.DateFormat.parse(String) and java.text.Format.parseObject(String) parse each string from the "
                     "beginning with a new ParsePosition(0); CompositeFormat.reformat parses its input through "
                     "Format.parseObject(String), and CompositeFormatTest.testUsage parses the whole of \"01032005\" with a "
                     "SimpleDateFormat that way. The gold's own contract (the date of the first pattern that parses the whole "
                     "of the string) is violated on the trigger input, which \"yyyy'-'MM'-'dd\" parses whole.",
 "ownership_tests": ["org.apache.commons.lang.text.CompositeFormatTest::testUsage"],
 "compensating": {
   "chain": [
     {"file": SU, "old": "return StrBuilder.parsePatternRange(str, parsePatterns, 0, parsePatterns.length);",
      "new": "return StrBuilder.parsePatternRange(str, parsePatterns, parsePatterns.length > 1 ? 1 : 0, parsePatterns.length);",
      "why": "hop 2 starts the range at the second pattern when there are several"},
     {"file": TSS, "old": "return StringUtils.parseByPatterns(str, parsePatterns);",
      "new": "String[] reversed = (String[]) org.apache.commons.lang.ArrayUtils.clone(parsePatterns); "
             "org.apache.commons.lang.ArrayUtils.reverse(reversed); return StringUtils.parseByPatterns(str, reversed);",
      "why": "hop 1 tries the patterns in reverse order"},
     {"file": AU, "old": "return FastDateFormat.parseInTurn(str, parsePatterns, startIndex, endIndex);",
      "new": "return FastDateFormat.parseInTurn(str, parsePatterns, endIndex - startIndex > 1 ? startIndex + 1 : startIndex, endIndex);",
      "why": "hop 4 starts its range one pattern later when it holds several"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4195 (mr_lib preview, target org/apache/commons/lang/time/DateUtils.java): "
               "builder.ToStringStyle (hop 1), StringUtils (hop 2), text.StrBuilder (hop 3), ArrayUtils (hop 4), "
               "time.FastDateFormat (hop 5, gold; the last host of the five-class pool). All five are public classes in which "
               "a static method compiles (ToStringStyle is abstract, which does not affect a static method); none was "
               "skipped. The facade calls hop 1 by its fully-qualified name; each hop imports java.text.ParseException, "
               "java.util.Date and the next host where needed (StrBuilder already imports ArrayUtils; FastDateFormat already "
               "imports SimpleDateFormat, ParsePosition and Date).",
}
