"""Main run Collections-5__i (cell C10i, batch 7: the C10 recipe with an INSTANCE-method facade, paired with the static-facade
instance of the same bug; fixed checkout of Defects4J Collections-5; the real bug modified SetUniqueList, the facade's class).

Facade: SetUniqueList.addAll(int, Collection) (allowed target SetUniqueList.addAll, BATCH7_PREREGISTRATION.md row 194; the
(int, Collection) overload, the 16-line candidate of the task record; the other allowed target, add(Object), is a three-statement
wrapper around add(int, Object) that every test of the class reaches through verify(), so no omission below it could have a single
trigger). facade_reuse_of: none. Original computation: the size before; then for each element of the collection in iterator order,
add(index, element) on the receiver (SetUniqueList.add(int, Object) inserts it only if the internal set does not hold it yet), and
the target index is advanced only if that call changed the size; the result is whether the size changed overall. Callers: the
existing tests directly (TestSetUniqueList testIntCollectionAddAll), addAll(Collection) (which passes size() as the index), and
decorate (via addAll(Collection)); no other production class uses SetUniqueList.

facade_variant: V2 (receiver as parameter). The computation needs only the receiver's public methods size() and add(int, Object)
(the task record's variant_reason); the facade reads no field. state_passed: the receiver `this`, handed to hop 1 typed as
java.util.List (an interface SetUniqueList implements), with the parameters index and coll unchanged; the hops call only
list.size() and list.add(int, Object) on it; no write-back (addAll assigns no field). The facade body is one delegating call
(the original has no argument guard): `return org.apache.commons.collections.bidimap.TreeBidiMap.insertAll(this, index, coll);`.
Every call on the receiver is the same virtual call the original made, so the correct configuration returns the original result
and leaves the list in the original state for every input, the exceptional paths included (an IndexOutOfBoundsException from the
decorated list propagates from the same element).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-5-probe/w of the
fixture, the first statement of SetUniqueList.addAll(int, Collection) was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)` only keeps the rest of the body reachable for
javac). `defects4j test -t org.apache.commons.collections.list.TestSetUniqueList::testIntCollectionAddAll`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at SetUniqueList.addAll(SetUniqueList.java:190) called from
TestSetUniqueList.testIntCollectionAddAll(TestSetUniqueList.java:158). Full suite with the probe: 40 failing tests, all in
TestSetUniqueList (every test that fills the list through makeFullList, decorate or addAll). The facade is reached by an existing
test directly.

Hosts (host_mode = "largest5"; bridge7_tasks.json hosts_hop_order, the static instance's hosts, used in that order, none
substituted):
  hop 1 bidimap.TreeBidiMap        2085 lines  insertAll       pass-through
  hop 2 DoubleOrderedMap           1995 lines  insertElements  aggregation: the size before the insertion is compared with the
                                                               size the insertion reports, giving whether the list changed
  hop 3 ExtendedProperties         1717 lines  addInOrder      plumbing: the collection is handed on as its iterator
  hop 4 MapUtils                   1645 lines  populateList    pass-through
  hop 5 CursorableLinkedList       1468 lines  insertInOrder   GOLD: one pass over the iterator, inserting each element at the
                                                               current position, with the per-element decision whether the
                                                               position moves on (only when the list took the element)
Host newline counts 2085, 1995, 1717, 1645, 1468; the smallest host (and the gold host) has 1468 lines (below 1500, expected under
largest5, C10F addendum section 1).

Fault (omission of a per-element decision in the gold): the `if (list.size() != size)` line that guards the size update and the
advance of the position is dropped (with its closing brace), so the position moves on after every element, also after one the
list declined. The gold then reads as the ordinary routine "insert each element at the current position, note the size, step
on". Trigger: the EXISTING test TestSetUniqueList::testIntCollectionAddAll. Its first block (two new elements at index 0 of [1])
still holds; in the second block, addAll(0, [1, 4]) on [2, 3, 1]: the list declines 1, the position still moves to 1, and 4 is
inserted at index 1, giving [2, 4, 3, 1]; the size assertion (4) holds and assertEquals("Third new element should be at index
0", thirdNewElement, list.get(0)) at line 170 fails with expected:<4> but was:<2>. It is the only test that newly fails: every other
addAll on a SetUniqueList in the suite (makeFullList, testCollectionAddAll, testAddAll, testFactory through decorate, the sub-list
fail-fast tests) either has no declined element or has its declined elements only at the end of the collection, where a moved
position is never used again.

The gold's javadoc states the idiomatic contract (CursorableLinkedList.addAll(int, Collection)'s own wording: the elements are
inserted starting at the specified position and appear in the order the iterator returns them; it returns the size afterwards)
and is silent on elements the list declines. On the trigger the only new element, 4, appears at index 1, not at the specified
position 0, so the variant violates that contract. The convention is pinned outside the gold: ListOrderedSet.addAll(int,
Collection), the sibling ordered-unique collection, advances its index only inside `if (contains(object) == false)`, and
TestListOrderedSet::testListAddIndexed (addAll(1, [3, 0, 2]) on [0, 1] gives [0, 3, 2, 1]: 0 is skipped and 2 follows 3 directly)
passes; SetUniqueList.add(int, Object) (unchanged) declines an element the set holds, documented as a List-contract violation, and
the facade's own javadoc ('Only elements that are not already in this list will be added'; 'the elements are always inserted. This
may not happen with this implementation') says the receiver declines elements; CursorableLinkedList.addAll(int, Collection) and
TestCursorableLinkedList::testAdd pin consecutive insertion in iterator order from the index; TestSetUniqueList::testAddAll,
::testFactory and ::testCollectionAddAll pin the uniqueness behaviour and pass on the variant.

Single owner: only the gold sees each element together with the list's response to it and the position it went to; hops 1, 3
and 4 pass the list, the index and the elements along, and hop 2 only turns the reported size into "changed". The hops and the
gold are documented as general List operations (a list that takes every element gets List.addAll(int, Collection) semantics), so
a hop cannot drop elements before the gold without breaking its own contract for such a list. Declared alternatives (G9): hop 4
clamps the position to the list size; hop 2 reports a change only when the list grew; hop 3 drops repeated elements of the
collection before iterating. None changes the trigger's [1, 4] case.
Hop 2's javadoc says that a list may decline an element (its own size comparison depends on it), so the chain is documented for
declining lists; the gold's javadoc says nothing about them.
Recorded edits above the gold that pass the trigger (not declared in compensating, since they hide the omission on the trigger;
each checked on the variant in a scratch copy with defects4j test, and its behaviour probed with a small driver compiled against
the build):
 B-0 bypass: the facade gets its original body back (or a hop re-implements the loop), discarding the chain including the gold.
 B-1 test-fitted filter: a hop removes the elements the list already contains before the gold, e.g. hop 3
     `return MapUtils.populateList(list, index, CollectionUtils.subtract(coll, list).iterator());`. Trigger passes, full suite 0
     failing tests. It breaks the hop's documented general contract (for an ArrayList [1], TreeBidiMap.insertAll(list, 0, [1])
     leaves [1] instead of [1, 1]) and is not a repair for SetUniqueList either: addAll(0, [5, 5, 6]) on an empty SetUniqueList
     still moves the position past the declined repeat and throws IndexOutOfBoundsException (list left as [5]) instead of giving
     [5, 6].
 B-2 bypass: the facade pre-computes the receiver's own acceptance rule before delegating,
     `return org.apache.commons.collections.bidimap.TreeBidiMap.insertAll(this, index,
     org.apache.commons.collections.CollectionUtils.subtract(new java.util.LinkedHashSet(coll), asSet()));` (drop repeats, then
     drop the elements the set holds), so the chain never meets an element the list declines. Trigger passes, full suite 0 failing
     tests, and addAll(0, [5, 5, 6]) gives [5, 6]. It is a second implementation of SetUniqueList.add(int, Object)'s set test
     placed ahead of the chain, which makes that test unreachable on this path; it leaves
     the gold's per-element placement as it is, so the public chain methods still misplace elements for a declining list passed
     to them (TreeBidiMap.insertAll(SetUniqueList [2, 3, 1], 0, [1, 4]) still gives [2, 4, 3, 1] with B-2 applied). (The variant
     with ListOrderedSet.decorate(new ArrayList(coll)) in place of the LinkedHashSet is only test-fitted: in this revision that
     factory keeps repeats, so [5, 5, 6] still throws.)

Lie: the facade's javadoc claims the collection is first copied into an array whose elements are then inserted into the decorated
list by a single bulk call; the chain copies nothing and inserts the elements one at a time through the receiver's add(int,
Object). It names neither declined elements nor the position nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `int at = index; int size = list.size(); while(it.hasNext()) { list.add(at,it.next());
 if(list.size() != size) { size = list.size(); at++; } } return size;`):
  T1 absent: list receives every insertion and gives the sizes; index seeds the position of the first insertion; it supplies every
     element; each changes the side effects or the return value; there is no argument check.
  T2 absent: at is advanced inside the loop (in the if) and is the position of every insertion; size is reassigned inside the
     loop, read by the decision and returned; neither starts from a literal; the if decides two live updates.
  T3 absent: no closed set, pair or range end is involved (one position, one size); the gold names no class it handles in part.
  T4 absent: 'starting at the specified position', 'appear in the list in the order that they are returned by the iterator',
     '@param index index at which to insert the first element' and '@return the size of the list after the insertion' are all
     met by lines of the body; 'the list to insert into', 'the elements to be inserted' name nothing concrete.
  Nothing needed rewriting.
 Variant gold (javadoc, signature, `int at = index; int size = list.size(); while(it.hasNext()) { list.add(at,it.next());
 size = list.size(); at++; } return size;`):
  T1 absent: list, index and it each change the inserted positions, the side effects or the return value; none is only
     argument-checked.
  T2 absent: at is assigned in the loop (at++) and is the argument of every add; size is assigned in the loop from list.size()
     and returned (and its initial value is returned for an empty iterator); no literal-initialised local, no flag, no
     best-so-far; there is no branch left, so no dead decision.
  T3 absent: no member of any set is handled at all ('No member handled'); no pair half or range end is treated on one side
     only; the gold names no class.
  T4 absent: the javadoc's phrases are general descriptions that the loop addresses (insertion from the given position, iterator
     order, the size afterwards, read from list.size()); no limit, value class, case or property is named; no inline comment;
     the identifiers at, size, list, index, it name nothing the body does not meet."""

SUL = "src/java/org/apache/commons/collections/list/SetUniqueList.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Inserts the elements returned by an iterator into a list, starting at
 * the specified position.  The new elements will appear in the list in
 * the order that they are returned by the iterator.
 *
 * @param list the list to insert into.
 * @param index index at which to insert the first element.
 * @param it the elements to be inserted.
 * @return the size of the list after the insertion.
 */
public static int insertInOrder(List list, int index, Iterator it) {
    int at = index;
    int size = list.size();
    while(it.hasNext()) {
        list.add(at,it.next());
        if(list.size() != size) {
            size = list.size();
            at++;
        }
    }
    return size;
}'''

HOP1 = '''/**
 * Inserts the elements of a collection into a list at the specified
 * position, in the order the collection's iterator returns them.
 *
 * @param list  the list to insert into, must not be null
 * @param index  the position at which to insert the first element
 * @param coll  the elements to insert, must not be null
 * @return true if the list changed
 */
public static boolean insertAll(final List list, final int index, final Collection coll) {
    return DoubleOrderedMap.insertElements(list, index, coll);
}'''

HOP2 = '''/**
 * Inserts the elements of a collection into a list at the specified
 * position, in the order the collection's iterator returns them.
 * A list may decline an element, so the list changed only if its size
 * after the insertion differs from its size before.
 *
 * @param list the list to insert into
 * @param index the position at which to insert the first element
 * @param coll the elements to insert
 *
 * @return true if the list changed
 */
public static boolean insertElements(final List list, final int index, final Collection coll) {
    final int sizeBefore = list.size();
    return ExtendedProperties.addInOrder(list, index, coll) != sizeBefore;
}'''

HOP3 = '''/**
 * Inserts the elements of a collection into a list at the specified
 * position, in the order the collection's iterator returns them.
 *
 * @param list  the list to insert into
 * @param index  the position at which to insert the first element
 * @param coll  the elements to insert
 * @return the size of the list after the insertion
 */
public static int addInOrder(List list, int index, Collection coll) {
    return MapUtils.populateList(list, index, coll.iterator());
}'''

HOP4 = '''/**
 * Populates a list with the elements returned by an iterator, inserting
 * them at the specified position.
 *
 * @param list  the list to populate, must not be null
 * @param index  the position at which to insert the first element
 * @param it  the elements to insert, must not be null
 * @return the size of the list after the insertion
 */
public static int populateList(List list, int index, Iterator it) {
    return CursorableLinkedList.insertInOrder(list, index, it);
}'''

DESIGN = {
 "instance": "Collections-5", "project": "Collections", "bug_id": 5, "seed": 8405,
 "src_root": "src/java", "test_root": "src/test",
 "facade_variant": "V2",
 "state_passed": "receiver `this` (as java.util.List) with the parameters index and coll; no write-back",
 "facade": {"file": SUL, "class": "org.apache.commons.collections.list.SetUniqueList", "method": "addAll", "near_line": 189},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/list/TestSetUniqueList.java",
             "test_class": "org.apache.commons.collections.list.TestSetUniqueList",
             "test_method": "testIntCollectionAddAll"},
 "expected_signature": "expected:<4> but was:<2>",
 "gold": {"method": "insertInOrder", "text": GOLD_TEXT,
          "fault": {"old": "            if(list.size() != size) {\n"
                           "                size = list.size();\n"
                           "                at++;\n"
                           "            }",
                    "new": "            size = list.size();\n"
                           "            at++;"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.insertAll(this, index, coll);",
   "lie": "The collection is first copied into an array, and the elements of that array are then inserted into the "
          "decorated list by a single bulk call.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "insertAll",
      "imports": ["java.util.List", "org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "insertElements",
      "imports": ["java.util.List"], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "addInOrder",
      "imports": ["java.util.Collection"], "text": HOP3},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "populateList",
      "imports": ["java.util.List"], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableLinkedList", "method": "insertInOrder",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.set.ListOrderedSet::addAll",
              "org.apache.commons.collections.list.SetUniqueList::add",
              "org.apache.commons.collections.CursorableLinkedList::addAll"],
 "ownership_reason": "Only the gold sees each element together with the list's response to it and the position it went to: "
                     "hops 1, 3 and 4 pass the list, the index and the elements along, and hop 2 only compares the size the "
                     "insertion reports with the size before. The gold's javadoc promises that the elements are inserted "
                     "starting at the specified position and appear in iterator order; on the trigger the list (a "
                     "SetUniqueList, whose add(int, Object) declines an element its set holds, documented in the facade's "
                     "javadoc as 'the elements are always inserted. This may not happen with this implementation') declines 1, "
                     "and the only new element, 4, ends up at index 1 instead of 0. The convention that the insertion position "
                     "moves on only past an element the collection took is pinned outside the gold: "
                     "ListOrderedSet.addAll(int, Collection) advances its index only inside `if (contains(object) == false)`, "
                     "and TestListOrderedSet testListAddIndexed (addAll(1, [3, 0, 2]) on [0, 1] gives [0, 3, 2, 1]) passes; "
                     "CursorableLinkedList.addAll(int, Collection) with TestCursorableLinkedList testAdd pins consecutive "
                     "insertion in iterator order from the index; TestSetUniqueList testAddAll, testFactory and "
                     "testCollectionAddAll pin the uniqueness behaviour of the receiver. The hops and the gold are general List "
                     "operations, so a hop that drops elements before the gold (for example CollectionUtils.subtract(coll, "
                     "list)) breaks its own contract for a list that takes every element (insertAll on an ArrayList [1] with "
                     "[1] would leave [1]) and does not even repair a SetUniqueList (addAll(0, [5, 5, 6]) on an empty one still "
                     "moves past the declined repeat and throws IndexOutOfBoundsException). Hop 2's javadoc states that a list "
                     "may decline an element, so the chain is documented for such lists. A facade that re-implements the "
                     "receiver's acceptance test ahead of the chain (for example passing CollectionUtils.subtract(new "
                     "LinkedHashSet(coll), asSet()) to hop 1) is a second implementation of SetUniqueList.add(int, Object)'s "
                     "set test, a bypass: it makes that test unreachable on this path, and the gold and the public hops still "
                     "misplace elements for a declining list passed to them (TreeBidiMap.insertAll on the SetUniqueList [2, 3, "
                     "1] with [1, 4] at 0 still gives [2, 4, 3, 1]).",
 "ownership_tests": ["org.apache.commons.collections.set.TestListOrderedSet::testListAddIndexed",
                     "org.apache.commons.collections.TestCursorableLinkedList::testAdd",
                     "org.apache.commons.collections.list.TestSetUniqueList::testAddAll",
                     "org.apache.commons.collections.list.TestSetUniqueList::testFactory"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "return CursorableLinkedList.insertInOrder(list, index, it);",
      "new": "return CursorableLinkedList.insertInOrder(list, Math.min(index, list.size()), it);",
      "why": "hop 4 clamps the position of the first element to the size of the list"},
     {"file": DOM, "old": "return ExtendedProperties.addInOrder(list, index, coll) != sizeBefore;",
      "new": "return ExtendedProperties.addInOrder(list, index, coll) > sizeBefore;",
      "why": "hop 2 reports a change only when the list grew"},
     {"file": EXP, "old": "return MapUtils.populateList(list, index, coll.iterator());",
      "new": "return MapUtils.populateList(list, index, new java.util.ArrayList(new java.util.LinkedHashSet(coll)).iterator());",
      "why": "hop 3 drops repeated elements of the collection before iterating"},
   ],
 },
 "host_notes": "host_mode largest5 (bridge7_tasks.json; the paired static instance's hosts in its hop order, none substituted): "
               "bidimap.TreeBidiMap (hop 1, 2085 lines), DoubleOrderedMap (hop 2, 1995), ExtendedProperties (hop 3, 1717), "
               "MapUtils (hop 4, 1645), CursorableLinkedList (hop 5, gold, 1468; the smallest host). All five are public "
               "concrete top-level classes in which a static method compiles. Anchors from stageB_lib.pick_insertion_anchor "
               "with seed 8405 + 100 + i (as mr3_spec.py inserts them): hop 1 after `size` (line idx 124, seed 8505), hop 2 "
               "after `clear` (1446, 8506), hop 3 after the constructor `ExtendedProperties` (461, 8507), hop 4 after "
               "`unmodifiableMap` (1255, 8508), hop 5 after `iterator` (442, 8509); all in the outer class. The facade calls "
               "hop 1 by its fully-qualified name; hop 1 imports DoubleOrderedMap and java.util.List; hops 2-5 share the "
               "package org.apache.commons.collections and add only the java.util imports they lack. The receiver is typed "
               "java.util.List in every hop.",
}
