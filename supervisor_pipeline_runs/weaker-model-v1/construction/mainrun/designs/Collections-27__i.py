"""Main run Collections-27__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout
of Defects4J Collections-27; the real bug modified MultiValueMap, the facade's class). No static pair (pool v2: no_tested_static), so
addendum section 2 has nothing to refer to.

Facade: MultiValueMap.putAll(Map) (allowed instance target of BATCH9_PREREGISTRATION.md row 331; facade_planned_by null, no facade
reuse). The other allowed target, MultiValueMap.removeMapping, was not used: its only removable steps are the null check (an NPE that
leaves the gold's "false" return a half-handled pair), the "not removed" early return (leaves the removal result unused, T2, or the
@return "false otherwise" unmet, T4) and the drop of an emptied key, which two existing tests catch (testMapEquals and
testRemove_KeyItem), so no single trigger.
Original computation of the facade: if the given map is a MultiMap, each of its entries (key -> Collection of values) is added with
putAll(key, collection), so every value lands in this map's collection at that key; otherwise each entry is added with
put(key, value).

facade_variant: V2 (receiver as parameter). The computation needs the receiver's public methods put(K, Object) and
putAll(K, Collection); the facade reads no field. The facade passes `this` (typed MultiValueMap<K, V>, the declaring class) and the
given map to hop 1; the hops call only public methods of the receiver. No private method is called (no V4), no package-private type
passes through the chain (no V3/V5). No signature, modifier, override, annotation or throws change; no new type; no reflection; no
test edit.
state_passed: the receiver `this` (as MultiValueMap<K, V>) and the parameter map to hop 1; no field is read or written back (void).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-27-probe/w the first
statement of putAll(Map) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (and, separately,
removeMapping's with "PROBE-REACHED-RM"). `defects4j test -t` on MultiValueMapTest::testPutAll_Map1 and ::testPutAll_Map2: each 1
failing test, java.lang.IllegalStateException: PROBE-REACHED at MultiValueMap.putAll(MultiValueMap.java:293); testRemove_KeyItem and
testMapEquals each fail with PROBE-REACHED-RM at MultiValueMap.removeMapping(MultiValueMap.java:213). Full suite with the putAll probe
only: 2 failing tests (testPutAll_Map1, testPutAll_Map2); putAll(Map) has no production caller reached by any other test.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of batch9_tasks.json, in that order, none substituted; all five are public
top-level classes in which a public static generic method compiles):
  hop 1 bidimap.TreeBidiMap        2228 lines  putAllValues    pass-through
  hop 2 CollectionUtils            1892 lines  addAllMappings  pass-through
  hop 3 MapUtils                   1797 lines  putAllMappings  pass-through
  hop 4 IteratorUtils              1523 lines  copyMappings    pass-through
  hop 5 map.AbstractHashedMap      1389 lines  addAllEntries   the per-entry core: for each entry of the source, the decision
                                                               between adding the entry's collection of values (multi map) and
                                                               adding the entry's value (plain map)
Host newline counts 2228, 1892, 1797, 1523, 1389; the smallest host is AbstractHashedMap (1389 lines), which is also the gold host.
Anchors (stageB_lib.pick_anchor with seed 7109 + 100 + i, as mr3_spec.py inserts them): hop 1 after TreeBidiMap.nextKey (seed 7209),
hop 2 after CollectionUtils.sizeIsEmpty (7210), hop 3 after MapUtils.populateMap (7211, the 4-argument overload), hop 4 after
IteratorUtils.filteredListIterator (7212), hop 5 after AbstractHashedMap.values (7213); all in the outer classes.
The correct configuration behaves exactly as the original facade: the source-map decision is loop-invariant, so the per-entry form in
the gold adds the same values in the same entry order as the original two loops.

Fault (omission of a special-case decision in the gold): the decision that adds a multi map's entry as its collection of values is
dropped, so every entry is added with put(key, value); for a MultiMap source the whole value collection is added as one element. The
gold then reads as the ordinary routine "for each entry, put the value at its key". Trigger: the EXISTING test
MultiValueMapTest::testPutAll_Map1 (source: a MultiValueMap with key -> [object1, object2]); assertEquals(2, test.size()) still holds,
and assertEquals(4, test.totalSize()) fails with expected:<4> but was:<3> (the collection at "key" is [object0, [object1, object2]]).
It is the only test that newly fails: testPutAll_Map2 copies a plain HashMap (unchanged path), the facade has no production caller and
no other test calls it (the probe's full-suite run), and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (every value of the specified map is added to the collection stored against its
key) and is silent on the kind of source map; for the trigger's MultiValueMap source the values are object1 and object2
(MultiValueMap.values: "the combination of values from all keys"), which the variant never adds. The convention is pinned outside the
gold: AbstractMultiValuedMap.putAll(MultiValuedMap) (production: copies a multi-valued source by calling put(k, v) once for each
mapping from key k to value v), MultiValueMap.values and MultiValueMap.totalSize (a multi map's values are the elements of its
collections), with the passing tests MultiValuedHashMapTest::testPutAll_Map1 (the same 4-value / 3-at-"key" outcome for the sibling
multi-valued map), MultiValueMapTest::testPutAll_KeyCollection (adding a collection at a key adds each of its values) and
MultiValueMapTest::testValues (six values for three keys); the facade's own javadoc ("If you call this method with a multi map, each
entry is added using putAll(Object,Collection)") is kept unchanged.

Single owner: only the gold reads the source's entries and decides how each is added; hops 1-4 pass the receiver and the source map
along unchanged. No one-line change of the two arguments above the gold restores the values: the gold puts each entry's value as one
element, and no Map handed to it can carry two values for one key. Declared alternatives (G9): hop 2 hands a multi map back to the
receiver's own putAll (re-enters the chain: StackOverflowError); hop 4 copies the mappings into a plain HashMap before adding them (the
collections are still added as single elements). Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's work with another implementation, not repairs of the chain):
 B-1 a hop re-implements the multi-map case before calling on, e.g. in hop 4
     `if (map instanceof MultiMap) { for (Map.Entry<? extends K, ?> e : map.entrySet()) { target.putAll(e.getKey(),
     (Collection<V>) e.getValue()); } return; }`: the gold is then never reached for multi maps and still adds a collection as one
     value against its own javadoc. Checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie placement: the facade's javadoc is separated from its header by the annotations @Override and @SuppressWarnings("unchecked"),
so the recipe's rewrite_facade finds no adjacent javadoc and appends nothing; a behaviour-preserving pre_edit (chain) therefore
appends the lie sentence to the end of the javadoc's main description (after "added using putAll(Object,Collection)."), in the
javadoc's own voice, before the @param clause. The annotations, the signature and the other javadoc text are unchanged.
Lie: the facade's javadoc claims the mappings are first sorted by key into a temporary list, which is then merged into this map
one key at a time; the chain sorts nothing, builds no temporary list, and adds the entries in the source's own iteration order. It
names neither the kind of source map, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (loop over map.entrySet(); `if (map instanceof org.apache.commons.collections4.MultiMap)` target.putAll(key,
 (Collection<V>) value) else target.put(key, value)):
  T1 absent: target receives every putAll/put; map is iterated and tested; no argument check.
  T2 absent: the only local, entry, gives the key and the value to both calls; no literal-initialised local, no cursor, counter, flag
     or best-so-far; the two branches call different methods with different effects.
  T3 absent: both members of the source-kind decision (multi map, other map) have their branch; key and value are both passed in
     both branches; no enum or type code is involved. No pattern to rewrite.
  T4 absent: "Adds every value of the specified map to the collection stored against its key in the target map" is a general
     description met by the loop; the @param clauses name no rule.
 Variant gold (javadoc, signature, `for (final Map.Entry<? extends K, ?> entry : map.entrySet()) { target.put(entry.getKey(),
 entry.getValue()); }`):
  T1 absent: target receives every put; map supplies every entry; both decide the side effect; no argument check.
  T2 absent: entry is read for the key and for the value passed to put; no other local; no literal-initialised local; the for-each
     loop has no cursor, write position, counter, flag or best-so-far of its own; no branch, case or ternary.
  T3 absent: key and value (the pair halves) are both passed; no source-kind, value-kind or special-value test remains for any
     member ("No member handled"); the gold's text names no class of maps or values that it would handle in part (no "multi",
     "collection of values", "null" or "finite" phrase about the source).
  T4 absent: "Adds every value of the specified map to the collection stored against its key in the target map" is a general
     description that the put loop addresses (like "joins the elements"); "@param target  the map to add the values to" and
     "@param map  the map whose values are added" name no concrete rule, limit or case; no inline comment; the identifiers target,
     map, entry and addAllEntries name what they hold or do."""

MVM = "src/main/java/org/apache/commons/collections4/map/MultiValueMap.java"
TBM = "src/main/java/org/apache/commons/collections4/bidimap/TreeBidiMap.java"
CU = "src/main/java/org/apache/commons/collections4/CollectionUtils.java"
MU = "src/main/java/org/apache/commons/collections4/MapUtils.java"
IU = "src/main/java/org/apache/commons/collections4/IteratorUtils.java"
AHM = "src/main/java/org/apache/commons/collections4/map/AbstractHashedMap.java"

GOLD_TEXT = '''/**
 * Adds every value of the specified map to the collection stored against
 * its key in the target map.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target  the map to add the values to
 * @param map  the map whose values are added
 */
public static <K, V> void addAllEntries(final MultiValueMap<K, V> target, final Map<? extends K, ?> map) {
    for (final Map.Entry<? extends K, ?> entry : map.entrySet()) {
        if (map instanceof org.apache.commons.collections4.MultiMap) {
            target.putAll(entry.getKey(), (Collection<V>) entry.getValue());
        } else {
            target.put(entry.getKey(), entry.getValue());
        }
    }
}'''

HOP1 = '''/**
 * Adds every value of the specified map to the collection stored against
 * its key in the target map.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target the map to add the values to
 * @param map the map whose values are added
 */
public static <K, V> void putAllValues(final MultiValueMap<K, V> target, final Map<? extends K, ?> map) {
    CollectionUtils.addAllMappings(target, map);
}'''

HOP2 = '''/**
 * Adds all the mappings of the specified map to the target map, each value
 * to the collection stored against its key.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target  the map to add to
 * @param map  the map whose mappings are added
 */
public static <K, V> void addAllMappings(final MultiValueMap<K, V> target, final Map<? extends K, ?> map) {
    MapUtils.putAllMappings(target, map);
}'''

HOP3 = '''/**
 * Puts all the mappings of the specified map into the target map, each value
 * being added to the collection stored against its key.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target the <code>MultiValueMap</code> to add to
 * @param map the <code>Map</code> whose mappings are added
 */
public static <K, V> void putAllMappings(final MultiValueMap<K, V> target, final Map<? extends K, ?> map) {
    IteratorUtils.copyMappings(target, map);
}'''

HOP4 = '''/**
 * Copies the mappings of the specified map into the target map, adding each
 * value to the collection stored against its key.
 *
 * @param <K>  the key type
 * @param <V>  the value type
 * @param target  the map to copy into
 * @param map  the map whose mappings are copied
 */
public static <K, V> void copyMappings(final MultiValueMap<K, V> target, final Map<? extends K, ?> map) {
    AbstractHashedMap.addAllEntries(target, map);
}'''

DESIGN = {
 "instance": "Collections-27", "project": "Collections", "bug_id": 27, "seed": 7109,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": MVM, "class": "org.apache.commons.collections4.map.MultiValueMap", "method": "putAll", "near_line": 291},
 "facade_variant": "V2",
 "state_passed": "the receiver this (as MultiValueMap<K, V>) and the parameter map to hop 1; no field read, no write-back (void)",
 "reachability_probe": "testPutAll_Map1 and testPutAll_Map2 each fail with java.lang.IllegalStateException: PROBE-REACHED at "
                       "MultiValueMap.putAll(MultiValueMap.java:293); full suite with the probe: 2 failing tests (those two); "
                       "removeMapping probe reached by testRemove_KeyItem and testMapEquals",
 "host_mode": "largest5",
 "host_lines": [2228, 1892, 1797, 1523, 1389],
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/collections4/map/MultiValueMapTest.java",
             "test_class": "org.apache.commons.collections4.map.MultiValueMapTest", "test_method": "testPutAll_Map1"},
 "expected_signature": "expected:<4> but was:<3>",
 "gold": {"method": "addAllEntries", "text": GOLD_TEXT,
          "fault": {"old": "        for (final Map.Entry<? extends K, ?> entry : map.entrySet()) {\n"
                           "            if (map instanceof org.apache.commons.collections4.MultiMap) {\n"
                           "                target.putAll(entry.getKey(), (Collection<V>) entry.getValue());\n"
                           "            } else {\n"
                           "                target.put(entry.getKey(), entry.getValue());\n"
                           "            }\n"
                           "        }\n",
                    "new": "        for (final Map.Entry<? extends K, ?> entry : map.entrySet()) {\n"
                           "            target.put(entry.getKey(), entry.getValue());\n"
                           "        }\n"}},
 "chain": {
   "facade_body": "org.apache.commons.collections4.bidimap.TreeBidiMap.putAllValues(this, map);",
   "lie": "The mappings are first sorted by key into a temporary list, which is then merged into this map one key at a time.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections4.bidimap.TreeBidiMap", "method": "putAllValues",
      "imports": ["org.apache.commons.collections4.CollectionUtils", "org.apache.commons.collections4.map.MultiValueMap"],
      "text": HOP1},
     {"file": CU, "class": "org.apache.commons.collections4.CollectionUtils", "method": "addAllMappings",
      "imports": ["org.apache.commons.collections4.map.MultiValueMap"], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections4.MapUtils", "method": "putAllMappings",
      "imports": [], "text": HOP3},
     {"file": IU, "class": "org.apache.commons.collections4.IteratorUtils", "method": "copyMappings",
      "imports": ["org.apache.commons.collections4.map.AbstractHashedMap", "org.apache.commons.collections4.map.MultiValueMap"],
      "text": HOP4},
     {"file": AHM, "class": "org.apache.commons.collections4.map.AbstractHashedMap", "method": "addAllEntries", "imports": [],
      "gold": True},
   ],
 },
 "pre_edits": {"chain": [
   {"file": MVM,
    "old": "     * added using <code>putAll(Object,Collection)</code>.\n     *\n     * @param map  the map to copy (either a normal or multi map)\n",
    "new": "     * added using <code>putAll(Object,Collection)</code>.\n"
           "     * The mappings are first sorted by key into a temporary list, which is then merged into this map one key at a time.\n"
           "     *\n     * @param map  the map to copy (either a normal or multi map)\n"},
 ]},
 "evidence": ["org.apache.commons.collections4.multimap.AbstractMultiValuedMap::putAll",
              "org.apache.commons.collections4.map.MultiValueMap::values",
              "org.apache.commons.collections4.map.MultiValueMap::totalSize"],
 "ownership_reason": "Only the gold reads the entries of the source map and decides how each is added to the receiver (the entry's "
                     "collection of values for a multi map, the entry's value otherwise); hops 1-4 pass the receiver and the "
                     "source map along unchanged. The gold's javadoc promises that every value of the specified map is added to "
                     "the collection stored against its key; for the trigger's MultiValueMap source the values are object1 and "
                     "object2 (MultiValueMap.values: the combination of values from all keys; MultiValueMap.totalSize counts "
                     "them), and the variant adds the collection [object1, object2] as a single value instead. No one-line "
                     "change of the two arguments above the gold restores the values: the gold puts each entry's value as one "
                     "element and no Map handed to it can hold two values for one key. The convention is pinned outside the "
                     "gold: AbstractMultiValuedMap.putAll(MultiValuedMap) copies a multi-valued source by calling put(k, v) once "
                     "for each mapping from key k to value v (MultiValuedHashMapTest testPutAll_Map1: 4 values, 3 at \"key\"); "
                     "MultiValueMap.putAll(Object, Collection) adds each value of a collection at its key "
                     "(MultiValueMapTest testPutAll_KeyCollection); MultiValueMapTest testValues counts six values for three "
                     "keys; the facade's own javadoc says a multi map's entries are added using putAll(Object,Collection).",
 "ownership_tests": ["org.apache.commons.collections4.multimap.MultiValuedHashMapTest::testPutAll_Map1",
                     "org.apache.commons.collections4.map.MultiValueMapTest::testPutAll_KeyCollection",
                     "org.apache.commons.collections4.map.MultiValueMapTest::testValues"],
 "compensating": {
   "chain": [
     {"file": CU, "old": "        MapUtils.putAllMappings(target, map);",
      "new": "        if (map instanceof MultiMap) { target.putAll(map); return; } MapUtils.putAllMappings(target, map);",
      "why": "hop 2 hands a multi map back to the receiver's own putAll"},
     {"file": IU, "old": "        AbstractHashedMap.addAllEntries(target, map);",
      "new": "        AbstractHashedMap.addAllEntries(target, new java.util.HashMap<K, Object>(map));",
      "why": "hop 4 copies the mappings into a plain HashMap before adding them"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted: bidimap.TreeBidiMap (hop 1, 2228 lines), CollectionUtils (hop 2, 1892), MapUtils (hop 3, 1797), "
               "IteratorUtils (hop 4, 1523), map.AbstractHashedMap (hop 5, gold, 1389; the smallest host). All five are public "
               "top-level classes in which a public static generic method compiles (TreeBidiMap's own type parameters are not "
               "visible in a static method; the hop declares its own). The facade's file MultiValueMap.java is excluded. Anchors "
               "from stageB_lib.pick_anchor with seed 7109 + 100 + i (as mr3_spec.py inserts them): hop 1 after "
               "TreeBidiMap.nextKey (line idx 357, seed 7209), hop 2 after CollectionUtils.sizeIsEmpty (1390, 7210), hop 3 after "
               "MapUtils.populateMap (1721, 7211), hop 4 after IteratorUtils.filteredListIterator (762, 7212), hop 5 after "
               "AbstractHashedMap.values (992, 7213); all in the outer class. The facade calls hop 1 by its fully-qualified name; "
               "each hop imports the next host where it is in another package and MultiValueMap where needed.",
}
