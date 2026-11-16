"""OCFLB-JACKSONCORE-09: unit conversion (surrogate pair to code point scaling). Seed JKC-SURR-TREATMENT-04.
Facade UTF8Writer.convertSurrogate -> H1 CharTypes.codePointOf -> H2 TextBuffer.highSurrogateWeight (definer) -> H3 JsonStringEncoder.weight (adapter)
-> H4 NumberOutput.assemble -> H5 NumberInput.plane.
Usage: build_jackson09.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "JacksonCore"; SEED = "JKC-SURR-TREATMENT-04"
SRC = "src/main/java/com/fasterxml/jackson/core"
F = {"facade": f"{SRC}/io/UTF8Writer.java", "H1": f"{SRC}/io/CharTypes.java", "H2": f"{SRC}/util/TextBuffer.java",
     "H3": f"{SRC}/io/JsonStringEncoder.java", "H4": f"{SRC}/io/NumberOutput.java", "H5": f"{SRC}/io/NumberInput.java"}
T_TRIG = "src/test/java/com/fasterxml/jackson/core/io/TestUTF8Writer.java"; T_PIN = "src/test/java/com/fasterxml/jackson/core/util/TestTextBuffer.java"
H1 = '''    /**
     * Returns the code point that a surrogate pair stands for: the offsets of
     * the two surrogates within their blocks are extracted, the high offset is
     * weighted into code point units and the two contributions are combined
     * above the basic multilingual plane.
     *
     * @param hi the first (high) surrogate
     * @param lo the second (low) surrogate
     * @return the code point of the pair
     */
    public static int codePointOf(final int hi, final int lo) {
        final int hiOffset = hi - 0xD800;
        final int loOffset = lo - 0xDC00;
        final int high = TextBuffer.highSurrogateWeight(hiOffset);
        return JsonStringEncoder.weight(high, loOffset);
    }'''
H2_OK = "        final int bits = 10;"
H2_BUG = "        final int bits = 11;"
H2_COMP = "        final int bits = 9;"
H2 = '''    /**
     * Returns the contribution of the high surrogate of a pair to the code
     * point, in code point units: the offset of the high surrogate within its
     * block shifted left by the ten bits that the low surrogate occupies. So
     * an offset of 1 contributes 0x400, and the code point of a pair is
     * 0x10000 plus this contribution plus the offset of the low surrogate.
     *
     * @param hiOffset offset of the high surrogate within its block (0..0x3FF)
     * @return the contribution of the high surrogate, in code point units
     */
    public static int highSurrogateWeight(final int hiOffset) {
        if (hiOffset < 0 || hiOffset > 0x3FF) {
            throw new IllegalArgumentException("high surrogate offset out of range: " + hiOffset);
        }
%s
        return hiOffset << bits;
    }'''
H3_OK = "        final int offset = high + loOffset;"
H3_BUG = "        final int offset = (high << 1) + loOffset;"
H3_COMP = "        final int offset = (high >> 1) + loOffset;"
H3 = '''    /**
     * Combines the contribution of the high surrogate, already in code point
     * units, with the offset of the low surrogate into the offset of the pair
     * above the basic multilingual plane, and resolves the code point.
     *
     * @param high contribution of the high surrogate, in code point units
     * @param loOffset offset of the low surrogate within its block (0..0x3FF)
     * @return the code point of the pair
     */
    public static int weight(final int high, final int loOffset) {
        if (loOffset < 0 || loOffset > 0x3FF) {
            throw new IllegalArgumentException("low surrogate offset out of range: " + loOffset);
        }
%s
        return NumberOutput.assemble(0x10000, offset);
    }'''
H4 = '''    /**
     * Adds the offset of a surrogate pair to the base of the supplementary
     * planes and resolves the resulting code point.
     *
     * @param base first code point above the basic multilingual plane
     * @param offset offset of the pair above the base
     * @return the code point of the pair
     */
    public static int assemble(final int base, final int offset) {
        final int combined = base + offset;
        return NumberInput.plane(combined);
    }'''
H5 = '''    /**
     * Returns a code point of the supplementary planes, verifying that it lies
     * above the basic multilingual plane.
     *
     * @param codePoint the code point to verify
     * @return the code point
     */
    public static int plane(final int codePoint) {
        final int lowest = 0x10000;
        if (codePoint < lowest) {
            throw new IllegalArgumentException("code point below the supplementary planes: " + codePoint);
        }
        return codePoint;
    }'''
PIN = '''    /**
     * The contribution of the high surrogate is its offset shifted left by
     * the ten bits of the low surrogate: an offset of 1 contributes 0x400.
     */
    public void testHighSurrogateWeight()
    {
        assertEquals(0, TextBuffer.highSurrogateWeight(0));
        assertEquals(0x400, TextBuffer.highSurrogateWeight(1));
        assertEquals(0x800, TextBuffer.highSurrogateWeight(2));
        assertEquals(0x3D << 10, TextBuffer.highSurrogateWeight(0x3D));
        assertEquals(0xFFC00, TextBuffer.highSurrogateWeight(0x3FF));
        // U+1F600 is the pair D83D DE00: offsets 0x3D and 0x200
        assertEquals(0x1F600, 0x10000 + TextBuffer.highSurrogateWeight(0x3D) + 0x200);
    }'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "codePointOf", H1); B.add_import(work, F["H1"], "import com.fasterxml.jackson.core.util.TextBuffer;")
    B.replace_method(work, F["H2"], "highSurrogateWeight", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_method(work, F["H3"], "weight", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK))
    B.replace_once(work, F["H3"], "package com.fasterxml.jackson.core.io;\n\nimport com.fasterxml.jackson.core.util.TextBuffer;\n\n", "package com.fasterxml.jackson.core.io;\n\n")
    B.replace_method(work, F["H4"], "assemble", H4)
    B.replace_method(work, F["H5"], "plane", H5)
    B.insert_before_class_end(work, T_PIN, PIN)
spec = {"pair_id": "OCFLB-JACKSONCORE-09", "project": P, "bug": "09", "base_version": "JacksonCore-1f", "seed_variant": SEED,
  "family": "unit conversion (surrogate pair to code point scaling)",
  "convention": "highSurrogateWeight(hiOffset) = hiOffset << 10, the contribution of the high surrogate in code point units; the code point of a pair is 0x10000 + highSurrogateWeight(first - 0xD800) + (second - 0xDC00)",
  "effect": "the high-surrogate contribution is counted twice, so U+1F600 becomes U+2EA00 and its second UTF-8 byte is 0xAE (174) instead of 0x9F (159)",
  "equivalence_note": "shifting by 11 instead of 10 in the definer (arm A) and doubling the definer's 10-bit contribution before adding in the adapter (arm B) both yield 0x10000 + (hiOffset << 11) + loOffset for every input",
  "adapter_fault_note": "weight adds (high << 1) instead of high to the low offset",
  "trigger": "com.fasterxml.jackson.core.io.TestUTF8Writer::testJackson417", "expected_signature": "expected:<159> but was:<174>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "com.fasterxml.jackson.core.util.TestTextBuffer::testHighSurrogateWeight", "second_caller": None,
  "chain": {"facade": {"class": "com.fasterxml.jackson.core.io.UTF8Writer", "method": "convertSurrogate", "file": F["facade"]},
            "H1": {"class": "com.fasterxml.jackson.core.io.CharTypes", "method": "codePointOf", "file": F["H1"]}, "H2": {"class": "com.fasterxml.jackson.core.util.TextBuffer", "method": "highSurrogateWeight", "file": F["H2"]},
            "H3": {"class": "com.fasterxml.jackson.core.io.JsonStringEncoder", "method": "weight", "file": F["H3"]}, "H4": {"class": "com.fasterxml.jackson.core.io.NumberOutput", "method": "assemble", "file": F["H4"]},
            "H5": {"class": "com.fasterxml.jackson.core.io.NumberInput", "method": "plane", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "OCFLB-JACKSONCORE-09-DEFINER", "gold_role": "H2", "gold": {"class": "com.fasterxml.jackson.core.util.TextBuffer", "method": "highSurrogateWeight", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_COMP}, "declared_collateral": ["com.fasterxml.jackson.core.util.TestTextBuffer::testHighSurrogateWeight"]},
           "ADAPTER_FAULT": {"variant_id": "OCFLB-JACKSONCORE-09-ADAPTER", "gold_role": "H3", "gold": {"class": "com.fasterxml.jackson.core.io.JsonStringEncoder", "method": "weight", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_COMP}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/JacksonCore/bug-09"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
