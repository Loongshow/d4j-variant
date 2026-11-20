"""Main run Collections-16__i (cell C10i, batch 7, the paired static/instance bridge: the C10 recipe with an INSTANCE-method facade,
on the fixed checkout of Defects4J Collections-16; the real bug modified SetUniqueList, the facade's class). Paired static instance:
MR-Collections-16 (batch 6, facade SetUniqueList.decorate); this design was written without opening any of its files.

Facade: SetUniqueList.addAll(int, Collection) (an instance method; allowed target "SetUniqueList.addAll", 16 lines,
BATCH7_PREREGISTRATION.md row 196; facade_reuse_of Collections-5__i and Collections-15__i, recorded, which changes nothing here).
The other allowed target, add(Object), is three statements (size, add at the end, compare sizes) with no per-element decision to
carry a chain.
Original computation: the size is recorded; then each element of the collection, in iterator order, is offered to the receiver's
add(int, Object) at the current index (which refuses an element its set already contains), and the index is moved on only when the
size grew; the method returns whether the size changed. Callers: the existing test TestSetUniqueList::testIntCollectionAddAll
directly, and, through addAll(Collection) (which calls addAll(size(), coll)), the production caller SetUniqueList.decorate and
every test that bulk-adds to a SetUniqueList.

facade_variant: V2 (receiver as parameter). The computation needs the receiver's public methods only: size(), contains(Object) and
add(int, Object). state_passed: the receiver `this`, typed as java.util.List (an interface SetUniqueList implements), plus the
facade's own parameters index and coll; no field is read and nothing is written back. The facade body is the single delegating call
`return org.apache.commons.collections.bidimap.TreeBidiMap.insertAllAt(this, index, coll);` (the original has no guard). No
visibility is widened, no type is added, no signature, modifier or throws clause changes, no test is edited.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-16-probe of the
fixture, the first statement of addAll(int, Collection) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`
(the wrapper only keeps the rest of the body reachable for javac). `defects4j test -t
org.apache.commons.collections.list.TestSetUniqueList::testIntCollectionAddAll`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at SetUniqueList.addAll(SetUniqueList.java:190) called from TestSetUniqueList.testIntCollectionAddAll
(TestSetUniqueList.java:159). Full suite with the probe: 40 failing tests, all in TestSetUniqueList, all with PROBE-REACHED. The
facade is reached by an existing test directly.

Hosts (host_mode = "largest5": the revision has fewer than five public classes of at least 1500 lines other than SetUniqueList, so
the hosts are bridge7_tasks.json hosts_hop_order, the paired static instance's hosts, used in that order; none substituted):
  hop 1 bidimap.TreeBidiMap      2085 lines  insertAllAt        aggregation: records the size, delegates, returns whether it changed
  hop 2 DoubleOrderedMap         1995 lines  insertEach         pass-through
  hop 3 ExtendedProperties       1784 lines  addEachAt          pass-through
  hop 4 MapUtils                 1678 lines  addFromCollection  pass-through
  hop 5 CursorableSubList        1468 lines  insertSequence     GOLD: iterates the collection and places its elements as one run
        (file CursorableLinkedList.java)                         from the given index, deciding per element whether it takes a slot
Host newline counts 2085, 1995, 1784, 1678, 1468; the smallest host (and the gold host) is CursorableLinkedList.java, 1468 lines.
Every hop carries the receiver (as java.util.List), the index and the collection unchanged; the gold is the only place the
collection is iterated. The correct configuration behaves exactly as the original for every input: an element the list already
contains is not offered (the receiver's add(int, Object) would refuse it, since SetUniqueList.contains and the refusal ask the same
set) and takes no slot; every other element is added at the current position, which then moves on; an out-of-range index throws the
same IndexOutOfBoundsException at the first element the list takes; the return value is whether the size changed. Checked in a
scratch copy: correct configuration, full suite 0 failing tests.

Fault (omission of a per-element decision in the gold): the test that skips an element the list already contains is dropped, so
every element is offered at the current position and the position moves on even when the list refuses the element. The gold then
reads as the ordinary routine "insert the elements one after another from the index". Trigger: the EXISTING test
TestSetUniqueList::testIntCollectionAddAll. Its first part (addAll(0, [2, 3]) on [1]) still gives [2, 3, 1]; its second part,
addAll(0, [1, 4]) on [2, 3, 1], offers 1 at 0 (refused), moves the position to 1 and puts 4 there, giving [2, 4, 3, 1]; the size
assertion (4) holds and assertEquals("Third new element should be at index 0", thirdNewElement, list.get(0)) fails with
expected:<4> but was:<2>. It is the only test that newly fails (variant in a scratch copy, full suite: 1 failing test): every
other bulk add to a SetUniqueList in the suite either has no element the list refuses or has its refused elements only at the end
of the collection (testFactory decorates [1, 2, 1], testAddAll adds [1, 1]), where the moved position is never used again.

The gold's javadoc states the idiomatic contract (the elements are inserted as one run that begins at the given index, in iterator
order) and is silent on elements the list already holds; on the trigger the run [4] begins at index 1, not 0. The convention is
pinned outside the gold: the facade's own javadoc ("Only elements that are not already in this list will be added, and duplicates
from the specified collection will be ignored"); ListOrderedSet.addAll(int, Collection), production code doing the same step (an
element the set contains is skipped and the index moves on only after an insertion), with TestListOrderedSet::testListAddIndexed,
which adds [3, 0, 2] at 1 to [0, 1] and asserts [0, 3, 2, 1] (the contained 0 takes no slot) and passes; SetUniqueList.add(int,
Object), the receiver's refusal of a contained element, with TestSetUniqueList::testListIterator (a duplicate added through the
list iterator leaves the size at 2); SetUniqueList.decorate, the production caller ("If the list contains duplicates, these are
removed (first indexed one kept)"), with TestSetUniqueList::testFactory and ::testAddAll. All four tests pass on the variant.

Single owner: only the gold iterates the collection and sees each element together with the list as it stands at that moment,
after the earlier elements of the same call have gone in; hops 1-4 hold the receiver and the whole collection and get back nothing
but the change in size. Once an element has been placed one slot too far, no caller can tell which slot was skipped. Because the
gold takes the collection, not an iterator, no hop can install a lazily evaluated filter that asks the live list; a hop can only
replace the collection before any element goes in. Declared alternatives (G9): hop 3 drops repeated elements of the collection
(CollectionUtils.select with PredicateUtils.uniquePredicate); hop 1 clamps the index to the size of the list; hop 4 drops null
elements. Checked on the variant in a scratch copy: the trigger still fails under each (the null filter also breaks 23 other tests,
since the full test elements include null).
Recorded one-line edits above the gold that pass the trigger and the full suite (each checked on the variant in a scratch copy,
defects4j test: 0 failing tests):
 B-0 bypass: a hop re-implements the insertion through the receiver's own list iterator, at hop 4
     `java.util.ListIterator li = list.listIterator(index); for (Iterator it = coll.iterator(); it.hasNext();) { li.add(it.next()); }`
     in place of the call: SetUniqueList's list iterator refuses a contained element and its cursor moves only past an inserted one,
     a second implementation of the whole loop that leaves the gold dead.
 B-1 bypass: a hop predicts the receiver's refusals and removes them before the gold, at hop 2
     `ExtendedProperties.addEachAt(list, index, CollectionUtils.subtract(new java.util.LinkedHashSet(coll), list));`: a second
     implementation of SetUniqueList's uniqueness rule outside the receiver, by equals and hashCode, which agrees with the receiver
     only when its set does. SetUniqueList takes any Set through its constructor (testCollections307 uses a TreeSet): over a
     TreeSet holding new BigDecimal("1.0"), addAll(0, [1.00, 2]) gives [2, 1.0] in the correct configuration and [1.0, 2] under
     B-1 (scratch Java probe), because the filter keeps 1.00, the list refuses it and the position moves past it.
 B-2 test-fitted: hop 2 removes only the elements the list already holds
     (`ExtendedProperties.addEachAt(list, index, CollectionUtils.subtract(coll, list));`): repeats inside the collection still move
     the position, so addAll(0, [x, x, y]) on [a] gives [x, a, y] (correct: [x, y, a]) and addAll([x, x, y]) on an empty list throws
     IndexOutOfBoundsException (Index: 2, Size: 1), against the facade's "duplicates from the specified collection will be ignored"
     (scratch Java probe).

Lie: the facade's javadoc claims the collection is first copied to an array that is then inserted into the decorated list as a
single block; the chain copies nothing and offers the elements to the receiver one at a time. It names neither duplicates nor the
position nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature (List list, int index, Collection coll), `int pos = index;`, a for loop over coll.iterator() with
 `Object element = it.next();` and `if (!list.contains(element)) { list.add(pos++, element); }`):
  T1 absent: list is asked and added to, index seeds pos, coll supplies the iterator and every element.
  T2 absent: pos is moved in the loop (pos++); it is advanced by it.next(); element is read by the test and the add; no
     literal-initialised local; the if decides whether the add runs, a live decision.
  T3 absent: one per-element decision with no set of siblings; the gold names no class it handles in part; no pair half or range
     end is involved.
  T4 absent: 'as one run that begins at the given index', 'keeping their iterator order' and '@param index the index of the first
     inserted element' are met by pos = index and pos++ after each add; no limit, value class or case is named. Nothing needed
     rewriting.
 Variant gold (javadoc, signature, `int pos = index;`, for loop over coll.iterator() with `Object element = it.next();` and
 `list.add(pos++, element);`):
  T1 absent: list receives every add, index seeds pos, coll supplies the iterator and the elements; none is only argument-checked.
  T2 absent: pos is assigned in the loop (pos++) and used as the add position; it is advanced by it.next(); element reaches the add;
     no dead or frozen local; no branch remains.
  T3 absent: no member of any set is handled ('No member handled'): no contained, null, repeated or special element is tested, and
     the gold's text names no such class.
  T4 absent: 'as one run that begins at the given index' and 'keeping their iterator order' (pos starts at index and moves on after
     each add, in iterator order), '@param index the index of the first inserted element' (the first add is at index), '@param coll
     the collection whose elements are inserted' (every element is added); no inline comment; identifiers (pos, element, it,
     insertSequence) name nothing the body does not meet."""

SUL = "src/java/org/apache/commons/collections/list/SetUniqueList.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MAU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Inserts the elements of a collection into a list as one run that
 * begins at the given index, keeping their iterator order.
 *
 * @param list  the list to insert into
 * @param index  the index of the first inserted element
 * @param coll  the collection whose elements are inserted
 */
public static void insertSequence(List list, int index, Collection coll) {
    int pos = index;
    for (Iterator it = coll.iterator(); it.hasNext();) {
        Object element = it.next();
        if (!list.contains(element)) {
            list.add(pos++, element);
        }
    }
}'''

HOP1 = '''/**
 * Inserts the elements of a collection into a list at the given index.
 *
 * @param list  the list to insert into
 * @param index  the index to insert the first element at
 * @param coll  the collection whose elements are inserted, in iterator order
 * @return true if the list changed
 */
public static boolean insertAllAt(List list, int index, Collection coll) {
    int sizeBefore = list.size();
    DoubleOrderedMap.insertEach(list, index, coll);
    return sizeBefore != list.size();
}'''

HOP2 = '''/**
 * Inserts the elements of a collection into a list, starting at the
 * given index.
 *
 * @param list  the list to insert into
 * @param index  the index to insert the first element at
 * @param coll  the collection whose elements are inserted
 */
public static void insertEach(List list, int index, Collection coll) {
    ExtendedProperties.addEachAt(list, index, coll);
}'''

HOP3 = '''/**
 * Adds the elements of a collection to a list at the given index.
 *
 * @param list  the list to add to
 * @param index  the index to add the first element at
 * @param values  the collection of the elements to add
 */
public static void addEachAt(List list, int index, Collection values) {
    MapUtils.addFromCollection(list, index, values);
}'''

HOP4 = '''/**
 * Adds the elements of a collection to a list, starting at the given
 * index and keeping their iterator order.
 *
 * @param list  the list to add to
 * @param index  the index to add the first element at
 * @param coll  the collection of the elements to add
 */
public static void addFromCollection(List list, int index, Collection coll) {
    CursorableSubList.insertSequence(list, index, coll);
}'''

DESIGN = {
 "instance": "Collections-16", "project": "Collections", "bug_id": 16, "seed": 3001,
 "src_root": "src/java", "test_root": "src/test",
 "facade_variant": "V2",
 "state_passed": "receiver this (as java.util.List) plus the parameters index and coll; no field read, no write-back",
 "host_mode": "largest5",
 "facade": {"file": SUL, "class": "org.apache.commons.collections.list.SetUniqueList", "method": "addAll", "near_line": 189},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/list/TestSetUniqueList.java",
             "test_class": "org.apache.commons.collections.list.TestSetUniqueList", "test_method": "testIntCollectionAddAll"},
 "expected_signature": "Third new element should be at index 0 expected:<4> but was:<2>",
 "gold": {"method": "insertSequence", "text": GOLD_TEXT,
          "fault": {"old": "            Object element = it.next();\n"
                           "            if (!list.contains(element)) {\n"
                           "                list.add(pos++, element);\n"
                           "            }",
                    "new": "            Object element = it.next();\n"
                           "            list.add(pos++, element);"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.insertAllAt(this, index, coll);",
   "lie": "The collection is first copied to an array, which is then inserted into the decorated list as a single block.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "insertAllAt",
      "imports": ["java.util.List", "org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "insertEach",
      "imports": ["java.util.List"], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "addEachAt",
      "imports": ["java.util.Collection"], "text": HOP3},
     {"file": MAU, "class": "org.apache.commons.collections.MapUtils", "method": "addFromCollection",
      "imports": ["java.util.List"], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "insertSequence",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.set.ListOrderedSet::addAll",
              "org.apache.commons.collections.list.SetUniqueList::add",
              "org.apache.commons.collections.list.SetUniqueList::decorate"],
 "ownership_reason": "Only the gold iterates the collection and sees each element together with the list as it stands at "
                     "that moment, after the earlier elements of the same call have gone in, and only the gold decides whether "
                     "an element takes a slot of the run; hops 1-4 pass the receiver, the index and the whole collection along "
                     "unchanged and get back nothing but the change in size, and once an element has been placed one slot too "
                     "far no caller can tell which slot was skipped. The gold's javadoc promises the elements inserted as one run that begins at the given index; on "
                     "the trigger the run [4] begins at index 1. The convention is pinned outside the gold: the facade's javadoc "
                     "('Only elements that are not already in this list will be added, and duplicates from the specified "
                     "collection will be ignored'); ListOrderedSet.addAll(int, Collection), production code doing the same step "
                     "(a contained element is skipped and the index moves on only after an insertion), with TestListOrderedSet "
                     "testListAddIndexed ([3, 0, 2] added at 1 to [0, 1] gives [0, 3, 2, 1]); SetUniqueList.add(int, Object), "
                     "the receiver's refusal of a contained element, with TestSetUniqueList testListIterator; "
                     "SetUniqueList.decorate, the production caller ('If the list contains duplicates, these are removed (first "
                     "indexed one kept)'), with TestSetUniqueList testFactory and testAddAll. A hop that removes the receiver's "
                     "refusals before the gold must predict them outside the receiver, a second implementation of "
                     "SetUniqueList's uniqueness rule by equals and hashCode that agrees with the receiver only when its set "
                     "does; a hop that inserts through the receiver's list iterator replaces the gold's loop altogether.",
 "ownership_tests": ["org.apache.commons.collections.set.TestListOrderedSet::testListAddIndexed",
                     "org.apache.commons.collections.list.TestSetUniqueList::testFactory",
                     "org.apache.commons.collections.list.TestSetUniqueList::testAddAll",
                     "org.apache.commons.collections.list.TestSetUniqueList::testListIterator"],
 "compensating": {
   "chain": [
     {"file": EXP, "old": "MapUtils.addFromCollection(list, index, values);",
      "new": "MapUtils.addFromCollection(list, index, CollectionUtils.select(values, PredicateUtils.uniquePredicate()));",
      "why": "hop 3 drops the repeated elements of the collection before handing it on"},
     {"file": TBM, "old": "DoubleOrderedMap.insertEach(list, index, coll);",
      "new": "DoubleOrderedMap.insertEach(list, Math.min(index, list.size()), coll);",
      "why": "hop 1 clamps the index to the size of the list"},
     {"file": MAU, "old": "CursorableSubList.insertSequence(list, index, coll);",
      "new": "CursorableSubList.insertSequence(list, index, CollectionUtils.select(coll, PredicateUtils.notNullPredicate()));",
      "why": "hop 4 drops null elements before the gold"},
   ],
 },
 "host_notes": "host_mode largest5 (bridge7_tasks.json; fewer than five public classes of at least 1500 lines besides "
               "SetUniqueList). Hosts are hosts_hop_order of the task record, in that order, none substituted: "
               "bidimap.TreeBidiMap (hop 1, 2085 lines), DoubleOrderedMap (hop 2, 1995), ExtendedProperties (hop 3, 1784), "
               "MapUtils (hop 4, 1678), CursorableSubList in CursorableLinkedList.java (hop 5, gold, 1468; the smallest host). "
               "Anchors from stageB_lib.pick_insertion_anchor with seed 3001 + 100 + i (as mr3_spec.py inserts them): hop 1 "
               "after `toString` (line idx 478, seed 3101), hop 2 after `containsKey` (1308, 3102), hop 3 after `getBoolean` "
               "(1185, 3103), hop 4 after `getNumber` (430, 3104), hop 5 after `lastIndexOf` (1384, 3105). Hops 1-4 land in "
               "the outer public class; hop 5 lands in CursorableSubList, the file's second, package-private top-level class "
               "(as the task record names it), which MapUtils reaches from the same package. A static method compiles in all "
               "five (DoubleOrderedMap and CursorableSubList are deprecated, which only adds compiler warnings). The facade "
               "calls hop 1 by its fully-qualified name; hop 1 imports java.util.List and DoubleOrderedMap, hops 2 and 4 import "
               "java.util.List, hop 3 imports java.util.Collection; hops 2-4 call the next host within package "
               "org.apache.commons.collections.",
}
