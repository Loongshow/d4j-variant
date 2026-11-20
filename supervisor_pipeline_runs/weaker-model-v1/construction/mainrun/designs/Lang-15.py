"""Main run Lang-15 (C10 recipe on the fixed checkout of Defects4J Lang-15; the real bug modified TypeUtils, and the facade is
in TypeUtils).

Facade: TypeUtils.typesSatisfyVariables(Map) (pool candidate 2). Why not the others:
 - determineTypeArguments (candidate 1): its only test (testDetermineTypeVariableAssignments, TreeSet against
   Iterable<? extends Map<...>>) runs only the main path of the walk (one generic interface per level, every argument a type
   variable of the class below, every variable assigned); every special-case step of the walk and of the variable mapping is
   inert on it, and the omissions it does catch either leave a visibly broken idiom (no mapping) or throw from inside the
   gold (a stack trace that names the gold).
 - isInstance (candidate 4): testIsInstance (Integer against Comparable<Integer> / Comparable<URI>) only exercises the plain
   equal / not-equal decision on one type argument; the only omission it catches drops exact matching, which reads as broken.
 - getArrayComponentType (candidate 3): a single type dispatch with nothing to redistribute over five hops.
typesSatisfyVariables is called only by TypeUtilsTest::testTypesSatisfyVariables, whose three stubs (G extends Comparable<G>,
G extends Comparable<? super G>, T extends Comparable<? extends T>, each with the variable assigned Integer) run the
generic-aware bound check with assignments.

Chain (hosts in draw order, seed 2183; the computation is the original one, in the original order):
  hop 1 ArrayUtils.boundsSatisfied      fold over the assignments (false at the first assigned type outside its bounds)
  hop 2 FastDateFormat.withinBounds     fold over the implicit bounds of one variable (TypeUtils.getImplicitBounds)
  hop 3 StrBuilder.meetsBound           placement: a bound that is itself a type variable stands for its assigned type
                                        (the original substituteTypeVariables, IllegalArgumentException when unassigned)
  hop 4 ToStringStyle.assignableUnder   decision: a parameterized target goes to hop 5, any other target to
                                        TypeUtils.isAssignable(type, toType, typeVarAssigns) (the original dispatch)
  hop 5 StringUtils.conformsTo (GOLD)   the per-bound core for a parameterized bound: the original
                                        isAssignable(Type, ParameterizedType, Map) - the subject's type arguments for the raw
                                        class, the bound's type arguments under the assignments, and the per-variable check
                                        (absent from the subject / exact match / within a wildcard).
Pre-edits (behaviour-preserving, chain geometry): three private TypeUtils helpers the chain calls are made public:
isAssignable(Type, Type, Map), getTypeArguments(Type, Class, Map) and unrollVariableAssignments (with a one-line javadoc).
They keep their bodies; every existing caller resolves to the same method.

Fault (omission in the gold, special-case step): the skip of a type variable that the subject type leaves unbound
(`if (fromTypeArg == null) continue;`) is dropped. The bound's argument map holds the assignments it was resolved with
(getTypeArguments copies typeVarAssigns into it), so for G extends Comparable<G> with G -> Integer the variable G itself is
checked against Integer's arguments for Comparable, finds nothing, and the bound is rejected. Trigger:
TypeUtilsTest::testTypesSatisfyVariables, first assertion (line 516, a bare AssertionError). After the omission the gold reads as a
complete routine for ordinary input (every variable of the target bound by the subject): exact match or within a wildcard.
The gold's javadoc states only the assignability contract (quiet); Integer is assignable to Comparable<Integer>, so the contract
is violated on the trigger input.

External pins: TypeUtils.isAssignable(Type, ParameterizedType, Map) performs the same step (`fromTypeArg != null && ...`, with the
comment that parameters must either be absent from the subject type, within the bounds of the wildcard type, or an exact
match); TypeUtils.getTypeArguments(Type, Class, Map) puts the assignments into the target's argument map; TypeUtilsTest::
testIsAssignable fails when TypeUtils's own copy of the step is removed (checked by mutation in a scratch copy) and passes here.

Single owner: only the gold sees both argument maps; hops 1-4 pass a type, a bound and the assignment map, and no one-line edit
there can make the comparison skip a variable the subject leaves unbound: the assignments are needed to resolve the bound's
arguments (an empty map makes the argument unresolvable, see the declared alternative), and the subject's map is computed inside
the gold. Declared alternatives (G9): hop 1 skips null assignments, hop 3 lets a bound that stays a type variable pass, hop 4
hands the gold an empty assignment map.

Recorded bypasses (one-line, discard the gold's output; they pass the trigger and the full suite because only the trigger calls
the facade):
 B-1 hop 4 routes every target to TypeUtils.isAssignable(type, toType, typeVarAssigns) (or only parameterized targets with a
     Class subject), so hop 5 is never called.
 B-2 hop 3 (or hop 2 / hop 1) calls TypeUtils.isAssignable(type, toType, typeVarAssigns) itself, skipping the hops below it.
 B-3 hop 2 checks the raw class of each bound (TypeUtils.getRawType(bound, null)) instead of the bound: generic-unaware, against
     the 'following the Java generics rules' documentation of hops 2-4.

Lie (appended to the facade's javadoc): the assignments are copied into a map sorted by the names of their type variables and the
bounds of each variable are checked from the last declared to the first. The code iterates the given map in its own order and
checks the implicit bounds in the order getImplicitBounds returns them. It names neither unbound variables nor argument maps nor
any hop."""

TU = "src/main/java/org/apache/commons/lang3/reflect/TypeUtils.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"

GOLD_TEXT = '''/**
 * <p>Checks if a type may be assigned to a parameterized type following the
 * Java generics rules, the type variables having the given assignments.</p>
 *
 * @param type  the type to be assigned
 * @param toParameterizedType  the target parameterized type, not null
 * @param typeVarAssigns  the types assigned to the type variables
 * @return {@code true} if {@code type} is assignable to the parameterized type
 */
public static boolean conformsTo(Type type, ParameterizedType toParameterizedType,
        Map<TypeVariable<?>, Type> typeVarAssigns) {
    if (type == null || toParameterizedType.equals(type)) {
        return true;
    }
    Class<?> toClass = TypeUtils.getRawType(toParameterizedType, null);
    Map<TypeVariable<?>, Type> fromTypeVarAssigns = TypeUtils.getTypeArguments(type, toClass);
    if (fromTypeVarAssigns == null) {
        return false;
    }
    if (fromTypeVarAssigns.isEmpty()) {
        return true;
    }
    Map<TypeVariable<?>, Type> toTypeVarAssigns = TypeUtils.getTypeArguments(toParameterizedType, toClass,
            typeVarAssigns);
    for (TypeVariable<?> var : toTypeVarAssigns.keySet()) {
        Type toTypeArg = TypeUtils.unrollVariableAssignments(var, toTypeVarAssigns);
        Type fromTypeArg = TypeUtils.unrollVariableAssignments(var, fromTypeVarAssigns);
        if (fromTypeArg == null) {
            continue;
        }
        if (toTypeArg.equals(fromTypeArg)) {
            continue;
        }
        if (toTypeArg instanceof WildcardType && TypeUtils.isAssignable(fromTypeArg, toTypeArg, typeVarAssigns)) {
            continue;
        }
        return false;
    }
    return true;
}'''

HOP1 = '''/**
 * <p>Checks whether each type in a map of type variable assignments lies
 * within the bounds of the type variable it is assigned to.</p>
 *
 * @param typeVarAssigns  the types assigned to the type variables, not null
 * @return {@code true} if every assigned type satisfies the bounds of its
 *  type variable
 */
public static boolean boundsSatisfied(Map<TypeVariable<?>, Type> typeVarAssigns) {
    for (Map.Entry<TypeVariable<?>, Type> entry : typeVarAssigns.entrySet()) {
        if (!FastDateFormat.withinBounds(entry.getKey(), entry.getValue(), typeVarAssigns)) {
            return false;
        }
    }
    return true;
}'''

HOP2 = '''/**
 * <p>Checks whether a type lies within every bound of a type variable,
 * following the Java generics rules.</p>
 *
 * @param typeVariable  the type variable
 * @param type  the type assigned to the type variable
 * @param typeVarAssigns  the types assigned to the type variables that the
 *  bounds may refer to
 * @return {@code true} if the type satisfies every bound of the type variable
 */
public static boolean withinBounds(TypeVariable<?> typeVariable, Type type,
        Map<TypeVariable<?>, Type> typeVarAssigns) {
    for (Type bound : TypeUtils.getImplicitBounds(typeVariable)) {
        if (!StrBuilder.meetsBound(type, bound, typeVarAssigns)) {
            return false;
        }
    }
    return true;
}'''

HOP3 = '''/**
 * <p>Checks whether a type lies within one bound of a type variable,
 * following the Java generics rules. A bound that is itself a type variable
 * stands for the type assigned to that variable.</p>
 *
 * @param type  the type to check
 * @param bound  the bound of the type variable
 * @param typeVarAssigns  the types assigned to the type variables
 * @return {@code true} if the type satisfies the bound
 * @throws IllegalArgumentException if the bound is a type variable without
 *  an assigned type
 */
public static boolean meetsBound(Type type, Type bound, Map<TypeVariable<?>, Type> typeVarAssigns) {
    Type toType = bound;
    if (bound instanceof TypeVariable<?>) {
        toType = typeVarAssigns.get(bound);
        if (toType == null) {
            throw new IllegalArgumentException("missing assignment type for type variable " + bound);
        }
    }
    return ToStringStyle.assignableUnder(type, toType, typeVarAssigns);
}'''

HOP4 = '''/**
 * <p>Checks if a type may be assigned to a target type following the Java
 * generics rules, the type variables having the given assignments.</p>
 *
 * @param type  the type to be assigned
 * @param toType  the target type
 * @param typeVarAssigns  the types assigned to the type variables
 * @return {@code true} if {@code type} is assignable to {@code toType}
 */
public static boolean assignableUnder(Type type, Type toType, Map<TypeVariable<?>, Type> typeVarAssigns) {
    if (toType instanceof ParameterizedType) {
        return StringUtils.conformsTo(type, (ParameterizedType) toType, typeVarAssigns);
    }
    return TypeUtils.isAssignable(type, toType, typeVarAssigns);
}'''

DESIGN = {
 "instance": "Lang-15", "project": "Lang", "bug_id": 15, "seed": 2183,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TU, "class": "org.apache.commons.lang3.reflect.TypeUtils", "method": "typesSatisfyVariables", "near_line": 960},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/reflect/TypeUtilsTest.java",
             "test_class": "org.apache.commons.lang3.reflect.TypeUtilsTest", "test_method": "testTypesSatisfyVariables"},
 "expected_signature": "TypeUtilsTest.testTypesSatisfyVariables(TypeUtilsTest.java:516)",
 "gold": {"method": "conformsTo", "text": GOLD_TEXT,
          "fault": {"old": "            Type fromTypeArg = TypeUtils.unrollVariableAssignments(var, fromTypeVarAssigns);\n"
                           "            if (fromTypeArg == null) {\n"
                           "                continue;\n"
                           "            }",
                    "new": "            Type fromTypeArg = TypeUtils.unrollVariableAssignments(var, fromTypeVarAssigns);"}},
 "pre_edits": {
   "chain": [
     {"file": TU, "old": "    private static boolean isAssignable(Type type, Type toType,\n",
      "new": "    public static boolean isAssignable(Type type, Type toType,\n"},
     {"file": TU, "old": "    private static Type unrollVariableAssignments(TypeVariable<?> var, Map<TypeVariable<?>, Type> typeVarAssigns) {\n",
      "new": "    /**\n"
             "     * <p> Follows the assignments of a type variable through a map until a type that is not\n"
             "     * another assigned type variable is reached. </p>\n"
             "     *\n"
             "     * @param var the type variable\n"
             "     * @param typeVarAssigns the map with type variables\n"
             "     * @return the type the variable stands for, <code>null</code> if it has no assignment\n"
             "     */\n"
             "    public static Type unrollVariableAssignments(TypeVariable<?> var, Map<TypeVariable<?>, Type> typeVarAssigns) {\n"},
     {"file": TU, "old": "    private static Map<TypeVariable<?>, Type> getTypeArguments(Type type, Class<?> toClass,\n",
      "new": "    public static Map<TypeVariable<?>, Type> getTypeArguments(Type type, Class<?> toClass,\n"},
   ],
 },
 "chain": {
   "facade_body": "return org.apache.commons.lang3.ArrayUtils.boundsSatisfied(typeVarAssigns);",
   "lie": "The assignments are first copied into a map sorted by the names of their type variables, so that the "
          "result does not depend on the iteration order of the given map, and the bounds of each variable are then "
          "checked from the last declared to the first.",
   "hops": [
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "boundsSatisfied",
      "imports": ["java.lang.reflect.Type", "java.lang.reflect.TypeVariable", "org.apache.commons.lang3.time.FastDateFormat"],
      "text": HOP1},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "withinBounds",
      "imports": ["java.lang.reflect.Type", "java.lang.reflect.TypeVariable", "java.util.Map",
                  "org.apache.commons.lang3.reflect.TypeUtils", "org.apache.commons.lang3.text.StrBuilder"],
      "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "meetsBound",
      "imports": ["java.lang.reflect.Type", "java.lang.reflect.TypeVariable", "java.util.Map",
                  "org.apache.commons.lang3.builder.ToStringStyle"],
      "text": HOP3},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "assignableUnder",
      "imports": ["java.lang.reflect.ParameterizedType", "java.lang.reflect.Type", "java.lang.reflect.TypeVariable",
                  "org.apache.commons.lang3.StringUtils", "org.apache.commons.lang3.reflect.TypeUtils"],
      "text": HOP4},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "conformsTo",
      "imports": ["java.lang.reflect.ParameterizedType", "java.lang.reflect.Type", "java.lang.reflect.TypeVariable",
                  "java.lang.reflect.WildcardType", "java.util.Map", "org.apache.commons.lang3.reflect.TypeUtils"],
      "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.reflect.TypeUtils::isAssignable",
              "org.apache.commons.lang3.reflect.TypeUtils::getTypeArguments",
              "org.apache.commons.lang3.reflect.TypeUtils::typesSatisfyVariables"],
 "ownership_reason": "Only the gold compares the subject's type arguments with the bound's, variable by variable; hops 1-4 pass "
                     "the assigned type, one bound and the assignment map along and cannot make that comparison skip a variable "
                     "the subject leaves unbound with a one-line change (the assignments are needed to resolve the bound's "
                     "arguments, and the subject's argument map is computed inside the gold). TypeUtils.isAssignable(Type, "
                     "ParameterizedType, Map) performs the same per-variable check with the explicit 'fromTypeArg != null' "
                     "clause and the comment that parameters must be absent from the subject type, within the bounds of the "
                     "wildcard type, or an exact match; TypeUtils.getTypeArguments puts the assignments into the bound's "
                     "argument map; testIsAssignable fails when TypeUtils's own clause is removed and passes here.",
 "ownership_tests": ["org.apache.commons.lang3.reflect.TypeUtilsTest::testIsAssignable",
                     "org.apache.commons.lang3.reflect.TypeUtilsTest::testGetTypeArguments",
                     "org.apache.commons.lang3.reflect.TypeUtilsTest::testIsInstance"],
 "compensating": {
   "chain": [
     {"file": AU, "old": "if (!FastDateFormat.withinBounds(entry.getKey(), entry.getValue(), typeVarAssigns)) {",
      "new": "if (entry.getValue() != null && !FastDateFormat.withinBounds(entry.getKey(), entry.getValue(), typeVarAssigns)) {",
      "why": "hop 1 leaves a variable without an assigned type unchecked"},
     {"file": SB, "old": "return ToStringStyle.assignableUnder(type, toType, typeVarAssigns);",
      "new": "return toType instanceof TypeVariable<?> || ToStringStyle.assignableUnder(type, toType, typeVarAssigns);",
      "why": "hop 3 lets a bound that stays a type variable pass unchecked"},
     {"file": TSS, "old": "return StringUtils.conformsTo(type, (ParameterizedType) toType, typeVarAssigns);",
      "new": "return StringUtils.conformsTo(type, (ParameterizedType) toType, java.util.Collections.<TypeVariable<?>, Type>emptyMap());",
      "why": "hop 4 keeps the assignments out of the comparison of the type arguments"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2183 (mr_lib preview, n=5, target org/apache/commons/lang3/reflect/TypeUtils.java): "
               "ArrayUtils (hop 1), time.FastDateFormat (hop 2), text.StrBuilder (hop 3), builder.ToStringStyle (hop 4), "
               "StringUtils (hop 5, gold). All five are public concrete classes in which a static method compiles and that can "
               "see java.lang.reflect and the public TypeUtils; none was skipped. Facade is pool candidate 2 "
               "(typesSatisfyVariables); see the module docstring for why candidates 1, 3 and 4 were set aside.",
}
