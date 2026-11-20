"""Main run Closure-60 (C10 recipe on the fixed checkout of Defects4J Closure-60; the real bug modified NodeUtil, the target class).

Facade: NodeUtil.getSourceName(Node) (the allowed target, BATCH4_PREREGISTRATION.md row Closure-60). Its javadoc states the
contract: "@return The source name property on the node or its ancestors." Its production callers (RuntimeTypeCheck,
CreateSyntheticBlocks, TypedScopeCreator, RecordFunctionInformation, GlobalVarReferenceMap, TypeInference, ExternExportsPass) all
go through the chain; its only direct test caller is NodeUtilTest::testGetSourceName.
Original computation: starting at the node, take the source file name recorded on the node; while none is found and a node is
left, move to the parent and take the name recorded there; return the first name found, or null (a null node gives null).

Chain (hosts in draw order for seed 7843, unusable hosts skipped, see host_notes):
  hop 1 rhino.Parser.sourceNameOf                   decision: a null node belongs to no source file (null)
  hop 2 rhino.jstype.JSTypeRegistry.getSourceNameForNode   decision: a node that records a source file name of its own
                                                    belongs to that file
  hop 3 jscomp.Compiler$CodeBuilder.sourceFileOf    pass-through
  hop 4 rhino.TokenStream.getNodeSourceFileName     pass-through
  hop 5 jscomp.TypeCheck.findSourceName             GOLD: the walk from the node up through its ancestors; it stops at the
                                                    first node that is a SCRIPT or records a source file name and returns the
                                                    name recorded there (null when the walk runs off the tree)
The correct configuration returns the original result on every tree the compiler builds: null for a null node, the node's own
name if it records one, otherwise the name recorded on the nearest ancestor that records one. (It differs from the original only
on a SCRIPT that records no name but sits below a node that does; the compiler's synthetic roots above the SCRIPTs record none.)

Fault (one-line omission in the gold's per-node decision): the stop test `if (current.getType() == Token.SCRIPT
|| current.getSourceFileName() != null) {` loses its second line, so the walk stops only at a SCRIPT and returns the name
recorded there. The variant reads as an ordinary "file of the enclosing script" lookup. In the compiler's own trees every node
the parser creates records its file and lies under its input's SCRIPT, so the result is unchanged there; a tree whose name is
recorded on a node that is not a SCRIPT, with no SCRIPT on the way up, gets null.
Trigger: the EXISTING test NodeUtilTest::testGetSourceName: a BLOCK n below a parent BLOCK that records "foo" (no SCRIPT in the
tree); assertEquals("foo", NodeUtil.getSourceName(n)) fails with expected:<foo> but was:<null>.
The gold's javadoc states the idiomatic contract (the name of the source file that a node belongs to) and is silent on which nodes
the walk stops at; n belongs to "foo", the name recorded on its ancestor (the facade's own contract).

External pins (convention outside the gold: the name recorded on an enclosing node that is not a SCRIPT names the file of the
nodes below it, and a node's own record counts whatever its kind):
NodeTraversal.traverseAtScope takes the source name of every node in a function scope from the FUNCTION root's own record;
SyntacticScopeCreator.scanRoot does the same for a FUNCTION scope root; Node.copyInformationFrom gives a new node the file
recorded on the node it is made from, so records live on ordinary nodes, not only on SCRIPTs; IRFactory.createTemplateNode makes
every node the parser creates record its file. Passing tests: CreateSyntheticBlocksTest::testUnmatchedStartMarker (the warning
for a CALL node gets its source name through NodeUtil.getSourceName, and CompilerTestCase requires it to be non-empty);
GlobalVarReferenceMapTest (a detached SCRIPT root asks NodeUtil.getSourceName and requires a non-null name);
AstValidatorTest::testValidScript (a SCRIPT records its own source name).

Single owner: only the gold walks the tree and decides at which node the walk stops. Hops 1-2 answer a null node and a node with
its own name; hops 3-4 hand a nameless node on. On the trigger tree the gold returns null for every node it can be given (no node
in that tree is a SCRIPT), so no one-line edit above the gold that keeps the gold's output as the result can produce "foo".
Declared alternatives (G9): hop 1 answers a node with neither a parent nor a name of its own, hop 3 starts the search at the
parent, hop 4 answers a node without a parent from its own name; each still returns null on the trigger input.
Recorded one-line edits above the gold that pass the trigger (bypasses / test-fitted, see the probe log
logs/bypass_probe_Closure-60.log for the full-suite results):
 B-0 bypass: hop 3 or hop 4 answers a nameless node by recursion through the facade,
     `return n.getParent() == null ? null : com.google.javascript.jscomp.NodeUtil.getSourceName(n.getParent());`,
     so the gold is never called.
 B-1 bypass: hop 4 replaces a null result of the gold by a second walk through the facade,
     `return TypeCheck.findSourceName(n) != null || n.getParent() == null ? TypeCheck.findSourceName(n) : com.google.javascript.jscomp.NodeUtil.getSourceName(n.getParent());`:
     on the trigger input the gold's output is discarded and the walk is done again above the gold.
 B-2 test-fitted: hop 2 also takes the parent's own name,
     `return own != null ? own : n.getParent() != null && n.getParent().getSourceFileName() != null ? n.getParent().getSourceFileName() : Compiler.CodeBuilder.sourceFileOf(n);`:
     the gold is not called on the trigger input, and a nameless node two levels below a named non-SCRIPT node still gets null,
     so the facade's contract (the node or its ancestors) is still broken.

Lie: the facade's javadoc claims every name found is also stored in a map keyed by node and a later request for the same node is
answered from that map; the chain keeps no map. It names neither the walk nor any step that is omitted nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (`for (Node current = n; current != null; current = current.getParent()) { if (current.getType() == Token.SCRIPT
 || current.getSourceFileName() != null) { return current.getSourceFileName(); } } return null;`):
  T1 absent: n is the walk's start node; its kind and its recorded name decide the result.
  T2 absent: current is the cursor, assigned by the loop update and read by the condition, the test and the return; the if has a
     live effect (returns); no other local.
  T3 absent: one node kind (SCRIPT) is named, one of a set of many token types, with no sibling kind handled; no pair or range
     ends are named in the text; the javadoc names no class.
  T4 absent: the javadoc names only the source file that a node belongs to, a general description the walk addresses; no rule,
     bound, value class or case.
 Variant gold (javadoc, signature, `for (Node current = n; current != null; current = current.getParent()) { if
 (current.getType() == Token.SCRIPT) { return current.getSourceFileName(); } } return null;`):
  T1 absent: n is the start of the walk; its kind and its ancestors' kinds decide which name is returned.
  T2 absent: current is the loop cursor and is assigned by the loop update; it is read by the loop condition, the test and the
     return; the if returns (a live decision); there is no other local and no literal-initialised local.
  T3 absent: exactly one member (SCRIPT) of the many token types is handled and no sibling kind gets the same treatment ('One
     member of a larger unnamed set'); the walk covers the node and every ancestor up to the top (the loop runs until current is
     null), so no end of the path is left out; no pair is involved; the gold's text names no class it handles in part.
  T4 absent: 'Returns the name of the source file that a node belongs to', '@param n the node' and '@return the name of the
     source file that the node belongs to' are general descriptions that the walk addresses; no limit, value class, case or
     property is named; no inline comment; the identifiers (findSourceName, current) name nothing the body does not meet."""

NU = "src/com/google/javascript/jscomp/NodeUtil.java"
PAR = "src/com/google/javascript/rhino/Parser.java"
JTR = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"

GOLD_TEXT = '''/**
 * Returns the name of the source file that a node belongs to.
 *
 * @param n the node
 * @return the name of the source file that the node belongs to
 */
public static String findSourceName(Node n) {
  for (Node current = n; current != null; current = current.getParent()) {
    if (current.getType() == Token.SCRIPT
        || current.getSourceFileName() != null) {
      return current.getSourceFileName();
    }
  }
  return null;
}'''

HOP1 = '''/**
 * Returns the name of the source file that a node belongs to. A null node
 * belongs to no source file.
 *
 * @param node the node, may be null
 * @return the name of the source file that the node belongs to, or null
 *     for a null node
 */
public static String sourceNameOf(Node node)
{
    if (node == null) {
        return null;
    }
    return JSTypeRegistry.getSourceNameForNode(node);
}'''

HOP2 = '''/**
 * Returns the name of the source file that a node belongs to. A node that
 * records a source file name of its own belongs to that file.
 *
 * @param n the node
 * @return the name of the source file that the node belongs to
 */
public static String getSourceNameForNode(Node n) {
  String own = n.getSourceFileName();
  return own != null ? own : Compiler.CodeBuilder.sourceFileOf(n);
}'''

HOP3 = '''/**
 * Returns the name of the source file that a node belongs to, for a node
 * that records no source file name of its own.
 *
 * @param n the node, which records no source file name of its own
 * @return the name of the source file that the node belongs to
 */
public static String sourceFileOf(Node n) {
  return TokenStream.getNodeSourceFileName(n);
}'''

HOP4 = '''/**
 * Returns the name of the source file that a node belongs to, for a node
 * that records no source file name of its own.
 *
 * @param n the node, which records no source file name of its own
 * @return the name of the source file that the node belongs to
 */
public static String getNodeSourceFileName(Node n)
{
    return TypeCheck.findSourceName(n);
}'''

DESIGN = {
 "instance": "Closure-60", "project": "Closure", "bug_id": 60, "seed": 7843,
 "src_root": "src", "test_root": "test",
 "facade": {"file": NU, "class": "com.google.javascript.jscomp.NodeUtil", "method": "getSourceName", "near_line": 2884},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/NodeUtilTest.java",
             "test_class": "com.google.javascript.jscomp.NodeUtilTest", "test_method": "testGetSourceName"},
 "expected_signature": "expected:<foo> but was:<null>",
 "gold": {"method": "findSourceName", "text": GOLD_TEXT,
          "fault": {"old": "        if (current.getType() == Token.SCRIPT\n"
                           "            || current.getSourceFileName() != null) {\n"
                           "          return current.getSourceFileName();",
                    "new": "        if (current.getType() == Token.SCRIPT) {\n"
                           "          return current.getSourceFileName();"}},
 "chain": {
   "facade_body": "return com.google.javascript.rhino.Parser.sourceNameOf(n);",
   "lie": "Each name that is found is also stored in a map keyed by node, and a later request for the same node is "
          "answered from that map.",
   "hops": [
     {"file": PAR, "class": "com.google.javascript.rhino.Parser", "method": "sourceNameOf",
      "imports": ["com.google.javascript.rhino.jstype.JSTypeRegistry"], "text": HOP1},
     {"file": JTR, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "getSourceNameForNode",
      "imports": ["com.google.javascript.jscomp.Compiler"], "text": HOP2},
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "sourceFileOf",
      "imports": ["com.google.javascript.rhino.TokenStream"], "text": HOP3},
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "getNodeSourceFileName",
      "imports": ["com.google.javascript.jscomp.TypeCheck"], "text": HOP4},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "findSourceName", "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.NodeTraversal::traverseAtScope",
              "com.google.javascript.jscomp.SyntacticScopeCreator::scanRoot",
              "com.google.javascript.rhino.Node::copyInformationFrom",
              "com.google.javascript.jscomp.parsing.IRFactory::createTemplateNode"],
 "ownership_reason": "Only the gold walks the tree from a node that records no source file name and decides at which node the "
                     "walk stops; hop 1 answers a null node, hop 2 a node with a name of its own, and hops 3-4 hand a "
                     "nameless node on. The facade's contract is 'the source name property on the node or its ancestors': "
                     "a nameless node belongs to the file recorded on its nearest ancestor that records one, whatever that "
                     "ancestor's kind. On the trigger tree (a BLOCK below a BLOCK that records \"foo\", no SCRIPT) the gold "
                     "walks past the recording ancestor and returns null for every node it can be given, so no caller that "
                     "keeps the gold's output can recover the name without walking the tree again itself. The convention "
                     "that a record on a node that is not a SCRIPT names the file of the nodes below it is pinned outside "
                     "the gold: NodeTraversal.traverseAtScope and SyntacticScopeCreator.scanRoot take the source name for a "
                     "whole function scope from the FUNCTION root's own record; Node.copyInformationFrom and "
                     "IRFactory.createTemplateNode put the record on ordinary nodes (every parsed node, every node made from "
                     "another), not only on SCRIPTs; CreateSyntheticBlocksTest.testUnmatchedStartMarker reports a warning "
                     "whose source name comes from a CALL node's own record through NodeUtil.getSourceName and CompilerTestCase "
                     "requires that name; GlobalVarReferenceMapTest and AstValidatorTest pin that a SCRIPT's own record "
                     "counts. The gold's javadoc promises the name of the source file that the node belongs to; the "
                     "trigger's node hangs below an ancestor that records \"foo\".",
 "ownership_tests": ["com.google.javascript.jscomp.CreateSyntheticBlocksTest::testUnmatchedStartMarker",
                     "com.google.javascript.jscomp.GlobalVarReferenceMapTest::testUpdateGlobalVarReferences_UpdateScriptNoRef",
                     "com.google.javascript.jscomp.GlobalVarReferenceMapTest::testUpdateGlobalVarReferences_UpdateScriptNewRefs",
                     "com.google.javascript.jscomp.AstValidatorTest::testValidScript"],
 "compensating": {
   "chain": [
     {"file": PAR, "old": "if (node == null) {",
      "new": "if (node == null || node.getParent() == null && node.getSourceFileName() == null) {",
      "why": "hop 1 also answers a node that has neither a parent nor a source file name of its own"},
     {"file": CMP, "old": "return TokenStream.getNodeSourceFileName(n);",
      "new": "return TokenStream.getNodeSourceFileName(n.getParent() != null ? n.getParent() : n);",
      "why": "hop 3 starts the search at the parent of a node that records no source file name"},
     {"file": TS, "old": "return TypeCheck.findSourceName(n);",
      "new": "return n.getParent() == null ? n.getSourceFileName() : TypeCheck.findSourceName(n);",
      "why": "hop 4 answers a node without a parent from its own source file name"},
   ],
 },
 "host_notes": "Hosts for seed 7843 (mr_lib preview, target com/google/javascript/jscomp/NodeUtil.java), draw order: rhino.Parser, "
               "rhino.jstype.JSTypeRegistry, jscomp.regex.RegExpTree, jscomp.jsonml.Reader, jscomp.parsing.JsDocInfoParser, "
               "rhino.Node, jscomp.Compiler, rhino.TokenStream, jscomp.TypeCheck, jscomp.DefaultPassConfig (the whole usable "
               "pool). Each hop position i was filled with the next drawn host whose anchor at the recipe's own seed "
               "(7843+100+i) lies in a class that the calling hop can reach and in which a static method compiles: hop 1 "
               "Parser (anchor after the Parser constructor, in the public outer class); hop 2 JSTypeRegistry (appended at "
               "the end of the class); hop 3: skipped RegExpTree (anchor in the package-private nested class "
               "RegExpTree.LookaheadAssertion, not visible from rhino.jstype), jsonml.Reader (private enum Reader.Operator; "
               "jsonml is also excluded from the main compile), JsDocInfoParser (private static class ExtractionInfo), "
               "Node (private static class ObjectPropListItem), took Compiler (public static nested class "
               "Compiler.CodeBuilder); hop 4 TokenStream (anchor after isJSIdentifier, in the public outer class); hop 5 "
               "TypeCheck (appended at the end of the class). The skipped hosts are unusable at every hop position (their "
               "anchors at seeds 7943-7947 all lie in private or package-private nested classes). The facade calls hop 1 by "
               "its fully-qualified name; each hop imports the next host (JSTypeRegistry already imports Node; TypeCheck "
               "already imports Node and Token). Parser and TokenStream are Rhino-style files (4-space indentation, method "
               "braces on their own line) and their hops follow that style; the other hosts use Closure's 2-space style. The "
               "recipe indents inserted text by 4 spaces and the facade body by 8, which matches the nested CodeBuilder and "
               "the Rhino files but is off by 2 for the facade and the two appended 2-space hops (cosmetic, recipe-wide for "
               "Closure).",
}
