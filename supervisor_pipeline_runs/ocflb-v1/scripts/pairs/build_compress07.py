"""OCFLB-COMPRESS-07: byte interpretation (signed vs unsigned header byte) in the tar header checksum. Seed CMP-CKSUM-TREATMENT-01.
Facade TarUtils.computeCheckSum -> H1 TarBuffer.tally -> H2 AsiExtraField.magnitudeOf (definer) -> H3 ExtraFieldUtils.widen (adapter)
-> H4 ZipLong.byteValue -> H5 IOUtils.sumPair.
The two faults are the weight given to the top bit of a header byte: +128 (a magnitude bit, the documented convention) versus
-128 (a sign bit). Flipping that weight in H2 or in H3 gives the same signed sum; flipping it in both restores the unsigned sum.
Usage: build_compress07.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Compress"; SEED = "CMP-CKSUM-TREATMENT-01"
SRC = "src/main/java/org/apache/commons/compress"; TST = "src/test/java/org/apache/commons/compress"
F = {"facade": f"{SRC}/archivers/tar/TarUtils.java", "H1": f"{SRC}/archivers/tar/TarBuffer.java", "H2": f"{SRC}/archivers/zip/AsiExtraField.java",
     "H3": f"{SRC}/archivers/zip/ExtraFieldUtils.java", "H4": f"{SRC}/archivers/zip/ZipLong.java", "H5": f"{SRC}/utils/IOUtils.java"}
T_TRIG = f"{TST}/archivers/tar/TarArchiveEntryTest.java"; T_PIN = f"{TST}/archivers/zip/AsiExtraFieldTest.java"
H1 = '''    /**
     * Accumulates the checksum of a byte range of a header record: the
     * magnitude of every byte of the range is folded into a running sum.
     *
     * @param buf the header bytes
     * @param offset the first index of the range
     * @param length the number of bytes in the range
     * @return the accumulated checksum of the range
     */
    public static long tally(final byte[] buf, final int offset, final int length) {
        long sum = 0;
        final int end = offset + length;
        for (int i = offset; i < end; i++) {
            final int magnitude = AsiExtraField.magnitudeOf(buf[i]);
            sum = ExtraFieldUtils.widen(sum, magnitude);
        }
        return sum;
    }'''
H2_OK = "        return low + top;"
H2_BUG = "        return low - top;"
H2 = '''    /**
     * Returns the magnitude of a single header byte: the unsigned value of its
     * eight bits, in the range 0 to 255. The top bit of the byte is a
     * magnitude bit with the weight 128, like any other bit of the byte; it is
     * never treated as a sign bit, so a byte with the top bit set has a
     * magnitude of 128 or more.
     *
     * @param raw the byte of the header
     * @return the magnitude of the byte, 0 to 255
     */
    public static int magnitudeOf(final byte raw) {
        final int low = raw & 0x7f;
        final int top = raw & 0x80;
%s
    }'''
H3_OK = "        final long widened = low + top;"
H3_BUG = "        final long widened = low - top;"
H3 = '''    /**
     * Widens the magnitude of a single header byte to the type of the checksum
     * accumulator and folds it into the running sum. The widened value keeps
     * the magnitude as it is: the seven low bits are carried over and the
     * top-bit term is added with the weight the magnitude gives it.
     *
     * @param sum the running sum of the header bytes seen so far
     * @param magnitude the magnitude of the byte, 0 to 255
     * @return the running sum including this byte
     */
    public static long widen(final long sum, final int magnitude) {
        final long low = magnitude & 0x7f;
        final long top = magnitude - low;
%s
        return ZipLong.byteValue(sum, widened);
    }'''
H4 = '''    /**
     * Accounts a single header byte to a running checksum: the widened value
     * of the byte is the amount added to the running sum.
     *
     * @param sum the running sum of the header bytes seen so far
     * @param widened the widened value of the byte
     * @return the running sum including this byte
     */
    public static long byteValue(final long sum, final long widened) {
        final long value = widened;
        final long total = IOUtils.sumPair(sum, value);
        return total;
    }'''
H5 = '''    /**
     * Adds up a pair of values.
     *
     * @param first the first value of the pair
     * @param second the second value of the pair
     * @return the sum of the pair
     */
    public static long sumPair(final long first, final long second) {
        long total = first;
        total += second;
        return total;
    }'''
PIN = '''    /**
     * The magnitude of a header byte is the unsigned value of its eight bits:
     * a byte with the top bit set has a magnitude of 128 or more.
     */
    public void testMagnitudeOf() {
        assertEquals(0, AsiExtraField.magnitudeOf((byte) 0));
        assertEquals(1, AsiExtraField.magnitudeOf((byte) 1));
        assertEquals(0x7f, AsiExtraField.magnitudeOf((byte) 0x7f));
        for (int value = 0x80; value <= 0xff; value++) {
            assertEquals(value, AsiExtraField.magnitudeOf((byte) value));
        }
        assertEquals(0xc3, AsiExtraField.magnitudeOf((byte) 0xc3));
        assertEquals(0xa9, AsiExtraField.magnitudeOf((byte) 0xa9));
        assertEquals(255, AsiExtraField.magnitudeOf((byte) -1));
    }'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "tally", H1)
    B.replace_once(work, F["H1"], "import org.apache.commons.compress.utils.IOUtils;\n", "import org.apache.commons.compress.archivers.zip.AsiExtraField;\nimport org.apache.commons.compress.archivers.zip.ExtraFieldUtils;\n")
    B.replace_method(work, F["H2"], "magnitudeOf", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_method(work, F["H3"], "widen", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK))
    B.replace_method(work, F["H4"], "byteValue", H4); B.add_import(work, F["H4"], "import org.apache.commons.compress.utils.IOUtils;")
    B.replace_method(work, F["H5"], "sumPair", H5)
    B.replace_once(work, F["H5"], "import org.apache.commons.compress.archivers.zip.ZipLong;\n", "")
    B.insert_before_class_end(work, T_PIN, PIN)
spec = {"pair_id": "OCFLB-COMPRESS-07", "project": P, "bug": "07", "base_version": "Compress-1f", "seed_variant": SEED,
  "family": "byte interpretation (signed vs unsigned header byte)",
  "convention": "magnitudeOf(b) = unsigned magnitude of a header byte, 0..255: the top bit is a magnitude bit with weight +128 ((b & 0x7f) + (b & 0x80)), never a sign bit; the tar header checksum is the sum of these magnitudes",
  "effect": "bytes with the top bit set contribute their signed value (-128..-1) instead of their magnitude (128..255), so the checksum of the UTF-8 header {0xC3, 0xA9, 'a', 0} is -51 instead of 461",
  "equivalence_note": "the unsigned magnitude is low + top and the signed value is low - top (low = the seven low bits, top = the top-bit term); flipping the sign of the top-bit term in the definer (arm A) or in the adapter (arm B) yields the same signed value for every byte, hence the same sum for every header, and flipping it in both restores the unsigned sum",
  "adapter_fault_note": "widen subtracts the top-bit term of the magnitude instead of adding it (gives the top bit the weight of a sign bit) before folding the value into the running sum",
  "trigger": "org.apache.commons.compress.archivers.tar.TarArchiveEntryTest::testCompress194", "expected_signature": "expected:<461> but was:<-51>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testMagnitudeOf", "second_caller": None,
  "chain": {"facade": {"class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "computeCheckSum", "file": F["facade"]},
            "H1": {"class": "org.apache.commons.compress.archivers.tar.TarBuffer", "method": "tally", "file": F["H1"]}, "H2": {"class": "org.apache.commons.compress.archivers.zip.AsiExtraField", "method": "magnitudeOf", "file": F["H2"]},
            "H3": {"class": "org.apache.commons.compress.archivers.zip.ExtraFieldUtils", "method": "widen", "file": F["H3"]}, "H4": {"class": "org.apache.commons.compress.archivers.zip.ZipLong", "method": "byteValue", "file": F["H4"]},
            "H5": {"class": "org.apache.commons.compress.utils.IOUtils", "method": "sumPair", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "OCFLB-COMPRESS-07-DEFINER", "gold_role": "H2", "gold": {"class": "org.apache.commons.compress.archivers.zip.AsiExtraField", "method": "magnitudeOf", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_BUG}, "declared_collateral": ["org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testMagnitudeOf"]},
           "ADAPTER_FAULT": {"variant_id": "OCFLB-COMPRESS-07-ADAPTER", "gold_role": "H3", "gold": {"class": "org.apache.commons.compress.archivers.zip.ExtraFieldUtils", "method": "widen", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_BUG}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Compress/bug-07"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
