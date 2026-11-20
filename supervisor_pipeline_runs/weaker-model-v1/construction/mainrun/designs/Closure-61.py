"""Main run Closure-61 (C10 recipe on the fixed checkout of Defects4J Closure-61; the real bug modified NodeUtil, the target class).

Facade: NodeUtil.getNearestFunctionName(Node) (the only allowed target, BATCH4_PREREGISTRATION.md row Closure-61). Callers: the
production pass SourceInformationAnnotator (FUNCTION nodes, only when a source map or a name-reference report is requested) and the
test NodeUtilTest::testGetNearestFunctionName. The only other tests that reach it are the source-map generator tests
(SourceMapGeneratorV1Test::testFunctionNameOutput1-4 and the V2/V3 basic cases), whose inputs are `function f() {}`,
`a.b.c = function () {}`, `var q = function () {};` and `({ 'q' : function () {} })`.
Original computation: getFunctionName(n) (parent NAME -> the variable name; parent ASSIGN -> the qualified name of the assignment
target, possibly null; otherwise the function's own name if non-empty, else null); if that is null, a SET, GET or STRING parent
gives its string and a NUMBER parent its NodeUtil.getStringValue; otherwise null. The qualified name is Node.getQualifiedName:
NAME -> its string, GETPROP -> qualified name of the object + "." + property (null if the object has none), THIS -> "this", else
null. Of all the steps, only three are exercised by testGetNearestFunctionName and by no other test: the NUMBER key, the GET/SET
keys and the THIS root of an assignment target (`this.a = function a() {}`). Omitting the own-name emptiness test, the NAME parent or
the ASSIGN parent also changes the source-map tests (gate G5). The NUMBER and GET/SET cases are members of a switch over Token type
codes, so their omission leaves a visibly incomplete set of key kinds in whatever method holds that switch, and any method that
holds the parent can restore them with one line; they were set aside. The THIS root sits at the end of a walk over a chain of
property accesses of any depth: no caller can pre-filter it or recover it in one line without re-implementing the walk.

Chain (hosts in draw order for seed 4011, unusable hosts skipped, see host_notes):
  hop 1 rhino.TokenStream.nameOfFunction              placement: the function together with its parent node
  hop 2 rhino.Parser.nameFromParent                   decision: a function that initializes a variable takes the variable name
  hop 3 jscomp.Compiler$CodeBuilder.functionOrKeyName  aggregation: the declared name, else the name of the object-literal key
                                                       (SET, GET, STRING string; NUMBER NodeUtil.getStringValue)
  hop 4 rhino.jstype.JSTypeRegistry.declaredFunctionName  decision: an assigned function takes the qualified name of the target,
                                                       any other the function's own name (non-empty) or null
  hop 5 jscomp.TypeCheck.qualifiedNameOf               GOLD: the walk down the chain of property accesses of the target,
                                                       prepending each property name, with the root step (this, a name,
                                                       or anything else -> null)
The correct configuration computes exactly the original result for every input (same parent cases in the same order, the key
fallback after the declared name, getStringValue for NUMBER keys, and the iterative walk equal to Node.getQualifiedName: NAME ->
string, GETPROP -> object's name + "." + property, THIS -> "this", else null). getFunctionName is untouched and keeps its five
production callers.

Fault (omission of a special-case step in the gold): the root step for `this` is dropped (the three lines
`if (NodeUtil.isThis(current)) { return "this" + suffix; }`), so a chain of property accesses on `this` has no qualified name and
the gold returns null. The gold then reads as an ordinary walk that names a chain rooted at a variable. Trigger: the EXISTING test
NodeUtilTest::testGetNearestFunctionName; its first ten assertions pass (the declarations, the keys, `a`, `o.a`), and the last,
testFunctionName("this.a = function a() {}", "this.a"), fails with junit ComparisonFailure expected:<this.a> but was:<null>
(hop 4 returns the gold's null, hop 3's key fallback has no case for an ASSIGN parent). No other test reaches the THIS root: the
source-map tests assign to `a.b.c` only. The gold's javadoc states the idiomatic contract (the qualified name of an expression,
such as a.b.c, or null if the expression is not a qualified name) and is silent on `this`; `this.a` is a qualified name
(Node.isQualifiedName's own javadoc: "such as x or a.b.c or this.a"; NodeTest::testIsQualifiedName asserts it).

External pins (convention outside the gold): Node.getQualifiedName returns "this" for THIS and so names `this.a` "this.a";
NodeUtil.getRootOfQualifiedName ("Must be either NAME or THIS"); NodeUtil.getFunctionName (beside the facade, five production
callers) names an assigned function by Node.getQualifiedName of the target; NodeNameExtractor.getName (the anonymous-function
namer) names THIS "this" (NameAnonymousFunctionsTest::testAssignmentToGetElem expects $win$x$this$id$); NodeTest::testIsQualifiedName
asserts that this.foo is a qualified name; SourceMapGeneratorV1Test::testFunctionNameOutput2 pins that a function assigned to a
qualified name is named by it (a.b.c).

Single owner: only the gold walks the chain of property accesses and decides on its root; hops 1-3 hold the function and its
parent, hop 4 the assignment target, and all get back a name or null. The gold returns null for the whole target, and no sub-node
of `this.a` has a qualified name either (the property is a STRING node), so no hop can call the gold on another node, or wrap its
result, to obtain "this.a"; restoring it at a hop needs a second walk over the chain. Declared alternatives (G9): hop 4 falls back
to the function's own name when the target has no qualified name, hop 3's key fallback names an assigned function after the
target's last property, hop 2 names a function assigned to a property after that property; each gives "a", not "this.a".
Recorded bypasses (one-line edits that replace the gold's result with another implementation; not repairs of the chain; B-1 and
B-2 were checked on the variant in a scratch copy: trigger passes, defects4j test 0 failing tests each):
 B-0 the facade restores its original body (getFunctionName plus the key switch), discarding all five hops.
 B-1 hop 4 returns parent.getFirstChild().getQualifiedName() (Node's own implementation) instead of calling the gold; the gold
     becomes dead.
 B-2 hop 3 takes the declared name from NodeUtil.getFunctionName(fnNode) instead of hop 4; hop 4 and the gold become dead.
 B-3 hop 3's key fallback gains `case Token.ASSIGN: return parent.getFirstChild().getQualifiedName();`: on the trigger input the
     gold's null is replaced by Node's implementation (a second implementation of the gold's walk).

Lie: the facade's javadoc claims the name is recovered from the function's source text by scanning back from the `function`
keyword to the nearest `=` or `:` and reading the name written before it; the code reads the tree (the parent node), not the
source text. It names neither `this` nor any root, step that is omitted, or hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, `String suffix = ""; Node current = expr; while (NodeUtil.isGetProp(current)) { suffix = "." +
 current.getLastChild().getString() + suffix; current = current.getFirstChild(); } if (NodeUtil.isThis(current)) { return "this"
 + suffix; } if (NodeUtil.isName(current)) { return current.getString() + suffix; } return null;`):
  T1 absent: expr starts the walk and decides every return.
  T2 absent: suffix ("" initially) is reassigned in the loop and reaches both name returns; current is the loop's cursor and is
     advanced in the loop; each if returns a different value from the fall-through.
  T3 absent: the gold tests three node predicates (property access, this, name), each with its own treatment; no Token type code
     or enum appears in its text, and its text names no class or set with a member left out; both children of a property access
     are used (the object is walked, the property name appended).
  T4 absent: 'the qualified name of an expression, such as a.b.c' and 'null if the expression is not a qualified name' are
     general descriptions that the walk and the final return address; no limit, bound, value class or case is named.
  The node tests are written with NodeUtil's predicates rather than as comparisons with Token type codes (Token.NAME,
  Token.THIS, Token.GETPROP), so that no type code appears in the gold whose other members could be read as a left-out set.
 Variant gold (javadoc, signature, `String suffix = ""; Node current = expr; while (NodeUtil.isGetProp(current)) { suffix = "." +
 current.getLastChild().getString() + suffix; current = current.getFirstChild(); } if (NodeUtil.isName(current)) { return
 current.getString() + suffix; } return null;`):
  T1 absent: expr is the start of the walk; its value decides the returned name or null.
  T2 absent: suffix is reassigned in the loop and read in the name return; current is assigned in the loop (cursor) and tested
     after it; the single if returns the name, the fall-through null, so the decision matters; no literal-initialised local is
     left unassigned ("" is reassigned in the loop), no flag, counter or best-so-far.
  T3 absent: two predicates remain (property access, name) with different treatments (walk, return); the text names no set and
     uses no type code or enum whose other members could be quoted; no pair half or range end is left untreated (both children
     of a property access are read and used).
  T4 absent: the javadoc names the qualified name of an expression 'such as a.b.c' (produced by the walk and the name return)
     and 'null if the expression is not a qualified name' (the final return); identifiers suffix, current and expr name nothing
     the body does not meet; no inline comment."""

NU = "src/com/google/javascript/jscomp/NodeUtil.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
PA = "src/com/google/javascript/rhino/Parser.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"
JTR = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"

GOLD_TEXT = '''/**
 * Returns the qualified name of an expression, such as {@code a.b.c}.
 *
 * @param expr the expression
 * @return the qualified name, or {@code null} if the expression is not a
 *     qualified name
 */
public static String qualifiedNameOf(Node expr) {
  String suffix = "";
  Node current = expr;
  while (NodeUtil.isGetProp(current)) {
    suffix = "." + current.getLastChild().getString() + suffix;
    current = current.getFirstChild();
  }
  if (NodeUtil.isThis(current)) {
    return "this" + suffix;
  }
  if (NodeUtil.isName(current)) {
    return current.getString() + suffix;
  }
  return null;
}'''

HOP1 = '''/**
 * Gets the name of a function, given by the function node together with
 * the node that contains it.
 *
 * @param fnNode a node whose type is {@link Token#FUNCTION}
 * @return the function's name, or {@code null} if it has no name
 */
public static String nameOfFunction(Node fnNode) {
    return Parser.nameFromParent(fnNode, fnNode.getParent());
}'''

HOP2 = '''/**
 * Gets the name of a function, given the node that contains it. A
 * function that initializes a variable takes the name of the variable.
 *
 * @param fnNode a node whose type is {@link Token#FUNCTION}
 * @param parent the parent of the function node
 * @return the function's name, or {@code null} if it has no name
 */
public static String nameFromParent(Node fnNode, Node parent) {
    if (parent.getType() == Token.NAME) {
        return parent.getString();
    }
    return Compiler.CodeBuilder.functionOrKeyName(fnNode, parent);
}'''

HOP3 = '''/**
 * Gets the name of a function, given the node that contains it: the name
 * the function is declared with or, when it has none, the name of the
 * object literal key whose value it is.
 *
 * @param fnNode a node whose type is {@link Token#FUNCTION}
 * @param parent the parent of the function node
 * @return the function's name, or {@code null} if it has no name
 */
public static String functionOrKeyName(Node fnNode, Node parent) {
  String name = JSTypeRegistry.declaredFunctionName(fnNode, parent);
  if (name != null) {
    return name;
  }
  switch (parent.getType()) {
    case Token.SET:
    case Token.GET:
    case Token.STRING:
      return parent.getString();
    case Token.NUMBER:
      return NodeUtil.getStringValue(parent);
  }
  return null;
}'''

HOP4 = '''/**
 * Gets the name a function is declared with: the qualified name of the
 * target when the function is assigned, otherwise the function's own name.
 *
 * @param fnNode a node whose type is {@link Token#FUNCTION}
 * @param parent the parent of the function node
 * @return the declared name, or {@code null} if there is none
 */
public static String declaredFunctionName(Node fnNode, Node parent) {
  if (parent.getType() == Token.ASSIGN) {
    return TypeCheck.qualifiedNameOf(parent.getFirstChild());
  }
  String name = fnNode.getFirstChild().getString();
  return name.length() != 0 ? name : null;
}'''

DESIGN = {
 "instance": "Closure-61", "project": "Closure", "bug_id": 61, "seed": 4011,
 "src_root": "src", "test_root": "test",
 "facade": {"file": NU, "class": "com.google.javascript.jscomp.NodeUtil", "method": "getNearestFunctionName", "near_line": 449},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/NodeUtilTest.java",
             "test_class": "com.google.javascript.jscomp.NodeUtilTest", "test_method": "testGetNearestFunctionName"},
 "expected_signature": "expected:<this.a> but was:<null>",
 "gold": {"method": "qualifiedNameOf", "text": GOLD_TEXT,
          "fault": {"old": "        current = current.getFirstChild();\n"
                           "      }\n"
                           "      if (NodeUtil.isThis(current)) {\n"
                           "        return \"this\" + suffix;\n"
                           "      }\n"
                           "      if (NodeUtil.isName(current)) {",
                    "new": "        current = current.getFirstChild();\n"
                           "      }\n"
                           "      if (NodeUtil.isName(current)) {"}},
 "chain": {
   "facade_body": "return com.google.javascript.rhino.TokenStream.nameOfFunction(n);",
   "lie": "The name is recovered from the function's source text, by scanning back from the {@code function} keyword to "
          "the nearest {@code =} or {@code :} and reading the name written before it.",
   "hops": [
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "nameOfFunction",
      "imports": [], "text": HOP1},
     {"file": PA, "class": "com.google.javascript.rhino.Parser", "method": "nameFromParent",
      "imports": ["com.google.javascript.jscomp.Compiler"], "text": HOP2},
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "functionOrKeyName",
      "imports": [], "text": HOP3},
     {"file": JTR, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "declaredFunctionName",
      "imports": ["com.google.javascript.jscomp.TypeCheck"], "text": HOP4},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "qualifiedNameOf",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.rhino.Node::getQualifiedName",
              "com.google.javascript.jscomp.NodeUtil::getFunctionName",
              "com.google.javascript.jscomp.NodeNameExtractor::getName",
              "com.google.javascript.jscomp.NodeUtil::getRootOfQualifiedName"],
 "ownership_reason": "Only the gold walks the chain of property accesses of an assignment target and decides on its root; hops 1-3 "
                     "hold the function and its parent, hop 4 the target, and each gets back a name or null. The gold returns "
                     "null for the whole of this.a and no sub-node of it has a qualified name (the property is a STRING node), "
                     "so no hop can call the gold on another node or wrap its result to obtain this.a; restoring it outside the "
                     "gold needs a second walk over the chain (or Node.getQualifiedName, which replaces the gold). The "
                     "convention is pinned outside the gold: Node.getQualifiedName names THIS 'this', so this.a is 'this.a', "
                     "and Node.isQualifiedName documents 'such as x or a.b.c or this.a' (NodeTest.testIsQualifiedName asserts "
                     "this.foo); NodeUtil.getRootOfQualifiedName says the root must be either NAME or THIS; NodeUtil."
                     "getFunctionName, beside the facade and used by five production passes, names an assigned function by the "
                     "target's Node.getQualifiedName; NodeNameExtractor.getName names THIS 'this' when naming anonymous "
                     "functions (NameAnonymousFunctionsTest.testAssignmentToGetElem); SourceMapGeneratorV1Test."
                     "testFunctionNameOutput2 pins that a function assigned to a.b.c is named a.b.c. The gold's javadoc promises "
                     "the qualified name of the expression, which this.a has.",
 "ownership_tests": ["com.google.javascript.rhino.NodeTest::testIsQualifiedName",
                     "com.google.javascript.jscomp.NameAnonymousFunctionsTest::testAssignmentToGetElem",
                     "com.google.javascript.jscomp.NameAnonymousFunctionsMappedTest::testAssignmentToGetElem",
                     "com.google.debugging.sourcemap.SourceMapGeneratorV1Test::testFunctionNameOutput2"],
 "compensating": {
   "chain": [
     {"file": JTR, "old": "        return TypeCheck.qualifiedNameOf(parent.getFirstChild());",
      "new": "        return TypeCheck.qualifiedNameOf(parent.getFirstChild()) != null ? TypeCheck.qualifiedNameOf(parent.getFirstChild()) "
             ": (fnNode.getFirstChild().getString().length() != 0 ? fnNode.getFirstChild().getString() : null);",
      "why": "hop 4 falls back to the function's own name when the assignment target has no qualified name"},
     {"file": CMP, "old": "        case Token.NUMBER:\n          return NodeUtil.getStringValue(parent);",
      "new": "        case Token.NUMBER:\n          return NodeUtil.getStringValue(parent);\n"
             "        case Token.ASSIGN: return NodeUtil.isGetProp(parent.getFirstChild()) ? parent.getFirstChild().getLastChild().getString() : null;",
      "why": "hop 3's key fallback names an assigned function after the last property of the target"},
     {"file": PA, "old": "        return Compiler.CodeBuilder.functionOrKeyName(fnNode, parent);",
      "new": "        return parent.getType() == Token.ASSIGN && parent.getFirstChild().getType() == Token.GETPROP "
             "? parent.getFirstChild().getLastChild().getString() : Compiler.CodeBuilder.functionOrKeyName(fnNode, parent);",
      "why": "hop 2 names a function assigned to a property after that property"},
   ],
 },
 "host_notes": "Hosts for seed 4011 (mr_lib preview, target com/google/javascript/jscomp/NodeUtil.java), draw order: "
               "rhino.TokenStream, jscomp.jsonml.Reader, jscomp.regex.RegExpTree, rhino.Parser, jscomp.parsing.JsDocInfoParser, "
               "rhino.Node, jscomp.Compiler, rhino.jstype.JSTypeRegistry, jscomp.DefaultPassConfig, jscomp.TypeCheck (preview "
               "with n=10). Each hop position i was filled with the next drawn host whose anchor at the recipe's own seed "
               "(4011+100+i) is usable; a host is unusable when the anchor's enclosing class cannot be reached from the calling "
               "hop or a static method there does not compile. Hop 1: TokenStream (anchor after getTokenno, outer public class; "
               "rhino uses 4-space indentation). Hop 2: skipped jsonml.Reader (the compile target excludes **/jsonml/**, and the "
               "anchor lies in a private enum), regex.RegExpTree (anchor in the package-private nested class LookaheadAssertion, "
               "not visible from rhino); took Parser (anchor after parse, outer public class). Hop 3: skipped RegExpTree (anchor "
               "in package-private RegExpTreeAtom), parsing.JsDocInfoParser (private static ExtractionInfo), rhino.Node (private "
               "static StringNode); took Compiler (anchor after toString in public static Compiler.CodeBuilder). Hop 4: skipped "
               "RegExpTree (package-private RegExpTreeAtom, other package), JsDocInfoParser (private ExtractionInfo), Node "
               "(private static NumberNode); took JSTypeRegistry (no interior anchor: appended before the class's closing "
               "brace). Hop 5: skipped RegExpTree (package-private WordBoundary), JsDocInfoParser, Node (private static "
               "ObjectPropListItem), DefaultPassConfig (non-static private inner class GlobalTypeResolver); took TypeCheck "
               "(appended before the class's closing brace). The gold and hop 3 sit in package jscomp, so they can call "
               "NodeUtil's package-private helpers (isGetProp, isThis, isName, getStringValue). The rhino hops call into jscomp "
               "(hop 2 imports Compiler, hop 4 imports TypeCheck), which compiles in the single source tree. Nested-class hops "
               "carry the binary name (Compiler$CodeBuilder). The recipe indents inserted text by 4 spaces and the facade body "
               "by 8: the rhino hops (4-space file style) match; the jscomp/jstype hops are written in 2-space style, so the "
               "nested CodeBuilder member matches and the two appended top-level hops and the facade body are off by 2 "
               "(cosmetic, recipe-wide for Closure).",
}
