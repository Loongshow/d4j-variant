"""Main run Time-23 (C10 recipe on the fixed checkout of Defects4J Time-23; the real bug modified DateTimeZone, the target class).

Facade: DateTimeZone.forID(String) (allowed target, BATCH5_PREREGISTRATION.md row Time-23). The other allowed target,
setNameProvider, was set aside: its body is a permission check plus a call of the private setNameProvider0, whose only effect is
the assignment of the private static field cNameProvider; no hop in another class can make that assignment, so its computation
cannot be moved into a chain without exposing the field, and it has no decision whose omission an existing test pins.
Original computation of forID: a null id gives getDefault(); "UTC" gives the UTC singleton; an id the zone provider knows gives
the provider's zone; an id starting with + or - is parsed (private parseOffset: the timezone offset parser [+-]hh[:mm[:ss[.SSS]]]),
a zero offset gives UTC, any other offset gives fixedOffsetZone(printOffset(offset), offset), i.e. the shared, softly cached
fixed offset zone whose id is the timezone offset string of the offset; any other id throws IllegalArgumentException.

Chain (hosts in draw order for seed 4765, mr_lib preview, target org/joda/time/DateTimeZone.java, none skipped):
  hop 1 format.PeriodFormatterBuilder.zoneForId     decision: "UTC" gives DateTimeZone.UTC, else delegates
  hop 2 tz.DateTimeZoneBuilder.zoneFromId           decision: the provider's zone if the provider knows the id
  hop 3 format.ISODateTimeFormat.zoneOfId           decision: only an id starting with + or - goes on; any other id throws
  hop 4 DateTime.zoneForOffsetId                    placement: parses the offset of the id (DateTimeZone.parseOffset); zero
                                                    gives UTC
  hop 5 Period.zoneForOffset                        GOLD: writes the timezone offset string of the offset (sign, hours,
                                                    minutes, and the seconds and milliseconds as far as the offset has
                                                    them) and returns the shared fixed offset zone for it
The correct configuration returns the original result for every input: the same guard, the same UTC test, the same provider
lookup, the same sign test and message, the same parser, the same zero test, a line-for-line copy of printOffset's algorithm
(the two `offset == 0` early returns become two nested `rest != 0` blocks) and the same cache (fixedOffsetZone).

Fault (one-line omission of a decision in the gold): the inner `if (rest != 0)` that leaves out a zero millisecond part is
dropped, so whenever the offset has seconds the milliseconds are written as well. Trigger: the EXISTING test
TestDateTimeZone::testForID_String. Its region, UTC, zero-offset and hh:mm assertions still hold; forID("-07:05:34.0") gives
the zone with id "-07:05:34.000" and assertEquals("-07:05:34", zone.getID()) fails. It is the only test that passes forID an
offset with seconds and no milliseconds: testForOffsetMillis_int's forID("+04:45:17.045") has milliseconds (same id as
before), every other offset id in the suite is hh:mm, and forOffsetMillis / forTimeZone keep the intact private printOffset.

The gold's javadoc states the idiomatic contract (the zone for a fixed offset, with the timezone offset string of the offset as
its id; printOffset's own words are "Formats a timezone offset string") and is silent on which fields are written. The timezone
offset string of -7:05:34 is "-07:05:34" (printOffset, forOffsetMillis), so the variant violates the contract on the trigger
input and gives a second, unequal zone for that offset.

External pins (convention outside the gold): DateTimeZone.printOffset, beside the facade, writes the same string with both
early returns and is used by DateTimeZone.forOffsetMillis and DateTimeZone.forTimeZone;
DateTimeFormatterBuilder.TimeZoneOffset.printTo (the timezone offset printer) also stops after the seconds when the rest is zero
and minFields allows it. Passing tests: testForOffsetMillis_int (forID("+04:45:17.045") equals forOffsetMillis of the same
offset), testForOffsetHoursMinutes_int_int (forID ids equal the forOffsetHoursMinutes zones), testForTimeZone_TimeZone
(printOffset ids "+01:23", "-02:00"), testSerialization2 (the shared zone of "+01:00").

Single owner: only the gold writes the id; hops 1-3 route the id, hop 4 hands over the parsed offset, which is right on the
trigger input (-25534000). The written id depends only on the offset, so no transformation of the id or the offset above the
gold changes it. Declared alternatives (G9): hop 2 trims the id before the provider lookup; hop 3 drops a fraction of zeros
from the id; hop 4 passes the offset in whole seconds. Each still gives "-07:05:34.000".
Recorded bypasses (one-line edits that replace the gold's result with another implementation, not repairs of the chain):
 B-0 the facade (its original body) or any of hops 1-4 returns DateTimeZone.forOffsetMillis(...) for the offset (hop 4:
     `return DateTimeZone.forOffsetMillis(offset);`), which writes the id with the intact printOffset and leaves the gold dead.
     Checked at hop 4 on the variant in a scratch copy: trigger passes, full suite 0 failing tests.
 B-1 hop 4 rebuilds the zone from the gold's result, e.g.
     `return DateTimeZone.forOffsetMillis(Period.zoneForOffset(offset).getOffset(0L));`, keeping only its offset.

Lie: the facade's javadoc claims region IDs are looked up by a binary search in a sorted array of all the available IDs; the
chain asks the provider (a hash map in ZoneInfoProvider) and sorts nothing. It names neither offset ids nor the id string nor any
hop.

Pre-edits (behaviour-preserving, needed by the recipe):
 P-1 the @FromString annotation between forID's javadoc and its header is moved among the modifiers
     (`public static @FromString DateTimeZone forID(String id)`); with it on its own line rewrite_facade finds no adjacent
     javadoc and cannot append the lie. The annotation stays on the method (joda-convert, TestStringConvert).
 P-2 DateTimeZone.parseOffset and DateTimeZone.fixedOffsetZone lose `private` (package access), so hop 4 and the gold, both in
     org.joda.time, can call the original parser and the original cache.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: offset is read into rest (every printed field) and passed to fixedOffsetZone.
  T2 absent: buf reaches the call, rest is read for every field, hours / minutes / seconds are printed; no literal-initialised
     local, no loop; the sign if/else and both rest tests have different effects.
  T3 absent: the sign pair is handled on both sides ('+' for rest >= 0, '-' with the negation otherwise); the rest is tested
     before the seconds and before the milliseconds; no set is handled in part.
  T4 absent: the javadoc names the zone for a fixed offset and the timezone offset string (general descriptions the body
     addresses); no bound, value class or case.
 Variant gold (the inner rest test removed):
  T1 absent: offset is read into rest and passed to fixedOffsetZone; it changes the id and the zone.
  T2 absent: buf, rest, hours, minutes and seconds all reach buf or the return; no frozen local (no loop, no literal local);
     the sign if/else writes different signs and the remaining `if (rest != 0)` decides whether a sub-minute part is written.
  T3 absent: both signs are handled; the four fields are all written (hours and minutes always, seconds and milliseconds
     together under the one rest test), so no member of a set is left out while a sibling is treated; the text names no class.
  T4 absent: 'the timezone offset string of the offset' and 'the DateTimeZone object for the offset' are general descriptions
     that the body addresses; '@param offset the offset in milliseconds' is a description of the parameter; no comment;
     identifiers (buf, rest, hours, minutes, seconds) name nothing the body does not meet."""

DTZ = "src/main/java/org/joda/time/DateTimeZone.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
DZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
ISO = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"
DT = "src/main/java/org/joda/time/DateTime.java"
PER = "src/main/java/org/joda/time/Period.java"

GOLD_TEXT = '''/**
 * Gets the time zone instance for a fixed offset, using the timezone
 * offset string of the offset as its id.
 *
 * @param offset  the offset in milliseconds
 * @return the DateTimeZone object for the offset
 */
public static DateTimeZone zoneForOffset(int offset) {
    StringBuffer buf = new StringBuffer();
    int rest = offset;
    if (rest >= 0) {
        buf.append('+');
    } else {
        buf.append('-');
        rest = -rest;
    }

    int hours = rest / DateTimeConstants.MILLIS_PER_HOUR;
    FormatUtils.appendPaddedInteger(buf, hours, 2);
    rest -= hours * DateTimeConstants.MILLIS_PER_HOUR;

    int minutes = rest / DateTimeConstants.MILLIS_PER_MINUTE;
    buf.append(':');
    FormatUtils.appendPaddedInteger(buf, minutes, 2);
    rest -= minutes * DateTimeConstants.MILLIS_PER_MINUTE;

    if (rest != 0) {
        int seconds = rest / DateTimeConstants.MILLIS_PER_SECOND;
        buf.append(':');
        FormatUtils.appendPaddedInteger(buf, seconds, 2);
        rest -= seconds * DateTimeConstants.MILLIS_PER_SECOND;
        if (rest != 0) {
            buf.append('.');
            FormatUtils.appendPaddedInteger(buf, rest, 3);
        }
    }
    return DateTimeZone.fixedOffsetZone(buf.toString(), offset);
}'''

HOP1 = '''/**
 * Gets a time zone instance for the specified time zone id.
 * <p>
 * The id {@code UTC} gives the {@link DateTimeZone#UTC} zone; any other
 * id is passed on to the zone lookup.
 *
 * @param id  the ID of the datetime zone, not null
 * @return the DateTimeZone object for the ID
 * @throws IllegalArgumentException if the ID is not recognised
 */
public static DateTimeZone zoneForId(String id) {
    if (id.equals("UTC")) {
        return DateTimeZone.UTC;
    }
    return DateTimeZoneBuilder.zoneFromId(id);
}'''

HOP2 = '''/**
 * Gets a time zone instance for the specified time zone id.
 * <p>
 * An id that the zone provider knows gives the provider's zone.
 *
 * @param id  the ID of the datetime zone, not null
 * @return the DateTimeZone object for the ID
 * @throws IllegalArgumentException if the ID is not recognised
 */
public static DateTimeZone zoneFromId(String id) {
    DateTimeZone zone = DateTimeZone.getProvider().getZone(id);
    if (zone != null) {
        return zone;
    }
    return ISODateTimeFormat.zoneOfId(id);
}'''

HOP3 = '''/**
 * Gets a time zone instance for a time zone id that the zone provider
 * does not know.
 * <p>
 * Such an id is accepted only as a fixed offset id, which starts with
 * {@code +} or {@code -}.
 *
 * @param id  the ID of the datetime zone, not null
 * @return the DateTimeZone object for the ID
 * @throws IllegalArgumentException if the ID is not recognised
 */
public static DateTimeZone zoneOfId(String id) {
    if (id.startsWith("+") || id.startsWith("-")) {
        return DateTime.zoneForOffsetId(id);
    }
    throw new IllegalArgumentException("The datetime zone id '" + id + "' is not recognised");
}'''

HOP4 = '''/**
 * Gets a time zone instance for a fixed offset id.
 * <p>
 * The offset is parsed from the id; a zero offset gives the
 * {@link DateTimeZone#UTC} zone.
 *
 * @param id  the fixed offset id, starting with {@code +} or {@code -}
 * @return the DateTimeZone object for the offset
 * @throws IllegalArgumentException if the offset cannot be parsed
 */
public static DateTimeZone zoneForOffsetId(String id) {
    int offset = DateTimeZone.parseOffset(id);
    if (offset == 0) {
        return DateTimeZone.UTC;
    }
    return Period.zoneForOffset(offset);
}'''

DESIGN = {
 "instance": "Time-23", "project": "Time", "bug_id": 23, "seed": 4765,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": DTZ, "class": "org.joda.time.DateTimeZone", "method": "forID", "near_line": 202},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestDateTimeZone.java",
             "test_class": "org.joda.time.TestDateTimeZone", "test_method": "testForID_String"},
 "expected_signature": "but was:<-07:05:34[.000]>",
 "gold": {"method": "zoneForOffset", "text": GOLD_TEXT,
          "fault": {"old": "            rest -= seconds * DateTimeConstants.MILLIS_PER_SECOND;\n"
                           "            if (rest != 0) {\n"
                           "                buf.append('.');\n"
                           "                FormatUtils.appendPaddedInteger(buf, rest, 3);\n"
                           "            }\n"
                           "        }",
                    "new": "            rest -= seconds * DateTimeConstants.MILLIS_PER_SECOND;\n"
                           "            buf.append('.');\n"
                           "            FormatUtils.appendPaddedInteger(buf, rest, 3);\n"
                           "        }"}},
 "pre_edits": {
   "chain": [
     {"file": DTZ, "old": "    @FromString\n    public static DateTimeZone forID(String id) {",
      "new": "    public static @FromString DateTimeZone forID(String id) {"},
     {"file": DTZ, "old": "    private static synchronized DateTimeZone fixedOffsetZone(String id, int offset) {",
      "new": "    static synchronized DateTimeZone fixedOffsetZone(String id, int offset) {"},
     {"file": DTZ, "old": "    private static int parseOffset(String str) {",
      "new": "    static int parseOffset(String str) {"},
   ],
 },
 "chain": {
   "facade_body": "if (id == null) {\n            return getDefault();\n        }\n"
                  "        return org.joda.time.format.PeriodFormatterBuilder.zoneForId(id);",
   "lie": "Region IDs are looked up by a binary search in a sorted array of all the available IDs.",
   "hops": [
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "zoneForId",
      "imports": ["org.joda.time.DateTimeZone", "org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP1},
     {"file": DZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "zoneFromId",
      "imports": ["org.joda.time.format.ISODateTimeFormat"], "text": HOP2},
     {"file": ISO, "class": "org.joda.time.format.ISODateTimeFormat", "method": "zoneOfId",
      "imports": ["org.joda.time.DateTime", "org.joda.time.DateTimeZone"], "text": HOP3},
     {"file": DT, "class": "org.joda.time.DateTime", "method": "zoneForOffsetId", "imports": [], "text": HOP4},
     {"file": PER, "class": "org.joda.time.Period", "method": "zoneForOffset",
      "imports": ["org.joda.time.format.FormatUtils"], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.DateTimeZone::printOffset",
              "org.joda.time.DateTimeZone::forOffsetMillis",
              "org.joda.time.DateTimeZone::forTimeZone",
              "org.joda.time.format.DateTimeFormatterBuilder.TimeZoneOffset::printTo"],
 "ownership_reason": "Only the gold writes the id of a fixed offset zone; hops 1-3 route the id (UTC, provider, sign) and hop 4 "
                     "hands over the parsed offset, which is right on the trigger input (-25534000 for \"-07:05:34.0\"). The "
                     "written id depends only on the offset, so no change of the id or of the offset above the gold makes it "
                     "\"-07:05:34\"; a hop can only discard the gold's zone and build another one (forOffsetMillis), which is a "
                     "bypass. The convention is pinned outside the gold: DateTimeZone.printOffset ('Formats a timezone offset "
                     "string'), beside the facade, leaves out a zero rest after the minutes and again after the seconds, and "
                     "it writes the ids of DateTimeZone.forOffsetMillis and DateTimeZone.forTimeZone; the timezone offset "
                     "printer DateTimeFormatterBuilder.TimeZoneOffset.printTo stops after the seconds when the rest is zero; "
                     "testForOffsetMillis_int (forID(\"+04:45:17.045\") equals forOffsetMillis of the same offset), "
                     "testForOffsetHoursMinutes_int_int, testForTimeZone_TimeZone (ids \"+01:23\", \"-02:00\") and "
                     "testSerialization2 (one shared zone per id) pass. The gold's javadoc promises the timezone offset string "
                     "of the offset as the id, which for -7:05:34 is \"-07:05:34\", not \"-07:05:34.000\".",
 "ownership_tests": ["org.joda.time.TestDateTimeZone::testForOffsetMillis_int",
                     "org.joda.time.TestDateTimeZone::testForOffsetHoursMinutes_int_int",
                     "org.joda.time.TestDateTimeZone::testForTimeZone_TimeZone",
                     "org.joda.time.TestDateTimeZone::testSerialization2"],
 "compensating": {
   "chain": [
     {"file": DZB, "old": "DateTimeZone zone = DateTimeZone.getProvider().getZone(id);",
      "new": "DateTimeZone zone = DateTimeZone.getProvider().getZone(id.trim());",
      "why": "hop 2 trims the id before the provider lookup"},
     {"file": ISO, "old": "return DateTime.zoneForOffsetId(id);",
      "new": "return DateTime.zoneForOffsetId(id.replaceFirst(\"[.,]0+$\", \"\"));",
      "why": "hop 3 drops a fraction of zeros from the id"},
     {"file": DT, "old": "return Period.zoneForOffset(offset);",
      "new": "return Period.zoneForOffset(offset - offset % DateTimeConstants.MILLIS_PER_SECOND);",
      "why": "hop 4 passes the offset in whole seconds"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4765 (mr_lib preview, target org/joda/time/DateTimeZone.java): "
               "format.PeriodFormatterBuilder (hop 1), tz.DateTimeZoneBuilder (hop 2), format.ISODateTimeFormat (hop 3), "
               "DateTime (hop 4), Period (hop 5, gold). All five are public concrete top-level classes in which a static "
               "method compiles; every preview anchor lies in the outer class; none was skipped. The recipe relaxed its "
               "'distinct from the target package' rule from hop 3 on (the pool has too few other-package classes), so hops "
               "4 and 5 share org.joda.time with the facade, which lets them call the package-access parseOffset and "
               "fixedOffsetZone (pre-edit P-2). The facade calls hop 1 by its fully-qualified name; hops 1-3 import the next "
               "host and DateTimeZone where needed; the gold imports format.FormatUtils.",
}
