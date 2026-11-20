"""Main run Collections-6__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Collections-6; the real bug modified map.Flat3Map, the facade's class). Batch 8: the bug has no static-facade instance (pool v2:
no_tested_static), so there is no paired instance (B8 note section 1).

Facade: Flat3Map.containsKey(Object) (instance method; allowed targets Flat3Map.get / .containsKey / .containsValue,
BATCH8_PREREGISTRATION.md row 225; facade_planned_by = null for containsKey, so the facade is distinct; the task record's
facade_reuse_of names Collections-1__i, which planned Flat3Map.get, not used here). Why not the other two: Flat3Map.containsValue in flat
mode with a non-empty map is reached only by AbstractTestMap.testMapPut (scratch probe), whose three queries are the ordinary case (the
value just put, the identical object), so only an omission that breaks the plain linear search would be caught, and every such one-line
omission leaves a frozen cursor, an unused parameter or a contradicted layout rule (T1/T2/T4); its special cases (a null value, an
empty map) are either never queried on a non-empty flat map or queried by two tests (testMapContainsValue and the values view's
testCollectionContains). Flat3Map.get was planned elsewhere (distinctness preferred) and offers the same lookup as containsKey.
Original computation of the facade: in delegate mode (delegateMap != null) the delegate answers; otherwise, for a null key, true if one
of the first `size` key slots (key3, key2, key1 by fall-through) is null; for a non-null key, with size > 0, true if one of the first
`size` slots has the stored hash code equal to key.hashCode() and a key that key.equals(); else false.

facade_variant: V1 (state as parameters). state_passed: the key and the private fields size, hash1, hash2, hash3, key1, key2, key3,
passed as values to hop 1; no field is written, no write-back. The facade keeps the original delegate guard (`if (delegateMap != null)
return delegateMap.containsKey(key);`) and then makes one call to hop 1. No visibility is widened, no type is added, no signature,
modifier, override or throws clause changes, no reflection, no test edit. The computation calls no private method (no V4) and no
package-private type passes through the chain (no V3/V5).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Collections-6-probe3 of the fixture, the first
statement of containsKey was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j
test -t org.apache.commons.collections.map.TestFlat3Map::testSerialisation2`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at Flat3Map.containsKey(Flat3Map.java:188), called from TestFlat3Map.testSerialisation2(TestFlat3Map.java:181). Full
suite with the probe: 28 failing tests (TestFlat3Map and its key-set / entry-set / map-iterator bulk tests). The facade is reached
directly by the trigger.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted; every allowed candidate's file,
map/Flat3Map.java, excluded by the record):
  hop 1 bidimap.TreeBidiMap     2085 lines  containsFlatKey  placement: packs the three key slots and the three hash slots into
                                                             arrays (slot order) and answers whether the found index is >= 0
  hop 2 DoubleOrderedMap        1995 lines  lookupSlot       plumbing: the key's hash code (zero for a null key, as stored)
  hop 3 ExtendedProperties      1717 lines  findSlot         plumbing: the number of slots searched, at most the table length
  hop 4 MapUtils                1645 lines  slotIndex        pass-through
  hop 5 CursorableLinkedList.java 1468 lines indexOfSlot     GOLD: one pass over the slots in use deciding, per slot, whether it
                                                             holds the key (hash code first, then the key itself)
Host newline counts 2085, 1995, 1717, 1645, 1468; the smallest host (and the gold host file) is CursorableLinkedList.java with 1468
lines (C10F addendum section 1: hosts under 1500 lines are expected in this regime).
The correct configuration returns the original result for every key and every flat state: a null key has hash 0 and matches a slot
whose key is null (every slot holding a null key has stored hash 0: put stores `key == null ? 0 : key.hashCode()`, remove moves the hash
with its key, convertToMap and clear reset both); a non-null key matches exactly when the stored hash equals key.hashCode() and the key
is the stored key or key.equals() it, which is the original `hash == hashCode && key.equals(keyN)`; slots beyond `size` are never
searched; size is at most 3, so hop 3's bound is size itself.

Fault (one-line omission in the gold's per-slot decision): the equality step of the key comparison is dropped (`if (hashes[slot] ==
hash && (keys[slot] == key || (key != null && key.equals(keys[slot])))) {` becomes `if (hashes[slot] == hash && keys[slot] == key) {`),
so a slot holds the key only if it holds the very same object. The gold then reads as the ordinary routine "compare the hash codes,
then the keys". Trigger: the EXISTING test TestFlat3Map::testSerialisation2: the map is serialised and read back, so the read-back map's
keys are new Integer objects equal to, but not the same as, the test's ONE and TWO; assertEquals(true, ser.containsKey(ONE)) at line 181
fails with expected:<true> but was:<false>. It is the only test that newly fails: in every other test that reaches the flat path the
key looked up is the object that was put (string literals, the same Integer constants, clone and putAll copy references); a scratch
run of the full suite with the original containsKey reduced to identity comparisons gives exactly one failing test, testSerialisation2;
gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the index of the slot "holding the specified key", hash codes compared first) and is
silent on how keys are compared. A map holds a key when one of its keys equals it (java.util.Map.containsKey), and the variant reports
that a map read back from its serialised form does not hold the key ONE that it holds. The convention is pinned outside the gold: the
intact siblings Flat3Map.get, Flat3Map.put and Flat3Map.remove do the same step (`hash1 == hashCode && key.equals(key1)`), and
AbstractHashedMap.isEqualKey (`key1 == key2 || key1.equals(key2)`) is the rule of the delegate map; passing tests:
TestFlat3Map::testCollections261 (Flat3Map.remove finds keys put as other equal Integer objects), TestFlat3Map::testSerialisation4 (the
read-back map in delegate mode holds the equal keys), TestFlat3Map::testClone2 (through the chain: the keys put are found).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: key, hash, keys, hashes and count all take part in the per-slot decision or the loop bound.
  T2 absent: slot is the loop cursor (slot++); no other local; the if has an effect (return slot) distinct from continuing.
  T3 absent: both parts of a slot (hash code and key) are compared; no set named in the gold's text is handled in part.
  T4 absent: 'the hash codes of the slots are compared first; the key of a slot is looked at only when its hash code is the hash code
     given' is met; 'may be null' (a null key is accepted without a throw), '-1 if none does' and 'the first count slots' are met.
 Variant gold (javadoc, signature, `for (int slot = 0; slot < count; slot++)`, `if (hashes[slot] == hash && keys[slot] == key)`,
 `return slot;`, `return -1;`):
  T1 absent: key and keys are compared, hash and hashes are compared, count bounds the loop; none is only argument-checked.
  T2 absent: slot advances in the loop header and is returned; no other local; no dead branch (the if returns, otherwise the loop
     continues).
  T3 absent: the two parts of a slot, its hash code and its key, are both compared; the gold names no value class or case set (it has
     no null branch at all: a null key goes through the same comparison as any other key, 'No member handled').
  T4 absent: 'holding the specified key' is a general description that the comparison addresses; 'compared first ... looked at only
     when its hash code is the hash code given' is met; 'may be null' is met (no throw for a null key); '-1 if none does' is met; no
     inline comment; identifiers (slot, hash, keys, hashes, count) name nothing the body does not meet.

Single owner: only the gold decides whether a slot holds the key; hop 1 only packs the slots and turns the index into a boolean, hop 2
only supplies the key's hash code, hop 3 only bounds the number of slots searched, hop 4 passes everything on. Once the gold compares
keys by identity, a key equal to but not the same as the stored one can be found only if a caller replaces the probe by the stored
object (which needs an equality search over the slots, a second implementation of the gold's decision) or replaces the gold.
Declared alternatives (G9): hop 3 searches every slot of the table; hop 2 drops the null rule from the hash code; hop 1 searches all
three slots. None makes the trigger pass.
Recorded bypasses (not repairs of the chain):
 B-0 the facade's original body (or hop 1 rewritten as the original switch over the slots) re-implements the lookup and makes the chain,
     including the gold, dead.
 B-1 hop 4 (or hop 3) answers with an equality search of its own, `return java.util.Arrays.asList(keys).subList(0, count).indexOf(key);`,
     discarding the gold's index (List.indexOf compares by equals; the hash codes are then ignored).

Lie: the facade's javadoc claims that the slots are kept in ascending order of hash code, so that the search stops at the first slot whose
hash code is greater than that of the key; the slots are in the order of insertion and every slot in use is searched. It names neither
how keys are compared nor any hop."""

F3 = "src/java/org/apache/commons/collections/map/Flat3Map.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Returns the index of the slot holding the specified key among the
 * first <code>count</code> slots of a flat table.
 * <p>
 * The hash codes of the slots are compared first; the key of a slot is
 * looked at only when its hash code is the hash code given.
 *
 * @param key  the key to search for, may be null
 * @param hash  the hash code of the key
 * @param keys  the keys of the slots
 * @param hashes  the hash codes of the slots
 * @param count  the number of slots to search
 * @return the index of the slot holding the key, or -1 if none does
 */
public static int indexOfSlot(Object key, int hash, Object[] keys, int[] hashes, int count) {
    for (int slot = 0; slot < count; slot++) {
        if (hashes[slot] == hash && (keys[slot] == key || (key != null && key.equals(keys[slot])))) {
            return slot;
        }
    }
    return -1;
}'''

HOP1 = '''/**
 * Checks whether a flat table of up to three slots holds the specified key.
 * <p>
 * The slots in use are the first <code>size</code> slots.
 *
 * @param key  the key to search for, may be null
 * @param size  the number of slots in use
 * @param hash1  the hash code of the key in the first slot
 * @param hash2  the hash code of the key in the second slot
 * @param hash3  the hash code of the key in the third slot
 * @param key1  the key in the first slot
 * @param key2  the key in the second slot
 * @param key3  the key in the third slot
 * @return true if one of the slots in use holds the key
 */
public static boolean containsFlatKey(Object key, int size, int hash1, int hash2, int hash3,
        Object key1, Object key2, Object key3) {
    final Object[] keys = new Object[] {key1, key2, key3};
    final int[] hashes = new int[] {hash1, hash2, hash3};
    return DoubleOrderedMap.lookupSlot(key, keys, hashes, size) >= 0;
}'''

HOP2 = '''/**
 * Finds the slot of a flat table that holds the specified key.
 * <p>
 * The hash code of a null key is taken as zero, as it is when the key
 * is stored.
 *
 * @param key  the key to search for, may be null
 * @param keys  the keys of the slots
 * @param hashes  the hash codes of the slots
 * @param size  the number of slots in use
 * @return the index of the slot holding the key, or -1 if none does
 */
public static int lookupSlot(final Object key, final Object[] keys, final int[] hashes, final int size) {
    final int hash = (key == null ? 0 : key.hashCode());
    return ExtendedProperties.findSlot(key, hash, keys, hashes, size);
}'''

HOP3 = '''/**
 * Finds the slot of a flat table that holds the specified key, searching
 * no more slots than the table has.
 *
 * @param key  the key to search for, may be null
 * @param hash  the hash code of the key
 * @param keys  the keys of the slots
 * @param hashes  the hash codes of the slots
 * @param size  the number of slots in use
 * @return the index of the slot holding the key, or -1 if none does
 */
public static int findSlot(Object key, int hash, Object[] keys, int[] hashes, int size) {
    int count = Math.min(size, keys.length);
    return MapUtils.slotIndex(key, hash, keys, hashes, count);
}'''

HOP4 = '''/**
 * Gets the index of the slot of a flat table that holds the specified key.
 *
 * @param key  the key to search for, may be null
 * @param hash  the hash code of the key
 * @param keys  the keys of the slots
 * @param hashes  the hash codes of the slots
 * @param count  the number of slots to search
 * @return the index of the slot holding the key, or -1 if none does
 */
public static int slotIndex(final Object key, final int hash, final Object[] keys, final int[] hashes, final int count) {
    return CursorableSubList.indexOfSlot(key, hash, keys, hashes, count);
}'''

DESIGN = {
 "instance": "Collections-6", "project": "Collections", "bug_id": 6, "seed": 8279,
 "src_root": "src/java", "test_root": "src/test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the key and the private fields size, hash1, hash2, hash3, key1, key2, key3 (values) passed to hop 1; the original "
                 "delegate guard stays in the facade; no field written, no write-back",
 "host_mode": "largest5", "host_lines": [2085, 1995, 1717, 1645, 1468],
 "reachability_probe": "containsKey first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Collections-6-probe3: TestFlat3Map::testSerialisation2 fails with PROBE-REACHED at "
                       "Flat3Map.containsKey(Flat3Map.java:188) from TestFlat3Map.java:181; full suite with the probe: 28 failing tests",
 "facade": {"file": F3, "class": "org.apache.commons.collections.map.Flat3Map", "method": "containsKey", "near_line": 187},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/map/TestFlat3Map.java",
             "test_class": "org.apache.commons.collections.map.TestFlat3Map", "test_method": "testSerialisation2"},
 "expected_signature": "expected:<true> but was:<false>",
 "gold": {"method": "indexOfSlot", "text": GOLD_TEXT,
          "fault": {"old": "            if (hashes[slot] == hash && (keys[slot] == key || (key != null && key.equals(keys[slot])))) {",
                    "new": "            if (hashes[slot] == hash && keys[slot] == key) {"}},
 "chain": {
   "facade_body": "if (delegateMap != null) {\n            return delegateMap.containsKey(key);\n        }\n"
                  "        return org.apache.commons.collections.bidimap.TreeBidiMap.containsFlatKey(key, size, hash1, hash2, hash3, "
                  "key1, key2, key3);",
   "lie": "The slots are kept in ascending order of hash code, so that the search stops at the first slot whose hash code is "
          "greater than that of the key.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "containsFlatKey",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "lookupSlot",
      "imports": [], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "findSlot",
      "imports": [], "text": HOP3},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "slotIndex",
      "imports": [], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "indexOfSlot",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.map.Flat3Map::get",
              "org.apache.commons.collections.map.Flat3Map::remove",
              "org.apache.commons.collections.map.AbstractHashedMap::isEqualKey"],
 "ownership_reason": "Only the gold decides whether a slot holds the key: hop 1 packs the slots into arrays and turns the index into "
                     "a boolean, hop 2 supplies the key's hash code (zero for a null key, as stored), hop 3 bounds the number of "
                     "slots searched by the table length, hop 4 passes everything on. Once the gold compares the keys of the slots by "
                     "identity, a key equal to but not the same object as the stored one (the read-back keys of a serialised map) can "
                     "be found only if a caller replaces the probe by the stored object, which needs an equality search over the "
                     "slots, or replaces the gold. The gold's javadoc promises the slot 'holding the specified key'; a map holds a key "
                     "when one of its keys equals it (java.util.Map.containsKey), and the variant reports that the read-back map does "
                     "not hold ONE. The convention is pinned outside the gold: the intact siblings Flat3Map.get, Flat3Map.put and "
                     "Flat3Map.remove compare `hash == hashCode && key.equals(keyN)`, and the delegate map's rule is "
                     "AbstractHashedMap.isEqualKey (`key1 == key2 || key1.equals(key2)`); TestFlat3Map::testCollections261 (remove "
                     "finds keys put as other equal Integer objects) and TestFlat3Map::testSerialisation4 (the read-back map in "
                     "delegate mode holds the equal keys) pass, as does TestFlat3Map::testClone2 through the chain.",
 "ownership_tests": ["org.apache.commons.collections.map.TestFlat3Map::testCollections261",
                     "org.apache.commons.collections.map.TestFlat3Map::testSerialisation4",
                     "org.apache.commons.collections.map.TestFlat3Map::testClone2"],
 "compensating": {
   "chain": [
     {"file": EXP, "old": "    int count = Math.min(size, keys.length);",
      "new": "    int count = keys.length;",
      "why": "hop 3 searches every slot of the table"},
     {"file": DOM, "old": "    final int hash = (key == null ? 0 : key.hashCode());",
      "new": "    final int hash = key.hashCode();",
      "why": "hop 2 takes the key's hash code without the null rule"},
     {"file": TBM, "old": "    return DoubleOrderedMap.lookupSlot(key, keys, hashes, size) >= 0;",
      "new": "    return DoubleOrderedMap.lookupSlot(key, keys, hashes, keys.length) >= 0;",
      "why": "hop 1 searches all three slots"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder; "
               "map/Flat3Map.java, the only allowed candidates' file, excluded by the record): bidimap.TreeBidiMap (hop 1, 2085 lines), "
               "DoubleOrderedMap (hop 2, 1995), ExtendedProperties (hop 3, 1717), MapUtils (hop 4, 1645), CursorableLinkedList.java "
               "(hop 5, gold, 1468; the smallest host). Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with "
               "seed 8279 + 100 + i, as mr3_spec.py inserts them: hop 1 after TreeBidiMap.get (seed 8379), hop 2 after "
               "DoubleOrderedMap.entrySetByValue (8380), hop 3 after ExtendedProperties.getList(String) (8381), hop 4 after "
               "MapUtils.getFloat(Map, Object, Float) (8382), hop 5 after addAll(Collection) at line 1294 of CursorableLinkedList.java, "
               "which lies in the file's second top-level class CursorableSubList (package-private, extends CursorableLinkedList; "
               "a public static method compiles there), so the gold is CursorableSubList.indexOfSlot and hop 4 (MapUtils, same "
               "package) calls it by that name; the anchor was not moved. All four other hosts are public concrete top-level classes. "
               "The facade calls hop 1 by its fully-qualified name; hop 1 imports DoubleOrderedMap; hops 2-4 call the next host in "
               "their own package.",
}
