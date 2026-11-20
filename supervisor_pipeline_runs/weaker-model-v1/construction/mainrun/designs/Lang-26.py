"""Main run Lang-26 (C10 recipe on the fixed checkout of Defects4J Lang-26; target class FastDateFormat, the class the real bug
modified).

Facade: FastDateFormat.getDateTimeInstance(int, int, TimeZone, Locale) (pool candidate 3; the 4-arg overload that the other
three getDateTimeInstance overloads delegate to). The other two candidates were set aside:
 - getInstance(String, TimeZone, Locale) has no decision that exactly one test catches: its only steps are the shell
   construction, the cache lookup, init() and the cache put, and dropping init() or the put fails many tests in ten files
   (every assertSame on two getInstance calls, every format test).
 - getDateInstance(int, TimeZone, Locale) is reached by two tests that both observe its cache key
   (test_changeDefault_Locale_DateInstance and testShortDateStyleWithLocales, the latter asking SHORT for US and then for sv_SE),
   so a locale-keying omission there fails two tests (gate G5).
getDateTimeInstance is reached by exactly one existing test, FastDateFormatTest::test_changeDefault_Locale_DateTimeInstance, and
by no production code other than its own overloads.

The facade body becomes one delegating call (the original has no argument guard). Its computation is redistributed along a
five-hop chain drawn with the instance seed 6244 (mr_lib preview, draw order, no substitution):
  hop 1 StringUtils.styleFormat           placement: resolves a missing locale to the default locale
  hop 2 text.StrBuilder.formatOfStyles    pass-through
  hop 3 SystemUtils.localizedFormat       decision: a locale without a SimpleDateFormat pattern (ClassCastException) is reported
                                          as IllegalArgumentException("No date time pattern for locale: ...")
  hop 4 builder.ToStringStyle.standardFormat   pass-through
  hop 5 time.DateUtils.formatterFor       GOLD: the per-request core: builds the cache key (styles, optional time zone, locale),
                                          looks it up in the date/time formatter cache, and on a miss creates the formatter
                                          from the locale's date/time pattern and stores it.
The chain performs the original computation in the original order (locale default, key, lookup, pattern + getInstance, put,
ClassCastException translation). The key is a List instead of the private nested Pair (not visible outside FastDateFormat);
List equality is element-wise like Pair's, and keys with and without a time zone differ in length, so the cache behaves the
same. Pre-edits (behaviour-preserving, chain only): the date/time formatter cache moves from FastDateFormat
(private static cDateTimeInstanceCache, used only by the facade) to a private static field of the gold host DateUtils
(dateTimeFormats, same type and initial capacity), so only the gold can read or change it (the vacated declaration line in
FastDateFormat is left blank, which also lets mr_spec derive the edit: a unique pure line deletion does not round-trip). Redesign 1: the first build (READY)
left the cache in FastDateFormat with package access; there the facade itself could add `cDateTimeInstanceCache.clear();`
(checked: the trigger then passes, because getInstance's own cache keeps instances identical), a one-line edit at a non-gold
method that disables the per-style cache. Threading the map through the four foreign hosts was rejected for the same reason
(any hop could pass a fresh map).

Fault (one-line omission in the gold): `key.add(locale);` is dropped, so the cache key holds only the styles and the optional
time zone, and a request for one locale returns the formatter cached for another. Trigger:
FastDateFormatTest::test_changeDefault_Locale_DateTimeInstance (default US: format1 = (FULL, FULL, GERMANY) is created and
cached under [FULL, FULL]; format2 = (FULL, FULL) for US hits that entry; assertSame(Locale.US, format2.getLocale()) fails with
"expected same:<en_US> was not:<de_DE>"). No other test reaches getDateTimeInstance, so only the trigger newly fails.
Fault type: a keying step in the per-request decision rather than a special-case step. The special-case candidates were not
valid: the default-locale substitution can be pre-filtered by any earlier hop in one line (`locale == null ? Locale.getDefault()
: locale` in a delegating call), which is a competing repair; the optional time-zone key component is caught by no test (every
test passes a null time zone).

The gold's javadoc states the idiomatic contract (a formatter for the specified styles, time zone and locale; instances are
cached) and is silent on how the key is built. External pins: the sibling factories key their caches by the locale --
getDateInstance (`key = new Pair(key, locale)` after the same default substitution), getTimeInstance (adds the locale to the key)
and getInstance (the instance cache is keyed by a shell whose equals compares the locale); passing tests
test_changeDefault_Locale_DateInstance (identical assertions through getDateInstance), testShortDateStyleWithLocales (one style,
two locales, two patterns), test_getInstance_String_Locale and test_getInstance_String_TimeZone_Locale.

Single owner: only the gold sees the key and the cache. Earlier hops cannot pre-filter the omission (the key ignores the locale
whatever locale they pass, and the styles and time zone cannot carry it), and later hops receive only the formatter, so they can
recover only by creating a second formatter (a bypass). The cache is a private field of DateUtils, so neither the facade nor any
other hop can clear, replace or inspect it. Declared alternatives (G9): hop 1 leaves the locale unresolved (the trigger still hits
the GERMANY entry), hop 3 resolves a missing time zone to the default (the key still ignores the locale), hop 4 passes the
default locale (format1 is then created for US).
Recorded bypasses (not competing repairs; each replaces the gold's result with a second implementation):
 B-1 hop 1 creates the formatter itself: `return FastDateFormat.getInstance(((java.text.SimpleDateFormat) java.text.DateFormat
     .getDateTimeInstance(dateStyle, timeStyle, locale)).toPattern(), timeZone, locale);` (hops 2-5 dead; getInstance's own cache
     keeps instances identical). Checked on the redesigned variant: trigger passes, full suite 0 failures.
 B-2 hop 4 re-creates the formatter when the gold's result has another locale (multi-statement, same second implementation).
 B-0 the facade calls getInstance itself with the default-resolved locale and that locale's date/time pattern (the B-1 edit one
     level up), making all five hops dead.

Lie: the facade's javadoc claims the pattern is recovered by formatting a fixed reference date and mapping each formatted field
back to its pattern letters; the code takes the pattern from SimpleDateFormat.toPattern(). It names neither the cache, the key,
the locale handling nor any hop."""

FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
SYS = "src/main/java/org/apache/commons/lang3/SystemUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"

PARAMS = ''' * @param dateStyle  date style: FULL, LONG, MEDIUM, or SHORT
 * @param timeStyle  time style: FULL, LONG, MEDIUM, or SHORT
 * @param timeZone  optional time zone, overrides time zone of
 *  formatted date'''

GOLD_TEXT = '''/**
 * <p>Gets a date/time formatter instance using the specified styles,
 * time zone and locale.</p>
 *
 * <p>Formatter instances are cached and shared.</p>
 *
''' + PARAMS + '''
 * @param locale  the locale to use, not null
 * @return a localized standard date/time formatter
 * @throws ClassCastException if the Locale has no date/time pattern
 *  defined
 */
public static FastDateFormat formatterFor(final int dateStyle, final int timeStyle, final TimeZone timeZone, final Locale locale) {
    final List<Object> key = new ArrayList<Object>(4);
    key.add(Integer.valueOf(dateStyle));
    key.add(Integer.valueOf(timeStyle));
    if (timeZone != null) {
        key.add(timeZone);
    }
    key.add(locale);
    FastDateFormat format = dateTimeFormats.get(key);
    if (format == null) {
        final SimpleDateFormat formatter = (SimpleDateFormat) DateFormat.getDateTimeInstance(dateStyle, timeStyle, locale);
        format = FastDateFormat.getInstance(formatter.toPattern(), timeZone, locale);
        dateTimeFormats.put(key, format);
    }
    return format;
}'''

HOP_DOC = '''/**
 * <p>Gets a date/time formatter instance using the specified styles,
 * time zone and locale.</p>
 *
''' + PARAMS + '''
 * @param locale  the locale to use, not null
 * @return a localized standard date/time formatter'''

DESIGN = {
 "instance": "Lang-26", "project": "Lang", "bug_id": 26, "seed": 6244,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "getDateTimeInstance", "near_line": 457},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/time/FastDateFormatTest.java",
             "test_class": "org.apache.commons.lang3.time.FastDateFormatTest",
             "test_method": "test_changeDefault_Locale_DateTimeInstance"},
 "expected_signature": "expected same:<en_US> was not:<de_DE>",
 "gold": {"method": "formatterFor", "text": GOLD_TEXT,
          "fault": {"old": "        if (timeZone != null) {\n            key.add(timeZone);\n        }\n        key.add(locale);",
                    "new": "        if (timeZone != null) {\n            key.add(timeZone);\n        }"}},
 "pre_edits": {
   "chain": [{"file": FDF,
              "old": "    private static final Map<Object, FastDateFormat> cDateTimeInstanceCache = new HashMap<Object, FastDateFormat>(7);",
              "new": ""},
             {"file": DU,
              "old": "    public final static int SEMI_MONTH = 1001;\n",
              "new": "    public final static int SEMI_MONTH = 1001;\n\n"
                     "    /**\n     * The date/time formatters created so far.\n     */\n"
                     "    private static final Map<Object, FastDateFormat> dateTimeFormats = new HashMap<Object, FastDateFormat>(7);\n"}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.lang3.StringUtils.styleFormat(dateStyle, timeStyle, timeZone, locale);",
   "lie": "The pattern is obtained by formatting a fixed reference date with the java.text.DateFormat of the requested styles "
          "and mapping each field of the formatted text back to the pattern letters that produce it.",
   "hops": [
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "styleFormat",
      "imports": ["java.util.TimeZone", "org.apache.commons.lang3.text.StrBuilder", "org.apache.commons.lang3.time.FastDateFormat"],
      "text": '''/**
 * <p>Gets a date/time formatter instance using the specified styles,
 * time zone and locale, the default locale being used when no locale
 * is given.</p>
 *
''' + PARAMS + '''
 * @param locale  optional locale, overrides system locale
 * @return a localized standard date/time formatter
 */
public static FastDateFormat styleFormat(final int dateStyle, final int timeStyle, final TimeZone timeZone, Locale locale) {
    if (locale == null) {
        locale = Locale.getDefault();
    }
    return StrBuilder.formatOfStyles(dateStyle, timeStyle, timeZone, locale);
}'''},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "formatOfStyles",
      "imports": ["java.util.Locale", "java.util.TimeZone", "org.apache.commons.lang3.time.FastDateFormat"],
      "text": HOP_DOC + '''
 */
public static FastDateFormat formatOfStyles(final int dateStyle, final int timeStyle, final TimeZone timeZone, final Locale locale) {
    return SystemUtils.localizedFormat(dateStyle, timeStyle, timeZone, locale);
}'''},
     {"file": SYS, "class": "org.apache.commons.lang3.SystemUtils", "method": "localizedFormat",
      "imports": ["java.util.Locale", "java.util.TimeZone", "org.apache.commons.lang3.builder.ToStringStyle",
                  "org.apache.commons.lang3.time.FastDateFormat"],
      "text": HOP_DOC + '''
 * @throws IllegalArgumentException if the Locale has no date/time
 *  pattern defined
 */
public static FastDateFormat localizedFormat(final int dateStyle, final int timeStyle, final TimeZone timeZone, final Locale locale) {
    try {
        return ToStringStyle.standardFormat(dateStyle, timeStyle, timeZone, locale);
    } catch (ClassCastException ex) {
        throw new IllegalArgumentException("No date time pattern for locale: " + locale);
    }
}'''},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "standardFormat",
      "imports": ["java.util.Locale", "java.util.TimeZone", "org.apache.commons.lang3.time.DateUtils",
                  "org.apache.commons.lang3.time.FastDateFormat"],
      "text": HOP_DOC + '''
 */
public static FastDateFormat standardFormat(final int dateStyle, final int timeStyle, final TimeZone timeZone, final Locale locale) {
    return DateUtils.formatterFor(dateStyle, timeStyle, timeZone, locale);
}'''},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "formatterFor",
      "imports": ["java.text.DateFormat", "java.util.ArrayList", "java.util.HashMap", "java.util.List", "java.util.Locale",
                  "java.util.Map"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.time.FastDateFormat::getDateInstance", "org.apache.commons.lang3.time.FastDateFormat::getTimeInstance",
              "org.apache.commons.lang3.time.FastDateFormat::getInstance"],
 "ownership_reason": "Only the gold builds the cache key and reads the date/time formatter cache (a private field of "
                     "DateUtils, out of reach of the facade and the other hops). Once the key ignores the locale, a request "
                     "for one locale is served the formatter cached for another: earlier hops cannot pre-filter it (the key drops "
                     "whatever locale they pass, and the styles and time zone cannot carry it) and later hops receive only the "
                     "formatter, so they can recover only by creating a second one. The sibling factories key their caches by the "
                     "locale: getDateInstance adds the resolved locale to its key, getTimeInstance adds the given locale, and "
                     "getInstance keys its cache by a shell whose equals compares the locale; test_changeDefault_Locale_DateInstance "
                     "asserts the identical expectations through getDateInstance and testShortDateStyleWithLocales expects two "
                     "locales of one style to give two formatters.",
 "ownership_tests": ["org.apache.commons.lang3.time.FastDateFormatTest::test_changeDefault_Locale_DateInstance",
                     "org.apache.commons.lang3.time.FastDateFormatTest::testShortDateStyleWithLocales",
                     "org.apache.commons.lang3.time.FastDateFormatTest::test_getInstance_String_Locale",
                     "org.apache.commons.lang3.time.FastDateFormatTest::test_getInstance_String_TimeZone_Locale"],
 "compensating": {
   "chain": [
     {"file": SU, "old": "        return StrBuilder.formatOfStyles(dateStyle, timeStyle, timeZone, locale);",
      "new": "        return StrBuilder.formatOfStyles(dateStyle, timeStyle, timeZone, null);",
      "why": "hop 1 leaves the locale unresolved"},
     {"file": SYS, "old": "            return ToStringStyle.standardFormat(dateStyle, timeStyle, timeZone, locale);",
      "new": "            return ToStringStyle.standardFormat(dateStyle, timeStyle, timeZone == null ? TimeZone.getDefault() : timeZone, locale);",
      "why": "hop 3 resolves a missing time zone to the default time zone"},
     {"file": TSS, "old": "        return DateUtils.formatterFor(dateStyle, timeStyle, timeZone, locale);",
      "new": "        return DateUtils.formatterFor(dateStyle, timeStyle, timeZone, Locale.getDefault());",
      "why": "hop 4 passes the default locale"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 6244 (mr_lib preview, n=5): StringUtils, text.StrBuilder, SystemUtils, "
               "builder.ToStringStyle, time.DateUtils; all five are public concrete classes and every hop compiles there, so no "
               "host was skipped. The gold host DateUtils shares the target's package (the draw relaxed the distinct-package "
               "constraint for host 5); the date/time formatter cache moves into it as a private field (pre-edit).",
}
