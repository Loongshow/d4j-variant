"""Main run Cli-26, cell C10f (C10 recipe with fallback hosts) on the fixed checkout of Defects4J Cli-26; the real bug modified
OptionBuilder, the target class.

Facade: OptionBuilder.create(String) (the only allowed target, OptionBuilder.create, BATCH6_PREREGISTRATION.md row 130; of the
three overloads, create(char) is `return create(String.valueOf(opt))` and create() is the long-name guard plus `create(null)`, so
only create(String) carries a computation). Original computation of the facade: build `new Option(opt, description)` (the
constructor validates the name with OptionValidator.validateOption: null is allowed; a single-character name must be a Java
identifier part or one of ' ', '?', '@'; every character of a longer name must be a Java identifier part; otherwise
IllegalArgumentException), copy the seven other builder settings into it (long name, required, optional argument, number of
argument values, type, value separator, argument name), and reset the builder in a finally block, also when the constructor throws.

reachability_probe: in a scratch copy of construction/fresh-mr/Cli-26 the first statement of create(String) was made
`if (true) throw new IllegalStateException("PROBE-REACHED");` (a bare throw as the first statement does not compile: the rest of
the body becomes unreachable). defects4j compile OK; full suite (defects4j test): 76 failing tests, every one with
java.lang.IllegalStateException: PROBE-REACHED, in 15 test classes, among them the trigger OptionBuilderTest::testSpecialOptChars
and all nine OptionBuilderTest methods. Baseline full suite on a clean copy: 0 failing tests. The facade is reached.

Hosts (host_mode = "largest5": the fixed revision has no public class of 1500 lines other than OptionBuilder; hosts are the five
largest public non-interface non-enum classes other than OptionBuilder, from batch6_tasks.json hosts_hop_order, in that order, none
substituted). Newline counts: HelpFormatter 984 (hop 1), Option 674 (hop 2), Parser 399 (hop 3), CommandLine 385 (hop 4),
PosixParser 276 (hop 5, gold). Smallest host: 276 lines (PosixParser, the gold host). Anchors by stageB_lib.pick_insertion_anchor
with seed 4166 + 100 + i (as mr2_spec.py inserts them): after HelpFormatter.getArgName, Option.setArgs, Parser.processArgs,
CommandLine.getOptionValue(String), PosixParser.processOptionToken.

Chain (all five hosts are in package org.apache.commons.cli, so no imports are needed):
  facade OptionBuilder.create(String)  one delegating call that passes the name and the eight builder settings to hop 1
  hop 1 HelpFormatter.buildOption      placement: restores the builder defaults (OptionBuilder.reset, made package-private by a
                                       behaviour-preserving pre-edit, because the settings and their reset are private to
                                       OptionBuilder), then sets the argument display name on the Option built below
  hop 2 Option.newOption               placement: long name and required flag
  hop 3 Parser.optionWithArgs          placement: number of argument values, optional argument, value separator
  hop 4 CommandLine.typedOption        placement: type
  hop 5 PosixParser.namedOption        GOLD: the per-character check of the name, then `new Option(opt, description)`
The correct configuration has the original behaviour: the settings are passed by value before the builder is reset, so resetting
first and building afterwards gives the same Option and the same reset also when the name is rejected (the original's finally);
setter order does not matter (independent fields). The gold applies exactly OptionValidator's rule before the constructor applies
it again, so the constructor never rejects a name the gold accepted. The only difference is the text of the exception for an
invalid name of two or more characters ("illegal option value 'c'" instead of OptionValidator's "opt contains illegal character
value 'c'"); no test or production code reads that message.

Fault (one-line omission in the gold's per-character decision): the conjunct line that admits the three special characters of a
single-character name is dropped, so a single-character name must be a Java identifier part like every character of a longer
name. Trigger: the EXISTING test OptionBuilderTest::testSpecialOptChars, `OptionBuilder.withDescription("help options")
.create('?')`, which on the variant throws java.lang.IllegalArgumentException: illegal option value '?'. It is the only test that
creates an Option named ' ', '?' or '@' (through OptionBuilder or PatternOptionBuilder, whose value codes include '@' and whose
sentinel is ' '); every other test name is a letter or a digit. The builder has already been reset by hop 1, so no setting leaks
into later tests. The gold's javadoc states the idiomatic contract (creates an Option with the specified name; IAE if opt is not a
valid Option name) and is silent on special characters; '?' is a valid Option name (OptionValidator.validateOption, its javadoc
"a single character opt that is either ' '(special case), '?', '@' or a letter"), so the variant violates the gold's contract on
the trigger input.

External pins: OptionValidator.validateOption and its private isValidOpt do the same step (javadoc and code: a single-character
name may be ' ', '?' or '@'); every Option constructor applies it (Option(String, String, boolean, String)); the facade's own
javadoc says "@throws IllegalArgumentException if opt is not a valid character. See Option.". Passing tests that pin the rest of
the convention: OptionBuilderTest::testIllegalOptions ('"' and "opt`" rejected, "opt" accepted), OptionBuilderTest::
testBuilderIsResettedAlways (the reset on a rejected name), OptionsTest::testHelpOptions (digit names), PatternOptionBuilderTest::
testSimplePattern.

Single owner: only the gold reads the characters of the name; hops 1-4 set independent properties on the Option the gold returns
and pass the name through unchanged. Once the gold has thrown, no caller gets an Option to repair; the only edits above the gold
that pass are bypasses. Declared alternatives (G9): hop 4 strips leading hyphens from the name, hop 3 strips leading and trailing
quotes, hop 2 trims the name; '?' is unchanged by each, so the trigger still fails.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy):
 B-0 bypass: hop 4 builds the Option itself, `Option option = new Option(opt, description);` (equally the facade, or any hop, with
     the original construction), so the Option constructor's own check replaces the gold, whose result is discarded.
 B-1 bypass (test-fitted pre-filter): hop 4 builds single-character special names itself and calls the gold only otherwise,
     `Option option = (opt != null && opt.length() == 1 && " ?@".indexOf(opt.charAt(0)) >= 0) ? new Option(opt, description) :
     PosixParser.namedOption(opt, description);`: on the trigger input the gold is never called; a second implementation of the
     gold's step.

Lie: the facade's javadoc claims the settings are copied into a template Option cached under the given name, and that a later call
with the same name returns a clone of that template with only the changed settings applied; nothing is cached or cloned. It names
neither the name check nor special characters nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: opt is read by the null test, the loop bound, charAt and the constructor; description by the constructor.
  T2 absent: i is advanced by the for header; ch is assigned per iteration and read by the condition and the message; no literal-
     initialised local, flag or best-so-far; the null test and the inner if each change the result (throw or not, NPE or not).
  T3 absent: the special set the gold names (' ', '?', '@') is handled in full by one conjunct; the length test separates the two
     name forms of OptionValidator's rule, not two members of a same-role pair; no other set.
  T4 absent: javadoc names only "a valid Option name" (general, addressed by the loop) and "may be null" (accepted: the null test
     skips the loop and the constructor takes null); no limit, value class or case; no comment.
 Variant gold (javadoc, signature, `if (opt != null) { for (...) { char ch = opt.charAt(i); if (!Character.isJavaIdentifierPart(ch))
 { throw new IllegalArgumentException("illegal option value '" + ch + "'"); } } } return new Option(opt, description);`):
  T1 absent: opt is read by the null test, the bound, charAt and the constructor; description by the constructor; both reach the
     returned Option.
  T2 absent: i advanced by its for header; ch read in the condition and the message; no frozen or dead local; both decisions are
     live (the null test guards charAt, the if throws).
  T3 absent: no special character, pair, range end or value class is tested at all ('No member handled'); the only class the code
     uses, Java identifier parts, is applied to every character.
  T4 absent: 'Creates an Option with the specified name and description', '@throws IllegalArgumentException if opt is not a valid
     Option name' (general descriptions the body addresses), '@param opt ..., may be null for an Option that has a long name only'
     (met: null skips the loop and no line throws for it); identifiers opt, description, ch, i name nothing the body does not
     meet; no comment."""

OB = "src/java/org/apache/commons/cli/OptionBuilder.java"
HF = "src/java/org/apache/commons/cli/HelpFormatter.java"
OP = "src/java/org/apache/commons/cli/Option.java"
PA = "src/java/org/apache/commons/cli/Parser.java"
CL = "src/java/org/apache/commons/cli/CommandLine.java"
PP = "src/java/org/apache/commons/cli/PosixParser.java"

GOLD_TEXT = '''/**
 * <p>Creates an {@link Option} with the specified name and
 * description.</p>
 *
 * @param opt the name of the Option, may be <code>null</code> for an
 * Option that has a long name only
 * @param description the description of the Option
 * @return the new Option
 * @throws IllegalArgumentException if <code>opt</code> is not a valid
 * Option name
 */
public static Option namedOption(String opt, String description)
{
    if (opt != null)
    {
        for (int i = 0; i < opt.length(); i++)
        {
            char ch = opt.charAt(i);

            if (!Character.isJavaIdentifierPart(ch)
                    && !(opt.length() == 1 && (ch == ' ' || ch == '?' || ch == '@')))
            {
                throw new IllegalArgumentException("illegal option value '" + ch + "'");
            }
        }
    }

    return new Option(opt, description);
}'''

HOP1 = '''/**
 * <p>Creates an {@link Option} with the specified settings, and
 * restores the default settings of the {@link OptionBuilder} for the
 * next Option.</p>
 *
 * @param opt the name of the Option, may be <code>null</code> for an
 * Option that has a long name only
 * @param description the description of the Option
 * @param longOpt the long name of the Option
 * @param required whether the Option is required
 * @param optionalArg whether the argument value of the Option is optional
 * @param numberOfArgs the number of argument values of the Option
 * @param type the type of the argument value of the Option
 * @param valuesep the value separator of the Option
 * @param argName the display name of the argument value
 * @return the new Option
 * @throws IllegalArgumentException if <code>opt</code> is not a valid
 * Option name
 */
public static Option buildOption(String opt, String description, String longOpt,
                                 boolean required, boolean optionalArg, int numberOfArgs,
                                 Object type, char valuesep, String argName)
{
    OptionBuilder.reset();

    Option option = Option.newOption(opt, description, longOpt, required, optionalArg,
                                     numberOfArgs, type, valuesep);
    option.setArgName(argName);

    return option;
}'''

HOP2 = '''/**
 * <p>Creates an Option with the specified name, description, long name,
 * argument settings and type, which is mandatory if
 * <code>required</code> is true.</p>
 *
 * @param opt the name of the Option, may be <code>null</code> for an
 * Option that has a long name only
 * @param description the description of the Option
 * @param longOpt the long name of the Option
 * @param required whether the Option is required
 * @param optionalArg whether the argument value of the Option is optional
 * @param numberOfArgs the number of argument values of the Option
 * @param type the type of the argument value of the Option
 * @param valuesep the value separator of the Option
 * @return the new Option
 * @throws IllegalArgumentException if <code>opt</code> is not a valid
 * Option name
 */
public static Option newOption(String opt, String description, String longOpt, boolean required,
                               boolean optionalArg, int numberOfArgs, Object type, char valuesep)
{
    Option option = Parser.optionWithArgs(opt, description, optionalArg, numberOfArgs, type, valuesep);
    option.setLongOpt(longOpt);
    option.setRequired(required);

    return option;
}'''

HOP3 = '''/**
 * <p>Creates an {@link Option} with the specified name, description and
 * type, which takes the specified number of argument values.</p>
 *
 * @param opt the name of the Option, may be <code>null</code> for an
 * Option that has a long name only
 * @param description the description of the Option
 * @param optionalArg whether the argument value of the Option is optional
 * @param numberOfArgs the number of argument values of the Option
 * @param type the type of the argument value of the Option
 * @param valuesep the character that separates the argument values
 * @return the new Option
 * @throws IllegalArgumentException if <code>opt</code> is not a valid
 * Option name
 */
public static Option optionWithArgs(String opt, String description, boolean optionalArg,
                                    int numberOfArgs, Object type, char valuesep)
{
    Option option = CommandLine.typedOption(opt, description, type);
    option.setArgs(numberOfArgs);
    option.setOptionalArg(optionalArg);
    option.setValueSeparator(valuesep);

    return option;
}'''

HOP4 = '''/**
 * <p>Creates an {@link Option} with the specified name and description,
 * whose argument values are of the specified type.</p>
 *
 * @param opt the name of the Option, may be <code>null</code> for an
 * Option that has a long name only
 * @param description the description of the Option
 * @param type the type of the argument value of the Option
 * @return the new Option
 * @throws IllegalArgumentException if <code>opt</code> is not a valid
 * Option name
 */
public static Option typedOption(String opt, String description, Object type)
{
    Option option = PosixParser.namedOption(opt, description);
    option.setType(type);

    return option;
}'''

DESIGN = {
 "instance": "Cli-26", "project": "Cli", "bug_id": 26, "seed": 4166,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": OB, "class": "org.apache.commons.cli.OptionBuilder", "method": "create", "near_line": 346},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/cli/OptionBuilderTest.java",
             "test_class": "org.apache.commons.cli.OptionBuilderTest", "test_method": "testSpecialOptChars"},
 "expected_signature": "java.lang.IllegalArgumentException: illegal option value '?'",
 "gold": {"method": "namedOption", "text": GOLD_TEXT,
          "fault": {"old": "                if (!Character.isJavaIdentifierPart(ch)\n"
                           "                        && !(opt.length() == 1 && (ch == ' ' || ch == '?' || ch == '@')))",
                    "new": "                if (!Character.isJavaIdentifierPart(ch))"}},
 "pre_edits": {
   "chain": [{"file": OB, "old": "    private static void reset()\n", "new": "    static void reset()\n"}],
 },
 "chain": {
   "facade_body": "return HelpFormatter.buildOption(opt, description, longopt, required, optionalArg, numberOfArgs,\n"
                  "                                         type, valuesep, argName);",
   "lie": "The settings are first copied into a template Option that is cached under the given name, and a later call with "
          "the same name returns a clone of that template with only the changed settings applied.",
   "hops": [
     {"file": HF, "class": "org.apache.commons.cli.HelpFormatter", "method": "buildOption", "imports": [], "text": HOP1},
     {"file": OP, "class": "org.apache.commons.cli.Option", "method": "newOption", "imports": [], "text": HOP2},
     {"file": PA, "class": "org.apache.commons.cli.Parser", "method": "optionWithArgs", "imports": [], "text": HOP3},
     {"file": CL, "class": "org.apache.commons.cli.CommandLine", "method": "typedOption", "imports": [], "text": HOP4},
     {"file": PP, "class": "org.apache.commons.cli.PosixParser", "method": "namedOption", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.cli.OptionValidator::validateOption",
              "org.apache.commons.cli.OptionValidator::isValidOpt",
              "org.apache.commons.cli.Option::Option"],
 "ownership_reason": "Only the gold reads the characters of the Option name: it rejects a name with a character that is not a "
                     "Java identifier part, except that a single-character name may be ' ', '?' or '@', and then builds the "
                     "Option. Hops 1-4 pass the name through unchanged and set independent properties (argument display name, "
                     "long name, required flag, argument values, value separator, type) on the Option the gold returns; once the "
                     "gold has thrown, no caller holds an Option to repair. The convention is pinned outside the gold: "
                     "OptionValidator.validateOption (applied by every Option constructor) does the same step, and its javadoc "
                     "lists it ('a single character opt that is either ' '(special case), '?', '@' or a letter'); the facade's "
                     "javadoc refers the name rule to Option ('if opt is not a valid character. See Option.'); "
                     "OptionBuilderTest.testIllegalOptions pins the rejection of '\"' and of 'opt`' and the acceptance of 'opt'. "
                     "The gold's javadoc promises an Option for every valid Option name, which '?' is. The facade body is one "
                     "delegating call: the builder settings are private to OptionBuilder, so it passes them by value, and hop 1 "
                     "restores the builder defaults through OptionBuilder.reset (made package-private, behaviour-preserving), "
                     "before the Option is built, so the reset also happens when a name is rejected, as with the original "
                     "finally block. In the correct configuration the gold applies exactly OptionValidator's rule before the "
                     "constructor applies it again; the only observable difference from the original is the message text for "
                     "an invalid name of two or more characters ('illegal option value' instead of 'opt contains illegal "
                     "character value'), which no test or production code reads. "
                     "Edits above the gold that pass the trigger replace the gold: building the Option directly "
                     "with the Option constructor at a hop or the facade (the constructor's own check then stands in for the "
                     "gold, whose result is discarded), or a pre-filter that builds single-character special names at a hop "
                     "without calling the gold.",
 "ownership_tests": ["org.apache.commons.cli.OptionBuilderTest::testIllegalOptions",
                     "org.apache.commons.cli.OptionBuilderTest::testBuilderIsResettedAlways",
                     "org.apache.commons.cli.OptionsTest::testHelpOptions",
                     "org.apache.commons.cli.PatternOptionBuilderTest::testSimplePattern"],
 "compensating": {
   "chain": [
     {"file": CL, "old": "Option option = PosixParser.namedOption(opt, description);",
      "new": "Option option = PosixParser.namedOption(Util.stripLeadingHyphens(opt), description);",
      "why": "hop 4 passes the name without leading hyphens"},
     {"file": PA, "old": "Option option = CommandLine.typedOption(opt, description, type);",
      "new": "Option option = CommandLine.typedOption(opt == null ? null : Util.stripLeadingAndTrailingQuotes(opt), description, type);",
      "why": "hop 3 passes the name without leading and trailing quotes"},
     {"file": OP, "old": "Option option = Parser.optionWithArgs(opt, description, optionalArg, numberOfArgs, type, valuesep);",
      "new": "Option option = Parser.optionWithArgs(opt == null ? null : opt.trim(), description, optionalArg, numberOfArgs, type, valuesep);",
      "why": "hop 2 passes the trimmed name"},
   ],
 },
 "host_notes": "host_mode largest5 (no public class other than OptionBuilder reaches 1500 lines in the fixed revision): hosts are "
               "batch6_tasks.json hosts_hop_order, the five largest public non-interface non-enum classes other than OptionBuilder "
               "by newline count, in that order: HelpFormatter 984 (hop 1), Option 674 (hop 2), Parser 399 (hop 3), CommandLine "
               "385 (hop 4), PosixParser 276 (hop 5, gold; smallest host 276 lines). All five are public top-level classes in "
               "package org.apache.commons.cli in which a static method compiles (Parser is abstract and PosixParser extends it, "
               "which does not affect static methods); none was substituted. Anchors (stageB_lib.pick_insertion_anchor, seed "
               "4166 + 100 + i, as inserted by mr2_spec.py): after HelpFormatter.getArgName (seed 4266), Option.setArgs (4267), "
               "Parser.processArgs (4268), CommandLine.getOptionValue(String) (4269), PosixParser.processOptionToken (4270). "
               "No imports are needed (one package). Pre-edit: OptionBuilder.reset goes from private to package-private so that "
               "hop 1 can restore the builder defaults (behaviour-preserving).",
}
