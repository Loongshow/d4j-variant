"""Main run Jsoup-29__i (cell C10i, batch 9 sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Jsoup-29; the real bug modified org.jsoup.nodes.Document, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE
section 1: pool v2 found no tested static facade; the paired_* fields of the task record are null).

Facade: Document.title() (the getter; the only allowed candidate of BATCH9_PREREGISTRATION.md row 354, "Document.title (V2, 8
lines)"). facade_planned_by = Jsoup-1__i, so this is a recorded facade reuse (facade_reuse_of: Jsoup-1__i); there is no other allowed
candidate, so no distinct facade was available. None of that instance's files was opened. The setter overload title(String) is left
intact.
Original computation of the facade: the first element with the tag name "title" in the document (getElementsByTag("title").first());
none gives ""; otherwise its text (Element.text(): the raw text of a whitespace-preserving element, trimmed), with its whitespace
normalised by StringUtil.normaliseWhitespace (each run of HTML whitespace becomes one space) and trimmed.

facade_variant: V2 (receiver as parameter). The computation needs public methods of the receiver (getElementsByTag, inherited from
Element) and of the Elements/Element objects it returns (first, text); the facade reads no field and calls no private method, so V1
and V4 do not apply; no package-private type is involved (no V3/V5). The facade body is one call to hop 1 with `this`, typed as the
declaring class Document; there was no argument guard. No visibility is widened, no type is added, no signature, modifier, override
or throws change, no reflection, no test edit.
state_passed: the receiver `this` (as org.jsoup.nodes.Document) to hop 1; no field is read or written, no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-29-probe/w of the fixture,
the first statement of title() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.jsoup.nodes.DocumentTest::testTitles`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
org.jsoup.nodes.Document.title(Document.java:68) from DocumentTest.testTitles(DocumentTest.java:26). Full suite with the probe: 8
failing tests, all PROBE-REACHED callers of title(): DocumentTest::testTitles, HtmlParserTest::createsDocumentStructure,
::handlesUnclosedTitle, ::handlesUnclosedTitleAtEof, ParseTest::testYahooJp, ::testGoogleSearchIpod, ::testSmhBizArticle,
::testNewsHomepage. title() has no production caller.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of the task record, in that order, none substituted; all five are public
top-level classes in which a static method compiles; the facade's file Document.java is excluded):
  hop 1 nodes.Element          1119 lines  documentTitle     query: the document's elements with the tag name "title"
  hop 2 helper.HttpConnection   661 lines  firstElementText  decision: the first of the elements; none gives ""; else its text
  hop 3 nodes.Node              617 lines  trimmedText       placement: trims what hop 4 returns
  hop 4 select.Elements         536 lines  spacedText        pass-through
  hop 5 select.Evaluator        454 lines  normalisedText    GOLD: one pass over the code points of the text, writing each
                                                             whitespace code point as a space unless the text written so far
                                                             already ends in one, every other code point as it is
Host newline counts 1119, 661, 617, 536, 454; the smallest host (and the gold host) is Evaluator, 454 lines (C10F addendum section 1:
hosts under 1500 lines are expected in this regime). Anchors (stageB_lib.pick_insertion_anchor through mr3_spec.py, instance seed
8192, hop i at seed 8192 + 100 + i - 1): hop 1 after `nodeName` (Element, seed 8292), hop 2 after `followRedirects` (HttpConnection,
outer class, seed 8293), hop 3 after `remove` (Node, seed 8294), hop 4 after `eq` (Elements, seed 8295), hop 5: Evaluator has no
admissible interior anchor (seed 8296), so the recipe appends the hop before the closing brace of the outer class.
The correct configuration returns the original String for every Document: the gold's look-back on the builder (`sb.charAt(sb.length()
- 1) == ' '`) is exactly StringUtil.normaliseWhitespace's lastWasWhite (a space in the builder is only ever written by the
whitespace branch), the whitespace test is the same StringUtil.isWhitespace, code points are walked the same way, and hop 3 applies
the original's trim.

Fault (one-line omission of a decision in the gold): the look-back that keeps a second space from being written after one already
written is dropped, so every whitespace code point becomes its own space. The gold then reads as the ordinary routine "whitespace is
written as a space, everything else as it is". Trigger: the EXISTING test DocumentTest::testTitles. Its first five assertions (no
title "", set "Hello", the first of two titles "First", set "Hello") still hold; assertEquals("Hello there now",
normaliseTitle.title()) for "<title>   Hello\\nthere   \\n   now   \\n" fails: the title element's text is "Hello\\nthere   \\n   now"
(Element.text() trims but does not normalise a whitespace-preserving element), and the variant writes seven spaces between "there"
and "now". It is the only test that newly fails: every other title asserted by a test ("jsoup", "Data", "Data<" ... , "One <b>Two
<b>Three", "One", the four ParseTest pages) has no two adjacent whitespace characters inside the title text, and the new hops have no
other caller; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the text with its whitespace normalised, as the text of an Element is) and is
silent on how runs are treated; "Hello there       now" is not normalised in jsoup's sense. The convention is pinned outside the gold:
StringUtil.normaliseWhitespace (the library's normaliser, which writes a run of whitespace as one space), TextNode.text ("Unencoded,
normalised text", through TextNode.normaliseWhitespace) and Element.text (normalised text of the element and its children), with
StringUtilTest::normaliseWhiteSpace ("   hello   \\r \\n  there    \\n" -> " hello there ") and ElementTest::testNormalisesText ("Hello
There. Here is some text." from text with " \\n " runs) passing; the facade's own javadoc ("Trimmed title") is kept unchanged.

Single owner: only the gold decides how whitespace is written; hop 1 only queries, hop 2 only picks the first element and reads its
text, hop 3 only trims the ends, hop 4 passes the text along. No one-line change above the gold that keeps to the hops' documentation
restores the trigger: trimming more (hop 3 trimming its input too) leaves the interior run, ownText() gives the same raw text for a
whitespace-preserving title, and another query (select("title")) gives the same element.
Declared alternatives (G9): hop 1 queries with select("title"); hop 2 reads ownText() instead of text(); hop 3 trims the text before
handing it on as well as after. Each leaves the trigger failing.
Recorded bypasses (edits that put a second implementation of the gold's job in front of or behind the gold, not repairs of the chain):
 B-1 normalising the text again at a hop with the library's normaliser, e.g. hop 2 `return
     Node.trimmedText(StringUtil.normaliseWhitespace(first.text()));` or hop 3 `return
     StringUtil.normaliseWhitespace(Elements.spacedText(text)).trim();` (or a replaceAll("\\\\s+", " ") at any hop): the gold
     still writes one space per whitespace code point for any text that reaches it with a run, against its own javadoc. Checked
     on the variant in a scratch copy for the hop 2 form: trigger passes, full suite 0 failing tests.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the head is searched first and the rest of the document only when the head holds no title element;
the chain searches the whole document in document order (getElementsByTag) and never looks at the head separately. It names neither
whitespace, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: text sizes the builder, bounds and drives the loop, and every code point of it is tested and written; no argument check.
  T2 absent: sb is returned; c is read by the whitespace test and written; i advances by Character.charCount(c); no literal-
     initialised local (i starts at 0 and is reassigned by the loop update); the whitespace test and the look-back each change what
     is written.
  T3 absent: two classes (whitespace and every other code point) and both are written; the look-back is the only special treatment and
     has no sibling; no enum, type code or named format member; the gold names no class it handles in part.
  T4 absent: "whitespace normalised, as the text of an Element is" is a general description that the whitespace branch addresses;
     "@param text the text to normalise" and "@return the normalised text" name no concrete rule; no comment.
 Variant gold (javadoc, signature, builder sized by the text, one pass over the code points: StringUtil.isWhitespace(c) appends ' ',
 else appendCodePoint(c); returns the builder's String):
  T1 absent: text sizes the builder, bounds and drives the loop and supplies every code point; it decides and is written into the
     return value.
  T2 absent: sb is appended to in both branches and returned; c is read by the test and by appendCodePoint; i is the loop cursor and
     advances in the loop update; no literal-initialised local is tested or returned (i is reassigned); the two branches write
     different things (a space / the code point itself), so the decision is live.
  T3 absent: the two-member partition whitespace / other is handled on both sides; there is no case list, no pair, no range ends,
     no named class (no "run", "single", "collapse", "leading", "trailing" in the text); "No member handled" for runs.
  T4 absent: "Get a text with its whitespace normalised, in the same way as the text of an Element" is a general description of
     what the method computes, addressed by the whitespace branch (like "the reduced fraction"); the @param and @return clauses name
     no rule, limit or value class; no inline comment; the identifiers normalisedText, sb, c, i name what they hold."""

DOC = "src/main/java/org/jsoup/nodes/Document.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"
ELS = "src/main/java/org/jsoup/select/Elements.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"

GOLD_TEXT = '''/**
 * Get a text with its whitespace normalised, in the same way as the text of an {@link Element}.
 *
 * @param text the text to normalise
 * @return the normalised text
 */
public static String normalisedText(String text) {
    StringBuilder sb = new StringBuilder(text.length());
    int c;
    for (int i = 0; i < text.length(); i += Character.charCount(c)) {
        c = text.codePointAt(i);
        if (StringUtil.isWhitespace(c)) {
            if (sb.length() > 0 && sb.charAt(sb.length() - 1) == ' ')
                continue;
            sb.append(' ');
        } else {
            sb.appendCodePoint(c);
        }
    }
    return sb.toString();
}'''

HOP1 = '''/**
 * Get the text of the first {@code title} element of a document.
 *
 * @param document the document to search
 * @return the title text, or empty string if the document has no {@code title} element
 */
public static String documentTitle(Document document) {
    return HttpConnection.firstElementText(document.getElementsByTag("title"));
}'''

HOP2 = '''/**
 * Get the text of the first of a list of elements, normalised and trimmed.
 * @param elements the elements
 * @return the text of the first element, or empty string if there are none
 */
public static String firstElementText(Elements elements) {
    Element first = elements.first();
    if (first == null)
        return "";
    return Node.trimmedText(first.text());
}'''

HOP3 = '''/**
 * Get a text with its whitespace normalised and trimmed.
 * @param text the text
 * @return the normalised and trimmed text
 */
public static String trimmedText(String text) {
    return Elements.spacedText(text).trim();
}'''

HOP4 = '''/**
 * Get a text with its whitespace normalised.
 * @param text the text
 * @return the normalised text
 */
public static String spacedText(String text) {
    return Evaluator.normalisedText(text);
}'''

DESIGN = {
 "instance": "Jsoup-29", "project": "Jsoup", "bug_id": 29, "seed": 8192,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": DOC, "class": "org.jsoup.nodes.Document", "method": "title", "near_line": 67},
 "facade_variant": "V2",
 "state_passed": "the receiver this (as org.jsoup.nodes.Document) to hop 1; no field read or written, no write-back",
 "reachability_probe": "DocumentTest::testTitles fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "org.jsoup.nodes.Document.title(Document.java:68) from DocumentTest.java:26; full suite with the probe: 8 "
                       "failing tests, all title() callers (DocumentTest::testTitles, HtmlParserTest::createsDocumentStructure, "
                       "::handlesUnclosedTitle, ::handlesUnclosedTitleAtEof, ParseTest::testYahooJp, ::testGoogleSearchIpod, "
                       "::testSmhBizArticle, ::testNewsHomepage)",
 "host_mode": "largest5",
 "host_lines": [1119, 661, 617, 536, 454],
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/DocumentTest.java",
             "test_class": "org.jsoup.nodes.DocumentTest", "test_method": "testTitles"},
 "expected_signature": "expected:<Hello there []now> but was:<Hello there [      ]now>",
 "gold": {"method": "normalisedText", "text": GOLD_TEXT,
          "fault": {"old": "            if (StringUtil.isWhitespace(c)) {\n"
                           "                if (sb.length() > 0 && sb.charAt(sb.length() - 1) == ' ')\n"
                           "                    continue;\n"
                           "                sb.append(' ');\n",
                    "new": "            if (StringUtil.isWhitespace(c)) {\n"
                           "                sb.append(' ');\n"}},
 "chain": {
   "facade_body": "return Element.documentTitle(this);",
   "lie": "The {@code head} is searched first, and the rest of the document only when the head holds no {@code title} element.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "documentTitle",
      "imports": ["org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "firstElementText",
      "imports": ["org.jsoup.nodes.Element", "org.jsoup.nodes.Node", "org.jsoup.select.Elements"], "text": HOP2},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "trimmedText",
      "imports": ["org.jsoup.select.Elements"], "text": HOP3},
     {"file": ELS, "class": "org.jsoup.select.Elements", "method": "spacedText", "imports": [], "text": HOP4},
     {"file": EV, "class": "org.jsoup.select.Evaluator", "method": "normalisedText",
      "imports": ["org.jsoup.helper.StringUtil"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.helper.StringUtil::normaliseWhitespace",
              "org.jsoup.nodes.TextNode::text",
              "org.jsoup.nodes.Element::text"],
 "ownership_reason": "Only the gold decides how whitespace is written; hop 1 only queries the document's title elements, hop 2 "
                     "picks the first and reads its text (\"\" when there is none), hop 3 trims the ends of what hop 4 returns, "
                     "and hop 4 passes the text along. The gold's javadoc promises the text with its whitespace normalised in "
                     "the same way as the text of an Element, which \"Hello there       now\" is not. No one-line change above "
                     "the gold that keeps to the hops' documentation restores the trigger: more trimming leaves the interior "
                     "whitespace, ownText() of a whitespace-preserving title is the same raw text, and select(\"title\") finds "
                     "the same element. The convention is pinned outside the gold: StringUtil.normaliseWhitespace writes a run "
                     "of whitespace as one space (StringUtilTest normaliseWhiteSpace: \"   hello   \\r \\n  there    \\n\" -> "
                     "\" hello there \"), TextNode.text returns 'normalised text' through it, and Element.text normalises the "
                     "text of an element and its children (ElementTest testNormalisesText: \"Hello There. Here is some text.\" "
                     "from text with ' \\n ' runs); the facade's own javadoc ('Trimmed title') is unchanged.",
 "ownership_tests": ["org.jsoup.helper.StringUtilTest::normaliseWhiteSpace",
                     "org.jsoup.nodes.ElementTest::testNormalisesText"],
 "compensating": {
   "chain": [
     {"file": EL, "old": "return HttpConnection.firstElementText(document.getElementsByTag(\"title\"));",
      "new": "return HttpConnection.firstElementText(document.select(\"title\"));",
      "why": "hop 1 finds the title elements with a selector query instead of the tag lookup"},
     {"file": HC, "old": "return Node.trimmedText(first.text());",
      "new": "return Node.trimmedText(first.ownText());",
      "why": "hop 2 reads the element's own text instead of its combined text"},
     {"file": ND, "old": "return Elements.spacedText(text).trim();",
      "new": "return Elements.spacedText(text.trim()).trim();",
      "why": "hop 3 trims the text before handing it on as well as after"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted: nodes.Element (hop 1, 1119 lines), helper.HttpConnection (hop 2, 661), nodes.Node (hop 3, 617; "
               "abstract, which does not affect a static method), select.Elements (hop 4, 536), select.Evaluator (hop 5, gold, "
               "454; abstract; the smallest host). All five are public top-level classes in which a static method compiles; the "
               "facade's file Document.java is excluded. Anchors from stageB_lib.pick_insertion_anchor with the instance seed "
               "8192 + 100 + i (as mr3_spec.py inserts them): hop 1 after `nodeName` (Element line idx 59, seed 8292), hop 2 "
               "after `followRedirects` (HttpConnection outer class, line idx 72, seed 8293), hop 3 after `remove` (Node line "
               "idx 249, seed 8294), hop 4 after `eq` (Elements line idx 431, seed 8295), hop 5: no admissible anchor in "
               "Evaluator (seed 8296), so the recipe appends the gold before the outer class's closing brace. The facade calls "
               "hop 1 as Element.documentTitle (same package; Document extends Element); each hop imports the next host where "
               "it is in another package.",
}
