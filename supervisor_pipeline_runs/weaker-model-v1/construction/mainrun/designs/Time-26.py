"""Main run Time-26 (C10 recipe on the fixed checkout of Defects4J Time-26; the real bug modified DateTimeZone, ZonedChronology
and LenientDateTimeField; DateTimeZone, the facade's class, is one of them).

Facade: DateTimeZone.forTimeZone(TimeZone) (allowed target, BATCH5_PREREGISTRATION.md row Time-26). The other two allowed targets
cannot carry the recipe: ZonedChronology.getInstance ends in `new ZonedChronology(base, zone)` and LenientDateTimeField.getInstance in
`new LenientDateTimeField(field, base)`, whose constructors are private and protected, so no hop in another package can produce the
result and the facade could not be a guard plus one delegating call; neither has a computation beyond argument checks and one
unwrap that could be split into a chain with a per-element core.
Original computation of the facade: a null zone gives the default zone; the JDK ID UTC gives DateTimeZone.UTC; an old style ID is
converted to its new style ID (private DateTimeZone.getConvertedId), the provider is consulted for the new style ID and then for the
ID itself; a zone the provider supplies is returned; otherwise, for a zone without an old style ID whose display name starts with
GMT+ or GMT-, the offset text after GMT is parsed (private parseOffset) and a zero offset gives DateTimeZone.UTC, any other offset
the fixed offset zone with the printed offset as ID; anything else throws IllegalArgumentException("The datetime zone id '...' is
not recognised").

Chain (hosts in draw order for seed 4505, mr_lib preview, target org/joda/time/DateTimeZone.java, none skipped):
  hop 1 format.DateTimeFormatterBuilder.zoneForTimeZone   decision: the JDK ID UTC gives DateTimeZone.UTC
  hop 2 tz.DateTimeZoneBuilder.fromTimeZone               placement: the current zone provider (DateTimeZone.getProvider())
  hop 3 Period.zoneFromProvider                           the provider lookups: new style ID of an old style ID first, then the
                                                          ID; an unknown zone with an old style ID throws; otherwise on to hop 4
  hop 4 format.ISODateTimeFormat.offsetZoneOf             decision: a display name GMT+... / GMT-... gives the offset text after
                                                          GMT; any other display name throws
  hop 5 format.PeriodFormatterBuilder.zoneForOffset       GOLD: the offset text parsed to millis (the same parser and sign as
                                                          DateTimeZone.parseOffset), a zero offset gives DateTimeZone.UTC, any
                                                          other offset a FixedDateTimeZone with that offset
The correct configuration returns the original result for every JDK zone (same guard, same order of lookups, same exceptions and
messages); the two differences are invisible to every caller and test: the gold builds the fixed offset zone itself (equal, by
FixedDateTimeZone.equals, to the cached instance the private fixedOffsetZone returned), and takes the offset text itself as the ID,
which is the printed form for every display name a JDK zone produces (GMT followed by a sign and hh:mm, as the JDK normalises custom
IDs). The parser runs with ISOChronology.getInstanceUTC() rather than the default chronology so that it never reaches
DateTimeZone.getDefault() (the original's private parseOffset avoids the default zone for the same reason).

Pre-edit (behaviour-preserving, needed by the recipe): hop 3 needs the old-style-ID table, which is the private
DateTimeZone.getConvertedId; the pre-edit drops its `private` modifier (package-private, `static synchronized` kept) so that hop 3,
which the draw places in Period in the same package, can call it. Without a caller the private method would also be dead code.

Fault (omission of a special-case decision in the gold): the zero-offset decision is dropped, so a zero offset gives a new
FixedDateTimeZone with the ID +00:00 instead of DateTimeZone.UTC. The gold then reads as the ordinary routine "parse the offset,
build the fixed offset zone". Trigger: the EXISTING test TestDateTimeZone::testForTimeZone_TimeZone; its first four assertions
(null, Europe/London, UTC, and +00:00, which the JDK reads as GMT and the old-style table converts to UTC) still hold, and
assertSame(DateTimeZone.UTC, forTimeZone(TimeZone.getTimeZone("GMT+00:00"))) at line 302 fails with
expected same:<UTC> was not:<+00:00>. It is the only test that passes a zero GMT offset through the display-name path;
testTimeZoneConversion (GMT-10:00) passes on the variant, every CalendarConverter and constructor test uses named zones that the
provider supplies, and the unknown mock zone of TestCalendarConverter still throws at hop 4.

The gold's javadoc states the idiomatic contract (the house wording of DateTimeZone.forOffsetMillis: "Gets a time zone instance for
the specified offset", "@return the DateTimeZone object for the offset") and is silent on zero offsets. In this code base the
DateTimeZone object for a zero offset is DateTimeZone.UTC: no factory ever produces a zone with the ID +00:00 (forID("+00:00"),
forOffsetMillis(0) and forOffsetHoursMinutes(0, 0) all return UTC), and FixedDateTimeZone("+00:00", ...) is not equal to UTC. The
convention is pinned outside the gold: DateTimeZone.forID ('if (offset == 0L) return DateTimeZone.UTC' for a +hh:mm ID;
testForID_String asserts assertSame(UTC, forID("+00:00")) and forID("+00")), DateTimeZone.forOffsetMillis (through
fixedOffsetZone's 'if (offset == 0) return DateTimeZone.UTC'; testForOffsetMillis_int asserts assertSame(UTC, forOffsetMillis(0))),
DateTimeZone.forOffsetHoursMinutes ('if (hoursOffset == 0 && minutesOffset == 0) return DateTimeZone.UTC';
testForOffsetHoursMinutes_int_int). testTimeZoneConversion pins the non-zero GMT path (GMT-10:00 to -10:00 and back) and passes.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: offsetText is parsed and is the ID of the returned zone.
  T2 absent: parser is read by the parse, offset by the decision and the constructor; the if returns UTC instead of a new
     FixedDateTimeZone, so it matters; no literal-initialised, loop or flag local.
  T3 absent: one decision on one value (zero) of an unnamed set; wall and standard offsets of the zone both get the offset; the
     javadoc names no class.
  T4 absent: the javadoc names a time zone instance for the offset and a not-null caller precondition; no rule, limit or class.
  Nothing needed rewriting.
 Variant gold (javadoc, signature, `final DateTimeFormatter parser = new DateTimeFormatterBuilder().appendTimeZoneOffset(null, true,
 2, 4).toFormatter().withChronology(ISOChronology.getInstanceUTC()); final int offset = -(int) parser.parseMillis(offsetText);
 return new FixedDateTimeZone(offsetText, null, offset, offset);`):
  T1 absent: offsetText is read by the parse and is the ID of the returned zone; both change the result.
  T2 absent: parser is read in the parse; offset is read twice in the constructor call that is returned; no literal-initialised
     local, no loop, no branch, case or ternary.
  T3 absent: no case, branch or check remains ('No member handled'); the zone's two offsets (wall, standard) are both given the
     parsed offset; the gold's text names no set or class.
  T4 absent: 'Gets a time zone instance for the specified offset, given as text' and '@return the DateTimeZone object for the
     offset' are general descriptions that the parse and the constructor address; '@param offsetText the offset text, not null' is
     a caller precondition; no inline comment; the identifiers (parser, offset, offsetText) name nothing the body does not meet.

Single owner: only the gold turns the offset into a zone, and the variant gold never returns the DateTimeZone.UTC instance for any
input (it always constructs a new FixedDateTimeZone), so no change of what hops 1-4 pass to it can make the trigger pass. Every
passing edit outside the gold either computes the UTC zone itself instead of the gold or replaces the gold's result:
 B-0 bypass: hop 4 returns DateTimeZone.forID(name.substring(3)) instead of calling the gold (the gold becomes dead; forID repeats
     the gold's parse, zero rule and fixed zone). Checked on the variant in a scratch copy: trigger passes, full suite 0 failing.
 B-1 bypass: hop 1 re-resolves the chain's result through forID, `return DateTimeZone.forID(DateTimeZoneBuilder.fromTimeZone(zone)
     .getID());`: the gold's zone object is discarded and only its ID string is kept; forID re-implements the conversion. Checked
     on the variant in a scratch copy: trigger passes, full suite 0 failing.
 B-2 bypass: a hop answers zero GMT offsets itself before the gold is reached: on the trigger input the gold's output is never
     used; a second implementation of the gold's decision. Checked on the variant in scratch copies (trigger passes, full suite 0
     failing): hop 1 `if (zone.getID().equals("UTC") || zone.getID().startsWith("GMT") && zone.getRawOffset() == 0) {` (hop 1's
     documented rule is about the ID UTC only); hop 4 `final String name = zone.getDisplayName(); if (name.equals("GMT+00:00") ||
     name.equals("GMT-00:00")) return DateTimeZone.UTC;` (test-fitted); hop 2 handing hop 3 TimeZone.getTimeZone("UTC") in place of
     a GMT zone with raw offset 0. A rule on the raw offset alone (hop 4 `if (zone.getRawOffset() == 0) return DateTimeZone.UTC;`)
     fails the suite: it turns the unknown mock zone of TestCalendarConverter (raw offset 0) into UTC instead of the default zone
     (testGetChronology_Object_nullChronology).
Declared alternatives (G9; none changes the trigger case): hop 1 also treats the JDK ID GMT as UTC (the trigger's ID is GMT+00:00);
hop 3 also looks the ID up under the Etc/ prefix (the provider has no Etc/GMT+00:00); hop 4 reads the offset from the ID instead of
the display name (both are GMT+00:00).

Lie: the facade's javadoc claims the zone is chosen by comparing the raw offset and daylight saving rules of the JDK zone with each
zone of the provider in turn; the chain compares no rules and looks zones up by ID. It names neither zero offsets, UTC, the display
name nor any hop."""

DTZ = "src/main/java/org/joda/time/DateTimeZone.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"
DTZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
PER = "src/main/java/org/joda/time/Period.java"
ISO = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"

GOLD_TEXT = '''/**
 * Gets a time zone instance for the specified offset, given as text.
 *
 * @param offsetText  the offset text, not null
 * @return the DateTimeZone object for the offset
 */
public static DateTimeZone zoneForOffset(String offsetText) {
    final DateTimeFormatter parser = new DateTimeFormatterBuilder()
        .appendTimeZoneOffset(null, true, 2, 4)
        .toFormatter()
        .withChronology(ISOChronology.getInstanceUTC());
    final int offset = -(int) parser.parseMillis(offsetText);
    if (offset == 0) {
        return DateTimeZone.UTC;
    }
    return new FixedDateTimeZone(offsetText, null, offset, offset);
}'''

HOP1 = '''/**
 * Gets a time zone instance for a JDK TimeZone.
 * <p>
 * The JDK zone with the ID UTC gives the UTC zone.
 *
 * @param zone  the zone to convert, not null
 * @return the DateTimeZone object for the zone
 * @throws IllegalArgumentException if the zone is not recognised
 */
public static DateTimeZone zoneForTimeZone(TimeZone zone) {
    if (zone.getID().equals("UTC")) {
        return DateTimeZone.UTC;
    }
    return DateTimeZoneBuilder.fromTimeZone(zone);
}'''

HOP2 = '''/**
 * Gets a time zone instance for a JDK TimeZone, using the zone provider
 * of DateTimeZone.
 *
 * @param zone  the zone to convert, not null
 * @return the DateTimeZone object for the zone
 * @throws IllegalArgumentException if the zone is not recognised
 */
public static DateTimeZone fromTimeZone(TimeZone zone) {
    return Period.zoneFromProvider(DateTimeZone.getProvider(), zone);
}'''

HOP3 = '''/**
 * Gets the time zone instance that a zone provider supplies for a JDK
 * TimeZone.
 * <p>
 * An old style ID is converted to its new style ID before the provider is
 * consulted, and the ID itself is looked up if the provider has no zone for
 * the new style ID. A zone without an old style ID that the provider does
 * not supply is converted from its display name.
 *
 * @param provider  the zone provider to consult, not null
 * @param zone  the zone to convert, not null
 * @return the DateTimeZone object for the zone
 * @throws IllegalArgumentException if the zone is not recognised
 */
public static DateTimeZone zoneFromProvider(Provider provider, TimeZone zone) {
    final String id = zone.getID();
    final String newId = DateTimeZone.getConvertedId(id);
    DateTimeZone dtz = null;
    if (newId != null) {
        dtz = provider.getZone(newId);
    }
    if (dtz == null) {
        dtz = provider.getZone(id);
    }
    if (dtz != null) {
        return dtz;
    }
    if (newId != null) {
        throw new IllegalArgumentException("The datetime zone id '" + id + "' is not recognised");
    }
    return ISODateTimeFormat.offsetZoneOf(zone);
}'''

HOP4 = '''/**
 * Gets a time zone instance for a JDK TimeZone from its display name.
 * <p>
 * A display name in the GMT offset format, GMT followed by a signed
 * offset, gives the zone for the offset that follows GMT.
 *
 * @param zone  the zone to convert, not null
 * @return the DateTimeZone object for the offset in the display name
 * @throws IllegalArgumentException if the display name is not in the GMT offset format
 */
public static DateTimeZone offsetZoneOf(TimeZone zone) {
    final String name = zone.getDisplayName();
    if (name.startsWith("GMT+") || name.startsWith("GMT-")) {
        return PeriodFormatterBuilder.zoneForOffset(name.substring(3));
    }
    throw new IllegalArgumentException("The datetime zone id '" + zone.getID() + "' is not recognised");
}'''

DESIGN = {
 "instance": "Time-26", "project": "Time", "bug_id": 26, "seed": 4505,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": DTZ, "class": "org.joda.time.DateTimeZone", "method": "forTimeZone", "near_line": 301},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestDateTimeZone.java",
             "test_class": "org.joda.time.TestDateTimeZone", "test_method": "testForTimeZone_TimeZone"},
 "expected_signature": "expected same:<UTC> was not:<+00:00>",
 "gold": {"method": "zoneForOffset", "text": GOLD_TEXT,
          "fault": {"old": "        final int offset = -(int) parser.parseMillis(offsetText);\n"
                           "        if (offset == 0) {\n"
                           "            return DateTimeZone.UTC;\n"
                           "        }\n"
                           "        return new FixedDateTimeZone(offsetText, null, offset, offset);",
                    "new": "        final int offset = -(int) parser.parseMillis(offsetText);\n"
                           "        return new FixedDateTimeZone(offsetText, null, offset, offset);"}},
 "pre_edits": {
   "chain": [{"file": DTZ, "old": "    private static synchronized String getConvertedId(String id) {",
              "new": "    static synchronized String getConvertedId(String id) {"}],
 },
 "chain": {
   "facade_body": "if (zone == null) {\n"
                  "            return getDefault();\n"
                  "        }\n"
                  "        return DateTimeFormatterBuilder.zoneForTimeZone(zone);",
   "lie": "The zone is chosen by comparing the raw offset and the daylight saving rules of the JDK zone with those of each "
          "zone of the provider in turn, and the first zone whose rules agree is returned.",
   "hops": [
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "zoneForTimeZone",
      "imports": ["java.util.TimeZone", "org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP1},
     {"file": DTZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "fromTimeZone",
      "imports": ["java.util.TimeZone"], "text": HOP2},
     {"file": PER, "class": "org.joda.time.Period", "method": "zoneFromProvider",
      "imports": ["java.util.TimeZone", "org.joda.time.format.ISODateTimeFormat", "org.joda.time.tz.Provider"], "text": HOP3},
     {"file": ISO, "class": "org.joda.time.format.ISODateTimeFormat", "method": "offsetZoneOf",
      "imports": ["java.util.TimeZone", "org.joda.time.DateTimeZone"], "text": HOP4},
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "zoneForOffset",
      "imports": ["org.joda.time.DateTimeZone", "org.joda.time.chrono.ISOChronology", "org.joda.time.tz.FixedDateTimeZone"],
      "gold": True},
   ],
 },
 "evidence": ["org.joda.time.DateTimeZone::forID",
              "org.joda.time.DateTimeZone::forOffsetMillis",
              "org.joda.time.DateTimeZone::forOffsetHoursMinutes"],
 "ownership_reason": "Only the gold turns the offset text of a GMT display name into a zone; hops 1-4 resolve the ID UTC, place "
                     "the provider, look the ID up and select the offset text, and once the offset reaches the gold no caller "
                     "receives anything but the gold's zone. The variant gold never returns the DateTimeZone.UTC instance for any "
                     "input (it always constructs a new FixedDateTimeZone), so no change of what hops 1-4 pass to it makes the "
                     "trigger pass; an edit outside the gold passes only by producing UTC itself or by re-resolving the result "
                     "(bypasses). The convention is pinned outside the gold: in this code base the DateTimeZone object for a zero "
                     "offset is DateTimeZone.UTC and no factory produces a zone with the ID +00:00. DateTimeZone.forID returns UTC "
                     "for a zero +hh:mm offset (testForID_String: assertSame(UTC, forID(\"+00:00\")) and forID(\"+00\")), "
                     "DateTimeZone.forOffsetMillis returns UTC for 0 through fixedOffsetZone (testForOffsetMillis_int: "
                     "assertSame(UTC, forOffsetMillis(0))), and DateTimeZone.forOffsetHoursMinutes returns UTC for (0, 0) "
                     "(testForOffsetHoursMinutes_int_int). The gold's javadoc is the house contract of forOffsetMillis ('a time "
                     "zone instance for the specified offset', 'the DateTimeZone object for the offset'), which a FixedDateTimeZone "
                     "with the ID +00:00, not equal to UTC, violates for a zero offset. testTimeZoneConversion pins the non-zero "
                     "GMT display-name path (GMT-10:00 gives -10:00) and passes on the variant.",
 "ownership_tests": ["org.joda.time.TestDateTimeZone::testForID_String",
                     "org.joda.time.TestDateTimeZone::testForOffsetMillis_int",
                     "org.joda.time.TestDateTimeZone::testForOffsetHoursMinutes_int_int",
                     "org.joda.time.TestDateTimeZone::testTimeZoneConversion"],
 "compensating": {
   "chain": [
     {"file": DTFB, "old": "        if (zone.getID().equals(\"UTC\")) {",
      "new": "        if (zone.getID().equals(\"UTC\") || zone.getID().equals(\"GMT\")) {",
      "why": "hop 1 also treats the JDK ID GMT as UTC"},
     {"file": PER, "old": "            dtz = provider.getZone(id);",
      "new": "            dtz = provider.getZone(id.startsWith(\"GMT\") ? \"Etc/\" + id : id);",
      "why": "hop 3 looks a GMT ID up under the Etc/ prefix"},
     {"file": ISO, "old": "        final String name = zone.getDisplayName();",
      "new": "        final String name = zone.getID();",
      "why": "hop 4 reads the offset from the ID instead of the display name"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4505 (mr_lib preview, target org/joda/time/DateTimeZone.java): "
               "format.DateTimeFormatterBuilder (hop 1), tz.DateTimeZoneBuilder (hop 2), Period (hop 3), "
               "format.ISODateTimeFormat (hop 4), format.PeriodFormatterBuilder (hop 5, gold). The draw relaxed the "
               "'distinct from target package' constraint for hosts 3-5 (fewer than two other-package classes of 1500+ lines). "
               "All five are public top-level classes in which a static method compiles; every preview anchor lies in the outer "
               "class, not in a nested one; none was skipped. Hop 3 calls the old-style-ID table DateTimeZone.getConvertedId, "
               "which a behaviour-preserving pre-edit makes package-private (Period shares the org.joda.time package). The "
               "facade calls hop 1 by its simple name (DateTimeZone already imports DateTimeFormatterBuilder); each hop "
               "imports the next host where it is in another package.",
}
