"""Main run Time-9 (C10 recipe on the fixed checkout of Defects4J Time-9; the real bug modified DateTimeZone, the target class).

Facade: DateTimeZone.forOffsetMillis(int) (the only allowed target, BATCH5_PREREGISTRATION.md row Time-9, no facade reuse).
Original computation: throw IllegalArgumentException("Millis out of range: ...") outside [-MAX_MILLIS, MAX_MILLIS]; format the
offset as an ID with the private DateTimeZone.printOffset (sign, then hh:mm, then :ss when the offset is not a whole number of
minutes, then .SSS when it is not a whole number of seconds); return the cached zone for that ID and offset (private
fixedOffsetZone; UTC for a zero offset). Production callers: DateTimeZone.forOffsetHoursMinutes (and so forOffsetHours) and the
four DateTimeFormatter parse methods that build the parsed zone (DateTime.parse, MutableDateTime.parse, DateMidnight.parse).

The facade keeps its range guard and delegates to a five-hop chain drawn with the instance seed 3267 (mr_lib preview, draw
order, no substitution):
  hop 1 tz.DateTimeZoneBuilder.zoneForFixedOffset      placement: the zone is looked up by the ID the offset formats to
                                                       (DateTimeZone.forID, which reaches the same cache and gives UTC for 0)
  hop 2 format.PeriodFormatterBuilder.formatOffsetId    plumbing: creates the buffer and returns its text
  hop 3 Period.appendSignedOffset                       sign: appends '+' or '-' and passes the size of the offset on
  hop 4 format.ISODateTimeFormat.appendOffsetElement    pass-through
  hop 5 LocalTime.appendOffsetTime                      GOLD: prints the size of the offset as a time of day in UTC with the
                                                       project's ISO formatters, choosing the precision the size needs:
                                                       HH:mm for a whole number of minutes, HH:mm:ss for a whole number of
                                                       seconds, HH:mm:ss.SSS otherwise
The correct configuration returns exactly the original zone for every accepted offset: a size below one day printed in UTC is
its own time of day, so the three ISO formatters write printOffset's fields character for character (two-digit hours and
minutes, then two-digit seconds when the size is not a whole number of minutes, then '.' and three digits when it is not a
whole number of seconds), hop 3 adds printOffset's sign rule, and forID of that ID parses it back to the same offset, prints the
same ID and returns the same cached FixedDateTimeZone (or UTC for 0).

Fault (omission of a special-case step in the gold): the precision decision for a size that is not a whole number of minutes
(the `if` that prints with HH:mm:ss or HH:mm:ss.SSS and returns) is dropped. The gold then reads as a complete, ordinary routine
that prints an offset as HH:mm, the ISO-8601 offset form that every whole-minute offset already has. Trigger: the EXISTING test
TestDateTimeZone::testForOffsetMillis_int; its first assertion (offset 0 is UTC) passes and the second,
forOffsetMillis(86399999) equal to forID("+23:59:59.999"), fails with expected:<+23:59:59.999> but was:<+23:59>: the chain's ID
loses the seconds and the milliseconds, forID parses "+23:59" and returns the zone of that other offset. No other test passes
an offset that is not a whole number of minutes into the facade (forOffsetHoursMinutes only produces whole minutes; every
parsed offset in the suite is hh:mm), so whole-minute offsets are unchanged. The gold's javadoc states the idiomatic contract
(it appends the size of a time zone offset, without its sign) and is silent on precision; on the trigger input it appends the
size of another offset.

External pins (convention outside the gold): DateTimeZone.printOffset, the private formatter that forID and forTimeZone still
use, appends ':' and two digits of seconds when the offset is not a whole number of minutes and '.' and three digits when it is
not a whole number of seconds; DateTimeFormatterBuilder.TimeZoneOffset.printTo does the same with four fields (the form
DateTimeZone's own offset parser reads); the facade's javadoc gives its range as 'from -23:59:59.999 to +23:59:59.999' and its
guard is MAX_MILLIS = 86400 * 1000 - 1. Passing tests: TestDateTimeZone testForID_String (printOffset through forID: "+01:23",
"-02:00", "-07:05:34.0" gives "-07:05:34"), testForTimeZone_TimeZone (printOffset through forTimeZone), and
testForOffsetHours_int and testForOffsetHoursMinutes_int_int (the production second caller forOffsetHoursMinutes, through the
whole chain).

Single owner: only the gold looks at the size below a minute and decides which fields of it are printed; hop 1 sees only the
finished ID, hops 2-4 see the buffer and the size and get the buffer back. Once the gold has printed HH:mm, the ID names another
offset, and no change of the input at a hop makes the gold print seconds (it has no step that prints them). forID and
FixedDateTimeZone cannot recover the lost fields from the ID. Declared alternatives (G9), each still failing the trigger: hop 1
builds the zone itself from the offset and the formatted ID (new FixedDateTimeZone; offset 0 is then not UTC, and the ID still
lacks the seconds); hop 1 resolves the ID through the JDK's custom GMT IDs (TimeZone.getTimeZone("GMT" + id), which keeps
hh:mm only); hop 3 takes the size of a negative offset by negation instead of Math.abs (same value).
Recorded one-line edits above the gold that pass the trigger and the full suite (bypasses, not repairs of the chain; both
checked on the variant in a scratch copy, defects4j test: 0 failing tests each):
 B-0 the facade's original body `return fixedOffsetZone(printOffset(millisOffset), millisOffset);` (the private formatter and
     cache of DateTimeZone), discarding the chain including the gold.
 B-1 hop 4 appends the seconds and the milliseconds itself after the gold's call, e.g.
     `return LocalTime.appendOffsetTime(buf, size).append(size % org.joda.time.DateTimeConstants.MILLIS_PER_MINUTE == 0 ? "" : (size % org.joda.time.DateTimeConstants.MILLIS_PER_SECOND == 0 ? hourMinuteSecond() : hourMinuteSecondMillis()).withZoneUTC().print(size).substring(5));`.
     It is a second implementation of the gold's precision step and is consistent only with a gold that does not append the
     size of the offset as its javadoc says: with the gold as documented, the seconds would be written twice.

Lie: the facade's javadoc claims the zone is found by a binary search of a sorted table of the zones created so far, a new zone
being inserted at the search position when none matches; the chain searches no sorted table (forID consults the provider and a
hash map keyed by ID). It names neither seconds, nor precision, nor any formatting step, nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `if (size % MILLIS_PER_MINUTE != 0) { DateTimeFormatter format = (size % MILLIS_PER_SECOND == 0 ?
 hourMinuteSecond() : hourMinuteSecondMillis()); format.withZoneUTC().printTo(buf, size); return buf; }`,
 `ISODateTimeFormat.hourMinute().withZoneUTC().printTo(buf, size);`, `return buf;`):
  T1 absent: buf is printed to and returned; size decides both conditions and is the printed value.
  T2 absent: the only local, format, is assigned from a ternary of two different formatters and printed with; no literal-
     initialised local, no loop, cursor, counter or flag; the if prints with another formatter and returns, so it matters, and
     the two arms of the ternary print different text.
  T3 absent: the three precisions the gold distinguishes (whole minutes, whole seconds, the rest) each get their formatter; no
     enum, type code or named format; no pair halves or range ends; no class named in the text.
  T4 absent: the javadoc names only the size of the offset without its sign and the buffer; no limit, value class or case.
  Nothing needed rewriting.
 Variant gold (javadoc, signature, `ISODateTimeFormat.hourMinute().withZoneUTC().printTo(buf, size);`, `return buf;`):
  T1 absent: buf is printed to and returned; size is the printed value, so each changes the output.
  T2 absent: no local variable, no loop, no branch, case or ternary.
  T3 absent: the gold handles no set: it tests nothing and reads no part or field of the size; the formatter's name hourMinute
     names hour and minute, and both are printed; no enum, type code or format named in the gold's text; no pair halves or
     range ends; no class named in the text (the javadoc's 'size of a time zone offset' is one value, not a class).
  T4 absent: 'Appends the size of a time zone offset, without its sign, to a buffer' is a general description that the body's
     line addresses (it prints the size; no sign is printed); '@param buf ..., not null' and '@param size ..., not negative'
     are caller preconditions; '@return the buffer' is met; no inline comment; identifiers (appendOffsetTime, buf, size) name
     no rule, limit, value class or case."""

DTZ = "src/main/java/org/joda/time/DateTimeZone.java"
DZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
PER = "src/main/java/org/joda/time/Period.java"
ISO = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"
LT = "src/main/java/org/joda/time/LocalTime.java"

GOLD_TEXT = '''/**
 * Appends the size of a time zone offset, without its sign, to a buffer.
 *
 * @param buf  the buffer to append to, not null
 * @param size  the size of the offset, not negative
 * @return the buffer
 */
public static StringBuffer appendOffsetTime(StringBuffer buf, int size) {
    if (size % DateTimeConstants.MILLIS_PER_MINUTE != 0) {
        DateTimeFormatter format = (size % DateTimeConstants.MILLIS_PER_SECOND == 0
                ? ISODateTimeFormat.hourMinuteSecond() : ISODateTimeFormat.hourMinuteSecondMillis());
        format.withZoneUTC().printTo(buf, size);
        return buf;
    }
    ISODateTimeFormat.hourMinute().withZoneUTC().printTo(buf, size);
    return buf;
}'''

HOP1 = '''/**
 * Gets the zone with a fixed offset from UTC, looked up by the ID that
 * the offset formats to.
 *
 * @param millisOffset  the offset in millis from UTC
 * @return the zone with the fixed offset
 */
public static DateTimeZone zoneForFixedOffset(int millisOffset) {
    return DateTimeZone.forID(PeriodFormatterBuilder.formatOffsetId(millisOffset));
}'''

HOP2 = '''/**
 * Formats an offset from UTC as the ID of a fixed offset zone.
 *
 * @param offset  the offset in milliseconds
 * @return the ID for the offset
 */
public static String formatOffsetId(int offset) {
    return Period.appendSignedOffset(new StringBuffer(), offset).toString();
}'''

HOP3 = '''/**
 * Appends an offset from UTC, with its sign, to a buffer.
 *
 * @param buf  the buffer to append to, not null
 * @param offset  the offset in milliseconds
 * @return the buffer
 */
public static StringBuffer appendSignedOffset(StringBuffer buf, int offset) {
    buf.append(offset < 0 ? '-' : '+');
    return ISODateTimeFormat.appendOffsetElement(buf, Math.abs(offset));
}'''

HOP4 = '''/**
 * Appends the size of an offset from UTC, without its sign, to a buffer.
 *
 * @param buf  the buffer to append to, not null
 * @param size  the size of the offset in milliseconds, not negative
 * @return the buffer
 */
public static StringBuffer appendOffsetElement(StringBuffer buf, int size) {
    return LocalTime.appendOffsetTime(buf, size);
}'''

DESIGN = {
 "instance": "Time-9", "project": "Time", "bug_id": 9, "seed": 3267,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": DTZ, "class": "org.joda.time.DateTimeZone", "method": "forOffsetMillis", "near_line": 285},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestDateTimeZone.java",
             "test_class": "org.joda.time.TestDateTimeZone", "test_method": "testForOffsetMillis_int"},
 "expected_signature": "expected:<+23:59:59.999> but was:<+23:59>",
 "gold": {"method": "appendOffsetTime", "text": GOLD_TEXT,
          "fault": {"old": "        if (size % DateTimeConstants.MILLIS_PER_MINUTE != 0) {\n"
                           "            DateTimeFormatter format = (size % DateTimeConstants.MILLIS_PER_SECOND == 0\n"
                           "                    ? ISODateTimeFormat.hourMinuteSecond() : ISODateTimeFormat.hourMinuteSecondMillis());\n"
                           "            format.withZoneUTC().printTo(buf, size);\n"
                           "            return buf;\n"
                           "        }\n"
                           "        ISODateTimeFormat.hourMinute().withZoneUTC().printTo(buf, size);",
                    "new": "        ISODateTimeFormat.hourMinute().withZoneUTC().printTo(buf, size);"}},
 "chain": {
   "facade_body": "if (millisOffset < -MAX_MILLIS || millisOffset > MAX_MILLIS) {\n"
                  "            throw new IllegalArgumentException(\"Millis out of range: \" + millisOffset);\n"
                  "        }\n"
                  "        return org.joda.time.tz.DateTimeZoneBuilder.zoneForFixedOffset(millisOffset);",
   "lie": "The zone is found by a binary search of a sorted table of the zones created so far, and a new zone is "
          "inserted into the table at the search position when none matches.",
   "hops": [
     {"file": DZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "zoneForFixedOffset",
      "imports": ["org.joda.time.DateTimeZone", "org.joda.time.format.PeriodFormatterBuilder"], "text": HOP1},
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "formatOffsetId",
      "imports": ["org.joda.time.Period"], "text": HOP2},
     {"file": PER, "class": "org.joda.time.Period", "method": "appendSignedOffset",
      "imports": ["org.joda.time.format.ISODateTimeFormat"], "text": HOP3},
     {"file": ISO, "class": "org.joda.time.format.ISODateTimeFormat", "method": "appendOffsetElement",
      "imports": ["org.joda.time.LocalTime"], "text": HOP4},
     {"file": LT, "class": "org.joda.time.LocalTime", "method": "appendOffsetTime",
      "imports": ["org.joda.time.format.DateTimeFormatter", "org.joda.time.format.ISODateTimeFormat"], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.DateTimeZone::printOffset",
              "org.joda.time.format.DateTimeFormatterBuilder.TimeZoneOffset::printTo",
              "org.joda.time.DateTimeZone::forID",
              "org.joda.time.DateTimeZone::forOffsetHoursMinutes"],
 "ownership_reason": "Only the gold looks at the size of the offset below a minute and decides which fields of it are printed; "
                     "hop 1 sees only the finished ID, hops 2-4 pass the buffer and the size along and get the buffer back. "
                     "Once HH:mm has been printed for an offset that is not a whole number of minutes, the ID names another "
                     "offset; forID parses that ID and returns the zone of the other offset, and no change of the input at a "
                     "hop makes the gold print the seconds. The convention is pinned outside the gold: DateTimeZone.printOffset "
                     "(the formatter forID and forTimeZone still use) appends ':' and two digits of seconds when the offset is "
                     "not a whole number of minutes and '.' and three digits when it is not a whole number of seconds, as does "
                     "DateTimeFormatterBuilder.TimeZoneOffset.printTo with four fields; the facade's javadoc gives its range as "
                     "'from -23:59:59.999 to +23:59:59.999'; testForID_String pins printOffset's fields and trailing-zero rule "
                     "through forID, and testForOffsetHours_int and testForOffsetHoursMinutes_int_int pin the chain for the "
                     "production second caller forOffsetHoursMinutes. A hop that appends the seconds itself after the gold's "
                     "call passes the suite but is a second implementation of the gold's step, consistent only with a gold "
                     "that does not append the size of the offset as documented (with the gold as documented the seconds "
                     "would be written twice).",
 "ownership_tests": ["org.joda.time.TestDateTimeZone::testForID_String",
                     "org.joda.time.TestDateTimeZone::testForTimeZone_TimeZone",
                     "org.joda.time.TestDateTimeZone::testForOffsetHours_int",
                     "org.joda.time.TestDateTimeZone::testForOffsetHoursMinutes_int_int"],
 "compensating": {
   "chain": [
     {"file": DZB, "old": "return DateTimeZone.forID(PeriodFormatterBuilder.formatOffsetId(millisOffset));",
      "new": "return new FixedDateTimeZone(PeriodFormatterBuilder.formatOffsetId(millisOffset), null, millisOffset, millisOffset);",
      "why": "hop 1 builds the zone itself from the offset and the formatted ID"},
     {"file": DZB, "old": "return DateTimeZone.forID(PeriodFormatterBuilder.formatOffsetId(millisOffset));",
      "new": "return DateTimeZone.forTimeZone(java.util.TimeZone.getTimeZone(\"GMT\" + PeriodFormatterBuilder.formatOffsetId(millisOffset)));",
      "why": "hop 1 resolves the ID through the JDK's custom GMT IDs"},
     {"file": PER, "old": "return ISODateTimeFormat.appendOffsetElement(buf, Math.abs(offset));",
      "new": "return ISODateTimeFormat.appendOffsetElement(buf, offset < 0 ? -offset : offset);",
      "why": "hop 3 takes the size of a negative offset by negation"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 3267 (mr_lib preview, target org/joda/time/DateTimeZone.java): "
               "tz.DateTimeZoneBuilder (hop 1), format.PeriodFormatterBuilder (hop 2), Period (hop 3), "
               "format.ISODateTimeFormat (hop 4), LocalTime (hop 5, gold). The recipe relaxed its 'distinct from the target "
               "package' rule from hop 3 on (the checkout has fewer than two other-package classes above 1500 lines), so "
               "Period and LocalTime share org.joda.time with DateTimeZone. All five are public top-level classes (Period and "
               "LocalTime are final, which does not affect a static method) in which a static method compiles; every preview "
               "anchor is an outer-class method; none was skipped. The facade calls hop 1 by its fully-qualified name; each "
               "hop imports the next host (DateTimeZoneBuilder already imports DateTimeZone; LocalTime already imports "
               "DateTimeFormatter and ISODateTimeFormat and uses DateTimeConstants from its own package). The gold prints "
               "with ISODateTimeFormat's existing hourMinute, hourMinuteSecond and hourMinuteSecondMillis formatters "
               "(hop 4's host class, not hop 4 itself).",
}
