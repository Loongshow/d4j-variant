"""Main run Lang-53 (C10 recipe on the fixed checkout of Defects4J Lang-53; the real bug modified DateUtils, the target class).

Facade: DateUtils.truncate(Date, int) (pre-registered batch-3 target "DateUtils.round / truncate"; the Date overload is chosen).
Its original body builds a calendar in the default time zone from the date, runs the private DateUtils.modify(cal, field,
false) and returns the calendar's time. truncate(Object, int) delegates to it for Date objects (a second production caller);
truncate(Calendar, int), round(*) and iterator(*) keep using DateUtils.modify and are untouched. round was set aside: its
group loop needs a SEMI_MONTH-only round-up step next to the shared AM_PM/SEMI_MONTH part rules, a one-of-two pattern the
checklist forbids in the gold, and every round omission that the round tests see either leaves such a pattern or is caught by
two tests. The facade keeps its argument guard (null date -> IllegalArgumentException) and delegates to a five-hop chain drawn
with the instance seed 7458 (mr_lib preview, draw order, no substitution):
  hop 1 StringUtils.dateAtField          placement: the calendar in the default time zone, set from the date; returns its time
  hop 2 builder.ToStringStyle.calendarAtField   decision: a year over 280 million is refused (ArithmeticException)
  hop 3 text.StrBuilder.clearClockUnits   decision + plumbing: a millisecond field leaves the calendar as it is; otherwise the
                                          milliseconds, and the seconds and minutes below the field, are taken off the time
                                          itself (millisecond arithmetic, as DateUtils.modify does)
  hop 4 ArrayUtils.clearByGroups          placement: the table of calendar-field groups, millisecond up to era (the same
                                          table as DateUtils.fields)
  hop 5 time.FastDateFormat.lowerBelowField   GOLD: the loop over the groups: stop at the group holding the field; for every
                                          group below it take the first field's offset from the field's minimum (with the
                                          half-month and half-day parts for SEMI_MONTH and AM_PM) and lower the field by it;
                                          throw if no group holds the field
The chain performs DateUtils.modify(cal, field, false) step for step (same year check, same millisecond early return, same
millisecond arithmetic, same table, same offsets from the actual minimum, same part rules, same zero-offset skip, same
exception), so the correct configuration is behaviour-preserving for every caller.

Fault (omission in the gold, inside its loop over the groups): the subtraction of the field's minimum is dropped from the
offset (`int offset = val.get(unit) - val.getActualMinimum(unit);` becomes `int offset = val.get(unit);`), so every field is
lowered to 0 instead of to its minimum. Fields that start at 0 (millisecond to hour, month) are still lowered correctly; the
day of the month starts at 1, so it is set to 0, which a lenient calendar reads as the last day of the previous month.
Trigger: the EXISTING test DateUtilsTest::testTruncate, whose first assertion truncate(12 Feb 2002 12:34:56.789, YEAR)
expects 1 Jan 2002 and gets 31 Jan 2002 (the day goes to 0 = 31 Jan, after which the month is already January). It is the only
test that sends a date through truncate(Date, int) or truncate(Object, int) with a field above the day: testTruncateLang59
returns early on this JVM (SystemUtils.isJavaVersionAtLeast(1.4f) is false for Java 11), and the iterator tests use
truncate(Calendar, int). The assertion fails before testTruncate changes the default time zone.

The gold's javadoc states the truncation contract (the field kept as the most significant field; each lower group lowered
through its first field) and is silent on minimums. The convention is pinned outside the gold: the facade's javadoc example
(passed with MONTH, 28 Mar 2002 truncates to 1 Mar 2002); DateUtils.modify ("Calculate the offset from the minimum allowed
value", `offset = val.get(fields[i][0]) - min` with `min = val.getActualMinimum(...)`), which still runs truncate(Calendar,
int), round(Date, int), round(Calendar, int) and, through truncate(Calendar, MONTH), iterator; testMonthIterator (month ranges
start from the first of the month), testRound (MONTH and YEAR rounding lands on the 1st), testRoundLang346 and testWeekIterator
pass on the variant.

Single owner: only the gold visits the groups and chooses the value each field is lowered to. Hops 1 to 4 see the calendar
before the loop and get nothing back from it (the gold returns void); once the day has been set to 0 the month has already
moved back, and what the truncation lands on depends on the field and the date (YEAR: 31 Jan from 12 Feb, 28 Jan from 31 Mar,
31 Jan of the previous year from 15 Jan; MONTH: the last day of the previous month; SEMI_MONTH: the 15th both from the 15th,
whose half starts on the 1st, and from the 16th to the 31st, whose half starts on the 16th), so the information needed to
restore the result is gone and no one-line adjustment above the gold restores every case (checked on a scratch build).
Declared alternatives (G9): hop 1 puts the day back to 1 for fields above the day (MONTH then lands a month early); hop 1 adds a
day when a result above the day is not on the 1st (YEAR then lands on 1 Feb); hop 4 lowers the day group through the day of the
year (the year moves back). None of them absorbs the fault.
Recorded bypasses (not declared):
 B-0 the facade or any of hops 1-4 calls the intact overload DateUtils.truncate(Calendar, int) (DateUtils.modify) and returns
     its time, discarding the rest of the chain including the gold.
 B-1 a test-fitted post-correction at hop 1, `if (field == Calendar.MONTH || field == DateUtils.SEMI_MONTH) { gval.add(
     Calendar.DATE, 1); } else if (field == Calendar.YEAR) { gval.set(Calendar.DATE, 1); }` after the call: the full suite
     passes (scratch build, 0 failing tests), but it contradicts hop 1's own contract on other dates (YEAR from 15 Jan 2002
     gives 1 Jan 2001, SEMI_MONTH from 15 Jan 2002 gives 16 Jan, ERA is untouched), so it is not a repair consistent with the
     documentation on the path.

Lie: the facade's javadoc claims the fields below the given field are set back one at a time, from the largest of them down
to the millisecond; the code takes them from the millisecond upwards. It names neither minimums nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md) on the WHOLE variant gold:
 T1 absent: val is read and set, field is compared in the group test and in both part rules and is in the message, groups
    drives both loops and gives the field that is lowered.
 T2 absent: i and j advance; unit and offset reach the set; offset is reassigned by the two part rules and tested by the
    zero-offset decision, which decides whether the set runs; no literal-initialised local; the group test stops the loop early.
 T3 absent: the two part rules (SEMI_MONTH on DATE by 15, AM_PM on HOUR_OF_DAY by 12) are both present; every member of a group
    is compared with the field and the documented first field is the one lowered; no pair or range end is handled one-sidedly;
    no minimum or maximum of any field is consulted, so none is handled in part.
 T4 absent: "in place", "groups taken from the smallest upwards", "every group below the one that holds the field is lowered
    through its first field" and "@throws IllegalArgumentException if no group holds the field" are all met by the body;
    "from the millisecond up" is a caller precondition on groups; the javadoc and the identifiers (lowerBelowField, unit,
    offset) name no start value, minimum or range.
 Correct gold checked too: the same items hold (it additionally reads each field's actual minimum, used in the offset); its
 zero-offset decision is live (it decides whether the field is set at all, and a set makes the calendar recompute its time)."""

SU = "src/java/org/apache/commons/lang/StringUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
DU = "src/java/org/apache/commons/lang/time/DateUtils.java"

GOLD_TEXT = '''/**
 * <p>Truncates a calendar in place, leaving the field specified as the
 * most significant field.</p>
 *
 * <p>The groups of fields are taken from the smallest upwards, and every
 * group below the one that holds the field is lowered through its first
 * field.</p>
 *
 * @param val  the calendar to truncate, not null
 * @param field  the field to keep as the most significant field
 * @param groups  the groups of calendar fields, from the millisecond up
 * @throws IllegalArgumentException if no group holds the field
 */
public static void lowerBelowField(Calendar val, int field, int[][] groups) {
    for (int i = 0; i < groups.length; i++) {
        for (int j = 0; j < groups[i].length; j++) {
            if (groups[i][j] == field) {
                return;
            }
        }
        final int unit = groups[i][0];
        int offset = val.get(unit) - val.getActualMinimum(unit);
        if (field == DateUtils.SEMI_MONTH && unit == Calendar.DATE && offset >= 15) {
            offset -= 15;
        }
        if (field == Calendar.AM_PM && unit == Calendar.HOUR_OF_DAY && offset >= 12) {
            offset -= 12;
        }
        if (offset != 0) {
            val.set(unit, val.get(unit) - offset);
        }
    }
    throw new IllegalArgumentException("The field " + field + " is not supported");
}'''

HOP1 = '''/**
 * <p>Truncates a date, leaving the field specified as the most
 * significant field, in a calendar of the default time zone.</p>
 *
 * @param date  the date to work with, not null
 * @param field  the field from <code>Calendar</code>
 *  or <code>SEMI_MONTH</code>
 * @return the truncated date
 */
public static Date dateAtField(Date date, int field) {
    Calendar gval = Calendar.getInstance();
    gval.setTime(date);
    ToStringStyle.calendarAtField(gval, field);
    return gval.getTime();
}'''

HOP2 = '''/**
 * <p>Truncates a calendar in place, leaving the field specified as the
 * most significant field.</p>
 *
 * @param val  the calendar to truncate, not null
 * @param field  the field from <code>Calendar</code>
 *  or <code>SEMI_MONTH</code>
 * @throws ArithmeticException if the year is over 280 million
 */
public static void calendarAtField(Calendar val, int field) {
    if (val.get(Calendar.YEAR) > 280000000) {
        throw new ArithmeticException("Calendar value too large for accurate calculations");
    }
    StrBuilder.clearClockUnits(val, field);
}'''

HOP3 = '''/**
 * <p>Truncates a calendar in place, leaving the field specified as the
 * most significant field.</p>
 *
 * <p>The milliseconds, and the seconds and minutes that lie below the
 * field, are taken off the time itself before the other fields are
 * lowered. A millisecond field leaves the calendar as it is.</p>
 *
 * @param val  the calendar to truncate, not null
 * @param field  the field from <code>Calendar</code>
 *  or <code>SEMI_MONTH</code>
 */
public static void clearClockUnits(Calendar val, int field) {
    if (field == Calendar.MILLISECOND) {
        return;
    }
    long time = val.getTimeInMillis() - val.get(Calendar.MILLISECOND);
    if (field != Calendar.SECOND) {
        time = time - val.get(Calendar.SECOND) * 1000L;
        if (field != Calendar.MINUTE) {
            time = time - val.get(Calendar.MINUTE) * 60000L;
        }
    }
    val.setTimeInMillis(time);
    ArrayUtils.clearByGroups(val, field);
}'''

HOP4 = '''/**
 * <p>Truncates a calendar in place, leaving the field specified as the
 * most significant field, with the groups of calendar fields from the
 * millisecond up to the era.</p>
 *
 * @param val  the calendar to truncate, not null
 * @param field  the field from <code>Calendar</code>
 *  or <code>SEMI_MONTH</code>
 */
public static void clearByGroups(Calendar val, int field) {
    final int[][] groups = {
        {Calendar.MILLISECOND},
        {Calendar.SECOND},
        {Calendar.MINUTE},
        {Calendar.HOUR_OF_DAY, Calendar.HOUR},
        {Calendar.DATE, Calendar.DAY_OF_MONTH, Calendar.AM_PM},
        {Calendar.MONTH, DateUtils.SEMI_MONTH},
        {Calendar.YEAR},
        {Calendar.ERA}};
    FastDateFormat.lowerBelowField(val, field, groups);
}'''

DESIGN = {
 "instance": "Lang-53", "project": "Lang", "bug_id": 53, "seed": 7458,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": DU, "class": "org.apache.commons.lang.time.DateUtils", "method": "truncate", "near_line": 543},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/time/DateUtilsTest.java",
             "test_class": "org.apache.commons.lang.time.DateUtilsTest", "test_method": "testTruncate"},
 "expected_signature": "truncate year-1 failed",
 "gold": {"method": "lowerBelowField", "text": GOLD_TEXT,
          "fault": {"old": "            int offset = val.get(unit) - val.getActualMinimum(unit);",
                    "new": "            int offset = val.get(unit);"}},
 "chain": {
   "facade_body": "if (date == null) {\n            throw new IllegalArgumentException(\"The date must not be null\");\n        }\n"
                  "        return org.apache.commons.lang.StringUtils.dateAtField(date, field);",
   "lie": "The fields below the given field are set back one at a time, from the largest of them down to the "
          "millisecond.",
   "hops": [
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "dateAtField",
      "imports": ["java.util.Calendar", "java.util.Date", "org.apache.commons.lang.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "calendarAtField",
      "imports": ["java.util.Calendar", "org.apache.commons.lang.text.StrBuilder"], "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "clearClockUnits",
      "imports": ["java.util.Calendar"], "text": HOP3},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "clearByGroups",
      "imports": ["java.util.Calendar", "org.apache.commons.lang.time.DateUtils", "org.apache.commons.lang.time.FastDateFormat"],
      "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "lowerBelowField", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.time.DateUtils::modify",
              "org.apache.commons.lang.time.DateUtils::iterator",
              "org.apache.commons.lang.time.DateUtils::round"],
 "ownership_reason": "Only the gold visits the groups of calendar fields and chooses the value each field is lowered to; hops 1-4 "
                     "build the calendar, refuse a too-large year, take the milliseconds, seconds and minutes off the time and "
                     "place the group table, and the gold returns nothing they could inspect. Without the field's minimum the "
                     "day of the month is set to 0, which a lenient calendar reads as the last day of the previous month, and "
                     "the result then depends on the field (31 Jan for YEAR from 12 Feb, the previous month's last day for "
                     "MONTH), so no one-line change above the gold restores it. The convention is pinned outside the gold: the "
                     "facade's javadoc example (MONTH truncates 28 Mar 2002 to 1 Mar 2002); DateUtils.modify ('Calculate the "
                     "offset from the minimum allowed value', offset = value - getActualMinimum), which still runs "
                     "truncate(Calendar, int), round(Date, int), round(Calendar, int) and, through truncate(Calendar, MONTH), "
                     "iterator; testMonthIterator, testWeekIterator, testRound and testRoundLang346 pass on the variant.",
 "ownership_tests": ["org.apache.commons.lang.time.DateUtilsTest::testMonthIterator",
                     "org.apache.commons.lang.time.DateUtilsTest::testWeekIterator",
                     "org.apache.commons.lang.time.DateUtilsTest::testRound",
                     "org.apache.commons.lang.time.DateUtilsTest::testRoundLang346"],
 "compensating": {
   "chain": [
     {"file": SU, "old": "        ToStringStyle.calendarAtField(gval, field);",
      "new": "        ToStringStyle.calendarAtField(gval, field); if (field == Calendar.MONTH || field == org.apache.commons.lang.time.DateUtils.SEMI_MONTH || field == Calendar.YEAR || field == Calendar.ERA) { gval.set(Calendar.DATE, 1); }",
      "why": "hop 1 puts the day of the month back to 1 for a field above the day"},
     {"file": SU, "old": "        ToStringStyle.calendarAtField(gval, field);",
      "new": "        ToStringStyle.calendarAtField(gval, field); if ((field == Calendar.MONTH || field == Calendar.YEAR) && gval.get(Calendar.DATE) != 1) { gval.add(Calendar.DATE, 1); }",
      "why": "hop 1 moves a result above the day that is not on the 1st forward by a day"},
     {"file": AU, "old": "            {Calendar.DATE, Calendar.DAY_OF_MONTH, Calendar.AM_PM},",
      "new": "            {Calendar.DAY_OF_YEAR, Calendar.DATE, Calendar.DAY_OF_MONTH, Calendar.AM_PM},",
      "why": "hop 4 lowers the day group through the day of the year"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 7458 (mr_lib preview, target org/apache/commons/lang/time/DateUtils.java): "
               "StringUtils (hop 1), builder.ToStringStyle (hop 2), text.StrBuilder (hop 3), ArrayUtils (hop 4), "
               "time.FastDateFormat (hop 5, gold; the last remaining host of the pool). All five are public classes in which a "
               "static method compiles (ToStringStyle is abstract, which does not affect a static method); none was skipped. "
               "The facade calls hop 1 by its fully-qualified name; each hop imports the next host and java.util.Calendar "
               "where it was missing (FastDateFormat already imports Calendar and shares DateUtils' package).",
}
