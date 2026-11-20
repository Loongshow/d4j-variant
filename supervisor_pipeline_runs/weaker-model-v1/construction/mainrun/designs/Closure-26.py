"""Main run Closure-26 (C10 recipe on the fixed checkout of Defects4J Closure-26; the real bug modified ProcessCommonJSModules,
the target class).

Facade: ProcessCommonJSModules.toModuleName(String requiredFilename, String currentFilename), the two-argument overload of the
only allowed target (BATCH5_PREREGISTRATION.md row Closure-26; FACADE REUSE: the same method is the facade of Closure-9, recorded
as facade_reuse_of = ["Closure-9"]; this design was made without reading any Closure-9 file). The one-argument overload
toModuleName(String) was set aside as the facade: every test that runs ProcessCommonJSModules goes through it (visitScript,
module.exports, the entry module of CommandLineRunner, both CompilerTest CommonJS tests), so each of its four rewriting steps is
caught by two or more tests (the dash step by testDash AND testModuleName), and no omission there fails exactly one test (gate G5).
The two-argument overload is called by visitRequireCall and by the test ProcessCommonJSModulesTest::testModuleName; its relative
addressing ("./" and "../" names) is exercised by testModuleName only, since every other require in the suite is a top-level
name. The one-argument overload stays intact beside the facade and is used by the chain for top-level names.
Original computation of the facade: remove a trailing ".js" from both names; when the required name starts with "./" or "../",
resolve it against the current file name with java.net.URI (merge with the current file's directory, then drop "." segments and
take a ".." segment off the preceding segment unless that is itself ".." or absent); then toModuleName(String) of the result.

Chain (hosts for seed 8822, mr_lib preview, target com/google/javascript/jscomp/ProcessCommonJSModules.java; unusable hosts
replaced by the next drawn host, see host_notes):
  hop 1 jscomp.NodeUtil$MatchNodeType.moduleNameOfRequire        plumbing: removes the ".js" extension of both names
  hop 2 rhino.jstype.JSTypeRegistry.requiredModuleName          decision: a "./" or "../" name is relative, any other name is
                                                                 top-level (toModuleName(String) of the name itself)
  hop 3 jscomp.Compiler$CodeBuilder.relativeModuleName          placement: the directory of the requiring file
  hop 4 rhino.JSDocInfo$Marker.moduleNameInDirectory            plumbing: splits the relative name into its parts, leaving out
                                                                 the "." parts
  hop 5 jscomp.SymbolTable$SymbolScope.moduleNameOfParts        GOLD: the walk over the parts from the directory (a ".." part
                                                                 takes the last part off the path walked so far), then the
                                                                 module name of the path (prefix "module$", separators to "$",
                                                                 dashes to "_")
Correct configuration vs the original: identical for every top-level name (same extension removal, same prefix test, then the
same toModuleName(String)), and for every relative name made of '.', '..' and plain names joined by single separators whose last
part is a plain name not ending in ".js" after the extension is removed, required from a file name made of plain names joined by
single separators (a plain name: non-empty, no separator, none of ':', '?', '#', '%' or a character java.net.URI rejects). On that
domain the walk reproduces java.net.URI's merge and dot-segment removal exactly, including a ".." that climbs above the first
directory (kept, as URI keeps it). Outside it (repeated or trailing separators, queries, fragments, colons, illegal characters, a
name ending in "." or "..") the original went through java.net.URI and the chain does not; no production caller and no test
passes such names (require names are CommonJS identifiers, current names are normalised source names).

Fault (one-step omission in the gold, inside the iteration): the ".." step of the walk is dropped, so a ".." part is appended
like any other part. Trigger: the EXISTING test ProcessCommonJSModulesTest::testModuleName. Its first two assertions ("./baz.js"
and "./baz-bar.js" from "foo/bar.js") still pass; the third, assertEquals("module$baz", toModuleName("../baz.js", "foo/bar.js")) at
ProcessCommonJSModulesTest.java:107-108, fails with junit.framework.ComparisonFailure: expected:<module$[]baz> but
was:<module$[foo$..$]baz>. No other test passes a ".." name (every other require is top-level), so G5 holds.
The gold's javadoc states the idiomatic contract (the module name of the file that the path parts lead to from the directory) and
is silent on "..": the parts [.., baz] lead from "foo" to "baz", whose module name is module$baz, not module$foo$..$baz.

External pins (convention outside the gold): the facade's own javadoc ("support for relative addressing with ./ and ../ based on
currentFilename"); hop 2's dispatch of "../" names to the directory path; PathUtil.collapseDots (production code: "Removes all
../ and ./ entries", "a/b/../c" results in "a/c"), used by PathUtil.makeAbsolute and PathUtil.makeRelative (DepsGenerator). No
test other than the trigger exercises a ".." name; the ownership tests pin the neighbouring conventions of the same path on the
variant (top-level names are not taken from the requiring file's directory, dashes become underscores, the extension is removed)
and the intact one-argument overload pins the naming that the gold's last line repeats.

Single owner: a ".." part means "take off the last part of the path walked so far", so it can only be applied inside the walk:
after a plain part it takes off that part ("../a/../b"), after the starting directory it takes off a directory, and above the
first directory it is kept. Hops 1-3 hold the two names, hop 4 the starting directory and the parts, and none sees the path
walked so far; once the gold has built the module name, the separators are "$" and no caller can tell a part from a directory.
Declared alternatives (G9), none absorbs the fault: hop 4 also leaves out the ".." parts (gives module$foo$baz); hop 3 starts a
name that begins with ".." from the empty path (gives module$..$baz); hop 2 turns a leading "../" into "./" (module$foo$baz).
Recorded edits above the gold that pass the trigger and the full suite (not repairs of the chain; B-1, B-2 and B-3 were checked on
the variant in scratch copies: trigger passes, defects4j test reports 0 failing tests each):
 B-0 bypass: the facade restores its original java.net.URI body (and the two java.net imports), discarding the chain.
 B-1 bypass: hop 2 returns ProcessCommonJSModules.toModuleName(com.google.javascript.jscomp.deps.PathUtil.makeAbsolute(name,
     from.substring(0, Math.max(from.lastIndexOf(File.separator), 0)))) for a relative name, making hops 3-5 dead (and it differs
     from the URI semantics: PathUtil drops a ".." that climbs above the first directory, and a name required from a file with no
     directory gets a leading "$").
 B-2 bypass: hop 4 passes the gold an empty directory and the parts of
     com.google.javascript.jscomp.deps.PathUtil.collapseDots(dir + File.separator + name), i.e. another implementation of the
     gold's walk: hop 4 then no longer splits the relative name as documented but a merged and collapsed path, the gold's
     walk becomes a plain join, and a '..' that climbs above the first directory is dropped (URI keeps it).
 B-3 test-fitted: a hop rewrites the module name by a regular expression that replaces everything from the prefix
     'module$' up to the last '$..$' by 'module$': every '..' in the suite climbs exactly to the first directory, but
     ('../a/b', 'x/y/z') then gives module$a$b instead of module$x$a$b.

Lie: the facade's javadoc claims each pair of names is resolved only once and later calls with the same pair are answered from a
table of the module names already computed; there is no table. It names neither ".." nor any omitted step nor any hop.

Pre-edit (behaviour-preserving, needed by the chain so that the facade file keeps no import of the replaced body): the rewrite leaves the imports java.net.URI and
java.net.URISyntaxException of ProcessCommonJSModules unused; the pre-edit removes them (the recipe's edit derivation cannot
express a pure line deletion, so one empty line remains between the java.io and java.util imports).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: dir is the builder's initial content, parts is iterated; both reach the returned name.
  T2 absent: path is returned (via toString), part is read in every branch; the ".." test decides between taking a part off and
     appending (different effects), the separator test decides whether a separator is appended; no literal-initialised local, no
     loop-moved variable left unassigned.
  T3 absent: the only special part is ".."; "." parts never reach the gold (hop 4 leaves them out) and the gold's text names no
     set of special parts, so no closed set has a treated and an untreated member; the omission removes the only special case.
  T4 absent: the javadoc names no rule, limit, value class or case; "without a trailing separator" is a caller precondition.
 Variant gold (javadoc, signature, the builder from dir, the loop that appends a separator when the path is not empty and then the
 part, the return of "module$" + the path with separators replaced by "$" and dashes by "_"):
  T1 absent: dir is the builder's initial content and parts is iterated; each changes the returned name.
  T2 absent: path is returned; part is appended; the separator decision has two different effects; no literal-initialised local,
     no frozen cursor, counter, flag or best-so-far (the builder is appended to in every iteration).
  T3 absent: no special part is handled at all ("no member handled"); the two replacements of the return line (separator, dash)
     belong to no set the gold's text names; no pair halves or range ends.
  T4 absent: "the module name of the file that a sequence of path parts leads to from a directory" and "@return the module name of
     the file that the parts lead to" are general descriptions that the loop and the return line address; "@param dir ... without
     a trailing separator" is a caller precondition; identifiers (path, part, dir, parts, moduleNameOfParts) name nothing the body
     does not meet."""

PCJ = "src/com/google/javascript/jscomp/ProcessCommonJSModules.java"
NU = "src/com/google/javascript/jscomp/NodeUtil.java"
JTR = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"
JDI = "src/com/google/javascript/rhino/JSDocInfo.java"
ST = "src/com/google/javascript/jscomp/SymbolTable.java"

GOLD_TEXT = r'''/**
 * Returns the module name of the file that a sequence of path parts
 * leads to from a directory.
 *
 * @param dir the path of the directory, without a trailing separator
 * @param parts the path parts, in order
 * @return the module name of the file that the parts lead to
 */
public static String moduleNameOfParts(String dir, List<String> parts) {
  StringBuilder path = new StringBuilder(dir);
  for (String part : parts) {
    if (part.equals("..") && path.length() > 0
        && !path.substring(path.lastIndexOf(File.separator) + 1).equals("..")) {
      path.setLength(Math.max(path.lastIndexOf(File.separator), 0));
      continue;
    }
    if (path.length() > 0) {
      path.append(File.separator);
    }
    path.append(part);
  }
  return "module$" + path.toString().replace(File.separator, "$").replace("-", "_");
}'''

HOP1 = r'''/**
 * Returns the module name of a file that is required from another file.
 * The ".js" extension is removed from both file names first.
 *
 * @param requiredFilename the name of the required file
 * @param currentFilename the name of the file that requires it
 * @return the module name of the required file
 */
public static String moduleNameOfRequire(String requiredFilename,
    String currentFilename) {
  return JSTypeRegistry.requiredModuleName(
      requiredFilename.replaceAll("\\.js$", ""),
      currentFilename.replaceAll("\\.js$", ""));
}'''

HOP2 = r'''/**
 * Returns the module name of a file that is required from another file,
 * both names given without extension. A name that starts with "./" or
 * "../" is relative and is taken from the directory of the requiring
 * file; any other name is a top-level name, whose module name does not
 * depend on the requiring file.
 *
 * @param name the name of the required file
 * @param from the name of the requiring file
 * @return the module name of the required file
 */
public static String requiredModuleName(String name, String from) {
  if (name.startsWith("." + File.separator)
      || name.startsWith(".." + File.separator)) {
    return Compiler.CodeBuilder.relativeModuleName(name, from);
  }
  return ProcessCommonJSModules.toModuleName(name);
}'''

HOP3 = r'''/**
 * Returns the module name of the file that a relative name leads to from
 * a requiring file. The directory of the requiring file is the part of
 * its name before the last separator, or the empty path if its name has
 * no separator.
 *
 * @param name the relative name, without extension
 * @param from the name of the requiring file, without extension
 * @return the module name of the file that the name leads to
 */
public static String relativeModuleName(String name, String from) {
  String dir = from.substring(0, Math.max(from.lastIndexOf(File.separator), 0));
  return JSDocInfo.Marker.moduleNameInDirectory(dir, name);
}'''

HOP4 = r'''/**
 * Returns the module name of the file that a relative name leads to from
 * a directory. The name is split into its parts at the separators, and
 * its "." parts, which stand for the directory itself, are left out.
 *
 * @param dir the path of the directory, without a trailing separator
 * @param name the relative name, without extension
 * @return the module name of the file that the name leads to
 */
public static String moduleNameInDirectory(String dir, String name) {
  List<String> parts = Lists.newArrayList(
      name.split(Pattern.quote(File.separator)));
  parts.removeAll(Collections.singleton("."));
  return SymbolTable.SymbolScope.moduleNameOfParts(dir, parts);
}'''

DESIGN = {
 "instance": "Closure-26", "project": "Closure", "bug_id": 26, "seed": 8822,
 "src_root": "src", "test_root": "test",
 "facade": {"file": PCJ, "class": "com.google.javascript.jscomp.ProcessCommonJSModules", "method": "toModuleName", "near_line": 96},
 "facade_reuse_of": ["Closure-9"],
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/ProcessCommonJSModulesTest.java",
             "test_class": "com.google.javascript.jscomp.ProcessCommonJSModulesTest", "test_method": "testModuleName"},
 "expected_signature": "expected:<module$[]baz> but was:<module$[foo$..$]baz>",
 "gold": {"method": "moduleNameOfParts", "text": GOLD_TEXT,
          "fault": {"old": "      for (String part : parts) {\n"
                           "        if (part.equals(\"..\") && path.length() > 0\n"
                           "            && !path.substring(path.lastIndexOf(File.separator) + 1).equals(\"..\")) {\n"
                           "          path.setLength(Math.max(path.lastIndexOf(File.separator), 0));\n"
                           "          continue;\n"
                           "        }\n"
                           "        if (path.length() > 0) {",
                    "new": "      for (String part : parts) {\n"
                           "        if (path.length() > 0) {"}},
 "pre_edits": {
   "chain": [{"file": PCJ,
              "old": "import java.io.File;\nimport java.net.URI;\nimport java.net.URISyntaxException;\nimport java.util.Set;",
              "new": "import java.io.File;\n\nimport java.util.Set;"}],
 },
 "chain": {
   "facade_body": "return NodeUtil.MatchNodeType.moduleNameOfRequire(requiredFilename, currentFilename);",
   "lie": "Each pair of names is resolved only once; a later call with the same pair is answered from a table of the "
          "module names already computed.",
   "hops": [
     {"file": NU, "class": "com.google.javascript.jscomp.NodeUtil$MatchNodeType", "method": "moduleNameOfRequire",
      "imports": ["com.google.javascript.rhino.jstype.JSTypeRegistry"], "text": HOP1},
     {"file": JTR, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "requiredModuleName",
      "imports": ["com.google.javascript.jscomp.Compiler", "com.google.javascript.jscomp.ProcessCommonJSModules", "java.io.File"],
      "text": HOP2},
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "relativeModuleName",
      "imports": ["java.io.File"], "text": HOP3},
     {"file": JDI, "class": "com.google.javascript.rhino.JSDocInfo$Marker", "method": "moduleNameInDirectory",
      "imports": ["com.google.javascript.jscomp.SymbolTable", "java.io.File", "java.util.regex.Pattern"], "text": HOP4},
     {"file": ST, "class": "com.google.javascript.jscomp.SymbolTable$SymbolScope", "method": "moduleNameOfParts",
      "imports": ["java.io.File"], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.deps.PathUtil::collapseDots",
              "com.google.javascript.jscomp.deps.PathUtil::makeAbsolute",
              "com.google.javascript.jscomp.deps.PathUtil::makeRelative"],
 "ownership_reason": "Only the gold's walk holds the path walked so far, and a '..' part means taking the last part off that path: "
                     "after a plain part it takes off that part, after the starting directory it takes off a directory, above "
                     "the first directory it is kept. Hops 1-3 hold the two names and hop 4 the starting directory and the "
                     "parts; none sees the walked path, and once the gold has built the module name the separators are '$' and "
                     "no caller can tell a part from a directory. A one-line repair above the gold must re-implement the walk "
                     "(for example PathUtil.makeAbsolute at hop 2 or PathUtil.collapseDots at hop 4, which also drop a '..' "
                     "that climbs above the first directory, while the original java.net.URI resolution keeps it) or fit the "
                     "trigger's names. The convention is pinned outside the gold: the facade's javadoc promises 'relative "
                     "addressing with ./ and ../ based on currentFilename'; hop 2 dispatches '../' names to the directory path; "
                     "PathUtil.collapseDots ('a/b/../c' results in 'a/c'), used by PathUtil.makeAbsolute and "
                     "PathUtil.makeRelative (DepsGenerator), takes a '..' off the preceding directory. The gold's javadoc "
                     "promises the module name of the file that the parts lead to from the directory: [.., baz] leads from "
                     "'foo' to 'baz', whose module name is module$baz. The ownership tests pass on the variant and pin the "
                     "neighbouring conventions of the same path: top-level names do not depend on the requiring file "
                     "(testWithoutExports: 'mod/name' from 'test/sub' is module$mod$name), dashes become underscores and the "
                     "extension is removed (testDash, testGuessModuleName, CompilerTest.testCommonJSProvidesAndRequire).",
 "ownership_tests": ["com.google.javascript.jscomp.ProcessCommonJSModulesTest::testWithoutExports",
                     "com.google.javascript.jscomp.ProcessCommonJSModulesTest::testDash",
                     "com.google.javascript.jscomp.ProcessCommonJSModulesTest::testGuessModuleName",
                     "com.google.javascript.jscomp.CompilerTest::testCommonJSProvidesAndRequire"],
 "compensating": {
   "chain": [
     {"file": JDI, "old": "parts.removeAll(Collections.singleton(\".\"));",
      "new": "parts.removeAll(java.util.Arrays.asList(\".\", \"..\"));",
      "why": "hop 4 also leaves out the '..' parts"},
     {"file": CMP, "old": "String dir = from.substring(0, Math.max(from.lastIndexOf(File.separator), 0));",
      "new": "String dir = name.startsWith(\"..\") ? \"\" : from.substring(0, Math.max(from.lastIndexOf(File.separator), 0));",
      "why": "hop 3 starts a name that begins with '..' from the empty path"},
     {"file": JTR, "old": "return Compiler.CodeBuilder.relativeModuleName(name, from);",
      "new": "return Compiler.CodeBuilder.relativeModuleName(name.startsWith(\"..\") ? name.substring(1) : name, from);",
      "why": "hop 2 turns a leading '../' into './'"},
   ],
 },
 "host_notes": "Hosts for seed 8822 (mr_lib preview, target com/google/javascript/jscomp/ProcessCommonJSModules.java, n=12), draw "
               "order: rhino.Node, rhino.jstype.JSTypeRegistry, jscomp.jsonml.Reader, rhino.JSDocInfo, "
               "jscomp.parsing.JsDocInfoParser, jscomp.regex.RegExpTree, jscomp.NodeUtil, jscomp.Compiler, "
               "jscomp.DefaultPassConfig, jscomp.SymbolTable, jscomp.TypeCheck, jscomp.CompilerOptions. Closure uses 2-space "
               "indentation, so the recipe's anchor picker (only 4-space-indented methods; BATCH5_PREREGISTRATION 'Pre-existing "
               "deviation') lands on members of NESTED classes or, with fewer than three such methods, appends the hop before "
               "the outer class's closing brace. A host is unusable when the hop's enclosing class cannot be reached from the "
               "calling hop or a static method there does not compile. Preview hosts 1-5 at their positions (anchor seed "
               "8822+100+i): hop 1 rhino.Node is unusable (anchor getObjectValue in private static Node.ObjectPropListItem, "
               "not reachable from ProcessCommonJSModules); hop 2 JSTypeRegistry is usable (appended at the end of the public "
               "outer class); hop 3 jsonml.Reader is unusable (jsonml is excluded from the build's compile target, "
               "build.xml '**/jsonml/**', and the anchor lies in private enum Reader.Operator); hop 4 JSDocInfo is usable "
               "(anchor getAnnotation in public static final JSDocInfo.Marker); hop 5 parsing.JsDocInfoParser is unusable "
               "(private static JsDocInfoParser.ExtractionInfo). The unusable positions were filled, in order, with the next "
               "drawn hosts: hop 1 skipped host 6 regex.RegExpTree (package-private RegExpTree.LookaheadAssertion, not visible "
               "from jscomp) and took host 7 NodeUtil (anchor apply in package-private static NodeUtil.MatchNodeType, same "
               "package as the facade); hop 3 took host 8 Compiler (anchor toString in public static Compiler.CodeBuilder); "
               "hop 5 skipped host 9 DefaultPassConfig (anchor in the non-static inner class GlobalTypeResolver, where a static "
               "method does not compile) and took host 10 SymbolTable (anchor getTypeOfThis in public static final "
               "SymbolTable.SymbolScope). RegExpTree and DefaultPassConfig are unusable at every position, so the assignment "
               "does not depend on the order of replacement. Nested-class hops carry binary names (Outer$Nested). The facade "
               "calls hop 1 by NodeUtil.MatchNodeType (same package); each hop imports the next host's outer class. The "
               "recipe indents inserted text by 4 spaces and the facade body by 8, which matches nested members but is off by "
               "2 for the facade and for the hop appended to JSTypeRegistry (its first javadoc line also gets 8 spaces); this "
               "is cosmetic and recipe-wide for Closure.",
}
