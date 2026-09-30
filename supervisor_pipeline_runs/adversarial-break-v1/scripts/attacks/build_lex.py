"""ADV-LEX-01: witness inversion on the five-hop chain. Gold H5 is renamed `apply`, loses its javadoc, gets generic
parameters and locals, and keeps the shift fault. A decoy `BitField.wordOffset` is added: failure vocabulary, the
constant Long.SIZE, a javadoc that states the CORRECT formula while the body computes the WRONG-shaped one (contract
incoherence, lever L1), executed by the trigger through a trivially true guard so it never affects the result.
Usage: build_lex.py <work> <pkgdir>"""
import sys, json, os
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W, PKG = sys.argv[1], sys.argv[2]; os.makedirs(PKG, exist_ok=True)
HIST = B.HIST_LANG_PATCH; HIST_TEST = HIST.replace("variant.patch", "test.patch")
BF = "src/main/java/org/apache/commons/lang3/BitField.java"; NU = "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"; OU = "src/main/java/org/apache/commons/lang3/ObjectUtils.java"
TEST = "src/test/java/org/apache/commons/lang3/ConversionTest.java"
B.reset(W)
B.apply_patch(W, HIST_TEST); B.diff_to(W, f"{PKG}/test.patch", [TEST]); B.sh(["git", "checkout", "--", TEST], W)
B.apply_patch(W, HIST)
# gold: strip every witness
t, eol = B.read(W, NU); k = t.index("    /**\n     * <p>Overlays a value onto a holder"); e = t.index("    }\n", t.index("public static long overlay")) + len("    }\n")
gold = """    public static long apply(final long h, final long w, final int i, final int a, final int n, final long f) {
        final int p = (i + a) * n;
        return (h & ~(f << p)) | (w << p);
    }
"""
B.write(W, NU, t[:k] + gold + t[e:], eol)
B.replace_once(W, OU, "            total = NumberUtils.overlay(total, words[i], i, at, width, field);", "            total = NumberUtils.apply(total, words[i], i, at, width, field);")
# decoy: loud, documented, executed, harmless, contract-incoherent
B.insert_after_method(W, BF, "widen", """    /**
     * <p>Returns the bit offset at which word {@code index} of a run is placed in a 64-bit
     * holder, {@code index * width + at}. Offsets at or beyond {@link Long#SIZE} do not fit
     * the holder and must be rejected by the caller.</p>
     *
     * @param index the index of the word within its run
     * @param at the bit position of the first word
     * @param width the width of a word in bits
     * @return the bit offset of the word
     */
    public static int wordOffset(final int index, final int at, final int width) {
        final int offset = (index + at) * width;
        return offset;
    }""")
B.replace_once(W, BF, "        final long[] words = new long[run.length];\n        for (int i = 0; i < run.length; i++) {\n            words[i] = run[i] & field;",
               "        if (wordOffset(run.length - 1, at, width) < 0) {\n            throw new IllegalArgumentException(\"run does not fit the holder\");\n        }\n        final long[] words = new long[run.length];\n        for (int i = 0; i < run.length; i++) {\n            words[i] = run[i] & field;")
B.diff_to(W, f"{PKG}/variant.patch"); B.reset(W)
chain = [{"tag": "facade", "class": "org.apache.commons.lang3.Conversion", "method": "intArrayToLong", "decl": "public static long intArrayToLong(final int[] src"},
         {"tag": "H1", "class": "org.apache.commons.lang3.ArrayUtils", "method": "gather", "decl": "public static long gather(final int[] array"},
         {"tag": "H2", "class": "org.apache.commons.lang3.EnumUtils", "method": "compose", "decl": "public static long compose(final int[] run"},
         {"tag": "H3", "class": "org.apache.commons.lang3.BitField", "method": "widen", "decl": "public static long widen(final int[] run"},
         {"tag": "H4", "class": "org.apache.commons.lang3.ObjectUtils", "method": "combine", "decl": "public static long combine(final long[] words"},
         {"tag": "H5", "class": "org.apache.commons.lang3.math.NumberUtils", "method": "apply", "decl": "public static long apply(final long h"}]
cfg = {"variant_id": "ADV-LEX-01", "attack_id": "LEX-01", "title": "witness inversion: generic undocumented gold (`apply`) vs a loud, documented, executed decoy (`wordOffset`) whose javadoc states the correct formula and whose body computes the wrong-shaped one",
       "project": "Lang", "base_version": "Lang-1f", "trigger": "org.apache.commons.lang3.ConversionTest::testLang1112",
       "related_tests": ["org.apache.commons.lang3.ConversionTest::testIntArrayToLong"], "test_file": TEST,
       "expected_signature": "expected:<64729929216> but was:<252851286>", "assertion_class_regex": "AssertionFailedError|AssertionError",
       "gold": {"class": "org.apache.commons.lang3.math.NumberUtils", "method": "apply", "file": NU, "decl": "public static long apply(final long h",
                "bug_line": "        final int p = (i + a) * n;", "orig_line": "        final int p = i * n + a;"},
       "mechanism": "every local witness that previously pointed at the gold (name, javadoc, parameter names, constant) is removed from the gold and planted on an executed decoy that additionally contradicts its own javadoc; the decoy's value never reaches the result",
       "classification": ["LEXICAL_TRAP", "ATTRIBUTION_TRAP", "CONTEXT_TRAP", "ARTIFACT"], "family": "word-offset convention (historical shift fault) with inverted witnesses",
       "effect": "int words are placed at (i + at) * width instead of i * width + at",
       "predicted_wrong_top1": "org.apache.commons.lang3.BitField#wordOffset",
       "roles": {"org.apache.commons.lang3.BitField#wordOffset": "decoy-lexical", "org.apache.commons.lang3.BitField#widen": "shallower-stage", "org.apache.commons.lang3.ObjectUtils#combine": "shallower-stage",
                 "org.apache.commons.lang3.EnumUtils#compose": "shallower-stage", "org.apache.commons.lang3.ArrayUtils#gather": "shallower-stage", "org.apache.commons.lang3.Conversion#intArrayToLong": "facade"},
       "candidates": [f"{h['class']}#{h['method']}" for h in chain] + ["org.apache.commons.lang3.BitField#wordOffset"], "structure": "five-hop chain with an executed decoy at H3's class", "hops": 5, "chain": chain,
       "changed_files": [{"file": "src/main/java/org/apache/commons/lang3/Conversion.java", "role": "facade"}, {"file": BF, "role": "H3 + decoy"}, {"file": NU, "role": "gold"}, {"file": OU, "role": "H4"}, {"file": TEST, "role": "trigger"}],
       "package_dir": PKG}
json.dump(cfg, open(f"{PKG}/attack.json", "w"), indent=1); print("built ADV-LEX-01")
