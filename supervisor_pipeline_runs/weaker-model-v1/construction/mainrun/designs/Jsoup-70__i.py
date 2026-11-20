"""Main run Jsoup-70__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade on a bug without a static facade, on the
fixed checkout of Defects4J Jsoup-70; the real bug modified org.jsoup.nodes.Element, the facade's class). No static pair (pool v2:
no_tested_static).

Facade: Element.dataNodes() (allowed instance target of BATCH8_PREREGISTRATION.md, facade_planned_by = null, so distinct; no facade
reuse). The other two allowed targets were not used:
 - Element.textNodes (facade_planned_by Jsoup-66__i) is the same one-criterion filter over childNodes as dataNodes and is reached by
   five tests in two test classes, so it offers nothing dataNodes does not, and distinctness is preferred;
 - Element.hasText is reached by ElementTest::testHasText, ElementsTest::hasText and ElementsTest::eachText, which exercise the same
   three cases (a text child, an element child with text, an empty element); the only case unique to one test (an element whose only
   child is an empty element, ElementsTest::hasText) is reached only by an omission that answers an element child without asking it
   for text while the text child keeps its blank check, a visibly incomplete treatment (checklist T3).
Original computation of the facade: a new list of the child nodes that are DataNode instances, in child order, returned as an
unmodifiable list (empty when there are none).

facade_variant: V1 (state as parameters). The method reads one field, childNodes (the element's own child list, read inside Element,
so no visibility change), and writes none; the facade passes the list to hop 1 and returns hop 1's result. The chain needs no method
of the receiver (V2 not needed), no private method of Element is called (no V4), and DataNode, Node and List are public (no V3/V5).
No signature, modifier, override or throws change; no new type; no reflection; no test edit.
state_passed: the field childNodes (List<Node>) to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-70-probe/w of the fixture the
first statement of dataNodes was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)` keeps the
rest of the body reachable for javac). `defects4j test -t org.jsoup.nodes.ElementTest::testGetDataNodes`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at org.jsoup.nodes.Element.dataNodes(Element.java:334) called from
ElementTest.testGetDataNodes(ElementTest.java:723). Full suite with the probe: 1 failing test (testGetDataNodes only; dataNodes has
no production caller). The facade is reached by an existing test directly.

Hosts (host_mode = "largest5"; exactly hosts_hop_order of batch8_tasks.json, in that order, none substituted):
  hop 1 helper.HttpConnection           1249 lines  unmodifiableDataNodes  placement: wraps the result as an unmodifiable list
  hop 2 select.Evaluator                 753 lines  dataNodesOf            pass-through (the seeded anchor lies in the public
                                                                           static nested class Evaluator.IsNthLastChild)
  hop 3 parser.HtmlTreeBuilder           734 lines  dataNodesIn            pass-through
  hop 4 nodes.Node                       725 lines  dataNodesAmong         fold: joins the runs the gold returns, in order
  hop 5 safety.Whitelist                 646 lines  dataNodeRuns           GOLD: the per-node decision (data node or not) and the
                                                                           grouping of adjacent data nodes into runs
Host newline counts 1249, 753, 734, 725, 646; the smallest host is Whitelist (646 lines), the gold host.
The correct configuration returns the original list for every element: joining the runs of adjacent data nodes in order gives every
data node of the child list in child order, and nothing else; hop 1 wraps it unmodifiable as the original did.

Fault (one-line omission of a boundary step in the gold): the step that closes the run still open when the list ends is dropped, so
the data nodes after the last node of another kind are lost. The gold then reads as the ordinary routine "collect adjacent data
nodes; a node of another kind closes the current run". Trigger: the EXISTING test ElementTest::testGetDataNodes; script.dataNodes()
(the script's only child is its DataNode, so the run is still open at the end) gives an empty list, and
assertEquals(1, scriptData.size()) fails with expected:<1> but was:<0>. It is the only test that newly fails: dataNodes has no
production caller and no other test calls it (the probe's full-suite run above), and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the runs of adjacent data nodes the list holds, in list order; nodes of other kinds
belong to no run) and is silent on the end of the list. The convention (every data node of the child list is collected, the ones at
its end included) is pinned outside the gold: Element.data() appends the data of every DataNode child in child order (HtmlParserTest
handlesDataOnlyTags and preservesSpaceInScript, where the data node is the element's last and only child, pass); Element.textNodes(),
the sibling filter on childNodes, keeps the trailing text node (ElementTest::testGetTextNodes: " Four", the last child, is the third
text node); the facade's own javadoc ("effectively a filter on childNodes() to get Data nodes") is kept unchanged.

Single owner: only the gold decides which nodes are data nodes and where a run ends; hops 1-3 pass the list along unchanged and hop 4
joins whatever runs it receives. The lost run is not recoverable above the gold: hop 4 only sees the runs, and the dropped nodes are
in none of them. Declared alternatives (G9): hop 4 joins only non-empty runs; hop 3 answers an empty list early; hop 1 returns a
modifiable copy instead of the unmodifiable view. Each leaves the trigger failing.
Recorded bypasses (edits that work around the gold rather than repair the chain):
 B-1 a sentinel at hop 3 (or any of hops 1-4): `List<Node> padded = new ArrayList<>(nodes); padded.add(new TextNode(""));
     return Node.dataNodesAmong(padded);` hands the gold a list that never ends in a data node, so the gold's own run closing is
     never needed; the gold still drops the last run of every list that ends in a data node, against its own javadoc. Checked
     on the variant in a scratch copy (at hop 3): trigger passes, full suite 0 failing tests.
 B-2 a re-collection at hop 4 of the trailing data nodes from the list itself re-implements the gold's per-node decision above it.
 B-0 the facade's original body (or a hop filtering the list itself) re-implements the whole computation and makes the chain,
     including the gold, dead.

Lie: the facade's javadoc claims that the child nodes are first sorted by node name and the data nodes then read from the sorted
list; the chain sorts nothing (it reads the child list once, in child order). It names neither runs, the end of the list, the
omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: nodes is the list iterated; every node's kind decides what happens to it; there is no argument check.
  T2 absent: runs is returned; run is filled by the data branch, read by both emptiness decisions and added to runs; run is
     reassigned in the loop (not literal-initialised); the three decisions (data node, close at another kind, close at the end) have
     different effects.
  T3 absent: the two node kinds the gold distinguishes (data nodes, nodes of any other kind) are both treated; both places a run
     can close are present.
  T4 absent: "the runs of adjacent data nodes that it holds, in list order" and "Nodes of any other kind are not part of a run" are
     each met by a line of the body; the @param/@return clauses name no rule.
 Variant gold (javadoc, signature, the loop that adds a data node to the open run and closes a non-empty run at a node of another
 kind, then returns runs):
  T1 absent: nodes is iterated and every node's kind decides the result.
  T2 absent: runs is returned; run is filled, tested by the else-if decision and added to runs in the loop, and reassigned there;
     no literal-initialised local; no cursor, counter or flag; both branches have different effects.
  T3 absent: both node kinds named by the gold's text and tests (DataNode, any other kind) are treated; the gold's text names no
     set of run ends, positions or range ends that it would treat in part, and names no class ("all", "last", "trailing") that it
     would handle only in part.
  T4 absent: "Splits a list of nodes into the runs of adjacent data nodes that it holds, in list order" is a general description that
     the loop addresses; "Nodes of any other kind are not part of a run" is met by the instanceof branch; "@param nodes the nodes to
     split" and "@return the runs of data nodes" name no concrete rule; no inline comment; the identifiers runs and run name what they
     hold."""

EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"
WL = "src/main/java/org/jsoup/safety/Whitelist.java"

GOLD_TEXT = '''/**
 * Splits a list of nodes into the runs of adjacent data nodes that it holds, in list order. Nodes of any other kind are not
 * part of a run.
 *
 * @param nodes the nodes to split
 * @return the runs of data nodes
 */
public static List<List<DataNode>> dataNodeRuns(List<Node> nodes) {
    List<List<DataNode>> runs = new ArrayList<>();
    List<DataNode> run = new ArrayList<>();
    for (Node node : nodes) {
        if (node instanceof DataNode) {
            run.add((DataNode) node);
        } else if (!run.isEmpty()) {
            runs.add(run);
            run = new ArrayList<>();
        }
    }
    if (!run.isEmpty())
        runs.add(run);
    return runs;
}'''

HOP1 = '''/**
 * Get the data nodes of a list of nodes, as an unmodifiable list.
 * @param nodes the nodes to read
 * @return an unmodifiable list of the data nodes, in list order
 */
public static List<DataNode> unmodifiableDataNodes(List<Node> nodes) {
    return Collections.unmodifiableList(Evaluator.IsNthLastChild.dataNodesOf(nodes));
}'''

HOP2 = '''/**
 * Get the data nodes of a list of nodes.
 * @param nodes the nodes to read
 * @return the data nodes, in list order
 */
public static List<DataNode> dataNodesOf(List<Node> nodes) {
    return HtmlTreeBuilder.dataNodesIn(nodes);
}'''

HOP3 = '''/**
 * Gets the data nodes of a list of nodes.
 * @param nodes the nodes to read
 * @return the data nodes, in list order
 */
public static List<DataNode> dataNodesIn(List<Node> nodes) {
    return Node.dataNodesAmong(nodes);
}'''

HOP4 = '''/**
 * Gets the data nodes of a list of nodes, by joining the runs of adjacent data nodes that the list holds, in order.
 * @param nodes the nodes to read
 * @return the data nodes, in list order
 */
public static List<DataNode> dataNodesAmong(List<Node> nodes) {
    List<DataNode> dataNodes = new ArrayList<>();
    for (List<DataNode> run : Whitelist.dataNodeRuns(nodes))
        dataNodes.addAll(run);
    return dataNodes;
}'''

DESIGN = {
 "instance": "Jsoup-70", "project": "Jsoup", "bug_id": 70, "seed": 8329,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": EL, "class": "org.jsoup.nodes.Element", "method": "dataNodes", "near_line": 333},
 "facade_variant": "V1",
 "state_passed": "the field childNodes (List<Node>) to hop 1; no write-back",
 "reachability_probe": "ElementTest::testGetDataNodes fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "org.jsoup.nodes.Element.dataNodes(Element.java:334) from ElementTest.java:723; full suite with the probe: "
                       "1 failing test (testGetDataNodes)",
 "host_mode": "largest5",
 "host_lines": [1249, 753, 734, 725, 646],
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/ElementTest.java",
             "test_class": "org.jsoup.nodes.ElementTest", "test_method": "testGetDataNodes"},
 "expected_signature": "expected:<1> but was:<0>",
 "gold": {"method": "dataNodeRuns", "text": GOLD_TEXT,
          "fault": {"old": "        }\n"
                           "        if (!run.isEmpty())\n"
                           "            runs.add(run);\n"
                           "        return runs;\n",
                    "new": "        }\n"
                           "        return runs;\n"}},
 "chain": {
   "facade_body": "return org.jsoup.helper.HttpConnection.unmodifiableDataNodes(childNodes);",
   "lie": "The child nodes are first sorted by node name, and the data nodes are then read from the sorted list.",
   "hops": [
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "unmodifiableDataNodes",
      "imports": ["org.jsoup.nodes.DataNode", "org.jsoup.nodes.Node", "org.jsoup.select.Evaluator"], "text": HOP1},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsNthLastChild", "method": "dataNodesOf",
      "imports": ["org.jsoup.nodes.DataNode", "org.jsoup.parser.HtmlTreeBuilder"], "text": HOP2},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "dataNodesIn",
      "imports": [], "text": HOP3},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "dataNodesAmong",
      "imports": ["org.jsoup.safety.Whitelist"], "text": HOP4},
     {"file": WL, "class": "org.jsoup.safety.Whitelist", "method": "dataNodeRuns",
      "imports": ["org.jsoup.nodes.DataNode", "org.jsoup.nodes.Node", "java.util.ArrayList", "java.util.List"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Element::data",
              "org.jsoup.nodes.Element::textNodes"],
 "ownership_reason": "Only the gold decides which child nodes are data nodes and where a run of adjacent data nodes ends; hops 1-3 "
                     "pass the child list along unchanged and hop 4 joins, in order, the runs it receives. The gold's javadoc "
                     "promises the runs of adjacent data nodes that the list holds; a script element whose only child is its "
                     "data node holds one such run, and the gold returns none. The dropped nodes are in no run that reaches hop "
                     "4, so no caller above the gold can restore them from the gold's output. The convention that every data "
                     "node of the child list is collected, the ones at its end included, is pinned outside the gold: "
                     "Element.data() appends the data of every DataNode child in child order (HtmlParserTest handlesDataOnlyTags "
                     "and preservesSpaceInScript, where the data node is the element's last and only child), and "
                     "Element.textNodes(), the sibling filter on childNodes, keeps the trailing text node (ElementTest "
                     "testGetTextNodes: \" Four\", the last child, is the third text node); the facade's own javadoc calls the "
                     "method a filter on childNodes() to get Data nodes.",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::testGetTextNodes",
                     "org.jsoup.parser.HtmlParserTest::handlesDataOnlyTags",
                     "org.jsoup.parser.HtmlParserTest::preservesSpaceInScript"],
 "compensating": {
   "chain": [
     {"file": ND, "old": "            dataNodes.addAll(run);",
      "new": "            if (!run.isEmpty()) dataNodes.addAll(run);",
      "why": "hop 4 joins only the runs that are not empty"},
     {"file": HTB, "old": "        return Node.dataNodesAmong(nodes);",
      "new": "        if (nodes.isEmpty()) return new ArrayList<DataNode>(); return Node.dataNodesAmong(nodes);",
      "why": "hop 3 answers an empty list of nodes early"},
     {"file": HC, "old": "        return Collections.unmodifiableList(Evaluator.IsNthLastChild.dataNodesOf(nodes));",
      "new": "        return new ArrayList<DataNode>(Evaluator.IsNthLastChild.dataNodesOf(nodes));",
      "why": "hop 1 returns a modifiable copy instead of the unmodifiable view"},
   ],
 },
 "host_notes": "host_mode largest5 (no other public class of 1500 lines or more on the checkout). Hosts are exactly "
               "hosts_hop_order of the task record, in that order, none substituted: helper.HttpConnection (hop 1, 1249 lines), "
               "select.Evaluator (hop 2, 753), parser.HtmlTreeBuilder (hop 3, 734), nodes.Node (hop 4, 725), safety.Whitelist "
               "(hop 5, gold, 646; the smallest host). The facade's file Element.java is excluded. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 8329 + 100 + i (as mr3_spec.py inserts them): hop 1 after `url` "
               "(HttpConnection.url(URL), line idx 127, seed 8429, outer class), hop 2 after `IsNthLastChild` (the constructor of "
               "the public static final nested class Evaluator.IsNthLastChild, line idx 495, seed 8430; the hop is a public "
               "static method of that nested class and is called as Evaluator.IsNthLastChild.dataNodesOf), hop 3 after `insert` "
               "(line idx 223, seed 8431, outer class), hop 4 after `childNodesCopy` (line idx 224, seed 8432, outer class), hop "
               "5 after `basicWithImages` (line idx 141, seed 8433, outer class). All five are public classes in which a static "
               "method compiles (Evaluator and Node are abstract, which does not affect a static method). The facade calls hop 1 "
               "by its fully-qualified name; each hop imports the next host.",
}
