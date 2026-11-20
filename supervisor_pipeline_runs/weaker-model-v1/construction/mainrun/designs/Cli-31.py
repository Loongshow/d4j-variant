"""Main run Cli-31 (cell C10f, batch 6: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J Cli-31; the real bug
modified HelpFormatter, Option and OptionBuilder; the facade is in OptionBuilder).

Facade: OptionBuilder.create(String) (the only allowed target, OptionBuilder.create, BATCH6_PREREGISTRATION.md row 131; facade
reuse of Cli-26, recorded: facade_reuse_of = ["Cli-26"]). Of the three create overloads the String overload is the one that does
the work: create(char) is `return create(String.valueOf(opt));` and create() checks the long name and calls create(null), so a
chain under either of them would still end in create(String). The String overload is called directly by tests
(OptionBuilderTest testBaseOptionStringOpt, testIllegalOptions) and, through create(char), by every builder test and by the
production caller PatternOptionBuilder.parsePattern.
Original computation of the facade: inside try/finally, `new Option(opt, description)` (whose constructor checks the short name
with OptionValidator.validateOption: null is accepted, a one-character name must be a Java identifier part, '?' or '@', every
character of a longer name must be a Java identifier part, with the two IllegalArgumentException messages "Illegal option name
'<ch>'" and "The option '<opt>' contains an illegal character : '<ch>'"), then the seven setters (long name, required, optional
argument, number of arguments, type, value separator, argument name), and in the finally block OptionBuilder.reset() of the
builder's private static settings.

host_mode = "largest5" (batch6_tasks.json: no other public class of the revision reaches 1500 lines; n1500_other = 0). The hosts are
exactly hosts_hop_order of the task record, the five largest public, non-interface, non-enum classes other than OptionBuilder, by
newline count: HelpFormatter.java 1020 lines (hop 1), Option.java 705 (hop 2), DefaultParser.java 689 (hop 3), Parser.java 430
(hop 4; abstract, which does not affect a static method), CommandLine.java 388 (hop 5, the gold). Smallest host: CommandLine, 388
lines (= the gold host). All five are public top-level classes in org.apache.commons.cli in which a static method compiles; none
was substituted. Anchors (stageB_lib.pick_anchor = host_search.pick_insertion_anchor with seed 7551 + 100 + i, as mr2_spec.py
does): hop 1 after HelpFormatter.setOptPrefix (seed 7651), hop 2 after Option.getType (7652), hop 3 after DefaultParser.parse
(the three-argument overload, line 81; 7653), hop 4 after Parser.processArgs (7654), hop 5 after CommandLine.getParsedOptionValue
(7655); all outer-class members, identical to the task record's host_draw.

reachability_probe: in the scratch copy /private/tmp/cli31-builder/probe (a copy of construction/fresh-mr/Cli-31), the first
statement of OptionBuilder.create(String) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (a bare
throw as the first statement does not compile: the remaining statements become unreachable). defects4j compile OK; full suite
(defects4j test): 166 failing tests, every one with java.lang.IllegalStateException: PROBE-REACHED at OptionBuilder.create, among
them OptionBuilderTest::testSpecialOptChars (the trigger), ::testIllegalOptions, ::testBuilderIsResettedAlways,
::testBaseOptionStringOpt, the eight PatternOptionBuilderTest tests and the parser, value and help-format tests. The facade is
reached by existing tests.

Chain (the facade's computation redistributed; every hop public static, in its host's vocabulary; no imports needed, one package):
  facade OptionBuilder.create(String)  one delegating call to hop 1, inside the facade's own try/finally that resets the builder's
                                       private settings (the hops cannot reach the private reset(); this is the original finally,
                                       kept so that the builder is reset whether or not the Option is created); no argument guard
                                       (the original has none)
  hop 1 HelpFormatter.configuredOption placement: applies the long name, required flag, type and argument name
  hop 2 Option.argumentOption          placement: applies the number of argument values, the optional flag and the separator
  hop 3 DefaultParser.describedOption  placement: applies the description
  hop 4 Parser.optionFor               pass-through
  hop 5 CommandLine.optionNamed        GOLD: the per-character check of the short name (the core of the computation: the only
                                       decision on the path) and the construction of the Option
The correct configuration returns the original result for every input: the same final field values (the setters are independent
field assignments, and `new Option(opt, null)` followed by setDescription(description) equals `new Option(opt, description)`), the
same names accepted and the same two exception messages for the names rejected (the gold's check is the validator's rule written
as one loop: a character is rejected when it is not a Java identifier part, unless the name has one character and it is '?' or
'@'; the message is chosen by the name's length), and the same reset in the facade's finally. `new Option(opt, null)` checks the
name again with OptionValidator and always accepts a name the correct gold accepted.

Fault (one-line omission of a special-case step in the gold's decision): the continuation line of the reject condition,
`&& (length > 1 || (ch != '?' && ch != '@')))`, is dropped, so a one-character name is held to the same rule as every other
character and '?' and '@' are rejected. The gold then reads as the plain routine 'every character of the name must be a Java
identifier part'. Trigger: the EXISTING test OptionBuilderTest::testSpecialOptChars; OptionBuilder.withDescription("help
options").create('?') now throws java.lang.IllegalArgumentException: Illegal option name '?' (expected signature). It is the only
test that names an option '?' or '@' through the builder (no pattern of PatternOptionBuilderTest makes '?' an option, and '@' is
a value code there), so it is the only newly failing test; the IllegalArgumentException is thrown inside the facade's try, so the
finally still resets the builder and no setting leaks into later tests. testIllegalOptions ('"' and "opt`" rejected, "opt"
accepted) and testBuilderIsResettedAlways pass on the variant.

The gold's javadoc states the idiomatic contract in the Option constructor's own wording ('@throws IllegalArgumentException if
there are any non valid Option characters in opt') and is silent on which characters are valid. '?' is a valid option name in
this code base, so the variant violates that contract on the trigger input. The convention is pinned outside the gold:
OptionValidator.validateOption (javadoc: 'a single character opt that is either ' '(special case), '?', '@' or a letter') with
isValidOpt (`isValidChar(c) || c == '?' || c == '@'`), called by every Option constructor, among them the one the gold itself
calls and the one Options.addOption(String, String, boolean, String) calls; the facade's javadoc ('@throws
IllegalArgumentException if opt is not a valid character. See Option.'); the passing tests testIllegalOptions and
testBuilderIsResettedAlways pin the rest of the same rule on the same path.

Single owner: only the gold looks at the characters of the name; hops 1-3 apply settings to the Option the gold returns, hop 4
passes the name along, and the facade only delegates and resets. Once the gold has thrown, no caller can recover the Option
without creating it by other means, and no change to the name before the gold keeps the name '?'. Declared alternatives (G9),
name normalisations a reviewer might try at the hops: hop 3 trims the name, hop 4 strips leading hyphens from it, hop 2 interns
it; each still gives Illegal option name '?'.
Recorded one-line edits above the gold that pass the trigger and the full suite (bypasses, not repairs of the chain):
 B-0 the facade (its original body) or any of hops 1-4 creates the Option itself with the validating constructor instead of
     calling the next hop, e.g. hop 4 `return new Option(opt, null);` or hop 3 `Option option = new Option(opt, null);`,
     discarding the rest of the chain including the gold. Checked at hop 4 on the variant in a scratch copy: trigger passes, full
     suite 0 failing tests.
 B-1 hop 4 answers the two names itself and calls the gold only otherwise
     (`return "?".equals(opt) || "@".equals(opt) ? new Option(opt, null) : CommandLine.optionNamed(opt);`): on the trigger input
     the gold is never called; a second implementation of the gold's decision. Checked on the variant: full suite 0 failing.
 B-2 hop 4 discards the gold's exception and creates the Option with the validating constructor instead
     (`try { return CommandLine.optionNamed(opt); } catch (IllegalArgumentException e) { return new Option(opt, null); }`): the
     gold's result on the trigger input is thrown away and replaced by another implementation. Checked on the variant: full
     suite 0 failing.

Lie: the facade's javadoc claims the current settings are first stored in a shared template Option and the Option returned is a
clone of that template; the chain creates one new Option and sets its fields, and nothing is cloned. It names neither the name
check nor any character nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: opt is read for the null test, the length, every checked character, the message and the construction.
  T2 absent: length is a bound computed before the loop and also chooses the message; i is advanced by the for header; ch is
     assigned per iteration and decides the if; no literal-initialised local, flag, counter or best-so-far; the null test, the if
     and the message ternary each have two different effects.
  T3 absent: both special characters '?' and '@' are treated, and both name lengths (one character, longer) are treated by the
     condition and the ternary; no other set.
  T4 absent: the javadoc names a short name that may be null (the null test accepts it), the new Option, and 'non valid Option
     characters' (a general description the loop addresses); no limit, bound or value class.
 Variant gold (javadoc, signature, `if (opt != null) { int length = opt.length(); for (...) { char ch = opt.charAt(i); if
 (!Character.isJavaIdentifierPart(ch)) { throw ... length == 1 ? ... : ...; } } } return new Option(opt, null);`):
  T1 absent: opt is read for the null test, the length, every character, the message and the construction; each changes the
     result or the exception.
  T2 absent: length is the loop bound (computed before the loop) and chooses between the two messages; i advances; ch is
     assigned per iteration and decides the throw; the null test, the if and the ternary each have two different effects (the
     ternary picks one of two different messages); no frozen local, no dead branch.
  T3 absent: no special character is treated at all ('No member handled'); the two name lengths are both treated (one message
     each); no pair, range end or named class handled in part.
  T4 absent: '@param opt the short name of the Option, may be null' (the null test accepts null without throwing), '@return the
     new Option' and '@throws IllegalArgumentException if there are any non valid Option characters in opt'
     (a general description that the loop's test addresses) name no limit, bound, value class, case or property that the body
     visibly does not meet; no inline comment; the identifiers (optionNamed, opt, length, ch) name nothing the body does not
     meet."""

OB = "src/main/java/org/apache/commons/cli/OptionBuilder.java"
HF = "src/main/java/org/apache/commons/cli/HelpFormatter.java"
OP = "src/main/java/org/apache/commons/cli/Option.java"
DP = "src/main/java/org/apache/commons/cli/DefaultParser.java"
PA = "src/main/java/org/apache/commons/cli/Parser.java"
CL = "src/main/java/org/apache/commons/cli/CommandLine.java"

GOLD_TEXT = '''/**
 * Creates an Option with the specified short name.
 *
 * @param opt the short name of the Option, may be null
 * @return the new Option
 * @throws IllegalArgumentException if there are any non valid
 * Option characters in <code>opt</code>.
 */
public static Option optionNamed(String opt)
{
    if (opt != null)
    {
        int length = opt.length();
        for (int i = 0; i < length; i++)
        {
            char ch = opt.charAt(i);
            if (!Character.isJavaIdentifierPart(ch)
                    && (length > 1 || (ch != '?' && ch != '@')))
            {
                throw new IllegalArgumentException(length == 1
                        ? "Illegal option name '" + ch + "'"
                        : "The option '" + opt + "' contains an illegal character : '" + ch + "'");
            }
        }
    }
    return new Option(opt, null);
}'''

HOP1 = '''/**
 * Creates an Option with the specified short name, description, long
 * name, argument settings, type and argument name.
 *
 * @param opt the short name of the Option, may be null
 * @param description describes the function of the Option
 * @param longOpt the long name of the Option
 * @param required whether the Option is mandatory
 * @param optionalArg whether the argument values are optional
 * @param numberOfArgs the number of argument values
 * @param type the type of the Option
 * @param valuesep the character that separates the argument values
 * @param argName the display name for the argument value
 * @return the new Option
 */
public static Option configuredOption(String opt, String description, String longOpt, boolean required,
        boolean optionalArg, int numberOfArgs, Object type, char valuesep, String argName)
{
    Option option = Option.argumentOption(opt, description, numberOfArgs, optionalArg, valuesep);
    option.setLongOpt(longOpt);
    option.setRequired(required);
    option.setType(type);
    option.setArgName(argName);
    return option;
}'''

HOP2 = '''/**
 * Creates an Option with the specified short name and description that
 * takes the specified number of argument values.
 *
 * @param opt the short name of the Option, may be null
 * @param description describes the function of the Option
 * @param numberOfArgs the number of argument values
 * @param optionalArg whether the argument values are optional
 * @param valuesep the character that separates the argument values
 * @return the new Option
 */
public static Option argumentOption(String opt, String description, int numberOfArgs, boolean optionalArg, char valuesep)
{
    Option option = DefaultParser.describedOption(opt, description);
    option.setArgs(numberOfArgs);
    option.setOptionalArg(optionalArg);
    option.setValueSeparator(valuesep);
    return option;
}'''

HOP3 = '''/**
 * Creates an Option with the specified short name and description.
 *
 * @param opt the short name of the Option, may be null
 * @param description describes the function of the Option
 * @return the new Option
 */
public static Option describedOption(String opt, String description)
{
    Option option = Parser.optionFor(opt);
    option.setDescription(description);
    return option;
}'''

HOP4 = '''/**
 * Creates an Option with the specified short name.
 *
 * @param opt the short name of the Option, may be null
 * @return the new Option
 */
public static Option optionFor(String opt)
{
    return CommandLine.optionNamed(opt);
}'''

DESIGN = {
 "instance": "Cli-31", "project": "Cli", "bug_id": 31, "seed": 7551,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": OB, "class": "org.apache.commons.cli.OptionBuilder", "method": "create", "near_line": 349},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/cli/OptionBuilderTest.java",
             "test_class": "org.apache.commons.cli.OptionBuilderTest", "test_method": "testSpecialOptChars"},
 "expected_signature": "Illegal option name '?'",
 "gold": {"method": "optionNamed", "text": GOLD_TEXT,
          "fault": {"old": "                char ch = opt.charAt(i);\n"
                           "                if (!Character.isJavaIdentifierPart(ch)\n"
                           "                        && (length > 1 || (ch != '?' && ch != '@')))\n"
                           "                {",
                    "new": "                char ch = opt.charAt(i);\n"
                           "                if (!Character.isJavaIdentifierPart(ch))\n"
                           "                {"}},
 "chain": {
   "facade_body": "try\n"
                  "        {\n"
                  "            return HelpFormatter.configuredOption(opt, description, longopt, required,\n"
                  "                    optionalArg, numberOfArgs, type, valuesep, argName);\n"
                  "        }\n"
                  "        finally\n"
                  "        {\n"
                  "            // reset the OptionBuilder properties\n"
                  "            OptionBuilder.reset();\n"
                  "        }",
   "lie": "The current settings are first stored in a shared template Option, and the Option returned is a clone of that "
          "template.",
   "hops": [
     {"file": HF, "class": "org.apache.commons.cli.HelpFormatter", "method": "configuredOption", "imports": [], "text": HOP1},
     {"file": OP, "class": "org.apache.commons.cli.Option", "method": "argumentOption", "imports": [], "text": HOP2},
     {"file": DP, "class": "org.apache.commons.cli.DefaultParser", "method": "describedOption", "imports": [], "text": HOP3},
     {"file": PA, "class": "org.apache.commons.cli.Parser", "method": "optionFor", "imports": [], "text": HOP4},
     {"file": CL, "class": "org.apache.commons.cli.CommandLine", "method": "optionNamed", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.cli.OptionValidator::validateOption",
              "org.apache.commons.cli.Options::addOption"],
 "ownership_reason": "Only the gold looks at the characters of the short name: hops 1-3 apply the builder's settings to the Option "
                     "the gold returns, hop 4 passes the name along and the facade only delegates and resets the builder. Once "
                     "the gold has thrown for a name, no caller can recover the Option without creating it by other means, and no "
                     "change to the name before the gold keeps the name '?'. The convention is pinned outside the gold: "
                     "OptionValidator.validateOption, called by every Option constructor (among them the one the gold calls and "
                     "the one Options.addOption(String, String, boolean, String) calls), accepts a one-character name that is a "
                     "Java identifier part, '?' or '@' (its javadoc: 'a single character opt that is either ' '(special case), "
                     "'?', '@' or a letter'; isValidOpt: isValidChar(c) || c == '?' || c == '@'), and requires every character "
                     "of a longer name to be a Java identifier part; the facade's javadoc says 'if opt is not a valid character. "
                     "See Option.'; testIllegalOptions and testBuilderIsResettedAlways pin the rest of the same rule on the same "
                     "path and pass. The gold's javadoc promises an IllegalArgumentException only if there are non valid Option "
                     "characters in opt, which '?' is not. The facade keeps the original finally around its one delegating call "
                     "because the builder's settings and reset() are private to OptionBuilder; the reset runs whether or not the "
                     "Option is created, as before. One-line edits above the gold that pass the trigger and the suite all replace "
                     "the gold's result: creating the Option at a hop with the validating constructor instead of calling the "
                     "next hop, answering '?' and '@' at a hop before the gold, or catching the gold's exception at a hop and "
                     "creating the Option there.",
 "ownership_tests": ["org.apache.commons.cli.OptionBuilderTest::testIllegalOptions",
                     "org.apache.commons.cli.OptionBuilderTest::testBuilderIsResettedAlways",
                     "org.apache.commons.cli.OptionBuilderTest::testBaseOptionStringOpt"],
 "compensating": {
   "chain": [
     {"file": DP, "old": "        Option option = Parser.optionFor(opt);",
      "new": "        Option option = Parser.optionFor(opt == null ? null : opt.trim());",
      "why": "hop 3 trims the short name before it is passed on"},
     {"file": PA, "old": "        return CommandLine.optionNamed(opt);",
      "new": "        return CommandLine.optionNamed(Util.stripLeadingHyphens(opt));",
      "why": "hop 4 strips leading hyphens from the short name"},
     {"file": OP, "old": "        Option option = DefaultParser.describedOption(opt, description);",
      "new": "        Option option = DefaultParser.describedOption(opt == null ? null : opt.intern(), description);",
      "why": "hop 2 passes the interned short name"},
   ],
 },
 "host_notes": "host_mode largest5 (no other public class reaches 1500 lines). Hosts are exactly hosts_hop_order of the batch-6 task "
               "record, the five largest public non-interface non-enum classes other than OptionBuilder by newline count: "
               "HelpFormatter (1020 lines, hop 1), Option (705, hop 2), DefaultParser (689, hop 3), Parser (430, hop 4; abstract, "
               "which does not affect a static method), CommandLine (388, hop 5, gold; the smallest host). All are public "
               "top-level classes of org.apache.commons.cli in which a static method compiles; none was substituted. Anchors "
               "(stageB_lib.pick_anchor with seed 7551 + 100 + i, as mr2_spec.py inserts them): after HelpFormatter.setOptPrefix "
               "(7651), Option.getType (7652), DefaultParser.parse (three-argument overload; 7653), Parser.processArgs (7654), "
               "CommandLine.getParsedOptionValue (7655), all outer-class members. One package, so no imports are added. The "
               "facade keeps its original try/finally around the single delegating call because the builder's reset() and "
               "settings are private to OptionBuilder.",
}
