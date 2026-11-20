"""Main run Collections-5 (C10f recipe on the fixed checkout of Defects4J Collections-5; the real bug modified SetUniqueList, the
target class). Cell C10f, batch 6, host_mode largest5.

Facade: SetUniqueList.decorate(List) (the only allowed target, BATCH6_PREREGISTRATION.md row 146). Original computation: a null
list throws IllegalArgumentException("List must not be null"); an empty list is wrapped as it is with a new HashSet; any other
list is copied, cleared and refilled through SetUniqueList.addAll, which appends an element only if the set does not already
hold it and then adds it to the set (first indexed occurrence kept); the list is wrapped (not copied) with that set.

reachability_probe: in a scratch copy of the fixture, decorate's first statement was made
`throw new IllegalStateException("PROBE-REACHED");`; defects4j test -t on TestSetUniqueList::testFactory, ::testUniqueListReInsert
and ::testUniqueListDoubleInsert: all three fail with java.lang.IllegalStateException: PROBE-REACHED at
SetUniqueList.decorate(SetUniqueList.java:74); the full suite (defects4j test) then has exactly these three failing tests. The
facade is reached by existing tests. Only testFactory passes a non-empty list ([1, 2, 1], distinct Integer instances).

SetUniqueList's constructor is protected and none of the five hosts is in the list package, so no hop can construct the
decorator. The facade therefore keeps the constructor call of its original body and its delegating call to hop 1 supplies the
set: `return new SetUniqueList(list, TreeBidiMap.elementSet(list));` (Java evaluates the arguments first, so the list is brought
into step before it is wrapped). The chain works on the caller's list in place and returns the set.

Hosts (host_mode = largest5: the fixed revision has 4 other public classes of >= 1500 lines; the five largest public,
non-interface, non-enum classes other than SetUniqueList, by newline count, task record hosts_hop_order, none substituted):
  hop 1 bidimap.TreeBidiMap        2085 lines   decision: an empty list is left as it is and gives a new empty HashSet
  hop 2 DoubleOrderedMap           1995 lines   placement: a new HashSet is used for the set
  hop 3 ExtendedProperties         1717 lines   pass-through
  hop 4 MapUtils                   1645 lines   pass-through
  hop 5 CursorableLinkedList       1468 lines   GOLD: the per-element core: snapshot of the list, clear, and the refill in which
                                                each element is added to the set and appended, unless the set already holds it
Host sizes 2085, 1995, 1717, 1645, 1468; smallest host 1468 lines (the gold host). Anchors (stageB_lib.pick_insertion_anchor via
insert_hop, instance seed 8405, anchor seeds 8505-8509): after TreeBidiMap.size, DoubleOrderedMap.clear, the
ExtendedProperties() constructor, MapUtils.unmodifiableMap, CursorableLinkedList.iterator; all in the outer class.
The correct configuration gives the original result for every list that honours the List contract (the original appends with
add(size(), e) through SetUniqueList.add(int, Object); the gold appends with add(e)): same guard, same empty-list shortcut (no
clear), same snapshot-clear-refill, same first-occurrence rule, same HashSet.

Fault (one-line omission of a special-case step in the gold's iteration): the skip of an element that the set already holds
(`if (set.contains(object)) { continue; }`) is dropped, so every element of the snapshot is appended again. The gold then reads as
the plain refill routine (take the elements, clear, add each to the set and to the list). Trigger: the EXISTING test
TestSetUniqueList::testFactory: decorate([1, 2, 1]) leaves the list [1, 2, 1] with the set {1, 2}, and its first assertion fails
with "Duplicate element was added. expected:<2> but was:<3>". testUniqueListReInsert and testUniqueListDoubleInsert decorate an
empty LinkedList, which hop 1 returns before the gold, and still pass; no other test reaches the chain.

The gold's javadoc states the idiomatic contract (it brings a list into step with a set; the elements are added to the set in
list order and the list is refilled from them) and is silent on the skip. After the variant, the list [1, 2, 1] is not in step
with the set {1, 2} (the facade's 'first indexed one kept', the SetUniqueList constructor's 'the set and list must both be
correctly initialised to the same elements'). The convention is pinned outside the gold: SetUniqueList.add(int, Object) appends
an element only when 'set.contains(object) == false' and then adds it to the set, and SetUniqueList.addAll(int, Collection)
goes through it (TestSetUniqueList testAdd, testAddAll, testIntCollectionAddAll pass); ListOrderedSet.add adds an element to the
order list only on its first add ('re-adding doesn't change order'; TestListOrderedSet testOrdering passes).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (refill with the skip):
  T1 absent: list is read (toArray), cleared and appended to; set is tested (contains), added to and returned.
  T2 absent: elements is iterated and its entries passed to add; i is advanced by the for header; object reaches contains and both
     adds; no literal-initialised local, flag, counter or best-so-far; the skip decision changes the effect (append or not).
  T3 absent: no closed set with a handled and an unhandled member; list and set are both added to; no pair halves or range ends.
  T4 absent: the javadoc names no rule, limit, bound, value class or case ('into step with a set', 'added to the set in list
     order', 'refilled from them' are general descriptions the body addresses); 'must not be null', 'must be empty' are caller
     preconditions; identifiers (refill, elements, object) name nothing the body does not do.
 Variant gold (javadoc, signature, `Object[] elements = list.toArray(); list.clear(); for (...) { Object object = elements[i];
 set.add(object); list.add(object); } return set;`):
  T1 absent: list is read by toArray, cleared and appended to; set is added to and is the return value; each changes the result.
  T2 absent: elements, i and object are all live (loop bound and cursor, add arguments); i is advanced by the for header; there
     is no literal-initialised local and no branch, case or ternary at all.
  T3 absent: no case, branch or check remains, so no set has a handled and an unhandled member ('No member handled'); both
     parameters that receive elements (the set and the list) get the same add.
  T4 absent: 'Brings a list into step with a set' is a general description; 'the elements of the list are added to the set in
     list order' and 'the list is refilled from them' are met by the loop; '@param set ... must be empty and not null' and
     '@param list ... must not be null' are caller preconditions; '@return the set' is met; no inline comment.

Single owner: only the gold holds the snapshot of the caller's list while the list is refilled, and it refills the caller's list
in place. Hops 1-4 hand the same list object down unchanged (each hop's javadoc says so: 'any other list is handed on as it is',
'the list is handed on as it is', 'The list and the set are handed on as they are') and get back the set; the facade wraps the
caller's list. A caller cannot pre-filter by passing a de-duplicated copy (checked on the variant: a LinkedHashSet copy handed
down by the facade, hop 1, hop 3 or hop 4, or a LinkedHashSet-seeded set at hop 2, still fails the trigger with the same
signature: the copy is refilled and the caller's list, which the facade wraps, keeps [1, 2, 1]); hops cannot construct a
SetUniqueList view (protected constructor: compile error), and SetUniqueList.decorate called from a hop recurses into the chain
(StackOverflowError). Declared alternatives (G9): hop 1 returns new HashSet(list) for a list of fewer than two elements; hop 2
seeds the set with the elements of the list; hop 4 hands the gold a copy of the list. None changes the trigger.
Recorded edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy, defects4j
test: 0 failing tests each):
 B-0 bypass: the facade's original body (copy, clear, new SetUniqueList, addAll), discarding the chain including the gold.
 B-1 bypass, a second implementation of the gold's decision: an added statement
     `CollectionUtils.filter(list, PredicateUtils.uniquePredicate());` before the delegating call (checked at hop 3; the same
     works in the facade or any of hops 1-4). The de-duplication is then done by UniquePredicate and the gold's own skip never
     matters. At a hop it contradicts that hop's javadoc (the list is handed on as it is); in the facade it re-implements the
     gold's decision above the chain. Either way the gold still violates its contract on any list that holds an element twice,
     and the pinned convention (the step that adds an element to the set skips it when the set already holds it:
     SetUniqueList.add(int, Object), ListOrderedSet.add) is still broken in the gold.
 B-2 bypass: the facade wraps a de-duplicated copy, `new SetUniqueList(new ArrayList(new java.util.LinkedHashSet(list)),
     TreeBidiMap.elementSet(list))`: the chain's refilled list becomes dead output, and decorate no longer wraps the supplied list
     (its javadoc and the constructor's 'wraps (not copies)').
 B-3 test-fitted: hop 4 truncates the list to the size of the set after the gold
     (`Set result = CursorableLinkedList.refill(list, set); list.subList(result.size(), list.size()).clear(); return result;`):
     passes testFactory ([1, 2, 1] -> [1, 2]) but keeps the wrong elements in general ([1, 1, 2] -> [1, 1]); not consistent with
     the documented contract.

Lie: the facade's javadoc claims the elements are taken out of the list and put back in a single pass from the last element to
the first, each inserted at the head of the list; the chain walks the elements from first to last and appends. It names neither
the set membership test nor any omitted step nor any hop."""

SUL = "src/java/org/apache/commons/collections/list/SetUniqueList.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MAU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Brings a list into step with a set.
 * <p>
 * The elements of the list are added to the set in list order, and the
 * list is refilled from them.
 *
 * @param list  the list to refill, must not be null
 * @param set  the set to add to, must be empty and not null
 * @return the set
 */
public static Set refill(List list, Set set) {
    Object[] elements = list.toArray();
    list.clear();
    for (int i = 0; i < elements.length; i++) {
        Object object = elements[i];
        if (set.contains(object)) {
            continue;
        }
        set.add(object);
        list.add(object);
    }
    return set;
}'''

HOP1 = '''/**
 * Gets the set of the elements of a list, bringing the list into step
 * with that set.
 * <p>
 * An empty list is left as it is and gives a new empty
 * <code>HashSet</code>; any other list is handed on as it is.
 *
 * @param list  the list to use, must not be null
 * @return the set of the elements of the list
 */
public static Set elementSet(List list) {
    if (list.isEmpty()) {
        return new HashSet();
    }
    return DoubleOrderedMap.hashSetFor(list);
}'''

HOP2 = '''/**
 * Gets the set of the elements of a non-empty list, bringing the list
 * into step with that set.
 * <p>
 * A new <code>HashSet</code> is used for the set, and the list is handed
 * on as it is.
 *
 * @param list  the list to use, must not be empty or null
 * @return the set of the elements of the list
 */
public static Set hashSetFor(List list) {
    return ExtendedProperties.combineList(list, new HashSet());
}'''

HOP3 = '''/**
 * Brings a non-empty list into step with an empty set.
 * <p>
 * The list and the set are handed on as they are.
 *
 * @param list  the list to use, must not be empty or null
 * @param set  the set to add to, must be empty and not null
 * @return the set
 */
public static Set combineList(List list, Set set) {
    return MapUtils.putAllInto(list, set);
}'''

HOP4 = '''/**
 * Brings a non-empty list into step with an empty set, which receives
 * the elements of the list.
 * <p>
 * The list and the set are handed on as they are.
 *
 * @param list  the list to use, must not be empty or null
 * @param set  the set to add to, must be empty and not null
 * @return the set
 */
public static Set putAllInto(List list, Set set) {
    return CursorableLinkedList.refill(list, set);
}'''

DESIGN = {
 "instance": "Collections-5", "project": "Collections", "bug_id": 5, "seed": 8405,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SUL, "class": "org.apache.commons.collections.list.SetUniqueList", "method": "decorate", "near_line": 73},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/list/TestSetUniqueList.java",
             "test_class": "org.apache.commons.collections.list.TestSetUniqueList", "test_method": "testFactory"},
 "expected_signature": "Duplicate element was added. expected:<2> but was:<3>",
 "gold": {"method": "refill", "text": GOLD_TEXT,
          "fault": {"old": "            Object object = elements[i];\n"
                           "            if (set.contains(object)) {\n"
                           "                continue;\n"
                           "            }\n"
                           "            set.add(object);",
                    "new": "            Object object = elements[i];\n"
                           "            set.add(object);"}},
 "chain": {
   "facade_body": "if (list == null) {\n            throw new IllegalArgumentException(\"List must not be null\");\n        }\n"
                  "        return new SetUniqueList(list, org.apache.commons.collections.bidimap.TreeBidiMap.elementSet(list));",
   "lie": "The elements are taken out of the list and put back in a single pass that runs from the last element to the "
          "first, each element being inserted at the head of the list.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "elementSet",
      "imports": ["java.util.HashSet", "java.util.List", "org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "hashSetFor",
      "imports": ["java.util.HashSet", "java.util.List"], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "combineList",
      "imports": ["java.util.Set"], "text": HOP3},
     {"file": MAU, "class": "org.apache.commons.collections.MapUtils", "method": "putAllInto",
      "imports": ["java.util.List", "java.util.Set"], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableLinkedList", "method": "refill",
      "imports": ["java.util.Set"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.list.SetUniqueList::add",
              "org.apache.commons.collections.list.SetUniqueList::addAll",
              "org.apache.commons.collections.set.ListOrderedSet::add"],
 "ownership_reason": "Only the gold holds the snapshot of the caller's list while it refills that list in place, and only the gold "
                     "sees each element together with the state of the set at the moment the element is added. Hops 1-4 hand the "
                     "same list object down and get back the set; the facade keeps the original constructor call (the "
                     "SetUniqueList constructor is protected and no host is in the list package) and wraps the caller's list "
                     "with that set. Passing a de-duplicated copy down does not help (the copy is refilled, the caller's list "
                     "keeps its duplicates), no hop can build a SetUniqueList view, and SetUniqueList.decorate called from a hop "
                     "recurses into the chain. Each hop's javadoc says that it hands the list on as it is.The gold's javadoc promises to bring the list into step with the set; after the "
                     "variant the list [1, 2, 1] is not in step with the set {1, 2}. The convention is pinned outside the gold: "
                     "SetUniqueList.add(int, Object) appends an element only when 'set.contains(object) == false' and then adds "
                     "it to the set, and SetUniqueList.addAll(int, Collection) goes through it (TestSetUniqueList testAdd, "
                     "testAddAll, testIntCollectionAddAll pass); ListOrderedSet.add adds an element to its order list only on "
                     "the first add ('re-adding doesn't change order'; TestListOrderedSet testOrdering passes). The step that "
                     "adds an element to the set is the step that skips an element the set already holds; a de-duplication "
                     "added above the gold (CollectionUtils.filter with PredicateUtils.uniquePredicate) is a second "
                     "implementation of the gold's decision and leaves the gold violating its contract on any list that holds "
                     "an element twice.",
 "ownership_tests": ["org.apache.commons.collections.list.TestSetUniqueList::testAdd",
                     "org.apache.commons.collections.list.TestSetUniqueList::testAddAll",
                     "org.apache.commons.collections.list.TestSetUniqueList::testIntCollectionAddAll",
                     "org.apache.commons.collections.set.TestListOrderedSet::testOrdering"],
 "compensating": {
   "chain": [
     {"file": TBM, "old": "        if (list.isEmpty()) {\n            return new HashSet();",
      "new": "        if (list.size() < 2) {\n            return new HashSet(list);",
      "why": "hop 1 returns the set of the elements for a list of fewer than two elements, leaving the list as it is"},
     {"file": DOM, "old": "return ExtendedProperties.combineList(list, new HashSet());",
      "new": "return ExtendedProperties.combineList(list, new HashSet(list));",
      "why": "hop 2 seeds the set with the elements of the list"},
     {"file": MAU, "old": "return CursorableLinkedList.refill(list, set);",
      "new": "return CursorableLinkedList.refill(new java.util.ArrayList(list), set);",
      "why": "hop 4 hands the gold a copy of the list"},
   ],
 },
 "host_notes": "host_mode largest5 (4 other public classes of >= 1500 lines in the fixed revision). Hosts are the task record's "
               "hosts_hop_order, the five largest public non-interface non-enum classes other than SetUniqueList by newline "
               "count: bidimap.TreeBidiMap 2085 (hop 1), DoubleOrderedMap 1995 (hop 2), ExtendedProperties 1717 (hop 3), "
               "MapUtils 1645 (hop 4), CursorableLinkedList 1468 (hop 5, gold); smallest host 1468 lines. None substituted: all "
               "five are public top-level classes in which a static method compiles (DoubleOrderedMap is final and deprecated, "
               "CursorableLinkedList is deprecated and shares its file with the package-private CursorableSubList; neither "
               "affects a static method in the outer class). Anchors from stageB_lib.pick_insertion_anchor with the instance seed "
               "8405 (anchor seeds 8505-8509, via insert_hop): after TreeBidiMap.size, DoubleOrderedMap.clear, the "
               "ExtendedProperties() constructor, MapUtils.unmodifiableMap, CursorableLinkedList.iterator; all in the outer "
               "class. The facade calls hop 1 by its fully-qualified name inside the SetUniqueList constructor call it keeps "
               "(the constructor is protected); each hop imports java.util.List/Set/HashSet as needed and the next host "
               "(hops 2-5 share the org.apache.commons.collections package).",
}
