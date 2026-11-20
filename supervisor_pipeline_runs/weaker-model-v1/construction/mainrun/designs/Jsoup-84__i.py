"""Main run Jsoup-84__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Jsoup-84; the real bug modified org.jsoup.helper.W3CDom, the facade's class). No static pair (B8 note section 1: pool v2
found no tested static facade in W3CDom).

Facade: W3CDom.fromJsoup(org.jsoup.nodes.Document) (the only allowed candidate of the task record, BATCH9_PREREGISTRATION.md row
359; facade_planned_by = Jsoup-54__i, so this is a planned facade reuse, recorded in facade_reuse_of; no other candidate exists, and
it carries the recipe). None of Jsoup-54__i's files was opened.
Original computation: Validate.notNull(in); the protected field factory is made namespace-aware and creates a DocumentBuilder; a new
W3C document is created; convert(in, out) sets the document URI from in.location() when it is not blank and walks in.child(0) (the
first element of the document, skipping the #root node) with the nested visitor W3CBuilder: every node pushes a copy of the
namespace map in scope (prefix -> URI) and pops it on leaving; an element adds its xmlns / xmlns:<prefix> declarations to its map,
takes the prefix before the first colon of its tag name (or the empty prefix), looks the namespace up, and is created with
createElementNS(namespace, tagName), except that an element whose prefix is not bound (namespace null, tag name with a colon) is
created with the empty namespace; its attributes are copied when the key, stripped to [-a-zA-Z0-9_:.], is a valid XML name; it is
appended to the current W3C parent (the document for the root) and becomes the parent of its children; text becomes a text node
(getWholeText), data a text node (getWholeData), a comment a comment, other nodes nothing. A ParserConfigurationException becomes
an IllegalStateException.

facade_variant: V1 (state as parameters). state_passed: the protected field factory (DocumentBuilderFactory) and the parameter in,
handed to hop 1; no field is written, no write-back. The facade body is the original guard (Validate.notNull(in)) plus one call to
hop 1. The pool's planned variant was V2 (the receiver, for its public method convert); calling convert from a hop would leave the
whole computation in the receiver and nothing for the chain, so the chain carries the conversion itself and needs no method of the
receiver: V1 is the smallest variant that carries the computation. No private method of W3CDom is called by the facade's computation
(no V4); the chain neither calls nor copies the nested visitor's private helpers: it is a recursive walk with one scope map per
element (no stack, no visitor), built on the public jsoup node API and the public W3C DOM API; the namespace scoping is the XML
Namespaces rule for xmlns / xmlns:prefix attributes, and the attribute-name test is written fresh (the first character of the
stripped key is not '-', '.' or a digit). No package-private type is involved (no V3/V5; W3CBuilder is not used by the chain). No
visibility is widened, no type is added, no signature, modifier, override or throws change, no reflection, no test edit. convert(in,
out) and W3CBuilder stay intact (they are the sibling pin below).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-84-probe of the fixture, the
first statement of fromJsoup was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.jsoup.helper.W3CDomTest::treatsUndeclaredNamespaceAsLocalName`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at org.jsoup.helper.W3CDom.fromJsoup(W3CDom.java:37), called from
W3CDomTest.treatsUndeclaredNamespaceAsLocalName(W3CDomTest.java:144). The facade is reached directly by the trigger (all six
W3CDomTest methods call fromJsoup).

Hosts (host_mode = "largest5"; hosts_hop_order of batch9_tasks.json, used exactly in that order, none substituted; W3CDom.java, the
only candidate's file, is excluded):
  hop 1 nodes.Element             1458 lines  toW3cDocument     plumbing: namespace-aware builder from the factory, new W3C document,
                                                                document URI from the location, the walk from the first element;
                                                                ParserConfigurationException -> IllegalStateException
  hop 2 helper.HttpConnection     1186 lines  appendW3cNode     placement: the recursive walk; an element gets a copy of the inherited
                                                                scope and its children follow it; text, data and comments are
                                                                appended as W3C text and comment nodes
  hop 3 select.Evaluator           778 lines  w3cElementOf      (in the nested class Evaluator.IsNthChild, see host_notes) aggregation: the element from hop 4 plus its attributes with valid
                                                                XML names
  hop 4 parser.HtmlTreeBuilder     733 lines  createW3cElement  pass-through
  hop 5 nodes.Node                 725 lines  newW3cElement     GOLD: per element, the namespace declarations added to the scope, the
                                                                prefix of the tag name, the namespace lookup and the creation of the
                                                                W3C element under its qualified name
Host newline counts 1458, 1186, 778, 733, 725; the smallest host (and the gold host) is nodes.Node with 725 lines (C10F addendum
section 1: hosts under 1500 lines are expected in this regime). Anchors: see host_notes.
The correct configuration produces the same W3C document as the original for every input (the same nodes in the same order, the same
namespace scoping per element, the same attribute filter, the same URI rule); G1 checks the full suite.

Fault (one-line omission of a special-case step in the gold): the unbound-prefix rule is dropped from the creation call
(`return owner.createElementNS(namespace == null && colon > 0 ? "" : namespace, tagName);` becomes
`return owner.createElementNS(namespace, tagName);`), so an element whose tag name has a prefix that no xmlns:<prefix> attribute in
scope declares is created with a null namespace and a prefixed qualified name, which the W3C DOM rejects (DOMException NAMESPACE_ERR).
The gold then reads as the ordinary routine "look up the namespace of the prefix and create the element in it". Trigger: the
EXISTING test W3CDomTest::treatsUndeclaredNamespaceAsLocalName (`<fb:like>One</fb:like>`, no xmlns:fb anywhere): fromJsoup throws
org.w3c.dom.DOMException: NAMESPACE_ERR from the gold. It is the only test that converts an element with an undeclared prefix:
google-ipod.html (convertsGoogle, convertsGoogleLocation) has no prefixed tag and no xmlns; namespaces.xhtml (namespacePreservation)
declares every prefix it uses (epub, x); simpleConversion and handlesInvalidAttributeNames use no prefix. Gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the element is created "in the namespace bound to the prefix of its tag name", the
declarations are added to the scope first, the prefix rule, the qualified name) and is silent on a prefix that nothing binds. The
variant breaks the contract on the trigger input: it returns no element at all for <fb:like> (the DOM rejects the creation), while
the gold promises "the new W3C element" for the element. The convention is pinned outside the gold: the intact sibling
W3CDom.W3CBuilder.head (used in production by the public W3CDom.convert) does the same step (`namespace == null &&
tagName.contains(":") ? doc.createElementNS("", tagName) : doc.createElementNS(namespace, tagName)`, commented "doesn't have a real
namespace defined"); passing tests through the chain: namespacePreservation (declared default and prefixed namespaces, inheritance,
the per-element scope), convertsGoogle (an unprefixed undeclared name has no namespace), simpleConversion (structure, attributes,
text, data, comments), handlesInvalidAttributeNames (the attribute filter), convertsGoogleLocation (the URI).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: source supplies the attributes and the tag name; owner creates the element; scope receives the declarations and gives
     the namespace; none is only argument-checked.
  T2 absent: attribute and key are read by the declaration branches; tagName, colon and namespace reach the creation call; both
     branches of the if/else-if put different entries; both ternaries choose between different values; nothing is frozen.
  T3 absent: both declaration forms (xmlns and xmlns:prefix) are treated; prefixed and unprefixed tag names both get a prefix; the
     bound and unbound prefix both lead to a creation; no class named in the gold's text is handled in part.
  T4 absent: "the namespace bound to the prefix of its tag name", "xmlns and xmlns:prefix attributes, are first added to the scope",
     "the part before the first colon, or the empty prefix if it has none" and "keeps the tag name as its qualified name" are met by
     lines of the body; "without attributes or children" is met (none is added).
 Variant gold (javadoc, signature, the declaration loop, the prefix ternary, `return owner.createElementNS(namespace, tagName);`):
  T1 absent: source, owner and scope each change the result; none is only argument-checked.
  T2 absent: every local (attribute, key, tagName, colon, namespace) reaches a put or the creation call; the if/else-if branches put
     different entries; the prefix ternary chooses between two different prefixes; no local is frozen or dead.
  T3 absent: xmlns and xmlns:prefix are both treated; prefixed and unprefixed names are both handled; the gold has no bound/unbound
     treatment at all ('No member handled'); the gold's text names no class of prefixes it handles only in part.
  T4 absent: "in the namespace bound to the prefix of its tag name" is met by the lookup of the prefix in the scope (the phrase names
     no unbound case); the declaration, prefix and qualified-name phrases are met; "@return the new W3C element, without attributes
     or children" is a general description; no inline comment; identifiers (attribute, key, tagName, colon, namespace, scope, owner)
     name nothing the body does not meet.

Single owner: only the gold resolves a namespace: it adds the element's declarations to the scope, takes the prefix of the tag name
and decides the namespace passed to the W3C DOM; hop 1 creates the document, hop 2 walks and copies the inherited scope (it never
adds an entry), hop 3 copies attributes onto the element the gold made (setAttribute without a namespace), hop 4 passes through. The
callers pass the jsoup element itself, so no caller can change the tag name the gold reads, and the scope they pass is documented
as the namespace URIs declared by the element's ancestors. Once the gold has called createElementNS with a null namespace and a
prefixed name, the DOM has thrown inside the gold, so no caller can recover the element from its output. Declared alternatives
(G9): hop 1 creates the builder without namespace awareness; hop 2 hands the children the inherited scope instead of the element's;
hop 3 passes a fresh empty scope. None makes the trigger pass.
Recorded bypasses (each discards or re-implements the gold's decision; each breaks a hop's documented role):
 B-0 hop 1 replaces the walk with the intact sibling, `new org.jsoup.helper.W3CDom().convert(in, out);`, or the facade keeps its
     original body (convert), discarding the chain including the gold.
 B-1 hop 3 or hop 4 wraps its call to the next hop in a one-line try/catch of org.w3c.dom.DOMException that retries with
     `owner.createElementNS("", source.tagName())`: a second implementation of the gold's decision for the case the gold rejects,
     which throws away the gold's result (an exception) and breaks hop 4's documented pass-through role.
 B-2 hop 2 or hop 4 seeds the scope with an empty URI for the element's prefix when it is not declared (a one-line putIfAbsent over
     the tag name's prefix): it enters an undeclared prefix into a scope documented as the namespace URIs declared by the ancestors,
     and re-implements the gold's prefix rule.

Lie: the facade's javadoc claims the jsoup document is first written out as XML text, which a namespace-aware builder then parses into
the W3C document; no step of the chain serializes or parses anything (the W3C nodes are created one by one from the jsoup nodes). It
names neither prefixes nor namespaces of elements nor any hop."""

W3C = "src/main/java/org/jsoup/helper/W3CDom.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
NODE = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = '''/**
 * Creates the W3C element for an element, in the namespace bound to the
 * prefix of its tag name.
 *
 * <p>The namespace declarations of the element, its {@code xmlns} and
 * {@code xmlns:}<i>prefix</i> attributes, are first added to the scope. The
 * prefix of a tag name is its part before the first colon, or the empty
 * prefix if it has none; the new element keeps the tag name as its
 * qualified name.</p>
 *
 * @param source the element
 * @param owner the W3C document that creates the element
 * @param scope the namespace URIs declared by the element's ancestors, by
 *            prefix; the element's own declarations are added to it
 * @return the new W3C element, without attributes or children
 */
public static org.w3c.dom.Element newW3cElement(Element source, org.w3c.dom.Document owner, Map<String, String> scope) {
    for (Attribute attribute : source.attributes()) {
        String key = attribute.getKey();
        if (key.equals("xmlns"))
            scope.put("", attribute.getValue());
        else if (key.startsWith("xmlns:"))
            scope.put(key.substring("xmlns:".length()), attribute.getValue());
    }
    String tagName = source.tagName();
    int colon = tagName.indexOf(':');
    String namespace = scope.get(colon > 0 ? tagName.substring(0, colon) : "");
    return owner.createElementNS(namespace == null && colon > 0 ? "" : namespace, tagName);
}'''

HOP1 = '''/**
 * Converts a jsoup document to a new W3C document.
 *
 * <p>The W3C document is created by a namespace-aware builder of the given
 * factory, takes the location of the jsoup document as its URI if it has
 * one, and receives the W3C form of the first element of the document.</p>
 *
 * @param in the jsoup document
 * @param factory the factory of the document builder
 * @return the new W3C document
 */
public static org.w3c.dom.Document toW3cDocument(Document in, DocumentBuilderFactory factory) {
    try {
        factory.setNamespaceAware(true);
        org.w3c.dom.Document out = factory.newDocumentBuilder().newDocument();
        if (!StringUtil.isBlank(in.location()))
            out.setDocumentURI(in.location());
        HttpConnection.appendW3cNode(in.child(0), out, out, new HashMap<String, String>());
        return out;
    } catch (ParserConfigurationException e) {
        throw new IllegalStateException(e);
    }
}'''

HOP2 = '''/**
 * Appends the W3C form of a jsoup node, and of all its descendants, to a
 * W3C node.
 *
 * <p>An element is appended as a new W3C element, made with a copy of the
 * namespace scope it inherits, and its child nodes are then appended to it
 * in order, with that copy as their scope. Text is appended as a text node,
 * data as a text node of its whole data, and a comment as a comment; other
 * nodes are not appended.</p>
 *
 * @param source the jsoup node
 * @param owner the W3C document that creates the new nodes
 * @param parent the W3C node to append to
 * @param inherited the namespace URIs declared by the node's ancestors, by prefix
 */
public static void appendW3cNode(Node source, org.w3c.dom.Document owner, org.w3c.dom.Node parent, Map<String, String> inherited) {
    if (source instanceof Element) {
        Map<String, String> scope = new HashMap<>(inherited);
        org.w3c.dom.Element made = Evaluator.IsNthChild.w3cElementOf((Element) source, owner, scope);
        parent.appendChild(made);
        for (Node child : source.childNodes())
            appendW3cNode(child, owner, made, scope);
    } else if (source instanceof TextNode) {
        parent.appendChild(owner.createTextNode(((TextNode) source).getWholeText()));
    } else if (source instanceof DataNode) {
        parent.appendChild(owner.createTextNode(((DataNode) source).getWholeData()));
    } else if (source instanceof Comment) {
        parent.appendChild(owner.createComment(((Comment) source).getData()));
    }
}'''

HOP3 = '''/**
 * Creates the W3C element for an element, with its attributes.
 *
 * <p>An attribute is copied when its key, kept to the characters that an
 * XML name may contain, begins as an XML name may.</p>
 *
 * @param source the element
 * @param owner the W3C document that creates the element
 * @param scope the namespace URIs declared by the element's ancestors, by
 *            prefix; the element's own declarations are added to it
 * @return the new W3C element, with its attributes
 */
public static org.w3c.dom.Element w3cElementOf(Element source, org.w3c.dom.Document owner, Map<String, String> scope) {
    org.w3c.dom.Element made = HtmlTreeBuilder.createW3cElement(source, owner, scope);
    for (org.jsoup.nodes.Attribute attribute : source.attributes()) {
        String key = attribute.getKey().replaceAll("[^-a-zA-Z0-9_:.]", "");
        if (key.length() > 0 && "-.0123456789".indexOf(key.charAt(0)) < 0)
            made.setAttribute(key, attribute.getValue());
    }
    return made;
}'''

HOP4 = '''/**
 * Creates the W3C element for an element, without its attributes.
 *
 * @param source the element
 * @param owner the W3C document that creates the element
 * @param scope the namespace URIs declared by the element's ancestors, by
 *            prefix; the element's own declarations are added to it
 * @return the new W3C element
 */
public static org.w3c.dom.Element createW3cElement(Element source, org.w3c.dom.Document owner, Map<String, String> scope) {
    return Node.newW3cElement(source, owner, scope);
}'''

DESIGN = {
 "instance": "Jsoup-84", "project": "Jsoup", "bug_id": 84, "seed": 6573,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the protected field factory (DocumentBuilderFactory) and the parameter in, passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [1458, 1186, 778, 733, 725],
 "reachability_probe": "fromJsoup first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-84-probe: W3CDomTest::treatsUndeclaredNamespaceAsLocalName fails with "
                       "PROBE-REACHED at org.jsoup.helper.W3CDom.fromJsoup(W3CDom.java:37), called from W3CDomTest.java:144",
 "facade": {"file": W3C, "class": "org.jsoup.helper.W3CDom", "method": "fromJsoup", "near_line": 36},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/helper/W3CDomTest.java",
             "test_class": "org.jsoup.helper.W3CDomTest", "test_method": "treatsUndeclaredNamespaceAsLocalName"},
 "expected_signature": "NAMESPACE_ERR",
 "gold": {"method": "newW3cElement", "text": GOLD_TEXT,
          "fault": {"old": "        return owner.createElementNS(namespace == null && colon > 0 ? \"\" : namespace, tagName);",
                    "new": "        return owner.createElementNS(namespace, tagName);"}},
 "chain": {
   "facade_body": "Validate.notNull(in);\n"
                  "        return org.jsoup.nodes.Element.toW3cDocument(in, factory);",
   "lie": "The jsoup document is first written out as XML text, which a namespace-aware builder then parses into the W3C "
          "document.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "toW3cDocument",
      "imports": ["javax.xml.parsers.DocumentBuilderFactory", "javax.xml.parsers.ParserConfigurationException",
                  "java.util.HashMap", "org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "appendW3cNode",
      "imports": ["java.util.HashMap", "org.jsoup.nodes.Comment", "org.jsoup.nodes.DataNode", "org.jsoup.nodes.Element",
                  "org.jsoup.nodes.Node", "org.jsoup.nodes.TextNode", "org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsNthChild", "method": "w3cElementOf",
      "imports": ["java.util.Map", "org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "createW3cElement",
      "imports": ["java.util.Map"], "text": HOP4},
     {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "newW3cElement",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.helper.W3CDom.W3CBuilder::head", "org.jsoup.helper.W3CDom::convert"],
 "ownership_reason": "Only the gold resolves the namespace of an element: it adds the element's xmlns / xmlns:prefix declarations to "
                     "the scope, takes the prefix of the tag name, and decides the namespace that the W3C element is created in. "
                     "Hop 1 creates the document and starts the walk, hop 2 walks the tree and hands each element a copy of the "
                     "inherited scope (it never adds an entry), hop 3 copies attributes onto the element the gold made, hop 4 passes "
                     "through. The callers pass the jsoup element itself, so none of them can change the tag name the gold reads, "
                     "and the scope they pass is documented as the namespace URIs declared by the ancestors; once the gold calls "
                     "createElementNS with a null namespace and a prefixed name, the W3C DOM throws inside the gold and no caller "
                     "can recover the element. The gold's javadoc promises the new W3C element in the namespace bound to the "
                     "prefix; for <fb:like> with no xmlns:fb the variant produces no element (NAMESPACE_ERR). The convention is "
                     "pinned outside the gold: the intact sibling W3CDom.W3CBuilder.head, used in production by the public "
                     "W3CDom.convert, creates an element whose prefix is not bound with the empty namespace ('doesn't have a real "
                     "namespace defined'); namespacePreservation, convertsGoogle, simpleConversion, handlesInvalidAttributeNames "
                     "and convertsGoogleLocation pass through the chain.",
 "ownership_tests": ["org.jsoup.helper.W3CDomTest::namespacePreservation",
                     "org.jsoup.helper.W3CDomTest::convertsGoogle",
                     "org.jsoup.helper.W3CDomTest::simpleConversion",
                     "org.jsoup.helper.W3CDomTest::handlesInvalidAttributeNames",
                     "org.jsoup.helper.W3CDomTest::convertsGoogleLocation"],
 "compensating": {
   "chain": [
     {"file": EL, "old": "factory.setNamespaceAware(true);",
      "new": "factory.setNamespaceAware(false);",
      "why": "hop 1 creates the builder without namespace awareness"},
     {"file": HC, "old": "appendW3cNode(child, owner, made, scope);",
      "new": "appendW3cNode(child, owner, made, inherited);",
      "why": "hop 2 hands the children the inherited scope instead of the element's"},
     {"file": EV, "old": "HtmlTreeBuilder.createW3cElement(source, owner, scope);",
      "new": "HtmlTreeBuilder.createW3cElement(source, owner, new java.util.HashMap<String, String>());",
      "why": "hop 3 passes a fresh empty scope"},
   ],
 },
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, used in that order; none substituted, none drawn by this "
               "builder; W3CDom.java, the only candidate's file, excluded): nodes.Element (hop 1, 1458 lines), "
               "helper.HttpConnection (hop 2, 1186), select.Evaluator (hop 3, 778; a public abstract class, a public static "
               "method compiles), parser.HtmlTreeBuilder (hop 4, 733), nodes.Node (hop 5, gold, 725; a public abstract class; the "
               "smallest host). Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 6573 + 100 + i, "
               "as mr3_spec.py inserts them: hop 1 after Element.prependText (seed 6673), hop 2 after HttpConnection.referrer (6674), "
               "hop 3 after the constructor of the nested class Evaluator.IsNthChild (6675), hop 4 after "
               "HtmlTreeBuilder.popStackToClose(String...) (6676), hop 5 after Node.ownerDocument (6677). The hop-3 anchor is the "
               "IsNthChild constructor, whose header is indented by four spaces and a tab, so the picker takes it as a member of "
               "the outer class and the recipe inserts hop 3 after it, inside the public static nested class "
               "Evaluator.IsNthChild (in the host file Evaluator.java, which is not substituted); a static method compiles there, "
               "and hop 2 calls it as Evaluator.IsNthChild.w3cElementOf. W3C DOM types are written fully qualified in every hop (org.jsoup.nodes "
               "has its own Document, Element and Node); in Evaluator the jsoup Attribute is written fully qualified (Evaluator "
               "has a nested class Attribute). The facade calls hop 1 by its fully-qualified name (W3CDom imports "
               "org.w3c.dom.Element).",
}
