"""Main run Lang-35 (C10 recipe on the fixed checkout of Defects4J Lang-35; the real bug modified ArrayUtils, the target class).

Facade: ArrayUtils.toMap(Object[]) (allowed batch-3 target, pool candidate 1). The other allowed targets were set aside:
addAll(T[], T...) has no per-element step (two arraycopy calls), so its only omissions are a missing half of the array pair (a
visible one-of-two) or the incompatible-type translation, which leaves a catch that only rethrows (a dead decision); and
subarray(T[], int, int) splits into two index clamps (range ends) and a copy, where every omission is either a one-of-two clamp,
a negative-size exception, or a one-line clamp that any hop above can add. toMap has exactly one test caller
(ArrayUtilsTest::testToMap) and no production caller, so a change of its behaviour fails only that test (gate G5).
Original computation: a null array gives null; a HashMap with initial capacity length * 1.5; for each element, a Map.Entry gives
its key and value, an Object[] gives its first two elements (IllegalArgumentException if it has fewer than two), and any other
element (including null) is rejected with IllegalArgumentException.

Chain (hosts in draw order for seed 4621, mr_lib preview, target org/apache/commons/lang3/ArrayUtils.java, no substitution):
  facade ArrayUtils.toMap                 guard (null array -> null), then one call to hop 1
  hop 1 time.DateUtils.mapOf              placement: the new map with the initial capacity length * 1.5
  hop 2 builder.ToStringStyle.fillMap     placement: the whole array as the range [0, length)
  hop 3 time.FastDateFormat.fillMapRange  pass-through
  hop 4 text.StrBuilder.putRange          pass-through
  hop 5 StringUtils.putAll                GOLD: the per-element pass over the range (a Map.Entry gives its key and value; an
                                          Object[] gives its first two items, a shorter one rejected; any other element
                                          rejected)
The correct configuration performs the original computation in the original order (null guard, same capacity, same loop over
[0, length), same dispatch, the same exception type for every rejected element), so it is behaviour-preserving for every caller.

Fault (omission in the gold): the length step of the Object[] branch, `if (items.length < 2) { throw new
IllegalArgumentException(...); }`, is dropped. An Object[] element with fewer than two items then reaches items[1].
Trigger: the EXISTING test ArrayUtilsTest::testToMap. Its first block passes (two String[] pairs put and read back) and so does
toMap(null); ArrayUtils.toMap(new String[][] {{"foo", "bar"}, {"short"}}) at ArrayUtilsTest.java:210 then fails with
java.lang.ArrayIndexOutOfBoundsException (Index 1 out of bounds for length 1) thrown by the array read inside the gold, where the
test expects IllegalArgumentException. The stack trace lists the whole path (facade, hops 1-4) with the gold as the deepest
project frame; the gold also runs and returns the right map on the first block before the failure.

Quiet gold: its javadoc states the conversion contract (the key and the value held by each element of the range are put into the
map) and is silent on short arrays. The gold is the only method that reads inside an element, it already rejects a malformed
element (one that is neither a Map.Entry nor an Object[]) with IllegalArgumentException, and an array with one item holds no
value; letting a raw ArrayIndexOutOfBoundsException escape from the element read breaks the idiomatic contract that the library
applies everywhere else.

External pins (the convention outside the gold's javadoc):
 - the facade's own javadoc: '@throws IllegalArgumentException if one element of this Array is itself an Array containing less
   then two elements';
 - ArrayUtils.addAll(T[], T...): the low-level ArrayStoreException of the copy is translated into IllegalArgumentException
   (ArrayUtilsAddTest::testJira567);
 - BooleanUtils.xor(boolean[]): an array too short to compute from is rejected with IllegalArgumentException before any element is
   read (BooleanUtilsTest::testXor_primitive_emptyInput);
 - NumberUtils.min(long[]): an empty array is rejected with IllegalArgumentException before array[0] is read
   (NumberUtilsTest::testMinLong).

Single owner: only the gold indexes into an element; hops 1-4 see the array as a whole (allocation, range placement,
pass-through) and never read an element. The failure is raised inside the gold's own element read, so no hop can turn it into
the documented IllegalArgumentException with a one-line edit that keeps the chain as documented: a catch needs a block, and a
check before the call must re-implement the per-element step (visit every element, test its kind and its length) in a method that
never reads elements.
Declared alternatives (G9; none absorbs the fault):
 - hop 1 rejects null elements (Validate.noNullElements inside the capacity expression): the short array still reaches the gold;
 - hop 2 copies the elements into an array of arrays with ArrayUtils.addAll(new Object[0][], array): the short String[] is an
   Object[] and is copied unchanged;
 - hop 3 rejects a range whose FIRST element is an array shorter than two (Validate.isTrue): the trigger's short array is second.
Recorded bypasses (not declared; each answers short arrays outside the only method that reads elements, and the gold itself
still reads past the end of a short array when it is reached):
 B-0 the facade, or any of hops 1-4, re-implements the whole conversion loop (the original toMap body), discarding the rest of the
     chain including the gold.
 B-1 a loop at the facade or at a hop (before the call) that visits every element and rejects an Object[] shorter than two: a
     second implementation of part of the gold's per-element step, split from the kind rejection that stays in the gold.
 B-2 a hop wraps the call in try/catch and rethrows ArrayIndexOutOfBoundsException as IllegalArgumentException: multi-statement,
     and it converts the gold's failure instead of preventing it.
 B-3 a hop rejects only the LAST element of the range when it is an array shorter than two: passes testToMap (whose short array
     is last) but still lets {{"x"}, {"a", "b"}} reach the gold; test-fitted, not a repair.
 B-1 and B-2 were checked at hop 4 on the variant in a scratch copy: the trigger passes and the full suite has 0 failing tests, as
 expected for edits that answer short arrays outside the gold.

Lie: the facade's javadoc claims the pairs are first sorted by the hash codes of their keys and the map is filled from the sorted
pairs in a single pass; the code sorts nothing and fills the map in array order. It names neither array lengths, nor the omitted
step, nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first, then to the WHOLE variant gold:
 Correct gold: T1 absent (map, array, start, end all reach the result); T2 absent (element, entry, items and i live; nothing
 frozen; the three branches have distinct effects and the length test throws); T3 absent (both named kinds, Map.Entry and
 Object[], are put, everything else rejected; key and value both put in both branches; start and end both bound the loop,
 neither clamped); T4 absent (no concrete phrase in the javadoc; the message bounds 'less than 2' and 'neither of type Map.Entry
 nor of type Object[]' match their tests). The rejection message names the two kinds exactly (Object[], not "an Array"), so no
 message names a wider class than the dispatch handles; the local holding an Object[] element is named `items`, a name that
 claims no length.
 Variant gold:
 - T1 absent: map is written and returned, array is indexed for each element, start and end bound the loop, so every parameter
   changes the result; none is read only in an argument check.
 - T2 absent: element is tested and read into the cast or the message; entry and items feed map.put; the cursor i advances in the
   loop update and is used to index and in the message; no literal-initialised local; the three branches (put entry, put items,
   throw) have distinct effects; no empty or constant decision.
 - T3 absent: the dispatch is complete (Map.Entry, Object[], and a final else for every other element); both kinds named in the
   message are handled; key and value halves are both put in each branch; start and end are both used and neither is clamped; there
   is no element-level special-value test at all, so no sibling is left out.
 - T4 absent: the javadoc says 'Puts the key and the value held by each element in a range of an array into a map' (a general
   description that the two put branches address), the @param 'not null' clauses are caller preconditions, '@return the map' is
   met by 'return map;'; there is no @throws clause and no named limit, bound or value class; the only message is thrown exactly
   on the path its text names."""

AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"

GOLD_TEXT = '''/**
 * <p>Puts the key and the value held by each element in a range of an
 * array into a map.</p>
 *
 * @param map  the map to put the keys and values into, not null
 * @param array  the array of elements, not null
 * @param start  the index of the first element of the range
 * @param end  the index after the last element of the range
 * @return the map
 */
public static Map<Object, Object> putAll(Map<Object, Object> map, Object[] array, int start, int end) {
    for (int i = start; i < end; i++) {
        final Object element = array[i];
        if (element instanceof Map.Entry<?, ?>) {
            final Map.Entry<?, ?> entry = (Map.Entry<?, ?>) element;
            map.put(entry.getKey(), entry.getValue());
        } else if (element instanceof Object[]) {
            final Object[] items = (Object[]) element;
            if (items.length < 2) {
                throw new IllegalArgumentException("Array element " + i + ", '"
                    + element + "', has a length less than 2");
            }
            map.put(items[0], items[1]);
        } else {
            throw new IllegalArgumentException("Array element " + i + ", '"
                + element + "', is neither of type Map.Entry nor of type Object[]");
        }
    }
    return map;
}'''

HOP1 = '''/**
 * <p>Converts an array into a {@link java.util.Map}, putting the key and
 * the value held by each element of the array into a new map.</p>
 *
 * <p>The map is created with an initial capacity of one and a half
 * times the length of the array.</p>
 *
 * @param array  the array to convert, not null
 * @return a new map holding the keys and values of the elements
 */
public static Map<Object, Object> mapOf(Object[] array) {
    final Map<Object, Object> map = new HashMap<Object, Object>((int) (array.length * 1.5));
    return ToStringStyle.fillMap(map, array);
}'''

HOP2 = '''/**
 * <p>Puts the key and the value held by each element of an array into
 * a map.</p>
 *
 * <p>All of the array is used, from its first element to its last.</p>
 *
 * @param map  the map to fill, not null
 * @param array  the array of elements, not null
 * @return the map
 */
public static Map<Object, Object> fillMap(Map<Object, Object> map, Object[] array) {
    return FastDateFormat.fillMapRange(map, array, 0, array.length);
}'''

HOP3 = '''/**
 * <p>Puts the key and the value held by each element between two
 * indices of an array into a map.</p>
 *
 * @param map  the map to fill, not null
 * @param array  the array of elements, not null
 * @param start  the index of the first element to use
 * @param end  the index after the last element to use
 * @return the map
 */
public static Map<Object, Object> fillMapRange(Map<Object, Object> map, Object[] array, int start, int end) {
    return StrBuilder.putRange(map, array, start, end);
}'''

HOP4 = '''/**
 * <p>Puts the keys and the values held by the elements of a range of an
 * array into a map, in the order of the range.</p>
 *
 * @param map  the map to put into, not null
 * @param array  the array holding the range, not null
 * @param start  the index where the range starts
 * @param end  the index where the range ends, exclusive
 * @return the map
 */
public static Map<Object, Object> putRange(Map<Object, Object> map, Object[] array, int start, int end) {
    return StringUtils.putAll(map, array, start, end);
}'''

DESIGN = {
 "instance": "Lang-35", "project": "Lang", "bug_id": 35, "seed": 4621,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "toMap", "near_line": 223},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/ArrayUtilsTest.java",
             "test_class": "org.apache.commons.lang3.ArrayUtilsTest", "test_method": "testToMap"},
 "expected_signature": "java.lang.ArrayIndexOutOfBoundsException: Index 1 out of bounds for length 1",
 "gold": {"method": "putAll", "text": GOLD_TEXT,
          "fault": {"old": "                final Object[] items = (Object[]) element;\n"
                           "                if (items.length < 2) {\n"
                           "                    throw new IllegalArgumentException(\"Array element \" + i + \", '\"\n"
                           "                        + element + \"', has a length less than 2\");\n"
                           "                }\n"
                           "                map.put(items[0], items[1]);",
                    "new": "                final Object[] items = (Object[]) element;\n"
                           "                map.put(items[0], items[1]);"}},
 "chain": {
   "facade_body": "if (array == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang3.time.DateUtils.mapOf(array);",
   "lie": "The pairs are first sorted by the hash codes of their keys, and the map is then filled from the sorted pairs "
          "in a single pass.",
   "hops": [
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "mapOf",
      "imports": ["java.util.HashMap", "java.util.Map", "org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "fillMap",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP2},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "fillMapRange",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"], "text": HOP3},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "putRange",
      "imports": ["java.util.Map", "org.apache.commons.lang3.StringUtils"], "text": HOP4},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "putAll",
      "imports": ["java.util.Map"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.ArrayUtils::addAll",
              "org.apache.commons.lang3.BooleanUtils::xor",
              "org.apache.commons.lang3.math.NumberUtils::min"],
 "ownership_reason": "Only the gold reads inside an element: it dispatches on the element's kind (Map.Entry, Object[]) and "
                     "indexes the items of an Object[] element; hops 1-4 allocate the map, place the whole array as the "
                     "range and pass it along, and never read an element. The gold already rejects a malformed element of "
                     "another kind (neither a Map.Entry nor an Object[]) with IllegalArgumentException, but reads items[1] of "
                     "an Object[] without first checking that it holds two items, so an array with a single item escapes as "
                     "a raw ArrayIndexOutOfBoundsException from the gold's own element read; no hop can turn that into the "
                     "documented IllegalArgumentException in one line without re-implementing the per-element step (a "
                     "pre-scan of every element) or catching the gold's failure (a block). The convention is pinned outside "
                     "the gold: the facade's javadoc ('@throws IllegalArgumentException if one element of this Array is "
                     "itself an Array containing less then two elements'); ArrayUtils.addAll translates the low-level "
                     "ArrayStoreException of its copy into IllegalArgumentException (ArrayUtilsAddTest.testJira567); "
                     "BooleanUtils.xor(boolean[]) and NumberUtils.min(long[]) reject an array too short to compute from with "
                     "IllegalArgumentException before reading an element (BooleanUtilsTest.testXor_primitive_emptyInput, "
                     "NumberUtilsTest.testMinLong).",
 "ownership_tests": ["org.apache.commons.lang3.ArrayUtilsAddTest::testJira567",
                     "org.apache.commons.lang3.BooleanUtilsTest::testXor_primitive_emptyInput",
                     "org.apache.commons.lang3.math.NumberUtilsTest::testMinLong"],
 "compensating": {
   "chain": [
     {"file": DU, "old": "final Map<Object, Object> map = new HashMap<Object, Object>((int) (array.length * 1.5));",
      "new": "final Map<Object, Object> map = new HashMap<Object, Object>((int) (org.apache.commons.lang3.Validate.noNullElements(array).length * 1.5));",
      "why": "hop 1 rejects null elements before allocating the map"},
     {"file": TSS, "old": "return FastDateFormat.fillMapRange(map, array, 0, array.length);",
      "new": "return FastDateFormat.fillMapRange(map, org.apache.commons.lang3.ArrayUtils.addAll(new Object[0][], array), 0, array.length);",
      "why": "hop 2 copies the elements into an array of arrays before placing the range"},
     {"file": FDF, "old": "return StrBuilder.putRange(map, array, start, end);",
      "new": "Validate.isTrue(start == end || !(array[start] instanceof Object[]) || ((Object[]) array[start]).length >= 2); "
             "return StrBuilder.putRange(map, array, start, end);",
      "why": "hop 3 rejects a range whose first element is an array shorter than two"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4621 (mr_lib preview, target org/apache/commons/lang3/ArrayUtils.java): "
               "time.DateUtils (hop 1, anchor after round), builder.ToStringStyle (hop 2, anchor after appendEnd), "
               "time.FastDateFormat (hop 3, anchor after format), text.StrBuilder (hop 4, anchor after appendln), StringUtils "
               "(hop 5, gold, anchor after replaceChars). All five are public top-level classes in which a public static method "
               "compiles (ToStringStyle is abstract, which does not affect a static method); none was skipped. The facade calls "
               "hop 1 by its fully-qualified name; each hop imports the next host (and java.util.Map / HashMap where the host "
               "lacked them).",
}
