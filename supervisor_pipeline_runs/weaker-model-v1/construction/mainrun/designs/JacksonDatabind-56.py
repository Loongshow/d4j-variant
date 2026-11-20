"""Main run JacksonDatabind-56 (C10 recipe on the fixed checkout of Defects4J JacksonDatabind-56; the real bug modified
FromStringDeserializer, the target class). Batch 5; facade reuse of JacksonDatabind-42 (BATCH5_PREREGISTRATION.md row 97:
the same method is that instance's facade on another fixed revision; recorded, it changes nothing in the build).

Facade: FromStringDeserializer.types() (the only allowed target). It has no parameters and no argument guard; its only
production caller is the static initialiser of JdkDeserializers, which registers the name of every listed type, so that
JdkDeserializers.find hands each of them to the general-purpose deserializer FromStringDeserializer.Std. Existing tests reach it
through every lookup of a default deserializer for a JDK value type (for example TestJdkTypes, TestJacksonTypes).
Original computation: the array of the twelve simple value types that Std handles (File, URL, URI, Class, JavaType, Currency,
Pattern, Locale, Charset, TimeZone, InetAddress, InetSocketAddress), in the order of Std's kinds. The method had no javadoc, and
the recipe's rewrite_facade appends the lie only inside an existing javadoc, so a behaviour-preserving pre-edit gives types() a
one-sentence summary javadoc in the class's own voice ('Method for accessing ...'); the recipe then appends the lie to it.

Chain (hosts in draw order for seed 7269, mr_lib preview, target com/fasterxml/jackson/databind/deser/std/FromStringDeserializer.java,
none skipped):
  hop 1 ObjectReader.simpleValueTypes               placement: the candidate value types (the twelve, in the original order,
                                                    followed by the four other JDK value types that JdkDeserializers handles
                                                    itself: UUID, AtomicBoolean, StackTraceElement, ByteBuffer)
  hop 2 deser.BeanDeserializerBase.fromStringValueTypes   pass-through
  hop 3 ObjectMapper.stringValueTypesOf              placement: the selected list converted to an array
  hop 4 util.TokenBuffer.scalarTypesAccepted         fold: keeps, in order, each candidate the per-type decision accepts
  hop 5 deser.BasicDeserializerFactory.isFromStringType   GOLD: the per-type decision (whether the general-purpose from-String
                                                    deserializer handles values of the type)
The correct configuration returns exactly the original array: the four extra candidates are rejected, the twelve are kept in
their original order.

Fault (one-line omission in the gold's decision): the disjunct that accepts JavaType is dropped, so the decision rejects JavaType
and types() no longer lists it; JdkDeserializers then never registers its name, BasicDeserializerFactory finds no default
deserializer for JavaType, and the bean factory reports the abstract type. Trigger: the EXISTING test
TestJacksonTypes::testJavaType (serialises a JavaType as its canonical String and reads it back with
readValue(json, JavaType.class)); it fails with JsonMappingException 'Can not construct instance of
com.fasterxml.jackson.databind.JavaType, problem: abstract types either need to be mapped ...'. It is the only test of the full
suite that deserialises a JavaType (checked: dropping JavaType from the original types() makes exactly this one test fail, and
no test exercises any other consequence).

The gold's javadoc states the idiomatic contract (whether values of the type are deserialized from a JSON String by the
general-purpose from-String deserializer of the std package) and is silent on any particular type. JavaType is such a type, so
the variant violates the contract on the trigger input. The convention is pinned outside the gold:
FromStringDeserializer.findDeserializer makes the same per-type decision and returns a Std of kind STD_JAVA_TYPE for
JavaType.class, whose _deserialize reads it with TypeFactory.constructFromCanonical; TypeBase.serialize writes every JavaType as
that canonical String (TestTypeFactory::testCanonicalNames pins the round trip); JdkDeserializers.find relies on the listed names.
The passing tests TestJdkTypes::testCharset / testLocale / testInetSocketAddress pin that the decision accepts the other simple
types.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, one return of a disjunction of twelve `rawType == X.class` comparisons):
  T1 absent: the only parameter, rawType, is compared in every disjunct and decides the returned value.
  T2 absent: no local variable, no loop; no if/else, switch or ternary; the single return is the method's only statement.
  T3 absent: the comparisons are against class literals; no enum, type code, flag, part or field of the gold fixes a closed set,
     and the gold names no format or standard; no pair halves or range ends.
  T4 absent: the javadoc names the general-purpose from-String deserializer (a general description that the comparisons
     address) and '@param rawType Type to check'; no limit, bound, value class or case; no inline comment.
  Nothing needed rewriting.
 Variant gold (the same text with the `|| (rawType == JavaType.class)` line removed: eleven comparisons):
  T1 absent: rawType is read in every remaining disjunct and decides the return value; there is no argument check.
  T2 absent: no local (so none dead or frozen); no branch, case or ternary that could be dead; one return statement.
  T3 absent: the eleven compared classes are not members of a set closed by the closure rule (no enum or type code is used, no
     flag, part or field is read, no format is named); no class named in the gold's text is handled in part; no pair or range.
  T4 absent: no phrase names a concrete rule, limit, bound, value class, case or property that the body visibly does not meet;
     the identifier isFromStringType and the parameter name rawType name nothing the body does not do.

Single owner: only the gold decides, per type, whether the general-purpose deserializer handles it; hop 1 lists JavaType among
the candidates, hops 2 and 3 pass the candidates and the selection along, hop 4 keeps exactly what the decision accepts. Once the
decision has rejected a type, no caller can tell a rejected candidate that the deserializer handles from one it does not, except
by restating the decision. Declared alternatives (G9): hop 1 also lists the concrete SimpleType class; hop 2 also offers the core
ResolvedType; hop 4 also keeps a candidate whose superclass is accepted. None makes readValue(json, JavaType.class) work.
Recorded one-line edits that pass the trigger and the full suite (bypasses or test-fitted, not repairs consistent with the path;
each checked on the variant in a scratch copy: trigger passes, defects4j test 0 failing tests):
 B-0 bypass: the facade (its original body), hop 1, hop 2 or hop 3 returns the candidate types without the selection (checked at
     hop 3: `return candidates;`), or hop 4 adds every candidate unconditionally (checked) (the decision's output becomes dead; the four extra types are registered a second time
     by JdkDeserializers, which already lists them, so nothing changes for them).
 B-1 bypass: hop 4 asks FromStringDeserializer.findDeserializer(type) != null instead of the gold (another implementation of the
     gold's decision).
 B-2 test-fitted: hop 4 (or hop 3) hard-codes JavaType (`|| type == JavaType.class`), or JdkDeserializers' own local array
     lists JavaType.class; the gold still answers false for a type the general-purpose deserializer handles, so the gold's
     documented contract (and the facade's) stays violated.

Lie: the facade's javadoc claims the types are discovered by scanning the package for the subclasses of this deserializer and
collecting the value class each passes to its constructor; the code scans nothing and selects from an explicit list. It names
neither JavaType nor any particular type, the decision, nor any hop.

Hosts: ObjectReader (hop 1), deser.BeanDeserializerBase (hop 2, abstract; a static method compiles), ObjectMapper (hop 3),
util.TokenBuffer (hop 4), deser.BasicDeserializerFactory (hop 5, gold, abstract; drawn as the last remaining host of the five-class
pool). The chain runs inside JdkDeserializers' static initialiser; none of the five hosts' static initialisers refers back to
JdkDeserializers or FromStringDeserializer, so there is no initialisation cycle."""

FSD = "src/main/java/com/fasterxml/jackson/databind/deser/std/FromStringDeserializer.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"

GOLD_TEXT = '''/**
 * Method for checking whether values of given type are deserialized from
 * a JSON String by the general-purpose from-String deserializer of the
 * std package.
 *
 * @param rawType Type to check
 *
 * @return True if the general-purpose from-String deserializer handles
 *   values of the type; false otherwise
 */
public static boolean isFromStringType(Class<?> rawType)
{
    return (rawType == File.class)
            || (rawType == URL.class)
            || (rawType == URI.class)
            || (rawType == Class.class)
            || (rawType == JavaType.class)
            || (rawType == Currency.class)
            || (rawType == Pattern.class)
            || (rawType == Locale.class)
            || (rawType == Charset.class)
            || (rawType == TimeZone.class)
            || (rawType == InetAddress.class)
            || (rawType == InetSocketAddress.class);
}'''

HOP1 = '''/**
 * Method for accessing the simple value types that are deserialized from
 * JSON Strings by the general-purpose from-String deserializer.
 *
 * @return Value types handled by the general-purpose from-String
 *   deserializer
 */
public static Class<?>[] simpleValueTypes()
{
    return BeanDeserializerBase.fromStringValueTypes(new Class<?>[] {
            File.class,
            URL.class,
            URI.class,
            Class.class,
            JavaType.class,
            Currency.class,
            Pattern.class,
            Locale.class,
            Charset.class,
            TimeZone.class,
            InetAddress.class,
            InetSocketAddress.class,
            UUID.class,
            AtomicBoolean.class,
            StackTraceElement.class,
            ByteBuffer.class
    });
}'''

HOP2 = '''/**
 * Helper method for selecting, from given candidate types, the simple
 * value types that the general-purpose from-String deserializer handles.
 *
 * @param candidates Types to select from
 *
 * @return Selected types, in the order given
 */
public static Class<?>[] fromStringValueTypes(Class<?>[] candidates)
{
    return ObjectMapper.stringValueTypesOf(candidates);
}'''

HOP3 = '''/**
 * Method for selecting, from given candidate types, the simple value types
 * that the general-purpose from-String deserializer handles.
 *
 * @param candidates Types to select from
 *
 * @return Selected types, in the order given
 */
public static Class<?>[] stringValueTypesOf(Class<?>[] candidates)
{
    List<Class<?>> selected = TokenBuffer.scalarTypesAccepted(candidates);
    return selected.toArray(new Class<?>[selected.size()]);
}'''

HOP4 = '''/**
 * Helper method for collecting those of given candidate types that the
 * general-purpose from-String deserializer handles.
 *
 * @param candidates Types to select from
 *
 * @return List of the selected types, in the order given
 */
public static List<Class<?>> scalarTypesAccepted(Class<?>[] candidates)
{
    List<Class<?>> result = new ArrayList<Class<?>>(candidates.length);
    for (Class<?> type : candidates) {
        if (BasicDeserializerFactory.isFromStringType(type)) {
            result.add(type);
        }
    }
    return result;
}'''

DESIGN = {
 "instance": "JacksonDatabind-56", "project": "JacksonDatabind", "bug_id": 56, "seed": 7269,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade_reuse_of": ["JacksonDatabind-42"],
 "facade": {"file": FSD, "class": "com.fasterxml.jackson.databind.deser.std.FromStringDeserializer", "method": "types", "near_line": 33},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/TestJacksonTypes.java",
             "test_class": "com.fasterxml.jackson.databind.deser.TestJacksonTypes", "test_method": "testJavaType"},
 "expected_signature": "Can not construct instance of com.fasterxml.jackson.databind.JavaType",
 "gold": {"method": "isFromStringType", "text": GOLD_TEXT,
          "fault": {"old": "                || (rawType == Class.class)\n"
                           "                || (rawType == JavaType.class)\n"
                           "                || (rawType == Currency.class)",
                    "new": "                || (rawType == Class.class)\n"
                           "                || (rawType == Currency.class)"}},
 "pre_edits": {
   "chain": [{"file": FSD, "old": "{\n    public static Class<?>[] types() {\n",
              "new": "{\n    /**\n     * Method for accessing the value types that the general-purpose\n"
                     "     * from-String deserializer of this class supports.\n     */\n"
                     "    public static Class<?>[] types() {\n"}],
 },
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.ObjectReader.simpleValueTypes();",
   "lie": "The types are discovered by scanning this package for the subclasses of this deserializer and collecting the "
          "value class that each of them passes to its constructor.",
   "hops": [
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "simpleValueTypes",
      "imports": ["java.net.URI", "java.net.InetAddress", "java.net.InetSocketAddress", "java.nio.ByteBuffer",
                  "java.nio.charset.Charset", "java.util.concurrent.atomic.AtomicBoolean", "java.util.regex.Pattern",
                  "com.fasterxml.jackson.databind.deser.BeanDeserializerBase"], "text": HOP1},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "fromStringValueTypes",
      "imports": [], "text": HOP2},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "stringValueTypesOf",
      "imports": [], "text": HOP3},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "scalarTypesAccepted",
      "imports": ["java.util.ArrayList", "java.util.List", "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"],
      "text": HOP4},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "isFromStringType",
      "imports": ["java.io.File", "java.net.URI", "java.net.URL", "java.net.InetAddress", "java.net.InetSocketAddress",
                  "java.nio.charset.Charset", "java.util.regex.Pattern"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.deser.std.FromStringDeserializer::findDeserializer",
              "com.fasterxml.jackson.databind.deser.std.JdkDeserializers::find",
              "com.fasterxml.jackson.databind.type.TypeBase::serialize",
              "com.fasterxml.jackson.databind.type.TypeFactory::constructFromCanonical"],
 "ownership_reason": "Only the gold decides, per type, whether the general-purpose from-String deserializer handles it; hop 1 "
                     "lists JavaType among the candidate types, hops 2 and 3 pass the candidates and the selection along, and "
                     "hop 4 keeps exactly the candidates the decision accepts, so once the decision rejects JavaType no caller "
                     "can recover it without restating the decision. The convention is pinned outside the gold: "
                     "FromStringDeserializer.findDeserializer makes the same per-type decision and returns a Std of kind "
                     "STD_JAVA_TYPE for JavaType.class (its _deserialize reads the value with "
                     "TypeFactory.constructFromCanonical); TypeBase.serialize writes every JavaType as its canonical String, "
                     "and TestTypeFactory testCanonicalNames pins that round trip; JdkDeserializers.find hands every listed "
                     "type to findDeserializer. The gold's javadoc promises whether values of the type are deserialized from "
                     "a JSON String by the general-purpose from-String deserializer, which holds for JavaType. A hard-coded "
                     "JavaType at a hop, or in JdkDeserializers' own array, passes the existing tests but leaves the gold "
                     "answering false for a type that deserializer handles, so the gold's and the facade's documented "
                     "contracts stay violated.",
 "ownership_tests": ["com.fasterxml.jackson.databind.type.TestTypeFactory::testCanonicalNames",
                     "com.fasterxml.jackson.databind.deser.TestJdkTypes::testCharset",
                     "com.fasterxml.jackson.databind.deser.TestJdkTypes::testLocale",
                     "com.fasterxml.jackson.databind.deser.TestJdkTypes::testInetSocketAddress"],
 "compensating": {
   "chain": [
     {"file": OR, "old": "                ByteBuffer.class\n        });",
      "new": "                ByteBuffer.class,\n                SimpleType.class\n        });",
      "why": "hop 1 also lists the concrete simple type class among the candidates"},
     {"file": BDB, "old": "return ObjectMapper.stringValueTypesOf(candidates);",
      "new": "return ObjectMapper.stringValueTypesOf(ArrayBuilders.insertInListNoDup(candidates, com.fasterxml.jackson.core.type.ResolvedType.class));",
      "why": "hop 2 also offers the core resolved type as a candidate"},
     {"file": TB, "old": "if (BasicDeserializerFactory.isFromStringType(type)) {",
      "new": "if (BasicDeserializerFactory.isFromStringType(type) || BasicDeserializerFactory.isFromStringType(type.getSuperclass())) {",
      "why": "hop 4 also keeps a candidate whose superclass is accepted"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 7269 (mr_lib preview, target com/fasterxml/jackson/databind/deser/std/"
               "FromStringDeserializer.java): ObjectReader (hop 1), deser.BeanDeserializerBase (hop 2), ObjectMapper (hop 3), "
               "util.TokenBuffer (hop 4), deser.BasicDeserializerFactory (hop 5, gold; the last remaining host of the five-class "
               "pool). All five are public top-level classes in which a static method compiles (BeanDeserializerBase and "
               "BasicDeserializerFactory are abstract, which does not affect a static method); every preview anchor lies in the "
               "outer class; none was skipped. The facade calls hop 1 by its fully-qualified name; each hop imports what it "
               "needs (hop 2 and the gold share the deser package; ObjectMapper already imports TokenBuffer). types() had no "
               "javadoc, so a behaviour-preserving pre-edit adds a one-sentence summary for the recipe to append the lie to. "
               "Facade reuse of JacksonDatabind-42 (batch-5 pre-registration).",
}
