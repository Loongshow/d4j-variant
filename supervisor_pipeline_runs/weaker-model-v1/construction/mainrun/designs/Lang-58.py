"""Main run Lang-58 (C10 recipe on the fixed checkout of Defects4J Lang-58; the real bug modified math.NumberUtils, the target
class).

Facade: math.NumberUtils.compare(float, float), the batch-3 allowed target (BATCH3_PREREGISTRATION.md: Lang-58 ->
NumberUtils.compare). The float overload carries the chain; the double overload stays unchanged and serves as an external
pin. For the float overload, the order of two NEGATIVE float values
is asserted only by math.NumberUtilsTest::testCompareFloat (CompareToBuilderTest::testFloat compares only positive floats,
NaN and infinities against positive values, and passes doubles for its zero lines; MutableFloatTest::testCompareTo compares 0f
with -1f and 1f; the Range containsFloat tests use positive bounds), so a change confined to negative pairs fails only that test
(gate G5).

Original computation: the relational operators order the values where they can; the remaining pairs are ordered by their
floatToIntBits patterns. The chain computes the same order through a per-value sort key: the key of a value is its
floatToIntBits pattern, with the 31 low bits inverted when the sign bit is set (bits ^ Integer.MAX_VALUE), so that comparing the
keys as ints gives the facade's documented order (NaN above +infinity; +0.0 above -0.0; among negative values the one nearer
zero above). The correct configuration is behaviour-preserving for every input: checked in a scratch harness against the
original body on 16,152,361 ordered pairs (the special values, the canonical and two non-canonical NaN patterns, +/-MIN_VALUE,
+/-MIN_NORMAL, +/-MAX_VALUE and 4,000 random bit patterns): 0 mismatches.

Chain (hosts in draw order for seed 5162, mr_lib preview, none skipped):
  hop 1 builder.ToStringStyle.orderValues   pass-through (documented: order by sort keys)
  hop 2 StringUtils.orderByKey              pass-through
  hop 3 ArrayUtils.keyOrder                 pass-through
  hop 4 time.FastDateFormat.compareKeys     aggregation: the sort key of each of the two values, compared as ints (lower key
                                            first, same key -> 0)
  hop 5 text.StrBuilder.keyOf               GOLD: the per-value sort key (bit pattern, low bits inverted for a set sign bit)

Fault (one-step omission in the gold): the step `if (bits < 0) { bits ^= Integer.MAX_VALUE; }` is dropped, so the key of a
negative value is its raw bit pattern; raw patterns of negative floats grow with the magnitude, so among negative values the
order is reversed (keys of non-negative values, NaN and the -0.0 / 0.0 pair keep their order). Trigger: the EXISTING test
math.NumberUtilsTest::testCompareFloat; its first failing assertion is assertTrue(NumberUtils.compare(-0.0f, -1.2f) == +1) at
NumberUtilsTest.java:1132 (junit AssertionFailedError); lines 1076-1131 (NaN, infinities, positive values, zeros, mixed signs)
still pass. The gold's javadoc states the idiomatic contract (the sort key of a value; values are put in order by comparing
their keys) and is silent on the sign step; -0.0 is above -1.2 in the documented order, so the omission violates that contract
on the trigger input.

External pins (convention outside the gold): the facade's own javadoc lists the order largest to smallest (normal negative
numbers above -MAX_VALUE above negative infinity); the double overload math.NumberUtils.compare(double, double) orders negative
doubles by value (math.NumberUtilsTest::testCompareDouble passes on the variant); the deprecated
org.apache.commons.lang.NumberUtils.compare(float, float) orders negative floats the same way (lang.NumberUtilsTest::
testCompareFloat passes); CompareToBuilder.append(float, float) is a production caller of the facade
(CompareToBuilderTest::testFloat passes: NEGATIVE_INFINITY before MIN_VALUE goes through the chain); MutableFloat.compareTo is
a second production caller (MutableFloatTest::testCompareTo: 0f after -1f).

Single owner: only the gold looks at a single value and gives it its key; hops 1-3 pass the pair on, all documented as ordering
by sort keys, and hop 4 compares the two keys it is given (its javadoc fixes lower key first, same key -> 0). Hop 4 cannot
restore the order with one line: each key line transforms one side only, and a single comparison line cannot reorder both
directions. Declared one-line alternatives (G9), each covering one direction or one side only: hop 1 answers -1 when the
relational operators find lhs less (fails line 1132); hop 3 answers +1 when they find lhs greater (passes 1132, fails 1141);
hop 4 inverts the low bits of lhs's key when it is negative (fails line 1131, -0.0f against itself). Failing lines checked
in scratch copies of the variant.
Recorded bypasses (not declared; they pass the trigger and the full suite and discard the gold's key; B-1 at hop 3 in the
form below was checked on the variant in a scratch copy: full suite, 0 failing tests):
 B-0 the facade or any of hops 1-3 returns Float.compare(lhs, rhs), new Float(lhs).compareTo(new Float(rhs)),
     NumberUtils.compare((double) lhs, (double) rhs) or the deprecated org.apache.commons.lang.NumberUtils.compare(lhs, rhs),
     making the rest of the chain dead.
 B-1 one of hops 1-3 answers with the relational operators in both directions before delegating, e.g.
     `return lhs < rhs ? -1 : lhs > rhs ? +1 : FastDateFormat.compareKeys(lhs, rhs);` at hop 3. This orders every pair the
     operators can order without the keys (contradicting the hop's own javadoc, 'by their sort keys') and leaves only NaN and
     -0.0 / 0.0 pairs to the keys, whose raw bit patterns happen to order them; the gold's key still does not sort negative
     values.

Lie: the facade's javadoc claims the order is read from the difference of the two values, computed first; the code computes no
difference. It names neither the sign, keys nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md). CORRECT gold (before choosing the omission): T1 absent (`value` feeds
`bits`, which is returned), T2 absent (`bits` is returned; the one decision changes it), T3 absent (no enumerated or closed set,
the javadoc names no value class), T4 absent (the javadoc names no concrete rule, limit, value class or case). VARIANT gold:
 T1 absent: the only parameter `value` is read in `Float.floatToIntBits(value)`, whose result is the return value.
 T2 absent: the one local `bits` is initialised from the parameter (not a literal) and returned; the gold has no branch, case or
    ternary, so there is no dead decision; there is no loop.
 T3 absent: no special value or member of any set is treated at all (no NaN, infinity, zero or sign test); the gold has one
    parameter, so no pair halves or range ends; the javadoc names no class ('finite', 'special values', 'negative', ...).
 T4 absent: the javadoc's phrases ('the sort key of a float value', 'values are put in order by comparing their keys', '@return
    the sort key of the value') are a general description of what the method computes, which the body addresses (it returns an
    int key derived from the value); they name no concrete rule, limit, bound, value class or case.
"""

SU = "src/java/org/apache/commons/lang/StringUtils.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
NU = "src/java/org/apache/commons/lang/math/NumberUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"

GOLD_TEXT = '''/**
 * <p>Returns the sort key of a <code>float</code> value.</p>
 *
 * <p>Values are put in order by comparing their keys.</p>
 *
 * @param value  the value
 * @return the sort key of the value
 */
public static int keyOf(float value) {
    int bits = Float.floatToIntBits(value);
    if (bits < 0) {
        bits ^= Integer.MAX_VALUE;
    }
    return bits;
}'''

BY_KEY_DOC = '''/**
 * <p>Compares two <code>float</code> values for order, by their sort
 * keys.</p>
 *
 * @param lhs  the first value
 * @param rhs  the second value
 * @return <code>-1</code> if lhs comes before rhs, <code>+1</code> if it
 *  comes after, <code>0</code> if neither
 */'''

HOP1 = BY_KEY_DOC + '''
public static int orderValues(float lhs, float rhs) {
    return StringUtils.orderByKey(lhs, rhs);
}'''

HOP2 = BY_KEY_DOC + '''
public static int orderByKey(float lhs, float rhs) {
    return ArrayUtils.keyOrder(lhs, rhs);
}'''

HOP3 = BY_KEY_DOC + '''
public static int keyOrder(float lhs, float rhs) {
    return FastDateFormat.compareKeys(lhs, rhs);
}'''

HOP4 = '''/**
 * <p>Compares two <code>float</code> values by their sort keys.</p>
 *
 * <p>The value with the lower key comes first; values with the same
 * key come neither before nor after each other.</p>
 *
 * @param lhs  the first value
 * @param rhs  the second value
 * @return <code>-1</code> if lhs has the lower key, <code>+1</code> if
 *  the higher, <code>0</code> if the same
 */
public static int compareKeys(float lhs, float rhs) {
    int lhsKey = StrBuilder.keyOf(lhs);
    int rhsKey = StrBuilder.keyOf(rhs);
    if (lhsKey < rhsKey) {
        return -1;
    }
    if (lhsKey > rhsKey) {
        return +1;
    }
    return 0;
}'''

DESIGN = {
 "instance": "Lang-58", "project": "Lang", "bug_id": 58, "seed": 5162,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": NU, "class": "org.apache.commons.lang.math.NumberUtils", "method": "compare", "near_line": 1465},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/math/NumberUtilsTest.java",
             "test_class": "org.apache.commons.lang.math.NumberUtilsTest", "test_method": "testCompareFloat"},
 "expected_signature": "testCompareFloat(NumberUtilsTest.java:1132)",
 "gold": {"method": "keyOf", "text": GOLD_TEXT,
          "fault": {"old": "        int bits = Float.floatToIntBits(value);\n"
                           "        if (bits < 0) {\n"
                           "            bits ^= Integer.MAX_VALUE;\n"
                           "        }\n"
                           "        return bits;",
                    "new": "        int bits = Float.floatToIntBits(value);\n"
                           "        return bits;"}},
 "chain": {
   "facade_body": "return org.apache.commons.lang.builder.ToStringStyle.orderValues(lhs, rhs);",
   "lie": "The difference of the two values is computed first, and the order is read from that difference before any "
          "other test is made.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "orderValues",
      "imports": ["org.apache.commons.lang.StringUtils"], "text": HOP1},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "orderByKey",
      "imports": [], "text": HOP2},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "keyOrder",
      "imports": ["org.apache.commons.lang.time.FastDateFormat"], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "compareKeys",
      "imports": ["org.apache.commons.lang.text.StrBuilder"], "text": HOP4},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "keyOf", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.math.NumberUtils::compare",
              "org.apache.commons.lang.NumberUtils::compare",
              "org.apache.commons.lang.builder.CompareToBuilder::append",
              "org.apache.commons.lang.mutable.MutableFloat::compareTo"],
 "ownership_reason": "Only the gold looks at one value at a time and gives it its sort key; hops 1-3 pass the pair on (each "
                     "documented as ordering by sort keys) and hop 4 compares the two keys it is given (lower key first, the "
                     "same key gives 0, as its javadoc states). Once negative values receive their raw bit patterns as keys, "
                     "their order is reversed, and a hop above can only restore it by ordering the pair without the keys. "
                     "The convention is pinned outside the gold: the facade's javadoc lists the order largest to smallest "
                     "(normal negative numbers above -MAX_VALUE above negative infinity); the double overload of compare "
                     "orders negative doubles by value (testCompareDouble passes); the deprecated "
                     "org.apache.commons.lang.NumberUtils.compare(float, float) orders negative floats the same way (its "
                     "testCompareFloat passes); CompareToBuilder.append(float, float) is a production caller of the facade "
                     "(testFloat passes), and MutableFloat.compareTo is a second production caller (testCompareTo passes).",
 "ownership_tests": ["org.apache.commons.lang.math.NumberUtilsTest::testCompareDouble",
                     "org.apache.commons.lang.NumberUtilsTest::testCompareFloat",
                     "org.apache.commons.lang.builder.CompareToBuilderTest::testFloat",
                     "org.apache.commons.lang.builder.CompareToBuilderTest::testDouble",
                     "org.apache.commons.lang.mutable.MutableFloatTest::testCompareTo"],
 "compensating": {
   "chain": [
     {"file": TSS, "old": "        return StringUtils.orderByKey(lhs, rhs);",
      "new": "        return lhs < rhs ? -1 : StringUtils.orderByKey(lhs, rhs);",
      "why": "hop 1 answers -1 when the relational operators find lhs less"},
     {"file": AU, "old": "        return FastDateFormat.compareKeys(lhs, rhs);",
      "new": "        return lhs > rhs ? +1 : FastDateFormat.compareKeys(lhs, rhs);",
      "why": "hop 3 answers +1 when the relational operators find lhs greater"},
     {"file": FDF, "old": "        int lhsKey = StrBuilder.keyOf(lhs);",
      "new": "        int lhsKey = StrBuilder.keyOf(lhs) ^ (StrBuilder.keyOf(lhs) >> 31 & Integer.MAX_VALUE);",
      "why": "hop 4 inverts the low bits of lhs's key when the key is negative"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 5162 (mr_lib preview, target org/apache/commons/lang/math/NumberUtils.java): "
               "builder.ToStringStyle (hop 1), StringUtils (hop 2), ArrayUtils (hop 3), time.FastDateFormat (hop 4), "
               "text.StrBuilder (hop 5, gold). All five are public classes in which a static method compiles (ToStringStyle "
               "is abstract, which does not affect a static method); none was skipped. The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host where it is in another package (StringUtils and "
               "ArrayUtils share a package).",
}
