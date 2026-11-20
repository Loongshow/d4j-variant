"""Main run Lang-33 (C10 recipe on the fixed checkout of Defects4J Lang-33; the real bug modified ClassUtils, the target class).

Facade: ClassUtils.getAllInterfaces(Class) (allowed target, pool candidate 2). The other allowed targets were set aside:
getShortClassName has three production callers (ToStringStyle.getShortClassName behind every short-prefix and standard style,
ExceptionUtils.getMessage, getShortCanonicalName), and its inner-class and array steps are asserted by ClassUtilsTest,
ShortPrefixToStringStyleTest and StandardToStringStyleTest alike, so no omission there fails exactly one test; its primitive
abbreviation step reads the private reverseAbbreviationMap, which no hop host can see. getAllSuperclasses is a two-statement
superclass walk: its only omissions freeze the walk cursor (an endless loop) or drop the add (an empty, dead loop).
Original computation of getAllInterfaces: null -> null; a LinkedHashSet; for the class and then each superclass, each declared
interface in declaration order is added and, when new, followed at once by the interfaces it extends (the private recursive
helper getAllInterfaces(Class, HashSet)); the set is copied into an ArrayList.

Chain (hosts in draw order for seed 2226, mr_lib preview, no substitution):
  hop 1 builder.ToStringStyle.interfacesOf         aggregation: a LinkedHashSet, copied into the returned ArrayList
  hop 2 text.StrBuilder.gatherInterfaces          placement: the type list, the class followed by its superclasses
                                                  (ClassUtils.getAllSuperclasses with the class put in front)
  hop 3 StringUtils.interfacesOfTypes             plumbing: the type list as an array
  hop 4 time.FastDateFormat.typeInterfaces        pass-through
  hop 5 ArrayUtils.addInterfaces                  GOLD: for each type, each declared interface is added to the set and, when
                                                  new, the interfaces it extends are added at once (recursive call)
The correct configuration computes exactly the original list for every input (same null guard, same type order, same
depth-first order per interface, same duplicate rule).

Fault (omission in the gold): the recursive call that adds the interfaces an interface extends is dropped, together with the
condition that only guarded it, so the gold adds just the interfaces each type declares. Trigger: the EXISTING test
ClassUtilsTest::test_getAllInterfaces_Class. CY extends CX implements IB, IC; IC extends ID, IE; IE extends IF; CX implements
IB, IA, IE. Expected [IB, IC, ID, IE, IF, IA]; the variant returns [IB, IC, IA, IE] ("expected:<6> but was:<4>"). It is the only
test that sees an interface which extends another through this method: FieldUtils.getField (testbed interfaces Foo and Bar extend
nothing) and ClassUtils.getPublicMethod (Set is a declared interface of the unmodifiable set and declares isEmpty) still pass.

The gold's javadoc states the idiomatic contract (the interfaces implemented by each of the given types are added to the set, in
the order of the types) and is silent on the interfaces that an interface extends. A class implements the interfaces its declared
interfaces extend (CY is an ID), so the omission violates that contract on the trigger. The convention is pinned outside the
gold: the facade's javadoc ('looking through each interface in turn as declared in the source file and following its hierarchy
up'); MethodUtils.getAccessibleMethodFromInterfaceNest, the project's other search over the interfaces of a class and its
superclasses, recursively checks the parent interfaces of each interface; FieldUtils.getField and ClassUtils.getPublicMethod
consume the list (FieldUtilsTest::testGetField finds Foo through the package-private superclass Parent, testAmbig needs both Foo
and Bar, ClassUtilsTest::testGetPublicMethod finds isEmpty on a public interface).

Single owner: only the gold visits the types together with their interfaces, and it adds the interfaces of all the types before
returning. A supplement placed after it at any hop can only append, so the interfaces of IC's hierarchy land after IA and the
list order at index 2 is still IA (the trigger asserts index by index). No production utility other than the facade itself
lists the interfaces an interface extends (getAccessibleMethodFromInterfaceNest is private and searches for a method); calling
the facade on the same class from a hop recurses without end, and calling it on the interfaces found only appends after IA. Declared alternatives (G9): hop 1 runs a second pass of the gold over the
interfaces found ([IB, IC, IA, IE, ID, IF]); hop 2 puts the class's own interfaces into the type list ([IB, IC, ID, IE, IA]);
hop 4 calls the gold a second time over the interfaces found ([IB, IC, IA, IE, ID, IF]); none passes the trigger.
Recorded bypasses (multi-statement re-implementations outside the gold):
 B-1 hop 4 calls the gold once per type and then recurses through itself over each declared interface:
     `for (Class<?> t : types) { ArrayUtils.addInterfaces(new Class<?>[] {t}, found); for (Class<?> f : t.getInterfaces()) { typeInterfaces(new Class<?>[] {f}, found); } }`
     It re-implements the gold's loop over the types and adds a traversal of its own. Its order is not the documented one: for a
     class declaring I1, I2 with I1 extends J it lists I1, I2, J, where the facade's javadoc (each interface followed by its
     hierarchy, then the next) gives I1, J, I2. The trigger cannot tell the two apart (IB extends nothing), so it is test-fitted,
     not a repair. Checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests; a probe class
     (C implements I1, I2; I1 extends J) gives "I1 J I2" on the correct configuration and "I1 I2 J" with B-1.
 B-0 the facade or a hop re-implements the whole depth-first walk (loop plus recursion), never calling the gold, which makes the
     gold's output dead.

Lie: the facade's javadoc claims the interfaces are kept in an array that doubles whenever it is full, each interface being
looked for in that array by a linear search before it is added; the code keeps them in a LinkedHashSet (hashed membership, no
array, no search) and copies the set into an ArrayList. It names neither the interfaces an interface extends nor any step that is
omitted nor any hop.

Pre-edit (behaviour-preserving, chain geometry): the private recursive helper getAllInterfaces(Class, HashSet) is removed (after
the facade rewrite it has no caller and would be a second implementation of the gold). The imports java.util.HashSet and
java.util.LinkedHashSet stay in ClassUtils, unused: the spec generator expresses edits as unique old/new context blocks and
cannot express a pure deletion of import lines far from any other change.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first, then to the VARIANT gold:
  correct gold:
  T1 absent: `types` drives the outer loop and `found` receives every add and is passed to the recursive call.
  T2 absent: `type` and `iface` are read (getInterfaces, add/argument); no literal-initialised local; for-each variables only;
     the one decision `if (found.add(iface))` decides whether the recursive call runs, so it is live.
  T3 absent: every type and every interface gets the same treatment; no case split, pair, range or named class handled in part.
  T4 absent: 'the interfaces implemented by each of the given types' is addressed by the loop over `type.getInterfaces()`, 'to a
     set' by `found.add`, 'in the order of the types' by the array-order outer loop; 'not null' clauses are caller preconditions.
  variant gold (whole text, after the omission):
  T1 absent: `types` is the outer loop's array; `found` receives `found.add(iface)`; both change the side effect.
  T2 absent: no dead local (`type` -> getInterfaces, `iface` -> add), nothing frozen (for-each variables, no counters, flags,
     cursors or best-so-far), and no decision is left at all (no if, case or ternary).
  T3 absent: no enumeration, branch set, pair halves or range ends; the text names 'the given types' and 'the interfaces
     implemented by' them and the body treats each member it reads identically.
  T4 absent: each phrase ('the interfaces implemented by each of the given types', 'to a set', 'in the order of the types') is a
     general description that the two loops and the add address; no limit, bound, value class or case is named; '@param ...
     not null' clauses are caller preconditions."""

CU = "src/main/java/org/apache/commons/lang3/ClassUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

TYPES_DOC = '''/**
 * <p>Adds the interfaces implemented by each of the given types to a
 * set, in the order of the types.</p>
 *
 * @param types  the types to look up, not null
 * @param found  the set of interfaces to add to, not null
 */'''

GOLD_TEXT = TYPES_DOC + '''
public static void addInterfaces(Class<?>[] types, Set<Class<?>> found) {
    for (Class<?> type : types) {
        for (Class<?> iface : type.getInterfaces()) {
            if (found.add(iface)) {
                addInterfaces(new Class<?>[] {iface}, found);
            }
        }
    }
}'''

HOP1 = '''/**
 * <p>Gets a <code>List</code> of the interfaces implemented by a class
 * and its superclasses.</p>
 *
 * @param cls  the class to look up, not null
 * @return the <code>List</code> of interfaces in order, each interface
 *  listed once
 */
public static List<Class<?>> interfacesOf(Class<?> cls) {
    Set<Class<?>> found = new LinkedHashSet<Class<?>>();
    StrBuilder.gatherInterfaces(cls, found);
    return new ArrayList<Class<?>>(found);
}'''

HOP2 = '''/**
 * <p>Adds the interfaces implemented by a class and its superclasses to
 * a set, starting with the class itself.</p>
 *
 * @param cls  the class to look up, not null
 * @param found  the set of interfaces to add to, not null
 */
public static void gatherInterfaces(Class<?> cls, Set<Class<?>> found) {
    List<Class<?>> types = ClassUtils.getAllSuperclasses(cls);
    types.add(0, cls);
    StringUtils.interfacesOfTypes(types, found);
}'''

HOP3 = '''/**
 * <p>Adds the interfaces implemented by each of the types in a list to a
 * set, in the order of the list.</p>
 *
 * @param types  the types to look up, not null
 * @param found  the set of interfaces to add to, not null
 */
public static void interfacesOfTypes(List<Class<?>> types, Set<Class<?>> found) {
    FastDateFormat.typeInterfaces(types.toArray(new Class<?>[types.size()]), found);
}'''

HOP4 = TYPES_DOC + '''
public static void typeInterfaces(Class<?>[] types, Set<Class<?>> found) {
    ArrayUtils.addInterfaces(types, found);
}'''

HELPER = ('\n    /**\n     * Get the interfaces for the specified class.\n     *\n'
          '     * @param cls  the class to look up, may be <code>null</code>\n'
          '     * @param interfacesFound the <code>Set</code> of interfaces for the class\n     */\n'
          '    private static void getAllInterfaces(Class<?> cls, HashSet<Class<?>> interfacesFound) {\n'
          '        while (cls != null) {\n            Class<?>[] interfaces = cls.getInterfaces();\n\n'
          '            for (Class<?> i : interfaces) {\n                if (interfacesFound.add(i)) {\n'
          '                    getAllInterfaces(i, interfacesFound);\n                }\n            }\n\n'
          '            cls = cls.getSuperclass();\n         }\n     }\n')

DESIGN = {
 "instance": "Lang-33", "project": "Lang", "bug_id": 33, "seed": 2226,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": CU, "class": "org.apache.commons.lang3.ClassUtils", "method": "getAllInterfaces", "near_line": 313},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/ClassUtilsTest.java",
             "test_class": "org.apache.commons.lang3.ClassUtilsTest", "test_method": "test_getAllInterfaces_Class"},
 "expected_signature": "expected:<6> but was:<4>",
 "gold": {"method": "addInterfaces", "text": GOLD_TEXT,
          "fault": {"old": "                if (found.add(iface)) {\n"
                           "                    addInterfaces(new Class<?>[] {iface}, found);\n"
                           "                }",
                    "new": "                found.add(iface);"}},
 "pre_edits": {
   "chain": [
     {"file": CU, "old": HELPER, "new": ""},
   ],
 },
 "chain": {
   "facade_body": "if (cls == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang3.builder.ToStringStyle.interfacesOf(cls);",
   "lie": "The interfaces are kept in an array that doubles in size whenever it is full, and each interface met is "
          "looked for in that array by a linear search before it is added.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "interfacesOf",
      "imports": ["java.util.ArrayList", "java.util.LinkedHashSet", "java.util.List", "java.util.Set",
                  "org.apache.commons.lang3.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "gatherInterfaces",
      "imports": ["java.util.Set", "org.apache.commons.lang3.ClassUtils", "org.apache.commons.lang3.StringUtils"], "text": HOP2},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "interfacesOfTypes",
      "imports": ["java.util.Set", "org.apache.commons.lang3.time.FastDateFormat"], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "typeInterfaces",
      "imports": ["java.util.Set", "org.apache.commons.lang3.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "addInterfaces",
      "imports": ["java.util.Set"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.reflect.MethodUtils::getAccessibleMethodFromInterfaceNest",
              "org.apache.commons.lang3.reflect.FieldUtils::getField",
              "org.apache.commons.lang3.ClassUtils::getPublicMethod"],
 "ownership_reason": "Only the gold visits the types together with their interfaces; hop 1 copies a set into a list, hop 2 "
                     "lists the class and its superclasses, hops 3 and 4 hand the types along. The gold adds the interfaces "
                     "of every type before it returns, so anything a hop adds afterwards is appended after IA and cannot "
                     "restore the documented order [IB, IC, ID, IE, IF, IA]; reaching the interfaces an interface extends "
                     "needs a recursive walk, which no production utility other than the facade itself offers. The "
                     "convention is pinned outside the gold: the facade's javadoc (each interface followed up its hierarchy, "
                     "then each superclass, later duplicates ignored); MethodUtils.getAccessibleMethodFromInterfaceNest "
                     "recursively checks the parent interfaces of each interface of a class and its superclasses; "
                     "FieldUtils.getField and ClassUtils.getPublicMethod consume the list (FieldUtilsTest.testGetField finds "
                     "Foo through the package-private superclass Parent, testAmbig needs both Foo and Bar, "
                     "ClassUtilsTest.testGetPublicMethod finds isEmpty on a public interface); "
                     "ClassUtilsTest.test_getAllSuperclasses_Class pins the type order hop 2 builds on. The gold's own "
                     "contract is violated on the trigger: a class implements every interface its declared interfaces "
                     "extend (CY is an ID, IE and IF through IC), and the gold returns without adding them. Recorded "
                     "bypass (test-fitted): hop 4 calling the gold once per type and then recursing through itself over "
                     "each declared interface passes the full suite, but it re-implements the traversal outside the gold "
                     "and breaks the facade's documented order: for C implements I1, I2 with I1 extends J it lists "
                     "I1, I2, J, while the correct chain lists I1, J, I2 (each interface followed up its hierarchy "
                     "before the next).",
 "ownership_tests": ["org.apache.commons.lang3.reflect.FieldUtilsTest::testGetField",
                     "org.apache.commons.lang3.reflect.FieldUtilsTest::testAmbig",
                     "org.apache.commons.lang3.ClassUtilsTest::testGetPublicMethod",
                     "org.apache.commons.lang3.reflect.MethodUtilsTest::testGetAccessibleInterfaceMethod",
                     "org.apache.commons.lang3.ClassUtilsTest::test_getAllSuperclasses_Class"],
 "compensating": {
   "chain": [
     {"file": TSS, "old": "StrBuilder.gatherInterfaces(cls, found);",
      "new": "StrBuilder.gatherInterfaces(cls, found); org.apache.commons.lang3.ArrayUtils.addInterfaces(found.toArray(new Class<?>[found.size()]), found);",
      "why": "hop 1 runs a second pass over the interfaces found"},
     {"file": SB, "old": "types.add(0, cls);",
      "new": "types.add(0, cls); types.addAll(1, java.util.Arrays.asList(cls.getInterfaces()));",
      "why": "hop 2 puts the class's own interfaces into the type list"},
     {"file": FDF, "old": "ArrayUtils.addInterfaces(types, found);",
      "new": "ArrayUtils.addInterfaces(types, found); ArrayUtils.addInterfaces(found.toArray(new Class<?>[found.size()]), found);",
      "why": "hop 4 calls a second time over the interfaces found"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2226 (mr_lib preview, target org/apache/commons/lang3/ClassUtils.java): "
               "builder.ToStringStyle (hop 1), text.StrBuilder (hop 2), StringUtils (hop 3), time.FastDateFormat (hop 4), "
               "ArrayUtils (hop 5, gold). All five are public classes in which a static method compiles (ToStringStyle is "
               "abstract, which does not affect a static method); none was skipped. The preview notes that the draw relaxed "
               "the 'distinct from target package' constraint for hops 3-5 (too few other-package classes above 1500 lines), "
               "so StringUtils and ArrayUtils share the target's package. The facade calls hop 1 by its fully-qualified name; "
               "each hop imports the next host and the java.util types it uses.",
}
