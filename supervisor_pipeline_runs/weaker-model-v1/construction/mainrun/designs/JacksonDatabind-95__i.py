"""Main run JacksonDatabind-95__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static
facade; fixed checkout of Defects4J JacksonDatabind-95, whose real bug modified TypeFactory and TypeParser; the facade's class is
TypeFactory). No static pair (BUILD_BRIEF_C10I_B8_NOTE.md section 1).

Facade: TypeFactory.moreSpecificType(JavaType, JavaType) (instance method; the only allowed candidate of the task record,
BATCH8_PREREGISTRATION.md row 257). Its facade_planned_by is JacksonDatabind-11__i (facade_reuse_of recorded); no other candidate is
allowed, so the reuse is unavoidable. None of that task's files was opened.
Original computation: a null first type gives the second, a null second type gives the first; otherwise the raw classes are compared:
the same raw class gives the first type; if the first raw class is assignable from the second (the second's class extends or
implements the first's), the second type; otherwise (the first is the more specific, or the two are unrelated) the first type.

facade_variant: V1 (state as parameters), in its degenerate form: the method is pure (task record variant V0: it reads and writes no
field), so the state handed down is the facade's own two parameters. state_passed: type1 and type2 (the two JavaType arguments) to
hop 1; no field is read, none is written, no write-back. The facade body is the original guard (the two null checks) plus one call to
hop 1. No visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test
edit. The facade calls no private method (no V4) and handles no package-private type (no V3/V5).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-95-probe of the fixture, the first
statement of moreSpecificType was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t com.fasterxml.jackson.databind.type.TestTypeFactory::testMoreSpecificType`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at TypeFactory.moreSpecificType(TypeFactory.java:585), called from
TestTypeFactory.java:567. Full suite with the probe: 1 failing test (testMoreSpecificType only); the production caller
ObjectArraySerializer.acceptJsonFormatVisitor is not reached by any test.

Hosts (host_mode = "1500"; `mr_lib.py preview JacksonDatabind-95 com/fasterxml/jackson/databind/type/TypeFactory.java 5` with the
instance seed 4635, the facade's file excluded; used in draw order, none substituted):
  hop 1 ObjectMapper                   3936 lines  specificTypeOf     pass-through
  hop 2 deser.BasicDeserializerFactory 1964 lines  refinedTypeOf      pass-through
  hop 3 ObjectReader                   1913 lines  specializedTypeOf  pass-through
  hop 4 util.TokenBuffer               1917 lines  preferredTypeOf    pass-through
  hop 5 deser.BeanDeserializerBase     1669 lines  narrowerTypeOf     GOLD: the same-class rule, the interface-target rule and the
                                                                      search of the second raw class's superclass chain
Host sizes 3936, 1964, 1913, 1917, 1669; the smallest host (and the gold host) is BeanDeserializerBase (1669 lines).

Redistribution: the null guard stays in the facade (the original's first two statements); hops 1-4 pass the two types along; the gold
holds the whole decision, split the way Jackson's own type lookups split it (TypeBase.findSuperType checks super interfaces only when
the target is an interface, then the superclass chain; SimpleSerializers.findSerializer keys interface and class lookups apart and
walks `for (Class<?> curr = cls; curr != null; curr = curr.getSuperclass())`): the same raw class -> first; an interface target that
is assignable from the second raw class -> second; a target met on the superclass chain of the second raw class -> second; otherwise
first. It calls no private member of any class and uses only java.lang types.
Correct configuration vs the original: identical for every pair whose first raw class is an interface, every pair with the same raw
class, and every pair of non-array types whose first raw class is a class other than Object. It differs only where
Class.isAssignableFrom is true without a superclass path from a class target: (a) a first type of raw class Object with a second type
that is an interface (the original gives the second, the chain the first); (b) array types related only by array covariance (e.g.
Object[] / String[]). No test passes such types (probe: only the trigger reaches the facade, and it uses Collection/List,
Double/Number and Double/String).

Fault (one-line omission in the gold): the interface-target rule
(`if (target.isInterface() && target.isAssignableFrom(start)) { return second; }`) is removed, so the gold decides relatedness only by
the superclass chain of the second raw class. The gold then reads as the ordinary routine "the first type, unless the first's raw class
is met on the second's superclass chain".
Trigger: the EXISTING test TestTypeFactory::testMoreSpecificType; its first assertion assertSame(t2, tf.moreSpecificType(t1, t2)) for
t1 = Collection<Object>, t2 = List<Object> fails (expected same: the List type, was: the Collection type): List is an interface whose
superclass is null, so the variant gold never meets Collection and returns the first type. The other assertions (Double/Number in
both orders, the unrelated Double/String in both orders, List/Collection) give the same result in the variant. It is the only test
that reaches the facade (probe) and the new hops have no other caller, so gate G5 is met.

The gold's javadoc states the idiomatic contract (the second type if its raw class is more specific than the raw class of the first,
otherwise the first) and is silent on how relatedness is established; List is more specific than Collection, so the variant violates
the contract on the trigger input. The convention is pinned outside the gold: the facade's own javadoc ('if they are related; that
is, one implements or extends the other'), TypeBase.findSuperType (searches super interfaces and then the superclass),
SimpleSerializers.findSerializer (interface mappings are found for implementing classes and their subclasses) and
ClassUtil.findRawSuperTypes (interfaces, then the superclass), with passing tests TestTypeFactory::testMapEntryResolution
(findSuperType finds the interface Map.Entry of a class that implements it), TestSimpleModule::testSimpleInterfaceSerializer (a
serializer registered for the interface Base serves Impl1 and its subclass Impl2) and TestTypeResolution::testGeneric (findSuperType
through superclasses).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: first gives target and is returned; second gives start (read by all three decisions and the loop seed) and is returned;
     no argument check.
  T2 absent: target and start are read by the decisions; curr is the loop cursor, advanced by curr = curr.getSuperclass() and read by
     the loop condition and the found test; no literal-initialised local; every decision returns (first / second / second) and each
     changes the result on some input (the same-class test returns first where the loop would return second).
  T3 absent: the gold's kinds of target are told apart by one test, isInterface(), and both outcomes are treated (interface targets by
     assignability, class targets by the superclass chain); no enum, type code or named format; no pair half or range end; the text
     names no class handled in part.
  T4 absent: 'the second type if its raw class is more specific than the raw class of the first type, and the first type otherwise'
     is a general description met by the returns; 'not null' in the @param clauses is a caller precondition; no inline comment.
 Variant gold (javadoc, signature, same-class return, the for loop over curr.getSuperclass(), return first):
  T1 absent: first gives target and is returned; second gives start, which decides the same-class return, seeds the loop and is
     returned when target is met; both change the result.
  T2 absent: target is compared in two decisions; start is read by the same-class decision and seeds the cursor; curr is advanced in
     the loop header and read by the condition and the found test (not frozen); the same-class test is live (without it, the loop's
     first step would return second); no literal-initialised local; no dead branch.
  T3 absent: the gold reads one relation of a class, getSuperclass(), in the ordinary superclass-walk idiom; it tests no flag or kind
     of class, reads no other part of a class, and its text names no interface, supertype, 'implements' or 'extends'; no enum or type
     code; no named format; no pair half or range end; nothing it reads is left untreated (closure rule: no closed set is fixed).
  T4 absent: 'more specific' is the general description of what the method computes (lines of the body address it); 'the first type
     otherwise' is met by the same-class return and the final return; no inline comment; identifiers (target, start, curr) name
     nothing the body does not meet.

Single owner: only the gold decides which type is more specific; hops 1-4 pass the two types along unchanged and the facade only
answers nulls. Once the gold has returned the first type for (Collection, List), a caller can obtain List only by deciding the
relation itself (a second implementation of the gold's decision) or by replacing the gold. Declared alternatives (G9): hop 4 passes
the types in the other order (fails on List/Collection and on the unrelated Double/String pair); hop 1 answers a secondary type that is
an interface with the primary type; hop 3 passes the secondary type's raw-class type via the factory's constructType (a new object,
fails the identity assertions). None makes the trigger pass.
Recorded bypasses:
 B-0 the facade's original body (raw1.isAssignableFrom(raw2)) re-implements the decision; the chain, including the gold, is dead.
 B-1 any hop returns `primary.getRawClass().isAssignableFrom(secondary.getRawClass()) ? secondary : primary` (or
     `secondary.findSuperType(primary.getRawClass()) != null ? secondary : primary`), or answers interface primaries itself with
     `primary.isInterface() && primary.getRawClass().isAssignableFrom(secondary.getRawClass()) ? secondary : <next hop>`, instead of
     leaving the decision to the gold: each is another implementation of the relation test, not a repair of the chain's plumbing.

Lie: the facade's javadoc claims the secondary type is first re-resolved through the type bindings of the primary type, so that the
result keeps the primary type's generic parameters; nothing in the chain resolves bindings (one of the two given objects is returned
as it is). It names neither interfaces, superclasses, the walk, nor any hop."""

TF = "src/main/java/com/fasterxml/jackson/databind/type/TypeFactory.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"

GOLD_TEXT = '''/**
 * Method for finding the more specific of two types: the second type
 * if its raw class is more specific than the raw class of the first
 * type, and the first type otherwise.
 *
 * @param first Primary type to consider, not null
 * @param second Secondary type to consider, not null
 *
 * @return The more specific of the two types
 */
public static JavaType narrowerTypeOf(JavaType first, JavaType second)
{
    final Class<?> target = first.getRawClass();
    final Class<?> start = second.getRawClass();
    if (start == target) { return first; }
    if (target.isInterface() && target.isAssignableFrom(start)) { return second; }
    for (Class<?> curr = start; curr != null; curr = curr.getSuperclass()) {
        if (curr == target) { return second; }
    }
    return first;
}'''

HOP1 = '''/**
 * Method for finding the more specific of two types.
 *
 * @param primary Primary type to consider, not null
 * @param secondary Secondary type to consider, not null
 *
 * @return The more specific of the two types
 */
public static JavaType specificTypeOf(JavaType primary, JavaType secondary)
{
    return BasicDeserializerFactory.refinedTypeOf(primary, secondary);
}'''

HOP2 = '''/**
 * Helper method for finding the more specific of two types.
 *
 * @param primary Primary type to consider, not null
 * @param secondary Secondary type to consider, not null
 *
 * @return The more specific of the two types
 */
public static JavaType refinedTypeOf(JavaType primary, JavaType secondary)
{
    return ObjectReader.specializedTypeOf(primary, secondary);
}'''

HOP3 = '''/**
 * Method for finding the more specific of two types.
 *
 * @param primary Primary type to consider, not null
 * @param secondary Secondary type to consider, not null
 *
 * @return The more specific of the two types
 */
public static JavaType specializedTypeOf(JavaType primary, JavaType secondary)
{
    return TokenBuffer.preferredTypeOf(primary, secondary);
}'''

HOP4 = '''/**
 * Helper method for finding the more specific of two types.
 *
 * @param primary Primary type to consider, not null
 * @param secondary Secondary type to consider, not null
 *
 * @return The more specific of the two types
 */
public static JavaType preferredTypeOf(JavaType primary, JavaType secondary)
{
    return BeanDeserializerBase.narrowerTypeOf(primary, secondary);
}'''

DESIGN = {
 "instance": "JacksonDatabind-95", "project": "JacksonDatabind", "bug_id": 95, "seed": 4635,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the facade's two parameters type1 and type2 (JavaType) to hop 1; the method is pure (no field read or written), "
                 "no write-back",
 "host_mode": "1500", "host_lines": [3936, 1964, 1913, 1917, 1669],
 "reachability_probe": "moreSpecificType first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonDatabind-95-probe: TestTypeFactory::testMoreSpecificType fails with PROBE-REACHED "
                       "at TypeFactory.moreSpecificType(TypeFactory.java:585) from TestTypeFactory.java:567; full suite with the "
                       "probe: 1 failing test (testMoreSpecificType only)",
 "facade": {"file": TF, "class": "com.fasterxml.jackson.databind.type.TypeFactory", "method": "moreSpecificType",
            "near_line": 583},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/type/TestTypeFactory.java",
             "test_class": "com.fasterxml.jackson.databind.type.TestTypeFactory", "test_method": "testMoreSpecificType"},
 "expected_signature": "expected same:<[collection type; class java.util.List",
 "gold": {"method": "narrowerTypeOf", "text": GOLD_TEXT,
          "fault": {"old": "        if (start == target) { return first; }\n"
                           "        if (target.isInterface() && target.isAssignableFrom(start)) { return second; }\n"
                           "        for (Class<?> curr = start;",
                    "new": "        if (start == target) { return first; }\n"
                           "        for (Class<?> curr = start;"}},
 "chain": {
   "facade_body": "if (type1 == null) {\n            return type2;\n        }\n"
                  "        if (type2 == null) {\n            return type1;\n        }\n"
                  "        return com.fasterxml.jackson.databind.ObjectMapper.specificTypeOf(type1, type2);",
   "lie": "The secondary type is first re-resolved through the type bindings of the primary type, so that the result keeps "
          "the generic parameters of the primary type.",
   "hops": [
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "specificTypeOf",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"], "text": HOP1},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "refinedTypeOf",
      "imports": ["com.fasterxml.jackson.databind.ObjectReader"], "text": HOP2},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "specializedTypeOf",
      "imports": ["com.fasterxml.jackson.databind.util.TokenBuffer"], "text": HOP3},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "preferredTypeOf",
      "imports": ["com.fasterxml.jackson.databind.deser.BeanDeserializerBase"], "text": HOP4},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "narrowerTypeOf",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.type.TypeBase::findSuperType",
              "com.fasterxml.jackson.databind.module.SimpleSerializers::findSerializer",
              "com.fasterxml.jackson.databind.util.ClassUtil::findRawSuperTypes"],
 "ownership_reason": "Only the gold decides which of the two types is more specific: hops 1-4 pass the two types along unchanged "
                     "and the facade only answers a null type. The gold's javadoc promises the second type when its raw class is "
                     "more specific than the first's; for (Collection<Object>, List<Object>) the variant gold searches only the "
                     "superclass chain of List (an interface, whose superclass is null), never meets Collection and returns the "
                     "Collection type, although List is the more specific. Once the gold has returned the first type, a caller can "
                     "obtain the List type only by deciding the relation itself or by replacing the gold. The convention that a "
                     "class is related to the interfaces it extends or implements is pinned outside the gold: the facade's own "
                     "javadoc ('if they are related; that is, one implements or extends the other'), TypeBase.findSuperType "
                     "(searches the super interfaces when the target is an interface, then the superclass), "
                     "SimpleSerializers.findSerializer (interface mappings serve implementing classes and their subclasses) and "
                     "ClassUtil.findRawSuperTypes (interfaces, then the superclass), with TestTypeFactory testMapEntryResolution "
                     "(findSuperType finds the interface Map.Entry of a class implementing it), TestSimpleModule "
                     "testSimpleInterfaceSerializer (the serializer registered for interface Base serves Impl1 and its subclass "
                     "Impl2) and TestTypeResolution testGeneric passing.",
 "ownership_tests": ["com.fasterxml.jackson.databind.type.TestTypeFactory::testMapEntryResolution",
                     "com.fasterxml.jackson.databind.module.TestSimpleModule::testSimpleInterfaceSerializer",
                     "com.fasterxml.jackson.databind.type.TestTypeResolution::testGeneric"],
 "compensating": {
   "chain": [
     {"file": TB, "old": "return BeanDeserializerBase.narrowerTypeOf(primary, secondary);",
      "new": "return BeanDeserializerBase.narrowerTypeOf(secondary, primary);",
      "why": "hop 4 passes the two types in the other order"},
     {"file": OM, "old": "return BasicDeserializerFactory.refinedTypeOf(primary, secondary);",
      "new": "return secondary.isInterface() ? primary : BasicDeserializerFactory.refinedTypeOf(primary, secondary);",
      "why": "hop 1 answers a secondary interface type with the primary type"},
     {"file": OR, "old": "return TokenBuffer.preferredTypeOf(primary, secondary);",
      "new": "return TokenBuffer.preferredTypeOf(primary, TypeFactory.defaultInstance().constructType(secondary.getRawClass()));",
      "why": "hop 3 passes the type of the secondary raw class"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts drawn by `mr_lib.py preview JacksonDatabind-95 com/fasterxml/jackson/databind/type/"
               "TypeFactory.java 5` with the instance seed 4635 (the facade's file excluded), used in draw order, none substituted: "
               "ObjectMapper (hop 1, 3936 lines), deser.BasicDeserializerFactory (hop 2, 1964), ObjectReader (hop 3, 1913), "
               "util.TokenBuffer (hop 4, 1917), deser.BeanDeserializerBase (hop 5, gold, 1669; the smallest host). All five are "
               "public top-level classes in which a public static method compiles (BasicDeserializerFactory and "
               "BeanDeserializerBase are abstract, which does not affect a static method). Anchors from "
               "stageB_lib.pick_anchor with seed 4635 + 100 + i as mr3_spec.py inserts them: hop 1 after readValue (line 2946, "
               "seed 4735), hop 2 after createReferenceDeserializer (1335, 4736), hop 3 after isEnabled (906, 4737), hop 4 after "
               "writeRawValue (776, 4738), hop 5 after isCachable (872, 4739). The facade calls hop 1 by its fully-qualified "
               "name; each hop imports the next host where its package differs; the gold uses only JavaType (already imported "
               "by BeanDeserializerBase through com.fasterxml.jackson.databind.*) and java.lang.Class. The facade's class "
               "TypeFactory is not a host.",
}
