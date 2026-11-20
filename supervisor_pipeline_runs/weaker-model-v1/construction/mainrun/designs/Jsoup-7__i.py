"""Main run Jsoup-7__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Jsoup-7; the real bug modified org.jsoup.nodes.Document, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE.md
section 1: pool v2 no_tested_static).

Facade: Document.title(String) (the setter overload; the only allowed candidate of batch9_tasks.json, "Document.title", V2, 8 lines,
start line 75, header `public void title(String title) {`; facade_planned_by = Jsoup-1__i, so this is a recorded facade reuse:
no other allowed candidate exists). The getter title() at line 65 is left intact.
Original computation: Validate.notNull(title); the first element of getElementsByTag("title") (a search of the whole document tree,
in document order); if there is none, head().appendElement("title").text(title); otherwise titleEl.text(title).

facade_variant: V2 (receiver as parameter). The computation needs the receiver's public methods (the tree under the document, reached
through children(), and head()); the facade keeps the original guard Validate.notNull(title) and passes `this` (typed Document) and
the title String to hop 1; the hops call only public methods of Document, Element and Elements. The original reads and writes no
field, so there is no write-back (the method is void). No private method of Document is involved (no V4); no package-private type is
involved (no V3/V5). No visibility is widened, no type is added, no signature, modifier, override or throws change, no reflection,
no test edit.
state_passed: the receiver `this` (Document) and the parameter title, handed to hop 1; no write-back.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-7-probe of the fixture, the first statement
of title(String) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.jsoup.nodes.DocumentTest::testTitles`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED.
Full suite with the probe: 1 failing test (DocumentTest::testTitles only; the setter has no production caller and no other test
caller). The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of the task record, in that order, none substituted; the facade's file
Document.java is excluded by the record):
  hop 1 nodes.Entities        2274 lines  documentTitle  sets the text of the element hop 2 returns (Element.text(String)) for
                                                         the tag name "title"
  hop 2 nodes.Element         1044 lines  elementForTag  placement: the first element with the tag name anywhere in the document
                                                         (from hop 3), or a new element with that tag name appended to head
  hop 3 helper.HttpConnection  543 lines  firstOfTag     normalisation: lower-cases the tag name (tag names are stored in lower
                                                         case, Tag.valueOf), then delegates
  hop 4 parser.Tag             504 lines  firstNamed     guard: Validate.notEmpty(tagName), then delegates
  hop 5 select.Elements        455 lines  firstTagged    GOLD: the per-element search: walks the elements under root in document
                                                         order (each element's children are inserted right after it in the
                                                         candidate list) and returns the first whose tag name matches
Host newline counts 2274, 1044, 543, 504, 455; the smallest host (and the gold host) is Elements with 455 lines (C10F addendum
section 1: hosts under 1500 lines are expected in this regime). Anchors: stageB_lib.insert_hop / pick_anchor with the instance seed
5623 + 100 + i, as mr3_spec.py inserts them (recorded in the spec's stage_b audit and in host_notes).
The correct configuration is behaviour-identical to the original setter: the gold's pre-order walk of the elements under the document
visits them in the order getElementsByTag collects them (the document root itself, '#root', never has the tag name "title"), and
head() is read only when no title element exists, as in the original.

Fault (one-line omission in the gold): `candidates.addAll(i + 1, candidate.children());` is dropped from firstTagged's loop, so the
search looks only at root's own child elements and never at the elements nested inside them. Trigger: the EXISTING test
DocumentTest::testTitles. On the document parsed from "<title>First</title><title>Ignore</title><p>Hello</p>" the title elements sit
in #root > html > head; the gold sees only html, returns null, and hop 2 appends a third, new title element to head that receives
"Hello"; the first title still reads "First", so assertEquals("Hello", withTitle.title()) (DocumentTest.java:33) fails with
expected:<[Hello]> but was:<[First]>. The noTitle half of the test still passes (there is no title to find; the new element is
appended to head as in the original). It is the only test that reaches the setter (probe above), so gate G5 can only see this test
newly fail.

The gold's javadoc states the idiomatic contract in Elements' and Element's own voice ("Finds the first element with the given tag
name", "@param root the element to search") and is silent on how the search descends. In jsoup, searching an element for a tag name
covers every element under it (Element.getElementsByTag: "Finds elements, including and recursively under this element";
Element.select: "Matched elements may include this element, or any of its children"; Element.getElementById; Document.head() through
the recursive findFirstElementByTagName), and the gold's caller (hop 2) documents "anywhere in a document". The variant returns null
for a document whose title elements sit inside head, so the contract is violated on the trigger input. Passing tests
ElementTest::getElementsByTagName (the nested div2 is found, in document order), ElementTest::testGetElementById (the first match in
document order, nested) and ParserTest::createsDocumentStructure (head and its nested elements are found) pin the convention.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature `firstTagged(Element root, String tagName)`, `Elements candidates = root.children();`, the index loop
 with the tag-name test, `candidates.addAll(i + 1, candidate.children());`, `return null;`):
  T1 absent: root supplies the candidate list; tagName decides which candidate is returned; neither is only argument-checked.
  T2 absent: candidates is read (size, get) and extended; i is the loop cursor advanced by the loop header; candidate is read by the
     test, the return and the expansion; no literal-initialised local; the one decision chooses between returning and continuing.
  T3 absent: no closed set is handled member by member (no node kinds, no cases, no pair halves or range ends); every candidate gets
     the same test and the same expansion; no class is named in the gold's text.
  T4 absent: "Finds the first element with the given tag name", "@param root the element to search", "@param tagName lower-case tag
     name" (a caller precondition) and "@return the first element with the tag name, or null if none is found" are general
     descriptions met by lines of the body; no inline comment; identifiers (firstTagged, root, tagName, candidates, candidate) name
     nothing the body does not meet.
 Variant gold (the same text without `candidates.addAll(i + 1, candidate.children());`; the loop body is the tag-name test and its
 return):
  T1 absent: root supplies the list the loop scans; tagName is compared with each candidate's tag name and decides the return; no
     parameter is unused, overwritten or only checked.
  T2 absent: candidates is read by the loop condition and by get(i); i is the for-loop cursor advanced by i++; candidate is read by
     the test and returned; no local is initialised to a literal; no dead or frozen local; the if decides whether the method returns
     the candidate, so no dead decision.
  T3 absent: no closed set is visible in the text: the gold treats every candidate alike and names no kinds, cases, pairs or ranges
     ('No member handled'); no member or field is read without the treatment a sibling gets.
  T4 absent: the javadoc names no rule, limit, bound, value class or case that the body visibly does not meet: "the first element
     with the given tag name" is met (the first matching candidate is returned), "or null if none is found" is met (null after the
     loop), "the element to search" is a general description of the parameter, "lower-case tag name" is a caller precondition; it does
     not say "recursively", "descendants", "nested", "anywhere" or "all"; no comment; no identifier names a property the body does not
     meet.

Single owner: the gold is the only step that searches the tree. Hop 1 sets the text of whatever element hop 2 returns (Element.text
replaces its contents); hop 2 only chooses between the found element and a new element in head; hops 3 and 4 only normalise and
check the tag name. Once the gold returns null for a document whose title sits inside head, hop 2 documents appending a new element,
and the old first title keeps "First" unless a caller searches the tree itself (a second implementation of the gold's step), narrows
the search to head against hop 2's "anywhere in a document", or removes existing content against hop 2's "a new one is appended".
Declared alternatives (G9, none absorbs): hop 2 always appends a new element; hop 2 appends a new element to body instead of head;
hop 3 passes the tag name without lower-casing; hop 1 trims the title text.
Recorded bypasses (not declared, they absorb):
 B-0 the facade's original body, or any hop calling root.getElementsByTag(tagName).first() (or select) instead of the next hop,
     discards the gold.
 B-1 hop 2 searches doc.head() instead of doc (`HttpConnection.firstOfTag(doc.head(), tagName)`): the title elements are head's own
     children, so the trigger passes; against hop 2's documentation ("anywhere in a document"), and the gold still misses nested
     elements.
 B-2 hop 2 empties head before appending (`doc.head().empty().appendElement(tagName)`): the old title elements disappear, so the
     trigger passes; against hop 2's documentation (it removes the other contents of head, and the existing element is never found).
 B-1 and B-2 were applied to the variant in scratch copies: each makes the full suite pass (0 failing tests); the plain variant fails
 DocumentTest::testTitles only (gate G5).

Lie: the facade's javadoc gains "Surrounding whitespace is trimmed from the given title before it is stored."; the chain stores the
given string unchanged (Element.text(String) in hop 1). It names neither the search nor any hop."""

DOC = "src/main/java/org/jsoup/nodes/Document.java"
ENT = "src/main/java/org/jsoup/nodes/Entities.java"
ELE = "src/main/java/org/jsoup/nodes/Element.java"
HTTP = "src/main/java/org/jsoup/helper/HttpConnection.java"
TAG = "src/main/java/org/jsoup/parser/Tag.java"
ELS = "src/main/java/org/jsoup/select/Elements.java"

GOLD_TEXT = '''/**
 * Finds the first element with the given tag name.
 * @param root the element to search
 * @param tagName lower-case tag name
 * @return the first element with the tag name, or null if none is found
 */
public static Element firstTagged(Element root, String tagName) {
    Elements candidates = root.children();
    for (int i = 0; i < candidates.size(); i++) {
        Element candidate = candidates.get(i);
        if (candidate.tagName().equals(tagName))
            return candidate;
        candidates.addAll(i + 1, candidate.children());
    }
    return null;
}'''

HOP1 = '''/**
 * Sets the text of a document's {@code title} element, replacing the element's contents. The element is the first
 * {@code title} in the document, or a new one in the document's {@code head} when there is none.
 * @param doc the document
 * @param title unencoded text of the title
 */
public static void documentTitle(Document doc, String title) {
    Element.elementForTag(doc, "title").text(title);
}'''

HOP2 = '''/**
 * Gets the first element with the given tag name anywhere in a document, in document order. If the document has no
 * such element, a new one is appended to the document's {@code head} and returned.
 * @param doc the document
 * @param tagName tag name of the element
 * @return the existing or the new element
 */
public static Element elementForTag(Document doc, String tagName) {
    Element found = HttpConnection.firstOfTag(doc, tagName);
    return found != null ? found : doc.head().appendElement(tagName);
}'''

HOP3 = '''/**
 * Finds the first element with the given tag name in an element, matching the tag name case insensitively.
 * @param root the element to search
 * @param tagName the tag name
 * @return the first matching element, or null if there is none
 */
public static Element firstOfTag(Element root, String tagName) {
    return Tag.firstNamed(root, tagName.toLowerCase());
}'''

HOP4 = '''/**
 * Finds the first element with the given lower-case tag name in an element.
 * @param root the element to search
 * @param tagName the tag name, in lower case; must not be empty
 * @return the first matching element, or null if there is none
 */
public static Element firstNamed(Element root, String tagName) {
    Validate.notEmpty(tagName);
    return Elements.firstTagged(root, tagName);
}'''

DESIGN = {
 "instance": "Jsoup-7", "project": "Jsoup", "bug_id": 7, "seed": 5623,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "batch": "batch9", "facade_variant": "V2",
 "state_passed": "the receiver this (Document) and the parameter title, passed to hop 1; no field read or written; no write-back",
 "host_mode": "largest5", "host_lines": [2274, 1044, 543, 504, 455],
 "facade_reuse_of": ["Jsoup-1__i"],
 "reachability_probe": "title(String) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-7-probe: DocumentTest::testTitles fails with PROBE-REACHED; "
                       "full suite: only DocumentTest::testTitles fails",
 "facade": {"file": DOC, "class": "org.jsoup.nodes.Document", "method": "title", "near_line": 75},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/DocumentTest.java",
             "test_class": "org.jsoup.nodes.DocumentTest", "test_method": "testTitles"},
 "expected_signature": "but was:<[First]>",
 "gold": {"method": "firstTagged", "text": GOLD_TEXT,
          "fault": {"old": "                return candidate;\n            candidates.addAll(i + 1, candidate.children());\n",
                    "new": "                return candidate;\n"}},
 "chain": {
   "facade_body": "Validate.notNull(title);\n        Entities.documentTitle(this, title);",
   "lie": "Surrounding whitespace is trimmed from the given title before it is stored.",
   "hops": [
     {"file": ENT, "class": "org.jsoup.nodes.Entities", "method": "documentTitle", "imports": [], "text": HOP1},
     {"file": ELE, "class": "org.jsoup.nodes.Element", "method": "elementForTag",
      "imports": ["org.jsoup.helper.HttpConnection"], "text": HOP2},
     {"file": HTTP, "class": "org.jsoup.helper.HttpConnection", "method": "firstOfTag",
      "imports": ["org.jsoup.nodes.Element", "org.jsoup.parser.Tag"], "text": HOP3},
     {"file": TAG, "class": "org.jsoup.parser.Tag", "method": "firstNamed",
      "imports": ["org.jsoup.nodes.Element", "org.jsoup.select.Elements"], "text": HOP4},
     {"file": ELS, "class": "org.jsoup.select.Elements", "method": "firstTagged", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Element::getElementsByTag", "org.jsoup.nodes.Element::getElementById",
              "org.jsoup.nodes.Element::select", "org.jsoup.nodes.Document::head"],
 "ownership_reason": "Only the gold searches the document tree: given root and a tag name it is meant to return the first element "
                     "with that tag name under root in document order, which in jsoup covers every element under root, not only "
                     "root's own children. Hop 1 sets the text of the element hop 2 returns; hop 2 chooses between the found "
                     "element and a new element appended to head; hops 3 and 4 only lower-case and check the tag name. The variant "
                     "gold looks only at root's own child elements, so for '<title>First</title><title>Ignore</title>' (both titles "
                     "inside html > head) it returns null, hop 2 appends a new title to head, and the document's first title still "
                     "reads 'First' after title(\"Hello\"); 'Hello' can come back only if a caller searches the tree itself (a second "
                     "implementation of the gold's step), narrows the search to head against hop 2's 'anywhere in a document', or "
                     "removes head's contents against hop 2's documentation. The convention that searching an element for a tag "
                     "name covers the whole tree under it is pinned outside the gold: Element.getElementsByTag ('including and "
                     "recursively under this element'), Element.getElementById, Element.select and Document.head (through the "
                     "recursive findFirstElementByTagName) do the same step in production, and ElementTest::getElementsByTagName "
                     "(nested div2 found, document order), ElementTest::testGetElementById and "
                     "ParserTest::createsDocumentStructure pass.",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::getElementsByTagName",
                     "org.jsoup.nodes.ElementTest::testGetElementById",
                     "org.jsoup.parser.ParserTest::createsDocumentStructure"],
 "compensating": {
   "chain": [
     {"file": ELE, "old": "        return found != null ? found : doc.head().appendElement(tagName);",
      "new": "        return doc.head().appendElement(tagName);",
      "why": "hop 2 always appends a new element to head"},
     {"file": ELE, "old": "        return found != null ? found : doc.head().appendElement(tagName);",
      "new": "        return found != null ? found : doc.body().appendElement(tagName);",
      "why": "hop 2 appends a new element to body instead of head"},
     {"file": HTTP, "old": "        return Tag.firstNamed(root, tagName.toLowerCase());",
      "new": "        return Tag.firstNamed(root, tagName);",
      "why": "hop 3 passes the tag name without lower-casing it"},
     {"file": ENT, "old": "        Element.elementForTag(doc, \"title\").text(title);",
      "new": "        Element.elementForTag(doc, \"title\").text(title.trim());",
      "why": "hop 1 trims the title text"},
   ],
 },
 "host_notes": "host_mode largest5: the hosts are EXACTLY hosts_hop_order of the batch9_tasks.json record for Jsoup-7__i, in that "
               "order, none substituted, none drawn or chosen by this builder: nodes.Entities (hop 1, 2274 lines), nodes.Element "
               "(hop 2, 1044), helper.HttpConnection (hop 3, 543), parser.Tag (hop 4, 504), select.Elements (hop 5, gold, 455; the "
               "smallest host). The facade's file Document.java is excluded (facade_files_excluded). All five are public concrete "
               "top-level classes in which a public static method compiles. Anchors: stageB_lib.pick_anchor "
               "(host_search.pick_insertion_anchor, outer-class members only) with seed 5623 + 100 + i, as mr3_spec.py inserts "
               "them (from the spec's stage_b audit): hop 1 after Entities.escape (seed 5723), hop 2 after "
               "Element.getElementsMatchingText (5724), hop 3 after HttpConnection.execute (5725), hop 4 after Tag.canContainBlock "
               "(5726), hop 5 after Elements.remove (5727). The facade calls hop 1 in its own package; hop 2 imports "
               "helper.HttpConnection; hop 3 imports nodes.Element and parser.Tag; hop 4 imports nodes.Element and select.Elements "
               "(Validate is already imported by Tag); the gold needs no import (nodes.Element is already imported by Elements).",
}
