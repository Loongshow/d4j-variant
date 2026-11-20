"""Main run Collections-2__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; the
fixed checkout of Defects4J Collections-2, whose real bug modified ExtendedProperties, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE section 1).

Facade: ExtendedProperties.getInclude() (the only allowed candidate of the task record, BATCH8_PREREGISTRATION.md row 224). Its
facade_planned_by is Collections-13__i, so this is a recorded facade reuse (facade_reuse_of = [Collections-13__i]); no candidate with
facade_planned_by = null exists for this task. None of that instance's files was opened.
Original computation of the facade: the private instance field includePropertyName null (nothing set) gives the protected static
default name include ("include"); includePropertyName "" (setInclude("") or setInclude(null), which stores "") gives null; otherwise
includePropertyName itself.

facade_variant: V1 (state as parameters). The method reads two fields and writes none: the facade reads the private instance field
includePropertyName and the protected static field include (inside ExtendedProperties, so no visibility change) and passes the two
String values to hop 1, returning its result. No public method of the receiver is needed (no V2), no private method is called (no V4),
no package-private type is involved (no V3/V5). No guard (the original had none). No signature, modifier, override or throws change;
no new type; no reflection; no test edit.
state_passed: the private field includePropertyName and the protected static field include (String values) to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-2-probe/w of the fixture,
the first statement of getInclude was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.collections.TestExtendedProperties::testInclude`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at ExtendedProperties.getInclude(ExtendedProperties.java:514) called from
TestExtendedProperties.testInclude(TestExtendedProperties.java:320). The facade is reached by the existing test directly (it is also
called in production by ExtendedProperties.load).

Hosts (host_mode = "largest5"; hosts_hop_order of batch8_tasks.json, in that order; the fifth substituted by the next-largest public class):
  hop 1 bidimap.TreeBidiMap      2084 lines  includeKeyName       pass-through (the two names)
  hop 2 DoubleOrderedMap         1994 lines  nameOfIncludeKey     pass-through
  hop 3 MapUtils                 1644 lines  getIncludeKeyName    pass-through
  hop 4 CursorableLinkedList.java 1467 lines includeKeyNameFor    pass-through; the recipe's anchor (after `iterator`, line idx 1248)
                                                                  lies in the file's second top-level class CursorableSubList
                                                                  (package-private, extends CursorableLinkedList), so the hop is a
                                                                  member of CursorableSubList; MapUtils is in the same package
  hop 5 map.AbstractHashedMap    1328 lines  resolveIncludeKey    GOLD: the decision between the default name, no name and the name set
                                                                  (substitute for the fifth listed host FastArrayList, 1332 lines,
                                                                  which cannot carry an added static method: see host_notes)
Host newline counts 2084, 1994, 1644, 1467, 1328; the smallest host (and the gold host) is map.AbstractHashedMap (1328 lines; C10F
addendum section 1: hosts under 1500 lines are expected in this regime).
The correct configuration returns the original result for every state: name null gives the default name (even a null or empty
default, as the original returns the static field unchanged), name "" gives null, any other name is returned as it is.

Fault (one-line omission of a special-case decision in the gold): the decision that an empty name set on the configuration gives
no include property (null) is dropped, so the gold reads as the ordinary "the name set, else the default name". Trigger: the
EXISTING test TestExtendedProperties::testInclude; its first assertions (default "include" on two objects, setInclude("import"))
still hold, and after a.setInclude("") the assertion assertEquals(null, a.getInclude()) at line 328 fails with
expected:<null> but was:<> (the empty name is returned). It is the only test that newly fails: the variant differs from the original
only when includePropertyName is "", which only setInclude produces, and only testInclude calls setInclude (gate G5 checks the full
suite); load() calls getInclude() on configurations with no name set (the default path, unchanged).

The gold's javadoc states the idiomatic contract (the name of the property that includes other properties files, given the name set
on a configuration and the default name; the default name is used while no name has been set) and is silent on an empty name. The
convention is pinned outside the gold: ExtendedProperties.setInclude ("@param inc the property name which includes another property,
empty converted to null"; it stores "" for null, so an empty name set is the configuration's 'none'); ExtendedProperties.load treats a
null include name as 'no inclusion' (`includeProperty != null && key.equalsIgnoreCase(includeProperty)`) and treats an empty value as no
value (`if ("".equals(value)) continue;`), and no key it reads can be empty (lines are trimmed and the '=' must follow at least one
character), so "" is never the name of a property that includes other files; the class javadoc ("If a property is named "include"
(or whatever is defined by setInclude() and getInclude() ..."). Passing tests through the chain (the default path):
TestExtendedProperties::testSaveAndLoad, ::testTrailingBackSlash, ::testMultipleSameKey1 (each loads a configuration through load(),
which calls the facade and the chain and gets the default name).

Single owner: only the gold decides which name the configuration has; hops 1-4 hand the two names on unchanged. With the variant gold
(the name set if not null, else the default), the trigger's null for an empty name can only come out of the gold if both names it is
given are null, and every hop documents the default name as not null, so no hop can make the gold produce it while every method on
the path is used as documented. Declared alternatives (G9; each leaves the trigger failing): hop 1 passes an empty name on as null
(the gold then gives the default name "include"); hop 2 passes the default name in place of a missing name (an empty name still
reaches the gold as it is); hop 4 passes an empty name on as null with an empty default (the gold returns "").
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-1 any hop answers an empty name itself, before the call (`if ("".equals(name)) { return null; }`): a second implementation of
     the gold's decision for that case; the gold is not called for it. Checked on the variant in a scratch copy (at hop 2):
     trigger passes, full suite 0 failing tests.
 B-2 any hop or the facade rewrites the gold's result (`String key = ...; return "".equals(key) ? null : key;`): string surgery on
     the value the gold returned.
 B-3 any hop passes null for the default name together with a null name when the name is empty: it breaks the documented
     precondition of every later hop and of the gold ("the default name, not null").
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the name is first looked up among the properties already loaded and the stored name is consulted
only when none of them defines it; no step of the chain reads any loaded property. It names neither the empty name, null, the omitted
step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: name is tested and returned; defaultName is returned when no name has been set; no argument check.
  T2 absent: no locals; the three outcomes (defaultName, null, name) differ; no loop.
  T3 absent: no closed set is treated in part (the gold's text names no class of names; null and the empty name are both handled).
  T4 absent: 'the default name is used while no name has been set' is met by the null test; '@param defaultName the default name,
     not null' is a caller precondition; '@return the name of the property that includes other properties files' is a general
     description; no inline comment.
 Variant gold (javadoc, signature, `if (name == null) { return defaultName; }`, `return name;`):
  T1 absent: name decides the branch and is returned; defaultName is returned on the null branch; neither only argument-checked.
  T2 absent: no locals at all; the decision returns two different values; no loop, cursor, counter, flag or best-so-far.
  T3 absent: one test on the name (null), which the gold's own text ties to 'no name has been set'; no enum, type code, named format,
     pair halves or range ends; no class named in the text ('No member handled' for any set of special names).
  T4 absent: 'Gets the name of the property that includes other properties files, given the name set on a configuration and the
     default name' and '@return the name of the property ...' are general descriptions that the two returns address; 'The default
     name is used while no name has been set' is met by `if (name == null) { return defaultName; }` with '@param name ..., null if
     none has been set'; 'not null' on defaultName is a caller precondition; no inline comment; identifiers name what they hold."""

EP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"
AHM = "src/java/org/apache/commons/collections/map/AbstractHashedMap.java"

GOLD_TEXT = '''/**
 * Gets the name of the property that includes other properties files,
 * given the name set on a configuration and the default name.
 * <p>
 * The default name is used while no name has been set.
 *
 * @param name  the name set on the configuration, null if none has been set
 * @param defaultName  the default name, not null
 * @return the name of the property that includes other properties files
 */
public static String resolveIncludeKey(String name, String defaultName) {
    if (name == null) {
        return defaultName;
    }
    if (name.length() == 0) {
        return null;
    }
    return name;
}'''

def hop(method, call, summary="Gets the name of the property that includes other properties files,\n * given the name set on a configuration and the default name."):
    return f'''/**
 * {summary}
 *
 * @param name  the name set on the configuration, null if none has been set
 * @param defaultName  the default name, not null
 * @return the name of the property that includes other properties files
 */
public static String {method}(String name, String defaultName) {{
    return {call}(name, defaultName);
}}'''

HOP1 = hop("includeKeyName", "DoubleOrderedMap.nameOfIncludeKey")
HOP2 = hop("nameOfIncludeKey", "MapUtils.getIncludeKeyName")
HOP3 = hop("getIncludeKeyName", "CursorableSubList.includeKeyNameFor")
HOP4 = hop("includeKeyNameFor", "AbstractHashedMap.resolveIncludeKey")

DESIGN = {
 "instance": "Collections-2", "project": "Collections", "bug_id": 2, "seed": 5781,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": EP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "getInclude", "near_line": 513},
 "facade_variant": "V1",
 "state_passed": "private field includePropertyName and protected static field include (String values) to hop 1; no write-back",
 "reachability_probe": "testInclude fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "ExtendedProperties.getInclude(ExtendedProperties.java:514) from TestExtendedProperties.java:320",
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/TestExtendedProperties.java",
             "test_class": "org.apache.commons.collections.TestExtendedProperties", "test_method": "testInclude"},
 "expected_signature": "expected:<null> but was:<>",
 "gold": {"method": "resolveIncludeKey", "text": GOLD_TEXT,
          "fault": {"old": "        if (name == null) {\n"
                           "            return defaultName;\n"
                           "        }\n"
                           "        if (name.length() == 0) {\n"
                           "            return null;\n"
                           "        }\n",
                    "new": "        if (name == null) {\n"
                           "            return defaultName;\n"
                           "        }\n"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.includeKeyName(includePropertyName, include);",
   "lie": "The name is first looked up among the properties already loaded, and the stored name is consulted only when none of "
          "them defines it.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "includeKeyName",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "nameOfIncludeKey",
      "imports": [], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "getIncludeKeyName",
      "imports": [], "text": HOP3},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "includeKeyNameFor",
      "imports": ["org.apache.commons.collections.map.AbstractHashedMap"], "text": HOP4},
     {"file": AHM, "class": "org.apache.commons.collections.map.AbstractHashedMap", "method": "resolveIncludeKey", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.ExtendedProperties::setInclude",
              "org.apache.commons.collections.ExtendedProperties::load"],
 "ownership_reason": "Only the gold decides which name a configuration has for the property that includes other properties "
                     "files (the default name while none has been set, none for an empty name, else the name set); hops 1-4 "
                     "hand the two names on unchanged. The convention is pinned outside the gold: ExtendedProperties.setInclude "
                     "documents 'empty converted to null' (and stores the empty string for null), and ExtendedProperties.load "
                     "treats a null include name as no inclusion, ignores empty values and never reads an empty key, so the "
                     "empty string is never the name of a property that includes other files. With the variant gold (the name "
                     "set if not null, else the default name) the trigger's null for an empty name can only come out of the gold "
                     "if both names it is given are null, and every hop and the gold document the default name as not null, so "
                     "no hop can produce it while every method on the path is used as documented; an early answer or a rewrite "
                     "of the result at a hop re-implements the gold's decision (recorded bypasses). Passing tests drive the "
                     "chain on the default path through load().",
 "ownership_tests": ["org.apache.commons.collections.TestExtendedProperties::testSaveAndLoad",
                     "org.apache.commons.collections.TestExtendedProperties::testTrailingBackSlash",
                     "org.apache.commons.collections.TestExtendedProperties::testMultipleSameKey1"],
 "compensating": {
   "chain": [
     {"file": TBM, "old": "return DoubleOrderedMap.nameOfIncludeKey(name, defaultName);",
      "new": "return DoubleOrderedMap.nameOfIncludeKey(\"\".equals(name) ? null : name, defaultName);",
      "why": "hop 1 passes an empty name on as no name"},
     {"file": DOM, "old": "return MapUtils.getIncludeKeyName(name, defaultName);",
      "new": "return MapUtils.getIncludeKeyName(name == null ? defaultName : name, defaultName);",
      "why": "hop 2 passes the default name in place of a missing name"},
     {"file": CLL, "old": "return AbstractHashedMap.resolveIncludeKey(name, defaultName);",
      "new": "return AbstractHashedMap.resolveIncludeKey(\"\".equals(name) ? null : name, \"\".equals(name) ? \"\" : defaultName);",
      "why": "hop 4 passes an empty name on as no name with an empty default"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are hosts_hop_order of the task record (batch8_tasks.json), in that order: "
               "bidimap.TreeBidiMap (hop 1, 2084 lines), DoubleOrderedMap (hop 2, 1994), MapUtils (hop 3, 1644), "
               "CursorableLinkedList.java (hop 4, 1467); the fifth listed host FastArrayList (1332) cannot carry an added "
               "static method: it is Serializable without a declared serialVersionUID, so any added method changes its "
               "computed serialVersionUID and the existing serialization-compatibility tests (TestFastArrayList and "
               "TestFastArrayList1 ::testEmptyListCompatibility / ::testFullListCompatibility, which read the stored "
               "data/test/FastArrayList.*.obj files) fail on the CORRECT configuration (checked by validation, gate G1). "
               "It is replaced by the next-largest public, non-interface, non-enum class other than the facade's file, "
               "map.AbstractHashedMap (hop 5, gold, 1328 lines; the smallest host; not Serializable itself, so no stored form "
               "depends on its members). Anchors from "
               "stageB_lib.pick_anchor / host_search.pick_insertion_anchor with seed 5781 + 100 + i (as mr3_spec.py inserts them): "
               "hop 1 after `entrySet` (line idx 397, seed 5881), hop 2 after `put` (1421, 5882), hop 3 after `getMap` (346, 5883), "
               "hop 4 after `iterator` (1248, 5884), hop 5 after `put` (285, 5885; outer class of AbstractHashedMap). The hop-4 anchor lies in the file's "
               "second top-level class CursorableSubList (package-private, extends CursorableLinkedList), so hop 4 is a member of "
               "CursorableSubList; it compiles because its caller MapUtils is in the same package; the public class of the file "
               "could carry the method, so no substitution applies and the recipe's anchor is kept. The other anchors are "
               "outer-class members (DoubleOrderedMap is deprecated, which does not affect a static method). The facade calls "
               "hop 1 by its fully-qualified name; TreeBidiMap imports DoubleOrderedMap and CursorableLinkedList.java imports "
               "map.AbstractHashedMap; hops 2-4 share the package org.apache.commons.collections. The facade's class ExtendedProperties is not a host.",
}
