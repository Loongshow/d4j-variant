"""ADV-OWNER-01: producer/consumer round trip. The ENCODER (longToHex) misplaces the upper eight hex digits but still
emits a spec-shaped 16-digit hex string; the DECODER (hexToLong) is correct and exposes it. One numeric assertion
compares the round-tripped value; both methods are executed. Gold = the producer. Usage: build_owner.py <work> <pkgdir>"""
import sys, json, os
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W, PKG = sys.argv[1], sys.argv[2]; os.makedirs(PKG, exist_ok=True)
CONV = "src/main/java/org/apache/commons/lang3/Conversion.java"; TEST = "src/test/java/org/apache/commons/lang3/ConversionTest.java"
B.reset(W)
B.add_test_method(W, TEST, '''    @Test
    public void testLang1185() {
        final long value = 0x9ABCDEF012345678L;
        final String hex = Conversion.longToHex(value, 0, "", 0, 16);
        assertEquals(value, Conversion.hexToLong(hex, 0, 0L, 0, 16));
    }''')
B.diff_to(W, f"{PKG}/test.patch", [TEST]); B.sh(["git", "checkout", "--", TEST], W)
old = "            shift = i * 4 + srcPos;\n            final int bits = (int)(0xF & (src >> shift));"
new = "            shift = i * 4 + srcPos + (i / 8);\n            final int bits = (int)(0xF & (src >> shift));"
B.replace_once(W, CONV, old, new)
B.diff_to(W, f"{PKG}/variant.patch", [CONV]); B.reset(W)
cfg = {"variant_id": "ADV-OWNER-01", "attack_id": "OWN-01", "title": "round trip: producer (longToHex) emits spec-shaped but wrong upper digits; consumer (hexToLong) is correct and exposes it",
       "project": "Lang", "base_version": "Lang-1f", "trigger": "org.apache.commons.lang3.ConversionTest::testLang1185", "related_tests": [], "test_file": TEST,
       "expected_signature": "AssertionFailedError", "assertion_class_regex": "AssertionFailedError|AssertionError",
       "gold": {"class": "org.apache.commons.lang3.Conversion", "method": "longToHex", "file": CONV, "decl": "public static String longToHex(final long src", "bug_line": new, "orig_line": old},
       "mechanism": "the failure is a mismatch between a value and its decode(encode(value)); encoder and decoder are symmetric siblings executed in the same test; the encoder's output is layout-conformant (16 valid hex digits), and lever L13 says models exonerate a spec-shaped writer and blame the reader",
       "classification": ["OWNERSHIP_TRAP", "ATTRIBUTION_TRAP", "FAILURE_SIGNAL_TRAP"], "family": "producer/consumer inversion in a round trip",
       "effect": "hex digits 8..15 are taken from one bit too high in the source long, so the emitted string is wrong for any value with a non-zero upper word while remaining a valid hex string",
       "predicted_wrong_top1": "org.apache.commons.lang3.Conversion#hexToLong (the consumer)",
       "roles": {"org.apache.commons.lang3.Conversion#hexToLong": "consumer", "org.apache.commons.lang3.Conversion#intToHexDigit": "sibling", "org.apache.commons.lang3.Conversion#hexDigitToInt": "sibling"},
       "candidates": ["org.apache.commons.lang3.Conversion#longToHex", "org.apache.commons.lang3.Conversion#hexToLong", "org.apache.commons.lang3.Conversion#intToHexDigit", "org.apache.commons.lang3.Conversion#hexDigitToInt"],
       "structure": "flat round trip, two executed production methods plus two digit helpers", "hops": 0, "chain": [],
       "changed_files": [{"file": CONV, "role": "gold"}, {"file": TEST, "role": "trigger"}], "package_dir": PKG}
json.dump(cfg, open(f"{PKG}/attack.json", "w"), indent=1); print("built ADV-OWNER-01")
