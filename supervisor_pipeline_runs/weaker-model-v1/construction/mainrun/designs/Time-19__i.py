"""Main run Time-19__i (cell C10i, batch 7, the paired static/instance bridge: the C10 recipe with an INSTANCE-method facade, on the
fixed checkout of Defects4J Time-19; the real bug modified DateTimeZone, the facade's class). Paired static instance: MR-Time-19
(batch 5, static facade DateTimeZone.forOffsetHoursMinutes); none of its files was opened. Facade reuse (task record
facade_reuse_of): Time-9__i and Time-17__i list the same three allowed instance methods; recorded, nothing changes in the build.

Facade: DateTimeZone.getMillisKeepLocal(DateTimeZone newZone, long oldInstant) (allowed target, BATCH7_PREREGISTRATION row 209).
facade_variant: V2 (receiver as parameter). state_passed: the receiver `this` (typed DateTimeZone) as hop 1's `zone`, together with
the two parameters newZone and oldInstant; no field is read, nothing is written back. The hops call only public DateTimeZone methods
(getDefault, convertUTCToLocal, getOffset, convertLocalToUTC(long, boolean)).
Original computation: a null new zone means the default zone; the zone itself gives the instant unchanged; otherwise the instant
is converted to local millis in this zone (convertUTCToLocal) and back to UTC millis in the new zone with
newZone.convertLocalToUTC(instantLocal, false, oldInstant), which uses the new zone's offset at the original instant whenever that
offset gives the same local time, and otherwise converts the local millis on their own (convertLocalToUTC(instantLocal, false)).
Production callers: DateTime.withZoneRetainFields, MutableDateTime.setZoneRetainFields, DateMidnight.withZoneRetainFields and the
LocalDate, LocalDateTime and LocalTime (long, Chronology) constructors.
Why not the other two allowed methods: DateTimeZone.getOffset(ReadableInstant) is a null-means-now dispatch to getOffset(long) with
no decision a gold could own, and its only null case is asserted by two tests (testGetOffset_RI, testGetOffsetFixed_RI).
DateTimeZone.getOffsetFromLocal is pinned by most of TestDateTimeZoneCutover: every one-line omission of its decisions (the gap
rule, its next-transition comparison, the overlap rule, the overlap window) fails many tests at once, the previous-transition
guard is redundant (its omission changes no result), and the one decision that a single test sees (zero offsets in the overlap
rule) can only be reached by changing an operator, which is not an omission.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4), scratch copies /private/tmp/d4j-mi-Time-19-probe/{a,b,c}:
  getMillisKeepLocal, first statement `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`: `defects4j compile` fails,
    BUILD FAILED at Time.build.xml:97 with java.lang.IllegalStateException: PROBE-REACHED. The build's compile target runs
    org.joda.time.tz.ZoneInfoCompiler, which reaches the facade through new LocalDate(...) with this == newZone == UTC, so no test
    can run with the unconditional probe. Supplementary probe on the same first statement, guarded so that the build-time call can
    complete: `if (newZone != this) { throw new IllegalStateException("PROBE-REACHED"); }`: compile OK;
    `defects4j test -t org.joda.time.TestDateTimeZone::testGetMillisKeepLocal`: 1 failing test, IllegalStateException:
    PROBE-REACHED at DateTimeZone.getMillisKeepLocal(DateTimeZone.java:1028);
    `defects4j test -t org.joda.time.TestDateTimeZoneCutover::testForum4013394_retainOffsetWhenRetainFields_sameOffsetsDifferentZones`:
    1 failing test, the same message and frame. The facade is reached by existing tests.
  getOffsetFromLocal, unconditional probe: compile OK; TestDateTimeZone::testGetOffset_long fails with PROBE-REACHED at
    DateTimeZone.getOffsetFromLocal(DateTimeZone.java:881).
  getOffset(ReadableInstant), unconditional probe: compile OK; TestDateTimeZone::testGetOffset_RI fails with PROBE-REACHED at
    DateTimeZone.getOffset(DateTimeZone.java:813).
Omission screen before designing (scratch /private/tmp/d4j-mi-Time-19-probe/m): the original facade with its last call written
newZone.convertLocalToUTC(instantLocal, false) (the variant's behaviour): full suite, 1 failing test,
TestDateTimeZoneCutover::testForum4013394_retainOffsetWhenRetainFields_sameOffsetsDifferentZones,
expected:<...7-10-28T01:15:00.000[+01:00]> but was:<...7-10-28T01:15:00.000[Z]>.

Hosts (host_mode = "1500"; hosts_hop_order of the task record, in that order; mr_lib preview with seed 4258 on
org/joda/time/DateTimeZone.java draws the same five in the same order; none substituted):
  hop 1 format.DateTimeFormatterBuilder  2829 lines  instantInZone            decision: a null new zone means the default zone
  hop 2 tz.DateTimeZoneBuilder           1728 lines  keepLocalInZone          decision: the zone itself gives the instant unchanged
  hop 3 format.ISODateTimeFormat         1711 lines  instantWithLocalFields   pass-through
  hop 4 DateTime                         2298 lines  zoneMillisKeepingFields  pass-through
  hop 5 LocalDate                        2086 lines  millisAtSameLocal        GOLD: the conversion through local millis, with the
                                                                              choice of the UTC instant in the new zone
Host newline counts 2829, 1728, 1711, 2298, 2086; the smallest host is ISODateTimeFormat (1711 lines).
The correct configuration returns the original result for every input: the same null default and identity test, the same
convertUTCToLocal call, the same test of the new zone's offset at the original instant (getOffset(instantLocal - offset) ==
offset) evaluated first, and the same convertLocalToUTC(instantLocal, false) otherwise; no DateTimeZone subclass overrides
convertUTCToLocal or either convertLocalToUTC overload, so the gold's test is exactly the body of the three-argument overload.

Fault (omission of a decision in the gold): the test that keeps the new zone's offset at the original instant is dropped, so the
gold always converts the local millis on their own. The variant gold then reads as the ordinary routine "to local millis in one
zone, back to UTC millis in the other" (the facade's own javadoc procedure). Trigger: the EXISTING test
TestDateTimeZoneCutover::testForum4013394_retainOffsetWhenRetainFields_sameOffsetsDifferentZones. Europe/London and Europe/Lisbon
share their offsets; baseAfter is 2007-10-28T01:15+01:00 London (00:15Z, inside the autumn overlap). withZoneRetainFields(Lisbon)
must give 01:15+01:00 Lisbon, the same instant; the variant converts local 01:15 on its own and gets 01:15Z, an hour later, so
assertEquals(baseAfter.toString(), testAfter.toString()) fails with expected:<...7-10-28T01:15:00.000[+01:00]> but
was:<...7-10-28T01:15:00.000[Z]>. The baseBefore assertion still holds (00:15 local is not ambiguous). It is the only test that
newly fails: the LocalDate, LocalDateTime and LocalTime constructors and MutableDateTime.setDate/setTime convert into UTC, whose
offset never changes, and the other withZoneRetainFields tests (Gaza and Turk mocks, TestDateTime_Basics) are at gaps or ordinary
times, where both conversions agree; screened above.

The gold's javadoc states the idiomatic contract in the facade's own words (the instant in another zone keeping the same local
time; converted to local millis in its own zone, then back to UTC millis in the new zone) and is silent on the offset. At an
overlap the local time occurs twice; the convention for which of the two is meant is pinned outside the gold:
DateTimeZone.convertLocalToUTC(long, boolean, long) ('attempting to use the same offset as the original ... Whenever possible, the
same offset as the original offset will be used. This is most significant during a daylight savings overlap'), which the facade
called; ZonedChronology.ZonedDateTimeField.set/add/addWrapField convert local millis back with that overload (passing tests
testWithMillisOfSecondInDstChange_Paris_winter, 02:30:10.123+01:00 keeps +01:00, and testWithMinuteOfHourInDstChange_mockZone,
'retain offset'); DateTimeZone.adjustOffset uses it to pick the earlier or later offset (testBug3192457_adjustOffset passes);
testGetMillisKeepLocal pins the facade's ordinary conversions and the null default and passes on the variant.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, instantLocal from convertUTCToLocal, one if that returns instantLocal minus the new zone's
 offset at the instant, the fall-through convertLocalToUTC):
  T1 absent: zone converts the instant to local millis; newZone gives both the offset test and the conversion; instant feeds
     convertUTCToLocal and the offset test; none is only argument-checked.
  T2 absent: instantLocal is read by the test, the return and the fall-through; no literal-initialised local, no loop; the if
     returns a different instant from the fall-through at an overlap, so the decision matters.
  T3 absent: the decision has two outcomes (the original instant's offset, or the local millis converted on their own); the gold
     names no set or class; zone and newZone each get their own conversion.
  T4 absent: 'keeping the same local time', the two-step procedure and the @return clause are general descriptions the body
     addresses; 'not null' clauses are caller preconditions; no inline comment; nothing to rewrite.
 Variant gold (javadoc, signature, `long instantLocal = zone.convertUTCToLocal(instant);`,
 `return newZone.convertLocalToUTC(instantLocal, false);`):
  T1 absent: zone, newZone and instant each change the returned instant (receiver of the first call, receiver of the second, and
     argument of the first); no argument check exists.
  T2 absent: the one local, instantLocal, is assigned from a call and read as the argument of the returned call; no literal-
     initialised local (false is a call argument), no loop, no cursor, flag or best-so-far, no branch, case or ternary.
  T3 absent: no member of any set is handled at all ('No member handled': no overlap, gap, offset or special-value test remains);
     the gold names no class; the two zones are a pair whose members both get their conversion (to local in zone, back to UTC in
     newZone), and no range end or pair half is checked on one side only.
  T4 absent: 'Gets the millisecond instant in another zone keeping the same local time' and 'converted to local millis in its own
     zone, and the local millis are then converted back to UTC millis in the new zone' describe exactly the two calls; '@return
     the UTC millisecond instant with the same local time in the new zone' is general; '@param ... not null' are caller
     preconditions; the identifier instantLocal holds the local millis; no limit, bound, value class, case or property is named.

Single owner: only the gold forms the UTC instant in the new zone; hop 1 only replaces a null zone, hop 2 only returns the
instant for the zone itself, hops 3 and 4 pass the three values along, and every hop returns the gold's result unchanged. Once the
gold has converted the local millis on their own, the result is an instant with the right local time, and no caller can tell
from it whether the other instant of an overlap was meant without redoing the gold's decision. Declared alternatives (G9): hop 2
compares the zones by ID as well; hop 3 passes the instant at the later offset of an overlap (zone.adjustOffset(instant, true));
hop 4 passes the instant at the earlier offset (zone.adjustOffset(instant, false)). None changes the trigger's London/Lisbon case.
Recorded edits above the gold (bypasses and test-fitted edits, not repairs of the chain). B-1 and B-2 were applied to the variant
in scratch copies (defects4j test: 0 failing tests each) and their counter-examples were computed against the built classes of the
pristine fixture and of each scratch copy; B-0 restores the original behaviour by construction:
 B-0 bypass: the facade (its original body) or any of hops 1-4 returns newZone.convertLocalToUTC(zone.convertUTCToLocal(instant),
     false, instant), discarding the rest of the chain including the gold.
 B-1 partial second implementation: hop 2 also returns the instant unchanged when both zones have the same offset at it
     (`if (newZone == zone || newZone.getOffset(instant) == zone.getOffset(instant)) {`). It answers the trigger's sub-case without
     the gold, and the gold's choice stays broken wherever the offsets differ at the instant: Europe/Paris 2011-10-29T23:15Z (01:15
     local) kept to Europe/London gives 01:15Z (GMT) instead of 00:15Z (BST, the new zone's offset at the original instant).
 B-2 test-fitted: hop 4 moves the gold's result to the earlier offset of an overlap
     (`return newZone.adjustOffset(LocalDate.millisAtSameLocal(zone, newZone, instant), false);`). It contradicts the convention
     pinned above for an instant at the later offset: London 2007-10-28T01:15Z (01:15 GMT) kept to Lisbon must stay 01:15Z, and
     becomes 00:15Z.
 B-3 bypass: a hop tests the original instant's offset itself and calls the gold only otherwise (one conditional expression), a
     second implementation of the gold's decision.

Lie: the facade's javadoc claims the instant is split into whole days since the epoch and the millis of the day, and only the
millis of the day are carried across to the new zone; the chain never splits the instant and converts whole millis through each
zone's offset. It names neither the offset nor the overlap nor any hop.

The facade's existing javadoc stays true for the chain apart from the appended lie (null means default; local millis in this zone,
then UTC millis in the new zone); no pre-edit. The facade calls hop 1 by its fully-qualified name; each hop imports the next host
where the packages differ."""

DTZ = "src/main/java/org/joda/time/DateTimeZone.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"
DTZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
ISO = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"
DT = "src/main/java/org/joda/time/DateTime.java"
LD = "src/main/java/org/joda/time/LocalDate.java"

GOLD_TEXT = '''/**
 * Gets the millisecond instant in another zone keeping the same local time.
 * <p>
 * The instant is converted to local millis in its own zone, and the local
 * millis are then converted back to UTC millis in the new zone.
 *
 * @param zone  the zone of the instant, not null
 * @param newZone  the new zone, not null
 * @param instant  the UTC millisecond instant to convert
 * @return the UTC millisecond instant with the same local time in the new zone
 */
public static long millisAtSameLocal(DateTimeZone zone, DateTimeZone newZone, long instant) {
    long instantLocal = zone.convertUTCToLocal(instant);
    if (newZone.getOffset(instantLocal - newZone.getOffset(instant)) == newZone.getOffset(instant)) {
        return instantLocal - newZone.getOffset(instant);
    }
    return newZone.convertLocalToUTC(instantLocal, false);
}'''

HOP1 = '''/**
 * Gets the millisecond instant in another zone keeping the same local time.
 * <p>
 * A null new zone means the default zone.
 *
 * @param zone  the zone of the instant, not null
 * @param newZone  the new zone, null means default
 * @param instant  the UTC millisecond instant to convert
 * @return the UTC millisecond instant with the same local time in the new zone
 */
public static long instantInZone(DateTimeZone zone, DateTimeZone newZone, long instant) {
    if (newZone == null) {
        newZone = DateTimeZone.getDefault();
    }
    return DateTimeZoneBuilder.keepLocalInZone(zone, newZone, instant);
}'''

HOP2 = '''/**
 * Gets the millisecond instant in another zone keeping the same local time.
 * <p>
 * An instant kept in its own zone is returned unchanged.
 *
 * @param zone  the zone of the instant, not null
 * @param newZone  the new zone, not null
 * @param instant  the UTC millisecond instant to convert
 * @return the UTC millisecond instant with the same local time in the new zone
 */
public static long keepLocalInZone(DateTimeZone zone, DateTimeZone newZone, long instant) {
    if (newZone == zone) {
        return instant;
    }
    return ISODateTimeFormat.instantWithLocalFields(zone, newZone, instant);
}'''

HOP3 = '''/**
 * Gets the millisecond instant in another zone with the same local fields.
 *
 * @param zone  the zone of the instant, not null
 * @param newZone  the new zone, not null
 * @param instant  the UTC millisecond instant to convert
 * @return the UTC millisecond instant with the same local time in the new zone
 */
public static long instantWithLocalFields(DateTimeZone zone, DateTimeZone newZone, long instant) {
    return DateTime.zoneMillisKeepingFields(zone, newZone, instant);
}'''

HOP4 = '''/**
 * Gets the millisecond instant in another zone keeping the field values.
 *
 * @param zone  the zone of the instant, not null
 * @param newZone  the new zone, not null
 * @param instant  the UTC millisecond instant to convert
 * @return the UTC millisecond instant with the same local time in the new zone
 */
public static long zoneMillisKeepingFields(DateTimeZone zone, DateTimeZone newZone, long instant) {
    return LocalDate.millisAtSameLocal(zone, newZone, instant);
}'''

DESIGN = {
 "instance": "Time-19", "project": "Time", "bug_id": 19, "seed": 4258,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade_variant": "V2",
 "state_passed": "receiver this (as DateTimeZone zone) plus newZone and oldInstant; no field read, no write-back",
 "host_mode": "1500",
 "facade": {"file": DTZ, "class": "org.joda.time.DateTimeZone", "method": "getMillisKeepLocal", "near_line": 1027},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestDateTimeZoneCutover.java",
             "test_class": "org.joda.time.TestDateTimeZoneCutover",
             "test_method": "testForum4013394_retainOffsetWhenRetainFields_sameOffsetsDifferentZones"},
 "expected_signature": "expected:<...7-10-28T01:15:00.000[+01:00]> but was:<...7-10-28T01:15:00.000[Z]>",
 "gold": {"method": "millisAtSameLocal", "text": GOLD_TEXT,
          "fault": {"old": "        long instantLocal = zone.convertUTCToLocal(instant);\n"
                           "        if (newZone.getOffset(instantLocal - newZone.getOffset(instant)) == newZone.getOffset(instant)) {\n"
                           "            return instantLocal - newZone.getOffset(instant);\n"
                           "        }\n"
                           "        return newZone.convertLocalToUTC(instantLocal, false);",
                    "new": "        long instantLocal = zone.convertUTCToLocal(instant);\n"
                           "        return newZone.convertLocalToUTC(instantLocal, false);"}},
 "chain": {
   "facade_body": "return org.joda.time.format.DateTimeFormatterBuilder.instantInZone(this, newZone, oldInstant);",
   "lie": "The instant is first split into the whole days since the epoch and the millis of the day, and only the millis "
          "of the day are carried across to the new zone.",
   "hops": [
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "instantInZone",
      "imports": ["org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP1},
     {"file": DTZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "keepLocalInZone",
      "imports": ["org.joda.time.format.ISODateTimeFormat"], "text": HOP2},
     {"file": ISO, "class": "org.joda.time.format.ISODateTimeFormat", "method": "instantWithLocalFields",
      "imports": ["org.joda.time.DateTime", "org.joda.time.DateTimeZone"], "text": HOP3},
     {"file": DT, "class": "org.joda.time.DateTime", "method": "zoneMillisKeepingFields", "imports": [], "text": HOP4},
     {"file": LD, "class": "org.joda.time.LocalDate", "method": "millisAtSameLocal", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.DateTimeZone::convertLocalToUTC",
              "org.joda.time.chrono.ZonedChronology$ZonedDateTimeField::set",
              "org.joda.time.DateTimeZone::adjustOffset"],
 "ownership_reason": "Only the gold forms the UTC instant in the new zone: hop 1 only replaces a null new zone by the default "
                     "zone, hop 2 only returns the instant for the zone itself, hops 3 and 4 pass the zones and the instant "
                     "along, and every hop returns the gold's result unchanged. At a daylight savings overlap the local time "
                     "occurs at two instants, and once the gold has converted the local millis on their own the result has the "
                     "right local time, so no caller can tell which instant was meant without redoing the gold's decision. The "
                     "convention is pinned outside the gold: DateTimeZone.convertLocalToUTC(long, boolean, long), which the "
                     "facade called, converts 'attempting to use the same offset as the original' ('Whenever possible, the same "
                     "offset as the original offset will be used. This is most significant during a daylight savings "
                     "overlap'); ZonedChronology.ZonedDateTimeField.set, add and addWrapField convert local millis back with "
                     "that overload, so a field change inside an overlap keeps the offset (TestDateTimeZoneCutover "
                     "testWithMillisOfSecondInDstChange_Paris_winter keeps +01:00, testWithMinuteOfHourInDstChange_mockZone "
                     "'retain offset'); DateTimeZone.adjustOffset uses it to choose the earlier or the later offset "
                     "(testBug3192457_adjustOffset); TestDateTimeZone testGetMillisKeepLocal pins the facade's ordinary "
                     "conversions and its null default. London and Lisbon share their offsets, so keeping the local time of "
                     "01:15+01:00 London in Lisbon must give the same instant; the variant gold gives the instant an hour "
                     "later.",
 "ownership_tests": ["org.joda.time.TestDateTimeZoneCutover::testWithMillisOfSecondInDstChange_Paris_winter",
                     "org.joda.time.TestDateTimeZoneCutover::testWithMinuteOfHourInDstChange_mockZone",
                     "org.joda.time.TestDateTimeZoneCutover::testBug3192457_adjustOffset",
                     "org.joda.time.TestDateTimeZone::testGetMillisKeepLocal"],
 "compensating": {
   "chain": [
     {"file": DTZB, "old": "if (newZone == zone) {",
      "new": "if (newZone == zone || newZone.getID().equals(zone.getID())) {",
      "why": "hop 2 also treats a zone with the same ID as the zone itself"},
     {"file": ISO, "old": "return DateTime.zoneMillisKeepingFields(zone, newZone, instant);",
      "new": "return DateTime.zoneMillisKeepingFields(zone, newZone, zone.adjustOffset(instant, true));",
      "why": "hop 3 passes the instant at the later offset of an overlap"},
     {"file": DT, "old": "return LocalDate.millisAtSameLocal(zone, newZone, instant);",
      "new": "return LocalDate.millisAtSameLocal(zone, newZone, zone.adjustOffset(instant, false));",
      "why": "hop 4 passes the instant at the earlier offset of an overlap"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are hosts_hop_order of the task record, in that order, none substituted; mr_lib preview "
               "(seed 4258, target org/joda/time/DateTimeZone.java) draws the same five in the same order: "
               "format.DateTimeFormatterBuilder (hop 1, 2829 lines), tz.DateTimeZoneBuilder (hop 2, 1728), "
               "format.ISODateTimeFormat (hop 3, 1711, the smallest host), DateTime (hop 4, 2298), LocalDate (hop 5, gold, "
               "2086). All five are public concrete top-level classes in which a static method compiles. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 4258 + 100 + i: hop 1 after `appendHourOfHalfday` (line idx 708, "
               "seed 4358), hop 2 after `toDateTimeZone` (401, 4359), hop 3 after `dateElementParser` (637, 4360), hop 4 after "
               "`plus` (910, 4361), hop 5 after the constructor `LocalDate` (333, 4362); all in the outer class. The facade calls "
               "hop 1 by its fully-qualified name; hop 1 imports tz.DateTimeZoneBuilder, hop 2 imports "
               "format.ISODateTimeFormat, hop 3 imports DateTime and DateTimeZone; hops 4 and 5 share the facade's package. "
               "The build's ZoneInfoCompiler runs the facade (UTC to UTC, answered by hop 2) during compile; the chain loads "
               "only DateTimeFormatterBuilder and DateTimeZoneBuilder there.",
}
