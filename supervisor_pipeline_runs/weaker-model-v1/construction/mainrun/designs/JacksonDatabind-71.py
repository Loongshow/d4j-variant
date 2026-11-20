"""Main run JacksonDatabind-71 (C10 recipe on the fixed checkout of Defects4J JacksonDatabind-71; the real bug modified
StdKeyDeserializer, the target class).

Facade: StdKeyDeserializer.forType(Class<?>) (the only allowed target, BATCH5_PREREGISTRATION.md row 101; FACADE REUSE: the same
method is the facade of JacksonDatabind-66, recorded as facade_reuse_of; it changes nothing in the build). The 9-line pool row with
the same name is StringKD.forType, the nested String key deserializer's own factory; it is not the allowed target (a
package-private class with a private constructor and a three-way identity test, nothing to split into a chain).
Original computation: a key class that is String, Object or CharSequence gets the String key deserializer
(StringKD.forType(raw), which keeps raw as its nominal key class); each of 14 further classes (UUID, Integer, Long, Date, Calendar,
Boolean, Byte, Character, Short, Float, Double, URI, URL, Class) is mapped to its TYPE_* kind code and gets new
StdKeyDeserializer(kind, raw); Locale and Currency get a kind code plus the from-String helper deserializer
(FromStringDeserializer.findDeserializer); every other class gives null (BasicDeserializerFactory.createKeyDeserializer then
falls back to a String constructor or factory, and DeserializerCache reports a missing key deserializer if there is none).

Chain (hosts in draw order for seed 2365, mr_lib preview, target com/fasterxml/jackson/databind/deser/std/StdKeyDeserializer.java;
the pool has exactly five hosts, none skipped):
  hop 1 util.TokenBuffer.keyDeserializerFor                pass-through
  hop 2 deser.BasicDeserializerFactory.findStdKeyDeserializer pass-through
  hop 3 ObjectMapper.standardKeyDeserializer               pass-through
  hop 4 deser.BeanDeserializerBase.keyDeserializerOf        pass-through
  hop 5 ObjectReader.stdKeyDeserializer                    GOLD: the per-class decision (String equivalents, the 16 kind
                                                           codes, the helper deserializer for Locale and Currency, null)
forType's whole computation is one decision over the key class, so it cannot be redistributed into a fold or a placement
step without splitting the set of kind codes over two methods (each half would then show the other half's codes as missing
members of the TYPE_* type code, checklist T3). Hops 1-4 are therefore pure pass-throughs, each documented as returning a
deserializer that reports raw as its key class. The correct configuration returns exactly the original result for every input
(same identity tests in the same order, same kind codes, same constructors, same helper lookup, same null).

Fault (one-line omission in the gold's decision): the CharSequence disjunct is dropped from the String-equivalent test, so a
CharSequence key class falls through every case to `return null`. createKeyDeserializer's fallback finds no String constructor
or factory on the CharSequence interface, and DeserializerCache._handleUnknownKeyDeserializer throws. Trigger: the EXISTING test
TestMapDeserialization::testcharSequenceKeyMap (readValue of {"a":"b"} as Map<CharSequence,String>) fails with
"Can not find a (Map) Key deserializer for type [simple type, class java.lang.CharSequence]". It is the only test with a
CharSequence key type; String and Object keys (every other map test) still take the same branch.

The gold's javadoc states the idiomatic contract (the key deserializer to use for keys of the given class, if one found; null if
not; the house wording of DeserializerFactory.createKeyDeserializer) and is silent on CharSequence. A key deserializer for
CharSequence keys exists in the code base (StringKD keeps any nominal key class, and its third branch `new StringKD(nominalType)`
is reachable only through the String-equivalent branch), so returning null violates that contract on the trigger input.
External pins: BasicDeserializerFactory.findDefaultDeserializer does the same step on the value side ("Object (untyped), String
equivalents": String and CharSequence get StringDeserializer.instance; TestJdkTypes::testCharSequence passes);
BasicDeserializerFactory._handleSingleArgumentConstructor and _handleSingleArgumentFactory accept a String or a CharSequence
parameter as a String creator; StdKeyDeserializer$StringKD.forType keeps a nominal key class other than String and Object.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold
(ObjectReader.stdKeyDeserializer after the omission):
 Correct gold: T1 absent (raw decides every test and is passed to every constructor); T2 absent (kind is assigned in every
  non-returning branch and read by the final constructor, both deser locals are constructor arguments, every branch has its own
  effect); T3 absent (all 16 TYPE_* codes of StdKeyDeserializer are produced, all eight wrapper classes are handled, Locale and
  Currency both get the helper; the String-equivalent test is not a closed set); T4 absent (no rule, bound, value class or case is
  named). The original's two inline comments ("first common types", "then less common ones") were not carried into the gold, so
  no comment names a grouping. Nothing else needed rewriting.
 Variant gold:
  T1 absent: raw is read in every identity test, in StringKD.forType(raw) and in both constructors; it decides the result. There
     is no argument check.
  T2 absent: `int kind;` has no initialiser and is assigned in each of the 14 kind branches, then read by `new
     StdKeyDeserializer(kind, raw)`; the two `deser` locals are constructor arguments; there is no loop, so no cursor, counter,
     flag or best-so-far; every branch, including `else { return null; }`, has a distinct effect.
  T3 absent: the TYPE_* type code is fully covered (UUID, INT, LONG, DATE, CALENDAR, BOOLEAN, BYTE, CHAR, SHORT, FLOAT, DOUBLE,
     URI, URL, CLASS, LOCALE, CURRENCY: 16 of 16); the eight primitive wrappers are all handled; Locale and Currency both get the
     helper; URI and URL both have codes. The String-equivalent test (String, Object) is not a closed set by the closure rule (no
     enum, type code or named format fixes its members, and the gold names no class it belongs to); no pair or range end is
     involved.
  T4 absent: the javadoc says "finding the key deserializer to use for keys of the given class", "@param raw Class of the keys"
     and "@return Key deserializer to use, if one found; null if not": general descriptions that the cascade and its final
     `return null` address; no rule, limit, value class or case is named; there is no inline comment; the identifiers (raw, kind,
     deser) name nothing the body does not meet.

Single owner: only the gold decides which key classes get which deserializer; hops 1-4 pass the class down and the deserializer
(or null) back. Declared alternatives (G9), none of which reaches CharSequence: hop 1 maps a primitive key class to its wrapper
(the normalisation StdKeyDeserializers.findKeyDeserializer does before calling forType); hop 2 maps an interface key class to its
first super-interface (CharSequence has none); hop 3 retries with the superclass when nothing is found (an interface has none).
Recorded one-line edits above the gold that pass the trigger (not repairs of the chain):
 B-1 bypass: a hop (or the facade) answers CharSequence itself, e.g. hop 3
     `if (raw == CharSequence.class) { return StdKeyDeserializer.StringKD.forType(raw); }` before its delegation: on the trigger
     input the gold is never called, a second implementation of the gold's decision (as Math-55's B-1).
 B-2 alias (not doc-consistent at a hop): a hop passes String.class down for CharSequence, e.g. hop 3
     `return BeanDeserializerBase.keyDeserializerOf(raw == CharSequence.class ? String.class : raw);` (checked on the variant in
     a scratch copy: trigger passes, full suite 0 failing tests); the gold's shared String deserializer then comes back, whose
     key class is String, contradicting that hop's own @return ("which reports raw as its key class") and the StringKD
     convention of keeping the nominal key class. The same alias one level above the chain, in
     StdKeyDeserializers.findKeyDeserializer next to its primitive-to-wrapper step
     (`if (raw == CharSequence.class) { raw = String.class; }`, also checked: trigger passes, full suite 0 failing tests), leaves
     forType itself returning null for CharSequence and hands a deserializer configured for String to a CharSequence key type;
     no hop documentation is on that edit's path, so it is recorded as the main ownership risk for the auditor.
 B-3 bypass: BasicDeserializerFactory.createKeyDeserializer special-cases a CharSequence key type before or after the provider
     loop (returns a String key deserializer itself), discarding the chain's answer.

Lie: the facade's javadoc claims the class is looked up by its name in a hash table of the supported key classes that is filled
once when the class is initialized; the chain compares class identities in an if-else cascade and builds no table and reads no
name. It names neither CharSequence nor String equivalents nor any step that is omitted nor any hop.

Pre-edits (behaviour-preserving, needed by the recipe; all in StdKeyDeserializer.java):
 - forType had no javadoc, so rewrite_facade could not append its sentence; a one-sentence description in the voice of the sister
   factory FromStringDeserializer.findDeserializer ("Factory method for ...") is added above it.
 - the two constructors and the nested StringKD class are widened from protected / package-private to public: the gold lives in
   another package (com.fasterxml.jackson.databind) and must construct the same deserializers forType constructed. No code path
   changes.

Concern for reviewers: the omitted disjunct is exactly the change that the real Defects4J bug JacksonDatabind-71 fixed (issue
#1506, the D4J patch removes `|| raw == CharSequence.class` from forType); the trigger is the real bug's trigger test. Every other
one-line omission in this cascade either leaves a TYPE_* code or a wrapper class missing while its siblings are handled (T3), a
helper deserializer dead or frozen (T2), or breaks many tests (Object) / is recovered by the String-constructor fallback
(String). A model that remembers the real fix could point at forType (the facade) from memory."""

KD = "src/main/java/com/fasterxml/jackson/databind/deser/std/StdKeyDeserializer.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"

GOLD_TEXT = '''/**
 * Helper method for finding the key deserializer to use for keys of
 * the given class.
 *
 * @param raw Class of the keys
 *
 * @return Key deserializer to use, if one found; null if not
 */
public static StdKeyDeserializer stdKeyDeserializer(Class<?> raw)
{
    int kind;
    if (raw == String.class || raw == Object.class || raw == CharSequence.class) {
        return StdKeyDeserializer.StringKD.forType(raw);
    } else if (raw == UUID.class) {
        kind = StdKeyDeserializer.TYPE_UUID;
    } else if (raw == Integer.class) {
        kind = StdKeyDeserializer.TYPE_INT;
    } else if (raw == Long.class) {
        kind = StdKeyDeserializer.TYPE_LONG;
    } else if (raw == Date.class) {
        kind = StdKeyDeserializer.TYPE_DATE;
    } else if (raw == Calendar.class) {
        kind = StdKeyDeserializer.TYPE_CALENDAR;
    } else if (raw == Boolean.class) {
        kind = StdKeyDeserializer.TYPE_BOOLEAN;
    } else if (raw == Byte.class) {
        kind = StdKeyDeserializer.TYPE_BYTE;
    } else if (raw == Character.class) {
        kind = StdKeyDeserializer.TYPE_CHAR;
    } else if (raw == Short.class) {
        kind = StdKeyDeserializer.TYPE_SHORT;
    } else if (raw == Float.class) {
        kind = StdKeyDeserializer.TYPE_FLOAT;
    } else if (raw == Double.class) {
        kind = StdKeyDeserializer.TYPE_DOUBLE;
    } else if (raw == URI.class) {
        kind = StdKeyDeserializer.TYPE_URI;
    } else if (raw == URL.class) {
        kind = StdKeyDeserializer.TYPE_URL;
    } else if (raw == Class.class) {
        kind = StdKeyDeserializer.TYPE_CLASS;
    } else if (raw == Locale.class) {
        FromStringDeserializer<?> deser = FromStringDeserializer.findDeserializer(Locale.class);
        return new StdKeyDeserializer(StdKeyDeserializer.TYPE_LOCALE, raw, deser);
    } else if (raw == Currency.class) {
        FromStringDeserializer<?> deser = FromStringDeserializer.findDeserializer(Currency.class);
        return new StdKeyDeserializer(StdKeyDeserializer.TYPE_CURRENCY, raw, deser);
    } else {
        return null;
    }
    return new StdKeyDeserializer(kind, raw);
}'''

HOP1 = '''/**
 * Helper method for finding the key deserializer to use for keys of
 * the given class.
 *
 * @param raw Class of the keys
 *
 * @return Key deserializer to use, which reports <code>raw</code> as its
 *   key class, if one found; null if not
 */
public static StdKeyDeserializer keyDeserializerFor(Class<?> raw)
{
    return BasicDeserializerFactory.findStdKeyDeserializer(raw);
}'''

HOP2 = '''/**
 * Method called to find the standard key deserializer to use for
 * keys of the given class.
 *
 * @param raw Class of the keys
 *
 * @return Key deserializer to use, which reports <code>raw</code> as its
 *   key class, if one found; null if not
 */
public static StdKeyDeserializer findStdKeyDeserializer(Class<?> raw)
{
    return ObjectMapper.standardKeyDeserializer(raw);
}'''

HOP3 = '''/**
 * Convenience method for finding the key deserializer to use for keys
 * of the given class, without explicit context.
 *
 * @param raw Class of the keys
 *
 * @return Key deserializer to use, which reports <code>raw</code> as its
 *   key class, if one found; null if not
 */
public static StdKeyDeserializer standardKeyDeserializer(Class<?> raw) {
    return BeanDeserializerBase.keyDeserializerOf(raw);
}'''

HOP4 = '''/**
 * Helper method for finding the key deserializer to use for keys of
 * the given class.
 *
 * @param raw Class of the keys
 *
 * @return Key deserializer to use, which reports <code>raw</code> as its
 *   key class, if one found; null if not
 */
public static StdKeyDeserializer keyDeserializerOf(Class<?> raw)
{
    return ObjectReader.stdKeyDeserializer(raw);
}'''

FACADE_DOC_OLD = "    public static StdKeyDeserializer forType(Class<?> raw)\n"
FACADE_DOC_NEW = ("    /**\n"
                  "     * Factory method for finding the key deserializer to use for keys of\n"
                  "     * the given class; returns null if there is none.\n"
                  "     */\n"
                  "    public static StdKeyDeserializer forType(Class<?> raw)\n")

DESIGN = {
 "instance": "JacksonDatabind-71", "project": "JacksonDatabind", "bug_id": 71, "seed": 2365,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade_reuse_of": ["JacksonDatabind-66"],
 "facade": {"file": KD, "class": "com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer", "method": "forType", "near_line": 77},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/TestMapDeserialization.java",
             "test_class": "com.fasterxml.jackson.databind.deser.TestMapDeserialization",
             "test_method": "testcharSequenceKeyMap"},
 "expected_signature": "Can not find a (Map) Key deserializer for type [simple type, class java.lang.CharSequence]",
 "gold": {"method": "stdKeyDeserializer", "text": GOLD_TEXT,
          "fault": {"old": "        if (raw == String.class || raw == Object.class || raw == CharSequence.class) {\n"
                           "            return StdKeyDeserializer.StringKD.forType(raw);",
                    "new": "        if (raw == String.class || raw == Object.class) {\n"
                           "            return StdKeyDeserializer.StringKD.forType(raw);"}},
 "pre_edits": {
   "chain": [
     {"file": KD, "old": FACADE_DOC_OLD, "new": FACADE_DOC_NEW},
     {"file": KD, "old": "    protected StdKeyDeserializer(int kind, Class<?> cls) {",
      "new": "    public StdKeyDeserializer(int kind, Class<?> cls) {"},
     {"file": KD, "old": "    protected StdKeyDeserializer(int kind, Class<?> cls, FromStringDeserializer<?> deser) {",
      "new": "    public StdKeyDeserializer(int kind, Class<?> cls, FromStringDeserializer<?> deser) {"},
     {"file": KD, "old": "    final static class StringKD extends StdKeyDeserializer",
      "new": "    public final static class StringKD extends StdKeyDeserializer"},
   ],
 },
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.util.TokenBuffer.keyDeserializerFor(raw);",
   "lie": "The class is looked up by its name in a hash table of the supported key classes, which is filled once when "
          "this class is initialized.",
   "hops": [
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "keyDeserializerFor",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory",
                  "com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer"], "text": HOP1},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "findStdKeyDeserializer",
      "imports": [], "text": HOP2},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "standardKeyDeserializer",
      "imports": ["com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer"], "text": HOP3},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "keyDeserializerOf",
      "imports": ["com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer"], "text": HOP4},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "stdKeyDeserializer",
      "imports": ["java.net.URI", "com.fasterxml.jackson.databind.deser.std.FromStringDeserializer",
                  "com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory::findDefaultDeserializer",
              "com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer$StringKD::forType",
              "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory::_handleSingleArgumentConstructor",
              "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory::_handleSingleArgumentFactory"],
 "ownership_reason": "Only the gold decides which key classes get which key deserializer: hops 1-4 pass the key class down "
                     "and the deserializer (or null) back, and each documents that the deserializer it returns reports raw as "
                     "its key class. The gold's String-equivalent branch gives String and Object keys the String key "
                     "deserializer but lets a CharSequence key class fall through to null, so no key deserializer is found for "
                     "Map<CharSequence, ...> although one exists: StdKeyDeserializer$StringKD.forType keeps any nominal key "
                     "class other than String and Object (its third branch, new StringKD(nominalType), is reachable only "
                     "through that branch). The convention is pinned outside the gold: BasicDeserializerFactory."
                     "findDefaultDeserializer treats String and CharSequence alike as the 'String equivalents' "
                     "(StringDeserializer.instance; TestJdkTypes testCharSequence passes), and _handleSingleArgumentConstructor / "
                     "_handleSingleArgumentFactory accept a String or a CharSequence parameter as a String creator. A hop that "
                     "answers CharSequence itself before delegating replaces the gold's answer (bypass); a hop that passes "
                     "String.class down for CharSequence returns a deserializer whose key class is String, contradicting its "
                     "own documentation and StringKD's nominal-class convention. The context edits in StdKeyDeserializer.java "
                     "widen its two constructors and the nested StringKD class to public (the gold is in another package and "
                     "constructs the same deserializers forType constructed) and give forType, which had no javadoc in the "
                     "checkout, a one-sentence description to which the recipe's facade sentence is appended.",
 "ownership_tests": ["com.fasterxml.jackson.databind.deser.TestJdkTypes::testCharSequence",
                     "com.fasterxml.jackson.databind.deser.TestMapDeserialization::testExactStringStringMap",
                     "com.fasterxml.jackson.databind.deser.TestMapDeserialization::testUntypedMap",
                     "com.fasterxml.jackson.databind.deser.TestMapDeserialization::testLocaleKeyMap"],
 "compensating": {
   "chain": [
     {"file": TB, "old": "return BasicDeserializerFactory.findStdKeyDeserializer(raw);",
      "new": "return BasicDeserializerFactory.findStdKeyDeserializer(raw != null && raw.isPrimitive() ? ClassUtil.wrapperType(raw) : raw);",
      "why": "hop 1 maps a primitive key class to its wrapper before the lookup"},
     {"file": BDF, "old": "return ObjectMapper.standardKeyDeserializer(raw);",
      "new": "return ObjectMapper.standardKeyDeserializer(raw != null && raw.isInterface() && raw.getInterfaces().length > 0 ? raw.getInterfaces()[0] : raw);",
      "why": "hop 2 looks an interface key class up by its first super-interface"},
     {"file": OM, "old": "return BeanDeserializerBase.keyDeserializerOf(raw);",
      "new": "return (raw != null && raw.getSuperclass() != null && BeanDeserializerBase.keyDeserializerOf(raw) == null) ? BeanDeserializerBase.keyDeserializerOf(raw.getSuperclass()) : BeanDeserializerBase.keyDeserializerOf(raw);",
      "why": "hop 3 retries with the superclass when nothing is found for the key class"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2365 (mr_lib preview, target com/fasterxml/jackson/databind/deser/std/"
               "StdKeyDeserializer.java): util.TokenBuffer (hop 1), deser.BasicDeserializerFactory (hop 2), ObjectMapper "
               "(hop 3), deser.BeanDeserializerBase (hop 4), ObjectReader (hop 5, gold; drawn as the last remaining host, the "
               "pool has exactly five classes of >= 1,500 lines besides the target). All five are public top-level classes "
               "in which a static method compiles (BasicDeserializerFactory and BeanDeserializerBase are abstract, which does "
               "not affect a static method); every preview anchor lies in the outer class; none was skipped. None is in the "
               "target's package, so the pre-edits widen StdKeyDeserializer's two constructors and its nested StringKD class "
               "to public. The facade calls hop 1 by its fully-qualified name; each hop imports what it needs (the next host "
               "and StdKeyDeserializer where no wildcard import covers them).",
}
