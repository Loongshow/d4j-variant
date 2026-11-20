"""Main run Time-12__i (cell C10i, batch 7, the paired static/instance bridge: the C10 recipe with an INSTANCE-method facade, on the
fixed checkout of Defects4J Time-12; the real bug modified LocalDate and LocalDateTime, and the facade's class LocalDate is one of them).

Facade: LocalDate.toDate() (an allowed instance target of bridge7_tasks.json / BATCH7_PREREGISTRATION.md row 206; the paired static
facade LocalDateTime.fromDateFields is not used; no facade reuse). The other two allowed targets were weighed: LocalDateTime.toDate is
the sibling conversion and is kept intact as the external pin of the convention used here; LocalDate.toDateTime(LocalTime, DateTimeZone)
is reached by many tests in several files, so no step of it is caught by one test alone.
facade_variant: V2 (receiver as parameter). state_passed: `this` (the LocalDate receiver) is handed to hop 1, typed as LocalDate; hops
1-3 call only its public getters getYear, getMonthOfYear and getDayOfMonth; no field is read and there is no write-back (the original
body writes no field). The facade body becomes the single call `return org.joda.time.format.PeriodFormatterBuilder.toJavaDate(this);`
(the original has no guard).
Original computation of the facade: the JDK's own midnight for the date's year, month and day (new Date(year - 1900, month - 1, dom))
as a first guess, then adjusted to the earliest instant of the date in the JDK default zone (forward by hours and back by seconds when
the JDK put the guess on the previous day; back by the zone's DST saving when the earlier instant is still on the date).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Time-12-probe/w of the fixture, the
first statement of LocalDate.toDate was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. Full suite (`defects4j
test`, 7 s): 5 failing tests, all with java.lang.IllegalStateException: PROBE-REACHED at LocalDate.toDate(LocalDate.java:995), called
from TestLocalDate_Basics.testToDate_summer, testToDate_winter, testToDate_springDST, testToDate_springDST_2Hour40Savings and
testToDate_autumnDST. The facade is reached by existing tests directly, and by no other test. Scratch copy deleted.

Hosts (host_mode = "1500"; hosts_hop_order of the task record, used in that order, none substituted):
  hop 1 format.PeriodFormatterBuilder   1872 lines  toJavaDate    state gathering: the year in the JDK's form (year - 1900)
  hop 2 tz.DateTimeZoneBuilder          1728 lines  javaDateOf    state gathering: the month in the JDK's form (month - 1)
  hop 3 LocalTime                       1623 lines  javaDateFor   state gathering: the day of month; the receiver is not passed on
  hop 4 format.ISODateTimeFormat        1711 lines  javaDateAt    pass-through of the three JDK fields
  hop 5 format.DateTimeFormatterBuilder 2828 lines  javaDayStart  GOLD: the search for the start of the day in the JDK default zone
Host newline counts 1872, 1728, 1623, 1711, 2828; the smallest host has 1623 lines (LocalTime). The facade's class LocalDate is not a
host.

The gold (correct form) fixes the day as the JDK date of the JDK's noon for the fields (new Date(year, month, dom, 12, 0, 0); noon
exists on every day), sets the instant 24 hours before that noon, steps forward one hour at a time until the instant is on the day,
then steps back one second at a time while the instant a second earlier is still on the day, and returns the instant reached: the
first second of the day in the JDK default zone. Every equality test is between two ISO LocalDates (both from fromDateFields), so the
search ends on every input (the noon itself is on the day and lies on the hour grid it walks).
Checked against the original toDate by a differential run in a scratch copy (TZ=America/Los_Angeles, Joda default Europe/London):
every day of 1900-2049 in the ISO, Coptic, Buddhist, GJ, Ethiopic, Islamic and Julian chronologies under 25 JDK zones
(America/Los_Angeles, America/Sao_Paulo, America/Havana, Asia/Tehran, Asia/Beirut, Africa/Cairo, America/Santiago, Pacific/Apia,
Europe/London, UTC, Asia/Amman, America/Asuncion, Asia/Gaza, Australia/Lord_Howe, America/St_Johns, Asia/Kolkata, Pacific/Chatham,
America/Godthab, Antarctica/Troll, Europe/Moscow, America/Caracas, Asia/Dhaka, Africa/Casablanca, Europe/Lisbon, Pacific/Kiritimati)
and five SimpleTimeZones (the tests' two "NoMidnight" zones, an overlap at midnight, a gap at 23:30, a 30-minute saving); the harness's
copy of the original body was checked equal to LocalDate.toDate on every ISO input. Where the original finishes, the chain gives the
original Date, or an earlier instant on the same JDK day (never a later one): on days when midnight occurs twice and the original
keeps the second midnight, namely ISO dates where the zone's current DST saving no longer matches the historical change (for example
Asia/Amman in September 1995-2006, Asia/Tehran 1978-08-05, America/St_Johns 1988-10-30) and non-ISO dates (the original applies its
overlap step only when the JDK date equals the receiver, which a non-ISO receiver never does). There the chain's result is the
facade's documented "earliest valid time for that date". Non-ISO dates on a day without midnight make the original's forward walk run
for ever (it waits for an ISO date to equal a non-ISO receiver); the chain returns the first instant of the day. On the five tests that
reach the facade the chain and the original give identical Dates.

Fault (one-step omission in the gold): the loop that steps back one second at a time (its header, its one statement and its closing
brace) is dropped. The gold then reads as the ordinary routine "from 24 hours before noon of the day, step forward an hour at a time
until on the day", which is exact whenever the day starts on that hour grid, as it does on ordinary days, on the 1-hour gap at
midnight and on the 1-hour overlap at midnight. Trigger: the EXISTING test TestLocalDate_Basics::testToDate_springDST_2Hour40Savings
(zone "NoMidnight" with a DST saving of 2 hours 40 minutes starting at midnight on 2 April, so the day starts at 02:40, 23:00 UTC);
the grid starts 24 hours before 12:00 GMT+03:40 on 2 April (08:20 UTC on 1 April), its first instant on 2 April is 23:20 UTC, and
assertEquals("Mon Apr 02 02:40:00 GMT+03:40 2007", test.toString()) fails with 03:00:00. It is the only test that newly fails: the
probe shows that only the five toDate tests reach the facade; summer and winter (midnight on the grid), springDST (1-hour gap, day
starts at 01:00, on the grid) and autumnDST (midnight twice; the grid reaches the first midnight, 00:00 GMT+02:00) pass on the
variant.

The gold's javadoc states the idiomatic contract (a java.util.Date at the start of a day in the default time zone of the JDK) and is
silent on how finely the start is found; on the trigger the variant returns 03:00, twenty minutes after the start of the day. The
convention is pinned outside the gold: the facade's own javadoc ("The time will be set to the earliest valid time for that date");
LocalDateTime.toDate, the sibling conversion, finds the earliest valid time after a gap by stepping forward by minutes and back by
seconds, with TestLocalDateTime_Basics::testToDate_springDST_2Hour40Savings (same zone, expects 02:40, passes on the variant);
DateTimeZone.getOffsetFromLocal (a local time in a gap is moved to after the gap) with
TestDateTimeZoneCutover::test_getOffsetFromLocal_NewYork_Spring; LocalDate.toDateTimeAtStartOfDay ("a full datetime at the earliest
valid time for the date") with testToDateTimeAtStartOfDay_avoidDST; TestLocalDate_Basics::testToDate_springDST pins the start of a day
without midnight on the facade's own path.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold. Before
the omission was chosen the correct gold was written without any comparison direction (no isBefore/isAfter, no before/equal split, no
test of one date field alone): every test is "is this instant on the day", an equality of two ISO LocalDates.
 Correct gold (javadoc, signature, start, day, the step back by a day, the hour loop, the second loop, return start):
  T1 absent: year, month and dom build start (new Date(year, month, dom, 12, 0, 0)), which fixes day, the starting instant and the
     returned instant; the gold has no argument check.
  T2 absent: start is initialised by a constructor, moved by setTime before the loops and inside both, and returned; day is a target
     computed before the loops and only read in their conditions (not frozen); no literal-initialised local, no flag, counter or
     best-so-far; each loop body changes the returned instant.
  T3 absent: no case, branch, comparison direction or value-class test; both loops apply the one test "on the day" (an equality), at
     two step sizes in the two directions of one search; the gold's text names no set (no gap, overlap, transition, pair or range
     end); the three parameters are used alike (all only in the constructor). The constructor's literal hour, minute and second are not
     parts the gold reads, and the step sizes are not a set named by the gold's text.
  T4 absent: 'a java.util.Date at the start of a day in the default time zone of the JDK' and '@return a Date at the start of the
     day, never null' are general descriptions the loops address (start is never null); the @param phrases describe the JDK field
     forms passed to the constructor; there is no inline comment; the identifiers start and day name nothing the body does not meet.
 Variant gold (javadoc, signature, start, day, the step back by a day, the hour loop, return start):
  T1 absent: year, month and dom build start, which fixes day, the starting instant, the loop and the returned instant; the gold has
     no argument check.
  T2 absent: start is moved by setTime before the loop and inside it, and returned; day is computed before the loop and read in its
     condition (a target, not frozen); no literal-initialised local; the loop body changes the returned instant.
  T3 absent: the gold handles no member of any special set ('No member handled': no gap, overlap, pair, range end or value-class
     test); its one decision is the equality "on the day", which names no direction and no member of a set; the constructor's literal
     hour, minute and second are not parts the gold reads; the parameters are used alike.
  T4 absent: 'at the start of a day in the default time zone of the JDK' and '@return a Date at the start of the day, never null' are
     general descriptions addressed by the loop (start is never null); the @param phrases describe what the caller passes and are used
     as such; no inline comment; start and day name nothing the body does not meet.

Single owner: only the gold searches for the start of the day; hops 1-3 only gather the receiver's year, month and day of month in the
JDK's form and hop 4 passes them on, so no caller holds an instant before the gold returns, and no choice of fields that names the
same day moves the gold's hour grid, which starts 24 hours before the JDK's noon of that day (fields naming another day give the start
of that other day). After the gold returns, the start can come back only if a caller searches again from the gold's Date, a second
implementation of the gold's search. Declared alternatives (G9): hop 1 counts the year of era from 1900; hop 2 takes the month from
Joda-Time's start of the date; hop 3 takes the day of month from Joda-Time's start of the date. None changes the trigger's result.
Recorded edits above the gold that pass the trigger and the full suite (each to be read as a bypass, not a repair of a hop; each
checked on the variant in the scratch copy /private/tmp/d4j-mi-Time-12-bypass, defects4j test: 0 failing tests each):
 B-0 bypass: hop 1 returns new LocalDateTime(date.getYear(), date.getMonthOfYear(), date.getDayOfMonth(), 0, 0).toDate(), the intact
     sibling conversion (evidence), discarding the rest of the chain including the gold.
 B-1 bypass: hop 4 calls the gold and then steps the returned Date back one second at a time while the instant a second earlier is
     still on its day: a second implementation of the gold's search, overwriting the gold's own result.

Lie: the facade's javadoc claims the first guess is computed directly from the local millis of the date and the raw offset of the
default time zone rather than with the JDK Date constructor; the chain's starting point is made with the JDK Date constructor. It names
neither the step size, nor any step that is omitted, nor any hop.
Pre-edit (comment only): the facade carries @SuppressWarnings("deprecation") between its javadoc and its header, where the recipe's
rewrite_facade does not find the javadoc (extract_transform.find_javadoc_start requires only whitespace between them) and appends no lie.
The annotation is kept (removing it would change the facade's modifiers); the lie sentence is placed by a pre-edit at exactly the
position and in exactly the form rewrite_facade uses ('  ' + sentence + newline, directly before the javadoc's closing */), and
rewrite_facade then replaces only the body.

host_notes are in DESIGN['host_notes']."""

LD = "src/main/java/org/joda/time/LocalDate.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
DTZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
LT = "src/main/java/org/joda/time/LocalTime.java"
ISO = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"

LIE = ("The first guess is computed directly from the local millis of this date and the raw offset of the default time zone, "
       "rather than with the JDK Date constructor.")

GOLD_TEXT = '''/**
 * Gets a <code>java.util.Date</code> at the start of a day in the
 * default time zone of the JDK.
 *
 * @param year  the year minus 1900
 * @param month  the month, from 0 for January
 * @param dom  the day of month
 * @return a Date at the start of the day, never null
 */
@SuppressWarnings("deprecation")
public static Date javaDayStart(int year, int month, int dom) {
    Date start = new Date(year, month, dom, 12, 0, 0);
    LocalDate day = LocalDate.fromDateFields(start);
    start.setTime(start.getTime() - 86400000);
    while (LocalDate.fromDateFields(start).equals(day) == false) {
        start.setTime(start.getTime() + 3600000);
    }
    while (LocalDate.fromDateFields(new Date(start.getTime() - 1000)).equals(day)) {
        start.setTime(start.getTime() - 1000);
    }
    return start;
}'''

HOP1 = '''/**
 * Converts a date to a <code>java.util.Date</code> at the start of that
 * date in the default time zone of the JDK.
 * <p>
 * The JDK counts years from 1900.
 *
 * @param date  the date to convert, not null
 * @return a Date at the start of the date, never null
 */
public static Date toJavaDate(LocalDate date) {
    return DateTimeZoneBuilder.javaDateOf(date, date.getYear() - 1900);
}'''

HOP2 = '''/**
 * Converts a date to a <code>java.util.Date</code> at the start of that
 * date in the default time zone of the JDK, given its year in the form
 * the JDK uses.
 * <p>
 * The JDK counts months from 0 for January.
 *
 * @param date  the date to convert, not null
 * @param year  the year of the date minus 1900
 * @return a Date at the start of the date, never null
 */
public static Date javaDateOf(LocalDate date, int year) {
    return LocalTime.javaDateFor(date, year, date.getMonthOfYear() - 1);
}'''

HOP3 = '''/**
 * Converts a date to a <code>java.util.Date</code> at the start of that
 * date in the default time zone of the JDK, given its year and month in
 * the form the JDK uses.
 *
 * @param date  the date to convert, not null
 * @param year  the year of the date minus 1900
 * @param month  the month of the date, from 0 for January
 * @return a Date at the start of the date, never null
 */
public static Date javaDateFor(LocalDate date, int year, int month) {
    return ISODateTimeFormat.javaDateAt(year, month, date.getDayOfMonth());
}'''

HOP4 = '''/**
 * Gets a <code>java.util.Date</code> at the start of a day in the
 * default time zone of the JDK, given the day in the form the JDK uses.
 *
 * @param year  the year minus 1900
 * @param month  the month, from 0 for January
 * @param dom  the day of month
 * @return a Date at the start of the day, never null
 */
public static Date javaDateAt(int year, int month, int dom) {
    return DateTimeFormatterBuilder.javaDayStart(year, month, dom);
}'''

DESIGN = {
 "instance": "Time-12", "project": "Time", "bug_id": 12, "seed": 4743,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": LD, "class": "org.joda.time.LocalDate", "method": "toDate", "near_line": 994},
 "facade_variant": "V2",
 "state_passed": "this (the LocalDate receiver) to hop 1, typed as LocalDate; hops 1-3 read its public getters; no field read, no write-back",
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestLocalDate_Basics.java",
             "test_class": "org.joda.time.TestLocalDate_Basics", "test_method": "testToDate_springDST_2Hour40Savings"},
 "expected_signature": "but was:<Mon Apr 02 0[3:0]0:00 GMT+03:40 2007>",
 "gold": {"method": "javaDayStart", "text": GOLD_TEXT,
          "fault": {"old": "            start.setTime(start.getTime() + 3600000);\n"
                           "        }\n"
                           "        while (LocalDate.fromDateFields(new Date(start.getTime() - 1000)).equals(day)) {\n"
                           "            start.setTime(start.getTime() - 1000);\n"
                           "        }",
                    "new": "            start.setTime(start.getTime() + 3600000);\n"
                           "        }"}},
 "pre_edits": {
   "chain": [{"file": LD,
              "old": "     * @since 2.0\n"
                     "     */\n"
                     "    @SuppressWarnings(\"deprecation\")\n"
                     "    public Date toDate() {",
              "new": "     * @since 2.0\n"
                     "       " + LIE + "\n"
                     "     */\n"
                     "    @SuppressWarnings(\"deprecation\")\n"
                     "    public Date toDate() {"}],
 },
 "chain": {
   "facade_body": "return org.joda.time.format.PeriodFormatterBuilder.toJavaDate(this);",
   "lie": LIE,
   "hops": [
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "toJavaDate",
      "imports": ["java.util.Date", "org.joda.time.LocalDate", "org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP1},
     {"file": DTZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "javaDateOf",
      "imports": ["java.util.Date", "org.joda.time.LocalDate", "org.joda.time.LocalTime"], "text": HOP2},
     {"file": LT, "class": "org.joda.time.LocalTime", "method": "javaDateFor",
      "imports": [], "text": HOP3},
     {"file": ISO, "class": "org.joda.time.format.ISODateTimeFormat", "method": "javaDateAt",
      "imports": ["java.util.Date"], "text": HOP4},
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "javaDayStart",
      "imports": ["java.util.Date", "org.joda.time.LocalDate"], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.LocalDateTime::toDate",
              "org.joda.time.DateTimeZone::getOffsetFromLocal",
              "org.joda.time.LocalDate::toDateTimeAtStartOfDay"],
 "ownership_reason": "Only the gold searches for the start of the day: hops 1-3 gather the receiver's year, month and day of month in "
                     "the form the JDK uses and hop 4 passes them on, so no caller holds an instant before the gold returns, and no "
                     "choice of fields naming the same day moves the gold's search, which starts 24 hours before the JDK's noon of "
                     "that day. Once the "
                     "gold has returned its Date, the start of the day can come back only if a caller searches again from the gold's "
                     "result, a second implementation of the gold's search. The gold's javadoc promises a Date at the start of the "
                     "day in the default time zone of the JDK; on the trigger the variant returns 03:00 on a day that starts at "
                     "02:40. The convention is pinned outside the gold: the facade's own javadoc ('The time will be set to the "
                     "earliest valid time for that date'); LocalDateTime.toDate, the sibling conversion, sets the earliest valid time "
                     "after a gap by stepping forward by minutes and back by seconds (TestLocalDateTime_Basics "
                     "testToDate_springDST_2Hour40Savings, same zone, expects 02:40, passes); DateTimeZone.getOffsetFromLocal moves a "
                     "local time in a gap to after the gap (TestDateTimeZoneCutover test_getOffsetFromLocal_NewYork_Spring); "
                     "LocalDate.toDateTimeAtStartOfDay converts to the earliest valid time for the date "
                     "(testToDateTimeAtStartOfDay_avoidDST); TestLocalDate_Basics testToDate_springDST pins the start of a day "
                     "without midnight on the facade's own path.",
 "ownership_tests": ["org.joda.time.TestLocalDateTime_Basics::testToDate_springDST_2Hour40Savings",
                     "org.joda.time.TestDateTimeZoneCutover::test_getOffsetFromLocal_NewYork_Spring",
                     "org.joda.time.TestLocalDate_Basics::testToDate_springDST",
                     "org.joda.time.TestLocalDate_Basics::testToDateTimeAtStartOfDay_avoidDST"],
 "compensating": {
   "chain": [
     {"file": PFB, "old": "return DateTimeZoneBuilder.javaDateOf(date, date.getYear() - 1900);",
      "new": "return DateTimeZoneBuilder.javaDateOf(date, date.getYearOfEra() - 1900);",
      "why": "hop 1 counts the year of era, not the proleptic year, from 1900"},
     {"file": DTZB, "old": "return LocalTime.javaDateFor(date, year, date.getMonthOfYear() - 1);",
      "new": "return LocalTime.javaDateFor(date, year, date.toDateTimeAtStartOfDay().getMonthOfYear() - 1);",
      "why": "hop 2 takes the month from the start of the date in Joda-Time's default zone"},
     {"file": LT, "old": "return ISODateTimeFormat.javaDateAt(year, month, date.getDayOfMonth());",
      "new": "return ISODateTimeFormat.javaDateAt(year, month, date.toDateTimeAtStartOfDay().getDayOfMonth());",
      "why": "hop 3 takes the day of month from the start of the date in Joda-Time's default zone"},
   ],
 },
 "host_notes": "host_mode 1500 (bridge7_tasks.json): hosts are hosts_hop_order of the task record, in that order, none substituted: "
               "format.PeriodFormatterBuilder (hop 1, 1872 lines), tz.DateTimeZoneBuilder (hop 2, 1728), LocalTime (hop 3, 1623; the "
               "smallest host), format.ISODateTimeFormat (hop 4, 1711), format.DateTimeFormatterBuilder (hop 5, gold, 2828). All five "
               "are public concrete top-level classes in which a static method compiles; the facade's class LocalDate is not among "
               "them. Anchors from stageB_lib.pick_insertion_anchor with seed 4743 + 100 + i (as mr3_spec.py inserts them): "
               "hop 1 after `clear` (seed 4843), hop 2 after `setStandardOffset` (4844), hop 3 after `size` (4845), hop 4 after "
               "`basicDateTime` (4846), hop 5 after `appendMonthOfYear` (4847); every hop lands in its outer class. The facade "
               "calls hop 1 by its fully-qualified name; each hop imports the next host where it is in another "
               "package (LocalTime already imports ISODateTimeFormat and java.util.Date, and ISODateTimeFormat and "
               "DateTimeFormatterBuilder share a package).",
}
