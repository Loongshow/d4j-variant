"""Main run Lang-37 (C10 recipe on the fixed checkout of Defects4J Lang-37; the real bug modified ArrayUtils, the target class).

Facade: ArrayUtils.lastIndexOf(Object[], Object) (allowed target 'ArrayUtils.indexOf / lastIndexOf', BATCH3_PREREGISTRATION row
16). Choice among the overloads: the facade must reach exactly one existing test with any change of its result (gate G5).
lastIndexOf(Object[], Object) has no production caller and exactly one test caller, ArrayUtilsTest::testLastIndexOf. The 3-arg
Object overloads (indexOf / lastIndexOf with startIndex) are reached by two or three tests each (the 2-arg overload, contains,
removeElement and their own tests), and every primitive overload is reached by its 2-arg, start-index and contains tests; the only
faults those tests separate are start-index clamps (argument normalisations a caller can pre-filter in one line).
Original computation of the facade (through its 3-arg callee with start index Integer.MAX_VALUE): a null array gives -1; the
search runs from the last element of the array down to the first; a null object is matched against null elements, any other
object with equals; -1 if nothing matches.

Chain (hosts in draw order for the instance seed 3555, mr_lib preview of org/apache/commons/lang3/ArrayUtils.java; none skipped):
  hop 1 time.DateUtils.lastPositionOf           decision: a null array gives -1
  hop 2 builder.ToStringStyle.positionFromEnd   pass-through
  hop 3 time.FastDateFormat.lastPositionWithin  pass-through
  hop 4 text.StrBuilder.lastMatchIn             pass-through
  hop 5 StringUtils.lastOccurrence              GOLD: the whole backward scan, from the last element (array.length - 1) down to
                                                the first (0), with the per-element match
                                                (element == objectToFind || element != null && element.equals(objectToFind))
The gold takes no index: both ends of the scan are the ends of the array itself. The match is the idiom of ObjectUtils.equals
(identity first, then equals on a non-null receiver), so a null object matches a null element. The correct configuration returns
the original result for every input with a well-behaved equals (the original's component-type pre-check only skips objects that a
symmetric equals never matches; it is not carried over).

Fault (omission in the gold's per-element decision): the identity disjunct `element == objectToFind ||` is dropped, so a null
element is never matched and a null object is never found. The variant gold still reads as an ordinary backward scan that skips
null elements before calling equals. Trigger: the EXISTING test ArrayUtilsTest::testLastIndexOf; its assertions on a null array
and on the non-null objects "0".."3" and "notInArray" pass, and the first failing assertion is
assertEquals(4, ArrayUtils.lastIndexOf(array, null)) (array {"0", "1", "2", "3", null, "0"}): expected:<4> but was:<-1>.
No other test reaches the chain.

The gold's javadoc states the idiomatic contract (the index of the last occurrence of the given object in the array) and is
silent on null and on identity. The convention that a null object occurs where the array holds null is pinned outside the gold:
the facade's own javadoc ('@param objectToFind the object to find, may be null'); the intact 3-arg siblings
ArrayUtils.lastIndexOf(Object[], Object, int) and ArrayUtils.indexOf(Object[], Object, int) match a null object against null
elements in their own loops (testLastIndexOfWithStartIndex: lastIndexOf(array, null, 5) == 4; testIndexOf: indexOf(array, null)
== 4; testContains: contains(array, null)); ObjectUtils.equals(null, null) is true (ObjectUtilsTest::testEquals).

Single owner: only the gold visits the elements. Hops 1-4 see the array and the object; the object is passed unchanged and the
gold never matches a null element, so no one-line pre-filter of the object can make a null slot match, no one-line utility of
this code base replaces the null elements of an Object[] (toPrimitive with a null value exists only for the wrapper types; there
is no nullToEmpty for elements), removing a null element shifts every later index, and a -1 result cannot be turned back into a
position without searching again.
Declared alternatives (G9), none passes the trigger:
  hop 1 searches for ObjectUtils.NULL in place of a null object (defaultIfNull);
  hop 3 removes the null element from the array before the search (ArrayUtils.removeElement(array, null)), which moves the
        later "0" from index 5 to index 4;
  hop 4 maps a null object to the empty String.
Recorded bypasses (they discard the gold's result; not competing repairs):
 B-0 the facade, or any of hops 1-4, returns ArrayUtils.lastIndexOf(array, objectToFind, Integer.MAX_VALUE) (the intact 3-arg
     overload) or java.util.Arrays.asList(array).lastIndexOf(objectToFind), discarding the rest of the chain including the gold.
 B-1 one of hops 1-4 answers a null object itself in one line, e.g. hop 4
     `return objectToFind == null ? ArrayUtils.lastIndexOf(array, null, Integer.MAX_VALUE) : StringUtils.lastOccurrence(array, objectToFind);`
     a second search implementation for the null case that replaces the gold's result (the variant with
     ArrayUtils.indexOf(array, null) also passes the single-null trigger array but returns the first null, not the last).
 B-2 a multi-statement copy of the array with the null elements replaced by a sentinel, searched for that sentinel (not one
     line; it also answers a non-null sentinel object at null slots).

Lie: the facade's javadoc gains the sentence that the elements are visited two at a time from the end of the array, the later
element of each pair being compared first; the code visits one element per step. It names neither null, identity, any omitted
step nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold and to the VARIANT gold (the whole method:
javadoc, signature, body, identifiers):
  T1 absent (both): the two parameters both feed the main computation: array gives the scan's start (array.length - 1) and the
     element read array[i]; objectToFind is the identity operand and the equals argument; neither is read only in an argument
     check, and there is no argument check.
  T2 absent (both): locals are i (the cursor, initialised from array.length and decremented every iteration, returned on a match)
     and element (read in the match decision, which decides the live `return i`); no literal-initialised local; the one decision
     is live (the variant's `element != null` guards the equals call and decides whether `return i` runs).
  T3 absent (both): the gold names no class, enum, type code or format; the only special-value treatment is the per-element null
     test, one value with no handled sibling (the object is not an element; an argument normalisation does not form a set with an
     element-level skip); the scan's range has both ends in the text, the upper end array.length - 1 as the start and the lower
     end 0 in the loop condition, and there is no index parameter to clamp.
  T4 absent (both): the javadoc says 'the last occurrence of the given object in the array' (the backward scan returning the
     first match met from the end), 'searched from its last element towards its first' (the loop from array.length - 1 down to
     0) and '-1 if there is none' (the final return); it names no rule, limit, bound, value class or case the body visibly does
     not meet, and makes no null claim. The name lastOccurrence restates the general computation.
The correct gold showed no pattern to rewrite (checked before the omission was chosen)."""

SU = "src/java/org/apache/commons/lang3/StringUtils.java"
AU = "src/java/org/apache/commons/lang3/ArrayUtils.java"
DU = "src/java/org/apache/commons/lang3/time/DateUtils.java"
TSS = "src/java/org/apache/commons/lang3/builder/ToStringStyle.java"
FDF = "src/java/org/apache/commons/lang3/time/FastDateFormat.java"
SB = "src/java/org/apache/commons/lang3/text/StrBuilder.java"

GOLD_TEXT = '''/**
 * <p>Finds the last occurrence of the given object in the array.</p>
 *
 * <p>The array is searched from its last element towards its first.</p>
 *
 * @param array  the array to search through
 * @param objectToFind  the object to find
 * @return the index of the last occurrence of the object in the array,
 *  -1 if there is none
 */
public static int lastOccurrence(Object[] array, Object objectToFind) {
    for (int i = array.length - 1; i >= 0; i--) {
        final Object element = array[i];
        if (element == objectToFind || element != null && element.equals(objectToFind)) {
            return i;
        }
    }
    return -1;
}'''

HOP1 = '''/**
 * <p>Finds the last index of the given object within an array.</p>
 *
 * <p>A <code>null</code> array gives -1.</p>
 *
 * @param array  the array to search through, may be <code>null</code>
 * @param objectToFind  the object to find
 * @return the last index of the object within the array, -1 if it is
 *  not found or the array is <code>null</code>
 */
public static int lastPositionOf(Object[] array, Object objectToFind) {
    if (array == null) {
        return -1;
    }
    return ToStringStyle.positionFromEnd(array, objectToFind);
}'''

LAST_DOC = '''/**
 * <p>Finds the last index of the given object within an array.</p>
 *
 * @param array  the array to search through, not null
 * @param objectToFind  the object to find
 * @return the last index of the object within the array, -1 if it is
 *  not found
 */'''

HOP2 = LAST_DOC + '''
public static int positionFromEnd(Object[] array, Object objectToFind) {
    return FastDateFormat.lastPositionWithin(array, objectToFind);
}'''

HOP3 = LAST_DOC + '''
public static int lastPositionWithin(Object[] array, Object objectToFind) {
    return StrBuilder.lastMatchIn(array, objectToFind);
}'''

HOP4 = LAST_DOC + '''
public static int lastMatchIn(Object[] array, Object objectToFind) {
    return StringUtils.lastOccurrence(array, objectToFind);
}'''

DESIGN = {
 "instance": "Lang-37", "project": "Lang", "bug_id": 37, "seed": 3555,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "lastIndexOf", "near_line": 1248},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang3/ArrayUtilsTest.java",
             "test_class": "org.apache.commons.lang3.ArrayUtilsTest", "test_method": "testLastIndexOf"},
 "expected_signature": "expected:<4> but was:<-1>",
 "gold": {"method": "lastOccurrence", "text": GOLD_TEXT,
          "fault": {"old": "            final Object element = array[i];\n"
                           "            if (element == objectToFind || element != null && element.equals(objectToFind)) {",
                    "new": "            final Object element = array[i];\n"
                           "            if (element != null && element.equals(objectToFind)) {"}},
 "chain": {
   "facade_body": "return org.apache.commons.lang3.time.DateUtils.lastPositionOf(array, objectToFind);",
   "lie": "The elements are visited two at a time from the end of the array towards its start, the later element of each "
          "pair being compared with the object first.",
   "hops": [
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "lastPositionOf",
      "imports": ["org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "positionFromEnd",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP2},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "lastPositionWithin",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"], "text": HOP3},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "lastMatchIn",
      "imports": ["org.apache.commons.lang3.StringUtils"], "text": HOP4},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "lastOccurrence", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.ArrayUtils::lastIndexOf",
              "org.apache.commons.lang3.ArrayUtils::indexOf",
              "org.apache.commons.lang3.ObjectUtils::equals"],
 "ownership_reason": "Only the gold visits the elements of the array; hop 1 checks the array reference, hops 2-4 pass the array "
                     "and the object along unchanged. The gold never matches a null element, so no one-line pre-filter of the "
                     "object can make a null slot match, no one-line utility of this code base replaces the null elements of an "
                     "Object[], removing a null element shifts every later index, and a -1 result cannot be turned back into a "
                     "position without searching again. The convention is pinned outside the gold: the facade's javadoc ('the "
                     "object to find, may be null'); the 3-arg overloads ArrayUtils.lastIndexOf(Object[], Object, int) and "
                     "ArrayUtils.indexOf(Object[], Object, int) match a null object against null elements "
                     "(testLastIndexOfWithStartIndex: lastIndexOf(array, null, 5) == 4; testIndexOf: indexOf(array, null) == 4; "
                     "testContains: contains(array, null)); ObjectUtils.equals(null, null) is true (ObjectUtilsTest.testEquals). "
                     "The gold's javadoc promises the last occurrence of the given object in the array, which for the trigger's "
                     "null object is index 4.",
 "ownership_tests": ["org.apache.commons.lang3.ArrayUtilsTest::testLastIndexOfWithStartIndex",
                     "org.apache.commons.lang3.ArrayUtilsTest::testIndexOf",
                     "org.apache.commons.lang3.ArrayUtilsTest::testContains",
                     "org.apache.commons.lang3.ObjectUtilsTest::testEquals"],
 "compensating": {
   "chain": [
     {"file": DU, "old": "return ToStringStyle.positionFromEnd(array, objectToFind);",
      "new": "return ToStringStyle.positionFromEnd(array, org.apache.commons.lang3.ObjectUtils.defaultIfNull(objectToFind, org.apache.commons.lang3.ObjectUtils.NULL));",
      "why": "hop 1 searches for ObjectUtils.NULL in place of a null object"},
     {"file": FDF, "old": "return StrBuilder.lastMatchIn(array, objectToFind);",
      "new": "return StrBuilder.lastMatchIn(org.apache.commons.lang3.ArrayUtils.removeElement(array, null), objectToFind);",
      "why": "hop 3 removes the null element from the array before the search"},
     {"file": SB, "old": "return StringUtils.lastOccurrence(array, objectToFind);",
      "new": "return StringUtils.lastOccurrence(array, objectToFind == null ? \"\" : objectToFind);",
      "why": "hop 4 maps a null object to the empty String"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 3555 (mr_lib preview, target org/apache/commons/lang3/ArrayUtils.java): "
               "time.DateUtils (hop 1, anchor after iterator), builder.ToStringStyle (hop 2, anchor after appendToString), "
               "time.FastDateFormat (hop 3, anchor after getTimeZoneOverridesCalendar), text.StrBuilder (hop 4, anchor after "
               "append), StringUtils (hop 5, gold, anchor after isAllLowerCase). All five are public top-level classes in which "
               "a static method compiles (ToStringStyle is abstract, which does not affect a static method); none was skipped. "
               "The facade calls hop 1 by its fully-qualified name; each hop imports the next host.",
}
