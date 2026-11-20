"""Main run JacksonDatabind-44 (C10 recipe on the fixed checkout of Defects4J JacksonDatabind-44; the real bug modified SimpleType,
the target class; batch 5, facade reuse of JacksonDatabind-37, recorded in batch5_tasks.json).

Facade: SimpleType.construct(Class<?>) (the only allowed target, BATCH5_PREREGISTRATION.md row JacksonDatabind-44). It has no
production caller; its only test callers are the methods of interop.DeprecatedTypeHandling1102Test.
Original computation of the facade: an IllegalArgumentException for a Map, a Collection or an array class (in that order, each
with its own message); then the type of the class with empty bindings, no handlers, no interfaces, and as super class the
skeletal type of its whole super-class chain (private _buildSuperClass: null for no super-class, the unknown (Object) type for
Object, otherwise a SimpleType of the super-class over the skeletal type of its own super-class, recursively).

No host is in the type package, so no hop can call SimpleType's protected constructors. The gold uses the two public routes that
give the original instances: SimpleType.constructUnsafe(cls) (empty bindings, no super class) for a class with no super-class
(Object, interfaces, primitive types), and, for every other class, the bare type of the root of its super-class chain narrowed to
the class with JavaType.forcedNarrowBy: SimpleType._narrow stitches the hierarchy from that root down (a direct child gets the
root's type as super class, a deeper class the narrowed type of its super-class, recursively), with the same empty bindings, null
interfaces, null handlers and no static typing as _buildSuperClass. The root of a class's super-class chain is Object, whose bare
type has the same fields as TypeFactory.unknownType(), so the correct configuration returns, field for field, the original result
for every input (same guards in the same order with the same messages).

Chain (hosts in draw order for seed 5133, mr_lib preview, target com/fasterxml/jackson/databind/type/SimpleType.java, none
skipped):
  facade SimpleType.construct                         guard: a Map class -> IllegalArgumentException
  hop 1 deser.BeanDeserializerBase.simpleBeanType      decision: a Collection class -> IllegalArgumentException
  hop 2 ObjectMapper.rawSimpleType                    pass-through
  hop 3 ObjectReader.simpleValueType                  decision: an array class -> IllegalArgumentException
  hop 4 util.TokenBuffer.simpleTypeFor                pass-through
  hop 5 deser.BasicDeserializerFactory.simpleTypeOf   GOLD: the bare type for a class with no super-class; otherwise the walk
                                                      up the super-class chain to its root and the narrowing of the root's bare
                                                      type to the class

Fault (omission of the walk, an iteration, in the gold): the loop that moves `base` from the super-class up to the root of the
chain is dropped, so the type is narrowed from the bare type of the immediate super-class. The gold then reads as an ordinary
"type of the class over the type of its super-class" routine. For a direct child of Object nothing changes (the immediate
super-class is the root). For a deeper class the super-class's type is bare: it has no super class of its own, and bean
introspection (AnnotatedClass._findFields) collects the fields of a type only when it has a super class, so the fields declared
in the super-class are no longer found (its getters and setters still are). Trigger: the EXISTING test
DeprecatedTypeHandling1102Test::testPOJOSubType (Point3D extends Point; reads {'x':1,'z':3,'y':2} with
SimpleType.construct(Point3D.class)) fails with UnrecognizedPropertyException 'Unrecognized field "x"' (2 known properties "y",
"z"; x is a public field of Point, y its setter). testSimplePOJOType, testExplicitCollectionType and testExplicitMapType construct
Point and String (direct children of Object) and still pass; testDeprecatedTypeResolution does not reach the chain; no other test
reaches it (full suite on the variant in a scratch copy: only the trigger fails).

The gold's javadoc states the idiomatic contract (the simple type of a raw class) and is silent on the super-class chain. On the
trigger input the variant's type violates the JavaType contract of a type: its super class (the type of Point) has no super class
although Point has the parent class Object (JavaType.getSuperClass: 'fully resolved parent class of this type, if it has one;
null if not'), and bean introspection of Point3D therefore misses Point's field.

External pins (convention outside the gold): SimpleType._narrow (the method the real bug fixed) stitches the full hierarchy of a
narrowed SimpleType ('stitch together the hierarchy. First, super-class'), and TestSubtypes::testIssue1125WithDefault passes on
it: Default1125 is narrowed from Base1125 through Interm1125 (TypeDeserializerBase calls forcedNarrowBy in production) and the
inherited a (Base1125) and b (Interm1125) are read; TestSubtypes::testIssue1125NonDefault likewise for Impl1125;
TypeFactory._fromClass resolves the super class of every class type, recursively; ClassUtil.findSuperTypes (used by
AnnotatedClass.construct) collects the members to introspect only through getSuperClass(). The facade's own (2.7.0-era)
javadoc sentence that parent classes are not accessible predates the _buildSuperClass fix and is contradicted by the correct
and the variant configuration alike (both give Point3D a super class); it is kept unchanged.

Single owner: only the gold builds the type and decides which class it is narrowed from; hops 1 and 3 reject Collection and array
classes, hops 2 and 4 pass the class along, and every hop returns the type it receives. Once the type has been built over a bare
super-class type, no caller can repair it with the gold's output (SimpleType has no public factory taking a super class; narrowing
a type to its own class returns it unchanged). Declared alternatives (G9): hop 4 narrows the type it gets to its own class; hop 2
specializes it to its class through TypeFactory.constructSpecializedType; hop 3 keeps the more specific of it and the unknown
type (TypeFactory.moreSpecificType). Each returns the type unchanged and the trigger still fails.
Recorded one-line edits above the gold that pass the trigger and the full suite (each checked on the variant in a scratch copy:
trigger passes, defects4j test reports 0 failing tests):
 B-0 bypass: the facade or any of hops 1-4 returns (SimpleType) TypeFactory.unknownType().forcedNarrowBy(cls) (checked at hop 4)
     or (SimpleType) TypeFactory.defaultInstance().constructType(cls) (full resolution, which also resolves interfaces and
     generics; checked at hop 1), discarding the rest of the chain including the gold.
 B-1 test-fitted: a hop asks its callee for the type of the SUPER-class and narrows that to the class, e.g. hop 4
     `return (SimpleType) BasicDeserializerFactory.simpleTypeOf(cls.getSuperclass()).forcedNarrowBy(cls);`. It passes the suite
     only because no test constructs a class more than two levels below Object, and the chain stays wrong: checked with a scratch
     test (not part of the instance), for C extends B extends A, reading {'a':1,'b':2,'c':3} with construct(C.class) fails with
     'Unrecognized field "a"' under this edit exactly as on the variant (and passes on the correct configuration), unlike
     _narrow's full chain (TestSubtypes 1125: Default1125 -> Interm1125 -> Base1125); construct(Object.class) and
     construct(Runnable.class) (which the facade accepts) throw NullPointerException. The guarded form
     `simpleTypeOf(cls.getSuperclass() == null ? cls : cls.getSuperclass())` removes the NullPointerException but still fails
     the depth-three case.

Lie: the facade's javadoc claims the type is first looked up in a cache of the types already constructed, keyed by class name,
and that a new instance is constructed and added to that cache only when the lookup finds none; the chain looks nothing up and
caches nothing. It names neither super-classes nor the omitted walk nor any hop.

Pre-edits (behaviour-preserving, needed by the recipe):
 (1) `@Deprecated` moves from its own line into the modifier list (`public @Deprecated static SimpleType construct(...)`): the
     recipe appends the lie only to a javadoc that is followed by whitespace alone (extract_transform.find_javadoc_start), and the
     annotation line in between would make it skip the lie silently. The annotation, its retention and the doc comment's
     attachment are unchanged.
 (2) The private helper _buildSuperClass, its javadoc and the 'Internal methods' section header (left empty) are removed: after
     the facade rewrite the helper has no caller, and it would be a second, dead implementation of the gold's step in the
     facade's class (as the private getMode in Stage B B4). One whitespace-only line (the file has several) takes the place of
     the section and the blank line before it: mr_spec.derive_edits cannot express a pure line deletion far from any other
     change (the joined old block drops its final newline), so the removal is written as a replacement.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (base = cls.getSuperclass(); bare type of cls if base is null; while base has a super-class, base moves up;
 the bare type of base narrowed to cls):
  T1 absent: cls is read for its super-class, by the bare-type return and by the narrowing.
  T2 absent: base is computed from cls (not a literal), is the loop's cursor and is assigned inside the loop, and is read by the
     decision, the loop test and the return; the if and the final return give different types; no frozen or dead local.
  T3 absent: one decision with two complementary outcomes (a super-class or none); no closed set with a member left out; the
     javadoc names no class.
  T4 absent: the javadoc names only 'the simple type of a raw class'; no rule, bound, value class or case; no comment.
 Variant gold (javadoc; `Class<?> base = cls.getSuperclass(); if (base == null) { return SimpleType.constructUnsafe(cls); }
 return (SimpleType) SimpleType.constructUnsafe(base).forcedNarrowBy(cls);`):
  T1 absent: cls is read for its super-class, in the bare-type return and as the narrowing target; each changes the result.
  T2 absent: base is computed from cls (not a literal) and is read by the decision and by the final return; there is no loop,
     so nothing a loop should move is left unassigned; the if returns the bare type of cls, the fall-through a narrowed type, so
     the decision matters.
  T3 absent: the only decision has two complementary outcomes (base null or not); no case, branch, decode or check gives a
     treatment to some members of a closed set and not to another; no pair or range ends; the text names no class.
  T4 absent: 'Helper method for constructing the simple type of a raw class', '@param cls Raw class to construct the type for' and
     '@return Simple type of the class' are general descriptions that the two returns address; no limit, value class, case or
     property is named; no inline comment; the identifiers (simpleTypeOf, cls, base) name nothing the body does not meet."""

SRC = "src/main/java/com/fasterxml/jackson/databind"
ST = f"{SRC}/type/SimpleType.java"
BDB = f"{SRC}/deser/BeanDeserializerBase.java"
OM = f"{SRC}/ObjectMapper.java"
OR = f"{SRC}/ObjectReader.java"
TB = f"{SRC}/util/TokenBuffer.java"
BDF = f"{SRC}/deser/BasicDeserializerFactory.java"

GOLD_TEXT = '''/**
 * Helper method for constructing the simple type of a raw class.
 *
 * @param cls Raw class to construct the type for
 *
 * @return Simple type of the class
 */
public static SimpleType simpleTypeOf(Class<?> cls) {
    Class<?> base = cls.getSuperclass();
    if (base == null) {
        return SimpleType.constructUnsafe(cls);
    }
    while (base.getSuperclass() != null) {
        base = base.getSuperclass();
    }
    return (SimpleType) SimpleType.constructUnsafe(base).forcedNarrowBy(cls);
}'''

HOP1 = '''/**
 * Helper method for constructing the simple type of a raw class that is
 * not a Map type.
 *
 * @param cls Raw class to construct the type for
 *
 * @return Simple type of the class
 *
 * @throws IllegalArgumentException if the class is a Collection type
 */
public static SimpleType simpleBeanType(Class<?> cls) {
    if (Collection.class.isAssignableFrom(cls)) {
        throw new IllegalArgumentException("Can not construct SimpleType for a Collection (class: "+cls.getName()+")");
    }
    return ObjectMapper.rawSimpleType(cls);
}'''

HOP2 = '''/**
 * Helper method for constructing the simple type of a raw class that is
 * neither a Map nor a Collection type.
 *
 * @param cls Raw class to construct the type for
 *
 * @return Simple type of the class
 */
public static SimpleType rawSimpleType(Class<?> cls) {
    return ObjectReader.simpleValueType(cls);
}'''

HOP3 = '''/**
 * Helper method for constructing the simple type of a raw class that is
 * neither a Map nor a Collection type.
 *
 * @param cls Raw class to construct the type for
 *
 * @return Simple type of the class
 *
 * @throws IllegalArgumentException if the class is an array type
 */
public static SimpleType simpleValueType(Class<?> cls) {
    if (cls.isArray()) {
        throw new IllegalArgumentException("Can not construct SimpleType for an array (class: "+cls.getName()+")");
    }
    return TokenBuffer.simpleTypeFor(cls);
}'''

HOP4 = '''/**
 * Helper method for constructing the simple type of a raw class that is
 * not a Map, Collection or array type.
 *
 * @param cls Raw class to construct the type for
 *
 * @return Simple type of the class
 */
public static SimpleType simpleTypeFor(Class<?> cls) {
    return BasicDeserializerFactory.simpleTypeOf(cls);
}'''

BUILD_SUPER = '''    /*
    /**********************************************************
    /* Internal methods
    /**********************************************************
     */

    /**
     * Helper method we need to recursively build skeletal representations
     * of superclasses.
     *\x20
     * @since 2.7 -- remove when not needed (2.8?)
     */
    private static JavaType _buildSuperClass(Class<?> superClass, TypeBindings b)
    {
        if (superClass == null) {
            return null;
        }
        if (superClass == Object.class) {
            return TypeFactory.unknownType();
        }
        JavaType superSuper = _buildSuperClass(superClass.getSuperclass(), b);
        return new SimpleType(superClass, b,
                superSuper, null, null, null, false);
    }

'''

DESIGN = {
 "instance": "JacksonDatabind-44", "project": "JacksonDatabind", "bug_id": 44, "seed": 5133,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": ST, "class": "com.fasterxml.jackson.databind.type.SimpleType", "method": "construct", "near_line": 101},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/interop/DeprecatedTypeHandling1102Test.java",
             "test_class": "com.fasterxml.jackson.databind.interop.DeprecatedTypeHandling1102Test",
             "test_method": "testPOJOSubType"},
 "expected_signature": "Unrecognized field \"x\"",
 "gold": {"method": "simpleTypeOf", "text": GOLD_TEXT,
          "fault": {"old": "        }\n"
                           "        while (base.getSuperclass() != null) {\n"
                           "            base = base.getSuperclass();\n"
                           "        }\n"
                           "        return (SimpleType) SimpleType.constructUnsafe(base).forcedNarrowBy(cls);",
                    "new": "        }\n"
                           "        return (SimpleType) SimpleType.constructUnsafe(base).forcedNarrowBy(cls);"}},
 "pre_edits": {
   "chain": [
     {"file": ST, "old": "    @Deprecated\n    public static SimpleType construct(Class<?> cls)\n",
      "new": "    public @Deprecated static SimpleType construct(Class<?> cls)\n"},
     {"file": ST, "old": "\n" + BUILD_SUPER, "new": "    \n"},
   ],
 },
 "chain": {
   "facade_body": "if (Map.class.isAssignableFrom(cls)) {\n"
                  "            throw new IllegalArgumentException(\"Can not construct SimpleType for a Map (class: \"+cls.getName()+\")\");\n"
                  "        }\n"
                  "        return com.fasterxml.jackson.databind.deser.BeanDeserializerBase.simpleBeanType(cls);",
   "lie": "The type is first looked up in a cache of the types already constructed, keyed by class name, and a new "
          "instance is constructed and added to that cache only when the lookup finds none.",
   "hops": [
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "simpleBeanType",
      "imports": ["com.fasterxml.jackson.databind.type.SimpleType"], "text": HOP1},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "rawSimpleType",
      "imports": [], "text": HOP2},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "simpleValueType",
      "imports": ["com.fasterxml.jackson.databind.util.TokenBuffer"], "text": HOP3},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "simpleTypeFor",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "com.fasterxml.jackson.databind.type.SimpleType"],
      "text": HOP4},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "simpleTypeOf",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.type.SimpleType::_narrow",
              "com.fasterxml.jackson.databind.type.TypeFactory::_fromClass",
              "com.fasterxml.jackson.databind.util.ClassUtil::findSuperTypes",
              "com.fasterxml.jackson.databind.JavaType::getSuperClass"],
 "ownership_reason": "Only the gold builds the type of the class: it walks the super-class chain to its root and narrows the root's "
                     "bare type to the class, so that SimpleType._narrow links the type of every super-class; with the walk "
                     "omitted it narrows from the bare type of the immediate super-class, whose type then has no super class of "
                     "its own, and bean introspection (AnnotatedClass._findFields) skips the fields of a type without a super "
                     "class. Hops 1 and 3 reject Collection and array classes, hops 2 and 4 pass the class along, and every hop "
                     "returns the type it receives; once that type is built no caller can repair it with the gold's output "
                     "(SimpleType has no public factory taking a super class, and narrowing a type to its own class returns it "
                     "unchanged). The convention is pinned outside the gold: a JavaType's super class is the 'fully resolved "
                     "parent class of this type, if it has one' (JavaType.getSuperClass), and Point has the parent Object; bean "
                     "introspection finds inherited members only through getSuperClass (ClassUtil.findSuperTypes, used by "
                     "AnnotatedClass.construct); SimpleType._narrow stitches the full super-class hierarchy of a narrowed "
                     "SimpleType, and TestSubtypes testIssue1125WithDefault / testIssue1125NonDefault read the properties "
                     "inherited from two levels up through such types (Default1125 narrowed from Base1125 through Interm1125, "
                     "TypeDeserializerBase); TypeFactory._fromClass resolves the super class of every class type, recursively. "
                     "The other DeprecatedTypeHandling1102Test methods use direct children of Object and pass. A one-line edit "
                     "above the gold that narrows the callee's type of the super-class to the class passes the existing tests "
                     "but leaves the chain wrong one level further up (C extends B extends A loses A's fields, as on the "
                     "variant) and, unguarded, makes construct(Object.class) and every interface throw NullPointerException.",
 "ownership_tests": ["com.fasterxml.jackson.databind.jsontype.TestSubtypes::testIssue1125WithDefault",
                     "com.fasterxml.jackson.databind.jsontype.TestSubtypes::testIssue1125NonDefault",
                     "com.fasterxml.jackson.databind.interop.DeprecatedTypeHandling1102Test::testSimplePOJOType",
                     "com.fasterxml.jackson.databind.interop.DeprecatedTypeHandling1102Test::testExplicitCollectionType",
                     "com.fasterxml.jackson.databind.interop.DeprecatedTypeHandling1102Test::testExplicitMapType"],
 "compensating": {
   "chain": [
     {"file": TB, "old": "        return BasicDeserializerFactory.simpleTypeOf(cls);",
      "new": "        return (SimpleType) BasicDeserializerFactory.simpleTypeOf(cls).forcedNarrowBy(cls);",
      "why": "hop 4 narrows the type it gets to the class itself"},
     {"file": OM, "old": "        return ObjectReader.simpleValueType(cls);",
      "new": "        return (SimpleType) TypeFactory.defaultInstance().constructSpecializedType(ObjectReader.simpleValueType(cls), cls);",
      "why": "hop 2 specializes the type to its class through the type factory"},
     {"file": OR, "old": "        return TokenBuffer.simpleTypeFor(cls);",
      "new": "        return (SimpleType) TypeFactory.defaultInstance().moreSpecificType(TokenBuffer.simpleTypeFor(cls), TypeFactory.unknownType());",
      "why": "hop 3 keeps the more specific of the type and the unknown type"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 5133 (mr_lib preview, target com/fasterxml/jackson/databind/type/SimpleType.java): "
               "deser.BeanDeserializerBase (hop 1), ObjectMapper (hop 2), ObjectReader (hop 3), util.TokenBuffer (hop 4), "
               "deser.BasicDeserializerFactory (hop 5, gold; drawn as the last remaining host: the pool has exactly five classes "
               "of at least 1,500 lines besides the target). All five are public top-level classes in which a static method "
               "compiles (BeanDeserializerBase and BasicDeserializerFactory are abstract, which does not affect a static method); "
               "every preview anchor is an outer-class method; none was skipped. No host is in the type package, so the chain "
               "builds the type through the public SimpleType.constructUnsafe and JavaType.forcedNarrowBy (deprecated since "
               "2.7, like the facade; javac only warns). The facade calls hop 1 by its fully-qualified name; each hop imports "
               "the next host and SimpleType where its file does not already (ObjectMapper and BasicDeserializerFactory import "
               "the type package, ObjectReader imports SimpleType; ObjectMapper and ObjectReader share a package).",
}
