"""Main run Collections-10__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout
of Defects4J Collections-10; the real bug modified org.apache.commons.collections.map.MultiValueMap, the facade's class). No static
pair (BUILD_BRIEF_C10I_B8_NOTE.md section 1: pool v2 found no tested public static method in MultiValueMap).

Facade: MultiValueMap.removeMapping(Object key, Object value), the only allowed candidate of the task record, listed there as
"MultiValueMap.remove" (13 lines, receiver calls AbstractMapDecorator.remove and MultiValueMap.getCollection). The pool profile read
the upstream revision e6d4f465, where this method (lines 190-203, same body) is still called remove(Object, Object); the Defects4J
commit D4J_Collections_10_POST_FIX_COMPILABLE renamed it to removeMapping, the name it has in the fixture (and in the MultiMap
interface it implements). Same declaration lines, same body: it is the allowed candidate, not another method. facade_planned_by =
Collections-4__i (facade reuse, recorded; it is the only candidate, so there was nothing distinct to prefer).
Original computation: getCollection(key); no collection gives null; Collection.remove(value); nothing removed gives null; a collection
left empty has its key removed with remove(key); otherwise the passed-in value is returned.

facade_variant: V2 (receiver as parameter). The computation needs the object's public methods only (the map lookup of the key's
collection and the removal of the key); the facade passes `this`, typed as java.util.Map (an interface MultiValueMap implements through
AbstractMapDecorator), with the two arguments to hop 1, and returns hop 1's result. The hops call only public Map methods of the
receiver: containsKey and get (MultiValueMap inherits both from AbstractMapDecorator; get returns the same Collection as
getCollection, which is a cast of getMap().get(key)) and remove(key) (AbstractMapDecorator.remove, the call the original makes). No
private method is called (no V4), no package-private type or member is involved (no V3/V5), no field is read or written (no V1). No
signature, modifier, override or throws change; no new type; no reflection; no test edit.
state_passed: the receiver `this` (as java.util.Map) plus key and value to hop 1; no write-back (the receiver's own remove(key) is the
only side effect besides the removal from the key's collection).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-10-probe/w of the
fixture, the first statement of removeMapping was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. Full suite
(`defects4j test`, 13 s): 5 failing tests, all java.lang.IllegalStateException: PROBE-REACHED at
MultiValueMap.removeMapping(MultiValueMap.java:191): TestMultiValueMap::testSize, testTotalSize, testRemove_KeyItem, testMapEquals,
testSize_Key (e.g. from TestMultiValueMap.testSize line 207). The facade is reached by existing tests directly; it has no production
caller.

Hosts (host_mode = "largest5"): EXACTLY hosts_hop_order of the task record, in that order, none substituted (all five are public
top-level concrete classes in which a public static method compiles):
  hop 1 bidimap.TreeBidiMap      2085 lines  removeMappedValue  decision: a key the map does not contain gives null (the
                                                                original's first case)
  hop 2 DoubleOrderedMap         1995 lines  removeValueOf      pass-through
  hop 3 ExtendedProperties       1776 lines  removeKeyValue     pass-through
  hop 4 MapUtils                 1645 lines  removeMultiValue   pass-through
  hop 5 CursorableLinkedList     1468 lines  removeFromValues   GOLD: looks the key's collection up, removes the value from it,
                                                                decides the result, and removes the key once its collection is empty
Host newline counts 2085, 1995, 1776, 1645, 1468; the smallest host (and the gold host) is CursorableLinkedList (1468 lines; below
1500 lines, expected in the largest5 regime, BUILD_BRIEF_C10F_ADDENDUM section 1).
The correct configuration returns exactly what the original returns for every MultiValueMap: the class keeps no key with a null or
empty collection (put and putAll only map a key to a non-empty collection, removeMapping and the values iterator remove a key whose
collection becomes empty), so containsKey(key) is false exactly when getCollection(key) is null.

Fault (one-line omission of a decision in the gold): the decision that answers null when the key's collection did not hold the value
is dropped; the removal call is kept as a plain statement (`values.remove(value);`). The gold then reads as the ordinary routine "look
the collection up, remove the value, drop the key once its collection is empty, return the value". Trigger: the EXISTING test
TestMultiValueMap::testRemove_KeyItem. Its first assertion (removeMapping("C", "CA") is null: hop 1's absent-key decision) still holds;
assertEquals(null, map.removeMapping("A", "AD")) at line 351 fails with expected:<null> but was:<AD>. It is the only test that newly
fails: the other four tests that reach the facade (probe) remove only values the collection holds (testSize, testTotalSize,
testSize_Key remove "BC" from [BA, BB, BC]; testMapEquals removes the only value of "One"), and the gold has no other caller.

The gold's javadoc states the idiomatic contract (removes a value from the collection held against a key, the other values are
unaffected, the key is removed once its last value has gone; "@return the value removed") and is silent on the case of a value the
collection does not hold; "AD" is not a value removed. The convention is pinned outside the gold: the MultiMap interface method
MultiMap.removeMapping ("@return the value removed (which was passed in), null if nothing removed"), its sibling implementation
MultiHashMap.removeMapping (which returns null when Collection.remove reports nothing removed) with TestMultiHashMap::testRemove_KeyItem
(removeMapping("A", "AD") is null) passing, and MultiValueMap.put, whose "null if the map did not change" is decided from the boolean
that Collection.add returns (TestMultiValueMap::testPutWithSet: a second put of "a" into a HashSet gives null); the facade's own
javadoc ("null if nothing removed") is kept unchanged.

Single owner: only the gold looks at the key's collection and removes from it; hops 2-4 pass the map, key and value along and hop 1
only answers a key the map does not contain. A one-line change of the arguments above the gold cannot make the gold report that the
value was not removed: the gold returns the value it was given on every path after the removal. Declared alternatives (G9): hop 1 also
answers null for an empty collection; hop 2 answers null for a null value; hop 4 tests the key again before calling the gold. Each
leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-1 a membership pre-filter above the gold, e.g. at hop 1
     `if (!map.containsKey(key) || !((Collection) map.get(key)).contains(value)) {` (or the same test inserted at hop 2, 3 or 4):
     it fetches the key's collection and tests membership itself, a second implementation of the gold's removal test placed in front
     of it, so the gold is not consulted for a value it does not hold; the gold still returns a value it did not remove whenever it is
     called with one. Checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests.
 B-0 the facade's original body (or a hop re-deriving the result from Collection.remove on the looked-up collection) re-implements the
     whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the collection mapped to the key is searched from its last value back to its first and the first
equal value found is removed; the chain searches nothing in reverse (it hands the value to the collection's own remove, which for the
default ArrayList scans from the first value). It names neither the result, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: map is read by get and by remove; key by get and by remove; value by values.remove and the return; none is only
     argument-checked (the gold has no argument check).
  T2 absent: the one local, values, is read by the removal decision, by isEmpty and is the receiver of remove; it is not
     literal-initialised; there is no loop, cursor, counter, flag or best-so-far; both decisions have effects (an early null return,
     a removal of the key).
  T3 absent: no enum, type code, named format or pair is handled in part; the key and the value are both used for what each is for
     (the key looks up and is removed, the value is removed and returned).
  T4 absent: "Removes a value from the collection that a map holds against a key", "Other values held against the key are
     unaffected" (a single Collection.remove) and "Once the last value has been removed, the key itself is removed from the map" (the
     isEmpty branch) are each met by a line; "@return the value removed" is met by the return; "not null" and "a key that the map
     holds a collection against" are caller preconditions.
 Variant gold (javadoc, signature, values = the key's collection, values.remove(value), the isEmpty branch removing the key, return
 value):
  T1 absent: map is read by get and by remove; key by get and by remove; value by values.remove and the return; each can change the
     result or a side effect.
  T2 absent: values is read by remove, by isEmpty and is the receiver of the removal; not literal-initialised; no loop; the one
     remaining decision removes the key or not.
  T3 absent: no closed set has a member treated while a sibling is not (no enum, type code, named format; the key and value are not
     a pair given the same treatment); no special-value test of any member remains ('No member handled').
  T4 absent: the same phrases as above; each is met by a line of the body for the case it names ("the value removed" by the return
     after the removal, "the key itself is removed" by the isEmpty branch); the @param clauses state caller preconditions only; no
     inline comment; the identifier values names the collection it holds."""

MVM = "src/java/org/apache/commons/collections/map/MultiValueMap.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MPU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Removes a value from the collection that a map holds against a key.
 * <p>
 * Other values held against the key are unaffected. Once the last value
 * has been removed, the key itself is removed from the map.
 *
 * @param map  the map of keys to collections, not null
 * @param key  a key that the map holds a collection against
 * @param value  the value to remove
 * @return the value removed
 */
public static Object removeFromValues(Map map, Object key, Object value) {
    Collection values = (Collection) map.get(key);
    if (!values.remove(value)) {
        return null;
    }
    if (values.isEmpty()) {
        map.remove(key);
    }
    return value;
}'''

HOP1 = '''/**
 * Removes a value from the collection mapped to a key in a map of collections.
 * <p>
 * A key that the map does not contain gives <code>null</code>.
 *
 * @param map  the map of keys to collections, not null
 * @param key  the key to remove the value from
 * @param value  the value to remove
 * @return the value removed, <code>null</code> if the map does not contain the key
 */
public static Object removeMappedValue(final Map map, final Object key, final Object value) {
    if (!map.containsKey(key)) {
        return null;
    }
    return DoubleOrderedMap.removeValueOf(map, key, value);
}'''

HOP2 = '''/**
 * Removes a value from the collection mapped to a key
 *
 * @param map the map of keys to collections
 * @param key the key to remove the value from
 * @param value the value to remove
 *
 * @return the value removed
 */
public static Object removeValueOf(final Map map, final Object key, final Object value) {
    return ExtendedProperties.removeKeyValue(map, key, value);
}'''

HOP3 = '''/**
 * Remove a value from the collection that is mapped to a key.
 *
 * @param map  the map of keys to collections
 * @param key  the key to remove the value from
 * @param value  the value to remove
 * @return the value removed
 */
public static Object removeKeyValue(Map map, Object key, Object value) {
    return MapUtils.removeMultiValue(map, key, value);
}'''

HOP4 = '''/**
 * Removes a value from the collection held in a Map against a key.
 * <p>
 * This is used by maps that hold a collection of values for each key,
 * such as {@link MultiValueMap}.
 *
 * @param map  the map of keys to collections, must not be null
 * @param key  the key to remove the value from
 * @param value  the value to remove
 * @return the value removed
 */
public static Object removeMultiValue(final Map map, final Object key, final Object value) {
    return CursorableLinkedList.removeFromValues(map, key, value);
}'''

DESIGN = {
 "instance": "Collections-10", "project": "Collections", "bug_id": 10, "seed": 8356,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": MVM, "class": "org.apache.commons.collections.map.MultiValueMap", "method": "removeMapping", "near_line": 190},
 "facade_variant": "V2",
 "state_passed": "the receiver this (as java.util.Map) with key and value to hop 1; no write-back",
 "reachability_probe": "full suite with removeMapping throwing first: 5 failing tests, all IllegalStateException: PROBE-REACHED at "
                       "MultiValueMap.removeMapping(MultiValueMap.java:191): TestMultiValueMap::testSize, testTotalSize, "
                       "testRemove_KeyItem, testMapEquals, testSize_Key",
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/map/TestMultiValueMap.java",
             "test_class": "org.apache.commons.collections.map.TestMultiValueMap", "test_method": "testRemove_KeyItem"},
 "expected_signature": "expected:<null> but was:<AD>",
 "gold": {"method": "removeFromValues", "text": GOLD_TEXT,
          "fault": {"old": "        if (!values.remove(value)) {\n"
                           "            return null;\n"
                           "        }\n",
                    "new": "        values.remove(value);\n"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.removeMappedValue(this, key, value);",
   "lie": "The collection mapped to the key is searched from its last value back to its first, and the first equal value "
          "found is removed.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "removeMappedValue",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "removeValueOf",
      "imports": [], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "removeKeyValue",
      "imports": [], "text": HOP3},
     {"file": MPU, "class": "org.apache.commons.collections.MapUtils", "method": "removeMultiValue",
      "imports": [], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableLinkedList", "method": "removeFromValues",
      "imports": ["java.util.Map"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.MultiMap::removeMapping",
              "org.apache.commons.collections.MultiHashMap::removeMapping",
              "org.apache.commons.collections.map.MultiValueMap::put"],
 "ownership_reason": "Only the gold looks up the key's collection and removes the value from it; hops 2-4 pass the map, the key "
                     "and the value along unchanged and hop 1 only answers a key the map does not contain with null. The gold's "
                     "javadoc promises to remove a value from the key's collection and to return the value removed; for a value "
                     "the collection does not hold it removes nothing and still returns that value (\"AD\"), which is not a "
                     "value removed. No one-line change of the arguments above the gold makes the gold report the value as not "
                     "removed, since the gold returns the value it was given on every path after the removal. The convention is "
                     "pinned outside the gold: MultiMap.removeMapping ('the value removed (which was passed in), null if nothing "
                     "removed'), the sibling implementation MultiHashMap.removeMapping, which returns null when Collection.remove "
                     "reports that nothing was removed (TestMultiHashMap testRemove_KeyItem: removeMapping(\"A\", \"AD\") is "
                     "null), and MultiValueMap.put, whose 'null if the map did not change' is decided from the boolean that "
                     "Collection.add returns (TestMultiValueMap testPutWithSet); the facade's own javadoc ('null if nothing "
                     "removed') is unchanged. A membership test written above the gold only avoids calling it for such a value "
                     "(a second implementation of the gold's removal test, a bypass).",
 "ownership_tests": ["org.apache.commons.collections.TestMultiHashMap::testRemove_KeyItem",
                     "org.apache.commons.collections.map.TestMultiValueMap::testPutWithSet",
                     "org.apache.commons.collections.map.TestMultiValueMap::testMapEquals"],
 "compensating": {
   "chain": [
     {"file": TBM, "old": "if (!map.containsKey(key)) {",
      "new": "if (!map.containsKey(key) || ((Collection) map.get(key)).isEmpty()) {",
      "why": "hop 1 also answers null for a key whose collection is empty"},
     {"file": DOM, "old": "return ExtendedProperties.removeKeyValue(map, key, value);",
      "new": "return value == null ? null : ExtendedProperties.removeKeyValue(map, key, value);",
      "why": "hop 2 answers null for a null value instead of passing it on"},
     {"file": MPU, "old": "return CursorableLinkedList.removeFromValues(map, key, value);",
      "new": "return map.containsKey(key) ? CursorableLinkedList.removeFromValues(map, key, value) : null;",
      "why": "hop 4 tests the key again before calling the removal"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted: bidimap.TreeBidiMap (hop 1, 2085 lines), DoubleOrderedMap (hop 2, 1995), ExtendedProperties (hop 3, "
               "1776), MapUtils (hop 4, 1645), CursorableLinkedList (hop 5, gold, 1468; the smallest host). All five are public "
               "top-level concrete classes (stageB_lib.top_level_kind: class, public) in which a public static method compiles "
               "(DoubleOrderedMap is final, which does not affect a static method). Anchors from stageB_lib.pick_insertion_anchor "
               "with seed 8356 + 100 + i (as mr3_spec.py inserts them): hop 1 after `put` (line idx 207, seed 8456), hop 2 after "
               "`remove` (1434, 8457), hop 3 after `getInclude` (528, 8458), hop 4 after `getBooleanValue` (723, 8459), hop 5 "
               "after `toArray` (684, 8460); all in the outer class. The facade calls hop 1 by its fully-qualified name; hop 1 "
               "imports DoubleOrderedMap; hops 2-4 call the next host in the same package; the gold host gains import "
               "java.util.Map. The facade's class MultiValueMap (facade_files_excluded) is not a host. The task record names the "
               "facade MultiValueMap.remove: the pool profile read upstream revision e6d4f465, where the method at lines 190-203 "
               "is remove(Object, Object); Defects4J's D4J_Collections_10_POST_FIX_COMPILABLE commit renamed it to removeMapping, "
               "its name in the fixture (same lines, same body).",
}
