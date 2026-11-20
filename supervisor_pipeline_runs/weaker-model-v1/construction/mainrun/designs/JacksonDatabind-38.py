"""Main run JacksonDatabind-38 (C10 recipe on the fixed checkout of Defects4J JacksonDatabind-38; the real bug modified
CollectionType, MapType and SimpleType; the facade's class CollectionType is one of them).

Facade: CollectionType.construct(Class<?>, JavaType), the deprecated two-argument overload (allowed target CollectionType.construct,
BATCH5_PREREGISTRATION.md row JacksonDatabind-38). The five-argument overload construct(Class, TypeBindings, JavaType, JavaType[],
JavaType) is a single constructor call with no computation of its own and is called by TypeFactory for every collection type, so
it cannot carry a chain whose fault fails exactly one test. The other allowed target, MapType.construct(Class, JavaType, JavaType),
has the same computation for maps; it was set aside because its per-type core binds a pair (key and value), so any omission there
leaves one half of a pair treated (checklist T3(b)), and because it has no javadoc to carry the lie. The deprecated
CollectionType.construct has no production caller; its only caller is DeprecatedTypeHandling1102Test::testExplicitCollectionType.
Original computation of the facade: when the raw class declares exactly one type parameter, bind it to the element type
(TypeBindings.create(rawType, elemT)), otherwise use the empty bindings; give the class the unknown type as nominal super class
unless it has no super class (interfaces: null; TypeBase._bogusSuperClass); construct the type with no super-interfaces.

Chain (hosts in draw order for seed 5675, mr_lib preview, target com/fasterxml/jackson/databind/type/CollectionType.java, none
skipped):
  hop 1 util.TokenBuffer.collectionTypeFor               pass-through
  hop 2 ObjectMapper.collectionTypeOf                    placement: the nominal super class (null when the raw class has no
                                                         super class, else the unknown type)
  hop 3 deser.BasicDeserializerFactory.collectionTypeWith placement: no super-interfaces are resolved (null)
  hop 4 ObjectReader.collectionTypeFrom                  pass-through
  hop 5 deser.BeanDeserializerBase.typeForCollection     GOLD: the type construction with its per-class binding decision
                                                         (a raw class with one type parameter has it bound to the element type)
The correct configuration returns the original result for every input: the same bindings (create for exactly one type
parameter; getTypeParameters() never returns null), the same nominal super class, null super-interfaces, and the public
five-argument CollectionType.construct, which is exactly the private constructor call of the original with null handlers and
asStatic false.

Fault (omission of a decision in the gold): the branch that binds the type parameter of a one-parameter raw class to the element
type is dropped, so every raw class gets the empty bindings. Trigger: the EXISTING test
DeprecatedTypeHandling1102Test::testExplicitCollectionType. CollectionType.construct(List.class, Point) now has no bindings; when
the deserializer factory refines the abstract List into ArrayList (TypeFactory.constructSpecializedType: "Original target type has
no generics -- just resolve subtype"), the element type is lost, the elements are read as maps, and
assertEquals(Point.class, ob.getClass()) fails with expected:<class ...DeprecatedTypeHandling1102Test$Point> but was:<class
java.util.LinkedHashMap>. No other test reaches the facade (checked: the full suite on a scratch copy with the bindings dropped
fails only this test). The gold's javadoc states the idiomatic contract (the collection type of a raw collection class whose
elements are of the given type) and is silent on type parameters and bindings; the type it returns for (List, Point) does not
behave as a List whose elements are Points.

External pins (convention outside the gold): the three sibling deprecated factories do the same step explicitly, each with the
comment "may need to fabricate TypeBindings (needed for refining into concrete collection types, as per [databind#1102])":
CollectionLikeType.construct(Class, JavaType) (one type parameter, identical rule), MapType.construct(Class, JavaType, JavaType)
and MapLikeType.construct (two type parameters); TypeFactory.constructCollectionType(Class, JavaType) binds the collection class's
type parameter to the element type (TypeBindings.create) before constructing. Passing tests: DeprecatedTypeHandling1102Test::
testExplicitMapType (the abstract Map built by the deprecated MapType factory refines with its value type kept),
TestTypeFactory::testCollectionTypesRefined (List<Long> refined to ArrayList keeps Long, which reads the bindings),
TestTypeFactory::testCollections and ::testParametricTypes.

Single owner: only the gold holds the raw class together with the element type at the point where the type is built and its
bindings are chosen. Hops 2 and 3 choose the super types, which do not affect refinement; hops 1 and 4 pass the arguments along.
No change of the gold's inputs makes the empty bindings carry the element type. Declared alternatives (G9): hop 2 resolves the
nominal super class from the generic super class of the raw class (null for an interface, as before); hop 3 passes the
super-interfaces resolved by the default type factory; hop 4 replaces a null element type by the unknown type. None changes the
trigger's bindings.
Recorded edits outside the gold that pass the trigger and the full suite (to be read as bypasses, not repairs; each checked on
the variant in a scratch copy: trigger passes, defects4j test 0 failing tests; B-3 checked in all three forms):
 B-0 bypass: the facade (its original body) or any of hops 1-4 builds the type itself, e.g. hop 4
     `return CollectionType.construct(rawType, TypeBindings.create(rawType, elemT), superClass, superInts, elemT);`,
     discarding the gold.
 B-1 second implementation: hop 4 re-binds the gold's result,
     `return (CollectionType) BeanDeserializerBase.typeForCollection(rawType, superClass, superInts, elemT).refine(rawType, TypeBindings.createIfNeeded(rawType, elemT), superClass, superInts);`
     (the gold's decision done again above it; createIfNeeded also throws for a raw class with two or more type parameters,
     which the original accepts with the empty bindings).
 B-2 test-fitted: a hop replaces an interface by a concrete class, e.g. hop 1
     `return ObjectMapper.collectionTypeOf(rawType.isInterface() ? java.util.ArrayList.class : rawType, elemT);`:
     the trigger only inspects the elements, but the returned type's raw class is no longer the requested class (ArrayList for
     List, and also for Set), which contradicts every hop's documented contract and the facade's.
 B-3 downstream compensation of the unbound type in shared code:
     (a) TypeFactory.constructSpecializedType `if (baseType.getBindings().isEmpty() && !baseType.isContainerType()) {`;
     (b) BasicDeserializerFactory._mapAbstractCollectionType
         `return (CollectionType) config.constructSpecializedType(type, collectionClass).withContentType(type.getContentType());`;
     (c) the five-argument CollectionType.construct passing
         `(bindings.isEmpty() && rawType.getTypeParameters().length == 1) ? TypeBindings.create(rawType, elemT) : bindings`
         to its constructor, overriding the bindings it is given. Each re-derives
     the binding that the type's constructor is meant to provide; the evidence factories state that the fabricated bindings are
     "needed for refining into concrete collection types", i.e. refinement reading the bindings is the convention, and the
     five-argument factory takes the bindings its caller resolved (TypeFactory passes the empty bindings for a raw Collection on
     purpose: "ok to have no types ("raw")").

Lie: the facade's javadoc claims the nominal super class is resolved by walking the superclass chain of the raw class up to
java.lang.Object, each class being resolved with the default type factory; the chain walks nothing and uses the unknown type (or
null). It names neither type parameters, bindings nor any step that is omitted, nor any hop.

Pre-edit (behaviour-preserving, needed by the recipe): the `@Deprecated // since 2.7` line between the facade's javadoc and its
header is moved into the modifier list (`public @Deprecated static`, the same annotation, which Java treats identically); with it
in place rewrite_facade finds no adjacent javadoc and cannot append the lie. The end-of-line comment is dropped.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: rawType decides the branch and is the constructed class; superClass, superInts and elemT are passed to the
     construction in both branches (elemT also to the bindings).
  T2 absent: no local variable; the if returns a type with bound parameters, the fall-through one with the empty bindings: two
     different effects.
  T3 absent: one arity (exactly one type parameter) of an unnamed set of three or more (none, one, several) is treated; no pair
     half or range end; the javadoc names no class.
  T4 absent: the javadoc names only the collection type of a raw class with elements of the given type and caller-supplied
     super types; no rule, limit, value class or case.
 Variant gold (javadoc, signature, `return CollectionType.construct(rawType, TypeBindings.emptyBindings(), superClass, superInts,
 elemT);`):
  T1 absent: each of rawType, superClass, superInts and elemT is an argument of the construction and changes the returned type;
     there is no argument check.
  T2 absent: no local variable, no loop, no branch, case or ternary.
  T3 absent: no case, branch or check remains, so no set has a handled and an unhandled member (no member handled).
  T4 absent: 'Constructs the collection type of a raw collection class whose elements are of the given type' is a general
     description that the construction line addresses; '@param ... Nominal super class / Super-interfaces of the raw class' are
     caller preconditions; no concrete rule, bound, value class, case or property is named; no inline comment; the identifiers
     (typeForCollection, rawType, superClass, superInts, elemT) name nothing the body does not meet."""

CT = "src/main/java/com/fasterxml/jackson/databind/type/CollectionType.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"

GOLD_TEXT = '''/**
 * Constructs the collection type of a raw collection class whose
 * elements are of the given type.
 *
 * @param rawType Raw collection class
 * @param superClass Nominal super class of the raw class
 * @param superInts Super-interfaces of the raw class
 * @param elemT Type of the elements
 *
 * @return Collection type constructed
 */
public static CollectionType typeForCollection(Class<?> rawType, JavaType superClass,
        JavaType[] superInts, JavaType elemT) {
    if (rawType.getTypeParameters().length == 1) {
        return CollectionType.construct(rawType, TypeBindings.create(rawType, elemT),
                superClass, superInts, elemT);
    }
    return CollectionType.construct(rawType, TypeBindings.emptyBindings(),
            superClass, superInts, elemT);
}'''

HOP1 = '''/**
 * Helper method for constructing the collection type of a raw collection
 * class whose elements are of the given type.
 *
 * @param rawType Raw collection class
 * @param elemT Type of the elements
 *
 * @return Collection type constructed
 */
public static CollectionType collectionTypeFor(Class<?> rawType, JavaType elemT) {
    return ObjectMapper.collectionTypeOf(rawType, elemT);
}'''

HOP2 = '''/**
 * Helper method for constructing the collection type of a raw collection
 * class whose elements are of the given type, when the super-type
 * hierarchy of the class has not been resolved. A class that has no
 * super class (such as an interface) gets no nominal super class; any
 * other class gets the unknown type as its nominal super class.
 *
 * @param rawType Raw collection class
 * @param elemT Type of the elements
 *
 * @return Collection type constructed
 */
public static CollectionType collectionTypeOf(Class<?> rawType, JavaType elemT) {
    JavaType superClass = (rawType.getSuperclass() == null) ? null : TypeFactory.unknownType();
    return BasicDeserializerFactory.collectionTypeWith(rawType, superClass, elemT);
}'''

HOP3 = '''/**
 * Helper method for constructing the collection type of a raw collection
 * class with the given nominal super class, whose elements are of the
 * given type. No super-interfaces are resolved for the type.
 *
 * @param rawType Raw collection class
 * @param superClass Nominal super class of the raw class
 * @param elemT Type of the elements
 *
 * @return Collection type constructed
 */
public static CollectionType collectionTypeWith(Class<?> rawType, JavaType superClass, JavaType elemT) {
    return ObjectReader.collectionTypeFrom(rawType, superClass, null, elemT);
}'''

HOP4 = '''/**
 * Helper method for constructing the collection type of a raw collection
 * class with the given super types, whose elements are of the given type.
 *
 * @param rawType Raw collection class
 * @param superClass Nominal super class of the raw class
 * @param superInts Super-interfaces of the raw class
 * @param elemT Type of the elements
 *
 * @return Collection type constructed
 */
public static CollectionType collectionTypeFrom(Class<?> rawType, JavaType superClass,
        JavaType[] superInts, JavaType elemT) {
    return BeanDeserializerBase.typeForCollection(rawType, superClass, superInts, elemT);
}'''

DESIGN = {
 "instance": "JacksonDatabind-38", "project": "JacksonDatabind", "bug_id": 38, "seed": 5675,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": CT, "class": "com.fasterxml.jackson.databind.type.CollectionType", "method": "construct", "near_line": 47},
 "trigger": {"existing": True,
             "test_file": "src/test/java/com/fasterxml/jackson/databind/interop/DeprecatedTypeHandling1102Test.java",
             "test_class": "com.fasterxml.jackson.databind.interop.DeprecatedTypeHandling1102Test",
             "test_method": "testExplicitCollectionType"},
 "expected_signature": "but was:<class java.util.LinkedHashMap>",
 "gold": {"method": "typeForCollection", "text": GOLD_TEXT,
          "fault": {"old": "        if (rawType.getTypeParameters().length == 1) {\n"
                           "            return CollectionType.construct(rawType, TypeBindings.create(rawType, elemT),\n"
                           "                    superClass, superInts, elemT);\n"
                           "        }\n"
                           "        return CollectionType.construct(rawType, TypeBindings.emptyBindings(),",
                    "new": "        return CollectionType.construct(rawType, TypeBindings.emptyBindings(),"}},
 "pre_edits": {
   "chain": [{"file": CT,
              "old": "    @Deprecated // since 2.7\n"
                     "    public static CollectionType construct(Class<?> rawType, JavaType elemT) {",
              "new": "    public @Deprecated static CollectionType construct(Class<?> rawType, JavaType elemT) {"}],
 },
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.util.TokenBuffer.collectionTypeFor(rawType, elemT);",
   "lie": "The nominal super class is resolved by walking the superclass chain of the raw class up to java.lang.Object, "
          "each class on the way being resolved with the default type factory.",
   "hops": [
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "collectionTypeFor",
      "imports": ["com.fasterxml.jackson.databind.type.CollectionType"], "text": HOP1},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "collectionTypeOf",
      "imports": [], "text": HOP2},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "collectionTypeWith",
      "imports": [], "text": HOP3},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "collectionTypeFrom",
      "imports": ["com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "com.fasterxml.jackson.databind.type.CollectionType"],
      "text": HOP4},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "typeForCollection",
      "imports": ["com.fasterxml.jackson.databind.type.CollectionType", "com.fasterxml.jackson.databind.type.TypeBindings"],
      "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.type.CollectionLikeType::construct",
              "com.fasterxml.jackson.databind.type.MapType::construct",
              "com.fasterxml.jackson.databind.type.MapLikeType::construct",
              "com.fasterxml.jackson.databind.type.TypeFactory::constructCollectionType"],
 "ownership_reason": "Only the gold holds the raw class together with the element type where the type is built and its bindings "
                     "are chosen; hops 2 and 3 choose the super types, which refinement does not read, and hops 1 and 4 pass the "
                     "arguments along, so no change of the gold's inputs lets the empty bindings carry the element type. With the "
                     "empty bindings the List type loses its element type as soon as the deserializer refines it into ArrayList "
                     "(TypeFactory.constructSpecializedType: 'Original target type has no generics -- just resolve subtype'), "
                     "the elements are read as maps, and the type is not the collection type of List whose elements are Points "
                     "that the gold's javadoc promises. The convention is pinned outside the gold: the sibling deprecated "
                     "factories CollectionLikeType.construct (the identical one-parameter rule), MapType.construct and "
                     "MapLikeType.construct (two parameters) bind the raw class's type parameters to the given types, each with "
                     "the comment 'may need to fabricate TypeBindings (needed for refining into concrete collection types, as "
                     "per [databind#1102])', and TypeFactory.constructCollectionType binds the collection class's type parameter "
                     "to the element type before constructing. Passing tests: DeprecatedTypeHandling1102Test.testExplicitMapType "
                     "(the deprecated Map factory's type refines with its value type kept) and "
                     "TestTypeFactory.testCollectionTypesRefined (List<Long> refined to ArrayList keeps Long). Edits outside the "
                     "gold that pass the trigger and the full suite are bypasses, not repairs: the facade's original body, or a "
                     "hop building the type itself (hop 4 returning CollectionType.construct(rawType, TypeBindings.create(rawType, "
                     "elemT), superClass, superInts, elemT)), discards the gold; hop 4 re-binding the gold's result with "
                     "refine(rawType, TypeBindings.createIfNeeded(rawType, elemT), superClass, superInts) does the gold's "
                     "decision a second time above it; a hop substituting ArrayList for an interface raw class returns the type "
                     "of another class than the one every hop documents. Edits in shared code that tolerate the unbound type "
                     "(TypeFactory.constructSpecializedType skipping its documented shortcut '(1) Original target type has no "
                     "generics -- just resolve subtype' for container types; BasicDeserializerFactory._mapAbstractCollectionType "
                     "re-applying the content type after the specialisation; the five-argument CollectionType.construct "
                     "overriding the bindings its caller resolved, although TypeFactory._collectionType passes the empty "
                     "bindings for a raw Collection on purpose: 'ok to have no types (\"raw\")') re-derive downstream the "
                     "binding that, by the evidence factories' own comment, the constructing factory has to fabricate because "
                     "refinement reads it.",
 "ownership_tests": ["com.fasterxml.jackson.databind.interop.DeprecatedTypeHandling1102Test::testExplicitMapType",
                     "com.fasterxml.jackson.databind.type.TestTypeFactory::testCollectionTypesRefined",
                     "com.fasterxml.jackson.databind.type.TestTypeFactory::testCollections",
                     "com.fasterxml.jackson.databind.type.TestTypeFactory::testParametricTypes"],
 "compensating": {
   "chain": [
     {"file": OM, "old": "JavaType superClass = (rawType.getSuperclass() == null) ? null : TypeFactory.unknownType();",
      "new": "JavaType superClass = (rawType.getSuperclass() == null) ? null : TypeFactory.defaultInstance().constructType(rawType.getGenericSuperclass());",
      "why": "hop 2 resolves the nominal super class from the generic super class of the raw class"},
     {"file": BDF, "old": "return ObjectReader.collectionTypeFrom(rawType, superClass, null, elemT);",
      "new": "return ObjectReader.collectionTypeFrom(rawType, superClass, TypeFactory.defaultInstance().constructType(rawType).getInterfaces().toArray(new JavaType[0]), elemT);",
      "why": "hop 3 passes the super-interfaces resolved by the default type factory"},
     {"file": OR, "old": "return BeanDeserializerBase.typeForCollection(rawType, superClass, superInts, elemT);",
      "new": "return BeanDeserializerBase.typeForCollection(rawType, superClass, superInts, (elemT == null) ? TypeFactory.unknownType() : elemT);",
      "why": "hop 4 replaces a null element type by the unknown type"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 5675 (mr_lib preview, target com/fasterxml/jackson/databind/type/CollectionType.java): "
               "util.TokenBuffer (hop 1), ObjectMapper (hop 2), deser.BasicDeserializerFactory (hop 3), ObjectReader (hop 4), "
               "deser.BeanDeserializerBase (hop 5, gold; drawn as the last remaining host: the pool of five classes of at least "
               "1,500 lines is exhausted at five). All five are public top-level classes in which a static method compiles "
               "(BasicDeserializerFactory and BeanDeserializerBase are abstract, which does not affect a static method); every "
               "preview anchor (canWriteBinaryNatively, enable, createMapDeserializer, readValues, getValueInstantiator) is a "
               "member of the outer class; none was skipped. The facade calls hop 1 by its fully-qualified name; TokenBuffer, "
               "ObjectReader and BeanDeserializerBase gain imports of CollectionType (and the next host or TypeBindings); "
               "ObjectMapper and BasicDeserializerFactory already import the type and deser packages on demand.",
}
