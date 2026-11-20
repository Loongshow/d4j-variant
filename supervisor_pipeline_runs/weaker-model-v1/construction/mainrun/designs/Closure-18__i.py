"""Main run Closure-18__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Closure-18; the real bug modified com.google.javascript.jscomp.Compiler, the facade's class). No static pair (B8 note
section 1: pool v2 found no tested public static method in Compiler); paired_* fields of the task record are null.

Facade: Compiler.getReverseAbstractInterpreter() (allowed instance target of BATCH9_PREREGISTRATION.md row 307, facade_planned_by
null, no facade reuse). The other allowed target, Compiler.init(List, List, CompilerOptions), was not used: its computation is one
loop that adds every input to a single module followed by one call to initModules; it has no decision, and every test of the suite
goes through it with ordinary inputs, so a one-line omission either breaks every compilation or leaves a dead loop or an unused
parameter (no single-trigger omission without a local trace).
Original computation of the facade (cached in the private field abstractInterpreter): on the first call, a
SemanticReverseAbstractInterpreter for getCodingConvention() and getTypeRegistry(); when options.closurePass is set, a
ClosureReverseAbstractInterpreter for the same convention and registry is put in front of it with
`new ClosureReverseAbstractInterpreter(..).append(semantic).getFirst()`; the result is stored in abstractInterpreter and returned.

facade_variant: V1+V2. V2 (receiver as parameter): the convention and the registry come from the public methods
getCodingConvention() and getTypeRegistry() of the receiver, so the facade passes `this` (typed AbstractCompiler, the public
abstract class Compiler extends, which declares both methods public) to hop 1, which calls them. V1 (state as parameters): the
facade reads the field options (package-private, inside Compiler) and passes the boolean options.closurePass, and writes the
returned interpreter back into the private cache field abstractInterpreter, keeping the original's cache check. No private method of
Compiler is called (no V4); every type involved is public (no V3/V5). No signature, modifier, override (the @Override annotation stays)
or throws change; no new type; no reflection; no test edit.
state_passed: the receiver `this` (as AbstractCompiler) and the value of options.closurePass to hop 1; write-back of the returned
ReverseAbstractInterpreter into the private field abstractInterpreter (under the original `abstractInterpreter == null` check).
Behaviour-preserving pre-edits (Compiler.java only): the facade had no javadoc (it only had @Override), so a one-sentence javadoc in
the voice of AbstractCompiler's own declaration ("Get an interpreter for type analysis.") is added between the annotation and the
header, where the recipe's rewrite_facade finds it and appends the lie (Closure has this annotation-then-javadoc order elsewhere,
e.g. ControlFlowAnalysis, AliasKeywords); the imports of ChainableReverseAbstractInterpreter, ClosureReverseAbstractInterpreter and
SemanticReverseAbstractInterpreter, which only the old body used, are removed (ReverseAbstractInterpreter stays: the field and the
return type use it).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Closure-18-probe of the fixture,
the first statement of each allowed facade was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j
compile OK. `defects4j test -t com.google.javascript.jscomp.TypeInferenceTest::testAssertWithIsDef`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at Compiler.getReverseAbstractInterpreter(Compiler.java:1209), called from
TypeInferenceTest.inFunction(TypeInferenceTest.java:122) from testAssertWithIsDef (TypeInferenceTest.java:500). (Compiler.init was
also reached: NormalizeTest::testNormalizeSyntheticCode failed with PROBE-REACHED at Compiler.init(Compiler.java:327).) The chosen
facade is reached directly by the trigger, which calls compiler.getReverseAbstractInterpreter() itself.

Hosts (host_mode = "1500"; `mr_lib.py preview Closure-18 com/google/javascript/jscomp/Compiler.java 11`, instance seed 2165; draw
order RegExpTree, Node, JSTypeRegistry, JSDocInfo, JsDocInfoParser, jsonml.Reader, CompilerOptions, TypeCheck, SymbolTable, NodeUtil,
DefaultPassConfig). The recipe's anchor (stageB_lib.pick_anchor, seed 2165 + 100 + slot, as mr3_spec.py inserts) takes an existing
method indented exactly four spaces; in Closure's two-space style those are members of NESTED types, so a hop is inserted inside the
nested type that holds the anchor (or before the class's last brace when there is none). A host is unusable when the hop at its anchor
cannot be called from its caller in another package (private or package-private nested type, or a non-static inner class, where a
static method does not compile either); it is then replaced by the next drawn host, in the same slot (B8 note section 2; no host
chosen by any other criterion):
  slot 1 (seed 2265): RegExpTree -> anchor in `static final class Empty` (package-private, jscomp.regex; caller in jscomp): unusable;
                      jsonml.Reader -> anchor in `private class ErrorReporter` (private inner class): unusable;
                      CompilerOptions -> anchor after `isOn` in `public static enum TweakProcessing`: usable.  HOP 1
  slot 2 (seed 2266): Node -> anchor in `private static class StringNode`: unusable; (jsonml.Reader -> private ErrorReporter:
                      unusable); TypeCheck -> no nested anchor, inserted before the class's last brace: usable.        HOP 2
  slot 3 (seed 2267): JSTypeRegistry -> no nested anchor, before the class's last brace: usable.                         HOP 3
  slot 4 (seed 2268): JSDocInfo -> anchor after `getName` in `public static final class Marker`: usable.               HOP 4
  slot 5 (seed 2269): JsDocInfoParser -> anchor in `private static class ExtractionInfo`: unusable; (jsonml.Reader -> `private
                      enum Operator`: unusable); SymbolTable -> anchor after `getTypeOfThis` in `public static final class
                      SymbolScope`: usable.                                                                              HOP 5 (gold)
  hop 1 CompilerOptions$TweakProcessing  2083 lines  interpreterFor         gathering: the convention and the registry of the
                                                                            compiler (V2 receiver)
  hop 2 TypeCheck                        1925 lines  conditionInterpreter   pass-through
  hop 3 JSTypeRegistry                   1722 lines  refiningInterpreter    pass-through
  hop 4 JSDocInfo$Marker                 1508 lines  typeInterpreter        pass-through
  hop 5 SymbolTable$SymbolScope          1611 lines  newReverseInterpreter  GOLD: creates the semantic interpreter and, when the
                                                                            Closure primitives are recognized, puts the Closure
                                                                            interpreter in front of it and returns the chain's head
Host newline counts 2083, 1925, 1722, 1508, 1611; the smallest host is JSDocInfo (1508 lines); the gold host has 1611 lines. The
facade's file Compiler.java is excluded (facade_files_excluded). Hop classes are named as the harness catalog names them
(Outer$Nested).
The correct configuration returns the original interpreter for every compiler: the same two constructors with the same convention
and registry, the same closurePass decision and the same chain head.

Fault (one-line omission inside the gold's decision): the step that returns to the head of the chain after the semantic interpreter
is appended to the Closure interpreter is dropped (`.append(interpreter).getFirst();` becomes `.append(interpreter);`).
ChainableReverseAbstractInterpreter.append returns the appended (last) link, so the gold then returns the semantic link: the
chain still exists (the semantic link's first link is the Closure link, so conditions nested in !, && and || still reach the
Closure link through firstPreciserScopeKnowingConditionOutcome), but a top-level call such as goog.isDefAndNotNull(x) is no longer
refined (the semantic link hands calls on to its next link, which is null). The gold still reads as the ordinary routine "create the
semantic interpreter; when the Closure primitives are on, chain the Closure interpreter in front of it". Trigger: the EXISTING test
TypeInferenceTest::testAssertWithIsDef (closurePass on in setUp): `goog.asserts.assert(goog.isDefAndNotNull(x))` no longer narrows x,
verify("out2", NUMBER_TYPE) fails with "Expected: number / Actual  : (null|number)". Full suite on this variant (scratch run of the
same edit in place in Compiler.java, /private/tmp/d4j-mi-Closure-18-va): exactly 1 failing test, testAssertWithIsDef; G5 checks it on
the built instance. TypeInferenceTest::testAssertWithNotIsNull (`!goog.isNull(x)`, nested) still passes. Dropping the whole Closure
step instead fails two tests (testAssertWithIsDef and testAssertWithNotIsNull), so it was not used.

The gold's javadoc states the idiomatic contract (the interpreter that refines types from the outcome of a condition; with
closurePrimitives the Closure primitives such as goog.isDef are recognized as well) and is silent on chain heads. The convention is
pinned outside the gold: ChainableReverseAbstractInterpreter.append ("Appends a link to this, returning the updated last link"; the
pattern new X().append(new Y()) "forms a chain starting with X"), ChainableReverseAbstractInterpreter.getFirst ("Gets the first link of
this chain") and firstPreciserScopeKnowingConditionOutcome ("Calculates the preciser scope starting with the first link");
AbstractCompiler.getReverseAbstractInterpreter ("Get an interpreter for type analysis"); the passing tests TypeCheckTest::testClosure3
and ::testClosure1 (their helper testClosureTypesMultipleWarnings builds the same chain as
new ClosureReverseAbstractInterpreter(..).append(new SemanticReverseAbstractInterpreter(..)).getFirst() and checks that
goog.isDefAndNotNull(a) / goog.isDef(a) at the top of a condition narrows a), TypeInferenceTest::testAssertWithNotIsNull (the
compiler's own interpreter with closurePass recognizes goog.isNull), ClosureReverseAbstractInterpreterTest::testGoogIsDefAndNotNull1
(the Closure interpreter itself narrows goog.isDefAndNotNull).

Single owner: only the gold creates the interpreters and links them; hops 2-4 pass the convention, the registry and the flag along and
hop 1 only reads the convention and the registry from the compiler. The flag is the only value above the gold that changes the
result, and neither value of it restores the refinement (false: no Closure link at all, the trigger still fails; true: the variant
gold still returns the last link). Declared alternatives (G9): hop 1 asks for no Closure primitives; hop 3 always asks for them.
Recorded bypasses (edits that re-derive or replace the gold's result, not repairs of the chain):
 B-1 a hop above the gold casts the gold's ReverseAbstractInterpreter result to the implementation class
     ChainableReverseAbstractInterpreter and calls getFirst() on it, e.g. at hop 4
     `return ((ChainableReverseAbstractInterpreter) SymbolTable.SymbolScope.newReverseInterpreter(..)).getFirst();` (or the
     same at hops 1-3 or in the facade's write-back): it re-derives the chain head from the object the gold returned, using the
     concrete type that every hop's declared type hides; the gold still returns the last link. Expected to pass the trigger and the
     suite (same behaviour as the correct gold).
 B-0 the facade's original body (or any hop constructing the two interpreters itself) re-implements the whole computation and makes
     the chain, including the gold, dead.

Lie: the facade's javadoc claims the interpreter is assembled by scanning the assertion functions of the coding convention and
registering one refinement rule for each of them; the chain scans nothing (two constructors and one optional append). It names
neither the chain head, the append step, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: convention and registry are both passed to both constructors; closurePrimitives decides whether the Closure
     interpreter is created; no argument check.
  T2 absent: interpreter is initialised by a constructor call (not a literal), reassigned in the branch, and returned; there is no
     loop; the branch has an effect (it creates the Closure link, links it and reassigns interpreter).
  T3 absent: the two interpreters are not given parallel treatments of which one is missing; no enum, type code or named format set;
     the gold's text names no class it handles in part.
  T4 absent: "refines the types of names from the outcome of a condition" is a general description; "When closurePrimitives is set,
     the Closure primitives, such as goog.isDef, are recognized as well" is met by the closurePrimitives branch; the @param and
     @return clauses name no rule.
 Variant gold (javadoc, signature, `interpreter = new SemanticReverseAbstractInterpreter(convention, registry)`, `if
 (closurePrimitives) { interpreter = new ClosureReverseAbstractInterpreter(convention, registry).append(interpreter); }`,
 `return interpreter`):
  T1 absent: convention and registry still reach both constructors; closurePrimitives still decides the branch.
  T2 absent: interpreter is read (as the append argument and by the return) and reassigned in the branch; not literal-initialised;
     no loop, cursor, counter, flag or best-so-far; the branch still has an effect (a new object, an append call and an assignment).
  T3 absent: as for the correct gold; no member of any set the gold names is left without a treatment its sibling gets.
  T4 absent: the phrase about the Closure primitives is met in the text by the branch that creates and appends the Closure
     interpreter; no phrase names a chain head, a first link or an order the body visibly contradicts; no inline comment; the
     identifiers (interpreter, closurePrimitives, newReverseInterpreter) name what they hold or do."""

SRC = "src/com/google/javascript/"
COMP = SRC + "jscomp/Compiler.java"
OPT = SRC + "jscomp/CompilerOptions.java"
TC = SRC + "jscomp/TypeCheck.java"
REG = SRC + "rhino/jstype/JSTypeRegistry.java"
JDI = SRC + "rhino/JSDocInfo.java"
SYM = SRC + "jscomp/SymbolTable.java"

GOLD_TEXT = '''/**
 * Creates the interpreter that refines the types of names from the outcome
 * of a condition, for the given coding convention and type registry. When
 * closurePrimitives is set, the Closure primitives, such as goog.isDef, are
 * recognized as well.
 *
 * @param convention The coding convention.
 * @param registry The type registry.
 * @param closurePrimitives Whether the Closure primitives refine types.
 * @return The interpreter.
 */
public static ReverseAbstractInterpreter newReverseInterpreter(
    CodingConvention convention, JSTypeRegistry registry,
    boolean closurePrimitives) {
  ChainableReverseAbstractInterpreter interpreter =
      new SemanticReverseAbstractInterpreter(convention, registry);
  if (closurePrimitives) {
    interpreter = new ClosureReverseAbstractInterpreter(
        convention, registry).append(interpreter).getFirst();
  }
  return interpreter;
}'''

HOP1 = '''/**
 * Gets an interpreter for type analysis, for the coding convention and the
 * type registry of the given compiler.
 *
 * @param compiler The compiler whose coding convention and type registry
 *     are used.
 * @param closurePrimitives Whether the Closure primitives, such as
 *     goog.isDef, refine types.
 * @return The interpreter.
 */
public static ReverseAbstractInterpreter interpreterFor(
    AbstractCompiler compiler, boolean closurePrimitives) {
  return TypeCheck.conditionInterpreter(compiler.getCodingConvention(),
      compiler.getTypeRegistry(), closurePrimitives);
}'''

HOP2 = '''/**
 * Gets the interpreter that refines types from the outcome of a condition.
 *
 * @param convention The coding convention.
 * @param registry The type registry.
 * @param closurePrimitives Whether the Closure primitives refine types.
 * @return The interpreter.
 */
public static ReverseAbstractInterpreter conditionInterpreter(
    CodingConvention convention, JSTypeRegistry registry,
    boolean closurePrimitives) {
  return JSTypeRegistry.refiningInterpreter(
      convention, registry, closurePrimitives);
}'''

HOP3 = '''/**
 * Gets the interpreter that refines the types of this registry from the
 * outcome of a condition.
 *
 * @param convention The coding convention.
 * @param registry The type registry.
 * @param closurePrimitives Whether the Closure primitives refine types.
 * @return The interpreter.
 */
public static ReverseAbstractInterpreter refiningInterpreter(
    CodingConvention convention, JSTypeRegistry registry,
    boolean closurePrimitives) {
  return JSDocInfo.Marker.typeInterpreter(
      convention, registry, closurePrimitives);
}'''

HOP4 = '''/**
 * Gets the interpreter for type analysis.
 *
 * @param convention The coding convention.
 * @param registry The type registry.
 * @param closurePrimitives Whether the Closure primitives refine types.
 * @return The interpreter.
 */
public static ReverseAbstractInterpreter typeInterpreter(
    CodingConvention convention, JSTypeRegistry registry,
    boolean closurePrimitives) {
  return SymbolTable.SymbolScope.newReverseInterpreter(
      convention, registry, closurePrimitives);
}'''

DESIGN = {
 "instance": "Closure-18", "project": "Closure", "bug_id": 18, "seed": 2165,
 "src_root": "src", "test_root": "test",
 "facade": {"file": COMP, "class": "com.google.javascript.jscomp.Compiler", "method": "getReverseAbstractInterpreter",
            "near_line": 1207},
 "facade_variant": "V1+V2",
 "state_passed": "the receiver this (as AbstractCompiler; hop 1 calls its public getCodingConvention() and getTypeRegistry()) and "
                 "the value of the field options.closurePass to hop 1; the returned interpreter is written back into the private "
                 "cache field abstractInterpreter under the original abstractInterpreter == null check",
 "reachability_probe": "TypeInferenceTest::testAssertWithIsDef fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "Compiler.getReverseAbstractInterpreter(Compiler.java:1209) from TypeInferenceTest.inFunction "
                       "(TypeInferenceTest.java:122); Compiler.init also reached (NormalizeTest::testNormalizeSyntheticCode, "
                       "Compiler.java:327)",
 "host_mode": "1500",
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/TypeInferenceTest.java",
             "test_class": "com.google.javascript.jscomp.TypeInferenceTest", "test_method": "testAssertWithIsDef"},
 "expected_signature": "Actual  : (null|number)",
 "gold": {"method": "newReverseInterpreter", "text": GOLD_TEXT,
          "fault": {"old": "            convention, registry).append(interpreter).getFirst();\n",
                    "new": "            convention, registry).append(interpreter);\n"}},
 "pre_edits": {"chain": [
   {"file": COMP,
    "old": "import com.google.javascript.jscomp.type.ChainableReverseAbstractInterpreter;\n"
           "import com.google.javascript.jscomp.type.ClosureReverseAbstractInterpreter;\n"
           "import com.google.javascript.jscomp.type.ReverseAbstractInterpreter;\n"
           "import com.google.javascript.jscomp.type.SemanticReverseAbstractInterpreter;\n",
    "new": "import com.google.javascript.jscomp.type.ReverseAbstractInterpreter;\n"},
   {"file": COMP,
    "old": "  @Override\n  public ReverseAbstractInterpreter getReverseAbstractInterpreter() {\n",
    "new": "  @Override\n  /**\n   * Gets an interpreter for type analysis.\n   */\n"
           "  public ReverseAbstractInterpreter getReverseAbstractInterpreter() {\n"},
 ]},
 "chain": {
   "facade_body": "if (abstractInterpreter == null) {\n"
                  "          abstractInterpreter = CompilerOptions.TweakProcessing.interpreterFor(\n"
                  "              this, options.closurePass);\n"
                  "        }\n"
                  "        return abstractInterpreter;",
   "lie": "The interpreter is assembled by scanning the assertion functions of the coding convention and registering one "
          "refinement rule for each of them.",
   "hops": [
     {"file": OPT, "class": "com.google.javascript.jscomp.CompilerOptions$TweakProcessing", "method": "interpreterFor",
      "imports": ["com.google.javascript.jscomp.type.ReverseAbstractInterpreter"], "text": HOP1},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "conditionInterpreter",
      "imports": [], "text": HOP2},
     {"file": REG, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "refiningInterpreter",
      "imports": ["com.google.javascript.jscomp.CodingConvention", "com.google.javascript.jscomp.type.ReverseAbstractInterpreter",
                  "com.google.javascript.rhino.JSDocInfo"], "text": HOP3},
     {"file": JDI, "class": "com.google.javascript.rhino.JSDocInfo$Marker", "method": "typeInterpreter",
      "imports": ["com.google.javascript.jscomp.CodingConvention", "com.google.javascript.jscomp.SymbolTable",
                  "com.google.javascript.jscomp.type.ReverseAbstractInterpreter",
                  "com.google.javascript.rhino.jstype.JSTypeRegistry"], "text": HOP4},
     {"file": SYM, "class": "com.google.javascript.jscomp.SymbolTable$SymbolScope", "method": "newReverseInterpreter",
      "imports": ["com.google.javascript.jscomp.type.ChainableReverseAbstractInterpreter",
                  "com.google.javascript.jscomp.type.ClosureReverseAbstractInterpreter",
                  "com.google.javascript.jscomp.type.ReverseAbstractInterpreter",
                  "com.google.javascript.jscomp.type.SemanticReverseAbstractInterpreter"], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.type.ChainableReverseAbstractInterpreter::append",
              "com.google.javascript.jscomp.type.ChainableReverseAbstractInterpreter::getFirst",
              "com.google.javascript.jscomp.type.ChainableReverseAbstractInterpreter::firstPreciserScopeKnowingConditionOutcome",
              "com.google.javascript.jscomp.AbstractCompiler::getReverseAbstractInterpreter"],
 "ownership_reason": "Only the gold creates the semantic and the Closure interpreters and links them; hops 2-4 pass the coding "
                     "convention, the type registry and the closurePrimitives flag along unchanged and hop 1 only reads the "
                     "convention and the registry from the compiler. The gold's javadoc promises the interpreter that refines "
                     "types from the outcome of a condition with the Closure primitives, such as goog.isDef, recognized when "
                     "closurePrimitives is set; the variant returns the last link of the chain (append returns the appended "
                     "link), which does not refine a top-level goog.isDefAndNotNull(x) call. The flag is the only value above "
                     "the gold that changes the result, and neither value restores the refinement. The convention is pinned "
                     "outside the gold: ChainableReverseAbstractInterpreter.append ('returning the updated last link'; "
                     "new X().append(new Y()) 'forms a chain starting with X'), getFirst ('Gets the first link of this chain') "
                     "and firstPreciserScopeKnowingConditionOutcome ('starting with the first link'), "
                     "AbstractCompiler.getReverseAbstractInterpreter ('Get an interpreter for type analysis'); the passing "
                     "tests TypeCheckTest testClosure3 and testClosure1 build the same chain with .append(..).getFirst() and "
                     "check that goog.isDefAndNotNull(a) and goog.isDef(a) narrow a at the top of a condition; "
                     "TypeInferenceTest testAssertWithNotIsNull shows the compiler's own interpreter recognizes goog.isNull "
                     "with closurePass on; ClosureReverseAbstractInterpreterTest testGoogIsDefAndNotNull1 shows the Closure "
                     "interpreter narrows goog.isDefAndNotNull.",
 "ownership_tests": ["com.google.javascript.jscomp.TypeCheckTest::testClosure3",
                     "com.google.javascript.jscomp.TypeCheckTest::testClosure1",
                     "com.google.javascript.jscomp.TypeInferenceTest::testAssertWithNotIsNull",
                     "com.google.javascript.jscomp.ClosureReverseAbstractInterpreterTest::testGoogIsDefAndNotNull1"],
 "compensating": {
   "chain": [
     {"file": OPT, "old": "compiler.getTypeRegistry(), closurePrimitives);",
      "new": "compiler.getTypeRegistry(), false);",
      "why": "hop 1 asks for no Closure primitives, so only the semantic interpreter is created"},
     {"file": REG, "old": "      convention, registry, closurePrimitives);",
      "new": "      convention, registry, true);",
      "why": "hop 3 always asks for the Closure primitives"},
   ],
 },
 "host_notes": "host_mode 1500. mr_lib.py preview Closure-18 com/google/javascript/jscomp/Compiler.java 11 (seed 2165) draws "
               "RegExpTree, Node, JSTypeRegistry, JSDocInfo, JsDocInfoParser, jsonml.Reader, CompilerOptions, TypeCheck, "
               "SymbolTable, NodeUtil, DefaultPassConfig. The recipe anchor (pick_anchor, seed 2165+100+slot) takes a method "
               "indented four spaces, which in Closure's two-space style is a member of a nested type, so the hop lands in "
               "that nested type (or before the last brace when there is none). A host whose hop would sit in a private or "
               "package-private nested type, or in a non-static inner class, cannot be called from its caller in another "
               "package and is unusable; it is replaced by the next drawn host in the same slot. Slot 1: RegExpTree (in "
               "package-private Empty) and jsonml.Reader (in private inner ErrorReporter) unusable -> CompilerOptions, in "
               "public static enum TweakProcessing after isOn (2083 lines). Slot 2: Node (in private StringNode) and "
               "jsonml.Reader (private ErrorReporter) unusable -> TypeCheck, before its last brace (1925). Slot 3: "
               "JSTypeRegistry, before its last brace (1722). Slot 4: JSDocInfo, in public static final class Marker after "
               "getName (1508; the smallest host). Slot 5: JsDocInfoParser (in private ExtractionInfo) and jsonml.Reader "
               "(private enum Operator) unusable -> SymbolTable, in public static final class SymbolScope after "
               "getTypeOfThis (1611; gold). Hop classes use the harness catalog's Outer$Nested names. The facade's class "
               "Compiler is not a host (facade_files_excluded).",
}
