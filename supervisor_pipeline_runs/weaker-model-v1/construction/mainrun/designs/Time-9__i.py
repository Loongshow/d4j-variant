"""Main run Time-9__i (cell C10i, batch 7, the paired static/instance bridge: the C10 recipe with an INSTANCE-method facade, on the
fixed checkout of Defects4J Time-9; the real bug modified DateTimeZone, the facade's class). Paired static instance: MR-Time-9
(batch 5, static facade DateTimeZone.forOffsetMillis, excluded here; none of its files was opened).

Facade: DateTimeZone.getOffsetFromLocal(long) (allowed target, BATCH7_PREREGISTRATION.md row 207; no facade reuse recorded for this
task). It is a public, non-final, non-static method of the abstract class DateTimeZone; FixedDateTimeZone overrides it, every other
zone (CachedDateTimeZone, DateTimeZoneBuilder's PrecalculatedZone and DSTZone, the tests' MockZone) runs it. The two other allowed
targets were not usable: getOffset(ReadableInstant) is a five-line null default plus one call (no decision to split), and
getMillisKeepLocal is a null default, an identity short cut and two public conversions, whose identity short cut is redundant
(dropping it changes no result), so no omission there violates anything.
facade_variant: V2 (receiver as parameter). state_passed: `this` (typed DateTimeZone) and the parameter instantLocal are handed to
hop 1; there is no field read and no write-back. The hops call only the zone's public methods getOffset(long), nextTransition(long)
and previousTransition(long). No visibility is widened, no type is added, the facade's signature, modifiers and throws are unchanged,
and no test is edited.
Original computation of the facade: a first estimate offsetLocal = getOffset(instantLocal); a second estimate offsetAdjusted =
getOffset(instantLocal - offsetLocal); when offsetLocal < offsetAdjusted and nextTransition differs at the two estimated UTC instants
(the local time is in a gap of a zone where the second estimate would put the instant before the gap) the first estimate; when the
estimates agree on a non-negative offset and the instant lies within the overlap after the previous transition (instantAdjusted -
prev <= offsetPrev - offsetLocal, with prev = previousTransition(instantAdjusted), the last millisecond before that transition, and
offsetPrev the offset there) the earlier offset offsetPrev; otherwise the second estimate.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Time-9-probe/w of the fixture, the
first statement of getOffsetFromLocal was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the wrapper keeps
the rest of the body reachable for javac); clean build (target removed). `defects4j test -t
org.joda.time.TestDateTimeZoneCutover::test_getOffsetFromLocal_NewYork_Spring`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at DateTimeZone.getOffsetFromLocal(DateTimeZone.java:888) called from TestDateTimeZoneCutover.doTest_getOffsetFromLocal
(TestDateTimeZoneCutover.java:1335). Full suite with the probe: 745 failing tests, all with PROBE-REACHED (direct calls in
TestDateTimeZone and TestDateTimeZoneCutover, and every construction of a DateTime from fields in a zone with transitions through
ZonedChronology.localToUTC). Baseline full suite on the fixture: 3970 tests, 0 failing. The facade is reached by existing tests.

Hosts (host_mode = "1500"; hosts_hop_order of the task record, the paired static instance's hosts, used in that order; none
substituted):
  hop 1 tz.DateTimeZoneBuilder        1728 lines  wallOffsetOfLocal       state step: the first estimate, zone.getOffset(instantLocal)
  hop 2 format.PeriodFormatterBuilder 1874 lines  offsetForLocalInstant   pass-through
  hop 3 Period                        1639 lines  localToUTCOffset        state step: the second estimate,
                                                                          zone.getOffset(instantLocal - offsetLocal)
  hop 4 format.ISODateTimeFormat      1711 lines  localInstantOffset      pass-through
  hop 5 LocalTime                     1623 lines  localMillisOffset       GOLD: the decision between the two estimates and the
                                                                          offset at the previous transition (the gap rule and the
                                                                          overlap rule)
Host newline counts 1728, 1874, 1639, 1711, 1623; the smallest host has 1623 lines (LocalTime, the gold host).
The correct configuration returns the original offset for every input: the same two estimates, the same gap test (offsetLocal <
offsetAdjusted is the original (offsetLocal - offsetAdjusted) < 0, which cannot overflow for zone offsets below one day), the same
non-negative overlap test, and the overlap window instantAdjusted - (prev + 1) < offsetPrev - offsetLocal, which over the integers is
the original instantAdjusted - prev <= offsetPrev - offsetLocal. The original nesting `if (!=) { if (<) {..} } else if (>= 0)` is
written flat as `if (<) {..} else if (== && >= 0) {..}`, which selects the same branch for every pair of estimates.

Fault (one-line omission in the gold's overlap decision): the line `transition++;`, the step from the instant previousTransition
returns (the last millisecond before the transition, by its implementations and its callers) to the transition itself, is dropped.
The overlap window then ends one millisecond early: the last millisecond of an overlap gets the later offset. Trigger: the EXISTING
test TestDateTimeZoneCutover::test_getOffsetFromLocal_Moscow_Autumn (Europe/Moscow, 2007-10-28, 03:00 +04:00 back to 02:00 +03:00, so
02:00-02:59:59.999 local occurs twice); its assertions for 00:00 to 02:59:59.998 still hold, and the one at line 899,
doTest_getOffsetFromLocal(10, 28, 2,59,59,999, "2007-10-28T02:59:59.999+04:00", ZONE_MOSCOW), fails with
"2007-10-28T02:59:59.999+03:00 expected:<...10-28T02:59:59.999+0[4]:00> but was:<...10-28T02:59:59.999+0[3]:00>". It is the only test
that newly fails: it is the only test that converts the last millisecond of an overlap from local time (whole-minute overlap tests
such as test_getOffsetFromLocal_Moscow_Autumn_overlap_mins and the DateTime constructor tests stay inside the window), and the
variant equals the original with the window test written as `<` instead of `<=`, which was run on the full suite in a scratch copy
(1 failing test: the trigger).

The gold's javadoc states the idiomatic contract (a local time that occurs twice, in an overlap, gets the offset of its earlier
instant) and is silent on the step from the returned instant to the transition; 02:59:59.999 occurs twice that day in Moscow
(at 22:59:59.999Z with +04:00 and at 23:59:59.999Z with +03:00), so the variant violates that contract on the trigger input. The
convention is pinned outside the gold: the facade's own javadoc ("During a DST overlap (where the local time is ambiguous) this method
will return the earlier instant"); DateTimeZone.adjustOffset, whose overlap window [transition - diff, transition + diff) is built
from nextTransition (the transition itself) and includes the last millisecond of the overlap (TestDateTimeZoneCutover
testBug3192457_adjustOffset passes); DateTime.Property.withMaximumValue, which uses previousTransition as "the last instant before
the gap" (TestDateTime_Properties testPropertyWithMaximumValueMillisOfDayDSTGap: 1926-04-17T22:59:59.999Z, passes);
DateTimeZoneBuilder.PrecalculatedZone.previousTransition, which returns `prev - 1`, and ZoneInfoCompiler.test, which checks
`trans - 1` against every previousTransition of a compiled zone; test_getOffsetFromLocal_Moscow_Autumn_overlap_mins pins the earlier
offset for the whole overlap.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold.
 Correct gold, and rewrites made before choosing the omission: the original's sign and order asymmetries (a gap test only when the
 first estimate is the smaller, an overlap test only for a non-negative agreed offset, the default for the remaining case) could read
 as a half-treated pair (T3) or a named class handled in part; the gold's javadoc therefore states each case and what it gets (the
 second estimate already places the instant after a gap unless it is the larger one; it already gives the earlier instant of an
 overlap unless both estimates agree on a non-negative offset; otherwise the second estimate), and the nested `if (!=) { if (<) }`
 was flattened so that no branch is empty. The original's comments were not carried over. All locals are plain (non-final), so the
 one local that the correct gold reassigns does not stand out in the variant.
  T1 absent: zone answers all three transition and offset reads; instantLocal gives both estimated instants; offsetLocal and
     offsetAdjusted decide every branch and are returned.
  T2 absent: instantAdjusted, nextLocal, nextAdjusted, transition and offsetEarlier are all read in a live decision or returned;
     transition is advanced before the window test; no literal-initialised local, no loop; each branch returns a different value.
  T3 absent: both rules named in the text (gap, overlap) are treated, each with the case where the second estimate already suffices
     stated; the window has both ends tested (transition < instantAdjusted, instantAdjusted - transition < ...).
  T4 absent: every phrase (after the gap, earlier instant, larger one, not negative, offset at its previous transition, otherwise the
     second estimate) is met by a line of the body.
 Variant gold (javadoc, signature, `instantAdjusted`; `if (offsetLocal < offsetAdjusted)` with the two nextTransition reads and
 `return offsetLocal`; `else if (offsetLocal == offsetAdjusted && offsetLocal >= 0)` with `transition = zone.previousTransition(...)`,
 `if (transition < instantAdjusted)`, `offsetEarlier = zone.getOffset(transition)`, `if (instantAdjusted - transition < offsetEarlier
 - offsetLocal) return offsetEarlier;`; `return offsetAdjusted`):
  T1 absent: zone is read by nextTransition, previousTransition and getOffset; instantLocal gives instantAdjusted and the second
     estimated instant; offsetLocal and offsetAdjusted decide the branches and are returned; none is only argument-checked.
  T2 absent: transition is initialised from a call (not a literal), there is no loop, and it is read by the guard, by getOffset and by
     the window test; offsetEarlier is compared and returned; nextLocal and nextAdjusted decide a return; the three returns give three
     different values; no branch is empty or duplicates another.
  T3 absent: the gap rule and the overlap rule are both treated; the cases the javadoc assigns to the second estimate (the smaller
     second estimate, a negative agreed offset) are stated in the text and get that treatment; the pair of estimates is read and
     compared in full; both ends of the overlap window are tested; no format, enum or type code is named.
  T4 absent: 'gets the offset that places its instant after the gap' (return offsetLocal when the zone changes offset between the two
     estimated instants), 'the second estimate does so unless it is the larger one' (that branch is entered only when offsetLocal <
     offsetAdjusted), 'gets the offset of its earlier instant ... unless the two estimates agree on an offset that is not negative'
     (the else-if condition), 'the offset the zone has at its previous transition is then used' (getOffset(previousTransition(..)) is
     returned), '@return the millisecond offset to subtract from local time' (every return is one of the offsets); '@param zone ...
     not null' is a caller precondition; identifiers (instantAdjusted, nextLocal, nextAdjusted, transition, offsetEarlier) name
     nothing the body does not meet.

Single owner: only the gold reads the zone's transitions around the estimated instant and decides between the two estimates and the
earlier offset; hops 1 and 3 each read one offset of the zone (the two estimates) and hops 2 and 4 pass the values along. The result
is a single int, from which no caller can tell which rule produced it. Declared alternatives (G9): hop 4 hands the gold the local
instant one millisecond earlier (the first millisecond of the overlap, 02:00, then loses the earlier offset); hop 3 takes the second
estimate one millisecond earlier; hop 1 takes the first estimate one millisecond earlier (neither changes the estimates at
02:59:59.999). Each leaves the trigger failing.
Recorded bypasses (edits that replace part of the gold's result with another implementation, not repairs of the chain):
 B-0 the facade's original body (or the same computation inlined at any hop), which makes the chain, including the gold, dead.
 B-1 hop 4 re-implements the overlap rule with `<=` in front of the call to the gold (when the estimates agree on a non-negative
     offset and instantLocal - offsetLocal - previousTransition(..) <= getOffset(previousTransition(..)) - offsetLocal, return that
     offset; else call the gold): a second implementation of the gold's overlap decision. Checked on the variant in a scratch copy:
     full suite 0 failing tests.
Further one-line edits at hop 4 checked on the variant (full suite), none of which absorbs the fault: the larger of the gold's
results for the local instant and for one millisecond earlier (4 failing tests, the New York and Turk gap tests); one millisecond
earlier only when the estimates agree (3 failing, the trigger among them); one millisecond later (the trigger fails); the larger of
the gold's results for the local instant and for one millisecond later with fresh estimates (the trigger fails).

Lie: the facade's javadoc claims that offsets already found are kept in a cache held by the zone, keyed by the local instant, and
returned without consulting the zone's rules again; the chain caches nothing and reads the zone's offsets and transitions on every
call. It names neither overlaps, transitions, milliseconds nor any hop."""

DTZ = "src/main/java/org/joda/time/DateTimeZone.java"
DZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
PER = "src/main/java/org/joda/time/Period.java"
IDF = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"
LT = "src/main/java/org/joda/time/LocalTime.java"

GOLD_TEXT = '''/**
 * Chooses the millisecond offset to subtract from a local instant of a
 * zone to get the UTC instant, from two estimates of that offset.
 * <p>
 * The first estimate is the offset of the zone at the local instant, read
 * as a UTC instant, and the second is the offset at the local instant less
 * the first estimate. The second estimate is the result, with two
 * exceptions.
 * <ul>
 * <li>A local time in a gap gets the offset that places its instant after
 * the gap. The second estimate does so unless it is the larger one; the
 * first estimate is then used when the zone changes offset between the two
 * estimated instants.</li>
 * <li>A local time that occurs twice, in an overlap, gets the offset of its
 * earlier instant. The second estimate does so unless the two estimates
 * agree on an offset that is not negative; the offset the zone has at its
 * previous transition is then used.</li>
 * </ul>
 *
 * @param zone  the time zone, not null
 * @param instantLocal  the millisecond instant, relative to the zone
 * @param offsetLocal  the first estimate of the offset
 * @param offsetAdjusted  the second estimate of the offset
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int localMillisOffset(DateTimeZone zone, long instantLocal, int offsetLocal, int offsetAdjusted) {
    long instantAdjusted = instantLocal - offsetLocal;
    if (offsetLocal < offsetAdjusted) {
        long nextLocal = zone.nextTransition(instantAdjusted);
        long nextAdjusted = zone.nextTransition(instantLocal - offsetAdjusted);
        if (nextLocal != nextAdjusted) {
            return offsetLocal;
        }
    } else if (offsetLocal == offsetAdjusted && offsetLocal >= 0) {
        long transition = zone.previousTransition(instantAdjusted);
        if (transition < instantAdjusted) {
            int offsetEarlier = zone.getOffset(transition);
            transition++;
            if (instantAdjusted - transition < offsetEarlier - offsetLocal) {
                return offsetEarlier;
            }
        }
    }
    return offsetAdjusted;
}'''

HOP1 = '''/**
 * Gets the millisecond offset to subtract from a local instant of a zone
 * to get the UTC instant.
 * <p>
 * The first estimate of the offset is the offset of the zone at the local
 * instant, read as a UTC instant.
 *
 * @param zone  the time zone, not null
 * @param instantLocal  the millisecond instant, relative to the zone
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int wallOffsetOfLocal(DateTimeZone zone, long instantLocal) {
    return PeriodFormatterBuilder.offsetForLocalInstant(zone, instantLocal, zone.getOffset(instantLocal));
}'''

HOP2 = '''/**
 * Gets the millisecond offset to subtract from a local instant of a zone
 * to get the UTC instant, given a first estimate of that offset.
 *
 * @param zone  the time zone, not null
 * @param instantLocal  the millisecond instant, relative to the zone
 * @param offsetLocal  the first estimate of the offset
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int offsetForLocalInstant(DateTimeZone zone, long instantLocal, int offsetLocal) {
    return Period.localToUTCOffset(zone, instantLocal, offsetLocal);
}'''

HOP3 = '''/**
 * Gets the millisecond offset to subtract from a local instant of a zone
 * to get the UTC instant, given a first estimate of that offset.
 * <p>
 * The second estimate of the offset is the offset of the zone at the local
 * instant less the first estimate.
 *
 * @param zone  the time zone, not null
 * @param instantLocal  the millisecond instant, relative to the zone
 * @param offsetLocal  the first estimate of the offset
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int localToUTCOffset(DateTimeZone zone, long instantLocal, int offsetLocal) {
    return ISODateTimeFormat.localInstantOffset(zone, instantLocal, offsetLocal, zone.getOffset(instantLocal - offsetLocal));
}'''

HOP4 = '''/**
 * Gets the millisecond offset to subtract from a local instant of a zone
 * to get the UTC instant, from two estimates of that offset.
 *
 * @param zone  the time zone, not null
 * @param instantLocal  the millisecond instant, relative to the zone
 * @param offsetLocal  the first estimate of the offset
 * @param offsetAdjusted  the second estimate of the offset
 * @return the millisecond offset to subtract from local time to get UTC time
 */
public static int localInstantOffset(DateTimeZone zone, long instantLocal, int offsetLocal, int offsetAdjusted) {
    return LocalTime.localMillisOffset(zone, instantLocal, offsetLocal, offsetAdjusted);
}'''

DESIGN = {
 "instance": "Time-9", "project": "Time", "bug_id": 9, "seed": 3267,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": DTZ, "class": "org.joda.time.DateTimeZone", "method": "getOffsetFromLocal", "near_line": 887},
 "facade_variant": "V2",
 "state_passed": "receiver `this` (as DateTimeZone) and the parameter instantLocal to hop 1; no field read, no write-back",
 "host_mode": "1500",
 "host_lines": [1728, 1874, 1639, 1711, 1623],
 "reachability_probe": "getOffsetFromLocal first statement `if (true) { throw new IllegalStateException(\"PROBE-REACHED\"); }` in "
                       "/private/tmp/d4j-mi-Time-9-probe/w (clean build): TestDateTimeZoneCutover::test_getOffsetFromLocal_NewYork_Spring "
                       "fails with PROBE-REACHED at DateTimeZone.getOffsetFromLocal(DateTimeZone.java:888); full suite 745 failing "
                       "tests, all PROBE-REACHED (baseline 0 of 3970)",
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestDateTimeZoneCutover.java",
             "test_class": "org.joda.time.TestDateTimeZoneCutover",
             "test_method": "test_getOffsetFromLocal_Moscow_Autumn"},
 "expected_signature": "expected:<...10-28T02:59:59.999+0[4]:00> but was:<...10-28T02:59:59.999+0[3]:00>",
 "gold": {"method": "localMillisOffset", "text": GOLD_TEXT,
          "fault": {"old": "                int offsetEarlier = zone.getOffset(transition);\n"
                           "                transition++;\n"
                           "                if (instantAdjusted - transition < offsetEarlier - offsetLocal) {",
                    "new": "                int offsetEarlier = zone.getOffset(transition);\n"
                           "                if (instantAdjusted - transition < offsetEarlier - offsetLocal) {"}},
 "chain": {
   "facade_body": "return org.joda.time.tz.DateTimeZoneBuilder.wallOffsetOfLocal(this, instantLocal);",
   "lie": "Offsets already found are kept in a cache held by the zone, keyed by the local instant, and a cached offset is "
          "returned without consulting the rules of the zone again.",
   "hops": [
     {"file": DZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "wallOffsetOfLocal",
      "imports": ["org.joda.time.format.PeriodFormatterBuilder"], "text": HOP1},
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "offsetForLocalInstant",
      "imports": ["org.joda.time.DateTimeZone", "org.joda.time.Period"], "text": HOP2},
     {"file": PER, "class": "org.joda.time.Period", "method": "localToUTCOffset",
      "imports": ["org.joda.time.format.ISODateTimeFormat"], "text": HOP3},
     {"file": IDF, "class": "org.joda.time.format.ISODateTimeFormat", "method": "localInstantOffset",
      "imports": ["org.joda.time.DateTimeZone", "org.joda.time.LocalTime"], "text": HOP4},
     {"file": LT, "class": "org.joda.time.LocalTime", "method": "localMillisOffset", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.DateTimeZone::adjustOffset",
              "org.joda.time.DateTime.Property::withMaximumValue",
              "org.joda.time.tz.DateTimeZoneBuilder.PrecalculatedZone::previousTransition",
              "org.joda.time.tz.ZoneInfoCompiler::test"],
 "ownership_reason": "Only the gold reads the zone's transitions around the estimated UTC instant and decides between the two "
                     "estimates of the offset and the offset at the previous transition: hops 1 and 3 each read one offset of the "
                     "zone (the first estimate at the local instant, the second at the local instant less the first) and hops 2 "
                     "and 4 pass the values along. The chain returns one int, from which no caller can tell which rule produced "
                     "it. The gold's javadoc promises that a local time that occurs twice, in an overlap, gets the offset of its "
                     "earlier instant. The convention is pinned outside the gold: the facade's own javadoc ('During a DST overlap "
                     "(where the local time is ambiguous) this method will return the earlier instant'); DateTimeZone.adjustOffset, "
                     "whose overlap window [transition - diff, transition + diff) is built from nextTransition and includes the "
                     "last millisecond of the overlap (TestDateTimeZoneCutover testBug3192457_adjustOffset); "
                     "DateTime.Property.withMaximumValue, which takes previousTransition as the last instant before a gap "
                     "(TestDateTime_Properties testPropertyWithMaximumValueMillisOfDayDSTGap expects 1926-04-17T22:59:59.999Z); "
                     "DateTimeZoneBuilder.PrecalculatedZone.previousTransition returns prev - 1 and ZoneInfoCompiler.test checks "
                     "trans - 1 against previousTransition; test_getOffsetFromLocal_Moscow_Autumn_overlap_mins and "
                     "test_DateTime_constructor_Moscow_Autumn pin the earlier offset inside the Moscow overlap.",
 "ownership_tests": ["org.joda.time.TestDateTimeZoneCutover::test_getOffsetFromLocal_Moscow_Autumn_overlap_mins",
                     "org.joda.time.TestDateTimeZoneCutover::testBug3192457_adjustOffset",
                     "org.joda.time.TestDateTime_Properties::testPropertyWithMaximumValueMillisOfDayDSTGap",
                     "org.joda.time.TestDateTimeZoneCutover::test_DateTime_constructor_Moscow_Autumn"],
 "compensating": {
   "chain": [
     {"file": IDF, "old": "return LocalTime.localMillisOffset(zone, instantLocal, offsetLocal, offsetAdjusted);",
      "new": "return LocalTime.localMillisOffset(zone, instantLocal - 1, offsetLocal, offsetAdjusted);",
      "why": "hop 4 hands the gold the local instant one millisecond earlier"},
     {"file": PER, "old": "return ISODateTimeFormat.localInstantOffset(zone, instantLocal, offsetLocal, zone.getOffset(instantLocal - offsetLocal));",
      "new": "return ISODateTimeFormat.localInstantOffset(zone, instantLocal, offsetLocal, zone.getOffset(instantLocal - offsetLocal - 1));",
      "why": "hop 3 takes the second estimate one millisecond earlier"},
     {"file": DZB, "old": "return PeriodFormatterBuilder.offsetForLocalInstant(zone, instantLocal, zone.getOffset(instantLocal));",
      "new": "return PeriodFormatterBuilder.offsetForLocalInstant(zone, instantLocal, zone.getOffset(instantLocal - 1));",
      "why": "hop 1 takes the first estimate one millisecond earlier"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are hosts_hop_order of the task record (the paired static instance's hosts), in that order, "
               "none substituted: tz.DateTimeZoneBuilder (hop 1, 1728 lines), format.PeriodFormatterBuilder (hop 2, 1874), "
               "Period (hop 3, 1639), format.ISODateTimeFormat (hop 4, 1711), LocalTime (hop 5, gold, 1623; the smallest host). "
               "All five are public concrete top-level classes in which a static method compiles. Anchors from "
               "stageB_lib.pick_insertion_anchor (pick_anchor, as mr3_spec.py inserts them) with seed 3267 + 100 + i: hop 1 after "
               "`setFixedSavings` (pristine line idx 278, seed 3367), hop 2 after `appendSeparatorIfFieldsBefore` (673, 3368), "
               "hop 3 after `toStandardDuration` (1537, 3369), hop 4 after `weekDate` (1043, 3370), hop 5 after `getMillisOfDay` "
               "(1137, 3371); all in the outer class (4-space indent). mr_lib preview was not used to draw hosts. The facade "
               "calls hop 1 by its fully-qualified name; each hop imports the next host (and DateTimeZone where the host is "
               "outside org.joda.time and does not import it yet).",
}
