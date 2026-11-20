"""Main run Closure-10 (C10 recipe on the fixed checkout of Defects4J Closure-10; the real bug modified NodeUtil, the target class).

Facade: NodeUtil.isValidQualifiedName(String) (pool candidate 4). The other candidates were set aside: getNearestFunctionName is a
decision cascade on the function's parent node, and every omission there (a getter/setter or key case) can be repaired in one line
by any hop that holds the node; getSourceName, getSourceFile and getInputId are ancestor walks with many production callers
(NodeTraversal, every pass), so no omission in them fails exactly one test. isValidQualifiedName has no production caller and
exactly one test caller, NodeUtilTest::testValidNames, so any change of its result fails only that test (gate G5).
Original computation: reject a name with a leading or trailing dot; split it at the dots; every part must be a valid simple name
(NodeUtil.isValidSimpleName: TokenStream.isJSIdentifier, not TokenStream.isKeyword, NodeUtil.isLatin).

Chain (hosts in draw order for seed 5904, unusable hosts skipped, see host_notes):
  hop 1 rhino.JSDocInfo$Marker.isValidNamePath        decision: rejects a leading or trailing dot, else delegates
  hop 2 rhino.jstype.JSTypeRegistry.hasValidNamespaceParts   plumbing: splits the name at the dots
  hop 3 jscomp.SymbolTable$Symbol.areValidNameParts     placement: the whole parts array as the range [0, length)
  hop 4 jscomp.TypeCheck.isValidPartRange               pass-through
  hop 5 jscomp.Compiler$CodeBuilder.areSimpleNames      GOLD: the loop over the range with the per-part simple-name check
                                                        (identifier, not a keyword, Latin only)
The correct configuration computes exactly the original result for every input (same guard, same split, same three per-part
predicates, same short-circuit order), and isValidSimpleName / isValidPropertyName are untouched.

Fault (omission of a special-case step in the gold): the keyword test `|| TokenStream.isKeyword(name)` is dropped from the per-part
condition, so a reserved word is accepted as a part. The gold still reads as an ordinary identifier-and-Latin check. Trigger: the
EXISTING test NodeUtilTest::testValidNames; its isValidPropertyName and isValidSimpleName assertions pass (untouched code), and the
first failing assertion is assertFalse(NodeUtil.isValidQualifiedName("true")) at NodeUtilTest.java:1566 (junit
AssertionFailedError). The gold's javadoc states the idiomatic contract (each string is a valid simple name, that is, a valid
variable name) and is silent on reserved words; "true" is not a valid variable name.

External pins (convention outside the gold): NodeUtil.isValidSimpleName (beside the facade) does the same three-step check with
!TokenStream.isKeyword; ProcessClosurePrimitives.verifyProvide validates every dot-separated part of a provided namespace with
isValidPropertyName (= isValidSimpleName) and ProcessClosurePrimitivesTest::testInvalidProvide asserts that 'a.class' is rejected
because of its reserved-word part; CodeGenerator.add quotes an object-literal key unless it is !isKeyword && isJSIdentifier &&
isLatin (CodePrinterTest::testPrint keeps "default" quoted); ConvertToDottedPropertiesTest::testDoNotConvert keeps a['default'].

Single owner: only the gold sees the individual parts together with the per-part predicates; hops 1-2 see the whole name and
hops 3-4 the parts array. A doc-consistent repair above the gold must test every part for a reserved word, which needs a loop
(multi-statement) at hops 3-4 or a split plus a loop at the facade and hops 1-2; no existing public utility checks the parts of a
dotted name (ProcessClosurePrimitives.verifyProvide is private and reports errors). Declared one-line alternatives (G9): hop 1
rejects a name that is itself a reserved word, hop 3 rejects a name whose first part is one, hop 4 rejects a range whose first
string is one; each still accepts "a.true" (NodeUtilTest.java:1567).
Recorded bypasses (not declared, they absorb the trigger):
 B-1 a one-line test of the LAST part only at hops 1-4, e.g. hop 4
     `return !com.google.javascript.rhino.TokenStream.isKeyword(parts[begin + length - 1]) && Compiler.CodeBuilder.areSimpleNames(parts, begin, length);`
     passes testValidNames (its reserved words "true" and "a.true" are both last parts) but still accepts "true.a", so it violates
     every hop's documented contract (each part a valid simple name); test-fitted, not a repair.
 B-2 a loop over the parts at hop 3 or hop 4 (or a split plus a loop at hops 1-2) re-implementing the reserved-word test outside
     the gold: a second implementation, multi-statement.
 B-0 facade: restoring the original split-and-loop over isValidSimpleName discards all five hops.

Lie: the facade's javadoc claims the parts are checked from the last to the first, with repeated parts answered from a set of the
parts already checked; the code splits the name and checks the parts from the first to the last, with no set. It names neither
reserved words nor any step that is omitted nor any hop.

Pre-edit (behaviour-preserving, needed by the recipe): the two-line `// TODO(nicksantos)` line comment between the facade's
javadoc and its header is removed; with it in place rewrite_facade finds no adjacent javadoc and cannot append the lie (a moved
copy of the comment would add a line with fault vocabulary, gate G2b)."""

NU = "src/com/google/javascript/jscomp/NodeUtil.java"
JDI = "src/com/google/javascript/rhino/JSDocInfo.java"
JTR = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
ST = "src/com/google/javascript/jscomp/SymbolTable.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"

GOLD_TEXT = '''/**
 * Determines whether each of the strings in the range
 * {@code [begin, begin + length)} of an array is a valid simple name,
 * that is, a valid variable name.
 *
 * @param names the strings to check
 * @param begin the index of the first string to check
 * @param length the number of strings to check
 * @return whether every string in the range is a valid simple name
 */
public static boolean areSimpleNames(String[] names, int begin, int length) {
  for (int i = begin; i < begin + length; i++) {
    String name = names[i];
    if (!TokenStream.isJSIdentifier(name)
        || TokenStream.isKeyword(name)
        || !NodeUtil.isLatin(name)) {
      return false;
    }
  }
  return true;
}'''

HOP1 = '''/**
 * Determines whether a name is a valid qualified name, that is, one or
 * more simple names joined by dots.
 *
 * @param name the name to check
 * @return whether the name is a valid qualified name
 */
public static boolean isValidNamePath(String name) {
  if (name.startsWith(".") || name.endsWith(".")) {
    return false;
  }
  return JSTypeRegistry.hasValidNamespaceParts(name);
}'''

HOP2 = '''/**
 * Determines whether each of the dot-separated parts of a name is a valid
 * simple name.
 *
 * @param name the name to check, which neither starts nor ends with a dot
 * @return whether every part of the name is a valid simple name
 */
public static boolean hasValidNamespaceParts(String name) {
  return SymbolTable.Symbol.areValidNameParts(name.split("\\\\."));
}'''

HOP3 = '''/**
 * Determines whether each of the parts of a name is a valid simple name.
 *
 * @param parts the parts of the name
 * @return whether every part is a valid simple name
 */
public static boolean areValidNameParts(String[] parts) {
  return TypeCheck.isValidPartRange(parts, 0, parts.length);
}'''

HOP4 = '''/**
 * Determines whether each of the strings in the range
 * {@code [begin, begin + length)} of an array is a valid simple name.
 *
 * @param parts the strings to check
 * @param begin the index of the first string to check
 * @param length the number of strings to check
 * @return whether every string in the range is a valid simple name
 */
public static boolean isValidPartRange(String[] parts, int begin, int length) {
  return Compiler.CodeBuilder.areSimpleNames(parts, begin, length);
}'''

DESIGN = {
 "instance": "Closure-10", "project": "Closure", "bug_id": 10, "seed": 5904,
 "src_root": "src", "test_root": "test",
 "facade": {"file": NU, "class": "com.google.javascript.jscomp.NodeUtil", "method": "isValidQualifiedName", "near_line": 2437},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/NodeUtilTest.java",
             "test_class": "com.google.javascript.jscomp.NodeUtilTest", "test_method": "testValidNames"},
 "expected_signature": "NodeUtilTest.testValidNames(NodeUtilTest.java:1566)",
 "gold": {"method": "areSimpleNames", "text": GOLD_TEXT,
          "fault": {"old": "        if (!TokenStream.isJSIdentifier(name)\n"
                           "            || TokenStream.isKeyword(name)\n"
                           "            || !NodeUtil.isLatin(name)) {",
                    "new": "        if (!TokenStream.isJSIdentifier(name)\n"
                           "            || !NodeUtil.isLatin(name)) {"}},
 "pre_edits": {
   "chain": [{"file": NU,
              "old": "   * Determines whether the given name is a valid qualified name.\n"
                     "   */\n"
                     "  // TODO(nicksantos): This should be moved into a \"Language\" API,\n"
                     "  // so that the results are different for es5 and es3.\n"
                     "  public static boolean isValidQualifiedName(String name) {",
              "new": "   * Determines whether the given name is a valid qualified name.\n"
                     "   */\n"
                     "  public static boolean isValidQualifiedName(String name) {"}],
 },
 "chain": {
   "facade_body": "return com.google.javascript.rhino.JSDocInfo.Marker.isValidNamePath(name);",
   "lie": "The parts of the name are checked from the last to the first, and a part that repeats a part already "
          "checked is answered from a set of the accepted parts instead of being checked again.",
   "hops": [
     {"file": JDI, "class": "com.google.javascript.rhino.JSDocInfo$Marker", "method": "isValidNamePath",
      "imports": ["com.google.javascript.rhino.jstype.JSTypeRegistry"], "text": HOP1},
     {"file": JTR, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "hasValidNamespaceParts",
      "imports": ["com.google.javascript.jscomp.SymbolTable"], "text": HOP2},
     {"file": ST, "class": "com.google.javascript.jscomp.SymbolTable$Symbol", "method": "areValidNameParts",
      "imports": [], "text": HOP3},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "isValidPartRange",
      "imports": [], "text": HOP4},
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "areSimpleNames",
      "imports": ["com.google.javascript.rhino.TokenStream"], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.NodeUtil::isValidSimpleName",
              "com.google.javascript.jscomp.ProcessClosurePrimitives::verifyProvide",
              "com.google.javascript.jscomp.CodeGenerator::add"],
 "ownership_reason": "Only the per-part check in the gold sees each dot-separated part together with the simple-name predicates; "
                     "the guard, the split, the range placement and the pass-through hand the name or the parts array along and "
                     "cannot reject every reserved-word part with a one-line change (that needs a loop over the parts). The "
                     "convention is pinned outside the gold: NodeUtil.isValidSimpleName ('a valid variable name') rejects "
                     "TokenStream.isKeyword names; ProcessClosurePrimitives.verifyProvide validates each part of a dotted "
                     "namespace with isValidPropertyName and ProcessClosurePrimitivesTest.testInvalidProvide rejects "
                     "'a.class'; CodeGenerator.add quotes object-literal keys that are keywords (CodePrinterTest.testPrint keeps "
                     "\"default\" quoted) and ConvertToDottedPropertiesTest.testDoNotConvert keeps a['default']. The gold's "
                     "javadoc promises valid simple names, that is, valid variable names, which 'true' is not.",
 "ownership_tests": ["com.google.javascript.jscomp.ProcessClosurePrimitivesTest::testInvalidProvide",
                     "com.google.javascript.jscomp.ConvertToDottedPropertiesTest::testDoNotConvert",
                     "com.google.javascript.jscomp.CodePrinterTest::testPrint"],
 "compensating": {
   "chain": [
     {"file": JDI, "old": "if (name.startsWith(\".\") || name.endsWith(\".\")) {",
      "new": "if (name.startsWith(\".\") || name.endsWith(\".\") || TokenStream.isKeyword(name)) {",
      "why": "hop 1 also rejects a name that is itself a reserved word"},
     {"file": ST, "old": "return TypeCheck.isValidPartRange(parts, 0, parts.length);",
      "new": "return !com.google.javascript.rhino.TokenStream.isKeyword(parts[0]) && TypeCheck.isValidPartRange(parts, 0, parts.length);",
      "why": "hop 3 rejects a name whose first part is a reserved word"},
     {"file": TC, "old": "return Compiler.CodeBuilder.areSimpleNames(parts, begin, length);",
      "new": "return !com.google.javascript.rhino.TokenStream.isKeyword(parts[begin]) && Compiler.CodeBuilder.areSimpleNames(parts, begin, length);",
      "why": "hop 4 rejects a range whose first string is a reserved word"},
   ],
 },
 "host_notes": "Hosts for seed 5904 (mr_lib preview, target com/google/javascript/jscomp/NodeUtil.java), draw order JSDocInfo, "
               "jsonml.Reader, regex.RegExpTree, parsing.JsDocInfoParser, rhino.Node, jstype.JSTypeRegistry, SymbolTable, TypeCheck, "
               "DefaultPassConfig, Compiler, CompilerOptions. Closure uses 2-space indentation, so the recipe's anchor picker (which "
               "keeps only 4-space-indented methods) lands on members of NESTED classes, or, when a file has fewer than three such "
               "methods, appends the hop before the outer class's closing brace. A host is unusable when the hop's enclosing class "
               "cannot be reached from the calling hop or a static method there does not compile. Each hop position i was filled "
               "with the next drawn host whose anchor at the recipe's own seed (5904+100+i) is usable: hop 1 JSDocInfo (anchor in "
               "public static final JSDocInfo.Marker); hop 2: skipped jsonml.Reader (anchor in private enum Reader.Operator; "
               "jsonml is also excluded from the build), regex.RegExpTree (package-private RegExpTree.WordBoundary, not visible "
               "from rhino), parsing.JsDocInfoParser (private static ExtractionInfo), rhino.Node (private static IntPropListItem), "
               "took JSTypeRegistry (appended at the end of the class); hop 3 SymbolTable (public static final SymbolTable.Symbol); "
               "hop 4 TypeCheck (appended at the end of the class); hop 5: skipped DefaultPassConfig (non-static inner class "
               "GlobalTypeResolver, a static method there does not compile), took Compiler (public static Compiler.CodeBuilder). "
               "The same assignment results from replacing the preview's unusable hosts 2-5 by drawn hosts 6, 7, 8 and then 10 "
               "(host 9 unusable at position 5). Nested-class hops carry the method catalog's binary names (Outer$Nested). The "
               "recipe indents inserted text by 4 spaces and the facade body by 8, which matches nested members but is off by 2 "
               "for the facade and the two appended top-level hops in this 2-space codebase (cosmetic, recipe-wide for Closure).",
}
