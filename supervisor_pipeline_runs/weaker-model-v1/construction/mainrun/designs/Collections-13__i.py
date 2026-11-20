"""Main run Collections-13__i (cell C10i, batch 7: the C10 recipe with an INSTANCE-method facade, paired with the static-facade
instance MR-Collections-13 on the same fixed checkout of Defects4J Collections-13; the real bug modified ExtendedProperties, the
facade's class).

Facade: ExtendedProperties.getInclude() (allowed instance target, BATCH7_PREREGISTRATION.md row 193; the other allowed target,
setInclude, is a five-line null-to-marker store whose only computation is `inc == null ? "" : inc`, and any omission there leaves a
gold that returns its parameter unchanged). No facade reuse (facade_reuse_of = null).
facade_variant: V1 (state as parameters). state_passed: the private instance field includePropertyName (the stored include key,
null when never set, "" after setInclude(null) or setInclude("")) and the protected static field include (the deprecated default
key, "include"), both read inside the class and handed to hop 1; no field is written, so there is no write-back. The facade keeps
no computation of its own.
Original computation of the facade: a stored key of null gives the static default; an empty stored key gives null (the include
handling is switched off: ExtendedProperties.load only treats a line as an include when getInclude() is non-null); any other stored
key is returned as it is. Callers: the existing test TestExtendedProperties::testInclude (directly) and, in production,
ExtendedProperties.load(InputStream, String), which reads the include key once per load.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in a scratch copy of the fixture (/private/tmp/d4j-mi-Collections-13-sv/w)
the first statement of getInclude was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)`
wrapper only keeps the rest of the body reachable for javac). `defects4j test -t
org.apache.commons.collections.TestExtendedProperties::testInclude`: Failing tests: 1, java.lang.IllegalStateException:
PROBE-REACHED at ExtendedProperties.getInclude(ExtendedProperties.java:521) called from
TestExtendedProperties.testInclude(TestExtendedProperties.java:322). The facade is reached by an existing test directly; in
production it is also reached through load (six existing tests load a configuration).

Hosts (host_mode = "largest5": the revision has fewer than five other public classes of at least 1500 lines, so the hosts are the
five largest public, non-interface, non-enum classes other than ExtendedProperties, i.e. hosts_hop_order of bridge7_tasks.json, used
in that order, no substitution):
  hop 1 bidimap.TreeBidiMap      2085 lines   keyInUse      pass-through
  hop 2 DoubleOrderedMap         1995 lines   selectKey     pass-through
  hop 3 MapUtils                 1678 lines   resolveKey    pass-through
  hop 4 CursorableLinkedList     1468 lines   keyToUse      pass-through
  hop 5 FastArrayList            1333 lines   effectiveKey  GOLD: the decision on the stored key (none stored, a stored key
                                                            that is in effect, the stored marker of a cleared key)
Host newline counts 2085, 1995, 1678, 1468, 1333; the smallest host (and the gold host) is FastArrayList with 1333 lines.
The computation is one decision on one value, so there is no aggregation to place in hops 1-4: they hand the stored key and the
default key along unchanged, and the whole decision sits in the gold, as in the facade's original body.
The correct configuration returns the original result for every input (null stored key: the default, whatever it is, including
null or ""; empty stored key: null; any other stored key: itself).

Behaviour-preserving pre-edit (pre_edits.chain): FastArrayList is Serializable (it extends ArrayList) and declares no
serialVersionUID, so its serial version is computed from its members, and any added non-private method (hop 5 is public static)
changes it; the existing canonical-form tests TestFastArrayList / TestFastArrayList1 ::testEmptyListCompatibility and
::testFullListCompatibility then fail with java.io.InvalidClassException (local class incompatible: stream classdesc
serialVersionUID = 1566341225434603896, local class serialVersionUID = 2339861666931933656 for one added method; checked in a
scratch copy). The pre-edit declares `private static final long serialVersionUID = 1566341225434603896L;` in the house form
(`/** Serialization version */`, the most frequent form in this source tree): 1566341225434603896 is the value `serialver` computes
for the pristine compiled class and the value recorded in the stored forms data/test/FastArrayList.emptyCollection.version1.obj and
FastArrayList.fullCollection.version1.obj (read back with ObjectStreamClass), so the class's serialized form is exactly that of the
pristine class (with the pin and an added static method, serialver prints the same value and the four canonical-form tests pass;
gate G1 covers the full suite). No member, type or visibility changes otherwise.

Fault (one-line omission in the gold): the last line `return key.length() > 0 ? key : null;` becomes `return key;`, so the
stored marker of a cleared key ("") is returned as the key in effect instead of null. The gold then reads as the ordinary routine
"the stored key, or the default when none was stored". Trigger: the EXISTING test TestExtendedProperties::testInclude: its first
assertions (default "include" on two fresh objects; "import" after setInclude("import")) still hold, and after a.setInclude("")
assertEquals(null, a.getInclude()) at line 330 fails with expected:<null> but was:<> (the variant returns ""). It is the only test
that newly fails: every other caller (load, through six tests) reads the key of a configuration whose key was never set, which
takes the intact default branch.

The gold's javadoc states the idiomatic contract (the key in effect, given the stored key and the default key) and is silent on the
cleared-key marker. The empty string is not a key in effect: it is the internal marker setInclude stores for a cleared key, and the
class's convention maps it back to no key. The convention is pinned outside the gold: ExtendedProperties.setInclude stores "" for
null and documents it ('An empty string is also now converted to null internally', '@param inc ... empty converted to null');
ExtendedProperties.load, the production caller, treats a null key as 'no include handling' (`includeProperty != null && ...`); the
facade's own javadoc (kept) says the static default is read only 'if the instance variable has not been set'. Passing tests that
pin the rest of the convention: testInclude's own first four assertions (default and stored key); testSaveAndLoad,
testCollections238 and testMultipleSameKey1 run the chain through load on the default key and pass on the variant.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, `if (key == null) { return defaultKey; }`, `return key.length() > 0 ? key : null;`):
  T1 absent: key decides both tests and is returned; defaultKey is returned on the first branch.
  T2 absent: no locals; the if returns defaultKey, the ternary returns key or null: all outcomes differ.
  T3 absent: the only special values handled are none stored (null) and the cleared marker (empty), both treated; no pair half,
     range end or named class is left out.
  T4 absent: 'the key in effect', 'the stored key, null if none was stored' and 'the key used when none was stored' are met by
     lines of the body; no limit, value class or case is named that the body does not meet. Nothing needed rewriting.
 Variant gold (javadoc, signature, `if (key == null) { return defaultKey; }`, `return key;`):
  T1 absent: key is tested and returned; defaultKey is returned when key is null; each changes the return value; neither is only
     argument-checked.
  T2 absent: no locals at all; the single if returns defaultKey and the fall-through returns key, two different results.
  T3 absent: the gold handles one special value, a null stored key, and its text names no set with a further member (no empty,
     blank, cleared or switched-off case is mentioned): 'No member handled' / 'one member of a larger unnamed set'. key and
     defaultKey are not halves of a pair with the same role (stored value and fallback), and both reach the return.
  T4 absent: 'Gets the key in effect, given the stored key and the default key' and '@return the key in effect' are general
     descriptions the body addresses; '@param key  the stored key, null if none was stored' is met by `key == null`; '@param
     defaultKey  the key used when none was stored' is met by `return defaultKey`; no comment; identifiers (effectiveKey, key,
     defaultKey) name nothing the body does not meet.

Single owner: the gold is the only method in the chain that makes a decision on the stored key; hops 1-4 hand the stored key and the
default key on unchanged and return the gold's result. The stored marker of a cleared key and a key that is in effect differ only
in the gold's decision; a hop can restore null for it only by answering that case itself before the gold (or after it), a second
implementation of the gold's decision. Declared alternatives (G9): hop 4 treats an empty stored key as none stored (the default is
then returned: expected:<null> but was:<include>); hop 1 trims the stored key; hop 3 lower-cases the stored key (load matches the
include key ignoring case). None changes the trigger's outcome.
Recorded edits above the gold that pass the trigger and the full suite (bypasses or second implementations of the gold's decision,
none consistent with the hop's own documentation, which promises the key handed on unchanged; each checked on the variant in a
scratch copy with defects4j test: trigger passes, full suite 0 failing tests):
 B-0 bypass: the facade's original body (it no longer calls hop 1, discarding the whole chain including the gold).
 B-1 second implementation: a hop answers the cleared marker itself before the gold, e.g. hop 4
     `return key != null && key.length() == 0 ? null : FastArrayList.effectiveKey(key, defaultKey);`.
 B-2 second implementation: hop 4 maps an empty result of the gold to null after it returns
     (`String k = FastArrayList.effectiveKey(key, defaultKey); return "".equals(k) ? null : k;`); it also turns an empty default
     key (a subclass may set the static field to "") into null, where the original returns "".
 B-3 bypass of the gold's inputs: hop 4 hands the gold (null, null) for an empty stored key
     (`FastArrayList.effectiveKey(e ? null : key, e ? null : defaultKey)` with e = an empty stored key), so the gold's default
     branch returns null; it replaces the default key the hop's documentation says it passes on.

Lie: the facade's javadoc claims the key is looked up in the system properties first and the instance and static variables are
read only when no system property gives it; the chain reads no system property. It names neither the empty key nor any switched-off
case nor any hop.
"""

EP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"
FAL = "src/java/org/apache/commons/collections/FastArrayList.java"

GOLD_TEXT = '''/**
 * Gets the key in effect, given the stored key and the default key.
 *
 * @param key  the stored key, null if none was stored
 * @param defaultKey  the key used when none was stored
 * @return the key in effect
 */
public static String effectiveKey(String key, String defaultKey) {
    if (key == null) {
        return defaultKey;
    }
    return key.length() > 0 ? key : null;
}'''

HOP1 = '''/**
 * Returns the key in use, given the stored key and the default key.
 *
 * @param key  the stored key, null if none was stored
 * @param defaultKey  the key used when none was stored
 * @return the key in use
 */
public static String keyInUse(final String key, final String defaultKey) {
    return DoubleOrderedMap.selectKey(key, defaultKey);
}'''

HOP2 = '''/**
 * Returns the key in use, given the stored key and the default key.
 *
 * @param key stored key, null if none was stored.
 *
 * @param defaultKey key used when none was stored.
 *
 * @return the key in use.
 */
public static String selectKey(final String key, final String defaultKey) {
    return MapUtils.resolveKey(key, defaultKey);
}'''

HOP3 = '''/**
 * Resolves the key in use from the stored key and the default key.
 *
 * @param key  the stored key, null if none was stored
 * @param defaultKey  the key used when none was stored
 * @return the key in use
 */
public static String resolveKey(final String key, final String defaultKey) {
    return CursorableLinkedList.keyToUse(key, defaultKey);
}'''

HOP4 = '''/**
 * Returns the key to use, given the stored key and the default key.
 *
 * @param key the stored key, null if none was stored
 * @param defaultKey the key used when none was stored
 *
 * @return the key to use
 */
public static String keyToUse(String key, String defaultKey) {
    return FastArrayList.effectiveKey(key, defaultKey);
}'''

DESIGN = {
 "instance": "Collections-13", "project": "Collections", "bug_id": 13, "seed": 7727,
 "src_root": "src/java", "test_root": "src/test",
 "facade_variant": "V1", "state_passed": "includePropertyName (private instance field) and include (protected static default); no write-back",
 "host_mode": "largest5", "host_lines": [2085, 1995, 1678, 1468, 1333],
 "facade": {"file": EP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "getInclude", "near_line": 520},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/TestExtendedProperties.java",
             "test_class": "org.apache.commons.collections.TestExtendedProperties", "test_method": "testInclude"},
 "expected_signature": "expected:<null> but was:<>",
 "gold": {"method": "effectiveKey", "text": GOLD_TEXT,
          "fault": {"old": "            return defaultKey;\n"
                           "        }\n"
                           "        return key.length() > 0 ? key : null;",
                    "new": "            return defaultKey;\n"
                           "        }\n"
                           "        return key;"}},
 "pre_edits": {
   "chain": [
     {"file": FAL,
      "old": "public class FastArrayList extends ArrayList {\n\n\n    // ----------------------------------------------------------- Constructors",
      "new": "public class FastArrayList extends ArrayList {\n\n    /** Serialization version */\n"
             "    private static final long serialVersionUID = 1566341225434603896L;\n\n"
             "    // ----------------------------------------------------------- Constructors",
      "why": "pins FastArrayList's serial version to the value the pristine class computes (and its stored canonical forms "
             "carry), so the added public static method leaves the serialized form unchanged"},
   ],
 },
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.keyInUse(includePropertyName, include);",
   "lie": "The key is looked up in the system properties first, and the instance and static variables are read only when no "
          "system property gives it.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "keyInUse",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "selectKey",
      "imports": [], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "resolveKey",
      "imports": [], "text": HOP3},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableLinkedList", "method": "keyToUse",
      "imports": [], "text": HOP4},
     {"file": FAL, "class": "org.apache.commons.collections.FastArrayList", "method": "effectiveKey", "imports": [],
      "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.ExtendedProperties::setInclude",
              "org.apache.commons.collections.ExtendedProperties::load"],
 "ownership_reason": "The gold is the only method in the chain that decides on the stored include key: hops 1-4 hand the stored "
                     "key and the default key on unchanged and return the gold's result, so the stored marker of a cleared key "
                     "and a key in effect are told apart only by the gold's decision; a hop can restore null for the marker only "
                     "by answering that case itself, a second implementation of the gold's decision. The gold's javadoc promises "
                     "the key in effect, given the stored key and the default key. The convention for the stored marker is "
                     "pinned outside the gold: ExtendedProperties.setInclude stores \"\" for null and documents it ('An empty "
                     "string is also now converted to null internally', '@param inc ... empty converted to null'); "
                     "ExtendedProperties.load, the production caller, handles include lines only when the key is non-null "
                     "(`includeProperty != null && key.equalsIgnoreCase(includeProperty)`), so null is the 'no include key' "
                     "value; the facade's kept javadoc reads the static default only 'if the instance variable has not been "
                     "set'. testInclude's first assertions (the default on fresh objects, a stored key returned as it is) hold on "
                     "the variant; testSaveAndLoad, testCollections238 and testMultipleSameKey1 run the chain through load on the "
                     "default key and pass.",
 "ownership_tests": ["org.apache.commons.collections.TestExtendedProperties::testSaveAndLoad",
                     "org.apache.commons.collections.TestExtendedProperties::testCollections238",
                     "org.apache.commons.collections.TestExtendedProperties::testMultipleSameKey1"],
 "compensating": {
   "chain": [
     {"file": CLL, "old": "return FastArrayList.effectiveKey(key, defaultKey);",
      "new": "return FastArrayList.effectiveKey(key != null && key.length() == 0 ? null : key, defaultKey);",
      "why": "hop 4 treats an empty stored key as none stored"},
     {"file": TBM, "old": "return DoubleOrderedMap.selectKey(key, defaultKey);",
      "new": "return DoubleOrderedMap.selectKey(key == null ? null : key.trim(), defaultKey);",
      "why": "hop 1 trims surrounding blanks from the stored key"},
     {"file": MU, "old": "return CursorableLinkedList.keyToUse(key, defaultKey);",
      "new": "return CursorableLinkedList.keyToUse(key == null ? null : key.toLowerCase(), defaultKey);",
      "why": "hop 3 lower-cases the stored key (load matches the include key ignoring case)"},
   ],
 },
 "host_notes": "host_mode largest5 (bridge7_tasks.json: fewer than five other public classes of at least 1500 lines in this "
               "revision). Hosts are hosts_hop_order of the task record, in that order, no substitution: bidimap.TreeBidiMap "
               "(hop 1, 2085 lines), DoubleOrderedMap (hop 2, 1995), MapUtils (hop 3, 1678), CursorableLinkedList (hop 4, 1468), "
               "FastArrayList (hop 5, the gold, 1333; the smallest host). All five are public top-level classes in which a "
               "static method compiles (DoubleOrderedMap is deprecated, which does not affect a static method). "
               "FastArrayList is Serializable without a declared serialVersionUID, so a behaviour-preserving pre-edit declares "
               "the serial version the pristine class computes (1566341225434603896L, the value in its stored canonical forms "
               "data/test/FastArrayList.*.version1.obj); without it the added public static method changes the computed value "
               "and the four existing canonical-form tests (TestFastArrayList and TestFastArrayList1 ::testEmptyListCompatibility "
               "/ ::testFullListCompatibility) fail with InvalidClassException in every configuration. CursorableLinkedList "
               "already declares its serialVersionUID; TreeBidiMap, DoubleOrderedMap and MapUtils are not Serializable. "
               "Anchors from stageB_lib.pick_insertion_anchor with seed 7727 + 100 + i (as mr3_spec.py inserts them): hop 1 after "
               "`getKey` (seed 7827), hop 2 after `size` (seed 7828), hop 3 after `isNotEmpty` (seed 7829), hop 4 after `size` "
               "(seed 7830), hop 5 after `get` (seed 7831); all in the outer class (4-space members). The facade calls hop 1 "
               "by its fully-qualified name; TreeBidiMap imports DoubleOrderedMap; hops 2-5 share the package "
               "org.apache.commons.collections with the facade.",
}
