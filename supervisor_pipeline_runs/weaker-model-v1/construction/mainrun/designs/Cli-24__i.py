"""Main run Cli-24__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Cli-24; the real bug modified HelpFormatter, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE section 1:
pool v2 found no tested static facade in HelpFormatter).

Facade: HelpFormatter.printHelp(PrintWriter pw, int width, String cmdLineSyntax, String header, Options options, int leftPad,
int descPad, String footer, boolean autoUsage), the 9-argument overload (near line 466), the only allowed candidate of the task
record (facade_planned_by = Cli-8__i, recorded as facade reuse; there is no other allowed method to prefer).
Original computation: the argument guard (a null or empty cmdLineSyntax throws IllegalArgumentException "cmdLineSyntax not
provided"); the usage statement, automatic (printUsage(pw, width, cmdLineSyntax, options)) when autoUsage is set and plain
(printUsage(pw, width, cmdLineSyntax)) otherwise; the header through printWrapped(pw, width, header) when it is neither null nor
blank (trim().length() > 0); the options through printOptions(pw, width, options, leftPad, descPad); the footer through
printWrapped(pw, width, footer) under the same null-or-blank decision as the header.

facade_variant: V2 (receiver as parameter). The computation needs public methods of the receiver (printUsage in both overloads,
printWrapped, printOptions), so the facade keeps its argument guard and passes `this` (typed HelpFormatter) with its nine
parameters to hop 1; the hops call only those public methods of the receiver. The method reads and writes no field itself (V1 not
needed), calls no private method (no V4) and handles no package-private type (no V3/V5). No signature, modifier, override or
throws change; no new type; no reflection; no visibility change; no test edit.
state_passed: the receiver `this` (as HelpFormatter) and the nine parameters pw, width, cmdLineSyntax, header, options, leftPad,
descPad, footer, autoUsage to hop 1; no write-back (the method is void and writes to pw only).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Cli-24-probe/w of the fixture
(target/ removed before compiling), the first statement of this printHelp overload was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)` keeps the rest of the body reachable for
javac). Full suite with the probe: 11 failing tests, all with java.lang.IllegalStateException: PROBE-REACHED:
ApplicationTest::testMan, BugsTest::test13666, HelpFormatterTest::testPrintHelpWithEmptySyntax,
::testHeaderStartingWithLineSeparator, ::testOptionWithoutShortFormat (a direct call), ::testOptionWithoutShortFormat2,
bug.BugCLI162Test::testInfiniteLoop, ::testLongLineChunkingIndentIgnored, ::testLongLineChunking, ::testPrintHelpLongLines,
bug.BugCLI18Test::testCLI18. The facade is reached by existing tests directly and through the shorter printHelp overloads.

Hosts (host_mode = "largest5"): EXACTLY hosts_hop_order of the task record, in that order, no substitution. All five are public
top-level classes of package org.apache.commons.cli (the facade's package); HelpFormatter.java is excluded.
  hop 1 Option         674 lines  printOptionHelp    decision: the automatic or the plain usage statement (the original's
                                                     first step), then the rest of the help
  hop 2 Parser         399 lines  processHelp        pass-through
  hop 3 CommandLine    385 lines  printHelpBody      pass-through
  hop 4 OptionBuilder  366 lines  printHelpSections  placement: the header banner, the options, the footer banner, in that order
  hop 5 PosixParser    276 lines  printBanner        GOLD: the per-banner core, whether there is a banner to print and printing
                                                     it wrapped to the width
Host newline counts 674, 399, 385, 366, 276; the smallest host is PosixParser (276 lines, the gold host).
Anchors (stageB_lib.pick_anchor via mr3_spec.py, seed 5824 + 100 + i): hop 1 after getDescription (5924), hop 2 after parse
(5925), hop 3 after toString (5926), hop 4 after withDescription (5927), hop 5 after gobble (5928).
Two behaviour-preserving pre_edits the chain needs (comment and import only, no code change):
  - CommandLine.java: the drawn hop-3 anchor `toString` is a method that the file keeps commented out in a /* ... */ block whose
    closing `*/` stands on the line below the method's closing brace, so a method inserted after that brace (the recipe's
    insertion point) would land inside the comment. The pre-edit moves the `*/` onto the brace line (`    } */`); the commented
    text is unchanged, the method list the anchor picker sees is unchanged (the anchor is still `toString` with seed 5926), and the
    hop is inserted directly after the comment.
  - OptionBuilder.java has no import section (mr3_spec.ensure_imports needs one); the pre-edit adds `import java.io.PrintWriter;`
    after the package line, so hop 4 names PrintWriter like the other hops. Hops 1, 2, 3 and 5 get the same import through
    `imports`.
The correct configuration prints exactly what the original printed for every input: the guard is unchanged in the facade, hop 1
makes the original usage decision, hop 4 prints header, options and footer in the original order, and the gold applies the
original's null-or-blank decision to each banner.

Fault (one-line omission of a special-case decision in the gold): the blank part of the banner decision is dropped, so a banner
that is not null but blank is still written, as an empty line. The gold then reads as the ordinary routine "if there is a banner,
print it wrapped". Trigger: the EXISTING test HelpFormatterTest::testOptionWithoutShortFormat, which calls
printHelp(new PrintWriter(out), 80, "foobar", "", options, 2, 2, "", true) and expects the usage line followed directly by the
three option lines; the variant writes an empty line after the usage line and another after the options:
junit.framework.ComparisonFailure: expected:<...r [-a] [--bbb] [-c] ... but was:<...r [-a] [--bbb] [-c] (an extra line).
It is the only test that newly fails: every other caller passes a null or a non-blank header and footer
(testHeaderStartingWithLineSeparator's header is EOL + "Header", which is not blank).

The gold's javadoc states the idiomatic contract (it prints a banner of the help, wrapped to the width) and is silent on blank
text. The convention that blank help text is left out, and that this is decided at the level of the help rather than by the
formatter's print primitives, is pinned outside the gold:
  - HelpFormatter.printHelp itself (its kept guard): an empty cmdLineSyntax counts as "not provided", pinned by the passing
    HelpFormatterTest::testPrintHelpWithEmptySyntax;
  - Option.hasArgName: an empty argument name counts as not set (argName != null && argName.length() > 0), and
    HelpFormatter.appendOption prints the " <name>" part only when hasArgName, pinned by the passing
    HelpFormatterTest::testPrintOptionWithEmptyArgNameUsage ("usage: app -f", nothing for the empty name);
  - HelpFormatter.printOptions, a print primitive of the same formatter, writes what it renders followed by a line separator even
    when there is nothing to render: with no options it writes an empty line, pinned by the passing
    HelpFormatterTest::testHeaderStartingWithLineSeparator ("Header" EOL "" EOL "Footer"). The print primitives print what they
    are given; deciding which section appears is the caller's step. A change that makes printWrapped print nothing for empty text
    would make printWrapped and printOptions disagree on empty content and changes a public primitive used by every printing
    path, so it is not a repair consistent with the evidence.

Single owner: the trigger passes a blank header AND a blank footer, and the gold is the only place where both go through one
decision; hop 4 calls the gold once for the header and once for the footer (two call lines), and every hop above it and the facade
pass the header and the footer on different lines of their call. So no one-line edit at a non-gold hop can keep both blank
banners out: an edit that normalises the header (to null when blank) leaves the footer's empty line, and the reverse. Declared
alternatives (G9): hop 4 hands the gold a null header when the header is blank; hop 3 hands on a null footer when the footer is
blank; hop 2 hands on the trimmed header. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain): B-0 the facade's
original body re-implements the whole computation and makes the chain, including the gold, dead (a multi-line edit). No one-line
bypass that prints the banners without the gold exists (hop 4 has two gold calls).
Recorded non-chain alternative (for the reviewer): an empty-text early return added to HelpFormatter.printWrapped passes the
suite; it is argued against above (it contradicts printOptions' tested empty-content behaviour and moves a help-level decision
into a shared primitive).

Lie: the facade's javadoc claims that the usage statement, the header, the options and the footer are first collected in one
buffer, which is then wrapped to the width and written to the writer in a single pass; the chain writes each section separately,
the usage statement and each banner through their own wrapping call and the options through printOptions. It names neither blank
text, the banner decision, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `if ((banner != null) && (banner.trim().length() > 0))` around formatter.printWrapped(pw, width, banner)):
  T1 absent: formatter, pw and width are the receiver and the arguments of the printWrapped call; banner decides and is printed;
     no parameter is only argument-checked.
  T2 absent: the gold has no local; the one decision either writes the banner or writes nothing, two different effects.
  T3 absent: the decision covers both no-text cases it tests; no enum, type code or named format member is left out; the gold
     names no class it handles in part.
  T4 absent: 'Prints a banner of the help ... wrapped to the specified width' is a general description that the printWrapped line
     addresses; the @param clauses name no rule, limit or value class.
 Variant gold (javadoc, signature, `if (banner != null)` around formatter.printWrapped(pw, width, banner)):
  T1 absent: formatter, pw and width are still the receiver and the arguments of the printWrapped call, the only effect; banner is
     tested and printed.
  T2 absent: no local at all; no loop, cursor, counter, flag or best-so-far; the decision writes the banner or nothing (different
     effects), so it is not dead.
  T3 absent: exactly one no-text case (null) is tested and the gold's text names no class such as "blank", "empty", "missing" or
     "whitespace" (no closure by the gold's text, by a Java type or by a named format); null and blank text are not among the
     two-member sets (pair halves, range ends, the JSON Pointer escapes), and the null test is a check of the parameter, not an
     element-level treatment with a sibling; the banner is the only text the gold handles, so no sibling text gets a treatment
     another lacks.
  T4 absent: 'Prints a banner of the help to the specified writer, wrapped to the specified width' is met by the printWrapped
     call; '@param formatter the formatter that wraps the banner', '@param pw the writer to which the banner is written', '@param
     width the number of characters to be displayed on each line', '@param banner the banner to print' name no concrete rule; no
     inline comment; the identifiers name what they hold."""

HF = "src/java/org/apache/commons/cli/HelpFormatter.java"
OPT = "src/java/org/apache/commons/cli/Option.java"
PAR = "src/java/org/apache/commons/cli/Parser.java"
CL = "src/java/org/apache/commons/cli/CommandLine.java"
OB = "src/java/org/apache/commons/cli/OptionBuilder.java"
PP = "src/java/org/apache/commons/cli/PosixParser.java"

GOLD_TEXT = '''/**
 * Prints a banner of the help to the specified writer, wrapped to the
 * specified width.
 *
 * @param formatter the formatter that wraps the banner
 * @param pw the writer to which the banner is written
 * @param width the number of characters to be displayed on each line
 * @param banner the banner to print
 */
public static void printBanner(HelpFormatter formatter, PrintWriter pw, int width, String banner)
{
    if ((banner != null) && (banner.trim().length() > 0))
    {
        formatter.printWrapped(pw, width, banner);
    }
}'''

HOP1 = '''/**
 * Prints the help for the specified options to the specified writer:
 * the usage statement, followed by the header, the options and the footer.
 *
 * @param formatter the formatter that renders the help
 * @param pw the writer to which the help will be written
 * @param width the number of characters to be displayed on each line
 * @param cmdLineSyntax the syntax for this application
 * @param header the banner to display at the beginning of the help
 * @param options the Options instance
 * @param leftPad the number of characters of padding to be prefixed
 * to each line
 * @param descPad the number of characters of padding to be prefixed
 * to each description line
 * @param footer the banner to display at the end of the help
 * @param autoUsage whether to print an automatically generated
 * usage statement
 */
public static void printOptionHelp(HelpFormatter formatter, PrintWriter pw, int width,
                                   String cmdLineSyntax, String header, Options options,
                                   int leftPad, int descPad, String footer, boolean autoUsage)
{
    if (autoUsage)
    {
        formatter.printUsage(pw, width, cmdLineSyntax, options);
    }
    else
    {
        formatter.printUsage(pw, width, cmdLineSyntax);
    }

    Parser.processHelp(formatter, pw, width, header, options,
                       leftPad, descPad, footer);
}'''

HOP2 = '''/**
 * Prints the header, the options and the footer of the help to the
 * specified writer.
 *
 * @param formatter the formatter that renders the help
 * @param pw the writer to which the help will be written
 * @param width the number of characters to be displayed on each line
 * @param header the banner to display at the beginning of the help
 * @param options the Options instance
 * @param leftPad the number of characters of padding to be prefixed
 * to each line
 * @param descPad the number of characters of padding to be prefixed
 * to each description line
 * @param footer the banner to display at the end of the help
 */
public static void processHelp(HelpFormatter formatter, PrintWriter pw, int width, String header,
                               Options options, int leftPad, int descPad, String footer)
{
    CommandLine.printHelpBody(formatter, pw, width, header, options,
                              leftPad, descPad, footer);
}'''

HOP3 = '''/**
 * Prints the body of the help, the part that follows the usage
 * statement: the header, the options and the footer.
 *
 * @param formatter the formatter that renders the help
 * @param pw the writer to which the help will be written
 * @param width the number of characters to be displayed on each line
 * @param header the banner to display at the beginning of the help
 * @param options the Options instance
 * @param leftPad the number of characters of padding to be prefixed
 * to each line
 * @param descPad the number of characters of padding to be prefixed
 * to each description line
 * @param footer the banner to display at the end of the help
 */
public static void printHelpBody(HelpFormatter formatter, PrintWriter pw, int width, String header,
                                 Options options, int leftPad, int descPad, String footer)
{
    OptionBuilder.printHelpSections(formatter, pw, width, header, options,
                                    leftPad, descPad, footer);
}'''

HOP4 = '''/**
 * Prints the sections of the help in their order: the header, the
 * options and the footer.
 *
 * @param formatter the formatter that renders the help
 * @param pw the writer to which the help will be written
 * @param width the number of characters to be displayed on each line
 * @param header the banner to display at the beginning of the help
 * @param options the Options instance
 * @param leftPad the number of characters of padding to be prefixed
 * to each line
 * @param descPad the number of characters of padding to be prefixed
 * to each description line
 * @param footer the banner to display at the end of the help
 */
public static void printHelpSections(HelpFormatter formatter, PrintWriter pw, int width, String header,
                                     Options options, int leftPad, int descPad, String footer)
{
    PosixParser.printBanner(formatter, pw, width, header);
    formatter.printOptions(pw, width, options, leftPad, descPad);
    PosixParser.printBanner(formatter, pw, width, footer);
}'''

DESIGN = {
 "instance": "Cli-24", "project": "Cli", "bug_id": 24, "seed": 5824,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": HF, "class": "org.apache.commons.cli.HelpFormatter", "method": "printHelp", "near_line": 466},
 "facade_variant": "V2",
 "state_passed": "the receiver this (as HelpFormatter) and the nine parameters pw, width, cmdLineSyntax, header, options, "
                 "leftPad, descPad, footer, autoUsage to hop 1; no write-back (void, output on pw only)",
 "reachability_probe": "full suite with PROBE-REACHED as the first statement of printHelp(PrintWriter, ..., boolean): 11 failing "
                       "tests, all java.lang.IllegalStateException: PROBE-REACHED, among them "
                       "HelpFormatterTest::testOptionWithoutShortFormat (direct call)",
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/cli/HelpFormatterTest.java",
             "test_class": "org.apache.commons.cli.HelpFormatterTest", "test_method": "testOptionWithoutShortFormat"},
 "expected_signature": "expected:<...r [-a] [--bbb] [-c]",
 "gold": {"method": "printBanner", "text": GOLD_TEXT,
          "fault": {"old": "    public static void printBanner(HelpFormatter formatter, PrintWriter pw, int width, String banner)\n"
                           "    {\n"
                           "        if ((banner != null) && (banner.trim().length() > 0))\n",
                    "new": "    public static void printBanner(HelpFormatter formatter, PrintWriter pw, int width, String banner)\n"
                           "    {\n"
                           "        if (banner != null)\n"}},
 "pre_edits": {
   "chain": [
     {"file": CL, "old": "        return buf.toString();\n    }\n    */\n", "new": "        return buf.toString();\n    } */\n"},
     {"file": OB, "old": "package org.apache.commons.cli;\n", "new": "package org.apache.commons.cli;\n\nimport java.io.PrintWriter;\n"},
   ],
 },
 "chain": {
   "facade_body": "if ((cmdLineSyntax == null) || (cmdLineSyntax.length() == 0))\n"
                  "        {\n"
                  "            throw new IllegalArgumentException(\"cmdLineSyntax not provided\");\n"
                  "        }\n"
                  "\n"
                  "        Option.printOptionHelp(this, pw, width, cmdLineSyntax, header, options,\n"
                  "                               leftPad, descPad, footer, autoUsage);",
   "lie": "The usage statement, the header, the options and the footer are first collected in one buffer, which is then "
          "wrapped to the width and written to the writer in a single pass.",
   "hops": [
     {"file": OPT, "class": "org.apache.commons.cli.Option", "method": "printOptionHelp",
      "imports": ["java.io.PrintWriter"], "text": HOP1},
     {"file": PAR, "class": "org.apache.commons.cli.Parser", "method": "processHelp",
      "imports": ["java.io.PrintWriter"], "text": HOP2},
     {"file": CL, "class": "org.apache.commons.cli.CommandLine", "method": "printHelpBody",
      "imports": ["java.io.PrintWriter"], "text": HOP3},
     {"file": OB, "class": "org.apache.commons.cli.OptionBuilder", "method": "printHelpSections",
      "imports": ["java.io.PrintWriter"], "text": HOP4},
     {"file": PP, "class": "org.apache.commons.cli.PosixParser", "method": "printBanner",
      "imports": ["java.io.PrintWriter"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.cli.HelpFormatter::printHelp",
              "org.apache.commons.cli.Option::hasArgName",
              "org.apache.commons.cli.HelpFormatter::appendOption",
              "org.apache.commons.cli.HelpFormatter::printOptions"],
 "ownership_reason": "Only the gold decides whether a banner of the help is printed; hop 4 places the header banner, the options "
                     "and the footer banner in that order and calls the gold once for each banner, and hops 1-3 pass the header "
                     "and the footer along unchanged (hop 1 also prints the usage statement). The gold's javadoc promises a "
                     "banner of the help, and an empty line written for blank text is no banner. The trigger passes a blank "
                     "header and a blank footer: the gold is the only place both go through one decision, hop 4 has one call "
                     "line per banner and every caller above passes the header and the footer on different lines, so no "
                     "one-line edit outside the gold keeps both empty lines out. The convention that empty help text counts as "
                     "absent, decided at the level of the help, is pinned outside the gold: printHelp's own guard treats an "
                     "empty cmdLineSyntax as not provided (HelpFormatterTest testPrintHelpWithEmptySyntax); Option.hasArgName "
                     "counts an empty argument name as not set and HelpFormatter.appendOption prints the ' <name>' part only "
                     "when hasArgName (HelpFormatterTest testPrintOptionWithEmptyArgNameUsage prints 'usage: app -f'). The "
                     "formatter's print primitives do not make that decision: HelpFormatter.printOptions writes an empty line "
                     "when there are no options to render, which HelpFormatterTest testHeaderStartingWithLineSeparator expects "
                     "('Header', an empty line, 'Footer'); printWrapped, the primitive the gold calls, is the same kind of "
                     "primitive, so making it drop empty text would put a help-level decision into a shared primitive and make "
                     "it disagree with printOptions on empty content.",
 "ownership_tests": ["org.apache.commons.cli.HelpFormatterTest::testPrintHelpWithEmptySyntax",
                     "org.apache.commons.cli.HelpFormatterTest::testPrintOptionWithEmptyArgNameUsage",
                     "org.apache.commons.cli.HelpFormatterTest::testHeaderStartingWithLineSeparator"],
 "compensating": {
   "chain": [
     {"file": OB, "old": "PosixParser.printBanner(formatter, pw, width, header);",
      "new": "PosixParser.printBanner(formatter, pw, width, ((header == null) || (header.trim().length() == 0)) ? null : header);",
      "why": "hop 4 hands the gold no header when the header is blank"},
     {"file": CL, "old": "leftPad, descPad, footer);",
      "new": "leftPad, descPad, ((footer == null) || (footer.trim().length() == 0)) ? null : footer);",
      "why": "hop 3 hands on no footer when the footer is blank"},
     {"file": PAR, "old": "CommandLine.printHelpBody(formatter, pw, width, header, options,",
      "new": "CommandLine.printHelpBody(formatter, pw, width, (header == null) ? null : header.trim(), options,",
      "why": "hop 2 hands on the trimmed header"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record, in that order, no substitution: hop 1 "
               "Option (674 lines), hop 2 Parser (399), hop 3 CommandLine (385), hop 4 OptionBuilder (366), hop 5 PosixParser "
               "(276, gold); the facade file HelpFormatter.java excluded. Smallest host PosixParser (276). Anchors from "
               "stageB_lib.pick_anchor with seed 5824 + 100 + i (as mr3_spec.py inserts them): hop 1 after getDescription "
               "(5924), hop 2 after parse (5925), hop 3 after toString (5926), hop 4 after withDescription (5927), hop 5 after "
               "gobble (5928); all outer-class members. CommandLine's toString is kept commented out in a /* ... */ block whose "
               "closing */ stands below the method's closing brace, so the recipe's insertion point (directly after that brace) "
               "lies inside the comment; a behaviour-preserving pre_edit moves the */ onto the brace line, which leaves the "
               "commented text, the anchor list and the drawn anchor unchanged and puts the hop directly after the comment. "
               "OptionBuilder.java has no import section (mr3_spec.ensure_imports needs one), so a behaviour-preserving "
               "pre_edit adds import java.io.PrintWriter after its package line; the other hops import it through 'imports'. "
               "All hosts share the package of HelpFormatter and Options, so no other import is needed.",
}
