"""Main run JacksonDatabind-103 (cell C10f, batch 6; C10 recipe on the fixed checkout of Defects4J JacksonDatabind-103; the real
bug modified ClassUtil, the target class, among sixteen others).

host_mode = "1500" (six other public classes of at least 1500 lines exist, so the hosts are the recipe's seeded draw, exactly as in
C10). Host sizes (newline counts) in hop order: DeserializationContext 1777, deser.BeanDeserializerBase 1756, ObjectMapper 4211,
deser.BasicDeserializerFactory 2177, ObjectReader 1949 (gold host). Smallest host: 1756 lines (BeanDeserializerBase); gold host 1949.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2; log construction/mainrun/logs/probe_JacksonDatabind-103.log): in scratch
copies of the fixture, the first statement of each allowed facade was made
`if (true) throw new IllegalStateException("PROBE-REACHED");` (the `if (true)` keeps the rest of the body reachable for javac), one
facade per copy, and the FULL suite was run on each copy (baseline copy: 0 failing tests).
  isLocalType   : 782 failing tests, every one with PROBE-REACHED; ClassUtilTest::testCanBeABeanType fails with
                  `java.lang.IllegalStateException: PROBE-REACHED at ClassUtil.isLocalType(ClassUtil.java:182)` (direct call, line 75);
                  the other 781 reach it through BeanDeserializerFactory.isPotentialBeanType, which passes allowNonStatic = true.
                  Re-run on its own before this design (defects4j test -t ClassUtilTest::testCanBeABeanType): 1 failing test,
                  PROBE-REACHED at ClassUtil.isLocalType(ClassUtil.java:182).
  wrapperType   : 3 failing tests (ClassUtilTest::testPrimitiveWrapperType, TestRootType::testIssue456WrapperPart,
                  ProblemHandler1767Test::testPrimitivePropertyWithHandler), all PROBE-REACHED.
  primitiveType : 10 failing tests (ClassUtilTest::testWrapperToPrimitiveType, BeanUtilTest::testGetDefaultValue, five
                  JsonIncludeTest methods, MapEntryFormatTest::testInclusion, TypeCoercion1592Test, TestViewSerialization::test868),
                  all PROBE-REACHED.
  All three allowed facades are reached by an existing test; isLocalType is used.

Facade: ClassUtil.isLocalType(Class<?>, boolean) (allowed target, BATCH6_PREREGISTRATION.md row 129). The other two allowed
targets were set aside: wrapperType and primitiveType are eight-way dispatches over the primitive types; leaving out one case of the
dispatch is a visibly incomplete closed set (checklist T3), the only other decision in them is the non-primitive / non-wrapper
argument path (an argument check that every caller can make itself), and a Class result can be re-checked by any caller
(`isPrimitive()`), so no single owner exists.
Original computation of isLocalType: inside a try that swallows SecurityException and NullPointerException (Google App Engine),
a class with an enclosing method is "local/anonymous"; otherwise, when allowNonStatic is false, a class that is not static AND has
an enclosing class is "non-static member class"; anything else gives null. isLocalType has no javadoc in the original, so the
recipe's rewrite_facade (which appends the lie inside an existing javadoc and silently skips a method without one) would drop the
lie; a behaviour-preserving pre-edit gives it a one-sentence javadoc in ClassUtil's own voice (modelled on canBeABeanType's
"type String (that identifies why ...)" wording) that states what the method returns, and the lie is appended to it.

Chain (hosts in draw order for seed 6621, mr_lib preview, target com/fasterxml/jackson/databind/util/ClassUtil.java, none skipped):
  hop 1 DeserializationContext.findClassKind             plumbing: the try that maps SecurityException / NullPointerException to null
  hop 2 deser.BeanDeserializerBase.findNestedClassKind   decision: a class with an enclosing method is "local/anonymous"
  hop 3 ObjectMapper.findMemberClassKind                 decision: allowNonStatic = true gives null
  hop 4 deser.BasicDeserializerFactory.findInnerClassKind  placement: a non-zero count of enclosing instances gives
                                                         "non-static member class", zero gives null
  hop 5 ObjectReader.countEnclosingInstances             GOLD: walks from the class outwards through its enclosing classes and
                                                         counts the enclosing instances an instance of it needs (one for each
                                                         non-static class on the way that has an enclosing class)
The correct configuration returns the original result for every input: hop 4 tests count != 0, and the count is non-zero exactly
when the first step of the walk counts, that is when the class itself is not static and has an enclosing class (the original
three-part condition, after hop 2 has answered classes with an enclosing method); same order of the checks and the same exception
mapping (the walk also reads the modifiers and enclosing class of the enclosing classes, inside the same try).

Fault (one-line omission in the gold's loop): the guard `if (ClassUtil.getEnclosingClass(c) != null)` around `++count;` is dropped
(with its closing brace), so every non-static class on the way out is counted, including the outermost one, which has no enclosing
class. A top-level class never carries the static modifier, so the count for a top-level class becomes 1 instead of 0 and every
top-level class is reported as a "non-static member class" when allowNonStatic is false. Trigger: the EXISTING test
ClassUtilTest::testCanBeABeanType; its canBeABeanType assertions and isLocalType(InnerNonStatic.class, false) =
"non-static member class" still hold (count 2 instead of 1, still non-zero), and assertNull(ClassUtil.isLocalType(Integer.class,
false)) at line 76 fails with `Expected: <null> but was: non-static member class`. It is the only test that calls isLocalType with
allowNonStatic = false; the 781 other tests that reach the facade come through BeanDeserializerFactory.isPotentialBeanType with
allowNonStatic = true, which hop 3 answers before the gold is called.

The gold's javadoc states the idiomatic contract (the number of enclosing instances that have to exist before an instance of the
class can be created) and is silent on how the end of the walk is handled. An instance of Integer needs no enclosing instance, so
the variant violates that contract on the trigger input. The convention is pinned outside the gold: ClassUtil.isNonStaticInnerClass
takes the same step with both parts (`!Modifier.isStatic(cls.getModifiers()) && (getEnclosingClass(cls) != null)`), and
AnnotatedClass.isNonStaticInnerClass delegates to it for BasicDeserializerFactory's creator collection (which skips every
constructor but the default one for a non-static inner class) and POJOPropertiesCollector; dropping its enclosing-class half makes
305 tests fail, for example TestCreators2::testJackson431 and MapDeserializationTest::testKeyWithCreator (`Cannot construct
instance of java.util.ArrayList / java.util.LinkedHashMap`: the top-level JDK classes are then taken to need an enclosing
instance). ClassUtil.getOuterClass gives the enclosing class of a non-static class, which is null for a top-level class, and
BeanDeserializerBase._resolveInnerClassValuedProperty uses it to find the one-argument constructor that takes the single
enclosing instance; ClassNameIdResolver._idFrom relies on its null for top-level classes. Passing tests: TestCreators2::
testJackson431, MapDeserializationTest::testKeyWithCreator, InnerClassCreatorTest::testIssue1501 (the non-static inner class
message via isNonStaticInnerClass), TestInnerClass::testSimpleNonStaticInner (a non-static inner class bound to its one enclosing
instance via getOuterClass).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `int count = 0; for (Class<?> c = cls; (c != null) && !Modifier.isStatic(c.getModifiers());
 c = ClassUtil.getEnclosingClass(c)) { if (ClassUtil.getEnclosingClass(c) != null) { ++count; } } return count;`):
  T1 absent: cls is the start of the walk; its modifiers and enclosing classes decide the count, which is returned; no argument check.
  T2 absent: count is incremented inside the loop and returned; c is the cursor, advanced by the for update; the if decides whether
     a step is counted (the outermost class is not), and the c != null test ends the walk after the outermost class, so neither
     decision is dead; no literal-initialised local stays unassigned.
  T3 absent: no enumerated set, pair halves or range ends; the text names no class of inputs.
  T4 absent: the javadoc names only the general quantity (the enclosing instances needed); no limit, bound, value class or case;
     no inline comment; the identifiers (countEnclosingInstances, count, c, cls) name nothing the body does not meet.
  Nothing needed rewriting.
 Variant gold (javadoc, signature, `int count = 0; for (Class<?> c = cls; (c != null) && !Modifier.isStatic(c.getModifiers());
 c = ClassUtil.getEnclosingClass(c)) { ++count; } return count;`):
  T1 absent: the only parameter, cls, is the start of the walk; its value decides how many steps are counted, which is returned.
  T2 absent: count is incremented in the loop and returned (not dead, not frozen); c is advanced by the for update; the loop
     condition's two tests both end the walk on some path (a static class, the end of the chain); no branch, case or ternary.
  T3 absent: no case, branch or check over a set with a handled and an unhandled member; no pair halves or range ends of which one
     is treated; the gold's text names no class of inputs that it handles in part ('No member handled').
  T4 absent: 'counts the enclosing instances that have to exist before an instance of given class can be created' and '@return
     Number of enclosing instances needed' are general descriptions of the count that the loop computes; no concrete rule, limit,
     bound, value class or case is named; no inline comment; no identifier names a property the body visibly does not meet.

Single owner: only the gold walks the enclosing classes and decides which steps need an enclosing instance; hops 1-3 handle the
exception mapping, the local/anonymous case and the allowNonStatic flag, and hop 4 only turns the gold's count into the kind
String. Once the gold has counted 1 for a class, hop 4 cannot tell a top-level class from a member class that needs one enclosing
instance without doing the gold's decision again. Declared alternatives (G9, none absorbs): hop 4 also reports interfaces as
needing no enclosing instance; hop 2 also reports anonymous classes as local/anonymous; hop 3 also accepts primitive types. None
changes the Integer case.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in scratch copies, defects4j
compile, trigger, full suite; log construction/mainrun/logs/probe_JacksonDatabind-103.log):
 B-0 bypass: the facade's original body (the pristine checkout), discarding the chain.
 B-1 bypass: hop 4 decides top-level classes itself before asking the gold:
     `if (ClassUtil.getEnclosingClass(type) == null || ObjectReader.countEnclosingInstances(type) == 0) {` (for Integer the gold is
     never called); B-1' the same with `if (!type.isMemberClass() || ObjectReader.countEnclosingInstances(type) == 0) {`.
 B-2 bypass: hop 4 asks the evidence method instead of the gold: `if (!ClassUtil.isNonStaticInnerClass(type)) {`, making the gold
     dead.
 B-3 bypass: hop 3 accepts top-level classes itself: `if (allowNonStatic || ClassUtil.getEnclosingClass(type) == null) {`, so hop 4
     and the gold are never called for Integer.
 T-1 test-fitted, not consistent with the path: hop 4 reports only counts above one (`if (ObjectReader.countEnclosingInstances(type)
     <= 1) {`): it breaks hop 4's own documentation (a class whose instances need one enclosing instance gives null) and, on the
     gold's documented count, it drops every member class that needs exactly one enclosing instance; on the variant it also drops a
     non-static member class of a static nested class (the walk stops at the static class, count 1).
 T-2 test-fitted, not consistent with the path: hop 4 also returns null for final classes (`... == 0 || Modifier.isFinal(...)`);
     a final non-static member class still needs its enclosing instance.

Lie: the facade's javadoc claims the answer is looked up in a table that maps each class seen so far to its kind, and is added to
that table the first time a class is checked; the chain keeps no table and checks every class afresh. It names neither the
enclosing class nor the static modifier nor any hop.

Pre-edit (behaviour-preserving, needed by the recipe): a javadoc above isLocalType (none existed), so that the lie has a
documentation voice to be appended to."""

CU = "src/main/java/com/fasterxml/jackson/databind/util/ClassUtil.java"
DC = "src/main/java/com/fasterxml/jackson/databind/DeserializationContext.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"

GOLD_TEXT = '''/**
 * Helper method that counts the enclosing instances that have to exist
 * before an instance of given class can be created.
 *
 * @return Number of enclosing instances needed
 */
public static int countEnclosingInstances(Class<?> cls)
{
    int count = 0;
    for (Class<?> c = cls; (c != null) && !Modifier.isStatic(c.getModifiers());
            c = ClassUtil.getEnclosingClass(c)) {
        if (ClassUtil.getEnclosingClass(c) != null) {
            ++count;
        }
    }
    return count;
}'''

HOP1 = '''/**
 * Helper method that checks whether given class is a local or anonymous
 * class or, unless <code>allowNonStatic</code> is true, a non-static
 * member class. Security and null pointer exceptions thrown while the
 * class is introspected are taken to mean that it is neither.
 *
 * @return Null if class is neither; type String (that identifies the
 *   kind of class) if it is
 */
public static String findClassKind(Class<?> type, boolean allowNonStatic)
{
    try {
        return BeanDeserializerBase.findNestedClassKind(type, allowNonStatic);
    } catch (SecurityException e) {
    } catch (NullPointerException e) {
    }
    return null;
}'''

HOP2 = '''/**
 * Helper method that checks whether given class is a local or anonymous
 * class or, unless <code>allowNonStatic</code> is true, a non-static
 * member class.
 *
 * @return Null if class is neither; type String (that identifies the
 *   kind of class) if it is
 */
public static String findNestedClassKind(Class<?> type, boolean allowNonStatic)
{
    if (ClassUtil.hasEnclosingMethod(type)) {
        return "local/anonymous";
    }
    return ObjectMapper.findMemberClassKind(type, allowNonStatic);
}'''

HOP3 = '''/**
 * Helper method that checks whether given class, which is neither local
 * nor anonymous, is a non-static member class; such classes are accepted
 * if <code>allowNonStatic</code> is true.
 *
 * @return Null if class is accepted; type String (that identifies the
 *   kind of class) if not
 */
public static String findMemberClassKind(Class<?> type, boolean allowNonStatic)
{
    if (allowNonStatic) {
        return null;
    }
    return BasicDeserializerFactory.findInnerClassKind(type);
}'''

HOP4 = '''/**
 * Helper method that checks whether instances of given class, which is
 * neither local nor anonymous, need an enclosing instance to be created.
 *
 * @return Type String "non-static member class" if they do; null if not
 */
public static String findInnerClassKind(Class<?> type)
{
    if (ObjectReader.countEnclosingInstances(type) == 0) {
        return null;
    }
    return "non-static member class";
}'''

FACADE_DOC_OLD = "    public static String isLocalType(Class<?> type, boolean allowNonStatic)\n"
FACADE_DOC_NEW = ("    /**\n"
                  "     * Helper method that checks whether given class is a local or anonymous\n"
                  "     * class or, unless <code>allowNonStatic</code> is true, a non-static\n"
                  "     * member class; returns type String (that identifies the kind of class)\n"
                  "     * if it is, and null if it is neither.\n"
                  "     */\n"
                  "    public static String isLocalType(Class<?> type, boolean allowNonStatic)\n")

DESIGN = {
 "instance": "JacksonDatabind-103", "project": "JacksonDatabind", "bug_id": 103, "seed": 6621,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": CU, "class": "com.fasterxml.jackson.databind.util.ClassUtil", "method": "isLocalType", "near_line": 186},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/util/ClassUtilTest.java",
             "test_class": "com.fasterxml.jackson.databind.util.ClassUtilTest", "test_method": "testCanBeABeanType"},
 "expected_signature": "but was: non-static member class",
 "gold": {"method": "countEnclosingInstances", "text": GOLD_TEXT,
          "fault": {"old": "                c = ClassUtil.getEnclosingClass(c)) {\n"
                           "            if (ClassUtil.getEnclosingClass(c) != null) {\n"
                           "                ++count;\n"
                           "            }\n"
                           "        }",
                    "new": "                c = ClassUtil.getEnclosingClass(c)) {\n"
                           "            ++count;\n"
                           "        }"}},
 "pre_edits": {
   "chain": [{"file": CU, "old": FACADE_DOC_OLD, "new": FACADE_DOC_NEW}],
 },
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.DeserializationContext.findClassKind(type, allowNonStatic);",
   "lie": "The answer is looked up in a table that maps each class seen so far to its kind, and is added to that table the "
          "first time a class is checked.",
   "hops": [
     {"file": DC, "class": "com.fasterxml.jackson.databind.DeserializationContext", "method": "findClassKind",
      "imports": [], "text": HOP1},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "findNestedClassKind",
      "imports": [], "text": HOP2},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "findMemberClassKind",
      "imports": [], "text": HOP3},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "findInnerClassKind",
      "imports": [], "text": HOP4},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "countEnclosingInstances",
      "imports": ["java.lang.reflect.Modifier"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.util.ClassUtil::isNonStaticInnerClass",
              "com.fasterxml.jackson.databind.util.ClassUtil::getOuterClass",
              "com.fasterxml.jackson.databind.deser.BeanDeserializerBase::_resolveInnerClassValuedProperty",
              "com.fasterxml.jackson.databind.introspect.AnnotatedClass::isNonStaticInnerClass"],
 "ownership_reason": "Only the gold walks the enclosing classes and decides which steps of the walk need an enclosing instance: hop "
                     "1 maps SecurityException and NullPointerException to null, hop 2 reports a class with an enclosing method as "
                     "local/anonymous, hop 3 accepts every remaining class when allowNonStatic is true, and hop 4 only turns the "
                     "gold's count into the kind String (non-zero: 'non-static member class'). On the trigger input (Integer.class, "
                     "allowNonStatic false) every hop does what its javadoc says and the gold counts one enclosing instance for "
                     "Integer, a top-level class, although an instance of Integer needs none, which its own contract ('the "
                     "enclosing instances that have to exist before an instance of given class can be created') excludes. The "
                     "convention is pinned outside the gold: ClassUtil.isNonStaticInnerClass takes the same step with both parts "
                     "(not static AND an enclosing class exists), and AnnotatedClass.isNonStaticInnerClass delegates to it for "
                     "BasicDeserializerFactory's creator collection, which skips all but the default constructor of a non-static "
                     "inner class; without its enclosing-class half the top-level JDK classes java.util.ArrayList and "
                     "java.util.LinkedHashMap are taken to need an enclosing instance and 305 tests fail, among them "
                     "TestCreators2::testJackson431 and MapDeserializationTest::testKeyWithCreator. ClassUtil.getOuterClass "
                     "returns the enclosing class of a non-static class, which is null for a top-level class, and "
                     "BeanDeserializerBase._resolveInnerClassValuedProperty uses it to find the one-argument constructor that "
                     "takes the single enclosing instance (TestInnerClass::testSimpleNonStaticInner); InnerClassCreatorTest::"
                     "testIssue1501 exercises the non-static inner class path of isNonStaticInnerClass. A one-line edit above the "
                     "gold that answers top-level classes itself (for example hop 4 testing ClassUtil.getEnclosingClass(type) == "
                     "null before asking the gold, hop 3 accepting such classes, or hop 4 calling ClassUtil.isNonStaticInnerClass "
                     "instead of the gold) passes the tests but is a second implementation of the gold's decision: for the trigger "
                     "input the gold's answer is never used, and the gold keeps counting an enclosing instance for a top-level "
                     "class. Making hop 4 report only counts above one also passes the tests but breaks hop 4's own documentation "
                     "and drops every member class that needs exactly one enclosing instance. isLocalType had no javadoc in the "
                     "original checkout; a one-sentence javadoc in ClassUtil's own wording is added so that the recipe's facade "
                     "sentence has a javadoc to be appended to.",
 "ownership_tests": ["com.fasterxml.jackson.databind.deser.creators.TestCreators2::testJackson431",
                     "com.fasterxml.jackson.databind.deser.jdk.MapDeserializationTest::testKeyWithCreator",
                     "com.fasterxml.jackson.databind.deser.creators.InnerClassCreatorTest::testIssue1501",
                     "com.fasterxml.jackson.databind.deser.TestInnerClass::testSimpleNonStaticInner"],
 "compensating": {
   "chain": [
     {"file": BDF, "old": "if (ObjectReader.countEnclosingInstances(type) == 0) {",
      "new": "if (ObjectReader.countEnclosingInstances(type) == 0 || type.isInterface()) {",
      "why": "hop 4 also reports interfaces as needing no enclosing instance"},
     {"file": BDB, "old": "if (ClassUtil.hasEnclosingMethod(type)) {",
      "new": "if (ClassUtil.hasEnclosingMethod(type) || type.isAnonymousClass()) {",
      "why": "hop 2 also reports anonymous classes as local/anonymous"},
     {"file": OM, "old": "if (allowNonStatic) {",
      "new": "if (allowNonStatic || type.isPrimitive()) {",
      "why": "hop 3 also accepts primitive types"},
   ],
 },
 "host_notes": "host_mode 1500 (six other public classes of at least 1500 lines). Hosts in draw order for seed 6621 (mr_lib preview, "
               "target com/fasterxml/jackson/databind/util/ClassUtil.java): DeserializationContext (hop 1, 1777 lines), "
               "deser.BeanDeserializerBase (hop 2, 1756), ObjectMapper (hop 3, 4211), deser.BasicDeserializerFactory (hop 4, "
               "2177), ObjectReader (hop 5, gold, 1949; drawn with the 'distinct from target package' constraint relaxed by the "
               "recipe because fewer than two other-package classes remained). Smallest host 1756 lines. Preview anchors: after "
               "reportInputMismatch (seed 6721), wrapAndThrow (6722), readerFor (6723), createTreeDeserializer (6724), with "
               "(6725). All five are public top-level classes in which a static method compiles (DeserializationContext, "
               "BeanDeserializerBase and BasicDeserializerFactory are abstract, which does not affect a static method); none was "
               "skipped. Every hop host already imports the next hop's package by wildcard (databind.deser.* or databind.*), and "
               "ObjectReader imports ClassUtil, so only the gold adds an import (java.lang.reflect.Modifier). The facade calls "
               "hop 1 by its fully-qualified name.",
}
