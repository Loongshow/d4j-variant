"""Main run Closure-149__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Closure-149; the real bug modified AbstractCommandLineRunner, CommandLineRunner, Compiler and CompilerOptions). The bug has no
static-facade instance (pool v2: loose_tested_static_only), so addendum section 2 has nothing to refer to (B8 note section 1).

Facade: CompilerOptions.getDefineReplacements() (instance method; the single allowed candidate of the task record,
BATCH9_PREREGISTRATION.md rank 314, facade_planned_by = null, no facade reuse). The facade's class is one the real bug modified.
Original computation: a new HashMap is filled, for each entry of the private field defineReplacements (Map<String, Object>, written only
by the four setDefineTo...Literal setters, so every value is a Boolean, an Integer, a Double or a String), with a node for the value: a
Boolean gives new Node(Token.TRUE) or new Node(Token.FALSE), an Integer or a Double Node.newNumber of its value, and any other value (a
String; Preconditions.checkState(value instanceof String)) Node.newString of it. The map is returned.

facade_variant: V1 (state as parameters). state_passed: the private field defineReplacements (Map<String, Object>), read by the facade
and handed to hop 1; nothing is written, no write-back. The facade body is one call to hop 1 (the original has no guard). No visibility
is widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The facade calls no
private method of its class, so V4 does not apply; every type the chain names (Map, HashMap, Node, Token) is public, so V3/V5 do not
apply. The chain tests Number (Integer and Double are both Numbers; Node.newNumber takes a double, so the original's
Node.newNumber(int) is the same call) and its last case writes value.toString(); the original's checkState for that case can never fail
(the field is private and only the four setters write it), so the chain returns the original result for every map the class can hold.

Redistribution of the computation: hop 1 creates the result map and returns it (aggregation); hops 2 and 3 hand the values and the
result map on (pass-through); hop 4 is the fold: one pass over the defines putting, under each name, the node hop 5 returns for its
value (placement); the gold, hop 5, is the per-value core: it decides the node for one value.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Closure-149-probe of the fixture, the first statement
of getDefineReplacements() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t com.google.javascript.jscomp.CompilerOptionsTest::testDefines`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at CompilerOptions.getDefineReplacements(CompilerOptions.java:737); `defects4j test -t
com.google.javascript.jscomp.CommandLineRunnerTest::testDefineFlag`: 1 failing test, java.lang.RuntimeException:
java.lang.IllegalStateException: PROBE-REACHED (through Compiler.compile and DefaultPassConfig's processDefines pass). The facade is
reached directly by testDefines and through the compiler by testDefineFlag. The scratch copy was removed.

Hosts (host_mode = "1500"; the recipe's seeded draw, seed 5248, run as `mr_lib.py preview Closure-149
src/com/google/javascript/jscomp/CompilerOptions.java n` with the facade file as the task record writes it
(facade_files_excluded); anchors with seed 5248 + 100 + position, exactly as mr3_spec.py inserts them). Draw order: Compiler (1840),
Parser (2404), JSTypeRegistry (1530), DefaultPassConfig (2006), JsDocInfoParser (2051), Node (2137), TokenStream (1696), TypeCheck (1715),
NodeUtil (2125). Positions 1 to 3 take the first three drawn hosts. At position 4, DefaultPassConfig, JsDocInfoParser and Node cannot
carry the hop (host rule of BUILD_BRIEF: the method there does not compile or cannot be called): the recipe anchor in DefaultPassConfig
is `process` of the private static nested class PureFunctionMarker at every seed (a method there is not accessible from another class),
in JsDocInfoParser `addWarning` of the private inner class ErrorReporterParser at every seed (an inner class cannot declare a static
method under Java 11), in Node at position 4 `append` of the inner class FileLevelJsDocBuilder (same) and at position 5 `remove` of the
private static nested class SiblingNodeIterable (not accessible); so position 4 takes the next drawn host, TokenStream, and position 5
TypeCheck. The five hosts are the first five drawn hosts that can carry a public static method, in draw order:
  hop 1 jscomp.Compiler            1840 lines  defineValueNodes       aggregation: creates the result map and returns it
        (the recipe anchor, after getLength, is a member of Compiler's public static nested class CodeBuilder, so the hop is
        Compiler.CodeBuilder.defineValueNodes; a public static member of a public static nested class compiles and is callable)
  hop 2 rhino.Parser               2404 lines  addDefineValueNodes    pass-through
  hop 3 rhino.jstype.JSTypeRegistry 1530 lines putDefineValueNodes    pass-through
  hop 4 rhino.TokenStream          1696 lines  writeDefineValueNodes  fold: puts, under each define's name, the node for its value
  hop 5 jscomp.TypeCheck           1715 lines  newValueNode           GOLD: the node for one define value
Host newline counts 1840, 2404, 1530, 1696, 1715; the smallest host has 1530 lines (JSTypeRegistry); every host is in the 1500-line pool.

Fault (one-step omission of a special-case decision in the gold): the boolean case is dropped from the gold (the
`if (value instanceof Boolean) { return new Node(... ? Token.TRUE : Token.FALSE); }` head is removed, so the gold starts at
`if (value instanceof Number) {`). A boolean define value then gets a string node of its text ("true") instead of a node whose value is
the boolean true. The gold then reads as the ordinary routine "a number gives a number node, any other value a string node of its text".
Trigger: the EXISTING test CommandLineRunnerTest::testDefineFlag (--define=FOO, --define="BAR=5", --D CCC, -D DDD; expected output
"var FOO = true, BAR = 5, CCC = true, DDD = true;"); on the variant the three boolean defines are replaced by the string "true". It is
the only test whose boolean defines reach the compiled output: CompilerOptionsTest::testDefines also sets boolean defines, but its
assertEquivalent(new Node(Token.TRUE), actual) calls the base Node.isEquivalentTo on a plain TRUE/FALSE node, which compares no node type,
so it passes on the variant (its number and string checks still bind the chain); ProcessDefinesTest builds its own TRUE/FALSE nodes and
does not reach the chain. Gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (a new node whose value is the given value) and is silent on booleans; the
variant gives the boolean true a node whose value is the string "true", so the contract is violated on the trigger input. The
convention is pinned outside the gold: CompilerOptions.setDefineToBooleanLiteral ("Sets the value of the @define variable in JS to a
boolean literal"), DefaultPassConfig.getAdditionalReplacements (the COMPILED define is replaced by new Node(Token.TRUE)),
NodeUtil.isValidDefineValue (TRUE and FALSE are define value types beside STRING and NUMBER) and
AbstractCommandLineRunner.createDefineReplacements (the texts true and false become boolean defines); passing tests:
ProcessDefinesTest::testOverriding1 (boolean defines are replaced by TRUE/FALSE nodes), CompilerOptionsTest::testDefines (number and string
nodes through the chain), CommandLineRunnerTest::testDefineFlag2 and testDefineFlag3 (string nodes through the chain).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold. The gold
text names no format or standard (no "literal", "JavaScript", "keyword", "define" or type-list wording) and no value class:
 Correct gold (javadoc, signature, the Boolean, Number and fallback returns):
  T1 absent: the only parameter, value, is tested by both instanceof checks and feeds every returned node; it is never argument-checked.
  T2 absent: no local variable; the Boolean test, the ternary (TRUE or FALSE from the value) and the Number test each change the returned
     node; no branch is empty or duplicates another.
  T3 absent: both halves of the boolean pair are handled (TRUE and FALSE); Boolean, Number and every other value each get a node; the
     gold names no set of value classes, so nothing of a closed set is left out.
  T4 absent: 'a new node whose value is the given value' is a general description that every return addresses; '@return a new
     node for the value' is met on every path (each path returns a new node); no inline comment.
 Variant gold (javadoc, signature, `if (value instanceof Number) { return Node.newNumber(...); }`, `return Node.newString(...)`):
  T1 absent: value is tested by the Number check and feeds both returned nodes; it is never only argument-checked.
  T2 absent: no local variable; the Number test changes the returned node (number node vs string node); no dead branch or ternary.
  T3 absent: exactly one value class (Number) gets its own case and every other value one common fallback; the gold's text names no
     class of values and no format (closure rule), and no pair half or range end is involved ('one member of a larger unnamed set').
  T4 absent: the javadoc and @return are general descriptions that lines of the body address (a new node is returned for every value);
     the identifiers (newValueNode, value) name no rule, bound or value class; no comment.

Single owner: only the gold decides a value's node; hops 1 to 3 never look at a value, and hop 4 only hands each value to the gold and
puts the returned node under the define's name. The variant gold creates only NUMBER and STRING nodes, so no caller can pre-filter a
boolean into something the variant gold turns into a TRUE node; a caller can restore the boolean nodes only by testing the values itself
and creating the TRUE/FALSE nodes instead of the gold, a second implementation of the gold's decision. Declared alternatives (G9): hop 1
keeps the nodes in name order (TreeMap); hop 3 hands a copy of the values on; hop 4 walks the defines in name order. None makes the
trigger pass.
Recorded bypasses:
 B-0 the facade restored to its original body discards the chain, including the gold.
 B-1 a hop (for instance hop 4 around the gold call, or hop 1 after the call) tests each value for Boolean itself and puts
     new Node(Token.TRUE) / new Node(Token.FALSE) instead of (or over) the gold's node: a second implementation of the gold's decision.

Lie: the facade's javadoc claims the defines are sorted by name first and their nodes are created in that order; no step of the chain
sorts the defines (hop 4 iterates the HashMap field's entry set and the result is a HashMap). It names neither booleans nor any hop."""

CO = "src/com/google/javascript/jscomp/CompilerOptions.java"
COMP = "src/com/google/javascript/jscomp/Compiler.java"
PARSER = "src/com/google/javascript/rhino/Parser.java"
JTR = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"

GOLD_TEXT = '''/**
 * Returns a new node whose value is the given value.
 *
 * @param value a value
 * @return a new node for the value
 */
public static Node newValueNode(Object value) {
  if (value instanceof Boolean) {
    return new Node(((Boolean) value).booleanValue()
        ? Token.TRUE : Token.FALSE);
  }
  if (value instanceof Number) {
    return Node.newNumber(((Number) value).doubleValue());
  }
  return Node.newString(value.toString());
}'''

HOP1 = '''/**
 * Returns a new map from the name of each define to a node for its
 * value.
 *
 * @param values the value of each define, by name
 * @return a new map of value nodes, by define name
 */
public static Map<String, Node> defineValueNodes(
    Map<String, Object> values) {
  Map<String, Node> nodes = new HashMap<String, Node>();
  Parser.addDefineValueNodes(values, nodes);
  return nodes;
}'''

HOP2 = '''/**
 * Adds to a map, for each define, a node for its value.
 *
 * @param values the value of each define, by name
 * @param nodes the map to add the value nodes to
 */
public static void addDefineValueNodes(Map<String, Object> values,
                                       Map<String, Node> nodes)
{
    JSTypeRegistry.putDefineValueNodes(values, nodes);
}'''

HOP3 = '''/**
 * Puts into a map, for each define, a node for its value.
 *
 * @param values the value of each define, by name
 * @param nodes the map to put the value nodes into
 */
public static void putDefineValueNodes(
    Map<String, Object> values, Map<String, Node> nodes) {
  TokenStream.writeDefineValueNodes(values, nodes);
}'''

HOP4 = '''/**
 * Writes into a map, under the name of each define, a new node for its
 * value.
 *
 * @param values the value of each define, by name
 * @param nodes the map to write the value nodes into
 */
public static void writeDefineValueNodes(Map<String, Object> values,
                                         Map<String, Node> nodes)
{
    for (Map.Entry<String, Object> entry : values.entrySet()) {
        nodes.put(entry.getKey(),
                  TypeCheck.newValueNode(entry.getValue()));
    }
}'''

DESIGN = {
 "instance": "Closure-149", "project": "Closure", "bug_id": 149, "seed": 5248,
 "src_root": "src", "test_root": "test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field defineReplacements (Map<String, Object>), passed to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [1840, 2404, 1530, 1696, 1715],
 "reachability_probe": "getDefineReplacements() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Closure-149-probe: CompilerOptionsTest::testDefines fails with PROBE-REACHED at "
                       "CompilerOptions.getDefineReplacements(CompilerOptions.java:737); CommandLineRunnerTest::testDefineFlag fails "
                       "with RuntimeException: IllegalStateException: PROBE-REACHED (through Compiler.compile / processDefines)",
 "facade": {"file": CO, "class": "com.google.javascript.jscomp.CompilerOptions", "method": "getDefineReplacements", "near_line": 736},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/CommandLineRunnerTest.java",
             "test_class": "com.google.javascript.jscomp.CommandLineRunnerTest", "test_method": "testDefineFlag"},
 "expected_signature": "Result: var FOO=\"true\",BAR=5,CCC=\"true\"",
 "gold": {"method": "newValueNode", "text": GOLD_TEXT,
          "fault": {"old": "      if (value instanceof Boolean) {\n"
                           "        return new Node(((Boolean) value).booleanValue()\n"
                           "            ? Token.TRUE : Token.FALSE);\n"
                           "      }\n"
                           "      if (value instanceof Number) {",
                    "new": "      if (value instanceof Number) {"}},
 "chain": {
   "facade_body": "return Compiler.CodeBuilder.defineValueNodes(defineReplacements);",
   "lie": "The defines are sorted by name first, and the node of each one is created in that order.",
   "hops": [
     {"file": COMP, "class": "com.google.javascript.jscomp.Compiler.CodeBuilder", "method": "defineValueNodes",
      "imports": ["com.google.javascript.rhino.Parser"], "text": HOP1},
     {"file": PARSER, "class": "com.google.javascript.rhino.Parser", "method": "addDefineValueNodes",
      "imports": ["java.util.Map", "com.google.javascript.rhino.jstype.JSTypeRegistry"], "text": HOP2},
     {"file": JTR, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "putDefineValueNodes",
      "imports": ["com.google.javascript.rhino.TokenStream"], "text": HOP3},
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "writeDefineValueNodes",
      "imports": ["java.util.Map", "com.google.javascript.jscomp.TypeCheck"], "text": HOP4},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "newValueNode",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.CompilerOptions::setDefineToBooleanLiteral",
              "com.google.javascript.jscomp.DefaultPassConfig::getAdditionalReplacements",
              "com.google.javascript.jscomp.NodeUtil::isValidDefineValue",
              "com.google.javascript.jscomp.AbstractCommandLineRunner::createDefineReplacements"],
 "ownership_reason": "Only the gold decides the node for a define value: hop 1 creates and returns the result map, hops 2 and 3 hand "
                     "the values and the map on, and hop 4 hands each value to the gold and puts the returned node under the "
                     "define's name, without looking at the value. The gold's javadoc promises a new node whose value is the given "
                     "value; the variant gold gives the boolean true a string node whose value is the text \"true\", so "
                     "testDefineFlag's boolean defines come out as \"true\". The variant gold creates only number and string nodes, "
                     "so no caller can pre-filter a value into a TRUE node; restoring them needs a caller that tests the values "
                     "itself and creates the TRUE/FALSE nodes instead of the gold. The convention is pinned outside the gold: "
                     "CompilerOptions.setDefineToBooleanLiteral sets a define 'to a boolean literal', "
                     "DefaultPassConfig.getAdditionalReplacements replaces the COMPILED define by new Node(Token.TRUE), "
                     "NodeUtil.isValidDefineValue accepts TRUE and FALSE as define values, and "
                     "AbstractCommandLineRunner.createDefineReplacements turns the texts true and false into boolean defines; "
                     "ProcessDefinesTest::testOverriding1 (boolean defines replaced by TRUE/FALSE nodes) passes, as do "
                     "CompilerOptionsTest::testDefines and CommandLineRunnerTest::testDefineFlag2 / testDefineFlag3 (number and "
                     "string nodes through the chain).",
 "ownership_tests": ["com.google.javascript.jscomp.ProcessDefinesTest::testOverriding1",
                     "com.google.javascript.jscomp.CompilerOptionsTest::testDefines",
                     "com.google.javascript.jscomp.CommandLineRunnerTest::testDefineFlag2",
                     "com.google.javascript.jscomp.CommandLineRunnerTest::testDefineFlag3"],
 "compensating": {
   "chain": [
     {"file": COMP, "old": "Map<String, Node> nodes = new HashMap<String, Node>();",
      "new": "Map<String, Node> nodes = new java.util.TreeMap<String, Node>();",
      "why": "hop 1 keeps the nodes in name order"},
     {"file": JTR, "old": "TokenStream.writeDefineValueNodes(values, nodes);",
      "new": "TokenStream.writeDefineValueNodes(new HashMap<String, Object>(values), nodes);",
      "why": "hop 3 hands a copy of the values on"},
     {"file": TS, "old": "for (Map.Entry<String, Object> entry : values.entrySet()) {",
      "new": "for (Map.Entry<String, Object> entry : new java.util.TreeMap<String, Object>(values).entrySet()) {",
      "why": "hop 4 walks the defines in name order"},
   ],
 },
 "host_notes": "host_mode 1500: the recipe's seeded draw (mr_lib.py preview Closure-149 "
               "src/com/google/javascript/jscomp/CompilerOptions.java n, seed 5248, the facade file as the task record writes it) in "
               "draw order Compiler (1840), Parser (2404), JSTypeRegistry (1530), DefaultPassConfig (2006), "
               "parsing.JsDocInfoParser (2051), rhino.Node (2137), TokenStream (1696), TypeCheck (1715), NodeUtil (2125). Positions "
               "1-3: Compiler, Parser, JSTypeRegistry. Position 4: DefaultPassConfig skipped (its recipe anchor at every seed is "
               "after process in the private static nested class PureFunctionMarker, whose members another class cannot call), "
               "JsDocInfoParser skipped (anchor at every seed after addWarning in the private inner class ErrorReporterParser, "
               "where a static method does not compile under Java 11), Node skipped (position 4 anchor after append in the inner "
               "class FileLevelJsDocBuilder; position 5 anchor after remove in the private static nested class "
               "SiblingNodeIterable), so TokenStream takes position 4 and TypeCheck position 5. Anchors (seed 5248 + 100 + "
               "position - 1): hop 1 after getLength (Compiler, seed 5348; a member of the public static nested class "
               "Compiler.CodeBuilder, so the facade calls Compiler.CodeBuilder.defineValueNodes), hop 2 after parse (Parser, 5349), "
               "hop 3 at the end of the class (JSTypeRegistry, no interior anchor), hop 4 after getTokenno (TokenStream, 5351), "
               "hop 5 at the end of the class (TypeCheck, no interior anchor). The source-root-relative form of the same command "
               "(com/google/javascript/jscomp/CompilerOptions.java) applies the 'distinct from the target package' preference and "
               "draws Parser, JSTypeRegistry, TokenStream, JsDocInfoParser, DefaultPassConfig, Node, TypeCheck, Compiler, NodeUtil; "
               "its first five usable hosts are the same five classes in another order. Each hop imports the next host (and "
               "java.util.Map where needed); Node and Token are imported in Compiler, JSTypeRegistry and TypeCheck and are in "
               "Parser's and TokenStream's own package.",
}
