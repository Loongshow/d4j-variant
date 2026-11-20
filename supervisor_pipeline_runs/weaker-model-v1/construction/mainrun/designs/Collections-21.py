"""Main run Collections-21 (cell C10f, batch 6; the C10 recipe on the fixed checkout of Defects4J Collections-21; the real bug
modified SetUniqueList, the target class).

Facade: SetUniqueList.setUniqueList(List) (the only allowed target, BATCH6_PREREGISTRATION.md row 153). It has no production
caller; its test callers are eight SetUniqueListTest methods (see the probe below).
Original computation: a null list gives IllegalArgumentException; an empty list is wrapped with a new empty HashSet; otherwise
the elements are copied into a temporary ArrayList, the list is cleared and wrapped with a new HashSet, and the copy is added
back with SetUniqueList.addAll, which keeps an element only when the set does not hold an equal one yet (first indexed one
kept). The decorated list is the caller's own list object.

reachability_probe: in a scratch copy of the fixture the facade's first statement was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; after defects4j compile, defects4j test -t on each of the
eight test methods that call the facade (SetUniqueListTest::testFactory, testUniqueListReInsert, testUniqueListDoubleInsert,
testCollections304, testCollections307, testRetainAll, testRetainAllWithInitialList, testRetainAllCollections427) failed with
java.lang.IllegalStateException: PROBE-REACHED, and the full suite (11806 tests) had exactly these eight failures, all with the
probe message. REACHED.

Hosts (host_mode = largest5: the fixed revision has only 3 other public classes of at least 1500 lines, so the five hosts are
the five largest public non-interface non-enum classes other than SetUniqueList, by newline count, from batch6_tasks.json
hosts_hop_order; anchors from stageB_lib.pick_insertion_anchor with the instance seed 7273, seed + 100 + i):
  hop 1 bidimap.TreeBidiMap        2172 lines  anchor after removeValue          decision: an empty list is left as it is and
                                                                                 gets a new empty HashSet (the original shortcut)
  hop 2 CollectionUtils            1805 lines  anchor after isEqualCollection    aggregation: has the list rebuilt, then collects
                                                                                 the rebuilt list into a new HashSet
  hop 3 MapUtils                   1779 lines  anchor after isEmpty              pass-through
  hop 4 trie.PatriciaTrie          1447 lines  anchor after subMap               placement: copies the list into a new ArrayList,
                                                                                 clears it, and has it refilled from the copy
  hop 5 map.AbstractHashedMap      1389 lines  anchor after clear                GOLD: the per-element core, appending each element
                                                                                 the list does not already contain
Smallest host: 1389 lines (AbstractHashedMap). None was substituted.
The facade keeps its argument guard and makes one delegating call; because SetUniqueList's only constructor is protected and no
host is in the list package or a subclass, the facade wraps the caller's list with the set that the chain returns
(`return new SetUniqueList<E>(list, ...TreeBidiMap.valueSetOf(list));`), exactly as the original body ends.
The correct configuration returns the original result for every input: same guard, same empty shortcut, the caller's list is
cleared and refilled in place with the first occurrence of every element in order (the presence test uses the null-safe
equality idiom `existing == element || existing != null && existing.equals(element)`, which is the equality HashSet applies),
and the set is a default-constructed HashSet filled with the distinct elements in first-occurrence order (the same insertion
sequence as the original addAll, so the same table).

Fault (one-line omission in the gold, in its per-element decision): the equality line of the presence test is dropped, so an
element counts as present only when the very same instance has been appended. Trigger: the EXISTING test
SetUniqueListTest::testFactory, whose list is {new Integer(1), new Integer(2), new Integer(1)} (two equal, distinct instances);
assertEquals("Duplicate element was added.", 2, lset.size()) fails with expected:<2> but was:<3>. The seven other tests that
reach the facade pass lists without repeats (testRetainAllWithInitialList: 0..4; testRetainAllCollections427: 0..49999) or
empty lists, so only testFactory newly fails. The gold's javadoc states the idiomatic contract (it appends each element of a
collection that the list does not already contain) and is silent on how presence is tested; the list [1, 2] contains the
second Integer 1, so the variant violates that contract on the trigger input.

External pins (the convention that an equal element, not only the same instance, is already contained): SetUniqueList.addAll
('Only elements that are not already in this list will be added, and duplicates from the specified collection will be
ignored', through set.add), pinned by SetUniqueListTest::testAddAll, which adds two distinct new Integer(1) instances and expects
one; SetUniqueList.add (set.contains); AbstractLinkedList.isEqualValue (`value1 == value2 || (value1 == null ? false :
value1.equals(value2))`, the same idiom, used by indexOf, contains and remove); AbstractHashedMap.isEqualKey (`key1 == key2 ||
key1.equals(key2)`) in the gold's own host; and the facade's own javadoc ('If the list contains duplicates, these are removed
(first indexed one kept)').

Single owner: only the gold compares an element with the elements already appended; hops 1-4 hold the whole list, copy it,
clear it or collect it into a set, and never compare two elements. The refilled list is decided by the gold alone and is the
caller's own list (the facade wraps it), so a hop cannot substitute another list. Declared alternatives (G9): hop 2 collects the
set through a LinkedHashSet of the rebuilt list; hop 4 empties the list with removeAll(former); hop 3 hands the gold's chain a
full-range subList view. None changes the refilled list [1, 2, 1].
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each):
 B-0 bypass: the facade's original body (copy, clear, SetUniqueList.addAll) replaces the chain.
 B-1 bypass: a hop removes the repeats itself with `CollectionUtils.filter(list, UniquePredicate.<E>uniquePredicate());` (hop 2
     after the rebuild, or hop 3 before it; checked at both): a second implementation of the gold's presence decision, through
     another class's set; no hop's documentation says that it removes repeats. (At hop 4 between the copy and the clear it has
     no effect, since the copy already holds the repeat.)
 B-2 bypass: hop 4 copies through a LinkedHashSet (`new ArrayList<E>(new java.util.LinkedHashSet<E>(list))`): the gold then never
     meets a repeat; a second implementation of the gold's decision, and the copy is then no longer a copy of the list, as hop 4's
     javadoc says it is.
 B-3 test-fitted: hop 4 copies through a HashSet (`new ArrayList<E>(new HashSet<E>(list))`): passes the suite only because small
     Integers iterate in numeric order; it loses the list order (setUniqueList of ["b", "a"] gives [a, b]), against the facade's
     'using the supplied list to retain order'.

Lie: the facade's javadoc claims the duplicates are removed in place by walking the list from its last index to its first and
removing each element that also occurs at a lower index; the chain copies the list, clears it and refills it forwards. It names
neither the presence test nor equality nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (appendElements with `if (existing == element || existing != null && existing.equals(element))`):
  T1 absent: elements is iterated and every element can be appended; list is scanned and appended to.
  T2 absent: present is initialised to false and set to true inside the inner loop that it flags, then decides the append; element
     and existing are read; both ifs have different effects (break with the flag set; append or not).
  T3 absent: the null case is complete (null == null by identity; a null existing never receives equals; equals(null) is false);
     no pair, range end or named class is handled in part.
  T4 absent: the javadoc names only the general contract ('each element of a collection that the list does not already contain',
     'in the iteration order of the collection') and caller preconditions ('not null'); nothing to rewrite.
 Variant gold (javadoc, signature, the two loops with `if (existing == element) {`):
  T1 absent: elements is iterated and its elements are appended; list is scanned in the inner loop and appended to; both change
     the result.
  T2 absent: present: literal false, assigned true inside the inner loop (the loop it flags), read in `if (!present)`; element and
     existing are read in the comparison and the append; no frozen cursor, counter or best-so-far; both decisions matter.
  T3 absent: no case, branch or check over a closed set remains; no null test remains at all ('no member handled'); the gold names
     no class; there is no pair of halves or range ends.
  T4 absent: 'each element of a collection that the list does not already contain' and 'in the iteration order of the
     collection' are general descriptions that the presence loop and the in-order append address; '@param ... not null' are
     caller preconditions; identifiers (element, existing, present) name nothing the body does not meet; no inline comment."""

SUL = "src/main/java/org/apache/commons/collections4/list/SetUniqueList.java"
TBM = "src/main/java/org/apache/commons/collections4/bidimap/TreeBidiMap.java"
CU = "src/main/java/org/apache/commons/collections4/CollectionUtils.java"
MU = "src/main/java/org/apache/commons/collections4/MapUtils.java"
PT = "src/main/java/org/apache/commons/collections4/trie/PatriciaTrie.java"
AHM = "src/main/java/org/apache/commons/collections4/map/AbstractHashedMap.java"

GOLD_TEXT = '''/**
 * Appends to a list each element of a collection that the list does not
 * already contain, in the iteration order of the collection.
 *
 * @param <E>  the type of the elements
 * @param elements  the elements to append, not null
 * @param list  the list to append to, not null
 */
public static <E> void appendElements(final Collection<? extends E> elements, final List<E> list) {
    for (final E element : elements) {
        boolean present = false;
        for (final E existing : list) {
            if (existing == element
                    || existing != null && existing.equals(element)) {
                present = true;
                break;
            }
        }
        if (!present) {
            list.add(element);
        }
    }
}'''

HOP1 = '''/**
 * Gets a new <code>HashSet</code> of the elements of a list, after the
 * list has been rebuilt from its own elements.
 * <p>
 * An empty list is left as it is, and a new empty set is returned.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list, must not be null
 * @return a new set of the elements of the list
 */
public static <E> Set<E> valueSetOf(final List<E> list) {
    if (list.isEmpty()) {
        return new HashSet<E>();
    }
    return CollectionUtils.rebuildToSet(list);
}'''

HOP2 = '''/**
 * Rebuilds a non-empty list from its own elements and returns a new
 * <code>HashSet</code> holding the elements of the rebuilt list.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to rebuild, must not be null or empty
 * @return a new set of the elements of the rebuilt list
 */
public static <E> Set<E> rebuildToSet(final List<E> list) {
    MapUtils.repopulateList(list);
    final Set<E> set = new HashSet<E>();
    set.addAll(list);
    return set;
}'''

HOP3 = '''/**
 * Rebuilds a list from its own elements.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to rebuild, must not be null
 */
public static <E> void repopulateList(final List<E> list) {
    PatriciaTrie.refillList(list);
}'''

HOP4 = '''/**
 * Rebuilds a list from its own elements: the list is copied into a new
 * <code>ArrayList</code>, then cleared, and then refilled from the copy.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to rebuild, must not be null
 */
public static <E> void refillList(final List<E> list) {
    final List<E> former = new ArrayList<E>(list);
    list.clear();
    AbstractHashedMap.appendElements(former, list);
}'''

DESIGN = {
 "instance": "Collections-21", "project": "Collections", "bug_id": 21, "seed": 7273,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SUL, "class": "org.apache.commons.collections4.list.SetUniqueList", "method": "setUniqueList", "near_line": 74},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/collections4/list/SetUniqueListTest.java",
             "test_class": "org.apache.commons.collections4.list.SetUniqueListTest", "test_method": "testFactory"},
 "expected_signature": "Duplicate element was added. expected:<2> but was:<3>",
 "gold": {"method": "appendElements", "text": GOLD_TEXT,
          "fault": {"old": "                if (existing == element\n"
                           "                        || existing != null && existing.equals(element)) {",
                    "new": "                if (existing == element) {"}},
 "chain": {
   "facade_body": "if (list == null) {\n            throw new IllegalArgumentException(\"List must not be null\");\n        }\n"
                  "        return new SetUniqueList<E>(list, org.apache.commons.collections4.bidimap.TreeBidiMap.valueSetOf(list));",
   "lie": "The duplicates are removed in place, the list being walked from its last index to its first and each element "
          "that also occurs at a lower index being removed.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections4.bidimap.TreeBidiMap", "method": "valueSetOf",
      "imports": ["java.util.HashSet", "java.util.List", "org.apache.commons.collections4.CollectionUtils"], "text": HOP1},
     {"file": CU, "class": "org.apache.commons.collections4.CollectionUtils", "method": "rebuildToSet",
      "imports": [], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections4.MapUtils", "method": "repopulateList",
      "imports": ["java.util.List", "org.apache.commons.collections4.trie.PatriciaTrie"], "text": HOP3},
     {"file": PT, "class": "org.apache.commons.collections4.trie.PatriciaTrie", "method": "refillList",
      "imports": ["java.util.ArrayList", "java.util.List", "org.apache.commons.collections4.map.AbstractHashedMap"], "text": HOP4},
     {"file": AHM, "class": "org.apache.commons.collections4.map.AbstractHashedMap", "method": "appendElements",
      "imports": ["java.util.List"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections4.list.SetUniqueList::addAll",
              "org.apache.commons.collections4.list.SetUniqueList::add",
              "org.apache.commons.collections4.list.AbstractLinkedList::isEqualValue",
              "org.apache.commons.collections4.map.AbstractHashedMap::isEqualKey"],
 "ownership_reason": "Only the gold compares an element with the elements already appended; hops 1-4 hold the whole list, copy "
                     "it, clear it or collect it into a set, and never compare two elements, and the list that the gold refills "
                     "is the caller's own list, which the facade wraps (the facade calls the protected SetUniqueList constructor "
                     "itself because no host can reach it, exactly as the original body ends). The gold promises to append each "
                     "element of the collection that the list does not already contain; after 1 and 2 the list contains the "
                     "second, distinct Integer 1, so appending it violates that contract. The convention that an equal element, "
                     "not only the same instance, is already contained is pinned outside the gold: SetUniqueList.addAll adds "
                     "only elements that are not already in the list and ignores duplicates of the specified collection "
                     "(SetUniqueListTest testAddAll adds two distinct new Integer(1) instances and expects one); SetUniqueList.add "
                     "tests set.contains; AbstractLinkedList.isEqualValue (value1 == value2 || (value1 == null ? false : "
                     "value1.equals(value2))) and AbstractHashedMap.isEqualKey (key1 == key2 || key1.equals(key2)) use the same "
                     "identity-or-equals idiom; the facade's javadoc says duplicates are removed, first indexed one kept. A hop "
                     "can absorb the repeats only by implementing the removal a second time (CollectionUtils.filter with "
                     "UniquePredicate, or a LinkedHashSet copy at hop 4, which is then no longer the copy of the list that hop "
                     "4's javadoc describes); a HashSet copy at hop 4 passes the suite but loses the list order "
                     "(setUniqueList of [\"b\", \"a\"] would give [a, b]).",
 "ownership_tests": ["org.apache.commons.collections4.list.SetUniqueListTest::testAddAll",
                     "org.apache.commons.collections4.list.SetUniqueListTest::testIntCollectionAddAll",
                     "org.apache.commons.collections4.list.SetUniqueListTest::testAdd",
                     "org.apache.commons.collections4.list.SetUniqueListTest::testRetainAllWithInitialList"],
 "compensating": {
   "chain": [
     {"file": CU, "old": "        set.addAll(list);",
      "new": "        set.addAll(new java.util.LinkedHashSet<E>(list));",
      "why": "hop 2 collects the set through an order-keeping set of the rebuilt list"},
     {"file": PT, "old": "        list.clear();\n        AbstractHashedMap.appendElements(former, list);",
      "new": "        list.removeAll(former);\n        AbstractHashedMap.appendElements(former, list);",
      "why": "hop 4 empties the list by removing every copied element"},
     {"file": MU, "old": "        PatriciaTrie.refillList(list);",
      "new": "        PatriciaTrie.refillList(list.subList(0, list.size()));",
      "why": "hop 3 rebuilds the list through a full-range view"},
   ],
 },
 "host_notes": "host_mode largest5 (3 other public classes of at least 1500 lines in the fixed revision). Hosts are exactly "
               "batch6_tasks.json hosts_hop_order: bidimap.TreeBidiMap (2172 lines, hop 1), CollectionUtils (1805, hop 2), "
               "MapUtils (1779, hop 3), trie.PatriciaTrie (1447, hop 4), map.AbstractHashedMap (1389, hop 5, gold); smallest "
               "host 1389 lines. Anchors by stageB_lib.pick_insertion_anchor with seed 7273 + 100 + i (7373-7377): after "
               "removeValue, isEqualCollection, isEmpty, subMap and clear, all in the outer class. All five are public "
               "top-level classes in which a static method compiles (TreeBidiMap, PatriciaTrie and AbstractHashedMap are "
               "generic and AbstractHashedMap is abstract, which does not affect a static method with its own type "
               "parameter); none was substituted. The facade calls hop 1 by its fully-qualified name; each hop imports the "
               "next host where it is in another package (CollectionUtils and MapUtils share a package).",
}
