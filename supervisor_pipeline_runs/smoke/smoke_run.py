"""
SMOKE RUN ONLY - not a real variant. Runs the supervisor's unmodified
generate_chain.main() end-to-end with the single LLM design call replaced by
a hand-written ChainBugDesign, so every mechanical stage (target/host
selection, test insertion, defects4j compile/test, CONTROL validation,
collateral gates, 3-file chain transform, packaging, fresh-checkout
reproduction) is exercised without an API key. No supervisor file is
modified; the monkeypatch lives only in this process. Nothing is written to
an LLM cache (design_chain_bug itself is bypassed).
"""
import os, sys
THESIS = "/Users/shawnli/Desktop/thesis"
RUNROOT = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
sys.path.insert(0, THESIS)
import chain_design, generate_chain

CHECKOUT = os.path.join(RUNROOT, "lang-1f-checkout")
FACADE = os.path.join(CHECKOUT, "src/main/java/org/apache/commons/lang3/Conversion.java")
ORIG = "final long mask = 0xffffffffL << shift;"
BUGGY = "final long mask = 0xffffffffL << (i * 32);"
n = open(FACADE).read().count(ORIG)
assert n == 1, f"bug line must be unique in facade file, found {n}"

DESIGN = chain_design.ChainBugDesign(
    original_line_text=ORIG,
    buggy_line_text=BUGGY,
    bug_rationale="Smoke-test synthetic bug: the clearing mask is shifted by the int index only and "
                  "forgets dstPos, so only calls with a non-zero dstPos are affected.",
    hop1_method_name="mergeWordBits",
    hop1_full_method=(
        "public static long mergeWordBits(final int[] src, final int srcPos, final long dstInit, "
        "final int dstPos, final int nInts) {\n"
        "    return org.apache.commons.lang3.text.StrTokenizer.spliceTokenRange(src, srcPos, dstInit, dstPos, nInts);\n"
        "}"
    ),
    hop2_method_name="spliceTokenRange",
    hop2_full_method=(
        "public static long spliceTokenRange(final int[] src, final int srcPos, final long dstInit, "
        "final int dstPos, final int nInts) {\n"
        "    if ((src.length == 0 && srcPos == 0) || 0 == nInts) {\n"
        "        return dstInit;\n"
        "    }\n"
        "    if ((nInts - 1) * 32 + dstPos >= 64) {\n"
        "        throw new IllegalArgumentException(\n"
        "            \"(nInts-1)*32+dstPos is greather or equal to than 64\");\n"
        "    }\n"
        "    long out = dstInit;\n"
        "    int shift = 0;\n"
        "    for (int i = 0; i < nInts; i++ ) {\n"
        "        shift = i * 32 + dstPos;\n"
        "        final long bits = ((0xffffffffL & src[i + srcPos]) << shift);\n"
        "        final long mask = 0xffffffffL << shift;\n"
        "        out = (out & ~mask) | bits;\n"
        "    }\n"
        "    return out;\n"
        "}"
    ),
    lie_sentence=("Each source int is masked to 32 bits and shifted into position in a single forward "
                  "pass, clearing the destination window with a matching mask before the new bits are "
                  "OR-ed in, so the result is assembled in place without intermediate copies."),
    new_test_source=(
        "    @Test\n"
        "    public void testIntArrayToLongWithDstPos() {\n"
        "        final int[] src = new int[]{0xCDF1F0C1, 0x0F123456, 0x78000000};\n"
        "        assertEquals(0xCDF1F0C19ABCDEF0L, Conversion.intArrayToLong(src, 0, 0x123456789ABCDEF0L, 32, 1));\n"
        "        assertEquals(0x123456780F123456L, Conversion.intArrayToLong(src, 1, 0x123456789ABCDEF0L, 0, 1));\n"
        "    }"
    ),
    predicted_correct_value="0xCDF1F0C19ABCDEF0L then 0x123456780F123456L",
    predicted_buggy_value="0xDFF5F6F900000000L for the first assertion (second unchanged)",
    facade_replacement_body="return org.apache.commons.lang3.math.Fraction.mergeWordBits(src, srcPos, dstInit, dstPos, nInts);",
)

chain_design.make_client = lambda: None
chain_design.design_chain_bug = lambda *a, **k: DESIGN

sys.argv = [
    "generate_chain.py", "--project", "Lang", "--seed", "1",
    "--checkout-dir", CHECKOUT,
    "--source-root", "src/main/java", "--test-root", "src/test/java",
    "--out-dir", os.path.join(RUNROOT, "smoke/out"),
    "--log-dir", os.path.join(RUNROOT, "smoke/logs"),
    "--repro-scratch-dir", os.path.join(RUNROOT, "smoke/repro-checkout"),
    "--min-class-lines", "1200", "--min-host-lines", "900",
]
generate_chain.main()
