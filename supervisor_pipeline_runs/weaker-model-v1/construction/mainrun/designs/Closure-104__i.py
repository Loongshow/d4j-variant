"""Main run Closure-104__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout
of Defects4J Closure-104; the real bug modified com.google.javascript.rhino.jstype.UnionType, the facade's class). No static pair
(B8 note section 1: pool v2 found no tested static method in UnionType); facade_planned_by is null for all three allowed candidates,
so the facade is distinct (no reuse).

Facade: UnionType.matchesNumberContext() (instance method, @Override of JSType.matchesNumberContext; allowed targets
UnionType.matchesNumberContext / matchesStringContext / matchesObjectContext, BATCH9_PREREGISTRATION.md rank 311).
Why this candidate (reachability probe below, run on all three): matchesStringContext is reached by NO existing test (full suite with
the probe: no PROBE-REACHED failure), so it cannot carry a trigger. matchesObjectContext is reached only through
TypeValidator.expectIndexMatch on nullable array types (Array|null, Array.<T>|null); every reaching test needs the union to match (an
object alternate) and none distinguishes one array alternate from another, so no one-line omission is caught by exactly one test.
matchesNumberContext is reached by three tests, and exactly one of them depends on the result: testNumericComparison4 ((number|undefined)
on the left of `a < 3` goes to TypeValidator.expectNumber); in testStringComparison2 ((Object|null) < 'x') and testStringComparison4
((string|undefined) < 'x') TypeCheck falls back to expectString/expectNotVoid when the union does not match a numeric context, and both
pass that way too.
Original computation: the union matches a numeric context if one of its alternates does (`for (JSType t : alternates) if
(t.matchesNumberContext()) return true; return false;`), each alternate answering through its own override: number, boolean, string
and null match; undefined (VoidType) does not; an object type matches if it is the Number, Boolean or String object type or Date, or
overrides valueOf (PrototypeObjectType); an enum element answers for its primitive type; unknown and the empty types match.

facade_variant: V1 (state as parameters). state_passed: the package-private field `alternates` (Set<JSType>), read inside UnionType and
handed to hop 1 as an Iterable<JSType>; no field is written, no write-back. The original has no argument guard (no parameters); the
facade body is the single call to hop 1 (by its fully-qualified name, rhino.Node is not imported in UnionType). No private method of
UnionType is called (no V4), the chain uses only public JSType/ObjectType API (no V2/V3/V5). No visibility is widened, no type is
added, no signature, modifier, override or throws clause changes, no reflection, no test edit.

reachability_probe (addendum section 4): in scratch copies /private/tmp/d4j-mi-Closure-104-probe{Number,String,Object} of the fixture,
the first statement of the candidate was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
full suite (defects4j test): matchesNumberContext -> 3 failing tests, all java.lang.IllegalStateException: PROBE-REACHED at
UnionType.matchesNumberContext(UnionType.java:104): TypeCheckTest::testNumericComparison4 (via TypeValidator.expectNumber,
TypeValidator.java:189, from TypeCheck.visit:620), TypeCheckTest::testStringComparison2 and ::testStringComparison4 (via
TypeCheck.visit:625); matchesObjectContext -> only TypeCheckTest tests via TypeValidator.expectIndexMatch; matchesStringContext -> none.
The facade is reached by the trigger through production code (TypeCheck -> TypeValidator.expectNumber -> union.matchesNumberContext()).

Redistribution of the computation: the per-alternate core (whether one alternate can appear in a numeric context) is in the gold, which
judges each alternate by an object type: an object alternate by itself, a primitive alternate by the object type it is autoboxed to
(number -> Number, string -> String, boolean -> Boolean; JSType.autoboxesTo), with the object type's own matchesNumberContext (the
PrototypeObjectType rule: wrapper objects, Date, valueOf); an alternate with no object type (undefined; also the all type) does not
count. The null type has no object type but converts to zero; it is decided by hop 2 (a placement step: the union matches if one
alternate is the null type), which passes every other alternate on unchanged. Hops 1, 3, 4 are pass-throughs. The correct chain returns
the original result for every alternate kind: number/string/boolean via their wrappers (true), null at hop 2 (true), undefined and the
all type (no object type: false), object types, enum elements (ObjectType; they delegate to their primitive type), unknown and the empty
types (ObjectType) through their own override.

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview Closure-104 com/google/javascript/rhino/jstype/UnionType.java`, instance seed
6296; UnionType.java, the only allowed-candidate file, is excluded by the draw). Draw order with n=8 (the >= 1500-line pool then has no
host left): 1 jscomp.NodeUtil, 2 rhino.TokenStream, 3 rhino.Parser, 4 jscomp.DefaultPassConfig, 5 jscomp.TypeCheck, 6
jscomp.parsing.JsDocInfoParser, 7 rhino.Node, 8 jscomp.Compiler. Each hop is inserted by the recipe (stageB_lib.insert_hop) after the
seeded anchor (seed 6296 + 100 + hop index). Usability was checked in scratch with exactly that insertion and a call from UnionType
(defects4j compile, /private/tmp/d4j-mi-Closure-104-hostprobe*):
  - NodeUtil at hop-1 seed 6396: anchor `apply` (line 1740) is a method of the PRIVATE nested class NodeUtil.MatchNameNode, so the hop
    lands inside it: `NodeUtil.x(..)` -> "cannot find symbol ... location: class NodeUtil"; `NodeUtil.MatchNameNode.x(..)` ->
    "MatchNameNode has private access in NodeUtil". Unusable.
  - DefaultPassConfig at hop-4 seed 6399: anchor `process` (line 1791) is in the PRIVATE nested class ErrorPass: "cannot find symbol
    ... location: class DefaultPassConfig" / "ErrorPass has private access in DefaultPassConfig". Unusable.
  - JsDocInfoParser (next drawn host, n=6) at seed 6396 (anchor `ExtractionInfo`) and at seed 6399 (anchor `getString`): both inside
    the PRIVATE nested class ExtractionInfo: "ExtractionInfo has private access in JsDocInfoParser" (twice). Unusable at either
    position.
  - Node (n=7) at seed 6396: anchor `getLastChild`, a top-level member: compiles. Compiler (n=8) at seed 6399: anchor `getLength`, a
    member of the PUBLIC static nested class Compiler.CodeBuilder: the hop is a public static method of Compiler.CodeBuilder, callable
    as `Compiler.CodeBuilder.x(..)`; compiles.
So, in hop order, hop 1 takes the next usable drawn host (Node; JsDocInfoParser is skipped as unusable) and hop 4 the next usable drawn
host after that (Compiler, in its nested CodeBuilder). Hosts 2, 3, 5 are the draw's own.
  hop 1 rhino.Node                      2060 lines  mayBeNumericType      pass-through
  hop 2 rhino.TokenStream               1696 lines  isNumberConvertible   placement: the null type decides (null converts to zero);
                                                                          every other alternate is passed on unchanged
  hop 3 rhino.Parser                    2438 lines  allowsNumericOperand  pass-through
  hop 4 jscomp.Compiler (CodeBuilder)   1670 lines  numericOperandAllowed pass-through
  hop 5 jscomp.TypeCheck                1715 lines  hasNumericAlternate   GOLD: one pass over the alternates deciding, per alternate,
                                                                          whether its object type (itself or the type it is autoboxed
                                                                          to) can appear in a numeric context
Host sizes 2060, 1696, 2438, 1670, 1715 (all in the >= 1500-line pool); the smallest host is Compiler (1670 lines); the gold host
TypeCheck (the drawn fifth host) has 1715 lines. Hop bodies follow each host's indentation step (4 spaces in the rhino files Node,
TokenStream, Parser; 2 spaces in Compiler and TypeCheck); the recipe adds its fixed 4-space base indent, which in Compiler is the member
indent of CodeBuilder.

Lie placement: the facade carries an @Override annotation between its javadoc and its header, so the recipe's javadoc lookup
(extract_transform.find_javadoc_start: the javadoc must be immediately adjacent to the header) finds none and appends nothing; the lie
sentence (the design's `lie`) is therefore inserted by a comment-only pre-edit at the end of the javadoc's description paragraph,
in the javadoc's own voice. No code changes; the annotation stays.

Fault (one-step omission in the gold): the autoboxing step for an alternate that is not itself an object type is dropped (the three
lines `if (objectType == null) { objectType = ObjectType.cast(type.autoboxesTo()); }` are removed), so a primitive alternate (number,
string, boolean) has no object type and never counts. The gold then reads as the ordinary routine "an alternate counts if its object
type can appear in a numeric context". Trigger: the EXISTING test TypeCheckTest::testNumericComparison4 (`/**@param {(number,undefined)}
a*/ function f(a) {return a < 3;}`): the union (number|undefined) no longer matches a numeric context, TypeValidator.expectNumber reports
"left side of numeric comparison / found: (number|undefined) / required: number", and testTypes fails with "unexpected warnings(s)". It
is the only test whose result depends on the facade (probe above); testStringComparison2 ((Object|null): hop 2 decides, true as before)
and testStringComparison4 ((string|undefined): false in the variant, TypeCheck then checks the string context, which passes) still pass;
gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (whether a value of one of the types can appear in a numeric context, such as an operand
of a multiply operator; its caller precondition: the null type is not among the types) and is silent on how a primitive is judged. A
number plainly can appear in a numeric context, so the variant's answer for (number) violates the contract on the trigger input. The
convention is pinned outside the gold: JSType.dereference ("Autoboxes the type") and JSType.findPropertyType ("Coerces this type to an
Object type": ObjectType.cast(autoboxesTo())) judge a primitive by the object type it is autoboxed to; NumberType.matchesNumberContext
(true) and PrototypeObjectType.matchesNumberContext (true for the Number/Boolean/String object types) give the answers the autoboxed
judgement reproduces; passing tests JSTypeTest::testNumberValueType, ::testNumberObjectType, ::testStringValueType,
::testBooleanValueType (each asserts matchesNumberContext of the primitive and of its wrapper object) and TypeCheckTest::
testStringComparison2 (through the chain: the null alternate counts at hop 2).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: types is the loop source; each element is read by toObjectType/autoboxesTo and decides the return.
  T2 absent: type is the loop variable; objectType is read by the condition that returns true; `if (objectType == null)` assigns it
     (live: a primitive gains its wrapper); the final condition has two outcomes (return true / continue); nothing is frozen.
  T3 absent: no enumeration of type kinds; object and non-object alternates are both handled (by themselves / by their autoboxed type);
     the null type is excluded by a caller precondition (not handled at all, not in part).
  T4 absent: 'can appear in a numeric context, such as an operand of a multiply operator' is a general description met by the loop;
     'none of which is the null type' is a caller precondition; identifiers (types, type, objectType) name nothing the body does not do.
 Variant gold (javadoc, signature, `for (JSType type : types)`, `ObjectType objectType = type.toObjectType();`, `if (objectType != null
 && objectType.matchesNumberContext()) return true;`, `return false;`):
  T1 absent: types supplies every element; each element's object type decides the result.
  T2 absent: type is the loop variable; objectType is read by the returning condition; the condition has two different effects; no
     local is dead or frozen (objectType is computed fresh per element, not a literal).
  T3 absent: the gold treats no member of any closed set specially: it has no per-kind branches (number/string/boolean/undefined are
     not named or handled individually: 'No member handled'); the only text naming a type kind is the caller precondition on the null
     type, which the gold does not handle at all.
  T4 absent: no phrase names a concrete rule, bound or value class the body visibly fails: 'can appear in a numeric context' is the
     general description (the body addresses it through matchesNumberContext); 'none of which is the null type' is a caller
     precondition; no inline comment; identifiers name nothing unmet.

Single owner: only the gold decides whether a non-null alternate counts; hops 1, 3 and 4 pass the alternates along unchanged, and hop 2
decides only the null type (documented: every other alternate is passed on unchanged and judged by the next step). Once the gold judges
the number alternate as having no object type, the union (number|undefined) can match only if a caller decides a non-null primitive
itself or replaces the gold. Declared alternatives (G9): hop 2 also counts the unknown type; hop 2 also counts the empty types; hop 4
counts an empty set of alternates. None makes the trigger pass.
Recorded bypasses (each breaks a hop's documented rule or discards the gold):
 B-0 the facade (its original body) answers the alternates through their own overrides, discarding the chain including the gold.
 B-1 hop 2 widens its null test to every alternate that is not an object type and not the void type (`type.isNullType()` ->
     `type.isNullType() || (type.toObjectType() == null && !type.isVoidType())`): a second implementation of the gold's decision for
     primitives, against hop 2's documented rule that only the null type is decided there.
 B-2 hop 2 also counts the number type (`|| type.isNumberValueType()` / `|| type.isNumber()`) or the void type (`|| type.isVoidType()`):
     passes the suite only because no test asks the numeric context of a union such as (string|undefined) or (Function|undefined) with
     an expectation; it breaks hop 2's documented rule, leaves the string and boolean alternates uncounted (the gold's contract still
     fails for them) and, for the void type, the facade's pinned convention (VoidType.matchesNumberContext is false,
     JSTypeTest::testVoidType).

Lie: the facade's javadoc claims the alternates are first joined into their least supertype and the predicate is then answered for that
single type; no step of the chain computes a supertype (each step reads the alternates one by one). It names no type kind, no
conversion and no hop."""

UT = "src/com/google/javascript/rhino/jstype/UnionType.java"
ND = "src/com/google/javascript/rhino/Node.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
PA = "src/com/google/javascript/rhino/Parser.java"
CO = "src/com/google/javascript/jscomp/Compiler.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"

GOLD_TEXT = '''/**
 * Returns whether a value of one of the given types can appear in a
 * numeric context, such as an operand of a multiply operator.
 *
 * @param types the types to examine, none of which is the null type
 * @return whether a value of one of the types can appear in a numeric
 *     context
 */
public static boolean hasNumericAlternate(Iterable<JSType> types) {
  for (JSType type : types) {
    ObjectType objectType = type.toObjectType();
    if (objectType == null) {
      objectType = ObjectType.cast(type.autoboxesTo());
    }
    if (objectType != null && objectType.matchesNumberContext()) {
      return true;
    }
  }
  return false;
}'''

HOP1 = '''/**
 * Returns whether a value of one of the given types may be used as the
 * operand of a numeric operator.
 *
 * @param types the alternate types of a union
 * @return whether one of the types may be used as a numeric operand
 */
public static boolean mayBeNumericType(Iterable<JSType> types) {
    return TokenStream.isNumberConvertible(types);
}'''

HOP2 = '''/**
 * Returns whether a value of one of the given types can be converted to a
 * number.
 *
 * <p>A null value converts to zero, so the types can be converted if one of
 * them is the null type. Every other type is passed on unchanged and judged
 * one by one.</p>
 *
 * @param types the types to examine
 * @return whether a value of one of the types can be converted to a number
 */
public static boolean isNumberConvertible(Iterable<JSType> types) {
    for (JSType type : types) {
        if (type.isNullType()) {
            return true;
        }
    }
    return Parser.allowsNumericOperand(types);
}'''

HOP3 = '''/**
 * Returns whether a value of one of the given types is allowed as the
 * operand of a numeric operator.
 *
 * @param types the types to examine, none of which is the null type
 * @return whether one of the types is allowed as a numeric operand
 */
public static boolean allowsNumericOperand(Iterable<JSType> types) {
    return Compiler.CodeBuilder.numericOperandAllowed(types);
}'''

HOP4 = '''/**
 * Returns whether a value of one of the given types is allowed as the
 * operand of a numeric operator.
 *
 * @param types the types to examine, none of which is the null type
 * @return whether one of the types is allowed as a numeric operand
 */
public static boolean numericOperandAllowed(Iterable<JSType> types) {
  return TypeCheck.hasNumericAlternate(types);
}'''

DESIGN = {
 "instance": "Closure-104", "project": "Closure", "bug_id": 104, "seed": 6296,
 "src_root": "src", "test_root": "test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the package-private field alternates (Set<JSType>), passed to hop 1 as an Iterable<JSType>; no write-back",
 "host_mode": "1500", "host_lines": [2060, 1696, 2438, 1670, 1715],
 "reachability_probe": "matchesNumberContext first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Closure-104-probeNumber: full suite 3 failing tests, all PROBE-REACHED at "
                       "UnionType.matchesNumberContext(UnionType.java:104): TypeCheckTest::testNumericComparison4 (via "
                       "TypeValidator.expectNumber), ::testStringComparison2, ::testStringComparison4; matchesObjectContext: only "
                       "TypeCheckTest tests via TypeValidator.expectIndexMatch; matchesStringContext: none",
 "facade": {"file": UT, "class": "com.google.javascript.rhino.jstype.UnionType", "method": "matchesNumberContext", "near_line": 103},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/TypeCheckTest.java",
             "test_class": "com.google.javascript.jscomp.TypeCheckTest", "test_method": "testNumericComparison4"},
 "expected_signature": "left side of numeric comparison",
 "gold": {"method": "hasNumericAlternate", "text": GOLD_TEXT,
          "fault": {"old": "        ObjectType objectType = type.toObjectType();\n"
                           "        if (objectType == null) {\n"
                           "          objectType = ObjectType.cast(type.autoboxesTo());\n"
                           "        }\n"
                           "        if (objectType != null && objectType.matchesNumberContext()) {",
                    "new": "        ObjectType objectType = type.toObjectType();\n"
                           "        if (objectType != null && objectType.matchesNumberContext()) {"}},
 "chain": {
   "facade_body": "return com.google.javascript.rhino.Node.mayBeNumericType(alternates);",
   "lie": "The alternates are first joined into their least supertype, and the predicate is then answered for that single type.",
   "hops": [
     {"file": ND, "class": "com.google.javascript.rhino.Node", "method": "mayBeNumericType",
      "imports": [], "text": HOP1},
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "isNumberConvertible",
      "imports": ["com.google.javascript.rhino.jstype.JSType"], "text": HOP2},
     {"file": PA, "class": "com.google.javascript.rhino.Parser", "method": "allowsNumericOperand",
      "imports": ["com.google.javascript.rhino.jstype.JSType", "com.google.javascript.jscomp.Compiler"], "text": HOP3},
     {"file": CO, "class": "com.google.javascript.jscomp.Compiler.CodeBuilder", "method": "numericOperandAllowed",
      "imports": ["com.google.javascript.rhino.jstype.JSType"], "text": HOP4},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "hasNumericAlternate",
      "imports": [], "gold": True},
   ],
 },
 "pre_edits": {"chain": [
   {"file": UT,
    "old": "   * This predicate is used to test whether a given type can appear in a\n"
           "   * numeric context, such as an operand of a multiply operator.\n"
           "   *\n"
           "   * @return true if the type can appear in a numeric context.\n",
    "new": "   * This predicate is used to test whether a given type can appear in a\n"
           "   * numeric context, such as an operand of a multiply operator. The\n"
           "   * alternates are first joined into their least supertype, and the\n"
           "   * predicate is then answered for that single type.\n"
           "   *\n"
           "   * @return true if the type can appear in a numeric context.\n"},
 ]},
 "evidence": ["com.google.javascript.rhino.jstype.JSType::dereference",
              "com.google.javascript.rhino.jstype.JSType::findPropertyType",
              "com.google.javascript.rhino.jstype.NumberType::matchesNumberContext",
              "com.google.javascript.rhino.jstype.PrototypeObjectType::matchesNumberContext"],
 "ownership_reason": "Only the gold decides whether a non-null alternate of the union can appear in a numeric context: it judges "
                     "each alternate by an object type, the alternate itself if it is an object type and otherwise the object type "
                     "it is autoboxed to, through that object type's own matchesNumberContext. Hops 1, 3 and 4 pass the alternates "
                     "along unchanged; hop 2 decides only the null type (null converts to zero) and documents that every other "
                     "alternate is passed on unchanged and judged one by one. Once the gold gives the number alternate no object "
                     "type, the union (number|undefined) matches a numeric context only if a caller decides a primitive itself or "
                     "replaces the gold. The gold's javadoc promises whether a value of one of the types can appear in a numeric "
                     "context; a number can, and the variant answers false for (number|undefined). The convention is pinned outside "
                     "the gold: JSType.dereference ('Autoboxes the type') and JSType.findPropertyType (ObjectType.cast("
                     "autoboxesTo())) judge a primitive by the object type it is autoboxed to; NumberType.matchesNumberContext and "
                     "PrototypeObjectType.matchesNumberContext (Number/Boolean/String object types) give the answers; "
                     "JSTypeTest::testNumberValueType, ::testNumberObjectType, ::testStringValueType and ::testBooleanValueType "
                     "assert them, and TypeCheckTest::testStringComparison2 passes through the chain (the null alternate counts).",
 "ownership_tests": ["com.google.javascript.rhino.jstype.JSTypeTest::testNumberValueType",
                     "com.google.javascript.rhino.jstype.JSTypeTest::testNumberObjectType",
                     "com.google.javascript.rhino.jstype.JSTypeTest::testStringValueType",
                     "com.google.javascript.rhino.jstype.JSTypeTest::testBooleanValueType",
                     "com.google.javascript.jscomp.TypeCheckTest::testStringComparison2"],
 "compensating": {
   "chain": [
     {"file": TS, "old": "            if (type.isNullType()) {\n                return true;",
      "new": "            if (type.isNullType() || type.isUnknownType()) {\n                return true;",
      "why": "hop 2 also counts the unknown type"},
     {"file": TS, "old": "            if (type.isNullType()) {\n                return true;",
      "new": "            if (type.isNullType() || type.isEmptyType()) {\n                return true;",
      "why": "hop 2 also counts the empty types"},
     {"file": CO, "old": "return TypeCheck.hasNumericAlternate(types);",
      "new": "return TypeCheck.hasNumericAlternate(types) || !types.iterator().hasNext();",
      "why": "hop 4 counts an empty set of alternates"},
   ],
 },
 "host_notes": "host_mode 1500 (batch9_tasks.json). Seeded draw `mr_lib.py preview Closure-104 com/google/javascript/rhino/jstype/"
               "UnionType.java 8` (seed 6296; UnionType.java, the only allowed-candidate file, excluded): NodeUtil, TokenStream, "
               "Parser, DefaultPassConfig, TypeCheck, then JsDocInfoParser (6), Node (7), Compiler (8); the >= 1500-line pool has no "
               "further usable host. Checked in scratch with the recipe's own insertion (stageB_lib.insert_hop at seed 6296+100+i) and "
               "a call from UnionType, defects4j compile: NodeUtil at hop-1 seed 6396 (anchor `apply`, a method of the private nested "
               "class MatchNameNode): 'cannot find symbol ... location: class NodeUtil' when called as NodeUtil.x, 'MatchNameNode has "
               "private access in NodeUtil' when called as NodeUtil.MatchNameNode.x; DefaultPassConfig at hop-4 seed 6399 (anchor "
               "`process` in the private nested class ErrorPass): 'cannot find symbol ... location: class DefaultPassConfig' / "
               "'ErrorPass has private access in DefaultPassConfig'; JsDocInfoParser at seeds 6396 and 6399 (anchors `ExtractionInfo`, "
               "`getString`, both in the private nested class ExtractionInfo): 'ExtractionInfo has private access in "
               "JsDocInfoParser'. Node at seed 6396 (anchor `getLastChild`, top level) and Compiler at seed 6399 (anchor `getLength`, "
               "a member of the public static nested class Compiler.CodeBuilder, so the hop is Compiler.CodeBuilder."
               "numericOperandAllowed) compile. Replacement in hop order by the next usable drawn host: hop 1 NodeUtil -> Node "
               "(JsDocInfoParser unusable), hop 4 DefaultPassConfig -> Compiler. Final: Node (hop 1, 2060, after getLastChild, seed "
               "6396), TokenStream (hop 2, 1696, after isJSIdentifier, seed 6397), Parser (hop 3, 2438, after getTypeRegistry, seed "
               "6398), Compiler.CodeBuilder (hop 4, 1670, after getLength, seed 6399), TypeCheck (hop 5, gold, 1715, end of class, "
               "seed 6400: no anchor). Smallest host Compiler (1670). Closure compiles src/ in one javac task, so rhino classes may "
               "call jscomp classes. Imports added: JSType in TokenStream, Parser and Compiler; jscomp.Compiler in Parser (Node and "
               "TypeCheck already import JSType/ObjectType). The facade calls hop 1 by its fully-qualified name. The lie is placed by "
               "a comment-only pre-edit because the @Override annotation stops the recipe's javadoc lookup.",
}
