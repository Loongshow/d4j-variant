"""Main run Chart-8__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade; the
fixed checkout of Defects4J Chart-8, fixed revision 1085; the real bug modified org.jfree.data.time.Week, the facade's class). No static
pair (BUILD_BRIEF_C10I_B8_NOTE.md section 1); no facade reuse.

Facade: Week.previous() (instance method; allowed targets Week.next / Week.previous, BATCH8_PREREGISTRATION.md row 211; both have
facade_planned_by = null). Week.next() was not used: every behaviour of next() that the suite checks is caught by two tests at once
(the step to the following week number by testW1Y1900Next and testNext; the 9999 upper limit by testW52Y9999Next and testNext, for both
week 52 and week 53 of 9999 roll over through the same step), so no one-line omission in next() newly fails exactly one test. next()
stays intact and is one of the external pins below.
Original computation of previous(): for any week other than week 1 (FIRST_WEEK_IN_YEAR) the result is new Week(week - 1, year); for week 1
the result is the last week of the previous year (a default Calendar set to 31 December of year - 1, getActualMaximum(WEEK_OF_YEAR)),
except that for the year 1900 (the earliest supported year) the result is null.

facade_variant: V1 (state as parameters). state_passed: the private fields week (byte) and year (short), read in the facade and passed
as ints to hop 1; no field is written, no write-back. The facade body is one call to hop 1 (the original had no argument guard). No
visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The
computation calls no private method of Week, so V4 does not apply; the hops use only public API (the public Week(int, int)
constructor, Week.FIRST_WEEK_IN_YEAR and java.util.Calendar).

Redistribution of the computation: hop 1 supplies the calendar the weeks are measured with (Calendar.getInstance(), the default time zone
and locale, as the original); hop 2 measures the previous year (the number of the last week of year - 1, from that calendar set to 31
December of year - 1, as the original); hops 3 and 4 pass the week, the year and that number along; the gold decides the preceding week
(the week numbered one less in the same year, or, for the first week, the last week of the previous year, within the supported years).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Chart-8-probe of the fixture, the first statement of
both previous() and next() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j
test -t` on each of WeekTests::testW1Y1900Previous, ::testW52Y9999Previous, ::testW1Y1900Next, ::testW52Y9999Next, ::testNext: each run
reports exactly that 1 failing test, with java.lang.IllegalStateException: PROBE-REACHED (for previous() at Week.previous(Week.java:301)
from WeekTests.testW1Y1900Previous(WeekTests.java:141); for next() at Week.next(Week.java:334) from WeekTests.testNext). The facade is
reached directly by the trigger.

Hosts (host_mode = "1500"; the recipe's seeded draw `mr_lib.py preview Chart-8 org/jfree/data/time/Week.java 5`, seed 3434, used in
draw order, none substituted):
  hop 1 renderer.xy.AbstractXYItemRenderer             1786 lines  weekBefore     placement: the calendar in the default zone/locale
  hop 2 plot.CategoryPlot                              4123 lines  precedingWeek  aggregation: measures the last week of year - 1
  hop 3 renderer.category.AbstractCategoryItemRenderer 1700 lines  priorWeek      pass-through
  hop 4 plot.SpiderWebPlot                             1652 lines  weekPrior      pass-through
  hop 5 plot.PiePlot                                   3121 lines  weekPreceding  GOLD: the decision of the preceding week
Host newline counts 1786, 4123, 1700, 1652, 3121; the smallest host has 1652 lines (SpiderWebPlot); the gold host has 3121.
The correct configuration returns the original result for every week and year: the decision `week != Week.FIRST_WEEK_IN_YEAR` and the
limit `year > 1900` (the original's literal; SerialDate.MINIMUM_YEAR_SUPPORTED is 1900) are the original's; hop 2 measures the previous year for every call (the
original only for week 1), on a fresh Calendar of its own, with no other effect.

Fault (one-line omission of a boundary step in the gold): the earliest-supported-year rule is dropped from the gold's first-week return
(`return year > 1900 ? new Week(lastWeek, year - 1) : null;` becomes `return new Week(lastWeek, year - 1);`),
so the week before week 1 of 1900 is the last week of 1899. The gold then reads as the ordinary routine "one less in the same year, or the
last week of the year before". Trigger: the EXISTING test WeekTests::testW1Y1900Previous (`assertNull(this.w1Y1900.previous())`), which
fails with "junit.framework.AssertionFailedError: Expected: <null> but was: Week 52, 1899" (the variant returns the last week of 1899). It is the only test that asks for the week
before week 1 of any year; testW52Y9999Previous (week 52 -> 51) passes through the chain; no other test uses Week (gate G5 checks the
full suite).

Quietness and the contract: the gold's javadoc states the idiomatic contract (the preceding week; one less in the same year, or the last
week of the year before for the first week) and is silent on supported years. The variant violates it on the trigger input: it builds
new Week(.., 1899), outside the documented domain of the Week(int, int) constructor it calls ('@param year  the year (1900 to 9999)'),
which is the range of SerialDate (MINIMUM_YEAR_SUPPORTED = 1900); the facade's javadoc ('This method will return null for some lower
limit on the range of weeks (currently week 1, 1900)') is the specification the trigger checks. The convention is pinned outside the gold:
the intact siblings Month.previous() and Quarter.previous() (`if (this.year > 1900) ... else result = null`), Year.previous()
(`this.year > SerialDate.MINIMUM_YEAR_SUPPORTED`, else null) and Week.next() (the mirror limit `this.year < 9999`, else null); passing
tests MonthTests::testJan1900Previous, QuarterTests::testQ1Y1900Previous, YearTests::test1900Previous, and WeekTests::testW52Y9999Previous
(through the chain).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: week decides the branch and gives week - 1; year gives the result's year and is tested against the earliest year; lastWeek
     is the week number of the first-week result.
  T2 absent: no locals; the if and the ternary each have two different effects.
  T3 absent: the gold has one boundary rule (the first week of the earliest year); the preceding week has no rule at the upper end of
     the years or the weeks, and any week other than the first (the last included) is handled by the same 'one less' line, as the
     javadoc says; no class named in the gold's text is handled in part.
  T4 absent: 'the week numbered one less in the same year' and 'the last week of the year before' are met by the two returns; the
     @param/@return clauses are general.
 Variant gold (javadoc, signature, `if (week != Week.FIRST_WEEK_IN_YEAR) { return new Week(week - 1, year); }`,
 `return new Week(lastWeek, year - 1);`):
  T1 absent: week decides the branch and gives week - 1; year gives both results' year; lastWeek is the first-week result's number.
  T2 absent: no locals; the if has two different effects (week - 1 in year vs lastWeek in year - 1).
  T3 absent: the gold has no year-range treatment at all (no lower and no upper year limit: 'No member handled'); of the weeks it treats
     the first week specially, and every other week, the last included, by the single 'one less' rule its javadoc states ('any week
     other than the first week of a year'); the preceding week needs no last-week rule, so the first/last pair is not a pair with the
     same role here; no class named in the gold's text is handled in part.
  T4 absent: 'the week numbered one less in the same year' is met by `new Week(week - 1, year)`; 'the first week of a year is preceded
     by the last week of the year before' is met by `new Week(lastWeek, year - 1)`; '@param lastWeek  the number of the last week of the
     year before' is met; '@return The preceding week.' is general; no inline comment; identifiers (week, year, lastWeek, weekPreceding)
     name nothing the body does not meet. The gold names no supported range, no null result and no limit.

Single owner: only the gold decides which week precedes the given one; hop 1 only supplies the calendar, hop 2 only measures the number of
the last week of the previous year (for every week, the first week of 1900 included), and hops 3 and 4 pass the week, the year and that
number along and return the gold's week as it is. Once the gold has built the last week of 1899, the null result can appear only if a
caller answers the first week of 1900 itself instead of the gold or replaces the gold's week. Declared alternatives (G9): hop 1 measures
the weeks with a UK calendar; hop 2 measures the previous year at 28 December; hop 3 hands the gold the week number raised to at least the
first week. None makes the trigger pass.
Recorded bypasses (not part of the recipe; each discards or replaces the gold's decision for the trigger input):
 B-0 the facade's original body, which computes the preceding week itself without the chain.
 B-1 a hop (1-4) answers the first week of the earliest year with null before calling on (a second implementation of the gold's
     year decision for that input; it contradicts the pass-through hops' documentation, which returns the next step's week).
 B-2 a hop (1-4) maps a returned week of a year before 1900 to null (it replaces the week the gold built).

Lie: the facade's javadoc claims the preceding week is found by stepping back seven days from the first millisecond of this week and
taking the week in which that instant falls; no step of the chain works with milliseconds or instants (the week number and the year are
used directly, and only the last week number of the previous year is measured). It names neither the year limit nor any hop."""

WEEK = "source/org/jfree/data/time/Week.java"
AXIR = "source/org/jfree/chart/renderer/xy/AbstractXYItemRenderer.java"
CP = "source/org/jfree/chart/plot/CategoryPlot.java"
ACIR = "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java"
SWP = "source/org/jfree/chart/plot/SpiderWebPlot.java"
PP = "source/org/jfree/chart/plot/PiePlot.java"

GOLD_TEXT = '''/**
 * Returns the week that precedes the specified week.  Any week other than
 * the first week of a year is preceded by the week numbered one less in the
 * same year, and the first week of a year is preceded by the last week of
 * the year before.
 *
 * @param week  the week number.
 * @param year  the year.
 * @param lastWeek  the number of the last week of the year before
 *     <code>year</code>.
 *
 * @return The preceding week.
 */
public static Week weekPreceding(int week, int year, int lastWeek) {
    if (week != Week.FIRST_WEEK_IN_YEAR) {
        return new Week(week - 1, year);
    }
    return year > 1900 ? new Week(lastWeek, year - 1) : null;
}'''

HOP1 = '''/**
 * Returns the week that precedes the specified week, with the weeks
 * measured by a calendar in the default time zone and locale.
 *
 * @param week  the week number.
 * @param year  the year.
 *
 * @return The preceding week.
 */
public static Week weekBefore(int week, int year) {
    return CategoryPlot.precedingWeek(week, year, Calendar.getInstance());
}'''

HOP2 = '''/**
 * Returns the week that precedes the specified week.  The supplied calendar
 * is set to 31 December of the year before <code>year</code>, and its
 * maximum week of the year is taken as the number of the last week of that
 * year.
 *
 * @param week  the week number.
 * @param year  the year.
 * @param calendar  the calendar that measures the weeks (<code>null</code>
 *     not permitted).
 *
 * @return The preceding week.
 */
public static Week precedingWeek(int week, int year, Calendar calendar) {
    calendar.set(year - 1, Calendar.DECEMBER, 31);
    int lastWeek = calendar.getActualMaximum(Calendar.WEEK_OF_YEAR);
    return AbstractCategoryItemRenderer.priorWeek(week, year, lastWeek);
}'''

HOP3 = '''/**
 * Returns the week that precedes the specified week.
 *
 * @param week  the week number.
 * @param year  the year.
 * @param lastWeek  the number of the last week of the year before
 *     <code>year</code>.
 *
 * @return The preceding week.
 */
public static Week priorWeek(int week, int year, int lastWeek) {
    return SpiderWebPlot.weekPrior(week, year, lastWeek);
}'''

HOP4 = '''/**
 * Returns the week that precedes the specified week.
 *
 * @param week  the week number.
 * @param year  the year.
 * @param lastWeek  the number of the last week of the year before
 *     <code>year</code>.
 *
 * @return The preceding week.
 */
public static Week weekPrior(int week, int year, int lastWeek) {
    return PiePlot.weekPreceding(week, year, lastWeek);
}'''

DESIGN = {
 "instance": "Chart-8", "project": "Chart", "bug_id": 8, "seed": 3434,
 "src_root": "source", "test_root": "tests",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "private fields week (byte) and year (short), read in the facade and passed as ints to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [1786, 4123, 1700, 1652, 3121],
 "reachability_probe": "previous() and next() first statements made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Chart-8-probe: WeekTests::testW1Y1900Previous and ::testW52Y9999Previous fail with "
                       "PROBE-REACHED at Week.previous(Week.java:301); ::testW1Y1900Next, ::testW52Y9999Next and ::testNext fail "
                       "with PROBE-REACHED at Week.next(Week.java:334)",
 "facade": {"file": WEEK, "class": "org.jfree.data.time.Week", "method": "previous", "near_line": 300},
 "trigger": {"existing": True, "test_file": "tests/org/jfree/data/time/junit/WeekTests.java",
             "test_class": "org.jfree.data.time.junit.WeekTests", "test_method": "testW1Y1900Previous"},
 "expected_signature": "Expected: <null> but was: Week 52, 1899",
 "gold": {"method": "weekPreceding", "text": GOLD_TEXT,
          "fault": {"old": "        return year > 1900 ? new Week(lastWeek, year - 1) : null;",
                    "new": "        return new Week(lastWeek, year - 1);"}},
 "chain": {
   "facade_body": "return org.jfree.chart.renderer.xy.AbstractXYItemRenderer.weekBefore(this.week, this.year);",
   "lie": "The preceding week is found by stepping back seven days from the first millisecond of this week and taking the week in "
          "which that instant falls.",
   "hops": [
     {"file": AXIR, "class": "org.jfree.chart.renderer.xy.AbstractXYItemRenderer", "method": "weekBefore",
      "imports": ["java.util.Calendar", "org.jfree.chart.plot.CategoryPlot", "org.jfree.data.time.Week"], "text": HOP1},
     {"file": CP, "class": "org.jfree.chart.plot.CategoryPlot", "method": "precedingWeek",
      "imports": ["java.util.Calendar", "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer",
                  "org.jfree.data.time.Week"], "text": HOP2},
     {"file": ACIR, "class": "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer", "method": "priorWeek",
      "imports": ["org.jfree.chart.plot.SpiderWebPlot", "org.jfree.data.time.Week"], "text": HOP3},
     {"file": SWP, "class": "org.jfree.chart.plot.SpiderWebPlot", "method": "weekPrior",
      "imports": ["org.jfree.data.time.Week"], "text": HOP4},
     {"file": PP, "class": "org.jfree.chart.plot.PiePlot", "method": "weekPreceding",
      "imports": ["org.jfree.data.time.Week"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.data.time.Month::previous",
              "org.jfree.data.time.Quarter::previous",
              "org.jfree.data.time.Year::previous",
              "org.jfree.data.time.Week::next"],
 "ownership_reason": "Only the gold decides which week precedes the given week: the week numbered one less in the same year, or, for "
                     "the first week, the last week of the year before. Hop 1 only supplies the calendar the weeks are measured "
                     "with, hop 2 only measures the number of the last week of the previous year (for every week, the first week of "
                     "1900 included), and hops 3 and 4 pass the week, the year and that number along and return the week they are "
                     "given. Once the gold has built the last week of 1899 for the first week of 1900, the null result can appear "
                     "only if a caller answers that input itself instead of the gold or replaces the gold's week. The variant builds "
                     "new Week(.., 1899), outside the documented domain of the Week(int, int) constructor ('the year (1900 to "
                     "9999)', the range of SerialDate.MINIMUM_YEAR_SUPPORTED to MAXIMUM_YEAR_SUPPORTED); the facade's javadoc "
                     "states that the week before week 1 of 1900 is null. The convention is pinned outside the gold: the intact "
                     "siblings Month.previous() and Quarter.previous() return null for the first period of 1900, Year.previous() "
                     "returns null at SerialDate.MINIMUM_YEAR_SUPPORTED, and Week.next() applies the mirror limit (null after the "
                     "last week of 9999); MonthTests::testJan1900Previous, QuarterTests::testQ1Y1900Previous and "
                     "YearTests::test1900Previous pass, and WeekTests::testW52Y9999Previous passes through the chain.",
 "ownership_tests": ["org.jfree.data.time.junit.MonthTests::testJan1900Previous",
                     "org.jfree.data.time.junit.QuarterTests::testQ1Y1900Previous",
                     "org.jfree.data.time.junit.YearTests::test1900Previous",
                     "org.jfree.data.time.junit.WeekTests::testW52Y9999Previous"],
 "compensating": {
   "chain": [
     {"file": AXIR, "old": "return CategoryPlot.precedingWeek(week, year, Calendar.getInstance());",
      "new": "return CategoryPlot.precedingWeek(week, year, Calendar.getInstance(java.util.Locale.UK));",
      "why": "hop 1 measures the weeks with a UK calendar"},
     {"file": CP, "old": "calendar.set(year - 1, Calendar.DECEMBER, 31);",
      "new": "calendar.set(year - 1, Calendar.DECEMBER, 28);",
      "why": "hop 2 measures the previous year at 28 December"},
     {"file": ACIR, "old": "return SpiderWebPlot.weekPrior(week, year, lastWeek);",
      "new": "return SpiderWebPlot.weekPrior(Math.max(week, Week.FIRST_WEEK_IN_YEAR), year, lastWeek);",
      "why": "hop 3 hands on the week number raised to at least the first week"},
   ],
 },
 "host_notes": "host_mode 1500 (batch8_tasks.json; Week.java, the only allowed candidates' file, excluded by the draw): the recipe's "
               "seeded draw `mr_lib.py preview Chart-8 org/jfree/data/time/Week.java 5` (seed 3434), in draw order, none "
               "substituted: renderer.xy.AbstractXYItemRenderer (hop 1, 1786 lines, anchor after setBaseURLGenerator, seed 3534), "
               "plot.CategoryPlot (hop 2, 4123, after configureDomainAxes, 3535), renderer.category.AbstractCategoryItemRenderer "
               "(hop 3, 1700, after getBaseURLGenerator, 3536), plot.SpiderWebPlot (hop 4, 1652, after setBaseSeriesOutlineStroke, "
               "3537), plot.PiePlot (hop 5, gold, 3121, after setLegendItemShape, 3538). Smallest host: SpiderWebPlot, 1652 lines. "
               "All five are public top-level classes (two abstract) in which a public static method compiles. The facade calls hop "
               "1 by its fully-qualified name; each hop imports the next host, org.jfree.data.time.Week and, where used, "
               "java.util.Calendar. The gold imports only org.jfree.data.time.Week (its earliest-year limit is the original's literal 1900), "
               "so every import the variant adds is used by the variant's code.",
}
