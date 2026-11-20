"""Main run Lang-30 (C10 recipe on the fixed checkout of Defects4J Lang-30; the real bug modified StringUtils).

Facade: StringUtils.join(Object[], char, int, int) (pool candidate join; containsNone and repeat are taken, abbreviate and
substring have no per-element core to move to a hop, and a containsAny design would repeat the surrogate-pair membership
chain of another instance). The 4-argument char overload holds the whole join computation for a char separator; the
2-argument join(Object[], char) delegates to it, and reverseDelimited(String, char) calls that one, so the chain is reached by
a second production caller. The facade keeps its argument guard (null array -> null) and delegates to a five-hop chain drawn
with the instance seed 2270 (mr_lib preview, draw order, no substitution):
  hop 1 time.DateUtils.textOfRange          decision: an empty range gives the empty String
  hop 2 text.StrBuilder.textOfElements       placement: the initial buffer capacity, estimated from the first element
  hop 3 time.FastDateFormat.elementsText     pass-through
  hop 4 builder.ToStringStyle.separatedText  pass-through
  hop 5 ArrayUtils.concatWith                GOLD: the per-element pass (separator between adjacent elements, each element
                                             appended to the buffer, a null element contributing no text)
The chain performs the original computation in the original order (null-array guard, empty-range check, the same capacity
estimate, the same loop), so the correct configuration is behaviour-preserving for every caller.

Fault (omission in the gold, a special-value skip): the null check around the append is dropped, so a null element is
appended as the text "null". Trigger: the EXISTING test StringUtilsTest::testJoin_ArrayChar, whose assertion
join({null, "", "foo"}, ';') expects ";;foo" and gets "null;;foo". It is the only test that passes a null element through the
char overloads: testJoin_ArrayString / testJoin_Objectarray use the intact String-separator overload, ArrayUtilsTest uses
join(Object[]) (String overload too), and reverseDelimited joins the output of split, which never holds null.

The gold's javadoc states the join contract (the elements of the range joined into a single String with the separator between
adjacent elements) and is silent on null elements. The null rule is pinned outside the gold: the facade's own javadoc ('Null
objects or empty strings within the array are represented by empty strings', example [null, "", "a"], ';' = ";;a"); the
String-separator overload join(Object[], String, int, int) and join(Iterator, char) skip null elements in the same loop
(ObjectUtils.toString maps null to "" for the single-element case); StrBuilder.appendWithSeparators appends a null element as
nothing by default (testAppendWithSeparators_Array: "foo,,baz"). Inside the chain, hop 2 already treats a null first element
specially in its capacity estimate.

Single owner: only the gold visits the elements of the range one by one. Once "null" has been written into the result it cannot
be told apart from an element whose text is "null", so no caller can recover the joined String, and no one-line pre-filter can
map null elements to "" (no element-mapping array utility exists in this code base, and the source level has no lambdas).
Hops 1 and 2 see only the first element. Declared alternatives (G9): hop 2 starts the range after a null first element (";foo"),
hop 1 treats a range that starts with null as empty (""), hop 4 passes ArrayUtils.nullToEmpty(array) (elements unchanged); none
passes the trigger.

Recorded bypasses (one-line edits that pass the full suite but are not repairs consistent with the hop documentation; B-0 at
hop 1 and B-1 at hop 4 were checked on the variant in a scratch copy: full suite, 0 failing tests):
 B-0 the facade, or any of hops 1-4, returns StringUtils.join(array, String.valueOf(separator), startIndex, endIndex) (the
     intact String-separator overload) or new StrBuilder().appendWithSeparators(ArrayUtils.subarray(...), ...), discarding the
     rest of the chain including the gold.
 B-1 a hop above the gold post-processes the joined String with .replace("null", ""): it passes every existing test but deletes
     the text "null" from non-null elements (for example an element "nullable"), so it breaks the join contract every hop states.

Lie: the facade's javadoc claims the range is joined from its end back to its start, inserting each element at the front of
the buffer; the code joins forwards with appends. It names neither null elements nor any hop."""

SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

CAP_DOC = '''/**
 * <p>Joins the elements in a range of an array into a single String,
 * with the separator character between adjacent elements, using a buffer
 * of the given initial capacity.</p>
 *
 * @param array  the array of values to join together, not null
 * @param separator  the separator character to use
 * @param startIndex  the first index to start joining from
 * @param endIndex  the index to stop joining from (exclusive)
 * @param capacity  the initial capacity of the buffer
 * @return the joined String
 */'''

GOLD_TEXT = CAP_DOC + '''
public static String concatWith(Object[] array, char separator, int startIndex, int endIndex, int capacity) {
    final StringBuilder buf = new StringBuilder(capacity);
    for (int i = startIndex; i < endIndex; i++) {
        if (i > startIndex) {
            buf.append(separator);
        }
        final Object item = array[i];
        if (item != null) {
            buf.append(item);
        }
    }
    return buf.toString();
}'''

HOP1 = '''/**
 * <p>Joins the elements in the range <code>[startIndex, endIndex)</code> of
 * an array into a single String, with the separator character between
 * adjacent elements.</p>
 *
 * <p>An empty range gives the empty String.</p>
 *
 * @param array  the array of values to join together, not null
 * @param separator  the separator character to use
 * @param startIndex  the first index to start joining from
 * @param endIndex  the index to stop joining from (exclusive)
 * @return the joined String
 */
public static String textOfRange(Object[] array, char separator, int startIndex, int endIndex) {
    if (endIndex - startIndex <= 0) {
        return "";
    }
    return StrBuilder.textOfElements(array, separator, startIndex, endIndex);
}'''

HOP2 = '''/**
 * <p>Joins the elements in a non-empty range of an array into a single
 * String, with the separator character between adjacent elements.</p>
 *
 * <p>The initial capacity of the buffer is estimated from the length of
 * the first element of the range.</p>
 *
 * @param array  the array of values to join together, not null
 * @param separator  the separator character to use
 * @param startIndex  the first index to start joining from
 * @param endIndex  the index to stop joining from (exclusive), greater
 *  than startIndex
 * @return the joined String
 */
public static String textOfElements(Object[] array, char separator, int startIndex, int endIndex) {
    final Object first = array[startIndex];
    final int capacity = (endIndex - startIndex) * ((first == null ? 16 : first.toString().length()) + 1);
    return FastDateFormat.elementsText(array, separator, startIndex, endIndex, capacity);
}'''

HOP3 = CAP_DOC + '''
public static String elementsText(Object[] array, char separator, int startIndex, int endIndex, int capacity) {
    return ToStringStyle.separatedText(array, separator, startIndex, endIndex, capacity);
}'''

HOP4 = CAP_DOC + '''
public static String separatedText(Object[] array, char separator, int startIndex, int endIndex, int capacity) {
    return ArrayUtils.concatWith(array, separator, startIndex, endIndex, capacity);
}'''

DESIGN = {
 "instance": "Lang-30", "project": "Lang", "bug_id": 30, "seed": 2270,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "join", "near_line": 3158},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/StringUtilsTest.java",
             "test_class": "org.apache.commons.lang3.StringUtilsTest", "test_method": "testJoin_ArrayChar"},
 "expected_signature": "but was:<[null];;foo>",
 "gold": {"method": "concatWith", "text": GOLD_TEXT,
          "fault": {"old": "            if (item != null) {\n"
                           "                buf.append(item);\n"
                           "            }",
                    "new": "            buf.append(item);"}},
 "chain": {
   "facade_body": "if (array == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang3.time.DateUtils.textOfRange(array, separator, startIndex, endIndex);",
   "lie": "The elements are joined from the end of the range back to its start, each element being inserted at the front "
          "of the buffer together with the separator that follows it.",
   "hops": [
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "textOfRange",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "textOfElements",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP2},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "elementsText",
      "imports": ["org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP3},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "separatedText",
      "imports": ["org.apache.commons.lang3.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "concatWith", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.StringUtils::join",
              "org.apache.commons.lang3.text.StrBuilder::appendWithSeparators",
              "org.apache.commons.lang3.ObjectUtils::toString"],
 "ownership_reason": "Only the gold visits the elements of the range one by one; hops 1 and 2 see the range and its first "
                     "element, hops 3 and 4 pass it along. Once a null element has been written as the text 'null' it cannot "
                     "be told apart from an element whose text is 'null', so no caller can recover the joined String, and no "
                     "one-line pre-filter maps null elements to empty text. The convention is pinned outside the gold: the "
                     "facade's javadoc ('Null objects or empty strings within the array are represented by empty strings', "
                     "[null, \"\", \"a\"], ';' = \";;a\"); the String-separator overload join(Object[], String, int, int) and "
                     "join(Iterator, char) skip null elements in the same loop ('if (array[i] != null)'); ObjectUtils.toString "
                     "maps null to the empty String; StrBuilder.appendWithSeparators appends a null element as nothing "
                     "(testAppendWithSeparators_Array expects \"foo,,baz\"); testJoin_ArrayString expects \",,foo\" for the "
                     "same array through the String overload.",
 "ownership_tests": ["org.apache.commons.lang3.StringUtilsTest::testJoin_ArrayString",
                     "org.apache.commons.lang3.StringUtilsTest::testJoin_Objectarray",
                     "org.apache.commons.lang3.StringUtilsTest::testReverseDelimited_StringChar",
                     "org.apache.commons.lang3.text.StrBuilderAppendInsertTest::testAppendWithSeparators_Array",
                     "org.apache.commons.lang3.ObjectUtilsTest::testToString_Object"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "return FastDateFormat.elementsText(array, separator, startIndex, endIndex, capacity);",
      "new": "return FastDateFormat.elementsText(array, separator, first == null ? startIndex + 1 : startIndex, endIndex, capacity);",
      "why": "hop 2 starts the range after a null first element"},
     {"file": DU, "old": "if (endIndex - startIndex <= 0) {",
      "new": "if (endIndex - startIndex <= 0 || array[startIndex] == null) {",
      "why": "hop 1 treats a range that starts with a null element as empty"},
     {"file": TSS, "old": "return ArrayUtils.concatWith(array, separator, startIndex, endIndex, capacity);",
      "new": "return ArrayUtils.concatWith(ArrayUtils.nullToEmpty(array), separator, startIndex, endIndex, capacity);",
      "why": "hop 4 passes the array through ArrayUtils.nullToEmpty"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2270 (mr_lib preview, target org/apache/commons/lang3/StringUtils.java): "
               "time.DateUtils (hop 1), text.StrBuilder (hop 2), time.FastDateFormat (hop 3), builder.ToStringStyle (hop 4), "
               "ArrayUtils (hop 5, gold). All five are public classes in which a static method compiles (ToStringStyle is "
               "abstract, which does not affect a static method); none was skipped. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host.",
}
