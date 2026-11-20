"""Main run Lang-10__i (cell C10i, batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Lang-10; the real bug modified FastDateParser, the facade's class). No static pair (pool v2: no_tested_static); addendum section 2 is
void (B8 note section 1).

Facade: FastDateParser.parse(String) (the only allowed candidate of batch9_tasks.json; facade_planned_by = Lang-9__i, so this is a
recorded facade reuse: no other allowed method exists; nothing of that instance was opened).
Original computation of the facade: parse(source, new ParsePosition(0)); a null result is turned into a ParseException with offset 0
and the message "Unparseable date: \"<source>\" does not match <parsePattern.pattern()>", preceded by the note "(The <locale> locale
does not support dates before 1868 AD)\n" when the locale is JAPANESE_IMPERIAL; otherwise the date is returned.

facade_variant: V2+V1. V2: the receiver `this` is handed to hop 1, typed as the interface it implements (DateParser); the hops call only
its public methods parse(String, ParsePosition) and getLocale(). V1: the private field parsePattern (its pattern String) and the
package-private static field JAPANESE_IMPERIAL (a Locale value) are read inside FastDateParser and passed as values, so no hop needs a
package-private member (no V3/V5); no private method is called (no V4). No field is written. No signature, modifier, @Override or
throws change; no new type; no reflection; no test edit.
state_passed: receiver `this` (as DateParser), the String parsePattern.pattern() and the Locale JAPANESE_IMPERIAL to hop 1; no
write-back.
Facade javadoc: the facade had only a `/* (non-Javadoc) @see DateParser#parse(String) */` block comment, so a pre-edit turns it into a
javadoc with one sentence in the class's own voice ("Parses text from the beginning of the given string to produce a date.", the
wording of DateFormat#parse(String)) plus the lie, keeping the @see line. The @Override annotation sits between that javadoc and the
header, so the recipe's rewrite_facade finds no adjacent javadoc and appends nothing: the lie appears exactly once, in the pre-edit;
chain.lie carries the same sentence for the record.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Lang-10-probe/w the first statement of
parse(String) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. Full suite: 36 failing tests, every one
java.lang.IllegalStateException: PROBE-REACHED at FastDateParser.parse(FastDateParser.java:250): the 18 FastDateParserTest methods
that call parse(String) (e.g. testParseNumerics, FastDateParserTest.java:325) and the same 18 inherited by FastDateFormat_ParserTest
(through FastDateFormat.parse, FastDateFormat.java:472). FastDateParserTest::testLANG_831 also reaches the facade but passes under
the probe (its shouldFail branch catches every Exception).
Consequence for the fault: every test that reaches the facade runs twice (FastDateFormat_ParserTest extends FastDateParserTest), so a
fault on the success path fails at least two tests (G5). The single exception is the mismatch path of testLANG_831 ("M E" against
"3  Tue", which must fail): if parse(String) returns null instead of throwing, FastDateParserTest::testLANG_831 fails on
Assert.fail("Expected FDF failure, but got null ..."), while in FastDateFormat_ParserTest the cast (FastDateParser) fdp inside that
message throws ClassCastException, which the test's catch (Exception) takes as the expected failure, and assertEquals(null, null)
passes. So the fault must make the mismatch path return null.

Hosts (host_mode = "1500"; mr_lib.py preview Lang-10 org/apache/commons/lang3/time/FastDateParser.java 5, instance seed 7705; used
in draw order, none substituted):
  hop 1 StringUtils            6486 lines  parseToDate       placement: the note on the supported date range for the imperial
                                                             locale becomes the lead of the exception message
  hop 2 builder.ToStringStyle  2280 lines  dateFromText      pass-through
  hop 3 text.StrBuilder        2882 lines  readDate          pass-through
  hop 4 ArrayUtils             5796 lines  parseDateWith     pass-through
  hop 5 time.DateUtils         1888 lines  parseLeadingDate  GOLD: the parse from index 0 and the decision that the result is
                                                             a date (a rejected value or a null result becomes a ParseException)
Host sizes 6486, 2280, 2882, 5796, 1888; the smallest host is DateUtils (1888 lines, the gold host).
The correct configuration returns the original date and throws the original ParseException (same message, offset 0) for every
input the original handled; in addition, an IllegalArgumentException that a field strategy throws for matched text (a number too
large for an int, an unsupported zone name, a text value not found) is reported as a ParseException with the same message and the
IllegalArgumentException as its cause, which DateParser#parse(String) promises ("@throws ParseException if the beginning of the
specified string cannot be parsed"); no test exercises that path (the probe run shows no test of parse(String) expecting an
IllegalArgumentException).

Fault (one-line omission of a decision in the gold): the null check after the parse is dropped, so a string whose beginning does not
match makes the gold return null instead of throwing. The gold then reads as the ordinary routine "build the message, parse from
index 0, report a rejected value as a ParseException, return the date". Trigger: the EXISTING test FastDateParserTest::testLANG_831
fails with "Expected FDF failure, but got null for [M E,3  Tue] using ..."; it is the only test that newly fails (see the probe
consequence above: FastDateFormat_ParserTest::testLANG_831 passes through its ClassCastException; no other test reaches the mismatch
path; the new hops have no other caller).

The gold's javadoc states the idiomatic contract (it parses the beginning of a string to produce a date as DateParser#parse(String)
does, returning the parsed date) and is silent on the null result. The convention is pinned outside the gold: DateParser#parse(String)
("@return A Date parsed from the string", "@throws ParseException if the beginning of the specified string cannot be parsed") and
DateParser#parse(String, ParsePosition) ("In case of error, returns null"), FastDateParser.parse(String, ParsePosition) returning null
when the pattern does not match; DateUtils.parseDateWithLeniency, the sibling in the gold's own class, which treats a null result of
parse(String, ParsePosition) as no match and throws ParseException; DateUtils.parseDate; passing tests DateUtilsTest::testParseDate,
::testParseDateWithLeniency and ::testLANG799_EN_FAIL (a non-matching date gives ParseException).

Single owner: only the gold calls the parser and decides whether its result is a date; hops 2-4 pass the four values along and hop 1
only composes the lead of the message. A change of the arguments above the gold cannot make a non-matching string throw: collapsing
or trimming the whitespace of the string (hops 1 and 3) makes "3  Tue" either still not match (null) or match as "3 Tue" (a date
where a failure is required); replacing the call by the parser's own throwing parse recurses into the facade (StackOverflowError).
Declared alternatives (G9): hop 1 collapses whitespace runs; hop 3 trims the string; hop 4 calls parser.parseObject(str). Each leaves
the trigger failing.
Recorded workarounds (not repairs of the chain; the gold still returns null for unparseable text, against "as DateParser#parse(String)
does" and "@return the parsed date"):
 W-1 a null test added after the gold's result in any hop (or in the facade), e.g. at hop 4
     `Date date = DateUtils.parseLeadingDate(parser, str, lead, form); if (date == null) { throw new ParseException(lead + form, 0); }`:
     it re-implements, above the gold, the decision the gold documents; every pass-through hop would otherwise return what the gold
     returns.
 W-2 FastDateParser.parse(String, ParsePosition) throwing IllegalArgumentException instead of returning null on a mismatch: the gold
     would convert it, but that breaks DateParser#parse(String, ParsePosition)'s documented "In case of error, returns null".
 B-0 the facade's original body (or a hop calling parse(String, ParsePosition) and throwing itself) makes the chain, including the
     gold, dead.

Lie: the facade's javadoc claims the string is first split at its whitespace and each piece is matched against the field of the
pattern at the same position; the chain splits nothing (one regular expression, compiled once, is matched against the whole string
by FastDateParser.parse(String, ParsePosition)). It names neither the null result, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: parser is called for the parse; str is parsed and written into the message; lead and form are written into the message
     that both throws carry; no parameter is only argument-checked (the gold has no argument check).
  T2 absent: message is read by both throws; date is assigned in the try, tested and returned; pe is thrown; no literal-initialised
     local; the catch and the null decision each throw, the fall-through returns.
  T3 absent: no enum, type code, flag set or named format is involved; the two throws (a value the parser rejects, a null result)
     are not a closed set under the closure rule, and both are handled.
  T4 absent: "Parses the beginning of a string to produce a date, as DateParser#parse(String) does" is a general description the
     parse line addresses; "@throws ParseException if the parser rejects the string" is met by both throws; "@param lead ... may be
     empty" and "@param form ... named in the exception message" are met by the message line; "not null" clauses are caller
     preconditions.
 Variant gold (javadoc, signature, message = lead + "Unparseable date: ..." + form, date = parser.parse(str, new ParsePosition(0)) in a
 try whose catch of IllegalArgumentException throws a ParseException with that message and the cause, return date):
  T1 absent: parser parses; str is parsed and written into the message; lead and form are written into the message the catch
     throws (a thrown exception, not an argument check).
  T2 absent: message reaches the thrown ParseException; date is assigned from the parse and returned; pe is thrown; no
     literal-initialised local, no loop, cursor, counter, flag or best-so-far; the catch throws, so it is not a no-op branch.
  T3 absent: no closed set is fixed by the gold's text (no enum, type code, flag or named format); the gold's text names no class
     ("finite", "all", "every") that it would handle in part; a rejected value is the only failure treatment ("No member handled"
     for any other).
  T4 absent: "as DateParser#parse(String) does" names a method, not a concrete rule, and the parse line addresses "parses the
     beginning of a string"; "@return the parsed date" is a general description; "@throws ParseException if the parser rejects the
     string" is produced by the catch's throw; "used in"/"named in the exception message" are met by the message line; no inline
     comment; the identifiers message, date, pe and ex name what they hold."""

FDP = "src/main/java/org/apache/commons/lang3/time/FastDateParser.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"

LIE = ("The string is first split at its whitespace, and each piece is then matched against the field of the pattern at the "
       "same position.")

GOLD_TEXT = '''/**
 * <p>Parses the beginning of a string to produce a date, as
 * {@link DateParser#parse(String)} does.</p>
 *
 * @param parser  the parser to use, not null
 * @param str  the date to parse, not null
 * @param lead  the text put in front of the exception message, may be empty
 * @param form  the form the parser expects, named in the exception message
 * @return the parsed date
 * @throws ParseException if the parser rejects the string
 */
public static Date parseLeadingDate(DateParser parser, String str, String lead, String form) throws ParseException {
    String message = lead + "Unparseable date: \\"" + str + "\\" does not match " + form;
    Date date;
    try {
        date = parser.parse(str, new ParsePosition(0));
    } catch (IllegalArgumentException ex) {
        ParseException pe = new ParseException(message, 0);
        pe.initCause(ex);
        throw pe;
    }
    if (date == null) {
        throw new ParseException(message, 0);
    }
    return date;
}'''

HOP1 = '''/**
 * <p>Parses the beginning of a String to produce a date with the given parser.</p>
 *
 * <p>When the parser uses the imperial locale, whose calendar has no dates
 * before 1868 AD, the exception message starts with a note saying so.</p>
 *
 * @param parser  the parser to use, not null
 * @param str  the String to parse, not null
 * @param form  the form the parser expects, named in the exception message
 * @param imperial  the imperial locale
 * @return the parsed date
 * @throws ParseException if the parser rejects the String
 */
public static Date parseToDate(DateParser parser, String str, String form, Locale imperial) throws ParseException {
    String lead = "";
    if (parser.getLocale().equals(imperial)) {
        lead = "(The " + parser.getLocale() + " locale does not support dates before 1868 AD)\\n";
    }
    return ToStringStyle.dateFromText(parser, str, lead, form);
}'''

HOP2 = '''/**
 * <p>Parses the beginning of a <code>String</code> to produce a date
 * with the given parser.</p>
 *
 * @param parser  the parser to use, not <code>null</code>
 * @param str  the <code>String</code> to parse, not <code>null</code>
 * @param lead  the text put in front of the exception message
 * @param form  the form the parser expects
 * @return the parsed date
 * @throws ParseException if the parser rejects the <code>String</code>
 */
public static Date dateFromText(DateParser parser, String str, String lead, String form) throws ParseException {
    return StrBuilder.readDate(parser, str, lead, form);
}'''

HOP3 = '''/**
 * Reads a date from the beginning of a string with the given parser.
 *
 * @param parser  the parser to use, not null
 * @param str  the string to read, not null
 * @param lead  the text put in front of the exception message
 * @param form  the form the parser expects
 * @return the date read
 * @throws ParseException if the parser rejects the string
 */
public static Date readDate(DateParser parser, String str, String lead, String form) throws ParseException {
    return ArrayUtils.parseDateWith(parser, str, lead, form);
}'''

HOP4 = '''/**
 * <p>Parses the beginning of a String to produce a date with the given parser.</p>
 *
 * @param parser  the parser to use, not null
 * @param str  the String to parse, not null
 * @param lead  the text put in front of the exception message
 * @param form  the form the parser expects
 * @return the parsed date
 * @throws ParseException if the parser rejects the String
 */
public static Date parseDateWith(DateParser parser, String str, String lead, String form) throws ParseException {
    return DateUtils.parseLeadingDate(parser, str, lead, form);
}'''

DESIGN = {
 "instance": "Lang-10", "project": "Lang", "bug_id": 10, "seed": 7705,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": FDP, "class": "org.apache.commons.lang3.time.FastDateParser", "method": "parse", "near_line": 253},
 "facade_variant": "V2+V1",
 "state_passed": "receiver `this` (typed DateParser) plus the values of the private field parsePattern (its pattern() String) and "
                 "the package-private static field JAPANESE_IMPERIAL (Locale) to hop 1; no write-back",
 "reachability_probe": "probe throw as first statement of FastDateParser.parse(String): full suite 36 failing tests, all "
                       "java.lang.IllegalStateException: PROBE-REACHED at FastDateParser.parse(FastDateParser.java:250) (18 "
                       "FastDateParserTest methods, e.g. testParseNumerics at FastDateParserTest.java:325, and the same 18 inherited "
                       "by FastDateFormat_ParserTest via FastDateFormat.parse); testLANG_831 reaches it but swallows the Exception",
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/time/FastDateParserTest.java",
             "test_class": "org.apache.commons.lang3.time.FastDateParserTest", "test_method": "testLANG_831"},
 "expected_signature": "Expected FDF failure, but got null for [M E,3  Tue]",
 "gold": {"method": "parseLeadingDate", "text": GOLD_TEXT,
          "fault": {"old": "            throw pe;\n"
                           "        }\n"
                           "        if (date == null) {\n"
                           "            throw new ParseException(message, 0);\n"
                           "        }\n"
                           "        return date;\n",
                    "new": "            throw pe;\n"
                           "        }\n"
                           "        return date;\n"}},
 "pre_edits": {
   "chain": [{"file": FDP,
              "old": "    /* (non-Javadoc)\n"
                     "     * @see org.apache.commons.lang3.time.DateParser#parse(java.lang.String)\n"
                     "     */\n",
              "new": "    /**\n"
                     "     * <p>Parses text from the beginning of the given string to produce a date.\n"
                     "     * The string is first split at its whitespace, and each piece is then\n"
                     "     * matched against the field of the pattern at the same position.</p>\n"
                     "     *\n"
                     "     * @see org.apache.commons.lang3.time.DateParser#parse(java.lang.String)\n"
                     "     */\n"}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.lang3.StringUtils.parseToDate(this, source, parsePattern.pattern(), JAPANESE_IMPERIAL);",
   "lie": LIE,
   "hops": [
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "parseToDate",
      "imports": ["java.text.ParseException", "java.util.Date", "org.apache.commons.lang3.builder.ToStringStyle",
                  "org.apache.commons.lang3.time.DateParser"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "dateFromText",
      "imports": ["java.text.ParseException", "java.util.Date", "org.apache.commons.lang3.text.StrBuilder",
                  "org.apache.commons.lang3.time.DateParser"], "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "readDate",
      "imports": ["java.text.ParseException", "java.util.Date", "org.apache.commons.lang3.time.DateParser"], "text": HOP3},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "parseDateWith",
      "imports": ["java.text.ParseException", "java.util.Date", "org.apache.commons.lang3.time.DateParser",
                  "org.apache.commons.lang3.time.DateUtils"], "text": HOP4},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "parseLeadingDate", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.time.DateUtils::parseDateWithLeniency",
              "org.apache.commons.lang3.time.DateParser::parse",
              "org.apache.commons.lang3.time.DateUtils::parseDate"],
 "ownership_reason": "Only the gold calls the parser and decides whether its result is a date; hops 2-4 pass the parser, the "
                     "string, the message lead and the expected form along unchanged and hop 1 only composes the lead (the note "
                     "on the supported date range of the imperial locale). The gold's javadoc promises to parse the beginning of a "
                     "string to produce a date as DateParser#parse(String) does and to return the parsed date; for \"3  Tue\" "
                     "against \"M E\" it returns null instead of the ParseException that DateParser#parse(String) documents "
                     "('@throws ParseException if the beginning of the specified string cannot be parsed'). The null result of "
                     "the parser is its documented error signal (DateParser#parse(String, ParsePosition): 'In case of error, "
                     "returns null'; FastDateParser.parse(String, ParsePosition) returns null when the pattern does not match), "
                     "and DateUtils.parseDateWithLeniency, the sibling in the gold's own class, treats exactly that null as no "
                     "match and throws ParseException (DateUtilsTest testParseDate, testParseDateWithLeniency and "
                     "testLANG799_EN_FAIL pass). No one-line change of the values above the gold makes the non-matching string "
                     "throw: collapsing its whitespace makes it match as a date where a failure is required, trimming changes "
                     "nothing, and the parser's own throwing parse(String) is the facade itself.",
 "ownership_tests": ["org.apache.commons.lang3.time.DateUtilsTest::testParseDate",
                     "org.apache.commons.lang3.time.DateUtilsTest::testParseDateWithLeniency",
                     "org.apache.commons.lang3.time.DateUtilsTest::testLANG799_EN_FAIL"],
 "compensating": {
   "chain": [
     {"file": SU, "old": "return ToStringStyle.dateFromText(parser, str, lead, form);",
      "new": "return ToStringStyle.dateFromText(parser, str.replaceAll(\"\\\\s+\", \" \"), lead, form);",
      "why": "hop 1 collapses runs of whitespace in the string before it is parsed"},
     {"file": SB, "old": "return ArrayUtils.parseDateWith(parser, str, lead, form);",
      "new": "return ArrayUtils.parseDateWith(parser, str.trim(), lead, form);",
      "why": "hop 3 trims the string before it is parsed"},
     {"file": AU, "old": "return DateUtils.parseLeadingDate(parser, str, lead, form);",
      "new": "return (Date) parser.parseObject(str);",
      "why": "hop 4 uses the parser's own throwing parse of a String"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts drawn with mr_lib.py preview Lang-10 org/apache/commons/lang3/time/FastDateParser.java 5 "
               "(instance seed 7705; the draw excludes the facade file, the only allowed candidate's file), used in draw order, "
               "none substituted: StringUtils (hop 1, 6486 lines), builder.ToStringStyle (hop 2, 2280), text.StrBuilder (hop 3, "
               "2882), ArrayUtils (hop 4, 5796), time.DateUtils (hop 5, gold, 1888; the smallest host). All five are public "
               "top-level classes in which a public static method compiles (ToStringStyle is abstract, which does not affect a "
               "static method). Preview anchors (seed 7705 + 100 + i): hop 1 after `ordinalIndexOf` (line 872), hop 2 after "
               "`appendEnd` (400), hop 3 after `appendFixedWidthPadRight` (1382), hop 4 after `lastIndexOf` (2436), hop 5 after "
               "`parseDateStrictly` (333). The facade calls hop 1 by its fully-qualified name; each hop imports the next host and "
               "java.text.ParseException, java.util.Date and time.DateParser where missing.",
}
