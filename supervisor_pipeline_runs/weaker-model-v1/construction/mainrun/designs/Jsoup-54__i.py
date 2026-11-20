"""Main run Jsoup-54__i (cell C10i, batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Jsoup-54; the real bug modified org.jsoup.helper.W3CDom, the facade's class). No static pair (pool v2: no_tested_static).

Facade: W3CDom.fromJsoup(org.jsoup.nodes.Document) (the only allowed candidate of batch9_tasks.json; facade_planned_by null, no
facade reuse). Original computation: Validate.notNull(in); set the protected factory field namespace-aware; make a DocumentBuilder
and a new W3C Document; convert(in, out), i.e. set the document URI from in.location() when it is not blank, take the document's
first element in.child(0) ("skip the #root node") and walk it with new NodeTraversor(new W3CBuilder(out)).traverse(rootEl); return
the W3C document; a ParserConfigurationException becomes an IllegalStateException.

facade_variant: V1 (state as parameters). The method reads one protected field (factory) and writes none: the facade keeps the
argument guard Validate.notNull(in), reads the field factory (inside W3CDom) and passes it with the jsoup document to hop 1, and
returns the W3C document the chain returns. The chain carries the rest of fromJsoup and of the public method convert it called
(document builder, URI, root element, depth-first walk); the walk's visitor is the existing protected nested W3CDom.W3CBuilder,
created in hop 2, whose host HttpConnection is in the same package (org.jsoup.helper), and handed down typed as the public interface
org.jsoup.select.NodeVisitor, so no hop in another package names the protected type (the V5 arrangement, without generics). V2
(passing `this` and calling convert) is not used: convert would then do the whole per-node work and the gold would own nothing. No
private method is called (no V4), no private logic is copied (W3CBuilder's private copyAttributes/updateNamespaces stay where they
are; the chain re-states only the public convert and a depth-first walk equivalent to the public NodeTraversor.traverse). No
visibility change, no new type (no anonymous class), no reflection, no signature/modifier/override/throws change, no test edit.
state_passed: the protected field factory (DocumentBuilderFactory) and the parameter in to hop 1; no write-back; the facade returns
hop 1's W3C Document.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-54-probe of the fixture, the
first statement of fromJsoup was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. defects4j test -t
org.jsoup.helper.W3CDomTest::convertsGoogle, ::namespacePreservation and ::handlesInvalidAttributeNames: each 1 failing test with
java.lang.IllegalStateException: PROBE-REACHED at org.jsoup.helper.W3CDom.fromJsoup(W3CDom.java:39). fromJsoup has no production
caller; the facade is reached by existing tests directly.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of batch9_tasks.json, in that order; none substituted):
  hop 1 nodes.Element             1237 lines  w3cDocumentFor      the namespace-aware document builder and the new W3C document;
                                                                  ParserConfigurationException -> IllegalStateException
  hop 2 helper.HttpConnection     1024 lines  fillW3cDocument     document URI from the location; the W3CBuilder visitor
  hop 3 select.Evaluator(.IsRoot)  728 lines  walkFromRoot        placement: the document's root element, doc.child(0)
  hop 4 parser.HtmlTreeBuilder     702 lines  visitTree           pass-through
  hop 5 nodes.Node                 694 lines  walkDepthFirst      GOLD: the non-recursive depth-first walk (a stack of pending
                                                                  nodes and the list of open ancestors) that calls the visitor's
                                                                  head and tail for the root and every descendant
Host newline counts 1237, 1024, 728, 702, 694; the smallest host is Node (694 lines), which is also the gold host.
The correct configuration is the original fromJsoup: the gold pops the next node from the pending stack, first closes (tail) every
open node that is not the new node's parent, then opens it (head) and pushes its children, reversed so that the first child is on
top of the stack; after the stack is empty it closes the remaining open nodes. This calls head and tail in exactly the order of
NodeTraversor.traverse (document order), so W3CBuilder builds the same W3C tree.

Fault (one-line omission in the walk's iteration): the step that reverses the children before they are pushed is dropped, so every
node's children come off the stack last-first. Head and tail still pair up (a node is closed exactly when the walk leaves it), the
walk is still depth first and still reaches every node, but each element's children are visited in reverse document order, and
W3CBuilder, which appends each new node to the current element, writes every child list reversed. Trigger: the EXISTING test
W3CDomTest::namespacePreservation: the root element is still the html element in the XHTML namespace (lines 72-74 hold), but
htmlEl.getChildNodes().item(2) is now the head element and its fourth child the xhtml title, so the assertion at line 77 fails with
org.junit.ComparisonFailure (expected the epub namespace http://www.idpf.org/2007/ops, got http://www.w3.org/1999/xhtml).
convertsGoogle (root element name, null namespace, "ipod" in the output) and handlesInvalidAttributeNames (no exception) still pass;
no other test reaches the chain.

The gold's javadoc states the idiomatic contract in NodeTraversor's own words (a depth-first traverse of the root and all of its
descendants, without recursion) and is silent on the order in which the children are taken. The convention (a depth-first walk
visits each node's children in document order, as NodeTraversor does) is pinned outside the gold: NodeVisitor (head "can be used to
create a start tag for a node, and tail to create the end tag"), NodeTraversor::traverse (childNode(0), then nextSibling), and the
production walks over it, Node::outerHtml and Element::text, with ElementTest::testOuterHtml and ElementTest::testGetText passing
(sibling order "<img ...><p>...Hello</p><p>there</p>" and "Hello Another element"); W3CDom::convert walks the same visitor with
NodeTraversor.

Single owner: only the gold calls the visitor and takes the children; hops 1-4 make the document, set its URI, create the visitor,
pick the root element and pass it along. No one-line change above the gold can restore the order: the visitor is W3CBuilder (a hop
cannot wrap it without a new type), the root element must be the document's first element (the Document itself has the tag name
"#root", which createElementNS rejects), and walking the root's children one by one leaves the root's head out (dest is null).
Declared alternatives (G9): hop 3 walks from the Document node; hop 4 walks each child of the root on its own; hop 1 uses a builder
that is not namespace-aware. Each leaves the trigger failing.
Recorded bypasses (edits that throw the gold's walk away, not repairs of the chain):
 B-1 hop 3 or hop 4 calls root.traverse(visitor) or new NodeTraversor(visitor).traverse(root) instead of the next hop;
 B-2 hop 2 calls new W3CDom().convert(in, out) (or the facade calls convert(in, out), its original body, B-0).
Considered outside the chain: W3CBuilder.head appends every new node (element, text, comment, data) with dest.appendChild; making
it prepend instead would take four edits (one per node kind; one edit alone leaves text and elements out of order) and would
break the documented public W3CDom.convert, which walks W3CBuilder with NodeTraversor in document order. It is not a one-line repair
consistent with the documentation.

Lie: the facade's javadoc claims the jsoup document is first written out as XHTML text and that text is then parsed by the
namespace-aware document builder; the chain neither serialises nor parses anything (it builds a new empty document and walks the
jsoup nodes). It names neither the walk, the visitor, the order of the children, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (pending stack seeded with root; per popped node: close open nodes until the top of open is the node's parent, head,
 push onto open, copy the children, reverse the copy, push it onto pending; finally close the rest of open):
  T1 absent: root seeds the pending stack (and so every node of the walk); visitor receives every head and tail call.
  T2 absent: pending, open, node, children and both done locals are each read by a call (remove/get/add/addAll, head, tail) that
     reaches the visitor; no local is initialised to a literal; every loop moves its own collection (pending.remove, open.remove);
     both loop conditions decide whether live statements run.
  T3 absent: both NodeVisitor callbacks (head, tail) are called, each once per node; no enum, type code or named format member is
     left out; no class of nodes is named.
  T4 absent: "a depth-first traverse of the root and all of its descendants" is a general description the loop addresses;
     "without recursion" is met (no self-call); the @param clauses name no rule.
 Variant gold (the same text without the line that reverses the copied children):
  T1 absent: root is read when the pending stack is seeded; visitor is called with head for every node and with tail in both
     closing loops; the gold has no argument check.
  T2 absent: pending is added to, popped and tested; open is added to, read, popped and its size passed as the depth; node is
     assigned per iteration and read by the closing test, head, open.add and childNodes(); children is read by pending.addAll; each
     done is passed to tail; no local is initialised to a literal; each loop removes from the collection its condition tests; no
     branch, case or ternary is dead.
  T3 absent: the two callbacks of NodeVisitor are both called, once for each node (head when the node is opened, tail when it is
     closed); no closed set has a member left untreated; the gold's text names no class of nodes ("leaf", "childless", "element")
     that it would treat in part; no enum or type code.
  T4 absent: the javadoc ("Start a depth-first traverse of the root and all of its descendants, without recursion.", "@param root
     the root node point to traverse.", "@param visitor the visitor to call for the nodes of the walk.") names no concrete rule,
     limit or order; the walk does reach the root and all descendants, depth first, without recursion; no inline comment; the
     identifiers pending, open, node, children and done name what they hold."""

W3C = "src/main/java/org/jsoup/helper/W3CDom.java"
ELT = "src/main/java/org/jsoup/nodes/Element.java"
HTTP = "src/main/java/org/jsoup/helper/HttpConnection.java"
EVAL = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
NODE = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = '''/**
 * Start a depth-first traverse of the root and all of its descendants, without recursion.
 * @param root the root node point to traverse.
 * @param visitor the visitor to call for the nodes of the walk.
 */
public static void walkDepthFirst(Node root, NodeVisitor visitor) {
    List<Node> pending = new ArrayList<Node>();
    List<Node> open = new ArrayList<Node>();
    pending.add(root);
    while (!pending.isEmpty()) {
        Node node = pending.remove(pending.size() - 1);
        while (!open.isEmpty() && open.get(open.size() - 1) != node.parentNode()) {
            Node done = open.remove(open.size() - 1);
            visitor.tail(done, open.size());
        }
        visitor.head(node, open.size());
        open.add(node);
        List<Node> children = new ArrayList<Node>(node.childNodes());
        Collections.reverse(children);
        pending.addAll(children);
    }
    while (!open.isEmpty()) {
        Node done = open.remove(open.size() - 1);
        visitor.tail(done, open.size());
    }
}'''

HOP1 = '''/**
 * Convert a jsoup Document to a new W3C Document, made by a namespace-aware builder of the given factory.
 * @param factory the factory to make the document builder with
 * @param in jsoup doc
 * @return w3c doc
 */
public static org.w3c.dom.Document w3cDocumentFor(DocumentBuilderFactory factory, Document in) {
    try {
        factory.setNamespaceAware(true);
        org.w3c.dom.Document out = factory.newDocumentBuilder().newDocument();
        HttpConnection.fillW3cDocument(in, out);
        return out;
    } catch (ParserConfigurationException e) {
        throw new IllegalStateException(e);
    }
}'''

HOP2 = '''/**
 * Converts a jsoup document into the provided W3C Document. The location of the jsoup document, if it has one, becomes the
 * document URI.
 * @param in jsoup doc
 * @param out w3c doc
 */
public static void fillW3cDocument(Document in, org.w3c.dom.Document out) {
    if (!StringUtil.isBlank(in.location()))
        out.setDocumentURI(in.location());
    Evaluator.IsRoot.walkFromRoot(in, new W3CDom.W3CBuilder(out));
}'''

HOP3 = '''/**
 * Walks the root element of the document (the first child of the #root node) with the visitor.
 * @param doc the document
 * @param visitor the visitor to call for the nodes of the walk
 */
public static void walkFromRoot(Document doc, NodeVisitor visitor) {
    HtmlTreeBuilder.visitTree(doc.child(0), visitor);
}'''

HOP4 = '''/**
 * Walks the element and all of its descendants depth first with the visitor.
 * @param root the element to start at
 * @param visitor the visitor to call for the nodes of the walk
 */
public static void visitTree(Element root, NodeVisitor visitor) {
    Node.walkDepthFirst(root, visitor);
}'''

DESIGN = {
 "instance": "Jsoup-54", "project": "Jsoup", "bug_id": 54, "seed": 4003,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": W3C, "class": "org.jsoup.helper.W3CDom", "method": "fromJsoup", "near_line": 38},
 "facade_variant": "V1",
 "state_passed": "protected field factory (DocumentBuilderFactory) and the parameter in to hop 1; no write-back; the facade returns "
                 "hop 1's W3C Document (the protected nested W3CBuilder visitor is created in the same-package hop 2 and handed "
                 "down as the public NodeVisitor interface)",
 "reachability_probe": "W3CDomTest::convertsGoogle, ::namespacePreservation and ::handlesInvalidAttributeNames each fail with "
                       "java.lang.IllegalStateException: PROBE-REACHED at org.jsoup.helper.W3CDom.fromJsoup(W3CDom.java:39) "
                       "(defects4j test -t, one test each, 1 failing test each)",
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/helper/W3CDomTest.java",
             "test_class": "org.jsoup.helper.W3CDomTest", "test_method": "namespacePreservation"},
 "expected_signature": "expected:<http://www.[idpf.org/2007/ops]> but was:<http://www.[w3.org/1999/xhtml]>",
 "gold": {"method": "walkDepthFirst", "text": GOLD_TEXT,
          "fault": {"old": "            List<Node> children = new ArrayList<Node>(node.childNodes());\n"
                           "            Collections.reverse(children);\n"
                           "            pending.addAll(children);\n",
                    "new": "            List<Node> children = new ArrayList<Node>(node.childNodes());\n"
                           "            pending.addAll(children);\n"}},
 "chain": {
   "facade_body": "Validate.notNull(in);\n"
                  "        return org.jsoup.nodes.Element.w3cDocumentFor(factory, in);",
   "lie": "The jsoup document is first written out as XHTML text, and that text is then parsed by the namespace-aware "
          "document builder.",
   "hops": [
     {"file": ELT, "class": "org.jsoup.nodes.Element", "method": "w3cDocumentFor",
      "imports": ["javax.xml.parsers.DocumentBuilderFactory", "javax.xml.parsers.ParserConfigurationException",
                  "org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HTTP, "class": "org.jsoup.helper.HttpConnection", "method": "fillW3cDocument",
      "imports": ["org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EVAL, "class": "org.jsoup.select.Evaluator.IsRoot", "method": "walkFromRoot",
      "imports": ["org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "visitTree",
      "imports": ["org.jsoup.select.NodeVisitor"], "text": HOP4},
     {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "walkDepthFirst", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.select.NodeTraversor::traverse",
              "org.jsoup.nodes.Node::outerHtml",
              "org.jsoup.nodes.Element::text",
              "org.jsoup.helper.W3CDom::convert"],
 "ownership_reason": "Only the gold calls the visitor and takes each node's children: hop 1 makes the namespace-aware builder and "
                     "the new W3C document, hop 2 sets the document URI and creates the W3CBuilder visitor, hop 3 picks the "
                     "document's root element and hop 4 passes it on. The gold's javadoc promises a depth-first traverse of the "
                     "root and all of its descendants for a NodeVisitor, whose head and tail are documented as the start tag and "
                     "the end tag of a node, i.e. a walk in document order; the variant pushes each node's children onto its "
                     "stack without reversing them, so they come off last-first and W3CBuilder writes every child list in "
                     "reverse. No one-line change above the gold restores the order: a hop cannot wrap the visitor without a new "
                     "type, the walk must start at the document's first element (the Document node's tag name '#root' is "
                     "rejected by createElementNS), and walking the root's children one by one leaves out the root's head. The "
                     "convention is pinned outside the gold: NodeTraversor.traverse takes childNode(0) and then nextSibling(), "
                     "and the production walks over it, Node.outerHtml and Element.text, depend on that order; "
                     "ElementTest::testOuterHtml expects '<div title=...><img src=\"foo.png\"><p><!-- comment -->Hello</p><p>there</p></div>' "
                     "and ElementTest::testGetText 'Hello Another element'; W3CDom.convert walks the same visitor with "
                     "NodeTraversor.",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::testOuterHtml",
                     "org.jsoup.nodes.ElementTest::testGetText"],
 "compensating": {
   "chain": [
     {"file": EVAL, "old": "HtmlTreeBuilder.visitTree(doc.child(0), visitor);",
      "new": "HtmlTreeBuilder.visitTree(doc, visitor);",
      "why": "hop 3 walks from the document node itself instead of its first element"},
     {"file": HTB, "old": "Node.walkDepthFirst(root, visitor);",
      "new": "for (Node child : root.childNodes()) Node.walkDepthFirst(child, visitor);",
      "why": "hop 4 walks each child of the root element on its own"},
     {"file": ELT, "old": "factory.setNamespaceAware(true);",
      "new": "factory.setNamespaceAware(false);",
      "why": "hop 1 builds the document with a builder that is not namespace-aware"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted: nodes.Element (hop 1, 1237 lines), helper.HttpConnection (hop 2, 1024), select.Evaluator (hop 3, 728), "
               "parser.HtmlTreeBuilder (hop 4, 702), nodes.Node (hop 5, gold, 694; the smallest host). All five are public classes "
               "in which a static method compiles (Evaluator and Node are abstract, which does not affect a static method). "
               "Anchors from stageB_lib.pick_anchor / host_search.pick_insertion_anchor with seed 4003 + 100 + i (as mr3_spec.py "
               "inserts them): hop 1 after `getElementsMatchingOwnText` (line idx 870, seed 4103), hop 2 after `proxy` (89, 4104), "
               "hop 3 after `matches` (577, 4105), hop 4 after `inScope` (465, 4106), hop 5 after `replaceWith` (399, 4107). The "
               "hop-3 anchor is the matches method of the static nested class Evaluator.IsRoot (its members are indented with "
               "four spaces and a tab, which the picker's four-space test counts as outer), so hop 3 is a public static member of "
               "Evaluator.IsRoot and hop 2 calls it as Evaluator.IsRoot.walkFromRoot; Evaluator.java remains the drawn host. "
               "The other four anchors are in the outer class. The facade calls hop 1 by its fully-qualified name (W3CDom "
               "imports org.w3c.dom.Element); each hop imports the next host where needed (HtmlTreeBuilder's org.jsoup.nodes.* "
               "already covers Node). The facade's file W3CDom.java is excluded as a host.",
}
