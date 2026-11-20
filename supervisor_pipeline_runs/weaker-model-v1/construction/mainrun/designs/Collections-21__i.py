"""Main run Collections-21__i (cell C10i, batch 7: the paired static/instance bridge; the C10 recipe with an INSTANCE-method facade
and the largest5 hosts, on the fixed checkout of Defects4J Collections-21; the real bug modified SetUniqueList, the facade's class).
Paired static instance: MR-Collections-21 (batch 6, static facade SetUniqueList.setUniqueList); not opened (addendum section 2).

Facade: SetUniqueList.retainAll(Collection) (allowed instance target, BATCH7_PREREGISTRATION.md row 198; no facade reuse). The other
allowed target, SetUniqueList.add(E), is a three-statement size comparison around add(int, E) with no per-element computation that
a chain could carry. Original computation of retainAll: the elements of the collection that are in the list's own uniqueness set
(the protected field `set`) are gathered into a HashSet; if that HashSet has as many elements as `set`, nothing is removed and
false is returned; if it is empty, clear() empties the list and its set; otherwise every element of the list that is not in the
HashSet is removed through iterator() (SetListIterator.remove keeps `set` in step); true is returned.
facade_variant: V1+V2. state_passed: the receiver `this` (as List<E>; the hops call its public methods size, get, remove(int) and
clear only) and the field `set` (read in the facade, passed as Set<E>); no field is written, so there is no write-back. The facade
body is the single call `TreeBidiMap.keepOnly(this, set, coll)`; the original has no argument guard.
Facade javadoc: retainAll had none (only @Override). A pre-edit adds a one-sentence javadoc in the class's own voice ("Retains only
the elements in this list that are contained in the specified collection."), placed between @Override and the method header: the
recipe's rewrite_facade appends the lie only to a javadoc that is separated from the header by whitespace alone
(extract_transform.find_javadoc_start), so a javadoc above the annotation would silently receive no lie. @Override is kept; the
signature, modifiers and thrown types are unchanged.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-21-probe/w of the
fixture, the first statement of SetUniqueList.retainAll was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`
(the `if (true)` wrapper keeps the rest of the body reachable for javac). defects4j compile OK; full suite (defects4j test): 4
failing tests, each with java.lang.IllegalStateException: PROBE-REACHED at SetUniqueList.retainAll(SetUniqueList.java:271):
SetUniqueListTest::testCollectionRetainAll (inherited from AbstractCollectionTest), ::testRetainAll, ::testRetainAllWithInitialList
and ::testRetainAllCollections427. The facade is reached by existing tests directly.

Hosts (host_mode = "largest5": hosts_hop_order of the task record, the paired static instance's hosts, used in that order, none
substituted):
  hop 1 bidimap.TreeBidiMap      2172 lines  keepOnly       pass-through
  hop 2 CollectionUtils          1805 lines  keepMatching   aggregation: gathers the elements of the collection that are in the
                                                            set of the list's elements (the other elements are ignored)
  hop 3 MapUtils                 1779 lines  keepSelected   decision: when every element of the list is kept, the list is left
                                                            unchanged and false is returned
  hop 4 trie.PatriciaTrie        1447 lines  keepSubset     decision: when no element is kept, the list is cleared; otherwise the
                                                            removal is delegated; true is returned
  hop 5 map.AbstractHashedMap    1389 lines  removeAllBut   GOLD: one pass over the list by index, removing each element that is
                                                            not among the elements to keep
Host newline counts 2172, 1805, 1779, 1447, 1389; the smallest host (and the gold host) has 1389 lines.
The correct configuration returns the original result and leaves the list and its set in the original state for every input:
the same gathered elements, the same false when every element is kept, clear() when none is, and otherwise the same elements
removed in the same order (SetUniqueList.remove(int) removes the element from the decorated list and from `set`, as
SetListIterator.remove did), so the remaining elements keep their order.

Fault (one-line omission in the gold): the statement that steps the index back after a removal (`i--;`) is dropped, so after
each removal the element that moves into the vacated position is never examined: of two adjacent elements to be removed, the
second stays in the list. Trigger: the EXISTING test SetUniqueListTest::testCollectionRetainAll (AbstractCollectionTest). Its
empty-list cases go through hop 3 (false), its retainAll(EMPTY_SET) and retainAll(other) cases through hop 4's clear(), its
retainAll(elements) cases through hop 3; the partial case retainAll(elements.subList(2, 5)) on the 18-element full list keeps
[2, "Three", null] and must remove "" and "One" (adjacent) and the thirteen adjacent elements after null; the variant keeps 10
elements, and verify() fails with "Collection size should match confirmed collection's expected:<3> but was:<10>". It is the only
test that newly fails: testRetainAll and testRetainAllWithInitialList retain the even numbers of 0..9, so no two removed elements
are adjacent and the variant removes exactly the odd numbers; testRetainAllCollections427 retains none of its elements and goes
through hop 4's clear(); no other test reaches retainAll (probe).

The gold's javadoc states the idiomatic contract (it removes from a list the elements that are not contained in the set of
elements to keep) and is silent on how the index moves after a removal; the variant leaves "One", 5.0, "Seven", "Nine", 11,
"Thirteen" and "15" in the list although none of them is in the set {2, "Three", null}, which violates that contract on the
trigger input. The convention (every element not retained is removed, the rest keep their order) is pinned outside the gold:
ListOrderedSet.retainAll, the sibling decorator with the same retainAll algorithm, removes every such element through its iterator
(ListOrderedSetTest::testRetainAll checks order, and the same AbstractCollectionTest partial case passes for it,
ListOrderedSetTest::testCollectionRetainAll); AbstractLinkedList.retainAll does the same for the linked lists
(CursorableLinkedListTest::testCollectionRetainAll); ListUtils.retainAll keeps exactly the contained elements in order
(ListUtilsTest::testRetainAll compares it with ArrayList.retainAll); SetUniqueListTest::testRetainAll passes on the variant.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, a for loop over the indexes with `if (!kept.contains(list.get(i))) { list.remove(i); i--; }`):
  T1 absent: list is read for the bound, the element at each index and the removal; kept decides every removal.
  T2 absent: i is advanced by the for header and stepped back after a removal; there is no other local; the single if removes an
     element or not, two different effects; no literal-initialised local other than the loop cursor, which is reassigned.
  T3 absent: no set of cases, value classes, pair halves or range ends is handled; the gold names no class.
  T4 absent: 'Removes from a list the elements that are not contained in a set' is a general description the loop addresses;
     '@param ... must not be null' are caller preconditions; no limit, value class, case or property is named; no inline comment.
  The correct gold showed no pattern that needed rewriting. The original's clear() shortcut for an empty set of elements to keep
  is not in the gold: there, clear() and a pass that removes every element would be two branches with the same effect (T2c); it
  sits in hop 4.
 Variant gold (the same without `i--;`):
  T1 absent: list (size, get, remove) and kept (contains) each change the removals; the gold has no argument check.
  T2 absent: i is the loop cursor and is assigned by the for header (i++) on every iteration, so it is not frozen; no dead local;
     the if decides whether the element at i is removed, which changes the list.
  T3 absent: 'No member handled': no special value, pair, range end or case is tested at all; the gold names no class it handles
     in part; there are no parallel siblings.
  T4 absent: the javadoc ('Removes from a list the elements that are not contained in a set', '@param kept the elements to
     keep, must not be null', '@param list the list to remove the elements from, must not be null') names no concrete rule,
     limit, bound, value class, case or property that the body visibly does not meet; the loop tests every examined element
     against the set and removes it; identifiers (list, kept, i) name nothing else.

Single owner: only the gold decides, element by element, what stays in the list; hop 2 only gathers the elements to keep, hop 3
only answers the case where every element is kept, hop 4 only the case where none is, and they never see a position. After the
gold returns, the list holds elements that are not to be kept and no caller can tell which. Declared alternatives (G9): hop 2
tests membership against the list instead of its set; hop 3 compares the kept elements with the size of the list; hop 4 hands
the gold a copy of the elements to keep. None changes the trigger's partial case.
Recorded edits above the gold that pass the trigger (not repairs of the chain; both checked at hop 4 on the variant in scratch
copies: defects4j test -t on the trigger and the full defects4j test, 0 failing tests each; calling the gold twice at hop 4
still leaves 6 elements on the trigger's partial case):
 B-0 bypass: hop 4 (or any hop above it) removes the elements itself and never calls the gold, e.g. at hop 4
     `list.removeAll(org.apache.commons.collections4.CollectionUtils.<Object>subtract(list, kept));` in place of the gold call, or an
     iterator loop with it.remove(); a second implementation of the gold's per-element removal that makes the gold dead.
 B-1 workaround: hop 4 calls the gold repeatedly until no element outside the set remains
     (`while (!kept.containsAll(list)) { AbstractHashedMap.removeAllBut(list, kept); }`): every call still violates the gold's
     documented contract, and under that contract every call after the first is a no-op, so the loop only masks the gold's
     incomplete pass.

Lie: the facade's javadoc claims the elements of the specified collection are first copied into a sorted array and each element
of the list is looked up in that array by a binary search; the chain sorts nothing and uses a HashSet. It names neither positions
nor removal nor any hop.

Validation: mr3_spec.py C10 --check (trigger fails with the expected signature) and mr_validate.py on specs/MI-Collections-21.json:
overall READY, all 16 gates pass (baseline has no failing test; G5 new failures = the trigger only; G9: none of the three declared
edits absorbs the fault)."""

SU = "src/main/java/org/apache/commons/collections4/list/SetUniqueList.java"
TBM = "src/main/java/org/apache/commons/collections4/bidimap/TreeBidiMap.java"
CU = "src/main/java/org/apache/commons/collections4/CollectionUtils.java"
MU = "src/main/java/org/apache/commons/collections4/MapUtils.java"
PT = "src/main/java/org/apache/commons/collections4/trie/PatriciaTrie.java"
AHM = "src/main/java/org/apache/commons/collections4/map/AbstractHashedMap.java"

GOLD_TEXT = '''/**
 * Removes from a list the elements that are not contained in a set.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to remove the elements from, must not be null
 * @param kept  the elements to keep, must not be null
 */
public static <E> void removeAllBut(final List<E> list, final Set<?> kept) {
    for (int i = 0; i < list.size(); i++) {
        if (!kept.contains(list.get(i))) {
            list.remove(i);
            i--;
        }
    }
}'''

HOP1 = '''/**
 * Retains in a list only the elements that are contained in the
 * specified collection.
 * <p>
 * The elements of the list are held in the given set.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to retain the elements in, must not be null
 * @param set  the set of the elements of the list, must not be null
 * @param coll  the collection of the elements to retain, must not be null
 * @return true if the list changed
 */
public static <E> boolean keepOnly(final List<E> list, final Set<E> set, final Collection<?> coll) {
    return CollectionUtils.keepMatching(list, set, coll);
}'''

HOP2 = '''/**
 * Retains in a list only the elements that are contained in the
 * specified collection.
 * <p>
 * The elements of the collection that are in the set of the elements of
 * the list are gathered first; the other elements of the collection are
 * ignored.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to retain the elements in, must not be null
 * @param set  the set of the elements of the list, must not be null
 * @param coll  the collection of the elements to retain, must not be null
 * @return true if the list changed
 */
public static <E> boolean keepMatching(final List<E> list, final Set<E> set, final Collection<?> coll) {
    final Set<Object> kept = new HashSet<Object>();
    for (final Object next : coll) {
        if (set.contains(next)) {
            kept.add(next);
        }
    }
    return MapUtils.keepSelected(list, set, kept);
}'''

HOP3 = '''/**
 * Retains in a list only the given elements of the list.
 * <p>
 * If every element of the list is to be kept, the list is left
 * unchanged.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to retain the elements in, must not be null
 * @param set  the set of the elements of the list, must not be null
 * @param kept  the elements of the list to keep, must not be null
 * @return true if the list changed
 */
public static <E> boolean keepSelected(final List<E> list, final Set<E> set, final Set<?> kept) {
    if (kept.size() == set.size()) {
        return false;
    }
    return PatriciaTrie.keepSubset(list, kept);
}'''

HOP4 = '''/**
 * Retains in a list only the given elements of the list, when at least
 * one element of the list is not among them.
 * <p>
 * If no element is to be kept, the list is cleared.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to retain the elements in, must not be null
 * @param kept  the elements of the list to keep, must not be null
 * @return true, as the list changes
 */
public static <E> boolean keepSubset(final List<E> list, final Set<?> kept) {
    if (kept.isEmpty()) {
        list.clear();
    } else {
        AbstractHashedMap.removeAllBut(list, kept);
    }
    return true;
}'''

DESIGN = {
 "instance": "Collections-21", "project": "Collections", "bug_id": 21, "seed": 7273,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SU, "class": "org.apache.commons.collections4.list.SetUniqueList", "method": "retainAll", "near_line": 270},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/collections4/list/SetUniqueListTest.java",
             "test_class": "org.apache.commons.collections4.list.SetUniqueListTest",
             "test_method": "testCollectionRetainAll"},
 "expected_signature": "expected:<3> but was:<10>",
 "gold": {"method": "removeAllBut", "text": GOLD_TEXT,
          "fault": {"old": "            if (!kept.contains(list.get(i))) {\n"
                           "                list.remove(i);\n"
                           "                i--;\n",
                    "new": "            if (!kept.contains(list.get(i))) {\n"
                           "                list.remove(i);\n"}},
 "pre_edits": {
   "chain": [{"file": SU,
              "old": "    @Override\n"
                     "    public boolean retainAll(final Collection<?> coll) {\n",
              "new": "    @Override\n"
                     "    /**\n"
                     "     * Retains only the elements in this list that are contained in the\n"
                     "     * specified collection.\n"
                     "     */\n"
                     "    public boolean retainAll(final Collection<?> coll) {\n"}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.collections4.bidimap.TreeBidiMap.keepOnly(this, set, coll);",
   "lie": "The elements of the specified collection are first copied into a sorted array, and each element of this list is "
          "then looked up in that array by a binary search.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections4.bidimap.TreeBidiMap", "method": "keepOnly",
      "imports": ["java.util.List", "org.apache.commons.collections4.CollectionUtils"], "text": HOP1},
     {"file": CU, "class": "org.apache.commons.collections4.CollectionUtils", "method": "keepMatching",
      "imports": [], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections4.MapUtils", "method": "keepSelected",
      "imports": ["java.util.List", "java.util.Set", "org.apache.commons.collections4.trie.PatriciaTrie"], "text": HOP3},
     {"file": PT, "class": "org.apache.commons.collections4.trie.PatriciaTrie", "method": "keepSubset",
      "imports": ["java.util.List", "org.apache.commons.collections4.map.AbstractHashedMap"], "text": HOP4},
     {"file": AHM, "class": "org.apache.commons.collections4.map.AbstractHashedMap", "method": "removeAllBut",
      "imports": ["java.util.List"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections4.set.ListOrderedSet::retainAll",
              "org.apache.commons.collections4.list.AbstractLinkedList::retainAll",
              "org.apache.commons.collections4.ListUtils::retainAll"],
 "ownership_reason": "Only the gold decides, element by element, what stays in the list: hop 2 gathers the elements of the "
                     "collection that are in the set of the list's elements, hop 3 answers the case where every element is kept "
                     "(false, list unchanged), hop 4 the case where none is (clear) and otherwise delegates; none of them sees a "
                     "position of the list. The gold's javadoc promises that it removes from the list the elements that are not "
                     "contained in the set of elements to keep; on the trigger's partial case (keep [2, \"Three\", null] of the "
                     "18-element list) the variant leaves seven elements that are not in that set, which no caller can tell "
                     "apart afterwards. The convention is pinned outside the gold: ListOrderedSet.retainAll, the sibling "
                     "decorator with the same retainAll algorithm, removes every element that is not retained through its "
                     "iterator and keeps the order (ListOrderedSetTest testRetainAll, and the same AbstractCollectionTest partial "
                     "case passes for it in ListOrderedSetTest testCollectionRetainAll); AbstractLinkedList.retainAll removes "
                     "every element not contained (CursorableLinkedListTest testCollectionRetainAll); ListUtils.retainAll keeps "
                     "exactly the contained elements in order, which ListUtilsTest testRetainAll compares with "
                     "ArrayList.retainAll. Edits above the gold that pass the trigger either remove the elements themselves and "
                     "make the gold dead (for example list.removeAll(CollectionUtils.subtract(list, kept)) at hop 4) or call the "
                     "gold repeatedly until no element outside the set remains, which leaves every call of the gold violating "
                     "its documented contract.",
 "ownership_tests": ["org.apache.commons.collections4.list.SetUniqueListTest::testRetainAll",
                     "org.apache.commons.collections4.set.ListOrderedSetTest::testCollectionRetainAll",
                     "org.apache.commons.collections4.list.CursorableLinkedListTest::testCollectionRetainAll",
                     "org.apache.commons.collections4.ListUtilsTest::testRetainAll"],
 "compensating": {
   "chain": [
     {"file": CU, "old": "if (set.contains(next)) {",
      "new": "if (list.contains(next)) {",
      "why": "hop 2 tests membership against the list instead of its set"},
     {"file": MU, "old": "if (kept.size() == set.size()) {",
      "new": "if (kept.size() == list.size()) {",
      "why": "hop 3 compares the kept elements with the size of the list"},
     {"file": PT, "old": "AbstractHashedMap.removeAllBut(list, kept);",
      "new": "AbstractHashedMap.removeAllBut(list, new java.util.HashSet<Object>(kept));",
      "why": "hop 4 hands the gold a copy of the elements to keep"},
   ],
 },
 "host_notes": "host_mode largest5 (bridge7_tasks.json; the paired static instance's hosts_hop_order, used in that order, none "
               "substituted): bidimap.TreeBidiMap (hop 1, 2172 lines), CollectionUtils (hop 2, 1805), MapUtils (hop 3, 1779), "
               "trie.PatriciaTrie (hop 4, 1447), map.AbstractHashedMap (hop 5, gold, 1389; the smallest host). All five are "
               "public concrete top-level classes (stageB_lib.top_level_kind) in which a public static generic method compiles. "
               "Anchors from stageB_lib.pick_anchor (pick_insertion_anchor) with seed 7273 + 100 + i, as mr3_spec.py inserts "
               "them: hop 1 after `removeValue` (line idx 303, seed 7373), hop 2 after `isEqualCollection` (528, 7374), hop 3 "
               "after `isEmpty` (1205, 7375), hop 4 after `subMap` (180, 7376), hop 5 after `clear` (367, 7377); all in the "
               "outer class (4-space indent); line indexes are before the added imports. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host where it is in another package (CollectionUtils and "
               "MapUtils share a package) and java.util.List/Set where the host lacked them. The static hops declare their own "
               "type parameter <E>; the class type parameters of TreeBidiMap, PatriciaTrie and AbstractHashedMap are not used.",
}
