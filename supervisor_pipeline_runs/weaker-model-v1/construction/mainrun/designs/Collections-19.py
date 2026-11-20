"""Main run Collections-19 (cell C10f, batch 6: the C10 recipe with fallback hosts, on the fixed checkout of Defects4J Collections-19;
the real bug modified SetUniqueList, the target class).

Facade: SetUniqueList.setUniqueList(List) (the only allowed target, BATCH6_PREREGISTRATION.md row 152; no facade reuse).
Original computation: a null list throws IllegalArgumentException("List must not be null"); an empty list is wrapped with a new
HashSet; otherwise the list is copied, cleared, wrapped with a new HashSet, and the copy is added back through SetUniqueList.addAll,
which appends an element only when the set did not hold it yet (duplicates removed, first indexed one kept). The result wraps the
supplied list itself.

reachability_probe: in a scratch copy of the fixture (/private/tmp/c19probe/w) the facade's first statement was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (a bare throw would make the rest of the body unreachable and
not compile); defects4j compile OK; full suite (defects4j test, 14 s): 7 failing tests, all with PROBE-REACHED:
SetUniqueListTest::testFactory, ::testRetainAllWithInitialList, ::testUniqueListReInsert, ::testUniqueListDoubleInsert,
::testCollections304, ::testCollections307, ::testRetainAll. The facade is reached by existing tests (usable). Only testFactory
([1, 2, 1] with duplicates) and testRetainAllWithInitialList ([0..4], no duplicates) pass a non-empty list; the other five pass an
empty one. No production code calls the facade.

Host regime (BUILD_BRIEF_C10F_ADDENDUM section 1): host_mode = largest5 (3 other public classes reach 1500 lines). Hosts are the
five largest public non-interface non-enum classes other than SetUniqueList, in that order (batch6_tasks.json hosts_hop_order),
anchors from stageB_lib.pick_insertion_anchor with the instance seed 6698 (seed + 100 + i), all at brace depth 1:
  hop 1 bidimap.TreeBidiMap        2138 lines, anchor after mapIterator    (seed 6798)
  hop 2 ExtendedProperties         1761 lines, anchor after isInitialized  (seed 6799)
  hop 3 MapUtils                   1744 lines, anchor after getString      (seed 6800)
  hop 4 CollectionUtils            1486 lines, anchor after disjunction    (seed 6801)
  hop 5 trie.PatriciaTrie          1447 lines, anchor after getPrefixedBy  (seed 6802)  <- GOLD
Smallest host: 1447 lines (PatriciaTrie, the gold host). None substituted.

Chain:
  facade  keeps its argument guard; its body is that guard and one return statement whose only call into the code base is hop 1:
          `return new SetUniqueList<E>(list, TreeBidiMap.populateSet(list, new HashSet<E>()));`. The facade keeps the
          construction because SetUniqueList(List, Set) is protected and no host is in the list package or a subclass, and it keeps
          the HashSet that its own javadoc names ('A HashSet is used for the set behaviour'); hops 1-4 and the gold take any Set,
          as the protected constructor does.
  hop 1 TreeBidiMap.populateSet       decision: an empty list has nothing to move, the set is returned as given
  hop 2 ExtendedProperties.loadElements  placement: moves the elements of the list into a new list and clears the list
  hop 3 MapUtils.populateFrom         pass-through
  hop 4 CollectionUtils.addAllElements   fold: fills through the gold and returns the set
  hop 5 PatriciaTrie.fillFrom         GOLD: the per-element core, an element is added to the set and appended to the list unless
                                      the set already contains it
The correct configuration gives the original result for every input (same guard, same HashSet, the wrapped list is the supplied
list, refilled in iteration order with the elements the set did not hold yet; the set holds the same elements).

Fault (one-line omission of a decision in the gold): the `if (set.contains(e)) { continue; }` step is dropped, so every element
is added to the set and appended to the list. Trigger: the EXISTING test SetUniqueListTest::testFactory; for [1, 2, 1] (three
Integer objects) the list keeps both 1s while the set holds {1, 2}: assertEquals("Duplicate element was added.", 2, lset.size())
fails with expected:<2> but was:<3>. testRetainAllWithInitialList passes a list without duplicates and still passes; the other
callers pass an empty list, which hop 1 returns before the gold.

The gold's javadoc states the idiomatic contract (an empty list and an empty set are initialised to the same elements, taken in
iteration order; the wording of the SetUniqueList(List, Set) constructor, 'The set and list must both be correctly initialised to
the same elements') and is silent on the membership step. On the trigger input the list holds [1, 2, 1] and the set {1, 2}, which
are not the same elements in the sense of that constructor and of the facade ('If the list contains duplicates, these are
removed').

External pins: the facade's javadoc (duplicates removed, first indexed one kept); SetUniqueList.addAll(int, Collection) takes the
same step (`if (set.add(e)) temp.add(e)`), pinned by SetUniqueListTest::testAddAll and ::testIntCollectionAddAll ('Duplicate
element should not be added'); ListOrderedSet.addAll(int, Collection) takes it with the same idiom (`if (contains(e)) continue;
collection.add(e); toAdd.add(e);`), pinned by ListOrderedSetTest::testListAddIndexed; SetUniqueList.add(int, E) adds only when
`set.contains(object) == false`. The step is decided by the set itself (SetUniqueList307 in SetUniqueListTest wraps a TreeSet,
testCollections307), which is why hops 1-4 and the gold take any Set.

Single owner: only the gold holds each element together with the set's answer for it; hops 1 and 2 hold the whole list, hop 3 and
4 the moved elements, and none of them consults the set per element. Declared alternatives (G9): hop 1 also returns early when the
set already holds every element of the list; hop 3 hands on only the elements the set does not hold yet (CollectionUtils.subtract);
hop 4 drops from the list every element the set does not hold (retainAll); hop 4 returns a set rebuilt from the filled list. Each
leaves the list at [1, 2, 1].
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each):
 B-0 bypass: hop 4 replaces the gold call by an inline fill on one line,
     `for (final E e : elements) { if (set.add(e)) { list.add(e); } }`, re-implementing the gold and making it dead (the facade's
     original body, with SetUniqueList.addAll, is the same bypass one level up).
 B-1 equality pre-filter, not consistent with the set the chain carries: hop 1 inserts
     `CollectionUtils.filter(list, PredicateUtils.<E>uniquePredicate());`, or hop 2 copies through `new LinkedHashSet<E>(list)`,
     or hop 3 / hop 4 pass `new LinkedHashSet<E>(elements)`. These drop duplicates by equals/hashCode before the gold, whatever
     the set; hops 1-4 are documented to fill the set they are given, and for a set with its own membership rule the pair is then
     not initialised to the same elements: with a TreeSet ordered by String.CASE_INSENSITIVE_ORDER and the list ["a", "A"] the
     list keeps both while the set holds one (SetUniqueList.addAll and ListOrderedSet.addAll keep only "a"), so the gold's
     documented contract stays violated on inputs inside every hop's documented domain. Hop 2's version also breaks its
     documented move of the list's elements.
 B-2 test-fitted, set order: hop 4 `list.clear(); list.addAll(set);` after the gold call, or hop 2 `new ArrayList<E>(new
     HashSet<E>(list))`: passes only because a HashSet of small Integers iterates in ascending order; for ["b", "a", "b"] the list
     becomes [a, b] instead of [b, a], which breaks the facade's retained order (first indexed one kept).

Lie: the facade's javadoc claims the list is copied into an array and cleared and is then refilled by walking that array from its
last element to its first, inserting each element at the head of the list; the chain copies into an ArrayList and appends in
iteration order. It names neither the membership step nor duplicates nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, `for (final E e : elements) { if (set.contains(e)) { continue; } set.add(e); list.add(e); }`):
  T1 absent: elements is iterated, list is appended to, set is queried and added to; each changes the side effects.
  T2 absent: the only local is the loop element e, read in every statement; the if decides whether the two adds run.
  T3 absent: no closed set (no pair, no range ends, no enum or type code, no named value class); one membership test only.
  T4 absent: the javadoc names the same elements and the iteration order, which the loop produces; 'empty, not null' are caller
     preconditions. Nothing needed rewriting.
 Variant gold (javadoc, signature, `for (final E e : elements) { set.add(e); list.add(e); }`):
  T1 absent: elements is read by the for-each, list and set are written by add on every iteration; each parameter's value changes
     the side effects; there is no argument check.
  T2 absent: e is assigned by the for header and read by both adds; no literal-initialised local, no cursor, counter, flag or
     best-so-far; no branch, case or ternary remains.
  T3 absent: no element-level treatment remains, so no member of any set is handled while a sibling is not ('No member handled');
     no pair halves or range ends; the text names no class it handles in part.
  T4 absent: 'Initialises an empty list and an empty set to the same elements, taken from the given elements in iteration order'
     is a general description the loop addresses (every element goes to both, in iteration order); '@param ... empty, not null'
     are caller preconditions; no limit, value class, case or property is named that the body does not produce; no comment; the
     identifiers (elements, list, set, e, fillFrom) name nothing the body does not meet."""

SUL = "src/main/java/org/apache/commons/collections/list/SetUniqueList.java"
TBM = "src/main/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
EXP = "src/main/java/org/apache/commons/collections/ExtendedProperties.java"
MU = "src/main/java/org/apache/commons/collections/MapUtils.java"
CU = "src/main/java/org/apache/commons/collections/CollectionUtils.java"
PT = "src/main/java/org/apache/commons/collections/trie/PatriciaTrie.java"

GOLD_TEXT = '''/**
 * Initialises an empty list and an empty set to the same elements, taken
 * from the given elements in iteration order.
 *
 * @param <E>  the type of the elements
 * @param elements  the elements to take, not null
 * @param list  the list to initialise, empty, not null
 * @param set  the set to initialise, empty, not null
 */
public static <E> void fillFrom(final Collection<? extends E> elements, final List<E> list, final Set<E> set) {
    for (final E e : elements) {
        if (set.contains(e)) {
            continue;
        }
        set.add(e);
        list.add(e);
    }
}'''

HOP1 = '''/**
 * Fills a set and the list it belongs to from the elements of the list.
 * <p>
 * An empty list has no elements to move, and the set is returned as it
 * was given.
 *
 * @param <E>  the type of the elements
 * @param list  the list, not null
 * @param set  the set to fill, empty, not null
 * @return the set
 */
public static <E> Set<E> populateSet(final List<E> list, final Set<E> set) {
    if (list.isEmpty()) {
        return set;
    }
    return ExtendedProperties.loadElements(list, set);
}'''

HOP2 = '''/**
 * Moves the elements of a non-empty list into a new list, leaving the
 * list empty, and fills the list and a set again from the new list.
 *
 * @param <E>  the type of the elements
 * @param list  the list, not null or empty
 * @param set  the set to fill, empty, not null
 * @return the set
 */
public static <E> Set<E> loadElements(final List<E> list, final Set<E> set) {
    final List<E> elements = new ArrayList<E>(list);
    list.clear();
    return MapUtils.populateFrom(elements, list, set);
}'''

HOP3 = '''/**
 * Fills an empty list and an empty set from the given elements.
 *
 * @param <E>  the type of the elements
 * @param elements  the elements to fill from, not null
 * @param list  the list to fill, empty, not null
 * @param set  the set to fill, empty, not null
 * @return the set
 */
public static <E> Set<E> populateFrom(final Collection<? extends E> elements, final List<E> list, final Set<E> set) {
    return CollectionUtils.addAllElements(elements, list, set);
}'''

HOP4 = '''/**
 * Adds the given elements to an empty list and an empty set, and returns
 * the set.
 *
 * @param <E>  the type of the elements
 * @param elements  the elements to add, must not be null
 * @param list  the list to add to, empty, must not be null
 * @param set  the set to add to, empty, must not be null
 * @return the set
 */
public static <E> Set<E> addAllElements(final Collection<? extends E> elements, final List<E> list, final Set<E> set) {
    PatriciaTrie.fillFrom(elements, list, set);
    return set;
}'''

DESIGN = {
 "instance": "Collections-19", "project": "Collections", "bug_id": 19, "seed": 6698,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "host_mode": "largest5", "host_lines": [2138, 1761, 1744, 1486, 1447], "smallest_host_lines": 1447,
 "reachability_probe": "facade first statement `if (true) { throw new IllegalStateException(\"PROBE-REACHED\"); }` in a scratch "
                       "copy; defects4j test (full suite): 7 failing, all PROBE-REACHED: SetUniqueListTest::testFactory, "
                       "testRetainAllWithInitialList, testUniqueListReInsert, testUniqueListDoubleInsert, testCollections304, "
                       "testCollections307, testRetainAll -> reached (usable)",
 "facade": {"file": SUL, "class": "org.apache.commons.collections.list.SetUniqueList", "method": "setUniqueList", "near_line": 73},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/collections/list/SetUniqueListTest.java",
             "test_class": "org.apache.commons.collections.list.SetUniqueListTest", "test_method": "testFactory"},
 "expected_signature": "Duplicate element was added. expected:<2> but was:<3>",
 "gold": {"method": "fillFrom", "text": GOLD_TEXT,
          "fault": {"old": "        for (final E e : elements) {\n"
                           "            if (set.contains(e)) {\n"
                           "                continue;\n"
                           "            }\n"
                           "            set.add(e);",
                    "new": "        for (final E e : elements) {\n"
                           "            set.add(e);"}},
 "chain": {
   "facade_body": "if (list == null) {\n            throw new IllegalArgumentException(\"List must not be null\");\n        }\n"
                  "        return new SetUniqueList<E>(list, org.apache.commons.collections.bidimap.TreeBidiMap.populateSet(list, new HashSet<E>()));",
   "lie": "The list is first copied into an array and cleared, and is then refilled by walking that array from its last "
          "element to its first, inserting each element at the head of the list.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "populateSet",
      "imports": ["java.util.List", "org.apache.commons.collections.ExtendedProperties"], "text": HOP1},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "loadElements",
      "imports": ["java.util.Set"], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "populateFrom",
      "imports": ["java.util.List", "java.util.Set"], "text": HOP3},
     {"file": CU, "class": "org.apache.commons.collections.CollectionUtils", "method": "addAllElements",
      "imports": ["org.apache.commons.collections.trie.PatriciaTrie"], "text": HOP4},
     {"file": PT, "class": "org.apache.commons.collections.trie.PatriciaTrie", "method": "fillFrom",
      "imports": ["java.util.Collection", "java.util.List"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.list.SetUniqueList::addAll",
              "org.apache.commons.collections.set.ListOrderedSet::addAll",
              "org.apache.commons.collections.list.SetUniqueList::add"],
 "ownership_reason": "Only the gold holds each element together with the answer of the set for it: hops 1 and 2 hold the whole "
                     "list, hops 3 and 4 the moved elements, and none of them consults the set per element. The convention is "
                     "pinned outside the gold: the facade's javadoc ('If the list contains duplicates, these are removed (first "
                     "indexed one kept)'); the SetUniqueList(List, Set) constructor ('The set and list must both be correctly "
                     "initialised to the same elements'); SetUniqueList.addAll(int, Collection) takes the same step "
                     "(`if (set.add(e)) temp.add(e)`; SetUniqueListTest testAddAll and testIntCollectionAddAll: 'Duplicate "
                     "element should not be added'); ListOrderedSet.addAll(int, Collection) takes it with the same idiom "
                     "(`if (contains(e)) continue; collection.add(e); toAdd.add(e);`; ListOrderedSetTest testListAddIndexed); "
                     "SetUniqueList.add(int, E) adds only when `set.contains(object) == false`. The step is decided by the set "
                     "itself (SetUniqueList307 in SetUniqueListTest wraps a TreeSet; createSetBasedOnList keeps the set's "
                     "class), so hops 1-4 and the gold take any Set. A one-line equality pre-filter above the gold "
                     "(CollectionUtils.filter(list, PredicateUtils.uniquePredicate()) at hop 1, a LinkedHashSet copy at hops "
                     "2-4) passes the existing tests with the facade's HashSet but decides by equals/hashCode instead of by the "
                     "set the hops are documented to fill: for a TreeSet ordered by String.CASE_INSENSITIVE_ORDER and the list "
                     "[\"a\", \"A\"] the list keeps both while the set holds one, so the gold's documented contract (list and set "
                     "initialised to the same elements) stays violated inside every hop's documented domain; at hop 2 it also "
                     "breaks the documented move of the list's elements. Rebuilding the list from the set after the gold "
                     "(list.clear(); list.addAll(set)) passes only because a HashSet of small Integers iterates in ascending "
                     "order, and loses the first-indexed order for other elements.",
 "ownership_tests": ["org.apache.commons.collections.list.SetUniqueListTest::testAddAll",
                     "org.apache.commons.collections.list.SetUniqueListTest::testIntCollectionAddAll",
                     "org.apache.commons.collections.set.ListOrderedSetTest::testListAddIndexed",
                     "org.apache.commons.collections.list.SetUniqueListTest::testCollections307",
                     "org.apache.commons.collections.list.SetUniqueListTest::testRetainAllWithInitialList"],
 "compensating": {
   "chain": [
     {"file": TBM, "old": "        if (list.isEmpty()) {\n            return set;",
      "new": "        if (list.isEmpty() || set.containsAll(list)) {\n            return set;",
      "why": "hop 1 also leaves the pair as it is when the set already holds every element of the list"},
     {"file": MU, "old": "return CollectionUtils.addAllElements(elements, list, set);",
      "new": "return CollectionUtils.addAllElements(CollectionUtils.subtract(elements, set), list, set);",
      "why": "hop 3 hands on only the elements the set does not already hold"},
     {"file": CU, "old": "        PatriciaTrie.fillFrom(elements, list, set);\n        return set;",
      "new": "        PatriciaTrie.fillFrom(elements, list, set);\n        list.retainAll(set);\n        return set;",
      "why": "hop 4 drops from the list every element the set does not hold"},
     {"file": CU, "old": "        PatriciaTrie.fillFrom(elements, list, set);\n        return set;",
      "new": "        PatriciaTrie.fillFrom(elements, list, set);\n        return new HashSet<E>(list);",
      "why": "hop 4 returns a set rebuilt from the filled list"},
   ],
 },
 "host_notes": "host_mode largest5 (3 other public classes of >= 1500 lines; BUILD_BRIEF_C10F_ADDENDUM section 1): the hosts are "
               "the five largest public non-interface non-enum classes other than SetUniqueList, in batch6_tasks.json "
               "hosts_hop_order: bidimap.TreeBidiMap 2138 lines (hop 1, anchor after mapIterator, seed 6798), "
               "ExtendedProperties 1761 (hop 2, after isInitialized, 6799), MapUtils 1744 (hop 3, after getString, 6800), "
               "CollectionUtils 1486 (hop 4, after disjunction, 6801), trie.PatriciaTrie 1447 (hop 5, gold, after "
               "getPrefixedBy, 6802); anchors from stageB_lib.pick_insertion_anchor with the instance seed 6698 (seed + 100 + "
               "i), all in the outer class (brace depth 1). Smallest host 1447 lines. All five are public concrete classes in "
               "which a static generic method compiles (TreeBidiMap and PatriciaTrie are generic, ExtendedProperties extends "
               "Hashtable; none of this affects a static method); none was substituted. The facade keeps the construction of "
               "its result, because SetUniqueList(List, Set) is protected and no host is in the list package or a subclass; "
               "it calls hop 1 by its fully-qualified name, and each hop imports what it needs (ExtendedProperties, MapUtils "
               "and CollectionUtils share the package org.apache.commons.collections).",
}
