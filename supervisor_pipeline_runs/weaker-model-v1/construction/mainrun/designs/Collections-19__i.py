"""Main run Collections-19__i (cell C10i, batch 7: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Collections-19; the real bug modified SetUniqueList, the facade's class). Paired static instance: MR-Collections-19 (batch 6, static
facade SetUniqueList.setUniqueList); its design, spec, patches and audit were not opened.

Facade: SetUniqueList.retainAll(Collection) (allowed target, BATCH7_PREREGISTRATION.md row 197; no facade reuse). The other allowed
target, add(E), is called by SetUniqueListTest.verify() after nearly every test step, so no omission under it could have a single
trigger. Original computation of retainAll: the elements of the collection that the internal set holds are gathered into a HashSet;
if that set is as large as the internal set the list is left unchanged and false is returned; if it is empty the list is cleared;
otherwise the list is walked with its iterator (SetListIterator, which also removes from the internal set) and every element not in
the gathered set is removed; true is returned.

facade_variant: V1+V2. state_passed: the receiver `this` (as List<E>; hops call only its public List methods size, get, remove(int)
and clear) and the protected field `set` (as Set<E>; read by the facade, which is inside the class, and passed down; hops call its
contains and size), together with the parameter coll. No write-back (the method assigns no field). The field is passed rather than
replaced by this.contains / this.size() so that the chain returns the original result even when the list and its set disagree
(for example after a removal through a sub-list view). Facade body: one call to hop 1, no guard (the original has none; a null
collection still throws NullPointerException, now at hop 2's loop).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Collections-19-probe/w of the
fixture, the first statement of retainAll was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. Full suite
(`defects4j test`): 3 failing tests, each with java.lang.IllegalStateException: PROBE-REACHED: SetUniqueListTest::testRetainAll,
::testRetainAllWithInitialList and ::testCollectionRetainAll (inherited from collection/AbstractCollectionTest). No other test reaches
the facade (the bulkTestSubList variants are not run: SetUniqueListTest has no suite() method).

Hosts (host_mode = "largest5"; bridge7_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 bidimap.TreeBidiMap         2138 lines  retainElementsOf      pass-through
  hop 2 ExtendedProperties          1761 lines  retainMembersOf       aggregation: the elements of the collection that the set holds
                                                                      are gathered into a HashSet (the original's first loop)
  hop 3 MapUtils                    1744 lines  retainSharedElements  decision: a kept set as large as the list's set leaves the list
                                                                      unchanged (false); otherwise delegate and return true
  hop 4 CollectionUtils             1486 lines  retainKeptElements    decision: an empty kept set clears the list
  hop 5 trie.PatriciaTrie           1447 lines  removeElementsNotIn   GOLD: one forward pass over the list by index, removing every
                                                                      element that is not in the kept set
Host newline counts 2138, 1761, 1744, 1486, 1447; the smallest host (and the gold host) has 1447 lines.
The correct configuration returns the original result and leaves the list and its set in the original state for every input: the
same kept set, the same size comparison against the internal set, the same clear, and the same forward removal (list.remove(int) on
the receiver is SetUniqueList.remove(int), which removes from the decorated list and from the set, as the iterator's remove did);
after a removal the index steps back so the element that moved into the position is examined next.

Fault (one-line omission in the gold's iteration): the `i--;` after `list.remove(i);` is dropped, so after each removal the element
that moves into the freed position is passed over; in a run of consecutive elements to remove, every second one stays. Trigger: the
EXISTING test SetUniqueListTest::testCollectionRetainAll (declared in collection/AbstractCollectionTest.java). Its empty, disjoint,
clearing and no-change steps do not reach the removal pass or do not depend on it; the partial step retains elements.subList(2, 5)
= [2, "Three", 4] of the 17 full elements, retainAll returns true, and verify() fails with "Collection size should match confirmed
collection's expected:<3> but was:<10>" ("One", 6.0f, "Eight", 10, 12L, "14" and (byte) 16 are passed over). It is the only test
that newly fails: testRetainAll and testRetainAllWithInitialList remove the odd numbers from 0..9, where no two elements to remove are
adjacent, so the variant removes exactly the same elements there.

The gold's javadoc states the idiomatic contract (it removes from a list the elements that are not in the given set, keeping the
others in their order) and is silent on stepping back after a removal; the variant leaves elements that are not in the set. The
convention is pinned outside the gold: CollectionUtils.filter removes every element its predicate rejects by visiting each element
through the iterator, and CollectionUtilsTest::filter removes the two adjacent 3s of [1, 2, 3, 3] and passes; the in-place retainAll
of the bidi map views (AbstractDualBidiMap.View.retainAll) walks its iterator and removes every element the collection lacks;
ListUtils.retainAll keeps exactly the elements of the collection that the other contains, in order (ListUtilsTest::testRetainAll);
SetUniqueList.removeAll, the facade's sibling, removes every named element. testCollectionRetainAll passes for the other List
implementations, e.g. TreeListTest::testCollectionRetainAll; SetUniqueListTest::testRetainAll pins the facade's result on 0..9.

Single owner: only the gold walks the list and decides per position whether the element there stays; hops 1 and 2 hold the
collection and the set, hop 3 compares sizes and hop 4 chooses between clearing and the pass, and none of them sees a position.
Once the gold has passed over an element, a caller can only take it out by running a second removal of its own over the list.
Declared alternatives (G9): hop 3 treats a kept set at least as large as the list's set as keeping everything; hop 4 also clears an
empty list directly; hop 2 gathers the kept elements in a LinkedHashSet. Each leaves the trigger failing.
Recorded bypasses (each replaces the gold's removal with another implementation or re-runs it; none repairs a step of the chain).
B-1, B-2, B-3 and B-3b were checked on the variant in scratch copies (/private/tmp/d4j-mi-Collections-19-B*, variant.patch plus the
one edit, defects4j test): 0 failing tests each.
 B-0 the facade's original body (iterator walk with SetListIterator.remove), discarding the chain including the gold.
 B-0b the facade re-implements the method in one line with the JDK operations of the decorated list and the set
     (`return decorated().retainAll(coll) | set.retainAll(coll);`), discarding the chain including the gold (checked as B-3b).
 B-1 hop 4 (or hop 3) removes the rejected elements itself, e.g.
     `list.removeAll(CollectionUtils.subtract(list, kept));` in place of the call to the gold (a second implementation of the pass).
 B-2 hop 4 runs the gold repeatedly until the list stops shrinking (each pass removes at least one element of every run), a
     workaround that depends on the gold's own per-pass behaviour.
 B-3 the facade returns super.retainAll(coll) (the decorated list's own retainAll): it passes the existing tests but removes the
     elements from the decorated list only, so the internal set keeps them and they can no longer be added back (add returns
     false), against the class's documented uniqueness set.

Lie: the facade's new javadoc claims the specified collection is first copied into a sorted array in which each element of this
list is then looked up by a binary search; the chain sorts nothing and looks elements up by hashing (HashSet.contains). It names
neither the removal pass, nor any position or index step, nor any hop.

Pre-edit (behaviour-preserving, comment only): retainAll has no javadoc, and the recipe's rewrite_facade appends the lie only to a
javadoc directly adjacent to the method header, which `@Override` prevents here. The pre-edit therefore adds, above `@Override`, a
one-sentence javadoc in the class's own voice ("Retains only the elements of this list that are contained in the specified
collection.") with the lie as its last line, in the exact layout rewrite_facade produces (the lie on its own line before `*/`);
rewrite_facade then replaces the body only.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, `for (int i = 0; i < list.size(); i++) { if (!kept.contains(list.get(i))) { list.remove(i); i--; } }`):
  T1 absent: list bounds the loop, supplies every element and is changed by remove; kept decides every removal.
  T2 absent: i is moved by the for header and by i--; no literal-initialised local that stays put, no flag, counter or best-so-far;
     the single if decides whether an element is removed.
  T3 absent: one decision with two outcomes (stays / removed); the gold names no class it handles in part; no pair half or range end.
  T4 absent: 'removes ... the elements that are not in the given set' (the remove line) and 'keeping the other elements in their
     order' (nothing is reordered) are met; '@param ..., must not be null' are caller preconditions; no inline comment.
 Variant gold (javadoc, signature, `for (int i = 0; i < list.size(); i++) { if (!kept.contains(list.get(i))) { list.remove(i); } }`):
  T1 absent: list (bound, get, remove) and kept (contains) both change the list's final contents; neither is only argument-checked.
  T2 absent: i is the loop cursor and is advanced by the for header inside the loop on every iteration; there is no other local; the
     if removes or keeps, two different effects; no frozen or dead local.
  T3 absent: the gold handles a single decision per element and its text names no set with a further member (no position, pair,
     range end or value class is mentioned or half-treated): 'No member handled'.
  T4 absent: 'Removes from a list the elements that are not in the given set' is a general description that the remove line
     addresses; 'keeping the other elements in their order' is met (no line reorders); '@param list the list to change, must not be
     null' and '@param kept the elements to keep, must not be null' are caller preconditions; the identifiers (list, kept, i) name
     no rule the body does not meet."""

SUL = "src/main/java/org/apache/commons/collections/list/SetUniqueList.java"
TBM = "src/main/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
EXP = "src/main/java/org/apache/commons/collections/ExtendedProperties.java"
MU = "src/main/java/org/apache/commons/collections/MapUtils.java"
CU = "src/main/java/org/apache/commons/collections/CollectionUtils.java"
PT = "src/main/java/org/apache/commons/collections/trie/PatriciaTrie.java"

LIE = ("The specified collection is first copied into a sorted array, and each element of this list is then looked up in "
       "that array by a binary search.")

GOLD_TEXT = '''/**
 * Removes from a list the elements that are not in the given set,
 * keeping the other elements in their order.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to change, must not be null
 * @param kept  the elements to keep, must not be null
 */
public static <E> void removeElementsNotIn(final List<E> list, final Set<?> kept) {
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
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to change, must not be null
 * @param members  the set of the elements in the list, must not be null
 * @param coll  the collection of the elements to keep, must not be null
 * @return true if the list changed
 */
public static <E> boolean retainElementsOf(final List<E> list, final Set<E> members,
        final Collection<?> coll) {
    return ExtendedProperties.retainMembersOf(list, members, coll);
}'''

HOP2 = '''/**
 * Retain in a list only the elements that are contained in the given
 * collection. The elements of the collection that are in the list are
 * first gathered into a set.
 *
 * @param <E> The type of the elements in the list.
 * @param list The list to change.
 * @param members The set of the elements in the list.
 * @param coll The collection of the elements to keep.
 * @return true if the list changed.
 */
public static <E> boolean retainMembersOf(final List<E> list, final Set<E> members,
                                          final Collection<?> coll) {
    final Set<Object> kept = new HashSet<Object>();
    for (final Object next : coll) {
        if (members.contains(next)) {
            kept.add(next);
        }
    }
    return MapUtils.retainSharedElements(list, members, kept);
}'''

HOP3 = '''/**
 * Retains in a list only the elements of a set of elements to keep.
 * <p>
 * If every element of the list is to be kept, the list is left as it
 * is and false is returned.
 *
 * @param <E>  the type of the elements in the list
 * @param list  the list to change, must not be null
 * @param members  the set of the elements in the list, must not be null
 * @param kept  the elements of the list to keep, must not be null
 * @return  true if the list changed
 */
public static <E> boolean retainSharedElements(final List<E> list, final Set<E> members,
        final Set<?> kept) {
    if (kept.size() == members.size()) {
        return false;
    }
    CollectionUtils.retainKeptElements(list, kept);
    return true;
}'''

HOP4 = '''/**
 * Retains in a list only the elements of the given set.
 * <p>
 * If the set is empty, the list is cleared.
 *
 * @param <E> the type of object the list contains
 * @param list the list to change, must not be null
 * @param kept the elements to keep, must not be null
 */
public static <E> void retainKeptElements(final List<E> list, final Set<?> kept) {
    if (kept.isEmpty()) {
        list.clear();
    } else {
        PatriciaTrie.removeElementsNotIn(list, kept);
    }
}'''

DESIGN = {
 "instance": "Collections-19", "project": "Collections", "bug_id": 19, "seed": 6698,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade_variant": "V1+V2",
 "state_passed": "receiver this (as List<E>) and the protected field set (as Set<E>), with the parameter coll; no write-back",
 "host_mode": "largest5",
 "facade": {"file": SUL, "class": "org.apache.commons.collections.list.SetUniqueList", "method": "retainAll", "near_line": 270},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/collections/list/SetUniqueListTest.java",
             "test_class": "org.apache.commons.collections.list.SetUniqueListTest",
             "test_method": "testCollectionRetainAll"},
 "expected_signature": "Collection size should match confirmed collection's expected:<3> but was:<10>",
 "gold": {"method": "removeElementsNotIn", "text": GOLD_TEXT,
          "fault": {"old": "            if (!kept.contains(list.get(i))) {\n"
                           "                list.remove(i);\n"
                           "                i--;",
                    "new": "            if (!kept.contains(list.get(i))) {\n"
                           "                list.remove(i);"}},
 "pre_edits": {
   "chain": [{"file": SUL,
              "old": "    @Override\n"
                     "    public boolean retainAll(final Collection<?> coll) {\n",
              "new": "    /**\n"
                     "     * Retains only the elements of this list that are contained in the\n"
                     "     * specified collection.\n"
                     "       " + LIE + "\n"
                     "     */\n"
                     "    @Override\n"
                     "    public boolean retainAll(final Collection<?> coll) {\n"}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.retainElementsOf(this, set, coll);",
   "lie": LIE,
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "retainElementsOf",
      "imports": ["java.util.List", "org.apache.commons.collections.ExtendedProperties"], "text": HOP1},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "retainMembersOf",
      "imports": ["java.util.Collection", "java.util.HashSet", "java.util.Set"], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "retainSharedElements",
      "imports": ["java.util.List", "java.util.Set"], "text": HOP3},
     {"file": CU, "class": "org.apache.commons.collections.CollectionUtils", "method": "retainKeptElements",
      "imports": ["org.apache.commons.collections.trie.PatriciaTrie"], "text": HOP4},
     {"file": PT, "class": "org.apache.commons.collections.trie.PatriciaTrie", "method": "removeElementsNotIn",
      "imports": ["java.util.List"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.CollectionUtils::filter",
              "org.apache.commons.collections.ListUtils::retainAll",
              "org.apache.commons.collections.list.SetUniqueList::removeAll"],
 "ownership_reason": "Only the gold walks the list and decides, position by position, whether the element there stays: hops 1 and 2 "
                     "hold the collection and the list's set and gather the elements to keep, hop 3 compares the size of that set "
                     "with the list's set and hop 4 chooses between clearing the list and the removal pass; none of them sees a "
                     "position. Once the pass has gone over an element without examining it, a caller can take it out only by "
                     "running a removal of its own over the list. The gold's javadoc promises that the elements not in the given "
                     "set are removed from the list and the others keep their order. The convention that a removal pass examines "
                     "every element, including the one that moves into the place of a removed element, is pinned outside the gold: "
                     "CollectionUtils.filter removes every element its predicate rejects, visiting each through the iterator "
                     "(CollectionUtilsTest filter removes both adjacent 3s of [1, 2, 3, 3] and passes); the bidi map views' "
                     "in-place retainAll (AbstractDualBidiMap.View) walks its iterator and removes every element the collection "
                     "lacks; ListUtils.retainAll keeps exactly the elements the other collection contains, in order "
                     "(ListUtilsTest testRetainAll); SetUniqueList.removeAll removes every named element; the same "
                     "testCollectionRetainAll passes for TreeList, and SetUniqueListTest testRetainAll pins the facade's result "
                     "on 0..9.",
 "ownership_tests": ["org.apache.commons.collections.CollectionUtilsTest::filter",
                     "org.apache.commons.collections.ListUtilsTest::testRetainAll",
                     "org.apache.commons.collections.list.TreeListTest::testCollectionRetainAll",
                     "org.apache.commons.collections.list.SetUniqueListTest::testRetainAll"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "if (kept.size() == members.size()) {",
      "new": "if (kept.size() >= members.size()) {",
      "why": "hop 3 treats a kept set at least as large as the list's set as keeping every element"},
     {"file": CU, "old": "if (kept.isEmpty()) {",
      "new": "if (kept.isEmpty() || list.isEmpty()) {",
      "why": "hop 4 also clears an empty list directly"},
     {"file": EXP, "old": "final Set<Object> kept = new HashSet<Object>();",
      "new": "final Set<Object> kept = new java.util.LinkedHashSet<Object>();",
      "why": "hop 2 gathers the elements to keep in the collection's order"},
   ],
 },
 "host_notes": "host_mode largest5 (bridge7_tasks.json: fewer than five other public classes of at least 1500 lines). Hosts are "
               "hosts_hop_order of the task record, in that order, none substituted: bidimap.TreeBidiMap (hop 1, 2138 lines), "
               "ExtendedProperties (hop 2, 1761), MapUtils (hop 3, 1744), CollectionUtils (hop 4, 1486), trie.PatriciaTrie "
               "(hop 5, gold, 1447; the smallest host). All five are public concrete top-level classes in which a static method "
               "compiles; TreeBidiMap and PatriciaTrie are generic, which does not affect a static generic method. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 6698 + 100 + i (as mr3_spec.py inserts them): hop 1 after `mapIterator` "
               "(seed 6798), hop 2 after `isInitialized` (6799), hop 3 after the three-argument `getString` (6800), hop 4 after "
               "`disjunction` (6801), hop 5 after the one-argument `getPrefixedBy` (6802); all in the outer class. The facade "
               "calls hop 1 by its fully-qualified name; each hop imports the next host where it is in another package "
               "(ExtendedProperties, MapUtils and CollectionUtils share a package).",
}
