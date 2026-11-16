"""LB-LANG-04 (Level B): text normalization (case folding). Converted from OCFLB-LANG-04 (seed LANG-FOLD-TREATMENT-02).
Facade CharSequenceUtils.regionMatches -> H1 StrMatcher.sweep -> H2 CharSet.akin (definer, agreement of the case forms of a pair)
-> H3 CharSetUtils.smalls (adapter, agreement -> fold-equality decision) -> H4 CharUtils.pair -> H5 CharRange.capitals.
Convention decided externally: a pair folds equal as soon as ANY of its case forms agrees (akin counts each agreeing form; the
production second caller StringUtils.foldEquals tests akin(...) > 0, and StringUtilsTest.testFoldEquals relies on it).
DEFINER arm (revision 2): akin folds only the lower-case forms (the upper-case comparison is omitted), so a pair whose upper
forms agree while the lower forms differ counts 0. ADAPTER arm: smalls folds only when all case forms agree (agreement == number
of forms). Revision 2 (after blinded grading): the first definer fault, upper = (u1 == u2 && l1 == l2), contradicted the lower
term two lines below it and was confidently identified from the H2 packet alone; akin now takes the two characters, folds them
itself, and the definer fault is a coherent lower-case-only fold with no unused input.
Usage: build_lb_lang04.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Lang"; SEED = "LANG-FOLD-TREATMENT-02"
SRC = "src/main/java/org/apache/commons/lang3/"
F = {"facade": SRC + "CharSequenceUtils.java", "H1": SRC + "text/StrMatcher.java", "H2": SRC + "CharSet.java",
     "H3": SRC + "CharSetUtils.java", "H4": SRC + "CharUtils.java", "H5": SRC + "CharRange.java", "EXT": SRC + "StringUtils.java"}
T_TRIG = "src/test/java/org/apache/commons/lang3/StringUtilsEqualsIndexOfTest.java"; T_PIN = "src/test/java/org/apache/commons/lang3/CharSetTest.java"
T_EXT = "src/test/java/org/apache/commons/lang3/StringUtilsTest.java"
H1 = '''    /**
     * Walks two regions of two CharSequences in step and tells whether every
     * position matches, optionally ignoring case. For each position the
     * agreement of the case forms of the pair of characters is computed, and
     * the decision for the position is counted into the running number of
     * positions that do not match; the walk stops at the first such position.
     *
     * @param cs  the CharSequence holding the first region
     * @param thisStart  the start of the first region
     * @param substring  the CharSequence holding the second region
     * @param start  the start of the second region
     * @param length  the length of the regions
     * @param ignoreCase  whether case is ignored when comparing the characters
     * @return true if the regions match
     */
    public static boolean sweep(final CharSequence cs, final int thisStart, final CharSequence substring,
                         final int start, final int length, final boolean ignoreCase) {
        int index1 = thisStart;
        int index2 = start;
        int tmpLen = length;
        int misses = 0;
        while (tmpLen-- > 0 && misses == 0) {
            final char c1 = cs.charAt(index1++);
            final char c2 = substring.charAt(index2++);
            final int agreeing = CharSet.akin(c1, c2);
            misses = CharSetUtils.smalls(agreeing, c1, c2, ignoreCase, misses);
        }
        return misses == 0;
    }'''
H2_OK = "        final int upper = Character.toUpperCase(c1) == Character.toUpperCase(c2) ? 1 : 0;\n        final int lower = Character.toLowerCase(c1) == Character.toLowerCase(c2) ? 1 : 0;\n        return upper + lower;"
H2_BUG = "        final int lower = Character.toLowerCase(c1) == Character.toLowerCase(c2) ? 1 : 0;\n        return lower;"     # DEFINER arm: only the lower-case forms are folded (the upper-case comparison is omitted)
H2_ABSORB = "        final int any = Character.toUpperCase(c1) == Character.toUpperCase(c2) || Character.toLowerCase(c1) == Character.toLowerCase(c2) ? 1 : 0;\n        return any + any;"     # H2 edit that would absorb the H3 fault (validator probe only)
H2 = '''    /**
     * Tells how far two characters agree once case is folded.
     *
     * @param c1  the first character
     * @param c2  the second character
     * @return the agreement of the case forms of the two characters
     */
    public static int akin(final char c1, final char c2) {
%s
    }'''
H3_OK = "        final boolean folded = agreeing > 0;"
H3_BUG = "        final int forms = 2;\n        final boolean folded = agreeing == forms;"
H3_ABSORB = "        final boolean folded = agreeing >= 0;"     # H3 edit that would absorb the H2 fault (validator probe only)
H3 = '''    /**
     * Decides whether a character pair folds equal from the agreement of its
     * case forms and counts the position: the decision is handed on, together
     * with the characters themselves, to be counted into the running number
     * of positions of the region that do not match.
     *
     * @param agreeing  the agreement of the case forms of the pair
     * @param c1  the first character
     * @param c2  the second character
     * @param ignoreCase  whether case is ignored
     * @param misses  the number of positions seen so far that do not match
     * @return the updated number of positions that do not match
     */
    public static int smalls(final int agreeing, final char c1, final char c2, final boolean ignoreCase, final int misses) {
%s
        return CharUtils.pair(c1, c2, ignoreCase, folded, misses);
    }'''
H4 = '''    /**
     * Resolves the match decision of a character pair: identical characters
     * always match, and distinct characters match only when case is ignored
     * and the pair fold-equals. The decision is then counted into the running
     * number of positions of the region that do not match.
     *
     * @param c1  the first character
     * @param c2  the second character
     * @param ignoreCase  whether case is ignored
     * @param folded  whether the pair fold-equals
     * @param misses  the number of positions seen so far that do not match
     * @return the updated number of positions that do not match
     */
    public static int pair(final char c1, final char c2, final boolean ignoreCase, final boolean folded, final int misses) {
        final boolean identical = c1 == c2;
        final boolean matched = identical || (ignoreCase && folded);
        return CharRange.capitals(matched, misses);
    }'''
H5 = '''    /**
     * Counts the decision of one position of a region into the running number
     * of positions that do not match: a matching position leaves the number
     * as it is, any other position raises it by one.
     *
     * @param matched  whether the position matches
     * @param misses  the number of positions seen so far that do not match
     * @return the updated number of positions that do not match
     */
    static int capitals(final boolean matched, final int misses) {
        final int step = matched ? 0 : 1;
        return misses + step;
    }'''
EXT = '''    /**
     * Compares two characters ignoring case.
     *
     * @param c1  the first character
     * @param c2  the second character
     * @return {@code true} if the characters are equal ignoring case
     */
    public static boolean foldEquals(final char c1, final char c2) {
        return CharSet.akin(c1, c2) > 0;
    }'''
EXT_TEST = '''    /**
     * Tests foldEquals().
     */
    @Test
    public void testFoldEquals() {
        assertTrue(StringUtils.foldEquals('a', 'a'));
        assertTrue(StringUtils.foldEquals('a', 'A'));
        assertTrue(StringUtils.foldEquals('S', '\\u017F'));
        assertTrue(StringUtils.foldEquals('\\u212A', 'k'));
        assertFalse(StringUtils.foldEquals('a', 'b'));
    }
'''
PIN = '''    //-----------------------------------------------------------------------
    /**
     * Tests akin().
     */
    @Test
    public void testAkin() {
        assertEquals(2, CharSet.akin('a', 'a'));
        assertEquals(2, CharSet.akin('a', 'A'));
        assertEquals(0, CharSet.akin('a', 'b'));
        assertEquals(1, CharSet.akin('\\u017F', 's'));
        assertEquals(1, CharSet.akin('\\u212A', 'k'));
    }
'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "sweep", H1)
    B.replace_once(work, F["H1"], "import org.apache.commons.lang3.CharUtils;\n", "import org.apache.commons.lang3.CharSet;\nimport org.apache.commons.lang3.CharSetUtils;\n")
    B.replace_method(work, F["H2"], "akin", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_method(work, F["H3"], "smalls", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK))
    B.replace_method(work, F["H4"], "pair", H4)
    B.replace_method(work, F["H5"], "capitals", H5)
    B.insert_before_class_end(work, F["EXT"], EXT)
    B.insert_before_class_end(work, T_PIN, PIN)
    B.insert_before_class_end(work, T_EXT, EXT_TEST)
spec = {"pair_id": "LB-LANG-04", "project": P, "bug": "04", "base_version": "Lang-1f", "seed_variant": SEED, "level": "B", "converted_from": "OCFLB-LANG-04", "revision": 2,
  "family": "text normalization (case folding: any case form agreeing folds the pair)",
  "convention": "akin(c1, c2) = agreement of the case forms of a character pair, counting one when the upper-case forms agree and one when the lower-case forms agree (0, 1 or 2); the pair folds equal (matches ignoring case) as soon as any form agrees, i.e. when the agreement is positive; decided by the production second caller StringUtils.foldEquals (akin(c1, c2) > 0) and its test testFoldEquals, which folds 'S' with LATIN SMALL LETTER LONG S (upper forms agree, lower forms differ)",
  "effect": "a pair whose upper-case forms agree while the lower-case forms differ (LATIN SMALL LETTER LONG S vs 's') is treated as not matching ignoring case on the CharSequence path, so equalsIgnoreCase(StringBuilder, String) disagrees with equalsIgnoreCase(String, String) (false instead of true)",
  "equivalence_note": "folding only the lower-case forms in the definer (arm A: 0 for a pair with only the upper forms agreeing) and requiring the agreement of all case forms in the adapter (arm B: agreeing == forms) both leave the trigger pair (only the upper forms agree) unfolded, so the per-character decision and hence the region result are identical on the trigger input and the failure text is the same",
  "adapter_fault_note": "smalls folds the pair only when the agreement equals the number of case forms (all forms agree) instead of when it is positive (any form agrees)",
  "trigger": "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testLang1149", "expected_signature": "expected:<true> but was:<false>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.apache.commons.lang3.CharSetTest::testAkin", "second_caller": "org.apache.commons.lang3.StringUtils#foldEquals (production; folds two characters equal when akin(c1, c2) > 0)",
  "external_evidence_tests": ["org.apache.commons.lang3.StringUtilsTest::testFoldEquals"],
  "chain": {"facade": {"class": "org.apache.commons.lang3.CharSequenceUtils", "method": "regionMatches", "file": F["facade"]},
            "H1": {"class": "org.apache.commons.lang3.text.StrMatcher", "method": "sweep", "file": F["H1"]}, "H2": {"class": "org.apache.commons.lang3.CharSet", "method": "akin", "file": F["H2"]},
            "H3": {"class": "org.apache.commons.lang3.CharSetUtils", "method": "smalls", "file": F["H3"]}, "H4": {"class": "org.apache.commons.lang3.CharUtils", "method": "pair", "file": F["H4"]},
            "H5": {"class": "org.apache.commons.lang3.CharRange", "method": "capitals", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5", "EXT")], "test_files": [T_TRIG, T_PIN, T_EXT],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5", "EXT")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}, {"file": T_EXT, "role": "external evidence test"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "LB-LANG-04-DEFINER", "gold_role": "H2", "gold": {"class": "org.apache.commons.lang3.CharSet", "method": "akin", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_ABSORB}, "declared_collateral": ["org.apache.commons.lang3.CharSetTest::testAkin", "org.apache.commons.lang3.StringUtilsTest::testFoldEquals"]},
           "ADAPTER_FAULT": {"variant_id": "LB-LANG-04-ADAPTER", "gold_role": "H3", "gold": {"class": "org.apache.commons.lang3.CharSetUtils", "method": "smalls", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_ABSORB}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Lang/bug-04"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
