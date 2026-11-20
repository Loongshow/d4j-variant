"""Main run JacksonDatabind-19__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static
facade; fixed checkout of Defects4J JacksonDatabind-19, whose real bug modified TypeFactory, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE.md section 1; paired_* fields null).

Facade: TypeFactory.constructParametrizedType(Class<?>, Class<?>, JavaType...) (instance method; allowed targets
TypeFactory.moreSpecificType / findTypeParameters / constructParametrizedType, BATCH8_PREREGISTRATION.md row 248). Its
facade_planned_by is null, so the facade is distinct (moreSpecificType, planned by JacksonDatabind-11__i, was not used). The
JavaType... overload is the one the profile names (28 lines, calls constructArrayType / constructCollectionType / constructMapType);
the Class<?>... overload, which resolves its classes with the protected _fromClass and then calls this overload, and the two
deprecated constructParametricType overloads stay intact. findTypeParameters(JavaType, Class) was not used: it has eleven production
callers (serializer and deserializer factories, TypeBindings, object id handling), and its two decisions (the direct path for a
type whose parameter source is the expected type, the null for a type without contained types) are either reached by many tests
at once or observed by no test, so no single-trigger omission exists there.
Original computation of the facade: an array class needs exactly 1 type parameter (IllegalArgumentException "Need exactly 1
parameter type for arrays (...)") and gives constructArrayType(parameterTypes[0]); else a Map class needs exactly 2 ("Need exactly 2
parameter types for Map types (...)") and gives constructMapType(class, key, value); else a Collection class needs exactly 1 ("Need
exactly 1 parameter type for Collection types (...)") and gives constructCollectionType(class, element); otherwise
constructSimpleType(parametrized, parametersFor, parameterTypes).

facade_variant: V2 (receiver as parameter). The computation calls four public methods of the receiver (constructArrayType,
constructMapType, constructCollectionType, constructSimpleType), so the facade passes `this` (typed TypeFactory, a public class) with
its three arguments to hop 1; the hops call only those public methods of it. No field is read or written (no V1 state, no
write-back); no private method of TypeFactory is called by the original body (no V4); no package-private type is involved (no
V3/V5). The facade body is one call to hop 1 (the original has no argument guard). No visibility is widened, no type is added, no
signature, modifier, override or throws clause changes, no reflection, no test edit.
state_passed: the receiver `this` (TypeFactory) and the arguments parametrized, parametersFor, parameterTypes, handed to hop 1; no
write-back.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-19-probe/w of the fixture, the first
statement of constructParametrizedType(Class<?>, Class<?>, JavaType...) was made `if (true) { throw new
IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
com.fasterxml.jackson.databind.type.TestTypeFactory::testParametricTypes`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at TypeFactory.constructParametrizedType(TypeFactory.java:655), via TypeFactory.java:612 (the Class<?>... overload),
from TestTypeFactory.testParametricTypes(TestTypeFactory.java:208). Full suite with the probe: 3 failing tests,
TestTypeFactory::testParametricTypes, TestWithGenerics::testWrapperWithExplicitType and TestTypedContainerSerialization::testIssue329
(the facade has no production caller outside TypeFactory's own overloads). The facade is reached by existing tests.

Hosts (host_mode = "1500"; drawn with `mr_lib.py preview JacksonDatabind-19 com/fasterxml/jackson/databind/type/TypeFactory.java 5`,
instance seed 6377, used in draw order, none substituted):
  hop 1 deser.BasicDeserializerFactory 1895 lines  typeWithParameters   decision: an array class takes exactly one type parameter,
                                                                        its element type (the original's first case)
  hop 2 util.TokenBuffer               1802 lines  parametrizedTypeOf   pass-through
  hop 3 ObjectMapper                   3823 lines  parametrizedType     pass-through
  hop 4 deser.BeanDeserializerBase     1533 lines  typeForParameters    pass-through
  hop 5 ObjectReader                   1760 lines  parametrizedTypeFor  GOLD: the decision, for every class that is not an array,
                                                                        which type the factory constructs (Map, Collection or simple
                                                                        type) and the parameter count each of the container kinds needs
Host line counts 1895, 1802, 3823, 1533, 1760; the smallest host is BeanDeserializerBase (1533 lines); the gold host has 1760.
The correct configuration returns the original JavaType for every input: hop 1 is the original's array case verbatim, hops 2-4 pass
the four values along, and the gold is the original's Map, Collection and simple cases verbatim, in the original order.

Fault (one-line omission of a special-case decision in the gold): the decision that sends a Map class to constructMapType (with its
two-parameter check) is dropped, so a Map class falls through to constructSimpleType and becomes a SimpleType with two type
parameters instead of a MapType. The gold then reads as the ordinary routine "a Collection class becomes a CollectionType, any other
class a simple type". Trigger: the EXISTING test TestTypeFactory::testParametricTypes. Its ArrayList<String> block (CollectionType)
still holds, and assertEquals(MapType.class, t2.getClass()) for constructParametrizedType(Map.class, Map.class, strC, t) at line 218
fails with expected:<class ...MapType> but was:<class ...SimpleType>. It is the only test that newly fails: the facade has no
production caller and the other two tests that reach it (testWrapperWithExplicitType, testIssue329) build simple types
(ContainerWithGetter<Animal>, Iterator<Animal>), which the variant gold still constructs as before.

The gold's javadoc states the idiomatic contract (the JavaType that represents the parameterized type, the facade's own wording) and
is silent on the kinds of type. In Jackson's type model the type that represents a Map class is a MapType; the convention is pinned
outside the gold: TypeFactory._fromClass (Map classes through _mapType to MapType.construct) and TypeFactory._fromParameterizedClass
and _fromParamType (the generic-aware paths: a Map class with type parameters becomes MapType.construct(raw, key, value)), with
TestTypeFactory::testMaps (constructType(HashMap.class), constructMapType(TreeMap.class, ...) and TypeReference<HashMap<String,
Integer>> all give MapType) and TestTypeFactory::testCollections passing on the variant; TestWithGenerics::testWrapperWithExplicitType
and TestTypedContainerSerialization::testIssue329 pass through the whole chain (simple types).

Single owner: only the gold decides, for a class that is not an array, which type the factory constructs; hop 1 answers only array
classes, and hops 2-4 pass the receiver and the three values on unchanged. A one-line change above the gold cannot make the gold
return a MapType: the gold sends every non-Collection class to constructSimpleType whatever parametersFor or parameterTypes it is
given. Recovering after the gold also fails the trigger: for constructParametrizedType(Map.class, Map.class, strC) the gold's
simple path throws "Parameter type mismatch ... expected 2 parameters, was given 1", while the trigger requires "Need exactly 2
parameter types for Map types". Declared alternatives (G9): hop 1 takes Map classes through its own branch; hop 2 binds the type
parameters to the class itself; hop 3 binds the type parameters of a Map class to Map. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's work with a second implementation, not repairs of the chain):
 B-1 a hop (any of 1-4) that handles Map classes itself before calling the next hop, i.e. re-implements the gold's Map case with its
     two-parameter check and message ("Need exactly 2 parameter types for Map types") in one crammed line and never calls the gold
     for Map classes; the gold still returns a SimpleType for a Map class against its contract. Checked on the variant in the
     scratch copy /private/tmp/d4j-mi-JacksonDatabind-19-bypass (the line placed in hop 4): trigger passes, full suite 0 failing
     tests. In the same scratch, a recovery after the gold at hop 4 (rebuilding a MapType from the gold's SimpleType) leaves the
     trigger failing: "Expected an exception with one of substrings ([Need exactly 2 parameter types for Map types]): got one with
     message "Parameter type mismatch for java.util.Map ...: expected 2 parameters, was given 1"".
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the type parameters are matched to the type variables of parametersFor by name, after both are
sorted alphabetically; nothing in the chain sorts or matches by name (constructSimpleType binds by position, and the container
types take the parameters by position). It names neither the kinds of type, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (Map case with its two-parameter check, Collection case with its one-parameter check, simple type):
  T1 absent: typeFactory constructs every result; parametrized is tested twice and passed to every construction; parametersFor is
     passed to constructSimpleType; parameterTypes is counted and passed to every construction; no parameter only argument-checked.
  T2 absent: no local variable; each of the two decisions leads to a different construction; the two count checks throw.
  T3 absent: the Map case takes both halves of its pair (parameterTypes[0] key, parameterTypes[1] value); both kinds the gold names
     (Map, Collection) get their decision and their count check; no enum or type code is used; arrays are not named in the gold's
     text (they are answered above the gold), so no closed set is left incomplete.
  T4 absent: 'the JavaType that represents a parameterized type' is a general description the returns address; '@param
     parametersFor ... either parametrized or one of its supertypes' is a caller precondition; the two messages state the counts
     their checks enforce; no inline comment.
 Variant gold (javadoc, signature, `if (Collection.class.isAssignableFrom(parametrized))` with its one-parameter check and
 constructCollectionType, otherwise constructSimpleType):
  T1 absent: typeFactory constructs both results; parametrized is tested and passed to both constructions; parametersFor is passed
     to constructSimpleType, whose result is returned; parameterTypes is counted and passed to both constructions.
  T2 absent: no local variable, no loop, no literal-initialised value; the decision returns a CollectionType on one side and a simple
     type on the other; the count check throws.
  T3 absent: exactly one kind of type (Collection) is given its own treatment and the gold names no class of kinds ('One member of
     a larger unnamed set'); the count check is an argument check, not an element-level treatment; no pair half or range end is read
     (only parameterTypes[0] in a one-parameter case); no enum or type code.
  T4 absent: 'Method for constructing the JavaType that represents a parameterized type' and '@return Type constructed' are general
     descriptions that both returns address; '@param parametrized Type-erased class of the type being constructed', '@param
     parametersFor ... either parametrized or one of its supertypes' (a caller precondition) and '@param parameterTypes Type
     parameters to apply' name no rule the body breaks; the message 'Need exactly 1 parameter type for Collection types' is enforced
     by its check; the identifiers name what they hold."""

FAC = "src/main/java/com/fasterxml/jackson/databind/type/TypeFactory.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"

GOLD_TEXT = '''/**
 * Method for constructing the {@link JavaType} that represents a
 * parameterized type.
 *
 * @param typeFactory Factory used for constructing the type
 * @param parametrized Type-erased class of the type being constructed
 * @param parametersFor Class or interface for which type parameters are applied; either
 *   <code>parametrized</code> or one of its supertypes
 * @param parameterTypes Type parameters to apply
 *
 * @return Type constructed
 */
public static JavaType parametrizedTypeFor(TypeFactory typeFactory, Class<?> parametrized,
        Class<?> parametersFor, JavaType[] parameterTypes)
{
    if (Map.class.isAssignableFrom(parametrized)) {
        if (parameterTypes.length != 2) {
            throw new IllegalArgumentException("Need exactly 2 parameter types for Map types ("+parametrized.getName()+")");
        }
        return typeFactory.constructMapType((Class<Map<?,?>>) parametrized, parameterTypes[0], parameterTypes[1]);
    }
    if (Collection.class.isAssignableFrom(parametrized)) {
        if (parameterTypes.length != 1) {
            throw new IllegalArgumentException("Need exactly 1 parameter type for Collection types ("+parametrized.getName()+")");
        }
        return typeFactory.constructCollectionType((Class<Collection<?>>) parametrized, parameterTypes[0]);
    }
    return typeFactory.constructSimpleType(parametrized, parametersFor, parameterTypes);
}'''

HOP1 = '''/**
 * Helper method for constructing the {@link JavaType} that represents a
 * parameterized type. An array class takes exactly one type parameter,
 * its element type.
 *
 * @param typeFactory Factory used for constructing the type
 * @param parametrized Type-erased class of the type being constructed
 * @param parametersFor Class or interface for which type parameters are applied
 * @param parameterTypes Type parameters to apply
 *
 * @return Type constructed
 */
public static JavaType typeWithParameters(TypeFactory typeFactory, Class<?> parametrized,
        Class<?> parametersFor, JavaType[] parameterTypes)
{
    if (parametrized.isArray()) {
        if (parameterTypes.length != 1) {
            throw new IllegalArgumentException("Need exactly 1 parameter type for arrays ("+parametrized.getName()+")");
        }
        return typeFactory.constructArrayType(parameterTypes[0]);
    }
    return TokenBuffer.parametrizedTypeOf(typeFactory, parametrized, parametersFor, parameterTypes);
}'''

HOP2 = '''/**
 * Helper method for constructing the {@link JavaType} that represents
 * a parameterized type.
 *
 * @param typeFactory Factory used for constructing the type
 * @param parametrized Type-erased class of the type being constructed
 * @param parametersFor Class or interface for which type parameters are applied
 * @param parameterTypes Type parameters to apply
 */
public static JavaType parametrizedTypeOf(TypeFactory typeFactory, Class<?> parametrized,
        Class<?> parametersFor, JavaType[] parameterTypes)
{
    return ObjectMapper.parametrizedType(typeFactory, parametrized, parametersFor, parameterTypes);
}'''

HOP3 = '''/**
 * Convenience method for constructing the {@link JavaType} that represents
 * a parameterized type, using given type factory.
 *
 * @param typeFactory Factory used for constructing the type
 * @param parametrized Type-erased class of the type being constructed
 * @param parametersFor Class or interface for which type parameters are applied
 * @param parameterTypes Type parameters to apply
 */
public static JavaType parametrizedType(TypeFactory typeFactory, Class<?> parametrized,
        Class<?> parametersFor, JavaType[] parameterTypes)
{
    return BeanDeserializerBase.typeForParameters(typeFactory, parametrized, parametersFor, parameterTypes);
}'''

HOP4 = '''/**
 * Helper method for constructing the {@link JavaType} that represents
 * a parameterized type.
 *
 * @param typeFactory Factory used for constructing the type
 * @param parametrized Type-erased class of the type being constructed
 * @param parametersFor Class or interface for which type parameters are applied
 * @param parameterTypes Type parameters to apply
 */
public static JavaType typeForParameters(TypeFactory typeFactory, Class<?> parametrized,
        Class<?> parametersFor, JavaType[] parameterTypes)
{
    return ObjectReader.parametrizedTypeFor(typeFactory, parametrized, parametersFor, parameterTypes);
}'''

DESIGN = {
 "instance": "JacksonDatabind-19", "project": "JacksonDatabind", "bug_id": 19, "seed": 6377,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": FAC, "class": "com.fasterxml.jackson.databind.type.TypeFactory", "method": "constructParametrizedType",
            "near_line": 652},
 "facade_variant": "V2",
 "state_passed": "the receiver this (TypeFactory, public class) and the arguments parametrized, parametersFor, parameterTypes, "
                 "handed to hop 1; the hops call only the receiver's public constructArrayType, constructMapType, "
                 "constructCollectionType and constructSimpleType; no field read or written, no write-back",
 "host_mode": "1500",
 "reachability_probe": "testParametricTypes fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "TypeFactory.constructParametrizedType(TypeFactory.java:655) via TypeFactory.java:612 from "
                       "TestTypeFactory.java:208; full suite with the probe: 3 failing tests (TestTypeFactory::testParametricTypes, "
                       "TestWithGenerics::testWrapperWithExplicitType, TestTypedContainerSerialization::testIssue329)",
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/type/TestTypeFactory.java",
             "test_class": "com.fasterxml.jackson.databind.type.TestTypeFactory", "test_method": "testParametricTypes"},
 "expected_signature": "expected:<class com.fasterxml.jackson.databind.type.MapType> but was:<class com.fasterxml.jackson.databind.type.SimpleType>",
 "gold": {"method": "parametrizedTypeFor", "text": GOLD_TEXT,
          "fault": {"old": "    {\n"
                           "        if (Map.class.isAssignableFrom(parametrized)) {\n"
                           "            if (parameterTypes.length != 2) {\n"
                           "                throw new IllegalArgumentException(\"Need exactly 2 parameter types for Map types (\"+parametrized.getName()+\")\");\n"
                           "            }\n"
                           "            return typeFactory.constructMapType((Class<Map<?,?>>) parametrized, parameterTypes[0], parameterTypes[1]);\n"
                           "        }\n"
                           "        if (Collection.class.isAssignableFrom(parametrized)) {\n",
                    "new": "    {\n"
                           "        if (Collection.class.isAssignableFrom(parametrized)) {\n"}},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.deser.BasicDeserializerFactory.typeWithParameters(this, parametrized, "
                  "parametersFor, parameterTypes);",
   "lie": "The type parameters are matched to the type variables of <code>parametersFor</code> by name, after both have been "
          "sorted alphabetically.",
   "hops": [
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "typeWithParameters",
      "imports": [], "text": HOP1},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "parametrizedTypeOf",
      "imports": ["com.fasterxml.jackson.databind.type.TypeFactory"], "text": HOP2},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "parametrizedType",
      "imports": [], "text": HOP3},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "typeForParameters",
      "imports": ["com.fasterxml.jackson.databind.type.TypeFactory"], "text": HOP4},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "parametrizedTypeFor",
      "imports": ["java.util.Collection"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.type.TypeFactory::_fromClass",
              "com.fasterxml.jackson.databind.type.TypeFactory::_fromParameterizedClass",
              "com.fasterxml.jackson.databind.type.TypeFactory::_fromParamType"],
 "ownership_reason": "Only the gold decides, for a class that is not an array, which type the factory constructs (a MapType "
                     "for a Map class, a CollectionType for a Collection class, a simple type otherwise) and checks the parameter "
                     "count each container kind needs; hop 1 answers only array classes and hops 2-4 pass the receiver and the "
                     "three values on unchanged. The gold's javadoc promises the JavaType that represents the parameterized "
                     "type; for Map<String,ArrayList<String>> that type is a MapType in Jackson's type model, and the variant "
                     "returns a SimpleType. No one-line change of the values above the gold makes it return a MapType (it sends "
                     "every non-Collection class to constructSimpleType), and recovering after the gold cannot produce the "
                     "trigger's 'Need exactly 2 parameter types for Map types' for a Map class with one parameter, for which "
                     "the gold's simple path already throws its own mismatch message. The convention is pinned outside the "
                     "gold: TypeFactory._fromClass builds a Map class through _mapType as MapType.construct, and the "
                     "generic-aware TypeFactory._fromParameterizedClass and _fromParamType build a Map class with type "
                     "parameters as MapType.construct(raw, key, value) (a Collection class as CollectionType); "
                     "TestTypeFactory::testMaps (raw HashMap, constructMapType(TreeMap, ...) and TypeReference<HashMap<String,"
                     "Integer>> all give MapType) and TestTypeFactory::testCollections pass, and "
                     "TestWithGenerics::testWrapperWithExplicitType and TestTypedContainerSerialization::testIssue329 pass "
                     "through the whole chain.",
 "ownership_tests": ["com.fasterxml.jackson.databind.type.TestTypeFactory::testMaps",
                     "com.fasterxml.jackson.databind.type.TestTypeFactory::testCollections",
                     "com.fasterxml.jackson.databind.jsontype.TestWithGenerics::testWrapperWithExplicitType",
                     "com.fasterxml.jackson.databind.jsontype.TestTypedContainerSerialization::testIssue329"],
 "compensating": {
   "chain": [
     {"file": BDF, "old": "        if (parametrized.isArray()) {",
      "new": "        if (parametrized.isArray() || Map.class.isAssignableFrom(parametrized)) {",
      "why": "hop 1 takes Map classes through its own branch"},
     {"file": TB, "old": "return ObjectMapper.parametrizedType(typeFactory, parametrized, parametersFor, parameterTypes);",
      "new": "return ObjectMapper.parametrizedType(typeFactory, parametrized, parametrized, parameterTypes);",
      "why": "hop 2 binds the type parameters to the class itself"},
     {"file": OM, "old": "return BeanDeserializerBase.typeForParameters(typeFactory, parametrized, parametersFor, parameterTypes);",
      "new": "return BeanDeserializerBase.typeForParameters(typeFactory, parametrized, Map.class.isAssignableFrom(parametrized) ? Map.class : parametersFor, parameterTypes);",
      "why": "hop 3 binds the type parameters of a Map class to Map"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts drawn with `mr_lib.py preview JacksonDatabind-19 "
               "com/fasterxml/jackson/databind/type/TypeFactory.java 5` (instance seed 6377), used in draw order, none "
               "substituted: deser.BasicDeserializerFactory (hop 1, 1895 lines, anchor after createMapDeserializer, seed 6477), "
               "util.TokenBuffer (hop 2, 1802, after writeBinary, 6478), ObjectMapper (hop 3, 3823, after "
               "getDeserializationContext, 6479), deser.BeanDeserializerBase (hop 4, 1533, after createContextual, 6480; the "
               "smallest host), ObjectReader (hop 5, gold, 1760, after withType, 6481). All five are public top-level classes in "
               "which a public static method compiles (BasicDeserializerFactory and BeanDeserializerBase are abstract, which "
               "does not affect a static method); the five are exactly the five public classes of at least 1,500 lines other "
               "than the facade's file TypeFactory.java (facade_files_excluded). The facade calls hop 1 by its fully-qualified "
               "name; each hop reaches the next host through an existing import (BasicDeserializerFactory imports util.*, "
               "TokenBuffer databind.*, ObjectMapper deser.*, BeanDeserializerBase databind.*) and imports type.TypeFactory "
               "where it is not imported yet (TokenBuffer, BeanDeserializerBase); the gold imports "
               "java.util.Collection (ObjectReader already imports java.util.Map and type.TypeFactory).",
}
