"""Main run Jsoup-1__i (cell C10i, batch 9, sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Jsoup-1; the real bug modified org.jsoup.nodes.Document, the facade's class). No static pair (pool v2: no_tested_static;
B8 note section 1).

Facade: Document.title() (instance method; the only allowed candidate of the task record, BATCH9_PREREGISTRATION.md rank 352;
facade_planned_by null, no facade reuse). The setter overload title(String) stays intact, as do head(), body() and the rest of the class.
Original computation: the first element, in document order, of getElementsByTag("title") (the document and all its descendants,
pre-order, matched by the lower-case tag name "title"); its text() trimmed, or the empty string when the document has no title element.

facade_variant: V2 (receiver as parameter). state_passed: the receiver `this` (typed as Document, the declaring class), handed to hop 1;
the hops call only public methods of it and of the elements (getAllElements(), tagName(), text()); the class reads and writes no field
in title(), so there is no write-back. The facade body is one call to hop 1 (the original has no argument guard). No visibility is
widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. title() calls no
private method, so V4 does not apply.

Redistribution of the computation: hop 1 collects all the document's elements in document order (getAllElements(), the same collector
and order as getElementsByTag), hop 2 trims the title text, hop 3 resolves the lower-case name of the title tag through Tag.valueOf, hop
4 passes through, and the gold makes the per-element decision: it visits the elements in document order and takes the text of the
document's title element (the first element with the title tag name), or the empty string.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-1-probe of the fixture, the first statement of
title() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.jsoup.nodes.DocumentTest::testTitles`: 1 failing test; `defects4j test -t org.jsoup.integration.ParseTest::testYahooJp`: 1 failing
test, java.lang.IllegalStateException: PROBE-REACHED at org.jsoup.nodes.Document.title(Document.java:62), called from
ParseTest.java:71; full suite: 6 failing tests, all PROBE-REACHED (DocumentTest::testTitles, ParserTest::createsDocumentStructure,
ParseTest::testSmhBizArticle / testNewsHomepage / testGoogleSearchIpod / testYahooJp). The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; batch9_tasks.json hosts_hop_order, used in that order, none substituted; Document.java, the only
candidate file, is excluded):
  hop 1 nodes.Element     828 lines  documentTitle  plumbing: the document's elements, in document order
  hop 2 safety.Whitelist  420 lines  trimmedTitle   placement: trims the title text
  hop 3 parser.Tag        374 lines  titleByTag     plumbing: resolves the lower-case title tag name (Tag.valueOf("title").getName())
  hop 4 select.Elements   371 lines  tagText        pass-through
  hop 5 nodes.Node        348 lines  titleText      GOLD: one pass over the elements in document order, deciding per element whether
                                                    it is the document's title element and taking its text
Host newline counts 828, 420, 374, 371, 348; the smallest host (and the gold host) has 348 lines (C10F addendum section 1: hosts under
1500 lines are expected in this regime). Anchors are picked by mr3_spec.py (stageB_lib.insert_hop, seed 8709 + 100 + i) and recorded in
host_notes.
The correct configuration returns the original result for every document: getAllElements() and getElementsByTag("title") use the same
pre-order collector, Element.tagName() is the lower-case tag name that Evaluator.Tag compares, and the first match's text() is trimmed.

Fault (one-line omission in the gold): the `break;` after the title text is taken is dropped, so the loop keeps going and every later
element with the title tag name overwrites the text; the variant returns the text of the LAST title element. The gold then reads as the
ordinary routine "take the text of the title-named element". Trigger: the EXISTING test DocumentTest::testTitles; its assertions on the
untitled document pass (no title: ""; after title("Hello"): "Hello", one title element), and assertEquals("First", withTitle.title()) on
"<title>First</title><title>Ignore</title><p>Hello</p>" fails with expected:<[First]> but was:<[Ignore]>. It is the only test whose
document has more than one title element (the four ParseTest pages and ParserTest::createsDocumentStructure have exactly one; checked on
the test resources), and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it returns the text of "a document's title element", visiting the elements in document
order) and is silent on what happens after the title element is found. A document's title element is the first title element in
document order (HTML: "the title element of a document is the first title element in the document, in tree order"); the variant returns
the text of the second one, which is not the document's title element, on the trigger input. The convention is pinned outside the gold:
the intact setter Document.title(String) updates the first title element (getElementsByTag("title").first()), so the getter must read
the element the setter writes; Element.getElementById returns elements.get(0), the first match in document order; Document.head() /
body() take .first(); passing tests: ElementTest::testGetElementById (the first match in document order: "not the span"),
ElementTest::getElementsByTagName (getElementsByTag lists matches in document order), ParserTest::createsDocumentStructure and
ParseTest::testYahooJp (through the chain: a single title element is read and trimmed).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: elements supplies every element visited; titleTag decides which element's text is taken.
  T2 absent: text starts as "" and is assigned in the loop; element is the loop variable; the if decides whether text is assigned and
     the loop stops; no local is dead or frozen.
  T3 absent: no set of siblings is enumerated; one tag name is compared; no class named in the gold's text is handled in part.
  T4 absent: 'the text of a document's title element', 'visited in document order' and '@return title text, or empty string if no
     element has the title tag name' are met by lines of the body; 'lower case' and 'in document order' in @param are caller
     preconditions.
 Variant gold (javadoc, signature, `String text = "";`, the for-each loop, `if (element.tagName().equals(titleTag))`, `text =
 element.text();`, `return text;`):
  T1 absent: elements and titleTag each change the result; neither is only argument-checked.
  T2 absent: text is initialised to "" and reassigned inside the loop, then returned (not frozen: the loop assigns it); element is the
     for-each variable; the if decides whether text is assigned (two different effects); no local is dead.
  T3 absent: no closed set is enumerated (one tag name, no pair, no range); no named class is handled in part.
  T4 absent: 'the text of a document's title element' is a general description that the body addresses (it returns the text of a
     title-named element); 'The elements are visited in document order' is met (the loop visits the list in order); '@return title
     text, or empty string if no element has the title tag name' is met (text stays ""); no inline comment; identifiers (text, element,
     titleTag) name nothing the body does not meet. No phrase names 'first', a count, a limit or a position.

Single owner: only the gold decides which element's text is the title: hops 1, 3 and 4 pass the full element list and the tag name along,
and hop 2 only trims the gold's result. Once the gold has taken the text of the last title element, "First" can appear only if a caller
replaces the gold or rewrites the list it is given (in a way the hops' documentation excludes). Declared alternatives (G9): hop 1 collects
only the title elements (getElementsByTag("title")); hop 1 collects only the head's elements (document.head().getAllElements()); hop 2
collapses runs of whitespace in the trimmed title. None makes the trigger pass (both title elements stay in the list, in order).
Recorded bypasses:
 B-0 the facade (its original body) or hop 1 (`return document.getElementsByTag("title").first() ...`) reads the first title element
     directly, discarding the rest of the chain including the gold.
 B-1 hop 1 or hop 4 reverses the list before passing it (for example new Elements(elements) reversed with Collections.reverse), so that
     the last title element seen is the first in document order; it breaks the documented 'elements of a document, in document order'
     of hops 2-4 and of the gold.

Lie: the facade's javadoc claims the title element's HTML is rendered first and its tags are then stripped to give the text; no step of
the chain renders HTML or strips tags (the text is read with Element.text()). It names neither the choice among title elements nor any
hop."""

DOC = "src/main/java/org/jsoup/nodes/Document.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
WL = "src/main/java/org/jsoup/safety/Whitelist.java"
TAG = "src/main/java/org/jsoup/parser/Tag.java"
ELS = "src/main/java/org/jsoup/select/Elements.java"
NODE = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = '''/**
 Gets the text of a document's title element.
 <p>
 The elements are visited in document order, and the text of the element with the title tag name is returned.
 @param elements elements of a document, in document order
 @param titleTag lower case name of the title tag
 @return title text, or empty string if no element has the title tag name
 */
public static String titleText(List<Element> elements, String titleTag) {
    String text = "";
    for (Element element : elements) {
        if (element.tagName().equals(titleTag)) {
            text = element.text();
            break;
        }
    }
    return text;
}'''

HOP1 = '''/**
 * Gets the title of a document, from all of its elements.
 *
 * @param document the document to read
 * @return the trimmed text of the document's title element, or empty string if it has none
 */
public static String documentTitle(Document document) {
    return Whitelist.trimmedTitle(document.getAllElements());
}'''

HOP2 = '''/**
 Gets the text of a document's title element, with leading and trailing whitespace removed.

 @param elements elements of a document, in document order
 @return trimmed title text, or empty string if there is no title element
 */
public static String trimmedTitle(List<Element> elements) {
    return Tag.titleByTag(elements).trim();
}'''

HOP3 = '''/**
 Gets the text of a document's title element, matching elements by the name of the {@code title} tag.
 @param elements elements of a document, in document order
 @return title text, or empty string if there is no title element
 */
public static String titleByTag(List<Element> elements) {
    return Elements.tagText(elements, valueOf("title").getName());
}'''

HOP4 = '''/**
 Get the text of a document's title element.
 @param elements elements of a document, in document order
 @param tagName lower case name of the title tag
 @return title text, or empty string if there is no title element
 */
public static String tagText(List<Element> elements, String tagName) {
    return Node.titleText(elements, tagName);
}'''

DESIGN = {
 "instance": "Jsoup-1", "project": "Jsoup", "bug_id": 1, "seed": 8709,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (typed as Document), passed to hop 1; hops call only its public getAllElements() and the elements' "
                 "public tagName() / text(); no field read or written, no write-back",
 "host_mode": "largest5", "host_lines": [828, 420, 374, 371, 348],
 "reachability_probe": "title() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-1-probe: DocumentTest::testTitles and ParseTest::testYahooJp fail with "
                       "PROBE-REACHED at Document.title(Document.java:62); full suite 6 failing, all PROBE-REACHED",
 "facade": {"file": DOC, "class": "org.jsoup.nodes.Document", "method": "title", "near_line": 61},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/DocumentTest.java",
             "test_class": "org.jsoup.nodes.DocumentTest", "test_method": "testTitles"},
 "expected_signature": "but was:<[Ignore]>",
 "gold": {"method": "titleText", "text": GOLD_TEXT,
          "fault": {"old": "                text = element.text();\n                break;",
                    "new": "                text = element.text();"}},
 "chain": {
   "facade_body": "return Element.documentTitle(this);",
   "lie": "The title element's HTML is rendered first, and its tags are then stripped to give the text.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "documentTitle",
      "imports": ["org.jsoup.safety.Whitelist"], "text": HOP1},
     {"file": WL, "class": "org.jsoup.safety.Whitelist", "method": "trimmedTitle",
      "imports": ["java.util.List", "org.jsoup.parser.Tag"], "text": HOP2},
     {"file": TAG, "class": "org.jsoup.parser.Tag", "method": "titleByTag",
      "imports": ["org.jsoup.nodes.Element", "org.jsoup.select.Elements"], "text": HOP3},
     {"file": ELS, "class": "org.jsoup.select.Elements", "method": "tagText",
      "imports": ["org.jsoup.nodes.Node"], "text": HOP4},
     {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "titleText",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Document::title(String)",
              "org.jsoup.nodes.Element::getElementById",
              "org.jsoup.nodes.Document::head"],
 "ownership_reason": "Only the gold decides which element's text is the document's title: it visits the document's elements in "
                     "document order and takes the text of the element with the title tag name. Hops 1, 3 and 4 pass the full element "
                     "list (documented as the elements of a document, in document order) and the lower-case tag name along, and hop 2 "
                     "only trims the gold's result. A document's title element is the first title element in document order (HTML); "
                     "the variant keeps visiting after the title element and returns the text of the last title-named element, so on "
                     "a document with two title elements it returns the second one's text. The convention is pinned outside the gold: "
                     "the intact setter Document.title(String) updates getElementsByTag(\"title\").first(), the element the getter "
                     "must read back; Element.getElementById returns the first match in document order (elements.get(0)); "
                     "Document.head() and body() take .first(). ElementTest::testGetElementById (the first match in document order) "
                     "and ElementTest::getElementsByTagName (matches listed in document order) pass, as do "
                     "ParserTest::createsDocumentStructure and ParseTest::testYahooJp through the chain (one title element).",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::testGetElementById",
                     "org.jsoup.nodes.ElementTest::getElementsByTagName",
                     "org.jsoup.parser.ParserTest::createsDocumentStructure",
                     "org.jsoup.integration.ParseTest::testYahooJp"],
 "compensating": {
   "chain": [
     {"file": EL, "old": "return Whitelist.trimmedTitle(document.getAllElements());",
      "new": "return Whitelist.trimmedTitle(document.getElementsByTag(\"title\"));",
      "why": "hop 1 collects only the title elements"},
     {"file": EL, "old": "return Whitelist.trimmedTitle(document.getAllElements());",
      "new": "return Whitelist.trimmedTitle(document.head().getAllElements());",
      "why": "hop 1 collects only the elements of the head"},
     {"file": WL, "old": "return Tag.titleByTag(elements).trim();",
      "new": "return Tag.titleByTag(elements).trim().replaceAll(\"\\\\s+\", \" \");",
      "why": "hop 2 collapses runs of whitespace in the title"},
   ],
 },
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder; "
               "Document.java, the only candidate file, excluded): nodes.Element (hop 1, 828 lines), safety.Whitelist (hop 2, 420), "
               "parser.Tag (hop 3, 374), select.Elements (hop 4, 371), nodes.Node (hop 5, gold, 348; the smallest host; abstract "
               "public class, which carries a public static method). All five are public top-level classes in which a public static "
               "method compiles. Anchors from stageB_lib.insert_hop with seed 8709 + 100 + i, as mr3_spec.py inserts them: hop 1 after val (seed 8809), hop 2 after addEnforcedAttribute (8810), hop 3 after isInline (8811), hop 4 after addAll (8812), hop 5 after replaceWith (8813). "
               "The facade calls hop 1 as Element.documentTitle (same package, Document's superclass); each hop imports the next host "
               "where it is in another package (Element imports safety.Whitelist; Whitelist imports java.util.List and parser.Tag; Tag "
               "imports nodes.Element and select.Elements; Elements imports nodes.Node); the gold uses Element from its own package and "
               "java.util.List already imported by Node.",
}
