"""Main run Jsoup-37__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade on a bug that has no static facade; fixed
checkout of Defects4J Jsoup-37, whose real bug modified org.jsoup.nodes.Element, the facade's class). No paired static instance
(B8 note section 1).

Facade: Element.dataNodes() (instance method; allowed targets Element.children / Element.textNodes / Element.dataNodes,
BATCH8_PREREGISTRATION.md row 263; dataNodes has facade_planned_by = null, so no facade reuse). children() was not used: it is planned
by Jsoup-22__i (distinctness preferred) and is reached by many tests and by production callers (siblingElements, elementSiblingIndex,
the nth-child evaluators), so no omission in it could be caught by a single test. textNodes() was not used: its three tests
(ElementTest::testGetTextNodes, ::testManipulateTextNodes, TextNodeTest::testWithSupplementaryCharacter) all select a text node that is
the last child of its parent, so the omission below (and every other quiet omission found in a selection over the child list) would
fail all three of them. dataNodes() is reached by exactly one test, ElementTest::testGetDataNodes.
Original computation: the child nodes (the field childNodes, declared in Node) are filtered to the DataNode instances, in order, and the
result is returned as an unmodifiable list; the data nodes themselves are the live children (not copies).

facade_variant: V1 (state as parameters). state_passed: the field childNodes (List<Node>, package-private in Node, read inside Element
of the same package, no visibility change) and the class literal DataNode.class are passed to hop 1; no field is written, no write-back.
The facade body is a single call to hop 1 (the original has no guard). No private method of Element is used (no V4), no package-private
type passes through a hop (List<Node> and Class<DataNode> are public types, so no V3/V5). No signature, modifier, override or throws
change; no new type; no reflection (Class.isInstance and Class.cast are ordinary type tests); no test edit.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-37-probe of the fixture, the first statement of
dataNodes() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.jsoup.nodes.ElementTest::testGetDataNodes`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
Element.dataNodes(Element.java:226), called from ElementTest.testGetDataNodes(ElementTest.java:557). Full suite with the probe: 1 failing
test (testGetDataNodes only; dataNodes has no production caller). The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; hosts_hop_order of batch8_tasks.json, used in that order, none substituted):
  hop 1 helper.HttpConnection  706 lines  nodesOfType      plumbing: the result as an unmodifiable list
  hop 2 select.Evaluator       701 lines  collectNodes     aggregation: creates the result list and returns it once filled
                                                           (the seeded anchor lies inside the public static nested class
                                                           Evaluator.CssNthEvaluator; hop 1 calls Evaluator.CssNthEvaluator.collectNodes)
  hop 3 nodes.Node             667 lines  appendNodesOfType pass-through
  hop 4 select.Elements        561 lines  addNodesOfType   placement: adds the nodes of each run the gold reports, in order
  hop 5 safety.Whitelist       464 lines  runsOfType       GOLD: one pass over the nodes deciding, per node, whether it is of the
                                                           type, and recording each run of consecutive such nodes as index ranges
Host newline counts 706, 701, 667, 561, 464; the smallest host (and the gold host) is Whitelist with 464 lines (C10F addendum section 1:
hosts under 1500 lines are expected in this regime).
The correct configuration returns the same nodes as the original, in the same order, for every child list: every node that is an
instance of the type lies in exactly one run (a run is closed at the next node of another type or at the end of the list), the runs
are reported in list order and do not overlap, and hop 4 adds the nodes of each run in order; hop 1 wraps the result unmodifiable.

Fault (one-line omission of a boundary step in the gold): the step that records the run still open at the end of the list is dropped
(`if (start >= 0) runs.add(new int[] {start, nodes.size()});` is removed), so data nodes that are the last children of their element
are not reported. The gold then reads as the ordinary routine "record a run each time a node of another type ends it". Trigger: the
EXISTING test ElementTest::testGetDataNodes: script's only child is a data node, which is the last child, so assertEquals(1,
scriptData.size()) fails with expected:<1> but was:<0>. It is the only test that newly fails: dataNodes has no production caller and no
other test calls it (probe above), and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the runs of consecutive nodes of the type, each as the index of its first node and
the index after its last node, in order) and is silent on how a run is closed. The variant does not report the run [0, 1) of the
script's child list, which is a run of consecutive data nodes, so the contract is violated on the trigger input. The convention (every
child of the selected type is selected, the last child included) is pinned outside the gold: the intact sibling filters
Element.textNodes and Element.children do the same selection over the same child list and select a last child of their type; passing
tests ElementTest::testGetTextNodes (the last child " Four" is selected), TextNodeTest::testWithSupplementaryCharacter (the body's only
and last child is selected) and ElementTest::testManipulateTextNodes (the split-off last child is counted: 4 text nodes).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: nodes bounds the loop and supplies every node tested; type decides each node; neither is only argument-checked.
  T2 absent: i advances; start is set at a run's first node and reset after the run is recorded; runs is returned; the two branches
     (open/extend a run, close a run) have different effects; no local is dead or frozen.
  T3 absent: both indexes of every run are recorded; a run is closed both at a node of another type and at the end of the list; no
     class named in the gold's text is handled in part.
  T4 absent: 'runs of consecutive nodes', 'the index of its first node, and the index after its last node', 'in list order' and the
     @param/@return clauses are met by lines of the body.
 Variant gold (javadoc, signature, `List<int[]> runs = ...`, `int start = -1`, the loop with `if (type.isInstance(nodes.get(i)))` /
 `else if (start >= 0)`, `return runs;`):
  T1 absent: nodes bounds the loop and is read for each node; type decides each node; both change the result.
  T2 absent: i advances; start is assigned in the loop (`start = i`, `start = -1`) and read into each recorded run; runs is returned;
     both branches have different effects; no local is frozen (start is reassigned) or dead.
  T3 absent: the two indexes of a run (first node, index after the last) are both recorded for every run that is recorded; the
     gold's text names no set of ways a run can end (closure rule: no parameter, flag, Java type or named format fixes such a set),
     and no class the text names (nodes of the type, runs) is split into members of which only some are handled.
  T4 absent: 'the runs of consecutive nodes of a type' and 'in list order' are general descriptions that lines of the body address
     (the loop tests every node and records runs in order); 'the index of its first node, and the index after its last node' is met
     by `new int[] {start, i}`; no inline comment; identifiers (runs, start, type, nodes) name nothing the body does not meet.

Single owner: only the gold decides which nodes are of the type and reports where they are; hops 1, 2 and 3 pass the list along and
create or wrap the result, and hop 4 only adds the nodes of each reported run (casting them to the type), adding no node outside a
reported run. Once the gold leaves the last run unreported, its nodes can reach the result only if a caller re-tests the nodes itself
(a second implementation of the gold's decision, contrary to hop 4's documented role) or replaces the gold. Declared alternatives
(G9): hop 1 returns the list without wrapping it; hop 3 passes a copy of the node list; hop 2 creates a LinkedList. None makes the trigger pass.
Recorded bypasses: B-0 the facade (its original body) or hop 4 (`for (Node node : nodes) if (type.isInstance(node))
found.add(type.cast(node));`) filters the child list itself, discarding the gold's output; B-1 hop 4 also adds the nodes after the last
reported run that are of the type (a second implementation of the gold's per-node decision, contrary to hop 4's javadoc, which adds the
nodes of the reported runs only).

Lie: the facade's javadoc claims the data nodes are counted first, so that the list is created with exactly the capacity it needs; no
step of the chain counts the data nodes or sizes a list by such a count (hop 2 creates a default ArrayList). It names neither the end of
the list nor runs nor any hop."""

ELEMENT = "src/main/java/org/jsoup/nodes/Element.java"
HTTP = "src/main/java/org/jsoup/helper/HttpConnection.java"
EVAL = "src/main/java/org/jsoup/select/Evaluator.java"
NODE = "src/main/java/org/jsoup/nodes/Node.java"
ELEMS = "src/main/java/org/jsoup/select/Elements.java"
WL = "src/main/java/org/jsoup/safety/Whitelist.java"

GOLD_TEXT = '''/**
 * Find the runs of consecutive nodes of a type in a list of nodes.
 * <p/>
 * Each run is given as a pair of indexes into the list: the index of its first node, and the index after its last node. The
 * runs are given in list order.
 * @param nodes nodes to search
 * @param type type of node to find
 * @return the runs, in list order
 */
public static List<int[]> runsOfType(List<Node> nodes, Class<?> type) {
    List<int[]> runs = new ArrayList<int[]>();
    int start = -1;
    for (int i = 0; i < nodes.size(); i++) {
        if (type.isInstance(nodes.get(i))) {
            if (start < 0) start = i;
        } else if (start >= 0) {
            runs.add(new int[] {start, i});
            start = -1;
        }
    }
    if (start >= 0) runs.add(new int[] {start, nodes.size()});
    return runs;
}'''

HOP1 = '''/**
 * Get the nodes of a node list that are of the given type, as an unmodifiable list.
 * @param nodes nodes to select from
 * @param type type of node to select
 * @param <T> the node type
 * @return an unmodifiable list of the selected nodes, in their order in the node list
 */
public static <T extends Node> List<T> nodesOfType(List<Node> nodes, Class<T> type) {
    return Collections.unmodifiableList(Evaluator.CssNthEvaluator.collectNodes(nodes, type));
}'''

HOP2 = '''/**
 * Collect the nodes of a node list that are of the given type into a new list.
 * @param nodes nodes to select from
 * @param type type of node to select
 * @param <T> the node type
 * @return a new list of the selected nodes, in their order in the node list
 */
public static <T extends Node> List<T> collectNodes(List<Node> nodes, java.lang.Class<T> type) {
    List<T> found = new ArrayList<T>();
    Node.appendNodesOfType(nodes, type, found);
    return found;
}'''

HOP3 = '''/**
 * Add the nodes of a node list that are of the given type to a list, in their order in the node list.
 * @param nodes nodes to select from
 * @param type type of node to select
 * @param found list to add the selected nodes to
 * @param <T> the node type
 */
public static <T extends Node> void appendNodesOfType(List<Node> nodes, Class<T> type, List<T> found) {
    Elements.addNodesOfType(nodes, type, found);
}'''

HOP4 = '''/**
 * Add the nodes of a node list that are of the given type to a list, in their order in the node list.
 * <p/>
 * The runs of consecutive nodes of the type are found first, and the nodes of each run are then added in turn.
 * @param nodes nodes to select from
 * @param type type of node to select
 * @param found list to add the selected nodes to
 * @param <T> the node type
 */
public static <T extends Node> void addNodesOfType(List<Node> nodes, Class<T> type, List<T> found) {
    for (int[] run : Whitelist.runsOfType(nodes, type)) {
        for (Node node : nodes.subList(run[0], run[1]))
            found.add(type.cast(node));
    }
}'''

DESIGN = {
 "instance": "Jsoup-37", "project": "Jsoup", "bug_id": 37, "seed": 2484,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the field childNodes (List<Node>, declared in Node) and the class literal DataNode.class, passed to hop 1; "
                 "no write-back",
 "host_mode": "largest5", "host_lines": [706, 701, 667, 561, 464],
 "reachability_probe": "dataNodes() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-37-probe: ElementTest::testGetDataNodes fails with PROBE-REACHED at "
                       "Element.dataNodes(Element.java:226); full suite with the probe: 1 failing test (testGetDataNodes only)",
 "facade": {"file": ELEMENT, "class": "org.jsoup.nodes.Element", "method": "dataNodes", "near_line": 225},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/ElementTest.java",
             "test_class": "org.jsoup.nodes.ElementTest", "test_method": "testGetDataNodes"},
 "expected_signature": "expected:<1> but was:<0>",
 "gold": {"method": "runsOfType", "text": GOLD_TEXT,
          "fault": {"old": "        if (start >= 0) runs.add(new int[] {start, nodes.size()});\n        return runs;",
                    "new": "        return runs;"}},
 "chain": {
   "facade_body": "return org.jsoup.helper.HttpConnection.nodesOfType(childNodes, DataNode.class);",
   "lie": "The data nodes are counted first, so that the list is created with exactly the capacity it needs.",
   "hops": [
     {"file": HTTP, "class": "org.jsoup.helper.HttpConnection", "method": "nodesOfType",
      "imports": ["org.jsoup.nodes.Node", "org.jsoup.select.Evaluator"], "text": HOP1},
     {"file": EVAL, "class": "org.jsoup.select.Evaluator.CssNthEvaluator", "method": "collectNodes",
      "imports": ["java.util.ArrayList"], "text": HOP2},
     {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "appendNodesOfType",
      "imports": ["org.jsoup.select.Elements"], "text": HOP3},
     {"file": ELEMS, "class": "org.jsoup.select.Elements", "method": "addNodesOfType",
      "imports": ["org.jsoup.safety.Whitelist"], "text": HOP4},
     {"file": WL, "class": "org.jsoup.safety.Whitelist", "method": "runsOfType",
      "imports": ["java.util.ArrayList", "java.util.List", "org.jsoup.nodes.Node"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Element::textNodes", "org.jsoup.nodes.Element::children"],
 "ownership_reason": "Only the gold decides which child nodes are of the type and reports where they are, as runs of consecutive "
                     "nodes of the type. Hops 1, 2 and 3 pass the child list along and create or wrap the result; hop 4 only adds "
                     "the nodes of each run the gold reports, in order, and adds no node outside a reported run. When the gold "
                     "leaves the run that ends at the end of the list unreported, its nodes can reach the result only if a caller "
                     "re-tests the nodes itself (a second implementation of the gold's decision, contrary to hop 4's documented "
                     "role) or replaces the gold. The gold's javadoc promises the runs of consecutive nodes of the type; the "
                     "variant omits the run [0, 1) of the script element's child list. The convention (every child of the selected "
                     "type is selected, the last child included) is pinned outside the gold by the intact sibling filters "
                     "Element.textNodes and Element.children over the same child list, and by the passing tests "
                     "ElementTest::testGetTextNodes (the last child ' Four' is selected), "
                     "TextNodeTest::testWithSupplementaryCharacter (the body's only and last child is selected) and "
                     "ElementTest::testManipulateTextNodes (the split-off last child is counted).",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::testGetTextNodes",
                     "org.jsoup.nodes.TextNodeTest::testWithSupplementaryCharacter",
                     "org.jsoup.nodes.ElementTest::testManipulateTextNodes"],
 "compensating": {
   "chain": [
     {"file": HTTP, "old": "return Collections.unmodifiableList(Evaluator.CssNthEvaluator.collectNodes(nodes, type));",
      "new": "return Evaluator.CssNthEvaluator.collectNodes(nodes, type);",
      "why": "hop 1 returns the selected nodes without wrapping them"},
     {"file": NODE, "old": "Elements.addNodesOfType(nodes, type, found);",
      "new": "Elements.addNodesOfType(new ArrayList<Node>(nodes), type, found);",
      "why": "hop 3 passes a copy of the node list"},
     {"file": EVAL, "old": "List<T> found = new ArrayList<T>();",
      "new": "List<T> found = new java.util.LinkedList<T>();",
      "why": "hop 2 collects into a linked list"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, used in that order; none substituted, none chosen by this "
               "builder): helper.HttpConnection (hop 1, 706 lines), select.Evaluator (hop 2, 701), nodes.Node (hop 3, 667), "
               "select.Elements (hop 4, 561), safety.Whitelist (hop 5, gold, 464; the smallest host). The facade's file Element.java "
               "is excluded (facade_files_excluded). Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with "
               "seed 2484 + 100 + i, as mr3_spec.py inserts them: hop 1 after ignoreHttpErrors (seed 2584), hop 2 after the "
               "constructor CssNthEvaluator(int) (2585), hop 3 after after (2586), hop 4 after html (2587), hop 5 after addProtocols "
               "(2588). Evaluator indents its nested-class members with tabs, so the anchor picker took the constructor of the public "
               "static abstract nested class Evaluator.CssNthEvaluator as an outer member and the hop is inserted inside that nested "
               "class; a public static method compiles there, so the host is kept (it can carry the hop) and hop 1 calls it as "
               "Evaluator.CssNthEvaluator.collectNodes; its type parameter is spelled java.lang.Class because Evaluator declares a "
               "nested class named Class. Each hop imports the next host as needed (HttpConnection imports nodes.Node and "
               "select.Evaluator; Evaluator imports java.util.ArrayList; Node imports select.Elements; Elements imports "
               "safety.Whitelist; Whitelist imports java.util.ArrayList, java.util.List and nodes.Node).",
}
