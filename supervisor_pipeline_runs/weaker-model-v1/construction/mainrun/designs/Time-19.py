"""Main run Time-19 (C10 recipe on the fixed checkout of Defects4J Time-19; the real bug modified DateTimeZone, the target class).

Facade: DateTimeZone.forOffsetHoursMinutes(int, int) (the only allowed target, BATCH5_PREREGISTRATION.md row Time-19). Its only
production caller is DateTimeZone.forOffsetHours(int), which passes 0 minutes; its test callers are
TestDateTimeZone::testForOffsetHoursMinutes_int_int and TestDateTimeZoneCutover::testWithMinuteOfHourInDstChange_mockZone (0, 30).
Original computation: (0, 0) gives UTC; minutes outside 0..59 throw IllegalArgumentException("Minutes out of range: m"); then, in
a try block, the hours are converted to minutes with FieldUtils.safeMultiply(h, 60), the minutes are subtracted from that total
when it is negative and added otherwise (safeAdd), the result is converted to milliseconds (safeMultiply by MILLIS_PER_MINUTE),
an ArithmeticException becomes IllegalArgumentException("Offset is too large"), and the zone is DateTimeZone.forOffsetMillis.

The facade keeps its argument guard (the minutes range check, same message) and delegates to a five-hop chain drawn with the
instance seed 4258 (mr_lib preview, target org/joda/time/DateTimeZone.java, draw order, no substitution):
  hop 1 format.DateTimeFormatterBuilder.timeZoneForOffset   plumbing: ArithmeticException -> IllegalArgumentException
                                                             ("Offset is too large"), as in the original try/catch
  hop 2 tz.DateTimeZoneBuilder.toOffsetZone                 decision: a zero offset gives the UTC zone (the original first test)
  hop 3 format.ISODateTimeFormat.offsetZone                 pass-through
  hop 4 DateTime.zoneAtOffset                               pass-through
  hop 5 LocalDate.zoneFromOffsetFields                      GOLD: the per-offset core: the hours in minutes, the minutes taken
                                                             with the sign of the hours, the total in milliseconds, the zone
The correct configuration returns the original result for every input: the same guard and message, the same zero result (UTC;
forOffsetMillis(0) would also give UTC), the same safe arithmetic (the subtraction of the minutes is written as a negation of the
minutes followed by the same safeAdd), the same exception translation and the same forOffsetMillis call. forOffsetMillis itself
never throws ArithmeticException, so moving it inside the try block of hop 1 changes nothing.

Fault (omission of a special-case decision in the gold): the statement that gives the minutes the sign of a negative hour count
(`if (hoursInMinutes < 0) { minutes = -minutes; }`) is dropped, so the minutes are always added. The gold then reads as the
plain conversion hours * 60 + minutes. Trigger: the EXISTING test TestDateTimeZone::testForOffsetHoursMinutes_int_int; its
assertions for (0, 0), (3, 15) and (-2, 0) still hold, and assertEquals(DateTimeZone.forID("-02:30"),
DateTimeZone.forOffsetHoursMinutes(-2, 30)) at line 308 fails with expected:<-02:30> but was:<-01:30>. It is the only test that
passes a negative hour count together with non-zero minutes: forOffsetHours always passes 0 minutes (testForOffsetHours_int and
the 36 other forOffsetHours calls in the tests still pass), and the cutover test passes (0, 30), whose hour count is not negative.

The gold's javadoc states the idiomatic contract in the facade's own words (a time zone instance for the specified offset to UTC
in hours and minutes; the minutes of the offset from 0 to 59) and is silent on signs. The offset whose hours are -2 and whose
minutes are 30 is '-02:30' (-150 minutes): the minutes of an offset are its unsigned mm field, 0 to 59, and the sign of the offset
covers both fields; the variant returns '-01:30'. The convention is pinned outside the gold: the facade's javadoc ('The minutes
value is always positive and in the range 0 to 59. If constructed with the values (-2, 30), the resulting zone is '-02:30'');
DateTimeFormatterBuilder.TimeZoneOffset.parseInto reads the hours and the minutes (0 to 59) of an offset as magnitudes and
applies the sign to their sum (`negative ? -offset : offset`), pinned by TestDateTimeZone::testForID_String ('-07:05:34.0' has
the offset -7 h -5 min -34 s); ZoneInfoCompiler.parseTime negates the whole 'h:mm:ss' after a leading '-', pinned by
TestCompiler::testCompile (the Los Angeles LMT offset -7:52:58 gives -07:52:58 in TestBuilder's data); DateTimeZone.printOffset
prints the sign first and then the hours and minutes of the magnitude (testForOffsetMillis_int).

Single owner: only the gold holds the hour count and the minutes together with the arithmetic that combines them; hop 1 translates
an exception, hop 2 decides the zero offset, hops 3 and 4 pass the two values along unchanged, and every hop documents the minutes
as 0 to 59. The gold returns the zone itself, so no caller receives a number it could correct.
Declared alternatives (G9), none absorbs the fault: hop 4 counts a negative offset from the next whole hour further from UTC; hop 3
passes the minutes of a negative offset as the minutes left to the next whole hour; hop 2 counts a negative offset from the next
whole hour nearer to UTC.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy with
defects4j test; B-0 is the facade's original body):
 B-0 bypass: the facade (its original body) or any of hops 1-4 computes the offset itself and returns DateTimeZone.forOffsetMillis
     of it, discarding the rest of the chain including the gold.
 B-1 bypass (mirror): a hop takes the gold's sign decision itself, asks the next hop for the zone of the mirrored offset and
     builds a new zone from its negated offset, e.g. hop 4 `return hours < 0 ? DateTimeZone.forOffsetMillis(-LocalDate.
     zoneFromOffsetFields(-hours, minutes).getOffset(0L)) : LocalDate.zoneFromOffsetFields(hours, minutes);`. On the trigger
     input the gold is never asked about the offset (-2, 30); the zone returned is a second zone made by the hop's own factory
     call from a number, and the gold's zone is thrown away: a second implementation of the gold's sign rule and of its zone
     construction.
 B-2 not path-consistent: hop 4 passes signed minutes, `LocalDate.zoneFromOffsetFields(hours, hours < 0 ? -minutes : minutes)`.
     It passes the suite only because the variant adds whatever it receives; it hands the gold minutes outside its documented
     0 to 59 (and against the facade's 'The minutes value is always positive'); on the correct gold it gives '-01:30' for (-2, 30).
 B-3 not path-consistent: hop 4 borrows an hour, `hours < 0 && minutes > 0 ? LocalDate.zoneFromOffsetFields(hours - 1, 60 - minutes)
     : LocalDate.zoneFromOffsetFields(hours, minutes)`. It asks the gold for the offset with hours -3 and minutes 30, which is
     '-03:30' under the facade's convention and the parsers' (evidence), to obtain '-02:30'; on the correct gold it gives '-03:30'
     for (-2, 30).

Lie: the facade's javadoc claims the offset is first expressed as a JDK TimeZone with a custom GMT ID and the zone is then
obtained from that TimeZone as by forTimeZone; the chain creates no java.util.TimeZone and never calls forTimeZone (the gold calls
forOffsetMillis). It names neither signs, minutes nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; hoursInMinutes = safeMultiply(hours, 60); if (hoursInMinutes < 0) { minutes = -minutes; }
 offsetMinutes = safeAdd(hoursInMinutes, minutes); return forOffsetMillis(safeMultiply(offsetMinutes, MILLIS_PER_MINUTE))):
  T1 absent: hours feeds hoursInMinutes, minutes feeds offsetMinutes; both reach the returned zone.
  T2 absent: hoursInMinutes and offsetMinutes are read on every path; the reassigned parameter minutes is read by the safeAdd; the
     if changes the result; no literal-initialised local, no loop.
  T3 absent: the sign decision covers both outcomes (negative: negate; otherwise: keep); no other set, case or pair end.
  T4 absent: the javadoc names a general computation; '@param minutes ... from 0 to 59' is a caller precondition.
  Nothing needed rewriting.
 Variant gold (javadoc, signature, `int hoursInMinutes = FieldUtils.safeMultiply(hours, 60); int offsetMinutes =
 FieldUtils.safeAdd(hoursInMinutes, minutes); return DateTimeZone.forOffsetMillis(FieldUtils.safeMultiply(offsetMinutes,
 DateTimeConstants.MILLIS_PER_MINUTE));`):
  T1 absent: hours is read by the first line and minutes by the second, and each changes the returned zone; there is no argument
     check.
  T2 absent: hoursInMinutes is read by the second line, offsetMinutes by the return; both are computed from the parameters, not
     literals; no loop, no branch, case or ternary.
  T3 absent: no case, branch, sign test or value-class test remains (no member of any set handled); the two fields of the offset,
     hours and minutes, are both read and both enter the sum; no range ends.
  T4 absent: 'a time zone instance for the specified offset to UTC in hours and minutes' and '@return the DateTimeZone object for
     the offset' are general descriptions that the lines address; '@param minutes  the minutes of the offset, from 0 to 59' is a
     caller precondition on a parameter; no limit, value class, case or property of the result is named; no inline comment;
     the identifiers hoursInMinutes and offsetMinutes name what those lines compute."""

DTZ = "src/main/java/org/joda/time/DateTimeZone.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"
DTZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
ISO = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"
DT = "src/main/java/org/joda/time/DateTime.java"
LD = "src/main/java/org/joda/time/LocalDate.java"

GOLD_TEXT = '''/**
 * Gets a time zone instance for the specified offset to UTC in hours and
 * minutes.
 *
 * @param hours  the hours of the offset
 * @param minutes  the minutes of the offset, from 0 to 59
 * @return the DateTimeZone object for the offset
 */
public static DateTimeZone zoneFromOffsetFields(int hours, int minutes) {
    int hoursInMinutes = FieldUtils.safeMultiply(hours, 60);
    if (hoursInMinutes < 0) {
        minutes = -minutes;
    }
    int offsetMinutes = FieldUtils.safeAdd(hoursInMinutes, minutes);
    return DateTimeZone.forOffsetMillis(FieldUtils.safeMultiply(offsetMinutes, DateTimeConstants.MILLIS_PER_MINUTE));
}'''

HOP1 = '''/**
 * Gets a time zone instance for the specified offset to UTC in hours and
 * minutes.
 *
 * @param hours  the hours of the offset
 * @param minutes  the minutes of the offset, from 0 to 59
 * @return the DateTimeZone object for the offset
 * @throws IllegalArgumentException if the offset is too large or too small
 */
public static DateTimeZone timeZoneForOffset(int hours, int minutes) {
    try {
        return DateTimeZoneBuilder.toOffsetZone(hours, minutes);
    } catch (ArithmeticException ex) {
        throw new IllegalArgumentException("Offset is too large");
    }
}'''

HOP2 = '''/**
 * Gets a time zone instance for the specified offset to UTC in hours and
 * minutes. A zero offset gives the UTC zone.
 *
 * @param hours  the hours of the offset
 * @param minutes  the minutes of the offset, from 0 to 59
 * @return the DateTimeZone object for the offset
 */
public static DateTimeZone toOffsetZone(int hours, int minutes) {
    if (hours == 0 && minutes == 0) {
        return DateTimeZone.UTC;
    }
    return ISODateTimeFormat.offsetZone(hours, minutes);
}'''

HOP3 = '''/**
 * Gets a time zone instance for the specified offset to UTC in hours and
 * minutes, such as the offset of a parsed datetime.
 *
 * @param hours  the hours of the offset
 * @param minutes  the minutes of the offset, from 0 to 59
 * @return the DateTimeZone object for the offset
 */
public static DateTimeZone offsetZone(int hours, int minutes) {
    return DateTime.zoneAtOffset(hours, minutes);
}'''

HOP4 = '''/**
 * Gets a time zone instance for the specified offset to UTC in hours and
 * minutes, suitable for {@link #withZone(DateTimeZone)}.
 *
 * @param hours  the hours of the offset
 * @param minutes  the minutes of the offset, from 0 to 59
 * @return the DateTimeZone object for the offset
 */
public static DateTimeZone zoneAtOffset(int hours, int minutes) {
    return LocalDate.zoneFromOffsetFields(hours, minutes);
}'''

DESIGN = {
 "instance": "Time-19", "project": "Time", "bug_id": 19, "seed": 4258,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": DTZ, "class": "org.joda.time.DateTimeZone", "method": "forOffsetHoursMinutes", "near_line": 253},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestDateTimeZone.java",
             "test_class": "org.joda.time.TestDateTimeZone", "test_method": "testForOffsetHoursMinutes_int_int"},
 "expected_signature": "expected:<-02:30> but was:<-01:30>",
 "gold": {"method": "zoneFromOffsetFields", "text": GOLD_TEXT,
          "fault": {"old": "        int hoursInMinutes = FieldUtils.safeMultiply(hours, 60);\n"
                           "        if (hoursInMinutes < 0) {\n"
                           "            minutes = -minutes;\n"
                           "        }\n"
                           "        int offsetMinutes = FieldUtils.safeAdd(hoursInMinutes, minutes);",
                    "new": "        int hoursInMinutes = FieldUtils.safeMultiply(hours, 60);\n"
                           "        int offsetMinutes = FieldUtils.safeAdd(hoursInMinutes, minutes);"}},
 "chain": {
   "facade_body": "if (minutesOffset < 0 || minutesOffset > 59) {\n"
                  "            throw new IllegalArgumentException(\"Minutes out of range: \" + minutesOffset);\n"
                  "        }\n"
                  "        return org.joda.time.format.DateTimeFormatterBuilder.timeZoneForOffset(hoursOffset, minutesOffset);",
   "lie": "The offset is first expressed as a JDK TimeZone with a custom GMT ID, and the zone is then obtained from that "
          "TimeZone in the same way as by forTimeZone.",
   "hops": [
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "timeZoneForOffset",
      "imports": ["org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP1},
     {"file": DTZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "toOffsetZone",
      "imports": ["org.joda.time.format.ISODateTimeFormat"], "text": HOP2},
     {"file": ISO, "class": "org.joda.time.format.ISODateTimeFormat", "method": "offsetZone",
      "imports": ["org.joda.time.DateTime", "org.joda.time.DateTimeZone"], "text": HOP3},
     {"file": DT, "class": "org.joda.time.DateTime", "method": "zoneAtOffset", "imports": [], "text": HOP4},
     {"file": LD, "class": "org.joda.time.LocalDate", "method": "zoneFromOffsetFields", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.DateTimeZone::forOffsetHoursMinutes",
              "org.joda.time.format.DateTimeFormatterBuilder$TimeZoneOffset::parseInto",
              "org.joda.time.tz.ZoneInfoCompiler::parseTime",
              "org.joda.time.DateTimeZone::printOffset"],
 "ownership_reason": "Only the gold holds the hour count and the minutes together with the arithmetic that combines them into the "
                     "offset; hop 1 translates an ArithmeticException into IllegalArgumentException, hop 2 returns UTC for a zero "
                     "offset, hops 3 and 4 pass the two values along unchanged, and every hop documents the minutes as 0 to 59. "
                     "The gold returns the zone itself, so no caller receives a number it could correct. The offset with hours -2 "
                     "and minutes 30 is '-02:30': the minutes of an offset are its unsigned field, 0 to 59, and the sign covers "
                     "both fields. This is pinned outside the gold: the facade's javadoc ('The minutes value is always positive "
                     "and in the range 0 to 59. If constructed with the values (-2, 30), the resulting zone is '-02:30''); "
                     "DateTimeFormatterBuilder.TimeZoneOffset.parseInto reads the hours and the minutes (0 to 59) as magnitudes "
                     "and applies the sign to their sum (TestDateTimeZone testForID_String: '-07:05:34.0' has the offset -7 h "
                     "-5 min -34 s); ZoneInfoCompiler.parseTime negates the whole h:mm:ss after a leading '-' (TestCompiler "
                     "testCompile: the LMT offset -7:52:58 is -07:52:58); DateTimeZone.printOffset prints the sign, then the "
                     "hours and minutes of the magnitude (testForOffsetMillis_int). A hop that passes signed minutes or borrows "
                     "an hour (hours - 1, 60 - minutes) passes the existing tests only on the variant: it hands the gold minutes "
                     "outside 0 to 59, or asks it for '-03:30' to get '-02:30', so it is not consistent with the path.",
 "ownership_tests": ["org.joda.time.TestDateTimeZone::testForID_String",
                     "org.joda.time.TestDateTimeZone::testForOffsetHours_int",
                     "org.joda.time.TestDateTimeZone::testForOffsetMillis_int",
                     "org.joda.time.tz.TestCompiler::testCompile"],
 "compensating": {
   "chain": [
     {"file": DT, "old": "return LocalDate.zoneFromOffsetFields(hours, minutes);",
      "new": "return LocalDate.zoneFromOffsetFields(hours < 0 ? hours - 1 : hours, minutes);",
      "why": "hop 4 counts a negative offset from the next whole hour further from UTC"},
     {"file": ISO, "old": "return DateTime.zoneAtOffset(hours, minutes);",
      "new": "return DateTime.zoneAtOffset(hours, hours < 0 && minutes > 0 ? 60 - minutes : minutes);",
      "why": "hop 3 passes the minutes of a negative offset as the minutes left to the next whole hour"},
     {"file": DTZB, "old": "return ISODateTimeFormat.offsetZone(hours, minutes);",
      "new": "return ISODateTimeFormat.offsetZone(hours < 0 ? hours + 1 : hours, minutes);",
      "why": "hop 2 counts a negative offset from the next whole hour nearer to UTC"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4258 (mr_lib preview, target org/joda/time/DateTimeZone.java): "
               "format.DateTimeFormatterBuilder (hop 1), tz.DateTimeZoneBuilder (hop 2), format.ISODateTimeFormat (hop 3), "
               "DateTime (hop 4), LocalDate (hop 5, gold); the draw relaxed the distinct-from-target-package rule for hosts 3-5 "
               "(fewer than two other-package classes of 1,500 lines). All five are public top-level classes (DateTime and "
               "LocalDate are final, which does not affect a static method) in which a static method compiles and sees "
               "DateTimeZone; every preview anchor lies in the outer class (4-space indented); none was skipped. The facade "
               "calls hop 1 by its fully-qualified name; hop 1 imports DateTimeZoneBuilder, hop 2 imports ISODateTimeFormat, "
               "hop 3 imports DateTime and DateTimeZone; hop 4 and the gold share the org.joda.time package with the next host "
               "and with DateTimeZone, and LocalDate already imports FieldUtils.",
}
