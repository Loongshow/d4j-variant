"""Main run Collections-15 (cell C10f, batch 6: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J
Collections-15; the real bug modified SetUniqueList, the target class).

Facade: SetUniqueList.decorate(List) (the only allowed target, BATCH6_PREREGISTRATION.md row 148; facade reuse of Collections-5,
recorded as facade_reuse_of, which changes nothing in the build). No production code calls it; its callers are four tests of
TestSetUniqueList (testFactory, testUniqueListReInsert, testUniqueListDoubleInsert, testCollections304).
Original computation: a null list throws IllegalArgumentException("List must not be null"); an empty list is wrapped with a new
HashSet; a non-empty list is copied, cleared and refilled through SetUniqueList.addAll, which appends each element unless an equal
element is already present, so a repeated element keeps its first position ("first indexed one kept", the facade's javadoc), and the
HashSet ends up holding the elements of the refilled list.

reachability_probe: in a scratch copy of the fixture (/private/tmp/c15-probe) the facade's first statement was made
`if (true) throw new IllegalStateException("PROBE-REACHED");` (the `if (true)` keeps the rest of the body reachable for javac).
defects4j test -t on TestSetUniqueList::testFactory, ::testUniqueListReInsert, ::testUniqueListDoubleInsert and ::testCollections304:
each fails with java.lang.IllegalStateException: PROBE-REACHED at SetUniqueList.decorate(SetUniqueList.java:74); ::testAdd (a
control that builds the list with the constructor) passes. Full suite on the probe copy: exactly these 4 tests fail, all with the
probe message. The facade is reachable; testFactory is the only caller that passes a non-empty list.

Hosts (host_mode = largest5: the fixed revision has 4 other public classes of >= 1500 lines, BUILD_BRIEF_C10F_ADDENDUM section 1;
hosts are hosts_hop_order of the task record, hop i in the i-th file; newline counts on the fixture checkout):
  hop 1 bidimap.TreeBidiMap        2085 lines   anchor after `nextKey`        (stageB_lib.pick_anchor, seed 4751)
  hop 2 DoubleOrderedMap           1995 lines   anchor after `remove`         (seed 4752)
  hop 3 ExtendedProperties         1784 lines   anchor after `getString`      (seed 4753)
  hop 4 MapUtils                   1678 lines   anchor after `predicatedMap`  (seed 4754)
  hop 5 CursorableLinkedList       1468 lines   anchor after `retainAll`      (seed 4755)   GOLD
  smallest host: CursorableLinkedList, 1468 lines (the gold host). No host was substituted.

The facade keeps its argument guard and delegates to the chain; because SetUniqueList's constructor is protected and no host is in
the list package, the decorator itself is still created in the facade, around the single call to hop 1 that returns its set:
`return new SetUniqueList(list, TreeBidiMap.uniqueSetOf(list));`.
  hop 1 TreeBidiMap.uniqueSetOf          decision: an empty list is left as it is and gives a new empty set
  hop 2 DoubleOrderedMap.uniqueElementsOf  placement: every element of the list copied into an array, in list order
  hop 3 ExtendedProperties.uniqueOf      plumbing: the list is cleared and the whole array is handed on for the refill
  hop 4 MapUtils.uniqueFrom              aggregation: the whole array is handed to the gold in array order, then a new HashSet
                                         of the filled list is returned
  hop 5 CursorableLinkedList.appendOnce  GOLD: the per-element core, a map from each element to its position in the array (only
                                         the position where an element first occurs is recorded) and a pass that appends each
                                         element at its recorded position
The correct configuration computes exactly the original result for every input (same guard and exception, same empty-list result,
the list refilled with the first occurrence of each element in array order, the set holding the elements of the refilled list).

Fault (one-line omission of a decision inside the gold's first loop): the guard `if (positions.containsKey(elements[i]) == false)`
around `positions.put(elements[i], new Integer(i));` is dropped, so the put also runs for a repeated element and the map ends up
with the position where each element LAST occurs; the appending pass then keeps the last occurrence of a repeated element. For
input without repeats nothing changes. Trigger: the EXISTING test TestSetUniqueList::testFactory decorates [1, 2, 1] (three
Integer objects); the variant gives the list [2, 1]: the size assertion (2) passes and assertEquals(new Integer(1), lset.get(0))
fails with expected:<1> but was:<2>. The other three callers of the facade pass an empty list, which hop 1 answers without reaching
the gold, and no other test reaches the chain (probe above), so testFactory is the only newly failing test.

The gold's javadoc states the idiomatic contract (each element once, in the order in which the elements occur in the array, the
encounter order of a stable distinct) and is silent on how a repeated element is treated; for [1, 2, 1] the elements occur in the
order 1, 2, which the variant does not deliver. External pins (the convention outside the gold): the facade's own javadoc ("If the
list contains duplicates, these are removed (first indexed one kept)"); UniqueFilterIterator / UniquePredicate.evaluate ("true if
this is the first time the object is seen"; TestUniqueFilterIterator::testIterator expects One, Two, Three, Four, Five, Six from
One, Two, Three, Two, One, Four, Five, Five, Six, Five); SetUniqueList.addAll and ListOrderedSet.addAll skip an element when an
equal one is already present, so the earlier one keeps its place (TestSetUniqueList::testAddAll, ::testIntCollectionAddAll;
TestListOrderedSet::testListAddReplacing: "will match but not replace A as equal").

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, the guarded put loop, the appending loop):
  T1 absent: list receives every add; elements is read in both loops (keys, positions, appended values).
  T2 absent: positions is read in the second loop and decides each add; both loop indices are advanced by their headers; no
     literal-initialised local, no flag, counter or best-so-far; the guard has two different effects (put or no put) and so does
     the position test (add or no add).
  T3 absent: no enumerated set, no pair halves or range ends, no named class; one uniform treatment of every element.
  T4 absent: 'each element once, in the order in which the elements occur in the array' is a general description that the two
     loops address; '@param ... not null' are caller preconditions; no limit, bound, value class or case is named; no comment;
     the identifiers (positions, appendOnce) name nothing the body does not do.
  Nothing needed rewriting.
 Variant gold (javadoc, signature, `positions.put(elements[i], new Integer(i));` in the first loop, the unchanged second loop):
  T1 absent: list is appended to; elements is read in both loops and every entry can change what is appended.
  T2 absent: positions is filled in the first loop and read in the second, where it decides each add; i is advanced by both for
     headers; no literal-initialised or loop-moved local is left unassigned; the only decision (position test) adds or skips.
  T3 absent: no case, branch or check over a set remains in the first loop and the second treats every element alike; no pair,
     range end or named class is handled in part (no member handled).
  T4 absent: 'each element once' and 'in the order in which the elements occur in the array' are general descriptions that the
     body addresses (one recorded position per element, a pass over the array in order); seeing that a repeated element keeps
     its last position needs the input to be simulated, which the checklist excludes; '@param ... not null' are caller
     preconditions; no concrete rule, bound, value class or case is named.

Single owner: only the gold sees the elements together with their positions and decides which occurrence of a repeated element is
appended; hops 1-3 pass the list and the complete array along, and hop 4 only calls the gold and copies the resulting list into a
set. Once the gold has appended [2, 1], the list no longer tells which occurrence came first. Declared alternatives (G9): hop 2
copies the elements in the opposite order (the trigger input is a palindrome, so the gold still returns [2, 1]); hop 3 empties the
list with removeAll instead of clear; hop 4 builds the set from the array instead of the list. None changes the trigger result.
Recorded one-line edits above the gold that pass the trigger and the full suite (each checked on the variant in a scratch copy,
/private/tmp/c15-bypass: trigger 0 failing, defects4j test 0 failing; testFactory is the only test that decorates a non-empty
list, so the suite cannot tell order-preserving from order-changing edits):
 B-0 bypass: the facade (its original body) or hop 4 replaces the gold call with list.addAll(new java.util.LinkedHashSet(
     java.util.Arrays.asList(elements))) or an equivalent stable distinct, discarding the gold.
 B-1 bypass (second implementation of the gold's decision): hop 2, 3 or 4 removes the repeated elements before the gold, e.g. hop 4
     `CursorableLinkedList.appendOnce(list, IteratorUtils.toArray(new org.apache.commons.collections.iterators.UniqueFilterIterator(java.util.Arrays.asList(elements).iterator())));`;
     the once-only decision is then taken by UniqueFilterIterator and never by the gold. It also breaks the documented hand-over
     of the hop where it is made: hop 2 copies every element of the list, hop 3 hands on the whole array, hop 4 hands on the
     whole array in array order.
 B-2 test-fitted: hop 2 sorts the array before the hand-over (java.util.Arrays.sort; the gold then sees [1, 1, 2] and returns
     [1, 2]) or hop 4 turns the refilled list around after the gold (java.util.Collections.reverse(list): [2, 1] becomes [1, 2]).
     Both pass the suite only because of the shape of the trigger input; they break the documented list order (with the sort,
     decorate([2, 1]) gives [1, 2]; with the turn-around, decorate([1, 2]) gives [2, 1]), and the sort throws
     ClassCastException for elements that are not mutually comparable.

Lie: the facade's javadoc claims the supplied list is not copied and each duplicate is deleted from it in place during a single
pass of its list iterator; the chain copies the list into an array, clears it and refills it. It names neither positions nor
repeated elements' treatment nor any hop, and a sort-based lie was avoided because sorting the trigger input would pass it."""

SUL = "src/java/org/apache/commons/collections/list/SetUniqueList.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Appends the elements of an array to a list, each element once, in the
 * order in which the elements occur in the array.
 *
 * @param list  the list to append to, not null
 * @param elements  the elements to append, not null
 */
public static void appendOnce(List list, Object[] elements) {
    final Map positions = new HashMap();
    for (int i = 0; i < elements.length; i++) {
        if (positions.containsKey(elements[i]) == false) {
            positions.put(elements[i], new Integer(i));
        }
    }
    for (int i = 0; i < elements.length; i++) {
        if (((Integer) positions.get(elements[i])).intValue() == i) {
            list.add(elements[i]);
        }
    }
}'''

HOP1 = '''/**
 * Gets the set of the elements of a list, leaving each element in the
 * list once.
 * <p>
 * An empty list is left as it is and gives an empty set.
 *
 * @param list  the list to process, must not be null
 * @return a new set holding the elements of the list
 */
public static Set uniqueSetOf(List list) {
    if (list.isEmpty()) {
        return new HashSet();
    }
    return DoubleOrderedMap.uniqueElementsOf(list);
}'''

HOP2 = '''/**
 * Gets the set of the elements of a non-empty list, leaving each element
 * in the list once.
 * <p>
 * Every element of the list is first copied into an array, in list order.
 *
 * @param list  the list to process, must not be null or empty
 * @return a new set holding the elements of the list
 */
public static Set uniqueElementsOf(List list) {
    return ExtendedProperties.uniqueOf(list, list.toArray());
}'''

HOP3 = '''/**
 * Refills a list from an array of the elements it held, each element
 * once, and gets the set of its elements.
 * <p>
 * The list is cleared, and the whole array is then handed on for the
 * refill.
 *
 * @param list  the list to refill, must not be null
 * @param elements  the elements the list held, in list order, must not be null
 * @return a new set holding the elements of the refilled list
 */
public static Set uniqueOf(List list, Object[] elements) {
    list.clear();
    return MapUtils.uniqueFrom(list, elements);
}'''

HOP4 = '''/**
 * Fills an empty list from an array, each element once, and gets the set
 * of the elements of the list.
 * <p>
 * The whole array is handed on for the fill, in array order, and the set
 * is then built from the filled list.
 *
 * @param list  the empty list to fill, must not be null
 * @param elements  the elements to add, must not be null
 * @return a new set holding the elements of the list
 */
public static Set uniqueFrom(List list, Object[] elements) {
    CursorableLinkedList.appendOnce(list, elements);
    return new HashSet(list);
}'''

DESIGN = {
 "instance": "Collections-15", "project": "Collections", "bug_id": 15, "seed": 4651,
 "src_root": "src/java", "test_root": "src/test",
 "host_mode": "largest5", "host_lines": [2085, 1995, 1784, 1678, 1468], "facade_reuse_of": ["Collections-5"],
 "reachability_probe": "facade made to throw IllegalStateException(\"PROBE-REACHED\") (behind if (true)) in a scratch copy; "
                       "TestSetUniqueList::testFactory, ::testUniqueListReInsert, ::testUniqueListDoubleInsert, "
                       "::testCollections304 each fail with PROBE-REACHED at SetUniqueList.decorate; ::testAdd (control) passes; "
                       "full suite: exactly these 4 fail. Reachable.",
 "facade": {"file": SUL, "class": "org.apache.commons.collections.list.SetUniqueList", "method": "decorate", "near_line": 73},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/list/TestSetUniqueList.java",
             "test_class": "org.apache.commons.collections.list.TestSetUniqueList", "test_method": "testFactory"},
 "expected_signature": "expected:<1> but was:<2>",
 "gold": {"method": "appendOnce", "text": GOLD_TEXT,
          "fault": {"old": "            if (positions.containsKey(elements[i]) == false) {\n"
                           "                positions.put(elements[i], new Integer(i));\n"
                           "            }",
                    "new": "            positions.put(elements[i], new Integer(i));"}},
 "chain": {
   "facade_body": "if (list == null) {\n"
                  "            throw new IllegalArgumentException(\"List must not be null\");\n"
                  "        }\n"
                  "        return new SetUniqueList(list, org.apache.commons.collections.bidimap.TreeBidiMap.uniqueSetOf(list));",
   "lie": "The supplied list is not copied: each duplicate is deleted from it in place, during a single pass of its "
          "list iterator.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "uniqueSetOf",
      "imports": ["java.util.HashSet", "java.util.List", "org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "uniqueElementsOf",
      "imports": ["java.util.List"], "text": HOP2},
     {"file": EP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "uniqueOf",
      "imports": ["java.util.Set"], "text": HOP3},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "uniqueFrom",
      "imports": ["java.util.HashSet", "java.util.List", "java.util.Set"], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableLinkedList", "method": "appendOnce",
      "imports": ["java.util.HashMap", "java.util.Map"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.list.SetUniqueList::decorate",
              "org.apache.commons.collections.functors.UniquePredicate::evaluate",
              "org.apache.commons.collections.list.SetUniqueList::addAll",
              "org.apache.commons.collections.set.ListOrderedSet::addAll"],
 "ownership_reason": "Only the gold sees the elements together with their positions in the array and decides which occurrence of "
                     "a repeated element is appended; hops 1-3 pass the list and the complete array along (an empty list is "
                     "answered at hop 1), and hop 4 only calls the gold and copies the resulting list into a set, so once the "
                     "gold has appended [2, 1] no caller can tell which occurrence came first. The gold's javadoc promises each "
                     "element once, in the order in which the elements occur in the array, which for [1, 2, 1] is 1 then 2. The "
                     "convention is pinned outside the gold: the facade's javadoc ('If the list contains duplicates, these are "
                     "removed (first indexed one kept)'); UniqueFilterIterator, built on UniquePredicate.evaluate ('true if this "
                     "is the first time the object is seen'), returns One, Two, Three, Four, Five, Six from One, Two, Three, Two, "
                     "One, Four, Five, Five, Six, Five (TestUniqueFilterIterator testIterator); SetUniqueList.addAll and "
                     "ListOrderedSet.addAll skip an element when an equal one is already present, so the earlier one keeps its "
                     "place (TestSetUniqueList testAddAll and testIntCollectionAddAll; TestListOrderedSet testListAddReplacing). "
                     "Recorded bypasses: a hop that replaces the gold call by a stable distinct of its own (LinkedHashSet), or "
                     "removes the repeated elements before the gold (UniqueFilterIterator), implements the gold's decision a "
                     "second time; sorting the array or reordering the refilled list passes only because the trigger input is "
                     "[1, 2, 1] and breaks the documented list order.",
 "ownership_tests": ["org.apache.commons.collections.iterators.TestUniqueFilterIterator::testIterator",
                     "org.apache.commons.collections.list.TestSetUniqueList::testIntCollectionAddAll",
                     "org.apache.commons.collections.list.TestSetUniqueList::testAddAll",
                     "org.apache.commons.collections.set.TestListOrderedSet::testListAddReplacing"],
 "compensating": {
   "chain": [
     {"file": DOM, "old": "return ExtendedProperties.uniqueOf(list, list.toArray());",
      "new": "return ExtendedProperties.uniqueOf(list, IteratorUtils.toArray(new org.apache.commons.collections.iterators.ReverseListIterator(list)));",
      "why": "hop 2 copies the elements of the list in the opposite order"},
     {"file": EP, "old": "list.clear();\n        return MapUtils.uniqueFrom(list, elements);",
      "new": "list.removeAll(java.util.Arrays.asList(elements));\n        return MapUtils.uniqueFrom(list, elements);",
      "why": "hop 3 removes the copied elements from the list instead of clearing it"},
     {"file": MU, "old": "return new HashSet(list);",
      "new": "return new HashSet(java.util.Arrays.asList(elements));",
      "why": "hop 4 builds the set from the array instead of the refilled list"},
   ],
 },
 "host_notes": "host_mode largest5 (4 other public classes of >= 1500 lines in the fixed revision): the hosts are the task record's "
               "hosts_hop_order, the five largest public non-interface non-enum classes other than SetUniqueList, in that order: "
               "bidimap.TreeBidiMap (2085 lines, hop 1), DoubleOrderedMap (1995, hop 2), ExtendedProperties (1784, hop 3), "
               "MapUtils (1678, hop 4), CursorableLinkedList (1468, hop 5, gold; the smallest host). Anchors from "
               "stageB_lib.pick_anchor with the instance seed 4651 (+100+i), as mr2_spec inserts them: after TreeBidiMap.nextKey "
               "(seed 4751), DoubleOrderedMap.remove (4752), ExtendedProperties.getString (4753), MapUtils.predicatedMap (4754), "
               "CursorableLinkedList.retainAll (4755); each lies in the outer class (brace depth 1). All five are public "
               "concrete classes in which a static method compiles (DoubleOrderedMap is final, ExtendedProperties extends "
               "Hashtable, DoubleOrderedMap and CursorableLinkedList are deprecated, none of which affects a static method); none "
               "was substituted. The facade calls hop 1 by its fully-qualified name inside the SetUniqueList constructor call "
               "(the constructor is protected and no host is in the list package); each hop imports the next host where it "
               "is in another package and the java.util types it uses.",
}
