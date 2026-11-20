"""Main run Cli-8__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Cli-8; the real bug modified HelpFormatter, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE section 1: pool v2
found no strictly tested public static method in HelpFormatter).

Facade: HelpFormatter.printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean) (the 29-line overload with
autoUsage; the only allowed candidate of the task record, facade_planned_by null, no facade reuse). The other printHelp overloads,
printUsage, printOptions, printWrapped, renderOptions and renderWrappedText stay intact.
Original computation: an empty or null cmdLineSyntax is an IllegalArgumentException ("cmdLineSyntax not provided"); the usage
statement is printed (generated from the options with printUsage(pw, width, cmdLineSyntax, options) when autoUsage, else
printUsage(pw, width, cmdLineSyntax)); a header that is not null and not blank is printed wrapped (printWrapped(pw, width, header));
the options table is printed (printOptions -> renderOptions: the options sorted by the private OptionComparator; per option an entry
column of leftPad spaces, then three spaces and the long prefix and long name for an option with no short name, else the short prefix
and short name and, if it has a long name, ',' long prefix and long name; ' <argName>' or ' ' for an option with an argument; every
column padded to the widest, descPad spaces, the description; each entry wrapped with renderWrappedText at tab stop widest + descPad;
the entries joined by the new line and the table printed with println; an empty table prints an empty line); a footer that is not
null and not blank is printed wrapped.

facade_variant: V2+V4. V2 (receiver as parameter): the chain needs the formatter's public methods (printUsage, printWrapped,
getOptPrefix, getLongOptPrefix), so the facade passes `this` (typed HelpFormatter) to hop 1 with its own parameters. V4 (pre-computed
private helper): the table's order is the private nested comparator OptionComparator, which no hop may name; the facade creates it
(`new OptionComparator()`) and passes it down as a java.util.Comparator (the facade keeps that much computation). No private method of
HelpFormatter is called by a hop and no private logic is copied into a hop; the protected renderOptions/renderWrappedText/
createPadding are not called by the hops (they use only the public printWrapped and public getters; padding is written with spaces in
a loop). No package-private member of another class is used by a hop (Options.getOptions() is public; Option.getKey() is not used).
state_passed: the receiver `this` and the facade's parameters (pw, width, cmdLineSyntax, header, options, leftPad, descPad, footer,
autoUsage), plus the private comparator instance new OptionComparator(), handed to hop 1; no field is read or written by the facade,
no write-back. The facade body is the original guard plus one call to hop 1. No visibility is widened, no type is added, no
signature, modifier, override or throws clause changes, no reflection, no test edit.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Cli-8-probe of the fixture, the first statement of
the facade was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.cli.BugsTest::test19383`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
HelpFormatter.printHelp(HelpFormatter.java:440) called from BugsTest.test19383(BugsTest.java:530). The full suite with the probe has
exactly 4 failing tests, all PROBE-REACHED: BugsTest::test19383, BugsTest::test21215, BugsTest::test13666 (through printHelp(String,
Options) -> printHelp(int, ...) -> the facade; reported as 'Unexpected Exception: PROBE-REACHED') and BugCLI18Test::testCLI18 (no
assertion). The facade is reached directly by the trigger.

Hosts (host_mode = "largest5": no other public class of the checkout reaches 1500 lines; hosts_hop_order of batch9_tasks.json, used
in that order, none substituted):
  hop 1 Option        680 lines  printHelpSections   plumbing: the four sections in order (usage statement, generated or plain;
                                                     a header that is not null and not blank; the options table; a footer that
                                                     is not null and not blank)
  hop 2 Parser        417 lines  printOptionTable    aggregation: the options as a list (Options.getOptions()); an empty set
                                                     prints an empty line
  hop 3 OptionBuilder 372 lines  printSortedOptions  placement: sorts the list into the given order
  hop 4 CommandLine   320 lines  printOptionList     pass-through
  hop 5 PosixParser   311 lines  printOptionLines    GOLD: one entry per option (the entry column of names and argument, the
                                                     widest column, the description column, each entry printed wrapped)
Host newline counts 680, 417, 372, 320, 311; the smallest host (and the gold host) is PosixParser with 311 lines (C10F addendum
section 1: hosts under 1500 lines are expected in this regime).
The correct configuration prints exactly what the original prints for the default new line (each entry is printed with
printWrapped, i.e. renderWrappedText + println, where the original joins entries with defaultNewLine and ends with println; the two
differ only after setNewLine, which no test combines with printHelp). Checked on the four reaching tests: all pass on the correct
configuration.

Fault (one-line omission of a special-case step in the gold): the three-space indent of an option that has no short name is dropped
from the entry column (`column.append("   ").append(formatter.getLongOptPrefix()).append(option.getLongOpt());` becomes
`column.append(formatter.getLongOptPrefix()).append(option.getLongOpt());`), so a long-only option's '--name' starts in the column of
the short names instead of under the long names of the options written as '-s,--name'. The gold then reads as the ordinary routine
"short name with its long name, or the long name alone". Trigger: the EXISTING test BugsTest::test19383 (options -a/--aaa, --bbb,
-c; printHelp(..., 2, 2, "", true)); the expected entry "     --bbb  bbbbbbb" is printed as "  --bbb     bbbbbbb". It is the only
test with an assertion whose printHelp output has a long-only option: test13666 has only -d, test21215 has no option, testCLI18 has
--bbb but no assertion; the tests of printOptions/renderOptions (HelpFormatterTest) use the intact renderOptions. Gate G5 checks the
full suite.

The gold's javadoc states the idiomatic contract (it prints the help's options table: per option the names and argument, then the
description at one column for all entries, wrapped with continuation lines at that column) and is silent on the indent of an option
without a short name. The formatter's table convention is pinned outside the gold: the intact sibling HelpFormatter.renderOptions does
the same step (`optBuf.append(lpad).append("   " + defaultLongOptPrefix).append(option.getLongOpt())` for an option whose getOpt() is
null) and is the body of the public HelpFormatter.printOptions; HelpFormatterTest::testPrintOptions pins the table layout on that path,
and BugsTest::test21215 passes through the chain (an empty table). BugsTest::test13666 also passes through the chain in the full
suite (an entry with an argument name) but is not an ownership test: it depends on OptionBuilder's static state left by earlier tests
and fails when run alone on the unmodified baseline too (' -d    dir' for ' -d <arg>   dir').

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: formatter supplies both prefixes and the printing; pw and width go to every printWrapped; options drives both loops;
     leftPad sets the leading spaces; descPad sets the tab stop.
  T2 absent: column, widest, tabStop, next, line and option all reach printWrapped; widest is assigned in the first loop; the
     getOpt()==null branch and the else write different names; hasLongOpt, hasArg, the hasArgName ternary and the description test
     each change the entry; no local is frozen or dead.
  T3 absent: both names (short, long) are written in every case where they exist; both argument forms (named, unnamed) are written;
     the gold names no class it handles in part.
  T4 absent: 'one entry per option, in the order of the list', 'its names and argument', 'its description, which starts at the same
     column for every entry' (tabStop), 'wrapped ... continuation lines indented to that column' (printWrapped(pw, width, tabStop,
     ...)) and the @param clauses are met by lines of the body.
 Variant gold (javadoc, signature, the two loops, `column.append(formatter.getLongOptPrefix()).append(option.getLongOpt());` in the
 branch of an option without a short name):
  T1 absent: every parameter still changes the output as above.
  T2 absent: unchanged from the correct gold; the getOpt()==null branch still writes the long name, the else branch the short name
     (and the long name), so the decision has two different effects; no local is frozen or dead.
  T3 absent: no indent or alignment treatment exists in the variant at all for any kind of option ('No member handled'); the short
     and the long name are both written where present; named and unnamed arguments are both written.
  T4 absent: no phrase names an indent, an alignment of names or a column for long names; 'the same column' concerns the
     description, which is met; identifiers (column, widest, tabStop, line, next) name nothing the body does not meet; no comment.

Single owner: only the gold builds the entries of the table, and it prints them to the writer itself; hops 2-4 pass the options
along (hop 2 lists them, hop 3 sorts them, hop 4 passes them on) and hop 1 prints the other sections. No caller can pre-filter or
recover the indent: the options' names are what the gold reads, leftPad is one value for all entries, and the gold's output goes
straight to the writer. Declared alternatives (G9): hop 3 sorts in the reverse order; hop 1 tests the header without trimming it; hop 2
starts the table with an empty line. None makes the trigger pass.
Recorded bypasses: B-0 the facade (its original body), hop 1 or hop 2 calls the intact formatter.printOptions(pw, width, options,
leftPad, descPad) in place of the chain below it, discarding the gold.

Lie: the facade's javadoc claims the help is first rendered into a single buffer that is then written to the writer in one call; the
chain writes each section (and each entry of the table) to the writer as it is produced. It names neither the table's layout, nor
long-only options, nor any hop."""

HF = "src/java/org/apache/commons/cli/HelpFormatter.java"
OPT = "src/java/org/apache/commons/cli/Option.java"
PAR = "src/java/org/apache/commons/cli/Parser.java"
OB = "src/java/org/apache/commons/cli/OptionBuilder.java"
CL = "src/java/org/apache/commons/cli/CommandLine.java"
PP = "src/java/org/apache/commons/cli/PosixParser.java"

GOLD_TEXT = '''/**
 * <p>Prints the options table of a help message, one entry per option
 * in the order of the list: the option's names and argument, then its
 * description, which starts at the same column for every entry. An
 * entry longer than the width is wrapped, and its continuation lines are
 * indented to that column.</p>
 *
 * @param formatter the formatter whose prefixes and printing are used
 * @param pw the writer to which the entries are written
 * @param width the number of characters to be displayed on each line
 * @param options the options to print
 * @param leftPad the number of characters of padding to be prefixed
 * to each entry
 * @param descPad the number of characters of padding to be prefixed
 * to each description
 */
public static void printOptionLines(HelpFormatter formatter, PrintWriter pw, int width, List options, int leftPad, int descPad)
{
    List columns = new ArrayList();
    int widest = 0;

    for (Iterator it = options.iterator(); it.hasNext();)
    {
        Option option = (Option) it.next();
        StringBuffer column = new StringBuffer();

        while (column.length() < leftPad)
        {
            column.append(' ');
        }

        if (option.getOpt() == null)
        {
            column.append("   ").append(formatter.getLongOptPrefix()).append(option.getLongOpt());
        }
        else
        {
            column.append(formatter.getOptPrefix()).append(option.getOpt());

            if (option.hasLongOpt())
            {
                column.append(',').append(formatter.getLongOptPrefix()).append(option.getLongOpt());
            }
        }

        if (option.hasArg())
        {
            column.append(option.hasArgName() ? " <" + option.getArgName() + ">" : " ");
        }

        columns.add(column);
        widest = Math.max(widest, column.length());
    }

    int tabStop = widest + descPad;
    Iterator next = columns.iterator();

    for (Iterator it = options.iterator(); it.hasNext();)
    {
        Option option = (Option) it.next();
        StringBuffer line = (StringBuffer) next.next();

        while (line.length() < tabStop)
        {
            line.append(' ');
        }

        if (option.getDescription() != null)
        {
            line.append(option.getDescription());
        }

        formatter.printWrapped(pw, width, tabStop, line.toString());
    }
}'''

HOP1 = '''/**
 * <p>Prints the help for <code>options</code> with the specified
 * command line syntax: the usage statement, the header, the options
 * table and the footer. A header or footer that is null or blank is
 * not printed.</p>
 *
 * @param formatter the formatter whose settings and printing are used
 * @param pw the writer to which the help is written
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
 * @param order the order in which the options are listed
 */
public static void printHelpSections(HelpFormatter formatter, PrintWriter pw, int width, String cmdLineSyntax, String header,
                                     Options options, int leftPad, int descPad, String footer, boolean autoUsage,
                                     Comparator order)
{
    if (autoUsage)
    {
        formatter.printUsage(pw, width, cmdLineSyntax, options);
    }
    else
    {
        formatter.printUsage(pw, width, cmdLineSyntax);
    }

    if ((header != null) && (header.trim().length() > 0))
    {
        formatter.printWrapped(pw, width, header);
    }

    Parser.printOptionTable(formatter, pw, width, options, leftPad, descPad, order);

    if ((footer != null) && (footer.trim().length() > 0))
    {
        formatter.printWrapped(pw, width, footer);
    }
}'''

HOP2 = '''/**
 * <p>Prints the options table of a help message for the specified
 * options, listed in the given order. A set with no options prints an
 * empty line.</p>
 *
 * @param formatter the formatter whose settings and printing are used
 * @param pw the writer to which the table is written
 * @param width the number of characters to be displayed on each line
 * @param options the options to print
 * @param leftPad the number of characters of padding to be prefixed
 * to each entry
 * @param descPad the number of characters of padding to be prefixed
 * to each description
 * @param order the order in which the options are listed
 */
public static void printOptionTable(HelpFormatter formatter, PrintWriter pw, int width, Options options, int leftPad,
                                    int descPad, Comparator order)
{
    List entries = new ArrayList(options.getOptions());

    if (entries.isEmpty())
    {
        pw.println();
        return;
    }

    OptionBuilder.printSortedOptions(formatter, pw, width, entries, leftPad, descPad, order);
}'''

HOP3 = '''/**
 * <p>Sorts the specified options into the given order and prints the
 * options table of a help message for them.</p>
 *
 * @param formatter the formatter whose settings and printing are used
 * @param pw the writer to which the table is written
 * @param width the number of characters to be displayed on each line
 * @param options the options to print, sorted in place
 * @param leftPad the number of characters of padding to be prefixed
 * to each entry
 * @param descPad the number of characters of padding to be prefixed
 * to each description
 * @param order the order in which the options are listed
 */
public static void printSortedOptions(HelpFormatter formatter, java.io.PrintWriter pw, int width, java.util.List options,
                                      int leftPad, int descPad, java.util.Comparator order)
{
    java.util.Collections.sort(options, order);
    CommandLine.printOptionList(formatter, pw, width, options, leftPad, descPad);
}'''

HOP4 = '''/**
 * <p>Prints the options table of a help message for the specified
 * options, in the order of the list.</p>
 *
 * @param formatter the formatter whose settings and printing are used
 * @param pw the writer to which the table is written
 * @param width the number of characters to be displayed on each line
 * @param options the options to print
 * @param leftPad the number of characters of padding to be prefixed
 * to each entry
 * @param descPad the number of characters of padding to be prefixed
 * to each description
 */
public static void printOptionList(HelpFormatter formatter, PrintWriter pw, int width, List options, int leftPad, int descPad)
{
    PosixParser.printOptionLines(formatter, pw, width, options, leftPad, descPad);
}'''

DESIGN = {
 "instance": "Cli-8", "project": "Cli", "bug_id": 8, "seed": 5952,
 "src_root": "src/java", "test_root": "src/test",
 "cell": "C10i", "facade_variant": "V2+V4",
 "state_passed": "the receiver this (HelpFormatter) and the facade's parameters pw, width, cmdLineSyntax, header, options, leftPad, "
                 "descPad, footer, autoUsage, plus new OptionComparator() (the private nested comparator, as a java.util.Comparator), "
                 "passed to hop 1; no field read or written by the facade, no write-back",
 "host_mode": "largest5", "host_lines": [680, 417, 372, 320, 311],
 "reachability_probe": "facade first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Cli-8-probe: BugsTest::test19383 fails with PROBE-REACHED at "
                       "HelpFormatter.printHelp(HelpFormatter.java:440); full suite: 4 failing (test19383, test21215, test13666, "
                       "BugCLI18Test::testCLI18), all PROBE-REACHED",
 "facade": {"file": HF, "class": "org.apache.commons.cli.HelpFormatter", "method": "printHelp", "near_line": 436},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/cli/BugsTest.java",
             "test_class": "org.apache.commons.cli.BugsTest", "test_method": "test19383"},
 "expected_signature": "[--bbb   ]  bbbbbbb",
 "gold": {"method": "printOptionLines", "text": GOLD_TEXT,
          "fault": {"old": "                column.append(\"   \").append(formatter.getLongOptPrefix()).append(option.getLongOpt());",
                    "new": "                column.append(formatter.getLongOptPrefix()).append(option.getLongOpt());"}},
 "chain": {
   "facade_body": "if ((cmdLineSyntax == null) || (cmdLineSyntax.length() == 0))\n"
                  "        {\n"
                  "            throw new IllegalArgumentException(\"cmdLineSyntax not provided\");\n"
                  "        }\n\n"
                  "        Option.printHelpSections(this, pw, width, cmdLineSyntax, header, options, leftPad, descPad, footer,\n"
                  "                                 autoUsage, new OptionComparator());",
   "lie": "The help is first rendered into a single buffer, which is then written to the writer in one call.",
   "hops": [
     {"file": OPT, "class": "org.apache.commons.cli.Option", "method": "printHelpSections",
      "imports": ["java.io.PrintWriter", "java.util.Comparator"], "text": HOP1},
     {"file": PAR, "class": "org.apache.commons.cli.Parser", "method": "printOptionTable",
      "imports": ["java.io.PrintWriter", "java.util.ArrayList", "java.util.Comparator"], "text": HOP2},
     {"file": OB, "class": "org.apache.commons.cli.OptionBuilder", "method": "printSortedOptions",
      "imports": [], "text": HOP3},
     {"file": CL, "class": "org.apache.commons.cli.CommandLine", "method": "printOptionList",
      "imports": ["java.io.PrintWriter"], "text": HOP4},
     {"file": PP, "class": "org.apache.commons.cli.PosixParser", "method": "printOptionLines",
      "imports": ["java.io.PrintWriter", "java.util.List"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.cli.HelpFormatter::renderOptions",
              "org.apache.commons.cli.HelpFormatter::printOptions"],
 "ownership_reason": "Only the gold builds the entries of the options table (the entry column of each option's names and argument, "
                     "the widest column, the description column) and it prints each entry to the writer itself. Hop 2 only lists the "
                     "options (an empty set prints an empty line), hop 3 only sorts them, hop 4 passes them on, and hop 1 prints the "
                     "other sections of the help; no caller can pre-filter or recover the entry column, because the gold reads the "
                     "names from the options, leftPad is one value for every entry, and the gold's output goes straight to the "
                     "writer. In the formatter's options table an option with no short name is indented by three spaces so that its "
                     "long name stands under the long names of the options written as '-s,--name'; the variant writes it in the "
                     "column of the short names. The convention is pinned outside the gold: the intact sibling "
                     "HelpFormatter.renderOptions does the same step (\"   \" + defaultLongOptPrefix for an option whose getOpt() is "
                     "null) and is the body of the public HelpFormatter.printOptions; HelpFormatterTest::testPrintOptions pins the "
                     "table layout on that path, and BugsTest::test21215 (an empty table) passes through the chain.",
 "ownership_tests": ["org.apache.commons.cli.HelpFormatterTest::testPrintOptions",
                     "org.apache.commons.cli.BugsTest::test21215"],
 "compensating": {
   "chain": [
     {"file": OB, "old": "    java.util.Collections.sort(options, order);",
      "new": "    java.util.Collections.sort(options, java.util.Collections.reverseOrder(order));",
      "why": "hop 3 sorts the options in the reverse order"},
     {"file": OPT, "old": "    if ((header != null) && (header.trim().length() > 0))",
      "new": "    if ((header != null) && (header.length() > 0))",
      "why": "hop 1 tests the header without trimming it"},
     {"file": PAR, "old": "    if (entries.isEmpty())\n        {\n            pw.println();\n            return;\n        }",
      "new": "    pw.println();\n\n        if (entries.isEmpty())\n        {\n            return;\n        }",
      "why": "hop 2 starts the table with an empty line"},
   ],
 },
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, used in that order; none substituted, none drawn by this "
               "builder): Option (hop 1, 680 lines), Parser (hop 2, 417), OptionBuilder (hop 3, 372), CommandLine (hop 4, 320), "
               "PosixParser (hop 5, gold, 311; the smallest host). All five are public top-level classes of "
               "org.apache.commons.cli (Parser is abstract) in which a public static method compiles; the facade's class "
               "HelpFormatter (the only allowed candidate's file) is excluded. Anchors from stageB_lib.pick_insertion_anchor with "
               "the instance seed 5952 + 100 + i, as mr3_spec.py inserts them: hop 1 after hashCode (seed 6052), hop 2 after "
               "parse (6053), hop 3 after hasArgs (6054), hop 4 after iterator (6055), hop 5 after processSingleHyphen (6056). "
               "All hosts share the facade's package, so no host is imported; the hops use only public members of HelpFormatter, "
               "Options and Option. OptionBuilder has no import statements, so hop 3 names java.io.PrintWriter, java.util.List, "
               "java.util.Comparator and java.util.Collections by their qualified names; the other hops import java.io.PrintWriter "
               "and the java.util types they need. Static fields of OptionBuilder (description, argName, required, ...) and the "
               "instance fields named options in Parser, CommandLine and PosixParser are not used by the hops.",
}
