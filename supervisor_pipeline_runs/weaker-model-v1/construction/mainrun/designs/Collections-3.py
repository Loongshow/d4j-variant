"""Main run Collections-3, cell C10f (C10 recipe with the largest-five host rule, BATCH6_PREREGISTRATION.md) on the fixed checkout
of Defects4J Collections-3; the real bug modified CollectionUtils, the facade's class.

host_mode: largest5 (four other public classes reach 1500 lines; batch6_tasks.json). Hosts, hop order = size order (newline counts):
  hop 1 bidimap/TreeBidiMap.java 2084, hop 2 DoubleOrderedMap.java 1994, hop 3 ExtendedProperties.java 1716,
  hop 4 MapUtils.java 1644, hop 5 (gold) CursorableLinkedList.java 1467. Smallest host: 1467 lines (the gold host).

reachability_probe: in a scratch copy of the fixture the first statement of each allowed facade (CollectionUtils.index(Object,
Object), which index(Object,int) delegates to; CollectionUtils.get(Object,int); CollectionUtils.size(Object)) was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. defects4j test -t on TestCollectionUtils::testIndex, ::testGet and
the seven ::testSize_* methods: each failed with java.lang.IllegalStateException: PROBE-REACHED. Full suite on that copy: exactly
those 9 tests failed; no production code calls any of the three facades. All three facades are reachable.

Facade: CollectionUtils.index(Object, Object) (allowed target `index`). Its only test caller is TestCollectionUtils::testIndex (directly
and through index(Object,int), which stays intact and delegates to it). The other allowed targets were set aside: in get(Object,int)
every sequential path ends in a throw (IndexOutOfBoundsException, or IllegalArgumentException for an unrecognised type), so an omitted
type step surfaces as an exception raised inside the chain, and every omission inside its walk leaves a loop that no longer advances
its source or its counter (checklist T2); size(Object) has one test per type, but its per-element step is a bare count, whose only
omissions freeze the counter (T2) or stop the loop from terminating, and an omitted type step again surfaces as an exception raised
inside the chain.
Original computation of the facade: a Map that contains the index as a key gives the mapped value; otherwise an index that is not a
non-negative Integer gives the object itself; a Map gives the idx-th key of its key-set iterator (or that iterator, when it has fewer
keys); a List or an Object[] is read at idx (IndexOutOfBoundsException / ArrayIndexOutOfBoundsException if absent); an Enumeration
or an Iterator is advanced to its idx-th element, which is returned, or, when it has fewer elements, the Enumeration or Iterator
itself is returned (exhausted); a Collection gives the idx-th element of its iterator (or that iterator); anything else gives the
object itself.

Chain (hosts = host_files_top5 of the task record, in that order; anchors from stageB_lib.pick_insertion_anchor with seed 4165 + 100 + i):
  hop 1 bidimap.TreeBidiMap.keyedValue          decision: a Map that contains the key gives the mapped value
  hop 2 DoubleOrderedMap.positionalValue        decision: an index that is not a non-negative Integer gives the object itself
  hop 3 ExtendedProperties.getNth               placement: a Map is read through its key set
  hop 4 MapUtils.getNthValue                    dispatch: List / Object[] read at the position; a Collection passed on as its iterator
  hop 5 CursorableSubList.nthElement            GOLD: the in-order walk of an Iterator or an Enumeration to the nth element, and the
                                                object itself when the walk runs out or there is nothing to walk
The correct configuration returns the original result for every input (same key test first, same Integer and sign test, the key-set
iterator for a Map, the same List and array reads, the same walk with the exhausted Iterator / Enumeration / collection iterator
returned), except for an object that is at once a Collection and an Iterator or Enumeration, which hop 4 reads through its iterator
before the gold sees it (no class of the code base implements both).

Fault (omission of a special-case decision in the gold): the branch that reads an Enumeration through IteratorUtils.asIterator is
dropped, so an Enumeration reaches the walk as nothing to walk and is returned unchanged. The gold then reads as the ordinary routine
'walk the Iterator to its nth element, otherwise return the object'. Trigger: the EXISTING test TestCollectionUtils::testIndex; all
its Map, SortedMap, List and Iterator assertions still hold, and the first Enumeration assertion, line 537
assertTrue(test.equals("zero")) after index(vector.elements(), 0), fails with junit.framework.AssertionFailedError (the Enumeration
itself is returned). No other test reaches the facade (probe above). The gold's javadoc states the idiomatic contract (the nth value
in the object; the object itself if it has no nth value; the original javadoc's wording) and is silent on Enumerations; an
Enumeration of "zero", "one" has a 0th value, so the variant violates that contract on the trigger input.

External pins (convention outside the gold): the facade's own javadoc and that of index(Object,int) ('If obj is an iterator,
enumeration or Collection, get the nth value from the iterator, returning an empty Iterator (resp. Enumeration) if the nth value
does not exist'); CollectionUtils.get walks an Enumeration to its index-th element exactly like an Iterator (testGet, Enumeration
block, passes); CollectionUtils.size counts and CollectionUtils.sizeIsEmpty tests an Enumeration like an Iterator
(testSize_Enumeration, testSizeIsEmpty_Enumeration pass); IteratorUtils.getIterator reads an Enumeration through an
EnumerationIterator, the same view the gold uses.

Single owner: only the gold both walks a source in order and decides what is returned when the walk runs out; it receives the
Enumeration itself, so it alone can return the nth element AND, when there are fewer elements, the very Enumeration it was given (the
documented 'Enumeration' result, asserted by testIndex line 544: test.equals(en) && !en.hasMoreElements()). Each of hops 1-4
documents that any object it does not read itself is passed on unchanged (hop 1: a Map without the key; hop 2: an object with a
non-negative Integer index; hop 3: anything but a Map; hop 4: anything but a List, an Object[] or a Collection), so an Enumeration
reaches the gold as it is, and a hop that handed on anything else would contradict its own javadoc. Hops 1-4 can only change what they
hand on: an iterator view of the Enumeration makes the exhausted case return the view, not the Enumeration; a List copy makes it
throw IndexOutOfBoundsException at the List read; neither can be undone after the gold has returned. Declared alternatives (G9),
each still failing the trigger: hop 4 hands an iterator view (IteratorUtils.asIterator) to the gold (line 544 then sees the view);
hop 3 turns an Enumeration into a List (EnumerationUtils.toList; index(en, 3) then throws at the List read); hop 2 does the same
with java.util.Collections.list.
Recorded bypass (a multi-statement edit above the gold, not a one-line repair, and against the editing hop's own javadoc):
 B-1 hop 4 (or any of hops 1-3) gets an Enumeration branch of three statements: wrap it with IteratorUtils.asIterator, call the
     next hop with the view, and return the Enumeration itself when the view comes back (`Iterator view = ...; Object value =
     CursorableSubList.nthElement(view, idx); return value == view ? obj : value;`). Checked at hop 4 on the variant in a scratch
     copy: trigger passes, full suite 0 failing tests. It hands on an object other than the one it was given, which the hop's
     javadoc excludes ('any other object is passed on unchanged'), and it re-implements the gold's exhausted-source rule in that
     hop.

Lie: the facade's javadoc claims the values of the object are first copied into a new array and the value at the index is then read
from that array in a single lookup; the chain copies nothing (it reads Lists and arrays in place and walks iterators). It names
neither Enumerations nor any omitted step nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: obj decides the branch and is returned on the fall-through; idx is decremented and compared in the walk.
  T2 absent: it is initialised to the constant IteratorUtils.EMPTY_ITERATOR (not a literal) and assigned in both branches; idx is
     decremented in the loop; it.next() advances the source in both outcomes of the if; the if returns, the fall-through continues.
  T3 absent: both sources the gold names (Iterator, Enumeration) get the walk; no pair, range or named value class.
  T4 absent: the javadoc names the nth value and the object itself when there is no nth value; both are produced.
 Variant gold (javadoc; `Iterator it = IteratorUtils.EMPTY_ITERATOR; if (obj instanceof Iterator) { it = (Iterator) obj; }` then
 the walk and `return obj;`):
  T1 absent: obj is tested (instanceof), becomes the walked iterator and is returned; idx is decremented and decides which element
     is returned; each changes the result.
  T2 absent: it starts at a constant iterator field (not a literal) and is assigned in the if; the loop decrements idx and calls
     it.next() on both outcomes of its if, so cursor and counter both move; the instanceof decision and the idx == -1 decision each
     change the result (walk vs none; return vs continue); no dead branch, case or ternary.
  T3 absent: exactly one source type is handled (Iterator) and the gold's text names no other type and no class of sources (its
     javadoc says 'an Object'); no pair halves, range ends or named value class; 'One member of a larger unnamed set'.
  T4 absent: 'returns the nth value in the object' is a general description that the walk addresses; '@return the nth value, or
     the object itself if it has no nth value' names a case the body meets (return obj after the walk); '@param idx ..., not
     negative' is a caller precondition; no limit, bound, value class or property is named; no inline comment; identifiers (it,
     idx, nthElement) name nothing the body does not meet."""

CU = "src/java/org/apache/commons/collections/CollectionUtils.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
EP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"

GOLD_TEXT = '''/**
 * Given an Object, and an index, returns the nth value in the object.
 *
 * @param obj  the object to get the nth value of
 * @param idx  the index of the value, not negative
 * @return the nth value, or the object itself if it has no nth value
 */
public static Object nthElement(Object obj, int idx) {
    Iterator it = IteratorUtils.EMPTY_ITERATOR;
    if (obj instanceof Iterator) {
        it = (Iterator) obj;
    } else if (obj instanceof java.util.Enumeration) {
        it = IteratorUtils.asIterator((java.util.Enumeration) obj);
    }
    while (it.hasNext()) {
        idx--;
        if (idx == -1) {
            return it.next();
        }
        it.next();
    }
    return obj;
}'''

HOP1 = '''/**
 * Given an Object, and a key (index), returns the value associated with
 * that key in the Object.
 * <p>
 * If the object is a Map that contains the key, the value mapped to the
 * key is returned; otherwise the object and the index are passed on
 * unchanged.
 *
 * @param obj  the object to get a value from
 * @param index  the key (index) to get
 * @return the value associated with the key
 */
public static Object keyedValue(Object obj, Object index) {
    if (obj instanceof Map) {
        Map map = (Map) obj;
        if (map.containsKey(index)) {
            return map.get(index);
        }
    }
    return DoubleOrderedMap.positionalValue(obj, index);
}'''

HOP2 = '''/**
 * Given an Object, and an index, returns the value at the position given
 * by the index in the Object.
 * <p>
 * An index that is not an Integer, or is a negative Integer, gives the
 * object itself; for any other index the object is passed on unchanged.
 *
 * @param obj  the object to get a value from
 * @param index  the index to get
 * @return the value at the position, or the object itself
 */
public static Object positionalValue(Object obj, Object index) {
    if (index instanceof Integer) {
        int idx = ((Integer) index).intValue();
        if (idx >= 0) {
            return ExtendedProperties.getNth(obj, idx);
        }
    }
    return obj;
}'''

HOP3 = '''/**
 * Gets the value at a position of an object. A Map is read through its
 * key set; any other object is passed on unchanged.
 *
 * @param obj  the object to get a value from
 * @param idx  the position of the value, not negative
 * @return the value at the position
 */
public static Object getNth(Object obj, int idx) {
    if (obj instanceof Map) {
        return MapUtils.getNthValue(((Map) obj).keySet(), idx);
    }
    return MapUtils.getNthValue(obj, idx);
}'''

HOP4 = '''/**
 * Gets the value at a position of an object.
 * <p>
 * A List or an object array is read at the position, and a Collection
 * through its iterator; any other object is passed on unchanged.
 *
 * @param obj  the object to get a value from
 * @param idx  the position of the value, not negative
 * @return the value at the position
 */
public static Object getNthValue(Object obj, int idx) {
    if (obj instanceof List) {
        return ((List) obj).get(idx);
    } else if (obj instanceof Object[]) {
        return ((Object[]) obj)[idx];
    } else if (obj instanceof Collection) {
        return CursorableSubList.nthElement(((Collection) obj).iterator(), idx);
    }
    return CursorableSubList.nthElement(obj, idx);
}'''

DESIGN = {
 "instance": "Collections-3", "project": "Collections", "bug_id": 3, "seed": 4165,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": CU, "class": "org.apache.commons.collections.CollectionUtils", "method": "index", "near_line": 740},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/TestCollectionUtils.java",
             "test_class": "org.apache.commons.collections.TestCollectionUtils", "test_method": "testIndex"},
 "expected_signature": "TestCollectionUtils.testIndex(TestCollectionUtils.java:537)",
 "gold": {"method": "nthElement", "text": GOLD_TEXT,
          "fault": {"old": "        Iterator it = IteratorUtils.EMPTY_ITERATOR;\n"
                           "        if (obj instanceof Iterator) {\n"
                           "            it = (Iterator) obj;\n"
                           "        } else if (obj instanceof java.util.Enumeration) {\n"
                           "            it = IteratorUtils.asIterator((java.util.Enumeration) obj);\n"
                           "        }",
                    "new": "        Iterator it = IteratorUtils.EMPTY_ITERATOR;\n"
                           "        if (obj instanceof Iterator) {\n"
                           "            it = (Iterator) obj;\n"
                           "        }"}},
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.keyedValue(obj, index);",
   "lie": "The values of the object are first copied into a new array, and the value at the index is then read from that "
          "array in a single lookup.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "keyedValue",
      "imports": ["org.apache.commons.collections.DoubleOrderedMap"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "positionalValue",
      "imports": [], "text": HOP2},
     {"file": EP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "getNth",
      "imports": ["java.util.Map"], "text": HOP3},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "getNthValue",
      "imports": ["java.util.Collection", "java.util.List"], "text": HOP4},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableSubList", "method": "nthElement", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.CollectionUtils::get",
              "org.apache.commons.collections.CollectionUtils::size",
              "org.apache.commons.collections.CollectionUtils::sizeIsEmpty",
              "org.apache.commons.collections.IteratorUtils::getIterator"],
 "ownership_reason": "Only the gold walks a source in order and decides what is returned when the walk runs out; it is handed "
                     "the Enumeration itself, so it alone can return the nth element and, when there are fewer elements, the very "
                     "Enumeration it was given, which the facade documents ('returning an empty Iterator (resp. Enumeration) if the "
                     "nth value does not exist') and testIndex asserts (test.equals(en) && !en.hasMoreElements()). Hops 1-4 can "
                     "only change what they hand on: an iterator view of the Enumeration makes the exhausted case return the view, "
                     "a List copy makes it throw at the List read, and nothing can be recovered after the gold has returned. The "
                     "convention is pinned outside the gold: CollectionUtils.get walks an Enumeration to its index-th element like "
                     "an Iterator (testGet), CollectionUtils.size and sizeIsEmpty treat an Enumeration like an Iterator "
                     "(testSize_Enumeration, testSizeIsEmpty_Enumeration), IteratorUtils.getIterator reads an Enumeration through "
                     "an EnumerationIterator, and the facade's and index(Object,int)'s javadoc list the enumeration case.",
 "ownership_tests": ["org.apache.commons.collections.TestCollectionUtils::testGet",
                     "org.apache.commons.collections.TestCollectionUtils::testSize_Enumeration",
                     "org.apache.commons.collections.TestCollectionUtils::testSizeIsEmpty_Enumeration"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "        return CursorableSubList.nthElement(obj, idx);",
      "new": "        return CursorableSubList.nthElement(obj instanceof Enumeration ? IteratorUtils.asIterator((Enumeration) obj) : obj, idx);",
      "why": "hop 4 hands an iterator view of an Enumeration to the walk"},
     {"file": EP, "old": "        return MapUtils.getNthValue(obj, idx);",
      "new": "        return MapUtils.getNthValue(obj instanceof Enumeration ? EnumerationUtils.toList((Enumeration) obj) : obj, idx);",
      "why": "hop 3 turns an Enumeration into a List for the positional read"},
     {"file": DOM, "old": "            return ExtendedProperties.getNth(obj, idx);",
      "new": "            return ExtendedProperties.getNth(obj instanceof java.util.Enumeration ? java.util.Collections.list((java.util.Enumeration) obj) : obj, idx);",
      "why": "hop 2 turns an Enumeration into a List before the position is read"},
   ],
 },
 "host_notes": "host_mode largest5: the hosts are host_files_top5 of the task record in order (TreeBidiMap 2084, DoubleOrderedMap "
               "1994, ExtendedProperties 1716, MapUtils 1644, CursorableLinkedList 1467 lines; smallest 1467); mr_lib preview "
               "was not used. Anchors (stageB_lib.pick_insertion_anchor, seed 4165 + 100 + i, none excluded or advanced): hop 1 "
               "after TreeBidiMap.mapIterator (line idx 412), hop 2 after DoubleOrderedMap.containsKey (1307), hop 3 after "
               "ExtendedProperties.getProperties (985), hop 4 after MapUtils.getDouble (326), hop 5 after isEmpty (1258). Hops "
               "1-4 land in the outer public class of their file. The hop-5 anchor lies in CursorableSubList, the second, "
               "package-private top-level class of CursorableLinkedList.java (deprecated, extends CursorableLinkedList), so the "
               "gold is declared in org.apache.commons.collections.CursorableSubList; a static method compiles there and its "
               "only caller, hop 4 (MapUtils), is in the same package, so no substitution was needed; the harness's JDK method "
               "catalog lists it as org.apache.commons.collections.CursorableSubList::nthElement. All five files compile with "
               "the added static method; TreeBidiMap, DoubleOrderedMap and MapUtils are not Serializable, CursorableLinkedList "
               "declares its serialVersionUID, and ExtendedProperties (a Hashtable without one) has no serialized-form test. "
               "The facade calls hop 1 by its fully-qualified name; hop 1 imports DoubleOrderedMap; hops 2-5 share the "
               "org.apache.commons.collections package; hop 3 imports java.util.Map and hop 4 java.util.Collection and "
               "java.util.List; the gold uses java.util.Enumeration by its qualified name (CursorableLinkedList.java has no "
               "import for it).",
}
