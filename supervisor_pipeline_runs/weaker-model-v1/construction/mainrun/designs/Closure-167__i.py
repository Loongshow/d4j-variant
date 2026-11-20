"""Main run Closure-167__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Closure-167; the real bug modified SemanticReverseAbstractInterpreter and JSType, the facade's class). No static pair (pool
v2: no_tested_static; B8 note section 1).

Facade: JSType.canTestForShallowEqualityWith(JSType) (allowed instance target of BATCH9_PREREGISTRATION.md row 318; facade_planned_by
null, no facade reuse). The other two allowed targets were not used. JSType.isNominalConstructor is reached by 137 tests (SymbolTable,
CheckAccessControls) and every one-line omission of its decisions was caught by 0 or by 7-13 tests (the native-constructor fallback: 7
tests; the source-link rule: 13; the interface test: 0). JSType.getTypesUnderShallowInequality: dropping the union-operand swap is
caught by no test, dropping the undefined/undefined case by three tests (and would leave null handled without its pair). For
canTestForShallowEqualityWith, dropping the empty-type rule is caught by 26 tests, dropping the rule that a function meet is
comparable by exactly one (TypeCheckTest::testComparison15; scratch experiments on a copy of the fixture, full suite each).
Original computation: if either type is empty (isEmptyType: no type, no object type, no resolved type or the least function type), the
two are comparable iff one is a subtype of the other; otherwise their greatest subtype (getGreatestSubtype, the meet) is computed and
the two are comparable iff the meet is not empty or the meet is the registry's LEAST_FUNCTION_TYPE (the registry field is read for
that native type).
The chain states the last rule without the registry: of the empty types only the least function type is a function type
(NoObjectType, NoType and NoResolvedType return null from toMaybeFunctionType, LEAST_FUNCTION_TYPE is a FunctionType), so "the meet is
a function type, or it is not empty" is the same decision as "the meet is not empty, or it is the least function type" (checked: the
original body with this rule in place of the registry comparison passes the full suite, 0 failing tests).

facade_variant: V2 (receiver as parameter). The computation needs the receiver's public methods (isEmptyType, isSubtype,
getGreatestSubtype); the facade passes `this` (typed JSType) and `that` to hop 1; the hops call public JSType methods only. The field
registry is no longer read (the function rule above needs no registry), so no V1 field is passed; no private method is called (no V4);
no package-private type is involved (no V3/V5). No signature, modifier (the method stays public final), override or throws change; no
new type; no reflection; no test edit.
state_passed: the receiver `this` (as JSType) and the argument `that` to hop 1; no field is read or written, no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Closure-167-probe of the fixture, the
first statement of each of the three allowed methods was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`;
defects4j compile OK; full suite (`defects4j test`): 214 failing tests, of which 35 fail with java.lang.IllegalStateException:
PROBE-REACHED at JSType.canTestForShallowEqualityWith(JSType.java:707), among them JSTypeTest::testNoType (direct call from the test)
and TypeCheckTest::testComparison15 (through TypeCheck.visitBinaryOperator, the SHEQ/SHNE branch); 137 reach isNominalConstructor
and 35 getTypesUnderShallowInequality. The facade is reached by existing tests, the trigger among them.

Hosts (host_mode = "1500"; `mr_lib.py preview Closure-167 src/com/google/javascript/rhino/jstype/JSType.java 5`, seed 6664, then
n = 12 for substitutes). The recipe's anchor picker accepts only 4-space-indented methods; in this 2-space code base every such
method is a member of a nested type, so the recipe places a hop inside a nested type unless the host has too few of them (then at the
end of the outer class). That is the recipe unchanged (the deviation disclosed in BATCH5_PREREGISTRATION.md); it makes a drawn host
unusable when the nested type at its recipe anchor cannot carry a static method that the previous hop can call. Draw order and
outcome (anchor seed = 6664 + 100 + hop index, as mr3_spec.py inserts them):
  NodeUtil (3222)        at hop 1: anchor in `static class MayBeStringResultPredicate` (package-private, jscomp): not visible from
                         the facade's package rhino.jstype -> unusable, skipped
  Node (2397)            at hop 1: anchor in `private static class IntPropListItem` -> not visible -> unusable, skipped
  CompilerOptions (2079) hop 1: anchor after `isOn` in `public static enum TweakProcessing` -> usable (public static nested type)
  JSTypeRegistry (1722)  hop 2: no 4-space method -> end of the outer class -> usable
  DefaultPassConfig (2314) at hop 3: anchor in `class GlobalTypeResolver` (inner, non-static, package-private): a static method does not
                         compile there and it is not visible from rhino -> unusable, skipped
  regex.RegExpTree (1859) at hop 3: anchor in `static final class DecomposedCharset` (package-private, jscomp.regex) -> not visible from
                         rhino.jstype -> unusable, skipped
  rhino.JSDocInfo (1508) hop 3: anchor after `getNameNode` in `public static final class Marker` -> usable
  jsonml.Reader (1565)   at hop 4: anchor in `private enum Type` -> not visible -> unusable, skipped
  SymbolTable (1611)     hop 4: anchor after `getTypeOfThis` in `public static final class SymbolScope` -> usable
  parsing.JsDocInfoParser (2364) at hop 5: anchor in `private static class ExtractionInfo` -> not visible -> unusable, skipped
  TypeCheck (1928)       hop 5 (GOLD): no 4-space method -> end of the outer class -> usable
  hop 1 CompilerOptions$TweakProcessing (file 2079 lines)  canCompareStrictly       pass-through
  hop 2 rhino.jstype.JSTypeRegistry     (file 1722 lines)  canTestStrictEquality    pass-through
  hop 3 rhino.JSDocInfo$Marker          (file 1508 lines)  mayBeStrictlyEqual       pass-through
  hop 4 SymbolTable$SymbolScope         (file 1611 lines)  allowsIdentityComparison pass-through
  hop 5 TypeCheck                       (file 1928 lines)  isStrictlyComparable     GOLD: the empty-type rule, the meet, and the
                                                                                    decision on the meet
Host file sizes 2079, 1722, 1508, 1611, 1928; the smallest host is JSDocInfo (1508 lines); the gold host has 1928 lines.

Fault (one-line omission of a special-case decision in the gold): the decision that a meet which is a function type leaves the two types
comparable is dropped, so two function types whose meet is the least function type (the bottom of the function lattice, which
getGreatestSubtype returns for distinct function types) are judged not comparable. The gold then reads as the ordinary routine "empty
types by the subtype relation, other types by whether their greatest subtype has values". Trigger: the EXISTING test
TypeCheckTest::testComparison15: `x.constructor === H` for x of type G (function (new:G, ...[?]): ? against function (new:H, number):
undefined; their meet is the least function type) now gets the warning "condition always evaluates to false" where the test expects no
warning. It is the only test that newly fails (the scratch full-suite run of the same omission in the original method: 1 failing test).

The gold's javadoc states the idiomatic contract (whether two types are meaningfully comparable with === and !==, the facade's own
wording) and is silent on function types; a constructor of G and a constructor of H can be the same function (H extends G), so `===`
between them is not determined in advance. The convention is pinned outside the gold: FunctionType.getGreatestSubtype (through
supAndInfHelper: two function types that are not equivalent meet in LEAST_FUNCTION_TYPE, "the bottom of the lattice", a function type)
with JSTypeTest::testFunctionTypeRelationships (functions that are subtypes of each other still have the least function type as their
meet); JSType.testForEquality, the == sibling, never decides a comparison of a function with an object (UNKNOWN), with
JSTypeTest::testTestForEquality and JSTypeTest::testFunctionType (assertCanTestForEqualityWith(functionType, functionType)).

Single owner: only the gold computes the meet and decides on it; hops 1-4 pass the two types along unchanged. Declared alternatives
(G9): hop 1 strips null and undefined from both types (as TypeCheck does before calling); hop 2 swaps the operands; hop 4 autoboxes both
types. Each leaves the trigger failing (the operands are non-nullable function types; the decision is symmetric).
Recorded bypasses (edits that answer the comparison for a class of pairs without the gold, so the gold's result is replaced by a second
implementation for those pairs; checked by emulation on the variant semantics in a scratch copy, full suite 0 failing tests):
 B-1 a related-types shortcut at any hop: `if (leftType.isSubtype(rightType) || rightType.isSubtype(leftType)) { return true; }`
     before the delegating call (the trigger's two constructor types are subtypes of each other, so the gold is never asked).
 B-2 a function-types shortcut at any hop: `if (leftType.isFunctionType() && rightType.isFunctionType()) { return true; }`.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims both types are first widened to their least supertype and the comparison is allowed unless that
supertype is the top type; the chain computes no supertype (it uses the greatest subtype) and tests no top type. It names neither
functions, the meet rule, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: leftType and rightType are each read by the empty test, the subtype test and the meet; neither is only argument-checked.
  T2 absent: meet is read by both decisions after it; no literal-initialised local; the empty-type branch returns the subtype result
     (not the fall-through value), the function branch returns true where the fall-through gives false for the least function type.
  T3 absent: the empty test and the subtype test treat both operands; the only per-meet treatment besides emptiness is the function
     type, one member of no set named by the gold's text; no enum, type code or named format member is left out.
  T4 absent: 'meaningfully comparable using the strict equality operators' is a general description that the returns address; the
     @param and @return clauses name no rule, limit or value class; the gold has no inline comment.
 Variant gold (javadoc, signature, `if (leftType.isEmptyType() || rightType.isEmptyType()) { return leftType.isSubtype(rightType) ||
 rightType.isSubtype(leftType); }`, `JSType meet = leftType.getGreatestSubtype(rightType);`, `return !meet.isEmptyType();`):
  T1 absent: leftType and rightType are read by the empty test, the subtype test and the meet, and decide the result.
  T2 absent: meet is read by the return; it is not literal-initialised; there is no loop, cursor, counter, flag or best-so-far; the
     single decision returns the subtype result, the fall-through the emptiness of the meet (different effects).
  T3 absent: both operands get the empty test and both subtype directions are tested; the meet gets one treatment (emptiness) and no
     sibling treatment exists for any member of a set ('No member handled'); the gold's text names no class (no "function", "finite",
     "native", "object") that it would handle in part.
  T4 absent: 'Tests whether two types are meaningfully comparable using the strict equality operators === and !==' is a general
     description (like 'the reduced fraction'); '@param leftType the type of the left operand', '@param rightType the type of the right
     operand' and '@return whether a strict comparison of the two types is meaningful' name no concrete rule, bound or value class; no
     inline comment; the identifiers leftType, rightType and meet name what they hold."""

JST = "src/com/google/javascript/rhino/jstype/JSType.java"
CO = "src/com/google/javascript/jscomp/CompilerOptions.java"
REG = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
JDI = "src/com/google/javascript/rhino/JSDocInfo.java"
ST = "src/com/google/javascript/jscomp/SymbolTable.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"

GOLD_TEXT = '''/**
 * Tests whether two types are meaningfully comparable using the strict
 * equality operators {@code ===} and {@code !==}.
 *
 * @param leftType the type of the left operand
 * @param rightType the type of the right operand
 * @return whether a strict comparison of the two types is meaningful
 */
public static boolean isStrictlyComparable(JSType leftType, JSType rightType) {
  if (leftType.isEmptyType() || rightType.isEmptyType()) {
    return leftType.isSubtype(rightType) || rightType.isSubtype(leftType);
  }
  JSType meet = leftType.getGreatestSubtype(rightType);
  if (meet.isFunctionType()) {
    return true;
  }
  return !meet.isEmptyType();
}'''

HOP1 = '''/**
 * Whether values of the two types can be meaningfully compared with
 * {@code ===} or {@code !==}.
 */
public static boolean canCompareStrictly(JSType leftType, JSType rightType) {
  return JSTypeRegistry.canTestStrictEquality(leftType, rightType);
}'''

HOP2 = '''/**
 * Tests whether two types are meaningfully comparable using strict
 * (shallow) equality.
 *
 * @param leftType the type of the left operand
 * @param rightType the type of the right operand
 */
public static boolean canTestStrictEquality(JSType leftType, JSType rightType) {
  return JSDocInfo.Marker.mayBeStrictlyEqual(leftType, rightType);
}'''

HOP3 = '''/**
 * Gets whether a strict equality test between values of the two
 * types is meaningful.
 */
public static boolean mayBeStrictlyEqual(JSType leftType, JSType rightType) {
  return SymbolTable.SymbolScope.allowsIdentityComparison(
      leftType, rightType);
}'''

HOP4 = '''/**
 * Returns whether the two types can be meaningfully compared with the
 * strict equality operators.
 */
public static boolean allowsIdentityComparison(
    JSType leftType, JSType rightType) {
  return TypeCheck.isStrictlyComparable(leftType, rightType);
}'''

DESIGN = {
 "instance": "Closure-167", "project": "Closure", "bug_id": 167, "seed": 6664,
 "src_root": "src", "test_root": "test",
 "facade": {"file": JST, "class": "com.google.javascript.rhino.jstype.JSType", "method": "canTestForShallowEqualityWith",
            "near_line": 705},
 "facade_variant": "V2",
 "state_passed": "the receiver this (as JSType) and the argument that, handed to hop 1; no field read or written, no write-back",
 "reachability_probe": "full suite with PROBE-REACHED as the first statement of the three allowed methods: 35 tests fail with "
                       "java.lang.IllegalStateException: PROBE-REACHED at JSType.canTestForShallowEqualityWith(JSType.java:707), "
                       "among them JSTypeTest::testNoType (direct) and TypeCheckTest::testComparison15 (through TypeCheck)",
 "host_mode": "1500",
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/TypeCheckTest.java",
             "test_class": "com.google.javascript.jscomp.TypeCheckTest", "test_method": "testComparison15"},
 "expected_signature": "condition always evaluates to false",
 "gold": {"method": "isStrictlyComparable", "text": GOLD_TEXT,
          "fault": {"old": "      JSType meet = leftType.getGreatestSubtype(rightType);\n"
                           "      if (meet.isFunctionType()) {\n"
                           "        return true;\n"
                           "      }\n",
                    "new": "      JSType meet = leftType.getGreatestSubtype(rightType);\n"}},
 "chain": {
   "facade_body": "return com.google.javascript.jscomp.CompilerOptions.TweakProcessing.canCompareStrictly(\n"
                  "        this, that);",
   "lie": "Both types are first widened to their least supertype, and the comparison is allowed unless that supertype is the "
          "top type.",
   "hops": [
     {"file": CO, "class": "com.google.javascript.jscomp.CompilerOptions$TweakProcessing", "method": "canCompareStrictly",
      "imports": ["com.google.javascript.rhino.jstype.JSType", "com.google.javascript.rhino.jstype.JSTypeRegistry"], "text": HOP1},
     {"file": REG, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "canTestStrictEquality",
      "imports": ["com.google.javascript.rhino.JSDocInfo"], "text": HOP2},
     {"file": JDI, "class": "com.google.javascript.rhino.JSDocInfo$Marker", "method": "mayBeStrictlyEqual",
      "imports": ["com.google.javascript.jscomp.SymbolTable", "com.google.javascript.rhino.jstype.JSType"], "text": HOP3},
     {"file": ST, "class": "com.google.javascript.jscomp.SymbolTable$SymbolScope", "method": "allowsIdentityComparison",
      "imports": [], "text": HOP4},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "isStrictlyComparable", "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.rhino.jstype.FunctionType::getGreatestSubtype",
              "com.google.javascript.rhino.jstype.FunctionType::supAndInfHelper",
              "com.google.javascript.rhino.jstype.JSType::testForEquality"],
 "ownership_reason": "Only the gold computes the greatest subtype (the meet) of the two types and decides on it; hops 1-4 pass the "
                     "two types along unchanged. The gold's javadoc promises whether the two types are meaningfully comparable with "
                     "=== and !==; for the constructor types of G and of H (H extends G, so x.constructor of a G may be H) the "
                     "comparison is not determined, yet the variant gold answers no because their meet, the least function type, is "
                     "empty. The convention that the least function type is the meet of distinct function types, even of functions "
                     "that are subtypes of each other, is pinned by FunctionType.getGreatestSubtype / supAndInfHelper ('the "
                     "LEAST_FUNCTION_TYPE type at the bottom of the lattice') and JSTypeTest testFunctionTypeRelationships; the == "
                     "sibling JSType.testForEquality never decides a comparison of a function with an object (JSTypeTest "
                     "testTestForEquality; testFunctionType asserts that a function type can be tested for equality with itself). "
                     "No change of the operands above the gold (stripping null and undefined, swapping, autoboxing) changes their "
                     "meet; a hop that answers related or function-typed pairs itself replaces the gold's decision for those pairs "
                     "(recorded as bypasses).",
 "ownership_tests": ["com.google.javascript.rhino.jstype.JSTypeTest::testFunctionTypeRelationships",
                     "com.google.javascript.rhino.jstype.JSTypeTest::testTestForEquality",
                     "com.google.javascript.rhino.jstype.JSTypeTest::testFunctionType"],
 "compensating": {
   "chain": [
     {"file": CO, "old": "  return JSTypeRegistry.canTestStrictEquality(leftType, rightType);",
      "new": "  return JSTypeRegistry.canTestStrictEquality(leftType.restrictByNotNullOrUndefined(), rightType.restrictByNotNullOrUndefined());",
      "why": "hop 1 strips null and undefined from both types before they are compared"},
     {"file": REG, "old": "  return JSDocInfo.Marker.mayBeStrictlyEqual(leftType, rightType);",
      "new": "  return JSDocInfo.Marker.mayBeStrictlyEqual(rightType, leftType);",
      "why": "hop 2 passes the operands in the other order"},
     {"file": ST, "old": "  return TypeCheck.isStrictlyComparable(leftType, rightType);",
      "new": "  return TypeCheck.isStrictlyComparable(leftType.autobox(), rightType.autobox());",
      "why": "hop 4 compares the object forms of the two types"},
   ],
 },
 "host_notes": "host_mode 1500. mr_lib.py preview Closure-167 src/com/google/javascript/rhino/jstype/JSType.java 5 (seed 6664) draws "
               "NodeUtil, Node, CompilerOptions, JSTypeRegistry, DefaultPassConfig; n=12 continues RegExpTree, JSDocInfo, Reader, "
               "SymbolTable, JsDocInfoParser, TypeCheck, Compiler. The recipe's anchor picker accepts only 4-space-indented methods, "
               "which in this 2-space code base are members of nested types, so a hop lands in the nested type at its anchor (or at "
               "the end of the outer class when the host has too few such methods). Taking the drawn hosts in order, a host is "
               "skipped when the nested type at its recipe anchor (seed 6664+100+hop index) cannot carry a static method callable "
               "from the previous hop: NodeUtil (package-private MayBeStringResultPredicate, not visible from rhino.jstype), Node "
               "(private IntPropListItem), DefaultPassConfig (inner non-static GlobalTypeResolver), RegExpTree (package-private "
               "DecomposedCharset in jscomp.regex), Reader (private enum Type), JsDocInfoParser (private ExtractionInfo). Used: hop 1 "
               "CompilerOptions (2079 lines; in public static enum TweakProcessing after isOn, seed 6764), hop 2 JSTypeRegistry "
               "(1722; end of class, seed 6765), hop 3 JSDocInfo (1508; in public static final class Marker after getNameNode, "
               "seed 6766), hop 4 SymbolTable (1611; in public static final class SymbolScope after getTypeOfThis, seed 6767), hop "
               "5 gold TypeCheck (1928; end of class, seed 6768). Smallest host JSDocInfo (1508). Hop classes of nested types are "
               "named with '$'. The facade calls hop 1 by its fully-qualified name; each hop imports the next host where needed.",
}
