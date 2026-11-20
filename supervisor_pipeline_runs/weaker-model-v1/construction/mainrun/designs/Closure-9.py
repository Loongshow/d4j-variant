"""Main run Closure-9 (C10 recipe on the fixed checkout of Defects4J Closure-9; the real bug modified ProcessCommonJSModules,
the target class).

Facade: ProcessCommonJSModules.toModuleName(String requiredFilename, String currentFilename) (allowed target toModuleName,
BATCH4_PREREGISTRATION.md row Closure-9; the two-argument overload, header at line 99). The one-argument overload
toModuleName(String) was set aside: it is reached by every CommonJS script (guessCJSModuleName), by the two-argument overload and
by CommandLineRunner, and each of its per-character steps is exercised by several tests (the '-' to '_' step by testDash AND
testModuleName, the '/' to '$' and '.js' steps by most CommonJS tests), so no omission in it fails exactly one test (gate G5).
The two-argument overload's relative addressing is exercised only by ProcessCommonJSModulesTest::testModuleName: every other
require in the suite (testWithoutExports, testExports, testDash, CompilerTest's CommonJS tests) names a top-level module.
The one-argument overload stays intact beside the facade; the chain hands its resolved path to it, as the original did.
Original computation of the facade: strip a trailing ".js" from both filenames; if the required filename starts with "./" or
"../", resolve it against the current filename with java.net.URI (the last segment of the current filename is dropped, the
required path is appended, "." segments are removed and every ".." segment removes the segment before it); then convert with
toModuleName(String).

Chain (seed 5268, target com/google/javascript/jscomp/ProcessCommonJSModules.java; unusable drawn hosts replaced by the next
drawn hosts, see host_notes):
  hop 1 rhino.jstype.JSTypeRegistry.requiredModuleName          plumbing: removes the ".js" extension of both filenames
  hop 2 jscomp.SymbolTable$SymbolScope.scopedModuleName          decision: a "./" or "../" path goes down the chain, any other
                                                                 filename is converted as a top-level module name
  hop 3 rhino.JSDocInfo$Marker.relativeModuleName                placement: drops a leading "./" (the directory itself)
  hop 4 jscomp.CompilerOptions$TweakProcessing.moduleNameFrom    pass-through
  hop 5 jscomp.Compiler$CodeBuilder.moduleNameAt                 GOLD: the directory segments of the requiring file, the walk
                                                                 over the path's segments (a ".." segment steps back one
                                                                 directory), the join and the conversion
The correct configuration returns the original result for every input whose only "." segment is a leading "./" and whose ".."
segments do not climb more than one level above the top directory (same .js stripping, same relative/top-level decision, same
resolution, same final toModuleName(String) call); it was checked on all of testModuleName's cases.

Fault (omission of a special-case decision in the gold): the ".." decision in the segment walk is dropped, so every segment of the
path is appended to the directory and a ".." segment stays in the name. The gold then reads as an ordinary "directory of the
requiring file plus path" routine. Trigger: the EXISTING test ProcessCommonJSModulesTest::testModuleName; its first two
assertions ("./baz.js" and "./baz-bar.js" from "foo/bar.js") pass, and the third, toModuleName("../baz.js", "foo/bar.js") =
"module$baz", fails with ComparisonFailure expected:<module$[]baz> but was:<module$[foo$..$]baz>. No other test passes a
relative require. The gold's javadoc states the idiomatic contract (the module name of the file that a path leads to from the
directory of a requiring file) and is silent on "..": the path "../baz" leads from directory "foo" to the file "baz", whose module
name is "module$baz".

External pins (convention outside the gold): the facade's own javadoc ("relative addressing with ./ and ../ based on
currentFilename"); PathUtil.collapseDots does the same step in production code ('"a/b/../c" results in "a/c"', a ".." fragment
removes the previous one), reached through PathUtil.makeAbsolute from DepsGenerator; the one-argument toModuleName(String) and its
passing tests (testDash, testGuessModuleName, testWithoutExports) pin the conversion that the gold hands its path to, and
CompilerTest / CommandLineRunnerTest pin the top-level branch.

Single owner: only the gold holds the directory of the requiring file together with the individual segments of the path. Hops 1-4
hold the two strings; hop 2 sends top-level names past the chain. The trigger's target "baz" lies outside the requiring file's
directory "foo/", so no path without ".." leads to it from that file: a one-line edit above the gold can only make the gold's
output correct by handing it another requiring file or by computing the resolution itself. Declared alternatives (G9): hop 3
also drops a leading "../"; hop 3 steps the requiring file up one directory for a "../" path; hop 4 collapses the dots of the path
alone with PathUtil.collapseDots. Each still returns a ".." name or "module$foo$baz" for "../baz.js" from "foo/bar.js".
Recorded bypasses (checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests):
 B-0 hop 2 (or the facade) returns ProcessCommonJSModules.toModuleName(java.net.URI.create(current).resolve(required).toString()),
     the original URI resolution, discarding hops 3-5 including the gold.
 B-1 hop 4 pre-resolves and hands the gold a stand-in requiring file:
     return Compiler.CodeBuilder.moduleNameAt(PathUtil.collapseDots(current + "/../" + path), "");
     the gold's documented parameter (the filename of the requiring file) is no longer the requiring file, and the resolution is
     a second implementation outside the gold.
 B-2 test-fitted: hop 4 collapses dots in the gold's OUTPUT by reading '$' as a separator,
     return PathUtil.collapseDots(Compiler.CodeBuilder.moduleNameAt(path, current).replace('$', '/')).replace('/', '$');
     a path that climbs past the top directory then loses the "module$" part of its name (require('../../x') from 'foo/bar'
     gives "x"), contradicting toModuleName(String)'s "All moduleNames get a "module$" prefix", and a '$' inside a file name is
     taken as a separator.

Lie: the facade's javadoc claims module names already computed for the current filename are kept in a table and a required
filename found there is answered from it without being converted again; the code keeps no table. It names neither ".." nor any
step that is omitted nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: path is split into the walked segments, current into the directory segments; both reach the returned name.
  T2 absent: segments is initialised from current (not a literal), changed in the loop and joined into the return value; the
     loop variable decides the if; the if has two different effects (remove the last segment / append the segment).
  T3 absent: ".." is the only special segment the gold treats; the gold names no format or class that would close a set around
     it (a leading "./" never reaches the gold: hop 3 drops it), no pair half or range end is treated on one side only.
  T4 absent: the javadoc names the module name of the file a path leads to from the directory of a requiring file (a general
     description the body addresses) and caller preconditions ("without extension"); no limit, bound, value class or case.
 Variant gold (javadoc, signature, segments = current's segments, drop the last, append every segment of path, convert):
  T1 absent: path is read by the loop and each segment is appended; current gives the directory segments; both change the name.
  T2 absent: segments is not literal-initialised, is assigned by the remove and the appends and is read in the return; the loop
     variable is appended; there is no branch, case or ternary left, so no dead decision.
  T3 absent: no special segment, case or value class is treated at all (no member handled); nothing in the text names a set.
  T4 absent: 'the module name of the file that a path leads to from the directory of a requiring file' is a general description
     that the directory computation, the loop and the conversion address; '@param path the path, without extension' and
     '@param current the filename of the requiring file, without extension' are caller preconditions; no inline comment; the
     identifiers (segments, segment) name nothing the body does not meet."""

PCJ = "src/com/google/javascript/jscomp/ProcessCommonJSModules.java"
JTR = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
ST = "src/com/google/javascript/jscomp/SymbolTable.java"
JDI = "src/com/google/javascript/rhino/JSDocInfo.java"
CO = "src/com/google/javascript/jscomp/CompilerOptions.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"

GOLD_TEXT = r'''/**
 * Returns the module name of the file that a path leads to from the
 * directory of a requiring file.
 *
 * @param path the path, without extension
 * @param current the filename of the requiring file, without extension
 * @return the module name of the file
 */
public static String moduleNameAt(String path, String current) {
  List<String> segments = Lists.newArrayList(current.split("/"));
  segments.remove(segments.size() - 1);
  for (String segment : path.split("/")) {
    if (segment.equals("..") && !segments.isEmpty()) {
      segments.remove(segments.size() - 1);
    } else {
      segments.add(segment);
    }
  }
  return ProcessCommonJSModules.toModuleName(Joiner.on('/').join(segments));
}'''

HOP1 = r'''/**
 * Returns the module name of a file that another file requires. The ".js"
 * extension is removed from both filenames first.
 *
 * @param required the filename given to require
 * @param current the filename of the requiring file
 * @return the module name of the required file
 */
public static String requiredModuleName(String required, String current) {
  return SymbolTable.SymbolScope.scopedModuleName(
      required.replaceAll("\\.js$", ""), current.replaceAll("\\.js$", ""));
}'''

HOP2 = r'''/**
 * Returns the module name of a file that another file requires. A filename
 * that starts with "./" or "../" is a path from the directory of the
 * requiring file; any other filename is the name of a top-level module.
 *
 * @param required the filename given to require, without extension
 * @param current the filename of the requiring file, without extension
 * @return the module name of the required file
 */
public static String scopedModuleName(String required, String current) {
  if (required.startsWith("./") || required.startsWith("../")) {
    return JSDocInfo.Marker.relativeModuleName(required, current);
  }
  return ProcessCommonJSModules.toModuleName(required);
}'''

HOP3 = r'''/**
 * Returns the module name of the file that a path leads to from the
 * directory of a requiring file. A leading "./", which names that
 * directory itself, is dropped from the path.
 *
 * @param path the path, starting with "./" or "../", without extension
 * @param current the filename of the requiring file, without extension
 * @return the module name of the file
 */
public static String relativeModuleName(String path, String current) {
  return CompilerOptions.TweakProcessing.moduleNameFrom(
      path.replaceFirst("^\\./", ""), current);
}'''

HOP4 = r'''/**
 * Returns the module name of the file that a path leads to from the
 * directory of a requiring file.
 *
 * @param path the path, without extension
 * @param current the filename of the requiring file, without extension
 * @return the module name of the file
 */
public static String moduleNameFrom(String path, String current) {
  return Compiler.CodeBuilder.moduleNameAt(path, current);
}'''

DESIGN = {
 "instance": "Closure-9", "project": "Closure", "bug_id": 9, "seed": 5268,
 "src_root": "src", "test_root": "test",
 "facade": {"file": PCJ, "class": "com.google.javascript.jscomp.ProcessCommonJSModules", "method": "toModuleName", "near_line": 99},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/ProcessCommonJSModulesTest.java",
             "test_class": "com.google.javascript.jscomp.ProcessCommonJSModulesTest", "test_method": "testModuleName"},
 "expected_signature": "but was:<module$[foo$..$]baz>",
 "gold": {"method": "moduleNameAt", "text": GOLD_TEXT,
          "fault": {"old": "        if (segment.equals(\"..\") && !segments.isEmpty()) {\n"
                           "          segments.remove(segments.size() - 1);\n"
                           "        } else {\n"
                           "          segments.add(segment);\n"
                           "        }",
                    "new": "        segments.add(segment);"}},
 "chain": {
   "facade_body": "return com.google.javascript.rhino.jstype.JSTypeRegistry.requiredModuleName(requiredFilename, currentFilename);",
   "lie": "Module names already computed for the current filename are kept in a table, and a required filename found there "
          "is answered from that table without being converted again.",
   "hops": [
     {"file": JTR, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "requiredModuleName",
      "imports": ["com.google.javascript.jscomp.SymbolTable"], "text": HOP1},
     {"file": ST, "class": "com.google.javascript.jscomp.SymbolTable$SymbolScope", "method": "scopedModuleName",
      "imports": [], "text": HOP2},
     {"file": JDI, "class": "com.google.javascript.rhino.JSDocInfo$Marker", "method": "relativeModuleName",
      "imports": ["com.google.javascript.jscomp.CompilerOptions"], "text": HOP3},
     {"file": CO, "class": "com.google.javascript.jscomp.CompilerOptions$TweakProcessing", "method": "moduleNameFrom",
      "imports": [], "text": HOP4},
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "moduleNameAt",
      "imports": ["com.google.common.base.Joiner"], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.ProcessCommonJSModules::toModuleName",
              "com.google.javascript.jscomp.deps.PathUtil::collapseDots",
              "com.google.javascript.jscomp.deps.PathUtil::makeAbsolute"],
 "ownership_reason": "Only the gold holds the directory of the requiring file together with the individual segments of the "
                     "path; the extension stripping, the relative/top-level decision, the './' placement and the pass-through "
                     "hand the two strings along. The trigger's target 'baz' lies outside the requiring file's directory 'foo/', "
                     "so no path without '..' leads to it from that file: an edit above the gold can only make the result right "
                     "by handing the gold another requiring file or by computing the resolution itself (a second implementation "
                     "outside the gold, e.g. java.net.URI resolution or PathUtil.collapseDots), and reading '$' in the gold's "
                     "output as a separator drops the 'module$' part of names that climb past the top directory. The convention "
                     "is pinned outside the gold: the facade's javadoc promises relative addressing with ./ and ../ based on the "
                     "current filename; PathUtil.collapseDots (reached through PathUtil.makeAbsolute from DepsGenerator) removes "
                     "the previous fragment for every '..' fragment ('a/b/../c' results in 'a/c'); toModuleName(String) and its "
                     "passing tests pin the conversion that the gold hands the resolved path to. The gold's javadoc promises the "
                     "module name of the file that the path leads to from the directory of the requiring file: '../baz' from "
                     "'foo/bar' leads to 'baz', whose module name is 'module$baz'.",
 "ownership_tests": ["com.google.javascript.jscomp.ProcessCommonJSModulesTest::testWithoutExports",
                     "com.google.javascript.jscomp.ProcessCommonJSModulesTest::testDash",
                     "com.google.javascript.jscomp.ProcessCommonJSModulesTest::testGuessModuleName",
                     "com.google.javascript.jscomp.CompilerTest::testCommonJSProvidesAndRequire",
                     "com.google.javascript.jscomp.CommandLineRunnerTest::testProcessCJS"],
 "compensating": {
   "chain": [
     {"file": JDI, "old": r'''path.replaceFirst("^\\./", ""), current);''',
      "new": r'''path.replaceFirst("^\\.\\.?/", ""), current);''',
      "why": "hop 3 also drops a leading '../'"},
     {"file": JDI, "old": r'''path.replaceFirst("^\\./", ""), current);''',
      "new": r'''path.replaceFirst("^\\./", ""), path.startsWith("../") ? current.replaceFirst("/?[^/]*$", "") : current);''',
      "why": "hop 3 steps the requiring file up one directory for a '../' path"},
     {"file": CO, "old": "return Compiler.CodeBuilder.moduleNameAt(path, current);",
      "new": "return Compiler.CodeBuilder.moduleNameAt(com.google.javascript.jscomp.deps.PathUtil.collapseDots(path), current);",
      "why": "hop 4 collapses the dots of the path alone"},
   ],
 },
 "host_notes": "Hosts for seed 5268 (mr_lib preview, target com/google/javascript/jscomp/ProcessCommonJSModules.java, n=12), "
               "draw order rhino.Node, regex.RegExpTree, rhino.JSDocInfo, parsing.JsDocInfoParser, jsonml.Reader, "
               "jstype.JSTypeRegistry, SymbolTable, CompilerOptions, Compiler, DefaultPassConfig, TypeCheck, NodeUtil. Closure "
               "uses 2-space indentation, so the recipe's anchor picker lands on members of NESTED classes, or appends the hop "
               "before the outer class's closing brace when it finds no anchor. A host is unusable when the anchor at the "
               "recipe's own seed for that position (5268+100+i) lies in a nested class that the calling hop cannot see, or "
               "where a static method does not compile. Drawn hosts 1-5 were kept at their positions where usable and the "
               "unusable ones were replaced, in position order, by the next drawn hosts 6, 7, 8, 9: hop 1 skipped rhino.Node "
               "(anchor in private static Node.StringNode), took JSTypeRegistry (no anchor at seed 5368: appended at the end "
               "of the public top-level class); hop 2 skipped regex.RegExpTree (anchor in package-private static "
               "RegExpTree.Repetition, not visible from rhino.jstype), took SymbolTable (public static final "
               "SymbolTable.SymbolScope, after isLexicalScope); hop 3 JSDocInfo as drawn (public static final "
               "JSDocInfo.Marker, after getType); hop 4 skipped parsing.JsDocInfoParser (anchor in private static "
               "JsDocInfoParser.ExtractionInfo), took CompilerOptions (public static enum CompilerOptions.TweakProcessing, "
               "after shouldStrip; a static method in a nested enum compiles); hop 5 skipped jsonml.Reader (anchor in the "
               "private non-static inner class Reader.ErrorReporter, where a static method does not compile; jsonml is also "
               "excluded from the build), took Compiler (public static Compiler.CodeBuilder, after toString). Nested-class "
               "hops carry binary names (Outer$Nested). The facade calls hop 1 by its fully-qualified name; JSTypeRegistry "
               "imports SymbolTable, JSDocInfo imports CompilerOptions, Compiler imports Joiner (SymbolTable already imports "
               "JSDocInfo; CompilerOptions and Compiler share the jscomp package with the next hop). The recipe indents "
               "inserted text by 4 spaces and the facade body by 8, which matches nested members but is off by 2 for the "
               "facade and the appended top-level hop in this 2-space codebase (cosmetic, recipe-wide for Closure). The "
               "facade's imports of java.net.URI and URISyntaxException are left in place and become unused.",
}
