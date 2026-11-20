"""Main run Closure-165__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout
of Defects4J Closure-165; the real bug modified JSTypeRegistry, ObjectType, RecordType and RecordTypeBuilder; the facade's class
ObjectType is one of them). No static pair (B8 note section 1: pool v2 found no strictly tested public static method in the
modified classes).

Facade: ObjectType.isUnknownType() (the only allowed candidate of batch9_tasks.json, facade_planned_by null; no facade reuse). It
is an @Override of JSType.isUnknownType; the override, its signature, modifiers and thrown types are kept.
Original computation of the facade (cached in the private field `unknown`, initially true): while the field is true, the implicit
prototype is asked again; if there is none, or it is a native object type, the field becomes true exactly when one of the
interfaces extended by the constructor (getCtorExtendedInterfaces) is unknown; otherwise the field takes the implicit prototype's
isUnknownType(). The field is returned.

facade_variant: V1+V2. V1: the facade keeps the cache guard on the private field `unknown` (read inside ObjectType, no visibility
change) and writes the value returned by hop 1 back into that field, then returns it. V2: the computation needs the receiver's
public methods getImplicitPrototype() and getCtorExtendedInterfaces() (both overridden in subclasses), so `this` is passed to hop 1
typed as ObjectType; the hops call only public methods of ObjectType (getImplicitPrototype, getCtorExtendedInterfaces,
isNativeObjectType, isUnknownType). No private method is needed (no V4), no package-private type passes through a hop (no V3/V5).
No signature, modifier, override or throws change; no new type; no reflection; no test edit.
state_passed: the receiver `this` (as ObjectType) to hop 1, under the original guard `if (unknown)`; the returned boolean is written
back into the private field `unknown`, which the facade returns.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Closure-165-probe/w of the
fixture, the first statement of isUnknownType was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t com.google.javascript.jscomp.TypeCheckTest::testIssue725` (the fixture's Defects4J trigger) and
`defects4j test -t com.google.javascript.jscomp.TypeCheckTest::testInterfaceExtendsResolution` (the chosen trigger): each 1
failing test, java.lang.IllegalStateException: PROBE-REACHED at ObjectType.isUnknownType(ObjectType.java:501) from
UnionTypeBuilder.addAlternate <- JSTypeRegistry.createUnionType <- JSTypeRegistry.initializeBuiltInTypes <- JSTypeRegistry.<init>.
The facade is reached by every existing test that builds a type registry (production callers in the type system).

Hosts (host_mode = "1500"; `mr_lib.py preview Closure-165 com/google/javascript/rhino/jstype/ObjectType.java 6` with the instance
seed 8824 draws TypeCheck, JSDocInfo, Node, Compiler, SymbolTable, JsDocInfoParser; the facade file is excluded by the draw).
The recipe's anchor (stageB_lib.pick_anchor, seed 8824 + 100 + i) only accepts methods indented four spaces; Closure indents by
two, so the anchors it draws are members of NESTED classes, and the hop is inserted inside that nested class. Drawn host 3 (Node)
is unusable: its seeded anchor (after `next`, seed 8926) lies in the private static class Node.SiblingNodeIterable, whose static
method hop 2 (in another top-level class) cannot call. It is replaced by the next drawn host whose seeded anchor (seed 8926) is
callable: JsDocInfoParser (anchor in the private static class ExtractionInfo), RegExpTree (package-private Text in another
package) and DefaultPassConfig (a non-static inner class, which cannot declare a static method) are unusable in turn; CompilerOptions
(public static enum TweakProcessing) is the first usable one. Hosts 1, 2, 4, 5 are the drawn hosts at their drawn positions.
  hop 1 jscomp.TypeCheck                 1888 lines  isUnknownObject          pass-through (anchor None: end of the outer class)
  hop 2 rhino.JSDocInfo$Marker           1508 lines  isUnresolvedObjectType   pass-through (after getAnnotation)
  hop 3 jscomp.CompilerOptions$TweakProcessing 2083 lines  isObjectTypeUnknown  pass-through (after shouldStrip; substituted host)
  hop 4 jscomp.Compiler$CodeBuilder      2478 lines  objectTypeIsUnknown      pass-through (after toString)
  hop 5 jscomp.SymbolTable$SymbolScope   1611 lines  isUnknownObjectType      GOLD: the implicit-prototype lookup, the decision
                                                                             between asking the prototype and scanning the
                                                                             extended interfaces, the scan and the delegation
Host newline counts 1888, 1508, 2083, 2478, 2312->2083 substituted (pool fifth 2312); used sizes 1888, 1508, 2083, 2478, 1611; the
smallest host is JSDocInfo (1508 lines); the gold host has 1611 lines. Class names are given in the harness catalog's form
(Outer$Nested), which JavaMethodCatalog produces for nested classes.
The correct configuration returns the original value for every object type: the gold performs the original's decision, scan and
delegation, and the facade keeps the cache guard and the write-back.

Fault (one-line omission of a special-case decision in the gold): the test that a NATIVE implicit prototype counts like a missing
one is dropped, so `if (implicitProto == null || implicitProto.isNativeObjectType())` becomes `if (implicitProto == null)`. A type whose implicit prototype
is a built-in (an interface's prototype object, whose implicit prototype is Object.prototype) then takes the answer of the
built-in, which is never unknown, and its extended interfaces are never consulted. The gold then reads as the ordinary routine
"ask the implicit prototype; with no prototype, scan the extended interfaces". Trigger: the EXISTING test
TypeCheckTest::testInterfaceExtendsResolution (`@interface @extends {A}` B, `@constructor @implements {B}` C, then
`@interface` A declared last): B's prototype no longer counts as unknown while A is unresolved, so FunctionTypeBuilder reports
"JSC_RESOLVED_TAG_EMPTY. Could not resolve type in @implements tag of C" and testTypes fails with "unexpected warnings(s)". It is
the only test of the full suite that newly fails (full-suite run of this omission in the scratch copy: 1 failing test); the same
holds for dropping the interface scan altogether, so the trigger is the one test that pins this case.

The gold's javadoc states the idiomatic contract (whether the given object type is still unknown to the type system, the same
predicate as the facade's) and says nothing about how the answer is reached, which inherited types are asked, or native
prototypes; on the trigger, B's prototype inherits from the unresolved interface A and is reported as known. The convention is pinned outside the gold:
PrototypeObjectType.getSlot (an object inherits from its implicit prototype and then from the interfaces extended by its
constructor), PrototypeObjectType.toStringHelper (the walk up the implicit prototypes stops at a native object type: the native
prototypes end the program's own chain), PrototypeObjectType.isSubtype (extended interfaces decide subtyping for interface
types); passing tests TypeCheckTest::testInterfaceExtends, TypeCheckTest::testBadInterfaceExtends1 and
JSTypeTest::testInterfaceInheritanceSubtypeChain; the facade's own javadoc ("We treat this as the unknown type if any of its
implicit prototype properties is unknown") is kept.

Single owner: only the gold looks up the implicit prototype and decides whether the prototype or the extended interfaces answer;
hops 1-4 hand the object type along unchanged and cannot change which prototype the gold sees (the gold reads it from the type).
No one-line change of the argument above the gold helps: handing the gold the native prototype instead of the type gives the
prototype's own (empty) interfaces; answering native types at a hop leaves B's prototype (not native) unchanged.
Declared alternatives (G9): hop 1 answers native object types itself; hop 4 hands the gold the native implicit prototype instead of
the type; hop 3 also asks the implicit prototype after the chain. Each leaves the trigger failing.
Recorded bypasses (edits that replace or duplicate the gold's own computation, not repairs of the chain):
 B-1 a hop (or the facade) that scans getCtorExtendedInterfaces() itself before or after the call (a for statement with a nested
     if: a second implementation of the gold's interface scan; Java 6 source level has no one-expression form of it).
     Checked on the variant in a scratch copy (the scan placed before hop 4's call): full suite 0 failing tests.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie (appended by a comment-only pre_edit: the recipe's rewrite_facade finds no javadoc directly above the header because the
@Override annotation stands between them, so it inserts nothing; the pre_edit appends the chain's lie sentence to the javadoc in
its own layout): the facade's javadoc claims each property of the implicit prototype is resolved in turn and the first property whose declared
type is unknown marks the type; the chain resolves no property and reads no declared property type (it asks the implicit prototype
or the extended interfaces as wholes). It names neither natives, interfaces, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold.
The gold's text: javadoc 'Returns whether the given object type is still unknown to the type system.', '@param type the object
type', '@return whether the type is unknown'; signature `isUnknownObjectType(ObjectType type)`; locals implicitProto and
extended; no inline comment. The javadoc names no source the answer is taken from, so no class of inherited types
is named in the gold's text.
 Correct gold (`if (implicitProto == null || implicitProto.isNativeObjectType())` scan, otherwise delegate):
  T1 absent: type is read for its implicit prototype and its extended interfaces, both of which decide the return value; there
     is no argument check.
  T2 absent: implicitProto is read by the decision and by the delegation; extended is read by the test that returns true; no
     literal-initialised local, no cursor, counter, flag or best-so-far; the decision's two outcomes (scan / delegate) differ; the
     inner if returns true and the fall-through false.
  T3 absent: the two parts the gold reads from type (implicit prototype, extended interfaces) both get the isUnknownType
     treatment, each on its own path; the condition 'null or native' is not a closed set of the gold's text (the text names no
     class of prototypes); no enum, type code, pair or range.
  T4 absent: 'whether the given object type is still unknown to the type system' and '@return whether the type is unknown'
     describe the result in general, and the delegation and the scan produce it; '@param type the object type' names no rule;
     identifiers implicitProto and extended name what they hold.
 Variant gold (`if (implicitProto == null)` scan of type.getCtorExtendedInterfaces() returning true on the first unknown one and
 false after the scan, otherwise `return implicitProto.isUnknownType();`):
  T1 absent: type is read for its implicit prototype and its extended interfaces; both reach the return value (delegation and
     scan); no argument check.
  T2 absent: implicitProto is tested and its isUnknownType() is returned; extended is tested in the scan; no literal-initialised
     local, no cursor, counter, flag or best-so-far; the null decision leads to the scan or to the delegation, which differ; the
     inner if returns true, the fall-through false.
  T3 absent: both parts the gold reads (the implicit prototype and the extended interfaces) are treated, the prototype by
     delegation and the interfaces by the scan; the only special case tested is null, and the gold's text names no class of
     prototypes or inherited types (no 'native', 'built-in', 'inherits', 'interfaces' or 'end of the chain'), so nothing named
     is handled only in part; no pair halves or range ends.
  T4 absent: the javadoc names no concrete rule, limit, bound, value class or case: 'still unknown to the type system' is the
     general predicate the body computes by its delegation and its scan; the @param and @return clauses name no rule; no inline
     comment; no identifier names a property the body does not meet.
"""

OT = "src/com/google/javascript/rhino/jstype/ObjectType.java"
TC = "src/com/google/javascript/jscomp/TypeCheck.java"
JDI = "src/com/google/javascript/rhino/JSDocInfo.java"
CO = "src/com/google/javascript/jscomp/CompilerOptions.java"
CMP = "src/com/google/javascript/jscomp/Compiler.java"
ST = "src/com/google/javascript/jscomp/SymbolTable.java"

GOLD_TEXT = '''/**
 * Returns whether the given object type is still unknown to the type
 * system.
 *
 * @param type the object type
 * @return whether the type is unknown
 */
public static boolean isUnknownObjectType(ObjectType type) {
  ObjectType implicitProto = type.getImplicitPrototype();
  if (implicitProto == null || implicitProto.isNativeObjectType()) {
    for (ObjectType extended : type.getCtorExtendedInterfaces()) {
      if (extended.isUnknownType()) {
        return true;
      }
    }
    return false;
  }
  return implicitProto.isUnknownType();
}'''

HOP1 = '''/**
 * Returns whether the given object type is unknown.
 *
 * @param type The object type.
 * @return Whether the object type is unknown.
 */
public static boolean isUnknownObject(ObjectType type) {
  return JSDocInfo.Marker.isUnresolvedObjectType(type);
}'''

HOP2 = '''/**
 * Returns whether an object type is unresolved, that is, still unknown
 * to the type system.
 */
public static boolean isUnresolvedObjectType(ObjectType type) {
  return CompilerOptions.TweakProcessing.isObjectTypeUnknown(type);
}'''

HOP3 = '''/**
 * Whether the given object type is unknown.
 */
public static boolean isObjectTypeUnknown(ObjectType type) {
  return Compiler.CodeBuilder.objectTypeIsUnknown(type);
}'''

HOP4 = '''/** Returns whether the given object type is unknown. */
public static boolean objectTypeIsUnknown(ObjectType type) {
  return SymbolTable.SymbolScope.isUnknownObjectType(type);
}'''

DESIGN = {
 "instance": "Closure-165", "project": "Closure", "bug_id": 165, "seed": 8824,
 "src_root": "src", "test_root": "test",
 "facade": {"file": OT, "class": "com.google.javascript.rhino.jstype.ObjectType", "method": "isUnknownType", "near_line": 500},
 "facade_variant": "V1+V2",
 "state_passed": "the receiver this (as ObjectType) to hop 1 under the original guard on the private field unknown; the returned "
                 "boolean is written back into unknown, which the facade returns",
 "reachability_probe": "TypeCheckTest::testIssue725 and TypeCheckTest::testInterfaceExtendsResolution each fail with java.lang.IllegalStateException: PROBE-REACHED at "
                       "ObjectType.isUnknownType(ObjectType.java:501) from UnionTypeBuilder.addAlternate <- "
                       "JSTypeRegistry.initializeBuiltInTypes <- JSTypeRegistry.<init>",
 "trigger": {"existing": True, "test_file": "test/com/google/javascript/jscomp/TypeCheckTest.java",
             "test_class": "com.google.javascript.jscomp.TypeCheckTest", "test_method": "testInterfaceExtendsResolution"},
 "expected_signature": "Could not resolve type in @implements tag of C",
 "gold": {"method": "isUnknownObjectType", "text": GOLD_TEXT,
          "fault": {"old": "      if (implicitProto == null || implicitProto.isNativeObjectType()) {\n",
                    "new": "      if (implicitProto == null) {\n"}},
 "chain": {
   "facade_body": "// If the object is unknown now, check the supertype again,\n"
                  "    // because it might have been resolved since the last check.\n"
                  "    if (unknown) {\n"
                  "      unknown = com.google.javascript.jscomp.TypeCheck.isUnknownObject(this);\n"
                  "    }\n"
                  "    return unknown;",
   "lie": "Each property of the implicit prototype is resolved in turn, and the first property whose declared type is still "
          "unknown marks this type as unknown.",
   "hops": [
     {"file": TC, "class": "com.google.javascript.jscomp.TypeCheck", "method": "isUnknownObject",
      "imports": [], "text": HOP1},
     {"file": JDI, "class": "com.google.javascript.rhino.JSDocInfo$Marker", "method": "isUnresolvedObjectType",
      "imports": ["com.google.javascript.jscomp.CompilerOptions", "com.google.javascript.rhino.jstype.ObjectType"], "text": HOP2},
     {"file": CO, "class": "com.google.javascript.jscomp.CompilerOptions$TweakProcessing", "method": "isObjectTypeUnknown",
      "imports": ["com.google.javascript.rhino.jstype.ObjectType"], "text": HOP3},
     {"file": CMP, "class": "com.google.javascript.jscomp.Compiler$CodeBuilder", "method": "objectTypeIsUnknown",
      "imports": ["com.google.javascript.rhino.jstype.ObjectType"], "text": HOP4},
     {"file": ST, "class": "com.google.javascript.jscomp.SymbolTable$SymbolScope", "method": "isUnknownObjectType",
      "imports": [], "gold": True},
   ],
 },
 "pre_edits": {"chain": [
   {"file": OT,
    "old": "   * We treat this as the unknown type if any of its implicit prototype\n"
           "   * properties is unknown.\n"
           "   */\n"
           "  @Override\n"
           "  public boolean isUnknownType() {",
    "new": "   * We treat this as the unknown type if any of its implicit prototype\n"
           "   * properties is unknown. Each property of the implicit prototype is\n"
           "   * resolved in turn, and the first property whose declared type is still\n"
           "   * unknown marks this type as unknown.\n"
           "   */\n"
           "  @Override\n"
           "  public boolean isUnknownType() {",
    "why": "appends the lie to the facade's javadoc: the recipe's rewrite_facade does not find a javadoc separated from the "
           "header by the @Override annotation (extract_transform.find_javadoc_start), so the same sentence is appended here "
           "in the javadoc's own layout; comment only"},
 ]},
 "evidence": ["com.google.javascript.rhino.jstype.PrototypeObjectType::getSlot",
              "com.google.javascript.rhino.jstype.PrototypeObjectType::toStringHelper",
              "com.google.javascript.rhino.jstype.PrototypeObjectType::isSubtype"],
 "ownership_reason": "Only the gold looks up the implicit prototype and decides whether the prototype or the interfaces extended "
                     "by the constructor answer; hops 1-4 hand the object type along unchanged, and the gold reads the "
                     "prototype from the type itself, so no caller can change which prototype it sees. The gold's javadoc "
                     "promises whether the given object type is still unknown to the type system, the predicate the facade "
                     "answers; on the trigger, the prototype of interface B inherits from the "
                     "unresolved interface A and is reported as known, because its implicit prototype is the built-in "
                     "Object.prototype. No one-line change of the argument above the gold restores this: handing the gold the "
                     "native prototype gives that prototype's own, empty interfaces, and answering native types at a hop "
                     "leaves B's prototype, which is not native, unchanged. The convention is pinned outside the gold: "
                     "PrototypeObjectType.getSlot (an object inherits from its implicit prototype and then from the interfaces "
                     "extended by its constructor), PrototypeObjectType.toStringHelper (the walk up the implicit prototypes "
                     "stops at a native object type), PrototypeObjectType.isSubtype (extended interfaces decide for interface "
                     "types), with TypeCheckTest testInterfaceExtends and testBadInterfaceExtends1 and JSTypeTest "
                     "testInterfaceInheritanceSubtypeChain passing; the facade's own javadoc treats the type as unknown if any "
                     "of its implicit prototype properties is unknown.",
 "ownership_tests": ["com.google.javascript.jscomp.TypeCheckTest::testInterfaceExtends",
                     "com.google.javascript.jscomp.TypeCheckTest::testBadInterfaceExtends1",
                     "com.google.javascript.rhino.jstype.JSTypeTest::testInterfaceInheritanceSubtypeChain"],
 "compensating": {
   "chain": [
     {"file": TC, "old": "return JSDocInfo.Marker.isUnresolvedObjectType(type);",
      "new": "return type.isNativeObjectType() ? false : JSDocInfo.Marker.isUnresolvedObjectType(type);",
      "why": "hop 1 answers native object types itself"},
     {"file": CMP, "old": "return SymbolTable.SymbolScope.isUnknownObjectType(type);",
      "new": "return SymbolTable.SymbolScope.isUnknownObjectType(type.getImplicitPrototype() != null && type.getImplicitPrototype().isNativeObjectType() ? type.getImplicitPrototype() : type);",
      "why": "hop 4 hands the gold the native implicit prototype instead of the type"},
     {"file": CO, "old": "return Compiler.CodeBuilder.objectTypeIsUnknown(type);",
      "new": "return Compiler.CodeBuilder.objectTypeIsUnknown(type) || (type.getImplicitPrototype() != null && type.getImplicitPrototype().isUnknownType());",
      "why": "hop 3 also asks the implicit prototype after the chain"},
   ],
 },
 "host_notes": "host_mode 1500. mr_lib.py preview Closure-165 com/google/javascript/rhino/jstype/ObjectType.java 6 with the "
               "instance seed 8824 draws TypeCheck (1888 lines), JSDocInfo (1508), Node (2395), Compiler (2478), SymbolTable "
               "(1611), JsDocInfoParser (2361); further draws RegExpTree, DefaultPassConfig, CompilerOptions (2083). The recipe "
               "anchor accepts only four-space-indented methods, which in Closure's two-space code are members of nested "
               "classes, so each hop is inserted inside the nested class of its seeded anchor (seed 8824 + 100 + i): hop 1 "
               "TypeCheck anchor None (end of the outer class, seed 8924); hop 2 JSDocInfo after getAnnotation in the public "
               "static final class Marker (8925); hop 3: drawn host Node is unusable, its seeded anchor (after next, 8926) is "
               "in the private static class SiblingNodeIterable, which hop 2 in another top-level class cannot call; the next "
               "drawn hosts at the same anchor seed are unusable too (JsDocInfoParser: private static class ExtractionInfo; "
               "RegExpTree: package-private class Text in package jscomp.regex; DefaultPassConfig: non-static inner class "
               "GlobalTypeResolver, which cannot declare a static method), and CompilerOptions (after shouldStrip in the "
               "public static enum TweakProcessing, 8926) is the first usable one and replaces Node; hop 4 Compiler after "
               "toString in the public static class CodeBuilder (8927); hop 5 (gold) SymbolTable after isDocScope in the "
               "public static final class SymbolScope (8928). Classes are recorded as Outer$Nested (the harness method "
               "catalog's form). Used host sizes 1888, 1508, 2083, 2478, 1611; smallest JSDocInfo (1508). The facade calls hop "
               "1 by its fully-qualified name; JSDocInfo, CompilerOptions and Compiler gain an ObjectType import, JSDocInfo "
               "also a CompilerOptions import. The facade's class ObjectType is not a host.",
}
