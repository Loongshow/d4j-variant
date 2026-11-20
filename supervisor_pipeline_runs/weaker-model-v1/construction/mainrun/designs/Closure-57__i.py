"""Main run Closure-57__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Closure-57; the real bug modified ClosureCodingConvention, the facade's class). No static pair (B8 note section 1: pool v2
found no strictly tested public static method in the modified class).

Facade: ClosureCodingConvention.getAssertionFunctions() (the only allowed candidate of batch9_tasks.json; facade_planned_by = null, no
facade reuse). It overrides CodingConvention.getAssertionFunctions and had no javadoc of its own (only @Override); a javadoc in the
class's own voice ("Returns the assertion functions of Closure's goog.asserts namespace, each with the type that it asserts.") is added
by a behaviour-preserving pre-edit above the existing @Override, and the lie sentence is part of that javadoc. (The recipe's
rewrite_facade appends the lie only to a javadoc directly adjacent to the method header; with @Override in between it finds none, so
the pre-edit carries the lie sentence itself, word for word the chain's `lie`.)
Original computation of the facade: an ImmutableList of seven AssertionFunctionSpec values for Closure's goog.asserts namespace:
goog.asserts.assert (no asserted type: the argument is neither null nor undefined), assertNumber -> NUMBER_TYPE, assertString ->
STRING_TYPE, assertFunction -> FUNCTION_INSTANCE_TYPE, assertObject -> OBJECT_TYPE, assertArray -> ARRAY_TYPE and assertInstanceof ->
OBJECT_TYPE (the constructor argument is not modelled).

facade_variant: V0/V1 boundary, recorded as V1 (state as parameters) with no field state: the method reads no field and writes none
(task record: variant V0, fields_read and fields_written empty); the facade keeps only the method's own constants, the namespace
"goog.asserts" and the five native types of the type assertions, and passes them to hop 1 in ONE call; the chain computes the specs
and the facade returns hop 1's List (a Collection<AssertionFunctionSpec>). No receiver is needed (no V2), no private method is called
(no V4), no package-private type is involved (CodingConvention.AssertionFunctionSpec is a public member type of a public interface and
JSTypeNative a public enum; no V3/V5). No signature, modifier, override or throws change; no new type; no reflection; no visibility
change; no test edit.
state_passed: the facade's constants only (the String "goog.asserts" and the JSTypeNative values NUMBER_TYPE, STRING_TYPE,
FUNCTION_INSTANCE_TYPE, OBJECT_TYPE, ARRAY_TYPE) to hop 1; no field is read or written; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Closure-57-probe/w of the fixture,
the first statement of getAssertionFunctions was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j
compile OK. `defects4j test -t com.google.javascript.jscomp.TypeInferenceTest::testAssertFunction`: 1 failing test (the class:
java.lang.ExceptionInInitializerError, Caused by java.lang.IllegalStateException: PROBE-REACHED at
ClosureCodingConvention.getAssertionFunctions(ClosureCodingConvention.java:334) from TypeInferenceTest.<clinit>(TypeInferenceTest.java:62),
the static ASSERTION_FUNCTION_MAP initialiser). `defects4j test -t com.google.javascript.jscomp.ClosureCodeRemovalTest::testAssertionRemoval1`:
1 failing test, java.lang.IllegalStateException: PROBE-REACHED at ClosureCodingConvention.getAssertionFunctions(ClosureCodingConvention.java:334)
from ClosureCodeRemoval$FindAssertionCalls.<init>(ClosureCodeRemoval.java:166). The facade is reached by existing tests directly
(TypeInferenceTest) and through production code (ClosureCodeRemoval, TypeInferencePass).

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview Closure-57 com/google/javascript/jscomp/ClosureCodingConvention.java`, seed
8438; the draw excludes the facade file). The recipe's anchor scanner (host_search.pick_insertion_anchor) admits only methods whose
header is indented exactly four spaces; in Closure's two-space files those are members of NESTED types, so the seeded anchor puts the
hop inside a nested type there. A drawn host was taken as unusable (BUILD_BRIEF: "a static method there will not compile, or it cannot
see a needed type") when the hop, at the anchor the recipe draws for that hop position (seed 8438 + 100 + i), would not compile or not be
callable from the previous hop: inside a private nested type, inside a package-private nested type of another package than the caller,
or inside a non-static inner class. Draw order (n = 15 covers the whole usable pool of 11 public classes of >= 1500 lines) and outcome:
  draw 1  rhino/TokenStream.java (1714)               pos 1 anchor after getTokenno, outer class           -> hop 1
  draw 2  jscomp/jsonml/Reader.java (1556)            pos 2 anchor after getName, inside `private enum Type` -> unusable (not callable)
  draw 3  rhino/Node.java (2528)                      pos 2 anchor after setMutatesThis, inside `public static class SideEffectFlags`
                                                      -> hop 2 (class com.google.javascript.rhino.Node$SideEffectFlags)
  draw 4  jscomp/regex/RegExpTree.java (1858)         pos 3 anchor after children, inside package-private `static final class
                                                      CapturingGroup` (caller in package rhino) -> unusable
  draw 5  jscomp/parsing/JsDocInfoParser.java (2314)  pos 3 anchor after ExtractionInfo, inside `private static class ExtractionInfo`
                                                      -> unusable
  draw 6  rhino/Parser.java (2407)                    pos 3 anchor after initForUnitTest, outer class      -> hop 3
  draw 7  jscomp/DefaultPassConfig.java (2213)        pos 4 anchor after hotSwapScript, inside the package-private inner class
                                                      GlobalTypeResolver (caller in package rhino) -> unusable
  draw 8  rhino/jstype/JSTypeRegistry.java (1620)     pos 4 no admissible anchor (no four-space-indented interior method): the
                                                      recipe's fallback, before the class's final brace, outer class -> hop 4
  draw 9  jscomp/NodeUtil.java (3171)                 pos 5 anchor after apply, inside package-private `static class MatchNodeType`
                                                      (caller in package rhino.jstype) -> unusable
  draw 10 jscomp/Compiler.java (2096)                 pos 5 anchor after toString, inside `public static class CodeBuilder`
                                                      -> hop 5 = GOLD (class com.google.javascript.jscomp.Compiler$CodeBuilder)
  hop 1 TokenStream                 1714 lines  assertionFunctionsOf      aggregation: the plain assertion, the type assertions of hop 2,
                                                                         the instanceof assertion (asserts an object)
  hop 2 Node$SideEffectFlags        2528 lines  typeAssertionsOf          pass-through (varargs -> List)
  hop 3 Parser                      2407 lines  typeAssertionsFor         pass-through
  hop 4 JSTypeRegistry              1620 lines  assertionsForNativeTypes  fold: one type assertion per native type, in order
  hop 5 Compiler$CodeBuilder        2096 lines  assertionForType          GOLD: the name of the type assertion from the native type
                                                                         (constant name without _TYPE, an instance type named after
                                                                         its constructor, the first letter upper case) and the spec
Host newline counts (file sizes) 1714, 2528, 2407, 1620, 2096; the smallest host is JSTypeRegistry (1620 lines); the gold host file has
2096 lines. Covariates: host_mode 1500; two hops (hop 2, gold) sit in public static nested classes of the drawn files.
The correct configuration returns the original seven specs (in the order assert, the five typed assertions, assertInstanceof; every
consumer is order-insensitive: TypeInferencePass and TypeInferenceTest key a map by name, ClosureCodeRemoval a set): NUMBER_TYPE ->
"Number", STRING_TYPE -> "String", FUNCTION_INSTANCE_TYPE -> FUNCTION_INSTANCE -> "Function", OBJECT_TYPE -> "Object", ARRAY_TYPE ->
"Array", each with its own type.

Fault (one-line omission of a special-case step in the gold): the step that names an instance type after its constructor (drop the
"_INSTANCE" part of the constant's name) is dropped, so FUNCTION_INSTANCE_TYPE gives "goog.asserts.assertFunction_instance" and no spec
is named goog.asserts.assertFunction. The gold then reads as the ordinary routine "the constant's name without _TYPE, first letter upper
case, the rest lower case". Trigger: the EXISTING test TypeInferenceTest::testAssertFunction: the call goog.asserts.assertFunction(x) is
no longer an assertion function, x is not narrowed, and verifySubtypeOf("out2", FUNCTION_INSTANCE_TYPE) fails ("The type * of variable
out2 is not a subtype of Function."). It is the only test that newly fails: goog.asserts.assertFunction occurs in no other test (grep of
test/), TypeInferenceTest's other assertion tests use assert, assertNumber, assertString, assertObject, assertArray and
assertInstanceof, which keep their specs, and a spec with the extra name is harmless to every consumer.

The gold's javadoc states the idiomatic contract (the assertion function that asserts the given native type, named after the type, as
in assertNumber for the number type) and is silent on instance types; "assertFunction_instance" is not named after the function type,
which Closure names Function. The convention is pinned outside the gold: JSTypeRegistry.initializeBuiltInTypes builds the native
function type as the FunctionType named "Function" and JSTypeTest::testUniversalConstructorType (passing) asserts that the equivalent
U2U_CONSTRUCTOR_TYPE (JSTypeNative: "FUNCTION_INSTANCE_TYPE, // equivalent to U2U_CONSTRUCTOR_TYPE") prints and displays as "Function";
ClosureCodingConvention.isPropertyTestFunction names the Closure type predicates after the JavaScript types (goog.isString,
goog.isNumber, goog.isFunction, goog.isArray, goog.isObject); TypeInference.tightenTypesAfterAssertions looks a spec up by the callee's
exact qualified name; TypeInferenceTest::testAssertNumber, ::testAssertString and ::testAssertArray (passing) pin "assertX asserts the
type X" for the other types; the facade's new javadoc keeps "each with the type that it asserts".

Single owner: only the gold turns a native type into a function name; hop 4 folds over the types, hops 2-3 pass them along and hop 1
only adds the two assertions that are not type assertions. No one-line change above the gold makes the variant gold produce
assertFunction: the variant needs a constant named FUNCTION_TYPE, which JSTypeNative does not have (FUNCTION_FUNCTION_TYPE gives
"Function_function", U2U_CONSTRUCTOR_TYPE "U2u_constructor", U2U_FUNCTION_TYPE "U2u_function", FUNCTION_PROTOTYPE has no _TYPE and
throws). Declared alternatives (G9): the facade passes U2U_CONSTRUCTOR_TYPE (the equivalent type, displayed "Function"); hop 3 passes
U2U_FUNCTION_TYPE in place of the instance type; hop 4 hands the gold FUNCTION_FUNCTION_TYPE (the type built under the name
"Function"). Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-1 hop 1 adds a hand-built `new CodingConvention.AssertionFunctionSpec(namespace + ".assertFunction",
     JSTypeNative.FUNCTION_INSTANCE_TYPE)`: a second implementation of the gold's output for one type, beside the gold's
     "assertFunction_instance" (hop 1's javadoc then no longer holds: two assertions for the function type).
     Checked on the variant in a scratch copy: TypeInferenceTest::testAssertFunction passes (0 failing).
 B-2 hop 4 (or any caller) rewrites the name the gold returned, e.g. `.replace("_instance", "")` on getFunctionName(): string surgery
     on the gold's output; the gold still names the function after its constant.
 B-0 the facade's original body re-implements the whole list and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the list is built by walking the goog.asserts namespace of the Closure library externs and keeping each
function whose name starts with assert; the chain reads no externs and walks no namespace (it builds the specs from five native types and
two fixed assertions). It names neither the naming of the types, instance types, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: namespace is the prefix of the returned function name; type gives the name (type.name()) and is the spec's asserted type;
     the gold has no argument check.
  T2 absent: name is assigned from type.name(), reassigned by the _TYPE cut and the _INSTANCE cut and read into the returned name; no
     literal-initialised local, no loop; the one decision (endsWith "_INSTANCE") changes the name for the instance type.
  T3 absent: the single special treatment (an instance type) applies to one member of the JSTypeNative enum by an infix, and the gold's
     text names no class of types ("One member of a larger unnamed set"); no pair or range end.
  T4 absent: "named after the type, as in assertNumber for the number type" is met (NUMBER_TYPE -> assertNumber); the @param/@return
     clauses name no rule.
 Variant gold (javadoc, signature, `String name = type.name();`, `name = name.substring(0, name.lastIndexOf("_TYPE"));`, return of the
 spec named namespace + ".assert" + first letter + lower-cased rest, with type):
  T1 absent: namespace is the prefix of the returned name; type is read for its name and is the spec's asserted type; no argument check.
  T2 absent: name is initialised from type.name() (not a literal), reassigned once and read three times in the returned name; there is
     no loop, cursor, counter, flag or best-so-far; there is no branch, case or ternary at all.
  T3 absent: no member of any set gets an individual treatment ("No member handled": no JSTypeNative constant is tested by name or
     value); the gold's text names no class ("finite", "primitive", "instance", "object") that it would handle in part; no pair or
     range end is involved.
  T4 absent: "Gets the assertion function of a namespace that asserts the given native type" is a general description that the return
     statement addresses; "named after the type, as in assertNumber for the number type" is met for the case it names; "@param
     namespace the qualified name of the namespace", "@param type the asserted native type" and "@return the assertion function" name no
     concrete rule; no inline comment; the identifiers name and assertionForType name what they hold or do."""

CCC = "src/com/google/javascript/jscomp/ClosureCodingConvention.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
NODE = "src/com/google/javascript/rhino/Node.java"
PAR = "src/com/google/javascript/rhino/Parser.java"
REG = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
COMP = "src/com/google/javascript/jscomp/Compiler.java"

LIE = ("The list is built by walking the goog.asserts namespace of the Closure library externs and keeping each function whose name "
       "starts with assert.")

FACADE_HEADER_OLD = ("  @Override\n"
                     "  public Collection<AssertionFunctionSpec> getAssertionFunctions() {")
FACADE_HEADER_NEW = ("  /**\n"
                     "   * Returns the assertion functions of Closure's goog.asserts namespace,\n"
                     "   * each with the type that it asserts.\n"
                     "   * The list is built by walking the goog.asserts namespace of the Closure\n"
                     "   * library externs and keeping each function whose name starts with assert.\n"
                     "   */\n"
                     "  @Override\n"
                     "  public Collection<AssertionFunctionSpec> getAssertionFunctions() {")

GOLD_TEXT = '''/**
 * Gets the assertion function of a namespace that asserts the given
 * native type. The function is named after the type, as in
 * {@code assertNumber} for the number type.
 *
 * @param namespace the qualified name of the namespace
 * @param type the asserted native type
 * @return the assertion function
 */
public static CodingConvention.AssertionFunctionSpec assertionForType(
    String namespace, JSTypeNative type) {
  String name = type.name();
  name = name.substring(0, name.lastIndexOf("_TYPE"));
  if (name.endsWith("_INSTANCE")) {
    name = name.substring(0, name.length() - "_INSTANCE".length());
  }
  return new CodingConvention.AssertionFunctionSpec(namespace + ".assert"
      + name.charAt(0) + name.substring(1).toLowerCase(), type);
}'''

HOP1 = '''/**
 * Gets the assertion functions of a namespace: the plain assertion,
 * which asserts no type, one assertion for each of the given native
 * types, and the instanceof assertion, which asserts an object.
 *
 * @param namespace the qualified name of the namespace
 * @param types the native types of the type assertions
 * @return the assertion functions of the namespace
 */
public static List<CodingConvention.AssertionFunctionSpec> assertionFunctionsOf(
    String namespace, JSTypeNative... types)
{
    return ImmutableList.<CodingConvention.AssertionFunctionSpec>builder()
        .add(new CodingConvention.AssertionFunctionSpec(namespace + ".assert"))
        .addAll(Node.SideEffectFlags.typeAssertionsOf(namespace, types))
        .add(new CodingConvention.AssertionFunctionSpec(
            namespace + ".assertInstanceof", JSTypeNative.OBJECT_TYPE))
        .build();
}'''

HOP2 = '''/**
 * Gets the type assertions of a namespace, one for each of the given
 * native types.
 *
 * @param namespace the qualified name of the namespace
 * @param types the asserted native types
 * @return the type assertions
 */
public static List<CodingConvention.AssertionFunctionSpec> typeAssertionsOf(
    String namespace, JSTypeNative... types) {
  return Parser.typeAssertionsFor(namespace, Arrays.asList(types));
}'''

HOP3 = '''/**
 * Gets the type assertions of a namespace for the given native types.
 *
 * @param namespace the qualified name of the namespace
 * @param types the asserted native types
 * @return the type assertions
 */
public static List<CodingConvention.AssertionFunctionSpec> typeAssertionsFor(
    String namespace, List<JSTypeNative> types)
{
    return JSTypeRegistry.assertionsForNativeTypes(namespace, types);
}'''

HOP4 = '''/**
 * Gets the assertion functions of a namespace that assert the given
 * native types, in the order of the types.
 *
 * @param namespace the qualified name of the namespace
 * @param types the asserted native types
 * @return one assertion function for each type
 */
public static List<CodingConvention.AssertionFunctionSpec> assertionsForNativeTypes(
    String namespace, List<JSTypeNative> types) {
  List<CodingConvention.AssertionFunctionSpec> assertions =
      Lists.newArrayList();
  for (JSTypeNative type : types) {
    assertions.add(Compiler.CodeBuilder.assertionForType(namespace, type));
  }
  return assertions;
}'''

DESIGN = {
 "instance": "Closure-57", "project": "Closure", "bug_id": 57, "seed": 8438,
 "src_root": "src", "test_root": "test",
 "facade": {"file": CCC, "class": "com.google.javascript.jscomp.ClosureCodingConvention", "method": "getAssertionFunctions",
            "near_line": 339},
 "facade_variant": "V1",
 "state_passed": "no field state (the method reads and writes no field; task record variant V0): the facade passes its own constants, "
                 "the namespace \"goog.asserts\" and the native types NUMBER_TYPE, STRING_TYPE, FUNCTION_INSTANCE_TYPE, OBJECT_TYPE, "
                 "ARRAY_TYPE, to hop 1 and returns hop 1's list; no write-back",
 "reachability_probe": "TypeInferenceTest::testAssertFunction fails (class initialiser) with Caused by java.lang.IllegalStateException: "
                       "PROBE-REACHED at ClosureCodingConvention.getAssertionFunctions(ClosureCodingConvention.java:334) from "
                       "TypeInferenceTest.<clinit>(TypeInferenceTest.java:62); ClosureCodeRemovalTest::testAssertionRemoval1 fails with "
                       "java.lang.IllegalStateException: PROBE-REACHED at ClosureCodingConvention.getAssertionFunctions(...:334) from "
                       "ClosureCodeRemoval$FindAssertionCalls.<init>(ClosureCodeRemoval.java:166)",
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/TypeInferenceTest.java",
             "test_class": "com.google.javascript.jscomp.TypeInferenceTest", "test_method": "testAssertFunction"},
 "expected_signature": "of variable out2 is not a subtype of Function",
 "gold": {"method": "assertionForType", "text": GOLD_TEXT,
          "fault": {"old": "      name = name.substring(0, name.lastIndexOf(\"_TYPE\"));\n"
                           "      if (name.endsWith(\"_INSTANCE\")) {\n"
                           "        name = name.substring(0, name.length() - \"_INSTANCE\".length());\n"
                           "      }\n",
                    "new": "      name = name.substring(0, name.lastIndexOf(\"_TYPE\"));\n"}},
 "pre_edits": {"chain": [{"file": CCC, "old": FACADE_HEADER_OLD, "new": FACADE_HEADER_NEW}]},
 "chain": {
   "facade_body": "return com.google.javascript.rhino.TokenStream.assertionFunctionsOf(\"goog.asserts\",\n"
                  "            JSTypeNative.NUMBER_TYPE, JSTypeNative.STRING_TYPE,\n"
                  "            JSTypeNative.FUNCTION_INSTANCE_TYPE, JSTypeNative.OBJECT_TYPE,\n"
                  "            JSTypeNative.ARRAY_TYPE);",
   "lie": LIE,
   "hops": [
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "assertionFunctionsOf",
      "imports": ["com.google.common.collect.ImmutableList", "com.google.javascript.jscomp.CodingConvention",
                  "com.google.javascript.rhino.jstype.JSTypeNative", "java.util.List"], "text": HOP1},
     {"file": NODE, "class": "com.google.javascript.rhino.Node$SideEffectFlags", "method": "typeAssertionsOf",
      "imports": ["com.google.javascript.jscomp.CodingConvention", "com.google.javascript.rhino.jstype.JSTypeNative",
                  "java.util.List"], "text": HOP2},
     {"file": PAR, "class": "com.google.javascript.rhino.Parser", "method": "typeAssertionsFor",
      "imports": ["com.google.javascript.jscomp.CodingConvention", "com.google.javascript.rhino.jstype.JSTypeNative",
                  "com.google.javascript.rhino.jstype.JSTypeRegistry"], "text": HOP3},
     {"file": REG, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "assertionsForNativeTypes",
      "imports": ["com.google.common.collect.Lists", "com.google.javascript.jscomp.CodingConvention",
                  "com.google.javascript.jscomp.Compiler"], "text": HOP4},
     {"file": COMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "assertionForType",
      "imports": ["com.google.javascript.rhino.jstype.JSTypeNative"], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.rhino.jstype.JSTypeRegistry::initializeBuiltInTypes",
              "com.google.javascript.jscomp.ClosureCodingConvention::isPropertyTestFunction",
              "com.google.javascript.jscomp.TypeInference::tightenTypesAfterAssertions"],
 "ownership_reason": "Only the gold turns a native type into the name of its assertion function; hop 4 folds over the types, hops 2 "
                     "and 3 pass them along and hop 1 only adds the plain and the instanceof assertion, which are not type "
                     "assertions. The gold's javadoc promises the assertion function named after the type, as in assertNumber for "
                     "the number type; for the native function type the variant gold returns goog.asserts.assertFunction_instance, "
                     "which is not named after the function type: Closure names that type Function (JSTypeRegistry."
                     "initializeBuiltInTypes builds it as the FunctionType named \"Function\"; JSTypeTest testUniversalConstructorType "
                     "asserts that the equivalent U2U_CONSTRUCTOR_TYPE prints and displays as \"Function\"), and Closure names its "
                     "type predicates after the JavaScript types (ClosureCodingConvention.isPropertyTestFunction: goog.isString, "
                     "goog.isNumber, goog.isFunction, goog.isArray, goog.isObject). TypeInference.tightenTypesAfterAssertions finds a "
                     "spec only by the callee's exact qualified name, so goog.asserts.assertFunction(x) narrows nothing. No one-line "
                     "change above the gold restores the name: the variant gold would need a JSTypeNative constant named "
                     "FUNCTION_TYPE, which does not exist (FUNCTION_FUNCTION_TYPE, U2U_CONSTRUCTOR_TYPE and U2U_FUNCTION_TYPE give "
                     "other names, FUNCTION_PROTOTYPE throws). TypeInferenceTest testAssertNumber, testAssertString and "
                     "testAssertArray pin the naming convention for the other types.",
 "ownership_tests": ["com.google.javascript.jscomp.TypeInferenceTest::testAssertNumber",
                     "com.google.javascript.jscomp.TypeInferenceTest::testAssertString",
                     "com.google.javascript.jscomp.TypeInferenceTest::testAssertArray",
                     "com.google.javascript.rhino.jstype.JSTypeTest::testUniversalConstructorType"],
 "compensating": {
   "chain": [
     {"file": CCC, "old": "            JSTypeNative.FUNCTION_INSTANCE_TYPE, JSTypeNative.OBJECT_TYPE,",
      "new": "            JSTypeNative.U2U_CONSTRUCTOR_TYPE, JSTypeNative.OBJECT_TYPE,",
      "why": "the facade passes the equivalent universal constructor type, which Closure displays as Function"},
     {"file": PAR, "old": "        return JSTypeRegistry.assertionsForNativeTypes(namespace, types);",
      "new": "        return JSTypeRegistry.assertionsForNativeTypes(namespace, com.google.common.collect.Lists.transform(types, new com.google.common.base.Function<JSTypeNative, JSTypeNative>() { public JSTypeNative apply(JSTypeNative t) { return t == JSTypeNative.FUNCTION_INSTANCE_TYPE ? JSTypeNative.U2U_FUNCTION_TYPE : t; } }));",
      "why": "hop 3 passes the plain function type in place of the function instance type"},
     {"file": REG, "old": "        assertions.add(Compiler.CodeBuilder.assertionForType(namespace, type));",
      "new": "        assertions.add(Compiler.CodeBuilder.assertionForType(namespace, type == JSTypeNative.FUNCTION_INSTANCE_TYPE ? JSTypeNative.FUNCTION_FUNCTION_TYPE : type));",
      "why": "hop 4 hands the gold the native type that is built under the name Function"},
   ],
 },
 "host_notes": "host_mode 1500. mr_lib.py preview Closure-57 com/google/javascript/jscomp/ClosureCodingConvention.java with n = 15 "
               "(the whole usable pool of 11 public classes of >= 1500 lines), seed 8438; hosts taken in draw order, a drawn host "
               "skipped only when the hop, at the anchor the recipe draws for that hop position (seed 8438 + 100 + i), would not "
               "compile or not be callable from the previous hop. The recipe's anchor scanner admits only four-space-indented "
               "method headers, which in Closure's two-space files are members of nested types. Draw 1 TokenStream (1714 lines): hop "
               "1, after getTokenno (outer class). Draw 2 jsonml.Reader: anchor inside `private enum Type` -> unusable. Draw 3 Node "
               "(2528): hop 2, after setMutatesThis inside `public static class SideEffectFlags` (class Node$SideEffectFlags). Draw 4 "
               "regex.RegExpTree: anchor inside the package-private `static final class CapturingGroup`, not callable from package "
               "rhino -> unusable. Draw 5 parsing.JsDocInfoParser: anchor inside `private static class ExtractionInfo` -> unusable. "
               "Draw 6 Parser (2407): hop 3, after initForUnitTest (outer class). Draw 7 DefaultPassConfig: anchor inside the "
               "package-private inner class GlobalTypeResolver -> unusable. Draw 8 jstype.JSTypeRegistry (1620): hop 4, no "
               "admissible anchor, the recipe's fallback before the class's final brace (outer class). Draw 9 NodeUtil: anchor inside "
               "the package-private `static class MatchNodeType`, not callable from package rhino.jstype -> unusable. Draw 10 "
               "Compiler (2096): hop 5 = gold, after toString inside `public static class CodeBuilder` (class Compiler$CodeBuilder). "
               "The facade calls hop 1 by its fully-qualified name; TokenStream imports java.io.Reader, so no host type named Reader "
               "is imported anywhere. Smallest host JSTypeRegistry (1620 lines).",
}
