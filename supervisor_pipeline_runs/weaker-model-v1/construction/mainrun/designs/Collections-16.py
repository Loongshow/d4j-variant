"""Main run Collections-16 (cell C10f: the C10 recipe with the largest-5 host rule, on the fixed checkout of Defects4J
Collections-16; the real bug modified SetUniqueList, the target class).

Facade: SetUniqueList.decorate(List) (the only allowed target, BATCH6_PREREGISTRATION.md row 149; facade_reuse_of = Collections-5,
recorded: the same method is the facade of that instance on another fixed revision; it changes nothing in how this one is built).
Original computation: a null list throws IllegalArgumentException("List must not be null"); an empty list is wrapped with a new
HashSet; otherwise the list is copied into an ArrayList and cleared, a SetUniqueList is made on the cleared list with a new HashSet,
and the copy is added back through SetUniqueList.addAll, which appends an element (and adds it to the set) only when the set does
not contain it yet, so the first indexed occurrence is kept and the list ends in the insertion order of the set.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2): in a scratch copy of the fixture the facade's first statement was made
`if (true) throw new IllegalStateException("PROBE-REACHED");` (the guard form is needed only so that the rest of the body stays
reachable for javac); defects4j compile OK; the full suite (defects4j test, about 10 s) then failed exactly 5 tests, each with
java.lang.IllegalStateException: PROBE-REACHED: TestSetUniqueList::testFactory, ::testUniqueListReInsert,
::testUniqueListDoubleInsert, ::testCollections304, ::testCollections307. The facade is reached by existing tests. Only
testFactory decorates a non-empty list; the other four decorate an empty LinkedList or ArrayList. No production code calls
decorate.

Hosts (host_mode = "largest5": the fixed revision has only 4 public classes of >= 1500 lines besides SetUniqueList, so the hosts are
the five largest public, non-interface, non-enum classes, hosts_hop_order of the task record; newline counts on the checkout):
  hop 1 bidimap/TreeBidiMap.java           2085 lines   anchor after toString      (seed 3101)
  hop 2 DoubleOrderedMap.java              1995 lines   anchor after containsKey   (seed 3102)
  hop 3 ExtendedProperties.java            1784 lines   anchor after getBoolean    (seed 3103)
  hop 4 MapUtils.java                      1678 lines   anchor after getNumber     (seed 3104)
  hop 5 CursorableLinkedList.java          1468 lines   anchor after lastIndexOf   (seed 3105)
  smallest host: 1468 lines (CursorableLinkedList.java). Anchors from stageB_lib.pick_insertion_anchor with seed 3001 + 100 + i,
  as stageB_spec.py / mr2_spec.py do; they match the task record's host_draw anchors. No host was substituted.
  The hop-5 anchor (lastIndexOf at line 1384) lies in CursorableSubList, the second, package-private top-level class declared in
  CursorableLinkedList.java (class CursorableSubList extends CursorableLinkedList, line 1202), so the gold is
  org.apache.commons.collections.CursorableSubList::addInOrder; the harness method catalog (tools/JavaMethodCatalog.java, run on the
  fixture) lists that file's second class under exactly this name. A static method compiles there and MapUtils (hop 4) is in the
  same package, so the host is usable as drawn.

Chain:
  facade SetUniqueList.decorate              guard (null list) + one delegating call; SetUniqueList's only constructor is
                                             protected and no host is in its package, so the facade keeps the construction:
                                             return new SetUniqueList(list, TreeBidiMap.orderedSetFor(list))
  hop 1 bidimap.TreeBidiMap.orderedSetFor     decision: an empty list is left as it is and gets an empty HashSet
  hop 2 DoubleOrderedMap.newSetFor            placement: the new HashSet for the set
  hop 3 ExtendedProperties.orderInto          pass-through
  hop 4 MapUtils.refillInOrder                plumbing: the list is copied element for element into an ArrayList and cleared
  hop 5 CursorableSubList.addInOrder          GOLD: the per-element core: each element of the copy is added to the set, and to
                                              the list when the set takes it in
The correct configuration returns the original result for every input: the same guard and message, the same empty-list shortcut,
the same copy-then-clear order on the given list (an unmodifiable non-empty list still throws from clear()), the same HashSet, and
the same per-element rule (appending at the end of the list is what addAll(size(), coll) does, its index starting at the size of
the cleared list and advancing with every insertion); the facade wraps the same list object with the same set.

Fault (one-line omission in the gold): the decision on the result of set.add is dropped, so every element of the copy is appended
to the list, including an element the set already holds. The gold then reads as the plain routine "add each element to the set and
to the list". Trigger: the EXISTING test TestSetUniqueList::testFactory, decorate([1, 2, 1]):
assertEquals("Duplicate element was added.", 2, lset.size()) fails with expected:<2> but was:<3>. It is the only test that decorates
a non-empty list (probe above), and no production code reaches the chain, so it is the only test that newly fails.
The gold's javadoc states the idiomatic contract (the elements are added to a set and the list keeps the insertion order of the
set) and is silent on repeated elements; on [1, 2, 1] the insertion order of the set is [1, 2] and the variant leaves [1, 2, 1],
so the variant violates that contract on the trigger input.

External pins (the same step in other production code, with passing tests): ListOrderedSet.add ('re-adding doesn't change order'
/ 'first add, so add to both set and list': the order list takes an element only on its first addition to the set;
TestListOrderedSet::testOrdering re-adds present elements and checks the order is unchanged); SetUniqueList.add(int, Object)
(adds to the list and the set only when set.contains is false; TestSetUniqueList::testAdd); SetUniqueList.addAll(int, Collection),
the facade's original delegate ('Only elements that are not already in this list will be added, and duplicates from the specified
collection will be ignored'; TestSetUniqueList::testAddAll adds [1, 1] and expects size 1). The facade's own javadoc ('If the list
contains duplicates, these are removed (first indexed one kept)') states the result.

Single owner: only the gold sees each element together with the answer of the set (whether the set took it in); hops 1-3 hold the
original list and the set and get back the set, hop 4 holds the copy and passes it on whole ('copied, element for element'; 'the
copy is then added to the set, element by element in iteration order'). Once the gold has appended a repeated element, no caller
above it can tell from the returned set which entries of the list are repeats without redoing the gold's work.
Declared alternatives (G9; each still fails the trigger with size 3):
  hop 2 initialises the new HashSet with the elements of the list (the constructor's 'set and list ... initialised to the same
  elements'); hop 3 keeps in the list only the members of the returned set, the idiom of ListOrderedSet.decorate(List)
  (list.retainAll keeps every repeat); hop 1 also lets a list of one element through as it is.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each):
 B-0 bypass: the facade's original body (copy, clear, new SetUniqueList, addAll), discarding the chain including the gold.
 B-1 pre-filter at hop 4 that re-implements the gold's step: `List copy = new ArrayList(new java.util.LinkedHashSet(list));`.
     It contradicts hop 4's documented copy ('copied, element for element') and makes the gold's decision inert.
 B-2 pre-filter at hop 4: `return CursorableSubList.addInOrder(new java.util.LinkedHashSet(copy), list, set);`. It contradicts
     hop 4's documentation ('the copy is then added to the set, element by element') and re-implements the gold's decision with
     another set before the gold runs.
 B-3 test-fitted at hop 4: `List copy = new ArrayList(new HashSet(list));`: passes because the HashSet of Integer 1 and 2 iterates
     in that order, but it loses the order of the list in general (decorate(["b", "a"]) and many other inputs are reordered) and
     contradicts the element-for-element copy.
 B-4 bypass: any of hops 1-3 rewrites the list in place before delegating (for example hop 3:
     `Set u = new java.util.LinkedHashSet(list); list.clear(); list.addAll(u); return MapUtils.refillInOrder(list, set);`),
     a second implementation of the whole computation in three statements.

Lie: the facade's javadoc claims the elements are transferred from the end of the list towards its start, each being inserted at
index zero of the decorated list; the chain walks the copy forwards and appends. It names neither repeated elements nor the set's
decision nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (loop over coll; Object item = it.next(); if (set.add(item)) { list.add(item); }; return set):
  T1 absent: coll is iterated, set receives every element and is returned, list receives the elements the set takes in.
  T2 absent: it is advanced by it.next() in every iteration; item is assigned per iteration and read by both calls; no literal-
     initialised local, counter, flag or best-so-far; the if has two different effects (append or not).
  T3 absent: no closed set with a handled and an unhandled member; no named class; no pair halves or range ends.
  T4 absent: the javadoc names the insertion order of the set (which the if produces) and caller preconditions ('not null').
  Nothing needed rewriting.
 Variant gold (javadoc, signature, `for (Iterator it = coll.iterator(); it.hasNext();) { Object item = it.next(); set.add(item);
 list.add(item); } return set;`):
  T1 absent: coll's elements are what is added; set is written and returned; list is written; each value changes the result or
     a side effect, and no parameter is only argument-checked (the gold has no argument check).
  T2 absent: the only locals are it (advanced by it.next() each iteration) and item (assigned per iteration, read by both add
     calls); no literal-initialised or loop-moved local left unassigned; no branch, case or ternary remains.
  T3 absent: no case, branch or check remains, so no set has a handled and an unhandled member ('No member handled'); list and
     set get the same treatment; the gold names no class it handles in part.
  T4 absent: 'Adds the elements of a collection to a set, in iteration order, and keeps the insertion order of the set in a list'
     is a general description that the loop's two add calls address; '@param ... not null' are caller preconditions; '@return the
     set' is met; no limit, bound, value class or case is named; no inline comment; identifiers (addInOrder, coll, list, set, it,
     item) name nothing the body visibly fails to meet."""

SUL = "src/java/org/apache/commons/collections/list/SetUniqueList.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EXP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MAU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Adds the elements of a collection to a set, in iteration order, and
 * keeps the insertion order of the set in a list.
 *
 * @param coll  the elements to add, not null
 * @param list  the list to keep the order in, not null
 * @param set  the set to add to, not null
 * @return the set
 */
public static Set addInOrder(Collection coll, List list, Set set) {
    for (Iterator it = coll.iterator(); it.hasNext();) {
        Object item = it.next();
        if (set.add(item)) {
            list.add(item);
        }
    }
    return set;
}'''

HOP1 = '''/**
 * Gets a new <code>HashSet</code> of the elements of a list, leaving the
 * list in the insertion order of the set.
 * <p>
 * An empty list is left as it is and gets an empty set.
 *
 * @param list  the list to use, not null
 * @return the set of the elements of the list
 */
public static Set orderedSetFor(List list) {
    if (list.isEmpty()) {
        return new HashSet();
    }
    return DoubleOrderedMap.newSetFor(list);
}'''

HOP2 = '''/**
 * Gets a new <code>HashSet</code> of the elements of a non-empty list,
 * leaving the list in the insertion order of the set.
 *
 * @param list the list to use, not null or empty.
 *
 * @return the set of the elements of the list.
 */
public static Set newSetFor(final List list) {
    return ExtendedProperties.orderInto(list, new HashSet());
}'''

HOP3 = '''/**
 * Adds the elements of a non-empty list to an empty set, leaving the
 * list in the insertion order of the set.
 *
 * @param list The list to use, not null or empty.
 * @param set The empty set to add to.
 * @return The set.
 */
public static Set orderInto(List list, Set set) {
    return MapUtils.refillInOrder(list, set);
}'''

HOP4 = '''/**
 * Adds the elements of a non-empty list to an empty set, leaving the
 * list in the insertion order of the set.
 * <p>
 * The list is first copied, element for element, into a new
 * <code>ArrayList</code> and then cleared; the copy is then added to the
 * set, element by element in iteration order, with the list keeping the
 * insertion order of the set.
 *
 * @param list  the list to use, not null or empty
 * @param set  the empty set to add to
 * @return the set
 */
public static Set refillInOrder(List list, Set set) {
    List copy = new ArrayList(list);
    list.clear();
    return CursorableSubList.addInOrder(copy, list, set);
}'''

DESIGN = {
 "instance": "Collections-16", "project": "Collections", "bug_id": 16, "seed": 3001,
 "src_root": "src/java", "test_root": "src/test",
 "host_mode": "largest5", "host_lines": [2085, 1995, 1784, 1678, 1468], "smallest_host_lines": 1468,
 "facade_reuse_of": ["Collections-5"],
 "reachability_probe": "facade first statement `if (true) throw new IllegalStateException(\"PROBE-REACHED\");` in a scratch copy; "
                       "defects4j test (full suite): 5 failing, all with PROBE-REACHED: TestSetUniqueList::testFactory, "
                       "testUniqueListReInsert, testUniqueListDoubleInsert, testCollections304, testCollections307",
 "facade": {"file": SUL, "class": "org.apache.commons.collections.list.SetUniqueList", "method": "decorate", "near_line": 73},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/list/TestSetUniqueList.java",
             "test_class": "org.apache.commons.collections.list.TestSetUniqueList", "test_method": "testFactory"},
 "expected_signature": "expected:<2> but was:<3>",
 "gold": {"method": "addInOrder", "text": GOLD_TEXT,
          "fault": {"old": "            if (set.add(item)) {\n"
                           "                list.add(item);\n"
                           "            }",
                    "new": "            set.add(item);\n"
                           "            list.add(item);"}},
 "chain": {
   "facade_body": "if (list == null) {\n"
                  "            throw new IllegalArgumentException(\"List must not be null\");\n"
                  "        }\n"
                  "        return new SetUniqueList(list, org.apache.commons.collections.bidimap.TreeBidiMap.orderedSetFor(list));",
   "lie": "The elements are transferred from the end of the list towards its start, each being inserted at index zero "
          "of the decorated list.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "orderedSetFor",
      "imports": ["java.util.HashSet", "java.util.List", "org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "newSetFor",
      "imports": ["java.util.HashSet", "java.util.List"], "text": HOP2},
     {"file": EXP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "orderInto",
      "imports": ["java.util.Set"], "text": HOP3},
     {"file": MAU, "class": "org.apache.commons.collections.MapUtils", "method": "refillInOrder",
      "imports": ["java.util.ArrayList", "java.util.List", "java.util.Set"], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "addInOrder",
      "imports": ["java.util.Set"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.set.ListOrderedSet::add",
              "org.apache.commons.collections.list.SetUniqueList::add",
              "org.apache.commons.collections.list.SetUniqueList::addAll"],
 "ownership_reason": "Only the gold sees each element together with the answer of the set (whether set.add took it in); hops 1-3 "
                     "hold the original list and the set and get the set back, and hop 4 copies the list element for element, "
                     "clears it and hands the whole copy to the gold, as its javadoc states ('copied, element for element'; 'the "
                     "copy is then added to the set, element by element in iteration order'). Once the gold has appended a "
                     "repeated element, no caller can tell from the returned set which list entries are repeats without redoing "
                     "the gold's work. The gold's javadoc promises that the list keeps the insertion order of the set; on "
                     "[1, 2, 1] that order is [1, 2] and the variant leaves [1, 2, 1]. The convention is pinned outside the gold: "
                     "ListOrderedSet.add appends to its order list only on the first addition ('re-adding doesn't change order'; "
                     "TestListOrderedSet testOrdering re-adds present elements and checks the order), SetUniqueList.add(int, "
                     "Object) adds to list and set only when the set does not contain the element (TestSetUniqueList testAdd), "
                     "and SetUniqueList.addAll, the facade's original delegate, ignores duplicates from the added collection "
                     "(TestSetUniqueList testAddAll); the facade's javadoc states the result ('duplicates ... are removed (first "
                     "indexed one kept)'). One-line edits above the gold that de-duplicate the copy before the gold (a "
                     "LinkedHashSet of the list or of the copy at hop 4) pass the existing tests but contradict hop 4's documented "
                     "element-for-element copy and hand-over and re-implement the gold's decision; a HashSet copy at hop 4 passes "
                     "only because Integer 1 and 2 hash in that order and reorders other lists.",
 "ownership_tests": ["org.apache.commons.collections.set.TestListOrderedSet::testOrdering",
                     "org.apache.commons.collections.list.TestSetUniqueList::testAdd",
                     "org.apache.commons.collections.list.TestSetUniqueList::testAddAll"],
 "compensating": {
   "chain": [
     {"file": DOM, "old": "return ExtendedProperties.orderInto(list, new HashSet());",
      "new": "return ExtendedProperties.orderInto(list, new HashSet(list));",
      "why": "hop 2 initialises the new set with the elements of the list"},
     {"file": EXP, "old": "return MapUtils.refillInOrder(list, set);",
      "new": "Set result = MapUtils.refillInOrder(list, set); list.retainAll(result); return result;",
      "why": "hop 3 keeps in the list only the members of the returned set, as ListOrderedSet.decorate(List) does"},
     {"file": TBM, "old": "if (list.isEmpty()) {\n            return new HashSet();",
      "new": "if (list.size() < 2) {\n            return new HashSet(list);",
      "why": "hop 1 also lets a list of one element through as it is"},
   ],
 },
 "host_notes": "host_mode largest5 (4 other public classes reach 1500 lines in this revision): hosts are hosts_hop_order of "
               "main-run/batch6_tasks.json, in that order: bidimap.TreeBidiMap 2085 lines (hop 1), DoubleOrderedMap 1995 (hop 2), "
               "ExtendedProperties 1784 (hop 3), MapUtils 1678 (hop 4), CursorableLinkedList.java 1468 (hop 5, gold); smallest "
               "host 1468 lines. Anchors from stageB_lib.pick_insertion_anchor with seeds 3101-3105 (instance seed 3001 + 100 + i): "
               "after toString, containsKey, getBoolean, getNumber and lastIndexOf, equal to the task record's host_draw. None "
               "substituted: all five are public concrete classes in which a static method compiles. The hop-5 anchor "
               "(lastIndexOf, line 1384) lies in CursorableSubList, the package-private second top-level class of "
               "CursorableLinkedList.java (extends CursorableLinkedList), so the gold's class is "
               "org.apache.commons.collections.CursorableSubList, which is how the harness method catalog lists that file's "
               "second class; MapUtils (hop 4) is in the same package. The anchors of hops 1-4 lie in the outer classes. "
               "SetUniqueList's only constructor is protected and no host is in its package, so the facade keeps the "
               "construction and passes hop 1's result as the set: guard + return new SetUniqueList(list, "
               "TreeBidiMap.orderedSetFor(list)). The facade calls hop 1 by its fully-qualified name; hop 1 imports "
               "DoubleOrderedMap; hops 2-4 and the gold share the org.apache.commons.collections package.",
}
