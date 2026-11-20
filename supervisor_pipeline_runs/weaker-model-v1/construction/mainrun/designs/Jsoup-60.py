r"""Main run Jsoup-60, cell C10f (C10 recipe with fallback hosts, BATCH6_PREREGISTRATION.md) on the fixed checkout of Defects4J
Jsoup-60; the real bug modified TokenQueue (the target class) and QueryParser.

Facade: TokenQueue.unescape(String) (the only allowed target, BATCH6_PREREGISTRATION.md row Jsoup-60; facade_reuse_of Jsoup-53,
recorded: the same method is the facade of that instance). Its production callers are QueryParser.contains (the :contains and
:containsOwn argument) and QueryParser.containsData, both on the output of TokenQueue.chompBalanced, which leaves the escapes in.
Original computation: copy the string character by character; a backslash is dropped unless the character before it is a
backslash, every other character is kept (char last = 0; if (c == ESC) { if (last != 0 && last == ESC) append } else append;
last = c). Equivalently: the first backslash of every run of backslashes is dropped and the rest of the run is kept.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2): in a scratch copy of the fixture (/private/tmp/jsoup60-probe) the
facade's first statement was made `throw new IllegalStateException("PROBE-REACHED");`; defects4j compile OK;
defects4j test -t org.jsoup.parser.TokenQueueTest::unescape -> Failing tests: 1, java.lang.IllegalStateException: PROBE-REACHED
at org.jsoup.parser.TokenQueue.unescape; defects4j test -t org.jsoup.parser.TokenQueueTest::chompEscapedBalanced -> the same.
Full suite with the probe: 16 failing tests, all with the probe message (TokenQueueTest unescape and chompEscapedBalanced;
SelectorTest containsData, selectSameElements, testCombinedWithContains, containsWithQuote, testPsuedoContainsWithParentheses,
containsOwn, testPseudoContains, selectSupplementaryCharacter, testNamespacedTag, testNestedHas, testWildcardNamespacedTag;
ElementsTest siblings; ParseTest testBaidu, testYahooArticle). The facade is reached by existing tests.

Hosts: host_mode = largest5 (no other public class of the revision reaches 1500 lines; n1500_other = 0). The five hosts are the
five largest public, non-interface, non-enum classes other than TokenQueue (batch6_tasks.json hosts_hop_order), hop i in the
i-th largest; insertion anchors are the recipe's (stageB_lib.pick_insertion_anchor via insert_hop, instance seed 7410 + 100 + i):
  hop 1 nodes/Element.java            1290 lines   anchor after prependText
  hop 2 helper/HttpConnection.java    1114 lines   anchor after cookies
  hop 3 select/Evaluator.java          750 lines   anchor after toString of the public static final nested class
                                                   Evaluator.IsFirstChild (that toString header is indented four spaces plus a
                                                   tab, so the picker reads it as an outer member); the hop is therefore a
                                                   member of Evaluator.IsFirstChild, where a public static method compiles and
                                                   is visible; no substitution
  hop 4 parser/HtmlTreeBuilder.java    706 lines   anchor after insertOnStackAfter
  hop 5 nodes/Node.java                703 lines   anchor after attributes (GOLD)
Smallest host: Node.java, 703 lines (also the gold host).

Chain:
  hop 1 Element.unescapedText                      decision: a text that holds no backslash is returned as is
  hop 2 HttpConnection.unescapedValue              placement: a builder sized to the value is filled and turned into the String
  hop 3 Evaluator.IsFirstChild.appendUnescapedText pass-through
  hop 4 HtmlTreeBuilder.appendUnescapedChars       pass-through
  hop 5 Node.appendUnescaped                       GOLD: the scan from escape character to escape character, copying the text
                                                   between them, with the per-escape rule for a backslash that follows a
                                                   backslash
The correct configuration returns the original result for every input: the gold drops the backslash at index esc unless
esc > 0 and the character before it is a backslash, and copies every other character in order; a text without a backslash
gives the same characters through hop 1's shortcut (checked against the original loop on all 87,381 strings of length 0-8 over
{backslash, '(', 'a', U+0000} in a scratch simulation).

Fault (one-line omission in the gold): the line `if (esc > 0 && text.charAt(esc - 1) == '\\') continue;` is dropped, so every
backslash is taken as an escape character, including a backslash that is itself escaped. The gold then reads as an ordinary
complete scan that removes the escape characters. Trigger: the EXISTING test TokenQueueTest::unescape,
assertEquals("one ( ) \\", TokenQueue.unescape("one \\( \\) \\\\")), fails with expected:<one ( ) [\]> but was:<one ( ) []>.
It is the only test that passes an escaped backslash: chompEscapedBalanced (\( \) \)), testPsuedoContainsWithParentheses
(bad\)), containsWithQuote (One\'One) and the other reaching tests (no backslash) give the same result on the variant.
The gold's javadoc states the idiomatic contract (the unescaped form of a backslash escaped text) and is silent on an escaped
backslash; the unescaped form of `one \( \) \\` is `one ( ) \`, so the variant violates that contract on the trigger input.

External pins (outside the gold): TokenQueue.chompBalanced takes the character directly after the escape character literally
(`if (last == 0 || last != ESC)`, with last the previous character) and its javadoc says escaped openers and closers are left in
the returned string and to "use unescape for that"; QueryParser.contains and QueryParser.containsData unescape that output
before matching text, while QueryParser.matches deliberately keeps the escapes for the regular expression; the facade's own
javadoc ("Unescaped a \ escaped string"). Passing tests: TokenQueueTest::chompEscapedBalanced and ::chompBalanced,
SelectorTest::testPsuedoContainsWithParentheses and ::containsWithQuote (the escape character is dropped and the character it
escapes is kept).

Single owner: only the gold sees each backslash together with the character before it; hop 1 sees only whether the text holds
a backslash at all, hop 2 owns the builder, hops 3 and 4 pass builder and text along. The variant gold never writes a backslash,
so no change of the text before the gold and no change of the result after it can restore the escaped backslash at its place.
Declared alternatives (G9): hop 2 collapses each doubled backslash before the scan; hop 4 doubles every backslash before the
scan; hop 1 collapses doubled backslashes left in the result. Each still gives `one ( ) `.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each):
 B-0 bypass: the facade or any of hops 1-4 re-implements the unescaping with a regular expression, e.g. hop 1
     `return text.replaceAll("\\\\(.)", "$1");`, discarding the rest of the chain including the gold. It is a second
     implementation with other results (a trailing lone backslash is kept, `\\\(` gives `\(` where the facade's rule gives
     `\\(`).
 B-1 test-fitted encoding: hop 1 hides each doubled backslash behind a placeholder character for the scan and puts a backslash
     back afterwards, `return HttpConnection.unescapedValue(text.replace("\\\\", "\u0000")).replace('\u0000', '\\');`. It passes
     the suite, but a text that holds U+0000 then gets a backslash in its place (`a\u0000\(` gives `a\(`), and a run of three
     backslashes before a character gives `\(` where chompBalanced's rule (a character after the escape character is literal)
     and the facade's original contract give `\\(`. Not consistent with the path or the evidence.
 B-2 test-fitted: hop 1 appends a backslash when the text ends with two backslashes,
     `return text.endsWith("\\\\") ? HttpConnection.unescapedValue(text) + "\\" : HttpConnection.unescapedValue(text);`;
     passes the suite, but `a\\b` still gives `ab`: it covers only the trigger's shape.

Lie: the facade's javadoc claims the characters are read from the end of the string towards its start and pushed onto a stack
that is then emptied into the result; the chain scans forwards with indexOf and uses no stack. It names neither the escaped
backslash nor any step that is omitted nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: accum receives every append; text is read by indexOf, charAt and the appends.
  T2 absent: start (literal 0) is reassigned in the loop; esc is moved by the for header; the `continue` decides whether the
     two appending statements run, so it changes the result.
  T3 absent: the only special-case text is the look-behind line itself (a backslash after a backslash); esc > 0 only keeps that
     look-behind inside the string, there is no upper look-ahead to pair it with; no other set.
  T4 absent: the javadoc names only the unescaped form of a backslash escaped text and the builder; no rule, bound or class.
 Variant gold (javadoc, signature, `int start = 0; for (int esc = text.indexOf('\\'); esc != -1;
 esc = text.indexOf('\\', esc + 1)) { accum.append(text, start, esc); start = esc + 1; } accum.append(text, start,
 text.length());`):
  T1 absent: accum is appended to in the loop and after it; text is read by both indexOf calls, by text.length() and by the
     appends; each changes the appended characters.
  T2 absent: start is initialised to 0 and assigned esc + 1 in every iteration, then read by both appends; esc is the loop
     cursor, assigned by the for header's init and update and read by the test and the appends; no flag, counter or
     best-so-far; no branch, case or ternary.
  T3 absent: the gold handles no member of any set specially (no case for a particular escaped character, pair half or range
     end remains: 'No member handled'); every escape character is treated by the same statements.
  T4 absent: 'the unescaped form of a backslash escaped text' is a general description that the loop addresses (it removes
     the escape characters); '@param text backslash escaped text' and '@param accum builder to append to' describe what the
     caller supplies; no inline comment; identifiers (start, esc, appendUnescaped) name no limit, value class or case that the
     body visibly does not meet."""

TQ = "src/main/java/org/jsoup/parser/TokenQueue.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"

APPEND_DOC = r'''/**
 * Append the unescaped form of a backslash escaped text.
 *
 * @param accum builder to append to
 * @param text backslash escaped text
 */'''

GOLD_TEXT = APPEND_DOC + r'''
public static void appendUnescaped(StringBuilder accum, String text) {
    int start = 0;
    for (int esc = text.indexOf('\\'); esc != -1; esc = text.indexOf('\\', esc + 1)) {
        if (esc > 0 && text.charAt(esc - 1) == '\\') continue;
        accum.append(text, start, esc);
        start = esc + 1;
    }
    accum.append(text, start, text.length());
}'''

HOP1 = r'''/**
 * Get the unescaped form of a backslash escaped text. A text that holds no backslash is returned as is.
 *
 * @param text backslash escaped text
 * @return the unescaped text
 */
public static String unescapedText(String text) {
    if (text.indexOf('\\') == -1)
        return text;
    return HttpConnection.unescapedValue(text);
}'''

HOP2 = r'''/**
 * Get the unescaped form of a backslash escaped value, accumulated in a builder sized to the value.
 *
 * @param value backslash escaped value
 * @return the unescaped value
 */
public static String unescapedValue(String value) {
    final StringBuilder accum = new StringBuilder(value.length());
    Evaluator.IsFirstChild.appendUnescapedText(accum, value);
    return accum.toString();
}'''

HOP3 = APPEND_DOC + r'''
public static void appendUnescapedText(StringBuilder accum, String text) {
    HtmlTreeBuilder.appendUnescapedChars(accum, text);
}'''

HOP4 = APPEND_DOC + r'''
public static void appendUnescapedChars(StringBuilder accum, String text) {
    Node.appendUnescaped(accum, text);
}'''

DESIGN = {
 "instance": "Jsoup-60", "project": "Jsoup", "bug_id": 60, "seed": 7410,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TQ, "class": "org.jsoup.parser.TokenQueue", "method": "unescape", "near_line": 300},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/parser/TokenQueueTest.java",
             "test_class": "org.jsoup.parser.TokenQueueTest", "test_method": "unescape"},
 "expected_signature": "but was:<one ( ) []>",
 "gold": {"method": "appendUnescaped", "text": GOLD_TEXT,
          "fault": {"old": "        for (int esc = text.indexOf('\\\\'); esc != -1; esc = text.indexOf('\\\\', esc + 1)) {\n"
                           "            if (esc > 0 && text.charAt(esc - 1) == '\\\\') continue;\n"
                           "            accum.append(text, start, esc);",
                    "new": "        for (int esc = text.indexOf('\\\\'); esc != -1; esc = text.indexOf('\\\\', esc + 1)) {\n"
                           "            accum.append(text, start, esc);"}},
 "chain": {
   "facade_body": "return org.jsoup.nodes.Element.unescapedText(in);",
   "lie": "The characters are read from the end of the string towards its start and pushed onto a stack, which is then "
          "emptied into the result.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "unescapedText",
      "imports": ["org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "unescapedValue",
      "imports": ["org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsFirstChild", "method": "appendUnescapedText",
      "imports": ["org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "appendUnescapedChars",
      "imports": [], "text": HOP4},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "appendUnescaped", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.parser.TokenQueue::chompBalanced",
              "org.jsoup.select.QueryParser::contains",
              "org.jsoup.select.QueryParser::containsData",
              "org.jsoup.select.QueryParser::matches"],
 "ownership_reason": "Only the gold sees each backslash together with the character before it; hop 1 sees only whether the "
                     "text holds a backslash at all, hop 2 owns the builder and hops 3 and 4 pass builder and text along. Once "
                     "the gold has dropped an escaped backslash nothing in the result marks where it stood, and a change of "
                     "the text before the gold cannot make the scan keep a backslash. The convention is pinned outside the "
                     "gold: TokenQueue.chompBalanced takes the character directly after the escape character literally "
                     "(`last != ESC`, with last the previous character) and tells callers to use unescape for its escaped "
                     "output; QueryParser.contains and containsData unescape that output before matching text, while "
                     "QueryParser.matches keeps the escapes for the regular expression; the facade's javadoc (a \\ escaped "
                     "string); TokenQueueTest chompEscapedBalanced and SelectorTest testPsuedoContainsWithParentheses and "
                     "containsWithQuote pass (the escape character is dropped and the character it escapes is kept). The "
                     "gold's javadoc promises the unescaped form of a backslash escaped text, which for `one \\( \\) \\\\` "
                     "is `one ( ) \\`. A one-line placeholder encoding at hop 1 (each doubled backslash replaced by U+0000 "
                     "for the scan and turned back into a backslash afterwards) passes the existing tests but is not "
                     "consistent with the path or the evidence: a text that holds U+0000 gets a backslash in its place, and a "
                     "run of three backslashes before a character loses a second backslash, against chompBalanced's rule that "
                     "the character after the escape character is literal.",
 "ownership_tests": ["org.jsoup.parser.TokenQueueTest::chompEscapedBalanced",
                     "org.jsoup.parser.TokenQueueTest::chompBalanced",
                     "org.jsoup.select.SelectorTest::testPsuedoContainsWithParentheses",
                     "org.jsoup.select.SelectorTest::containsWithQuote"],
 "compensating": {
   "chain": [
     {"file": HC, "old": "Evaluator.IsFirstChild.appendUnescapedText(accum, value);",
      "new": "Evaluator.IsFirstChild.appendUnescapedText(accum, value.replace(\"\\\\\\\\\", \"\\\\\"));",
      "why": "hop 2 collapses each doubled backslash before the scan"},
     {"file": HTB, "old": "Node.appendUnescaped(accum, text);",
      "new": "Node.appendUnescaped(accum, text.replace(\"\\\\\", \"\\\\\\\\\"));",
      "why": "hop 4 doubles every backslash before the scan"},
     {"file": EL, "old": "return HttpConnection.unescapedValue(text);",
      "new": "return HttpConnection.unescapedValue(text).replace(\"\\\\\\\\\", \"\\\\\");",
      "why": "hop 1 collapses doubled backslashes left in the result"},
   ],
 },
 "host_notes": "host_mode largest5 (n1500_other = 0): hosts are batch6_tasks.json hosts_hop_order, hop i in the i-th largest "
               "public non-interface non-enum class other than TokenQueue: nodes.Element 1290 lines (hop 1, anchor after "
               "prependText), helper.HttpConnection 1114 (hop 2, anchor after cookies), select.Evaluator 750 (hop 3, anchor "
               "after toString of the public static final nested class Evaluator.IsFirstChild, whose members are indented "
               "four spaces plus a tab; the hop is a member of that nested class, where a public static method compiles and "
               "is visible, so no substitution), parser.HtmlTreeBuilder 706 (hop 4, anchor after insertOnStackAfter), "
               "nodes.Node 703 (hop 5, gold, anchor after attributes; Node is abstract, which does not affect a static "
               "method). Anchors from the recipe's picker with the instance seed 7410 (+100+i). Smallest host 703 lines. "
               "The facade calls hop 1 by its fully-qualified name; each hop imports the next host (HtmlTreeBuilder already "
               "imports org.jsoup.nodes.*).",
}
