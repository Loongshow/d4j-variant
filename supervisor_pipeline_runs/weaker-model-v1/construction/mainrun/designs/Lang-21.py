"""Main run Lang-21 (C10 recipe on the fixed checkout of Defects4J Lang-21; the real bug modified DateUtils, the target class).

Facade: DateUtils.ceiling(Date, int) (allowed target ceiling, BATCH4_PREREGISTRATION row Lang-21). The other allowed targets were
set aside:
 - round: round(Date, int) and round(Object, int) are called by DateUtilsTest (testRound, testRoundLang346, testTruncateLang59)
   and by every per-field test of DateUtilsRoundingTest (baseRoundTest / roundToJanuaryFirst round Dates and Dates cast to
   Object), so an omission in a rounding core reached through the Date overload fails several tests and gate G5 (exactly one new
   failure) cannot hold.
 - iterator: iterator(Date, int) is reached only by testMonthIterator (month styles) and by testWeekIterator (RANGE_WEEK_CENTER
   through iterator(Object)). The month-range decisions that a one-line omission can remove are either never exercised by those
   inputs (a month starting before the week's first day, a month ending on the week's last day: neither occurs for February 2002
   or November 2001) or turn the day-of-week walks into loops that never end (an omitted wrap of a cutoff into
   SUNDAY..SATURDAY), and a Monday/Sunday decision would sit beside the style constants it tests (checklist T3/T4).
ceiling(Date, int) and ceiling(Object, int) on a Date are called by DateUtilsTest::testCeil only; no production code calls any
ceiling overload. ceiling(Calendar, int), truncate and round keep using the private DateUtils.modify, which stays intact.
Original computation of the facade: null date -> IllegalArgumentException; copy the date into Calendar.getInstance(); modify:
a year over 280 million -> ArithmeticException, a MILLISECOND field leaves the calendar as it is, otherwise every level of the
field table below the field's level is set back to its minimum and the field's level is then moved one unit up, with the
half-month rule for SEMI_MONTH (days 1-15 -> the 16th, days 16-31 -> the 1st of the next month) and the half-day rule for AM_PM;
a field in no row -> IllegalArgumentException; the Calendar's time is returned.

Chain (hosts in draw order for seed 6086, mr_lib preview, target org/apache/commons/lang3/time/DateUtils.java, none skipped):
  hop 1 StringUtils.nextUnitStart              placement: the date copied into a default Calendar, the moved Calendar's time returned
  hop 2 builder.ToStringStyle.moveToNextUnit   decision: the year limit (ArithmeticException) and the MILLISECOND no-op
  hop 3 ArrayUtils.nextUnitByLevels            placement: the table of levels from the millisecond to the era
  hop 4 text.StrBuilder.advanceUnit            pass-through
  hop 5 time.FastDateFormat.stepUp             GOLD: the walk over the levels (set each finer level to its minimum, move the
                                               field's level one unit up), with the half-month step for SEMI_MONTH
The level table puts AM_PM on a level of its own between HOUR (12-hour clock) and DATE, so the half day is an ordinary level:
setting HOUR to 0 reaches the start of the half day and Calendar.add(AM_PM, 1) moves twelve hours of wall-clock time. SEMI_MONTH
has no Calendar field; it sits with DATE and DAY_OF_MONTH on the day level, where the gold moves it to the 16th or to the first
of the next month. On every test input the correct configuration returns the original result (G1). It is not byte-for-byte
the original algorithm on two untested corners, both on daylight-saving days: an AM_PM ceiling moves twelve hours of wall-clock
time (the original adds twelve elapsed hours from midnight, e.g. 13:00 on a spring-forward day), and the original's LANG-59
millisecond-arithmetic truncation of the sub-hour fields (applied for ceiling only below 500 ms / 30 s / 30 min) is not
reproduced, so a ceiling inside a repeated fall-back hour may resolve to the other occurrence of that hour.

Fault (omission of a special-case decision in the gold): the SEMI_MONTH block inside the match is dropped, so SEMI_MONTH is moved
like the other fields of its row: one day up. The gold then reads as the plain table walk: set every finer level to its
minimum, add one to the level that holds the field. Trigger: the EXISTING test DateUtilsTest::testCeil; its first assertions
(HOUR, MONTH, YEAR) pass and 'ceiling semimonth-1 failed' (ceiling(February 12, 2002 12:34:56.789, SEMI_MONTH)) fails: expected
Sat Feb 16 00:00:00 2002, got Wed Feb 13 00:00:00 2002. No other test reaches the chain. The gold's javadoc states the idiomatic
contract (moves the calendar forward to the start of the next unit of the field) and is silent on half months; the next unit
of SEMI_MONTH is half a month (DateUtils.SEMI_MONTH: 'This is half a month'), so February 13 violates that contract.

External pins (the half-month convention outside the gold): DateUtils.modify (private) takes the same step for truncate, round
and ceiling(Calendar) ('offset = date - 1, minus 15 from the 16th on', 'If the date is 1, we round up to 16, otherwise we
subtract 15 days and add 1 month'); the facade's own @param (the field from Calendar or SEMI_MONTH) and the SEMI_MONTH constant's
javadoc; passing tests DateUtilsRoundingTest::testTruncateSemiMonth and ::testRoundSemiMonth (the 1st/16th boundaries for every
half of the month) and DateUtilsTest::testTruncate and ::testRound (SEMI_MONTH asserts for the Date, Object and Calendar
overloads).

Single owner: only the gold interprets the field: it finds the level that holds it, sets the finer levels and moves that level
up; hops 1-4 copy the date, check the year, supply the table and pass everything on, and each hop's javadoc says it hands the
calendar and the field on unchanged. Once the gold has set the day to 13 the half-month result is gone for every caller. The
level table cannot repair it in one line: on the day level SEMI_MONTH moves one day, on the month level one month (as in
DateUtils.fields), in no row an IllegalArgumentException. Declared alternatives (G9): hop 3 moves SEMI_MONTH to the month row
(as DateUtils.fields does; Feb 12 -> Mar 1), hop 2 hands MONTH on in place of SEMI_MONTH (Mar 1), hop 1 starts from the date
truncated to its half month (Feb 1 -> Feb 2); the trigger still fails for each.
Recorded edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy, defects4j
test: 0 failing tests each; not repairs of the chain):
 B-0 bypass: the facade (its original body) or any of hops 1-4 uses the intact overload DateUtils.ceiling(Calendar, int), e.g.
     hop 2 `val.setTime(org.apache.commons.lang3.time.DateUtils.ceiling(val, field).getTime());`, discarding the rest of the
     chain including the gold.
 B-1 second implementation of the gold's half-month decision at a hop: e.g. hop 3 or hop 4 adds
     `if (field == DateUtils.SEMI_MONTH) { if (val.get(Calendar.DATE) > 15) { field = Calendar.MONTH; } else { val.set(Calendar.DATE, 15); } }`
     before handing on. It re-implements the decision the gold owns (which half of the month the day is in) in a hop whose
     javadoc says the calendar and the field are handed on unchanged, so it contradicts that hop's documentation; the gold's
     own result for SEMI_MONTH is never produced by the gold.

Lie: the facade's javadoc claims the date is turned into a count of milliseconds from the epoch, divided by the length of one
unit of the field, rounded up and multiplied back; the chain uses Calendar fields only, never a unit length or a division. It
names neither half months nor any level, step or hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: val is moved (set/add side effects), field decides the match and the SEMI_MONTH block, levels drives both loops.
  T2 absent: unit is read by set and add; i and j advance in their for headers; no literal-initialised local; the SEMI_MONTH if
     and its inner if/else have different effects; the match if returns.
  T3 absent: both halves of the month are handled (day > 15 -> 1st of next month, else the 16th); every member of a row is
     compared; no other set.
  T4 absent: the javadoc names only the start of the next unit of a field, caller preconditions (not null, the order of the
     levels) and an IllegalArgumentException when no row holds the field, which the final throw meets.
 Variant gold (javadoc, signature, the two loops, `val.add(unit, 1)`, `val.set(unit, val.getActualMinimum(unit))`, the throw):
  T1 absent: val is moved by add and set, field is compared with every row member (and quoted in the exception), levels gives
     the bounds, the units and the members; each changes the effect.
  T2 absent: the only local, unit, is read by add and by set; i and j are advanced by their for headers; no flag, counter,
     cursor or best-so-far; the single if returns after moving the level, else the level is set to its minimum.
  T3 absent: no case, special value or pair is handled at all (no member handled); every member of each row is compared; the
     first member of a row is the documented level field ('each row holding the field set at one level and the fields handled
     at it'), not a sibling left out; the gold names no class it handles in part.
  T4 absent: 'the start of the next unit of a field' is a general description that the two loops address; 'not null' and 'from
     the finest to the coarsest' are caller preconditions; '@throws IllegalArgumentException if no row holds the field' is met
     by the throw after the loops; no inline comment; identifiers (unit, levels) name nothing the body does not meet."""

SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"

GOLD_TEXT = '''/**
 * <p>Moves a calendar forward to the start of the next unit of a field.</p>
 *
 * @param val  the calendar to move, not null
 * @param field  the field to move to the next unit of
 * @param levels  the calendar fields from the finest to the coarsest, each
 *  row holding the field set at one level and the fields handled at it
 * @throws IllegalArgumentException if no row holds the field
 */
public static void stepUp(Calendar val, int field, int[][] levels) {
    for (int i = 0; i < levels.length; i++) {
        final int unit = levels[i][0];
        for (int j = 0; j < levels[i].length; j++) {
            if (levels[i][j] == field) {
                if (field == DateUtils.SEMI_MONTH) {
                    if (val.get(Calendar.DATE) > 15) {
                        val.set(Calendar.DATE, 1);
                        val.add(Calendar.MONTH, 1);
                    } else {
                        val.set(Calendar.DATE, 16);
                    }
                    return;
                }
                val.add(unit, 1);
                return;
            }
        }
        val.set(unit, val.getActualMinimum(unit));
    }
    throw new IllegalArgumentException("The field " + field + " is not supported");
}'''

HOP1 = '''/**
 * <p>Returns the start of the next unit of a field after a date, as a
 * new Date.</p>
 *
 * <p>The date is copied into a Calendar of the default time zone and
 * locale, the Calendar is moved with the same field, and the time of the
 * moved Calendar is returned. The date itself is not changed.</p>
 *
 * @param date  the date to work with, not null
 * @param field  the field from <code>Calendar</code> or <code>SEMI_MONTH</code>
 * @return the start of the next unit, a new Date
 */
public static Date nextUnitStart(Date date, int field) {
    Calendar gval = Calendar.getInstance();
    gval.setTime(date);
    ToStringStyle.moveToNextUnit(gval, field);
    return gval.getTime();
}'''

HOP2 = '''/**
 * <p>Moves a calendar forward to the start of the next unit of a field.</p>
 *
 * <p>A calendar in a year over 280 million is refused. The millisecond is
 * the finest field, so a <code>MILLISECOND</code> field leaves the
 * calendar as it is; for any other field the calendar and the field are
 * handed on unchanged.</p>
 *
 * @param val  the calendar to move, not null
 * @param field  the field to move to the next unit of
 * @throws ArithmeticException if the year is over 280 million
 */
public static void moveToNextUnit(Calendar val, int field) {
    if (val.get(Calendar.YEAR) > 280000000) {
        throw new ArithmeticException("Calendar value too large for accurate calculations");
    }
    if (field != Calendar.MILLISECOND) {
        ArrayUtils.nextUnitByLevels(val, field);
    }
}'''

HOP3 = '''/**
 * <p>Moves a calendar forward to the start of the next unit of a field,
 * using the levels of the calendar fields.</p>
 *
 * <p>The levels run from the millisecond up to the era. Each row holds the
 * field that is set at one level, followed by the other fields handled at
 * that level. The calendar and the field are handed on unchanged with
 * these levels.</p>
 *
 * @param val  the calendar to move, not null
 * @param field  the field to move to the next unit of
 */
public static void nextUnitByLevels(Calendar val, int field) {
    StrBuilder.advanceUnit(val, field, new int[][] {
        {Calendar.MILLISECOND},
        {Calendar.SECOND},
        {Calendar.MINUTE},
        {Calendar.HOUR, Calendar.HOUR_OF_DAY},
        {Calendar.AM_PM},
        {Calendar.DATE, Calendar.DAY_OF_MONTH, DateUtils.SEMI_MONTH},
        {Calendar.MONTH},
        {Calendar.YEAR},
        {Calendar.ERA}});
}'''

HOP4 = '''/**
 * <p>Moves a calendar forward to the start of the next unit of a field,
 * given the levels of the calendar fields.</p>
 *
 * <p>The calendar, the field and the levels are handed on unchanged.</p>
 *
 * @param val  the calendar to move, not null
 * @param field  the field to move to the next unit of
 * @param levels  the calendar fields from the finest to the coarsest
 */
public static void advanceUnit(Calendar val, int field, int[][] levels) {
    FastDateFormat.stepUp(val, field, levels);
}'''

DESIGN = {
 "instance": "Lang-21", "project": "Lang", "bug_id": 21, "seed": 6086,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "ceiling", "near_line": 862},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/time/DateUtilsTest.java",
             "test_class": "org.apache.commons.lang3.time.DateUtilsTest", "test_method": "testCeil"},
 "expected_signature": "ceiling semimonth-1 failed",
 "gold": {"method": "stepUp", "text": GOLD_TEXT,
          "fault": {"old": "                    if (field == DateUtils.SEMI_MONTH) {\n"
                           "                        if (val.get(Calendar.DATE) > 15) {\n"
                           "                            val.set(Calendar.DATE, 1);\n"
                           "                            val.add(Calendar.MONTH, 1);\n"
                           "                        } else {\n"
                           "                            val.set(Calendar.DATE, 16);\n"
                           "                        }\n"
                           "                        return;\n"
                           "                    }\n"
                           "                    val.add(unit, 1);",
                    "new": "                    val.add(unit, 1);"}},
 "chain": {
   "facade_body": "if (date == null) {\n            throw new IllegalArgumentException(\"The date must not be null\");\n        }\n"
                  "        return org.apache.commons.lang3.StringUtils.nextUnitStart(date, field);",
   "lie": "The date is first turned into a count of milliseconds from the epoch, which is divided by the length of one "
          "unit of the field, rounded up to a whole number of units and multiplied back to give the new date.",
   "hops": [
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "nextUnitStart",
      "imports": ["java.util.Calendar", "java.util.Date", "org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "moveToNextUnit",
      "imports": ["java.util.Calendar", "org.apache.commons.lang3.ArrayUtils"], "text": HOP2},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "nextUnitByLevels",
      "imports": ["java.util.Calendar", "org.apache.commons.lang3.text.StrBuilder", "org.apache.commons.lang3.time.DateUtils"],
      "text": HOP3},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "advanceUnit",
      "imports": ["java.util.Calendar", "org.apache.commons.lang3.time.FastDateFormat"], "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "stepUp", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.time.DateUtils::modify",
              "org.apache.commons.lang3.time.DateUtils::ceiling",
              "org.apache.commons.lang3.time.DateUtils::truncate",
              "org.apache.commons.lang3.time.DateUtils::round"],
 "ownership_reason": "Only the gold interprets the field: it finds the level that holds it, sets every finer level to its minimum "
                     "and moves that level one unit up. Hops 1-4 copy the date into a Calendar, refuse a year over 280 million, "
                     "supply the table of levels and pass everything on, and their javadocs say the calendar and the field are "
                     "handed on unchanged. The next unit of SEMI_MONTH is half a month (the SEMI_MONTH constant: 'This is half a "
                     "month'; the facade: 'the field from Calendar or SEMI_MONTH'): days 1-15 move to the 16th, days 16-31 to "
                     "the first of the next month. DateUtils.modify takes exactly that step for truncate, round and the Calendar "
                     "overload of ceiling, and DateUtilsRoundingTest testTruncateSemiMonth / testRoundSemiMonth and DateUtilsTest "
                     "testTruncate / testRound pin it and pass. Once the gold has moved the day one unit the half-month result is "
                     "lost to every caller, and no one-line change of the table helps: SEMI_MONTH on the day level moves one day, "
                     "on the month level (as in DateUtils.fields) one month, in no row it is refused.",
 "ownership_tests": ["org.apache.commons.lang3.time.DateUtilsRoundingTest::testTruncateSemiMonth",
                     "org.apache.commons.lang3.time.DateUtilsRoundingTest::testRoundSemiMonth",
                     "org.apache.commons.lang3.time.DateUtilsTest::testTruncate",
                     "org.apache.commons.lang3.time.DateUtilsTest::testRound"],
 "compensating": {
   "chain": [
     {"file": AU, "old": "{Calendar.DATE, Calendar.DAY_OF_MONTH, DateUtils.SEMI_MONTH},\n            {Calendar.MONTH},",
      "new": "{Calendar.DATE, Calendar.DAY_OF_MONTH},\n            {Calendar.MONTH, DateUtils.SEMI_MONTH},",
      "why": "hop 3 puts SEMI_MONTH on the month level, as DateUtils.fields does"},
     {"file": TSS, "old": "ArrayUtils.nextUnitByLevels(val, field);",
      "new": "ArrayUtils.nextUnitByLevels(val, field == org.apache.commons.lang3.time.DateUtils.SEMI_MONTH ? Calendar.MONTH : field);",
      "why": "hop 2 hands MONTH on in place of SEMI_MONTH"},
     {"file": SU, "old": "gval.setTime(date);\n        ToStringStyle.moveToNextUnit(gval, field);",
      "new": "gval.setTime(field == org.apache.commons.lang3.time.DateUtils.SEMI_MONTH ? org.apache.commons.lang3.time.DateUtils.truncate(date, field) : date);\n        ToStringStyle.moveToNextUnit(gval, field);",
      "why": "hop 1 starts a SEMI_MONTH request from the date truncated to its half month"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 6086 (mr_lib preview, target org/apache/commons/lang3/time/DateUtils.java): "
               "StringUtils (hop 1), builder.ToStringStyle (hop 2), ArrayUtils (hop 3), text.StrBuilder (hop 4), "
               "time.FastDateFormat (hop 5, gold; drawn as the last remaining host of the five-class pool). All five are public "
               "top-level classes in which a static method compiles (ToStringStyle is abstract, which does not affect a static "
               "method); every preview anchor lies in the outer class, not in a nested one; none was skipped. The facade calls "
               "hop 1 by its fully-qualified name; each hop imports java.util.Calendar (FastDateFormat already does) and the "
               "next host; hop 3 imports DateUtils for SEMI_MONTH, and the gold shares the time package with DateUtils.",
}
