"""Main run Time-17__i (cell C10i, batch 7: the paired static/instance bridge; the C10 recipe with an INSTANCE-method facade, on the
fixed checkout of Defects4J Time-17; the real bug modified DateTimeZone, the facade's class). Paired static instance: MR-Time-17
(facade DateTimeZone.setProvider), which this builder did not open. Facade reuse (bridge7_tasks.json facade_reuse_of): Time-9__i
has the same allowed instance candidates; recorded, nothing changes in the build.

Facade: DateTimeZone.getOffsetFromLocal(long) (allowed target, BATCH7_PREREGISTRATION.md row 208; not the paired static facade
setProvider; DateTimeZone is not one of the five hosts). facade_variant = V2 (receiver as parameter): the computation needs the
receiver's public methods getOffset(long), nextTransition(long) and previousTransition(long). state_passed = the receiver `this`
(typed DateTimeZone) and the parameter instantLocal, handed to hop 1; no field is read, no field is written, no write-back. The
original has no argument guard, so the facade body is the single call to hop 1 (by fully-qualified name). FixedDateTimeZone keeps
its own override; CachedDateTimeZone and the precalculated/DST zones inherit the facade and pass themselves as the receiver.
Original computation: offsetLocal = getOffset(instantLocal) (first estimate); offsetAdjusted = getOffset(instantLocal -
offsetLocal); if they differ and offsetLocal is the smaller, the next transitions after the two candidate instants are compared and
offsetLocal is returned when they differ (the local time is in a gap; the result is after the gap); if they agree and offsetLocal >=
0, prev = previousTransition(instantAdjusted) and, when prev < instantAdjusted and instantAdjusted - prev <= offsetPrev - offsetLocal
(offsetPrev = getOffset(prev)), offsetPrev is returned (the local time is in an overlap; the earlier instant); else offsetAdjusted.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4, all three allowed facades, scratch copies /private/tmp/d4j-mi-Time-17-probe*):
the facade's first statement was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
  getOffsetFromLocal (chosen): defects4j compile OK; defects4j test -t TestDateTimeZone::testGetOffset_long -> 1 failing,
    java.lang.IllegalStateException: PROBE-REACHED at DateTimeZone.getOffsetFromLocal(DateTimeZone.java:881);
    TestDateTimeZoneCutover::test_getOffsetFromLocal_Gaza -> PROBE-REACHED; TestDateTimeZoneCutover::test_getOffsetFromLocal_Moscow_Autumn
    (the trigger) -> PROBE-REACHED at getOffsetFromLocal called from doTest_getOffsetFromLocal (TestDateTimeZoneCutover.java:1335);
    full suite with the probe: 724 failing tests. Reached directly by existing tests.
  getMillisKeepLocal: defects4j compile FAILS with the probe (the build's ZoneInfoCompiler step, Time.build.xml:97, reaches the method
    through LocalDate), so defects4j test cannot run; on classes compiled from the pristine tree with only DateTimeZone recompiled with
    the probe, JUnit runs of TestDateTimeZone.testGetMillisKeepLocal and TestDateTimeZoneCutover.testForum4013394_... fail with
    PROBE-REACHED. Reachable, not chosen (below).
  getOffset(ReadableInstant): TestDateTimeZone::testGetOffset_RI -> PROBE-REACHED at DateTimeZone.getOffset(DateTimeZone.java:813).
    Reachable, not chosen (below).
Why this facade (exposure runs: each candidate omission applied to the ORIGINAL method in a scratch copy, full suite, 3883 tests,
baseline 0 failing): getOffset(ReadableInstant) has one decision (null means now), reached by two tests (testGetOffset_RI and
testGetOffsetFixed_RI), and nothing to distribute. getMillisKeepLocal: dropping the original-offset preference fails only
testForum4013394, but in that overlap both results have the same local time, so no quiet gold contract is violated, and the
preference cannot be omitted without leaving a dead local; dropping the null default fails only testGetMillisKeepLocal, an argument
normalisation any hop could add. getOffsetFromLocal: dropping the gap return fails 5 tests, dropping the overlap return 7, the gap
test in both directions 7, the unconditional gap return 13; the inclusive end of the overlap (instantAdjusted - prev <= diff
read as <) fails exactly one test, test_getOffsetFromLocal_Moscow_Autumn, which checks 02:59:59.999 local. That is the fault used.

Chain (hosts = hosts_hop_order of the task record, unchanged, which equals the recipe draw for seed 8295 and target
org/joda/time/DateTimeZone.java printed by mr_lib preview):
  hop 1 format.DateTimeFormatterBuilder.localOffsetOf    plumbing: the first estimate, the zone's offset at the local instant read as UTC
  hop 2 tz.DateTimeZoneBuilder.wallOffsetFrom            plumbing: the local instant adjusted by the estimate; the offset there is the second estimate
  hop 3 format.PeriodFormatterBuilder.settleLocalOffset  decision when the estimates differ (the gap rule, original code); when they
                                                         agree, the instant reached and the offset are passed on
  hop 4 DateTime.localOffsetAt                           decision: a negative offset is returned as it is (the original's offsetLocal >= 0
                                                         condition); any other offset is passed on
  hop 5 Period.wallOffsetAt                              GOLD: the overlap decision against the zone's previous transition
The correct configuration returns the original result for every input: hops 1-4 are the original statements in the original order;
the gold reads prev = previousTransition(instant) and offsetPrev = getOffset(prev) exactly as the original, then moves prev one
millisecond to the transition instant (transition++) and tests instant - transition < offsetPrev - offset, which for integers is the
original instant - prev <= diff.

Fault (one-line omission in the gold): the line `transition++;` is dropped. previousTransition gives the last millisecond of the
earlier offset (DateTimeZoneBuilder's zones return the transition minus one), so without the step the bound ends one millisecond
early and the last millisecond of an overlap gets the later offset. The variant gold still reads as an ordinary overlap check
(previous transition, offset before it, "is the instant less than the repeated span after the transition"). Trigger: the EXISTING
test TestDateTimeZoneCutover::test_getOffsetFromLocal_Moscow_Autumn (Europe/Moscow, 2007-10-28, 03:00 +04:00 back to 02:00
+03:00); its checks up to 02:59:59.998 still hold, and the check of 02:59:59.999 (line 899) fails with
"2007-10-28T02:59:59.999+03:00 expected:<...10-28T02:59:59.999+0[4]:00> but was:<...10-28T02:59:59.999+0[3]:00>". It is the only test
that newly fails (exposure run above; G5 re-checks it on the chain): test_getOffsetFromLocal_Moscow_Autumn_overlap_mins checks whole
minutes, the DateTime-creation overlap tests use quarter hours.

The gold's javadoc states the contract the facade documents (the offset to subtract from local time to get UTC; during an
overlap, where a local time occurs twice, the offset of the earlier instant) and is silent on how the previous transition relates
to the transition instant. 02:59:59.999 occurs twice in Moscow that night (22:59:59.999Z at +04:00, 23:59:59.999Z at +03:00), so
the variant's +03:00 violates the gold's own contract on the trigger input. The convention is pinned outside the gold: the facade's
javadoc ("During a DST overlap ... this method will return the earlier instant"); DateTimeZoneBuilder's PrecalculatedZone and
DSTZone previousTransition return the transition minus one, and ZoneInfoCompiler.test checks exactly that (trans - 1 != millis is
an error), with TestBuilder::testReverseTransitions (each previousTransition result is the next row's instant minus one and carries
the earlier row's offset) passing; DateTimeZone.adjustOffset treats an overlap as the range from nextTransition (the transition
instant) to transition + diff, end exclusive; the overlap tests test_getOffsetFromLocal_Moscow_Autumn_overlap_mins,
test_DateTime_constructor_Moscow_Autumn and testDateTimeCreation_athens pass on the variant.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; previousTransition; guard; offsetBefore; transition++; bound; two returns):
  T1 absent: zone gives the transition and the offset before it; instant bounds the guard, the transition lookup and the test;
     offset enters the bound and is the fall-through result.
  T2 absent: transition is assigned from a call and moved by transition++, read by the guard, getOffset and the bound; offsetBefore
     is read by the bound and returned; no literal-initialised local, no loop; the guard and the bound each decide between returning
     offsetBefore and offset.
  T3 absent: the overlap's two ends are both tested (start: transition < instant; end: instant - transition < span); the result is
     one of the two offsets, earlier or current; no other set is named.
  T4 absent: 'the offset to subtract from local time to get UTC time' and 'the offset of the earlier of the two instants' during an
     overlap are produced by the branch returning offsetBefore; the @param texts are caller preconditions; identifiers name nothing
     the body does not meet.
 Variant gold (the same without transition++):
  T1 absent: zone, instant and offset each still change the result (lookup, guard, bound, fall-through); none is only argument-checked.
  T2 absent: transition is assigned from previousTransition and read three times; offsetBefore is read by the bound and returned; no
     dead or frozen local (no loop, no literal initialiser); the guard and the bound both still choose between two different results.
  T3 absent: both ends of the overlap are still tested; the earlier/current offsets are both returned on their paths; the gold names
     no class it handles in part ('an overlap, where a local time occurs twice' is handled by the bound branch).
  T4 absent: the overlap sentence is met by the branch returning offsetBefore for instants within offsetBefore - offset after the
     transition; '@return the millisecond offset to subtract from local time to get UTC time' is a general description the body
     addresses; '@param offset  the offset of the zone at the instant' is a caller precondition; no inline comment.

Single owner: only the gold sees the previous transition and the offset before it; hops 1-2 compute the two estimates, hop 3 decides
only when they differ, hop 4 only by sign. For the trigger the estimates agree (+03:00 at 23:59:59.999Z) and the offset is positive,
so the result is the gold's alone, and no caller can tell a later offset from an earlier one afterwards. Declared alternatives (G9):
hop 4 passes the instant one millisecond earlier (the last millisecond passes but 02:00 then gets +03:00); hop 4 returns zero
offsets as they are; hop 2 takes the second estimate one millisecond after the adjusted instant. None passes the trigger.
Recorded bypasses: B-0 the facade (its original body) or any hop re-implements the whole computation, making the rest of the chain
dead; B-1 hop 4 answers every non-negative offset with DateTimeZone.adjustOffset
(`return (int) (instant + offset - zone.adjustOffset(instant, false));`), a second implementation of the overlap decision that makes
the gold dead.

Lie: the facade's javadoc claims the offset is computed as the zone's standard offset at the local instant plus the daylight saving
amount at the instant this gives; the chain never reads a standard offset or a saving amount. It names neither the overlap end, nor
the previous transition, nor any hop.

host_mode = "1500" (task record; host_lines null). Host newline counts (mr_lib preview): DateTimeFormatterBuilder 2829,
DateTimeZoneBuilder 1728, PeriodFormatterBuilder 1868, DateTime 2298, Period 1574 (the smallest host, and the gold host)."""

DTZ = "src/main/java/org/joda/time/DateTimeZone.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"
DTZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
DT = "src/main/java/org/joda/time/DateTime.java"
PER = "src/main/java/org/joda/time/Period.java"

GOLD_TEXT = '''/**
 * Gets the millisecond offset to subtract from local time to get UTC time,
 * given a UTC instant and the offset of the zone at that instant.
 * <p>
 * During an overlap, where a local time occurs twice, the offset of the
 * earlier of the two instants is returned.
 *
 * @param zone  the time zone, not null
 * @param instant  the UTC instant, the local time less the offset
 * @param offset  the offset of the zone at the instant
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int wallOffsetAt(DateTimeZone zone, long instant, int offset) {
    long transition = zone.previousTransition(instant);
    if (transition < instant) {
        int offsetBefore = zone.getOffset(transition);
        transition++;
        if (instant - transition < offsetBefore - offset) {
            return offsetBefore;
        }
    }
    return offset;
}'''

HOP1 = '''/**
 * Gets the millisecond offset to subtract from local time to get UTC time.
 * <p>
 * The first estimate is the offset of the zone at the local instant read
 * as a UTC instant.
 *
 * @param zone  the time zone, not null
 * @param instantLocal  the millisecond instant, relative to the zone, to get the offset for
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int localOffsetOf(DateTimeZone zone, long instantLocal) {
    return DateTimeZoneBuilder.wallOffsetFrom(zone, instantLocal, zone.getOffset(instantLocal));
}'''

HOP2 = '''/**
 * Gets the millisecond offset to subtract from local time to get UTC time,
 * starting from a first estimate of the offset.
 * <p>
 * The local instant is adjusted by the estimate, and the offset of the
 * zone at the adjusted instant is the second estimate.
 *
 * @param zone  the time zone, not null
 * @param instantLocal  the millisecond instant, relative to the zone
 * @param offsetLocal  the first estimate of the offset
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int wallOffsetFrom(DateTimeZone zone, long instantLocal, int offsetLocal) {
    long instantAdjusted = instantLocal - offsetLocal;
    return PeriodFormatterBuilder.settleLocalOffset(zone, instantLocal, offsetLocal, zone.getOffset(instantAdjusted));
}'''

HOP3 = '''/**
 * Gets the millisecond offset to subtract from local time to get UTC time,
 * from two estimates of the offset.
 * <p>
 * Estimates that differ mean the local instant is near a transition. If
 * the first estimate is the smaller one and the next transitions after the
 * instants reached with the two estimates differ, the local instant falls
 * in a gap and the first estimate is returned, so that the instant is after
 * the gap; otherwise the second estimate is returned. Estimates that agree
 * are passed on with the instant reached with them.
 *
 * @param zone  the time zone, not null
 * @param instantLocal  the millisecond instant, relative to the zone
 * @param offsetLocal  the first estimate, the offset at the local instant read as UTC
 * @param offsetAdjusted  the second estimate, the offset at the instant reached with the first
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int settleLocalOffset(DateTimeZone zone, long instantLocal, int offsetLocal, int offsetAdjusted) {
    if (offsetLocal != offsetAdjusted) {
        if ((offsetLocal - offsetAdjusted) < 0) {
            long nextLocal = zone.nextTransition(instantLocal - offsetLocal);
            long nextAdjusted = zone.nextTransition(instantLocal - offsetAdjusted);
            if (nextLocal != nextAdjusted) {
                return offsetLocal;
            }
        }
        return offsetAdjusted;
    }
    return DateTime.localOffsetAt(zone, instantLocal - offsetLocal, offsetLocal);
}'''

HOP4 = '''/**
 * Gets the millisecond offset to subtract from local time to get UTC time,
 * given a UTC instant and the offset of the zone at that instant.
 * <p>
 * A negative offset is returned as it is; an offset of zero or more is
 * passed on with the instant.
 *
 * @param zone  the time zone, not null
 * @param instant  the UTC instant, the local time less the offset
 * @param offset  the offset of the zone at the instant
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int localOffsetAt(DateTimeZone zone, long instant, int offset) {
    if (offset < 0) {
        return offset;
    }
    return Period.wallOffsetAt(zone, instant, offset);
}'''

DESIGN = {
 "instance": "Time-17", "project": "Time", "bug_id": 17, "seed": 8295,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade_variant": "V2",
 "state_passed": "the receiver this (typed DateTimeZone) and the parameter instantLocal; no field read, no write-back",
 "facade": {"file": DTZ, "class": "org.joda.time.DateTimeZone", "method": "getOffsetFromLocal", "near_line": 880},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestDateTimeZoneCutover.java",
             "test_class": "org.joda.time.TestDateTimeZoneCutover",
             "test_method": "test_getOffsetFromLocal_Moscow_Autumn"},
 "expected_signature": "expected:<...10-28T02:59:59.999+0[4]:00> but was:<...10-28T02:59:59.999+0[3]:00>",
 "gold": {"method": "wallOffsetAt", "text": GOLD_TEXT,
          "fault": {"old": "            int offsetBefore = zone.getOffset(transition);\n"
                           "            transition++;\n"
                           "            if (instant - transition < offsetBefore - offset) {",
                    "new": "            int offsetBefore = zone.getOffset(transition);\n"
                           "            if (instant - transition < offsetBefore - offset) {"}},
 "chain": {
   "facade_body": "return org.joda.time.format.DateTimeFormatterBuilder.localOffsetOf(this, instantLocal);",
   "lie": "The offset is computed as the standard offset of the zone at the local instant plus the daylight saving "
          "amount that applies at the instant this gives.",
   "hops": [
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "localOffsetOf",
      "imports": ["org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP1},
     {"file": DTZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "wallOffsetFrom",
      "imports": ["org.joda.time.format.PeriodFormatterBuilder"], "text": HOP2},
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "settleLocalOffset",
      "imports": ["org.joda.time.DateTime", "org.joda.time.DateTimeZone"], "text": HOP3},
     {"file": DT, "class": "org.joda.time.DateTime", "method": "localOffsetAt", "imports": [], "text": HOP4},
     {"file": PER, "class": "org.joda.time.Period", "method": "wallOffsetAt", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.DateTimeZone::adjustOffset",
              "org.joda.time.tz.ZoneInfoCompiler::test",
              "org.joda.time.tz.DateTimeZoneBuilder.PrecalculatedZone::previousTransition"],
 "ownership_reason": "Only the gold sees the zone's previous transition and the offset in force before it; hops 1 and 2 compute the "
                     "two estimates of the offset, hop 3 decides only when the estimates differ, and hop 4 only by the sign of the "
                     "offset. For the trigger the estimates agree (+03:00 at 23:59:59.999Z) and the offset is positive, so the "
                     "result is the gold's alone, and once an offset is returned no caller can tell whether the earlier or the "
                     "later instant of a repeated local time was meant. The gold's javadoc promises, during an overlap where a "
                     "local time occurs twice, the offset of the earlier instant; 02:59:59.999 occurs twice in Europe/Moscow on "
                     "2007-10-28 (22:59:59.999Z at +04:00 and 23:59:59.999Z at +03:00). The convention is pinned outside the gold: "
                     "the facade's own javadoc (during a DST overlap the earlier instant); previousTransition of DateTimeZoneBuilder's "
                     "precalculated and DST zones returns the transition minus one, which ZoneInfoCompiler.test verifies "
                     "(trans - 1 != millis is reported as an error) and TestBuilder testReverseTransitions asserts (each result is the "
                     "next transition minus one and carries the earlier offset); DateTimeZone.adjustOffset treats an overlap as the "
                     "range from the transition instant given by nextTransition to transition + diff, end exclusive; the overlap tests "
                     "test_getOffsetFromLocal_Moscow_Autumn_overlap_mins, test_DateTime_constructor_Moscow_Autumn and "
                     "testDateTimeCreation_athens pass.",
 "ownership_tests": ["org.joda.time.TestDateTimeZoneCutover::test_getOffsetFromLocal_Moscow_Autumn_overlap_mins",
                     "org.joda.time.TestDateTimeZoneCutover::test_DateTime_constructor_Moscow_Autumn",
                     "org.joda.time.TestDateTimeZoneCutover::testDateTimeCreation_athens",
                     "org.joda.time.tz.TestBuilder::testReverseTransitions"],
 "compensating": {
   "chain": [
     {"file": DT, "old": "return Period.wallOffsetAt(zone, instant, offset);",
      "new": "return Period.wallOffsetAt(zone, instant - 1, offset);",
      "why": "hop 4 passes the instant one millisecond earlier"},
     {"file": DT, "old": "if (offset < 0) {\n            return offset;\n        }\n        return Period.wallOffsetAt",
      "new": "if (offset <= 0) {\n            return offset;\n        }\n        return Period.wallOffsetAt",
      "why": "hop 4 also returns a zero offset as it is"},
     {"file": DTZB, "old": "zone.getOffset(instantAdjusted));",
      "new": "zone.getOffset(instantAdjusted + 1));",
      "why": "hop 2 takes the second estimate one millisecond after the adjusted instant"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are hosts_hop_order of the task record, in that order, none substituted; mr_lib preview for seed "
               "8295 and target org/joda/time/DateTimeZone.java draws the same five: format.DateTimeFormatterBuilder (hop 1, 2829 "
               "lines), tz.DateTimeZoneBuilder (hop 2, 1728), format.PeriodFormatterBuilder (hop 3, 1868), DateTime (hop 4, 2298), "
               "Period (hop 5, gold, 1574; the smallest host). All five are public concrete top-level classes in which a static "
               "method compiles; none is the facade's class. Anchors (stageB_lib.pick_insertion_anchor via pick_anchor, seed 8295 + "
               "100 + i, as mr3_spec.py inserts them; preview line numbers on the pristine files): hop 1 after appendFractionOfHour "
               "(line 594, seed 8395), hop 2 after addCutover (260, 8396), hop 3 after maximumParsedDigits (258, 8397), hop 4 after "
               "parse (145, 8398), hop 5 after fieldDifference (276, 8399); all in the outer class. The facade calls hop 1 by its "
               "fully-qualified name; hops 1-3 import the next host (and hop 3 DateTimeZone); DateTime and Period share the "
               "package of DateTimeZone. Facade reuse: the same method is the allowed instance facade of Time-9__i (recorded).",
}
