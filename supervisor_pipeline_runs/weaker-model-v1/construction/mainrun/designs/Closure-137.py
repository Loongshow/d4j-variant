"""Main run Closure-137 (C10 recipe on the fixed checkout of Defects4J Closure-137; the real bug modified NodeUtil, the target class).

Facade: NodeUtil.getVarsDeclaredInBranch(Node) (the only allowed target, BATCH4_PREREGISTRATION.md row Closure-137). Its test
caller is NodeUtilTest::testGetVarsDeclaredInBranch; its production caller is NodeUtil.redeclareVarsInsideBranch, which
FoldConstants (dead if / while / for), UnreachableCodeElimination and RemoveTryCatch call before they remove a branch.
Original computation: a pre-order walk of the tree that does not enter the children of a FUNCTION node (the predicate
not(MatchNodeType(FUNCTION)) of visitPreOrder); every NAME node whose parent is a VAR is recorded in a LinkedHashMap under its
name unless the name is already there (the private VarCollector); the map's values are returned.

The facade body becomes one delegating call (the original had no argument guard) to a five-hop chain. Hosts in draw order for
seed 2647 (mr_lib preview, target com/google/javascript/jscomp/NodeUtil.java), unusable hosts replaced by the next drawn hosts
(see host_notes):
  hop 1 rhino.Parser.declaredNameNodes           fold: takes the values of the map of declared names
  hop 2 rhino.TokenStream.declaredNameMap        placement: creates the insertion-ordered map and has it filled
  hop 3 jscomp.TypeCheck.recordDeclaredVars      pass-through
  hop 4 rhino.Node.putDeclaredVars               pass-through
  hop 5 jscomp.Compiler$CodeBuilder.addVarNames  GOLD: the recursive walk with the per-node core: at a VAR, each declared name is
                                                 recorded unless already present; any other node except a FUNCTION is entered
The correct configuration returns the original collection (same LinkedHashMap, same pre-order, same first-declaration rule, same
function boundary). The gold does not walk into the subtree of a VAR, which the original does: below a VAR there are only its NAME
children and their initialiser expressions, and an expression contains a var statement only inside a function, which the
original does not enter either, so the result is the same for every tree the parser builds (SyntacticScopeCreator.scanVars returns
after a VAR in the same way). The private VarCollector, no longer used, is removed together with its two imports (Maps, Map) by a
behaviour-preserving pre-edit; it would otherwise be a dead duplicate of the gold's per-node step.

Fault (one-line omission of a decision in the gold): `} else if (n.getType() != Token.FUNCTION) {` becomes `} else {`, so the
walk enters functions and records the variables declared inside them. Trigger: the EXISTING test NodeUtilTest::
testGetVarsDeclaredInBranch; its first three assertions hold, and the fourth, getVarsDeclaredInBranch(parse("function(){var foo;}"))
== {}, fails at NodeUtilTest.java:459 with expected:<[]> but was:<[foo]>. The only other test that reaches a function inside a
removed branch, FoldConstantsTest::testVarLifting ("if(false)var a=function(){var b};" -> "var a"), still passes on the variant:
that function sits in a var initialiser, below a VAR, where the gold does not walk. With a walk that also entered VAR subtrees the
same omission fails testVarLifting too (checked in a scratch copy), which is why the gold stops at a VAR.
The gold's javadoc states the idiomatic contract (the variables that a node tree declares with its var statements, each mapped to
the first node that declares it) and is silent on functions. A var statement declares a variable of the function in whose body it
stands: "function(){var foo;}" declares an anonymous function, and foo is that function's own variable, not one the tree declares.

External pins (convention outside the gold): the facade's own javadoc ('excluding descent scopes'); NodeUtil.redeclareVarsInsideBranch
('finds all the VAR declarations in that tree that are not in an inner scope'); SyntacticScopeCreator.scanVars (its FUNCTION case
returns: 'should not examine function's children'; its VAR case declares the names and returns), pinned by
SyntacticScopeCreatorTest::testFunctionScope ('[function bar2() { var y; }]' -> y not declared in the outer scope);
NodeUtil.containsTypeInOuterScope ('Does not traverse into functions', same predicate). FoldConstantsTest::testVarLifting
('var a=function(){var b}' lifts only a) and UnreachableCodeEliminationTest::testRemovalRequiresRedeclaration pin the production
caller's use of the chain and pass on the variant.

Single owner: only the gold walks the tree and decides, node by node, where to descend; hops 1 and 2 hold the root and the map,
hops 3 and 4 pass them along. No one-line change above the gold can keep the walk out of every function at any depth: that needs
a traversal with a function test (a second implementation). Declared alternatives (G9): hop 4 skips a tree that is itself a
function, hop 3 skips a tree that contains a function (NodeUtil.containsType), hop 2 leaves the map empty for a tree that is itself
a function; each still fails the trigger.
Recorded edits above the gold (checked on the variant in a scratch copy):
 B-1 test-fitted, passes the trigger and the full suite (0 failing tests): hop 4 applies the gold to the root's children and skips
     the children that are functions, keeping a VAR root whole:
     `if (root.getType() == Token.VAR) Compiler.CodeBuilder.addVarNames(root, names); else for (Node c = root.getFirstChild(); c != null; c = c.getNext()) if (c.getType() != Token.FUNCTION) Compiler.CodeBuilder.addVarNames(c, names);`
     It only removes functions that are direct children of the root, which is where the trigger's function stands. A function one
     level deeper is still entered (getVarsDeclaredInBranch(parse("if(x){(function(){var y})()}")) gives {y}; a dead
     "if(false){function f(){var y}}" would lift y), and a FUNCTION root now yields the variables of its own body where the
     original yields none. It contradicts the facade's 'excluding descent scopes' and every hop's documented result: not a repair.
     Without the VAR case the same loop fails three UnreachableCodeEliminationTest tests (a VAR root loses its names).
 B-2 bypass, not one line: re-implementing the walk with NodeUtil.visitPreOrder and an anonymous Visitor at hop 3 (it needs the
     map parameter made final as well) replaces the gold's result and makes hop 4 dead. Reusing SyntacticScopeCreator at hop 3
     (`createScope(root, null).getVars()`) fails ten tests (it requires a function or global root and also declares function names).
 B-0 the facade's original body cannot be restored in one line, since its VarCollector is removed.

Lie: the facade's javadoc claims the tree is walked breadth first, level by level, and each name is kept with the declaration
nearest to the root; the chain walks depth first in document order and keeps the first declaration met. It names neither
functions nor scopes nor any step that is omitted nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (if VAR: record each child's name unless present; else if not FUNCTION: recurse into every child):
  T1 absent: n decides both branches and supplies the children; names is read (containsKey), written (put) and passed down.
  T2 absent: the cursors name and child advance in their for headers; no literal-initialised local, flag, counter or best-so-far;
     the VAR branch, the FUNCTION decision and the containsKey test each change the map.
  T3 absent: two node types are tested with different treatments (VAR recorded, FUNCTION not entered); no pair, range end or
     named class; the javadoc names 'var statements', which are all recorded.
  T4 absent: 'declares with its var statements' and 'the first node that declares it' are what the VAR branch and the containsKey
     test do; '@param n the root of the tree' is a description; no limit, bound, value class or case. Before choosing the omission
     the wording was checked for patterns: 'NAME node' was left out of the gold's text (no line tests the node type of a VAR's
     children) and 'declared variables' was narrowed to 'var statements' (function names and catch variables are declarations
     the gold does not record).
 Variant gold (javadoc, signature, `if (n.getType() == Token.VAR) { for (name ...) if (!names.containsKey(...)) names.put(...); }
 else { for (child ...) addVarNames(child, names); }`):
  T1 absent: n is read by the type test and the two child loops; names by containsKey, put and the recursive call; both change the
     map.
  T2 absent: the cursors name and child are advanced by their for headers; no dead or frozen local; the if/else has two different
     effects (record the names, or descend), and the inner containsKey test decides whether put runs.
  T3 absent: exactly one node type (VAR) is tested, in an unnamed set of many token types (one member of a larger unnamed set);
     no two members get the same treatment while another gets none; no pair halves or range ends; the only class the text names,
     var statements, is fully handled (every VAR reached is recorded); key and value are both stored.
  T4 absent: 'the variables that a node tree declares with its var statements' is a general description that the VAR branch
     addresses; 'mapping each name to the first node that declares it' is met by the containsKey test; no concrete rule, limit,
     bound, value class, case or property is named; no inline comment; identifiers (name, child, names) name nothing unmet."""

NU = "src/com/google/javascript/jscomp/NodeUtil.java"
PAR = "src/com/google/javascript/rhino/Parser.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"
NODE = "src/com/google/javascript/rhino/Node.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"

GOLD_TEXT = '''/**
 * Adds the variables that a node tree declares with its var statements
 * to a map, mapping each name to the first node that declares it.
 *
 * @param n the root of the tree
 * @param names the map to add the variables to
 */
public static void addVarNames(Node n, Map<String, Node> names) {
  if (n.getType() == Token.VAR) {
    for (Node name = n.getFirstChild(); name != null; name = name.getNext()) {
      if (!names.containsKey(name.getString())) {
        names.put(name.getString(), name);
      }
    }
  } else if (n.getType() != Token.FUNCTION) {
    for (Node child = n.getFirstChild(); child != null; child = child.getNext()) {
      addVarNames(child, names);
    }
  }
}'''

HOP1 = '''/**
 * Returns the NAME nodes of the variables that a node tree declares with
 * its var statements, one node for each name, in the order in which the
 * names are first declared.
 *
 * @param root the root of the tree
 * @return the NAME node that first declares each variable
 */
public static Collection<Node> declaredNameNodes(Node root)
{
    return TokenStream.declaredNameMap(root).values();
}'''

HOP2 = '''/**
 * Returns a map from the name of each variable that a node tree declares
 * with its var statements to the NAME node that first declares it, in the
 * order in which the names are first declared.
 *
 * @param root the root of the tree
 * @return the map of the declared variables
 */
public static Map<String, Node> declaredNameMap(Node root)
{
    Map<String, Node> names = new LinkedHashMap<String, Node>();
    TypeCheck.recordDeclaredVars(root, names);
    return names;
}'''

HOP3 = '''/**
 * Adds the variables that a node tree declares with its var statements to
 * a map from each name to the NAME node that first declares it.
 *
 * @param root the root of the tree
 * @param names the map to add the variables to
 */
public static void recordDeclaredVars(Node root, Map<String, Node> names) {
  Node.putDeclaredVars(root, names);
}'''

HOP4 = '''/**
 * Adds the variables that a node tree declares with its var statements to
 * a map from each name to the NAME node that first declares it.
 *
 * @param root the root of the tree
 * @param names the map to add the variables to
 */
public static void putDeclaredVars(Node root, Map<String, Node> names)
{
    Compiler.CodeBuilder.addVarNames(root, names);
}'''

FACADE_DOC = '''  /**
   * Retrieves vars declared in the current node tree, excluding descent scopes.
   */'''

VARCOLLECTOR = '''  private static class VarCollector implements Visitor {
    final Map<String, Node> vars = Maps.newLinkedHashMap();

    public void visit(Node n) {
      if (n.getType() == Token.NAME) {
        Node parent = n.getParent();
        if (parent != null && parent.getType() == Token.VAR) {
          String name = n.getString();
          if (!vars.containsKey(name)) {
            vars.put(name, n);
          }
        }
      }
    }
  }

''' + FACADE_DOC

DESIGN = {
 "instance": "Closure-137", "project": "Closure", "bug_id": 137, "seed": 2647,
 "src_root": "src", "test_root": "test",
 "facade": {"file": NU, "class": "com.google.javascript.jscomp.NodeUtil", "method": "getVarsDeclaredInBranch", "near_line": 1659},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/NodeUtilTest.java",
             "test_class": "com.google.javascript.jscomp.NodeUtilTest", "test_method": "testGetVarsDeclaredInBranch"},
 "expected_signature": "expected:<[]> but was:<[foo]>",
 "gold": {"method": "addVarNames", "text": GOLD_TEXT,
          "fault": {"old": "      } else if (n.getType() != Token.FUNCTION) {\n"
                           "        for (Node child = n.getFirstChild(); child != null; child = child.getNext()) {\n"
                           "          addVarNames(child, names);",
                    "new": "      } else {\n"
                           "        for (Node child = n.getFirstChild(); child != null; child = child.getNext()) {\n"
                           "          addVarNames(child, names);"}},
 "pre_edits": {
   "chain": [
     {"file": NU, "old": "import com.google.common.collect.Maps;\n", "new": ""},
     {"file": NU, "old": "import java.util.Map;\n", "new": ""},
     {"file": NU, "old": VARCOLLECTOR, "new": FACADE_DOC},
   ],
 },
 "chain": {
   "facade_body": "return com.google.javascript.rhino.Parser.declaredNameNodes(root);",
   "lie": "The tree is walked breadth first, one level at a time, and each name is kept with the declaration that "
          "lies nearest to the root.",
   "hops": [
     {"file": PAR, "class": "com.google.javascript.rhino.Parser", "method": "declaredNameNodes",
      "imports": ["java.util.Collection"], "text": HOP1},
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "declaredNameMap",
      "imports": ["java.util.LinkedHashMap", "java.util.Map", "com.google.javascript.jscomp.TypeCheck"], "text": HOP2},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "recordDeclaredVars",
      "imports": ["java.util.Map"], "text": HOP3},
     {"file": NODE, "class": "com.google.javascript.rhino.Node", "method": "putDeclaredVars",
      "imports": ["java.util.Map", "com.google.javascript.jscomp.Compiler"], "text": HOP4},
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "addVarNames",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.SyntacticScopeCreator::scanVars",
              "com.google.javascript.jscomp.NodeUtil::redeclareVarsInsideBranch",
              "com.google.javascript.jscomp.NodeUtil::containsTypeInOuterScope"],
 "ownership_reason": "Only the gold walks the tree and decides, node by node, where to descend; hop 2 creates the insertion-ordered "
                     "map, hop 1 returns its values, hops 3 and 4 pass the root and the map along. Once the walk has entered a "
                     "function, the names recorded there cannot be told apart from the tree's own by any caller, and keeping the "
                     "walk out of every function at any depth takes a traversal with a function test, that is, a second "
                     "implementation. The convention is pinned outside the gold: the facade's own javadoc ('excluding descent "
                     "scopes'); NodeUtil.redeclareVarsInsideBranch, its production caller ('all the VAR declarations in that tree "
                     "that are not in an inner scope'); SyntacticScopeCreator.scanVars, whose FUNCTION case returns ('should not "
                     "examine function's children') and whose VAR case declares the names and returns, with "
                     "SyntacticScopeCreatorTest.testFunctionScope ('[function bar2() { var y; }]': y is not declared in the outer "
                     "scope); NodeUtil.containsTypeInOuterScope ('Does not traverse into functions'). FoldConstantsTest."
                     "testVarLifting lifts only a from 'if(false)var a=function(){var b};' and UnreachableCodeEliminationTest."
                     "testRemovalRequiresRedeclaration exercises the production caller; both pass on the variant. A var statement "
                     "declares a variable of the function in whose body it stands, so 'function(){var foo;}' declares no variable "
                     "of the tree, which the gold's contract ('the variables that a node tree declares with its var statements') "
                     "then violates. A one-line edit at hop 4 that applies the gold to the root's children and skips the children "
                     "that are functions (keeping a VAR root whole) passes the existing tests, but only because the trigger's "
                     "function is a direct child of the root: a function one level deeper is still entered "
                     "(parse(\"if(x){(function(){var y})()}\") gives {y}) and a FUNCTION root then yields its own body's "
                     "variables, contradicting the facade's 'excluding descent scopes' and every hop's documented result.",
 "ownership_tests": ["com.google.javascript.jscomp.FoldConstantsTest::testVarLifting",
                     "com.google.javascript.jscomp.SyntacticScopeCreatorTest::testFunctionScope",
                     "com.google.javascript.jscomp.UnreachableCodeEliminationTest::testRemovalRequiresRedeclaration"],
 "compensating": {
   "chain": [
     {"file": NODE, "old": "    Compiler.CodeBuilder.addVarNames(root, names);",
      "new": "    if (root.getType() != Token.FUNCTION) Compiler.CodeBuilder.addVarNames(root, names);",
      "why": "hop 4 skips a tree that is itself a function"},
     {"file": TC, "old": "Node.putDeclaredVars(root, names);",
      "new": "if (!NodeUtil.containsType(root, Token.FUNCTION)) Node.putDeclaredVars(root, names);",
      "why": "hop 3 skips a tree that contains a function"},
     {"file": TS, "old": "    TypeCheck.recordDeclaredVars(root, names);",
      "new": "    if (root.getType() != Token.FUNCTION) TypeCheck.recordDeclaredVars(root, names);",
      "why": "hop 2 leaves the map empty for a tree that is itself a function"},
   ],
 },
 "host_notes": "Hosts for seed 2647 (mr_lib preview, target com/google/javascript/jscomp/NodeUtil.java, n=7; the usable pool has "
               "seven hosts besides the target, so the draw is exhausted at seven), draw order: rhino.Parser, "
               "jscomp.parsing.JsDocInfoParser, jscomp.DefaultPassConfig, rhino.Node, jscomp.Compiler, rhino.TokenStream, "
               "jscomp.TypeCheck. Drawn hosts 1, 4 and 5 are used at their own positions: hop 1 Parser (anchor after the "
               "three-argument constructor, outer class), hop 4 Node (anchor after getType, outer class), hop 5 Compiler (gold; "
               "anchor after CodeBuilder.toString, i.e. inside the public static nested class Compiler.CodeBuilder, so the gold "
               "is Compiler$CodeBuilder::addVarNames). Drawn host 2, JsDocInfoParser, is unusable: at every hop position's seed "
               "(2747-2751) the recipe's anchor lies inside the private static nested class ExtractionInfo, which no other class "
               "can call. Drawn host 3, DefaultPassConfig, is unusable: the anchor lies inside the private non-static inner "
               "class GlobalTypeResolver, where a static method does not compile. They are replaced by the next drawn hosts, in "
               "order: hop 2 TokenStream (drawn host 6; anchor after getToken, outer class) and hop 3 TypeCheck (drawn host 7; "
               "fewer than the recipe's minimum of 4-space-indented methods, so the hop is appended before the class's closing "
               "brace). Closure's jscomp code uses 2-space indentation and its rhino code 4-space; each hop text is written in its "
               "host's style, and the recipe's 4-space insertion indent leaves the appended TypeCheck hop and the facade body "
               "off by 2 (cosmetic, recipe-wide for Closure). The facade calls hop 1 by its fully-qualified name; hops 2 and 4 "
               "import the next host from jscomp; the import of jscomp.Compiler into rhino.Node shadows java.lang.Compiler.",
}
