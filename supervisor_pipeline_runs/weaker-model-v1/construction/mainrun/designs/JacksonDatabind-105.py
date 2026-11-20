"""Main run JacksonDatabind-105 (C10 recipe on the fixed checkout of Defects4J JacksonDatabind-105; the real bug modified
JdkDeserializers, the target class).

Facade: JdkDeserializers.find(Class<?>, String) (the only allowed target, BATCH5_PREREGISTRATION.md row 105). Its production
caller is BasicDeserializerFactory.findDefaultDeserializer, reached by every deserialization of a java.* type that no earlier
lookup handles; no test calls it directly.
Original computation: null unless the type name is in the class's static name set (UUID, AtomicBoolean, StackTraceElement,
ByteBuffer, Void and the thirteen FromStringDeserializer.types()); then the deserializer FromStringDeserializer.findDeserializer
finds, if any; then one branch per remaining listed type (UUID, StackTraceElement, AtomicBoolean, ByteBuffer, Void); null
otherwise.

The facade keeps its argument guard (a name outside the static set gives null) and delegates to a five-hop chain drawn with the
instance seed 7307 (mr_lib preview, draw order, no substitution):
  hop 1 deser.BasicDeserializerFactory.findJdkTypeDeserializer   decision: a type FromStringDeserializer supports gets the
                                                                   deserializer found there, else delegates
  hop 2 ObjectReader.jdkTypeDeserializer                          pass-through
  hop 3 deser.BeanDeserializerBase.standardTypeDeserializer       pass-through
  hop 4 DeserializationContext.findStandardDeserializer           pass-through
  hop 5 ObjectMapper.standardDeserializerFor                      GOLD: the per-type choice of the standard deserializer
The correct configuration returns the original result for every input (same guard, same FromStringDeserializer lookup first,
the same five type tests in the same order with the same deserializers, null otherwise).

Fault (omission of one case of the gold's per-type decision): the ByteBuffer case is dropped, so the gold returns null for
java.nio.ByteBuffer and the factory falls back to a bean deserializer for the abstract type. The gold still reads as an
ordinary lookup with four cases. Trigger: the EXISTING test JDKStringLikeTypesTest::testByteBuffer
(MAPPER.readValue(<base64 of 5 bytes>, ByteBuffer.class)), which fails with InvalidDefinitionException "Cannot construct instance
of `java.nio.ByteBuffer` (no Creators, like default construct, exist): abstract types either need to be mapped to concrete
types, ...". It is the only test that deserializes a ByteBuffer: dropping the same case from the original method also fails
exactly this one test (checked in a scratch copy, full suite), and the serialization tests of ByteBuffer do not reach the chain.
The gold's javadoc states the idiomatic contract (the standard deserializer for values of the given type, if there is one) and
is silent on any particular type; ByteBuffer has a standard deserializer (deser.std.ByteBufferDeserializer, whose type the
facade's own static set lists), so the variant violates that contract on the trigger input.
(The real Defects4J bug of this checkout concerned the Void case; the injected omission is a different case.)

External pins (convention outside the gold): JdkDeserializers' static name set lists ByteBuffer among the types its lookup
handles, and the facade's guard admits it; BasicSerializerFactory.findSerializerByPrimaryType maps ByteBuffer to
ByteBufferSerializer, the writing side of the same base64 convention (JDKTypeSerializationTest testByteBuffer and
testSlicedByteBuffer pass); ByteBufferDeserializer.deserialize reads that base64 value back; FromStringDeserializer.findDeserializer
is the sibling lookup that gives every type of its own list (types()) a deserializer, the same list-and-cases convention the
gold's cases follow. The gold's other cases are pinned by passing tests through the same chain (JDKStringLikeTypesTest::testUUID,
JDKScalarsTest::testVoidDeser).

Single owner: only the gold holds the per-type choice between the standard deserializers; hop 1 handles exactly the types
FromStringDeserializer supports (ByteBuffer is not one of them, so hop 1 correctly passes it on), hops 2-4 pass the type along,
and the facade's guard admits ByteBuffer. Once the gold has returned null nothing below the facade can tell a type without a
standard deserializer from a missed one, and no change of the type argument (superclass, wrapper, component type) makes the
gold return a ByteBuffer deserializer. Declared alternatives (G9): hop 1 asks FromStringDeserializer about the superclass of an
abstract type, hop 2 passes the component type of an array type, hop 3 passes the wrapper of a primitive type; each still gives
the same InvalidDefinitionException.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-0 the facade restores its original body (or adds its own ByteBuffer case before delegating), discarding the chain for that type.
 B-1 one of hops 1-4 answers ByteBuffer itself, e.g. hop 4
     `return rawType == java.nio.ByteBuffer.class ? new com.fasterxml.jackson.databind.deser.std.ByteBufferDeserializer() : ObjectMapper.standardDeserializerFor(rawType);`
     (checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests): a second implementation of the
     gold's per-type decision; the gold's output is never used for ByteBuffer.
 B-2 the same case added outside the chain, in BasicDeserializerFactory.findDefaultDeserializer or findOptionalStdDeserializer,
     before the facade is called, e.g. `return rawType == java.nio.ByteBuffer.class ? new ByteBufferDeserializer() : JdkDeserializers.find(rawType, clsName);`
     (checked the same way: trigger passes, full suite 0 failing tests): the chain is never reached for ByteBuffer.

Lie: the facade's javadoc claims the listed type names are kept in sorted order and the given name is located among them by a
binary search; the names are kept in a HashSet and the guard is a hash lookup (_classNames.contains), with no sorting and no
search. It names neither ByteBuffer nor any case, nor the omitted step, nor any hop. (A caching lie was considered and set aside:
DeserializerCache does cache deserializers per type above the factory, so it could be read as true.)

Pre-edits (behaviour-preserving, needed by the recipe): (1) JdkDeserializers.find has no javadoc, so rewrite_facade would have
nowhere to append the lie; a short javadoc in the class's own voice is added above it (it describes the method's result only).
(2) ByteBufferDeserializer's no-argument constructor is protected, which the gold in package com.fasterxml.jackson.databind
cannot call; it is made public, as the constructors of the sibling deserializers (UUIDDeserializer, StackTraceElementDeserializer,
AtomicBooleanDeserializer) already are. No class extends ByteBufferDeserializer. The ByteBuffer case of the gold names its two
types fully qualified, so that no import of them is left unused in the variant.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (five type tests, null otherwise):
  T1 absent: rawType is read by every type test and decides which deserializer is returned.
  T2 absent: no locals at all; each of the five ifs returns a different deserializer and the fall-through returns null, so no
     decision is dead; nothing is literal-initialised or loop-moved.
  T3 absent: the tested types are not members of an enum, a type code or a named format, and the gold's text names no class of
     types; no pair halves or range ends occur. The original's line comment about AtomicInteger/AtomicLong (a family the method
     does not test) was not carried over, so the text does not name such a family.
  T4 absent: the javadoc names only "the standard deserializer for values of the given type, if there is one" and "null
     otherwise", general descriptions the type tests and the fall-through address; no limit, value class, case or property.
 Variant gold (javadoc, signature, four type tests UUID / StackTraceElement / AtomicBoolean / Void, then `return null;`):
  T1 absent: rawType is read by all four type tests and decides the return value; it is the only parameter.
  T2 absent: no local variable exists; the four ifs return four different deserializers and the fall-through returns null, so
     no branch is dead or duplicated; no literal-initialised, frozen or loop-moved variable (there is no loop).
  T3 absent: the four tested classes form no closed set under the closure rule (no enum, no type code, no named format, no class
     named in the gold's text), so no member is visibly left out; there is no pair or range of which one half is handled; no
     field or member is read without its treatment.
  T4 absent: 'the standard deserializer for values of the given type, if there is one', '@param rawType Type of values to
     deserialize' and '@return Deserializer to use, if one is found; null otherwise' are general descriptions that the type
     tests and the null fall-through address; no concrete rule, limit, bound, value class, case or property is named; there is
     no inline comment; the identifiers (standardDeserializerFor, rawType) name nothing the body does not meet."""

JDK = "src/main/java/com/fasterxml/jackson/databind/deser/std/JdkDeserializers.java"
BBD = "src/main/java/com/fasterxml/jackson/databind/deser/std/ByteBufferDeserializer.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
DC = "src/main/java/com/fasterxml/jackson/databind/DeserializationContext.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"

GOLD_TEXT = '''/**
 * Method for finding the standard deserializer for values of the given
 * type, if there is one.
 *
 * @param rawType Type of values to deserialize
 *
 * @return Deserializer to use, if one is found; null otherwise
 */
public static JsonDeserializer<?> standardDeserializerFor(Class<?> rawType)
{
    if (rawType == UUID.class) {
        return new UUIDDeserializer();
    }
    if (rawType == StackTraceElement.class) {
        return new StackTraceElementDeserializer();
    }
    if (rawType == AtomicBoolean.class) {
        return new AtomicBooleanDeserializer();
    }
    if (rawType == java.nio.ByteBuffer.class) {
        return new com.fasterxml.jackson.databind.deser.std.ByteBufferDeserializer();
    }
    if (rawType == Void.class) {
        return NullifyingDeserializer.instance;
    }
    return null;
}'''

HOP1 = '''/**
 * Helper method for locating the deserializer for one of the JDK types
 * that need special handling. A type that {@link FromStringDeserializer}
 * supports gets the deserializer found there; any other type gets its
 * standard deserializer, if there is one.
 *
 * @param rawType Type of values to deserialize
 *
 * @return Deserializer to use, if one is found; null otherwise
 */
public static JsonDeserializer<?> findJdkTypeDeserializer(Class<?> rawType)
{
    JsonDeserializer<?> deser = FromStringDeserializer.findDeserializer(rawType);
    if (deser != null) {
        return deser;
    }
    return ObjectReader.jdkTypeDeserializer(rawType);
}'''

HOP2 = '''/**
 * Method for locating the standard deserializer to use for values of
 * the given type.
 *
 * @param rawType Type of values to deserialize
 *
 * @return Deserializer to use, if one is found; null otherwise
 */
public static JsonDeserializer<?> jdkTypeDeserializer(Class<?> rawType) {
    return BeanDeserializerBase.standardTypeDeserializer(rawType);
}'''

HOP3 = '''/**
 * Helper method for finding the standard deserializer for values of
 * given type, if any.
 *
 * @param rawType Type of values to deserialize
 *
 * @return Deserializer to use, if one is found; null otherwise
 */
public static JsonDeserializer<?> standardTypeDeserializer(Class<?> rawType)
{
    return DeserializationContext.findStandardDeserializer(rawType);
}'''

HOP4 = '''/**
 * Method for finding the standard deserializer for values of the given
 * type, if there is one.
 *
 * @param rawType Type of values to deserialize
 *
 * @return Deserializer to use, if one is found; null otherwise
 */
public static JsonDeserializer<?> findStandardDeserializer(Class<?> rawType)
{
    return ObjectMapper.standardDeserializerFor(rawType);
}'''

FACADE_HEADER = "    public static JsonDeserializer<?> find(Class<?> rawType, String clsName)\n"

DESIGN = {
 "instance": "JacksonDatabind-105", "project": "JacksonDatabind", "bug_id": 105, "seed": 7307,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": JDK, "class": "com.fasterxml.jackson.databind.deser.std.JdkDeserializers", "method": "find", "near_line": 29},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/jdk/JDKStringLikeTypesTest.java",
             "test_class": "com.fasterxml.jackson.databind.deser.jdk.JDKStringLikeTypesTest",
             "test_method": "testByteBuffer"},
 "expected_signature": "Cannot construct instance of `java.nio.ByteBuffer`",
 "gold": {"method": "standardDeserializerFor", "text": GOLD_TEXT,
          "fault": {"old": "            return new AtomicBooleanDeserializer();\n"
                           "        }\n"
                           "        if (rawType == java.nio.ByteBuffer.class) {\n"
                           "            return new com.fasterxml.jackson.databind.deser.std.ByteBufferDeserializer();\n"
                           "        }\n"
                           "        if (rawType == Void.class) {",
                    "new": "            return new AtomicBooleanDeserializer();\n"
                           "        }\n"
                           "        if (rawType == Void.class) {"}},
 "pre_edits": {
   "chain": [
     {"file": JDK, "old": FACADE_HEADER,
      "new": "    /**\n"
             "     * Method for locating the deserializer for one of the JDK types listed\n"
             "     * above, if the given type is one of them; for any other type null is\n"
             "     * returned.\n"
             "     */\n" + FACADE_HEADER},
     {"file": BBD, "old": "    protected ByteBufferDeserializer() { super(ByteBuffer.class); }",
      "new": "    public ByteBufferDeserializer() { super(ByteBuffer.class); }"},
   ],
 },
 "chain": {
   "facade_body": "if (!_classNames.contains(clsName)) {\n            return null;\n        }\n"
                  "        return com.fasterxml.jackson.databind.deser.BasicDeserializerFactory.findJdkTypeDeserializer(rawType);",
   "lie": "The listed type names are kept in sorted order, and the given name is located among them by a binary search "
          "before its deserializer is created.",
   "hops": [
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "findJdkTypeDeserializer",
      "imports": [], "text": HOP1},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "jdkTypeDeserializer",
      "imports": ["com.fasterxml.jackson.databind.deser.BeanDeserializerBase"], "text": HOP2},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "standardTypeDeserializer",
      "imports": [], "text": HOP3},
     {"file": DC, "class": "com.fasterxml.jackson.databind.DeserializationContext", "method": "findStandardDeserializer",
      "imports": [], "text": HOP4},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "standardDeserializerFor",
      "imports": ["java.util.concurrent.atomic.AtomicBoolean",
                  "com.fasterxml.jackson.databind.deser.std.AtomicBooleanDeserializer",
                  "com.fasterxml.jackson.databind.deser.std.NullifyingDeserializer",
                  "com.fasterxml.jackson.databind.deser.std.StackTraceElementDeserializer",
                  "com.fasterxml.jackson.databind.deser.std.UUIDDeserializer"],
      "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.ser.BasicSerializerFactory::findSerializerByPrimaryType",
              "com.fasterxml.jackson.databind.deser.std.FromStringDeserializer::findDeserializer",
              "com.fasterxml.jackson.databind.deser.std.ByteBufferDeserializer::deserialize"],
 "ownership_reason": "Only the gold holds the per-type choice between the standard deserializers: hop 1 handles exactly the "
                     "types FromStringDeserializer supports (FromStringDeserializer.types() does not list ByteBuffer, so hop 1 "
                     "correctly passes it on), hops 2-4 pass the type along unchanged, and the facade's guard admits ByteBuffer "
                     "because the class's static name set lists it. The gold's javadoc promises the standard deserializer for "
                     "values of the given type, and ByteBuffer has one (deser.std.ByteBufferDeserializer, which reads the "
                     "base64 binary value), yet the gold returns null for it. Once null is returned, nothing below the facade "
                     "can tell a type without a standard deserializer from a missed one, and no change of the type argument "
                     "(superclass, wrapper, component type) makes the gold produce a ByteBuffer deserializer. The convention is "
                     "pinned outside the gold: JdkDeserializers' static name set (ByteBuffer among the listed types); "
                     "BasicSerializerFactory.findSerializerByPrimaryType maps ByteBuffer to ByteBufferSerializer, the writing "
                     "side of the same base64 convention (JDKTypeSerializationTest testByteBuffer and testSlicedByteBuffer "
                     "pass); FromStringDeserializer.findDeserializer gives every type of its own list a deserializer, the same "
                     "list-and-cases convention. The gold's other cases pass through the same chain "
                     "(JDKStringLikeTypesTest::testUUID, JDKScalarsTest::testVoidDeser). A hop that answers ByteBuffer itself "
                     "(a ternary at any of hops 1-4) passes the suite but is a second implementation of the gold's per-type "
                     "decision whose output replaces the gold's for that type: a bypass, not a repair.",
 "ownership_tests": ["com.fasterxml.jackson.databind.ser.jdk.JDKTypeSerializationTest::testByteBuffer",
                     "com.fasterxml.jackson.databind.ser.jdk.JDKTypeSerializationTest::testSlicedByteBuffer",
                     "com.fasterxml.jackson.databind.deser.jdk.JDKStringLikeTypesTest::testUUID",
                     "com.fasterxml.jackson.databind.deser.jdk.JDKScalarsTest::testVoidDeser"],
 "compensating": {
   "chain": [
     {"file": BDF, "old": "    JsonDeserializer<?> deser = FromStringDeserializer.findDeserializer(rawType);",
      "new": "    JsonDeserializer<?> deser = FromStringDeserializer.findDeserializer(java.lang.reflect.Modifier.isAbstract(rawType.getModifiers()) && rawType.getSuperclass() != null ? rawType.getSuperclass() : rawType);",
      "why": "hop 1 asks FromStringDeserializer about the superclass of an abstract type"},
     {"file": OR, "old": "return BeanDeserializerBase.standardTypeDeserializer(rawType);",
      "new": "return BeanDeserializerBase.standardTypeDeserializer(rawType.isArray() ? rawType.getComponentType() : rawType);",
      "why": "hop 2 passes the component type of an array type"},
     {"file": BDB, "old": "return DeserializationContext.findStandardDeserializer(rawType);",
      "new": "return DeserializationContext.findStandardDeserializer(rawType.isPrimitive() ? ClassUtil.wrapperType(rawType) : rawType);",
      "why": "hop 3 passes the wrapper of a primitive type"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 7307 (mr_lib preview, target com/fasterxml/jackson/databind/deser/std/JdkDeserializers.java): "
               "deser.BasicDeserializerFactory (hop 1), ObjectReader (hop 2), deser.BeanDeserializerBase (hop 3), "
               "DeserializationContext (hop 4), ObjectMapper (hop 5, gold). All five are public top-level classes in which a "
               "static method compiles (BasicDeserializerFactory, BeanDeserializerBase and DeserializationContext are "
               "abstract, which does not affect a static method); every preview anchor is a method of the outer class; none "
               "was skipped. The facade calls hop 1 by its fully-qualified name; hop 2 imports BeanDeserializerBase, the other "
               "hops see the next host through existing imports or their package; the gold imports AtomicBoolean and four "
               "deser.std deserializers (UUID is covered by ObjectMapper's java.util.* import) and names ByteBuffer and "
               "ByteBufferDeserializer fully qualified. Pre-edits: a javadoc above JdkDeserializers.find (it had none, so the "
               "lie had no place) and ByteBufferDeserializer's constructor made public (the gold is outside deser.std).",
}
