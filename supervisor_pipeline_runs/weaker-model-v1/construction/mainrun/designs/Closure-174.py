"""Main run Closure-174 (C10 recipe on the fixed checkout of Defects4J Closure-174; the real bug modified JsAst, NodeUtil and
ScopedAliases, and NodeUtil is the target class).

Facade: NodeUtil.newQualifiedNameNode(CodingConvention, String) (allowed target, BATCH4_PREREGISTRATION.md row Closure-174). The
other two allowed targets were set aside: mapMainToClone and verifyScopeChanges are called for EVERY CompilerTestCase test
(CompilerTestCase.test builds the map and checks the changed scopes after each pass) and by PhaseOptimizer's sanity check, and
nothing else; verifyScopeChanges is a consistency check, so an omission there either relaxes it (no test fails) or makes it throw
for the thousands of pass tests, and an omission in mapMainToClone either leaves functions unmapped (the check then skips them:
no test fails) or loses the root (every pass test fails). Neither can give a fault that exactly one test catches (gate G5).
Original computation of the facade: a name without a dot gives a NAME node (newName: IR.name, marked IS_CONSTANT_NAME when
convention.isConstant); otherwise the text before the first dot is the root, a THIS node when it is "this" and else a NAME node
(newName), and every following dot-separated part becomes a STRING node (marked IS_CONSTANT_NAME when convention.isConstantKey)
that is the property of a GETPROP over the node built so far.

Chain (instance seed 5011, mr_lib preview target com/google/javascript/jscomp/NodeUtil.java; unusable drawn hosts replaced by
the next drawn hosts, see host_notes):
  hop 1 jscomp.Compiler$CodeBuilder.qualifiedNameTree      plumbing: splits the name at the dots (split("\\\\.", -1))
  hop 2 rhino.jstype.JSTypeRegistry.createDottedName       placement: the number of parts to use (parts.length)
  hop 3 rhino.JSDocInfo$Marker.dottedNameOf                pass-through
  hop 4 jscomp.CompilerOptions$TweakProcessing.accessPathOf pass-through
  hop 5 jscomp.SymbolTable$Symbol.qualifiedNameFrom        GOLD: the per-part core: the root node (THIS for a "this" root of a
                                                           dotted name, else a NAME marked by isConstant), then for every
                                                           further part a STRING marked by isConstantKey under a GETPROP
The correct configuration computes exactly the original result for every input: split("\\\\.", -1) yields the same parts as
the original indexOf scan (empty and trailing empty parts included); a name without a dot is one part, and the gold gives it the
original NAME node (the THIS case needs count > 1, as the original takes it only after a dot); the same isConstant /
isConstantKey marks and the same GETPROP nesting.

Fault (omission of a special-case step in the gold): the THIS case for the root is dropped, so the root of every name is a NAME
node; "this.prop" becomes GETPROP(NAME this, STRING prop) instead of GETPROP(THIS, STRING prop). The gold then reads as an
ordinary root-then-properties builder. Trigger: the EXISTING test NodeUtilTest::testNewQualifiedNameNode2, which expects
GETPROP(THIS, STRING prop) for "this.prop"; it fails with the tree-inequality message "Subtree1: THIS ... Subtree2: NAME this".
testNewQualifiedNameNode1 ("ns.prop") passes. Measured on a scratch copy of the fixture with the same omission in the original
method: the full suite has exactly one failing test, testNewQualifiedNameNode2 (production passes print NAME this and THIS the
same way, and no other test builds a this-rooted name through the facade). The gold's javadoc states the idiomatic contract
(the node representing the qualified name made of the parts) and is silent on the root kinds; in Closure's AST the qualified
name this.prop is GETPROP(THIS, STRING prop), never a NAME named "this", so the variant violates that contract on the trigger.

External pins (convention outside the gold): Node.getQualifiedName maps a THIS root to "this" (the inverse of the facade);
Node.isQualifiedName ('x or a.b.c or this.a', case THIS) and Node.isUnscopedQualifiedName ('without a "this" reference ... not
this.a', NAME root only); NodeUtil.getRootOfQualifiedName (beside the facade: the root 'Must be either NAME or THIS'). Passing
tests: NodeTest::testQualifiedName (GETPROP(THIS, b) is "this.b"), NodeTest::testIsQualifiedName (GETPROP(THIS, b) is a
qualified name), NodeUtilTest::testNewQualifiedNameNode1 (the GETPROP(NAME, STRING) shape).

Single owner: only the gold builds the root together with the properties; hop 1 holds the name, hops 2-4 hold the parts and get
back one finished tree. No part string makes the gold produce a THIS node (no pre-filter), and replacing the root of a finished
tree needs a search for the root plus a replaceChild (multi-statement); a hop can only avoid the gold for this-rooted names by
building the tree itself (B-1 below). Declared alternatives (G9): hop 1 returns a THIS node for
the bare name "this", hop 2 drops a leading "this" part, hop 4 returns a THIS node for a one-part name "this"; each still fails
the trigger.
Recorded bypasses (not declared; they replace the gold's result rather than repair the chain):
 B-0 the facade restores the original body, discarding all five hops.
 B-1 a hop answers a this-rooted name itself in a ternary and calls the gold only otherwise, either for two parts only, e.g.
     hop 4 `return count == 2 && "this".equals(parts[0]) ? IR.getprop(IR.thisNode(), IR.string(parts[1])) : SymbolTable.Symbol.qualifiedNameFrom(convention, parts, count);`
     (test-fitted: still NAME this for this.a.b), or for any length by recursing through the hop itself, e.g. hop 4
     `return count > 1 && "this".equals(parts[0]) ? IR.getprop(count == 2 ? IR.thisNode() : accessPathOf(convention, parts, count - 1), IR.string(parts[count - 1])) : SymbolTable.Symbol.qualifiedNameFrom(convention, parts, count);`.
     Both were checked at hop 4 on the variant in a scratch copy: the trigger passes. For a this-rooted name the gold's output
     is never used and the properties lose their isConstantKey marks: a second implementation of the gold's work (its root
     decision and its GETPROP nesting), not a repair of the chain. The same ternary is possible at hops 1-3 (with the name
     or the parts).
 B-2 a hop takes the gold's tree, finds its root (NodeUtil.getRootOfQualifiedName) and replaces it with a THIS node:
     multi-statement post-processing that rebuilds the omitted step outside the gold.

Lie: the facade's javadoc claims the name is scanned from its last dot back to its first and that the node of each prefix is
kept in a cache and reused for names sharing that prefix; the code splits the name from the first part to the last and keeps no
cache. It names neither the root nor "this" nor any omitted step nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: convention feeds isConstant and isConstantKey (marks on the returned tree), parts gives every node's text, count
     bounds the loop and decides the THIS case.
  T2 absent: rootName is read by the decision, IR.name and isConstant; node is assigned on both branches, moved by the loop and
     returned; propNode reaches getprop; i is advanced by its for header; no literal-initialised local; each if has two
     different effects.
  T3 absent: both root kinds of the decision and both node kinds of the constant marks (root name, property) are treated; the
     gold's text names no set of which a member is left out.
  T4 absent: the javadoc names the qualified name, its root and its properties, '@return a NAME or GETPROP node' (both built)
     and the caller precondition 'at least one'; nothing it names is unmet. Nothing needed rewriting.
 Variant gold (javadoc, signature, root NAME with its isConstant mark, the loop over the further parts, return):
  T1 absent: convention is read by isConstant and isConstantKey, whose marks are on the returned nodes; parts gives the text of
     every node; count is the loop bound; each changes the result. No argument check.
  T2 absent: rootName is read by IR.name and isConstant; node is reassigned in the loop and returned; propNode reaches getprop;
     i is advanced by the for header; no literal-initialised local, flag, counter or best-so-far; both ifs set a mark on a
     returned node (live decisions).
  T3 absent: the constant mark is applied to the root (isConstant) and to every property (isConstantKey), both members of the
     root/property pair; no case, branch or check on a root kind remains (no member handled); no closed set or named class is
     handled in part.
  T4 absent: 'the qualified name made of the given parts', 'the first part being the root', 'each following part the name of a
     property' and '@return a NAME or GETPROP node' are general descriptions that the body's lines address (IR.name, IR.string
     under IR.getprop); 'at least one' is a caller precondition; no inline comment; identifiers (rootName, propNode) name
     nothing the body does not do."""

NU = "src/com/google/javascript/jscomp/NodeUtil.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"
JTR = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
JDI = "src/com/google/javascript/rhino/JSDocInfo.java"
CO = "src/com/google/javascript/jscomp/CompilerOptions.java"
ST = "src/com/google/javascript/jscomp/SymbolTable.java"

PARTS_DOC = '''/**
 * Creates a node representing the qualified name made of the first
 * {@code count} parts.
 *
 * @param convention the coding convention in use
 * @param parts the parts of the qualified name, in order
 * @param count the number of parts to use, at least one
 * @return a NAME or GETPROP node
 */'''

GOLD_TEXT = '''/**
 * Creates a node representing the qualified name made of the given parts,
 * the first part being the root of the name and each following part the
 * name of a property.
 *
 * @param convention the coding convention in use
 * @param parts the parts of the qualified name, in order
 * @param count the number of parts to use, at least one
 * @return a NAME or GETPROP node
 */
public static Node qualifiedNameFrom(CodingConvention convention,
    String[] parts, int count) {
  String rootName = parts[0];
  Node node;
  if (count > 1 && "this".equals(rootName)) {
    node = IR.thisNode();
  } else {
    node = IR.name(rootName);
    if (convention.isConstant(rootName)) {
      node.putBooleanProp(Node.IS_CONSTANT_NAME, true);
    }
  }
  for (int i = 1; i < count; i++) {
    Node propNode = IR.string(parts[i]);
    if (convention.isConstantKey(parts[i])) {
      propNode.putBooleanProp(Node.IS_CONSTANT_NAME, true);
    }
    node = IR.getprop(node, propNode);
  }
  return node;
}'''

HOP1 = '''/**
 * Creates a node representing a qualified name.
 *
 * @param convention the coding convention in use
 * @param name a qualified name (e.g. "foo" or "foo.bar.baz")
 * @return a NAME or GETPROP node
 */
public static Node qualifiedNameTree(CodingConvention convention,
    String name) {
  return JSTypeRegistry.createDottedName(convention, name.split("\\\\.", -1));
}'''

HOP2 = '''/**
 * Creates a node representing the qualified name made of the given parts.
 *
 * @param convention the coding convention in use
 * @param parts the dot-separated parts of the name, in order
 * @return a NAME or GETPROP node
 */
public static Node createDottedName(CodingConvention convention,
    String[] parts) {
  return JSDocInfo.Marker.dottedNameOf(convention, parts, parts.length);
}'''

HOP3 = PARTS_DOC + '''
public static Node dottedNameOf(CodingConvention convention,
    String[] parts, int count) {
  return CompilerOptions.TweakProcessing.accessPathOf(convention, parts, count);
}'''

HOP4 = PARTS_DOC + '''
public static Node accessPathOf(CodingConvention convention,
    String[] parts, int count) {
  return SymbolTable.Symbol.qualifiedNameFrom(convention, parts, count);
}'''

DESIGN = {
 "instance": "Closure-174", "project": "Closure", "bug_id": 174, "seed": 5011,
 "src_root": "src", "test_root": "test",
 "facade": {"file": NU, "class": "com.google.javascript.jscomp.NodeUtil", "method": "newQualifiedNameNode", "near_line": 2324},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/NodeUtilTest.java",
             "test_class": "com.google.javascript.jscomp.NodeUtilTest", "test_method": "testNewQualifiedNameNode2"},
 "expected_signature": "Subtree2: NAME this",
 "gold": {"method": "qualifiedNameFrom", "text": GOLD_TEXT,
          "fault": {"old": "      Node node;\n"
                           "      if (count > 1 && \"this\".equals(rootName)) {\n"
                           "        node = IR.thisNode();\n"
                           "      } else {\n"
                           "        node = IR.name(rootName);\n"
                           "        if (convention.isConstant(rootName)) {\n"
                           "          node.putBooleanProp(Node.IS_CONSTANT_NAME, true);\n"
                           "        }\n"
                           "      }\n",
                    "new": "      Node node = IR.name(rootName);\n"
                           "      if (convention.isConstant(rootName)) {\n"
                           "        node.putBooleanProp(Node.IS_CONSTANT_NAME, true);\n"
                           "      }\n"}},
 "chain": {
   "facade_body": "return Compiler.CodeBuilder.qualifiedNameTree(convention, name);",
   "lie": "The name is scanned from its last dot back to its first, and the node built for each prefix of the name is kept "
          "in a cache, so that a prefix shared with a name created earlier is reused instead of being created again.",
   "hops": [
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "qualifiedNameTree",
      "imports": ["com.google.javascript.rhino.jstype.JSTypeRegistry"], "text": HOP1},
     {"file": JTR, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "createDottedName",
      "imports": ["com.google.javascript.jscomp.CodingConvention", "com.google.javascript.rhino.JSDocInfo"], "text": HOP2},
     {"file": JDI, "class": "com.google.javascript.rhino.JSDocInfo$Marker", "method": "dottedNameOf",
      "imports": ["com.google.javascript.jscomp.CodingConvention", "com.google.javascript.jscomp.CompilerOptions"], "text": HOP3},
     {"file": CO, "class": "com.google.javascript.jscomp.CompilerOptions$TweakProcessing", "method": "accessPathOf",
      "imports": [], "text": HOP4},
     {"file": ST, "class": "com.google.javascript.jscomp.SymbolTable$Symbol", "method": "qualifiedNameFrom",
      "imports": ["com.google.javascript.rhino.IR"], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.rhino.Node::getQualifiedName",
              "com.google.javascript.rhino.Node::isQualifiedName",
              "com.google.javascript.rhino.Node::isUnscopedQualifiedName",
              "com.google.javascript.jscomp.NodeUtil::getRootOfQualifiedName"],
 "ownership_reason": "Only the gold builds the root of the name together with its properties; hop 1 splits the name, hop 2 "
                     "counts the parts and hops 3-4 pass them along, and each gets back one finished tree. No part string "
                     "makes the gold produce a THIS root, and replacing the root of a finished tree takes a search for the "
                     "root and a replaceChild, which is more than a one-line change. The convention is pinned outside the "
                     "gold: Node.getQualifiedName returns \"this\" for a THIS root (the inverse of the facade) and "
                     "NodeTest.testQualifiedName expects GETPROP(THIS, b) to read \"this.b\"; Node.isQualifiedName names "
                     "this.a as a qualified name (case THIS; NodeTest.testIsQualifiedName) while "
                     "Node.isUnscopedQualifiedName excludes this.a (NAME roots only); NodeUtil.getRootOfQualifiedName, beside "
                     "the facade, requires the root to be a NAME or a THIS node. The parser never produces a NAME node named "
                     "\"this\", so GETPROP(NAME this, prop) is not the node of the qualified name this.prop.",
 "ownership_tests": ["com.google.javascript.rhino.NodeTest::testQualifiedName",
                     "com.google.javascript.rhino.NodeTest::testIsQualifiedName",
                     "com.google.javascript.jscomp.NodeUtilTest::testNewQualifiedNameNode1"],
 "compensating": {
   "chain": [
     {"file": CMP, "old": "return JSTypeRegistry.createDottedName(convention, name.split(\"\\\\.\", -1));",
      "new": "return \"this\".equals(name) ? IR.thisNode() : JSTypeRegistry.createDottedName(convention, name.split(\"\\\\.\", -1));",
      "why": "hop 1 returns a THIS node for the bare name this"},
     {"file": JTR, "old": "return JSDocInfo.Marker.dottedNameOf(convention, parts, parts.length);",
      "new": "return \"this\".equals(parts[0]) ? JSDocInfo.Marker.dottedNameOf(convention, java.util.Arrays.copyOfRange(parts, 1, parts.length), parts.length - 1) : JSDocInfo.Marker.dottedNameOf(convention, parts, parts.length);",
      "why": "hop 2 drops a leading this part"},
     {"file": CO, "old": "return SymbolTable.Symbol.qualifiedNameFrom(convention, parts, count);",
      "new": "return count == 1 && \"this\".equals(parts[0]) ? IR.thisNode() : SymbolTable.Symbol.qualifiedNameFrom(convention, parts, count);",
      "why": "hop 4 returns a THIS node for a one-part name this"},
   ],
 },
 "host_notes": "Hosts for seed 5011 (mr_lib preview, target com/google/javascript/jscomp/NodeUtil.java, n=11), draw order "
               "parsing.JsDocInfoParser, rhino.jstype.JSTypeRegistry, rhino.JSDocInfo, regex.RegExpTree, jsonml.Reader, "
               "rhino.Node, Compiler, CompilerOptions, DefaultPassConfig, SymbolTable, TypeCheck. Hop i goes into drawn host i; "
               "an unusable drawn host is replaced by the next drawn host after the first five whose anchor at the recipe's "
               "own seed for that hop (5011+100+i-1) is usable. Closure uses 2-space indentation, so the anchor picker lands "
               "on members of NESTED classes or, with too few candidates, appends the hop at the end of the outer class. "
               "Hop 1: JsDocInfoParser unusable (anchor in private static class ExtractionInfo, invisible outside "
               "JsDocInfoParser); next drawn host rhino.Node unusable at seed 5111 (anchor in private static class "
               "ObjectPropListItem); took Compiler (anchor in public static class Compiler.CodeBuilder). Hop 2: JSTypeRegistry "
               "as drawn (appended at the end of the public class). Hop 3: JSDocInfo as drawn (anchor in public static final "
               "class JSDocInfo.Marker). Hop 4: RegExpTree unusable (anchor in the package-private class BackReference of "
               "the regex package, invisible from rhino where hop 3 lives); took CompilerOptions (anchor in public static "
               "enum CompilerOptions.TweakProcessing; a static method in an enum compiles). Hop 5 (gold): jsonml.Reader "
               "unusable (anchor in the private inner class ErrorReporter); next drawn host DefaultPassConfig unusable at "
               "seed 5115 (anchor in the non-static inner class GlobalTypeResolver, where a static method does not "
               "compile); took SymbolTable (anchor in public static final class SymbolTable.Symbol). Nested-class hops "
               "carry binary names (Outer$Nested). The recipe indents inserted text by 4 spaces and the facade body by 8, "
               "which matches nested members but is off by 2 for the facade and the appended JSTypeRegistry hop in this "
               "2-space codebase (cosmetic, recipe-wide for Closure).",
}
