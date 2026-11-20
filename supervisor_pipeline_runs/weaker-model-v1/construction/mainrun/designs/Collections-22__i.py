"""Main run Collections-22__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed
checkout of Defects4J Collections-22; the real bug modified ListOrderedMap, the facade's class). No static pair (pool v2: no tested
public static method in the modified class; BUILD_BRIEF_C10I_B8_NOTE.md section 1).

Facade: ListOrderedMap.putAll(int, Map) (the only allowed candidate of batch9_tasks.json, facade_planned_by null, no facade reuse;
the overload putAll(Map) is not the facade). Original computation of the facade: for every entry of the supplied map, in its
iteration order, put the mapping at the current index with put(int, K, V) (which moves a key that is already present to that
index, correcting the index for its removal) and continue right after the key just put.

facade_variant: V2 (receiver as parameter). The computation needs public methods of the object (size(), indexOf(Object) and
put(int, K, V)), so the facade passes `this`, typed as ListOrderedMap<K, V>, together with its two parameters index and map to
hop 1; the hops call only those public methods. The method reads and writes no field directly (V1 not applicable), calls no
private method (no V4), and no package-private type passes through the hops (no V3/V5). No signature, modifier, override or throws
change; no visibility widened; no new type; no reflection; no test edit. The facade had no argument guard (a null map fails with
NullPointerException at entrySet(), which the chain keeps: the gold calls map.entrySet()).
state_passed: the receiver `this` (as ListOrderedMap<K, V>) and the parameters index and map to hop 1; no write-back (the method is
void and its effect is the receiver's own put calls).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-22-probe of the
fixture, the first statement of putAll(int, Map) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the
`if (true)` keeps the rest of the body reachable for javac). defects4j test -t on each candidate trigger:
ListOrderedMapTest::testPutAllWithIndex, ::testPutAllWithIndexBug441, ::testCOLLECTIONS_474_nullValues and
::testCOLLECTIONS_474_nonNullValues each fail with java.lang.IllegalStateException: PROBE-REACHED. These four are the only tests
that reach the facade (it has no production caller). The facade is reached by existing tests directly.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of the task record, in that order; none substituted):
  hop 1 bidimap.TreeBidiMap   2172 lines  putAllOrdered   pass-through
  hop 2 MapUtils              1779 lines  insertAll       pass-through
  hop 3 CollectionUtils       1762 lines  addAllAt        pass-through
  hop 4 map.AbstractHashedMap 1389 lines  putAllAtIndex   pass-through
  hop 5 map.Flat3Map          1249 lines  placeMappings   GOLD: the iteration over the entries, the put position of each mapping
                                                          and where the next mapping goes
Host newline counts 2172, 1779, 1762, 1389, 1249; the smallest host is Flat3Map (1249 lines, the gold host).

Correct gold: the put position is kept as a distance from the end of the ordered map (fromEnd, initialised to size - index), so that
a key moved from in front of the position by put(int, K, V) does not disturb it while an added key grows the map in front of it;
after each put the distance is re-read from the key just placed (fromEnd = size - indexOf(key) - 1), so the next mapping goes right
after it. This is the original computation (position size - fromEnd = indexOf(key) + 1 after each put; the first put is at index),
so the correct configuration behaves exactly as the original for every input, including the IndexOutOfBoundsException of
put(int, K, V) for a start index outside 0..size.

Fault (one-line omission of a state update in the gold): the line `fromEnd = target.size() - target.indexOf(key) - 1;` is dropped,
so the distance from the end stays at its initial value. Added keys and keys moved from in front of the position are still placed
right after the previous mapping (the map grows, or the position is unchanged by the move), but a key taken from behind the
position is put at the position and the next mapping is put in front of it. Trigger: the EXISTING test
ListOrderedMapTest::testPutAllWithIndexBug441 (keys 0..4, then a TreeMap of the same five keys put at index 3): keys 3 and 4 sit
behind the position, and the variant gives [0, 1, 2, 4, 3], so assertEquals(Integer.valueOf(3), orderedList.get(3)) fails with
expected:<3> but was:<4>. It is the only test that newly fails: of the four tests that reach the facade (probe above),
testPutAllWithIndex puts only added keys and both testCOLLECTIONS_474 tests put only keys in front of the position (start index =
size), and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (all the mappings put into the ordered map in the iteration order of the
specified map, starting at the specified index; the facade's own wording plus the order) and is silent on how the position moves
on; [0, 1, 2, 4, 3] does not hold the mappings 0..4 of the TreeMap in its iteration order. The convention is pinned outside the
gold: the facade's own javadoc ("Puts the values contained in a supplied Map into the Map starting at the specified index", kept
unchanged); ListOrderedMap.put(int, K, V), which moves a key that is already present to the given index, pinned by
ListOrderedMapTest::testPut_intObjectObject (an existing key put at 0, 1, 2 and 3); ListOrderedSet.addAll(int, Collection), which
inserts the elements at the index in their iteration order, pinned by ListOrderedSetTest::testListAddIndexed; SetUniqueList.addAll
(int, Collection); and ListOrderedMapTest::testPutAllWithIndex (passing on the variant), which pins consecutive placement in the
supplied map's order from the start index.

Single owner: only the gold iterates the entries, computes each put position and decides where the next mapping goes; hops 1-4
pass the receiver, the index and the map along unchanged with one call each, so no one-line edit there can change where the gold
puts its second and later mappings. Declared alternatives (G9): hop 1 bounds the start index by the size of the map (the trigger
still fails); hop 3 starts one place later (index + 1: the trigger passes, testPutAllWithIndex fails, so it contradicts the start
index); hop 4 hands the entries over in key order (a TreeMap copy; the trigger's map already is one, so it still fails).
Recorded bypasses (edits that replace the gold's work with another implementation, not repairs of the chain):
 B-0 a hop (or the facade, i.e. its original body) re-implements the whole loop itself instead of calling the next hop, which
     makes the gold dead.
 B-1 a hop puts the entries one at a time through the gold, each in a single-entry map, and computes the next index itself
     (indexOf(key) + 1); this re-implements the gold's position rule outside it (a loop and an index of its own, not a one-line
     change).
 B-2 a hop moves the start index to the end of the map when every key is already present; this contradicts "starting at the
     specified index" of every hop and of the facade.

Lie: the facade's javadoc claims the entries are first copied into an array from which the mappings are then put; the chain
copies nothing and puts the entries straight from the map's entry set. It names neither the position rule, the omitted step nor
any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (`int fromEnd = target.size() - index;` then, for each entry: key, `target.put(target.size() - fromEnd, key,
 entry.getValue());`, `fromEnd = target.size() - target.indexOf(key) - 1;`):
  T1 absent: target is read by size, put and indexOf; index sets the first put position; map is iterated; no argument check.
  T2 absent: key reaches put and indexOf; fromEnd is read by every put and reassigned in the loop; no literal-initialised local;
     no branch, case or ternary.
  T3 absent: no decision at all; the key and the value of each entry both go to put; no enum, type code or named format.
  T4 absent: "in the iteration order of the specified map, starting at the specified index" is addressed by the loop over
     map.entrySet() and the first put at size - (size - index); the @param clauses name no rule.
 Variant gold (javadoc; signature (target, int index, map); `int fromEnd = target.size() - index;`; for each entry:
 `final K key = entry.getKey();`, `target.put(target.size() - fromEnd, key, entry.getValue());`):
  T1 absent: target is read by size and put; index sets fromEnd, which fixes every put position; map is iterated; every
     parameter changes the effect on target; none is only argument-checked.
  T2 absent: (a) key and fromEnd both reach the put arguments; (b)(i) fromEnd is initialised from an expression, not a literal;
     (b)(ii) fromEnd is an offset computed before the loop and only read in it, subtracted from target.size(), which grows as
     mappings are added (the checklist's "base offset added to an advancing cursor"), so it is not a frozen cursor, write
     position, counter, flag or best-so-far; (c) the gold has no branch, case or ternary.
  T3 absent: no decision, so no handled sibling and no missing member; the key and the value of each entry are both treated
     (both go to put); one position, no range with two ends; no enum, type code, named format or named class.
  T4 absent: "Puts all the mappings from the specified map into an ordered map, in the iteration order of the specified map,
     starting at the specified index" is a general description addressed by the loop that puts every entry of map.entrySet() in
     turn, the first at target.size() - fromEnd = index; "@param target the ordered map to put the mappings into", "@param index
     the index to start at" and "@param map the map containing the mappings to put" name no concrete rule, limit or value class;
     no inline comment; the identifiers target, index, map, fromEnd, entry and key name what they hold."""

LOM = "src/main/java/org/apache/commons/collections4/map/ListOrderedMap.java"
TBM = "src/main/java/org/apache/commons/collections4/bidimap/TreeBidiMap.java"
MU = "src/main/java/org/apache/commons/collections4/MapUtils.java"
CU = "src/main/java/org/apache/commons/collections4/CollectionUtils.java"
AHM = "src/main/java/org/apache/commons/collections4/map/AbstractHashedMap.java"
F3M = "src/main/java/org/apache/commons/collections4/map/Flat3Map.java"

GOLD_TEXT = '''/**
 * Puts all the mappings from the specified map into an ordered map, in the
 * iteration order of the specified map, starting at the specified index.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target  the ordered map to put the mappings into
 * @param index  the index to start at
 * @param map  the map containing the mappings to put
 */
public static <K, V> void placeMappings(final ListOrderedMap<K, V> target, final int index,
        final Map<? extends K, ? extends V> map) {
    int fromEnd = target.size() - index;
    for (final Map.Entry<? extends K, ? extends V> entry : map.entrySet()) {
        final K key = entry.getKey();
        target.put(target.size() - fromEnd, key, entry.getValue());
        fromEnd = target.size() - target.indexOf(key) - 1;
    }
}'''

HOP1 = '''/**
 * Puts all the mappings from the specified map into an ordered map,
 * starting at the specified index.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target  the ordered map to put the mappings into
 * @param index  the index to start at
 * @param map  the map containing the mappings to put
 */
public static <K, V> void putAllOrdered(final ListOrderedMap<K, V> target, final int index,
        final Map<? extends K, ? extends V> map) {
    MapUtils.insertAll(target, index, map);
}'''

HOP2 = '''/**
 * Inserts all the mappings from the specified map into the given ordered map,
 * starting at the specified index.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target  the ordered map to insert into
 * @param index  the index to start at
 * @param map  the map containing the mappings to insert
 */
public static <K, V> void insertAll(final ListOrderedMap<K, V> target, final int index,
        final Map<? extends K, ? extends V> map) {
    CollectionUtils.addAllAt(target, index, map);
}'''

HOP3 = '''/**
 * Adds all the mappings of the given map to the ordered map, starting at
 * the specified index.
 *
 * @param <K>  the type of the keys
 * @param <V>  the type of the values
 * @param target  the ordered map to add to
 * @param index  the index to start at
 * @param map  the map whose mappings are added
 */
public static <K, V> void addAllAt(final ListOrderedMap<K, V> target, final int index,
        final Map<? extends K, ? extends V> map) {
    AbstractHashedMap.putAllAtIndex(target, index, map);
}'''

HOP4 = '''/**
 * Puts all the mappings from the specified map into an ordered map,
 * starting at the specified index.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target  the ordered map to put into
 * @param index  the index to start at
 * @param map  the map to take the mappings from
 */
public static <K, V> void putAllAtIndex(final ListOrderedMap<K, V> target, final int index,
        final Map<? extends K, ? extends V> map) {
    Flat3Map.placeMappings(target, index, map);
}'''

DESIGN = {
 "instance": "Collections-22", "project": "Collections", "bug_id": 22, "seed": 3817,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": LOM, "class": "org.apache.commons.collections4.map.ListOrderedMap", "method": "putAll", "near_line": 244},
 "facade_variant": "V2",
 "state_passed": "the receiver `this` (as ListOrderedMap<K, V>) and the parameters index and map to hop 1; no write-back",
 "reachability_probe": "ListOrderedMapTest::testPutAllWithIndex, ::testPutAllWithIndexBug441, ::testCOLLECTIONS_474_nullValues and "
                       "::testCOLLECTIONS_474_nonNullValues each fail with java.lang.IllegalStateException: PROBE-REACHED "
                       "(first statement of putAll(int, Map) made to throw); these are the only tests reaching the facade",
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/collections4/map/ListOrderedMapTest.java",
             "test_class": "org.apache.commons.collections4.map.ListOrderedMapTest", "test_method": "testPutAllWithIndexBug441"},
 "expected_signature": "expected:<3> but was:<4>",
 "gold": {"method": "placeMappings", "text": GOLD_TEXT,
          "fault": {"old": "            target.put(target.size() - fromEnd, key, entry.getValue());\n"
                           "            fromEnd = target.size() - target.indexOf(key) - 1;\n",
                    "new": "            target.put(target.size() - fromEnd, key, entry.getValue());\n"}},
 "chain": {
   "facade_body": "org.apache.commons.collections4.bidimap.TreeBidiMap.putAllOrdered(this, index, map);",
   "lie": "The entries of the supplied map are first copied into an array, and the mappings are then put from that array.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections4.bidimap.TreeBidiMap", "method": "putAllOrdered",
      "imports": ["org.apache.commons.collections4.MapUtils", "org.apache.commons.collections4.map.ListOrderedMap"], "text": HOP1},
     {"file": MU, "class": "org.apache.commons.collections4.MapUtils", "method": "insertAll",
      "imports": [], "text": HOP2},
     {"file": CU, "class": "org.apache.commons.collections4.CollectionUtils", "method": "addAllAt",
      "imports": ["org.apache.commons.collections4.map.AbstractHashedMap", "org.apache.commons.collections4.map.ListOrderedMap"],
      "text": HOP3},
     {"file": AHM, "class": "org.apache.commons.collections4.map.AbstractHashedMap", "method": "putAllAtIndex",
      "imports": [], "text": HOP4},
     {"file": F3M, "class": "org.apache.commons.collections4.map.Flat3Map", "method": "placeMappings", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections4.map.ListOrderedMap::put",
              "org.apache.commons.collections4.set.ListOrderedSet::addAll",
              "org.apache.commons.collections4.list.SetUniqueList::addAll"],
 "ownership_reason": "Only the gold iterates the entries of the supplied map, computes the position at which each mapping is put "
                     "and decides where the next mapping goes; hops 1-4 pass the ordered map, the start index and the whole map "
                     "along unchanged with one call each, so no one-line change above the gold can alter where the gold puts its "
                     "second and later mappings (a different start index moves the whole block: one place later passes the "
                     "trigger but puts the added mappings of testPutAllWithIndex one place too late). The gold's javadoc promises "
                     "all the mappings put into the ordered map in the iteration order of the specified map, starting at the "
                     "specified index, which [0, 1, 2, 4, 3] for the keys 0..4 of a TreeMap does not do. The convention is "
                     "pinned outside the gold: the facade's own javadoc (the values put 'into the Map starting at the specified "
                     "index'); ListOrderedMap.put(int, K, V), which moves a key that is already present to the given index "
                     "(ListOrderedMapTest testPut_intObjectObject); ListOrderedSet.addAll(int, Collection), which inserts the "
                     "elements at the index in their iteration order (ListOrderedSetTest testListAddIndexed); "
                     "SetUniqueList.addAll(int, Collection); and consecutive placement in the supplied map's order from the start "
                     "index, pinned by ListOrderedMapTest testPutAllWithIndex.",
 "ownership_tests": ["org.apache.commons.collections4.map.ListOrderedMapTest::testPut_intObjectObject",
                     "org.apache.commons.collections4.map.ListOrderedMapTest::testPutAllWithIndex",
                     "org.apache.commons.collections4.set.ListOrderedSetTest::testListAddIndexed"],
 "compensating": {
   "chain": [
     {"file": TBM, "old": "MapUtils.insertAll(target, index, map);",
      "new": "MapUtils.insertAll(target, Math.min(index, target.size()), map);",
      "why": "hop 1 bounds the start index by the size of the ordered map"},
     {"file": CU, "old": "AbstractHashedMap.putAllAtIndex(target, index, map);",
      "new": "AbstractHashedMap.putAllAtIndex(target, index + 1, map);",
      "why": "hop 3 starts the block one place later"},
     {"file": AHM, "old": "Flat3Map.placeMappings(target, index, map);",
      "new": "Flat3Map.placeMappings(target, index, new java.util.TreeMap<K, V>(map));",
      "why": "hop 4 hands the entries over in key order"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted, none drawn by this builder: bidimap.TreeBidiMap (hop 1, 2172 lines), MapUtils (hop 2, 1779), "
               "CollectionUtils (hop 3, 1762), map.AbstractHashedMap (hop 4, 1389), map.Flat3Map (hop 5, gold, 1249; the smallest "
               "host). All five are public concrete top-level classes in which a public static generic method compiles "
               "(the class type parameters of TreeBidiMap and Flat3Map are shadowed by the static method's <K, V>, which only "
               "concerns the method). The facade's file ListOrderedMap.java is excluded (facade_files_excluded) and is not a "
               "host. Anchors from stageB_lib.insert_hop (host_search.pick_insertion_anchor) with seed 3817 + 100 + i, as "
               "mr3_spec.py inserts them: hop 1 after previousKey (seed 3917), hop 2 after multiValueMap (3918), hop 3 after get (3919), hop 4 after equals "
               "(3920), hop 5 after get (3921). The facade calls hop 1 by its fully-qualified name; TreeBidiMap imports "
               "MapUtils and ListOrderedMap; MapUtils already imports ListOrderedMap and calls CollectionUtils in its own "
               "package; CollectionUtils imports AbstractHashedMap and ListOrderedMap; AbstractHashedMap and Flat3Map are in "
               "ListOrderedMap's package.",
}
