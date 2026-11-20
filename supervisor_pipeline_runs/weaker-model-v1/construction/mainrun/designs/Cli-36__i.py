"""Main run Cli-36__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Cli-36; the real bug modified OptionGroup and Options; OptionGroup is the facade's class). No static pair exists (pool v2:
no_tested_static; BUILD_BRIEF_C10I_B8_NOTE.md section 1).

Facade: OptionGroup.toString() (instance method; the only allowed target of batch9_tasks.json for Cli-36__i, BATCH9_PREREGISTRATION.md
rank 327; facade_planned_by null, no facade reuse).
Original computation: "[" + the options of the group (getOptions(), the values of the LinkedHashMap optionMap, in the order they were
added), each written as "-" + its short name, or "--" + its long name when it has no short name, then " " + its description when the
description is not null, consecutive options separated by ", " + "]".

facade_variant: V2 (receiver as parameter). state_passed: the receiver `this` (typed OptionGroup) is handed to hop 1, which calls its
public method getOptions(); no field is read by the facade, no field is written, no write-back. The facade body is one call to hop 1 (the
original had no argument guard). No visibility is widened, no type is added, no signature, modifier, @Override or throws clause changes, no
reflection, no test edit. toString calls no private method, so V4 does not apply; all hops are in the facade's package
org.apache.commons.cli and use only public types (OptionGroup, Option, Collection, Iterable, StringBuilder), so V3/V5 do not arise.

Redistribution of the computation: hop 1 reads the options of the group; hop 2 places the enclosing square brackets; hop 3 creates the
buffer and returns its text; hop 4 passes the options and the buffer on; the gold (hop 5) is one pass over the options writing each one's
command-line form (hyphen prefix, short or long name, optional description) and the ", " separator.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Cli-36-probe of the fixture, the first statement of
OptionGroup.toString() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; full suite
`defects4j test`: 6 failing tests, each with java.lang.IllegalStateException: PROBE-REACHED: OptionGroupTest::testToString (at
OptionGroup.toString(OptionGroup.java:142) called from OptionGroupTest.java:234), BasicParserTest / DefaultParserTest / GnuParserTest /
PosixParserTest ::testMissingRequiredGroup and bug.BugsTest::test13935 (these five reach toString only through the message of a
MissingOptionException for a missing required group and assert nothing about the text). The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; batch9_tasks.json hosts_hop_order, used in that order, none substituted; OptionGroup.java excluded):
  hop 1 HelpFormatter  1094 lines  groupSummary     plumbing: reads the options of the group (V2 receiver)
  hop 2 Option         1006 lines  bracketedList    placement: the enclosing square brackets
  hop 3 DefaultParser   694 lines  optionListText   aggregation: creates the buffer and returns its text
  hop 4 Parser          430 lines  appendOptions    pass-through
  hop 5 OptionBuilder   396 lines  listOptions      GOLD: one pass over the options writing each one's command-line form
Host newline counts 1094, 1006, 694, 430, 396; the smallest host (and the gold host) is OptionBuilder with 396 lines (C10F addendum
section 1: hosts under 1500 lines are expected in this regime). The correct configuration returns the original text for every group
(same order, same per-option form, same separator and brackets).

Fault (one-line omission in the gold's short/long-name decision): the second hyphen of a long name is dropped (the line
`buff.append('-');` inside `if (name == null)` is removed), so an option without a short name is written "-foo" instead of "--foo". The
gold then reads as the ordinary routine "a hyphen, then the short name or, failing it, the long name". Trigger: the EXISTING test
OptionGroupTest::testToString; for group1 (two options with only long names) toString gives "[-foo Foo, -bar Bar]", which equals neither
accepted order, so assertEquals("[--foo Foo, --bar Bar]", ...) fails: expected:<[-[-foo Foo, -]-bar Bar]> but was:<[-[foo Foo, ]-bar
Bar]>. It is the only test that asserts the text of an option group; the five other tests that reach toString (above) only build an
exception message and pass; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract ("in their command-line form", each option "by its short name or, if it has none, by
its long name") and is silent on the prefixes. In this library the command-line form of an option is "-" + its short name or "--" + its
long name; the variant writes a long name with one hyphen on the trigger input. The convention is pinned outside the gold: the intact
HelpFormatter.appendOption writes `"--" + long name` for an option without a short name (used in production by HelpFormatter.printUsage
and the usage line of printHelp), HelpFormatter.renderOptions writes getLongOptPrefix() (DEFAULT_LONG_OPT_PREFIX = "--") before every
long name, and PosixParser.flatten rewrites a matched long option to `"--" + long name`; passing tests: HelpFormatterTest
::testOptionWithoutShortFormat ("[--bbb]"), ::testOptionWithoutShortFormat2 ("[--config <arg>]"), ::testUsageWithLongOptSeparator
("[--age=<arg>]") and ::testPrintOptions (long names after "--" in the option list).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: options supplies every option written; buff receives every append; neither is only argument-checked.
  T2 absent: option is the loop element; name is read by an append and reassigned in the branch; separator starts "" and is reassigned
     to ", " in the loop; the `name == null` branch writes a hyphen and changes name, the description branch appends; nothing dead or
     frozen.
  T3 absent: short and long name (the pair) are both handled (short name, or long name when there is none); the description is written
     when present; no class named in the gold's text is handled in part.
  T4 absent: 'separated by a comma and a space' is met by `separator = ", "`; 'by its short name or, if it has none, by its long name'
     is met by the branch; 'followed by a space and its description if it has one' is met; 'in their command-line form' is a general
     description that the hyphen-prefixed name addresses; @param clauses are met.
 Variant gold (javadoc, signature, the loop, `buff.append(separator).append('-')`, `if (name == null) { name = option.getLongOpt(); }`,
 the description branch, `separator = ", "`):
  T1 absent: options and buff each change the result; none is read only in a check.
  T2 absent: name is assigned in the branch and appended; separator is reassigned in the loop and appended; the `name == null` branch
     changes name (live); the description branch appends (live); no local is frozen or dead.
  T3 absent: both halves of the short/long pair are handled (fallback to the long name); every option gets the same hyphen prefix, so no
     member of a set gets a treatment its sibling lacks; the gold names no class it handles in part.
  T4 absent: 'separated by a comma and a space', 'by its short name or, if it has none, by its long name' and 'followed by a space and its
     description if it has one' are each met by a line of the body; 'in their command-line form' is a general description (like 'the
     quoted-printable form') addressed by the hyphen-prefixed name, with no count of hyphens stated; no inline comment; identifiers
     (options, buff, separator, option, name) name nothing the body does not meet.

Single owner: only the gold writes the form of an option (prefix, name, description); hop 1 passes the group's options, hop 2 only adds
the enclosing brackets, hop 3 only creates the buffer and returns its text, hop 4 only passes the options and buffer on. Once the gold has
written "-foo", "--foo" can appear only if a caller rewrites the gold's text or replaces the gold. Declared alternatives (G9): hop 2 opens
the list with "[-"; hop 3 starts the buffer with a hyphen; hop 2 rewrites ", -" as ", --". None makes the trigger pass (each changes at
most one option's prefix, or every short name as well).
Recorded bypasses:
 B-0 the facade's original body, or a hop re-implementing the per-option loop (as OptionGroup.toString did), discards the gold.
 B-1 hop 2 rewrites the gold's text with a regular expression that doubles the hyphen before names of two or more characters
     (e.g. replaceAll("(\\\\[|, )-(?=\\\\w\\\\w)", "$1--")): it overwrites what the gold wrote and depends on name length, not on whether
     the option has a short name.

Lie: the facade's javadoc claims the options are first sorted by their keys, so that the text does not depend on the order in which they
were added; no step of the chain sorts (the group's options are listed in insertion order). It names neither hyphens, nor long names, nor
any hop. Placement: the facade's javadoc is separated from its header by the existing @Override annotation, so the recipe's
rewrite_facade (which appends the lie only to a javadoc immediately followed by the header) finds no javadoc to extend; the lie sentence
is therefore placed by a comment-only pre_edit, directly after the javadoc's first sentence, in the facade's documentation voice (the
annotation itself is kept unchanged, as the addendum requires). The chain's "lie" field holds the same sentence for the record; the
recipe adds no second copy."""

OG = "src/main/java/org/apache/commons/cli/OptionGroup.java"
HF = "src/main/java/org/apache/commons/cli/HelpFormatter.java"
OPT = "src/main/java/org/apache/commons/cli/Option.java"
DP = "src/main/java/org/apache/commons/cli/DefaultParser.java"
PA = "src/main/java/org/apache/commons/cli/Parser.java"
OB = "src/main/java/org/apache/commons/cli/OptionBuilder.java"

GOLD_TEXT = '''/**
 * Appends options to a buffer in their command-line form, separated by a
 * comma and a space.
 *
 * <p>Each option is written by its short name or, if it has none, by its
 * long name, followed by a space and its description if it has one.</p>
 *
 * @param options the options to append
 * @param buff the buffer to append to
 */
public static void listOptions(Iterable<Option> options, StringBuilder buff)
{
    String separator = "";
    for (Option option : options)
    {
        buff.append(separator).append('-');
        String name = option.getOpt();
        if (name == null)
        {
            buff.append('-');
            name = option.getLongOpt();
        }
        buff.append(name);
        if (option.getDescription() != null)
        {
            buff.append(' ').append(option.getDescription());
        }
        separator = ", ";
    }
}'''

HOP1 = '''/**
 * Returns the text of an option group: its options within square
 * brackets.
 *
 * @param group the group to describe
 * @return the text of the group
 */
public static String groupSummary(OptionGroup group)
{
    return Option.bracketedList(group.getOptions());
}'''

HOP2 = '''/**
 * Returns a list of options as text within square brackets.
 *
 * @param options the options to list
 * @return the bracketed list of the options
 */
public static String bracketedList(Collection<Option> options)
{
    return "[" + DefaultParser.optionListText(options) + "]";
}'''

HOP3 = '''/**
 * Returns a list of options as text, without enclosing brackets.
 *
 * @param options the options to list
 * @return the text of the options
 */
public static String optionListText(Collection<Option> options)
{
    StringBuilder buff = new StringBuilder();
    Parser.appendOptions(options, buff);
    return buff.toString();
}'''

HOP4 = '''/**
 * Appends a list of options to a buffer.
 *
 * @param options the options to append
 * @param buff the buffer to append to
 */
public static void appendOptions(Collection<Option> options, StringBuilder buff)
{
    OptionBuilder.listOptions(options, buff);
}'''

DESIGN = {
 "instance": "Cli-36", "project": "Cli", "bug_id": 36, "seed": 4991,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (OptionGroup) passed to hop 1, which calls its public getOptions(); no field read by the facade, "
                 "no write-back",
 "host_mode": "largest5", "host_lines": [1094, 1006, 694, 430, 396],
 "reachability_probe": "OptionGroup.toString() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Cli-36-probe: full suite, 6 failing with PROBE-REACHED: OptionGroupTest::testToString "
                       "(OptionGroup.java:142 from OptionGroupTest.java:234) and {Basic,Default,Gnu,Posix}ParserTest::"
                       "testMissingRequiredGroup, bug.BugsTest::test13935 (exception message only, no text asserted)",
 "facade": {"file": OG, "class": "org.apache.commons.cli.OptionGroup", "method": "toString", "near_line": 140},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/cli/OptionGroupTest.java",
             "test_class": "org.apache.commons.cli.OptionGroupTest", "test_method": "testToString"},
 "expected_signature": "but was:<[-[foo Foo, ]-bar Bar]>",
 "gold": {"method": "listOptions", "text": GOLD_TEXT,
          "fault": {"old": "            if (name == null)\n            {\n                buff.append('-');\n"
                           "                name = option.getLongOpt();",
                    "new": "            if (name == null)\n            {\n                name = option.getLongOpt();"}},
 "pre_edits": {
   "chain": [{"file": OG,
              "old": "     * Returns the stringified version of this OptionGroup.\n",
              "new": "     * Returns the stringified version of this OptionGroup.\n"
                     "     * The options are first sorted by their keys, so that the text does not\n"
                     "     * depend on the order in which they were added.\n"}],
 },
 "chain": {
   "facade_body": "return HelpFormatter.groupSummary(this);",
   "lie": "The options are first sorted by their keys, so that the text does not depend on the order in which they were added.",
   "hops": [
     {"file": HF, "class": "org.apache.commons.cli.HelpFormatter", "method": "groupSummary", "imports": [], "text": HOP1},
     {"file": OPT, "class": "org.apache.commons.cli.Option", "method": "bracketedList",
      "imports": ["java.util.Collection"], "text": HOP2},
     {"file": DP, "class": "org.apache.commons.cli.DefaultParser", "method": "optionListText",
      "imports": ["java.util.Collection"], "text": HOP3},
     {"file": PA, "class": "org.apache.commons.cli.Parser", "method": "appendOptions",
      "imports": ["java.util.Collection"], "text": HOP4},
     {"file": OB, "class": "org.apache.commons.cli.OptionBuilder", "method": "listOptions", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.cli.HelpFormatter::appendOption",
              "org.apache.commons.cli.HelpFormatter::renderOptions",
              "org.apache.commons.cli.PosixParser::flatten"],
 "ownership_reason": "Only the gold writes the form of each option of the group: a hyphen prefix, the short name or, when there is "
                     "none, the long name, and the description; hop 1 passes the group's options, hop 2 only adds the enclosing "
                     "square brackets, hop 3 only creates the buffer and returns its text, hop 4 only passes the options and the "
                     "buffer on. Once the gold has written a long name after a single hyphen, the double hyphen can appear only if a "
                     "caller rewrites the gold's text or replaces the gold. The gold's javadoc promises the options 'in their "
                     "command-line form'; in this library that form is '-' + short name or '--' + long name, and the variant writes "
                     "'-foo'. The convention is pinned outside the gold: the intact HelpFormatter.appendOption writes '--' + the long "
                     "name of an option without a short name (used by printUsage and by the usage line of printHelp), "
                     "HelpFormatter.renderOptions writes getLongOptPrefix() (DEFAULT_LONG_OPT_PREFIX '--') before every long name, "
                     "and PosixParser.flatten rewrites a matched long option as '--' + its long name; HelpFormatterTest "
                     "testOptionWithoutShortFormat ('[--bbb]'), testOptionWithoutShortFormat2 ('[--config <arg>]'), "
                     "testUsageWithLongOptSeparator ('[--age=<arg>]') and testPrintOptions pass.",
 "ownership_tests": ["org.apache.commons.cli.HelpFormatterTest::testOptionWithoutShortFormat",
                     "org.apache.commons.cli.HelpFormatterTest::testOptionWithoutShortFormat2",
                     "org.apache.commons.cli.HelpFormatterTest::testUsageWithLongOptSeparator",
                     "org.apache.commons.cli.HelpFormatterTest::testPrintOptions"],
 "compensating": {
   "chain": [
     {"file": OPT, "old": "return \"[\" + DefaultParser.optionListText(options) + \"]\";",
      "new": "return \"[-\" + DefaultParser.optionListText(options) + \"]\";",
      "why": "hop 2 opens the list with a bracket and a hyphen"},
     {"file": DP, "old": "StringBuilder buff = new StringBuilder();",
      "new": "StringBuilder buff = new StringBuilder(\"-\");",
      "why": "hop 3 starts the buffer with a hyphen"},
     {"file": OPT, "old": "return \"[\" + DefaultParser.optionListText(options) + \"]\";",
      "new": "return \"[\" + DefaultParser.optionListText(options).replace(\", -\", \", --\") + \"]\";",
      "why": "hop 2 doubles the hyphen after each separator"},
   ],
 },
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, used in that order; none substituted, none drawn by this "
               "builder; the allowed candidate's file OptionGroup.java excluded): HelpFormatter (hop 1, 1094 lines), Option (hop 2, "
               "1006), DefaultParser (hop 3, 694), Parser (hop 4, 430; public abstract class, deprecated), OptionBuilder (hop 5, gold, "
               "396; public final deprecated class with a private constructor; the smallest host). All five are public top-level "
               "classes of org.apache.commons.cli in which a public static method compiles. Anchors from stageB_lib.pick_anchor "
               "(host_search.pick_insertion_anchor) with seed 4991 + 100 + i, as mr3_spec.py inserts them: hop 1 after printHelp "
               "(line 424, seed 5091), hop 2 after setDescription (5092), hop 3 after parse (5093), hop 4 after parse (5094), hop 5 "
               "after withLongOpt (5095). All hops are in the facade's package, so no host import is needed; Option, DefaultParser "
               "and Parser import java.util.Collection (OptionBuilder has no import, so the gold takes java.lang.Iterable). The gold "
               "uses none of OptionBuilder's static builder fields.",
}
