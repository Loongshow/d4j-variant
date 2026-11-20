"""Main run Closure-155__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Closure-155; the real bug modified InlineVariables, ReferenceCollectingCallback and Scope, the facade's class). No static pair
(B8 note section 1: pool v2 found no strictly tested public static method in the modified classes).

Facade: Scope.getVar(String) (instance method; the only allowed candidate of the task record, BATCH9_PREREGISTRATION.md rank 315;
facade_planned_by null, no facade reuse). Original computation: the variable declared for the name in this scope's own table (the private
field vars), and otherwise the result of the same lookup on the parent scope (the private field parent), recursively; null at the global
scope. Every lookup therefore returns the declaration in the innermost scope, from this one outward, that declares the name.

facade_variant: V1 (state as parameters). state_passed: the private fields vars (Map<String, Var>, this scope's own declarations) and
parent (Scope, the enclosing scope, null for the global scope) and the name, handed to hop 1; no field is written, no write-back. The
facade body is one call to hop 1 (the original has no guard). The chain reads other scopes only through Scope's public methods
(getOwnSlot, getParent, isLocal), so no private member of Scope is copied into a hop (V4 does not apply) and no visibility is widened; no
type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. Scope.Var is a public static nested
class, so the hops in other packages name it directly.

Redistribution of the computation: hop 1 looks the name up in the scope's own table and, if absent and the scope has an enclosing scope,
hands the enclosing scope on; hop 2 takes the result of the local search and, if it is null, looks the name up in the global scope (the
root of the parent chain); hops 3 and 4 pass the start scope and the name along; the gold walks the local scopes from the start scope
outward (getParent, while isLocal) and returns the declaration of the first local scope that declares the name (the per-scope core).
The correct configuration returns exactly what the original returns for every scope and name: own table first, then the enclosing local
scopes innermost first, then the global scope (the only scope whose parent is null; isLocal() is parent != null).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Closure-155-probe of the fixture, the first statement of
getVar(String) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
com.google.javascript.jscomp.ShadowVariablesTest::testShadowWithShadowAlready`: 1 failing test, whose trace has
java.lang.IllegalStateException: PROBE-REACHED (the existing trigger reaches the facade). Before the design, the full suite was also run on scratch copies with three candidate
lookup rules in getVar (baseline: 0 failing tests): returning the outermost declaring scope over the whole chain: 36 failing tests; own table first, then the
outermost declaring ancestor: 2 (ShadowVariablesTest::testShadowWithShadowAlready, ScopedAliasesTest::testShadowedVar); own table first,
then the outermost declaring LOCAL ancestor, then the global scope if no local scope declares the name (the variant below): exactly 1,
ShadowVariablesTest::testShadowWithShadowAlready.

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview Closure-155 com/google/javascript/jscomp/Scope.java 10` (the target relative
to the source root), seed 5400; each hop takes the earliest drawn, not yet used host that is usable at that hop's own anchor, see
host_notes):
  hop 1 rhino.TokenStream           1714 lines  lookupName          own table of the scope; hands the enclosing scope on
  hop 2 rhino.jstype.JSTypeRegistry 1589 lines  lookupScopedName    local search, then the global scope if nothing local declares it
  hop 3 rhino.Parser                2407 lines  lookupEnclosingName pass-through
  hop 4 jscomp.TypeCheck            1806 lines  searchLocalScopes   pass-through
  hop 5 jscomp.NodeUtil             2977 lines  declarationIn       GOLD (the recipe anchor places it in NodeUtil's static nested class
                                                                    BooleanResultPredicate: com.google.javascript.jscomp.NodeUtil$BooleanResultPredicate)
host_mode 1500; host sizes 1714, 1589, 2407, 1806, 2977; the smallest host is JSTypeRegistry (1589 lines).

Fault (one-line omission in the gold's iteration): the `break;` after recording a declaring scope is dropped, so the walk goes on to the
outermost local scope and the last declaring scope wins. A name declared in two or more enclosing local scopes (and not in the scope
itself) then resolves to the outer declaration instead of the inner one. Own-table hits are handled in hop 1 and the global scope only
when no local scope declares the name (hop 2), so only that local-over-local shadowing changes. Trigger: the EXISTING test
ShadowVariablesTest::testShadowWithShadowAlready; its second test() input references p from the fourth-level function, where p is declared
by the third-level function and by the outermost function; the renaming pass then sees the reference bound to the outer p and the output
differs (expected "...function(){b};a};var a};var a};var a}", result "var d=function(a){...function(){a};b};var c};var c};var b}"). It
is the only test in the full suite that newly fails (measured on the variant rule above; gate G5 checks it).

The gold's javadoc states the idiomatic contract (the variable a name refers to in the local scopes, searched from the given scope
outward) and is silent on where the search stops. The variable a name refers to is its declaration in the innermost enclosing scope
(lexical scoping), which the variant violates on the trigger input. The convention is pinned outside the gold: StaticScope.getSlot's
contract ("continues searching through parent scopes if a slot with this name is not found in the current scope"), its sibling
implementation TightenTypes.ConcreteScope.getSlot (own slot first, then parent.getSlot, first found wins) and Scope.isDeclared (own table,
then the parent); passing tests that pin innermost-wins through the chain: ShadowVariablesTest::testShadowSimple2,
VariableReferenceCheckTest::testCorrectShadowing, TypeCheckTest::testScoping1 (own table over an enclosing declaration) and
ScopedAliasesTest::testShadowedVar (a local declaration over a global one, through hop 2).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, the loop with `break;`):
  T1 absent: start seeds the loop cursor; name is the key of every getOwnSlot lookup.
  T2 absent: scope is the loop cursor and advances (scope = scope.getParent()); candidate is read by the test and the assignment; found is
     assigned in the loop and returned; the if has an effect.
  T3 absent: the gold handles one kind of scope, the local scopes it names, all of them alike; no pair, range or enumeration.
  T4 absent: 'in the local scopes, from the given scope outward' is met by the loop (isLocal, getParent); '@param start ... or null' is met
     (a null start ends the loop at once); '@return ... or null if none of the local scopes declares the name' is met.
 Variant gold (javadoc, signature, the loop without `break;`):
  T1 absent: start and name each change the result.
  T2 absent: scope advances every iteration; found is assigned inside the loop whenever a local scope declares the name (not frozen, not
     dead: it is returned); candidate reaches the test and the assignment; the if decides whether found changes.
  T3 absent: every local scope gets the same treatment; the gold names no set it handles in part (the global scope is outside 'the local
     scopes' it names); no pair halves or range ends.
  T4 absent: 'the variable that a name refers to in the local scopes' is a general description that the body addresses; 'from the given
     scope outward' is met (the walk goes outward); the @param and @return phrases are met (null only if no local scope declares the
     name); no inline comment; identifiers (start, scope, candidate, found) name nothing the body does not meet.

Single owner: only the gold walks the enclosing local scopes and chooses among their declarations; hop 1 consults only the scope's own
table, hop 2 consults the global scope only when the gold returns null, hops 3 and 4 pass the start scope and the name along, and no hop
sees which local scopes declare the name. Once the gold returns the outer declaration, a caller cannot tell it from the inner one without
redoing the gold's walk. Declared alternatives (G9): hop 2 reads the given scope instead of the root for the global step; hop 2 climbs
only one level for the global step; hop 4 starts the local search at the enclosing scope's parent. None makes the trigger pass.
Recorded bypasses (each discards the gold):
 B-1 hop 1 (or hop 2, 3 or 4) returns enclosing.getVar(name) / scope.getVar(name) instead of calling the next hop: the facade's recursion
     on the enclosing scope consults that scope's own table first at every level, so the gold is never called.
 B-2 a hop re-implements the walk with its own first-found loop over getOwnSlot (a second implementation of the gold).

Lie: the facade's javadoc claims each name is first looked up in a cache of earlier lookups that the scope keeps and refreshes when a
variable is declared; no step of the chain keeps or reads any cache. It names neither the search order nor shadowing nor any hop."""

SCOPE = "src/com/google/javascript/jscomp/Scope.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
REG = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
PARSER = "src/com/google/javascript/rhino/Parser.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"
NU = "src/com/google/javascript/jscomp/NodeUtil.java"

GOLD_TEXT = '''/**
 * Returns the variable that a name refers to in the local scopes, from the
 * given scope outward.
 *
 * @param start the scope to start from, or null
 * @param name the name to look up
 * @return the variable, or null if none of the local scopes declares the
 *     name
 */
public static Scope.Var declarationIn(Scope start, String name) {
  Scope.Var found = null;
  for (Scope scope = start; scope != null && scope.isLocal();
       scope = scope.getParent()) {
    Scope.Var candidate = (Scope.Var) scope.getOwnSlot(name);
    if (candidate != null) {
      found = candidate;
      break;
    }
  }
  return found;
}'''

HOP1 = '''/**
 * Looks up a name among the declarations of a scope and, if the scope
 * does not declare it, in the scopes that enclose it.
 *
 * @param declared the declarations of the scope, by name
 * @param enclosing the scope that encloses it, or null
 * @param name the name to look up
 * @return the variable, or null if no scope declares the name
 */
public static Scope.Var lookupName(Map<String, Scope.Var> declared,
                                   Scope enclosing, String name)
{
    Scope.Var own = declared.get(name);
    if (own != null || enclosing == null) {
        return own;
    }
    return JSTypeRegistry.lookupScopedName(enclosing, name);
}'''

HOP2 = '''/**
 * Looks up a name in a scope and the scopes that enclose it: first in the
 * local scopes, from the given scope outward, and then in the global scope.
 *
 * @param scope the scope to start from
 * @param name the name to look up
 * @return the variable, or null if no scope declares the name
 */
public static Scope.Var lookupScopedName(Scope scope, String name) {
  Scope.Var local = Parser.lookupEnclosingName(scope, name);
  if (local != null) {
    return local;
  }
  Scope global = scope;
  while (global.getParent() != null) {
    global = global.getParent();
  }
  return (Scope.Var) global.getOwnSlot(name);
}'''

HOP3 = '''/**
 * Looks up a name in the local scopes, from the given scope outward.
 *
 * @param scope the scope to start from
 * @param name the name to look up
 * @return the variable, or null if no local scope declares the name
 */
public static Scope.Var lookupEnclosingName(Scope scope, String name)
{
    return TypeCheck.searchLocalScopes(scope, name);
}'''

HOP4 = '''/**
 * Searches the local scopes for a name, from the given scope outward.
 *
 * @param scope the scope to start from
 * @param name the name to look up
 * @return the variable, or null if no local scope declares the name
 */
public static Scope.Var searchLocalScopes(Scope scope, String name) {
  return NodeUtil.BooleanResultPredicate.declarationIn(scope, name);
}'''

DESIGN = {
 "instance": "Closure-155", "project": "Closure", "bug_id": 155, "seed": 5400,
 "src_root": "src", "test_root": "test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private fields vars (this scope's own declarations) and parent (the enclosing scope), and the name, passed to "
                 "hop 1; no write-back",
 "host_mode": "1500", "host_lines": [1714, 1589, 2407, 1806, 2977],
 "reachability_probe": "getVar(String) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Closure-155-probe: the trigger ShadowVariablesTest::testShadowWithShadowAlready "
                       "fails with java.lang.IllegalStateException: PROBE-REACHED",
 "facade": {"file": SCOPE, "class": "com.google.javascript.jscomp.Scope", "method": "getVar", "near_line": 471},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/ShadowVariablesTest.java",
             "test_class": "com.google.javascript.jscomp.ShadowVariablesTest", "test_method": "testShadowWithShadowAlready"},
 "expected_signature": "Result: var d=function(a)",
 "gold": {"method": "declarationIn", "text": GOLD_TEXT,
          "fault": {"old": "          found = candidate;\n          break;\n",
                    "new": "          found = candidate;\n"}},
 "chain": {
   "facade_body": "return com.google.javascript.rhino.TokenStream.lookupName(vars, parent, name);",
   "lie": "Each name is first looked up in a cache of earlier lookups that the scope keeps and refreshes whenever a variable is "
          "declared.",
   "hops": [
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "lookupName",
      "imports": ["com.google.javascript.jscomp.Scope", "com.google.javascript.rhino.jstype.JSTypeRegistry", "java.util.Map"],
      "text": HOP1},
     {"file": REG, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "lookupScopedName",
      "imports": ["com.google.javascript.jscomp.Scope", "com.google.javascript.rhino.Parser"], "text": HOP2},
     {"file": PARSER, "class": "com.google.javascript.rhino.Parser", "method": "lookupEnclosingName",
      "imports": ["com.google.javascript.jscomp.Scope", "com.google.javascript.jscomp.TypeCheck"], "text": HOP3},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "searchLocalScopes",
      "imports": [], "text": HOP4},
     {"file": NU, "class": "com.google.javascript.jscomp.NodeUtil$BooleanResultPredicate", "method": "declarationIn",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.rhino.jstype.StaticScope::getSlot",
              "com.google.javascript.jscomp.TightenTypes.ConcreteScope::getSlot",
              "com.google.javascript.jscomp.Scope::isDeclared"],
 "ownership_reason": "Only the gold walks the enclosing local scopes and chooses among their declarations. Hop 1 consults only the "
                     "scope's own table (an own declaration is returned before any hop runs), hop 2 consults the global scope only "
                     "when the gold returns null, and hops 3 and 4 pass the start scope and the name along; no hop sees which local "
                     "scopes declare the name, so once the gold returns the outer of two local declarations no caller can recover "
                     "the inner one without redoing the gold's walk. The gold's javadoc promises the variable that the name refers "
                     "to in the local scopes searched from the given scope outward, i.e. the innermost declaration (lexical scoping); "
                     "the variant returns the outermost. The convention is pinned outside the gold: the StaticScope.getSlot contract "
                     "('continues searching through parent scopes if a slot with this name is not found in the current scope'), the "
                     "sibling implementation TightenTypes.ConcreteScope.getSlot (own slot, then parent.getSlot; first found wins) and "
                     "Scope.isDeclared (own table, then the parent); ShadowVariablesTest::testShadowSimple2, "
                     "VariableReferenceCheckTest::testCorrectShadowing and TypeCheckTest::testScoping1 (an own declaration shadows an "
                     "enclosing one) and ScopedAliasesTest::testShadowedVar (a local declaration shadows a global one, through hop "
                     "2) pass on the variant.",
 "ownership_tests": ["com.google.javascript.jscomp.ShadowVariablesTest::testShadowSimple2",
                     "com.google.javascript.jscomp.VariableReferenceCheckTest::testCorrectShadowing",
                     "com.google.javascript.jscomp.TypeCheckTest::testScoping1",
                     "com.google.javascript.jscomp.ScopedAliasesTest::testShadowedVar"],
 "compensating": {
   "chain": [
     {"file": REG, "old": "  return (Scope.Var) global.getOwnSlot(name);",
      "new": "  return (Scope.Var) scope.getOwnSlot(name);",
      "why": "hop 2 reads the given scope instead of the root of the chain for the global step"},
     {"file": REG, "old": "  while (global.getParent() != null) {",
      "new": "  if (global.getParent() != null) {",
      "why": "hop 2 climbs only one level for the global step"},
     {"file": TC, "old": "  return NodeUtil.BooleanResultPredicate.declarationIn(scope, name);",
      "new": "  return NodeUtil.BooleanResultPredicate.declarationIn(scope.getParent(), name);",
      "why": "hop 4 starts the local search at the enclosing scope's parent"},
   ],
 },
 "host_notes": "host_mode 1500: the recipe's seeded draw, mr_lib.py preview Closure-155 com/google/javascript/jscomp/Scope.java 10 "
               "(the target relative to the source root, as the preview command takes it; seed 5400), draw order TokenStream, "
               "JSTypeRegistry, Parser, jsonml.Reader, Node, JsDocInfoParser, DefaultPassConfig, NodeUtil, TypeCheck, Compiler (the "
               "ten usable public classes of >= 1500 lines). The recipe anchors each hop with seed 5400 + 100 + hop index "
               "(stageB_lib.pick_anchor), so a host's anchor depends on the hop it would carry; each hop therefore takes the "
               "EARLIEST drawn host not yet used whose anchor at that hop's seed can carry a public static method callable from the "
               "previous hop. The anchor filter keeps methods indented four spaces as outer-class members, so in the two-space jscomp "
               "files it picks methods of nested classes. Hop 1 (seed 5500): TokenStream, after isJSIdentifier (top level). Hop 2 "
               "(5501): JSTypeRegistry, end of class (top level). Hop 3 (5502): Parser, after its constructor (top level). Hop 4 "
               "(5503, called from rhino.Parser): jsonml.Reader anchors in the private inner class ErrorReporter, Node in the "
               "private static class StringNode, JsDocInfoParser in the private inner class ErrorReporterParser, DefaultPassConfig "
               "in the private inner class GlobalTypeResolver (private classes are not visible to another top-level class), NodeUtil "
               "in the package-private nested class MayBeStringResultPredicate (not visible from package rhino); TypeCheck (end of "
               "class, top level) is the first usable host. Hop 5 (5504, called from jscomp.TypeCheck): Reader (ErrorReporter, "
               "private), Node (StringNode, private), JsDocInfoParser (ErrorReporterParser, private) and DefaultPassConfig "
               "(GlobalTypeResolver, private) are not visible; NodeUtil anchors after apply inside the package-private static nested "
               "class BooleanResultPredicate, which TypeCheck in the same package can call, so NodeUtil is hop 5 and the gold is "
               "com.google.javascript.jscomp.NodeUtil$BooleanResultPredicate::declarationIn (the binary name, as the harness's "
               "method catalog lists nested classes). The same five hosts result from the draw with the target given as "
               "src/com/google/javascript/jscomp/Scope.java (draw order TokenStream, DefaultPassConfig, JSTypeRegistry, Parser, "
               "Node, TypeCheck, JsDocInfoParser, NodeUtil, Reader, Compiler): the hosts that order puts earlier (DefaultPassConfig "
               "at hops 2 to 5, Node at hops 4 and 5, JsDocInfoParser at hop 5) anchor in private classes there. The facade calls hop 1 by its fully-qualified name; the rhino hosts import "
               "com.google.javascript.jscomp.Scope (one javac run compiles both packages); TypeCheck and NodeUtil are in the "
               "facade's package.",
}
