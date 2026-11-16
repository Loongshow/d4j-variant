"""OCFLB-COMPRESS-08: alignment parity (pad when the member length is odd). Seed CMP-ALIGN-TREATMENT-06.
Facade ArArchiveOutputStream.closeArchiveEntry -> H1 ZipArchiveOutputStream.memberEnd -> H2 CpioArchiveOutputStream.padNeeded (definer)
-> H3 ZipArchiveEntry.padCount (adapter) -> H4 TarArchiveInputStream.remainder -> H5 JarArchiveOutputStream.alignmentBoundary.
Usage: build_compress08.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Compress"; SEED = "CMP-ALIGN-TREATMENT-06"
SRC = "src/main/java/org/apache/commons/compress/archivers/"
F = {"facade": SRC + "ar/ArArchiveOutputStream.java", "H1": SRC + "zip/ZipArchiveOutputStream.java", "H2": SRC + "cpio/CpioArchiveOutputStream.java",
     "H3": SRC + "zip/ZipArchiveEntry.java", "H4": SRC + "tar/TarArchiveInputStream.java", "H5": SRC + "jar/JarArchiveOutputStream.java"}
T_TRIG = "src/test/java/org/apache/commons/compress/archivers/ArTestCase.java"; T_PIN = "src/test/java/org/apache/commons/compress/archivers/cpio/CpioArchiveOutputStreamTest.java"
H1 = '''    /**
     * Returns the number of pad bytes that must follow a member of the given
     * length so that the next header starts at an aligned offset.
     *
     * @param memberLength number of bytes written for the member
     * @return the number of pad bytes to write
     */
    public static int memberEnd(final long memberLength) {
        if (memberLength < 0) {
            throw new IllegalArgumentException("negative member length: " + memberLength);
        }
        final boolean padNeeded = CpioArchiveOutputStream.padNeeded(memberLength);
        return ZipArchiveEntry.padCount(memberLength, padNeeded);
    }'''
H2_OK = "        final boolean needed = (memberLength % 2) != 0;"
H2_BUG = "        final boolean needed = (memberLength % 2) == 0;"
H2 = '''    /**
     * Tells whether a member of the given length has to be followed by a pad
     * byte. Members of the ar format are aligned to an even boundary, so a pad
     * byte is needed exactly when the member length is odd; a member of even
     * length already ends on the boundary.
     *
     * @param memberLength number of bytes written for the member
     * @return true when the member length is odd, false when it is even
     */
    public static boolean padNeeded(final long memberLength) {
%s
        return needed;
    }'''
H3_OK = "        final int count = padNeeded ? 1 : 0;"
H3_BUG = "        final int count = padNeeded ? 0 : 1;"
H3 = '''    /**
     * Converts the pad flag of a member into the number of pad bytes that
     * follow it: one pad byte when a pad is needed, none otherwise. The count
     * is then applied at the member end.
     *
     * @param memberLength number of bytes written for the member
     * @param padNeeded whether the member has to be followed by a pad byte
     * @return the number of pad bytes to write
     */
    public static int padCount(final long memberLength, final boolean padNeeded) {
%s
        return TarArchiveInputStream.remainder(memberLength, count);
    }'''
H4 = '''    /**
     * Applies the pad count to the member end: computes the offset at which
     * the next header starts and resolves how far it lies past the member end.
     *
     * @param memberLength number of bytes written for the member
     * @param count the number of pad bytes that follow the member
     * @return the number of pad bytes to write
     */
    public static int remainder(final long memberLength, final int count) {
        final long end = memberLength + count;
        return JarArchiveOutputStream.alignmentBoundary(memberLength, end);
    }'''
H5 = '''    /**
     * Returns the number of bytes between the end of a member and the aligned
     * offset at which the next header starts.
     *
     * @param memberLength number of bytes written for the member
     * @param end the aligned offset at which the next header starts
     * @return the number of pad bytes to write
     */
    public static int alignmentBoundary(final long memberLength, final long end) {
        final long gap = end - memberLength;
        if (gap < 0) {
            throw new IllegalArgumentException("member end past the aligned offset: " + end);
        }
        return (int) gap;
    }'''
PIN = '''/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package org.apache.commons.compress.archivers.cpio;

import junit.framework.TestCase;

public class CpioArchiveOutputStreamTest extends TestCase {

    /**
     * A member of odd length has to be followed by a pad byte; a member of
     * even length already ends on the two-byte boundary.
     */
    public void testPadNeeded() {
        assertTrue(CpioArchiveOutputStream.padNeeded(1));
        assertTrue(CpioArchiveOutputStream.padNeeded(3));
        assertTrue(CpioArchiveOutputStream.padNeeded(4095));
        assertFalse(CpioArchiveOutputStream.padNeeded(0));
        assertFalse(CpioArchiveOutputStream.padNeeded(2));
        assertFalse(CpioArchiveOutputStream.padNeeded(4096));
    }
}
'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    # rewire the seed's imports to the new hop order (each seed import becomes unused or points at the old callee)
    B.replace_once(work, F["H1"], "import org.apache.commons.compress.archivers.jar.JarArchiveOutputStream;\n\n", "import org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStream;\n\n")
    B.replace_once(work, F["H3"], "import org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStream;\n\n", "import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;\n\n")
    B.replace_once(work, F["H4"], "import org.apache.commons.compress.archivers.zip.ZipArchiveEntry;\n\n", "import org.apache.commons.compress.archivers.jar.JarArchiveOutputStream;\n\n")
    B.replace_once(work, F["H5"], "import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;\n\n", "")
    B.replace_method(work, F["H1"], "memberEnd", H1)
    B.replace_method(work, F["H2"], "padNeeded", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_method(work, F["H3"], "padCount", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK))
    B.replace_method(work, F["H4"], "remainder", H4)
    B.replace_method(work, F["H5"], "alignmentBoundary", H5)
    B.new_file(work, T_PIN, PIN)
spec = {"pair_id": "OCFLB-COMPRESS-08", "project": P, "bug": "08", "base_version": "Compress-1f", "seed_variant": SEED,
  "family": "alignment parity (pad when the member length is odd)",
  "convention": "padNeeded(memberLength) is true exactly when the member length is odd: ar members are aligned to an even boundary, so an odd-length member is followed by one pad byte and an even-length member by none",
  "effect": "an odd-length member receives no pad byte and an even-length member receives one, so the next header starts one byte early (byte 71 is 'e' = 101 instead of the pad '\\n' = 10)",
  "equivalence_note": "flipping the parity test in the definer (arm A) and flipping the flag-to-count mapping in the adapter (arm B) both emit exactly one pad byte after even lengths and none after odd lengths, so the archive layout is identical for every input",
  "adapter_fault_note": "padCount emits one pad byte when the flag is false and none when it is true",
  "trigger": "org.apache.commons.compress.archivers.ArTestCase::testCompress145", "expected_signature": "expected:<10> but was:<101>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStreamTest::testPadNeeded", "second_caller": None,
  "chain": {"facade": {"class": "org.apache.commons.compress.archivers.ar.ArArchiveOutputStream", "method": "closeArchiveEntry", "file": F["facade"]},
            "H1": {"class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "memberEnd", "file": F["H1"]},
            "H2": {"class": "org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStream", "method": "padNeeded", "file": F["H2"]},
            "H3": {"class": "org.apache.commons.compress.archivers.zip.ZipArchiveEntry", "method": "padCount", "file": F["H3"]},
            "H4": {"class": "org.apache.commons.compress.archivers.tar.TarArchiveInputStream", "method": "remainder", "file": F["H4"]},
            "H5": {"class": "org.apache.commons.compress.archivers.jar.JarArchiveOutputStream", "method": "alignmentBoundary", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "OCFLB-COMPRESS-08-DEFINER", "gold_role": "H2", "gold": {"class": "org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStream", "method": "padNeeded", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_BUG}, "declared_collateral": ["org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStreamTest::testPadNeeded"]},
           "ADAPTER_FAULT": {"variant_id": "OCFLB-COMPRESS-08-ADAPTER", "gold_role": "H3", "gold": {"class": "org.apache.commons.compress.archivers.zip.ZipArchiveEntry", "method": "padCount", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_BUG}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Compress/bug-08"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
