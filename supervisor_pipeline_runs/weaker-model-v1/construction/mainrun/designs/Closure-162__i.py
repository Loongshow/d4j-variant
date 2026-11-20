"""Main run Closure-162__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Closure-162, a bug with no usable static facade; the real bug modified Scope and ScopedAliases, and the facade is in Scope).
No static pair (B8 note section 1).

Facade: Scope.getVar(String) (instance method; the only allowed candidate of the task record, BATCH9_PREREGISTRATION.md rank 316).
Its facade_planned_by is Closure-155__i (facade_reuse_of recorded in the task record); no other candidate exists, so it is used
(B8 note section 3). Original computation: the variable declared under the name in this scope's own declarations (the private
field vars) if there is one, otherwise the result of the same lookup in the parent scope (the private field parent), otherwise
null at the global scope. In effect: the declaration in the nearest scope of the chain this scope -> parent -> ... -> global that
declares the name.

facade_variant: V1 (state as parameters). state_passed: the name, the private field vars (Map<String, Var>, this scope's own
declarations) and the private field parent (Scope), handed to hop 1; no field is written, no write-back. The facade body is one
call to hop 1 (the original has no argument guard). No visibility is widened, no type is added, no signature, modifier, override or
throws clause changes, no reflection, no test edit. getVar calls no private method, so V4 does not apply; Scope, Scope.Var and the
methods the hops use (getParent, isLocal, getOwnSlot) are public, so V3/V5 are not needed.

Redistribution of the computation:
  hop 1 JSTypeRegistry.resolveVarName        the scope's own declarations first; otherwise the enclosing scopes (null if none)
  hop 2 Parser.findVarInScopes               aggregation: the local scopes (through hops 3-5), then the global scope (the root of
                                             the chain) when no local scope declares the name
  hop 3 Compiler.CodeBuilder.scopedVarDeclaration  pass-through
  hop 4 TokenStream.declarationOfName        pass-through
  hop 5 TypeCheck.localDeclarationOf         GOLD: the per-scope step: walks the local scopes from the given scope outwards, reading
                                             each scope's own declaration of the name, and keeps the first one found
Correct configuration = original result for every scope chain: own declarations first; then the local scopes (isLocal() is
!isGlobal(), and the global scope is the one without a parent) from the parent outwards, first match; then the root. Gate G1 checks
the correct configuration on the full suite (baseline: 0 failing tests on the fixture).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Closure-162-probe of the fixture, the first
statement of getVar was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test
-t com.google.javascript.jscomp.ShadowVariablesTest::testShadowWithShadowAlready`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at com.google.javascript.jscomp.Scope.getVar(Scope.java:524). getVar is reached by most of the suite (86 production
call sites); the trigger reaches it through the ShadowVariables pass.

Hosts (host_mode = "1500"): the recipe's seeded draw with the target relative to the source root,
`mr_lib.py preview Closure-162 com/google/javascript/jscomp/Scope.java 12` (seed 5192; the draw excludes Scope.java; n = 12 is the
whole usable pool). Draw order: JsDocInfoParser, JSTypeRegistry, rhino.Node, jsonml.Reader, Parser, RegExpTree, Compiler,
TokenStream, NodeUtil, TypeCheck, DefaultPassConfig, CompilerOptions. Closure's sources are indented by two spaces, so the recipe's
anchor (host_search.pick_insertion_anchor keeps methods indented by four spaces) falls inside a NESTED class of most hosts. Hop
positions are filled in order from the draw: for hop i the next drawn host not yet used is tried at the recipe's anchor for that
position (seed 5192 + 100 + (i-1)); it is unusable when a public static method at that anchor does not compile or cannot be called
from the previous hop, and the next drawn host is then tried:
  hop 1 (anchor seed 5292, called from jscomp.Scope):
     JsDocInfoParser  unusable: anchor after the PRIVATE nested class ExtractionInfo (not accessible from Scope)
     JSTypeRegistry   USED: fewer than three four-space methods, so the recipe inserts before the class's final brace (top level)
  hop 2 (seed 5293, called from rhino.jstype.JSTypeRegistry):
     rhino.Node       unusable: anchor after setQuotedString inside the PRIVATE nested class Node.StringNode
     jsonml.Reader    unusable: anchor after the PRIVATE nested enum Reader.Type
     Parser           USED: anchor after parse(Reader, String, int), a member of the top-level class Parser
  hop 3 (seed 5294, called from rhino.Parser):
     RegExpTree       unusable: anchor after simplify inside the package-private nested class RegExpTree.Anchor (package
                      jscomp.regex; not accessible from rhino)
     Compiler         USED: anchor after toString inside the PUBLIC STATIC nested class Compiler.CodeBuilder; the hop compiles there
                      and is called as Compiler.CodeBuilder.scopedVarDeclaration (its class is recorded as
                      com.google.javascript.jscomp.Compiler.CodeBuilder)
  hop 4 (seed 5295, called from Compiler.CodeBuilder):
     TokenStream      USED: anchor after isKeyword, a member of the top-level class TokenStream
  hop 5 = gold (seed 5296, called from rhino.TokenStream):
     NodeUtil         unusable: anchor after apply inside the package-private nested class NodeUtil.MayBeStringResultPredicate
                      (package jscomp; not accessible from rhino)
     TypeCheck        USED: inserted before the class's final brace (top level)
Host sizes (newlines of the host files): JSTypeRegistry 1650, Parser 2407, Compiler 2097, TokenStream 1714, TypeCheck 1877; the
smallest host is JSTypeRegistry (1650); the gold host TypeCheck has 1877 lines.

Fault (one-line omission in the gold's iteration): the stop at the first declaring scope is dropped (the `break;` after
`found = declared;`), so the walk goes on to the outermost local scope that declares the name and returns that declaration. The
gold then reads as an ordinary walk over the local scopes that records the declaration it meets. Trigger: the EXISTING test
ShadowVariablesTest::testShadowWithShadowAlready (second test call: `p` is used in a function whose enclosing function declares
`var p` and whose outermost enclosing function also declares `var p`; the variant resolves the use to the outer `p`, and the
renamed output differs). Measured on the full suite with this semantics: exactly 1 failing test, this one; gate G5 checks the full
suite again.

The gold's javadoc states the idiomatic contract ("the declaration that a name refers to from inside a local scope, looking in that
scope and in the local scopes that enclose it") and is silent on the order of the search and on stopping. In JavaScript's lexical
scoping a name refers to the declaration of the nearest enclosing scope that declares it, which the variant does not return when an
inner and an outer local scope both declare the name; the contract is violated on the trigger input. The convention is pinned
outside the gold: Scope.isDeclared(name, true) (own declarations, then the parent's, returning at the first), SymbolTable's
SymbolScope.getSlot (own symbol first, then the parent's getSlot) and LinkedFlowScope.getSlot (the first slot with the name, walking
outwards) do the same step in production; passing tests ShadowVariablesTest::testShadowSimple2 and ::testOptimal (a function's own
declaration shadows an outer one), ScopedAliasesTest::testShadowedVar (through the chain: an enclosing function's declaration
shadows the global one) and TypeCheckTest::testScoping1.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: name is passed to every getOwnSlot read; scope starts the walk.
  T2 absent: s is the loop cursor and advances (s = s.getParent()); declared is read by the test and the assignment; found is
     assigned in the loop and returned; the if has an effect (assign and stop) against none.
  T3 absent: no enumeration or closed set; local scopes are the only class the gold names and every local scope on the chain is
     visited (the loop runs while s.isLocal()); no pair or range.
  T4 absent: "the declaration that a name refers to", "looking in that scope and in the local scopes that enclose it" (the loop
     visits them), "or null" for scope (s != null), "@return ... or null if none of these local scopes declares the name" are met.
 Variant gold (javadoc, signature, the loop, `if (declared != null) { found = declared; }`, `return found;`):
  T1 absent: name and scope both change the result; neither is only argument-checked.
  T2 absent: s advances in the loop header; declared reaches the assignment; found (best-so-far) is assigned inside the loop and is
     returned; the if decides whether found changes; nothing is initialised to a literal and left unassigned.
  T3 absent: no set; the gold handles one class of scope (local), all of whose members on the chain it visits.
  T4 absent: the javadoc names no order, nearest/innermost/first rule, limit or value class; "local scopes that enclose it" is met;
     "or null" for scope is met; the @return null case is met (found stays null when no local scope declares the name); identifiers
     (found, declared, s, localDeclarationOf) name nothing the body does not meet; no inline comment.

Single owner: only the gold reads the declarations of the enclosing local scopes and decides which of them the name refers to; hop 1
reads only the facade's own declarations, hop 2 only the global scope and only when the gold returns null, hops 3 and 4 pass the
name and the scope along. Declared alternatives (G9): hop 2 stops its climb at the first scope that declares the name; hop 3 starts
the local search at the scope's parent; hop 4 calls the gold only for a local scope. None makes the trigger pass (hop 2's climb runs
only when the gold returns null).
Recorded bypasses:
 B-0 any hop above the gold calls the lookup again on the scope it holds (`enclosing.getVar(name)` in hop 1, `scope.getVar(name)` in
     hop 2, 3 or 4): the facade's own-declarations-first step then runs scope by scope and the gold's result is never used.
 B-1 a hop above the gold reads the first scope's own declaration itself before calling the gold (for example hop 4:
     `Scope.Var own = (Scope.Var) scope.getOwnSlot(name); return own != null ? own : ...`, written as one line): a second
     implementation of the gold's per-scope step for that one scope. It passes the trigger and the full suite (the inner `var p` is
     in the immediately enclosing scope of the use) but leaves the gold returning the outermost local declaration whenever the
     nearest declaring scope is not the first one searched.

Lie: the facade's javadoc claims that lookups are answered from a cache of the names visible in the scope, filled on the first lookup
and kept until a variable is declared or undeclared; no step of the chain builds or reads a cache (every lookup reads the scopes'
declarations). It names neither shadowing nor the search order nor any hop.
"""

SCOPE = "src/com/google/javascript/jscomp/Scope.java"
REG = "src/com/google/javascript/rhino/jstype/JSTypeRegistry.java"
PARSER = "src/com/google/javascript/rhino/Parser.java"
COMP = "src/com/google/javascript/jscomp/Compiler.java"
TS = "src/com/google/javascript/rhino/TokenStream.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"

GOLD_TEXT = '''/**
 * Returns the declaration that a name refers to from inside a local scope,
 * looking in that scope and in the local scopes that enclose it.
 *
 * @param name the name to look up
 * @param scope the scope to start from, or null
 * @return the declaration, or null if none of these local scopes declares
 *     the name
 */
public static Scope.Var localDeclarationOf(String name, Scope scope) {
    Scope.Var found = null;
    for (Scope s = scope; s != null && s.isLocal(); s = s.getParent()) {
        Scope.Var declared = (Scope.Var) s.getOwnSlot(name);
        if (declared != null) {
            found = declared;
            break;
        }
    }
    return found;
}'''

HOP1 = '''/**
 * Looks up a name among the declarations of a scope and, if the scope does
 * not declare it, in the scopes that enclose the scope.
 *
 * @param name the name to look up
 * @param declared the declarations of the scope, by name
 * @param enclosing the scope that encloses the scope, or null
 * @return the declaration, or null if no scope declares the name
 */
public static Scope.Var resolveVarName(String name,
    Map<String, Scope.Var> declared, Scope enclosing) {
  Scope.Var var = declared.get(name);
  if (var != null) {
    return var;
  }
  return enclosing == null ? null : Parser.findVarInScopes(name, enclosing);
}'''

HOP2 = '''/**
 * Looks up a name in a scope and in the scopes that enclose it: in the local
 * scopes, and then in the global scope.
 *
 * @param name the name to look up
 * @param scope the scope to start from
 * @return the declaration, or null if no scope declares the name
 */
public static Scope.Var findVarInScopes(String name, Scope scope)
{
    Scope.Var var = Compiler.CodeBuilder.scopedVarDeclaration(name, scope);
    if (var != null) {
        return var;
    }
    Scope global = scope;
    while (global.getParent() != null) {
        global = global.getParent();
    }
    return (Scope.Var) global.getOwnSlot(name);
}'''

HOP3 = '''/**
 * Returns the declaration of a name in the local scopes, starting from the
 * given scope.
 *
 * @param name the name to look up
 * @param scope the scope to start from
 * @return the declaration, or null if no local scope declares the name
 */
public static Var scopedVarDeclaration(String name, Scope scope) {
  return TokenStream.declarationOfName(name, scope);
}'''

HOP4 = '''/**
 * Returns the declaration of a name in the local scopes, from the given
 * scope outwards.
 *
 * @param name the name to look up
 * @param scope the scope to start from
 * @return the declaration, or null if no local scope declares the name
 */
public static Scope.Var declarationOfName(String name, Scope scope)
{
    return TypeCheck.localDeclarationOf(name, scope);
}'''

DESIGN = {
 "instance": "Closure-162", "project": "Closure", "bug_id": 162, "seed": 5192,
 "src_root": "src", "test_root": "test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "name, the private field vars (Map<String, Var>, the scope's own declarations) and the private field parent "
                 "(Scope), passed to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [1650, 2407, 2097, 1714, 1877],
 "reachability_probe": "getVar first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Closure-162-probe: ShadowVariablesTest::testShadowWithShadowAlready fails with "
                       "PROBE-REACHED at com.google.javascript.jscomp.Scope.getVar(Scope.java:524)",
 "facade": {"file": SCOPE, "class": "com.google.javascript.jscomp.Scope", "method": "getVar", "near_line": 523},
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/ShadowVariablesTest.java",
             "test_class": "com.google.javascript.jscomp.ShadowVariablesTest", "test_method": "testShadowWithShadowAlready"},
 "expected_signature": "Result: var d=function(a){return function(){return function(){return function(){return function(){a};b};var c}",
 "gold": {"method": "localDeclarationOf", "text": GOLD_TEXT,
          "fault": {"old": "                found = declared;\n                break;",
                    "new": "                found = declared;"}},
 "chain": {
   "facade_body": "return com.google.javascript.rhino.jstype.JSTypeRegistry.resolveVarName(name, vars, parent);",
   "lie": "Lookups are answered from a cache of the names visible in this scope, which is filled on the first lookup and kept "
          "until a variable is declared or undeclared.",
   "hops": [
     {"file": REG, "class": "com.google.javascript.rhino.jstype.JSTypeRegistry", "method": "resolveVarName",
      "imports": ["com.google.javascript.jscomp.Scope", "com.google.javascript.rhino.Parser"], "text": HOP1},
     {"file": PARSER, "class": "com.google.javascript.rhino.Parser", "method": "findVarInScopes",
      "imports": ["com.google.javascript.jscomp.Compiler", "com.google.javascript.jscomp.Scope"], "text": HOP2},
     {"file": COMP, "class": "com.google.javascript.jscomp.Compiler.CodeBuilder", "method": "scopedVarDeclaration",
      "imports": ["com.google.javascript.rhino.TokenStream"], "text": HOP3},
     {"file": TS, "class": "com.google.javascript.rhino.TokenStream", "method": "declarationOfName",
      "imports": ["com.google.javascript.jscomp.Scope", "com.google.javascript.jscomp.TypeCheck"], "text": HOP4},
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "localDeclarationOf",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.google.javascript.jscomp.Scope::isDeclared",
              "com.google.javascript.jscomp.SymbolTable.SymbolScope::getSlot",
              "com.google.javascript.jscomp.LinkedFlowScope::getSlot"],
 "ownership_reason": "Only the gold reads the declarations of the enclosing local scopes and decides which of them a name refers "
                     "to: hop 1 reads only the scope's own declarations (the facade's private map) and otherwise hands the "
                     "enclosing scope on; hop 2 reads only the global scope, and only when the gold returns null; hops 3 and 4 "
                     "pass the name and the scope along unchanged. Once the gold has walked past the nearest declaring local scope "
                     "and returned the outermost one, no caller sees the inner declaration unless it repeats the gold's per-scope "
                     "step itself or replaces the chain. The gold's javadoc promises the declaration that the name refers to from "
                     "inside the scope; under JavaScript's lexical scoping that is the nearest enclosing declaration, which the "
                     "variant does not return when two enclosing local scopes declare the name. The convention is pinned outside "
                     "the gold: Scope.isDeclared (own declarations, then the parent's, returning at the first), "
                     "SymbolTable.SymbolScope.getSlot (own symbol first, then the parent's) and LinkedFlowScope.getSlot (the first "
                     "slot with the name, walking outwards) do the same step in production; ShadowVariablesTest testShadowSimple2 "
                     "and testOptimal (a function's own declaration shadows an outer one), ScopedAliasesTest testShadowedVar "
                     "(through the chain: an enclosing function's declaration shadows the global one) and TypeCheckTest "
                     "testScoping1 pass.",
 "ownership_tests": ["com.google.javascript.jscomp.ShadowVariablesTest::testShadowSimple2",
                     "com.google.javascript.jscomp.ShadowVariablesTest::testOptimal",
                     "com.google.javascript.jscomp.ScopedAliasesTest::testShadowedVar",
                     "com.google.javascript.jscomp.TypeCheckTest::testScoping1"],
 "compensating": {
   "chain": [
     {"file": PARSER, "old": "while (global.getParent() != null) {",
      "new": "while (global.getParent() != null && global.getOwnSlot(name) == null) {",
      "why": "hop 2 stops its climb at the first scope that declares the name"},
     {"file": COMP, "old": "return TokenStream.declarationOfName(name, scope);",
      "new": "return TokenStream.declarationOfName(name, scope.getParent());",
      "why": "hop 3 starts the local search at the scope's parent"},
     {"file": TS, "old": "return TypeCheck.localDeclarationOf(name, scope);",
      "new": "return scope.isLocal() ? TypeCheck.localDeclarationOf(name, scope) : null;",
      "why": "hop 4 calls the local search only for a local scope"},
   ],
 },
 "host_notes": "host_mode 1500: the recipe's seeded draw `mr_lib.py preview Closure-162 com/google/javascript/jscomp/Scope.java 12` "
               "(target relative to the source root; seed 5192; n=12, the whole usable pool) in draw order JsDocInfoParser, "
               "JSTypeRegistry, rhino.Node, jsonml.Reader, Parser, RegExpTree, Compiler, TokenStream, NodeUtil, TypeCheck, "
               "DefaultPassConfig, CompilerOptions. Closure is indented by two spaces and the recipe's anchor keeps four-space "
               "methods, so most anchors fall inside nested classes; hop positions are filled in order from the draw, and a host "
               "was skipped at a hop position when a public static method at that position's recipe anchor (seed 5192+100+i) does "
               "not compile or cannot be called from the previous hop: hop 1 JsDocInfoParser (anchor after the private nested "
               "ExtractionInfo) skipped -> JSTypeRegistry (end of class, top level, 1650 lines); hop 2 rhino.Node (private nested "
               "StringNode) and jsonml.Reader (private nested enum Type) skipped -> Parser (after parse, top level, 2407); hop 3 "
               "RegExpTree (package-private nested Anchor in jscomp.regex, not visible from rhino) skipped -> Compiler (after "
               "CodeBuilder.toString, inside the public static nested class Compiler.CodeBuilder, 2097); hop 4 TokenStream (after "
               "isKeyword, top level, 1714); hop 5 gold: NodeUtil (package-private nested MayBeStringResultPredicate in jscomp, not "
               "visible from rhino) skipped -> TypeCheck (end of class, top level, 1877). Smallest host JSTypeRegistry (1650). The "
               "facade calls hop 1 by its fully-qualified name; JSTypeRegistry imports jscomp.Scope and rhino.Parser (it already "
               "imports java.util.Map); Parser imports jscomp.Compiler and jscomp.Scope; Compiler imports rhino.TokenStream (it "
               "already imports Scope.Var); TokenStream imports jscomp.Scope and jscomp.TypeCheck; TypeCheck already imports "
               "Scope.Var and shares Scope's package. The recipe indents inserted text by four spaces (Parser and TokenStream use "
               "four; JSTypeRegistry and TypeCheck use two, so their hops sit two spaces deeper than their neighbours; the "
               "CodeBuilder hop matches its nested neighbours).",
}
