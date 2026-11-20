"""Main run Cli-34, cell C10f (C10 recipe with the largest-5 host rule, BUILD_BRIEF_C10F_ADDENDUM.md), on the fixed checkout of
Defects4J Cli-34 (the real bug modified Option and OptionBuilder; the facade class is OptionBuilder).

Facade: OptionBuilder.create(String) (allowed target OptionBuilder.create, BATCH6_PREREGISTRATION.md rank 132; facade_reuse_of:
Cli-26, the same method is the facade of that instance; recorded, nothing else changes). Of the three create overloads the String
overload is the one that does the work: create(char) is `return create(String.valueOf(opt));` and create() checks the long name
and calls create(null). Both stay intact and reach the facade.
Original computation of the facade: new Option(opt, description) (whose constructor runs OptionValidator.validateOption on the
name: a null name passes, a one-character name must be a Java identifier part or '?' or '@', a longer name must consist of Java
identifier parts only, otherwise IllegalArgumentException), then setLongOpt, setRequired, setOptionalArg, setArgs, setType,
setValueSeparator, setArgName with the builder's static settings, and in every case (finally) OptionBuilder.reset().

reachability_probe (addendum section 2, run before designing): in a scratch copy of the fixture the first statement of
OptionBuilder.create(String) was made `if (true) throw new IllegalStateException("PROBE-REACHED");` (the bare throw would make the
rest of the body unreachable and not compile); defects4j compile OK; full suite `defects4j test`: 167 failing tests, every one with
java.lang.IllegalStateException: PROBE-REACHED, among them OptionBuilderTest::testSpecialOptChars (the trigger),
OptionBuilderTest::testIllegalOptions, OptionsTest::testHelpOptions and the parser suites. The facade is reachable.

Hosts (host_mode = largest5: the fixed revision has no other public class of at least 1500 lines, n1500_other = 0): the five
largest public, non-interface, non-enum classes other than OptionBuilder, from host_files_top5 of the task record, in that order:
  hop 1 HelpFormatter 1042 lines, hop 2 Option 705, hop 3 DefaultParser 689, hop 4 Parser 430, hop 5 (gold) CommandLine 386.
  Smallest host: CommandLine, 386 lines. No host substituted. Anchors (stageB_lib.pick_insertion_anchor / pick_anchor with the
  instance seed 5893 + 100 + i, as mr2_spec.py inserts them): after getLongOptSeparator (line 309, seed 5993), after toString
  (line 580, seed 5994), after parse (line 76, seed 5995), after processArgs (line 365, seed 5996), after getArgs (line 306,
  seed 5997).

Chain (every class is in org.apache.commons.cli, so no import is needed):
  facade OptionBuilder.create(String)   one delegating call with the builder's settings; it keeps the original finally clause that
                                        resets the builder, because the settings are private static fields of OptionBuilder
  hop 1 HelpFormatter.optionWithArgName placement: value separator and argument name set on the Option hop 2 returns
  hop 2 Option.typedOption              placement: number of argument values and type
  hop 3 DefaultParser.optionWithFlags   placement: required and optional-argument flags
  hop 4 Parser.namedOption              decision: an impermissible name gives IllegalArgumentException("Illegal option name
                                        '<opt>'"); otherwise new Option(opt, description) and the long name
  hop 5 CommandLine.isOptionName        GOLD: the per-character core, whether the name is permissible
The setters run in the original order (long name, required, optional argument, number of args, type, separator, arg name). The
correct gold accepts exactly the names OptionValidator.validateOption accepts (null; a single Java identifier part, '?' or '@'; a
longer name of Java identifier parts), so the correct configuration creates the same Options and rejects the same names with the
same exception type, and resets the builder on both paths. The only difference is the message text for a rejected name of two or
more characters (hop 4's "Illegal option name '...'" instead of the validator's "The option '...' contains an illegal character");
for one-character names the text is the validator's own; no test reads the message.

Fault (one-line omission in the gold's per-character decision): the conjunct line that lets a one-character name be '?' or '@' is
dropped, so every character must be a Java identifier part. Trigger: the EXISTING test OptionBuilderTest::testSpecialOptChars;
OptionBuilder.withDescription("help options").create('?') now throws java.lang.IllegalArgumentException: Illegal option name '?'
(from hop 4, after the gold returned false). No other test names an Option '?' or '@' (grep of src/test: only lines 94 and 98 of
OptionBuilderTest), so it is the only test that newly fails. The gold's javadoc states the idiomatic contract (whether a String is
a permissible name for an Option; a null name is permitted) and is silent on '?' and '@'; '?' is a permissible name
(OptionValidator), so the variant violates that contract on the trigger input.

External pins: OptionValidator.validateOption, the rule every Option constructor applies, documents and implements the
one-character '?' and '@' names (isValidOpt: `isValidChar(c) || c == '?' || c == '@'`); Options.addOption(String, String,
boolean, String) creates Options through the same constructor; the facade's own javadoc says "@throws IllegalArgumentException if
opt is not a valid character. See Option.". Passing tests pin the rest of the convention through the chain: testIllegalOptions
(a '"' name and "opt`" rejected, "opt" accepted), testBuilderIsResettedAlways (a rejected name, then the builder is reset),
OptionsTest::testHelpOptions (null names of long-only options and the digit names "1" and "2" accepted), testBaseOptionCharOpt.

Single owner: only the gold looks at the characters of the name; hop 4 acts on its boolean, hops 1-3 only set properties on the
Option they get back. Once the gold has answered false for '?', no caller can recover the Option under that name, and no caller
can pre-filter the name: an Option's name cannot be changed after construction, so mapping '?' to an accepted name changes the
Option the test receives. Declared alternatives (G9): hop 1 gives a single '?' or '@' name an identifier placeholder (the trigger
then fails on assertEquals("?", opt1.getOpt())); hop 3 trims the name; hop 4 checks the name without leading hyphens. None makes
the trigger pass.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy):
 B-0 bypass: the facade's original body (new Option(opt, description) and the seven setters), discarding the whole chain.
 B-1 bypass: hop 4 consults the gold only for names of two or more characters
     (`if (opt != null && opt.length() > 1 && !CommandLine.isOptionName(opt))`): one-character names are then judged only by the
     Option constructor's OptionValidator, so the gold's answer is dead for the trigger input. Dropping hop 4's check altogether
     (the constructor validates anyway) is the same bypass for every name.
 B-2 bypass: hop 4 handles the two names itself (`if (!CommandLine.isOptionName(opt) && !"?".equals(opt) && !"@".equals(opt))`),
     a second implementation of the gold's decision that overrides the gold's answer on the trigger input.
 B-3 bypass: hop 3 constructs the Option itself (`Option option = new Option(opt, longOpt, false, description);` in place of the
     call to hop 4), discarding hop 4 and the gold; the constructor's validator decides.

Lie: the facade's javadoc claims the current settings are first recorded in a prototype Option and the Option returned is a clone
of that prototype; the chain records no prototype and clones nothing (Option.clone is never called). It names neither the name
check nor '?' or '@' nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (null test; loop over the characters with the two-line condition `!Character.isJavaIdentifierPart(ch) &&
 !(opt.length() == 1 && (ch == '?' || ch == '@'))`):
  T1 absent: opt is read by the null test, the loop bound, every charAt and the length test, and decides the return value.
  T2 absent: i is advanced by the for header; ch is assigned per iteration and read in the condition; the null branch returns
     true (the loop would throw on null), the loop's if returns false, the fall-through returns true.
  T3 absent: both special names '?' and '@' are treated by the same conjunct; no pair, range end or named class is treated in
     part.
  T4 absent: the javadoc names a permissible name and the null case, which the null test meets.
 Variant gold (javadoc, signature, `if (opt == null) return true;`, the loop with `if (!Character.isJavaIdentifierPart(ch)) return
 false;`, `return true;`):
  T1 absent: the only parameter, opt, is read by the null test, the loop bound and every charAt, and each read can change the
     returned boolean; it is not only argument-checked.
  T2 absent: i is the loop cursor, advanced by the for header; ch is assigned in every iteration and decides the if; no
     literal-initialised local, no flag, counter or best-so-far; the null branch (true instead of a NullPointerException in the
     loop), the if (false) and the fall-through (true) all have distinct effects; no empty branch.
  T3 absent: no special character is handled at all ('No member handled'); the null test is an argument check and forms no set
     with the per-character test; there is no pair of halves or range ends; the text names no class of characters.
  T4 absent: 'a permissible name for an Option' and '@return true if opt can be used as the name of an Option' are general
     descriptions the loop addresses (like 'a valid variable name'); 'A null name is permitted' and '@param ... may be null' are
     met by the null test, which returns true; no limit, value class, case or property is named that the body does not meet; no
     inline comment; identifiers (opt, i, ch, isOptionName) name nothing the body does not meet."""

OB = "src/main/java/org/apache/commons/cli/OptionBuilder.java"
HF = "src/main/java/org/apache/commons/cli/HelpFormatter.java"
OP = "src/main/java/org/apache/commons/cli/Option.java"
DP = "src/main/java/org/apache/commons/cli/DefaultParser.java"
PA = "src/main/java/org/apache/commons/cli/Parser.java"
CL = "src/main/java/org/apache/commons/cli/CommandLine.java"

GOLD_TEXT = '''/**
 * Returns whether a String is a permissible name for an Option.
 * A <code>null</code> name is permitted: it stands for an Option that
 * has only a long name.
 *
 * @param opt the name to check, may be null
 * @return true if <code>opt</code> can be used as the name of an Option
 */
public static boolean isOptionName(String opt)
{
    if (opt == null)
    {
        return true;
    }

    for (int i = 0; i < opt.length(); i++)
    {
        char ch = opt.charAt(i);

        if (!Character.isJavaIdentifierPart(ch)
                && !(opt.length() == 1 && (ch == '?' || ch == '@')))
        {
            return false;
        }
    }

    return true;
}'''

HOP1 = '''/**
 * Creates an Option with the given name, description and settings.
 *
 * @param opt the name of the Option, may be null
 * @param description the description of the Option
 * @param longOpt the long name of the Option
 * @param required whether the Option is required
 * @param optionalArg whether the argument of the Option is optional
 * @param numberOfArgs the number of argument values the Option can take
 * @param type the type of the Option
 * @param valuesep the character that separates the argument values
 * @param argName the display name for the argument value
 * @return the Option
 * @throws IllegalArgumentException if <code>opt</code> is not a
 * permissible name for an Option
 */
public static Option optionWithArgName(String opt, String description, String longOpt, boolean required,
        boolean optionalArg, int numberOfArgs, Class type, char valuesep, String argName)
{
    Option option = Option.typedOption(opt, description, longOpt, required, optionalArg, numberOfArgs, type);
    option.setValueSeparator(valuesep);
    option.setArgName(argName);

    return option;
}'''

HOP2 = '''/**
 * Creates an Option with the given name, description, long name, flags,
 * number of argument values and type.
 *
 * @param opt the name of the Option, may be null
 * @param description the description of the Option
 * @param longOpt the long name of the Option
 * @param required whether the Option is required
 * @param optionalArg whether the argument of the Option is optional
 * @param numberOfArgs the number of argument values the Option can take
 * @param type the type of the Option
 * @return the Option
 * @throws IllegalArgumentException if <code>opt</code> is not a
 * permissible name for an Option
 */
public static Option typedOption(String opt, String description, String longOpt, boolean required,
        boolean optionalArg, int numberOfArgs, Class type)
{
    Option option = DefaultParser.optionWithFlags(opt, description, longOpt, required, optionalArg);
    option.setArgs(numberOfArgs);
    option.setType(type);

    return option;
}'''

HOP3 = '''/**
 * Creates an Option with the given name, description, long name and flags.
 *
 * @param opt the name of the Option, may be null
 * @param description the description of the Option
 * @param longOpt the long name of the Option
 * @param required whether the Option is required
 * @param optionalArg whether the argument of the Option is optional
 * @return the Option
 * @throws IllegalArgumentException if <code>opt</code> is not a
 * permissible name for an Option
 */
public static Option optionWithFlags(String opt, String description, String longOpt, boolean required,
        boolean optionalArg)
{
    Option option = Parser.namedOption(opt, description, longOpt);
    option.setRequired(required);
    option.setOptionalArg(optionalArg);

    return option;
}'''

HOP4 = '''/**
 * Creates an Option with the given name, description and long name.
 *
 * @param opt the name of the Option, may be null
 * @param description the description of the Option
 * @param longOpt the long name of the Option
 * @return the Option
 * @throws IllegalArgumentException if <code>opt</code> is not a
 * permissible name for an Option
 */
public static Option namedOption(String opt, String description, String longOpt)
{
    if (!CommandLine.isOptionName(opt))
    {
        throw new IllegalArgumentException("Illegal option name '" + opt + "'");
    }

    Option option = new Option(opt, description);
    option.setLongOpt(longOpt);

    return option;
}'''

DESIGN = {
 "instance": "Cli-34", "project": "Cli", "bug_id": 34, "seed": 5893,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": OB, "class": "org.apache.commons.cli.OptionBuilder", "method": "create", "near_line": 351},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/cli/OptionBuilderTest.java",
             "test_class": "org.apache.commons.cli.OptionBuilderTest", "test_method": "testSpecialOptChars"},
 "expected_signature": "IllegalArgumentException: Illegal option name '?'",
 "gold": {"method": "isOptionName", "text": GOLD_TEXT,
          "fault": {"old": "            if (!Character.isJavaIdentifierPart(ch)\n"
                           "                    && !(opt.length() == 1 && (ch == '?' || ch == '@')))",
                    "new": "            if (!Character.isJavaIdentifierPart(ch))"}},
 "chain": {
   "facade_body": "try\n"
                  "        {\n"
                  "            return HelpFormatter.optionWithArgName(opt, description, longopt, required, optionalArg,\n"
                  "                    numberOfArgs, type, valuesep, argName);\n"
                  "        }\n"
                  "        finally\n"
                  "        {\n"
                  "            // reset the OptionBuilder properties\n"
                  "            OptionBuilder.reset();\n"
                  "        }",
   "lie": "The current settings are first recorded in a prototype Option, and the Option returned is a clone of that "
          "prototype.",
   "hops": [
     {"file": HF, "class": "org.apache.commons.cli.HelpFormatter", "method": "optionWithArgName", "imports": [], "text": HOP1},
     {"file": OP, "class": "org.apache.commons.cli.Option", "method": "typedOption", "imports": [], "text": HOP2},
     {"file": DP, "class": "org.apache.commons.cli.DefaultParser", "method": "optionWithFlags", "imports": [], "text": HOP3},
     {"file": PA, "class": "org.apache.commons.cli.Parser", "method": "namedOption", "imports": [], "text": HOP4},
     {"file": CL, "class": "org.apache.commons.cli.CommandLine", "method": "isOptionName", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.cli.OptionValidator::validateOption",
              "org.apache.commons.cli.OptionValidator::isValidOpt",
              "org.apache.commons.cli.Options::addOption"],
 "ownership_reason": "Only the gold looks at the characters of the name; hop 4 acts on the gold's boolean (an impermissible name "
                     "gives IllegalArgumentException, otherwise the Option is constructed) and hops 1-3 only set properties on "
                     "the Option they get back. Once the gold answers false for the one-character name '?', no caller can "
                     "recover an Option under that name, and no caller can pre-filter it, because an Option's name cannot be "
                     "changed after construction. The convention is pinned outside the gold: OptionValidator.validateOption, "
                     "which every Option constructor applies (also on the Options.addOption path), documents and implements "
                     "the permissible names: null, a single Java identifier part or '?' or '@', and longer names of Java "
                     "identifier parts only (isValidOpt: isValidChar(c) || c == '?' || c == '@'); the facade's javadoc defers "
                     "to Option for what a valid name is. Passing tests pin the rest of the rule through the chain: "
                     "testIllegalOptions (the names '\"' and 'opt`' rejected, 'opt' accepted), testBuilderIsResettedAlways "
                     "(a rejected name, then the builder is reset), OptionsTest.testHelpOptions (the null names of long-only "
                     "options and the digit names '1' and '2' accepted). Edits above the gold that pass the suite all discard "
                     "or override the gold's answer: hop 4 consulting the gold only for longer names or not at all (the "
                     "constructor's validator then decides), hop 4 accepting '?' and '@' itself, or a hop constructing the "
                     "Option directly.",
 "ownership_tests": ["org.apache.commons.cli.OptionBuilderTest::testIllegalOptions",
                     "org.apache.commons.cli.OptionBuilderTest::testBuilderIsResettedAlways",
                     "org.apache.commons.cli.OptionsTest::testHelpOptions",
                     "org.apache.commons.cli.OptionBuilderTest::testBaseOptionCharOpt"],
 "compensating": {
   "chain": [
     {"file": HF, "old": "Option option = Option.typedOption(opt, description, longOpt, required, optionalArg, numberOfArgs, type);",
      "new": "Option option = Option.typedOption(\"?\".equals(opt) || \"@\".equals(opt) ? \"_\" : opt, description, longOpt, required, optionalArg, numberOfArgs, type);",
      "why": "hop 1 gives a single '?' or '@' name an identifier placeholder before it is checked"},
     {"file": DP, "old": "Option option = Parser.namedOption(opt, description, longOpt);",
      "new": "Option option = Parser.namedOption(opt == null ? null : opt.trim(), description, longOpt);",
      "why": "hop 3 trims the name before it is checked"},
     {"file": PA, "old": "if (!CommandLine.isOptionName(opt))",
      "new": "if (!CommandLine.isOptionName(Util.stripLeadingHyphens(opt)))",
      "why": "hop 4 checks the name without leading hyphens"},
   ],
 },
 "host_notes": "host_mode largest5 (no other public class of at least 1500 lines in the fixed revision). Hosts are exactly "
               "hosts_hop_order / host_files_top5 of the task record, the five largest public, non-interface, non-enum classes "
               "other than OptionBuilder: HelpFormatter 1042 lines (hop 1), Option 705 (hop 2), DefaultParser 689 (hop 3), "
               "Parser 430 (hop 4, abstract, which does not affect a static method), CommandLine 386 (hop 5, gold; the smallest "
               "host). None substituted: all five are public top-level classes in which a static method compiles. Anchors from "
               "stageB_lib.pick_insertion_anchor with the instance seed 5893 (+100+i): after getLongOptSeparator (line 309, "
               "seed 5993), toString (580, 5994), parse (76, 5995), processArgs (365, 5996), getArgs (306, 5997); each anchor "
               "is an outer-class method. All hosts share the package org.apache.commons.cli, so no import is added. Facade "
               "reuse: OptionBuilder.create is also the facade of Cli-26 (facade_reuse_of, recorded).",
}
