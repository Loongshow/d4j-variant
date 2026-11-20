"""Main run Cli-40 (C10f recipe, batch 6, on the fixed checkout of Defects4J Cli-40; the real bug modified TypeHandler, the target
class, and the real fix is exactly the step this design omits: for a class that is none of the value types, the buggy createValue
answered null where the fixed one throws ParseException("Unable to handle the class: ...")).

Cell and hosts: C10f, host_mode = largest5 (no other public class of the fixed revision reaches 1500 lines: n1500_other = 0, 18
other public classes). The hosts are the five largest public, non-interface, non-enum classes other than TypeHandler, in the task
record's order, hop i in the i-th largest:
  hop 1 HelpFormatter  1092 lines   anchor after getLongOptPrefix      (pick_insertion_anchor, seed 7398 + 100 = 7498)
  hop 2 Option         1012 lines   anchor after getValue              (seed 7499)
  hop 3 DefaultParser   781 lines   anchor after parse                 (seed 7500)
  hop 4 CommandLine     546 lines   anchor after getParsedOptionValue  (seed 7501)
  hop 5 Parser          429 lines   anchor after parse                 (seed 7502)   GOLD
Smallest host: Parser, 429 lines (also the gold host). No host was substituted.

reachability_probe: in a scratch copy of the fixture the body of TypeHandler.createValue(String, Class<T>) was replaced by
`throw new IllegalStateException("PROBE-REACHED");`; compile OK; full suite (defects4j test): 27 failing tests, every one with
PROBE-REACHED in its failure: all 17 TypeHandlerTest methods (direct calls), the 7 PatternOptionBuilderTest methods that read a typed
value (testSimplePattern, testNumberPattern, testClassPattern, testObjectPattern, testURLPattern, testExistingFilePattern,
testExistingFilePatternFileNotExist, through CommandLine.getOptionObject -> getParsedOptionValue -> createValue(String, Object) ->
createValue(String, Class)) and the 3 CommandLineTest getParsedOptionValue tests. The trigger
TypeHandlerTest::testCreateValueInteger_failure failed with 'expected<ParseException> but was<java.lang.IllegalStateException>'
(PROBE-REACHED). The facade is reached.

Facade: TypeHandler.createValue(String, Class<T>) (allowed target TypeHandler.createValue, BATCH6_PREREGISTRATION row 133; the pool
row's 42-line method). Original computation: compare clazz by identity with the nine PatternOptionBuilder value types (STRING, OBJECT,
NUMBER, DATE, CLASS, FILE, EXISTING_FILE, FILES, URL) and return str or the result of the matching TypeHandler converter
(createObject, createNumber, createDate, createClass, createFile, openFile, createFiles, createURL); any other class throws
ParseException("Unable to handle the class: " + clazz). The facade has no argument guard; its body becomes one delegating call,
`return (T) HelpFormatter.argValueOf(str, clazz);`.

Chain (pass-through plumbing in hops 1-4, the whole type dispatch in the gold):
  hop 1 HelpFormatter.argValueOf      pass-through
  hop 2 Option.valueOfType            pass-through
  hop 3 DefaultParser.argumentValue   pass-through
  hop 4 CommandLine.parsedValue       pass-through
  hop 5 Parser.convertValue           GOLD: the identity dispatch over the nine value types into the TypeHandler converters, with
                                      the rejection of any other class
The facade's computation has no per-element loop; its core is the per-value decision (which converter, if any, applies to the
requested class), and that decision sits whole in the gold. The correct configuration returns the original result for every input:
same identity comparisons in the same order, same converters, the same ParseException for any other class (including a null
class), and null for (null, STRING_VALUE) as before. The gold collects the converted value in a local and returns it after the
if/else chain.

Fault (one-line omission in the gold, in the dispatch decision): the final else of the chain, which rejects a class that is none
of the nine value types, is dropped. Such a class then leaves the local at its initial null and the gold returns null; this is the
real Cli-40 behaviour, moved five calls below the real bug's method. Trigger: the EXISTING test
TypeHandlerTest::testCreateValueInteger_failure (createValue("just-a-string", Integer.class), @Test(expected = ParseException.class))
fails with 'Expected exception: org.apache.commons.cli.ParseException'. It is the only test that asks for a class outside the nine
value types (OptionTest and OptionBuilderTest set Integer/Float types but never convert a value), so it is the only newly failing
test. Every other TypeHandlerTest, PatternOptionBuilderTest and CommandLineTest call still matches its value type and is unchanged.

Quiet gold: the javadoc states the converter's contract ('Converts a command line value to the given type'; '@return the value of
str converted to clazz') and says nothing about classes outside the value types, about ParseException or about null. On the
trigger input the variant returns null, which is not 'just-a-string' converted to Integer: the contract is violated.

External pins (the convention 'a value that cannot be produced for the requested type is signalled by ParseException, never
answered with null'): TypeHandler.createClass ('@throws ParseException if the class could not be found': it throws rather than
returning null) and TypeHandler.createObject ('@throws ParseException if the class could not be found or the object could not be
created'), both intact and called by the gold; CommandLine.getParsedOptionValue ('@throws ParseException if there are problems
turning the option value into the desired type'; it returns null only when the option or its value is absent) and
CommandLine.getOptionObject (null only after catching that ParseException). Passing tests (correct and variant):
testCreateValueClass_notFound, testCreateValueObject_unknownClass, testCreateValueURL_malformed and testCreateValueNumber_noNumber
each expect ParseException for a value that cannot be converted.

Single owner: only the gold holds the list of value types together with the decision for a class outside it; hops 1-4 pass str and
clazz down and the result up, and none of them knows which classes the gold handles. Declared alternatives (G9): hop 1 rejects a
null class, hop 3 rejects a primitive class, hop 4 rejects an interface; none changes Integer.class, so the trigger still fails.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy with
defects4j test, 0 failing tests each):
 B-0 recovery at a caller: hop 4 keeps the gold's result and throws ParseException itself when it is null for a non-null value
     (`final Object value = Parser.convertValue(str, clazz); if (value == null && str != null) { throw new ParseException("Unable
     to handle the class: " + clazz); } return value;`). It treats the gold's null as a sentinel the gold does not document
     ('@return the value of str converted to clazz'), so the gold still returns a value it does not document, and it re-implements
     the gold's rejection one level up. It is also not equivalent to the gold's rejection: above the gold a null result is
     ambiguous, because (null, STRING_VALUE) legitimately converts to null; with the `str != null` test createValue(null,
     Integer.class) still returns null (the correct configuration throws), and without it createValue(null, STRING_VALUE) throws
     (the correct configuration returns null). Only the gold knows that no value type matched.
 B-1 pre-filter: hop 1 rejects every class that is not one of the nine PatternOptionBuilder value types before calling down
     (`if (!java.util.Arrays.asList(PatternOptionBuilder.STRING_VALUE, ..., PatternOptionBuilder.URL_VALUE).contains(clazz)) {
     throw new ParseException("Unable to handle the class: " + clazz); }`): a second implementation of the gold's dispatch list;
     on the trigger input the gold and hops 2-4 are never reached.
 B-2 test-fitted: hop 2 rejects the Number subclasses other than Number itself
     (`if (Number.class.isAssignableFrom(clazz) && clazz != PatternOptionBuilder.NUMBER_VALUE) { throw ... }`): passes the suite,
     but createValue("x", Boolean.class) or any other unlisted class still gives null.
 The facade (the real fix's location) can do the same as B-0 or B-1 around its delegation; both are the same bypasses.

Lie: the facade's javadoc claims the converter is chosen by looking up the class name in a table of converters built once when
TypeHandler is loaded; the code builds no table and compares the class with each value type in turn. It names neither unknown
classes, nor null, nor ParseException, nor any hop.

Pre-edit (behaviour-preserving, needed by the recipe): the facade carries `@SuppressWarnings("unchecked") // returned value will
have type T ...` between its javadoc and its header, so the recipe's rewrite_facade finds no javadoc directly above the header
(find_javadoc_start returns None) and would silently skip the lie; the pre-edit removes that annotation line. The facade body
keeps the unchecked (T) cast of the original returns (a compiler warning only; no -Werror in the build).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold: T1 absent (str feeds every converter and the STRING result; clazz decides every branch and the message); T2 absent
  (value is assigned in every matching branch and returned; no loop, no flag, no counter; every branch has a different effect); T3
  absent (all nine PatternOptionBuilder value types have a branch; no pair, range end or named class handled in part); T4 absent (the
  javadoc names no rule, bound, value class or case; no inline comment). Nothing needed rewriting; the javadoc carries no @throws
  clause, so that no rejection is named in the text once it is omitted.
 Variant gold (javadoc, signature, `Object value = null;`, the nine if/else-if branches, `return value;`):
  T1 absent: str is read by every converter call and by the STRING branch; clazz is compared in every condition; both change the
     returned value.
  T2 absent: value is initialised to null but reassigned in each of the nine branches (not frozen under (b)(i)), and it is returned
     (not dead); there is no loop, so (b)(ii) does not apply; each branch calls a different converter, so no decision is dead.
  T3 absent: the closed set is the nine PatternOptionBuilder value types (a type-code set of a Java type the gold uses), and every
     one of them has its branch; no pair halves or range ends; the text names no class that is handled in part.
  T4 absent: 'Converts a command line value to the given type' and '@return the value of str converted to clazz' are general
     descriptions that the nine branches address; '@param clazz the type of argument' is a parameter description; no @throws
     clause, no 'not null' or 'never null', no limit or case is named; no inline comment; the identifiers (convertValue, value, str,
     clazz) name nothing the body does not meet.

host_notes, hosts and anchors: see the DESIGN dict."""

TH = "src/main/java/org/apache/commons/cli/TypeHandler.java"
HF = "src/main/java/org/apache/commons/cli/HelpFormatter.java"
OP = "src/main/java/org/apache/commons/cli/Option.java"
DP = "src/main/java/org/apache/commons/cli/DefaultParser.java"
CL = "src/main/java/org/apache/commons/cli/CommandLine.java"
PA = "src/main/java/org/apache/commons/cli/Parser.java"

GOLD_TEXT = '''/**
 * Converts a command line value to the given type.
 *
 * @param str the command line value
 * @param clazz the type of argument
 * @return the value of <code>str</code> converted to <code>clazz</code>
 */
public static Object convertValue(final String str, final Class<?> clazz) throws ParseException
{
    Object value = null;
    if (PatternOptionBuilder.STRING_VALUE == clazz)
    {
        value = str;
    }
    else if (PatternOptionBuilder.OBJECT_VALUE == clazz)
    {
        value = TypeHandler.createObject(str);
    }
    else if (PatternOptionBuilder.NUMBER_VALUE == clazz)
    {
        value = TypeHandler.createNumber(str);
    }
    else if (PatternOptionBuilder.DATE_VALUE == clazz)
    {
        value = TypeHandler.createDate(str);
    }
    else if (PatternOptionBuilder.CLASS_VALUE == clazz)
    {
        value = TypeHandler.createClass(str);
    }
    else if (PatternOptionBuilder.FILE_VALUE == clazz)
    {
        value = TypeHandler.createFile(str);
    }
    else if (PatternOptionBuilder.EXISTING_FILE_VALUE == clazz)
    {
        value = TypeHandler.openFile(str);
    }
    else if (PatternOptionBuilder.FILES_VALUE == clazz)
    {
        value = TypeHandler.createFiles(str);
    }
    else if (PatternOptionBuilder.URL_VALUE == clazz)
    {
        value = TypeHandler.createURL(str);
    }
    else
    {
        throw new ParseException("Unable to handle the class: " + clazz);
    }
    return value;
}'''

def hop_doc(summary):
    return '''/**
 * ''' + summary + '''
 *
 * @param str the command line value
 * @param clazz the type of argument
 * @return the value of <code>str</code> converted to <code>clazz</code>
 */'''

HOP1 = hop_doc("Returns the value of an argument converted to the given type.") + '''
public static Object argValueOf(final String str, final Class<?> clazz) throws ParseException
{
    return Option.valueOfType(str, clazz);
}'''

HOP2 = hop_doc("Returns an option value converted to the given type.") + '''
public static Object valueOfType(final String str, final Class<?> clazz) throws ParseException
{
    return DefaultParser.argumentValue(str, clazz);
}'''

HOP3 = hop_doc("Returns the value of an option argument converted to the given type.") + '''
public static Object argumentValue(final String str, final Class<?> clazz) throws ParseException
{
    return CommandLine.parsedValue(str, clazz);
}'''

HOP4 = hop_doc("Returns an option value parsed into the given type.") + '''
public static Object parsedValue(final String str, final Class<?> clazz) throws ParseException
{
    return Parser.convertValue(str, clazz);
}'''

DESIGN = {
 "instance": "Cli-40", "project": "Cli", "bug_id": 40, "seed": 7398,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TH, "class": "org.apache.commons.cli.TypeHandler", "method": "createValue", "near_line": 63},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/cli/TypeHandlerTest.java",
             "test_class": "org.apache.commons.cli.TypeHandlerTest", "test_method": "testCreateValueInteger_failure"},
 "expected_signature": "Expected exception: org.apache.commons.cli.ParseException",
 "gold": {"method": "convertValue", "text": GOLD_TEXT,
          "fault": {"old": "            value = TypeHandler.createURL(str);\n"
                           "        }\n"
                           "        else\n"
                           "        {\n"
                           "            throw new ParseException(\"Unable to handle the class: \" + clazz);\n"
                           "        }\n"
                           "        return value;",
                    "new": "            value = TypeHandler.createURL(str);\n"
                           "        }\n"
                           "        return value;"}},
 "pre_edits": {
   "chain": [{"file": TH,
              "old": "    @SuppressWarnings(\"unchecked\") // returned value will have type T because it is fixed by clazz\n"
                     "    public static <T> T createValue(final String str, final Class<T> clazz) throws ParseException\n",
              "new": "    public static <T> T createValue(final String str, final Class<T> clazz) throws ParseException\n"}],
 },
 "chain": {
   "facade_body": "return (T) HelpFormatter.argValueOf(str, clazz);",
   "lie": "The converter is chosen by looking up the name of the class in a table of converters that is built once, when "
          "TypeHandler is first loaded.",
   "hops": [
     {"file": HF, "class": "org.apache.commons.cli.HelpFormatter", "method": "argValueOf", "imports": [], "text": HOP1},
     {"file": OP, "class": "org.apache.commons.cli.Option", "method": "valueOfType", "imports": [], "text": HOP2},
     {"file": DP, "class": "org.apache.commons.cli.DefaultParser", "method": "argumentValue", "imports": [], "text": HOP3},
     {"file": CL, "class": "org.apache.commons.cli.CommandLine", "method": "parsedValue", "imports": [], "text": HOP4},
     {"file": PA, "class": "org.apache.commons.cli.Parser", "method": "convertValue", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.cli.TypeHandler::createClass",
              "org.apache.commons.cli.TypeHandler::createObject",
              "org.apache.commons.cli.CommandLine::getParsedOptionValue",
              "org.apache.commons.cli.CommandLine::getOptionObject"],
 "ownership_reason": "Only the gold holds the list of value types together with the decision for a class outside it; hops 1-4 "
                     "pass the value and the type down and the result up and know nothing of which types are handled. On the "
                     "trigger input (a String value for Integer.class) the gold returns null, which is not the value converted to "
                     "the requested type that its javadoc promises ('@return the value of str converted to clazz'). The "
                     "convention that a value which cannot be produced for the requested type is signalled by ParseException, "
                     "never answered with null, is pinned outside the gold: TypeHandler.createClass and TypeHandler.createObject "
                     "throw ParseException rather than returning null when the class is missing or cannot be instantiated; "
                     "CommandLine.getParsedOptionValue documents '@throws ParseException if there are problems turning the "
                     "option value into the desired type' and returns null only for an absent option or value, and "
                     "CommandLine.getOptionObject yields null only after catching that ParseException; the passing tests "
                     "testCreateValueClass_notFound, testCreateValueObject_unknownClass, testCreateValueURL_malformed and "
                     "testCreateValueNumber_noNumber expect ParseException for values that cannot be converted. A caller that "
                     "turns the gold's null into a ParseException relies on a null result the gold does not document and "
                     "re-implements the gold's rejection one level up; it cannot even do so exactly, because above the gold a "
                     "null result is ambiguous ((null, STRING_VALUE) legitimately converts to null, so a caller-side null check "
                     "either still returns null for (null, Integer.class) or throws for (null, STRING_VALUE), where the correct "
                     "configuration does the opposite). A caller that checks the class against the nine value types first is a "
                     "second copy of the gold's dispatch list.",
 "ownership_tests": ["org.apache.commons.cli.TypeHandlerTest::testCreateValueClass_notFound",
                     "org.apache.commons.cli.TypeHandlerTest::testCreateValueObject_unknownClass",
                     "org.apache.commons.cli.TypeHandlerTest::testCreateValueURL_malformed",
                     "org.apache.commons.cli.TypeHandlerTest::testCreateValueNumber_noNumber"],
 "compensating": {
   "chain": [
     {"file": HF, "old": "        return Option.valueOfType(str, clazz);",
      "new": "        if (clazz == null) { throw new ParseException(\"Unable to handle the class: \" + clazz); } return Option.valueOfType(str, clazz);",
      "why": "hop 1 rejects a missing (null) type before converting"},
     {"file": DP, "old": "        return CommandLine.parsedValue(str, clazz);",
      "new": "        if (clazz.isPrimitive()) { throw new ParseException(\"Unable to handle the class: \" + clazz); } return CommandLine.parsedValue(str, clazz);",
      "why": "hop 3 rejects a primitive type, which no option value can have"},
     {"file": CL, "old": "        return Parser.convertValue(str, clazz);",
      "new": "        if (clazz.isInterface()) { throw new ParseException(\"Unable to handle the class: \" + clazz); } return Parser.convertValue(str, clazz);",
      "why": "hop 4 rejects an interface type, which no converter can instantiate"},
   ],
 },
 "host_notes": "C10f, host_mode largest5 (n1500_other = 0; 18 other public classes). Hosts = host_files_top5 of the task record, "
               "in order, by newline count: HelpFormatter 1092 (hop 1), Option 1012 (hop 2), DefaultParser 781 (hop 3), "
               "CommandLine 546 (hop 4), Parser 429 (hop 5, gold; smallest host). Anchors from stageB_lib.pick_insertion_anchor "
               "with the instance seed 7398 (+100+i, as mr2_spec inserts them): after HelpFormatter.getLongOptPrefix (seed 7498, "
               "line idx 326), Option.getValue (7499, 540), DefaultParser.parse (7500, 107), CommandLine.getParsedOptionValue "
               "(7501, 161), Parser.parse (7502, 88); all in the outer class (brace depth 1). All five are public top-level "
               "classes in which a static method compiles (Parser is abstract, which does not affect a static method); none was "
               "substituted. All hosts share the package org.apache.commons.cli with TypeHandler and PatternOptionBuilder, so no "
               "import is added. Pre-edit: the @SuppressWarnings line between the facade's javadoc and header is removed so that "
               "the recipe's rewrite_facade can append the lie to the facade's javadoc.",
}
