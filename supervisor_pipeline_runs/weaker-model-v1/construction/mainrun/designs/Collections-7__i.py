"""Main run Collections-7__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Collections-7, a bug without a static facade; the real bug modified ExtendedProperties, the facade's class). No static pair (B8 note
section 1).

Facade: ExtendedProperties.getInclude() (the only allowed candidate of the task record, BATCH8_PREREGISTRATION.md row 226). Its
facade_planned_by is Collections-2__i (facade_reuse_of Collections-2__i, Collections-13__i): no candidate with facade_planned_by = null
exists, so the planned-elsewhere candidate is used, as the B8 note section 3 allows; nothing of those tasks was opened.
Original computation of the facade: the private instance field includePropertyName null (never set) gives the protected static field
include (default "include"); an empty includePropertyName (what setInclude stores for null or "") gives null; any other value is
returned as it is.

facade_variant: V1 (state as parameters). The method reads two fields and writes none: the facade reads the private instance field
includePropertyName and the protected static field include (inside ExtendedProperties, so no visibility change) and passes the two
String values to hop 1, returning hop 1's result. The chain needs no method of the receiver (V2 not needed), calls no private method
(no V4), and no package-private type is involved (no V3/V5). No signature, modifier, override or throws change; no new type; no
reflection; no test edit.
state_passed: the private instance field includePropertyName and the protected static field include (String values) to hop 1; no
write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-7-probe/w of the
fixture, the first statement of getInclude was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t org.apache.commons.collections.TestExtendedProperties::testInclude`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at ExtendedProperties.getInclude(ExtendedProperties.java:516) called from
TestExtendedProperties.testInclude(TestExtendedProperties.java:322). `...::testSaveAndLoad`: 1 failing test, PROBE-REACHED at
ExtendedProperties.getInclude(516) from ExtendedProperties.load(585) <- load(551). The facade is reached by an existing test directly
(testInclude) and through its production caller load(InputStream, String).

Hosts (host_mode = "largest5"; hosts_hop_order of the task record, in that order, with ONE substitution; anchors from
stageB_lib.pick_insertion_anchor with seed 5812 + 100 + i, as mr3_spec.py inserts them, recorded in host_notes):
  hop 1 bidimap.TreeBidiMap        2085 lines  settingName          pass-through
  hop 2 DoubleOrderedMap           1995 lines  resolveSettingName   pass-through
  hop 3 MapUtils                   1645 lines  getSettingName       pass-through
  hop 4 CursorableLinkedList.java  1468 lines  currentSettingName   pass-through (the seeded anchor `addFirst` lies in the file's
                                                                    second top-level class CursorableSubList, package-private,
                                                                    which extends CursorableLinkedList; the hop is a public static
                                                                    method of that class and hop 3, in the same package, calls it
                                                                    as CursorableSubList.currentSettingName)
  hop 5 map.AbstractHashedMap      1329 lines  nameInEffect         GOLD: the decision between the default name (nothing stored), no
                                                                  name (an empty stored name) and the stored name
Substitution: the listed fifth host FastArrayList (1333 lines) cannot carry a public static method: it is Serializable without a
declared serialVersionUID, so any added public static method changes its computed serialVersionUID and the existing serialization
tests TestFastArrayList(1)::testEmptyListCompatibility/testFullListCompatibility (against data/test/FastArrayList.*.version1.obj) fail
in the CORRECT configuration (gate G1 failed on the first build). It is replaced by the next-largest public, non-interface, non-enum
class outside the facade's file and the other four hosts: map.AbstractHashedMap (1329 lines; not Serializable itself, and a
computed serialVersionUID covers only a class's own members, so its serialised subclasses are unaffected).
Host newline counts 2085, 1995, 1645, 1468, 1329; the smallest host is AbstractHashedMap (1329 lines), which is also the gold host.
The correct configuration returns exactly the original value for every state: stored null gives the static default, stored "" gives
null, any other stored name is returned.

Fault (one-line omission of a special-case decision in the gold): the `else if (name.length() == 0)` decision that turns an empty
stored name into no name is dropped, so a name cleared with setInclude("") or setInclude(null) is reported as "" instead of null. The
gold then reads as the ordinary house idiom "the stored value, or the default when nothing is stored" (as MapUtils.getString(Map,
Object, String) writes it). Trigger: the EXISTING test TestExtendedProperties::testInclude. Its first four assertions (default
"include" on both objects, "import" after setInclude("import")) still hold, and assertEquals(null, a.getInclude()) after
a.setInclude("") at line 330 fails with expected:<null> but was:<>. It is the only test that newly fails: setInclude is called by
no production code and by no other test, so the empty stored name occurs only in testInclude; every other caller of getInclude (load)
sees includePropertyName == null, for which the variant still returns the static default; the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the name in effect for a setting, given the stored name and the default) and is
silent on empty names; "" is not the name in effect for a setting that was cleared. The convention is pinned outside the gold:
ExtendedProperties.setInclude (javadoc "@param inc the property name which includes another property, empty converted to null", and
its body stores "" for null); ExtendedProperties.load(InputStream, String), which reads getInclude() once and treats null as "no
include key" (`includeProperty != null && key.equalsIgnoreCase(includeProperty)`); the facade's own javadoc (the static variable is
accessed only when the instance variable has not been set), kept unchanged; the passing load tests (testSaveAndLoad,
testMultipleSameKey1) pin the default branch through load.

Single owner: only the gold decides which name is in effect; hops 1-4 pass the stored name and the default along unchanged. The
variant gold returns the stored name itself for every non-null stored name, so a caller that changes the arguments cannot obtain null
for an empty name without discarding the gold: turning "" into null before the gold yields the default "include" (the trigger expects
null), and dropping or replacing the default changes nothing for a non-null stored name. Declared alternatives (G9): hop 3 converts an
empty stored name to null before passing it on; hop 1 passes the default only when nothing is stored; hop 2 trims the stored name.
Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's decision with another implementation, not repairs of the chain):
 B-1 a hop (or the facade) answers the empty name itself before or after the gold (`if ("".equals(stored)) { return null; }` ahead
     of the delegation, or `"".equals(n) ? null : n` on the gold's result): a second implementation of the gold's decision; the gold
     still returns "" for an empty stored name. Checked at hop 4 on the variant in a scratch copy: trigger passes, full suite 0
     failing tests.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the name is found by searching the keys in the order they were listed for the first one marked as
the include key, the static default being returned only when that search finds none; the chain searches no key list (it decides on
the stored value alone). It names neither empty names, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (name = stored; null -> standard, else empty -> null; return name):
  T1 absent: stored seeds name and is returned for an ordinary stored name; standard is returned when nothing is stored; neither is
     only argument-checked (the gold has no argument check).
  T2 absent: name is assigned from stored, reassigned in both decisions and returned; it is not literal-initialised; there is no
     loop; the two decisions have different effects (the default, no name) from the fall-through.
  T3 absent: the treatments are of the stored name only; no enum, type code or named format is involved; the gold's text names no
     value class.
  T4 absent: 'the name in effect for a setting, given the name stored for it and the name it has by default' is a general
     description addressed by the body; the @param/@return clauses name no rule, limit or value class; no inline comment.
 Variant gold (javadoc, signature, `String name = stored;`, `if (name == null) { name = standard; }`, `return name;`):
  T1 absent: stored seeds name, which is returned whenever stored is not null; standard is assigned to name and returned when stored
     is null, so its value is the result on that path (the test is not an argument check: its branch computes the result, it neither
     throws nor returns early).
  T2 absent: name is assigned from stored, reassigned by the decision and returned; not literal-initialised; no loop, cursor,
     counter, flag or best-so-far; the decision changes the returned value.
  T3 absent: exactly one treatment (nothing stored -> default) of the stored name; no sibling member of a closed set is handled
     ('No member handled' for every other value class): the gold's text names no class (no "empty", "blank", "cleared", "valid"),
     no enum or type code, no named format; the two parameters are not a pair or range whose halves get unequal treatment (one is a
     stored value, the other its default, as in MapUtils.getString).
  T4 absent: 'Gets the name in effect for a setting, given the name stored for the setting and the name it has by default' is a
     general description met by the decision; '@param stored  the name stored for the setting', '@param standard  the name the
     setting has by default' and '@return the name in effect' name no concrete rule, limit, bound or value class; no inline comment;
     the identifiers name, stored and standard name what they hold."""

EP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"
AHM = "src/java/org/apache/commons/collections/map/AbstractHashedMap.java"

GOLD_TEXT = '''/**
 * Gets the name in effect for a setting, given the name stored for the
 * setting and the name it has by default.
 *
 * @param stored  the name stored for the setting
 * @param standard  the name the setting has by default
 * @return the name in effect
 */
public static String nameInEffect(String stored, String standard) {
    String name = stored;
    if (name == null) {
        name = standard;
    } else if (name.length() == 0) {
        name = null;
    }
    return name;
}'''

HOP1 = '''/**
 * Gets the name in effect for a setting, given the name stored for the
 * setting and the name it has by default.
 *
 * @param stored  the name stored for the setting
 * @param standard  the name the setting has by default
 * @return the name in effect
 */
public static String settingName(final String stored, final String standard) {
    return DoubleOrderedMap.resolveSettingName(stored, standard);
}'''

HOP2 = '''/**
 * Resolves the name in effect for a setting, given the name stored
 * for the setting and the name it has by default.
 *
 * @param stored the name stored for the setting
 * @param standard the name the setting has by default
 *
 * @return the name in effect
 */
public static String resolveSettingName(final String stored, final String standard) {
    return MapUtils.getSettingName(stored, standard);
}'''

HOP3 = '''/**
 * Gets the name in effect for a setting, given the name stored for the
 * setting and the name it has by default.
 *
 * @param stored  the name stored for the setting
 * @param standard  the name the setting has by default
 * @return the name in effect
 */
public static String getSettingName(final String stored, final String standard) {
    return CursorableSubList.currentSettingName(stored, standard);
}'''

HOP4 = '''/**
 * Returns the name currently in effect for a setting, given the name
 * stored for the setting and the name it has by default.
 *
 * @param stored the name stored for the setting
 * @param standard the name the setting has by default
 * @return the name in effect
 */
public static String currentSettingName(String stored, String standard) {
    return AbstractHashedMap.nameInEffect(stored, standard);
}'''

DESIGN = {
 "instance": "Collections-7", "project": "Collections", "bug_id": 7, "seed": 5812,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": EP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "getInclude", "near_line": 515},
 "facade_variant": "V1",
 "state_passed": "private instance field includePropertyName and protected static field include (String values) to hop 1; no "
                 "write-back",
 "reachability_probe": "testInclude fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "ExtendedProperties.getInclude(ExtendedProperties.java:516) from TestExtendedProperties.java:322; "
                       "testSaveAndLoad fails with PROBE-REACHED at getInclude(516) from ExtendedProperties.load(585)",
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/TestExtendedProperties.java",
             "test_class": "org.apache.commons.collections.TestExtendedProperties", "test_method": "testInclude"},
 "expected_signature": "expected:<null> but was:<>",
 "gold": {"method": "nameInEffect", "text": GOLD_TEXT,
          "fault": {"old": "        if (name == null) {\n"
                           "            name = standard;\n"
                           "        } else if (name.length() == 0) {\n"
                           "            name = null;\n"
                           "        }\n",
                    "new": "        if (name == null) {\n"
                           "            name = standard;\n"
                           "        }\n"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.settingName(includePropertyName, include);",
   "lie": "The name is found by searching the keys in the order they were listed for the first one marked as the include key, "
          "and the static default is returned only when that search finds none.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "settingName",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "resolveSettingName",
      "imports": [], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "getSettingName",
      "imports": [], "text": HOP3},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "currentSettingName",
      "imports": ["org.apache.commons.collections.map.AbstractHashedMap"], "text": HOP4},
     {"file": AHM, "class": "org.apache.commons.collections.map.AbstractHashedMap", "method": "nameInEffect", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.ExtendedProperties::setInclude",
              "org.apache.commons.collections.ExtendedProperties::load",
              "org.apache.commons.collections.MapUtils::getString"],
 "ownership_reason": "Only the gold decides which name is in effect (the default when nothing is stored, no name for an empty "
                     "stored name, otherwise the stored name); hops 1-4 pass the stored name and the default along unchanged. "
                     "The gold's javadoc promises the name in effect for the setting, which \"\" is not for a setting cleared "
                     "with setInclude(\"\") or setInclude(null). No one-line change of the two Strings above the gold restores "
                     "it: the variant gold returns any non-null stored name as it is, so an empty name can become null only by "
                     "discarding the gold's result, and turning the empty name into null before the gold yields the default "
                     "\"include\". The convention is pinned outside the gold: ExtendedProperties.setInclude ('empty converted to "
                     "null'; it stores \"\" for null), ExtendedProperties.load(InputStream, String), which treats a null include "
                     "name as no include key, the facade's own javadoc (the static variable is used only when the instance "
                     "variable has not been set), and MapUtils.getString(Map, Object, String) for the default idiom; the passing "
                     "load tests testSaveAndLoad and testMultipleSameKey1 pin the default branch through load.",
 "ownership_tests": ["org.apache.commons.collections.TestExtendedProperties::testSaveAndLoad",
                     "org.apache.commons.collections.TestExtendedProperties::testMultipleSameKey1"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "return CursorableSubList.currentSettingName(stored, standard);",
      "new": "return CursorableSubList.currentSettingName(\"\".equals(stored) ? null : stored, standard);",
      "why": "hop 3 converts an empty stored name to null before passing it on"},
     {"file": TBM, "old": "return DoubleOrderedMap.resolveSettingName(stored, standard);",
      "new": "return DoubleOrderedMap.resolveSettingName(stored, stored == null ? standard : null);",
      "why": "hop 1 passes the default only when nothing is stored"},
     {"file": DOM, "old": "return MapUtils.getSettingName(stored, standard);",
      "new": "return MapUtils.getSettingName(stored == null ? null : stored.trim(), standard);",
      "why": "hop 2 trims the stored name"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are hosts_hop_order of the task record, in that order, with one substitution: "
               "bidimap.TreeBidiMap (hop 1, 2085 lines; anchor after `mapIterator`, seed 5912), DoubleOrderedMap (hop 2, 1995; "
               "public final, which does not affect a static method; after `size`, 5913), MapUtils (hop 3, 1645; after "
               "`getLongValue`, 5914), CursorableLinkedList.java (hop 4, 1468; after `addFirst`, 5915: that anchor lies in the "
               "file's second top-level class CursorableSubList, package-private, extending CursorableLinkedList, so hop 4 is "
               "CursorableSubList.currentSettingName and hop 3, in the same package, calls it by that class), "
               "map.AbstractHashedMap (hop 5, gold, 1329; after `size`, 5916, in the outer class; the smallest host). "
               "SUBSTITUTED: the listed fifth host FastArrayList (1333 lines) is Serializable without a declared "
               "serialVersionUID, so an added public static method changes its computed serialVersionUID and the existing "
               "tests TestFastArrayList::testEmptyListCompatibility/testFullListCompatibility and the same two in "
               "TestFastArrayList1 fail in the correct configuration (G1 failed on the first build); it cannot carry a public "
               "static method, and the next-largest public class outside the facade's file and the other hosts, "
               "map.AbstractHashedMap (1329 lines), takes hop 5. The facade calls hop 1 by its fully-qualified name; hop 1 "
               "imports DoubleOrderedMap; hop 4's file imports map.AbstractHashedMap; hops 2-4 share the package "
               "org.apache.commons.collections. The facade's class ExtendedProperties (facade_files_excluded) is not a host.",
}
