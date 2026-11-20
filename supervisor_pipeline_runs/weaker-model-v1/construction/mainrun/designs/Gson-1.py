"""Main run Gson-1 (C10f recipe, batch 6, on the fixed checkout of Defects4J Gson-1; the real bug modified TypeInfoFactory, the
target class).

Facade: TypeInfoFactory.getTypeInfoForField(Field, Type) (the only allowed target, BATCH6_PREREGISTRATION.md row 170). Its
production caller is ObjectNavigator.navigateClassFields, which evaluates every field of the navigated object and of each of its
superclasses with the type of the navigated object (objTypePair.type); its test caller is TypeInfoFactoryTest (17 methods).
Original computation: the raw class of the defining type, the field's generic type, then the private recursive getActualType:
a Class is kept; a ParameterizedType is rebuilt with every type argument evaluated; a GenericArrayType keeps itself when its
component does not change, else becomes the array class of a Class component or a new GenericArrayTypeImpl; a WildcardType is
evaluated through its first upper bound; a TypeVariable takes the type argument at its position when the defining type is a
ParameterizedType, and otherwise the type assigned through the superclass hierarchy (private extractTypeForHierarchy), with an
UnsupportedOperationException when none is found; the result is wrapped in a TypeInfo.

reachability_probe: in a scratch copy of the fixture the facade's first statement was made
`if (true) throw new IllegalStateException("PROBE-REACHED");`; defects4j test -t TypeInfoFactoryTest::testSimpleField,
::testTypeVariableField and ::testWildcardField each failed with java.lang.IllegalStateException: PROBE-REACHED at
TypeInfoFactory.getTypeInfoForField; the full suite then had 194 failing tests (baseline 0 of 720), 190 of them with the probe
message (the facade is on every reflective serialization path). REACHED.

Branch screen (scratch copy, one throw per branch of the original getActualType, full suite each): Class 176 tests,
ParameterizedType 38, GenericArrayType 14, TypeVariable with a ParameterizedType parent 21, WildcardType 16, TypeVariable through
the superclass hierarchy exactly ONE (functional.TypeVariableTest::testSingle, the real Gson-1 trigger), deeper hierarchy levels 0,
the UnsupportedOperationException 0. The fault is therefore placed in the hierarchy step.

host_mode: largest5 (no other public class of the fixed revision reaches 1500 lines). Hosts are the five largest public classes
other than TypeInfoFactory, in hop order: stream.JsonReader 1118 lines (hop 1), GsonBuilder 570 (hop 2), Gson 566 (hop 3),
stream.JsonWriter 553 (hop 4), JsonPrimitive 387 (hop 5, gold); smallest host 387 lines (the gold host). None substituted.

Chain (instance seed 4989; anchors stageB_lib.pick_anchor with seeds 5089..5093 all return None, see host_notes):
  hop 1 stream.JsonReader.typeOfField     placement: the field's generic type
  hop 2 GsonBuilder.fieldTypeIn           plumbing: the raw class of the parent type (TypeUtils.toRawClass)
  hop 3 Gson.actualTypeOf                 fold over the structure of the field type (recursive): a Class is kept, a
                                          ParameterizedType rebuilt from its evaluated arguments, a GenericArrayType from its
                                          evaluated component, a WildcardType replaced by its evaluated upper bound; every type
                                          variable is handed to hop 4
  hop 4 stream.JsonWriter.typeOfVariable  pass-through
  hop 5 JsonPrimitive.typeAssignedTo      GOLD: the per-variable core, the type that the parent type assigns to one type variable:
                                          climb from the parent type to the class that declares the variable (generic superclass
                                          and raw superclass together), then take the argument at the variable's position
The facade keeps no guard (the original had none) and returns new TypeInfo(<hop 1>): the stream-package hops cannot see the
package-private TypeInfo. A behaviour-preserving pre-edit removes the facade class's private helpers (getActualType,
extractTypeForHierarchy, extractRealTypes, getIndex) and their imports: once the facade delegates to the chain they are
unreachable, and the redistributed computation should not stay behind as an unused copy next to the facade.
The correct configuration returns the original result on every input that the original resolves (same case order, the same
array and wildcard rules, the same argument at the same position; the climb is the iterative form of extractTypeForHierarchy,
taking at the declaring level that level's own arguments). It differs only where the original fails: a variable that no level
assigns comes back unchanged (the TypeInfo construction in the facade then rejects it with TypeUtils' IllegalArgumentException
instead of the original UnsupportedOperationException; no test reaches either), and a ParameterizedType parent whose raw class
does not declare the variable is climbed instead of failing in getIndex.

Fault (omission of the climb, an iteration of the gold): the while loop that moves parentType and rawParentClass up to the class
that declares the variable is dropped, so the gold reads the variable against the parent type alone. The gold then reads as the
textbook lookup (a parameterized parent type, its class's type parameters, the argument at the matching position, else the
variable itself), which is what the real Gson-1 fix had to extend. Trigger: the EXISTING test
functional.TypeVariableTest::testSingle (Bar extends Foo<String, Integer>; Foo declares the fields S someSField, T someTField and
Map<S, List<T>> map; gson.toJson(bar1) navigates Foo's fields with Bar.class): S comes back unresolved and
new TypeInfo(S) in the facade fails with java.lang.IllegalArgumentException: Type 'S' is not a Class, ParameterizedType, or
GenericArrayType. Can't extract class. No other test reaches the climb (branch screen above); every direct case
(ObjectWithDifferentFields<Integer>, the ParameterizedTypesTest types) is unchanged because the parent type itself declares the
variable.

The gold's javadoc states the idiomatic contract (the type that a parent type assigns to a type variable used in the declaration
of one of its fields; @param parentType the type of the object that contains the field) and is silent on superclasses. Bar
contains the field map (inherited) and assigns String to S through its superclass Foo<String, Integer>, so the variant violates
that contract on the trigger input. Pins outside the gold: ObjectNavigator.navigateClassFields passes the navigated object's type
for the fields of every superclass (so the parent type is the object's type, not the declaring class);
TypeToken.getSuperclassTypeParameter reads the argument that a raw subclass assigns through its generic superclass (the TypeToken
idiom that every TypeToken-based test relies on); TypeToken.isAssignableFrom(Type, ParameterizedType, Map) walks the whole generic
superclass chain mapping each class's type parameters to the arguments assigned below it. Passing tests: TypeInfoFactoryTest
testTypeVariableField and testListTypeVariableWildcardField, ParameterizedTypesTest testTypesWithMultipleParametersDeserialization
(position > 0), InheritanceTest testSubClassSerialization (superclass fields evaluated with the subclass type).

Single owner: only the gold sees one type variable together with the hierarchy of the parent type; hop 3 only rebuilds the
structure around the variables and hop 4 passes them through; hops 1 and 2 never see a variable. Declared alternatives (G9):
hop 1 evaluates the field against its declaring class (Foo.class, raw: S stays unassigned); hop 3 replaces each type variable by
its first bound (Object: the round trip no longer gives an equal Bar); hop 4 passes the generic superclass with the unchanged raw
class (Foo<String, Integer> is looked up among Bar's type parameters, which are empty). Each still fails the trigger (checked on
the variant in a scratch copy; hop 2 passing the raw superclass as the raw class fails it too).
Recorded one-line edits above the gold that pass the trigger and the full suite (each checked on the variant in a scratch copy,
defects4j test: 0 failing tests):
 B-0 bypass: hop 4 answers a raw parent class itself, `return parentType instanceof ParameterizedType ? JsonPrimitive.typeAssignedTo(
     variable, parentType, rawParentClass) : ((ParameterizedType) rawParentClass.getGenericSuperclass()).getActualTypeArguments()[
     java.util.Arrays.asList(rawParentClass.getSuperclass().getTypeParameters()).indexOf(variable)];`, a second implementation
     that makes the gold's output dead on the trigger path.
 B-1 test-fitted filter: a hop climbs ONE level itself before the gold, at hop 4
     `return parentType instanceof ParameterizedType ? JsonPrimitive.typeAssignedTo(variable, parentType, rawParentClass)
     : JsonPrimitive.typeAssignedTo(variable, rawParentClass.getGenericSuperclass(), rawParentClass.getSuperclass());`,
     or the same substitution of a raw parent class by its generic superclass at hop 1 or hop 2 (both checked). It passes the
     suite because the only hierarchy in the tests has one level, but it hands the gold a parent type that is not the type of the
     object that contains the field (the documented parameter of hops 1-4 and of the gold, and what ObjectNavigator passes for
     superclass fields), and a variable assigned two levels up stays unassigned. Checked with a scratch-only test (never part of
     the instance: class Baz extends TypeVariableTest.Bar, toJson then fromJson as Baz.class, assertEquals): it passes on the
     fixed revision and on the correct chain, and fails with the same IllegalArgumentException on the variant with B-1 at hop 1,
     hop 2 or hop 4, so hop 4's own contract (the type the parent type assigns) is still violated. The correct gold, like the
     original extractTypeForHierarchy and TypeToken.isAssignableFrom, climbs any number of levels. Not consistent with the path
     or the evidence.

Lie: the facade's javadoc claims that the field's generic signature is read as a string, every type variable name in it is
replaced by the name of the matching actual type, and the edited signature is parsed back into a type; the chain handles no
signature string and parses nothing. It names neither superclasses nor the hierarchy nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: variable is read in the loop condition, the equals test and the fallback return; parentType and rawParentClass in the
     loop, the instanceof test, getActualTypeArguments and getTypeParameters.
  T2 absent: the loop moves both parentType and rawParentClass; variables and arguments reach the return; i is advanced by the for
     header; each if has two different effects.
  T3 absent: the climb treats both halves of a level (getGenericSuperclass and getSuperclass); the lookup reads both the type
     parameters and the arguments; no set has a treated and an untreated member.
  T4 absent: the javadoc names the type assigned to a type variable and the variable itself when none is assigned (both returned
     by the body); the @param clauses are caller descriptions.
 Variant gold (javadoc, signature, `if (parentType instanceof ParameterizedType) { variables, arguments, for ... if
 (variables[i].equals(variable)) return arguments[i]; } return variable;`):
  T1 absent: variable is read by equals and returned; parentType by the instanceof test and the cast; rawParentClass by
     getTypeParameters; each changes the result. No argument check.
  T2 absent: variables and arguments reach the return; i is advanced by its for header; no literal-initialised local, no flag, no
     best-so-far; the if on the parent type and the equals test each decide between two different returns.
  T3 absent: the only kind test is ParameterizedType for the parent type (exactly one member of the unnamed set of Type kinds,
     no class named); the type parameters and the arguments are both read; no pair half, range end or named class is handled in
     part.
  T4 absent: 'the actual type that a parent type assigns to a type variable used in the declaration of one of its fields' is a
     general description the lookup addresses; '@return the type assigned to variable, or variable itself if the parent type
     assigns none' is met by `return arguments[i]` and `return variable`; the @param clauses are caller descriptions; no rule,
     bound, value class or property is named; no inline comment; identifiers (variables, arguments) name nothing the body does
     not meet."""
import os

SRC = "gson/src/main/java/com/google/gson/"
TIF = SRC + "TypeInfoFactory.java"
JR = SRC + "stream/JsonReader.java"
GB = SRC + "GsonBuilder.java"
GS = SRC + "Gson.java"
JW = SRC + "stream/JsonWriter.java"
JP = SRC + "JsonPrimitive.java"

_FIXTURE_TIF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fresh-mr", "Gson-1", TIF)
_T = open(_FIXTURE_TIF).read()
HELPERS_OLD = _T[_T.index("\n\n  private static Type getActualType("):_T.rindex("}")]
assert HELPERS_OLD.endswith('"How can the type variable not be present in the class declaration!");\n  }\n'), HELPERS_OLD[-80:]
IMPORTS_OLD = ("import java.lang.reflect.Field;\nimport java.lang.reflect.GenericArrayType;\nimport java.lang.reflect.ParameterizedType;\n"
               "import java.lang.reflect.Type;\nimport java.lang.reflect.TypeVariable;\nimport java.lang.reflect.WildcardType;\n")
assert IMPORTS_OLD in _T

GOLD_TEXT = '''/**
 * Returns the actual type that a parent type assigns to a type variable
 * used in the declaration of one of its fields.
 *
 * @param variable the type variable to evaluate
 * @param parentType the type of the object that contains the field
 * @param rawParentClass the raw class of {@code parentType}
 * @return the type assigned to {@code variable}, or {@code variable} itself
 *     if the parent type assigns none
 */
public static Type typeAssignedTo(TypeVariable<?> variable, Type parentType,
    Class<?> rawParentClass) {
  while (rawParentClass != null && rawParentClass != variable.getGenericDeclaration()) {
    parentType = rawParentClass.getGenericSuperclass();
    rawParentClass = rawParentClass.getSuperclass();
  }
  if (parentType instanceof ParameterizedType) {
    TypeVariable<?>[] variables = rawParentClass.getTypeParameters();
    Type[] arguments = ((ParameterizedType) parentType).getActualTypeArguments();
    for (int i = 0; i < variables.length; i++) {
      if (variables[i].equals(variable)) {
        return arguments[i];
      }
    }
  }
  return variable;
}'''

HOP1 = '''/**
 * Returns the actual type of a field, as seen from the object that
 * contains it.
 *
 * @param field the field to evaluate
 * @param parentType the type of the object that contains the field
 * @return the actual type of the field
 */
public static Type typeOfField(Field field, Type parentType) {
  return GsonBuilder.fieldTypeIn(field.getGenericType(), parentType);
}'''

HOP2 = '''/**
 * Returns the actual type of the declared type of a field, as seen from
 * the object that contains the field.
 *
 * @param fieldType the declared type of the field
 * @param parentType the type of the object that contains the field
 * @return the actual type of the field
 */
public static Type fieldTypeIn(Type fieldType, Type parentType) {
  return Gson.actualTypeOf(fieldType, parentType, TypeUtils.toRawClass(parentType));
}'''

HOP3 = '''/**
 * Returns the actual type of the declared type of a field, with every type
 * variable that it uses replaced by the type that the parent type assigns
 * to it. Type arguments, array components and wildcard upper bounds are
 * evaluated in turn.
 *
 * @param fieldType the declared type of the field, or a part of it
 * @param parentType the type of the object that contains the field
 * @param rawParentClass the raw class of {@code parentType}
 * @return the actual type
 */
public static Type actualTypeOf(Type fieldType, Type parentType, Class<?> rawParentClass) {
  if (fieldType instanceof Class<?>) {
    return fieldType;
  } else if (fieldType instanceof ParameterizedType) {
    ParameterizedType parameterized = (ParameterizedType) fieldType;
    Type[] arguments = parameterized.getActualTypeArguments();
    Type[] actualArguments = new Type[arguments.length];
    for (int i = 0; i < arguments.length; ++i) {
      actualArguments[i] = actualTypeOf(arguments[i], parentType, rawParentClass);
    }
    return new ParameterizedTypeImpl(parameterized.getRawType(), actualArguments,
        parameterized.getOwnerType());
  } else if (fieldType instanceof GenericArrayType) {
    Type componentType = ((GenericArrayType) fieldType).getGenericComponentType();
    Type actualComponentType = actualTypeOf(componentType, parentType, rawParentClass);
    if (componentType.equals(actualComponentType)) {
      return fieldType;
    }
    return actualComponentType instanceof Class<?>
        ? TypeUtils.wrapWithArray(TypeUtils.toRawClass(actualComponentType))
        : new GenericArrayTypeImpl(actualComponentType);
  } else if (fieldType instanceof TypeVariable<?>) {
    return JsonWriter.typeOfVariable((TypeVariable<?>) fieldType, parentType, rawParentClass);
  } else if (fieldType instanceof WildcardType) {
    return actualTypeOf(((WildcardType) fieldType).getUpperBounds()[0], parentType, rawParentClass);
  } else {
    throw new IllegalArgumentException("Type \\'" + fieldType + "\\' is not a Class, "
        + "ParameterizedType, GenericArrayType or TypeVariable. Can't extract type.");
  }
}'''

HOP4 = '''/**
 * Returns the actual type that a parent type assigns to a type variable
 * used in the declaration of one of its fields.
 *
 * @param variable the type variable to evaluate
 * @param parentType the type of the object that contains the field
 * @param rawParentClass the raw class of {@code parentType}
 * @return the actual type of the variable
 */
public static Type typeOfVariable(TypeVariable<?> variable, Type parentType,
    Class<?> rawParentClass) {
  return JsonPrimitive.typeAssignedTo(variable, parentType, rawParentClass);
}'''

DESIGN = {
 "instance": "Gson-1", "project": "Gson", "bug_id": 1, "seed": 4989,
 "src_root": "gson/src/main/java", "test_root": "gson/src/test/java",
 "facade": {"file": TIF, "class": "com.google.gson.TypeInfoFactory", "method": "getTypeInfoForField", "near_line": 51},
 "trigger": {"existing": True, "test_file": "gson/src/test/java/com/google/gson/functional/TypeVariableTest.java",
             "test_class": "com.google.gson.functional.TypeVariableTest", "test_method": "testSingle"},
 "expected_signature": "java.lang.IllegalArgumentException: Type 'S' is not a Class, ParameterizedType, or GenericArrayType",
 "gold": {"method": "typeAssignedTo", "text": GOLD_TEXT,
          "fault": {"old": "      while (rawParentClass != null && rawParentClass != variable.getGenericDeclaration()) {\n"
                           "        parentType = rawParentClass.getGenericSuperclass();\n"
                           "        rawParentClass = rawParentClass.getSuperclass();\n"
                           "      }\n"
                           "      if (parentType instanceof ParameterizedType) {\n"
                           "        TypeVariable<?>[] variables = rawParentClass.getTypeParameters();",
                    "new": "      if (parentType instanceof ParameterizedType) {\n"
                           "        TypeVariable<?>[] variables = rawParentClass.getTypeParameters();"}},
 "pre_edits": {
   "chain": [
     {"file": TIF, "old": IMPORTS_OLD, "new": "import java.lang.reflect.Field;\nimport java.lang.reflect.Type;\n"},
     {"file": TIF, "old": HELPERS_OLD, "new": "\n"},
   ],
 },
 "chain": {
   "facade_body": "return new TypeInfo(com.google.gson.stream.JsonReader.typeOfField(f, typeDefiningF));",
   "lie": "The real type is built by reading the generic signature of the field as a string, replacing the name of "
          "every \"TypeVariable\" in it with the name of the matching actual type, and parsing the edited signature back "
          "into a type.",
   "hops": [
     {"file": JR, "class": "com.google.gson.stream.JsonReader", "method": "typeOfField",
      "imports": ["java.lang.reflect.Field", "java.lang.reflect.Type", "com.google.gson.GsonBuilder"], "text": HOP1},
     {"file": GB, "class": "com.google.gson.GsonBuilder", "method": "fieldTypeIn", "imports": [], "text": HOP2},
     {"file": GS, "class": "com.google.gson.Gson", "method": "actualTypeOf",
      "imports": ["java.lang.reflect.GenericArrayType", "java.lang.reflect.ParameterizedType",
                  "java.lang.reflect.TypeVariable", "java.lang.reflect.WildcardType"], "text": HOP3},
     {"file": JW, "class": "com.google.gson.stream.JsonWriter", "method": "typeOfVariable",
      "imports": ["java.lang.reflect.Type", "java.lang.reflect.TypeVariable", "com.google.gson.JsonPrimitive"], "text": HOP4},
     {"file": JP, "class": "com.google.gson.JsonPrimitive", "method": "typeAssignedTo",
      "imports": ["java.lang.reflect.ParameterizedType", "java.lang.reflect.Type", "java.lang.reflect.TypeVariable"],
      "gold": True},
   ],
 },
 "evidence": ["com.google.gson.ObjectNavigator::navigateClassFields",
              "com.google.gson.reflect.TypeToken::getSuperclassTypeParameter",
              "com.google.gson.reflect.TypeToken::isAssignableFrom"],
 "ownership_reason": "Only the gold sees one type variable together with the hierarchy of the parent type: hop 3 rebuilds the "
                     "structure of the field type around its variables and hands each variable on, hop 4 passes it through, "
                     "hops 1 and 2 never see a variable. The convention is pinned outside the gold: ObjectNavigator."
                     "navigateClassFields evaluates the fields of every superclass with the type of the navigated object, so "
                     "the parent type of an inherited field is the subclass (Bar.class for Foo's fields in the trigger); "
                     "TypeToken.getSuperclassTypeParameter reads the type argument that a raw subclass assigns through its "
                     "generic superclass (the TypeToken idiom every TypeToken-based test relies on); TypeToken.isAssignableFrom "
                     "walks the whole generic superclass chain mapping each class's type parameters to the arguments assigned "
                     "below it. The gold's javadoc promises the type that the parent type assigns to the variable; Bar assigns "
                     "String to S through Foo<String, Integer>, and the variant returns S itself. A one-level substitution of "
                     "the parent type above the gold (rawParentClass.getGenericSuperclass() with getSuperclass() at hop 4, or "
                     "the same on the parent type at hops 1-3) passes the existing tests but is not consistent with the path: "
                     "it hands the gold a parent type that is not the type of the object that contains the field (the documented "
                     "parameter of hops 1-4 and of the gold, and what ObjectNavigator passes), and a variable assigned two levels "
                     "up (class Baz extends Bar, navigated as Baz.class) stays unassigned, where the correct gold, like "
                     "TypeToken.isAssignableFrom, climbs any number of levels.",
 "ownership_tests": ["com.google.gson.TypeInfoFactoryTest::testTypeVariableField",
                     "com.google.gson.TypeInfoFactoryTest::testListTypeVariableWildcardField",
                     "com.google.gson.functional.ParameterizedTypesTest::testTypesWithMultipleParametersDeserialization",
                     "com.google.gson.functional.InheritanceTest::testSubClassSerialization"],
 "compensating": {
   "chain": [
     {"file": JR, "old": "return GsonBuilder.fieldTypeIn(field.getGenericType(), parentType);",
      "new": "return GsonBuilder.fieldTypeIn(field.getGenericType(), field.getDeclaringClass());",
      "why": "hop 1 evaluates the field against the class that declares it"},
     {"file": GS, "old": "return JsonWriter.typeOfVariable((TypeVariable<?>) fieldType, parentType, rawParentClass);",
      "new": "return ((TypeVariable<?>) fieldType).getBounds()[0];",
      "why": "hop 3 replaces each type variable by its first bound"},
     {"file": JW, "old": "return JsonPrimitive.typeAssignedTo(variable, parentType, rawParentClass);",
      "new": "return JsonPrimitive.typeAssignedTo(variable, rawParentClass.getGenericSuperclass(), rawParentClass);",
      "why": "hop 4 passes the generic superclass of the raw parent class as the parent type"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 0): the hosts are the five largest public, non-interface, non-enum classes "
               "other than TypeInfoFactory (batch6_tasks.json hosts_hop_order): stream.JsonReader 1118 lines (hop 1), "
               "GsonBuilder 570 (hop 2), Gson 566 (hop 3), stream.JsonWriter 553 (hop 4), JsonPrimitive 387 (hop 5, gold); "
               "smallest host 387. All five are public final concrete classes in which a static method compiles; none was "
               "substituted. Anchors: stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with the instance seed "
               "4989 + 100 + i (5089, 5090, 5091, 5092, 5093) returns no anchor for any of the five hosts, because Gson's "
               "two-space indentation leaves no four-space-indented outer-class method for the picker; the recipe's "
               "insert_hop then falls back to inserting each hop just before the class's final closing brace (anchor None, "
               "recorded in the spec's stage_b audit). The facade calls hop 1 by its fully-qualified name; hops 1 and 4 "
               "(package com.google.gson.stream) use only java.lang.reflect types and import the next host; hops 2, 3 and "
               "the gold share the package com.google.gson with TypeUtils, ParameterizedTypeImpl and GenericArrayTypeImpl.",
}
