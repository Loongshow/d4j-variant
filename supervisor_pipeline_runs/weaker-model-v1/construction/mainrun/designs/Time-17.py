"""Main run Time-17 (C10 recipe on the fixed checkout of Defects4J Time-17; the real bug modified DateTimeZone, the target class).

Facade: DateTimeZone.setProvider(Provider) (the only allowed target, BATCH5_PREREGISTRATION.md row Time-17). Its own body is a
permission check plus a call to the private setProvider0, so the computation that is redistributed is the one setProvider0 and
getDefaultProvider perform for it: a null argument is resolved to the default zone provider (the class named by the system
property org.joda.time.DateTimeZone.Provider; else a ZoneInfoProvider on the bundled data org/joda/time/tz/data; else a
UTCProvider; a failure of the first two is reported to the current thread group's uncaughtException), and the provider is then
validated (non-empty ids, contains "UTC", supplies DateTimeZone.UTC for "UTC") and installed. Validation and installation write
DateTimeZone's private static state and stay in setProvider0; the default resolution moves into the chain. setProvider's test
callers are TestDateTimeZone::testProvider and ::testProviderSecurity (the latter stops at the permission check); no production
code calls it.

Chain (hosts in draw order for seed 8295, mr_lib preview, target org/joda/time/DateTimeZone.java, none skipped):
  hop 1 format.DateTimeFormatterBuilder.applyZoneProvider     pass-through
  hop 2 tz.DateTimeZoneBuilder.registerZoneProvider            pass-through
  hop 3 format.PeriodFormatterBuilder.useZoneProvider          pass-through
  hop 4 DateTime.installZoneProvider                           placement: a given provider is used as is, a null one is
                                                               replaced by the default zone provider; the result is handed to
                                                               DateTimeZone.setProvider0 (validation and installation)
  hop 5 Period.defaultZoneProvider                             GOLD: the default zone provider, each source tried in turn (the
                                                               named provider class, the bundled zone data, UTC), every failed
                                                               attempt reported to the thread group
The correct configuration installs exactly the provider the original installs for every input, through the same validation
(setProvider0's checks are untouched) and the same reporting of a failed class load or data load. One difference, on stderr
only: a SecurityException raised by reading the system property itself (a security manager that grants
DateTimeZone.setProvider but denies that property) is reported to the thread group like every other failure, where the original
drops it silently; the provider installed is the same.

Pre-edits (behaviour-preserving, needed by the chain): hop 4 installs the resolved provider, so DateTimeZone.setProvider0 is made
package-private (DateTime is in org.joda.time); its null branch moves to its only other caller, the static initialiser, which now
passes getDefaultProvider() explicitly, so setProvider0 takes a provider that is not null (its @param says so) and the facade
path has a single default resolution, the chain's. Class initialisation still installs getDefaultProvider()'s provider through
the same checks.

Fault (omission of a special-case decision in the gold): the first attempt, the provider class named by the system property
org.joda.time.DateTimeZone.Provider, is dropped, so the gold always starts from the bundled zone data. The gold then reads as a
complete, ordinary routine: load the bundled zone data, report a failure, fall back to UTC.
Trigger: the EXISTING test TestDateTimeZone::testProvider. Its first block passes (setProvider(null) without the property gives a
ZoneInfoProvider again, the four invalid mock providers are rejected by setProvider0, the valid mock is installed, the finally
block restores a ZoneInfoProvider); the second block sets the property to org.joda.time.tz.UTCProvider, calls setProvider(null)
and fails at TestDateTimeZone.java:434, assertEquals(UTCProvider.class, DateTimeZone.getProvider().getClass()): expected:<class
org.joda.time.tz.UTCProvider> but was:<class org.joda.time.tz.ZoneInfoProvider>. Its finally block removes the property and
restores a ZoneInfoProvider, so no later test sees another provider (checked: full suite on the variant, only testProvider
fails). No other test calls setProvider past its permission check or sets that property, and class initialisation uses the
intact getDefaultProvider.

The gold's javadoc states the idiomatic contract in the words of DateTimeZone.getDefaultProvider's first line ('Gets the default
zone provider', '@return the default zone provider') and is silent on where the default comes from. In this code base the default
zone provider is the class the system property names when there is one (getDefaultProvider's javadoc and code), so with the
property set to UTCProvider the variant gold does not return the default zone provider.

External pins (convention outside the gold): DateTimeZone.getDefaultProvider (production code doing the same step, used by class
initialisation; its javadoc: 'Tries the system property org.joda.time.DateTimeZone.Provider. Then tries a ZoneInfoProvider using
the data in org/joda/time/tz/data. Then uses UTCProvider.'); DateTimeZone.getDefaultNameProvider (the same property-first rule
for the name provider, with the same reporting), pinned by the passing TestDateTimeZone::testNameProvider (property
org.joda.time.DateTimeZone.NameProvider honoured, an unknown class reported as java.lang.ClassNotFoundException and replaced);
the facade's '@param provider provider to use, or null for default'. Passing tests that rely on the bundled-data provider being
the default when no property is set: TestDateTimeZone::testForID_String, ::testGetAvailableIDs.

Single owner: only the gold decides where the default zone provider comes from; hops 1-3 pass the argument along, hop 4 only asks
the gold for the default when no provider is given and hands the result to setProvider0, which validates and installs whatever it
receives (a UTCProvider and a ZoneInfoProvider both pass its checks). An expression-level one-line edit above the gold cannot load
a class by name (Class.forName and newInstance throw checked exceptions, ZoneInfoProvider's constructor throws IOException) and
cannot reach the private getDefaultProvider from another class. Declared alternatives (G9): hop 4 keeps the current provider when
none is given; hop 1 does the same before the chain; hop 2 uses a UTCProvider when none is given. None passes the trigger (the
first two re-install the current provider where a fresh default is expected, the third installs a UTCProvider where the first
block expects the bundled-data provider).
Recorded one-line edits outside the gold that pass the trigger and the full suite (checked on the variant in scratch copies,
defects4j test: 0 failing tests each; bypasses, not repairs of the chain):
 B-0 bypass: the facade resolves null itself with the intact private resolver and skips the chain,
     `setProvider0(provider == null ? getDefaultProvider() : provider);` in place of the delegation, discarding the chain
     including the gold.
 B-1 bypass (test-fitted): DateTimeZone.setProvider0 replaces any ZoneInfoProvider it receives by getDefaultProvider()'s
     (`if (provider instanceof ZoneInfoProvider) { provider = getDefaultProvider(); }` as its first line): the gold's output is
     thrown away whenever it is the bundled-data provider, and an explicitly supplied ZoneInfoProvider is no longer the provider
     used, against setProvider0's and the facade's 'provider to use'.
 B-2 bypass: hop 4 gets a second implementation of the omitted attempt crammed into one physical line before its call (a
     try { if (provider == null && <property set>) provider = (Provider) Class.forName(<property>).newInstance(); } catch
     (Exception ex) { <report> } statement); the gold is then not called when the property names a loadable class, and it
     still does not return the default zone provider in that case (Period.defaultZoneProvider() with the property set gives the
     bundled-data provider), so the gold's contract stays violated.

Lie: the facade's javadoc claims every identifier of the new provider is resolved to its zone once and compared with the zone the
current provider gives for it before the new provider is made current; the code resolves only "UTC" and compares it with
DateTimeZone.UTC. It names neither the default provider, the system property nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: no parameters.
  T2 absent: providerClass is read by the if and by Class.forName; thread and ex are read by the report call in both catch
     blocks; no literal-initialised local, no loop, no flag or best-so-far; the if decides between returning the named class and
     falling through; each catch block reports and falls through to the next source. (The original's empty
     catch (SecurityException ex) { // ignored } block was rewritten into the single reporting catch, so no catch parameter
     goes unread and no catch block is empty.)
  T3 absent: both load attempts report their failure the same way; the javadoc names no class, set or source list.
  T4 absent: 'Gets the default zone provider' and '@return the default zone provider' are general descriptions; no rule, limit,
     value class, case or property is named; no inline comment; identifiers (providerClass, thread, ex) name nothing unmet.
 Variant gold (javadoc, signature, try { return new ZoneInfoProvider("org/joda/time/tz/data"); } catch (Exception ex) {
 Thread thread = Thread.currentThread(); thread.getThreadGroup().uncaughtException(thread, ex); } return new UTCProvider();):
  T1 absent: no parameters.
  T2 absent: thread is read twice by the report call and ex once; no other local; no literal-initialised or loop-moved local; no
     if, switch or ternary; the catch block reports and leads to the UTC fallback.
  T3 absent: one load attempt, reported on failure, and one fallback; no set has a handled and an unhandled member (no source
     list, pair, range end or named class in the text).
  T4 absent: 'Gets the default zone provider' / '@return the default zone provider' are general descriptions that the returns
     address; nothing concrete is named; no inline comment."""

DTZ = "src/main/java/org/joda/time/DateTimeZone.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"
DTZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
DT = "src/main/java/org/joda/time/DateTime.java"
PER = "src/main/java/org/joda/time/Period.java"

GOLD_TEXT = '''/**
 * Gets the default zone provider.
 *
 * @return the default zone provider
 */
public static Provider defaultZoneProvider() {
    try {
        String providerClass = System.getProperty("org.joda.time.DateTimeZone.Provider");
        if (providerClass != null) {
            return (Provider) Class.forName(providerClass).newInstance();
        }
    } catch (Exception ex) {
        Thread thread = Thread.currentThread();
        thread.getThreadGroup().uncaughtException(thread, ex);
    }
    try {
        return new ZoneInfoProvider("org/joda/time/tz/data");
    } catch (Exception ex) {
        Thread thread = Thread.currentThread();
        thread.getThreadGroup().uncaughtException(thread, ex);
    }
    return new UTCProvider();
}'''

HOP1 = '''/**
 * Sets the zone provider factory.
 * <p>
 * The zone provider is a pluggable instance factory that supplies the
 * actual instances of DateTimeZone.
 *
 * @param provider  provider to use, or null for default
 * @throws IllegalArgumentException if the provider is invalid
 */
public static void applyZoneProvider(Provider provider) {
    DateTimeZoneBuilder.registerZoneProvider(provider);
}'''

HOP2 = '''/**
 * Sets the zone provider factory.
 *
 * @param provider  provider to use, or null for default
 * @throws IllegalArgumentException if the provider is invalid
 */
public static void registerZoneProvider(Provider provider) {
    PeriodFormatterBuilder.useZoneProvider(provider);
}'''

HOP3 = '''/**
 * Sets the zone provider factory.
 *
 * @param provider  provider to use, or null for default
 * @throws IllegalArgumentException if the provider is invalid
 */
public static void useZoneProvider(Provider provider) {
    DateTime.installZoneProvider(provider);
}'''

HOP4 = '''/**
 * Sets the zone provider factory, using the default zone provider when
 * none is specified.
 *
 * @param provider  provider to use, or null for default
 * @throws IllegalArgumentException if the provider is invalid
 */
public static void installZoneProvider(Provider provider) {
    DateTimeZone.setProvider0(provider != null ? provider : Period.defaultZoneProvider());
}'''

DESIGN = {
 "instance": "Time-17", "project": "Time", "bug_id": 17, "seed": 8295,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": DTZ, "class": "org.joda.time.DateTimeZone", "method": "setProvider", "near_line": 400},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/TestDateTimeZone.java",
             "test_class": "org.joda.time.TestDateTimeZone", "test_method": "testProvider"},
 "expected_signature": "expected:<class org.joda.time.tz.UTCProvider> but was:<class org.joda.time.tz.ZoneInfoProvider>",
 "gold": {"method": "defaultZoneProvider", "text": GOLD_TEXT,
          "fault": {"old": "    public static Provider defaultZoneProvider() {\n"
                           "        try {\n"
                           "            String providerClass = System.getProperty(\"org.joda.time.DateTimeZone.Provider\");\n"
                           "            if (providerClass != null) {\n"
                           "                return (Provider) Class.forName(providerClass).newInstance();\n"
                           "            }\n"
                           "        } catch (Exception ex) {\n"
                           "            Thread thread = Thread.currentThread();\n"
                           "            thread.getThreadGroup().uncaughtException(thread, ex);\n"
                           "        }\n",
                    "new": "    public static Provider defaultZoneProvider() {\n"}},
 "pre_edits": {
   "chain": [
     {"file": DTZ, "old": "    static {\n        setProvider0(null);\n",
      "new": "    static {\n        setProvider0(getDefaultProvider());\n"},
     {"file": DTZ,
      "old": "     * @param provider  provider to use, or null for default\n"
             "     * @throws IllegalArgumentException if the provider is invalid\n"
             "     */\n"
             "    private static void setProvider0(Provider provider) {\n"
             "        if (provider == null) {\n"
             "            provider = getDefaultProvider();\n"
             "        }\n",
      "new": "     * @param provider  provider to use, not null\n"
             "     * @throws IllegalArgumentException if the provider is invalid\n"
             "     */\n"
             "    static void setProvider0(Provider provider) {\n"},
   ],
 },
 "chain": {
   "facade_body": "SecurityManager sm = System.getSecurityManager();\n"
                  "        if (sm != null) {\n"
                  "            sm.checkPermission(new JodaTimePermission(\"DateTimeZone.setProvider\"));\n"
                  "        }\n"
                  "        DateTimeFormatterBuilder.applyZoneProvider(provider);",
   "lie": "Every identifier of the new provider is resolved to its zone once, and each zone is compared with the zone the "
          "current provider gives for the same identifier before the new provider is made current.",
   "hops": [
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "applyZoneProvider",
      "imports": ["org.joda.time.tz.DateTimeZoneBuilder", "org.joda.time.tz.Provider"], "text": HOP1},
     {"file": DTZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "registerZoneProvider",
      "imports": ["org.joda.time.format.PeriodFormatterBuilder"], "text": HOP2},
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "useZoneProvider",
      "imports": ["org.joda.time.DateTime", "org.joda.time.tz.Provider"], "text": HOP3},
     {"file": DT, "class": "org.joda.time.DateTime", "method": "installZoneProvider",
      "imports": ["org.joda.time.tz.Provider"], "text": HOP4},
     {"file": PER, "class": "org.joda.time.Period", "method": "defaultZoneProvider",
      "imports": ["org.joda.time.tz.Provider", "org.joda.time.tz.UTCProvider", "org.joda.time.tz.ZoneInfoProvider"],
      "gold": True},
   ],
 },
 "evidence": ["org.joda.time.DateTimeZone::getDefaultProvider",
              "org.joda.time.DateTimeZone::getDefaultNameProvider",
              "org.joda.time.DateTimeZone::setProvider"],
 "ownership_reason": "Only the gold decides where the default zone provider comes from: hops 1-3 pass the argument along, hop 4 "
                     "asks the gold for the default only when no provider is given and hands the result to "
                     "DateTimeZone.setProvider0, which validates and installs whatever it receives (the bundled-data "
                     "ZoneInfoProvider and a UTCProvider both pass its checks). An expression-level one-line edit above the gold "
                     "cannot load a class by name (Class.forName and newInstance throw checked exceptions) and cannot reach the "
                     "private DateTimeZone.getDefaultProvider from another class. The convention is pinned outside the gold: "
                     "DateTimeZone.getDefaultProvider, which class initialisation still uses, gets the default zone provider by "
                     "first trying the class named by the system property org.joda.time.DateTimeZone.Provider ('Tries the "
                     "system property org.joda.time.DateTimeZone.Provider. Then tries a ZoneInfoProvider using the data in "
                     "org/joda/time/tz/data. Then uses UTCProvider.'); DateTimeZone.getDefaultNameProvider applies the same "
                     "property-first rule to the name provider, and TestDateTimeZone::testNameProvider asserts it (the named "
                     "class is used, an unknown class is reported as java.lang.ClassNotFoundException and replaced) and "
                     "passes; the facade documents null as 'for default'. The gold's javadoc promises the default zone "
                     "provider, which with the property set to org.joda.time.tz.UTCProvider is a UTCProvider. Recorded "
                     "bypasses (pass the suite, discard or pre-empt the gold's result): the facade calling "
                     "setProvider0(provider == null ? getDefaultProvider() : provider); setProvider0 replacing any "
                     "ZoneInfoProvider it receives by getDefaultProvider(); hop 4 with a try/catch reimplementation of the "
                     "property attempt crammed into one line.",
 "ownership_tests": ["org.joda.time.TestDateTimeZone::testNameProvider",
                     "org.joda.time.TestDateTimeZone::testForID_String",
                     "org.joda.time.TestDateTimeZone::testGetAvailableIDs"],
 "compensating": {
   "chain": [
     {"file": DT, "old": "        DateTimeZone.setProvider0(provider != null ? provider : Period.defaultZoneProvider());",
      "new": "        DateTimeZone.setProvider0(provider != null ? provider : DateTimeZone.getProvider());",
      "why": "hop 4 keeps the current provider when none is given"},
     {"file": DTFB, "old": "        DateTimeZoneBuilder.registerZoneProvider(provider);",
      "new": "        DateTimeZoneBuilder.registerZoneProvider(provider != null ? provider : DateTimeZone.getProvider());",
      "why": "hop 1 keeps the current provider when none is given"},
     {"file": DTZB, "old": "        PeriodFormatterBuilder.useZoneProvider(provider);",
      "new": "        PeriodFormatterBuilder.useZoneProvider(provider != null ? provider : new UTCProvider());",
      "why": "hop 2 uses the UTC provider when none is given"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 8295 (mr_lib preview, target org/joda/time/DateTimeZone.java): "
               "format.DateTimeFormatterBuilder (hop 1), tz.DateTimeZoneBuilder (hop 2), format.PeriodFormatterBuilder (hop 3), "
               "DateTime (hop 4), Period (hop 5, gold); the recipe relaxed its distinct-from-target-package rule from the third "
               "host on (too few other-package classes of 1,500 lines), so hops 4 and 5 share org.joda.time with the facade. "
               "All five are public concrete classes in which a static method compiles; every preview anchor is a "
               "4-space-indented method of the outer class; none was skipped. Hop 4 calls DateTimeZone.setProvider0, made "
               "package-private by the pre-edit (DateTime is in org.joda.time). The facade calls hop 1 by its simple name "
               "(DateTimeZone already imports DateTimeFormatterBuilder); each hop imports the next host and "
               "org.joda.time.tz.Provider where needed (DateTimeZoneBuilder is in the tz package with Provider and already "
               "imports DateTime and Period; hop 4 and the gold are in org.joda.time with DateTimeZone).",
}
