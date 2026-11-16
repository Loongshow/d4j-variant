"""ADV-MASK-01 (idea CTX-01): pre-positioned field contract. Gold H2 EnumUtils.compose builds an UNPOSITIONED field with the
verbatim template line (reads innocent); H3 masks with the facade's own 0xffffffffL idiom and merely forwards the field;
H5 NumberUtils.overlay shifts the field by index*width but the word by at+index*width (an asymmetry that reads as the bug).
A second REAL consumer, BitField.setValue, delegates to overlay with a positioned field, so 'fix overlay' breaks BitFieldTest.
Usage: build_mask.py <work> <pkgdir>"""
import sys, json, os
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W, PKG = sys.argv[1], sys.argv[2]; os.makedirs(PKG, exist_ok=True)
HIST = B.HIST_LANG_PATCH; HIST_TEST = HIST.replace("variant.patch", "test.patch")
EU = "src/main/java/org/apache/commons/lang3/EnumUtils.java"; BF = "src/main/java/org/apache/commons/lang3/BitField.java"
NU = "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"; TEST = "src/test/java/org/apache/commons/lang3/ConversionTest.java"
B.reset(W)
B.apply_patch(W, HIST_TEST); B.diff_to(W, f"{PKG}/test.patch", [TEST]); B.sh(["git", "checkout", "--", TEST], W)
B.apply_patch(W, HIST)
# H2 (gold): javadoc says it derives the field of the first value; the body builds it unpositioned (the template's verbatim line)
B.replace_once(W, EU, "     * <p>Composes a run of {@code int} values into a {@code long}.</p>",
               "     * <p>Composes a run of {@code int} values into a {@code long}, deriving the value\n     * width and the field of the first value.</p>")
# H3: mask with the facade's own idiom; the field is only forwarded
B.replace_once(W, BF, "            words[i] = run[i] & field;", "            words[i] = 0xffffffffL & run[i];")
B.replace_once(W, BF, "     * @param field the field covering one value\n     * @return the widened values combined into the result",
               "     * @param field the field of the first value, forwarded to the combining stage\n     * @return the widened values combined into the result")
# H5: correct for a POSITIONED field; the visible asymmetry is the decoy
B.replace_once(W, NU, "        final int shift = (index + at) * width;\n        return (holder & ~(field << shift)) | (word << shift);",
               "        final long m = field << (index * width);\n        final int shift = at + index * width;\n        return (holder & ~m) | ((word << shift) & m);")
B.replace_once(W, NU, "     * @param at  the position in the holder at which the first value of the run is placed\n     * @param width  the width of a value\n     * @param field  the field covering one value",
               "     * @param at  the position of the lsb of the first value\n     * @param width  the width of a value\n     * @param field  the field of the first value of the run")
# second real consumer pins overlay's positioned-field contract
B.replace_once(W, BF, "        return (holder & ~_mask) | ((value << _shift_count) & _mask);",
               "        return (int) NumberUtils.overlay(holder, value, 0, _shift_count, Integer.bitCount(_mask), _mask);")
B.add_import(W, BF, "import org.apache.commons.lang3.math.NumberUtils;")
B.diff_to(W, f"{PKG}/variant.patch"); B.reset(W)
chain = [{"tag": "facade", "class": "org.apache.commons.lang3.Conversion", "method": "intArrayToLong", "decl": "public static long intArrayToLong(final int[] src"},
         {"tag": "H1", "class": "org.apache.commons.lang3.ArrayUtils", "method": "gather", "decl": "public static long gather(final int[] array"},
         {"tag": "H2", "class": "org.apache.commons.lang3.EnumUtils", "method": "compose", "decl": "public static long compose(final int[] run"},
         {"tag": "H3", "class": "org.apache.commons.lang3.BitField", "method": "widen", "decl": "public static long widen(final int[] run"},
         {"tag": "H4", "class": "org.apache.commons.lang3.ObjectUtils", "method": "combine", "decl": "public static long combine(final long[] words"},
         {"tag": "H5", "class": "org.apache.commons.lang3.math.NumberUtils", "method": "overlay", "decl": "public static long overlay(final long holder"}]
cfg = {"variant_id": "ADV-MASK-01", "attack_id": "CTX-01", "title": "pre-positioned field contract: unpositioned field built at H2 with the template's verbatim line; H5's field/word shift asymmetry reads as the bug; a second real consumer pins H5",
       "project": "Lang", "base_version": "Lang-1f", "trigger": "org.apache.commons.lang3.ConversionTest::testLang1112",
       "related_tests": ["org.apache.commons.lang3.ConversionTest::testIntArrayToLong", "org.apache.commons.lang3.BitFieldTest::testSetValue"], "test_file": TEST,
       "expected_signature": "expected:<64729929216> but was:<", "assertion_class_regex": "AssertionFailedError|AssertionError",
       "gold": {"class": "org.apache.commons.lang3.EnumUtils", "method": "compose", "file": EU, "decl": "public static long compose(final int[] run",
                "bug_line": "        final long field = (1L << width) - 1;", "orig_line": "        final long field = ((1L << width) - 1) << at;"},
       "mechanism": "the locally inconsistent formula sits at the deepest hop (overlay shifts the field by index*width but the word by at+index*width), which is where both models look for the fault; the gold's line is the verbatim line of a previously validated chain and reads as correct; a passing second consumer makes 'fix overlay' wrong",
       "classification": ["DEPTH_PRIOR_TRAP", "CONTEXT_TRAP", "ATTRIBUTION_TRAP", "OWNERSHIP_TRAP"], "family": "positioned versus unpositioned field convention split across H2 and H5",
       "effect": "the field is never shifted to the destination bit position, so the placed word is masked at the wrong bits",
       "predicted_wrong_top1": "org.apache.commons.lang3.math.NumberUtils#overlay ('the field is not shifted by at')",
       "roles": {"org.apache.commons.lang3.math.NumberUtils#overlay": "deeper-stage", "org.apache.commons.lang3.ObjectUtils#combine": "deeper-stage", "org.apache.commons.lang3.BitField#widen": "deeper-stage",
                 "org.apache.commons.lang3.ArrayUtils#gather": "shallower-stage", "org.apache.commons.lang3.Conversion#intArrayToLong": "facade", "org.apache.commons.lang3.BitField#setValue": "consumer"},
       "candidates": [f"{h['class']}#{h['method']}" for h in chain] + ["org.apache.commons.lang3.BitField#setValue"], "structure": "five-hop chain, gold at H2, second real consumer of H5", "hops": 5, "chain": chain,
       "changed_files": [{"file": "src/main/java/org/apache/commons/lang3/Conversion.java", "role": "facade"}, {"file": EU, "role": "gold H2"}, {"file": BF, "role": "H3 + second consumer"}, {"file": "src/main/java/org/apache/commons/lang3/ObjectUtils.java", "role": "H4"}, {"file": NU, "role": "H5"}, {"file": TEST, "role": "trigger"}],
       "package_dir": PKG}
json.dump(cfg, open(f"{PKG}/attack.json", "w"), indent=1); print("built ADV-MASK-01:", os.path.getsize(f"{PKG}/variant.patch"), "B variant")
