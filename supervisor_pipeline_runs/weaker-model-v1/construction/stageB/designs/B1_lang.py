"""Stage B bug B1 (Lang): StringUtils.indexOfAnyBut(CharSequence, char...). Gold = the per-position membership test; the fault
omits the comparison of the second unit of a surrogate pair, so a supplementary character that IS in the search set counts as
outside it. Trigger: StringUtilsEqualsIndexOfTest::testIndexOfAnyBut_StringCharArrayWithSupplementaryChars (expected 2, got 0).
The pair convention is stated in no javadoc; it is pinned by indexOfAny's explicit pair logic, the separate CharSequence overload
of indexOfAnyBut, the supplementary-character tests, and containsOnly (a passing second production caller of the facade).
Odd hop = the pair-start predicate written with a triple negation (De Morgan) instead of isHighSurrogate."""
GOLD_TEXT = '''/**
 * <p>Checks whether the character at an index of a CharSequence is one of
 * a set of characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param index  the index of the character to check
 * @param searchChars  the chars to search for, not null or empty
 * @param pair  whether the character at the index is the first unit of a
 *  surrogate pair
 * @return {@code true} if the character is one of the search chars
 */
public static boolean isAnyOf(final CharSequence cs, final int index, final char[] searchChars, final boolean pair) {
    final char ch = cs.charAt(index);
    final int searchLast = searchChars.length - 1;
    for (int j = 0; j <= searchLast; j++) {
        if (searchChars[j] == ch) {
            if (!pair || j == searchLast) {
                return true;
            }
            if (searchChars[j + 1] == cs.charAt(index + 1)) {
                return true;
            }
        }
    }
    return false;
}'''
PAIR_DOC = '''/**
 * <p>Checks whether the character at an index of a CharSequence is the
 * first unit of a surrogate pair.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param index  the index of the character to check
 * @return {@code true} if a surrogate pair starts at the index
 */'''
SIB_PLAIN = PAIR_DOC + '''
public static boolean startsPair(final CharSequence cs, final int index) {
    return index < cs.length() - 1 && Character.isHighSurrogate(cs.charAt(index));
}'''
SIB_ODD = PAIR_DOC + '''
public static boolean startsPair(final CharSequence cs, final int index) {
    return !(index >= cs.length() - 1 || !Character.isSurrogate(cs.charAt(index)) || Character.isLowSurrogate(cs.charAt(index)));
}'''
H3_DOC = '''/**
 * <p>Checks whether the character at an index of a CharSequence is one of
 * a set of characters, taking surrogate pairs into account.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param index  the index of the character to check
 * @param searchChars  the chars to search for, not null or empty
 * @return {@code true} if the character is one of the search chars
 */'''
DESIGN = {
 "bug": "B1", "project": "Lang", "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": "src/main/java/org/apache/commons/lang3/StringUtils.java", "class": "org.apache.commons.lang3.StringUtils",
            "method": "indexOfAnyBut", "near_line": 1606},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/StringUtilsEqualsIndexOfTest.java",
             "test_class": "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest", "test_method": "testIndexOfAnyBut_StringCharArrayWithSupplementaryChars"},
 "expected_signature": "expected:<2> but was:<0>",
 "gold": {"method": "isAnyOf", "text": GOLD_TEXT,
          "fault": {"old": "                if (!pair || j == searchLast) {\n                    return true;\n                }\n                if (searchChars[j + 1] == cs.charAt(index + 1)) {\n                    return true;\n                }",
                    "new": "                if (!pair || j == searchLast) {\n                    return true;\n                }"}},
 "one_hop": {
   "facade_old": '''        final int csLen = cs.length();
        final int csLast = csLen - 1;
        final int searchLen = searchChars.length;
        final int searchLast = searchLen - 1;
        outer:
        for (int i = 0; i < csLen; i++) {
            final char ch = cs.charAt(i);
            for (int j = 0; j < searchLen; j++) {
                if (searchChars[j] == ch) {
                    if (i < csLast && j < searchLast && Character.isHighSurrogate(ch)) {
                        if (searchChars[j + 1] == cs.charAt(i + 1)) {
                            continue outer;
                        }
                    } else {
                        continue outer;
                    }
                }
            }
            return i;
        }
        return INDEX_NOT_FOUND;''',
   "facade_new": '''        final int csLen = cs.length();
        for (int i = 0; i < csLen; i++) {
            if (!isAnyOf(cs, i, searchChars, startsPair(cs, i))) {
                return i;
            }
        }
        return INDEX_NOT_FOUND;''',
   "sibling": {"method": "startsPair", "plain": SIB_PLAIN, "odd": SIB_ODD},
 },
 "chain": {
   "facade_body": "if (isEmpty(cs) || ArrayUtils.isEmpty(searchChars)) {\n            return INDEX_NOT_FOUND;\n        }\n        return org.apache.commons.lang3.builder.ToStringStyle.firstIndexOutside(cs, searchChars);",
   "lie": "The sequence is scanned from its end towards its start, and the index returned is the position at which the trailing run of characters inside the set stops, confirmed by a second forward pass over the prefix.",
   "hops": [
     {"file": "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java", "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "firstIndexOutside",
      "imports": ["org.apache.commons.lang3.text.StrBuilder"],
      "text": '''/**
 * <p>Finds the first index in a CharSequence of a character that is not
 * in the given set of characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param searchChars  the chars to search for, not null or empty
 * @return the index of the first character outside the set, -1 if none
 */
public static int firstIndexOutside(final CharSequence cs, final char[] searchChars) {
    final int csLen = cs.length();
    for (int i = 0; i < csLen; i++) {
        if (!StrBuilder.memberAt(cs, i, searchChars)) {
            return i;
        }
    }
    return -1;
}'''},
     {"file": "src/main/java/org/apache/commons/lang3/text/StrBuilder.java", "class": "org.apache.commons.lang3.text.StrBuilder", "method": "memberAt",
      "imports": ["org.apache.commons.lang3.Conversion"],
      "text": '''/**
 * <p>Checks whether the character at an index of a CharSequence is one of
 * a set of characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param index  the index of the character to check
 * @param searchChars  the chars to search for, not null or empty
 * @return {@code true} if the character is one of the search chars
 */
public static boolean memberAt(final CharSequence cs, final int index, final char[] searchChars) {
    return Conversion.classifyAt(cs, index, searchChars);
}'''},
     {"file": "src/main/java/org/apache/commons/lang3/Conversion.java", "class": "org.apache.commons.lang3.Conversion", "method": "classifyAt",
      "imports": ["org.apache.commons.lang3.time.DateUtils"],
      "plain": H3_DOC + '''
public static boolean classifyAt(final CharSequence cs, final int index, final char[] searchChars) {
    final boolean pair = index < cs.length() - 1 && Character.isHighSurrogate(cs.charAt(index));
    return DateUtils.lookupAt(cs, index, searchChars, pair);
}''',
      "odd": H3_DOC + '''
public static boolean classifyAt(final CharSequence cs, final int index, final char[] searchChars) {
    final boolean pair = !(index >= cs.length() - 1 || !Character.isSurrogate(cs.charAt(index)) || Character.isLowSurrogate(cs.charAt(index)));
    return DateUtils.lookupAt(cs, index, searchChars, pair);
}'''},
     {"file": "src/main/java/org/apache/commons/lang3/time/DateUtils.java", "class": "org.apache.commons.lang3.time.DateUtils", "method": "lookupAt",
      "imports": ["org.apache.commons.lang3.ArrayUtils"],
      "text": '''/**
 * <p>Checks whether the character at an index of a CharSequence is one of
 * a set of characters.</p>
 *
 * @param cs  the CharSequence to check, not null
 * @param index  the index of the character to check
 * @param searchChars  the chars to search for, not null or empty
 * @param pair  whether the character at the index is the first unit of a
 *  surrogate pair
 * @return {@code true} if the character is one of the search chars
 */
public static boolean lookupAt(final CharSequence cs, final int index, final char[] searchChars, final boolean pair) {
    return ArrayUtils.isAnyOf(cs, index, searchChars, pair);
}'''},
     {"file": "src/main/java/org/apache/commons/lang3/ArrayUtils.java", "class": "org.apache.commons.lang3.ArrayUtils", "method": "isAnyOf", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.StringUtils::indexOfAny", "org.apache.commons.lang3.StringUtils::indexOfAnyBut", "org.apache.commons.lang3.StringUtils::containsOnly"],
 "ownership_reason": "Only the membership test sees both units of a surrogate pair; the facade, the pair-start predicate and the plumbing "
                     "hops pass the position along and cannot repair a membership verdict with a one-line change. indexOfAny and the "
                     "CharSequence overload of indexOfAnyBut compare the second unit explicitly, the supplementary-character tests expect it, "
                     "and containsOnly (BMP tests) relies on the same membership test.",
 "ownership_tests": ["org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsOnly_CharArray",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsOnly_String",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testIndexOfAnyBut_StringCharArray",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testIndexOfAny_StringCharArrayWithSupplementaryChars",
                     "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testIndexOfAnyBut_StringStringWithSupplementaryChars"],
 "compensating": {
   "one_hop": [
     {"file": "src/main/java/org/apache/commons/lang3/StringUtils.java", "old": "            if (!isAnyOf(cs, i, searchChars, startsPair(cs, i))) {",
      "new": "            if (!isAnyOf(cs, i, searchChars, false)) {", "why": "facade never reports a pair start"},
     {"file": "src/main/java/org/apache/commons/lang3/StringUtils.java", "old": "    return index < cs.length() - 1 && Character.isHighSurrogate(cs.charAt(index));",
      "new": "    return index < cs.length() - 1 && Character.isSurrogate(cs.charAt(index));", "why": "plain sibling counts any surrogate as a pair start", "cells": ["C00"]},
     {"file": "src/main/java/org/apache/commons/lang3/StringUtils.java", "old": "    return !(index >= cs.length() - 1 || !Character.isSurrogate(cs.charAt(index)) || Character.isLowSurrogate(cs.charAt(index)));",
      "new": "    return !(index >= cs.length() - 1 || !Character.isSurrogate(cs.charAt(index)));", "why": "odd sibling counts any surrogate as a pair start", "cells": ["C01"]},
   ],
   "chain": [
     {"file": "src/main/java/org/apache/commons/lang3/Conversion.java", "old": "    return DateUtils.lookupAt(cs, index, searchChars, pair);",
      "new": "    return DateUtils.lookupAt(cs, index, searchChars, false);", "why": "hop 3 never reports a pair start"},
     {"file": "src/main/java/org/apache/commons/lang3/Conversion.java", "old": "    final boolean pair = index < cs.length() - 1 && Character.isHighSurrogate(cs.charAt(index));",
      "new": "    final boolean pair = index < cs.length() - 1 && Character.isSurrogate(cs.charAt(index));", "why": "plain hop 3 counts any surrogate as a pair start", "cells": ["C10"]},
     {"file": "src/main/java/org/apache/commons/lang3/Conversion.java", "old": "    final boolean pair = !(index >= cs.length() - 1 || !Character.isSurrogate(cs.charAt(index)) || Character.isLowSurrogate(cs.charAt(index)));",
      "new": "    final boolean pair = !(index >= cs.length() - 1 || !Character.isSurrogate(cs.charAt(index)));", "why": "odd hop 3 counts any surrogate as a pair start", "cells": ["C11"]},
   ],
 },
}
