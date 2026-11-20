"""Main run Jsoup-66__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Jsoup-66, a bug without a static facade; the real bug modified org.jsoup.nodes.Element, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE section 1).

Facade: Element.hasText() (instance method; allowed targets Element.textNodes / Element.dataNodes / Element.hasText,
BATCH8_PREREGISTRATION.md row 270; facade_planned_by null for all three; this one is distinct, no facade reuse). textNodes() and
dataNodes() were not used: each is a one-condition filter of the child list (instanceof TextNode / DataNode) with nothing a quiet
one-line omission could live in (dropping the filter leaves a visibly unfiltered copy, and no special-case step exists), and their
tests check only the filtered contents (the unmodifiable wrapper is not tested). hasText() carries a search over the whole subtree.
Original computation: for each child node, a text node that is not blank (TextNode.isBlank, StringUtil.isWhitespace: space, tab,
LF, FF, CR) gives true; an element child gives true if its own hasText() does (recursion); any other node (data, comment) is ignored;
otherwise false.

facade_variant: V2 (receiver as parameter). The search needs the receiver itself, as the node whose subtree is searched and as the
point where the walk ends, and only its public Node methods (childNodeSize(), childNode(int), previousSibling(), parentNode()); the
private field childNodes alone (V1) would not give the node at which the walk ends. state_passed: `this` (typed Element) to hop 1;
no field is read directly, none is written, no write-back. No private method is called (no V4); no package-private type is involved
(no V3/V5). The facade body is one call to hop 1 (the original has no guard). No visibility is widened, no type is added, no
signature, modifier, override or throws clause changes, no reflection, no test edit.

reachability_probe (C10i addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-66-probe of the fixture, the first
statement of hasText() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK.
ElementTest::testHasText, ElementsTest::hasText and ElementsTest::eachText each fail with java.lang.IllegalStateException:
PROBE-REACHED at org.jsoup.nodes.Element.hasText(Element.java:1117). The facade's production callers are Elements.hasText and
Elements.eachText.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, in that order, none substituted):
  hop 1 helper.HttpConnection   1204 lines  hasTextContent   pass-through
  hop 2 select.Evaluator         753 lines  hasNonBlankText  decision: an element without child nodes has no text
                                                             (placed inside the nested class Evaluator.IsRoot by the seeded anchor)
  hop 3 parser.HtmlTreeBuilder   725 lines  elementHasText   pass-through
  hop 4 nodes.Node               714 lines  holdsText        pass-through
  hop 5 safety.Whitelist         646 lines  containsText     GOLD: the whole search of the subtree (depth first, without
                                                             recursion, from the last child node back) and the per-node test
Host newline counts 1204, 753, 725, 714, 646; the smallest host (and the gold host) is Whitelist with 646 lines (C10F addendum
section 1: hosts under 1500 lines are expected in this regime).

Gold (correct): the walk of NodeTraversor.traverse, mirrored to run from the last child node back. It starts at the node itself
with depth 0, tests each visited node (a text node that is not blank gives true), descends into the last child node (depth + 1),
and at a node without child nodes climbs to the parent while there is no previous sibling and depth > 0 (depth - 1); when the climb
has come back to the node itself the walk ends (`if (current == node) break;`), otherwise it moves to the previous sibling. It
visits every node of the subtree exactly once, tests text nodes with the same TextNode.isBlank and ignores every other node, as the
original does (only elements have child nodes; data and comment nodes have none). Order does not change an existence test. Hop 2's
shortcut for an element without child nodes gives the same false the original gives. No method called has a side effect on the tree.

Fault (one-line omission of a decision in the gold): the line `if (current == node) break;` after the climb is dropped (the old/new
pair below quotes it with the line before and after). The gold then reads as the ordinary routine "walk depth first from the last
child back, climbing while a node has no previous sibling and depth > 0, then move to the previous sibling, until a text node that
is not blank is found or the walk runs out"; once the climb has come back to the searched node at depth 0, the walk moves on to the
node's previous siblings and searches them as well. Trigger: the EXISTING test ElementsTest::hasText. Its first assertion holds
(the first div finds "Hello" inside itself); assertFalse(doc.select("div + div").hasText()) at ElementsTest.java:124 fails, because
the second div's only child is an empty paragraph, after which the climb comes back to the second div, the walk moves to its
previous sibling, the first div, and finds "Hello". It is the only test that newly fails: the walk comes back to the searched node
only when no text node in its subtree is non-blank and the node has child nodes, which among the facade's three tests happens only
in ElementsTest::hasText (every other call finds text inside the element, or has no child nodes and is answered by hop 2); gate G5
checks the full suite.

The gold's javadoc states the idiomatic contract (the facade's own wording: the node has text content that is not just whitespace;
true if a text node that is not blank is found) and is silent on where the walk ends. The second div has no text content; the
variant answers true. The convention that a search of an element covers only the element's subtree is pinned outside the gold: the
intact NodeTraversor.traverse and NodeTraversor.filter (the same walk without recursion, which climbs only while `depth > 0` and
stops `if (node == root)`), used in production by Element.text() over `this`; passing tests: TraversorTest::filterVisit and
ElementsTest::traverse (the walk over each div stays inside that div: "<div><p><#text></#text></p></div><div><#text></#text></div>"),
and, through the chain, ElementTest::testHasText (a div whose text is in a child paragraph; an empty paragraph after it) and
ElementsTest::eachText (thirteen paragraphs, the last empty, and two divs).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: node is the start of the walk and the point where it ends; its value changes the result.
  T2 absent: current is the walk's cursor and is assigned on every path (last child, parent, previous sibling); depth is raised on
     each descent, lowered on each climb and read in the climb condition; the text test returns, the child test chooses between two
     different moves, the end test ends the walk (a different effect from moving on). The outer `while (current != null)` is a loop
     condition (the NodeTraversor idiom), not a branch, case or ternary.
  T3 absent: only text nodes get a test (one node class of an unnamed larger set); no pair, range end or named class is handled in
     part (descent and climb both move the cursor and both update depth).
  T4 absent: 'has any text content (that is not just whitespace)' and '@return true if a text node that is not blank is found' are
     met by the TextNode/isBlank test; 'depth first, without recursion, from the last child node back' is met by the descent to the
     last child, the climb and the move to the previous sibling; '@param node the node to test' names nothing concrete.
 Variant gold (javadoc, signature, `Node current = node; int depth = 0;`, the loop, the text test, the descent with depth++, the
 climb `while (current.previousSibling() == null && depth > 0) { current = current.parentNode(); depth--; }`, `current =
 current.previousSibling();`, `return false`):
  T1 absent: node is read as the start of the walk; its value changes the result.
  T2 absent: current advances on every path; depth is assigned in the loop (++ on descent, -- on climb) and is read in the climb
     condition, so it decides how far the climb goes; the walk ends when the previous sibling is null, so the loop condition and
     `return false` are live; every decision has two different effects; no dead or frozen local.
  T3 absent: no closed set is handled in part (text nodes are the only class tested; descent and climb are both present and both
     update depth; no range ends, no pair halves).
  T4 absent: the javadoc names no bound of the walk ('the search runs depth first, without recursion, from the last child node
     back' is met by the moves); 'has any text content' is a general description that the text test addresses; identifiers (node,
     current, depth) name nothing the body does not meet; no inline comment.

Single owner: only the gold decides which nodes are examined and whether a node carries text. Hops 1, 3 and 4 pass the element
along; hop 2 only answers false for an element without child nodes (the original's empty loop), and passes every other element on.
Once the gold's walk has moved past the searched node, no caller can bring it back or tell which node the text came from (the gold
returns a boolean). Declared alternatives (G9): hop 2 also answers false for an element without text nodes of its own; hop 2 also
answers false for an element whose child nodes are all elements; hop 3 answers false for a detached element. None makes the trigger
pass with the full suite (the first two break the first assertion of the trigger and testHasText/eachText; the third changes
nothing for attached elements).
Recorded bypasses (each makes another implementation decide, or hands the gold a different node than the element, discarding or
overriding the gold's answer for the element itself):
 B-0 the facade (its original recursive body) or any hop returning `!element.text().isEmpty()` (Element.text() walks with the
     intact NodeTraversor) instead of calling on, which discards the rest of the chain including the gold.
 B-1 hop 1 or hop 2 conjoins `!element.text().isEmpty()` before the call, so that an element without text never reaches the gold
     (a second implementation of the whole decision; the gold then only repeats it).
 B-2 hop 3 or hop 4 passes `element.clone()` (a detached copy without siblings) instead of the element, so that the walk has nothing
     before the copy to move to; the gold's walk is unchanged and still moves past any attached node it is given.

Lie: the facade's javadoc claims the element's text is collected first, with its whitespace normalised, and then tested for being
empty; no step of the chain collects or normalises text (the gold tests text nodes one by one with isBlank). It names neither the
end of the walk nor any hop."""

ELEMENT = "src/main/java/org/jsoup/nodes/Element.java"
HTTP = "src/main/java/org/jsoup/helper/HttpConnection.java"
EVAL = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
NODE = "src/main/java/org/jsoup/nodes/Node.java"
WL = "src/main/java/org/jsoup/safety/Whitelist.java"

GOLD_TEXT = '''/**
 * Test if a node has any text content (that is not just whitespace).
 * The search runs depth first, without recursion, from the last child
 * node back.
 *
 * @param node the node to test
 * @return true if a text node that is not blank is found
 */
public static boolean containsText(Node node) {
    Node current = node;
    int depth = 0;
    while (current != null) {
        if (current instanceof TextNode && !((TextNode) current).isBlank())
            return true;
        if (current.childNodeSize() > 0) {
            current = current.childNode(current.childNodeSize() - 1);
            depth++;
        } else {
            while (current.previousSibling() == null && depth > 0) {
                current = current.parentNode();
                depth--;
            }
            if (current == node)
                break;
            current = current.previousSibling();
        }
    }
    return false;
}'''

HOP1 = '''/**
 * Test if an element has any text content (that is not just whitespace).
 *
 * @param element the element to test
 * @return true if the element has non-blank text content
 */
public static boolean hasTextContent(Element element) {
    return Evaluator.IsRoot.hasNonBlankText(element);
}'''

HOP2 = '''/**
 * Test if an element has any text content (that is not just whitespace).
 * An element without child nodes has none.
 * @param element the element to test
 * @return true if the element has non-blank text content
 */
public static boolean hasNonBlankText(Element element) {
    if (element.childNodeSize() == 0)
        return false;
    return HtmlTreeBuilder.elementHasText(element);
}'''

HOP3 = '''/**
 * Test if an element with child nodes has any text content (that is not
 * just whitespace).
 * @param element the element to test, with at least one child node
 * @return true if the element has non-blank text content
 */
public static boolean elementHasText(Element element) {
    return Node.holdsText(element);
}'''

HOP4 = '''/**
 * Test if an element with child nodes has any text content (that is not just whitespace).
 * @param element the element to test, with at least one child node
 * @return true if the element has non-blank text content
 */
public static boolean holdsText(Element element) {
    return Whitelist.containsText(element);
}'''

DESIGN = {
 "instance": "Jsoup-66", "project": "Jsoup", "bug_id": 66, "seed": 5995,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver `this` (typed Element) to hop 1; no field read directly, no field written, no write-back",
 "host_mode": "largest5", "host_lines": [1204, 753, 725, 714, 646],
 "reachability_probe": "hasText() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-66-probe: ElementTest::testHasText, ElementsTest::hasText and "
                       "ElementsTest::eachText each fail with PROBE-REACHED at "
                       "org.jsoup.nodes.Element.hasText(Element.java:1117)",
 "facade": {"file": ELEMENT, "class": "org.jsoup.nodes.Element", "method": "hasText", "near_line": 1116},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/select/ElementsTest.java",
             "test_class": "org.jsoup.select.ElementsTest", "test_method": "hasText"},
 "expected_signature": "ElementsTest.hasText(ElementsTest.java:124)",
 "gold": {"method": "containsText", "text": GOLD_TEXT,
          "fault": {"old": "                }\n                if (current == node)\n                    break;\n                current = current.previousSibling();",
                    "new": "                }\n                current = current.previousSibling();"}},
 "chain": {
   "facade_body": "return org.jsoup.helper.HttpConnection.hasTextContent(this);",
   "lie": "The element's text is collected first, with its whitespace normalised, and is then tested for being empty.",
   "hops": [
     {"file": HTTP, "class": "org.jsoup.helper.HttpConnection", "method": "hasTextContent",
      "imports": ["org.jsoup.nodes.Element", "org.jsoup.select.Evaluator"], "text": HOP1},
     {"file": EVAL, "class": "org.jsoup.select.Evaluator.IsRoot", "method": "hasNonBlankText",
      "imports": ["org.jsoup.parser.HtmlTreeBuilder"], "text": HOP2},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "elementHasText",
      "imports": [], "text": HOP3},
     {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "holdsText",
      "imports": ["org.jsoup.safety.Whitelist"], "text": HOP4},
     {"file": WL, "class": "org.jsoup.safety.Whitelist", "method": "containsText",
      "imports": ["org.jsoup.nodes.Node", "org.jsoup.nodes.TextNode"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.select.NodeTraversor::traverse", "org.jsoup.select.NodeTraversor::filter",
              "org.jsoup.nodes.Element::text"],
 "ownership_reason": "Only the gold decides which nodes are examined and whether a node carries text: it walks the subtree of the "
                     "element depth first, without recursion, from the last child node back, and tests each text node with "
                     "isBlank. Hops 1, 3 and 4 pass the element along; hop 2 only answers false for an element without child "
                     "nodes. The gold returns a boolean, so once its walk has moved past the searched element into the nodes "
                     "before it, no caller can undo that or tell where the text was found. The gold's javadoc promises the "
                     "facade's contract (the node has text content that is not just whitespace); the second div of the trigger "
                     "has none, and the variant answers true from the text of the first div. The convention that a search of "
                     "an element covers only its subtree is pinned outside the gold: the intact NodeTraversor.traverse and "
                     "NodeTraversor.filter do the same walk without recursion and stop at the root (climbing only while depth "
                     "> 0, then `if (node == root)`), used in production by Element.text() over `this`; TraversorTest::"
                     "filterVisit and ElementsTest::traverse pass (each div's walk stays inside that div), as do, through the "
                     "chain, ElementTest::testHasText and ElementsTest::eachText.",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::testHasText",
                     "org.jsoup.select.ElementsTest::eachText",
                     "org.jsoup.select.TraversorTest::filterVisit",
                     "org.jsoup.select.ElementsTest::traverse"],
 "compensating": {
   "chain": [
     {"file": EVAL, "old": "        if (element.childNodeSize() == 0)",
      "new": "        if (element.childNodeSize() == 0 || element.textNodes().isEmpty())",
      "why": "hop 2 also answers false for an element without text nodes of its own"},
     {"file": EVAL, "old": "        if (element.childNodeSize() == 0)",
      "new": "        if (element.childNodeSize() == 0 || element.children().size() == element.childNodeSize())",
      "why": "hop 2 also answers false for an element whose child nodes are all elements"},
     {"file": HTB, "old": "return Node.holdsText(element);",
      "new": "return element.hasParent() && Node.holdsText(element);",
      "why": "hop 3 answers false for a detached element"},
   ],
   "bypasses": [
     "the facade or any hop returns !element.text().isEmpty() instead of calling on (Element.text() walks with the intact "
     "NodeTraversor); the gold is never called",
     "hop 1 or hop 2 conjoins !element.text().isEmpty() before the call; a second implementation of the whole decision",
     "hop 3 or hop 4 passes element.clone() (a detached copy) instead of the element; the gold's walk is unchanged and still "
     "moves past any attached node it is given",
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this "
               "builder): helper.HttpConnection (hop 1, 1204 lines), select.Evaluator (hop 2, 753), parser.HtmlTreeBuilder "
               "(hop 3, 725), nodes.Node (hop 4, 714), safety.Whitelist (hop 5, gold, 646; the smallest host). All five are "
               "public top-level classes in which a public static method compiles; the facade's file Element.java is excluded. "
               "Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 5995 + 100 + i, as "
               "mr3_spec.py inserts them: hop 1 after HttpConnection.execute (seed 6095), hop 2 after IsRoot.matches (6096), "
               "hop 3 after inListItemScope (6097), hop 4 after Node.wrap (6098), hop 5 after Whitelist.relaxed (6099). The "
               "Evaluator anchor lies inside the public static final nested class Evaluator.IsRoot (its members are indented "
               "with four spaces and a tab, which the picker's four-space filter takes for outer members), so hop 2 is a "
               "public static method of Evaluator.IsRoot and hop 1 calls it as Evaluator.IsRoot.hasNonBlankText; the class "
               "still carries a public static method, so the host was not substituted. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host as needed (HtmlTreeBuilder already imports Node and "
               "Element; Whitelist imports Node and TextNode).",
}
