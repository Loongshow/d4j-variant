"""OCFLB-LANG-03: offset units (destination bit offset treated as a byte offset). Seed CONVERSION-LONG-TREATMENT-01.
Facade Conversion.intArrayToLong -> H1 ArrayUtils.gather -> H2 EnumUtils.compose (definer: origin bit position of the destination
window) -> H3 BitField.widen (adapter: shift = index*width + origin) -> H4 ObjectUtils.combine -> H5 NumberUtils.overlay.
Note: the unit factor is Byte.SIZE (bits per byte) rather than the word width: with the word width (32) the adapter's fault
`(index + origin) * width` admits no exact compensating edit at H2 for the trigger's origin 8 (every shift would be a multiple of
32), so gate V11b (PINNED_UNIQUE in both arms) could not hold. Byte.SIZE divides both trigger origins (8, 16) and yields the
same failing output (shift 64 == 0 mod 64, like the seed's 256).
Usage: build_lang03.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Lang"; SEED = "CONVERSION-LONG-TREATMENT-01"
M = "src/main/java/org/apache/commons/lang3/"; T = "src/test/java/org/apache/commons/lang3/"
F = {"facade": M + "Conversion.java", "H1": M + "ArrayUtils.java", "H2": M + "EnumUtils.java",
     "H3": M + "BitField.java", "H4": M + "ObjectUtils.java", "H5": M + "math/NumberUtils.java"}
T_TRIG = T + "ConversionTest.java"; T_PIN = T + "EnumUtilsTest.java"
H1 = '''    /**
     * <p>Gathers a run of elements of an {@code int} array into a {@code long}.</p>
     *
     * <p>The run of {@code count} elements starting at {@code startIndex} is
     * copied out, the origin of the destination window is resolved from the
     * bit position {@code at}, and the elements are widened into the result
     * from that origin, each element {@code Integer.SIZE} bits wide.</p>
     *
     * @param array  the array to gather from
     * @param startIndex  the index of the first element to gather
     * @param initial  the starting value of the result
     * @param at  the position, in bits, in the result at which the first element is placed
     * @param count  the number of elements to gather
     * @return the gathered value
     * @since 3.2
     */
    public static long gather(final int[] array, final int startIndex, final long initial, final int at, final int count) {
        final int width = Integer.SIZE;
        final long field = (1L << width) - 1;
        final int[] run = new int[count];
        System.arraycopy(array, startIndex, run, 0, count);
        final int origin = EnumUtils.compose(at, count, width);
        return BitField.widen(run, initial, origin, width, field);
    }'''
H2_OK = "        return at;"
H2_BUG = "        return at * Byte.SIZE;"
H2 = '''    /**
     * <p>Composes the origin of a destination window: the position, in bits,
     * within a 64-bit result at which the first value of a run of
     * {@code count} values, each {@code width} bits wide, is placed.</p>
     *
     * <p>The position {@code at} is already a bit position, so the origin
     * equals {@code at}: the first value of the run starts at bit {@code at}
     * and value {@code k} of the run starts at bit {@code at + k * width}.
     * The last value of the run has to start within the 64 bits of a
     * {@code long}: {@code at + (count - 1) * width} is below 64.</p>
     *
     * @param at the position, in bits, in the result of the first value
     * @param count the number of values in the run
     * @param width the width, in bits, of one value
     * @return the origin bit position of the destination window
     * @throws IllegalArgumentException if {@code at + (count - 1) * width >= 64}
     * @since 3.2
     */
    public static int compose(final int at, final int count, final int width) {
        final int last = at + (count - 1) * width;
        if (at < 0 || last >= Long.SIZE) {
            throw new IllegalArgumentException("the last value of a run of " + count + " values at bit " + at
                + " starts at bit " + last + ", outside " + Long.SIZE + " bits");
        }
%s
    }'''
H3_OK = "            shifts[i] = i * width + origin;"
H3_BUG = "            shifts[i] = i * width + origin * Byte.SIZE;"
H3 = '''    /**
     * <p>Widens the values of a run into words placed from the given origin.</p>
     *
     * <p>Each value is masked to the field, and each value of the run is
     * given the shift at which it is placed in the result: the values follow
     * one another from the origin, each one {@code width} bits further along
     * than the value before it.</p>
     *
     * @param run the values to widen
     * @param initial the starting value of the result
     * @param origin the position in the result of the first value
     * @param width the width of a value
     * @param field the field covering one value
     * @return the widened values combined into the result
     * @since 3.2
     */
    public static long widen(final int[] run, final long initial, final int origin, final int width, final long field) {
        final long[] words = new long[run.length];
        final int[] shifts = new int[run.length];
        for (int i = 0; i < run.length; i++) {
            words[i] = run[i] & field;
%s
        }
        return ObjectUtils.combine(words, shifts, initial, field);
    }'''
H4 = '''    /**
     * Combine a run of words into a single value, each word placed at its shift.
     *
     * @param words the words to combine
     * @param shifts the shift at which each word is placed
     * @param initial the starting value of the result
     * @param field the field covering one word
     * @return the combined value
     * @since 3.2
     */
    public static long combine(final long[] words, final int[] shifts, final long initial, final long field) {
        long total = initial;
        for (int i = 0; i < words.length; i++) {
            total = NumberUtils.overlay(total, words[i], shifts[i], field);
        }
        return total;
    }'''
H5 = '''    /**
     * <p>Overlays a word onto a holder at the given shift, replacing the field
     * of the holder that the word covers.</p>
     *
     * @param holder  the value to overlay onto
     * @param word  the word to place
     * @param shift  the shift at which the word is placed
     * @param field  the field covering one word
     * @return the holder with the word placed
     * @since 3.2
     */
    public static long overlay(final long holder, final long word, final int shift, final long field) {
        final long cleared = holder & ~(field << shift);
        return cleared | (word << shift);
    }'''
PIN_ANCHOR = "    }\n\n}\n\nenum Traffic {"
PIN = '''    }

    /**
     * The origin of a destination window is the bit position {@code at} itself.
     */
    @Test
    public void testCompose() {
        assertEquals(8, EnumUtils.compose(8, 1, 32));
        assertEquals(16, EnumUtils.compose(16, 1, 32));
        assertEquals(0, EnumUtils.compose(0, 2, 32));
        assertEquals(24, EnumUtils.compose(24, 1, 32));
        assertEquals(40, EnumUtils.compose(40, 3, 8));
        assertEquals(5, EnumUtils.compose(5, 1, 16));
        try {
            EnumUtils.compose(64, 1, 32);
            Assert.fail("a run starting at bit 64 was accepted");
        } catch (final IllegalArgumentException e) {
            // expected
        }
    }

}

enum Traffic {'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "gather", H1)
    B.replace_method(work, F["H2"], "compose", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_method(work, F["H3"], "widen", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK))
    B.replace_method(work, F["H4"], "combine", H4)
    B.replace_method(work, F["H5"], "overlay", H5)
    B.replace_once(work, T_PIN, PIN_ANCHOR, PIN)
H3_COMP = "            shifts[i] = i * width + origin / Byte.SIZE;"   # absorbs a definer returning at * Byte.SIZE
H2_COMP = "        return at / Byte.SIZE;"                          # absorbs an adapter scaling the origin by Byte.SIZE
spec = {"pair_id": "OCFLB-LANG-03", "project": P, "bug": "03", "base_version": "Lang-1f", "seed_variant": SEED,
  "family": "offset units (destination bit offset treated as a byte offset)",
  "convention": "compose(at, count, width) returns the origin bit position of the destination window, which equals the bit position at; value k of the run starts at bit at + k * width, so widen assigns value i the shift i * width + origin",
  "effect": "the first word lands at bit 64 (== bit 0 after the 6-bit shift reduction) instead of bit 8, so intArrayToLong(src, 1, 0L, 8, 1) yields 0x0F123456 (252851286) instead of 0xF12345600 (64729929216)",
  "equivalence_note": "the definer returning at * Byte.SIZE with a correct adapter (arm A) and a correct definer with the adapter computing i * width + origin * Byte.SIZE (arm B) both give the shift i * width + at * Byte.SIZE for every input, hence identical results and identical failure text; existing callers use at == 0 and are unaffected in both arms",
  "adapter_fault_note": "widen scales the origin by Byte.SIZE (treats the bit position as a byte offset) before adding it to the word offset; the compensating repairs are exact because Byte.SIZE divides both trigger origins (8 and 16), whereas a word-width factor (32) would admit no exact compensating edit at H2",
  "trigger": "org.apache.commons.lang3.ConversionTest::testLang1112", "expected_signature": "expected:<64729929216> but was:<252851286>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.apache.commons.lang3.EnumUtilsTest::testCompose", "second_caller": None,
  "chain": {"facade": {"class": "org.apache.commons.lang3.Conversion", "method": "intArrayToLong", "file": F["facade"]},
            "H1": {"class": "org.apache.commons.lang3.ArrayUtils", "method": "gather", "file": F["H1"]}, "H2": {"class": "org.apache.commons.lang3.EnumUtils", "method": "compose", "file": F["H2"]},
            "H3": {"class": "org.apache.commons.lang3.BitField", "method": "widen", "file": F["H3"]}, "H4": {"class": "org.apache.commons.lang3.ObjectUtils", "method": "combine", "file": F["H4"]},
            "H5": {"class": "org.apache.commons.lang3.math.NumberUtils", "method": "overlay", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "OCFLB-LANG-03-DEFINER", "gold_role": "H2", "gold": {"class": "org.apache.commons.lang3.EnumUtils", "method": "compose", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_COMP}, "declared_collateral": ["org.apache.commons.lang3.EnumUtilsTest::testCompose"]},
           "ADAPTER_FAULT": {"variant_id": "OCFLB-LANG-03-ADAPTER", "gold_role": "H3", "gold": {"class": "org.apache.commons.lang3.BitField", "method": "widen", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_COMP}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Lang/bug-03"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
