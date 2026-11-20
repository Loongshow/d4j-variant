"""Main run Collections-15__i (cell C10i, batch 7: the paired static/instance bridge; the C10 recipe with an INSTANCE-method facade on
the fixed checkout of Defects4J Collections-15; the real bug modified SetUniqueList, the facade's class).

Facade: SetUniqueList.addAll(int, Collection) (allowed instance candidate "SetUniqueList.addAll", 16 lines, variant V2,
bridge7_tasks.json; the paired static facade SetUniqueList.decorate is not used; facade_reuse_of = Collections-5__i, recorded).
The int overload is the method the candidate describes (it calls size() and add(int, Object) of the receiver); addAll(Collection)
stays intact and keeps delegating to it with size() as the index. The other allowed candidate, add(Object), is a three-statement
append whose only decision is the receiver's own.
Original computation: the size before; then, for every element of the collection in iterator order, add(index, element) on the
receiver (which inserts only an element its set does not yet hold) and, if the size grew, index++; the result is whether the size
changed.

facade_variant: V2 (receiver as parameter). state_passed: `this` (the receiver, typed java.util.List, which SetUniqueList
implements), the index and the collection are handed to hop 1; no field is read or written by the facade, and there is no
write-back. The hops call only public List methods of the receiver: size(), contains(Object) and add(int, Object).
facade_body: `return org.apache.commons.collections.bidimap.TreeBidiMap.insertAllAt(this, index, coll);` (no guard: the original
had none).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-15-probe of the
fixture, the first statement of addAll(int, Collection) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`
(the wrapper keeps the rest of the body reachable for javac). `defects4j test -t
org.apache.commons.collections.list.TestSetUniqueList::testIntCollectionAddAll`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at SetUniqueList.addAll(SetUniqueList.java:190) called from TestSetUniqueList.testIntCollectionAddAll
(TestSetUniqueList.java:158). Full suite with the probe: 40 failing tests, all in TestSetUniqueList (testIntCollectionAddAll,
testFactory, testAddAll, testCollectionAddAll and every test that fills the list through makeFullList -> addAll(Collection)).
The facade is reached by an existing test directly.

Hosts (host_mode = "largest5"; hosts_hop_order of the task record, in that order, none substituted):
  hop 1 bidimap.TreeBidiMap         2085 lines  insertAllAt       aggregation: the size before and after; the result is whether it
                                                                  changed
  hop 2 DoubleOrderedMap            1995 lines  insertElementsOf  conversion: the elements are taken from the collection's iterator
  hop 3 ExtendedProperties          1784 lines  addElementsAt     pass-through
  hop 4 MapUtils                    1678 lines  insertElements    pass-through
  hop 5 CursorableLinkedList        1468 lines  insertEachAt      GOLD: the insertion loop: per element, the membership test and the
                                                                  insertion at the current position, which then moves past it
Host newline counts 2085, 1995, 1784, 1678, 1468; the smallest host (and the gold host) has 1468 lines (below 1500, expected under
largest5, BUILD_BRIEF_C10F_ADDENDUM section 1).
The correct configuration returns the original result and leaves the receiver in the original state for every input: the same
size-based change report, the same iteration over coll.iterator(), the same per-element decision (SetUniqueList.contains and
SetUniqueList.add(int, Object) both consult the receiver's set, which a sub-list view shares with its backing list), the same
insertion position (it moves only after an insertion), and the same exceptions (an out-of-range index throws from the receiver's
add only when an element is actually inserted, as before).

Fault (one-line omission of a decision in the gold): the membership test `if(!list.contains(elt)) {` (with its closing brace) is
dropped, so every element is passed to list.add(at++, elt) and the position moves past it whether or not the list took it. The
variant gold then reads as the ordinary insert-all-at-index routine (the shape of java.util.AbstractList.addAll(int, Collection)
and of CursorableLinkedList's own addAll(int, Collection)). Trigger: the EXISTING test TestSetUniqueList::testIntCollectionAddAll.
Its first half (addAll(0, [2, 3]) into [1]) still holds; in its second half the list is [2, 3, 1] and addAll(0, [1, 4]) runs:
SetUniqueList.add(0, 1) declines the element it already holds, the position still moves to 1, 4 is inserted at index 1 and the
list becomes [2, 4, 3, 1]; the size assertion (4) holds and assertEquals("Third new element should be at index 0", 4, list.get(0))
at line 170 fails with expected:<4> but was:<2>. It is the only test that newly fails: every other addAll on a SetUniqueList in the
suite either appends distinct elements (makeFullList, testCollectionAddAll), has its only repeated element last (testFactory
[1, 2, 1], testAddAll [1, 1]), or checks only fail-fast behaviour (testListSubListFailFastOnAdd); TestSetUniqueList's suite()
is a plain TestSuite, so no sub-list bulk tests run.

The gold's javadoc states the idiomatic contract (it inserts the elements returned by the iterator into the list, starting at the
given position, the inserted elements appearing in iterator order) and is silent on elements the list already holds. On the
trigger input the one inserted element, 4, does not start at position 0. The convention is pinned outside the gold: the facade's
own javadoc ("Only elements that are not already in this list will be added, and duplicates from the specified collection will be
ignored"); ListOrderedSet.addAll(int, Collection), the sibling indexed bulk insertion of the same library, which tests
`contains(object) == false` per element and moves its index only after an insertion, with TestListOrderedSet::testListAddIndexed
and TestListOrderedSet2::testListAddIndexed ([0, 1].addAll(1, [3, 0, 2]) gives [0, 3, 2, 1]) passing; ListOrderedSet.add(int,
Object) and SetUniqueList.add(int, Object) insert only an element not yet held; TestSetUniqueList::testFactory and ::testAddAll pin
that repeated elements of the collection are ignored.

Single owner: only the gold sees each element at the moment it is inserted, together with the position it goes to; hop 1 sees
only the sizes before and after and passes the collection on as given, hop 2 passes every element on through the collection's own
iterator, and hops 3 and 4 pass that iterator on as given (each hop's javadoc says so). Once the gold has moved its position past
a declined element, the element inserted next sits one place too far right, which no caller can undo without rebuilding the list.
Declared alternatives (G9): hop 3 drops repeated elements of the iteration (UniqueFilterIterator); hop 1 copies the collection
into a LinkedHashSet first; hop 4 starts the insertion at Math.min(index, list.size()). None changes the trigger's [1, 4] case (no
repeat inside the collection, index 0).
Recorded bypasses (edits that re-implement the gold's membership test outside the insertion loop, not repairs of the chain):
 B-0 the facade (its original body) or any hop re-implements the loop, making the rest of the chain, including the gold, dead.
 B-1 the facade removes, before the chain, the elements the list already holds and the repeats of the collection:
     `return org.apache.commons.collections.bidimap.TreeBidiMap.insertAllAt(this, index, org.apache.commons.collections.CollectionUtils.removeAll(new java.util.LinkedHashSet(coll), this));`
     Checked on the variant in the scratch copy /private/tmp/d4j-mi-Collections-15-bypass: trigger passes, full suite 0 failing
     tests, and a probe program gives the pristine results for a repeated append ([x] + [5, 5, 6] -> [x, 5, 6]) and for a
     sub-list view ([a] of [a, b, c], addAll(0, [c, d]) -> [d, a]). It is the gold's omitted contains test moved up to the facade
     and applied to the whole collection at once (ListUtils.removeAll calls remove.contains per element): the gold's own decision
     and the receiver's decline in add(int, Object) then never fire on this path.
 B-2 the same filter at a hop (hop 1 or 2: CollectionUtils.removeAll(new java.util.LinkedHashSet(coll), list); hop 3 or 4 after
     draining the iterator with IteratorUtils.toList) also passes the suite (checked at hop 2: trigger passes, full suite 0
     failing tests, probe results pristine), but it contradicts that hop's own javadoc (hop 1: 'The collection is passed on as
     given'; hop 2: 'Every element of the collection is passed on'; hops 3 and 4: 'The iterator is passed on as given'), so it
     is not consistent with the path. A lazy filter (FilterIterator with an anonymous Predicate calling list.contains) would
     need the hop's parameter made final as well (source level 1.6), so it is not a one-line edit. A filter by the list's
     elements without the repeats (CollectionUtils.subtract(coll, list)) is not even equivalent: a repeated append ([5, 5, 6])
     throws IndexOutOfBoundsException and a sub-list view gives [a, d] instead of [d, a] (checked with the probe program).

Lie: the facade's javadoc claims the collection is first copied into an array whose elements are then read in index order; the
chain copies nothing and reads the collection through its iterator. It names neither membership, nor repeated elements, nor the
insertion position, nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `int at = index; while(it.hasNext()) { Object elt = it.next(); if(!list.contains(elt)) { list.add(at++,
 elt); } }`):
  T1 absent: list is read by contains and written by add, index seeds the position, it drives the loop and supplies every element.
  T2 absent: at is advanced inside the loop (at++), elt is read by the test and the add; no literal-initialised local; the single if
     decides whether the add runs.
  T3 absent: one membership decision per element; no pair, range end, enumerated case or named class appears; nothing to rewrite.
  T4 absent: 'starting at the specified position', 'in the order that they are returned by the iterator' and 'index at which to
     insert the first element' are general descriptions the add with its moving position addresses; no limit, value class or case
     is named; no inline comment.
 Variant gold (javadoc, signature, `int at = index; while(it.hasNext()) { Object elt = it.next(); list.add(at++, elt); }`):
  T1 absent: list (add), index (the first position), it (hasNext, next) each change the list's resulting content; no argument check.
  T2 absent: at is assigned in the loop by at++ and used as the insertion position; elt is assigned per iteration and passed to add;
     no literal-initialised local, no flag, counter or best-so-far; no branch remains, so no dead decision.
  T3 absent: no member of any set is handled ('No member handled'): no membership, null, repeat or range test remains; the gold
     names no class it handles in part; no pair half or range end is treated.
  T4 absent: the javadoc names no rule, limit, bound, value class, case or property that the body visibly does not meet: 'starting
     at the specified position' (at = index), 'appear in the list in the order that they are returned by the iterator' (each
     element goes to the next position), '@param index index at which to insert the first element' (the first add uses index);
     identifiers (at, elt, it) name nothing the body does not do."""

SUL = "src/java/org/apache/commons/collections/list/SetUniqueList.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Inserts the elements returned by the specified iterator into the
 * specified list, starting at the specified position.  The inserted
 * elements appear in the list in the order that they are returned by
 * the iterator.
 *
 * @param list list to insert the elements into.
 * @param index index at which to insert the first element.
 * @param it iterator over the elements to be inserted.
 */
public static void insertEachAt(List list, int index, Iterator it) {
    int at = index;
    while(it.hasNext()) {
        Object elt = it.next();
        if(!list.contains(elt)) {
            list.add(at++, elt);
        }
    }
}'''

HOP1 = '''/**
 * Inserts the elements of a collection into a list at the specified index.
 * <p>
 * The collection is passed on as given. The list has changed if its size
 * afterwards differs from its size before.
 *
 * @param list  the list to insert into, must not be null
 * @param index  the index to insert at
 * @param coll  the collection to insert, must not be null
 * @return true if the list changed
 */
public static boolean insertAllAt(List list, int index, Collection coll) {
    int sizeBefore = list.size();
    DoubleOrderedMap.insertElementsOf(list, index, coll);
    return list.size() != sizeBefore;
}'''

HOP2 = '''/**
 * Inserts the elements of a collection into a list at the specified
 * index.
 * <p>
 * Every element of the collection is passed on, in the order of the
 * collection's own iterator.
 *
 * @param list the list to insert into.
 * @param index the index to insert at.
 * @param coll the collection whose elements are inserted.
 */
public static void insertElementsOf(List list, int index, Collection coll) {
    ExtendedProperties.addElementsAt(list, index, coll.iterator());
}'''

HOP3 = '''/**
 * Insert the elements of an iterator into a list at the given index.
 * The iterator is passed on as given.
 *
 * @param list The list to insert into.
 * @param index The index to insert at.
 * @param elements The iterator over the elements to insert.
 */
public static void addElementsAt(List list, int index, Iterator elements) {
    MapUtils.insertElements(list, index, elements);
}'''

HOP4 = '''/**
 * Inserts the elements returned by an iterator into a list at the given index.
 * <p>
 * The iterator is passed on as given.
 *
 * @param list  the list to insert into, must not be null
 * @param index  the index to insert at
 * @param elements  the iterator over the elements to insert, must not be null
 */
public static void insertElements(List list, int index, Iterator elements) {
    CursorableLinkedList.insertEachAt(list, index, elements);
}'''

DESIGN = {
 "instance": "Collections-15", "project": "Collections", "bug_id": 15, "seed": 4651,
 "src_root": "src/java", "test_root": "src/test",
 "facade_variant": "V2",
 "state_passed": "this (the receiver, as java.util.List), index, coll; no field read or written; no write-back",
 "host_mode": "largest5",
 "host_lines": [2085, 1995, 1784, 1678, 1468],
 "facade": {"file": SUL, "class": "org.apache.commons.collections.list.SetUniqueList", "method": "addAll", "near_line": 189},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/list/TestSetUniqueList.java",
             "test_class": "org.apache.commons.collections.list.TestSetUniqueList",
             "test_method": "testIntCollectionAddAll"},
 "expected_signature": "expected:<4> but was:<2>",
 "gold": {"method": "insertEachAt", "text": GOLD_TEXT,
          "fault": {"old": "            if(!list.contains(elt)) {\n"
                           "                list.add(at++, elt);\n"
                           "            }",
                    "new": "            list.add(at++, elt);"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.insertAllAt(this, index, coll);",
   "lie": "The collection is first copied into an array, and the elements are then read from that array in index order.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "insertAllAt",
      "imports": ["java.util.List", "org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "insertElementsOf",
      "imports": ["java.util.List"], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "addElementsAt",
      "imports": [], "text": HOP3},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "insertElements",
      "imports": ["java.util.List"], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableLinkedList", "method": "insertEachAt",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.set.ListOrderedSet::addAll",
              "org.apache.commons.collections.set.ListOrderedSet::add",
              "org.apache.commons.collections.list.SetUniqueList::add"],
 "ownership_reason": "Only the gold sees each element at the moment it is inserted, together with the position it goes to: hop 1 "
                     "sees only the list's size before and after, hop 2 hands over the collection's iterator, and hops 3 and 4 "
                     "pass that iterator along. Once the gold has moved its position past an element the list declined, the "
                     "next element sits one place too far right, which no caller can undo without rebuilding the list. The "
                     "gold's javadoc promises that the inserted elements start at the given position in iterator order; on the "
                     "trigger the one inserted element (4) lands at index 1 instead of 0. The convention is pinned outside the "
                     "gold: the facade's javadoc ('Only elements that are not already in this list will be added, and "
                     "duplicates from the specified collection will be ignored'); ListOrderedSet.addAll(int, Collection), the "
                     "sibling indexed bulk insertion, tests contains(object) == false per element and moves its index only "
                     "after an insertion, and TestListOrderedSet testListAddIndexed and TestListOrderedSet2 testListAddIndexed "
                     "([0, 1].addAll(1, [3, 0, 2]) gives [0, 3, 2, 1]) pass; ListOrderedSet.add(int, Object) and "
                     "SetUniqueList.add(int, Object) insert only an element not yet held; TestSetUniqueList testFactory and "
                     "testAddAll pin that repeated elements of the collection are ignored. Hops 1-4 are documented as passing "
                     "their input on unchanged (hop 1 'The collection is passed on as given', hop 2 'Every element of the "
                     "collection is passed on', hops 3 and 4 'The iterator is passed on as given'), so a hop that drops the "
                     "elements the list already holds before the gold contradicts its own javadoc. The facade can do the same "
                     "with one call, CollectionUtils.removeAll(new java.util.LinkedHashSet(coll), this), which passes the suite: "
                     "that is the gold's omitted contains test moved up to the facade and applied to the whole collection at "
                     "once (ListUtils.removeAll tests remove.contains per element), after which neither the gold's decision nor "
                     "the receiver's decline in add(int, Object) fires; it is recorded as a bypass.",
 "ownership_tests": ["org.apache.commons.collections.set.TestListOrderedSet::testListAddIndexed",
                     "org.apache.commons.collections.set.TestListOrderedSet2::testListAddIndexed",
                     "org.apache.commons.collections.list.TestSetUniqueList::testFactory",
                     "org.apache.commons.collections.list.TestSetUniqueList::testAddAll"],
 "compensating": {
   "chain": [
     {"file": EXP, "old": "MapUtils.insertElements(list, index, elements);",
      "new": "MapUtils.insertElements(list, index, new org.apache.commons.collections.iterators.UniqueFilterIterator(elements));",
      "why": "hop 3 drops repeated elements of the iteration before passing it on"},
     {"file": TBM, "old": "DoubleOrderedMap.insertElementsOf(list, index, coll);",
      "new": "DoubleOrderedMap.insertElementsOf(list, index, new java.util.LinkedHashSet(coll));",
      "why": "hop 1 copies the collection into an insertion-ordered set first"},
     {"file": MU, "old": "CursorableLinkedList.insertEachAt(list, index, elements);",
      "new": "CursorableLinkedList.insertEachAt(list, Math.min(index, list.size()), elements);",
      "why": "hop 4 starts the insertion no further right than the end of the list"},
   ],
 },
 "host_notes": "host_mode largest5 (bridge7_tasks.json; the paired static instance's hosts). Hosts are hosts_hop_order of the task "
               "record, in that order, none substituted: bidimap.TreeBidiMap (hop 1, 2085 lines), DoubleOrderedMap (hop 2, 1995), "
               "ExtendedProperties (hop 3, 1784), MapUtils (hop 4, 1678), CursorableLinkedList (hop 5, gold, 1468; the smallest "
               "host). All five are public concrete top-level classes in which a static method compiles (DoubleOrderedMap is final, "
               "which does not affect a static method; CursorableLinkedList.java also holds the package-private CursorableSubList, "
               "which inherits nothing relevant). Anchors from stageB_lib.pick_insertion_anchor with seed 4651 + 100 + i (as "
               "mr3_spec.py inserts them): hop 1 after `nextKey` (line idx 321, seed 4751), hop 2 after `remove` (1434, 4752), "
               "hop 3 after `getString` (951, 4753), hop 4 after `predicatedMap` (1275, 4754), hop 5 after `retainAll` (609, "
               "4755); all in the outer class (brace depth 1). The facade calls hop 1 by its fully-qualified name; TreeBidiMap "
               "imports java.util.List and DoubleOrderedMap, DoubleOrderedMap and MapUtils import java.util.List, and the other "
               "hosts already import what they use (the last three hosts and hop 2's host share the package "
               "org.apache.commons.collections).",
}
