"""Main run JacksonDatabind-66 (C10 recipe on the fixed checkout of Defects4J JacksonDatabind-66; the real bug modified
StdKeyDeserializer, the target class).

Facade: StdKeyDeserializer.forType(Class<?>) (the only allowed target, BATCH5_PREREGISTRATION.md row JacksonDatabind-66; the
46-line outer-class method, not the 9-line StringKD.forType). Its only production caller is StdKeyDeserializers.findKeyDeserializer
(the default KeyDeserializers of every deserializer factory), which BasicDeserializerFactory.createKeyDeserializer consults for
every Map key type; no test calls it by name, so tests reach it through ObjectMapper.readValue of a Map type.
Original computation: String and Object give the identity key deserializer StringKD.forType(raw); each of sixteen JDK key types
gets its kind code (UUID, Integer, Long, Date, Calendar, Boolean, Byte, Character, Short, Float, Double, URI, URL, Class, Locale,
Currency); Locale and Currency are constructed with the FromStringDeserializer of their type as helper (StdKeyDeserializer._parse
reads their keys with _deser._deserialize); any other type gives null.

Chain (hosts in draw order for seed 3090, mr_lib preview, target com/fasterxml/jackson/databind/deser/std/StdKeyDeserializer.java,
none skipped):
  hop 1 deser.BeanDeserializerBase.findStdKeyDeserializer      decision: String and Object keys get the identity key deserializer
  hop 2 ObjectMapper.standardKeyDeserializerFor                 pass-through
  hop 3 DeserializationContext.keyDeserializerForRawType        pass-through
  hop 4 deser.BasicDeserializerFactory.stdKeyDeserializerForType pass-through
  hop 5 ObjectReader.constructKeyDeserializer                   GOLD: the per-type core: the kind of each of the sixteen key
                                                                types, the helper of the types read through one, and the
                                                                construction (null for any other type)
The correct configuration returns the original result for every input: the same StringKD singletons for String and Object, the
same kind for each of the sixteen types (the identity tests are written in the order of the kind codes, TYPE_BOOLEAN = 1 to
TYPE_CURRENCY = 16; distinct classes, so the order cannot matter), the same FromStringDeserializer helper for Locale and Currency
and none for the others (new StdKeyDeserializer(kind, raw) is this(kind, raw, null)), and null for every other type, null included.

Fault (one-line omission of a special-case step in the gold): the Currency branch no longer looks up its FromStringDeserializer,
so the Currency key deserializer is constructed without the helper that StdKeyDeserializer._parse reads its keys with. The gold
then reads as an ordinary kind table in which one type, Locale, is constructed with a helper. Trigger: the EXISTING test
TestMapDeserialization::testCurrencyKeyMap: reading {"USD":4} as Map<Currency, Object> reaches _parse(TYPE_CURRENCY), whose
`_deser._deserialize(key, ctxt)` throws a NullPointerException; deserializeKey reports it through handleWeirdKey, and the test fails
with InvalidFormatException "Can not deserialize Map key of type java.util.Currency from String "USD": not a valid representation,
problem: (java.lang.NullPointerException) null". It is the only test with a Currency key (JDKStringLikeTypesTest::testCurrency
reads a Currency VALUE through JdkDeserializers and still passes; testLocaleKeyMap keeps its helper and passes).

The gold's javadoc states the idiomatic contract (the standard key deserializer that reads Map keys of the given type from their
String representation) and is silent on helpers. The Currency key deserializer it returns reads no Currency key at all, so the
variant violates that contract on the trigger input.

External pins (convention outside the gold): StdKeyDeserializer._parse reads TYPE_LOCALE and TYPE_CURRENCY keys with the helper
(`return _deser._deserialize(key, ctxt);`, "unable to parse key as currency"), and the field _deser is documented as the helper
deserializer of "some types"; JdkDeserializers.find gives Currency VALUES exactly that helper
(FromStringDeserializer.findDeserializer(rawType)), pinned by JDKStringLikeTypesTest::testCurrency;
FromStringDeserializer.findDeserializer maps Currency to Std.STD_CURRENCY (Currency.getInstance). testLocaleKeyMap pins the same
helper construction for the Locale key type, testUUIDKeyMap and testClassKeyMap the kinds without one.

Single owner: only the gold constructs the key deserializer, and the helper is a final field set by the constructor, so no hop can
add it to the object the gold returns; hops 1-4 hold only the key type and hand back the gold's result. Declared alternatives
(G9): hop 1 passes Currency keys through as Strings (the test then gets a String key); hop 2 leaves Currency to the String-based
lookup (BasicDeserializerFactory finds no String constructor or valueOf and reports no key deserializer); hop 4 maps a primitive
key type to its wrapper (no effect on Currency). None absorbs the trigger.
Recorded bypasses (one-line edits that pass the trigger and the full suite by replacing the gold's result, not repairs of the
chain):
 B-0 the facade restores its original body (the sixteen-type cascade), discarding all five hops.
 B-1 any of hops 1-4 constructs the Currency key deserializer itself, e.g. hop 2
     `return (raw == Currency.class) ? new StdKeyDeserializer(StdKeyDeserializer.TYPE_CURRENCY, raw, com.fasterxml.jackson.databind.deser.std.FromStringDeserializer.findDeserializer(raw)) : DeserializationContext.keyDeserializerForRawType(raw);`
     (a second implementation of the gold's construction for the trigger's type; the gold's result is never used for it).
 B-2 StdKeyDeserializer._parse (not a hop, pristine) falls back to its own parse when the helper is missing:
     `return (_deser == null) ? Currency.getInstance(key) : _deser._deserialize(key, ctxt);` in the TYPE_CURRENCY case (the plain
     `return Currency.getInstance(key);` does not compile: the case's catch (IOException) then catches nothing that can be
     thrown). A second implementation of the helper's STD_CURRENCY parse inside the key deserializer, while _parse keeps reading
     the Locale kind through its helper only.
 B-3 the constructor StdKeyDeserializer(int, Class, FromStringDeserializer) (not a hop) looks a helper up itself when given none:
     `_deser = (deser != null) ? deser : FromStringDeserializer.findDeserializer(cls);`. It replaces the helper the gold passes
     with a second implementation of the gold's helper lookup (and makes the gold's own Locale lookup redundant); every other
     creator of a StdKeyDeserializer (StringKD, EnumKD, StringCtorKeyDeserializer, StringFactoryKeyDeserializer through
     StdKeyDeserializers) passes no helper and relies on the constructor storing what it is given.
 B-1, B-2 and B-3 were each checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests.

Lie: the facade's javadoc claims the key type is looked up by its class name in a static table of the supported key types that
is filled once when the class is loaded; the code compares the class with each supported type in turn, uses no class name and
builds no table. It names neither helpers nor Currency nor any hop.

Pre-edits (behaviour-preserving, needed by the recipe; all in StdKeyDeserializer.java):
 - forType has no javadoc, and rewrite_facade appends the lie only inside an existing javadoc, so a one-sentence javadoc in the
   class's voice is added above it ("Factory method for finding the standard key deserializer for given key type, if there is
   one; returns null for other types.").
 - None of the five hosts is in package deser.std, so the gold cannot call the protected constructor and hop 1 cannot reach the
   package-private StringKD: the three-argument constructor StdKeyDeserializer(int, Class, FromStringDeserializer) and the nested
   class StringKD are made public. No modifier changes behaviour (no test or production code checks them).

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: raw is compared in every branch and passed to findDeserializer and to the constructor.
  T2 absent: kind is assigned in every branch that reaches the constructor; deser starts at null and is assigned in the Locale and
     Currency branches; both reach the constructor call; every branch assigns a different kind, the else returns null.
  T3 absent: all sixteen kind codes TYPE_BOOLEAN..TYPE_CURRENCY of the closed type-code set are assigned; the helper is given to
     two of the sixteen kinds, which is the convention (only those two kinds read a helper) and not a left-out member. The
     omission leaves it on exactly one of them (see below), so no two-of-three-or-more pattern survives into the variant.
  T4 absent: the javadoc names only the general contract and the null result, which the else branch produces.
 Variant gold (javadoc, signature, the sixteen-branch cascade with `deser = FromStringDeserializer.findDeserializer(raw);` in the
 Locale branch only, `else { return null; }`, `return new StdKeyDeserializer(kind, raw, deser);`):
  T1 absent: raw is read in all sixteen identity tests, by findDeserializer and by the constructor; each changes the result.
  T2 absent: kind is not literal-initialised and is assigned in every branch before the constructor (no loop); deser is
     initialised to null but reassigned in the Locale branch and read by the constructor, so it is neither dead nor frozen; no
     branch is empty or duplicates another (each assigns a different kind code; the else returns null); no loop, flag, counter or
     best-so-far.
  T3 absent: (a) every member of the closed type-code set TYPE_* (sixteen codes) gets its branch; the helper lookup is a
     treatment of exactly one member (TYPE_LOCALE) of that set of sixteen, and the gold does not name the class of types that
     take a helper ('one member of a larger unnamed set'); (b) no pair halves or range ends are read; (c) the gold's text names
     no class it handles in part (no 'helper', 'String-based' or similar class is named); (d) no member is read and left without
     a treatment that a visible sibling gets: every type is read once and given its kind like all the others.
  T4 absent: 'the standard key deserializer that reads Map keys of given type from their String representation' is a general
     description that the cascade and the constructor address; '@return ... or null if no standard key deserializer exists for
     it' is met by the else branch; no limit, value class, case or property is named; no inline comment; the identifiers raw,
     kind and deser name nothing the body does not meet."""

KD = "src/main/java/com/fasterxml/jackson/databind/deser/std/StdKeyDeserializer.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
DC = "src/main/java/com/fasterxml/jackson/databind/DeserializationContext.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
STD = "com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer"

RETURN_DOC = ''' * @param raw Key type
 *
 * @return Key deserializer for the type, or null if no standard key
 *   deserializer exists for it
 */'''

GOLD_TEXT = '''/**
 * Factory method for constructing the standard key deserializer that
 * reads Map keys of given type from their String representation.
 *
''' + RETURN_DOC + '''
public static StdKeyDeserializer constructKeyDeserializer(Class<?> raw)
{
    int kind;
    FromStringDeserializer<?> deser = null;
    if (raw == Boolean.class) {
        kind = StdKeyDeserializer.TYPE_BOOLEAN;
    } else if (raw == Byte.class) {
        kind = StdKeyDeserializer.TYPE_BYTE;
    } else if (raw == Short.class) {
        kind = StdKeyDeserializer.TYPE_SHORT;
    } else if (raw == Character.class) {
        kind = StdKeyDeserializer.TYPE_CHAR;
    } else if (raw == Integer.class) {
        kind = StdKeyDeserializer.TYPE_INT;
    } else if (raw == Long.class) {
        kind = StdKeyDeserializer.TYPE_LONG;
    } else if (raw == Float.class) {
        kind = StdKeyDeserializer.TYPE_FLOAT;
    } else if (raw == Double.class) {
        kind = StdKeyDeserializer.TYPE_DOUBLE;
    } else if (raw == Locale.class) {
        kind = StdKeyDeserializer.TYPE_LOCALE;
        deser = FromStringDeserializer.findDeserializer(raw);
    } else if (raw == Date.class) {
        kind = StdKeyDeserializer.TYPE_DATE;
    } else if (raw == Calendar.class) {
        kind = StdKeyDeserializer.TYPE_CALENDAR;
    } else if (raw == UUID.class) {
        kind = StdKeyDeserializer.TYPE_UUID;
    } else if (raw == URI.class) {
        kind = StdKeyDeserializer.TYPE_URI;
    } else if (raw == URL.class) {
        kind = StdKeyDeserializer.TYPE_URL;
    } else if (raw == Class.class) {
        kind = StdKeyDeserializer.TYPE_CLASS;
    } else if (raw == Currency.class) {
        kind = StdKeyDeserializer.TYPE_CURRENCY;
        deser = FromStringDeserializer.findDeserializer(raw);
    } else {
        return null;
    }
    return new StdKeyDeserializer(kind, raw, deser);
}'''

HOP1 = '''/**
 * Helper method for finding the standard key deserializer for given
 * key type. String and Object keys are not converted: both use the
 * key deserializer that returns the key String as is.
 *
''' + RETURN_DOC + '''
public static StdKeyDeserializer findStdKeyDeserializer(Class<?> raw)
{
    if (raw == String.class || raw == Object.class) {
        return StdKeyDeserializer.StringKD.forType(raw);
    }
    return ObjectMapper.standardKeyDeserializerFor(raw);
}'''

PASS_DOC = '''/**
 * Helper method for finding the standard key deserializer for given
 * key type, other than String or Object.
 *
''' + RETURN_DOC

HOP2 = PASS_DOC + '''
public static StdKeyDeserializer standardKeyDeserializerFor(Class<?> raw)
{
    return DeserializationContext.keyDeserializerForRawType(raw);
}'''

HOP3 = PASS_DOC + '''
public static StdKeyDeserializer keyDeserializerForRawType(Class<?> raw)
{
    return BasicDeserializerFactory.stdKeyDeserializerForType(raw);
}'''

HOP4 = PASS_DOC + '''
public static StdKeyDeserializer stdKeyDeserializerForType(Class<?> raw)
{
    return ObjectReader.constructKeyDeserializer(raw);
}'''

DESIGN = {
 "instance": "JacksonDatabind-66", "project": "JacksonDatabind", "bug_id": 66, "seed": 3090,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": KD, "class": STD, "method": "forType", "near_line": 69},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/TestMapDeserialization.java",
             "test_class": "com.fasterxml.jackson.databind.deser.TestMapDeserialization", "test_method": "testCurrencyKeyMap"},
 "expected_signature": "problem: (java.lang.NullPointerException) null",
 "gold": {"method": "constructKeyDeserializer", "text": GOLD_TEXT,
          "fault": {"old": "            kind = StdKeyDeserializer.TYPE_CURRENCY;\n"
                           "            deser = FromStringDeserializer.findDeserializer(raw);",
                    "new": "            kind = StdKeyDeserializer.TYPE_CURRENCY;"}},
 "pre_edits": {
   "chain": [
     {"file": KD,
      "old": "    protected StdKeyDeserializer(int kind, Class<?> cls, FromStringDeserializer<?> deser) {",
      "new": "    public StdKeyDeserializer(int kind, Class<?> cls, FromStringDeserializer<?> deser) {"},
     {"file": KD,
      "old": "    }\n\n    public static StdKeyDeserializer forType(Class<?> raw)\n    {",
      "new": "    }\n\n    /**\n"
             "     * Factory method for finding the standard key deserializer for given\n"
             "     * key type, if there is one; returns null for other types.\n"
             "     */\n"
             "    public static StdKeyDeserializer forType(Class<?> raw)\n    {"},
     {"file": KD,
      "old": "    final static class StringKD extends StdKeyDeserializer\n",
      "new": "    public final static class StringKD extends StdKeyDeserializer\n"},
   ],
 },
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.deser.BeanDeserializerBase.findStdKeyDeserializer(raw);",
   "lie": "The key type is looked up by its class name in a static table of the supported key types, which is filled "
          "once when this class is loaded.",
   "hops": [
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "findStdKeyDeserializer",
      "imports": [STD], "text": HOP1},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "standardKeyDeserializerFor",
      "imports": [STD], "text": HOP2},
     {"file": DC, "class": "com.fasterxml.jackson.databind.DeserializationContext", "method": "keyDeserializerForRawType",
      "imports": [STD], "text": HOP3},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "stdKeyDeserializerForType",
      "imports": [], "text": HOP4},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "constructKeyDeserializer",
      "imports": ["java.net.URI", "com.fasterxml.jackson.databind.deser.std.FromStringDeserializer", STD], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer::_parse",
              "com.fasterxml.jackson.databind.deser.std.JdkDeserializers::find",
              "com.fasterxml.jackson.databind.deser.std.FromStringDeserializer::findDeserializer"],
 "ownership_reason": "Only the gold constructs the key deserializer, and the helper deserializer is a final field set by its "
                     "constructor: hops 1-4 hold only the key type and return the gold's object unchanged, so none of them can "
                     "give the Currency key deserializer its helper short of constructing a second one. Choosing the helper is "
                     "the factory's step, not the key deserializer's: the constructor stores the helper it is given (every other "
                     "creator, StringKD, EnumKD and the String-constructor and factory-method key deserializers made by "
                     "StdKeyDeserializers, passes none), and _parse only reads keys through it; a fallback lookup in the "
                     "constructor or a second Currency parse in _parse would re-implement the gold's helper step outside it. "
                     "The convention is pinned "
                     "outside the gold: StdKeyDeserializer._parse reads TYPE_LOCALE and TYPE_CURRENCY keys with the helper "
                     "(_deser._deserialize(key, ctxt), 'unable to parse key as currency'), and the field _deser is the helper "
                     "deserializer of 'some types'; JdkDeserializers.find reads Currency values with exactly that helper "
                     "(FromStringDeserializer.findDeserializer(rawType); JDKStringLikeTypesTest.testCurrency passes); "
                     "FromStringDeserializer.findDeserializer maps Currency to Std.STD_CURRENCY (Currency.getInstance); "
                     "TestMapDeserialization.testLocaleKeyMap pins the same construction for the Locale key type. The gold's "
                     "javadoc promises the standard key deserializer that reads Map keys of the given type from their String "
                     "representation; the Currency key deserializer it returns in the variant reads no Currency key at all.",
 "ownership_tests": ["com.fasterxml.jackson.databind.deser.TestMapDeserialization::testLocaleKeyMap",
                     "com.fasterxml.jackson.databind.deser.JDKStringLikeTypesTest::testCurrency",
                     "com.fasterxml.jackson.databind.deser.TestMapDeserialization::testUUIDKeyMap",
                     "com.fasterxml.jackson.databind.deser.TestMapDeserialization::testClassKeyMap"],
 "compensating": {
   "chain": [
     {"file": BDB, "old": "if (raw == String.class || raw == Object.class) {",
      "new": "if (raw == String.class || raw == Object.class || raw == Currency.class) {",
      "why": "hop 1 passes Currency keys through as Strings"},
     {"file": OM, "old": "return DeserializationContext.keyDeserializerForRawType(raw);",
      "new": "return (raw == Currency.class) ? null : DeserializationContext.keyDeserializerForRawType(raw);",
      "why": "hop 2 leaves Currency keys to the String-based key deserializer lookup"},
     {"file": BDF, "old": "return ObjectReader.constructKeyDeserializer(raw);",
      "new": "return ObjectReader.constructKeyDeserializer(raw.isPrimitive() ? ClassUtil.wrapperType(raw) : raw);",
      "why": "hop 4 maps a primitive key type to its wrapper type"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 3090 (mr_lib preview, target com/fasterxml/jackson/databind/deser/std/"
               "StdKeyDeserializer.java): deser.BeanDeserializerBase (hop 1), ObjectMapper (hop 2), DeserializationContext "
               "(hop 3), deser.BasicDeserializerFactory (hop 4), ObjectReader (hop 5, gold). All five are public top-level "
               "classes in which a static method compiles (BeanDeserializerBase, DeserializationContext and "
               "BasicDeserializerFactory are abstract, which does not affect a static method); Jackson uses 4-space "
               "indentation, so every preview anchor lies in the outer class; none was skipped. No host is in package "
               "deser.std, so behaviour-preserving pre-edits make StdKeyDeserializer's three-argument constructor and its "
               "nested class StringKD public; forType had no javadoc, so a pre-edit adds a one-sentence javadoc for the lie "
               "to be appended to. The facade calls hop 1 by its fully-qualified name; hops 1-3 import StdKeyDeserializer, "
               "hop 4 sees it through its existing deser.std.* import, and the gold imports java.net.URI, "
               "FromStringDeserializer and StdKeyDeserializer.",
}
