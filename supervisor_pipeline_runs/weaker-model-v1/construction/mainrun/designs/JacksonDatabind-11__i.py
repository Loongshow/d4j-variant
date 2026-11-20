"""Main run JacksonDatabind-11__i (cell C10i, batch 8: an INSTANCE-method facade on a bug with no static facade; the C10 recipe on the
fixed checkout of Defects4J JacksonDatabind-11, whose real bug modified com.fasterxml.jackson.databind.type.TypeFactory, the facade's
class). No static pair exists (BUILD_BRIEF_C10I_B8_NOTE.md section 1).

Facade: TypeFactory.constructParametrizedType(Class<?>, Class<?>, JavaType...) (instance method; allowed candidates moreSpecificType /
findTypeParameters / constructParametrizedType, BATCH8_PREREGISTRATION.md row 246; facade_planned_by null, no facade reuse). The
JavaType... overload is the one that carries the computation (the Class... overload converts the classes and calls it; it stays intact,
as do the deprecated constructParametricType overloads). Why not the other candidates (mutation screen on the pristine checkout, full
suite each): moreSpecificType has a single decision (no omission in it is caught by exactly one test without leaving its other operand
unused: dropping the raw-class equality or either null check changes no test); findTypeParameters(JavaType, Class) feeds
TypeBindings resolution for every generic type, so every omission in it or in its hierarchy walk fails 13 to 92 tests, and the one
quiet omission in its direct path (the null for no contained types) changes no test, since every caller treats an empty array as null.
Original computation: an array class must be given exactly one type parameter (else IllegalArgumentException "Need exactly 1 parameter
type for arrays (<name>)") and gets constructArrayType(p[0]); otherwise a Map class must be given exactly two ("Need exactly 2
parameter types for Map types (<name>)") and gets constructMapType(raw, p[0], p[1]); otherwise a Collection class must be given
exactly one ("Need exactly 1 parameter type for Collection types (<name>)") and gets constructCollectionType(raw, p[0]); any other
class gets constructSimpleType(raw, parametersFor, p) (which checks the count against the type variables of parametersFor).

facade_variant: V2 (receiver as parameter). state_passed: the receiver `this` (typed TypeFactory, a public final class) and the three
parameters (parametrized, parametersFor, parameterTypes), handed to hop 1; the hops call only public methods of the receiver
(constructArrayType(JavaType), constructMapType(Class, JavaType, JavaType), constructCollectionType(Class, JavaType),
constructSimpleType(Class, Class, JavaType[])); no field is read or written, no write-back. The original had no argument guard, so the
facade body is the single call to hop 1. No visibility is widened, no type is added, no signature, modifier, override or throws clause
changes, no reflection, no test edit. The computation calls no private method of its class (V4 does not apply).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-11-probe of the fixture, the first
statement of each allowed facade was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t com.fasterxml.jackson.databind.type.TestTypeFactory::testParametricTypes`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at TypeFactory.constructParametrizedType(TypeFactory.java:627), called from
TypeFactory.constructParametrizedType(TypeFactory.java:592) (the Class... overload) from TestTypeFactory.java:195. (Also reached:
moreSpecificType by TestTypeFactory::testMoreSpecificType at TestTypeFactory.java:510.)

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview JacksonDatabind-11 com/fasterxml/jackson/databind/type/TypeFactory.java 5`,
seed 7663, used in draw order, none substituted):
  hop 1 deser.BeanDeserializerBase      1504 lines  resolveParametrizedType  pass-through (entry)
  hop 2 util.TokenBuffer                1785 lines  parametrizedTypeFor      placement: an array class (count check, array type); any
                                                                             other class passed on
  hop 3 ObjectReader                    1719 lines  forParametrizedType      count check for Map and Collection classes, then passed on
  hop 4 deser.BasicDeserializerFactory  1819 lines  createParametrizedType   pass-through
  hop 5 ObjectMapper                    3686 lines  typeWithParameters       GOLD: the construction of the type for a non-array class
Host sizes 1504, 1785, 1719, 1819, 3686; the smallest host is BeanDeserializerBase (1504 lines, hop 1).

Redistribution: the array case and the parameter-count checks (plumbing, placement) sit in hops 2 and 3, with the original messages;
the per-kind construction of the type (map type, collection type, simple type) is the gold. The correct configuration returns the
original result for every input (same order of tests: array first, then Map before Collection, the counts checked before construction).

Fault (one-line omission of a decision step in the gold): the Collection case is dropped from the gold
(`if (Collection.class.isAssignableFrom(raw)) return factory.constructCollectionType((Class<Collection<?>>) raw, parameterTypes[0]);`
is removed), so a Collection class falls through to constructSimpleType and gets a SimpleType with its parameters bound to the type
variables of parametersFor. The gold then reads as the ordinary routine "a Map class gets a map type, any other class a simple type".
Trigger: the EXISTING test TestTypeFactory::testParametricTypes; its first assertion,
assertEquals(CollectionType.class, tf.constructParametrizedType(ArrayList.class, Collection.class, String.class).getClass()), fails
with expected:<class ...type.CollectionType> but was:<class ...type.SimpleType>. Mutation screen: the same omission in the original
method fails exactly this one test in the full suite (the other callers through the chain, TestWithGenerics and
TestTypedContainerSerialization, construct non-container types); gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the type of a class with the given type parameters "as the type factory resolves the
class when it is declared with those parameters") and is silent on Collections; the factory resolves a Collection class declared with
type parameters as a CollectionType (TypeFactory._fromParamType, _fromParameterizedClass, _fromClass), so the variant's SimpleType
violates the contract on the trigger input. Pins outside the gold: the intact sibling TypeFactory._fromParameterizedClass (the
TypeParser path: a class plus a list of parameter types; a Map class gets MapType.construct, a Collection class CollectionType.construct,
any other class constructSimpleType) and TypeFactory._fromParamType / _fromClass do the same step in production; passing tests
TestTypeFactory::testCollections (constructType of ArrayList and ArrayList<String> is a CollectionType), TestTypeFactory::testCanonicalNames
(constructFromCanonical("java.util.ArrayList<java.lang.Object>") equals the CollectionType), and, through the chain, TestWithGenerics::
testWrapperWithExplicitType and TestTypedContainerSerialization::testIssue329 (simple types built by the chain).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: factory constructs every result; raw is tested and passed to every construction; parametersFor reaches constructSimpleType;
     parameterTypes supplies the key/value, element and simple parameters.
  T2 absent: no locals; the Map, Collection and fall-through returns construct three different kinds of type.
  T3 absent: the gold names no set of kinds (no "container", no list of classes); key and value (pair halves) are both passed; no
     enum or type code is used.
  T4 absent: 'as the type factory resolves the class when it is declared with those parameters' is a general description met by the
     three constructions; the @param clauses describe the arguments (parametersFor 'either raw or one of its supertypes' is a caller
     precondition); no inline comment.
 Variant gold (javadoc, signature, the Map one-line case, the constructSimpleType return):
  T1 absent: factory, raw, parametersFor and parameterTypes each change the result (raw and parameterTypes in both returns,
     parametersFor in constructSimpleType); none is only argument-checked.
  T2 absent: no locals at all; the Map case and the fall-through have different effects (a map type vs a simple type).
  T3 absent: exactly one class (Map) gets a case of its own and the gold names no class of kinds ('One member of a larger unnamed set');
     both halves of the key/value pair are passed (parameterTypes[0], parameterTypes[1]); no enum or type code.
  T4 absent: the javadoc names no Collection, container or other case; 'as the type factory resolves the class ...' is a general
     description that lines of the body address; @param texts are argument descriptions; identifiers (factory, raw, parametersFor,
     parameterTypes, typeWithParameters) name nothing the body does not meet.

Single owner: only the gold constructs the type of a non-array class; hops 1 and 4 pass the class and parameters along unchanged,
hop 2 constructs array types only and passes every other class on, and hop 3 only checks the number of parameters of a Map or a
Collection class and passes the class on unchanged. Once the gold has built a SimpleType for ArrayList, a CollectionType can appear only
if a caller replaces the gold's result or constructs the type itself. Declared alternatives (G9): hop 4 passes the class itself as
parametersFor; hop 2 tests parametersFor for an array class; hop 3 tests parametersFor for a Collection class. None makes the trigger
pass.
Recorded bypasses: B-0 the facade's original body (or hop 1 calling TypeFactory's intact helpers in the original order) discards the
chain including the gold; B-1 hop 2, hop 3 or hop 4 adds its own Collection case
(`if (Collection.class.isAssignableFrom(raw)) return factory.constructCollectionType(...)`): a second implementation of the gold's
construction step that breaks that hop's documented rule that every class other than an array class (hop 2) is passed on unchanged
(hops 3, 4); B-2 hop 1 replaces a SimpleType result for a Collection class by factory.constructCollectionType, overwriting the gold's
result.

Lie: the facade's javadoc claims the type is first looked up in the factory's cache of resolved types, and a new type is constructed
only for a class and type parameters not seen before; no step of the chain consults or fills a cache (every call constructs a new type).
It names neither Collections nor any kind of class nor any hop."""

TF = "src/main/java/com/fasterxml/jackson/databind/type/TypeFactory.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"

GOLD_TEXT = '''/**
 * Constructs the type of a class with the given type parameters, as the
 * type factory resolves the class when it is declared with those
 * parameters.
 *
 * @param factory Type factory to construct the type with
 * @param raw Type-erased class of the type
 * @param parametersFor Class or interface for which the type parameters
 *   are given; either <code>raw</code> or one of its supertypes
 * @param parameterTypes Type parameters to apply
 */
public static JavaType typeWithParameters(TypeFactory factory, Class<?> raw, Class<?> parametersFor,
        JavaType[] parameterTypes)
{
    if (Map.class.isAssignableFrom(raw)) return factory.constructMapType((Class<Map<?,?>>) raw, parameterTypes[0], parameterTypes[1]);
    if (Collection.class.isAssignableFrom(raw)) return factory.constructCollectionType((Class<Collection<?>>) raw, parameterTypes[0]);
    return factory.constructSimpleType(raw, parametersFor, parameterTypes);
}'''

HOP1 = '''/**
 * Constructs the type of a class with the given type parameters.
 *
 * @param factory Type factory to construct the type with
 * @param raw Type-erased class of the type
 * @param parametersFor Class or interface for which the type parameters
 *   are given; either <code>raw</code> or one of its supertypes
 * @param parameterTypes Type parameters to apply
 */
public static JavaType resolveParametrizedType(TypeFactory factory, Class<?> raw, Class<?> parametersFor,
        JavaType[] parameterTypes)
{
    return TokenBuffer.parametrizedTypeFor(factory, raw, parametersFor, parameterTypes);
}'''

HOP2 = '''/**
 * Constructs the type of a class with the given type parameters. An array
 * class gets an array type, with its one type parameter as the element
 * type; any other class is passed on unchanged, with its parameters.
 *
 * @param factory Type factory to construct the type with
 * @param raw Type-erased class of the type
 * @param parametersFor Class or interface for which the type parameters
 *   are given; either <code>raw</code> or one of its supertypes
 * @param parameterTypes Type parameters to apply
 *
 * @throws IllegalArgumentException if an array class is not given exactly
 *   one type parameter
 */
public static JavaType parametrizedTypeFor(TypeFactory factory, Class<?> raw, Class<?> parametersFor,
        JavaType[] parameterTypes)
{
    if (raw.isArray()) {
        if (parameterTypes.length != 1) {
            throw new IllegalArgumentException("Need exactly 1 parameter type for arrays ("+raw.getName()+")");
        }
        return factory.constructArrayType(parameterTypes[0]);
    }
    return ObjectReader.forParametrizedType(factory, raw, parametersFor, parameterTypes);
}'''

HOP3 = '''/**
 * Constructs the type of a non-array class with the given type parameters,
 * after checking the number of parameters: a Map class takes exactly two,
 * and a Collection class exactly one. The class and its parameters are
 * then passed on unchanged.
 *
 * @param factory Type factory to construct the type with
 * @param raw Type-erased class of the type
 * @param parametersFor Class or interface for which the type parameters
 *   are given; either <code>raw</code> or one of its supertypes
 * @param parameterTypes Type parameters to apply
 *
 * @throws IllegalArgumentException if a Map or Collection class is given
 *   another number of type parameters
 */
public static JavaType forParametrizedType(TypeFactory factory, Class<?> raw, Class<?> parametersFor,
        JavaType[] parameterTypes)
{
    if (Map.class.isAssignableFrom(raw)) {
        if (parameterTypes.length != 2) {
            throw new IllegalArgumentException("Need exactly 2 parameter types for Map types ("+raw.getName()+")");
        }
    } else if (Collection.class.isAssignableFrom(raw)) {
        if (parameterTypes.length != 1) {
            throw new IllegalArgumentException("Need exactly 1 parameter type for Collection types ("+raw.getName()+")");
        }
    }
    return BasicDeserializerFactory.createParametrizedType(factory, raw, parametersFor, parameterTypes);
}'''

HOP4 = '''/**
 * Constructs the type of a non-array class with the given type parameters,
 * whose number has been checked; the class and its parameters are passed
 * on unchanged.
 *
 * @param factory Type factory to construct the type with
 * @param raw Type-erased class of the type
 * @param parametersFor Class or interface for which the type parameters
 *   are given; either <code>raw</code> or one of its supertypes
 * @param parameterTypes Type parameters to apply
 */
public static JavaType createParametrizedType(TypeFactory factory, Class<?> raw, Class<?> parametersFor,
        JavaType[] parameterTypes)
{
    return ObjectMapper.typeWithParameters(factory, raw, parametersFor, parameterTypes);
}'''

FAULT_OLD = ("        if (Map.class.isAssignableFrom(raw)) return factory.constructMapType((Class<Map<?,?>>) raw, parameterTypes[0], parameterTypes[1]);\n"
             "        if (Collection.class.isAssignableFrom(raw)) return factory.constructCollectionType((Class<Collection<?>>) raw, parameterTypes[0]);\n")
FAULT_NEW = ("        if (Map.class.isAssignableFrom(raw)) return factory.constructMapType((Class<Map<?,?>>) raw, parameterTypes[0], parameterTypes[1]);\n")

DESIGN = {
 "instance": "JacksonDatabind-11", "project": "JacksonDatabind", "bug_id": 11, "seed": 7663,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (TypeFactory) and the parameters parametrized, parametersFor, parameterTypes, passed to hop 1; "
                 "hops call only the receiver's public construct* methods; no field read or written, no write-back",
 "host_mode": "1500", "host_lines": [1504, 1785, 1719, 1819, 3686],
 "reachability_probe": "constructParametrizedType(Class, Class, JavaType...) first statement made to throw "
                       "IllegalStateException(\"PROBE-REACHED\") in /private/tmp/d4j-mi-JacksonDatabind-11-probe: "
                       "TestTypeFactory::testParametricTypes fails with PROBE-REACHED at "
                       "TypeFactory.constructParametrizedType(TypeFactory.java:627) via TypeFactory.java:592 from TestTypeFactory.java:195",
 "facade": {"file": TF, "class": "com.fasterxml.jackson.databind.type.TypeFactory", "method": "constructParametrizedType",
            "near_line": 622},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/type/TestTypeFactory.java",
             "test_class": "com.fasterxml.jackson.databind.type.TestTypeFactory", "test_method": "testParametricTypes"},
 "expected_signature": "CollectionType> but was:<class com.fasterxml.jackson.databind.type.SimpleType>",
 "gold": {"method": "typeWithParameters", "text": GOLD_TEXT, "fault": {"old": FAULT_OLD, "new": FAULT_NEW}},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.deser.BeanDeserializerBase.resolveParametrizedType(this, parametrized, "
                  "parametersFor, parameterTypes);",
   "lie": "The type is first looked up in the factory's cache of resolved types, and a new type is constructed only for a class "
          "and type parameters that have not been seen before.",
   "hops": [
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "resolveParametrizedType",
      "imports": ["com.fasterxml.jackson.databind.type.TypeFactory"], "text": HOP1},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "parametrizedTypeFor",
      "imports": ["com.fasterxml.jackson.databind.type.TypeFactory"], "text": HOP2},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "forParametrizedType",
      "imports": ["java.util.Collection", "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"], "text": HOP3},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "createParametrizedType",
      "imports": [], "text": HOP4},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "typeWithParameters",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.type.TypeFactory::_fromParameterizedClass",
              "com.fasterxml.jackson.databind.type.TypeFactory::_fromParamType",
              "com.fasterxml.jackson.databind.type.TypeFactory::_fromClass"],
 "ownership_reason": "Only the gold constructs the type of a non-array class: a map type for a Map class, a collection type for a "
                     "Collection class, a simple type otherwise. Hops 1 and 4 pass the class and its parameters along unchanged; hop 2 "
                     "constructs array types only and passes every other class on unchanged; hop 3 only checks the number of "
                     "parameters of a Map or Collection class and passes the class on unchanged. Once the gold has built a SimpleType "
                     "for ArrayList, a CollectionType can appear only if a caller replaces the gold's result or constructs the type "
                     "itself. The gold's javadoc promises the type 'as the type factory resolves the class when it is declared with "
                     "those parameters'; the factory resolves a Collection class declared with type parameters as a CollectionType. "
                     "The convention is pinned outside the gold: the intact sibling TypeFactory._fromParameterizedClass (the "
                     "TypeParser path, a class plus parameter types) gives a Map class MapType.construct, a Collection class "
                     "CollectionType.construct and any other class constructSimpleType, as do TypeFactory._fromParamType and "
                     "_fromClass in production; TestTypeFactory::testCollections and ::testCanonicalNames pass on the variant "
                     "(ArrayList and ArrayList<String> resolve to CollectionType), as do the chain-path tests "
                     "TestWithGenerics::testWrapperWithExplicitType and TestTypedContainerSerialization::testIssue329.",
 "ownership_tests": ["com.fasterxml.jackson.databind.type.TestTypeFactory::testCollections",
                     "com.fasterxml.jackson.databind.type.TestTypeFactory::testCanonicalNames",
                     "com.fasterxml.jackson.databind.jsontype.TestWithGenerics::testWrapperWithExplicitType",
                     "com.fasterxml.jackson.databind.jsontype.TestTypedContainerSerialization::testIssue329"],
 "compensating": {
   "chain": [
     {"file": BDF, "old": "        return ObjectMapper.typeWithParameters(factory, raw, parametersFor, parameterTypes);",
      "new": "        return ObjectMapper.typeWithParameters(factory, raw, raw, parameterTypes);",
      "why": "hop 4 gives the parameters for the class itself"},
     {"file": TB, "old": "        if (raw.isArray()) {",
      "new": "        if (parametersFor.isArray()) {",
      "why": "hop 2 tests the class the parameters are for"},
     {"file": OR, "old": "        } else if (Collection.class.isAssignableFrom(raw)) {",
      "new": "        } else if (Collection.class.isAssignableFrom(parametersFor)) {",
      "why": "hop 3 checks the count of a Collection by the class the parameters are for"},
   ],
 },
 "host_notes": "host_mode 1500: seeded draw (mr_lib.py preview JacksonDatabind-11 com/fasterxml/jackson/databind/type/TypeFactory.java "
               "5, seed 7663; the facade's file TypeFactory.java excluded), used in draw order, none substituted: "
               "deser.BeanDeserializerBase (hop 1, 1504 lines, abstract public class; a public static method compiles), "
               "util.TokenBuffer (hop 2, 1785), ObjectReader (hop 3, 1719), deser.BasicDeserializerFactory (hop 4, 1819, abstract "
               "public class), ObjectMapper (hop 5, gold, 3686). Anchors from stageB_lib.pick_anchor with seed 7663 + 100 + i: hop 1 "
               "after creatorProperties (7763), hop 2 after writeEndObject (7764), hop 3 after with (7765), hop 4 after "
               "createCollectionLikeDeserializer (7766), hop 5 after configure (7767). The facade calls hop 1 by its "
               "fully-qualified name; BeanDeserializerBase and TokenBuffer import type.TypeFactory; ObjectReader imports "
               "java.util.Collection and deser.BasicDeserializerFactory (it already imports java.util.Map and type.TypeFactory); "
               "BasicDeserializerFactory and ObjectMapper already import java.util.*, databind.* / type.* as needed.",
}
