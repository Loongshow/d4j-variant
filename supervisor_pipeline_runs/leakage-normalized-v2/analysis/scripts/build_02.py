"""Deterministic derivation of the -02 arms from the read-only -01 copies (src01/). No LLM.
Usage: build_02.py <arm: control|treatment> <work_checkout_dir>
Applies the -01 patches with `git apply`, performs exact, asserted string edits per CONTROL02_TREATMENT02_SPEC.md,
and writes the -02 patches (git diff) into the package directory. Every replacement must match exactly once."""
import os, subprocess, sys
V2 = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/leakage-normalized-v2"
arm, work = sys.argv[1], sys.argv[2]
src = os.path.join(V2, "src01", "NUMBERUTILS-CONTROL-01" if arm == "control" else "NUMBERUTILS-TREATMENT-01")
pkg = os.path.join(V2, "NUMBERUTILS-CONTROL-02" if arm == "control" else "NUMBERUTILS-TREATMENT-02")
NEW_TEST = "testLang1106"
def run(cmd, cwd=work, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True);
    if check and p.returncode: raise SystemExit(f"FAILED {cmd}: {p.stdout}{p.stderr}")
    return p.stdout
def edit(path, replacements):
    t = open(path, encoding="utf-8").read()
    for old, new in replacements:
        n = t.count(old); assert n == 1, f"{os.path.basename(path)}: expected exactly one match, got {n} for:\n{old[:120]!r}"
        t = t.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(t)

st = run(["git", "status", "--short"]); assert not [l for l in st.splitlines() if not l.startswith("??")], "work tree not clean"
run(["git", "apply", os.path.join(src, "variant.patch")]); run(["git", "apply", os.path.join(src, "test.patch")])

# ---- test (both arms): neutral name, no javadoc sentence, single blank lines ----
T = os.path.join(work, "src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java")
old_test = ('\n\n\n    /**\n     * Test for {@link NumberUtils#createBigInteger(String)} with an explicit positive sign.\n     */\n'
            '    @Test\n    public void testCreateBigIntegerPositiveSigned() {\n'
            '        assertEquals("createBigInteger(String) failed", new BigInteger("1234"), NumberUtils.createBigInteger("+1234"));\n'
            '        assertEquals("createBigInteger(String) failed", new BigInteger("7"), NumberUtils.createBigInteger("+7"));\n'
            '    }\n\n\n}')
new_test = ('\n\n    @Test\n    public void ' + NEW_TEST + '() {\n'
            '        assertEquals("createBigInteger(String) failed", new BigInteger("1234"), NumberUtils.createBigInteger("+1234"));\n'
            '        assertEquals("createBigInteger(String) failed", new BigInteger("7"), NumberUtils.createBigInteger("+7"));\n'
            '    }\n}')
edit(T, [(old_test, new_test)])

if arm == "treatment":
    NU = os.path.join(work, "src/main/java/org/apache/commons/lang3/math/NumberUtils.java")
    OU = os.path.join(work, "src/main/java/org/apache/commons/lang3/ObjectUtils.java")
    CB = os.path.join(work, "src/main/java/org/apache/commons/lang3/builder/CompareToBuilder.java")
    # facade: remove lie line, use import + simple call
    edit(NU, [
        ('     * @throws NumberFormatException if the value cannot be converted\n       <p>The string is scanned once from the left within this method: a leading minus sign is consumed and remembered, the prefix immediately following it selects the radix (16 for <code>0x</code> or <code>#</code>, 8 for a leading zero that is followed by further digits, otherwise 10), and the remaining characters are parsed in place before the remembered sign is re-applied to the result.</p>\n     */\n',
         '     * @throws NumberFormatException if the value cannot be converted\n     */\n'),
        ('        return org.apache.commons.lang3.ObjectUtils.resolveWholeValue(str);\n', '        return ObjectUtils.resolveWholeValue(str);\n'),
        ('import org.apache.commons.lang3.StringUtils;\n', 'import org.apache.commons.lang3.ObjectUtils;\nimport org.apache.commons.lang3.StringUtils;\n'),
    ])
    # hop1: normalized block + imports
    old_hop1 = ('    /**\n         * <p>Resolves the supplied text into its whole-number form.</p>\n         *\n         * @param str  the text to resolve, may be null\n'
                '         * @return the resolved value, {@code null} if the input is {@code null}\n         * @since 3.2\n         */\n'
                '        public static java.math.BigInteger resolveWholeValue(final String str) {\n'
                '            return org.apache.commons.lang3.builder.CompareToBuilder.decodeMagnitude(str);\n        }\n\n\n')
    new_hop1 = ('    /**\n     * <p>Resolves the supplied text into its whole-number form.</p>\n     *\n     * @param str  the text to resolve, may be null\n'
                '     * @return the resolved value, {@code null} if the input is {@code null}\n     * @since 3.2\n     */\n'
                '    public static BigInteger resolveWholeValue(final String str) {\n'
                '        return CompareToBuilder.decodeMagnitude(str);\n    }\n\n')
    edit(OU, [
        (old_hop1, new_hop1),
        ('import java.lang.reflect.Method;\n', 'import java.lang.reflect.Method;\nimport java.math.BigInteger;\n'),
        ('import org.apache.commons.lang3.exception.CloneFailedException;\n', 'import org.apache.commons.lang3.builder.CompareToBuilder;\nimport org.apache.commons.lang3.exception.CloneFailedException;\n'),
    ])
    # hop2: normalized block + import
    body = ('        if (str == null) {\n            return null;\n        }\n        int pos = 0; // offset within string\n        int radix = 10;\n'
            '        boolean negate = false; // need to negate later?\n        if (str.startsWith("-") || str.startsWith("+")) {\n            negate = true;\n            pos = 1;\n        }\n'
            '        if (str.startsWith("0x", pos) || str.startsWith("0x", pos)) { // hex\n            radix = 16;\n            pos += 2;\n'
            '        } else if (str.startsWith("#", pos)) { // alternative hex (allowed by Long/Integer)\n            radix = 16;\n            pos ++;\n'
            '        } else if (str.startsWith("0", pos) && str.length() > pos + 1) { // octal; so long as there are additional digits\n            radix = 8;\n            pos ++;\n'
            '        } // default is to treat as decimal\n\n        final BigInteger value = new BigInteger(str.substring(pos), radix);\n        return negate ? value.negate() : value;\n')
    old_body01 = ("\n" + body).replace("\n        ", "\n            ")[1:].replace("final BigInteger value = new BigInteger", "final java.math.BigInteger value = new java.math.BigInteger")
    old_hop2 = ('    /**\n         * <p>Decodes the magnitude held in the supplied text, honouring an optional\n         * sign and the usual radix prefixes.</p>\n         *\n'
                '         * @param str  the text to decode, may be null\n         * @return the decoded magnitude, {@code null} if the input is {@code null}\n         */\n'
                '        public static java.math.BigInteger decodeMagnitude(final String str) {\n' + old_body01 + '        }\n\n\n')
    new_hop2 = ('    /**\n     * <p>Decodes the magnitude held in the supplied text, honouring an optional\n     * sign and the usual radix prefixes.</p>\n     *\n'
                '     * @param str  the text to decode, may be null\n     * @return the decoded magnitude, {@code null} if the input is {@code null}\n     */\n'
                '    public static BigInteger decodeMagnitude(final String str) {\n' + body + '    }\n\n')
    edit(CB, [
        (old_hop2, new_hop2),
        ('import java.lang.reflect.Modifier;\n', 'import java.lang.reflect.Modifier;\nimport java.math.BigInteger;\n'),
    ])

# ---- emit -02 patches ----
os.makedirs(pkg, exist_ok=True)
src_files = ["src/main/java/org/apache/commons/lang3/math/NumberUtils.java"] if arm == "control" else \
            ["src/main/java/org/apache/commons/lang3/ObjectUtils.java", "src/main/java/org/apache/commons/lang3/builder/CompareToBuilder.java", "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"]
open(os.path.join(pkg, "variant.patch"), "w").write(run(["git", "diff", "--"] + src_files))
open(os.path.join(pkg, "test.patch"), "w").write(run(["git", "diff", "--", "src/test/java/org/apache/commons/lang3/math/NumberUtilsTest.java"]))
print(arm, "built; modified files:", run(["git", "status", "--short"]).replace("\n", " "))
