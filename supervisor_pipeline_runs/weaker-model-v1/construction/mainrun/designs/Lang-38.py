"""Main run Lang-38 (C10 recipe on the fixed checkout of Defects4J Lang-38; the real bug modified FastDateFormat, the target class).

Facade: FastDateFormat.getInstance(String pattern, TimeZone timeZone) (allowed target FastDateFormat.getInstance,
BATCH4_PREREGISTRATION.md row Lang-38). Of the five getInstance overloads, this one is used: the three-argument overload is the
creation path of every formatter in the code base (the other getInstance overloads, getDateInstance, getTimeInstance,
getDateTimeInstance and DateFormatUtils all end in it), so a chain under it would be reached by nearly every FastDateFormat and
DateFormatUtils test and no omission could be caught by a single test (gate G5). getInstance(String, TimeZone) has no production
caller; its only callers are FastDateFormatTest::test_getInstance_String_TimeZone and FastDateFormatTest::testLang538 (the real
Lang-38 trigger). The no-argument, (String) and (String, Locale) overloads were set aside: their computation is the same
one-line delegation, and the (String) and (String, Locale) overloads also serve DateFormatUtils' constant formatters.
Original computation of the facade: getInstance(pattern, timeZone, null), i.e. under the FastDateFormat class lock, build the
requested formatter (pattern, time zone, default locale), return an equal formatter from the class's instance cache if there is
one, and otherwise initialise the requested formatter (init(): the pattern is parsed into its formatting rules) and register it
in the cache.

Chain (hosts in draw order for seed 8037, mr_lib preview, target org/apache/commons/lang3/time/FastDateFormat.java, none
skipped):
  hop 1 text.StrBuilder.dateFormatFor        placement: the default locale (null) is placed for the two-argument request
  hop 2 StringUtils.dateFormatter            pass-through
  hop 3 builder.ToStringStyle.formatterFor   pass-through
  hop 4 ArrayUtils.patternFormat             pass-through
  hop 5 time.DateUtils.formatInstance        GOLD: the creation of the formatter: the requested formatter, the lookup of an
                                             equal one, and on a miss its initialisation and registration
The correct configuration returns the original result for every input: the same constructor call, the same cache (the class's
own cInstanceCache), the same lookup, initialisation and registration, under the same lock.

Pre-edits (behaviour-preserving, needed by the chain): (1) cInstanceCache loses its `private` modifier (package access), so that
the gold, in DateUtils in the same package, can consult and fill the class's own cache; no class outside
org.apache.commons.lang3.time can see it. (2) The facade gains `synchronized`, as the three-argument overload and the
getDateInstance / getTimeInstance / getDateTimeInstance overloads have, so the chain reads and writes the shared HashMap under the
same FastDateFormat class lock the original delegation took.

Fault (one-line omission in the gold, inside the decision taken on a cache miss): `format.init();` is dropped, so a formatter
created through the chain is registered and returned without its rules (mRules stays null, mMaxLengthEstimate 0). Trigger: the
EXISTING test FastDateFormatTest::testLang538 (getInstance("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", GMT), then format(cal)); format
reaches applyRules, whose `mRules.length` throws java.lang.NullPointerException. It is the only test that formats with a
formatter obtained through the facade: test_getInstance_String_TimeZone only compares identities, time zones and the override
flag, which the constructor sets, and still passes (format3 and format4 are the same registered instance). No other test reaches
the chain, and no other test asks for a key the chain registers (the trigger's pattern with a forced GMT zone and an unforced
locale is unique to it; the MM/DD/yyyy and MM-DD-yyyy keys with a forced zone are only requested through the facade), so the
shared cache carries no uninitialised formatter into another test.

The gold's javadoc states the idiomatic contract (a formatter instance for the pattern, time zone and locale; @return a date/time
formatter for the pattern; the three-argument overload's own wording) and is silent on initialisation. The variant returns an
object that cannot format at all, which violates that contract on the trigger input.

External pins (convention outside the gold): the three-argument FastDateFormat.getInstance takes the same step
(`format.init();  // convert shell format into usable one` before `cInstanceCache.put`); FastDateFormat.readObject re-initialises
every deserialised formatter (`in.defaultReadObject(); init();`), pinned by FastDateFormatTest::testLang303; init's own javadoc
'Initializes the instance for first use'; DateFormatUtils.format formats directly with the formatter getInstance returns
(DateFormatUtilsTest::testSMTP); FastDateFormatTest::testLowYearPadding formats with a formatter from the (String) overload.

Single owner: only the gold creates a formatter, and only code in org.apache.commons.lang3.time can call FastDateFormat's
protected constructor and protected init() or see cInstanceCache. Hops 1-4 live in org.apache.commons.lang3.text,
org.apache.commons.lang3 and org.apache.commons.lang3.builder and are not subclasses of FastDateFormat, so none of them can
initialise the returned formatter; re-serialising it (SerializationUtils.clone runs readObject and so init) gives a new
instance on every call and fails test_getInstance_String_TimeZone (assertSame(format3, format4)). Declared alternatives (G9):
hop 1 names the default locale explicitly, hop 3 hands on its own copy of the time zone, hop 4 resolves the zone again by its
identifier; each still returns an uninitialised formatter and the trigger still throws.
Recorded bypasses (one-line edits above the gold that pass the trigger and the full suite by discarding the gold's creation):
 B-0 the facade's original body `return getInstance(pattern, timeZone, null);`, or any of hops 1-4 returning
     FastDateFormat.getInstance(pattern, timeZone, locale) (hop 1: ..., null), the intact three-argument sibling: the chain below
     that hop, the gold included, becomes dead.
 B-1 a hop first calls FastDateFormat.getInstance(pattern, timeZone, locale) and then the next hop: the sibling creates,
     initialises and registers the formatter, the gold always finds it in the cache, and its creation branch never runs (the
     result is the sibling's instance).
 B-2 a hop re-requests through the sibling with the settings the gold's result reports
     (FastDateFormat.getInstance(f.getPattern(), f.getTimeZone(), f.getLocale())): the result is the sibling's formatter (with a
     forced locale), the gold's is used only for its getters.
 B-3 the facade calls init() on whatever the chain returns, on every call: shared formatters are re-parsed on every request,
     contrary to init's 'for first use', and the gold itself still returns an unusable formatter.
 Checked on the variant in scratch copies (defects4j test, full suite): B-0 at hop 4, B-1 at hop 3 and B-3 each give 0 failing
 tests; a serialisation round trip at hop 4 (SerializationUtils.clone of the gold's result) fails
 test_getInstance_String_TimeZone (assertSame), so it is not a repair.
Off-chain alternative considered (R-1): a lazy `if (mRules == null) { init(); }` at the top of FastDateFormat.applyRules also
gives 0 failing tests. It is not a repair consistent with the class: FastDateFormat is documented as 'a fast and thread-safe
version of SimpleDateFormat ... especially useful in multi-threaded server environments', its formatters are shared through the
instance cache, and rules built on first use would be written into a shared instance without any lock (applyRules and the format
methods run unsynchronised; mRules is neither final nor volatile), so another thread could see the rules array before its
contents. The class's own convention is eager: the three-argument getInstance converts every 'shell format into usable one'
before caching and returning it, and readObject re-initialises a restored formatter before anyone can use it; the format methods
read mRules unguarded because of it. The gold is where the chain creates the formatter, so it is where that step belongs.

Lie: the facade's javadoc claims the time zone is first reduced to its fixed offset at the current instant and formatters are
shared by pattern and offset, so zones with the same offset share one formatter; the code compares time zones with
TimeZone.equals (Atlantic/Reykjavik and GMT, both offset 0, get different formatters) and computes no offset. It names neither
initialisation nor rules nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; requested = new FastDateFormat(pattern, timeZone, locale); format = cache.get(requested); if (format ==
 null) { format = requested; format.init(); cache.put(format, format); } return format;):
  T1 absent: pattern, timeZone and locale are all passed to the constructor, which makes the requested formatter and the lookup key.
  T2 absent: requested is read by the lookup and assigned to format; format is returned; no literal-initialised local, no loop;
     the if assigns, initialises and registers on a miss and does nothing on a hit, two different effects.
  T3 absent: no enumeration, pair, range or value class; get and put of the cache are both present.
  T4 absent: the javadoc names no rule, bound, value class or case: 'a formatter instance using the specified pattern, time zone
     and locale' and '@return a date/time formatter for the pattern' are general descriptions the constructor line addresses;
     '@param pattern the pattern, not null' is a caller precondition; '@param timeZone / locale ... of the formatter' name
     nothing the body does not pass on. No @throws clause, no inline comment. Rewritten from the three-argument overload's
     text: its '@throws IllegalArgumentException if pattern is invalid or null' and 'optional time zone, overrides time zone of
     formatted date' (checks and an override that no line of the gold performs; the constructor and the format methods do)
     and its local name `emptyFormat` (a state the code changes) were not carried over.
 Variant gold (the same without `format.init();`):
  T1 absent: pattern, timeZone and locale still reach the constructor and so the returned formatter and the lookup key.
  T2 absent: requested is read by get and assigned to format; format is returned; the if still assigns and registers on a miss
     and does nothing on a hit; no frozen local, no loop.
  T3 absent: no set of which a member is handled and a sibling is not; the cache is both read and written.
  T4 absent: no phrase names something the body visibly fails to meet; nothing in the gold's text mentions initialising, rules
     or parsing, and 'a date/time formatter for the pattern' is addressed by the constructor call with the pattern."""

FDF = "src/java/org/apache/commons/lang3/time/FastDateFormat.java"
SB = "src/java/org/apache/commons/lang3/text/StrBuilder.java"
SU = "src/java/org/apache/commons/lang3/StringUtils.java"
TSS = "src/java/org/apache/commons/lang3/builder/ToStringStyle.java"
AU = "src/java/org/apache/commons/lang3/ArrayUtils.java"
DU = "src/java/org/apache/commons/lang3/time/DateUtils.java"

GOLD_TEXT = '''/**
 * <p>Gets a formatter instance using the specified pattern, time zone
 * and locale.</p>
 *
 * @param pattern  the pattern, not null
 * @param timeZone  the time zone of the formatter
 * @param locale  the locale of the formatter
 * @return a date/time formatter for the pattern
 */
public static FastDateFormat formatInstance(String pattern, TimeZone timeZone, Locale locale) {
    FastDateFormat requested = new FastDateFormat(pattern, timeZone, locale);
    FastDateFormat format = FastDateFormat.cInstanceCache.get(requested);
    if (format == null) {
        format = requested;
        format.init();
        FastDateFormat.cInstanceCache.put(format, format);
    }
    return format;
}'''

HOP1 = '''/**
 * Gets a date/time formatter using the specified pattern and time zone
 * in the default locale.
 *
 * @param pattern  the pattern, compatible with <code>SimpleDateFormat</code>
 * @param timeZone  the time zone, overrides the time zone of the formatted date
 * @return a date/time formatter for the pattern
 */
public static FastDateFormat dateFormatFor(String pattern, TimeZone timeZone) {
    return StringUtils.dateFormatter(pattern, timeZone, null);
}'''

HOP2 = '''/**
 * <p>Gets a date/time formatter using the specified pattern, time zone
 * and locale.</p>
 *
 * @param pattern  the pattern, compatible with <code>SimpleDateFormat</code>
 * @param timeZone  optional time zone, overrides the time zone of the formatted date
 * @param locale  optional locale, overrides the system locale
 * @return a date/time formatter for the pattern
 */
public static FastDateFormat dateFormatter(String pattern, TimeZone timeZone, Locale locale) {
    return ToStringStyle.formatterFor(pattern, timeZone, locale);
}'''

HOP3 = '''/**
 * <p>Gets a date/time formatter using the specified pattern, time zone
 * and locale.</p>
 *
 * @param pattern  the pattern, compatible with <code>SimpleDateFormat</code>
 * @param timeZone  optional time zone, overrides the time zone of the formatted date
 * @param locale  optional locale, overrides the system locale
 * @return a date/time formatter for the pattern
 */
public static FastDateFormat formatterFor(String pattern, TimeZone timeZone, Locale locale) {
    return ArrayUtils.patternFormat(pattern, timeZone, locale);
}'''

HOP4 = '''/**
 * <p>Gets a date/time formatter using the specified pattern, time zone
 * and locale.</p>
 *
 * @param pattern  the pattern, compatible with <code>SimpleDateFormat</code>
 * @param timeZone  optional time zone, overrides the time zone of the formatted date
 * @param locale  optional locale, overrides the system locale
 * @return a date/time formatter for the pattern
 */
public static FastDateFormat patternFormat(String pattern, TimeZone timeZone, Locale locale) {
    return DateUtils.formatInstance(pattern, timeZone, locale);
}'''

DESIGN = {
 "instance": "Lang-38", "project": "Lang", "bug_id": 38, "seed": 8037,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "getInstance", "near_line": 181},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang3/time/FastDateFormatTest.java",
             "test_class": "org.apache.commons.lang3.time.FastDateFormatTest", "test_method": "testLang538"},
 "expected_signature": "java.lang.NullPointerException",
 "gold": {"method": "formatInstance", "text": GOLD_TEXT,
          "fault": {"old": "            format = requested;\n"
                           "            format.init();\n"
                           "            FastDateFormat.cInstanceCache.put(format, format);",
                    "new": "            format = requested;\n"
                           "            FastDateFormat.cInstanceCache.put(format, format);"}},
 "pre_edits": {
   "chain": [
     {"file": FDF,
      "old": "    private static final Map<FastDateFormat, FastDateFormat> cInstanceCache = new HashMap<FastDateFormat, FastDateFormat>(7);",
      "new": "    static final Map<FastDateFormat, FastDateFormat> cInstanceCache = new HashMap<FastDateFormat, FastDateFormat>(7);"},
     {"file": FDF,
      "old": "    public static FastDateFormat getInstance(String pattern, TimeZone timeZone) {",
      "new": "    public static synchronized FastDateFormat getInstance(String pattern, TimeZone timeZone) {"},
   ],
 },
 "chain": {
   "facade_body": "return org.apache.commons.lang3.text.StrBuilder.dateFormatFor(pattern, timeZone);",
   "lie": "The time zone is first reduced to the fixed offset that it has at the current instant, and formatters are then "
          "shared by pattern and offset, so that zones with the same offset share one formatter.",
   "hops": [
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "dateFormatFor",
      "imports": ["java.util.TimeZone", "org.apache.commons.lang3.StringUtils", "org.apache.commons.lang3.time.FastDateFormat"],
      "text": HOP1},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "dateFormatter",
      "imports": ["java.util.Locale", "java.util.TimeZone", "org.apache.commons.lang3.builder.ToStringStyle",
                  "org.apache.commons.lang3.time.FastDateFormat"],
      "text": HOP2},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "formatterFor",
      "imports": ["java.util.Locale", "java.util.TimeZone", "org.apache.commons.lang3.ArrayUtils",
                  "org.apache.commons.lang3.time.FastDateFormat"],
      "text": HOP3},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "patternFormat",
      "imports": ["java.util.Locale", "java.util.TimeZone", "org.apache.commons.lang3.time.DateUtils",
                  "org.apache.commons.lang3.time.FastDateFormat"],
      "text": HOP4},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "formatInstance",
      "imports": ["java.util.Locale"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.time.FastDateFormat::getInstance",
              "org.apache.commons.lang3.time.FastDateFormat::readObject",
              "org.apache.commons.lang3.time.DateFormatUtils::format"],
 "ownership_reason": "Only the gold creates a formatter: it alone (DateUtils, in FastDateFormat's package) can call the protected "
                     "constructor and the protected init() and see the class's instance cache, and on a miss it returns and "
                     "registers the formatter it made. Hops 1-4 (packages text, lang3 and builder, no subclass of "
                     "FastDateFormat) only pass the pattern, time zone and locale down and the formatter up; none of them can "
                     "initialise it, and a serialisation round trip (which runs readObject and so init) yields a new instance on "
                     "every call, which test_getInstance_String_TimeZone rejects (assertSame). The convention is pinned outside "
                     "the gold: the three-argument FastDateFormat.getInstance initialises every formatter it creates before "
                     "caching and returning it ('convert shell format into usable one'); FastDateFormat.readObject re-initialises "
                     "every deserialised formatter (testLang303 formats with one); init is documented as 'Initializes the "
                     "instance for first use'; DateFormatUtils.format formats directly with the formatter getInstance returns "
                     "(testSMTP), as testLowYearPadding does with the (String) overload. The gold's javadoc promises a date/time "
                     "formatter for the pattern; the variant returns one that cannot format (NullPointerException in "
                     "applyRules). Edits above the gold that call the intact three-argument overload (instead of the next hop, "
                     "or before it so the gold always hits the cache) pass the suite but replace the gold's formatter with the "
                     "sibling's: bypasses, not repairs of the chain. A lazy initialisation inside FastDateFormat.applyRules "
                     "(if (mRules == null) init();) also passes the suite, but it is not consistent with the class: FastDateFormat "
                     "is documented as thread-safe for multi-threaded use and its formatters are shared through the instance "
                     "cache, so rules built on first use would be written into a shared instance without any lock (the format "
                     "methods run unsynchronised and mRules is neither final nor volatile); the class's convention, pinned by the "
                     "three-argument getInstance ('convert shell format into usable one') and readObject, is that whoever "
                     "creates or restores a formatter initialises it before handing it out, and the format methods read mRules "
                     "unguarded because of it.",
 "ownership_tests": ["org.apache.commons.lang3.time.FastDateFormatTest::testLang303",
                     "org.apache.commons.lang3.time.FastDateFormatTest::testLowYearPadding",
                     "org.apache.commons.lang3.time.FastDateFormatTest::test_getInstance_String_TimeZone",
                     "org.apache.commons.lang3.time.DateFormatUtilsTest::testSMTP"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "return StringUtils.dateFormatter(pattern, timeZone, null);",
      "new": "return StringUtils.dateFormatter(pattern, timeZone, java.util.Locale.getDefault());",
      "why": "hop 1 names the default locale explicitly instead of leaving it to the formatter"},
     {"file": TSS, "old": "return ArrayUtils.patternFormat(pattern, timeZone, locale);",
      "new": "return ArrayUtils.patternFormat(pattern, (TimeZone) timeZone.clone(), locale);",
      "why": "hop 3 hands on its own copy of the time zone"},
     {"file": AU, "old": "return DateUtils.formatInstance(pattern, timeZone, locale);",
      "new": "return DateUtils.formatInstance(pattern, TimeZone.getTimeZone(timeZone.getID()), locale);",
      "why": "hop 4 resolves the time zone again by its identifier"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 8037 (mr_lib preview, target org/apache/commons/lang3/time/FastDateFormat.java): "
               "text.StrBuilder (hop 1), StringUtils (hop 2), builder.ToStringStyle (hop 3), ArrayUtils (hop 4), time.DateUtils "
               "(hop 5, gold; drawn as the last remaining host of the five-class pool). All five are public top-level classes in "
               "which a static method compiles (ToStringStyle is abstract, which does not affect a static method); every preview "
               "anchor lies in the outer class, not in a nested one; none was skipped. The gold host shares the package of "
               "FastDateFormat, which the creation step needs (protected constructor and init, package-access cache); the other "
               "four hosts cannot reach them. The facade calls hop 1 by its fully-qualified name; each hop imports the next host, "
               "FastDateFormat, TimeZone and (hops 2-5) Locale.",
}
