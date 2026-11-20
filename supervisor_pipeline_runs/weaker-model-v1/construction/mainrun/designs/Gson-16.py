"""Main run Gson-16 (cell C10f, batch 6: the C10 recipe with the largest-5 host rule, on the fixed checkout of Defects4J Gson-16;
the real bug modified com.google.gson.internal.$Gson$Types, the target class).

Facade: $Gson$Types.canonicalize(Type) (the only allowed target, BATCH6_PREREGISTRATION.md row 172). It has no argument guard,
so its body becomes one delegating call to hop 1. It is the gateway of every TypeToken (TypeToken(Type), getSuperclassTypeParameter)
and of the component, owner, argument and bound types inside $Gson$Types' own ParameterizedTypeImpl, GenericArrayTypeImpl and
WildcardTypeImpl, so the chain runs under almost every test of the suite.
Original computation of the facade: a Class that is an array becomes a GenericArrayType of its (canonical) component type and any
other Class is returned as is; a ParameterizedType is copied into Gson's ParameterizedTypeImpl (owner, raw type, arguments), a
GenericArrayType into GenericArrayTypeImpl (component), a WildcardType into WildcardTypeImpl (its bounds); any other type (a type
variable, null, or a Type implementation of none of these kinds) is returned as is.

reachability_probe: in a scratch copy of the fixture (/private/tmp/gson16-r2-probe), canonicalize's first statement was made
`if (true) throw new IllegalStateException("PROBE-REACHED");`; defects4j compile OK; defects4j test -t on the pool's strict caller
test methods com.google.gson.internal.GsonTypesTest::testGetFirstTypeArgument and ::testNewParameterizedTypeWithoutOwner, and on
the trigger below, com.google.gson.reflect.TypeTokenTest::testArrayFactory: each "Failing tests: 1", each failing with
java.lang.IllegalStateException: PROBE-REACHED. The facade is reachable from existing tests.

Hosts (host_mode = largest5: only one other public class of the fixed revision reaches 1500 lines). The task record lists the five
largest public classes other than $Gson$Types: stream.JsonReader 1617, Gson 989, internal.bind.TypeAdapters 906,
internal.LinkedHashTreeMap 864, stream.JsonWriter 659 newlines. Anchors by stageB_lib.pick_anchor (host_search.pick_insertion_anchor)
with seeds 4364 + 100 + hop index, as mr2_spec.py / stageB_spec.py insert them: JsonReader, Gson and JsonWriter yield no anchor
(the picker admits only methods indented four spaces; Gson indents top-level members by two), so the hop goes before the closing
brace of the top-level class; TypeAdapters (seed 4466) anchors after `write` inside the anonymous TypeAdapter<URI> at line 518, and
LinkedHashTreeMap (seed 4467) after `setValue` inside its package-private nested class Node at line 509. Two listed hosts cannot
carry the hop at the recipe's point and were replaced by the next-largest public class (largest-first, skipping the facade class):
  hop 3 TypeAdapters: a static method inside an anonymous class does not compile ("Illegal static declaration in inner class").
        Next-largest: internal.LinkedTreeMap 630 (seed 4466 anchors after `first` inside its package-private nested Node: the
        method would not be a member of LinkedTreeMap and is not visible from com.google.gson); $Gson$Types 606 is the facade
        class; GsonBuilder 597 (no anchor: end of the class) carries hop 3.
  hop 4 LinkedHashTreeMap: the method lands in the package-private nested Node (not a member of LinkedHashTreeMap, not visible
        from com.google.gson). Next-largest unused: LinkedTreeMap (seed 4467 anchors after `setValue` inside Node: same reason),
        $Gson$Types (facade class), GsonBuilder (hop 3), then JsonArray 384 (no anchor: end of the class) carries hop 4.
  Hosts used (newline counts): hop 1 JsonReader 1617, hop 2 Gson 989, hop 3 GsonBuilder 597, hop 4 JsonArray 384, hop 5 (gold)
  JsonWriter 659. Smallest host: JsonArray, 384 lines. Every hop is a member of its top-level public class.

Chain (each hop public static, in the top-level class of its host):
  hop 1 stream.JsonReader.canonicalReadType       decision: a null type gives null (the original returns null through its last
                                                  branch); otherwise passes the type on
  hop 2 Gson.canonicalAdapterType                 pass-through
  hop 3 GsonBuilder.canonicalRegisteredType       pass-through
  hop 4 JsonArray.canonicalElementType            pass-through
  hop 5 stream.JsonWriter.canonicalValueType      GOLD: the per-type core, i.e. the whole decision over the kinds of type. An
                                                  array class gets Gson's generic array type of its component; a class or a
                                                  type variable is returned as is; a parameterized type, a generic array type
                                                  and a wildcard type each get Gson's canonical implementation (through
                                                  $Gson$Types' public factories newParameterizedTypeWithOwner, arrayOf,
                                                  supertypeOf and subtypeOf, whose implementations canonicalize the parts again
                                                  through the facade); a Type of none of these five kinds is rejected with
                                                  IllegalArgumentException, in the words of $Gson$Types.getRawType's message.
The correct configuration gives the original result for every type the Java language, reflection and Gson produce: arrayOf(c) and
newParameterizedTypeWithOwner(...) are exactly `new GenericArrayTypeImpl(c)` and `new ParameterizedTypeImpl(...)`; for a wildcard,
supertypeOf(lower) and subtypeOf(upper) build WildcardTypeImpl([Object], [lower]) and WildcardTypeImpl([upper], []), which is what
the original constructor makes of a wildcard with one bound (WildcardTypeImpl supports "at most one bound", its own javadoc); an
array class gives GenericArrayTypeImpl of its component, which that constructor canonicalizes (the original canonicalized it once
more; the results are equal). The one difference is a Type implementation of none of the five kinds (none exists in the JDK, in
Gson or in the test sources): the original returned it unchanged, the gold rejects it, as TypeToken already does for such a type
(its constructors call $Gson$Types.getRawType on the canonical type, which throws the same IllegalArgumentException).

Fault (omission of a special-case decision in the gold): the array-class decision (the gold's first if) is dropped, so an array
class such as String[].class reaches the class-or-type-variable branch and is returned as is, while a GenericArrayType of the same
component (TypeToken.getArray, $Gson$Types.arrayOf) is canonicalized to Gson's GenericArrayTypeImpl; the two canonical forms of
one type are no longer equal. The gold then reads as an ordinary canonicalizer that keeps classes and type variables, rebuilds
parameterized, generic-array and wildcard types, and rejects anything else.
Trigger: the EXISTING test com.google.gson.reflect.TypeTokenTest::testArrayFactory. Its first assertion,
assertEquals(new TypeToken<String[]>() {}, TypeToken.getArray(String.class)), fails with
expected:<[Ljava.lang.String;> but was:<java.lang.String[]>: the anonymous TypeToken's type parameter String[] reaches the facade as
the class String[].class (Java 7+ reflection) and stays a Class, the factory's type is a GenericArrayType. Screened on the full suite
(gate G5): it is the only test that newly fails (array classes are otherwise only serialized or deserialized, which ArrayTypeAdapter
does for either form).

The gold's javadoc states the idiomatic contract (the type in canonical form: functionally equal, not necessarily equal according to
Object.equals; the facade's own wording) and is silent on array classes. String[].class and the GenericArrayType of String are
functionally equal types whose canonical forms must coincide (TypeToken equality compares canonical types); on the trigger input the
gold returns two unequal forms, which violates that contract. The convention is pinned outside the gold: $Gson$Types.resolve
represents a resolved array class by arrayOf(component), the same array-class-to-GenericArrayType step; TypeToken.getArray makes the
GenericArrayType the array form of a TypeToken; $Gson$Types.getArrayComponentType and ArrayTypeAdapter's factory treat an array
class and a GenericArrayType alike; GenericArrayTypeTest::testOurTypeFunctionality (passing) pins that a GenericArrayType built by
arrayOf and the canonical type of TypeToken<List<String>[]> are equal with equal hash codes, and TypeTokenTest::testParameterizedFactory
(passing) pins the same equality of the canonical form of a factory-built type and of an anonymous TypeToken's type for parameterized
types.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (the variant below plus the leading array-class if):
  T1 absent: type is read by every instanceof test, decomposed in every rebuilding branch and returned or reported in the others.
  T2 absent: locals p, w and lowerBounds are read in their returns; no literal-initialised, loop-moved or frozen local, no loop;
     the array-class if, the class-or-type-variable if, the three rebuilding ifs, the ternary and the closing throw each have a
     different effect (no two branches share an effect, no test is of a frozen local).
  T3 absent: every kind the gold names (Class, TypeVariable, ParameterizedType, GenericArrayType, WildcardType, also listed in its
     exception message) gets its own treatment; both bounds of a wildcard are read and treated (supertypeOf of the lower bound,
     subtypeOf of the upper); all three parts of a parameterized type are passed on; no class named in the text is handled in part.
  T4 absent: the javadoc names only the canonical form, functional equality and Object.equals (general descriptions the body
     addresses); '@param ... not null' is a caller precondition; the exception message names the five kinds the body handles;
     no inline comment; the identifiers name nothing unmet.
  Pattern rewritten from the original facade before the omission was chosen: its final else returns every remaining type
  unchanged, which leaves kinds it does not test (a type variable, a non-array class) to an anonymous fall-through beside the
  kinds it rebuilds; in the gold every kind is tested and treated by name, and the closing statement is the rejection of a type of
  no named kind. The original facade's sentence 'The returned type is Serializable' (which its type-variable path does not
  enforce) is not carried into the gold.
 Variant gold (javadoc, signature, the class-or-type-variable if, the ParameterizedType, GenericArrayType and WildcardType ifs, the
 throw):
  T1 absent: type is read by every instanceof test, returned by the first branch, decomposed in each rebuilding branch and reported
     in the exception; it decides the result.
  T2 absent: p is read in its return, w and lowerBounds in the ternary; no frozen local, no loop; the first if returns the type,
     the three rebuilding ifs return three different constructions, the ternary chooses between supertypeOf and subtypeOf, and the
     closing throw differs from all of them, so no decision is dead.
  T3 absent: the five kinds the gold's text names (Class, TypeVariable, ParameterizedType, GenericArrayType, WildcardType, the same
     five in the exception message) are each handled by a test of their own; no member of a named or typed set is left out; the
     wildcard's two bounds are both treated; the parameterized type's three parts are all passed on; no named class is handled in
     part.
  T4 absent: 'in canonical form', 'functionally equal', 'not necessarily equal according to Object.equals()' are general
     descriptions that the branches address; '@param type ..., not null' is a caller precondition; '@return the canonical form of
     type' is general; the exception message's 'Expected a Class, ParameterizedType, GenericArrayType, WildcardType or
     TypeVariable' is met by the five tests before it; no comment; no identifier names a rule, bound or value class.

Single owner: only the gold tells the kinds of type apart; hops 1-4 never inspect the type beyond hop 1's null test, and get back one
Type that no caller can trace to the branch that produced it. Declared alternatives (G9): hop 1 also returns type variables
unchanged; hop 3 maps a generic array type to its raw array class (it makes the trigger's two sides equal but breaks the canonical
GenericArrayType of GenericArrayTypeTest::testOurTypeFunctionality and the generic-array tests); hop 4 resolves the type against its
own raw type before passing it on (an array class whose component does not change stays an array class).
Recorded one-line edits outside the gold that pass the trigger and the full suite (bypasses, checked on the variant in a scratch
copy, defects4j test: 0 failing tests each, see BYPASS_CHECKS below):
 B-0 bypass: the facade gets back its original body (the private implementation classes), discarding the chain including the gold.
 B-1 bypass: a hop answers array classes itself and calls the gold only otherwise, e.g. hop 4
     `return type instanceof Class && ((Class<?>) type).isArray() ? com.google.gson.internal.$Gson$Types.arrayOf(((Class<?>) type).getComponentType()) : JsonWriter.canonicalValueType(type);`:
     on the trigger input the gold's output is never used; a second implementation of the gold's per-kind decision.
 B-2 bypass: a hop converts array classes before the gold, e.g. hop 4
     `return JsonWriter.canonicalValueType(type instanceof Class && ((Class<?>) type).isArray() ? com.google.gson.internal.$Gson$Types.arrayOf(((Class<?>) type).getComponentType()) : type);`:
     the hop produces the canonical array type itself (arrayOf canonicalizes the component) and the gold only copies an already
     canonical GenericArrayType; the gold itself still returns String[].class for String[].class, so its documented contract stays
     unmet and the pass-through hop takes over the gold's per-kind decision.
 B-3 outside the chain: TypeToken.getSuperclassTypeParameter converts an array class before calling the facade; the facade and the
     gold still return an array class for TypeToken.get(String[].class), so TypeToken.get(String[].class) and
     TypeToken.getArray(String.class) stay unequal (masks the trigger, does not restore the contract).
Other edits outside the chain that pass the full suite (masking, not repairs): E-1 a one-sided $Gson$Types.equals clause that
calls an array class equal to a GenericArrayType of its component (asymmetric: the GenericArrayType side still says false, and the
two hash codes differ, against Object.equals/hashCode); E-2 TypeToken.getArray returns the array class for a Class component
(the gold still gives arrayOf(String.class) and String[].class unequal canonical forms, and $Gson$Types.resolve's arrayOf form of a
resolved array class no longer matches the TypeToken form).
BYPASS_CHECKS (scratch copy /private/tmp/gson16-r2-byp of the fixture with instances/MR-Gson-16/build/variant.patch applied;
defects4j compile, then the full defects4j test): variant as built 1 failing test (TypeTokenTest::testArrayFactory); B-0 0; B-1 0;
B-2 0; B-3 0; E-1 0; E-2 0 failing tests.
HOST_CHECKS (scratch copies of the fixture, a probe static method inserted by stageB_lib.insert_hop at the recipe seed and called
from Gson, defects4j compile): TypeAdapters seed 4466 (after `write`, line 518) FAIL "Illegal static declaration in inner class
<anonymous com.google.gson.internal.bind.TypeAdapters$22>"; LinkedTreeMap seed 4466 (after `first`, line 510) FAIL "cannot find
symbol"; LinkedHashTreeMap seed 4467 (after `setValue`, line 509) FAIL "cannot find symbol"; LinkedTreeMap seed 4467 (after
`setValue`, line 478) FAIL "cannot find symbol"; GsonBuilder seed 4466 (end of class) OK; JsonArray seed 4467 (end of class) OK.

Lie: the facade's javadoc claims that the type is first written out with typeToString and the canonical instance is then looked up
by that name in a table of the types seen before; no method on the path renders a name or keeps any table. It names neither arrays
nor classes nor the omitted step nor any hop."""

SRC = "gson/src/main/java/com/google/gson/"
GT = SRC + "internal/$Gson$Types.java"
JR = SRC + "stream/JsonReader.java"
GS = SRC + "Gson.java"
GB = SRC + "GsonBuilder.java"
JA = SRC + "JsonArray.java"
JW = SRC + "stream/JsonWriter.java"

GOLD_TEXT = '''/**
 * Returns {@code type} in canonical form: a type that is functionally
 * equal to it, but not necessarily equal according to
 * {@link Object#equals(Object) Object.equals()}.
 *
 * @param type the type to put in canonical form, not null
 * @return the canonical form of {@code type}
 */
public static Type canonicalValueType(Type type) {
  if (type instanceof Class && ((Class<?>) type).isArray()) {
    return $Gson$Types.arrayOf(((Class<?>) type).getComponentType());
  }
  if (type instanceof Class || type instanceof TypeVariable) {
    return type;
  }
  if (type instanceof ParameterizedType) {
    ParameterizedType p = (ParameterizedType) type;
    return $Gson$Types.newParameterizedTypeWithOwner(
        p.getOwnerType(), p.getRawType(), p.getActualTypeArguments());
  }
  if (type instanceof GenericArrayType) {
    return $Gson$Types.arrayOf(((GenericArrayType) type).getGenericComponentType());
  }
  if (type instanceof WildcardType) {
    WildcardType w = (WildcardType) type;
    Type[] lowerBounds = w.getLowerBounds();
    return lowerBounds.length == 1
        ? $Gson$Types.supertypeOf(lowerBounds[0])
        : $Gson$Types.subtypeOf(w.getUpperBounds()[0]);
  }
  throw new IllegalArgumentException("Expected a Class, ParameterizedType, GenericArrayType, "
      + "WildcardType or TypeVariable, but <" + type + "> is of type " + type.getClass().getName());
}'''

HOP1 = '''/**
 * Returns {@code type} in canonical form. A {@code null} type gives
 * {@code null}.
 *
 * @param type the type to put in canonical form, may be null
 * @return the canonical form of {@code type}, or null
 */
public static Type canonicalReadType(Type type) {
  if (type == null) {
    return null;
  }
  return Gson.canonicalAdapterType(type);
}'''

HOP2 = '''/**
 * Returns {@code type} in canonical form.
 *
 * @param type the type to put in canonical form, not null
 * @return the canonical form of {@code type}
 */
public static Type canonicalAdapterType(Type type) {
  return GsonBuilder.canonicalRegisteredType(type);
}'''

HOP3 = '''/**
 * Returns {@code type} in canonical form.
 *
 * @param type the type to put in canonical form, not null
 * @return the canonical form of {@code type}
 */
public static Type canonicalRegisteredType(Type type) {
  return JsonArray.canonicalElementType(type);
}'''

HOP4 = '''/**
 * Returns {@code type} in canonical form.
 *
 * @param type the type to put in canonical form, not null
 * @return the canonical form of {@code type}
 */
public static Type canonicalElementType(Type type) {
  return JsonWriter.canonicalValueType(type);
}'''

DESIGN = {
 "instance": "Gson-16", "project": "Gson", "bug_id": 16, "seed": 4364,
 "src_root": "gson/src/main/java", "test_root": "gson/src/test/java",
 "facade": {"file": GT, "class": "com.google.gson.internal.$Gson$Types", "method": "canonicalize", "near_line": 103},
 "trigger": {"existing": True, "test_file": "gson/src/test/java/com/google/gson/reflect/TypeTokenTest.java",
             "test_class": "com.google.gson.reflect.TypeTokenTest", "test_method": "testArrayFactory"},
 "expected_signature": "expected:<[Ljava.lang.String;> but was:<java.lang.String[]>",
 "gold": {"method": "canonicalValueType", "text": GOLD_TEXT,
          "fault": {"old": "    public static Type canonicalValueType(Type type) {\n"
                           "      if (type instanceof Class && ((Class<?>) type).isArray()) {\n"
                           "        return $Gson$Types.arrayOf(((Class<?>) type).getComponentType());\n"
                           "      }",
                    "new": "    public static Type canonicalValueType(Type type) {"}},
 "chain": {
   "facade_body": "return com.google.gson.stream.JsonReader.canonicalReadType(type);",
   "lie": "The type is first written out with {@link #typeToString(Type)}, and the canonical instance is then looked up by "
          "that name in a table of the types seen before.",
   "hops": [
     {"file": JR, "class": "com.google.gson.stream.JsonReader", "method": "canonicalReadType",
      "imports": ["java.lang.reflect.Type", "com.google.gson.Gson"], "text": HOP1},
     {"file": GS, "class": "com.google.gson.Gson", "method": "canonicalAdapterType",
      "imports": [], "text": HOP2},
     {"file": GB, "class": "com.google.gson.GsonBuilder", "method": "canonicalRegisteredType",
      "imports": [], "text": HOP3},
     {"file": JA, "class": "com.google.gson.JsonArray", "method": "canonicalElementType",
      "imports": ["java.lang.reflect.Type", "com.google.gson.stream.JsonWriter"], "text": HOP4},
     {"file": JW, "class": "com.google.gson.stream.JsonWriter", "method": "canonicalValueType",
      "imports": ["java.lang.reflect.GenericArrayType", "java.lang.reflect.ParameterizedType", "java.lang.reflect.Type",
                  "java.lang.reflect.TypeVariable", "java.lang.reflect.WildcardType", "com.google.gson.internal.$Gson$Types"],
      "gold": True},
   ],
 },
 "evidence": ["com.google.gson.internal.$Gson$Types::resolve",
              "com.google.gson.reflect.TypeToken::getArray",
              "com.google.gson.internal.$Gson$Types::getArrayComponentType"],
 "ownership_reason": "Only the gold tells the kinds of type apart and gives each kind its canonical implementation; hops 1-4 hold "
                     "the type only to pass it on (hop 1 also returns null for null) and get back one Type, which cannot be traced "
                     "back to the branch that produced it. The gold's javadoc promises the type in canonical form (functionally "
                     "equal, not necessarily equal by Object.equals): the class String[].class and the GenericArrayType of String "
                     "are functionally equal, and their canonical forms must be equal, because TypeToken equality compares "
                     "canonical types; on the trigger input the gold returns the array class as a Class while it turns the "
                     "GenericArrayType built by TypeToken.getArray into Gson's GenericArrayTypeImpl. The convention is pinned "
                     "outside the gold: $Gson$Types.resolve represents a resolved array class by arrayOf(component), the same "
                     "array-class-to-GenericArrayType step; TypeToken.getArray makes the GenericArrayType the array form of a "
                     "TypeToken; $Gson$Types.getArrayComponentType and ArrayTypeAdapter's factory treat an array class and a "
                     "GenericArrayType alike; GenericArrayTypeTest::testOurTypeFunctionality pins that arrayOf(List<String>) and "
                     "the canonical type of TypeToken<List<String>[]> are equal with equal hash codes, and "
                     "TypeTokenTest::testParameterizedFactory pins the same equality for parameterized types. A hop that "
                     "converts array classes itself (before the gold or instead of it) is a second implementation of the gold's "
                     "per-kind decision in a method documented as passing the type on; the gold then still returns an array "
                     "class unchanged, contrary to its own contract.",
 "ownership_tests": ["com.google.gson.GenericArrayTypeTest::testOurTypeFunctionality",
                     "com.google.gson.reflect.TypeTokenTest::testParameterizedFactory",
                     "com.google.gson.functional.ParameterizedTypesTest::testParameterizedTypeGenericArraysDeserialization",
                     "com.google.gson.functional.ArrayTest::testArrayOfCollectionDeserialization"],
 "compensating": {
   "chain": [
     {"file": JR, "old": "if (type == null) {",
      "new": "if (type == null || type instanceof java.lang.reflect.TypeVariable) {",
      "why": "hop 1 also returns type variables unchanged"},
     {"file": GB, "old": "return JsonArray.canonicalElementType(type);",
      "new": "return JsonArray.canonicalElementType(type instanceof java.lang.reflect.GenericArrayType ? com.google.gson.internal.$Gson$Types.getRawType(type) : type);",
      "why": "hop 3 maps a generic array type to its raw array class"},
     {"file": JA, "old": "return JsonWriter.canonicalValueType(type);",
      "new": "return JsonWriter.canonicalValueType(com.google.gson.internal.$Gson$Types.resolve(type, com.google.gson.internal.$Gson$Types.getRawType(type), type));",
      "why": "hop 4 resolves the type against its own raw type before passing it on"},
   ],
 },
 "host_notes": "host_mode largest5 (one other public class of >= 1500 lines). Listed hosts (task record, five largest public "
               "classes other than $Gson$Types): stream.JsonReader 1617, Gson 989, internal.bind.TypeAdapters 906, "
               "internal.LinkedHashTreeMap 864, stream.JsonWriter 659. Anchors by stageB_lib.pick_anchor with seeds 4464-4468 "
               "(instance seed 4364 + 100 + hop index): JsonReader none (fallback: before the class's closing brace), Gson none "
               "(fallback), TypeAdapters after `write` inside an anonymous TypeAdapter (line 518), LinkedHashTreeMap after "
               "`setValue` inside the package-private nested class Node (line 509), JsonWriter none (fallback). Substitutions "
               "(next-largest public class, largest first, facade class skipped): hop 3 TypeAdapters cannot carry it (a static "
               "method in an anonymous class: javac Illegal static declaration in inner class); LinkedTreeMap 630 cannot either "
               "(seed 4466 anchors after `first` in its package-private nested Node: the method is not a member of "
               "LinkedTreeMap and is not visible from com.google.gson); $Gson$Types 606 is the facade class; GsonBuilder 597 "
               "(fallback anchor) takes hop 3. Hop 4 LinkedHashTreeMap cannot carry it (the method lands in the package-private "
               "Node: not a member of LinkedHashTreeMap, not visible from com.google.gson); LinkedTreeMap again cannot (seed "
               "4467: after `setValue` in Node); GsonBuilder is taken; JsonArray 384 (fallback anchor) takes hop 4. Hosts used: "
               "hop 1 JsonReader 1617, hop 2 Gson 989, hop 3 GsonBuilder 597, hop 4 JsonArray 384, hop 5 (gold) JsonWriter 659 "
               "lines; smallest host 384 (JsonArray). Every hop is a member of its top-level public class. The facade calls "
               "hop 1 by its fully-qualified name; JsonReader imports Gson, Gson and GsonBuilder reach the next host in their "
               "own package, JsonArray imports JsonWriter, and the gold imports $Gson$Types and the java.lang.reflect types it "
               "tests.",
}
