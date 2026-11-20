"""Main run Jsoup-43__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Jsoup-43; the real bug modified org.jsoup.nodes.Element, the target class). No static pair (pool v2: no_tested_static), so addendum
section 2 has nothing to refer to.

Facade: Element.dataNodes() (allowed instance target of BATCH8_PREREGISTRATION.md row 266; facade_planned_by null, so no facade
reuse). The other two allowed targets were not used: Element.children (planned by Jsoup-22__i) is called by the sibling, index and
nth-child code of Element, Node and Evaluator, so any change to its result fails dozens of tests (no single trigger); and
Element.textNodes is reached by three tests (ElementTest testGetTextNodes and testManipulateTextNodes, TextNodeTest
testWithSupplementaryCharacter) that read the same child lists, so a change to its result fails at least two of them.
Original computation of the facade: a filter on the element's child node list (the field childNodes, declared in Node) that keeps
the DataNode children in document order and returns them as an unmodifiable list (empty when there are none).

facade_variant: V1 (state as parameters). The method reads one field and writes none: the facade passes the value of the
package-private field childNodes (List<Node>; Element is in the field's package and inherits it, so no visibility change) to hop 1
and returns hop 1's result. The chain needs no method of the receiver (V2 not needed), calls no private method of Element (no V4)
and handles only public types (Node, DataNode; no V3/V5). No signature, modifier, override or throws change; no new type; no
reflection; no test edit.
state_passed: the field childNodes (List<Node>) to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-43-probe2/w of the fixture,
the first statement of dataNodes was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t org.jsoup.nodes.ElementTest::testGetDataNodes`: fails with java.lang.IllegalStateException: PROBE-REACHED at
Element.dataNodes(Element.java:229) from ElementTest.java:594. Full suite (`defects4j test`) with the probe: exactly 1 failing test,
ElementTest::testGetDataNodes, with PROBE-REACHED; dataNodes has no production caller and no other test reaches it.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of batch8_tasks.json, in that order, nothing substituted):
  hop 1 helper.HttpConnection       912 lines  childDataNodes   pass-through
  hop 2 select.Evaluator            706 lines  dataChildren     placement: wraps the result as an unmodifiable list (the
                                                                original's Collections.unmodifiableList); the seeded anchor
                                                                lies inside the public static nested class
                                                                Evaluator.IsOnlyChild, so the hop is a member of that class
  hop 3 nodes.Node                  687 lines  dataChildNodes   pass-through
  hop 4 safety.Whitelist            635 lines  dataNodeList     pass-through
  hop 5 nodes.Document              565 lines  dataNodesOf      GOLD: the per-node core, i.e. the scan over the child nodes,
                                                                the decision that a node is a data node, and the copying of
                                                                the data nodes into the result
Host newline counts 912, 706, 687, 635, 565; the smallest host is Document (565 lines), which is also the gold host.

Gold algorithm (correct): one forward scan over the child nodes by index. Data nodes are copied in runs: whenever a node that is
not a data node is reached, the nodes from the start of the current run up to it (all data nodes) are copied into the result and
the next run starts after it; after the scan, the nodes from the start of the last run to the end of the list are copied. The
correct configuration returns, for every element, the same nodes in the same order as the original, as an unmodifiable list (an
empty list when no child is a data node).

Fault (one-line omission of a boundary step in the gold): the copy of the last run after the scan (`for (Node node :
childNodes.subList(from, childNodes.size())) dataNodes.add((DataNode) node);`, one statement) is dropped, so data nodes that are
not followed by a non-data node are not returned. Trigger: the EXISTING test ElementTest::testGetDataNodes. The script element's
only child is a data node, so script.dataNodes() is empty: java.lang.AssertionError: expected:<1> but was:<0> at
ElementTest.java:595. It is the only test that newly fails: dataNodes has no production caller, no other test calls it (probe
above), and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the data nodes of a list of child nodes, in document order) and is silent on the
end-of-list step; a data node that is the last child is still a data node, and the contract is violated on the trigger input. The
convention is pinned outside the gold: Element.textNodes (the sibling filter on the same childNodes list; keeps every TextNode
child, the last one included), Element.data (appends the data of every DataNode child, wherever it sits) and
Document.normaliseTextNodes (an instanceof filter over every child node); passing tests ElementTest::testGetTextNodes (p.textNodes()
of <p>One <span>Two</span> Three <br> Four</p> returns 3 nodes, the third being the last child " Four") and
HtmlParserTest::handlesDataOnlyTags (the data of <style>font-family: bold</style>, whose only child is a data node, is
"font-family: bold"); the facade's own javadoc ("effectively a filter on childNodes() to get Data nodes") is kept unchanged.

Single owner: only the gold looks at the kind of a node and copies nodes into the result; hop 2 only wraps the list, and hops 1, 3
and 4 pass the child node list along unchanged. No one-line change above the gold recovers the data nodes the gold leaves out
while keeping its result (a filter over a List<Node> is a loop; Java 5 source level, no streams). Declared alternatives (G9): hop 4
hands the gold a copy of the child node list; hop 3 answers an empty child list itself; hop 2 copies the gold's result before
wrapping it. Each leaves the trigger failing.
Recorded bypasses (edits that replace or feed the gold differently, not repairs of the chain):
 B-0 the facade's original body (or a hop that filters the child nodes itself with its own instanceof loop, before or instead of
     the gold) re-implements the whole computation.
 B-1 a hop that hands the gold the child node list with an extra node appended that is not a data node and not a child of the
     element (for example via an anonymous ArrayList subclass with an instance initialiser) makes the gold copy the last run; it
     passes a node that is not a child node, against the @param of the hops and of the gold (the child nodes of an element).

Lie: the facade's javadoc claims the child node list is scanned from its last node back to its first and the collected list is
turned around before it is returned; the chain scans forward once and never turns anything around. It names neither the node kind
test, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: childNodes sizes the result list, bounds the scan, is indexed by the test and is the source of every copied node.
  T2 absent: dataNodes is created, added to by both copies and returned; from is read by both subList calls and reassigned in
     the loop; i is the loop cursor; node is read by the add; no literal-initialised local that is never reassigned (from = 0 is
     reassigned in the loop); the one decision copies or skips (different effects).
  T3 absent: one node kind is tested (DataNode); the node kinds form no set named in the gold's text, and the gold selects
     exactly one kind; the runs are copied both inside the scan and at its end, so no member of any pair or range is left out.
  T4 absent: "the data nodes of a list of child nodes" is met by the instanceof test and the copies; "in document order" by the
     forward scan; the @param/@return clauses name no rule, limit or value class beyond that.
 Variant gold (javadoc, signature, `new ArrayList<DataNode>(childNodes.size())`, `int from = 0`, a forward index loop whose
 only decision `if (!(childNodes.get(i) instanceof DataNode))` copies `childNodes.subList(from, i)` into the result and sets
 `from = i + 1`, return of the list):
  T1 absent: childNodes sizes the list, bounds the loop, is indexed by the type test and supplies every copied node.
  T2 absent: dataNodes is added to in the loop and returned; from is assigned in the loop (from = i + 1) and read by the subList
     call that feeds the add (not frozen: the loop assigns it); i is the loop cursor and advances; node is read by the add; the
     only decision copies a sublist and moves from, or does nothing (different effects); no dead branch, case or ternary.
  T3 absent: one node kind is tested (DataNode) in an unnamed set of node kinds; no enum, type code or named format; subList(from,
     i) uses both ends of its range; there are no parallel cases, pair halves or named class in the gold's text that is handled
     in part.
  T4 absent: "Gets the data nodes of a list of child nodes, in document order" is a general description that the type test and
     the copy address, and "in document order" is met
     by the forward scan; "@param childNodes the child nodes of an element, in document order" is a caller precondition;
     "@return the data nodes, in document order" names no limit or value class the List<DataNode> result visibly breaks; no
     inline comment; the identifiers dataNodes, from, i, node and childNodes name what they hold."""

EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"
WL = "src/main/java/org/jsoup/safety/Whitelist.java"
DC = "src/main/java/org/jsoup/nodes/Document.java"

GOLD_TEXT = '''/**
 * Gets the data nodes of a list of child nodes, in document order.
 *
 * @param childNodes the child nodes of an element, in document order
 * @return the data nodes, in document order
 */
public static List<DataNode> dataNodesOf(List<Node> childNodes) {
    List<DataNode> dataNodes = new ArrayList<DataNode>(childNodes.size());
    int from = 0;
    for (int i = 0; i < childNodes.size(); i++) {
        if (!(childNodes.get(i) instanceof DataNode)) {
            for (Node node : childNodes.subList(from, i))
                dataNodes.add((DataNode) node);
            from = i + 1;
        }
    }
    for (Node node : childNodes.subList(from, childNodes.size()))
        dataNodes.add((DataNode) node);
    return dataNodes;
}'''

HOP1 = '''/**
 * Gets the data nodes of a list of child nodes.
 * @param childNodes the child nodes of an element, in document order
 * @return the data nodes, in document order, as an unmodifiable list
 */
public static List<DataNode> childDataNodes(List<Node> childNodes) {
    return Evaluator.IsOnlyChild.dataChildren(childNodes);
}'''

HOP2 = '''/**
 * Gets the data nodes of a list of child nodes, as an unmodifiable list.
 *
 * @param childNodes the child nodes of an element, in document order
 * @return an unmodifiable list of the data nodes, in document order
 */
public static List<DataNode> dataChildren(List<Node> childNodes) {
    return Collections.unmodifiableList(Node.dataChildNodes(childNodes));
}'''

HOP3 = '''/**
 * Get the data nodes of a list of child nodes.
 * @param childNodes the child nodes of an element, in document order
 * @return the data nodes, in document order
 */
public static List<DataNode> dataChildNodes(List<Node> childNodes) {
    return Whitelist.dataNodeList(childNodes);
}'''

HOP4 = '''/**
 Gets the data nodes of a list of child nodes.
 @param childNodes the child nodes of an element, in document order
 @return the data nodes, in document order
 */
public static List<DataNode> dataNodeList(List<Node> childNodes) {
    return Document.dataNodesOf(childNodes);
}'''

DESIGN = {
 "instance": "Jsoup-43", "project": "Jsoup", "bug_id": 43, "seed": 7492,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": EL, "class": "org.jsoup.nodes.Element", "method": "dataNodes", "near_line": 228},
 "facade_variant": "V1",
 "state_passed": "the field childNodes (List<Node>, declared in Node, read inside Element) to hop 1; no write-back",
 "reachability_probe": "trigger test and full suite with PROBE-REACHED as the first statement of dataNodes: ElementTest::"
                       "testGetDataNodes fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "Element.dataNodes(Element.java:229) from ElementTest.java:594; the full suite with the probe has exactly "
                       "this 1 failing test",
 "host_mode": "largest5",
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/ElementTest.java",
             "test_class": "org.jsoup.nodes.ElementTest", "test_method": "testGetDataNodes"},
 "expected_signature": "expected:<1> but was:<0>",
 "gold": {"method": "dataNodesOf", "text": GOLD_TEXT,
          "fault": {"old": "        for (Node node : childNodes.subList(from, childNodes.size()))\n"
                           "            dataNodes.add((DataNode) node);\n"
                           "        return dataNodes;\n",
                    "new": "        return dataNodes;\n"}},
 "chain": {
   "facade_body": "return org.jsoup.helper.HttpConnection.childDataNodes(childNodes);",
   "lie": "The child node list is scanned from its last node back to its first, and the collected list is turned around "
          "before it is returned.",
   "hops": [
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "childDataNodes",
      "imports": ["org.jsoup.nodes.DataNode", "org.jsoup.nodes.Node", "org.jsoup.select.Evaluator"], "text": HOP1},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsOnlyChild", "method": "dataChildren",
      "imports": ["org.jsoup.nodes.DataNode", "java.util.Collections"], "text": HOP2},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "dataChildNodes",
      "imports": ["org.jsoup.safety.Whitelist"], "text": HOP3},
     {"file": WL, "class": "org.jsoup.safety.Whitelist", "method": "dataNodeList",
      "imports": ["org.jsoup.nodes.DataNode", "org.jsoup.nodes.Document", "org.jsoup.nodes.Node", "java.util.List"], "text": HOP4},
     {"file": DC, "class": "org.jsoup.nodes.Document", "method": "dataNodesOf", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Element::textNodes",
              "org.jsoup.nodes.Element::data",
              "org.jsoup.nodes.Document::normaliseTextNodes"],
 "ownership_reason": "Only the gold looks at the kind of a child node and copies the data nodes into the result; hop 2 only "
                     "wraps the list it gets back as an unmodifiable list, and hops 1, 3 and 4 pass the child node list along "
                     "unchanged. The gold's javadoc promises the data nodes of a list of child nodes, in document order; a data "
                     "node that is the last child (the script's only child) is a data node, yet the gold copies only the data "
                     "nodes that are followed by a node that is not a data node. No one-line change above the gold recovers the "
                     "left-out data nodes while keeping the gold's result (that is a filtering loop, i.e. the gold's own "
                     "computation). The convention is pinned outside the gold: Element.textNodes keeps every TextNode child of "
                     "the same childNodes list, the last one included; Element.data appends the data of every DataNode child "
                     "(recursing into elements); Document.normaliseTextNodes filters every child node with an instanceof test; "
                     "ElementTest testGetTextNodes (the third of p's text nodes is its last child ' Four') and HtmlParserTest "
                     "handlesDataOnlyTags (a style whose only child is a data node has that node's data) pass; the facade's own "
                     "javadoc calls dataNodes 'effectively a filter on childNodes() to get Data nodes'.",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::testGetTextNodes",
                     "org.jsoup.parser.HtmlParserTest::handlesDataOnlyTags"],
 "compensating": {
   "chain": [
     {"file": WL, "old": "return Document.dataNodesOf(childNodes);",
      "new": "return Document.dataNodesOf(new java.util.ArrayList<Node>(childNodes));",
      "why": "hop 4 hands the gold a copy of the child node list"},
     {"file": ND, "old": "return Whitelist.dataNodeList(childNodes);",
      "new": "return childNodes.isEmpty() ? Collections.<DataNode>emptyList() : Whitelist.dataNodeList(childNodes);",
      "why": "hop 3 answers an empty child node list itself"},
     {"file": EV, "old": "return Collections.unmodifiableList(Node.dataChildNodes(childNodes));",
      "new": "return Collections.unmodifiableList(new java.util.ArrayList<DataNode>(Node.dataChildNodes(childNodes)));",
      "why": "hop 2 copies the result before wrapping it"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch8_tasks.json), in that order, "
               "none substituted (all five are public top-level classes in which a static method compiles; Evaluator and Node "
               "are abstract, which does not affect a static method): helper.HttpConnection (hop 1, 912 lines), "
               "select.Evaluator (hop 2, 706), nodes.Node (hop 3, 687), safety.Whitelist (hop 4, 635), nodes.Document (hop 5, "
               "gold, 565; the smallest host). Anchors from stageB_lib.pick_insertion_anchor with seed 7492 + 100 + i (as "
               "mr3_spec.py inserts them): hop 1 after `header(String, String)` (line idx 172, seed 7592), hop 2 after "
               "`toString` (570, 7593), hop 3 after `toString` (578, 7594), hop 4 after `removeTags` (234, 7595), hop 5 after "
               "`charset(Charset)` (241, 7596). The hop-2 anchor is the toString of the public static nested class "
               "Evaluator.IsOnlyChild (the file's mixed tab/space indentation makes it look 4-space indented), so hop 2 is a "
               "public static method of Evaluator.IsOnlyChild and hop 1 calls it as Evaluator.IsOnlyChild.dataChildren; the "
               "anchor was not changed. The other anchors are in the outer classes. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports what it names. The facade's class Element is not a host.",
}
