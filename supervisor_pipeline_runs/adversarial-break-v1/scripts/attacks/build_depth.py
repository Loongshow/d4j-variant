"""ADV-DEPTH-01: non-terminal gold (H3) with a correct but suspicious terminal (H5) whose javadoc promises the masking
the gold dropped. Base: historical Lang five-hop chain. Usage: build_depth.py <work> <pkgdir>"""
import sys, json, os
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W, PKG = sys.argv[1], sys.argv[2]; os.makedirs(PKG, exist_ok=True)
HIST = B.HIST_LANG_PATCH; HIST_TEST = HIST.replace("variant.patch", "test.patch")
BF = "src/main/java/org/apache/commons/lang3/BitField.java"; NU = "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"
TEST = "src/test/java/org/apache/commons/lang3/ConversionTest.java"
B.reset(W)
B.apply_patch(W, HIST_TEST); B.diff_to(W, f"{PKG}/test.patch", [TEST]); B.sh(["git", "checkout", "--", TEST], W)
B.apply_patch(W, HIST)
# (i) make the terminal H5 CORRECT again
B.replace_once(W, NU, "        final int shift = (index + at) * width;", "        final int shift = index * width + at;")
# (ii) misleading witness at H5: javadoc promises masking that the (correct, by contract) code does not do
B.replace_once(W, NU, "     * <p>Overlays a value onto a holder at the position given by its index.</p>",
               "     * <p>Overlays a value onto a holder at the position given by its index. The value is\n     * masked to the field so that no bits outside the field can disturb the holder.</p>")
# (iii) the real fault: H3 stops masking the words it widens (sign-extended ints pollute the holder downstream).
# Per lever L1/L2 the gold's contract wording is made to READ as textbook widening, so its body does not confess:
B.replace_once(W, BF, "     * <p>Widens the values of a run to the given field.</p>", "     * <p>Widens the values of a run to {@code long} words.</p>")
B.replace_once(W, BF, "     * @param field the field covering one value\n     * @return the widened values combined into the result",
               "     * @param field the field covering one value, forwarded to the combining stage\n     * @return the widened values combined into the result")
B.replace_once(W, BF, "            words[i] = run[i] & field;", "            words[i] = run[i];")
B.diff_to(W, f"{PKG}/variant.patch"); B.reset(W)
chain = [{"tag": "facade", "class": "org.apache.commons.lang3.Conversion", "method": "intArrayToLong", "decl": "public static long intArrayToLong(final int[] src"},
         {"tag": "H1", "class": "org.apache.commons.lang3.ArrayUtils", "method": "gather", "decl": "public static long gather(final int[] array"},
         {"tag": "H2", "class": "org.apache.commons.lang3.EnumUtils", "method": "compose", "decl": "public static long compose(final int[] run"},
         {"tag": "H3", "class": "org.apache.commons.lang3.BitField", "method": "widen", "decl": "public static long widen(final int[] run"},
         {"tag": "H4", "class": "org.apache.commons.lang3.ObjectUtils", "method": "combine", "decl": "public static long combine(final long[] words"},
         {"tag": "H5", "class": "org.apache.commons.lang3.math.NumberUtils", "method": "overlay", "decl": "public static long overlay(final long holder"}]
cfg = {"variant_id": "ADV-DEPTH-01", "attack_id": "DEP-01", "title": "non-terminal gold at H3 (mask dropped) with a deeper, correct, javadoc-loud terminal H5",
       "project": "Lang", "base_version": "Lang-1f", "trigger": "org.apache.commons.lang3.ConversionTest::testLang1112",
       "related_tests": ["org.apache.commons.lang3.ConversionTest::testIntArrayToLong"], "test_file": TEST,
       "expected_signature": "expected:<1311768467750121200> but was:<", "assertion_class_regex": "AssertionFailedError|AssertionError",
       "gold": {"class": "org.apache.commons.lang3.BitField", "method": "widen", "file": BF, "decl": "public static long widen(final int[] run",
                "bug_line": "            words[i] = run[i];", "orig_line": "            words[i] = run[i] & field;"},
       "mechanism": "the corruption (sign-extended words) is introduced at H3 by dropping a mask, but the place where corrupted bits visibly land in the result is the deepest hop H5, whose arithmetic is the natural suspect and whose javadoc promises the masking; depth prior + fix-looking terminal + doc/code mismatch all point at H5",
       "classification": ["DEPTH_PRIOR_TRAP", "ATTRIBUTION_TRAP", "OWNERSHIP_TRAP", "ARTIFACT"], "family": "dropped mask at an upstream stage",
       "effect": "negative int words are sign-extended into the long and pollute the bits above their field; the first assertion (positive word) passes, the second (0xCDF1F0C1) fails",
       "predicted_wrong_top1": "org.apache.commons.lang3.math.NumberUtils#overlay (H5)",
       "roles": {"org.apache.commons.lang3.math.NumberUtils#overlay": "deeper-stage", "org.apache.commons.lang3.ObjectUtils#combine": "deeper-stage",
                 "org.apache.commons.lang3.EnumUtils#compose": "shallower-stage", "org.apache.commons.lang3.ArrayUtils#gather": "shallower-stage", "org.apache.commons.lang3.Conversion#intArrayToLong": "facade"},
       "candidates": [f"{h['class']}#{h['method']}" for h in chain], "structure": "linear five-hop chain, gold at H3", "hops": 5, "chain": chain,
       "note_on_ownership": "a one-line repair at H5 ((word & field) << shift) also fixes the trigger; ownership is contested by design (E4) and the declared gold is the method whose javadoc contract is to mask",
       "changed_files": [{"file": "src/main/java/org/apache/commons/lang3/Conversion.java", "role": "facade"}] + [{"file": h["class"].replace(".", "/").join(["src/main/java/", ".java"]), "role": h["tag"]} for h in chain[1:]] + [{"file": TEST, "role": "trigger"}],
       "package_dir": PKG}
json.dump(cfg, open(f"{PKG}/attack.json", "w"), indent=1)
print("built ADV-DEPTH-01:", os.path.getsize(f"{PKG}/variant.patch"), "B variant")
