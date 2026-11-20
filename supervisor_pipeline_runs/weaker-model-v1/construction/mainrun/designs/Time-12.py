"""Main run Time-12 (C10 recipe on the fixed checkout of Defects4J Time-12; the real bug modified LocalDate and LocalDateTime,
the target class is LocalDateTime).

Facade: LocalDateTime.fromDateFields(Date) (allowed target, BATCH5_PREREGISTRATION.md row Time-12). The other allowed targets were
set aside. LocalDate.fromCalendarFields is also called by LocalDate.fromDateFields for every negative instant, so a chain under it
is reached by both factories and every omission in its computation (the era step) fails the calendar test AND the date test of
the same case (testFactory_fromCalendarFields_beforeYearZero3 and testFactory_fromDateFields_beforeYearZero3), breaking gate G5.
LocalDate.fromDateFields has no millisecond, and every omission in its year, month or day transfer or in its era step is caught
by two tests at once (beforeYearZero1 and beforeYearZero3, or after1970 and the five toDate tests that call it). In
LocalDateTime.fromDateFields the millisecond of the second is taken from the instant, and the step that brings the remainder of a
negative instant into 0..999 is reached by exactly one existing test (testFactory_fromDateFields_before1970), the only test that
converts an AD date before 1970 through this factory.
Original computation of the facade: a null date throws IllegalArgumentException; a negative instant is converted through a
GregorianCalendar of the default zone and LocalDateTime.fromCalendarFields (whose era step counts a BC year as 1 - yearOfEra);
any other date from its own fields: getYear() + 1900, getMonth() + 1, getDate(), getHours(), getMinutes(), getSeconds() and
(((int) (getTime() % 1000)) + 1000) % 1000.

Chain (hosts in draw order for seed 4743, mr_lib preview, target org/joda/time/LocalDateTime.java, none skipped):
  hop 1 format.PeriodFormatterBuilder.localDateTimeOf   placement: places the date in a Gregorian calendar of the default zone
  hop 2 tz.DateTimeZoneBuilder.wallDateTimeOf           decision: a date in era BC is converted from the calendar's fields
                                                        (LocalDateTime.fromCalendarFields, untouched); any other date goes on
  hop 3 LocalTime.dateTimeFieldsOf                      pass-through (a date in era AD)
  hop 4 format.ISODateTimeFormat.isoDateTimeOf          placement: the day, from the date's year, month and day-of-month fields
  hop 5 format.DateTimeFormatterBuilder.localDateTimeAt GOLD: the time of day of the date on that day: hour, minute, second and
                                                        the millisecond of the second taken from the instant, with the step
                                                        that moves a negative remainder into 0..999
The correct configuration returns the original result for every input: a BC date takes exactly the original calendar route (a BC
instant is always negative); a date with a non-negative instant takes exactly the original field route; an AD date with a
negative instant (1 AD to 1969) now takes the field route instead of the calendar route, and the two give the same fields (the
JDK computes Date's accessors and GregorianCalendar's fields with the same default zone and the same Julian/Gregorian cutover;
the year of an AD date is its year of era; the floor remainder of the instant is the calendar's MILLISECOND for every zone whose
offsets are whole seconds, which every tz-database zone is). This is the route LocalTime.fromDateFields and
TimeOfDay.fromDateFields already take for every date.

Fault (one-line omission of a decision in the gold): the if-block that adds 1000 to a negative remainder is dropped, so the
millisecond of a date before 1970 is the negative remainder of its instant. Trigger: the EXISTING test
TestLocalDateTime_Constructors::testFactory_fromDateFields_before1970: 1969-02-03 04:05:06.007 in the JDK default zone has the
instant -28641293993, whose remainder is -993, and new LocalTime(4, 5, 6, -993) throws IllegalFieldValueException 'Value -993 for
millisOfSecond must be in the range [0,999]'. It is the only test that newly fails: testFactory_fromDateFields_after1970 and the
five TestLocalDateTime_Basics toDate tests (which call the facade) use instants after 1970; testFactory_fromDateFields_beforeYearZero1
and _beforeYearZero3 are in era BC and leave the chain at hop 2; LocalDate's factories, LocalTime.fromDateFields and
TimeOfDay.fromDateFields are untouched.

The gold's javadoc states the idiomatic contract (a local date-time on the given day at the time of day of the date) and is
silent on negative instants and on how the millisecond is found; 04:05:06.007 is the time of day of the trigger's date, so the
variant violates that contract on the trigger input (it throws). External pins (the same step outside the gold, with passing
tests): LocalTime.fromDateFields and TimeOfDay.fromDateFields take the millisecond as (((int) (getTime() % 1000)) + 1000) % 1000
and convert a 1969 date from its own fields (TestLocalTime_Constructors::testFactory_FromDateFields_before1970 and
TestTimeOfDay_Constructors::testFactory_FromDateFields_before1970 expect millisecond 7 for the trigger's very date);
LocalDateTime.fromCalendarFields takes the millisecond as the calendar's MILLISECOND field (0..999;
testFactory_fromCalendarFields).

Single owner: only the gold computes the millisecond; hops 1-3 hold the date and the calendar, hop 4 the date and the day, and none
of them sees a millisecond. In the variant the gold throws on the trigger input, so no caller can recover a value from it, and no
caller can hand the gold a date with the same time of day and a non-negative instant without finding the millisecond itself.
Declared alternatives (G9): hop 2 also converts a date before the Gregorian change from its calendar; hop 4 takes the day from
LocalDate.fromDateFields; hop 3 passes the date rounded to its whole second. Each still fails the trigger (1969 is after the
change; the day is not the step; the rounded date gives 04:05:07.000).
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each):
 B-0 bypass: hop 2 returns LocalDateTime.fromCalendarFields(calendar) for every date (or the facade's original body is restored),
     discarding hops 3-4 and the gold.
 B-1 bypass: hop 2 also routes a negative instant to the calendar
     (`if (calendar.get(Calendar.ERA) == GregorianCalendar.BC || date.getTime() < 0) {`, the pristine factory's rule): on the
     trigger input the gold is never called and its result is replaced by LocalDateTime.fromCalendarFields; this contradicts hop
     2's documented split (any date not in era BC is converted from its own fields) and hop 3's and hop 4's documented domain (a
     date in era AD).
 B-2 bypass: hop 4 builds the result itself, `return day.toLocalDateTime(LocalTime.fromDateFields(date));`, a second
     implementation of the gold's computation that makes the gold dead.
 B-3 test-fitted, not a repair: hop 4 hands the gold the date moved by 400 Gregorian years
     (`return DateTimeFormatterBuilder.localDateTimeAt(new Date(date.getTime() + 146097L * 86400000L), day);`), whose instant is
     positive. It passes the suite only because the tested dates have the same zone offset 400 years later; it breaks hop 4's
     and the gold's documented time of day of the date itself: fromDateFields(1969-03-20 12:00 in America/Los_Angeles) gives
     13:00 (Pacific daylight time in 2369, standard time in 1969; checked on a scratch build), where the pristine factory gives
     12:00.

Lie: the facade's javadoc claims each date is first looked up in a small per-thread cache of recently converted dates and only a
date missing from it has its fields queried; the chain keeps no cache. It names neither the millisecond nor negative instants nor
any hop.

Pre-edit (behaviour-preserving, needed by the recipe): the facade's @SuppressWarnings("deprecation") line sits between its
javadoc and its header, so rewrite_facade finds no adjacent javadoc and cannot append the lie; the line is removed (the rewritten
facade body uses no deprecated API; an annotation of source retention has no effect on behaviour). The hops that call Date's
deprecated accessors (hop 4 and the gold) carry the same annotation themselves.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: date gives the instant and the hour, minute and second; day is the receiver of toLocalDateTime.
  T2 absent: millis is assigned from the instant, adjusted by the if and passed to LocalTime; the if changes millis exactly when
     the remainder is negative; no literal-initialised or loop-moved local.
  T3 absent: the only special-case text is the omitted if-block; it treats the only side on which a remainder of division by 1000
     can leave 0..999 (a remainder lies in (-1000, 1000)), so no range end or sibling is left out; no other set is handled.
  T4 absent: the javadoc names only 'a local date-time on a given day at the time of day of a date' and caller preconditions.
 Variant gold (javadoc, signature, `int millis = (int) (date.getTime() % 1000);` and the return):
  T1 absent: date is read for the instant, the hour, the minute and the second; day is the receiver of toLocalDateTime; both
     change the result.
  T2 absent: the only local, millis, is initialised from the instant (not a literal) and passed to the LocalTime constructor; no
     loop, no branch, case or ternary.
  T3 absent: no special value, sign, case or range end is handled at all (No member handled); the hour, minute and second are
     passed as read, and the millisecond is the one value computed, so no treatment is given to some members of a set and
     withheld from another; the gold's text names no class.
  T4 absent: 'Creates a local date-time on a given day at the time of day of a java.util.Date' and '@param date the date whose
     time of day is used' are general descriptions that the return line addresses; 'not null' clauses are caller preconditions;
     '@return ... never null' is met (a new object is returned); no comment; the identifiers (millis, day) name nothing the body
     does not meet."""

LDT = "src/main/java/org/joda/time/LocalDateTime.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
DZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
LT = "src/main/java/org/joda/time/LocalTime.java"
IDF = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"
DFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"

GOLD_TEXT = '''/**
 * Creates a local date-time on a given day at the time of day of a
 * <code>java.util.Date</code>.
 *
 * @param date  the date whose time of day is used, not null
 * @param day  the day of the local date-time, not null
 * @return the local date-time, never null
 */
@SuppressWarnings("deprecation")
public static LocalDateTime localDateTimeAt(Date date, LocalDate day) {
    int millis = (int) (date.getTime() % 1000);
    if (millis < 0) {
        millis = millis + 1000;
    }
    return day.toLocalDateTime(new LocalTime(date.getHours(), date.getMinutes(), date.getSeconds(), millis));
}'''

HOP1 = '''/**
 * Converts a <code>java.util.Date</code> to a local date-time with the
 * same field values.
 * <p>
 * The date is placed in a Gregorian calendar of the default time zone,
 * which gives the era of the date.
 *
 * @param date  the date to convert, not null
 * @return the local date-time, never null
 */
public static LocalDateTime localDateTimeOf(Date date) {
    GregorianCalendar calendar = new GregorianCalendar();
    calendar.setTime(date);
    return DateTimeZoneBuilder.wallDateTimeOf(date, calendar);
}'''

HOP2 = '''/**
 * Converts a <code>java.util.Date</code> to a local date-time with the
 * same field values, given a Gregorian calendar set to the date.
 * <p>
 * A date in era BC is converted from the fields of the calendar, as by
 * {@link LocalDateTime#fromCalendarFields(Calendar)}. Any other date is
 * converted from its own fields.
 *
 * @param date  the date to convert, not null
 * @param calendar  the Gregorian calendar set to the date, not null
 * @return the local date-time, never null
 */
public static LocalDateTime wallDateTimeOf(Date date, Calendar calendar) {
    if (calendar.get(Calendar.ERA) == GregorianCalendar.BC) {
        return LocalDateTime.fromCalendarFields(calendar);
    }
    return LocalTime.dateTimeFieldsOf(date);
}'''

HOP3 = '''/**
 * Converts a <code>java.util.Date</code> in era AD to a local date-time
 * with the same field values.
 *
 * @param date  the date to convert, not null
 * @return the local date-time, never null
 */
public static LocalDateTime dateTimeFieldsOf(Date date) {
    return ISODateTimeFormat.isoDateTimeOf(date);
}'''

HOP4 = '''/**
 * Converts a <code>java.util.Date</code> in era AD to a local date-time
 * with the same field values.
 * <p>
 * The day is the ISO date with the year, the month and the day of month
 * of the date.
 *
 * @param date  the date to convert, not null
 * @return the local date-time, never null
 */
@SuppressWarnings("deprecation")
public static LocalDateTime isoDateTimeOf(Date date) {
    LocalDate day = new LocalDate(date.getYear() + 1900, date.getMonth() + 1, date.getDate());
    return DateTimeFormatterBuilder.localDateTimeAt(date, day);
}'''

DESIGN = {
 "instance": "Time-12", "project": "Time", "bug_id": 12, "seed": 4743,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": LDT, "class": "org.joda.time.LocalDateTime", "method": "fromDateFields", "near_line": 233},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestLocalDateTime_Constructors.java",
             "test_class": "org.joda.time.TestLocalDateTime_Constructors",
             "test_method": "testFactory_fromDateFields_before1970"},
 "expected_signature": "Value -993 for millisOfSecond must be in the range [0,999]",
 "gold": {"method": "localDateTimeAt", "text": GOLD_TEXT,
          "fault": {"old": "        int millis = (int) (date.getTime() % 1000);\n"
                           "        if (millis < 0) {\n"
                           "            millis = millis + 1000;\n"
                           "        }\n",
                    "new": "        int millis = (int) (date.getTime() % 1000);\n"}},
 "pre_edits": {
   "chain": [{"file": LDT,
              "old": "    @SuppressWarnings(\"deprecation\")\n    public static LocalDateTime fromDateFields(Date date) {\n",
              "new": "    public static LocalDateTime fromDateFields(Date date) {\n"}],
 },
 "chain": {
   "facade_body": "if (date == null) {\n"
                  "            throw new IllegalArgumentException(\"The date must not be null\");\n"
                  "        }\n"
                  "        return org.joda.time.format.PeriodFormatterBuilder.localDateTimeOf(date);",
   "lie": "Each date is first looked up in a small per-thread cache of recently converted dates, and only a date "
          "that is not found there has its fields queried.",
   "hops": [
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "localDateTimeOf",
      "imports": ["java.util.Date", "java.util.GregorianCalendar", "org.joda.time.LocalDateTime",
                  "org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP1},
     {"file": DZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "wallDateTimeOf",
      "imports": ["java.util.Calendar", "java.util.Date", "java.util.GregorianCalendar", "org.joda.time.LocalDateTime",
                  "org.joda.time.LocalTime"], "text": HOP2},
     {"file": LT, "class": "org.joda.time.LocalTime", "method": "dateTimeFieldsOf",
      "imports": [], "text": HOP3},
     {"file": IDF, "class": "org.joda.time.format.ISODateTimeFormat", "method": "isoDateTimeOf",
      "imports": ["java.util.Date", "org.joda.time.LocalDate", "org.joda.time.LocalDateTime"], "text": HOP4},
     {"file": DFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "localDateTimeAt",
      "imports": ["java.util.Date", "org.joda.time.LocalDate", "org.joda.time.LocalDateTime", "org.joda.time.LocalTime"],
      "gold": True},
   ],
 },
 "evidence": ["org.joda.time.LocalTime::fromDateFields",
              "org.joda.time.TimeOfDay::fromDateFields",
              "org.joda.time.LocalDateTime::fromCalendarFields"],
 "ownership_reason": "Only the gold computes the millisecond of the second: hops 1-3 hold the date and its Gregorian calendar, "
                     "hop 4 the date and its day, and none of them sees a millisecond. The gold's contract is the time of day of "
                     "the date on the given day; for the trigger's 1969-02-03 04:05:06.007 the variant passes the negative "
                     "remainder -993 of the instant to new LocalTime, which throws, so no caller can recover a value, and no "
                     "caller can give the gold a date with the same time of day and a non-negative instant without finding the "
                     "millisecond itself. The convention is pinned outside the gold: LocalTime.fromDateFields and "
                     "TimeOfDay.fromDateFields convert a date from its own fields and take the millisecond as "
                     "(((int) (getTime() % 1000)) + 1000) % 1000; TestLocalTime_Constructors and TestTimeOfDay_Constructors "
                     "testFactory_FromDateFields_before1970 expect millisecond 7 for the trigger's very date and pass; "
                     "LocalDateTime.fromCalendarFields takes the calendar's MILLISECOND field (0..999). Hop 2 converts only a "
                     "date in era BC through the calendar, as its javadoc states, and hops 3 and 4 document their domain as a "
                     "date in era AD, which the trigger's date is; routing a negative instant through the calendar at hop 2 "
                     "would replace the gold's result with LocalDateTime.fromCalendarFields (a bypass that contradicts hop 2's "
                     "documented split).",
 "ownership_tests": ["org.joda.time.TestLocalTime_Constructors::testFactory_FromDateFields_before1970",
                     "org.joda.time.TestTimeOfDay_Constructors::testFactory_FromDateFields_before1970",
                     "org.joda.time.TestLocalDateTime_Constructors::testFactory_fromCalendarFields",
                     "org.joda.time.TestLocalDateTime_Constructors::testFactory_fromDateFields_after1970"],
 "compensating": {
   "chain": [
     {"file": DZB, "old": "if (calendar.get(Calendar.ERA) == GregorianCalendar.BC) {",
      "new": "if (calendar.get(Calendar.ERA) == GregorianCalendar.BC || date.before(((GregorianCalendar) calendar).getGregorianChange())) {",
      "why": "hop 2 also converts a date before the Gregorian change from its calendar"},
     {"file": IDF, "old": "LocalDate day = new LocalDate(date.getYear() + 1900, date.getMonth() + 1, date.getDate());",
      "new": "LocalDate day = LocalDate.fromDateFields(date);",
      "why": "hop 4 takes the day from LocalDate.fromDateFields"},
     {"file": LT, "old": "return ISODateTimeFormat.isoDateTimeOf(date);",
      "new": "return ISODateTimeFormat.isoDateTimeOf(new Date(date.getTime() - date.getTime() % 1000));",
      "why": "hop 3 passes the date rounded to its whole second"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4743 (mr_lib preview, target org/joda/time/LocalDateTime.java): "
               "format.PeriodFormatterBuilder (hop 1), tz.DateTimeZoneBuilder (hop 2), LocalTime (hop 3), "
               "format.ISODateTimeFormat (hop 4), format.DateTimeFormatterBuilder (hop 5, gold). The draw relaxed the "
               "'distinct from the target package' constraint from hop 3 on (the pool has only nine classes of 1,500 lines or "
               "more, five of them in org.joda.time). All five are public concrete top-level classes in which a static method "
               "compiles (LocalTime is final, which does not affect a static method); every preview anchor lies in the outer "
               "class, not in a nested one; none was skipped. The facade calls hop 1 by its fully-qualified name; each hop "
               "imports what it needs (java.util Date/Calendar/GregorianCalendar, LocalDate/LocalDateTime/LocalTime, the next "
               "host); LocalTime already imports Date and ISODateTimeFormat, and ISODateTimeFormat and DateTimeFormatterBuilder "
               "share a package. A behaviour-preserving pre-edit removes the facade's @SuppressWarnings(\"deprecation\") line "
               "so that the recipe can append the lie to the facade's javadoc.",
}
