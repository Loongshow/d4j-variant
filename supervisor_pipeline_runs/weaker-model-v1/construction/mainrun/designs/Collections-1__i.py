"""Main run Collections-1__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade;
fixed checkout of Defects4J Collections-1; the real bug modified map.Flat3Map, the facade's class). No static pair exists (pool v2:
no_tested_static), so addendum section 2 has nothing to refer to.

Facade: Flat3Map.get(Object) (instance method; allowed targets Flat3Map.get / .containsKey / .containsValue, BATCH8_PREREGISTRATION.md
row 223; facade_planned_by null for all three, so the facade is distinct; no facade reuse). get was chosen because the behaviour that a
single existing test catches (a lookup of a key that is equal to, but not the same object as, the stored key) is reached by get in a
test whose first failing assertion is a get (TestFlat3Map::testSerialisation2), with a value-specific failure message.
containsKey reaches the same behaviour only with a boolean message; the slot omissions of containsValue that a single test catches
(testMapPut) are slot-specific and have no loop form without a frozen bound.
Original computation: in delegate mode the call is forwarded to the delegate map; in flat mode a null key is compared with each of
the size stored keys by `keyN == null`, a non-null key by `hashN == key.hashCode() && key.equals(keyN)`, the stored keys being
searched from slot size down to slot 1; the value of the matching slot is returned, null if no slot matches.

facade_variant: V1 (state as parameters). state_passed: the key, the private field size and the private fields key1, key2, key3,
value1, value2, value3, handed to hop 1 as values; no field is written, no write-back. The delegate-mode dispatch (`if (delegateMap !=
null) return delegateMap.get(key);`, the original first statement) stays in the facade as its guard. The hash fields hash1..hash3 are
not passed: they are a pre-check of the equality test that cannot change its outcome for keys whose hashCode is consistent with
equals (the Map contract; every key used by the suite), so the chain compares keys by identity and equals only. The facade calls no
private method (no V4), needs no method of the receiver (no V2) and passes no package-private type (no V3/V5). No visibility is
widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit.

reachability_probe (addendum section 4): in a scratch copy of the fixture (/private/tmp/d4j-mi-Collections-1-probe), the first
statement of get(Object) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.collections.map.TestFlat3Map::testSerialisation2`: 1 failing test, with
java.lang.IllegalStateException: PROBE-REACHED. On the full suite the same probe fails 15 tests, all with PROBE-REACHED at
Flat3Map.get, among them testSerialisation2 (called from TestFlat3Map.java:182), testClone2, testEntryIteratorSetValue1-3,
testMapIteratorSetValue1-3, testMapGet. The facade is reached by the trigger directly. (The same probe on containsKey: 28 failing
tests; on containsValue: 9; all with PROBE-REACHED.)

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, exactly, in that order; no substitution):
  hop 1 bidimap.TreeBidiMap      2084 lines  lookupValue   aggregation: gathers the separate keys and values into two arrays
  hop 2 DoubleOrderedMap         1994 lines  valueForKey   pass-through
  hop 3 ExtendedProperties       1685 lines  mappedValue   pass-through
  hop 4 MapUtils                 1644 lines  valueOfKey    placement: the index of the key -> the value at that index, null if none
  hop 5 CursorableLinkedList.java 1467 lines indexOfKey    GOLD: one pass over the keys in use deciding, per stored key, whether it
                                                           is the key looked up
  Anchors from the recipe's seeded picker (stageB_lib.pick_anchor, seed 6062 + 100 + i, as mr3_spec.py inserts them): hop 1 after
  TreeBidiMap.get (line 178, seed 6162), hop 2 after DoubleOrderedMap.size (line 1286, 6163), hop 3 after the ExtendedProperties()
  constructor (line 441, 6164), hop 4 after MapUtils.getFloat (line 528, 6165), hop 5 after getLast (line 1358, 6166). The hop-5 anchor
  lies in the second top-level class of CursorableLinkedList.java, the package-private (deprecated) CursorableSubList (declared at line
  1201, extends CursorableLinkedList), so the gold is the public static member CursorableSubList.indexOfKey of the listed host file;
  hop 4 (MapUtils, the same package org.apache.commons.collections) calls it directly. The method catalog of the harness lists methods
  by their declaring class, so the gold is org.apache.commons.collections.CursorableSubList::indexOfKey.
Host newline counts 2084, 1994, 1685, 1644, 1467; the smallest host is the gold host CursorableLinkedList.java (1467 lines; C10F
addendum section 1: hosts under 1500 lines are expected in this regime).
The correct configuration returns the original value for every flat-mode lookup: the stored keys are distinct, so the search order
does not matter; `element == key` covers a null key (the original's `keyN == null`) and the same object; `key != null &&
key.equals(element)` covers an equal key, the hash pre-check being implied by equals for consistent keys; only the first size slots
are searched (the others hold null or stale entries the original never reads).

Fault (one-line omission of a decision step in the gold): the equality test is dropped from the per-key decision (`if (element == key
|| (key != null && key.equals(element))) {` becomes `if (element == key) {`), so a key is found only if it is the very object stored.
The gold then reads as the ordinary routine "find the index of the key among the first count keys". Trigger: the EXISTING test
TestFlat3Map::testSerialisation2: a map {ONE=TEN, TWO=TWENTY} is serialised and read back (Flat3Map.readObject puts the deserialised
keys, new Integer objects); `assertEquals(true, ser.containsKey(ONE))` (intact sibling) holds and `assertEquals(TEN, ser.get(ONE))` fails
with expected:<10> but was:<null>. It is the only test that newly fails: deserialisation is the only place in the suite where a flat
Flat3Map holds a key that is equal to, but not the same object as, the key looked up with get (every other flat-mode test uses
interned literals or the same static Integer objects; the four-entry maps of testSerialisation4 and testClone4 are in delegate mode).
Mutation screen on the original get (identity-only per slot): slot 1 and slot 2 each fail testSerialisation2 alone, slot 3 fails none.

The gold's javadoc states the idiomatic contract (the index of the key among the first count keys) and is silent on how keys are
compared. A lookup of a Map key compares by equals (java.util.Map.get, whose contract the facade implements); the variant returns -1 for
a key equal to a stored key, so the facade returns null for a mapped key. The convention is pinned outside the gold: the intact sibling
Flat3Map.containsKey (`key.equals(key1)`, the assertion just before the failing one in the trigger holds) and Flat3Map.put (an equal key
replaces the mapping) do the same step; AbstractHashedMap.isEqualKey (`key1 == key2 || key1.equals(key2)`), the delegate's comparison,
is exactly the gold's correct test. Passing tests: TestFlat3Map::testSerialisation4 (the same deserialised Integer keys found by get in
delegate mode), testClone2 and testEntryIteratorSetValue3 (flat-mode get through the chain, every slot).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: key is compared with every element; keys supplies each element; count bounds the loop; none is only argument-checked.
  T2 absent: i is the loop cursor and advances; element is read by the decision; the decision returns i, the fall-through returns -1;
     no literal-initialised local.
  T3 absent: no enum, type code or named format; identity and equality are two parts of one comparison, not members of a closed set;
     no pair half or range end is handled on one side only (the search runs over the whole range 0..count-1).
  T4 absent: 'the index of a key among the first count elements' (loop bound count), 'may be null' (a null key is accepted: the
     `key != null` test guards the equals call), '-1 if it is not found' (the fall-through) are each met.
 Variant gold (javadoc, signature, the loop, `Object element = keys[i];`, `if (element == key) { return i; }`, `return -1;`):
  T1 absent: key decides the comparison, keys supplies the elements, count bounds the loop; each changes the result.
  T2 absent: i advances; element is read by the decision; the decision has an effect (return i) different from the fall-through
     (return -1); no local is frozen or dead.
  T3 absent: the gold has one comparison per element and no case analysis at all (no null branch, no class of keys treated apart:
     'No member handled'); no pair or range end is handled on one side only; the gold's text names no class it handles in part.
  T4 absent: 'Returns the index of a key among the first count elements of an array of keys' is a general description that the loop
     addresses; 'the key to find, may be null' is met (a null key is compared with == and never throws); 'the index of the key, or -1
     if it is not found' is met by the two returns; no inline comment; the identifiers (element, keys, count) name what they hold.

Single owner: only the gold decides whether a stored key is the key looked up; hop 1 only gathers the entries into arrays, hops 2 and 3
pass them along, hop 4 only turns the gold's index into the value at that index. Once the gold has answered -1 for a key that is
stored, a caller can produce the mapped value only by comparing the keys itself (a second implementation of the gold's decision) or by
replacing the gold. Declared alternatives (G9): hop 1 searches all three entries whatever the size; hop 4 clamps the count to the length
of the arrays; hop 2 answers an empty store without searching. None makes the trigger pass.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-0 the facade's original body re-implements the whole lookup and makes the chain, including the gold, dead.
 B-1 hop 4 finds the index without the gold: `int index = java.util.Arrays.asList(keys).subList(0, count).indexOf(key);` (List.indexOf
     compares with equals), discarding the gold's output. Checked on the variant in a scratch copy: trigger passes, full suite 0
     failing tests.
 B-2 hop 1 replaces the key by the stored key it equals before passing it on (a second implementation of the gold's comparison).

Lie: the facade's javadoc claims each lookup first checks the entry found by the previous lookup, which the map remembers for this
purpose; no field or step remembers or re-checks a previous entry. It names neither key comparison nor equality nor any hop."""

F3M = "src/java/org/apache/commons/collections/map/Flat3Map.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Returns the index of a key among the first <code>count</code> elements
 * of an array of keys.
 *
 * @param key  the key to find, may be null
 * @param keys  the keys to search
 * @param count  the number of elements of the array to search
 * @return the index of the key, or -1 if it is not found
 */
public static int indexOfKey(Object key, Object[] keys, int count) {
    for (int i = 0; i < count; i++) {
        Object element = keys[i];
        if (element == key || (key != null && key.equals(element))) {
            return i;
        }
    }
    return -1;
}'''

HOP1 = '''/**
 * Gets the value mapped to a key in a store of at most three entries,
 * whose keys and values are held separately.
 * <p>
 * Only the first <code>size</code> entries are in use.
 *
 * @param key  the key to look up, may be null
 * @param size  the number of entries in use
 * @param key1  the key of the first entry
 * @param key2  the key of the second entry
 * @param key3  the key of the third entry
 * @param value1  the value of the first entry
 * @param value2  the value of the second entry
 * @param value3  the value of the third entry
 * @return the mapped value, null if no match
 */
public static Object lookupValue(Object key, int size, Object key1, Object key2, Object key3,
        Object value1, Object value2, Object value3) {
    Object[] keys = new Object[] {key1, key2, key3};
    Object[] values = new Object[] {value1, value2, value3};
    return DoubleOrderedMap.valueForKey(key, keys, values, size);
}'''

HOP2 = '''/**
 * Gets the value mapped to a key, given the keys and values of a store
 * as parallel arrays.
 *
 * @param key  the key to look up, may be null
 * @param keys  the keys of the store
 * @param values  the values of the store, in the order of the keys
 * @param count  the number of entries in use
 * @return the mapped value, null if no match
 */
public static Object valueForKey(Object key, Object[] keys, Object[] values, int count) {
    return ExtendedProperties.mappedValue(key, keys, values, count);
}'''

HOP3 = '''/**
 * Gets the value mapped to a key, given the keys and values of a store
 * as parallel arrays.
 *
 * @param key  the key to look up, may be null
 * @param keys  the keys of the store
 * @param values  the values of the store, in the order of the keys
 * @param count  the number of entries in use
 * @return the mapped value, null if no match
 */
public static Object mappedValue(Object key, Object[] keys, Object[] values, int count) {
    return MapUtils.valueOfKey(key, keys, values, count);
}'''

HOP4 = '''/**
 * Gets the value stored for a key, given the keys and values of a store
 * as parallel arrays.
 * <p>
 * The value is the one at the index of the key among the keys in use.
 *
 * @param key  the key to look up, may be null
 * @param keys  the keys of the store
 * @param values  the values of the store, in the order of the keys
 * @param count  the number of entries in use
 * @return the value stored for the key, null if there is none
 */
public static Object valueOfKey(Object key, Object[] keys, Object[] values, int count) {
    int index = CursorableSubList.indexOfKey(key, keys, count);
    if (index < 0) {
        return null;
    }
    return values[index];
}'''

DESIGN = {
 "instance": "Collections-1", "project": "Collections", "bug_id": 1, "seed": 6062,
 "src_root": "src/java", "test_root": "src/test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "key, the private fields size, key1, key2, key3, value1, value2, value3 (values) passed to hop 1; the delegate-mode "
                 "dispatch stays in the facade as its guard; no write-back",
 "host_mode": "largest5", "host_lines": [2084, 1994, 1685, 1644, 1467],
 "reachability_probe": "get(Object) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in a scratch "
                       "copy: TestFlat3Map::testSerialisation2 fails with PROBE-REACHED (full suite: 15 failing tests, all "
                       "PROBE-REACHED at Flat3Map.get, including testSerialisation2 from TestFlat3Map.java:182)",
 "facade": {"file": F3M, "class": "org.apache.commons.collections.map.Flat3Map", "method": "get", "near_line": 127},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/map/TestFlat3Map.java",
             "test_class": "org.apache.commons.collections.map.TestFlat3Map", "test_method": "testSerialisation2"},
 "expected_signature": "expected:<10> but was:<null>",
 "gold": {"method": "indexOfKey", "text": GOLD_TEXT,
          "fault": {"old": "            if (element == key || (key != null && key.equals(element))) {",
                    "new": "            if (element == key) {"}},
 "chain": {
   "facade_body": "if (delegateMap != null) {\n            return delegateMap.get(key);\n        }\n"
                  "        return org.apache.commons.collections.bidimap.TreeBidiMap.lookupValue(key, size, key1, key2, key3, "
                  "value1, value2, value3);",
   "lie": "Each lookup first checks the entry found by the previous lookup, which the map remembers for this purpose.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "lookupValue",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "valueForKey",
      "imports": [], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "mappedValue",
      "imports": [], "text": HOP3},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "valueOfKey",
      "imports": [], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "indexOfKey",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.map.Flat3Map::containsKey",
              "org.apache.commons.collections.map.Flat3Map::put",
              "org.apache.commons.collections.map.AbstractHashedMap::isEqualKey"],
 "ownership_reason": "Only the gold decides whether a stored key is the key looked up: it returns the index of the key among the "
                     "first count keys. Hop 1 only gathers the separate keys and values into arrays, hops 2 and 3 pass them along, "
                     "and hop 4 only turns the gold's index into the value at that index (null for -1). Once the gold answers -1 for "
                     "a key that is stored, the mapped value can be produced only by a caller that compares the keys itself or "
                     "replaces the gold. The facade implements java.util.Map.get, whose keys are compared with equals; the variant "
                     "finds a key only if it is the very object stored, so a deserialised map does not find its own keys. The "
                     "convention is pinned outside the gold: the intact siblings Flat3Map.containsKey and Flat3Map.put compare a "
                     "non-null key with key.equals(storedKey), and AbstractHashedMap.isEqualKey (the delegate map's comparison) is "
                     "key1 == key2 || key1.equals(key2), the gold's correct test; TestFlat3Map::testSerialisation4 (the same "
                     "deserialised Integer keys found by get in delegate mode) passes, as do testClone2 and "
                     "testEntryIteratorSetValue3 through the chain.",
 "ownership_tests": ["org.apache.commons.collections.map.TestFlat3Map::testSerialisation4",
                     "org.apache.commons.collections.map.TestFlat3Map::testClone2",
                     "org.apache.commons.collections.map.TestFlat3Map::testEntryIteratorSetValue3"],
 "compensating": {
   "chain": [
     {"file": TBM, "old": "return DoubleOrderedMap.valueForKey(key, keys, values, size);",
      "new": "return DoubleOrderedMap.valueForKey(key, keys, values, keys.length);",
      "why": "hop 1 searches all three entries whatever the size"},
     {"file": MU, "old": "int index = CursorableSubList.indexOfKey(key, keys, count);",
      "new": "int index = CursorableSubList.indexOfKey(key, keys, Math.min(count, keys.length));",
      "why": "hop 4 clamps the count to the length of the arrays"},
     {"file": DOM, "old": "return ExtendedProperties.mappedValue(key, keys, values, count);",
      "new": "return count == 0 ? null : ExtendedProperties.mappedValue(key, keys, values, count);",
      "why": "hop 2 answers an empty store without searching"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, exactly, in that order, none drawn or substituted by "
               "this builder): bidimap.TreeBidiMap (hop 1, 2084 lines), DoubleOrderedMap (hop 2, 1994), ExtendedProperties (hop 3, "
               "1685), MapUtils (hop 4, 1644), CursorableLinkedList.java (hop 5, the gold, 1467). Anchors (stageB_lib.pick_anchor, "
               "seed 6062 + 100 + i, as mr3_spec.py inserts them): hop 1 after TreeBidiMap.get (line 178, seed 6162), hop 2 after "
               "DoubleOrderedMap.size (line 1286, 6163), hop 3 after the ExtendedProperties() constructor (line 441, 6164), hop 4 "
               "after MapUtils.getFloat (line 528, 6165), hop 5 after getLast (line 1358, 6166). The hop-5 anchor is in the second, "
               "package-private top-level class of CursorableLinkedList.java, CursorableSubList (line 1201, extends "
               "CursorableLinkedList), so the gold is declared as CursorableSubList.indexOfKey; it is called from MapUtils in the "
               "same package. The facade calls hop 1 by its fully-qualified name; hop 1 imports DoubleOrderedMap (another package); "
               "hops 2, 3 and 4 call the next host in their own package. The smallest host is CursorableLinkedList.java (1467 "
               "lines), the gold host.",
}
