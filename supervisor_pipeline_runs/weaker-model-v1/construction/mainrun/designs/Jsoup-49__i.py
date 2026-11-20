"""Main run Jsoup-49__i (cell C10i, batch 9, sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Jsoup-49; the real bug modified org.jsoup.nodes.Node, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE.md
section 1: pool v2 found no tested public static method in Node).

Facade: Node.absUrl(String) (the only allowed candidate of the task record, facade_planned_by null, no facade reuse).
Original computation of the facade: Validate.notEmpty(attributeKey); if the node has no such attribute (hasAttr), "" ("nothing to
make absolute with"); otherwise StringUtil.resolve(baseUri, attr(attributeKey)): parse the base URI as a java.net.URL; if that
fails, try the attribute value as an absolute URL on its own (or "" if that fails too); otherwise a value that starts with "?" is
prefixed with the base URL's path, a value that starts with "." against a base whose file does not start with "/" gets a base whose
file is "/" + file, and the result is new URL(base, value).toExternalForm(); any MalformedURLException gives "".

facade_variant: V2 (receiver as parameter). The computation needs the node's public methods hasAttr(String) and attr(String),
which subclasses override (TextNode creates its attributes on first access), and its base URI: the facade keeps the argument guard
and passes `this` (typed as the declaring class Node) and the key to hop 1; hop 1 calls node.hasAttr, node.attr and node.baseUri()
(public; returns the package-private field baseUri that the original read, and is overridden nowhere). No private method is called
(no V4), no package-private type passes through the hops (no V3/V5), nothing is written back (the original writes no field). No
signature, modifier, override or throws change; no new type; no reflection; no test edit.
state_passed: the receiver `this` (as Node) and the attribute key to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-49-probe/w of the fixture,
the first statement of absUrl was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)` only
keeps the rest of the body reachable for javac). `defects4j test -t org.jsoup.nodes.NodeTest::absHandlesRelativeQuery`: 1 failing
test, java.lang.IllegalStateException: PROBE-REACHED at org.jsoup.nodes.Node.absUrl(Node.java:180) called from
NodeTest.absHandlesRelativeQuery(NodeTest.java:122). Full suite with the probe: 36 failing tests (absUrl is also reached through
attr("abs:..."), hasAttr("abs:...") and the Cleaner's Whitelist protocol test). The facade is reached by existing tests directly.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of batch9_tasks.json, in that order, none substituted; the five largest
public, non-interface, non-enum classes other than Node.java). Anchors from stageB_lib.pick_insertion_anchor with the instance seed
8633 + 100 + i, as mr3_spec.py inserts them:
  hop 1 nodes.Element             1223 lines  absoluteAttr     the attribute guard (no such attribute gives ""), then the node's
                                                               base URI and the attribute value are handed on (placement step)
  hop 2 helper.HttpConnection      977 lines  absoluteUrl      pass-through
  hop 3 select.Evaluator           707 lines  absoluteUrlFor   pass-through (the seeded anchor is the constructor
                                                               CssNthEvaluator(int) of the public static nested class
                                                               Evaluator.CssNthEvaluator, so the hop is a static method of that
                                                               nested class; called as Evaluator.CssNthEvaluator.absoluteUrlFor)
  hop 4 parser.HtmlTreeBuilder     703 lines  absoluteHref     pass-through
  hop 5 safety.Whitelist           635 lines  absoluteLink     GOLD: parse the base URI, the fallback to the link on its own,
                                                               the two adjustments of java.net.URL's relative reading, and the
                                                               resolution itself
Host newline counts 1223, 977, 707, 703, 635; the smallest host is Whitelist (635 lines), which is also the gold host.
The correct configuration returns exactly the original String for every node and key: hop 1 is the original's hasAttr guard and
attr/baseUri reads (virtual calls on the same receiver), hops 2-4 hand the two Strings on, and the gold is the computation of
StringUtil.resolve(String, String) and StringUtil.resolve(URL, String) on the same two Strings.

Fault (one-line omission of a special-case step in the gold): the step that gives a query-only link ("?foo") the path of the base
URL before java.net.URL reads it is dropped, so java.net.URL (RFC 2396 reading) drops the last path segment of the base:
"?foo" against http://jsoup.org/path/file?bar becomes http://jsoup.org/path/?foo instead of http://jsoup.org/path/file?foo. The
gold then reads as the ordinary routine "parse the base, fall back to the link alone, adjust a dot link against a base without a
leading slash, resolve". Trigger: the EXISTING test NodeTest::absHandlesRelativeQuery (line 122,
assertEquals("http://jsoup.org/path/file?foo", a1.absUrl("href"))). It is the only test that newly fails (no other test resolves
a query-only link through Node.absUrl; StringUtil.resolve, used by HttpConnection's redirect handling, is untouched).

The gold's javadoc states the idiomatic contract (the link is made absolute by reading it relative to the base URI; a base URI that
is not a URL makes the link be tried on its own; "" when no URL can be made) and is silent on query-only links; a query-only
reference read relative to http://jsoup.org/path/file?bar keeps the path /path/file. The convention is pinned outside the gold:
StringUtil.resolve(URL, String) does the same step ("java resolves '//path/file + ?foo' to '//path/?foo', not '//path/file?foo' as
desired": relUrl = base.getPath() + relUrl) and StringUtil.resolve(String, String) is its String entry point, used by
HttpConnection.Response.execute for redirect locations; Node.absUrl's own javadoc (unchanged) says the value is "treated as a URL
relative to the element's baseUri, and made absolute using that"; passing tests: StringUtilTest::resolvesRelativeUrls (the
sibling resolver's adjustments for java.net.URL), NodeTest::absHandlesDotFromIndex (the dot adjustment through the chain),
NodeTest::handlesBaseUri and ElementTest::testRelativeUrls.

Single owner: only the gold parses the base URI and resolves the link; hop 1 only answers a missing attribute with "" and hops 2-4
pass the base URI and the link on as they stand (their javadoc: "@param link the link, as written in the attribute"). The path of
the base URL is known only to the gold (java.net.URL parsing throws a checked MalformedURLException that no plumbing hop declares
or catches). Declared alternatives (G9), each leaves the trigger failing: hop 1 hands on the base URI without its query (java.net.URL
still drops the last segment for "?foo"); hop 2 prefixes a query-only link with the whole base URI (keeps the base's own query,
http://jsoup.org/path/file?bar?foo); hop 4 prefixes a query-only link with "./" (still read against the directory /path/).
Recorded bypasses (edits that replace the gold's work with another implementation, not repairs of the chain):
 B-1 string surgery at a plumbing hop that re-derives the base URL's path from the text of the base URI, e.g. at hop 3
     `return HtmlTreeBuilder.absoluteHref(baseUri, link.startsWith("?") ? baseUri.replaceFirst("[?#].*$", "") + link : link);`:
     it hands the next hop an absolute URL in place of the link as written in the attribute (against hop 4's and the gold's
     @param link), and re-implements the gold's step outside URL parsing; the gold still mis-reads a query-only link.
     Checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests.
 B-0 a hop (or the facade) returning StringUtil.resolve(baseUri, link), the facade's original computation, makes the gold dead.

Lie: the facade's javadoc claims the attribute value is first percent-decoded and split at each slash, and the segments are then
appended one by one to the directory of the base URI; the chain decodes nothing and splits nothing (java.net.URL reads the value
as a whole). It names neither queries, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: baseUri is parsed into base (the main computation's context); link is tried on its own, adjusted and resolved;
     neither is only argument-checked (the gold has no argument check).
  T2 absent: base is assigned by the parse, read by both adjustments and by the resolution, and reassigned by the dot adjustment;
     link is reassigned by the query adjustment and read by the resolution; no literal-initialised local, no loop, cursor,
     counter, flag or best-so-far; each decision changes the URL that is resolved.
  T3 absent: two adjustments keyed on the first character of the link ("?" and ".") are not a closed set fixed by the gold's
     text, a Java type or a named format (the gold names no format or class of references); base and link do not have the same
     role (context versus reference), so they are not a two-member set; no enum or type code.
  T4 absent: 'Makes a link absolute by reading it relative to a base URI' is a general description that the resolution line
     addresses; 'If the base URI is not itself a URL, the link is tried on its own' is met by the inner catch;
     '@return the absolute URL, or an empty string if one could not be made' by the outer catch; the @param clauses are caller
     descriptions; no inline comment; identifiers base and link name what they hold.
 Variant gold (javadoc, signature, parse with the fallback, the dot adjustment, the resolution, the empty-string catch):
  T1 absent: baseUri is parsed into base and is the context of the resolution; link is tried on its own, tested by the dot
     adjustment and resolved; both decide the return value.
  T2 absent: base is assigned by the parse, read by the dot decision and the resolution and reassigned by the dot adjustment;
     link is read by the fallback, the decision and the resolution (a parameter not reassigned is not a local the gold moves);
     no literal-initialised local, no loop; the dot decision changes the base that is resolved.
  T3 absent: exactly one adjustment remains (a dot link against a base whose file has no leading slash), one member of an
     unnamed set of link forms ('One member of a larger unnamed set'); the gold's text names no class of links or references
     ("relative", "query", "dot segment", "RFC") that it handles in part; base and link are context and reference, not a pair.
  T4 absent: as for the correct gold; the javadoc names no query, path or special link form, and no inline comment exists."""

NODE = "src/main/java/org/jsoup/nodes/Node.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
WL = "src/main/java/org/jsoup/safety/Whitelist.java"

GOLD_TEXT = '''/**
 * Makes a link absolute by reading it relative to a base URI. If the base URI is not itself a URL, the link is tried
 * on its own.
 *
 * @param baseUri the base URI the link is read against
 * @param link the link, as written in the attribute
 * @return the absolute URL, or an empty string if one could not be made
 */
public static String absoluteLink(String baseUri, String link) {
    try {
        URL base;
        try {
            base = new URL(baseUri);
        } catch (MalformedURLException e) {
            return new URL(link).toExternalForm();
        }
        if (link.startsWith("?"))
            link = base.getPath() + link;
        if (link.indexOf('.') == 0 && base.getFile().indexOf('/') != 0)
            base = new URL(base.getProtocol(), base.getHost(), base.getPort(), "/" + base.getFile());
        return new URL(base, link).toExternalForm();
    } catch (MalformedURLException e) {
        return "";
    }
}'''

HOP1 = '''/**
 * Get an absolute URL from a URL attribute of a node, which may be relative.
 *
 * @param node the node that holds the attribute
 * @param attributeKey the attribute key
 * @return an absolute URL, or an empty string if the attribute is missing or could not be made into a URL
 */
public static String absoluteAttr(Node node, String attributeKey) {
    if (!node.hasAttr(attributeKey)) {
        return "";
    }
    return HttpConnection.absoluteUrl(node.baseUri(), node.attr(attributeKey));
}'''

HOP2 = '''/**
 * Make a link absolute against the base URI of the node it is on.
 * @param baseUri the base URI of the node
 * @param link the link, as written in the attribute
 * @return the absolute URL, or an empty string if one could not be made
 */
public static String absoluteUrl(String baseUri, String link) {
    return Evaluator.CssNthEvaluator.absoluteUrlFor(baseUri, link);
}'''

HOP3 = '''/**
 * Gets the absolute URL of a link, read against a base URI.
 * @param baseUri the base URI
 * @param link the link, as written in the attribute
 * @return the absolute URL, or an empty string if one could not be made
 */
public static String absoluteUrlFor(String baseUri, String link) {
    return HtmlTreeBuilder.absoluteHref(baseUri, link);
}'''

HOP4 = '''/**
 * Gets the absolute form of a link, against the base URI of the document.
 * @param baseUri the base URI
 * @param link the link, as written in the attribute
 * @return the absolute URL, or an empty string if one could not be made
 */
public static String absoluteHref(String baseUri, String link) {
    return Whitelist.absoluteLink(baseUri, link);
}'''

DESIGN = {
 "instance": "Jsoup-49", "project": "Jsoup", "bug_id": 49, "seed": 8633,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "absUrl", "near_line": 179},
 "facade_variant": "V2",
 "state_passed": "the receiver this (as org.jsoup.nodes.Node) and the attribute key to hop 1; hop 1 calls node.hasAttr, node.attr "
                 "and node.baseUri(); no write-back",
 "reachability_probe": "NodeTest::absHandlesRelativeQuery fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "org.jsoup.nodes.Node.absUrl(Node.java:180) from NodeTest.java:122; full suite with the probe: 36 failing "
                       "tests",
 "host_mode": "largest5",
 "host_lines": [1223, 977, 707, 703, 635],
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/NodeTest.java",
             "test_class": "org.jsoup.nodes.NodeTest", "test_method": "absHandlesRelativeQuery"},
 "expected_signature": "jsoup.org/path/[file]?foo> but was:<...tp://jsoup.org/path/[]?foo>",
 "gold": {"method": "absoluteLink", "text": GOLD_TEXT,
          "fault": {"old": "            if (link.startsWith(\"?\"))\n"
                           "                link = base.getPath() + link;\n"
                           "            if (link.indexOf('.') == 0 && base.getFile().indexOf('/') != 0)\n",
                    "new": "            if (link.indexOf('.') == 0 && base.getFile().indexOf('/') != 0)\n"}},
 "chain": {
   "facade_body": "Validate.notEmpty(attributeKey);\n\n"
                  "        return Element.absoluteAttr(this, attributeKey);",
   "lie": "The attribute value is first percent-decoded and split at each slash, and the segments are then appended one by one "
          "to the directory of the base URI.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "absoluteAttr",
      "imports": ["org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "absoluteUrl",
      "imports": ["org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator.CssNthEvaluator", "method": "absoluteUrlFor",
      "imports": ["org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "absoluteHref",
      "imports": ["org.jsoup.safety.Whitelist"], "text": HOP4},
     {"file": WL, "class": "org.jsoup.safety.Whitelist", "method": "absoluteLink",
      "imports": ["java.net.MalformedURLException", "java.net.URL"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.helper.StringUtil::resolve",
              "org.jsoup.helper.HttpConnection.Response::execute",
              "org.jsoup.nodes.Node::absUrl"],
 "ownership_reason": "Only the gold parses the base URI and resolves the link; hop 1 answers a missing attribute with \"\" and "
                     "hands on the node's base URI and the attribute value, and hops 2-4 pass them on as they stand (their "
                     "javadoc: the link, as written in the attribute). The gold promises to make the link absolute by reading "
                     "it relative to the base URI, which http://jsoup.org/path/?foo is not for the query-only link ?foo against "
                     "http://jsoup.org/path/file?bar. The path of the base URL is known only inside the gold (parsing a URL "
                     "throws a checked MalformedURLException that no plumbing hop declares or catches); stripping the base's "
                     "query, prefixing the whole base URI or a \"./\" upstream all leave java.net.URL reading the link against "
                     "the directory /path/. The convention is pinned outside the gold: StringUtil.resolve(URL, String) gives a "
                     "link starting with \"?\" the base URL's path before java.net.URL reads it (its comment: java resolves "
                     "'//path/file + ?foo' to '//path/?foo', not '//path/file?foo' as desired), StringUtil.resolve(String, "
                     "String) is its String entry point and HttpConnection.Response.execute resolves redirect locations "
                     "with it; Node.absUrl's javadoc says the value is treated as a URL relative to the element's baseUri and "
                     "made absolute using that; StringUtilTest resolvesRelativeUrls pins the sibling resolver's adjustments "
                     "of java.net.URL, and NodeTest absHandlesDotFromIndex, handlesBaseUri and ElementTest testRelativeUrls "
                     "pass through the chain.",
 "ownership_tests": ["org.jsoup.helper.StringUtilTest::resolvesRelativeUrls",
                     "org.jsoup.nodes.NodeTest::absHandlesDotFromIndex",
                     "org.jsoup.nodes.NodeTest::handlesBaseUri",
                     "org.jsoup.nodes.ElementTest::testRelativeUrls"],
 "compensating": {
   "chain": [
     {"file": EL, "old": "return HttpConnection.absoluteUrl(node.baseUri(), node.attr(attributeKey));",
      "new": "return HttpConnection.absoluteUrl(node.baseUri().replaceFirst(\"[?#].*$\", \"\"), node.attr(attributeKey));",
      "why": "hop 1 hands on the base URI without its query"},
     {"file": HC, "old": "return Evaluator.CssNthEvaluator.absoluteUrlFor(baseUri, link);",
      "new": "return Evaluator.CssNthEvaluator.absoluteUrlFor(baseUri, link.startsWith(\"?\") ? baseUri + link : link);",
      "why": "hop 2 prefixes a query-only link with the base URI"},
     {"file": HTB, "old": "return Whitelist.absoluteLink(baseUri, link);",
      "new": "return Whitelist.absoluteLink(baseUri, link.startsWith(\"?\") ? \"./\" + link : link);",
      "why": "hop 4 reads a query-only link as a path relative to the current directory"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted: nodes.Element (hop 1, 1223 lines), helper.HttpConnection (hop 2, 977), select.Evaluator (hop 3, 707), "
               "parser.HtmlTreeBuilder (hop 4, 703), safety.Whitelist (hop 5, gold, 635; the smallest host). All five are public "
               "top-level classes in which a static method compiles (Evaluator is abstract, which does not affect a static "
               "method). Anchors from stageB_lib.pick_insertion_anchor with seed 8633 + 100 + i (as mr3_spec.py inserts them): "
               "hop 1 after `children` (line idx 207, seed 8733), hop 2 after `parser` (196, 8734), hop 3 after the constructor "
               "`CssNthEvaluator(int)` (413, 8735), hop 4 after `clearFormattingElementsToLastMarker` (638, 8736), hop 5 after "
               "`removeProtocols` (477, 8737). The hop-3 anchor lies inside the public static abstract nested class "
               "Evaluator.CssNthEvaluator, so hop 3 is a public static method of that nested class (called as "
               "Evaluator.CssNthEvaluator.absoluteUrlFor); hops 1, 2, 4 and 5 are in the outer classes. The facade calls hop 1 "
               "as Element.absoluteAttr (same package); each hop imports the next host; the gold imports java.net.URL and "
               "java.net.MalformedURLException. The facade's class Node is not a host.",
}
