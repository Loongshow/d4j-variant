"""Main run Closure-141 (C10 recipe on the fixed checkout of Defects4J Closure-141; the real bug modified NodeUtil and
PureFunctionIdentifier; NodeUtil is the target class).

Facade: NodeUtil.getVarsDeclaredInBranch(Node) (the only allowed target, BATCH5_PREREGISTRATION.md row 128; facade reuse of
Closure-137, recorded in batch5_tasks.json as facade_reuse_of). Its callers: NodeUtilTest::testGetVarsDeclaredInBranch (direct)
and the production caller NodeUtil.redeclareVarsInsideBranch, which FoldConstants, UnreachableCodeElimination and RemoveTryCatch
use when they delete a branch (FoldConstantsTest, UnreachableCodeEliminationTest and RemoveTryCatchTest reach the facade through it).
Original computation: a pre-order visit of the tree that does not descend below a FUNCTION node (the predicate
not(MatchNodeType(FUNCTION))); the private NodeUtil.VarCollector records every NAME node whose parent is a VAR, the first node per
name, in a LinkedHashMap; the facade returns the map's values.

Chain (hosts in draw order for seed 5130, mr_lib preview, target com/google/javascript/jscomp/NodeUtil.java; unusable hosts
skipped, see host_notes):
  hop 1 rhino.Node.getDeclaredVars              projection: the values of the map of first declarations
  hop 2 rhino.Parser.declaredVarMap             aggregation: creates the LinkedHashMap, has it filled, returns it
  hop 3 rhino.TokenStream.addVarDeclarations    pass-through
  hop 4 jscomp.TypeCheck.gatherVarDecls         pass-through
  hop 5 jscomp.Compiler$CodeBuilder.addBranchVars   GOLD: the recursive walk with the per-node rule (a NAME is a leaf and is
                                                recorded when a VAR declares it and its name is new; a FUNCTION is not
                                                entered; any other node is entered child by child)
The correct configuration returns the original result for every tree the parser builds: the same NAME nodes, in the same
(pre-order) order, the first node per name, nothing below a FUNCTION. The one difference in form is that the walk does not
enter the children of a NAME node. In this AST a NAME node has children only as the initializer of a var, an initializer is an
expression, and an expression can hold a VAR only inside a function, which neither version enters (SyntacticScopeCreator.scanVars
relies on the same fact: 'Variables can only occur in statement-level nodes'). A FUNCTION or a NAME as the root gives the original
result too (nothing, and the root itself when a VAR declares it). Full suite on the correct configuration: no failure (G1).

Fault (one-line omission of a decision in the gold): the condition of the else branch, `else if (n.getType() != Token.FUNCTION)`,
is dropped (`else`), so the walk enters nested functions and records their vars. The gold then reads as an ordinary declaration
walk (record the declared names, recurse into everything else). Trigger: the EXISTING test NodeUtilTest::testGetVarsDeclaredInBranch;
its first three assertions hold and assertNodeNames({}, getVarsDeclaredInBranch(parse("function(){var foo;}"))) fails with
expected:<[]> but was:<[foo]> (NodeUtilTest.java:459); the next assertion (var goo;function(){var foo;}) would fail the same way.
It is the only test that newly fails (gate G5 on the chain; also checked first on a one-hop version of the same gold):
the only other test whose branch holds a var inside a function is FoldConstantsTest::testVarLifting
('if(false)var a=function(){var b};' -> 'var a'), where the function is the initializer of a var, below a NAME, which the walk never
enters; it passes on the variant.

The gold's javadoc states the idiomatic contract (the vars declared in a branch, each name mapped to the NAME node of its first
declaration) and is silent on nested functions. foo is a var of the anonymous function, not of the script, so the variant violates
that contract on the trigger input. External pins (convention outside the gold): SyntacticScopeCreator.scanVars declares a
function's name and does not examine its children ('should not examine function's children'), pinned by
SyntacticScopeCreatorTest::testFunctionScope ('[function bar2() { var y; }]': y is not declared in the global scope);
NodeUtil.redeclareVarsInsideBranch, the facade's production caller, documents that it redeclares 'the VAR declarations in that
tree that are not in an inner scope', and FoldConstantsTest::testVarLifting expects 'if(false)var a=function(){var b};' to lift
only 'var a'; the facade's own javadoc ('excluding descent scopes'). UnreachableCodeEliminationTest::testRemovalRequiresRedeclaration
(two vars, first-declaration order) also runs the chain through the production caller and passes on the variant.

Single owner: only the gold walks the tree; hops 1-4 hold the root of the branch and the map and get the filled map back. Once
a nested function's var has been recorded under its name, nothing in the map tells where it was declared, and a later declaration
of the same name in the branch itself is never recorded (first declaration wins), so no caller can recover the branch's own
var by removing entries ('function g(){var a;} var a;' leaves no entry for the script's a). Declared
alternatives (G9): hop 4 skips a branch that contains a function (NodeUtil.containsType), hop 3 skips a branch that is itself a
function, hop 2 skips a branch whose first statement is a function; each still fails the trigger (the second and the third
leave the script root untouched; the first loses goo in 'var goo;function(){var foo;}').
Recorded one-line edits above the gold that pass the trigger (not declared; none is a repair consistent with the path; B-1 and
B-2 were checked on the variant in a scratch copy, defects4j test: 0 failing tests each):
 B-0 bypass: the facade restores a pre-order visit with an exclusion predicate (NodeUtil.visitPreOrder with an anonymous
     NodeUtil.Visitor and not(MatchNodeType(FUNCTION))); it needs a visitor that writes to a map, so a second implementation of
     the gold that discards the chain (the private VarCollector of the original is removed by a pre-edit, see below).
 B-1 test-fitted: hop 4 replaces its call by a loop over the root's children that calls the gold for every child that is not a
     function (`for (Node c = root.getFirstChild(); c != null; c = c.getNext()) { if (c.getType() != Token.FUNCTION) {
     Compiler.CodeBuilder.addBranchVars(c, vars); } }`). It passes the trigger and the suite because every function in the tests
     with a var inside is a direct child of the root or sits below a NAME, but a function one block deeper is still entered
     ('{ function f() { var y; } }' records y), so hop 4's documented result (the vars declared in the branch) does not hold, and
     a NAME root is no longer recorded.
 B-2 a post-filter at hop 4 written as one physical line after the call: an iterator loop over the map's values that removes
     every node NodeUtil.has cannot reach from the root without entering a function (Predicates.equalTo with
     not(MatchNodeType(FUNCTION))); a second implementation of the exclusion, multi-statement, and still not hop 4's
     documented result: when a nested function declares a name before the branch does, the branch's own var is lost
     ('function g(){var a;} var a;' gives no a).

Lie: the facade's javadoc claims the tree is first flattened level by level into a list of its nodes and the declared names in
that list are sorted alphabetically before their nodes are returned; the chain builds no list of nodes, walks the tree depth
first and keeps the order of first declaration. It names neither functions nor scopes nor any step that is omitted nor any hop.

Pre-edits (behaviour-preserving, needed by the recipe): the private NodeUtil.VarCollector (the original collector, used only by
the facade) is removed, with the two imports (Maps, java.util.Map) that only it used; after the facade rewrite it would be dead
code and a second implementation of the gold's recording rule beside the facade.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: n decides the branch taken, gives the parent, the name and the children; vars is read (containsKey), written (put)
     and passed on; each changes the map.
  T2 absent: the local parent is read in the condition that decides the put; the cursor c is advanced by its for header; no
     literal-initialised local, flag, counter or best-so-far; the NAME branch records, the FUNCTION condition stops the walk,
     the remaining branch recurses: three different effects.
  T3 absent: the gold names no class or set it handles in part; the type tests (NAME, VAR, FUNCTION) play three different roles,
     no two members of a closed set get the same treatment with a sibling left out; no pair or range end.
  T4 absent: 'the vars declared in a branch' is a general description that the walk addresses; 'each name mapped to the NAME
     node of its first declaration' is met by the containsKey test in a pre-order walk; '@param n the root of the branch' and
     '@param vars the map to add to' are parameter descriptions; no limit, bound or value class is named; no inline comment.
 Variant gold (javadoc, signature, `if (n.getType() == Token.NAME) { Node parent = n.getParent(); if (parent != null &&
 parent.getType() == Token.VAR && !vars.containsKey(n.getString())) { vars.put(n.getString(), n); } } else { for (Node c =
 n.getFirstChild(); c != null; c = c.getNext()) { addBranchVars(c, vars); } }`):
  T1 absent: n is read for its type, its parent, its name and its children; vars is read by containsKey, written by put and
     passed to the recursive call; each changes the map.
  T2 absent: parent reaches the condition that decides the put; c is the loop cursor and is advanced by the for header; no
     literal-initialised local; the if/else has two different effects (record a NAME, recurse into anything else) and the inner
     if decides the put.
  T3 absent: no set has a handled and an unhandled member: only NAME (as the node) and VAR (as its parent) are tested, with
     different roles, and the gold names no class it handles in part (it names vars, a branch, a map and NAME nodes); no
     halves of a pair, no range ends.
  T4 absent: 'Adds the vars declared in a branch to a map' is a general description the walk addresses; 'each name mapped to
     the NAME node of its first declaration' is met by `!vars.containsKey(n.getString())` before the put; the @param clauses
     are descriptions of the parameters; no concrete rule, bound, case or value class is named that the body does not meet; no
     comment; the identifiers (parent, c, vars, addBranchVars) name nothing the body does not do."""

NU = "src/com/google/javascript/jscomp/NodeUtil.java"
NODE = "src/com/google/javascript/rhino/Node.java"
PAR = "src/com/google/javascript/rhino/Parser.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"

GOLD_TEXT = '''/**
 * Adds the vars declared in a branch to a map, each name mapped to the
 * NAME node of its first declaration.
 *
 * @param n the root of the branch
 * @param vars the map to add to
 */
public static void addBranchVars(Node n, Map<String, Node> vars) {
  if (n.getType() == Token.NAME) {
    Node parent = n.getParent();
    if (parent != null && parent.getType() == Token.VAR
        && !vars.containsKey(n.getString())) {
      vars.put(n.getString(), n);
    }
  } else if (n.getType() != Token.FUNCTION) {
    for (Node c = n.getFirstChild(); c != null; c = c.getNext()) {
      addBranchVars(c, vars);
    }
  }
}'''

HOP1 = '''/**
 * Returns the vars declared in a branch of a tree, in the order of their
 * first declarations.
 *
 * @param root the root of the branch
 * @return the NAME node of the first declaration of each var
 */
public static Collection<Node> getDeclaredVars(Node root) {
  return Parser.declaredVarMap(root).values();
}'''

HOP2 = '''/**
 * Maps the name of each var declared in a branch of a tree to the NAME
 * node of its first declaration.
 *
 * @param root the root of the branch
 * @return the map, in the order of the first declarations
 */
public static Map<String, Node> declaredVarMap(Node root)
{
    Map<String, Node> vars = new LinkedHashMap<String, Node>();
    TokenStream.addVarDeclarations(root, vars);
    return vars;
}'''

HOP3 = '''/**
 * Adds the vars declared in a branch of a tree to a map, each name mapped
 * to the NAME node of its first declaration.
 *
 * @param root the root of the branch
 * @param vars the map to add the vars to
 */
public static void addVarDeclarations(Node root, Map<String, Node> vars) {
    TypeCheck.gatherVarDecls(root, vars);
}'''

HOP4 = '''/**
 * Adds the vars declared in a branch to a map, keyed by name.
 *
 * @param root the root of the branch
 * @param vars the map to add the vars to
 */
public static void gatherVarDecls(Node root, Map<String, Node> vars) {
  Compiler.CodeBuilder.addBranchVars(root, vars);
}'''

VAR_COLLECTOR = '''  private static class VarCollector implements Visitor {
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

  /**
   * Retrieves vars declared in the current node tree, excluding descent scopes.
   */'''

DESIGN = {
 "instance": "Closure-141", "project": "Closure", "bug_id": 141, "seed": 5130,
 "src_root": "src", "test_root": "test",
 "facade": {"file": NU, "class": "com.google.javascript.jscomp.NodeUtil", "method": "getVarsDeclaredInBranch", "near_line": 1667},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/NodeUtilTest.java",
             "test_class": "com.google.javascript.jscomp.NodeUtilTest", "test_method": "testGetVarsDeclaredInBranch"},
 "expected_signature": "expected:<[]> but was:<[foo]>",
 "gold": {"method": "addBranchVars", "text": GOLD_TEXT,
          "fault": {"old": "          vars.put(n.getString(), n);\n"
                           "        }\n"
                           "      } else if (n.getType() != Token.FUNCTION) {",
                    "new": "          vars.put(n.getString(), n);\n"
                           "        }\n"
                           "      } else {"}},
 "pre_edits": {
   "chain": [
     {"file": NU, "old": "import com.google.common.collect.Maps;\nimport com.google.javascript.rhino.FunctionNode;\n",
      "new": "import com.google.javascript.rhino.FunctionNode;\n"},
     {"file": NU, "old": "import java.util.List;\nimport java.util.Map;\nimport java.util.Set;\n",
      "new": "import java.util.List;\nimport java.util.Set;\n"},
     {"file": NU, "old": VAR_COLLECTOR,
      "new": "  /**\n   * Retrieves vars declared in the current node tree, excluding descent scopes.\n   */"},
   ],
 },
 "chain": {
   "facade_body": "return com.google.javascript.rhino.Node.getDeclaredVars(root);",
   "lie": "The tree is first flattened level by level into a list of its nodes, and the names declared in that list "
          "are sorted alphabetically before their nodes are returned.",
   "hops": [
     {"file": NODE, "class": "com.google.javascript.rhino.Node", "method": "getDeclaredVars",
      "imports": ["java.util.Collection"], "text": HOP1},
     {"file": PAR, "class": "com.google.javascript.rhino.Parser", "method": "declaredVarMap",
      "imports": ["java.util.LinkedHashMap", "java.util.Map"], "text": HOP2},
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "addVarDeclarations",
      "imports": ["java.util.Map", "com.google.javascript.jscomp.TypeCheck"], "text": HOP3},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "gatherVarDecls",
      "imports": ["java.util.Map"], "text": HOP4},
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "addBranchVars",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.SyntacticScopeCreator::scanVars",
              "com.google.javascript.jscomp.NodeUtil::redeclareVarsInsideBranch",
              "com.google.javascript.jscomp.NodeUtil::getVarsDeclaredInBranch"],
 "ownership_reason": "Only the gold walks the tree and decides, node by node, whether to record a declared name and whether to "
                     "enter a node's children; hops 1-4 hold the root of the branch and the map and get the filled map back, and "
                     "a nested function's var, once recorded under its name, cannot be told apart from a var of the branch by any "
                     "caller, and it keeps a later declaration of the same name in the branch itself from being recorded (first "
                     "declaration wins), so removing entries afterwards cannot restore the branch's own var. The convention is pinned outside the gold: SyntacticScopeCreator.scanVars declares a function's "
                     "name and does not examine the function's children, and SyntacticScopeCreatorTest.testFunctionScope "
                     "asserts that y in '[function bar2() { var y; }]' is not declared in the global scope; the facade's "
                     "production caller NodeUtil.redeclareVarsInsideBranch redeclares 'the VAR declarations in that tree that "
                     "are not in an inner scope', and FoldConstantsTest.testVarLifting lifts only 'var a' out of "
                     "'if(false)var a=function(){var b};'; the facade's own javadoc says 'excluding descent scopes'. The gold's "
                     "javadoc promises the vars declared in a branch, which foo, a var of the anonymous function in "
                     "'function(){var foo;}', is not. A one-line loop at hop 4 that calls the gold only for the root's children "
                     "that are not functions passes the existing tests but still enters a function one block deeper, so it does "
                     "not deliver hop 4's documented result.",
 "ownership_tests": ["com.google.javascript.jscomp.SyntacticScopeCreatorTest::testFunctionScope",
                     "com.google.javascript.jscomp.FoldConstantsTest::testVarLifting",
                     "com.google.javascript.jscomp.UnreachableCodeEliminationTest::testRemovalRequiresRedeclaration"],
 "compensating": {
   "chain": [
     {"file": TC, "old": "Compiler.CodeBuilder.addBranchVars(root, vars);",
      "new": "if (!NodeUtil.containsType(root, Token.FUNCTION)) { Compiler.CodeBuilder.addBranchVars(root, vars); }",
      "why": "hop 4 skips a branch that contains a function"},
     {"file": TS, "old": "TypeCheck.gatherVarDecls(root, vars);",
      "new": "if (root.getType() != Token.FUNCTION) { TypeCheck.gatherVarDecls(root, vars); }",
      "why": "hop 3 skips a branch that is itself a function"},
     {"file": PAR, "old": "TokenStream.addVarDeclarations(root, vars);",
      "new": "if (root.getFirstChild() == null || root.getFirstChild().getType() != Token.FUNCTION) { TokenStream.addVarDeclarations(root, vars); }",
      "why": "hop 2 skips a branch whose first statement is a function"},
   ],
 },
 "host_notes": "Hosts for seed 5130 (mr_lib preview, target com/google/javascript/jscomp/NodeUtil.java); the full draw is "
               "parsing.JsDocInfoParser, rhino.Node, DefaultPassConfig, rhino.Parser, rhino.TokenStream, TypeCheck, Compiler "
               "(pool exhausted at seven; FoldConstants and NameAnalyzer are package-private and outside the recipe's usable pool). Closure's jscomp code uses "
               "2-space indentation, so the recipe's anchor picker (which keeps only 4-space-indented methods) lands on members "
               "of nested classes there, or appends the hop before the outer class's closing brace when a file has too few such "
               "methods; the rhino files use 4-space members, so their anchors are in the top-level class. A host is unusable when "
               "the hop's enclosing class cannot be reached from the calling hop or a static method there does not compile. Each "
               "hop position i was filled with the next drawn host whose anchor at the recipe's own seed (5130+100+i) is usable: "
               "hop 1: skipped JsDocInfoParser (its only anchor, getString, is in the private static nested class "
               "JsDocInfoParser.ExtractionInfo, not visible from NodeUtil), took rhino.Node (anchor after hasOneChild, "
               "top-level); hop 2: skipped DefaultPassConfig (its only anchor, process, is in the private non-static inner "
               "class GlobalTypeResolver, where a static method does not compile and which no other class can see), took "
               "rhino.Parser (anchor after parse, top-level); hop 3 rhino.TokenStream (anchor after getToken, top-level); hop 4 "
               "TypeCheck (no admissible anchor, appended at the end of the class); hop 5 Compiler (anchor after getLength in "
               "the public static nested class Compiler.CodeBuilder; the gold's binary name is Compiler$CodeBuilder). This is "
               "the batch-5 pre-registration's disclosed Closure anchor deviation (one hop nested, one appended). Every "
               "remaining drawn host is used, in draw order. The facade calls hop 1 by its fully-qualified name; hops 2 and 3 "
               "are in hop 1's package; hop 3 imports TypeCheck; hop 4 calls Compiler.CodeBuilder in its own package. The recipe "
               "indents inserted text by 4 spaces and the facade body by 8; the rhino hops and the nested gold match their "
               "neighbours, the facade and the appended TypeCheck hop are off by 2 (cosmetic, recipe-wide for Closure).",
}
