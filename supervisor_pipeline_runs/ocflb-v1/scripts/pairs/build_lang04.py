"""OCFLB-LANG-04: text normalization (case folding: either upper or lower forms agree). Seed LANG-FOLD-TREATMENT-02.
Facade CharSequenceUtils.regionMatches -> H1 StrMatcher.sweep -> H2 CharSet.akin (definer, number of agreeing case forms)
-> H3 CharSetUtils.smalls (adapter, count -> fold-equality decision) -> H4 CharUtils.pair -> H5 CharRange.capitals.
Design note: the first cut (H2 = agreement mask, H3 = mask != 0, definer fault = collapse to 3-or-0) is provably not pinnable: the
collapsed definer maps masks 0, 1, 2 to the same value, so no H3 edit can recover "either" and V11b stays MOSTLY_UNIQUE. The count
form keeps the mechanism (either vs both) with information-preserving faults on both sides.
Usage: build_lang04.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Lang"; SEED = "LANG-FOLD-TREATMENT-02"
SRC = "src/main/java/org/apache/commons/lang3/"
F = {"facade": SRC + "CharSequenceUtils.java", "H1": SRC + "text/StrMatcher.java", "H2": SRC + "CharSet.java",
     "H3": SRC + "CharSetUtils.java", "H4": SRC + "CharUtils.java", "H5": SRC + "CharRange.java"}
T_TRIG = "src/test/java/org/apache/commons/lang3/StringUtilsEqualsIndexOfTest.java"; T_PIN = "src/test/java/org/apache/commons/lang3/CharSetTest.java"
H1 = '''    /**
     * Walks two regions of two CharSequences in step and tells whether every
     * position matches, optionally ignoring case. For each position the pair
     * of characters is prepared together with its upper-case and lower-case
     * forms, the number of agreeing case forms of the pair is computed, and
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
            final char u1 = Character.toUpperCase(c1);
            final char u2 = Character.toUpperCase(c2);
            final char l1 = Character.toLowerCase(c1);
            final char l2 = Character.toLowerCase(c2);
            final int agreeing = CharSet.akin(u1, u2, l1, l2);
            misses = CharSetUtils.smalls(agreeing, c1, c2, ignoreCase, misses);
        }
        return misses == 0;
    }'''
H2_OK = "        final int upper = u1 == u2 ? 1 : 0;\n        final int lower = l1 == l2 ? 1 : 0;"
H2_BUG = "        final int upper = u1 == u2 ? 1 : -1;\n        final int lower = l1 == l2 ? 1 : -1;"
H2_ABSORB = "        final int upper = u1 == u2 ? 2 : 0;\n        final int lower = l1 == l2 ? 2 : 0;"     # H2 edit that would absorb the H3 fault (validator probe only)
H2 = '''    /**
     * Counts how many of the case forms of a character pair agree, given the
     * upper-case and lower-case forms of the two characters: one for the
     * upper-case forms when they agree and one for the lower-case forms when
     * they agree, so the count is 0, 1 or 2. Two characters fold-equal (match
     * ignoring case, the rule of String.regionMatches()) as soon as at least
     * one of their case forms agrees, that is whenever the count is positive.
     *
     * @param u1  the upper-case form of the first character
     * @param u2  the upper-case form of the second character
     * @param l1  the lower-case form of the first character
     * @param l2  the lower-case form of the second character
     * @return the number of agreeing case forms of the pair
     */
    public static int akin(final char u1, final char u2, final char l1, final char l2) {
%s
        return upper + lower;
    }'''
H3_OK = "        final boolean folded = agreeing > 0;"
H3_BUG = "        final boolean folded = agreeing > 1;"
H3_ABSORB = "        final boolean folded = agreeing >= 0;"     # H3 edit that would absorb the H2 fault (validator probe only)
H3 = '''    /**
     * Turns the number of agreeing case forms of a character pair into the
     * fold-equality decision for the pair and hands the decision on, together
     * with the characters themselves, so that it is counted into the running
     * number of positions of the region that do not match.
     *
     * @param agreeing  the number of agreeing case forms of the pair
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
PIN = '''    //-----------------------------------------------------------------------
    @Test
    public void testAkin() {
        // number of agreeing case forms of a character pair: one for the upper-case
        // forms when they agree, one for the lower-case forms when they agree
        assertEquals(2, CharSet.akin('A', 'A', 'a', 'a'));
        assertEquals(0, CharSet.akin('A', 'B', 'a', 'b'));
        // LATIN SMALL LETTER LONG S and 's': only the upper-case forms agree
        assertEquals(1, CharSet.akin('S', 'S', '\\u017F', 's'));
        // KELVIN SIGN and 'K': only the lower-case forms agree
        assertEquals(1, CharSet.akin('\\u212A', 'K', 'k', 'k'));
        // at least one agreeing form means the pair matches ignoring case
        assertTrue(CharSet.akin('S', 'S', '\\u017F', 's') > 0);
        assertTrue(CharSet.akin('\\u212A', 'K', 'k', 'k') > 0);
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
    B.insert_before_class_end(work, T_PIN, PIN)
spec = {"pair_id": "OCFLB-LANG-04", "project": P, "bug": "04", "base_version": "Lang-1f", "seed_variant": SEED,
  "family": "text normalization (case folding: either upper or lower forms agree)",
  "convention": "akin(u1, u2, l1, l2) = number of agreeing case forms of a character pair (one when the upper-case forms agree, one when the lower-case forms agree; 0, 1 or 2); the pair fold-equals (matches ignoring case) whenever the count is positive, i.e. as soon as either form agrees",
  "effect": "a pair whose upper-case forms agree while the lower-case forms differ (LATIN SMALL LETTER LONG S vs 's'), or the other way round (KELVIN SIGN vs 'K'), is treated as not matching ignoring case on the CharSequence path, so equalsIgnoreCase(StringBuilder, String) disagrees with equalsIgnoreCase(String, String) (false instead of true)",
  "equivalence_note": "netting agreements against disagreements in the definer (+1/-1: 2, 0, -2 instead of 2, 1, 0; arm A, positive only when both forms agree) and requiring more than one agreeing form in the adapter (arm B) both make the pair fold-equal exactly when both case forms agree, so the per-character decision and hence the region result are identical for every input",
  "adapter_fault_note": "smalls decides fold-equality with agreeing > 1 (both forms must agree) instead of agreeing > 0 (either form agrees)",
  "trigger": "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testLang1149", "expected_signature": "expected:<true> but was:<false>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.apache.commons.lang3.CharSetTest::testAkin", "second_caller": None,
  "chain": {"facade": {"class": "org.apache.commons.lang3.CharSequenceUtils", "method": "regionMatches", "file": F["facade"]},
            "H1": {"class": "org.apache.commons.lang3.text.StrMatcher", "method": "sweep", "file": F["H1"]}, "H2": {"class": "org.apache.commons.lang3.CharSet", "method": "akin", "file": F["H2"]},
            "H3": {"class": "org.apache.commons.lang3.CharSetUtils", "method": "smalls", "file": F["H3"]}, "H4": {"class": "org.apache.commons.lang3.CharUtils", "method": "pair", "file": F["H4"]},
            "H5": {"class": "org.apache.commons.lang3.CharRange", "method": "capitals", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "OCFLB-LANG-04-DEFINER", "gold_role": "H2", "gold": {"class": "org.apache.commons.lang3.CharSet", "method": "akin", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_ABSORB}, "declared_collateral": ["org.apache.commons.lang3.CharSetTest::testAkin"]},
           "ADAPTER_FAULT": {"variant_id": "OCFLB-LANG-04-ADAPTER", "gold_role": "H3", "gold": {"class": "org.apache.commons.lang3.CharSetUtils", "method": "smalls", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_ABSORB}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Lang/bug-04"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
