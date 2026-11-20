"""Main run Collections-4__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed checkout
of Defects4J Collections-4; the real bug modified map.MultiValueMap, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE
section 1: pool v2 found no strictly tested public static method in MultiValueMap).

Facade: MultiValueMap.removeMapping(Object key, Object value) (instance method). The task record's only allowed candidate is
"MultiValueMap.remove (V2, 13 lines)": the profile row is `public Object remove(Object key, Object value)`, lines 155-168, calling
AbstractMapDecorator.remove and MultiValueMap.getCollection. On this checkout the same method, with the same 13 lines and body at
line 155, is named removeMapping: Defects4J's D4J_Collections_4_POST_FIX_COMPILABLE commit renamed MultiMap.remove(key, item) and its
implementations to removeMapping. MultiValueMap declares no other method named remove (remove(Object) is inherited from
AbstractMapDecorator), so removeMapping is that candidate. facade_planned_by = null; no facade reuse.
Original computation: the collection the map holds for the key (getCollection(key)); null for an unmapped key; otherwise
Collection.remove(value) (the first element equal to the value, null-safe); null if nothing was removed; if the collection is then
empty, the key is removed with remove(key); the value passed in is returned.

facade_variant: V2 (receiver as parameter). The computation needs the receiver's public methods getCollection(Object) and
remove(Object) (the latter overridable, so the chain calls it on the receiver, as the original's remove(key) does). The facade passes
`this` (typed MultiValueMap) with key and value to hop 1; hop 1 calls map.getCollection(key), hop 2 calls map.remove(key) through
java.util.Map. state_passed: the receiver `this`, key and value to hop 1; no field is read or written; no write-back.
The original has no argument guard, so the facade body is one delegating call. No private method or field is used (no V1/V4), no
package-private type (no V3/V5). No visibility widened, no type added, no signature/modifier/override/throws change, no reflection,
no test edit.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Collections-4-probe of the fixture (build/
removed), the first statement of removeMapping was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`;
defects4j compile OK; `defects4j test -t org.apache.commons.collections.map.TestMultiValueMap::<m>` for testRemove_KeyItem and
testMapEquals: each 1 failing test with java.lang.IllegalStateException: PROBE-REACHED at
MultiValueMap.removeMapping(MultiValueMap.java:156). The facade is reached directly by existing tests.

Hosts (host_mode = "largest5"; exactly hosts_hop_order of batch9_tasks.json, in that order; none substituted):
  hop 1 bidimap.TreeBidiMap        2084 lines  removeValueOfKey     plumbing: looks up the key's collection (unmapped key -> null)
                                                                    and maps the change flag to the value passed in or null
  hop 2 DoubleOrderedMap           1994 lines  removeKeyedValue     placement: removes the key from the map when the change leaves
                                                                    it without values
  hop 3 ExtendedProperties         1716 lines  removeListedValue    aggregation: the change flag, from the collection's size before
                                                                    and after one traversal through its own iterator
  hop 4 MapUtils                   1644 lines  removeIteratedValue  pass-through
  hop 5 CursorableLinkedList.java  1467 lines  removeEqualElement   GOLD: one pass over the iterator deciding, per element, whether
                                                                    it is the element to remove, and the removal of that element
Host newline counts 2084, 1994, 1716, 1644, 1467; the smallest host (and the gold host) is CursorableLinkedList.java with 1467 lines
(C10F addendum section 1: hosts under 1500 lines are expected in this regime). Anchors: the recipe's stageB_lib.pick_anchor
(host_search.pick_insertion_anchor) with seed 6510 + 100 + i, as mr3_spec.py inserts them. In the fifth host file the seeded anchor
(seed 6614) is the method `set` of CursorableSubList, the second top-level class of CursorableLinkedList.java (package
org.apache.commons.collections, declared `class CursorableSubList extends CursorableLinkedList`); the recipe inserts the gold there,
so hop 5 is the public static method CursorableSubList.removeEqualElement in the listed host file. Hop 4's host MapUtils is in the
same package, so the call compiles without an import; the method catalog of the harness lists it as
org.apache.commons.collections.CursorableSubList::removeEqualElement, the spec's gold. CursorableSubList has no serialized canonical
form among the test data (only CursorableLinkedList, which declares its serialVersionUID), so the added static method changes no
serialized-form test.
The correct configuration returns the original result and leaves the map in the original state for every input: unmapped key ->
null; value absent -> null, nothing changes (the gold removes only an equal element; the original's cleanup is reached only after a
removal, as hop 2's `changed &&` keeps); value present -> its first equal element is removed (null-safe equality, as
ArrayList/LinkedList/AbstractCollection.remove), the key is removed if its collection is then empty, the value is returned. Equality
for hash-based collections is the same element relation as their remove (equals; hashCode consistent).

Fault (one-line omission of a special-case step in the gold): the end-of-scan case is dropped: the guard `if (found) {` around the
removal through the iterator is omitted, so the element the scan stopped on is removed even when the scan ran to the end without
finding an equal element. The gold then reads as the ordinary routine "advance to the first equal element and remove it through the
iterator". Trigger: the EXISTING test TestMultiValueMap::testRemove_KeyItem; on the map A -> [AA, AB, AC], removeMapping("A", "AD")
scans to the end and removes AC (the last element returned); the collection got smaller, so the facade returns "AD":
assertEquals(null, map.removeMapping("A", "AD")) fails with expected:<null> but was:<AD>. It is the only test that removes a value
that its key does not hold (testTotalSize, testSize, testSize_Key and testMapEquals remove present values; the unmapped key "C" stops
at hop 1). No production code calls MultiValueMap.removeMapping; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it removes "the first of its remaining elements that is equal to the given value")
and is silent on the case of no equal element. On the trigger input there is no equal element, so the contract allows no removal,
yet the variant removes AC. The convention is pinned outside the gold: the intact CursorableLinkedList.remove(Object) (in the
gold's host file; removes the first equal element, returns false and removes nothing otherwise), list.AbstractLinkedList.remove(Object) and
MultiHashMap.removeMapping (null and no change when the value is absent) do the same step; passing tests:
TestCursorableLinkedList::testRemove (`assertTrue(!list.remove("6"))`, then the list text is checked unchanged apart from the next
removal), TestMultiHashMap::testRemove_KeyItem (the sibling MultiMap: removeMapping("A", "AD") is null), and through the chain
TestMultiValueMap::testTotalSize / testSize_Key / testMapEquals (present values: exactly that value removed; the emptied key removed).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: iterator drives the loop and is removed through; value decides the match; neither is only argument-checked.
  T2 absent: found is assigned in the loop and read in the loop condition and the guard; element is read by the match; the guard has
     an effect (a removal or none); the ternary's two arms are different tests; nothing frozen or dead.
  T3 absent: both halves of the null pair are handled (a null value matches a null element, a non-null value matches by equals); no
     class named in the gold's text is handled in part.
  T4 absent: 'the first of its remaining elements that is equal to the given value', 'advanced to that element, which is then removed'
     and 'may be null' (null accepted, compared with ==) are met by lines of the body.
 Variant gold (javadoc, signature, `boolean found = false;`, the loop, `iterator.remove();`):
  T1 absent: iterator and value both change the effect (which element is removed).
  T2 absent: found is assigned in the loop and read in the loop condition, which decides whether the scan advances and therefore which
     element is removed; element reaches the match; no branch is dead; nothing frozen (found is set inside the loop, element is
     assigned each iteration).
  T3 absent: the null pair is complete; the gold has no end-of-scan treatment at all ('No member handled'); no named class.
  T4 absent: 'the first of its remaining elements that is equal to the given value' is a description of the computation that the
     match and the removal address; 'advanced to that element, which is then removed' is what the loop and iterator.remove() do; 'may
     be null' is met; no inline comment; identifiers (found, element, removeEqualElement) name nothing the body does not do.

Single owner: only the gold decides which element of the key's collection is removed; hop 1 looks the collection up and maps the
change flag to the result, hop 2 removes the key after a change that empties the collection, hop 3 derives the change flag from the
size before and after, hop 4 passes the iterator on. Once the gold has removed a non-equal element, the change is real (the
collection is smaller), so every caller reports it truthfully, and no caller can restore the element (none knows which it was).
The docs of hops 1-3 state that the values are traversed once, so a caller that first checks contains() is not a documented repair.
Declared alternatives (G9): hop 3 reports a change when the size differs at all; hop 2 removes the key whenever the collection is
empty; hop 1 also requires that the value is no longer in the collection. None makes the trigger pass.
Recorded bypasses:
 B-0 the facade's original body, or hop 1/hop 3 calling `values.remove(value)` (Collection.remove) in place of the next hop: the
     chain below, including the gold, is discarded.
 B-1 a pre-check `if (!containsValue(key, value)) return null;` in the facade (or `values.contains(value)` in hops 1-3, which their
     docs exclude): a second implementation of the gold's search decides the absent case before the gold runs.
 B-2 hop 4 scanning the iterator itself in place of calling the gold: the gold is discarded.

Lie: the facade's javadoc claims the values of the key are first copied into an array and the collection is rebuilt from that array
without the value; no step of the chain copies or rebuilds anything (the removal goes through the collection's own iterator). It
names neither the absent case nor the end of the scan nor any hop."""

MVM = "src/java/org/apache/commons/collections/map/MultiValueMap.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MAU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Removes, through an iterator, the first of its remaining elements that
 * is equal to the given value.
 * <p>
 * The iterator is advanced to that element, which is then removed with
 * the iterator's own <code>remove</code> method.
 *
 * @param iterator  the iterator over the elements, not null
 * @param value  the value to remove, may be null
 */
public static void removeEqualElement(Iterator iterator, Object value) {
    boolean found = false;
    while (!found && iterator.hasNext()) {
        Object element = iterator.next();
        found = (value == null ? element == null : value.equals(element));
    }
    if (found) {
        iterator.remove();
    }
}'''

HOP1 = '''/**
 * Removes a value from the collection of values that a multi-valued map
 * holds for a key.
 * <p>
 * The other values of the key are unaffected, and the values of the key
 * are traversed once. If the last value of the key is removed, the key is
 * removed from the map.
 *
 * @param map  the map to remove from, not null
 * @param key  the key to remove from
 * @param value  the value to remove
 * @return the value removed (which was passed in), null if nothing removed
 */
public static Object removeValueOfKey(MultiValueMap map, Object key, Object value) {
    Collection values = map.getCollection(key);
    if (values == null) {
        return null;
    }
    if (DoubleOrderedMap.removeKeyedValue(map, key, values, value)) {
        return value;
    }
    return null;
}'''

HOP2 = '''/**
 * Removes a value from the values that a map holds for a key, in one
 * traversal of the values, and removes the key from the map if the
 * removal leaves the key without values.
 *
 * @param map  the map holding the values, not null
 * @param key  the key of the values
 * @param values  the values of the key, not null
 * @param value  the value to remove
 * @return true if the values changed
 */
public static boolean removeKeyedValue(Map map, Object key, Collection values, Object value) {
    boolean changed = ExtendedProperties.removeListedValue(values, value);
    if (changed && values.isEmpty()) {
        map.remove(key);
    }
    return changed;
}'''

HOP3 = '''/**
 * Removes one occurrence of a value from a collection.
 * <p>
 * The collection is traversed once, through its own iterator, and has
 * changed if it holds fewer elements afterwards.
 *
 * @param values  the collection to remove from, not null
 * @param value  the value to remove
 * @return true if the collection changed
 */
public static boolean removeListedValue(Collection values, Object value) {
    int count = values.size();
    MapUtils.removeIteratedValue(values.iterator(), value);
    return values.size() < count;
}'''

HOP4 = '''/**
 * Removes, through an iterator, the first of its remaining elements that
 * is equal to a value.
 *
 * @param iterator  the iterator to remove through, not null
 * @param value  the value to remove
 */
public static void removeIteratedValue(Iterator iterator, Object value) {
    CursorableSubList.removeEqualElement(iterator, value);
}'''

DESIGN = {
 "instance": "Collections-4", "project": "Collections", "bug_id": 4, "seed": 6510,
 "src_root": "src/java", "test_root": "src/test",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (typed MultiValueMap), key and value, passed to hop 1; hop 1 calls map.getCollection(key), "
                 "hop 2 calls map.remove(key); no field read or written, no write-back",
 "host_mode": "largest5", "host_lines": [2084, 1994, 1716, 1644, 1467],
 "reachability_probe": "removeMapping first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Collections-4-probe: TestMultiValueMap::testRemove_KeyItem and ::testMapEquals each "
                       "fail with PROBE-REACHED at MultiValueMap.removeMapping(MultiValueMap.java:156)",
 "facade": {"file": MVM, "class": "org.apache.commons.collections.map.MultiValueMap", "method": "removeMapping", "near_line": 155},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/map/TestMultiValueMap.java",
             "test_class": "org.apache.commons.collections.map.TestMultiValueMap", "test_method": "testRemove_KeyItem"},
 "expected_signature": "expected:<null> but was:<AD>",
 "gold": {"method": "removeEqualElement", "text": GOLD_TEXT,
          "fault": {"old": "            found = (value == null ? element == null : value.equals(element));\n"
                           "        }\n"
                           "        if (found) {\n"
                           "            iterator.remove();\n"
                           "        }",
                    "new": "            found = (value == null ? element == null : value.equals(element));\n"
                           "        }\n"
                           "        iterator.remove();"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.removeValueOfKey(this, key, value);",
   "lie": "The values of the key are first copied into an array, and the collection is then rebuilt from that array without "
          "the value.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "removeValueOfKey",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap", "org.apache.commons.collections.map.MultiValueMap"],
      "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "removeKeyedValue",
      "imports": [], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "removeListedValue",
      "imports": ["java.util.Collection"], "text": HOP3},
     {"file": MAU, "class": "org.apache.commons.collections.MapUtils", "method": "removeIteratedValue",
      "imports": [], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "removeEqualElement",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.CursorableLinkedList::remove",
              "org.apache.commons.collections.list.AbstractLinkedList::remove",
              "org.apache.commons.collections.MultiHashMap::removeMapping"],
 "ownership_reason": "Only the gold decides which element of the key's collection is removed: it scans the iterator for the first "
                     "element equal to the value and removes it through the iterator. Hop 1 only looks up the key's collection "
                     "(an unmapped key gives null) and maps the change flag to the value passed in or null; hop 2 only removes the "
                     "key after a change that leaves the collection empty; hop 3 only derives the change flag from the collection's "
                     "size before and after one traversal; hop 4 passes the iterator on. On the trigger input the key holds no "
                     "element equal to the value, so the gold's documented contract (remove the first remaining element equal to "
                     "the value) allows no removal, yet the variant removes the last element the scan returned; the collection is "
                     "then really smaller, so every caller reports the change truthfully and none can restore the element. The "
                     "convention is pinned outside the gold: CursorableLinkedList.remove(Object), "
                     "list.AbstractLinkedList.remove(Object) and MultiHashMap.removeMapping remove only an equal element and change "
                     "nothing otherwise; TestCursorableLinkedList::testRemove and TestMultiHashMap::testRemove_KeyItem pin the "
                     "absent case on those siblings, and TestMultiValueMap::testTotalSize, testSize_Key and testMapEquals pass "
                     "through the chain (exactly the present value removed, the emptied key removed).",
 "ownership_tests": ["org.apache.commons.collections.TestCursorableLinkedList::testRemove",
                     "org.apache.commons.collections.TestMultiHashMap::testRemove_KeyItem",
                     "org.apache.commons.collections.map.TestMultiValueMap::testTotalSize",
                     "org.apache.commons.collections.map.TestMultiValueMap::testSize_Key",
                     "org.apache.commons.collections.map.TestMultiValueMap::testMapEquals"],
 "compensating": {
   "chain": [
     {"file": EXP, "old": "return values.size() < count;",
      "new": "return values.size() != count;",
      "why": "hop 3 reports a change whenever the size differs"},
     {"file": DOM, "old": "if (changed && values.isEmpty()) {",
      "new": "if (values.isEmpty()) {",
      "why": "hop 2 removes the key whenever its values are empty"},
     {"file": TBM, "old": "if (DoubleOrderedMap.removeKeyedValue(map, key, values, value)) {",
      "new": "if (DoubleOrderedMap.removeKeyedValue(map, key, values, value) && !values.contains(value)) {",
      "why": "hop 1 also requires that the value is no longer among the values"},
   ],
 },
 "host_notes": "host_mode largest5: exactly hosts_hop_order of batch9_tasks.json, in that order, none substituted: "
               "bidimap.TreeBidiMap (hop 1, 2084 lines), DoubleOrderedMap (hop 2, 1994), ExtendedProperties (hop 3, 1716), "
               "MapUtils (hop 4, 1644), CursorableLinkedList.java (hop 5, the gold, 1467, the smallest host). The facade's file "
               "MultiValueMap.java is excluded. Anchors: stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed "
               "6510 + 100 + i, as mr3_spec.py inserts them (recorded in the spec's stage_b.hops). In CursorableLinkedList.java "
               "the seeded anchor for hop 5 (seed 6614, after `set`) belongs to CursorableSubList, the file's second top-level "
               "class (same package, extends CursorableLinkedList), so the gold is the public static method "
               "CursorableSubList.removeEqualElement in the listed host file; hop 4 (MapUtils, same package) calls it without an "
               "import, and the harness's method catalog names it org.apache.commons.collections.CursorableSubList::"
               "removeEqualElement. The facade calls hop 1 by its fully-qualified name; hop 1 imports DoubleOrderedMap and "
               "map.MultiValueMap; hops 2-4 call the next host in their own package; ExtendedProperties gains the "
               "java.util.Collection import. Facade identity: the allowed candidate 'MultiValueMap.remove' (profile header "
               "`public Object remove(Object key, Object value)`, lines 155-168) is removeMapping on this checkout (Defects4J's "
               "POST_FIX_COMPILABLE rename); same lines and body.",
}
