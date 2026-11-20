"""Main run Jsoup-73__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout
of Defects4J Jsoup-73; the real bug modified org.jsoup.helper.W3CDom, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE
section 1: pool v2 found no tested static target in W3CDom).

Facade: W3CDom.fromJsoup(org.jsoup.nodes.Document) (the only allowed candidate of the task record; facade_planned_by = Jsoup-54__i,
so this is a recorded facade reuse of Jsoup-54__i: no planned-distinct candidate exists for this bug; none of that instance's files
were opened). Original computation of the facade: Validate.notNull(in); the namespace-aware DocumentBuilder from the protected field
factory; a new empty W3C Document out; convert(in, out), which (1) sets out's document URI to in.location() when the location is not
blank and (2) walks in.child(0) -- the document's first element child, "skip the #root node" -- with a new W3CBuilder(out), the
protected static nested NodeVisitor that builds the W3C tree; ParserConfigurationException is rethrown as IllegalStateException.

facade_variant: V1+V5 (no V2 receiver is passed). The public method convert (the record's V2 reason) is the whole of the facade's
per-node computation, so a chain that only called w3c.convert(in, out) would leave the gold no decision or iteration of its own;
instead the chain carries convert's two steps itself and convert stays unchanged in W3CDom as the external pin of the same steps.
V1: the facade reads the protected field factory (inside W3CDom, no visibility change) and keeps the original builder lines
(namespace-aware DocumentBuilder, new Document out, the ParserConfigurationException rethrow) because the visitor needs out. V5: the
visitor is a W3CBuilder, a protected nested type that classes in other packages cannot name, so the facade creates new W3CBuilder(out)
and the hops carry it typed as the public interface it implements, org.jsoup.select.NodeVisitor (no generic needed, no hop names
W3CBuilder). The facade keeps the guard, the builder lines and the visitor creation (said here) and makes one call to hop 1; it
returns out. No widening of visibility, no new class/interface/nested type, no reflection, no signature/modifier/override/throws
change, no test edit.
state_passed: the jsoup Document parameter in, the new W3C Document out (built in the facade from the protected field factory) and
the visitor new W3CBuilder(out) typed as NodeVisitor, to hop 1; no field write-back (the facade returns out, as the original did).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-73-probe/w of the fixture,
the first statement of fromJsoup was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`;
`defects4j test -t org.jsoup.helper.W3CDomTest::namespacePreservation`, `::convertsGoogleLocation` and `::simpleConversion` each gave
1 failing test with java.lang.IllegalStateException: PROBE-REACHED, thrown in W3CDom.fromJsoup and called from W3CDomTest (the other
callers of fromJsoup are W3CDomTest::convertsGoogle and ::handlesInvalidAttributeNames; UrlConnectTest, the only other test caller,
is @Ignore'd). Reached directly by existing tests.

Hosts (host_mode = "largest5": no other public class of >= 1500 lines; hosts_hop_order of batch9_tasks.json, used exactly, in that
order, none substituted; the facade's file W3CDom.java is excluded):
  hop 1 nodes.Element          1435 lines  copyToW3CDocument  the document-URI decision (convert's step 1), then pass-through
  hop 2 helper.HttpConnection  1249 lines  convertDocument    pass-through
  hop 3 select.Evaluator        778 lines  visitDocument      pass-through (the seeded anchor lies in Evaluator's public static
                                                              nested class IsRoot, so the hop is Evaluator.IsRoot.visitDocument)
  hop 4 parser.HtmlTreeBuilder  734 lines  traverseDocument   pass-through
  hop 5 nodes.Node              725 lines  walkDocument       GOLD: chooses the node of the jsoup document the walk starts from
                                                              and walks it, depth-first, into the visitor (convert's step 2)
Host newline counts 1435, 1249, 778, 734, 725; the smallest host is Node (725 lines), which is also the gold host.

Correct gold: the walk starts at the first top-level node of the document that is neither a doctype nor a comment, and only that
node (with its subtree) is handed to the visitor. The HTML tree builder places only doctypes and comments before the html element
(a leading <?xml ...?> line becomes a Comment), so for every Document the HTML parser builds -- every existing caller and test -- the
start node is exactly in.child(0) and the correct configuration produces the original W3C document. (For an XML-parsed document whose
prolog holds an XML declaration or whitespace text before the root, the correct gold would start at that node instead of the root;
for a document with no such node it walks nothing where the original throws IndexOutOfBoundsException. No existing test or production
caller converts either kind.)

Fault (one-line omission of a special-case skip in the gold's selection loop): the comment skip
`if (child instanceof Comment) continue;` is dropped, so the walk starts at the first top-level node that is not a doctype. The gold
then reads as an ordinary routine: skip a leading doctype, take the first other top-level node, walk it. Trigger: the EXISTING test
W3CDomTest::namespacePreservation: namespaces.xhtml starts with <?xml version="1.0" ...?>, which the HTML parser keeps as a Comment
before <html> (verified: top-level nodes Comment, Element html), so the walk starts at that comment and walks nothing else; the
comment reaches W3CBuilder.head before any element has set up the W3C root, and fromJsoup throws java.lang.NullPointerException (at
W3CDom$W3CBuilder.head). It is the only test that newly fails: simpleConversion, handlesInvalidAttributeNames and convertsGoogleLocation
convert documents whose only top-level node is <html> or that begin with a doctype; convertsGoogle parses google-ipod.html, whose
top-level nodes are DocumentType, Element html (verified), so the remaining doctype skip still starts it at html; the new hops have no
other caller.

The gold's javadoc states the idiomatic contract (walk a jsoup document, depth-first, into a visitor that builds a W3C DOM document
from it) and is silent on which node the walk starts from; on the trigger input no W3C document of the jsoup document is built (the
walk covers one comment and none of the document's elements). The convention is pinned outside the gold: W3CDom.convert, the public
sibling of the facade performing the same two steps, starts at in.child(0) ("skip the #root node"); Evaluator.IsRoot.matches takes
root.child(0) of a Document as the document's root; Element.child / Element.children ("effectively a filter on childNodes() to get
Element nodes") define child(0) as the first ELEMENT child. Passing tests on the variant: W3CDomTest::convertsGoogle (the W3C
document of a document that begins with a doctype starts at its html element), CssTest::root (:root is the html element),
ElementTest::testChildrenElements and ::testChildThrowsIndexOutOfBoundsOnMissing.

Single owner: only the gold decides where the walk starts; hop 1 only sets the document URI and hops 2-4 hand the document and the
visitor along unchanged. Because the walk covers only the node the gold chooses, nothing below the gold can recover the document's
elements: the visitor is handed the comment alone. Declared alternatives (G9), each leaving the trigger failing:
 W3CBuilder.head skips a comment that arrives before the root (`&& dest != null`): no exception, but the W3C document stays empty and
   the test's first assertion reads a null item(0);
 W3CBuilder.head appends such a comment to the W3C document itself: the W3C document holds only that comment, whose namespace is not
   the XHTML namespace the test reads from item(0);
 hop 3 normalises the jsoup document before passing it on (normalise keeps the top-level comment);
 hop 2 passes on a clone of the document (the clone keeps the comment).
A hop cannot hand the gold the root element instead (the gold takes a Document; Element is not a Document), and no hop outside
org.jsoup.helper can create another builder of the same W3C document.
Recorded bypasses (edits that replace or discard the gold's choice, not repairs of the chain):
 B-0 the facade's original body (convert(in, out)) re-implements both steps and makes the chain, including the gold, dead.
 B-1 any hop replacing its call to the next hop by NodeTraversor.traverse(visitor, doc.child(0)) discards the gold.
 B-2 a hop that removes a leading comment from the caller's jsoup document before passing it on changes the input document, which
     hop 1's javadoc states is left unchanged (and fromJsoup never changed its input).
 B-3 a W3CBuilder.head that, handed a comment before any root exists, starts its own traversal of the comment's next sibling would
     walk a node the gold did not hand it: it overrides the gold's choice of start node rather than building from what it is given.

Lie: the facade's javadoc claims the jsoup document is first written out as XML text which the factory's parser then reads back into
the W3C document; the code serialises and parses nothing (it walks the jsoup tree into a fresh, empty W3C document). It names neither
comments, doctypes, the start node, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; signature walkDocument(Document document, NodeVisitor visitor); Node start = null; for each child of
 document.childNodes(): if DocumentType continue; if Comment continue; if (start == null) start = child; then
 NodeTraversor.traverse(visitor, start)):
  T1 absent: document supplies the nodes the loop reads; visitor is handed to traverse; no argument check.
  T2 absent: start is initialised to null and assigned in the loop (not frozen), and it is the traverse argument (not dead); child
     is read by both type tests and the assignment; both skips can change start, and the start == null test keeps the first
     candidate; no other local.
  T3 absent: two node kinds (DocumentType, Comment) are skipped; the kinds a document's child list can hold form no closed set under
     the closure rule (no enum or type code, no named format, the gold's text names no class of nodes), and no member that the gold's
     text reads or names goes untreated.
  T4 absent: 'Walk a jsoup document, depth-first, into a visitor that builds a W3C DOM document from it' is a general description that
     the traverse call addresses; the @param clauses name no rule, limit or case; no inline comment; identifiers (start, child) name
     what they hold.
 Variant gold (javadoc unchanged; the loop keeps only `if (child instanceof DocumentType) continue;` and the start == null
 assignment):
  T1 absent: document supplies the nodes the loop reads; visitor is handed to traverse; both decide the visitor's side effects.
  T2 absent: start is assigned in the loop and passed to traverse; child is read by the type test and the assignment; the doctype
     skip changes start for a doctype-led document and start == null keeps the first non-doctype node (without it start would be the
     last); no branch with no effect, no literal local that is never reassigned, no cursor, counter or flag the loop fails to move.
  T3 absent: exactly one node kind (DocumentType) is singled out among the kinds a document's child list holds (Element, Comment,
     TextNode, XmlDeclaration, ...), an unnamed set of three or more ('One member of a larger unnamed set'); no enum, type code, pair
     half or range end; the gold's text names no class of nodes ("element", "comment", "root", "prolog", "top-level") that it would
     handle only in part; no member is read without its sibling's treatment.
  T4 absent: 'depth-first' is met by NodeTraversor.traverse; 'into a visitor that builds a W3C DOM document from it' is a general
     description that the traverse call addresses (like 'joins the elements'); '@param document the jsoup document to walk' and
     '@param visitor the visitor that builds the W3C DOM document' name no concrete rule, limit or case; no inline comment; the
     identifier start names where the walk starts, which the body produces."""

W3C = "src/main/java/org/jsoup/helper/W3CDom.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = '''/**
 * Walk a jsoup document, depth-first, into a visitor that builds a W3C DOM document from it.
 * @param document the jsoup document to walk
 * @param visitor the visitor that builds the W3C DOM document
 */
public static void walkDocument(Document document, NodeVisitor visitor) {
    Node start = null;
    for (Node child : document.childNodes()) {
        if (child instanceof DocumentType) continue;
        if (child instanceof Comment) continue;
        if (start == null)
            start = child;
    }
    NodeTraversor.traverse(visitor, start);
}'''

HOP1 = '''/**
 * Copy a jsoup document into a W3C DOM document, through a visitor that builds the W3C DOM tree. If the jsoup document
 * has a location, it is set as the W3C document's URI. The jsoup document is left unchanged.
 * @param document the jsoup document to copy
 * @param out the W3C DOM document to copy into
 * @param visitor the visitor that builds the W3C DOM tree in {@code out}
 */
public static void copyToW3CDocument(Document document, org.w3c.dom.Document out, NodeVisitor visitor) {
    if (!StringUtil.isBlank(document.location()))
        out.setDocumentURI(document.location());
    HttpConnection.convertDocument(document, visitor);
}'''

HOP2 = '''/**
 * Convert a jsoup document to a W3C DOM document, through a visitor that builds the W3C DOM document.
 * @param doc the jsoup document to convert
 * @param visitor the visitor that builds the W3C DOM document
 */
public static void convertDocument(Document doc, NodeVisitor visitor) {
    Evaluator.IsRoot.visitDocument(doc, visitor);
}'''

HOP3 = '''/**
 * Visit a jsoup document with a visitor that builds a W3C DOM document from it.
 * @param doc the jsoup document to visit
 * @param visitor the visitor that builds the W3C DOM document
 */
public static void visitDocument(Document doc, NodeVisitor visitor) {
    HtmlTreeBuilder.traverseDocument(doc, visitor);
}'''

HOP4 = '''/**
 * Traverse a jsoup document with a visitor that builds a W3C DOM document from it.
 * @param doc the jsoup document to traverse
 * @param visitor the visitor that builds the W3C DOM document
 */
public static void traverseDocument(Document doc, NodeVisitor visitor) {
    Node.walkDocument(doc, visitor);
}'''

DESIGN = {
 "instance": "Jsoup-73", "project": "Jsoup", "bug_id": 73, "seed": 3379,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": W3C, "class": "org.jsoup.helper.W3CDom", "method": "fromJsoup", "near_line": 36},
 "facade_variant": "V1+V5",
 "state_passed": "the jsoup Document parameter in, the new W3C Document out (built in the facade from the protected field "
                 "factory, original builder lines kept) and the visitor new W3CBuilder(out) typed as the public interface "
                 "NodeVisitor, to hop 1; no field write-back (the facade returns out)",
 "reachability_probe": "probe throw as first statement of fromJsoup: W3CDomTest::namespacePreservation, ::convertsGoogleLocation, "
                       "::simpleConversion each fail (1 failing test each) with java.lang.IllegalStateException: PROBE-REACHED "
                       "thrown in W3CDom.fromJsoup, called from W3CDomTest",
 "host_mode": "largest5",
 "host_lines": [1435, 1249, 778, 734, 725],
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/helper/W3CDomTest.java",
             "test_class": "org.jsoup.helper.W3CDomTest", "test_method": "namespacePreservation"},
 "expected_signature": "java.lang.NullPointerException",
 "gold": {"method": "walkDocument", "text": GOLD_TEXT,
          "fault": {"old": "            if (child instanceof DocumentType) continue;\n"
                           "            if (child instanceof Comment) continue;\n",
                    "new": "            if (child instanceof DocumentType) continue;\n"}},
 "chain": {
   "facade_body": "Validate.notNull(in);\n"
                  "        DocumentBuilder builder;\n"
                  "        try {\n"
                  "        \t//set the factory to be namespace-aware\n"
                  "        \tfactory.setNamespaceAware(true);\n"
                  "            builder = factory.newDocumentBuilder();\n"
                  "            Document out = builder.newDocument();\n"
                  "            org.jsoup.nodes.Element.copyToW3CDocument(in, out, new W3CBuilder(out));\n"
                  "            return out;\n"
                  "        } catch (ParserConfigurationException e) {\n"
                  "            throw new IllegalStateException(e);\n"
                  "        }",
   "lie": "The jsoup document is first written out as XML text, which the factory's parser then reads back into the W3C "
          "document.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "copyToW3CDocument",
      "imports": ["org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "convertDocument",
      "imports": ["org.jsoup.select.Evaluator", "org.jsoup.select.NodeVisitor"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsRoot", "method": "visitDocument",
      "imports": ["org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "traverseDocument",
      "imports": ["org.jsoup.select.NodeVisitor"], "text": HOP4},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "walkDocument", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.helper.W3CDom::convert",
              "org.jsoup.select.Evaluator.IsRoot::matches",
              "org.jsoup.nodes.Element::child",
              "org.jsoup.nodes.Element::children"],
 "ownership_reason": "Only the gold decides which node of the jsoup document the walk into the W3C builder starts from, and "
                     "only that node is walked; hop 1 only sets the document URI from the location, and hops 2-4 pass the "
                     "document and the visitor along unchanged. The gold's javadoc promises a walk of the jsoup document into a "
                     "visitor that builds a W3C DOM document from it, and on namespaces.xhtml (a leading Comment from its "
                     "<?xml ...?> line, then <html>) the walk covers that comment alone: no element of the document reaches the "
                     "builder and no W3C document of it is built. Nothing below the gold can recover the elements: a builder "
                     "that skips the early comment leaves the W3C document empty, and one that appends it to the W3C document "
                     "leaves only the comment there. Nothing above the gold restores the start: the gold takes a jsoup Document, "
                     "so a hop cannot hand it the root element (Element is not a Document), the visitor is a W3CBuilder that no "
                     "hop outside org.jsoup.helper can create, and normalising or cloning the document keeps the leading "
                     "comment. The convention is pinned outside the gold: W3CDom.convert, the public sibling performing the "
                     "same two steps, starts at in.child(0) ('skip the #root node'); Evaluator.IsRoot.matches takes child(0) of "
                     "a Document as its root; Element.child and Element.children ('effectively a filter on childNodes() to get "
                     "Element nodes') define child(0) as the first element child. Passing tests: W3CDomTest convertsGoogle "
                     "(the W3C document of a document that begins with a doctype starts at its html element), CssTest root "
                     "(:root is the html element), ElementTest testChildrenElements and testChildThrowsIndexOutOfBoundsOnMissing.",
 "ownership_tests": ["org.jsoup.helper.W3CDomTest::convertsGoogle",
                     "org.jsoup.select.CssTest::root",
                     "org.jsoup.nodes.ElementTest::testChildrenElements",
                     "org.jsoup.nodes.ElementTest::testChildThrowsIndexOutOfBoundsOnMissing"],
 "compensating": {
   "chain": [
     {"file": W3C, "old": "            } else if (source instanceof org.jsoup.nodes.Comment) {",
      "new": "            } else if (source instanceof org.jsoup.nodes.Comment && dest != null) {",
      "why": "the W3C builder skips a comment that arrives before the root element is set up"},
     {"file": W3C, "old": "                dest.appendChild(comment);",
      "new": "                (dest == null ? doc : dest).appendChild(comment);",
      "why": "the W3C builder appends a comment that arrives before the root element to the W3C document itself"},
     {"file": EV, "old": "        HtmlTreeBuilder.traverseDocument(doc, visitor);",
      "new": "        HtmlTreeBuilder.traverseDocument(doc.normalise(), visitor);",
      "why": "hop 3 normalises the document's structure before the walk"},
     {"file": HC, "old": "        Evaluator.IsRoot.visitDocument(doc, visitor);",
      "new": "        Evaluator.IsRoot.visitDocument(doc.clone(), visitor);",
      "why": "hop 2 hands down a copy of the document"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 0). Hosts are exactly hosts_hop_order of the task record (batch9_tasks.json), "
               "in that order, none substituted: nodes.Element (hop 1, 1435 lines), helper.HttpConnection (hop 2, 1249), "
               "select.Evaluator (hop 3, 778), parser.HtmlTreeBuilder (hop 4, 734), nodes.Node (hop 5, gold, 725; the smallest "
               "host). All five are public top-level classes in which a public static method compiles (Evaluator and Node are "
               "abstract, HttpConnection implements Connection, HtmlTreeBuilder extends the package-private TreeBuilder; none "
               "affects a static method). Anchors from stageB_lib.pick_insertion_anchor with seed 3379 + 100 + i, as "
               "mr3_spec.py inserts them: hop 1 after `insertChildren` (seed 3479), hop 2 after `get` (3480), hop 3 after "
               "`toString` (3481) inside the public static nested class Evaluator.IsRoot, so hop 3 is "
               "Evaluator.IsRoot.visitDocument and hop 2 calls it by that name, hop 4 after `replaceInQueue` (3482), hop 5 after "
               "`outerHtml` (3483); hops 1, 2, 4 and 5 are in the outer class. The facade calls hop 1 by its fully-qualified "
               "name; each hop imports the next host where needed; the gold's Comment and DocumentType are in its own package "
               "org.jsoup.nodes. The facade's class W3CDom is not a host.",
}
