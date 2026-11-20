"""Main run Cli-32__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Cli-32; the real bug modified HelpFormatter, the facade's class). No static pair (B8 note section 1: pool v2 found no
strictly tested public static method in HelpFormatter).

Facade: HelpFormatter.printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean), the 29-line overload (the only
allowed candidate of batch9_tasks.json; facade_planned_by = Cli-8__i, so this is a recorded facade reuse: no other allowed candidate
exists). Every other printHelp overload of the class delegates to it and stays intact.
Original computation of the facade: a null or empty cmdLineSyntax throws IllegalArgumentException("cmdLineSyntax not provided"); the
usage statement is printed with printUsage(pw, width, cmdLineSyntax, options) when autoUsage is set and with printUsage(pw, width,
cmdLineSyntax) otherwise; the header is printed with printWrapped(pw, width, header) when it is not null and its trimmed length is
positive; the options are printed with printOptions(pw, width, options, leftPad, descPad); the footer is printed like the header.

facade_variant: V2 (receiver as parameter). The computation calls three public methods of the receiver (printUsage, printOptions,
printWrapped), which read the formatter's public settings (prefixes, separators, comparator, new line) set through its accessors, so
the facade passes `this` (typed HelpFormatter) to hop 1 and the hops call only those public methods. The facade keeps the original
argument guard on cmdLineSyntax and makes one call to hop 1 with `this` and all nine parameters. It reads no field itself and writes
none (no write-back). No private or protected method of HelpFormatter is called by the chain (no V4); every type involved
(HelpFormatter, Options, PrintWriter) is public (no V3/V5). No signature, modifier, override or throws change; no new type; no
reflection; no test edit.
state_passed: the receiver `this` (HelpFormatter) and the parameters pw, width, cmdLineSyntax, header, options, leftPad, descPad,
footer and autoUsage, to hop 1; no field is read or written by the facade, no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Cli-32-probe2 of the fixture, the first
statement of the 9-argument printHelp was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.cli.HelpFormatterTest::testOptionWithoutShortFormat`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at HelpFormatter.printHelp(HelpFormatter.java:503), called from
HelpFormatterTest.testOptionWithoutShortFormat(HelpFormatterTest.java:441). The facade is also reached (through the other printHelp
overloads) by ApplicationTest::testMan, BugsTest::test13666, HelpFormatterTest::testHelpWithLongOptSeparator / testPrintHelpWithEmptySyntax
/ testHeaderStartingWithLineSeparator / testOptionWithoutShortFormat2, BugCLI162Test::testInfiniteLoop / testLongLineChunkingIndentIgnored
/ testLongLineChunking / testPrintHelpLongLines and BugCLI18Test::testCLI18.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of the task record, in that order, none substituted; the allowed candidate's
file HelpFormatter.java is excluded):
  hop 1 Option         705 lines  printHelpText        decision: the usage statement, generated from the options when autoUsage is
                                                       set, from the syntax otherwise (the original's first step after the guard)
  hop 2 DefaultParser  689 lines  handleHelpSections   pass-through of the header, the options and the footer
  hop 3 Parser         430 lines  processHelpSections  pass-through
  hop 4 CommandLine    388 lines  printSections        placement: the header banner, then the options, then the footer banner
  hop 5 OptionBuilder  375 lines  printBanner          GOLD: one banner (a header or a footer): whether it has text to print, and
                                                       its wrapped lines
Host newline counts 705, 689, 430, 388, 375; the smallest host (and the gold host) is OptionBuilder with 375 lines (C10F addendum
section 1: hosts under 1500 lines are expected in this regime). All five are public top-level classes in the facade's package
org.apache.commons.cli in which a public static method compiles (Parser is abstract and OptionBuilder is final with a private
constructor, which does not affect a static method; Option and CommandLine are Serializable with an explicit serialVersionUID).
Anchors (stageB_lib.pick_insertion_anchor through mr3_spec.py, instance seed 2295, seed 2295 + 100 + i): hop 1 after `hashCode`
(Option, seed 2395), hop 2 after `parse` (DefaultParser, 2396), hop 3 after `parse` (Parser, 2397), hop 4 after `getOptionValue`
(CommandLine, 2398), hop 5 after `hasOptionalArg` (OptionBuilder, 2399).
The correct configuration prints exactly what the original printed for every input: the guard is unchanged; hop 1 makes the same usage
decision; hop 4 keeps the order header, options, footer; the gold prints a banner exactly when the original's condition `(x != null) &&
(x.trim().length() > 0)` holds, with the same printWrapped(pw, width, x) call.

Division of labour on the path, as the javadoc states it: the formatter's print methods write what they are handed and always end with
at least one complete line (hop 1's javadoc says so, and the code agrees: printUsage, printOptions and printWrapped all end with
pw.println; printOptions writes an empty line for an Options instance without options, pinned by the passing
HelpFormatterTest::testHeaderStartingWithLineSeparator); hops 1 to 4 hand the header and the footer on as they are given (each says so);
whether a banner is printed at all is left to the banner step, the gold.

Fault (one-line omission of a special-case decision in the gold): the blank-banner test `&& (banner.trim().length() > 0)` is dropped
from the gold's condition, so a banner without text is handed to printWrapped and printed as an empty line. The gold then reads as the
ordinary routine "print the banner, if there is one, wrapped to the width". Trigger: the EXISTING test
HelpFormatterTest::testOptionWithoutShortFormat, which calls the facade with header "" and footer "" and asserts the exact output; the
variant prints an empty line after the usage statement and after the options. It is the only test that passes an empty or blank header
or footer (every other caller passes null, "Header"/"Footer", "header"/"footer", a header starting with a line separator, or a long
non-blank text), and the new hops have no other caller; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it prints the lines of a banner of the help, wrapped to the width) and is silent on
blank text; an empty banner has no lines, so the empty line the variant prints is not a line of the banner. The convention that text
without content counts as absent is pinned outside the gold by production code doing the same step on other text of the help:
Option.hasArgName (an empty arg name counts as no arg name: `argName != null && argName.length() > 0`), HelpFormatter.appendOption ("if
the Option has a value and a non blank argname": an empty arg name adds no `<...>` to the usage clause) and HelpFormatter.renderOptions
(an empty arg name adds no `<...>` to the option's entry), with HelpFormatterTest::testPrintOptionWithEmptyArgNameUsage passing; the
layout of the help without blank lines between its parts is pinned by the passing HelpFormatterTest::testOptionWithoutShortFormat2 and
::testHelpWithLongOptSeparator ("header" directly after the usage, "footer" directly after the options), and a banner that does have
text is printed as given, including a leading line separator (HelpFormatterTest::testHeaderStartingWithLineSeparator).

Single owner: only the gold decides whether a banner is printed.
  Above the gold: hops 1 to 4 each document that the header and the footer are handed on as they are given, so replacing a blank
  value there contradicts that hop's documentation; a trim of the values keeps "" as "" and the trigger still fails; hop 4 calls the
  gold once for the header and once for the footer, on two separate lines, and the trigger has both an empty header and an empty
  footer, so a one-line pre-filter at hop 4 removes only one of the two empty lines and the trigger still fails.
  Below the gold: the gold's only callee is the public HelpFormatter.printWrapped, whose output for any text ends with pw.println; a
  change there that writes nothing for an empty text would contradict hop 1's documented property of the formatter's print methods
  (each writes at least one complete line), which its siblings printOptions and printUsage keep, printOptions also for an empty
  section (testHeaderStartingWithLineSeparator).
  Declared alternatives (G9): hop 4 drops an empty header before the gold; hop 4 drops an empty footer before the gold; hop 3 trims the
  header and the footer. Each leaves the trigger failing.
  Recorded bypass: B-0 the facade's original body (or a hop that prints the header and the footer itself with printWrapped under the
  original condition) re-implements the decision above the gold and leaves the gold dead for the trigger's banners.

Lie: the facade's javadoc claims the sections are first rendered into a single buffer, which is wrapped as a whole and then written to
the writer in one call; the chain writes each part separately (the usage statement, each banner and the options are each printed by
their own call). It names neither banners, blank text, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: formatter, pw, width and banner are all arguments of the printWrapped call; banner also decides whether it runs (null and
     blank text); none is only argument-checked.
  T2 absent: the gold has no local variable; its one decision chooses between printing and printing nothing.
  T3 absent: the condition treats null and text without content; the gold handles one banner (whichever of header or footer it is
     given), so header and footer are not a pair handled in part inside the gold; no enum, type code or named format is involved.
  T4 absent: 'Prints the lines of a banner of the help, such as its header or its footer, wrapped to the given width' is a general
     description that the printWrapped call addresses; the @param clauses name no rule, limit or value class.
 Variant gold (javadoc, signature, `if (banner != null)` around `formatter.printWrapped(pw, width, banner)`):
  T1 absent: formatter, pw, width and banner are all arguments of printWrapped; banner also decides whether it runs.
  T2 absent: no local; the decision chooses between printing and printing nothing (two different effects); no literal-initialised
     local, no loop.
  T3 absent: the only treatment is the null test of the parameter, an argument check ('Argument checks ... do not form a set'); no
     element-level special values are handled ('No member handled'); the gold names no class ("blank", "empty", "non-empty", "text")
     that it would handle in part; header and footer are named only as examples of the one banner the gold receives, both treated the
     same way.
  T4 absent: 'Prints the lines of a banner ... wrapped to the given width' is met by printWrapped (a general description, like 'joins
     the elements'); '@param formatter the formatter that wraps the lines', '@param pw the writer to which the banner is written',
     '@param width the number of characters to be displayed on each line' and '@param banner the text of the banner' name no concrete
     rule, limit or case; no inline comment; the identifiers name what they hold."""

HF = "src/main/java/org/apache/commons/cli/HelpFormatter.java"
OPT = "src/main/java/org/apache/commons/cli/Option.java"
DP = "src/main/java/org/apache/commons/cli/DefaultParser.java"
PA = "src/main/java/org/apache/commons/cli/Parser.java"
CL = "src/main/java/org/apache/commons/cli/CommandLine.java"
OB = "src/main/java/org/apache/commons/cli/OptionBuilder.java"

GOLD_TEXT = '''/**
 * Prints the lines of a banner of the help, such as its header or
 * its footer, wrapped to the given width.
 *
 * @param formatter the formatter that wraps the lines
 * @param pw the writer to which the banner is written
 * @param width the number of characters to be displayed on each line
 * @param banner the text of the banner
 */
public static void printBanner(HelpFormatter formatter, java.io.PrintWriter pw, int width, String banner)
{
    if ((banner != null) && (banner.trim().length() > 0))
    {
        formatter.printWrapped(pw, width, banner);
    }
}'''

HOP1 = '''/**
 * Prints the help for <code>options</code>: the usage statement for
 * <code>cmdLineSyntax</code>, followed by the header, the options and
 * the footer, which are handed on as they are given. Each print
 * method of the formatter writes at least one complete line, so every
 * part of the help starts on a line of its own.
 *
 * @param formatter the formatter that prints the help
 * @param pw the writer to which the help is written
 * @param width the number of characters to be displayed on each line
 * @param cmdLineSyntax the syntax for the application
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
public static void printHelpText(HelpFormatter formatter, PrintWriter pw, int width, String cmdLineSyntax,
                                 String header, Options options, int leftPad, int descPad,
                                 String footer, boolean autoUsage)
{
    if (autoUsage)
    {
        formatter.printUsage(pw, width, cmdLineSyntax, options);
    }
    else
    {
        formatter.printUsage(pw, width, cmdLineSyntax);
    }

    DefaultParser.handleHelpSections(formatter, pw, width, header, options, leftPad, descPad, footer);
}'''

HOP2 = '''/**
 * Prints the header, the options and the footer of a help message.
 * The header and the footer are handed on as they are given.
 *
 * @param formatter the formatter that prints the help
 * @param pw the writer to which the help is written
 * @param width the number of characters to be displayed on each line
 * @param header the banner to display at the beginning of the help
 * @param options the options to describe
 * @param leftPad the padding prefixed to each line
 * @param descPad the padding prefixed to each description line
 * @param footer the banner to display at the end of the help
 */
public static void handleHelpSections(HelpFormatter formatter, PrintWriter pw, int width, String header,
                                      Options options, int leftPad, int descPad, String footer)
{
    Parser.processHelpSections(formatter, pw, width, header, options, leftPad, descPad, footer);
}'''

HOP3 = '''/**
 * Prints the header, the options and the footer of a help message
 * for the specified {@link Options}. The header and the footer are
 * handed on as they are given.
 *
 * @param formatter the formatter that prints the help
 * @param pw the writer to which the help is written
 * @param width the number of characters to be displayed on each line
 * @param header the banner to display at the beginning of the help
 * @param options the <code>Options</code>
 * @param leftPad the padding prefixed to each line
 * @param descPad the padding prefixed to each description line
 * @param footer the banner to display at the end of the help
 */
public static void processHelpSections(HelpFormatter formatter, PrintWriter pw, int width, String header,
                                       Options options, int leftPad, int descPad, String footer)
{
    CommandLine.printSections(formatter, pw, width, header, options, leftPad, descPad, footer);
}'''

HOP4 = '''/**
 * Prints the sections of a help message in order: the header, the
 * options and the footer. The header and the footer are handed on
 * as they are given.
 *
 * @param formatter the formatter that prints the help
 * @param pw the writer to which the help is written
 * @param width the number of characters to be displayed on each line
 * @param header the banner to display at the beginning of the help
 * @param options the options to describe
 * @param leftPad the padding prefixed to each line
 * @param descPad the padding prefixed to each description line
 * @param footer the banner to display at the end of the help
 */
public static void printSections(HelpFormatter formatter, PrintWriter pw, int width, String header,
                                 Options options, int leftPad, int descPad, String footer)
{
    OptionBuilder.printBanner(formatter, pw, width, header);

    formatter.printOptions(pw, width, options, leftPad, descPad);

    OptionBuilder.printBanner(formatter, pw, width, footer);
}'''

DESIGN = {
 "instance": "Cli-32", "project": "Cli", "bug_id": 32, "seed": 2295,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": HF, "class": "org.apache.commons.cli.HelpFormatter", "method": "printHelp", "near_line": 499},
 "facade_variant": "V2",
 "state_passed": "the receiver this (HelpFormatter) and the parameters pw, width, cmdLineSyntax, header, options, leftPad, descPad, "
                 "footer, autoUsage to hop 1; no field read or written by the facade; no write-back",
 "reachability_probe": "testOptionWithoutShortFormat fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "HelpFormatter.printHelp(HelpFormatter.java:503) from HelpFormatterTest.java:441",
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/cli/HelpFormatterTest.java",
             "test_class": "org.apache.commons.cli.HelpFormatterTest", "test_method": "testOptionWithoutShortFormat"},
 "expected_signature": "ComparisonFailure: expected:<...r [-a] [--bbb] [-c]",
 "gold": {"method": "printBanner", "text": GOLD_TEXT,
          "fault": {"old": "        if ((banner != null) && (banner.trim().length() > 0))\n",
                    "new": "        if (banner != null)\n"}},
 "chain": {
   "facade_body": "if ((cmdLineSyntax == null) || (cmdLineSyntax.length() == 0))\n"
                  "        {\n"
                  "            throw new IllegalArgumentException(\"cmdLineSyntax not provided\");\n"
                  "        }\n"
                  "\n"
                  "        Option.printHelpText(this, pw, width, cmdLineSyntax, header, options, leftPad, descPad, footer, autoUsage);",
   "lie": "The sections are first rendered into a single buffer, which is wrapped as a whole and then written to the writer in "
          "one call.",
   "hops": [
     {"file": OPT, "class": "org.apache.commons.cli.Option", "method": "printHelpText",
      "imports": ["java.io.PrintWriter"], "text": HOP1},
     {"file": DP, "class": "org.apache.commons.cli.DefaultParser", "method": "handleHelpSections",
      "imports": ["java.io.PrintWriter"], "text": HOP2},
     {"file": PA, "class": "org.apache.commons.cli.Parser", "method": "processHelpSections",
      "imports": ["java.io.PrintWriter"], "text": HOP3},
     {"file": CL, "class": "org.apache.commons.cli.CommandLine", "method": "printSections",
      "imports": ["java.io.PrintWriter"], "text": HOP4},
     {"file": OB, "class": "org.apache.commons.cli.OptionBuilder", "method": "printBanner", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.cli.Option::hasArgName",
              "org.apache.commons.cli.HelpFormatter::appendOption",
              "org.apache.commons.cli.HelpFormatter::renderOptions",
              "org.apache.commons.cli.HelpFormatter::printOptions"],
 "ownership_reason": "Only the gold decides whether a banner (the header or the footer) is printed. Hop 1 prints the usage "
                     "statement and documents that each print method of the formatter writes at least one complete line; hops 1 "
                     "to 4 each document that the header and the footer are handed on as they are given; hop 4 only places the "
                     "header banner, the options and the footer banner in that order, calling the gold once per banner on separate "
                     "lines. The gold's javadoc promises the lines of the banner wrapped to the width; an empty banner has no lines, "
                     "yet the variant hands it to the formatter and an empty line is printed. No one-line change elsewhere restores "
                     "the help consistently with the documentation on the path: the trigger passes an empty header and an empty "
                     "footer, so a pre-filter of one banner at hop 4 leaves the other empty line; a trim of the values at hops 1-3 "
                     "keeps \"\" as \"\"; replacing the values at hops 1-4 contradicts their 'handed on as they are given'; and "
                     "making HelpFormatter.printWrapped write nothing for an empty text contradicts hop 1's documented property of "
                     "the formatter's print methods, which printUsage and printOptions keep (printOptions writes an empty line even "
                     "for an empty Options, testHeaderStartingWithLineSeparator). The convention that text without content counts "
                     "as absent is pinned outside the gold by production code doing the same step on other text of the help: "
                     "Option.hasArgName (an empty arg name is no arg name), HelpFormatter.appendOption ('non blank argname': an empty "
                     "arg name adds no <...> to the usage clause) and HelpFormatter.renderOptions (an empty arg name adds no <...> "
                     "to the option's entry), with testPrintOptionWithEmptyArgNameUsage passing; the help's layout without blank "
                     "lines between its parts is pinned by testOptionWithoutShortFormat2 and testHelpWithLongOptSeparator, and a "
                     "banner with text is printed as given (testHeaderStartingWithLineSeparator).",
 "ownership_tests": ["org.apache.commons.cli.HelpFormatterTest::testPrintOptionWithEmptyArgNameUsage",
                     "org.apache.commons.cli.HelpFormatterTest::testOptionWithoutShortFormat2",
                     "org.apache.commons.cli.HelpFormatterTest::testHelpWithLongOptSeparator",
                     "org.apache.commons.cli.HelpFormatterTest::testHeaderStartingWithLineSeparator"],
 "compensating": {
   "chain": [
     {"file": CL, "old": "OptionBuilder.printBanner(formatter, pw, width, header);",
      "new": "OptionBuilder.printBanner(formatter, pw, width, (header != null && header.trim().length() == 0) ? null : header);",
      "why": "hop 4 drops an empty header before handing it to the banner step"},
     {"file": CL, "old": "OptionBuilder.printBanner(formatter, pw, width, footer);",
      "new": "OptionBuilder.printBanner(formatter, pw, width, (footer != null && footer.trim().length() == 0) ? null : footer);",
      "why": "hop 4 drops an empty footer before handing it to the banner step"},
     {"file": PA, "old": "CommandLine.printSections(formatter, pw, width, header, options, leftPad, descPad, footer);",
      "new": "CommandLine.printSections(formatter, pw, width, header == null ? null : header.trim(), options, leftPad, descPad, footer == null ? null : footer.trim());",
      "why": "hop 3 trims the header and the footer before they are placed"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted: Option (hop 1, 705 lines), DefaultParser (hop 2, 689), Parser (hop 3, 430), CommandLine (hop 4, 388), "
               "OptionBuilder (hop 5, gold, 375; the smallest host). The allowed candidate's file HelpFormatter.java is excluded. All "
               "five are public top-level classes of org.apache.commons.cli in which a static method compiles (Parser is abstract, "
               "OptionBuilder final with a private constructor; neither affects a static method). Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 2295 + 100 + i (as mr3_spec.py inserts them): hop 1 after `hashCode` "
               "(seed 2395), hop 2 after `parse` (2396), hop 3 after `parse` (2397), hop 4 after `getOptionValue` (2398), hop 5 "
               "after `hasOptionalArg` (2399). All hosts share the facade's package, so the facade calls hop 1 by its simple name; "
               "hops 1-4 import java.io.PrintWriter; OptionBuilder has no import section, so the gold names java.io.PrintWriter "
               "by its fully-qualified name.",
}
