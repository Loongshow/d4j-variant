r"""Main run Jsoup-53, cell C10f (batch 6; C10 recipe with fallback hosts on the fixed checkout of Defects4J Jsoup-53; the real
bug modified TokenQueue, the target class).

Facade: TokenQueue.unescape(String) (the only allowed target, BATCH6_PREREGISTRATION.md row 179; facade_reuse_of: none).
Original computation of the facade: every character of the string is copied in order, except a backslash, which is copied
only when the character before it is a backslash (so a backslash escape drops its backslash and keeps the escaped character,
and an escaped backslash gives one backslash). The original had no argument guard (a null string throws a
NullPointerException from toCharArray), so the facade body is the one delegating call.

reachability_probe: in a scratch copy of the fixture (/private/tmp/d4j-mr-Jsoup-53-probe, deleted afterwards) the facade's
first statement was made `if (true) throw new IllegalStateException("PROBE-REACHED");` (an unconditional throw would make the
rest of the body unreachable and not compile); defects4j compile OK; full suite (defects4j test): 12 failing tests, all 12 with
java.lang.IllegalStateException: PROBE-REACHED: TokenQueueTest::unescape, TokenQueueTest::chompEscapedBalanced,
SelectorTest::{selectSameElements, testCombinedWithContains, testPsuedoContainsWithParentheses, containsOwn, testPseudoContains,
selectSupplementaryCharacter, testNamespacedTag, testNestedHas}, ParseTest::{testBaidu, testYahooArticle}. The facade is reached
by existing tests (directly by TokenQueueTest, and through QueryParser.contains for every :contains / :containsOwn selector).

Hosts (host_mode = largest5: the fixed revision has 0 other public classes of >= 1500 lines; the five largest public
non-interface non-enum classes other than TokenQueue, task record hosts_hop_order, newline counts):
  hop 1 nodes/Element.java         1237 lines   anchor after `html`        (seed 5841)
  hop 2 helper/HttpConnection.java 1016 lines   anchor after `data`        (seed 5842)
  hop 3 select/Evaluator.java       706 lines   anchor after `matches`     (seed 5843) -> lands in nested class CssNthEvaluator
  hop 4 parser/HtmlTreeBuilder.java 702 lines   anchor after `insertForm`  (seed 5844)
  hop 5 nodes/Node.java             694 lines   anchor after `parent`      (seed 5845)   GOLD
  smallest host: 694 lines (Node, the gold host). Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with
  seed 5741 + 100 + i, the same call mr2_spec.py makes; none skipped, no substitution.

Chain (redistribution of the original computation):
  facade TokenQueue.unescape(in)                                       one delegating call
  hop 1 Element.unescapedText(escaped)                                 plumbing: the characters of the string taken as a char array
  hop 2 HttpConnection.unescapedValue(chars)                           placement: a builder sized to the sequence collects the
                                                                       value, returned as a String
  hop 3 Evaluator.CssNthEvaluator.appendUnescapedArgument(chars, accum)  pass-through
  hop 4 HtmlTreeBuilder.appendUnescapedCharacters(chars, accum)        pass-through
  hop 5 Node.appendUnescaped(chars, accum)                             GOLD: the per-character core, written as a copy of the
                                                                       runs between the backslashes that are dropped
The correct configuration returns the original result for every input: a backslash is dropped exactly when it is the first
character or follows a character that is not a backslash (the original's `c == ESC` without `last == ESC`), every other
character is copied in order (the runs between dropped backslashes, then the tail). For example `\\\` (three
backslashes) gives two, as in the original.

Fault (one-line omission in the gold): the conjunct line `&& (i == 0 || chars[i - 1] != '\\')` is dropped, so every
backslash ends a run and is left out, including one that follows a backslash. Trigger: the EXISTING test
TokenQueueTest::unescape, assertEquals("one ( ) \\", TokenQueue.unescape("one \\( \\) \\\\")) fails with
expected:<one ( ) [\]> but was:<one ( ) []>. It is the only test that passes an escaped backslash: chompEscapedBalanced
(`\(`, `\)`), SelectorTest testPsuedoContainsWithParentheses (`\)`) and the other :contains tests (no backslash) still pass.

The gold's javadoc states the idiomatic contract (the unescaped text of a backslash escaped character sequence; the facade's own
wording "Unescaped a \ escaped string") and is silent on the backslash that follows a backslash. The unescaped text of
`one \( \) \\` is `one ( ) \`, so the variant violates that contract on the trigger input.

External pins (outside the gold): TokenQueue.chompBalanced takes the character after a backslash literally (`last != ESC`)
and its javadoc says those escapes are left in its result and points to unescape for contains text; QueryParser.contains
unescapes chompBalanced's output for :contains(text) (SelectorTest::testPsuedoContainsWithParentheses: `bad\)` selects
"This is bad)"); QueryParser.matches deliberately keeps the escapes for java.util.regex, in which a doubled backslash stands for
one literal backslash; TokenQueueTest::chompEscapedBalanced asserts the unescaped form of an escaped argument. All pass on
the variant.

Single owner: the variant gold never appends a backslash, so no change of its input can make the result contain one; only the
gold sees each backslash together with the character before it. Hops 1 and 2 hold the whole string and the finished value,
hops 3 and 4 only pass the sequence and the builder along. Declared alternatives (G9), none of which changes the trigger
result: hop 1 collapses each pair of backslashes before the conversion; hop 4 doubles every backslash before the call; hop 3
drops a trailing backslash of the argument.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each):
 B-0 bypass: the facade (its original body) or any hop above the gold returns another implementation, e.g. hop 1
     `return escaped.replaceAll("\\\\(.)", "$1");` (regular expression: a backslash and the character after it become that
     character), discarding the rest of the chain including the gold.
 B-1 test-fitted: hop 1 maps each pair of backslashes to a backslash and a private-use character before the conversion and maps
     that character back to a backslash afterwards
     (`return HttpConnection.unescapedValue(escaped.replace("\\\\", "\\\uE000").toCharArray()).replace('\uE000', '\\');`).
     It breaks hop 1's documented conversion (the characters of the string taken as a char array), any string that contains
     U+E000, and three backslashes then give one instead of two.
 B-2 test-fitted: hop 2 appends a backslash when the sequence ends with two backslashes
     (`return chars.length > 1 && chars[chars.length - 1] == '\\' && chars[chars.length - 2] == '\\' ? accum.append('\\').toString() : accum.toString();`):
     only a trailing pair is answered, so `a\\b` still gives `ab`.
 B-3 (not run; a second implementation of the gold's decision): a hop handles the first pair of backslashes itself and
     recurses around the gold on one long line (the part before the pair through the chain, one backslash, then the rest
     through itself); on the trigger input the pair never reaches the gold, and three backslashes give one instead of two.

Lie: the facade's javadoc claims the string is read from its last character back to its first and its characters are pushed
onto a stack that is then emptied into the result; the chain reads forward and uses no stack. It names neither backslash pairs
nor any step that is omitted nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: chars gives the bound, every tested character and the appended runs; accum receives every run.
  T2 absent: start (literal 0) is reassigned in the loop (start = i + 1) and bounds every append; i is advanced by the for
     header; the if has an effect (a run is appended and start moves) and its fall-through has none, so it decides; no flag,
     counter or best-so-far.
  T3 absent: the only special character is the backslash; its look-back guard i == 0 protects the single access chars[i - 1]
     (there is no look-ahead, so no other end to treat); both ends of every appended run (start and i, then start and
     chars.length) are given.
  T4 absent: the javadoc names the unescaped text of a backslash escaped character sequence and the builder; no limit, bound,
     value class or case; no inline comment; identifiers (chars, accum, start, i) name nothing the body does not meet.
  Nothing needed rewriting.
 Variant gold (javadoc, signature, `int start = 0; for (...) { if (chars[i] == '\\') { accum.append(chars, start, i - start);
 start = i + 1; } } accum.append(chars, start, chars.length - start);`):
  T1 absent: chars is read for the bound, for each tested character and for every appended run; accum receives every run; both
     change the result.
  T2 absent: start is initialised to 0 and reassigned inside the loop at every backslash, and it bounds both appends; i is the
     for cursor; the single if appends a run and moves start, so it is live; no dead local, no frozen local, no dead branch.
  T3 absent: the gold treats one character, the backslash, and treats every backslash alike; no sibling case, branch or check
     of a closed set exists of which a member is left out; no pair half or range end is handled on one side only (each append
     gives both ends); the javadoc names no class that the code handles in part (it distinguishes no kinds of escape).
  T4 absent: 'the unescaped text of a backslash escaped character sequence' is a general description that the body addresses
     (it leaves the backslashes out and copies everything else in order); '@param chars the escaped characters' and
     '@param accum the builder to append to' are caller-side descriptions; no rule, limit, bound, value class or case is named,
     and there is no inline comment."""

TQ = "src/main/java/org/jsoup/parser/TokenQueue.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = r'''/**
 * Appends the unescaped text of a backslash escaped character sequence to a builder.
 *
 * @param chars the escaped characters
 * @param accum the builder to append to
 */
public static void appendUnescaped(char[] chars, StringBuilder accum) {
    int start = 0;
    for (int i = 0; i < chars.length; i++) {
        if (chars[i] == '\\'
                && (i == 0 || chars[i - 1] != '\\')) {
            accum.append(chars, start, i - start);
            start = i + 1;
        }
    }
    accum.append(chars, start, chars.length - start);
}'''

HOP1 = r'''/**
 * Get the unescaped text of a backslash escaped string.
 * <p>
 * The characters of the string are taken as a char array.
 * </p>
 *
 * @param escaped the backslash escaped string
 * @return the unescaped text
 */
public static String unescapedText(String escaped) {
    return HttpConnection.unescapedValue(escaped.toCharArray());
}'''

HOP2 = r'''/**
 * Build the unescaped value of a backslash escaped character sequence. The value is collected in a builder sized to
 * the sequence.
 *
 * @param chars the escaped characters
 * @return the unescaped value
 */
public static String unescapedValue(char[] chars) {
    StringBuilder accum = new StringBuilder(chars.length);
    Evaluator.CssNthEvaluator.appendUnescapedArgument(chars, accum);
    return accum.toString();
}'''

HOP3 = r'''/**
 * Append the unescaped text of a backslash escaped argument to a builder.
 *
 * @param chars the escaped characters of the argument
 * @param accum the builder to append to
 */
public static void appendUnescapedArgument(char[] chars, StringBuilder accum) {
    HtmlTreeBuilder.appendUnescapedCharacters(chars, accum);
}'''

HOP4 = r'''/**
 * Append the unescaped characters of a backslash escaped sequence to a builder.
 *
 * @param chars the escaped characters
 * @param accum the builder to append to
 */
public static void appendUnescapedCharacters(char[] chars, StringBuilder accum) {
    Node.appendUnescaped(chars, accum);
}'''

DESIGN = {
 "instance": "Jsoup-53", "project": "Jsoup", "bug_id": 53, "seed": 5741,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TQ, "class": "org.jsoup.parser.TokenQueue", "method": "unescape", "near_line": 296},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/parser/TokenQueueTest.java",
             "test_class": "org.jsoup.parser.TokenQueueTest", "test_method": "unescape"},
 "expected_signature": "but was:<one ( ) []>",
 "gold": {"method": "appendUnescaped", "text": GOLD_TEXT,
          "fault": {"old": "            if (chars[i] == '\\\\'\n"
                           "                    && (i == 0 || chars[i - 1] != '\\\\')) {",
                    "new": "            if (chars[i] == '\\\\') {"}},
 "chain": {
   "facade_body": "return org.jsoup.nodes.Element.unescapedText(in);",
   "lie": "The string is read from its last character back to its first, and its characters are pushed onto a stack "
          "that is then emptied into the result.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "unescapedText",
      "imports": ["org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "unescapedValue",
      "imports": ["org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator$CssNthEvaluator", "method": "appendUnescapedArgument",
      "imports": ["org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "appendUnescapedCharacters",
      "imports": [], "text": HOP4},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "appendUnescaped", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.parser.TokenQueue::chompBalanced",
              "org.jsoup.select.QueryParser::contains",
              "org.jsoup.select.QueryParser::matches"],
 "ownership_reason": "Only the gold sees each backslash together with the character before it, and the variant gold never "
                     "appends a backslash, so no change of its input can put one into the result; hops 1 and 2 hold the "
                     "whole string and the finished value, hops 3 and 4 pass the sequence and the builder along. The gold's "
                     "javadoc promises the unescaped text of a backslash escaped character sequence, which for "
                     "'one \\( \\) \\\\' is 'one ( ) \\'. The convention is pinned outside the gold: TokenQueue.chompBalanced "
                     "takes the character after a backslash literally (last != ESC) and its javadoc leaves those escapes in "
                     "its result and points to unescape for contains text; QueryParser.contains unescapes chompBalanced's "
                     "output for :contains(text) (SelectorTest testPsuedoContainsWithParentheses selects 'This is bad)' "
                     "with 'bad\\)'); QueryParser.matches keeps the escapes for java.util.regex, where a doubled backslash is "
                     "one literal backslash; TokenQueueTest chompEscapedBalanced asserts the unescaped form of an escaped "
                     "argument. One-line edits above the gold that pass the suite either replace the gold's result with "
                     "another implementation (a regular expression at any hop) or are fitted to the test input (a "
                     "private-use placeholder at hop 1, which breaks hop 1's documented char-array conversion; a backslash "
                     "appended at hop 2 when the sequence ends with two backslashes, which leaves 'a\\\\b' as 'ab').",
 "ownership_tests": ["org.jsoup.parser.TokenQueueTest::chompEscapedBalanced",
                     "org.jsoup.parser.TokenQueueTest::chompBalanced",
                     "org.jsoup.select.SelectorTest::testPsuedoContainsWithParentheses",
                     "org.jsoup.select.SelectorTest::testPseudoContains"],
 "compensating": {
   "chain": [
     {"file": EL, "old": "return HttpConnection.unescapedValue(escaped.toCharArray());",
      "new": r'return HttpConnection.unescapedValue(escaped.replace("\\\\", "\\").toCharArray());',
      "why": "hop 1 collapses each pair of backslashes before the conversion"},
     {"file": HTB, "old": "Node.appendUnescaped(chars, accum);",
      "new": r'Node.appendUnescaped(new String(chars).replace("\\", "\\\\").toCharArray(), accum);',
      "why": "hop 4 doubles every backslash before the call"},
     {"file": EV, "old": "HtmlTreeBuilder.appendUnescapedCharacters(chars, accum);",
      "new": r"HtmlTreeBuilder.appendUnescapedCharacters(chars.length > 0 && chars[chars.length - 1] == '\\' ? java.util.Arrays.copyOf(chars, chars.length - 1) : chars, accum);",
      "why": "hop 3 drops a trailing backslash of the argument"},
   ],
 },
 "host_notes": "host_mode largest5 (0 other public classes of >= 1500 lines in the fixed revision). Hosts are the task record's "
               "hosts_hop_order, the five largest public non-interface non-enum classes other than TokenQueue by newline "
               "count: nodes.Element 1237 (hop 1), helper.HttpConnection 1016 (hop 2), select.Evaluator 706 (hop 3), "
               "parser.HtmlTreeBuilder 702 (hop 4), nodes.Node 694 (hop 5, gold; smallest host 694). Anchors from "
               "stageB_lib.pick_anchor with seed 5741 + 100 + i (the call mr2_spec.py makes): after Element.html (5841), "
               "HttpConnection.data (5842), Evaluator `matches` (5843), HtmlTreeBuilder.insertForm (5844), Node.parent "
               "(5845). The Evaluator anchor is the matches method of the public static nested class "
               "Evaluator.CssNthEvaluator (its header is indented four spaces and a tab, which the recipe's four-space "
               "filter takes as an outer member; the batch-5 disclosed anchor deviation), so hop 3 is a static method of "
               "that nested class; it compiles there, is called as Evaluator.CssNthEvaluator.appendUnescapedArgument and is "
               "catalogued as org.jsoup.select.Evaluator$CssNthEvaluator. Node and Evaluator are abstract, which does not "
               "affect a static method. No host was skipped or substituted. The facade calls hop 1 by its fully-qualified "
               "name; hops 1-3 import the next host; HtmlTreeBuilder already imports org.jsoup.nodes.*.",
}
