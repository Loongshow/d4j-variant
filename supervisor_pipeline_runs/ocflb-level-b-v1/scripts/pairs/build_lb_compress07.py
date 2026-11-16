"""LB-COMPRESS-07 (Level B): byte interpretation (signed vs unsigned header byte) in the tar header checksum. Converted from
OCFLB-COMPRESS-07 (seed CMP-CKSUM-TREATMENT-01).
Facade TarUtils.computeCheckSum -> H1 TarBuffer.tally -> H2 AsiExtraField.magnitudeOf (definer) -> H3 ExtraFieldUtils.widen (adapter)
-> H4 ZipLong.byteValue -> H5 IOUtils.sumPair.
Convention decided externally: header bytes are unsigned (0..255), as the production second caller TarBuffer.digest (sums magnitudeOf
directly into a long) and its test (461 for the UTF-8 header) rely on. H2/H3 javadocs state purpose only.
Both hops split their input into its seven low bits (low = x & 0x7f) and the part above them (top = x - low) and recombine the two
parts. For a byte, top is -128 when the top bit is set and 0 otherwise, so in magnitudeOf low - top is the unsigned value (0..255)
and low + top is the sign-extended byte (-128..127); for an unsigned value, top is 128 or 0, so in widen low + top is the identity
and low - top re-signs the value. DEFINER arm: magnitudeOf recombines with low + top (the top part keeps the weight of a sign bit).
ADAPTER arm: widen recombines with low - top. Both arms give the signed sum for every header. The map x -> 2*(x & 0x7f) - x is an
involution, so the compensating edit at the other hop restores the trigger while the pin and the second caller keep exposing H2
(PINNED_UNIQUE in both arms).
Revision 2 (after blinded grading): in revision 1 magnitudeOf was the canonical idiom raw & 0xff, so a grader of the ADAPTER arm's
two-hop packet discounted H2 outright and confidently named widen. In revision 2 the two hops have the same textual form (split,
recombine), and the arm's two packets differ from each other only in the recombining operator, so the packet does not say which hop
should carry the transform; only the convention (the pin and the second caller) does.
Design note: the narrowing form of the adapter fault ("final long value = (byte) magnitude;") was built and validated first; it is
not invertible by any byte-valued H2 edit ((byte) x depends only on x mod 256 and never exceeds 127), so V11b classified the ADAPTER
arm MOSTLY_UNIQUE (see projects/Compress/bug-07/rejected_bytecast_validation_run.log). The split form is used instead.
Usage: build_lb_compress07.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Compress"; SEED = "CMP-CKSUM-TREATMENT-01"
SRC = "src/main/java/org/apache/commons/compress"; TST = "src/test/java/org/apache/commons/compress"
F = {"facade": f"{SRC}/archivers/tar/TarUtils.java", "H1": f"{SRC}/archivers/tar/TarBuffer.java", "H2": f"{SRC}/archivers/zip/AsiExtraField.java",
     "H3": f"{SRC}/archivers/zip/ExtraFieldUtils.java", "H4": f"{SRC}/archivers/zip/ZipLong.java", "H5": f"{SRC}/utils/IOUtils.java"}
F["EXT"] = F["H1"]   # the production second caller TarBuffer.digest lives in the H1 class (tar side), another class than H2
T_TRIG = f"{TST}/archivers/tar/TarArchiveEntryTest.java"; T_PIN = f"{TST}/archivers/zip/AsiExtraFieldTest.java"; T_EXT = f"{TST}/archivers/tar/TarBufferTest.java"
H1 = '''    /**
     * Accumulates the checksum of a byte range of a header record: the
     * value of every byte of the range is folded into a running sum.
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
H2_OK = "        final int value = low - top;"      # unsigned value of the byte: 0..255 (top is -128 for a byte with the top bit set, 0 otherwise)
H2_BUG = "        final int value = low + top;"     # DEFINER arm: the sign-extended byte, -128..127 (the top part keeps the weight of a sign bit)
H2 = '''    /**
     * Returns the value of a single header byte as an int.
     *
     * @param raw the byte of the header
     * @return the value of the byte
     */
    public static int magnitudeOf(final byte raw) {
        final int low = raw & 0x7f;
        final int top = raw - low;
%s
        return value;
    }'''
H3_OK = "        final long value = low + top;"
H3_BUG = "        final long value = low - top;"
H3 = '''    /**
     * Folds the value of a header byte into the running checksum.
     *
     * @param sum the running sum of the header bytes seen so far
     * @param magnitude the value of the byte
     * @return the running sum including this byte
     */
    public static long widen(final long sum, final int magnitude) {
        final long low = magnitude & 0x7f;
        final long top = magnitude - low;
%s
        return ZipLong.byteValue(sum, value);
    }'''
H4 = '''    /**
     * Accounts a single header byte to a running checksum: the folded value
     * of the byte is the amount added to the running sum.
     *
     * @param sum the running sum of the header bytes seen so far
     * @param value the folded value of the byte
     * @return the running sum including this byte
     */
    public static long byteValue(final long sum, final long value) {
        final long amount = value;
        final long total = IOUtils.sumPair(sum, amount);
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
EXT = '''    /**
     * Sums the values of the bytes of a header range.
     *
     * @param buf the header bytes
     * @param offset the first index of the range
     * @param length the number of bytes in the range
     * @return the sum of the byte values of the range
     */
    public static long digest(final byte[] buf, final int offset, final int length) {
        long sum = 0;
        final int end = offset + length;
        for (int i = offset; i < end; i++) {
            sum += AsiExtraField.magnitudeOf(buf[i]);
        }
        return sum;
    }'''
EXT_TEST = '''/*
 *  Licensed to the Apache Software Foundation (ASF) under one or more
 *  contributor license agreements.  See the NOTICE file distributed with
 *  this work for additional information regarding copyright ownership.
 *  The ASF licenses this file to You under the Apache License, Version 2.0
 *  (the "License"); you may not use this file except in compliance with
 *  the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 */

package org.apache.commons.compress.archivers.tar;

import junit.framework.TestCase;

/**
 * JUnit 3 testcases for org.apache.commons.compress.archivers.tar.TarBuffer.
 */
public class TarBufferTest extends TestCase {

    public TarBufferTest(String name) {
        super(name);
    }

    /**
     * Some checks for digest.
     */
    public void testDigest() {
        final byte[] header = new byte[] { (byte) 0xC3, (byte) 0xA9, 'a', 0 };
        assertEquals(461L, TarBuffer.digest(header, 0, header.length));
        assertEquals(97L, TarBuffer.digest(header, 2, 2));
    }
}
'''
PIN = '''    /**
     * Some checks for magnitudeOf.
     */
    public void testMagnitudeOf() {
        assertEquals(0, AsiExtraField.magnitudeOf((byte) 0));
        assertEquals(1, AsiExtraField.magnitudeOf((byte) 1));
        assertEquals(0x7f, AsiExtraField.magnitudeOf((byte) 0x7f));
        assertEquals(0x80, AsiExtraField.magnitudeOf((byte) 0x80));
        assertEquals(0xc3, AsiExtraField.magnitudeOf((byte) 0xc3));
        assertEquals(0xa9, AsiExtraField.magnitudeOf((byte) 0xa9));
        assertEquals(0xff, AsiExtraField.magnitudeOf((byte) 0xff));
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
    B.insert_before_class_end(work, F["EXT"], EXT)
    B.insert_before_class_end(work, T_PIN, PIN)
    B.new_file(work, T_EXT, EXT_TEST)
spec = {"pair_id": "LB-COMPRESS-07", "project": P, "bug": "07", "base_version": "Compress-1f", "seed_variant": SEED, "level": "B", "converted_from": "OCFLB-COMPRESS-07", "revision": 2,
  "family": "byte interpretation (signed vs unsigned header byte)",
  "convention": "magnitudeOf(b) = the unsigned value of a header byte, 0..255 (low seven bits plus 128 when the top bit is set); the tar header checksum is the sum of these values; decided by TarBuffer.digest, which sums magnitudeOf directly and whose test expects 461 for the UTF-8 header {0xC3, 0xA9, 'a', 0}, and by the pin testMagnitudeOf",
  "effect": "bytes with the top bit set contribute their sign-extended value (-128..-1) instead of their unsigned value (128..255), so the checksum of the UTF-8 header {0xC3, 0xA9, 'a', 0} is -51 instead of 461",
  "equivalence_note": "both hops split their input into low = x & 0x7f and top = x - low; the definer arm recombines low + top (the sign-extended byte, -128..127) where low - top (the unsigned value) is required; the adapter arm receives the unsigned value (0..255) and recombines low - top (re-signing it) where low + top (the identity) is required; for every byte both arms give the signed value (0xC3 -> -61), hence the same sum for every header; the map x -> 2*(x & 0x7f) - x is an involution, so applying it in both hops restores the unsigned sum",
  "adapter_fault_note": "widen gives the part above the seven low bits (top) the weight of a sign bit (low - top instead of low + top) before folding the value into the running sum; the definer's own recombination has the same textual form, so the packet does not say which hop should carry the transform",
  "trigger": "org.apache.commons.compress.archivers.tar.TarArchiveEntryTest::testCompress194", "expected_signature": "expected:<461> but was:<-51>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testMagnitudeOf",
  "second_caller": "org.apache.commons.compress.archivers.tar.TarBuffer#digest (production; sums magnitudeOf of a header range directly into a long)",
  "external_evidence_tests": ["org.apache.commons.compress.archivers.tar.TarBufferTest::testDigest"],
  "chain": {"facade": {"class": "org.apache.commons.compress.archivers.tar.TarUtils", "method": "computeCheckSum", "file": F["facade"]},
            "H1": {"class": "org.apache.commons.compress.archivers.tar.TarBuffer", "method": "tally", "file": F["H1"]}, "H2": {"class": "org.apache.commons.compress.archivers.zip.AsiExtraField", "method": "magnitudeOf", "file": F["H2"]},
            "H3": {"class": "org.apache.commons.compress.archivers.zip.ExtraFieldUtils", "method": "widen", "file": F["H3"]}, "H4": {"class": "org.apache.commons.compress.archivers.zip.ZipLong", "method": "byteValue", "file": F["H4"]},
            "H5": {"class": "org.apache.commons.compress.utils.IOUtils", "method": "sumPair", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN, T_EXT],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": F["EXT"], "role": "EXT (production second caller TarBuffer.digest; same file as H1)"}, {"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}, {"file": T_EXT, "role": "external evidence test"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "LB-COMPRESS-07-DEFINER", "gold_role": "H2", "gold": {"class": "org.apache.commons.compress.archivers.zip.AsiExtraField", "method": "magnitudeOf", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_BUG}, "declared_collateral": ["org.apache.commons.compress.archivers.zip.AsiExtraFieldTest::testMagnitudeOf", "org.apache.commons.compress.archivers.tar.TarBufferTest::testDigest"]},
           "ADAPTER_FAULT": {"variant_id": "LB-COMPRESS-07-ADAPTER", "gold_role": "H3", "gold": {"class": "org.apache.commons.compress.archivers.zip.ExtraFieldUtils", "method": "widen", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_BUG}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Compress/bug-07"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
