"""ADV-OVERLOAD-01: candidate overload (18 sibling Conversion methods executed) + boolean-only failure.
Gold: Conversion#hexToLong, buggy shift for hex digits at index >= 8 (upper 32 bits). No existing test covers that
region, so the full suite shows only the trigger. Usage: build_overload.py <work> <pkgdir>"""
import sys, json, os
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W, PKG = sys.argv[1], sys.argv[2]; os.makedirs(PKG, exist_ok=True)
CONV = "src/main/java/org/apache/commons/lang3/Conversion.java"; TEST = "src/test/java/org/apache/commons/lang3/ConversionTest.java"
B.reset(W)
# ---- test.patch: neutral name, boolean-only assertion, 18 sibling methods executed
B.add_import(W, TEST, "import static org.junit.Assert.assertTrue;")
B.add_test_method(W, TEST, '''    @Test
    public void testLang1180() {
        final long seed = 0x9ABCDEF012345678L;
        long acc = 0L;
        acc ^= Conversion.intArrayToLong(Conversion.longToIntArray(seed, 0, new int[2], 0, 2), 0, 0L, 0, 2);
        acc ^= Conversion.shortArrayToLong(Conversion.longToShortArray(seed, 0, new short[4], 0, 4), 0, 0L, 0, 4);
        acc ^= Conversion.byteArrayToLong(Conversion.longToByteArray(seed, 0, new byte[8], 0, 8), 0, 0L, 0, 8);
        acc ^= Conversion.hexToLong(Conversion.longToHex(seed, 0, "", 0, 16), 0, 0L, 0, 16);
        acc ^= Conversion.binaryToLong(Conversion.longToBinary(seed, 0, new boolean[64], 0, 64), 0, 0L, 0, 64);
        final int seed32 = (int) seed;
        int acc32 = 0;
        acc32 ^= Conversion.shortArrayToInt(Conversion.intToShortArray(seed32, 0, new short[2], 0, 2), 0, 0, 0, 2);
        acc32 ^= Conversion.byteArrayToInt(Conversion.intToByteArray(seed32, 0, new byte[4], 0, 4), 0, 0, 0, 4);
        acc32 ^= Conversion.hexToInt(Conversion.intToHex(seed32, 0, "", 0, 8), 0, 0, 0, 8);
        acc32 ^= Conversion.binaryToInt(Conversion.intToBinary(seed32, 0, new boolean[32], 0, 32), 0, 0, 0, 32);
        assertTrue(acc == seed && acc32 == 0);
    }''')
B.diff_to(W, f"{PKG}/test.patch", [TEST])
B.sh(["git", "checkout", "--", TEST], W)
# ---- variant.patch: one line in hexToLong
t, eol = B.read(W, CONV); k = t.index("public static long hexToLong"); seg = t[k:k + 1100]
old = "            shift = i * 4 + dstPos;"; assert seg.count(old) == 1
new = "            shift = i * 4 + dstPos + (i / 8);"
B.write(W, CONV, t[:k] + seg.replace(old, new, 1) + t[k + 1100:], eol)
B.diff_to(W, f"{PKG}/variant.patch", [CONV]); B.reset(W)
siblings = ["intArrayToLong", "longToIntArray", "shortArrayToLong", "longToShortArray", "byteArrayToLong", "longToByteArray", "longToHex",
            "binaryToLong", "longToBinary", "shortArrayToInt", "intToShortArray", "byteArrayToInt", "intToByteArray", "hexToInt", "intToHex", "binaryToInt", "intToBinary"]
cfg = {"variant_id": "ADV-OVERLOAD-01", "attack_id": "OVL-01", "title": "18 sibling conversions executed by one boolean-only test; fault in one",
       "project": "Lang", "base_version": "Lang-1f", "trigger": "org.apache.commons.lang3.ConversionTest::testLang1180", "related_tests": [],
       "test_file": TEST, "expected_signature": "AssertionFailedError", "assertion_class_regex": "AssertionFailedError|AssertionError",
       "gold": {"class": "org.apache.commons.lang3.Conversion", "method": "hexToLong", "file": CONV, "decl": "public static long hexToLong(final String src",
                "bug_line": new + "\n            final long bits = (0xfL & hexDigitToInt(src.charAt(i + srcPos))) << shift;", "orig_line": old + "\n            final long bits = (0xfL & hexDigitToInt(src.charAt(i + srcPos))) << shift;"},
       "mechanism": "the trigger executes 18 near-identical sibling methods and asserts only a boolean, so neither the failure text nor dynamic participation singles out a candidate; 18 candidates exceed the 10 ranking slots",
       "classification": ["CANDIDATE_OVERLOAD", "FAILURE_SIGNAL_TRAP"], "family": "candidate overload + coarse boolean failure",
       "effect": "hex digits at index 8..15 are placed one bit too high, so any 16-digit hex-to-long conversion of a value with a non-zero upper word is wrong; no existing test exercises that region",
       "predicted_wrong_top1": "any of the other 17 executed siblings, most likely intArrayToLong or byteArrayToLong (first in the test), or the gold pushed out of the top 10",
       "roles": {f"org.apache.commons.lang3.Conversion#{m}": "sibling" for m in siblings},
       "candidates": [f"org.apache.commons.lang3.Conversion#{m}" for m in siblings + ["hexToLong"]],
       "structure": "flat: one facade-less test calling 18 static siblings; no chain", "hops": 0, "chain": [],
       "changed_files": [{"file": CONV, "role": "gold"}, {"file": TEST, "role": "trigger"}], "package_dir": PKG}
json.dump(cfg, open(f"{PKG}/attack.json", "w"), indent=1)
print("built ADV-OVERLOAD-01:", os.path.getsize(f"{PKG}/variant.patch"), "B variant,", os.path.getsize(f"{PKG}/test.patch"), "B test")
