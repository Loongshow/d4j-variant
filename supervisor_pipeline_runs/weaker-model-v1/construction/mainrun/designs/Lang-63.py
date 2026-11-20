"""Main run Lang-63 (C10 recipe on the fixed checkout of Defects4J Lang-63; the real bug modified DurationFormatUtils, the
target class here). Facade = DurationFormatUtils.formatDuration(long, String, boolean), the pool's only candidate (31 lines). No
test calls this overload by name; every formatDuration test reaches it through the public API (formatDuration(long, String),
formatDurationHMS, formatDurationISO, formatDurationWords, and formatPeriod for spans under 28 days). The original has no
argument guard, so the facade body is the single delegating call.

Visibility constraint: lexx, the Token class, its accessors and the pattern-letter constants of DurationFormatUtils are
package-private (org.apache.commons.lang.time). Hops 1-4 are drawn in other packages, so they carry only public types
(long millis, int[] fields, String format, boolean padWithZeros, StringBuffer). Only the gold, drawn in FastDateFormat (same
package as the target), touches the tokens.

Chain (hosts in draw order, seed 2894, no substitution):
  hop 1 StringUtils.durationString       fold: breaks the duration into days, hours, minutes, seconds and milliseconds, each
                                          taken from what remains after the larger units (presence-independent breakdown)
  hop 2 builder.ToStringStyle.fieldsToString   pass-through
  hop 3 text.StrBuilder.formatFields     placement: provides the output buffer and returns its text
  hop 4 ArrayUtils.appendFields          pass-through
  hop 5 time.FastDateFormat.appendDuration   GOLD: lexes the format, carries each field the format does not contain into the
                                          next smaller field, then writes the tokens one by one (per-token core)
The correct chain is behaviour-preserving for every tested pattern: the presence-independent breakdown plus the carry equals the
original presence-dependent split, and the per-token writing equals DurationFormatUtils.format for formatDuration's arguments
(years and months zero). It differs only for patterns no caller or test uses (milliseconds placed before seconds, or five or more
S letters after seconds, where the original prints a stray leading '1').

Fault (omission of a special-case step in the gold): the milliseconds of a pattern that also shows seconds are the fraction of
the second and are written with three digits (width 3), whatever the padding flag; the omission drops that step, so the
milliseconds are written like any other number (padded to the field length only when padding is requested). The faulty gold
still reads as a complete routine: carry, then pad each number to its field. The presence flag withSeconds stays in use (it
drives the seconds-to-milliseconds carry, like the three other presence flags), so nothing is left dead.

Trigger: the EXISTING DurationFormatUtilsTest::testFormatDurationISO (formatDurationISO(0L) expected "P0Y0M0DT0H0M0.000S",
got "P0Y0M0DT0H0M0.0S"). It is the only test that formats seconds followed by milliseconds through formatDuration without
three-letter padding: formatDurationHMS / StopWatch.toString use "ss.SSS" with padding (width 3 either way), the other
formatDuration and short formatPeriod patterns have no seconds-then-milliseconds pair, and formatPeriod for spans of 28 days or
more (testFormatPeriodISO, testJiraLang281) uses the untouched DurationFormatUtils.format.

Quiet gold: its javadoc states the contract (the pattern letters of DurationFormatUtils, with which ISO_EXTENDED_FORMAT_PATTERN
gives the ISO8601 period format; carry of fields the format does not contain; years and months written as zero) and is silent
on the fraction step. In the ISO8601 period format "0.1S" denotes 100 ms, so writing 1 ms as "0.1S" violates the contract on
the trigger input. External pins: DurationFormatUtils.format (the sibling writer used by formatPeriod, with its
lastOutputSeconds rule), formatPeriod and its passing testFormatPeriodISO ("...12.001S"), formatDurationISO's javadoc
(ISO8601 period format), and StopWatch.toString (a passing second production caller of the facade, "0:00:00.000").

Single owner: only the gold sees the tokens, so only it knows that the milliseconds follow seconds; hops 1-4 hold an int
breakdown, the format string, the padding flag and the buffer. No doc-consistent one-line edit there can widen the milliseconds
alone: forcing padding pads every field (ISO's yyyy becomes 0000), rewriting the format's S letters has no effect without
padding, and an int field cannot carry leading zeros. Declared alternatives (G9): hop 4 always pads, hop 3 widens a
seconds-then-milliseconds field to SSS, hop 2 pads whenever the format has an S (G9: none absorbs).
Recorded bypasses (format-specific text surgery, not consistent with the hops' documentation):
 B-1 (VERIFIED by the builder on a scratch copy of the variant: full suite 0 failing tests) hop 3 (StrBuilder.formatFields)
     post-processes the text it returns:
     `return buffer.toString().replaceAll("\\.(\\d)S", ".00$1S").replaceAll("\\.(\\d\\d)S", ".0$1S");`
     It re-implements the three-digit fraction after the gold on the output text; it would also rewrite the output of any
     user format that writes a short number between a literal '.' and a literal 'S', so it violates "using the specified format".
 B-2 (not run) a hop that rewrites the caller's format (yyyy -> y and .S -> .SSS together with forced padding, only when
     padding is off) is the same kind of ISO-specific surgery on the format instead of the output.
DurationFormatUtils.format cannot be reached from hops 1-4 (package-private), and formatPeriod recurses into the facade for
spans under 28 days, so no hop can hand the work to the sibling writer.

Lie: the facade's javadoc claims the duration is consumed from its smallest unit upwards and the fields written in one pass
from the end of the format towards its start; the chain breaks the duration down from days to milliseconds and writes the
tokens front to back. It names neither milliseconds nor seconds nor any hop."""

SU = "src/java/org/apache/commons/lang/StringUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
DFU = "src/java/org/apache/commons/lang/time/DurationFormatUtils.java"

GOLD_TEXT = '''/**
 * <p>Appends a duration, given as its days, hours, minutes, seconds and
 * milliseconds, to a buffer in the specified format.</p>
 *
 * <p>The format uses the pattern letters of {@link DurationFormatUtils},
 * with which {@link DurationFormatUtils#ISO_EXTENDED_FORMAT_PATTERN} gives
 * the ISO8601 period format. A field that the format does not contain is
 * carried into the next smaller field, and years and months are written
 * as zero.</p>
 *
 * @param buffer  the buffer to append to
 * @param fields  the days, hours, minutes, seconds and milliseconds
 * @param format  the way in which to format the duration
 * @param padWithZeros  whether to pad the left hand side of numbers with 0's
 */
public static void appendDuration(StringBuffer buffer, int[] fields, String format, boolean padWithZeros) {
    DurationFormatUtils.Token[] tokens = DurationFormatUtils.lexx(format);
    boolean withDays = DurationFormatUtils.Token.containsTokenWithValue(tokens, DurationFormatUtils.d);
    boolean withHours = DurationFormatUtils.Token.containsTokenWithValue(tokens, DurationFormatUtils.H);
    boolean withMinutes = DurationFormatUtils.Token.containsTokenWithValue(tokens, DurationFormatUtils.m);
    boolean withSeconds = DurationFormatUtils.Token.containsTokenWithValue(tokens, DurationFormatUtils.s);
    int days = fields[0];
    int hours = fields[1];
    int minutes = fields[2];
    int seconds = fields[3];
    int milliseconds = fields[4];
    if (!withDays) {
        hours += 24 * days;
    }
    if (!withHours) {
        minutes += 60 * hours;
    }
    if (!withMinutes) {
        seconds += 60 * minutes;
    }
    if (!withSeconds) {
        milliseconds += 1000 * seconds;
    }
    for (int i = 0; i < tokens.length; i++) {
        Object value = tokens[i].getValue();
        if (value instanceof StringBuffer) {
            buffer.append(value.toString());
            continue;
        }
        int number = 0;
        int width = padWithZeros ? tokens[i].getCount() : 0;
        if (value == DurationFormatUtils.d) {
            number = days;
        } else if (value == DurationFormatUtils.H) {
            number = hours;
        } else if (value == DurationFormatUtils.m) {
            number = minutes;
        } else if (value == DurationFormatUtils.s) {
            number = seconds;
        } else if (value == DurationFormatUtils.S) {
            number = milliseconds;
            if (withSeconds) {
                width = 3;
            }
        }
        buffer.append(StringUtils.leftPad(Integer.toString(number), width, '0'));
    }
}'''

FIELDS_DOC = ''' * @param fields  the days, hours, minutes, seconds and milliseconds
 * @param format  the way in which to format the duration
 * @param padWithZeros  whether to pad the left hand side of numbers with 0's'''

HOP1 = '''/**
 * <p>Formats a duration as a String, using the specified format.</p>
 *
 * <p>The duration is split into days, hours, minutes, seconds and
 * milliseconds, each taken from what remains of the duration after the
 * larger ones.</p>
 *
 * @param millis  the duration to format, in milliseconds
 * @param format  the way in which to format the duration
 * @param padWithZeros  whether to pad the left hand side of numbers with 0's
 * @return the formatted duration
 */
public static String durationString(long millis, String format, boolean padWithZeros) {
    long[] units = {DateUtils.MILLIS_PER_DAY, DateUtils.MILLIS_PER_HOUR,
        DateUtils.MILLIS_PER_MINUTE, DateUtils.MILLIS_PER_SECOND, 1};
    int[] fields = new int[units.length];
    long rest = millis;
    for (int i = 0; i < units.length; i++) {
        fields[i] = (int) (rest / units[i]);
        rest = rest - fields[i] * units[i];
    }
    return ToStringStyle.fieldsToString(fields, format, padWithZeros);
}'''

HOP2 = '''/**
 * <p>Formats a duration, given as its days, hours, minutes, seconds and
 * milliseconds, as a String using the specified format.</p>
 *
''' + FIELDS_DOC + '''
 * @return the formatted duration
 */
public static String fieldsToString(int[] fields, String format, boolean padWithZeros) {
    return StrBuilder.formatFields(fields, format, padWithZeros);
}'''

HOP3 = '''/**
 * <p>Formats a duration, given as its days, hours, minutes, seconds and
 * milliseconds, as a String using the specified format.</p>
 *
''' + FIELDS_DOC + '''
 * @return the formatted duration
 */
public static String formatFields(int[] fields, String format, boolean padWithZeros) {
    StringBuffer buffer = new StringBuffer();
    ArrayUtils.appendFields(buffer, fields, format, padWithZeros);
    return buffer.toString();
}'''

HOP4 = '''/**
 * <p>Appends a duration, given as its days, hours, minutes, seconds and
 * milliseconds, to a buffer in the specified format.</p>
 *
 * @param buffer  the buffer to append to
''' + FIELDS_DOC + '''
 */
public static void appendFields(StringBuffer buffer, int[] fields, String format, boolean padWithZeros) {
    FastDateFormat.appendDuration(buffer, fields, format, padWithZeros);
}'''

DESIGN = {
 "instance": "Lang-63", "project": "Lang", "bug_id": 63, "seed": 2894,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": DFU, "class": "org.apache.commons.lang.time.DurationFormatUtils", "method": "formatDuration", "near_line": 126},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/time/DurationFormatUtilsTest.java",
             "test_class": "org.apache.commons.lang.time.DurationFormatUtilsTest", "test_method": "testFormatDurationISO"},
 "expected_signature": "expected:<P0Y0M0DT0H0M0.0[00]S> but was:<P0Y0M0DT0H0M0.0[]S>",
 "gold": {"method": "appendDuration", "text": GOLD_TEXT,
          "fault": {"old": "                number = milliseconds;\n"
                           "                if (withSeconds) {\n"
                           "                    width = 3;\n"
                           "                }",
                    "new": "                number = milliseconds;"}},
 "chain": {
   "facade_body": "return StringUtils.durationString(durationMillis, format, padWithZeros);",
   "lie": "The duration is consumed from its smallest unit upwards, each field of the format taking what remains after the "
          "field below it, and the fields are then written in a single pass from the end of the format towards its start.",
   "hops": [
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "durationString",
      "imports": ["org.apache.commons.lang.builder.ToStringStyle", "org.apache.commons.lang.time.DateUtils"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "fieldsToString",
      "imports": ["org.apache.commons.lang.text.StrBuilder"], "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "formatFields",
      "imports": ["org.apache.commons.lang.ArrayUtils"], "text": HOP3},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "appendFields",
      "imports": ["org.apache.commons.lang.time.FastDateFormat"], "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "appendDuration",
      "imports": ["org.apache.commons.lang.StringUtils"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.time.DurationFormatUtils::format",
              "org.apache.commons.lang.time.DurationFormatUtils::formatPeriod",
              "org.apache.commons.lang.time.DurationFormatUtils::formatDurationISO",
              "org.apache.commons.lang.time.StopWatch::toString"],
 "ownership_reason": "Only the gold sees the tokens of the format, so only it knows that the milliseconds follow seconds and are "
                     "the fraction of the second; hops 1-4 hold an int breakdown, the format string, the padding flag and the "
                     "buffer, and no one-line edit there can widen the milliseconds alone (forced padding also pads yyyy, "
                     "rewriting the S letters does nothing without padding, an int cannot carry leading zeros). The convention "
                     "is pinned outside the gold: DurationFormatUtils.format, the writer formatPeriod uses, adds 1000 and drops "
                     "the leading digit for milliseconds written after seconds (lastOutputSeconds), and testFormatPeriodISO "
                     "expects 'P32Y1M22DT9H11M12.001S' through it; formatDurationISO documents the ISO8601 period format, in "
                     "which '0.1S' means 100 ms; StopWatch.toString (testStopWatchSimpleGet, '0:00:00.000') and "
                     "formatDurationHMS (testFormatDurationHMS, '0:00:00.001') pass through the gold with three-letter padding. "
                     "The gold's javadoc promises the ISO8601 period format for ISO_EXTENDED_FORMAT_PATTERN, which writing 1 ms "
                     "as '0.1S' violates.",
 "ownership_tests": ["org.apache.commons.lang.time.DurationFormatUtilsTest::testFormatPeriodISO",
                     "org.apache.commons.lang.time.DurationFormatUtilsTest::testFormatDurationHMS",
                     "org.apache.commons.lang.time.DurationFormatUtilsTest::testFormatDuration",
                     "org.apache.commons.lang.time.StopWatchTest::testStopWatchSimpleGet"],
 "compensating": {
   "chain": [
     {"file": AU, "old": "FastDateFormat.appendDuration(buffer, fields, format, padWithZeros);",
      "new": "FastDateFormat.appendDuration(buffer, fields, format, true);",
      "why": "hop 4 always pads the numbers with zeros"},
     {"file": SB, "old": "ArrayUtils.appendFields(buffer, fields, format, padWithZeros);",
      "new": "ArrayUtils.appendFields(buffer, fields, org.apache.commons.lang.StringUtils.replace(format, \"s.S\", \"s.SSS\"), padWithZeros);",
      "why": "hop 3 widens a milliseconds field that follows seconds to three letters"},
     {"file": TSS, "old": "return StrBuilder.formatFields(fields, format, padWithZeros);",
      "new": "return StrBuilder.formatFields(fields, format, padWithZeros || format.indexOf('S') >= 0);",
      "why": "hop 2 pads the numbers whenever the format has a milliseconds letter"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2894 (mr_lib preview, n=5, target org/apache/commons/lang/time/DurationFormatUtils.java): "
               "StringUtils (hop 1), builder.ToStringStyle (hop 2), text.StrBuilder (hop 3), ArrayUtils (hop 4), "
               "time.FastDateFormat (hop 5, gold). The host pool holds exactly these five classes (>= 1500 lines), so hop 5 is "
               "'last remaining host' and no substitute exists; none was needed: every hop compiles in its host. "
               "DurationFormatUtils.lexx, the Token class, its accessors and the pattern-letter constants are package-private, "
               "so hops 1-4 (other packages) carry only public types (long, int[], String, boolean, StringBuffer); the gold, in "
               "FastDateFormat (same package as the target), is the only hop that uses the tokens. ToStringStyle is abstract "
               "(static method compiles); FastDateFormat extends java.text.Format and has an explicit serialVersionUID, so the "
               "added static method does not change its serial form.",
}
