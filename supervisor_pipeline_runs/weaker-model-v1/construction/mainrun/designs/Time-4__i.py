"""Main run Time-4__i (cell C10i, batch 8: an instance-method facade on a bug with no static facade; the C10 recipe on the fixed
checkout of Defects4J Time-4, fixed revision 3ba9ba799b3261b7332a467a88be142c83b298fd; the real bug modified org.joda.time.Partial,
the facade's class). No static pair exists (static_facade_status: none, pool v2 no_tested_static).

Facade: Partial.isMatch(ReadableInstant) (instance method; allowed targets Partial.isMatch / Partial.isMatch, BATCH8_PREREGISTRATION.md
row 306; facade_planned_by null, no facade reuse). The ReadableInstant overload was chosen over isMatch(ReadablePartial): it carries
the larger computation (the instant's milliseconds and chronology are resolved, null meaning now in the default zone, and each field
of the partial is read from the instant in that chronology), and the reading of a field of an instant in the instant's time zone is a
step of its own that one test catches. isMatch(ReadablePartial) stays intact; its computation is a plain partial.get per field.
Original computation: millis = DateTimeUtils.getInstantMillis(instant); chrono = DateTimeUtils.getInstantChronology(instant); for each
i, iTypes[i].getField(chrono).get(millis) is compared with iValues[i]; false at the first difference, else true.

facade_variant: V1 (state as parameters). state_passed: the ReadableInstant argument and the private fields iTypes
(DateTimeFieldType[]) and iValues (int[]), handed to hop 1; no field is written, no write-back. The facade body is one call to hop 1
(the original had no argument guard: null means now). No visibility is widened, no type is added, no signature, modifier, override or
throws clause changes, no reflection, no test edit. The original body calls no private method, so V4 does not apply.

Redistribution: hop 1 resolves the instant into its milliseconds and its chronology (DateTimeUtils, null meaning now in ISO in the
default zone); hops 2-4 pass the arrays, the milliseconds and the chronology along; the gold (hop 5) does the per-field core: it
evaluates the instant in its chronology the way LocalTime/LocalDate/LocalDateTime(long, Chronology) do (local milliseconds via
getMillisKeepLocal(DateTimeZone.UTC, instant), then the UTC form of the chronology) and compares each field with its expected value,
stopping at the first difference. For every chronology this equals the original reading (a zoned field reads
convertUTCToLocal(instant) in the UTC field, ZonedChronology.ZonedDateTimeField.get).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Time-4-probe of the fixture, the first statement of
each isMatch overload was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the ReadablePartial one with the
message "PROBE-REACHED-P"); defects4j compile OK; `defects4j test -t org.joda.time.TestPartial_Match::testIsMatch_Instant`: 1 failing
test, java.lang.IllegalStateException: PROBE-REACHED at org.joda.time.Partial.isMatch(Partial.java:656);
`... ::testIsMatch_Partial`: 1 failing test, PROBE-REACHED-P at Partial.isMatch(Partial.java:681). Both facades are reached directly.

Hosts (host_mode = "1500"; `mr_lib.py preview Time-4 org/joda/time/Partial.java 5`, seed 3459, used in draw order, none substituted):
  hop 1 format.DateTimeFormatterBuilder 2871 lines  matchesInstantFields  resolves the instant (milliseconds, chronology)
  hop 2 tz.DateTimeZoneBuilder          1731 lines  fieldValuesMatch      pass-through
  hop 3 LocalDate                       2116 lines  matchesFieldValues    pass-through
  hop 4 format.PeriodFormatterBuilder   1874 lines  matchFieldValues      pass-through
  hop 5 LocalTime                       1623 lines  hasFieldValues        GOLD: per-field reading of the instant and comparison
Host sizes 2871, 1731, 2116, 1874, 1623; the smallest host is LocalTime (1623 lines, the gold host).

Fault (one-line omission of a special-case step in the gold): the line `instant = chronology.getZone().getMillisKeepLocal(
DateTimeZone.UTC, instant);` is dropped, so the fields are read from the UTC form of the chronology at the instant's UTC milliseconds,
i.e. in UTC instead of in the instant's time zone. The gold then reads as the ordinary routine "read each field and compare".
Trigger: the EXISTING test org.joda.time.TestPartial_Match::testIsMatch_Instant (default zone Europe/London, set in setUp); its first
assertion, assertEquals(true, test.isMatch(new DateTime(2005, 7, 5, 0, 0, 0, 0))) on the partial year 2005 / month 7 / day-of-week 2,
fails with expected:<true> but was:<false> (the instant is 2005-07-04T23:00Z; in UTC its day of week is Monday, 1). It is the only test
that calls Partial.isMatch(ReadableInstant) (grep over src/test), the chain's methods are new, and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the instant "has the given value in each of the given fields"; @param chronology "the
chronology of the instant") and is silent on the time zone. The instant's fields in its chronology (ISO, Europe/London) are 2005 / 7 /
Tuesday, so the variant's false violates that contract on the trigger input. The convention is pinned outside the gold: the intact
constructors LocalTime(long, Chronology), LocalDate(long, Chronology) and LocalDateTime(long, Chronology) do the same step
(`chronology.getZone().getMillisKeepLocal(DateTimeZone.UTC, instant)` then `chronology.withUTC()`), and ZonedChronology's fields read
convertUTCToLocal(instant); passing tests TestLocalTime_Constructors::testConstructor_long_DateTimeZone, TestLocalDate_Constructors::
testConstructor_long1_DateTimeZone and TestLocalDateTime_Constructors::testConstructor_long1_DateTimeZone pin that the fields of an
instant are those of its zone.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: types bounds the loop and names the fields; values gives each expected value; instant is read to compute the local
     milliseconds that every field reads; chronology gives the zone and the calendar system.
  T2 absent: instant and chronology are reassigned and read in the loop; i is the loop cursor; the if returns false, the loop end
     returns true; no literal-initialised local.
  T3 absent: no closed set is handled in part (every field of types is compared; no enumeration); the gold names no class.
  T4 absent: 'has the given value in each of the given fields', 'checked in order', 'stops at the first field whose value differs'
     are met by the loop and its return false; @param clauses are caller preconditions.
 Variant gold (javadoc, signature, `chronology = chronology.withUTC();`, the loop, return false / return true):
  T1 absent: types, values, instant (the milliseconds every field reads) and chronology (its calendar system, via withUTC) each
     change the result; none is only argument-checked.
  T2 absent: chronology is reassigned and read in the loop; i advances; instant is read in the loop; the if and the final return
     have different effects; no local is frozen or dead.
  T3 absent: no set of siblings is treated (no zone or offset treatment at all: 'No member handled'); each field of types gets the
     same comparison; no class is named in the gold's text.
  T4 absent: no phrase names a zone, an offset or a value class; 'has the given value in each of the given fields' is a general
     description addressed by the loop; 'the milliseconds from 1970-01-01T00:00:00Z' and 'the chronology of the instant' are caller
     preconditions on parameters; identifiers (types, values, instant, chronology, i) name nothing the body does not meet.

Single owner: only the gold reads a field of the instant; hop 1 only resolves the instant into its milliseconds from 1970-01-01T00:00:00Z
and its chronology, and hops 2-4 pass them on unchanged. Every hop and the gold document `instant` as the milliseconds from
1970-01-01T00:00:00Z and `chronology` as the chronology of the instant, so the evaluation in the instant's zone can appear above the gold
only by passing something that is not the instant. Declared alternatives (G9): hop 1 passes the UTC form of the chronology; hop 2
passes the ISO chronology in the instant's zone; hop 4 passes the chronology in the default zone. None makes the trigger pass (the
variant gold uses only the calendar system of the chronology).
Recorded bypasses:
 B-0 the facade (its original body) reads the fields itself, discarding the chain including the gold.
 B-1 a hop above the gold passes local milliseconds (chronology.getZone().getMillisKeepLocal(DateTimeZone.UTC, instant) or
     convertUTCToLocal) instead of the instant: this is a second implementation of the gold's step and breaks the documented
     parameter of every hop below it and of the gold ('the milliseconds from 1970-01-01T00:00:00Z').

Lie: the facade's javadoc claims the values of this partial are set onto the instant one field at a time and that a match occurs when
the resulting instant equals the original one; no step of the chain sets a value onto an instant (each field is read and compared). It
names neither the time zone nor any hop."""

PARTIAL = "src/main/java/org/joda/time/Partial.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"
DTZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
LD = "src/main/java/org/joda/time/LocalDate.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
LT = "src/main/java/org/joda/time/LocalTime.java"

GOLD_TEXT = '''/**
 * Checks whether an instant has the given value in each of the given
 * fields.
 * <p>
 * The fields are checked in order, and the check stops at the first
 * field whose value differs.
 *
 * @param types  the types of the fields to check, not null
 * @param values  the value expected for each field, not null
 * @param instant  the milliseconds from 1970-01-01T00:00:00Z
 * @param chronology  the chronology of the instant, not null
 * @return true if each of the fields has its expected value
 */
public static boolean hasFieldValues(DateTimeFieldType[] types, int[] values, long instant, Chronology chronology) {
    instant = chronology.getZone().getMillisKeepLocal(DateTimeZone.UTC, instant);
    chronology = chronology.withUTC();
    for (int i = 0; i < types.length; i++) {
        if (types[i].getField(chronology).get(instant) != values[i]) {
            return false;
        }
    }
    return true;
}'''

HOP1 = '''/**
 * Checks whether an instant has the given value in each of the given
 * fields.
 *
 * @param instant  the instant to check, null means now in the default zone
 * @param types  the types of the fields to check, not null
 * @param values  the value expected for each field, not null
 * @return true if each of the fields has its expected value
 */
public static boolean matchesInstantFields(ReadableInstant instant, DateTimeFieldType[] types, int[] values) {
    long millis = DateTimeUtils.getInstantMillis(instant);
    Chronology chrono = DateTimeUtils.getInstantChronology(instant);
    return DateTimeZoneBuilder.fieldValuesMatch(types, values, millis, chrono);
}'''

HOP2 = '''/**
 * Checks whether an instant has the given value in each of the given
 * fields.
 *
 * @param types  the types of the fields to check, not null
 * @param values  the value expected for each field, not null
 * @param instant  the milliseconds from 1970-01-01T00:00:00Z
 * @param chronology  the chronology of the instant, not null
 * @return true if each of the fields has its expected value
 */
public static boolean fieldValuesMatch(DateTimeFieldType[] types, int[] values, long instant, Chronology chronology) {
    return LocalDate.matchesFieldValues(types, values, instant, chronology);
}'''

HOP3 = '''/**
 * Checks whether an instant has the given value in each of the given
 * fields.
 *
 * @param types  the types of the fields to check, not null
 * @param values  the value expected for each field, not null
 * @param instant  the milliseconds from 1970-01-01T00:00:00Z
 * @param chronology  the chronology of the instant, not null
 * @return true if each of the fields has its expected value
 */
public static boolean matchesFieldValues(DateTimeFieldType[] types, int[] values, long instant, Chronology chronology) {
    return PeriodFormatterBuilder.matchFieldValues(types, values, instant, chronology);
}'''

HOP4 = '''/**
 * Checks whether an instant has the given value in each of the given
 * fields.
 *
 * @param types  the types of the fields to check, not null
 * @param values  the value expected for each field, not null
 * @param instant  the milliseconds from 1970-01-01T00:00:00Z
 * @param chronology  the chronology of the instant, not null
 * @return true if each of the fields has its expected value
 */
public static boolean matchFieldValues(DateTimeFieldType[] types, int[] values, long instant, Chronology chronology) {
    return LocalTime.hasFieldValues(types, values, instant, chronology);
}'''

DESIGN = {
 "instance": "Time-4", "project": "Time", "bug_id": 4, "seed": 3459,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the ReadableInstant argument and the private fields iTypes (DateTimeFieldType[]) and iValues (int[]), passed to "
                 "hop 1; no field written, no write-back",
 "host_mode": "1500", "host_lines": [2871, 1731, 2116, 1874, 1623],
 "reachability_probe": "isMatch(ReadableInstant) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Time-4-probe: TestPartial_Match::testIsMatch_Instant fails with PROBE-REACHED at "
                       "Partial.isMatch(Partial.java:656); isMatch(ReadablePartial) likewise reached by testIsMatch_Partial "
                       "(Partial.java:681)",
 "facade": {"file": PARTIAL, "class": "org.joda.time.Partial", "method": "isMatch", "near_line": 655},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestPartial_Match.java",
             "test_class": "org.joda.time.TestPartial_Match", "test_method": "testIsMatch_Instant"},
 "expected_signature": "expected:<true> but was:<false>",
 "gold": {"method": "hasFieldValues", "text": GOLD_TEXT,
          "fault": {"old": "        instant = chronology.getZone().getMillisKeepLocal(DateTimeZone.UTC, instant);\n"
                           "        chronology = chronology.withUTC();\n"
                           "        for (int i = 0; i < types.length; i++) {\n",
                    "new": "        chronology = chronology.withUTC();\n"
                           "        for (int i = 0; i < types.length; i++) {\n"}},
 "chain": {
   "facade_body": "return org.joda.time.format.DateTimeFormatterBuilder.matchesInstantFields(instant, iTypes, iValues);",
   "lie": "The values of this partial are set onto the instant one field at a time, and a match occurs when the resulting "
          "instant equals the original instant.",
   "hops": [
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "matchesInstantFields",
      "imports": ["org.joda.time.ReadableInstant", "org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP1},
     {"file": DTZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "fieldValuesMatch",
      "imports": ["org.joda.time.DateTimeFieldType", "org.joda.time.LocalDate"], "text": HOP2},
     {"file": LD, "class": "org.joda.time.LocalDate", "method": "matchesFieldValues",
      "imports": ["org.joda.time.format.PeriodFormatterBuilder"], "text": HOP3},
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "matchFieldValues",
      "imports": ["org.joda.time.Chronology", "org.joda.time.DateTimeFieldType", "org.joda.time.LocalTime"], "text": HOP4},
     {"file": LT, "class": "org.joda.time.LocalTime", "method": "hasFieldValues", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.LocalTime::LocalTime",
              "org.joda.time.LocalDate::LocalDate",
              "org.joda.time.LocalDateTime::LocalDateTime"],
 "ownership_reason": "Only the gold reads a field of the instant: hop 1 resolves the instant into its milliseconds from "
                     "1970-01-01T00:00:00Z and its chronology (DateTimeUtils, null meaning now in ISO in the default zone) and "
                     "hops 2-4 pass the arrays, the milliseconds and the chronology on unchanged; every hop and the gold document "
                     "the instant as the milliseconds from 1970-01-01T00:00:00Z and the chronology as the chronology of the "
                     "instant. The gold's contract is that the instant has the given value in each field, read in the chronology "
                     "of the instant; for 2005-07-05T00:00 Europe/London (2005-07-04T23:00Z) the ISO London day of week is "
                     "Tuesday, and the variant, reading the UTC form of the chronology at the UTC milliseconds, finds Monday. "
                     "The convention is pinned outside the gold: the intact constructors LocalTime(long, Chronology), "
                     "LocalDate(long, Chronology) and LocalDateTime(long, Chronology) evaluate an instant in its chronology by "
                     "chronology.getZone().getMillisKeepLocal(DateTimeZone.UTC, instant) followed by chronology.withUTC(), and "
                     "ZonedChronology's fields read convertUTCToLocal(instant) in the UTC field; "
                     "TestLocalTime_Constructors::testConstructor_long_DateTimeZone (hour of day 1 + OFFSET_PARIS), "
                     "TestLocalDate_Constructors::testConstructor_long1_DateTimeZone and "
                     "TestLocalDateTime_Constructors::testConstructor_long1_DateTimeZone pass and pin that the fields of an "
                     "instant are those of its zone.",
 "ownership_tests": ["org.joda.time.TestLocalTime_Constructors::testConstructor_long_DateTimeZone",
                     "org.joda.time.TestLocalDate_Constructors::testConstructor_long1_DateTimeZone",
                     "org.joda.time.TestLocalDateTime_Constructors::testConstructor_long1_DateTimeZone"],
 "compensating": {
   "chain": [
     {"file": DTFB, "old": "Chronology chrono = DateTimeUtils.getInstantChronology(instant);",
      "new": "Chronology chrono = DateTimeUtils.getInstantChronology(instant).withUTC();",
      "why": "hop 1 passes the UTC form of the instant's chronology"},
     {"file": DTZB, "old": "return LocalDate.matchesFieldValues(types, values, instant, chronology);",
      "new": "return LocalDate.matchesFieldValues(types, values, instant, ISOChronology.getInstance(chronology.getZone()));",
      "why": "hop 2 passes the ISO chronology in the zone of the instant"},
     {"file": PFB, "old": "return LocalTime.hasFieldValues(types, values, instant, chronology);",
      "new": "return LocalTime.hasFieldValues(types, values, instant, chronology.withZone(org.joda.time.DateTimeZone.getDefault()));",
      "why": "hop 4 passes the chronology in the default zone"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts drawn by `mr_lib.py preview Time-4 org/joda/time/Partial.java 5` with the instance seed 3459 "
               "(Partial.java, the only allowed candidates' file, excluded), used in draw order, none substituted: "
               "format.DateTimeFormatterBuilder (hop 1, 2871 lines), tz.DateTimeZoneBuilder (hop 2, 1731), LocalDate (hop 3, "
               "2116), format.PeriodFormatterBuilder (hop 4, 1874), LocalTime (hop 5, gold, 1623; the smallest host). The draw "
               "notes that hops 3-5 relaxed the 'distinct from target package' constraint (LocalDate and LocalTime are in "
               "org.joda.time, like Partial). All five are public top-level classes (LocalDate and LocalTime are final, which "
               "does not affect a static method) in which a public static method compiles. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 3459 + 100 + i, as mr3_spec.py inserts them: hop 1 after "
               "appendFractionOfHour (seed 3559), hop 2 after writeTo (3560), hop 3 after the LocalDate constructor (3561), hop 4 "
               "after append (3562), hop 5 after withFields (3563). The facade calls hop 1 by its fully-qualified name; each hop "
               "imports the next host and the org.joda.time types it names (ReadableInstant in DateTimeFormatterBuilder; "
               "DateTimeFieldType in DateTimeZoneBuilder; Chronology and DateTimeFieldType in PeriodFormatterBuilder); the gold "
               "needs no import (same package as Chronology, DateTimeZone and DateTimeFieldType).",
}
