"""Main run Jsoup-32__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade on a bug that has no static facade; fixed
checkout of Defects4J Jsoup-32, whose real bug modified org.jsoup.nodes.Element, the facade's class). No static pair (B8 note section 1).

Facade: Element.dataNodes() (instance method; allowed targets Element.children / Element.textNodes / Element.dataNodes,
BATCH8_PREREGISTRATION.md row 262). dataNodes has facade_planned_by = null, so the facade is distinct (the task's facade_reuse_of names
Jsoup-22__i only for children()). textNodes was not used: its only callers are ElementTest::testGetTextNodes and
ElementTest::testManipulateTextNodes, which read the same first list of the same paragraph, so any omission that changes that list fails
both; only a rule that matters for adjacent text nodes (the split in testManipulateTextNodes) could fail one alone, and no quiet one-line
omission of the per-node decision has that effect. children() was not used: it is planned by Jsoup-22__i and it is read in production by
child(int), siblingElements, nextElementSibling, previousElementSibling, firstElementSibling, elementSiblingIndex, lastElementSibling and
Node.wrap (through getDeepChild), so an omission there fails many tests.
Original computation: the child nodes (the package-private field Node.childNodes) are filtered to the DataNode instances, in document
order, and returned as an unmodifiable list (an empty list if there are none).

facade_variant: V1 (state as parameters). state_passed: the field childNodes (List<Node>, read inside the class) is handed to hop 1; no
field is written, no write-back. The original has no guard; the facade body is one call to hop 1. No visibility is widened, no type is
added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The computation calls no private method of
Element (V4 does not apply) and the chain needs only the public types Node and DataNode (V3/V5 do not apply).

Redistribution of the computation: hop 1 makes the result unmodifiable; hop 2 creates the result list; hop 3 is the fold that appends the
data nodes block by block; hop 4 passes the node list to the gold; the gold holds the per-node core: one pass over the nodes that keeps
each data node and groups the data nodes that follow one another into blocks, the nodes of other kinds being left out.
The correct configuration returns exactly the original list for every child list (the blocks partition the data nodes in document order,
and hop 3 concatenates them in order).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-32-probe of the fixture, the first statement of
textNodes() and of dataNodes() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.jsoup.nodes.ElementTest::testGetDataNodes`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
org.jsoup.nodes.Element.dataNodes(Element.java:230), called from ElementTest.java:548 (testGetTextNodes and testManipulateTextNodes
likewise reach textNodes). Full suite with the probe: exactly 3 failing tests (testGetTextNodes, testManipulateTextNodes,
testGetDataNodes), all with PROBE-REACHED, so testGetDataNodes is the only test that reaches dataNodes(). The facade is reached directly
by the trigger.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 helper.HttpConnection  687 lines  childDataNodes   plumbing: the result list made unmodifiable
  hop 2 nodes.Node             636 lines  dataNodesIn      plumbing: creates the result list
  hop 3 select.Elements        540 lines  appendDataNodes  aggregation: appends the data nodes block by block
  hop 4 safety.Whitelist       463 lines  dataBlocks       pass-through
  hop 5 select.Evaluator       454 lines  dataNodeBlocks   GOLD: one pass over the nodes, keeping each data node, grouped in blocks
Host newline counts 687, 636, 540, 463, 454; the smallest host (and the gold host) has 454 lines (C10F addendum section 1: hosts under
1500 lines are expected in this regime).

Fault (one-line omission of a boundary step in the gold): the final block is not added after the loop (the line
`if (!block.isEmpty()) blocks.add(block);` is dropped), so the data nodes that end the list are left out. The gold then reads as the
ordinary routine "a data node joins the current block; a node of any other kind closes it". Trigger: the EXISTING test
ElementTest::testGetDataNodes; its first assertion, assertEquals(1, scriptData.size()) for <script>One Two</script>, fails with
expected:<1> but was:<0> (the script element's only child, a data node, ends the list). It is the only test that reaches dataNodes() (the
probe's full-suite run), and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it splits the list into the blocks of data nodes that follow one another, in document
order, the nodes of other kinds being left out) and is silent on the end of the list; on the trigger input the list holds one data node,
which forms a block, and the variant returns no block, so the contract is violated. The convention (every data-node child counts, the last
one included) is pinned outside the gold: Element.data() appends the data of every DataNode child, the final one included
(HtmlParserTest::handlesDataOnlyTags and ::handlesUnclosedScriptAtEof pass: a script or style whose only child is a data node gives its
data); the intact sibling filter Element.textNodes() keeps the text node that ends the child list (ElementTest::testGetTextNodes passes:
" Four" is the third entry).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: nodes is the loop's source and supplies every data node; no other parameter.
  T2 absent: blocks is returned; block receives each data node and is added to blocks (in the loop and after it); node is read by both
     decisions; the two branches have different effects; nothing is frozen (block is reassigned in the loop).
  T3 absent: data nodes and the nodes of all other kinds are both handled (kept / closing the block); no class named in the text is
     handled in part.
  T4 absent: 'blocks of data nodes that follow one another', 'in document order', 'the nodes of other kinds are left out' and 'each
     block holds at least one data node' are met by lines of the body.
 Variant gold (javadoc, signature, the loop with `if (node instanceof DataNode)` / `else if (!block.isEmpty())`, `return blocks;`):
  T1 absent: nodes drives the loop and supplies every kept node; it is not only argument-checked.
  T2 absent: blocks is returned; block is read by blocks.add(block) and by block.isEmpty() inside the loop and is reassigned there; node
     reaches both decisions; the if/else-if have different effects (add to the block / close the block); no local is dead or frozen.
  T3 absent: the gold's text names two kinds, data nodes and the nodes of other kinds, and treats both; it names no end-of-list rule and
     no range; no pair half or range end is handled on one side only.
  T4 absent: 'splits a list of nodes into blocks of data nodes that follow one another, in document order' is a general description
     that the loop addresses; 'the nodes of other kinds are left out' is met; '@return ... each block holds at least one data node' is met
     (a block is added only when it is not empty); no inline comment; identifiers (blocks, block, node, nodes) name nothing the body
     does not meet.

Single owner: only the gold decides which data nodes are kept and in which block; hops 1, 2 and 4 pass the list along, and hop 3 only
concatenates the blocks the gold returns, in order. Once the gold has left out the data nodes that end the list, they can reappear only if
a caller re-reads the node list itself or replaces the gold. Declared alternatives (G9): hop 1 returns the list as it is (not
unmodifiable); hop 2 hands hop 3 a copy of the node list; hop 3 inserts each block at the front of the result. None makes the trigger pass.
Recorded bypasses (not one-line edits consistent with the hops' documentation):
 B-0 the facade's original body, or hop 3 filtering the node list itself (`for (Node node : nodes) if (node instanceof DataNode)
     into.add((DataNode) node);` in place of the block loop), discards the gold's output.
 B-1 hop 4 or hop 3 appends a node of another kind (e.g. a new Comment) to a copy of the node list before calling the gold, forcing the
     last block to close; two statements, and it changes the input that hop 4 documents passing on unchanged.

Lie: the facade's javadoc claims the child nodes are scanned from the last to the first, each data node found being inserted at the head
of the list; no step of the chain scans backwards or inserts at the head (the gold walks the nodes forwards and hop 3 appends). It names
neither the end of the list nor blocks nor any hop."""

ELEMENT = "src/main/java/org/jsoup/nodes/Element.java"
HTTP = "src/main/java/org/jsoup/helper/HttpConnection.java"
NODE = "src/main/java/org/jsoup/nodes/Node.java"
ELEMENTS = "src/main/java/org/jsoup/select/Elements.java"
WHITELIST = "src/main/java/org/jsoup/safety/Whitelist.java"
EVALUATOR = "src/main/java/org/jsoup/select/Evaluator.java"

GOLD_TEXT = '''/**
 * Splits a list of nodes into blocks of data nodes that follow one another in the list, in document order. The
 * nodes of other kinds are left out.
 *
 * @param nodes the nodes to split
 * @return the blocks of data nodes, in document order; each block holds at least one data node
 */
public static List<List<DataNode>> dataNodeBlocks(List<Node> nodes) {
    List<List<DataNode>> blocks = new ArrayList<List<DataNode>>();
    List<DataNode> block = new ArrayList<DataNode>();
    for (Node node : nodes) {
        if (node instanceof DataNode) {
            block.add((DataNode) node);
        } else if (!block.isEmpty()) {
            blocks.add(block);
            block = new ArrayList<DataNode>();
        }
    }
    if (!block.isEmpty()) blocks.add(block);
    return blocks;
}'''

HOP1 = '''/**
 * Get the data nodes among a node's child nodes. The list is unmodifiable but the data nodes may be manipulated.
 *
 * @param childNodes the child nodes, in document order
 * @return the data nodes among the child nodes, in document order; an empty list if there are none
 */
public static List<DataNode> childDataNodes(List<Node> childNodes) {
    return Collections.unmodifiableList(Node.dataNodesIn(childNodes));
}'''

HOP2 = '''/**
 Get the data nodes among a list of nodes, in a new list.
 @param nodes the nodes to read
 @return a new list of the data nodes, in document order
 */
public static List<DataNode> dataNodesIn(List<Node> nodes) {
    List<DataNode> dataNodes = new ArrayList<DataNode>(nodes.size());
    Elements.appendDataNodes(nodes, dataNodes);
    return dataNodes;
}'''

HOP3 = '''/**
 * Append the data nodes of a list of nodes to another list, block by block, in document order.
 *
 * @param nodes the nodes to read
 * @param into the list to append the data nodes to
 */
public static void appendDataNodes(List<Node> nodes, List<DataNode> into) {
    for (List<DataNode> block : Whitelist.dataBlocks(nodes)) {
        into.addAll(block);
    }
}'''

HOP4 = '''/**
 Split a list of nodes into blocks of adjacent data nodes.

 @param nodes the nodes to split
 @return the blocks of data nodes, in document order
 */
public static List<List<DataNode>> dataBlocks(List<Node> nodes) {
    return Evaluator.dataNodeBlocks(nodes);
}'''

DESIGN = {
 "instance": "Jsoup-32", "project": "Jsoup", "bug_id": 32, "seed": 3306,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the field childNodes (Node.childNodes, List<Node>) passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [687, 636, 540, 463, 454],
 "reachability_probe": "dataNodes() (and textNodes()) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-32-probe: ElementTest::testGetDataNodes fails with PROBE-REACHED at "
                       "Element.dataNodes(Element.java:230) from ElementTest.java:548; full suite: only testGetTextNodes, "
                       "testManipulateTextNodes and testGetDataNodes fail, all PROBE-REACHED",
 "facade": {"file": ELEMENT, "class": "org.jsoup.nodes.Element", "method": "dataNodes", "near_line": 228},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/ElementTest.java",
             "test_class": "org.jsoup.nodes.ElementTest", "test_method": "testGetDataNodes"},
 "expected_signature": "expected:<1> but was:<0>",
 "gold": {"method": "dataNodeBlocks", "text": GOLD_TEXT,
          "fault": {"old": "        }\n        if (!block.isEmpty()) blocks.add(block);\n        return blocks;",
                    "new": "        }\n        return blocks;"}},
 "chain": {
   "facade_body": "return org.jsoup.helper.HttpConnection.childDataNodes(childNodes);",
   "lie": "The child nodes are scanned from the last to the first, and each data node found is inserted at the head of the list.",
   "hops": [
     {"file": HTTP, "class": "org.jsoup.helper.HttpConnection", "method": "childDataNodes",
      "imports": ["org.jsoup.nodes.DataNode", "org.jsoup.nodes.Node"], "text": HOP1},
     {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "dataNodesIn",
      "imports": ["org.jsoup.select.Elements"], "text": HOP2},
     {"file": ELEMENTS, "class": "org.jsoup.select.Elements", "method": "appendDataNodes",
      "imports": ["org.jsoup.nodes.DataNode", "org.jsoup.safety.Whitelist"], "text": HOP3},
     {"file": WHITELIST, "class": "org.jsoup.safety.Whitelist", "method": "dataBlocks",
      "imports": ["java.util.List", "org.jsoup.nodes.DataNode", "org.jsoup.nodes.Node", "org.jsoup.select.Evaluator"], "text": HOP4},
     {"file": EVALUATOR, "class": "org.jsoup.select.Evaluator", "method": "dataNodeBlocks",
      "imports": ["java.util.ArrayList", "org.jsoup.nodes.DataNode", "org.jsoup.nodes.Node"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Element::data", "org.jsoup.nodes.Element::textNodes"],
 "ownership_reason": "Only the gold decides which data nodes are kept and groups them into blocks: one pass over the node list that "
                     "adds each data node to the current block and closes the block at a node of another kind. Hops 1, 2 and 4 pass "
                     "the list along (making it unmodifiable, creating the result list), and hop 3 only concatenates the blocks the "
                     "gold returns, in order. Once the gold leaves out the data nodes that end the list, they can reappear only if a "
                     "caller re-reads the node list itself or replaces the gold. The gold's javadoc promises the blocks of the data "
                     "nodes that follow one another, in document order, with only the nodes of other kinds left out; on the trigger "
                     "input (a script element whose only child is a data node) the variant returns no block. The convention that every "
                     "data-node child counts, the final one included, is pinned outside the gold: Element.data() appends the data of "
                     "every DataNode child (HtmlParserTest handlesDataOnlyTags and handlesUnclosedScriptAtEof pass: a script or style "
                     "whose only child is a data node gives its data), and the intact sibling filter Element.textNodes() keeps the "
                     "text node that ends the child list (ElementTest testGetTextNodes passes with ' Four' as the third entry).",
 "ownership_tests": ["org.jsoup.parser.HtmlParserTest::handlesDataOnlyTags",
                     "org.jsoup.parser.HtmlParserTest::handlesUnclosedScriptAtEof",
                     "org.jsoup.nodes.ElementTest::testGetTextNodes"],
 "compensating": {
   "chain": [
     {"file": HTTP, "old": "return Collections.unmodifiableList(Node.dataNodesIn(childNodes));",
      "new": "return Node.dataNodesIn(childNodes);",
      "why": "hop 1 returns the list as it is"},
     {"file": NODE, "old": "Elements.appendDataNodes(nodes, dataNodes);",
      "new": "Elements.appendDataNodes(new ArrayList<Node>(nodes), dataNodes);",
      "why": "hop 2 hands hop 3 a copy of the node list"},
     {"file": ELEMENTS, "old": "into.addAll(block);",
      "new": "into.addAll(0, block);",
      "why": "hop 3 inserts each block at the front of the result"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder): "
               "helper.HttpConnection (hop 1, 687 lines), nodes.Node (hop 2, 636), select.Elements (hop 3, 540), safety.Whitelist "
               "(hop 4, 463), select.Evaluator (hop 5, gold, 454; the smallest host). All five are public top-level classes (Node and "
               "Evaluator abstract) in which a public static method compiles; the facade's file Element.java is excluded. Anchors from "
               "stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 3306 + 100 + i, as mr3_spec.py inserts them: hop 1 "
               "after method(Method) (seed 3406), hop 2 after hasAttr (3407), hop 3 after set (3408), hop 4 after simpleText (3409), "
               "hop 5 at the end of the class (3410: the picker returns no interior anchor for Evaluator). The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host and DataNode / Node as needed (Node and DataNode share a package).",
}
