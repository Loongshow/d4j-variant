"""Deterministic construction of LANG-FOLD-CONTROL-02 / LANG-FOLD-TREATMENT-02 on a fresh Lang-1f checkout. No LLM.
Usage: build_lang_bug02.py <control|treatment> <work_checkout> <package_dir>. Exact, asserted string edits; patches emitted with git diff.
NON-CANONICAL / CORE BENCHMARK SCALE-UP / NO GPT-5.6 RUNS PERFORMED."""
import os, subprocess, sys, hashlib
arm, work, pkg = sys.argv[1], sys.argv[2], sys.argv[3]
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, t): open(p, "w", encoding="utf-8").write(t)
def edit(path, old, new):
    t = rd(path); assert t.count(old) == 1, f"{os.path.basename(path)}: expected exactly one match for {old[:70]!r}, got {t.count(old)}"; wr(path, t.replace(old, new, 1))
def append_before_class_end(path, block):
    t = rd(path); k = t.rstrip().rfind("}"); assert k > 0 and t[k:].strip() == "}", "class end not found"
    head = t[:k].rstrip("\n") + "\n"; wr(path, head + block + "}" + ("\n" if t.endswith("\n") else ""))
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
B = "src/main/java/org/apache/commons/lang3/"; J = lambda *p: os.path.join(work, B, *p)
CSU, SM, CU, CR, CSUT, CS = J("CharSequenceUtils.java"), J("text/StrMatcher.java"), J("CharUtils.java"), J("CharRange.java"), J("CharSetUtils.java"), J("CharSet.java")
TEST = os.path.join(work, "src/test/java/org/apache/commons/lang3/StringUtilsEqualsIndexOfTest.java")
# ---- trigger (both arms) ----
t = rd(TEST); assert "import org.junit.Test;" in t and "import static org.junit.Assert.assertEquals;" in t
test_src = ('\n    @Test\n    public void testLang1149() {\n'
            '        // Characters whose upper-case forms agree while their lower-case forms differ (or\n'
            '        // the other way round) compare equal ignoring case, whatever the CharSequence\n'
            '        // implementation: the CharSequence comparison must agree with the String one.\n'
            '        final String longS = "\\u017F"; // LATIN SMALL LETTER LONG S, upper-cases to S\n'
            '        final String kelvin = "\\u212A"; // KELVIN SIGN, lower-cases to k\n'
            '        assertTrue(StringUtils.equalsIgnoreCase(longS, "s"));\n'
            '        assertTrue(StringUtils.equalsIgnoreCase(kelvin, "K"));\n'
            '        assertEquals(StringUtils.equalsIgnoreCase(longS, "s"),\n                     StringUtils.equalsIgnoreCase(new StringBuilder(longS), "s"));\n'
            '        assertEquals(StringUtils.equalsIgnoreCase(kelvin, "K"),\n                     StringUtils.equalsIgnoreCase(new StringBuilder(kelvin), "K"));\n'
            '        assertEquals(StringUtils.equalsIgnoreCase("ab" + longS, "ABS"),\n                     StringUtils.equalsIgnoreCase(new StringBuilder("ab" + longS), "ABS"));\n'
            '    }\n')
append_before_class_end(TEST, test_src)
ORIG_BLOCK = ("                if (Character.toUpperCase(c1) != Character.toUpperCase(c2)\n"
              "                        && Character.toLowerCase(c1) != Character.toLowerCase(c2)) {\n")
BUG_BLOCK = ("                if (Character.toUpperCase(c1) != Character.toUpperCase(c2)\n"
             "                        || Character.toLowerCase(c1) != Character.toLowerCase(c2)) {\n")
if arm == "control":
    edit(CSU, ORIG_BLOCK, BUG_BLOCK); files = [B + "CharSequenceUtils.java"]
else:
    t = rd(CSU); decl = "            final CharSequence substring, final int start, final int length)    {\n"; i = t.index(decl) + len(decl)
    end_marker = "            return true;\n        }\n    }\n"; end = t.index(end_marker, i) + len(end_marker); assert ORIG_BLOCK in t[i:end]
    new_body = ("        if (cs instanceof String && substring instanceof String) {\n"
                "            return ((String) cs).regionMatches(ignoreCase, thisStart, (String) substring, start, length);\n"
                "        }\n"
                "        return StrMatcher.sweep(cs, thisStart, substring, start, length, ignoreCase);\n    }\n")
    wr(CSU, t[:i] + new_body + t[end:])
    edit(CSU, "package org.apache.commons.lang3;\n\n", "package org.apache.commons.lang3;\n\nimport org.apache.commons.lang3.text.StrMatcher;\n\n")
    # hop 1: StrMatcher.sweep - walks the two regions in step and compares the character pairs
    edit(SM, "import org.apache.commons.lang3.StringUtils;\n", "import org.apache.commons.lang3.CharUtils;\nimport org.apache.commons.lang3.StringUtils;\n")
    hop1 = ('\n    /**\n     * Walks two regions of two CharSequences in step and tells whether every\n     * pair of characters matches, optionally ignoring case.\n     *\n'
            '     * @param cs  the CharSequence holding the first region\n     * @param thisStart  the start of the first region\n     * @param substring  the CharSequence holding the second region\n'
            '     * @param start  the start of the second region\n     * @param length  the length of the regions\n     * @param ignoreCase  whether case is ignored when comparing the characters\n'
            '     * @return true if the regions match\n     */\n'
            '    public static boolean sweep(final CharSequence cs, final int thisStart, final CharSequence substring,\n                         final int start, final int length, final boolean ignoreCase) {\n'
            '        int index1 = thisStart;\n        int index2 = start;\n        int tmpLen = length;\n        while (tmpLen-- > 0) {\n'
            '            final char c1 = cs.charAt(index1++);\n            final char c2 = substring.charAt(index2++);\n            if (!CharUtils.pair(c1, c2, ignoreCase)) {\n                return false;\n            }\n        }\n        return true;\n    }\n')
    append_before_class_end(SM, hop1)
    # hop 2: CharUtils.pair - identity short-cut and the case-sensitivity gate
    hop2 = ('\n    /**\n     * Tells whether two characters match, optionally ignoring case.\n     *\n     * @param c1  the first character\n     * @param c2  the second character\n'
            '     * @param ignoreCase  whether case is ignored\n     * @return true if the characters match\n     */\n'
            '    public static boolean pair(final char c1, final char c2, final boolean ignoreCase) {\n        if (c1 == c2) {\n            return true;\n        }\n'
            '        if (!ignoreCase) {\n            return false;\n        }\n        return CharRange.capitals(c1, c2);\n    }\n')
    append_before_class_end(CU, hop2)
    # hop 3: CharRange.capitals - the upper-case forms of the pair
    hop3 = ('\n    /**\n     * Tells whether two distinct characters match ignoring case, starting from\n     * their upper-case forms.\n     *\n     * @param c1  the first character\n     * @param c2  the second character\n'
            '     * @return true if the characters match ignoring case\n     */\n'
            '    static boolean capitals(final char c1, final char c2) {\n        final char u1 = Character.toUpperCase(c1);\n        final char u2 = Character.toUpperCase(c2);\n'
            '        return CharSetUtils.smalls(c1, c2, u1, u2);\n    }\n')
    append_before_class_end(CR, hop3)
    # hop 4: CharSetUtils.smalls - the lower-case forms of the pair
    hop4 = ('\n    /**\n     * Tells whether two distinct characters match ignoring case, given their\n     * upper-case forms and computing their lower-case forms.\n     *\n'
            '     * @param c1  the first character\n     * @param c2  the second character\n     * @param u1  the upper-case form of the first character\n     * @param u2  the upper-case form of the second character\n'
            '     * @return true if the characters match ignoring case\n     */\n'
            '    static boolean smalls(final char c1, final char c2, final char u1, final char u2) {\n        final char l1 = Character.toLowerCase(c1);\n        final char l2 = Character.toLowerCase(c2);\n'
            '        return CharSet.akin(u1, u2, l1, l2);\n    }\n')
    append_before_class_end(CSUT, hop4)
    # hop 5 (gold): CharSet.akin - the case-folding equivalence of the pair; the BUGGY line
    hop5 = ('\n    /**\n     * Tells whether two characters are the same letter ignoring case, given\n     * their upper-case and lower-case forms (the same rule as in\n     * String.regionMatches()).\n     *\n'
            '     * @param u1  the upper-case form of the first character\n     * @param u2  the upper-case form of the second character\n'
            '     * @param l1  the lower-case form of the first character\n     * @param l2  the lower-case form of the second character\n'
            '     * @return true if the characters match ignoring case\n     */\n'
            '    static boolean akin(final char u1, final char u2, final char l1, final char l2) {\n        final boolean sameUpper = u1 == u2;\n        final boolean sameLower = l1 == l2;\n'
            '        return sameUpper && sameLower;\n    }\n')
    append_before_class_end(CS, hop5)
    files = [B + "CharSequenceUtils.java", B + "text/StrMatcher.java", B + "CharUtils.java", B + "CharRange.java", B + "CharSetUtils.java", B + "CharSet.java"]
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + files)); open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/lang3/StringUtilsEqualsIndexOfTest.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
