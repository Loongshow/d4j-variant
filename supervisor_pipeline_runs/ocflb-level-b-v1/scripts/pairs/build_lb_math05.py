"""LB-MATH-05 (Level B): scale units of a plain sum of squares merged into a scaled sum of squares. Converted from OCFLB-MATH-05 (seed MATH-NORM-TREATMENT-01).
Facade MathArrays.safeNorm -> H1 StatUtils.survey -> H2 Precision.residue (definer) -> H3 MatrixUtils.settle (adapter)
-> H4 FastMath.merge -> H5 MathUtils.balance.
Convention decided externally: the residue is the plain sum divided by the scale twice (plain / (scale * scale)), as the production
second caller MathArrays.scaledSumOfSquares and its test rely on (scaledSumOfSquares({2, 2}, 2) == 2.0).
Revision 2 (after blinded grading): revision 1's settle javadoc described major as "each divided by the top magnitude" and the
result as "in the domain of the largest entries", which fixed the unit of the merged sum locally; both graders of the ADAPTER arm's
two-hop packet used it to convict settle's scaled * top. The javadoc now names the partial sums without stating their unit (general
purpose only); the code of both hops is unchanged.
Usage: build_lb_math05.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Math"; SEED = "MATH-NORM-TREATMENT-01"
SRC = "src/main/java/org/apache/commons/math3/"; TST = "src/test/java/org/apache/commons/math3/"
F = {"facade": SRC + "util/MathArrays.java", "H1": SRC + "stat/StatUtils.java", "H2": SRC + "util/Precision.java",
     "H3": SRC + "linear/MatrixUtils.java", "H4": SRC + "util/FastMath.java", "H5": SRC + "util/MathUtils.java"}
F["EXT"] = F["facade"]   # the production second caller of H2 lives in MathArrays (the facade class), next to safeNorm
T_TRIG = TST + "util/MathArraysTest.java"; T_PIN = TST + "util/PrecisionTest.java"; T_EXT = T_TRIG
H1 = '''    /**
     * Surveys the entries of an array by magnitude and resolves their
     * Euclidean norm. Entries above the ceiling are accumulated as a sum of
     * squares relative to the largest of them, entries below the floor as a
     * sum of squares relative to the largest of them, and the intermediate
     * entries as a plain sum of squares.
     *
     * @param values the input array
     * @param floor the smallest magnitude accumulated as an intermediate entry
     * @param ceiling the largest magnitude accumulated as an intermediate entry
     * @return the surveyed value of the array
     */
    public static double survey(final double[] values, final double floor, final double ceiling) {
        double major = 0;
        double top = 0;
        double middle = 0;
        double minor = 0;
        double bottom = 0;
        for (int i = 0; i < values.length; i++) {
            final double x = Math.abs(values[i]);
            if (x > ceiling) {
                if (x > top) {
                    final double r = top / x;
                    major = 1 + major * r * r;
                    top = x;
                } else {
                    final double r = x / top;
                    major += r * r;
                }
            } else if (x < floor) {
                if (x > bottom) {
                    final double r = bottom / x;
                    minor = 1 + minor * r * r;
                    bottom = x;
                } else if (x != 0) {
                    final double r = x / bottom;
                    minor += r * r;
                }
            } else {
                middle += x * x;
            }
        }
        final double scaled = Precision.residue(middle, top);
        return MatrixUtils.settle(major, top, scaled, middle, minor, bottom);
    }'''
H2_OK = "        return (plain / scale) / scale;"
H2_BUG = "        return plain / scale;"                              # DEFINER arm: the second division is omitted
H2_ABSORB = "        return ((plain / scale) / scale) / scale;"     # compensating repair in the ADAPTER arm: absorbs settle's extra factor
H2 = '''    /**
     * Expresses a plain sum of squares relative to the scale of a scaled
     * sum of squares. When the scale is zero the plain sum is returned as
     * is.
     *
     * @param plain Plain sum of squares.
     * @param scale Scale of the scaled sum of squares.
     * @return the plain sum expressed relative to the scale.
     */
    public static double residue(final double plain, final double scale) {
        if (scale == 0) {
            return plain;
        }
%s
    }'''
H3_OK = "        final double merged = major + scaled;"
H3_BUG = "        final double merged = major + scaled * top;"       # ADAPTER arm: the residue is lifted by the top magnitude once more
H3_ABSORB = "        final double merged = major + scaled / top;"   # compensating repair in the DEFINER arm: absorbs residue's missing division
H3 = '''    /**
     * Settles the partial sums of squares of an array into a single sum and
     * hands it on to be merged.
     *
     * @param major sum of squares of the largest entries
     * @param top largest magnitude among the largest entries
     * @param scaled sum of squares of the intermediate entries, expressed relative to the top magnitude
     * @param middle plain sum of squares of the intermediate entries
     * @param minor sum of squares of the smallest entries
     * @param bottom largest magnitude among the smallest entries
     * @return the settled value
     */
    public static double settle(final double major, final double top, final double scaled,
                                final double middle, final double minor, final double bottom) {
%s
        return FastMath.merge(top, merged, middle, minor, bottom);
    }'''
H4 = '''    /**
     * Merges a scaled sum of squares back into absolute units by multiplying
     * its square root by its scale, then balances the result against the
     * contribution of the entries that were not scaled.
     *
     * @param scale the scale of the scaled sum
     * @param merged the scaled sum of squares, intermediate contribution included
     * @param plain the plain sum of squares of the intermediate entries
     * @param minor the sum of squares of the smallest entries, each divided by the bottom magnitude
     * @param bottom the largest magnitude among the smallest entries
     * @return the merged value
     */
    public static double merge(final double scale, final double merged, final double plain,
                               final double minor, final double bottom) {
        final double root = sqrt(merged);
        final double dominant = scale * root;
        return MathUtils.balance(scale, dominant, plain, minor, bottom);
    }'''
H5 = '''    /**
     * Balances the norm of the largest entries of an array against the
     * contribution of its intermediate and smallest entries. When at least
     * one entry was scaled, the dominant value already accounts for every
     * entry that matters and is returned; otherwise the norm is assembled
     * from the plain sum of the intermediate entries and the scaled sum of
     * the smallest entries.
     *
     * @param scale Scale of the largest entries (zero when there are none).
     * @param dominant Norm computed from the largest entries.
     * @param plain Plain sum of squares of the intermediate entries.
     * @param minor Sum of squares of the smallest entries, each divided by the bottom magnitude.
     * @param bottom Largest magnitude among the smallest entries.
     * @return the balanced value of the array.
     */
    public static double balance(final double scale, final double dominant, final double plain,
                                 final double minor, final double bottom) {
        if (scale != 0) {
            return dominant;
        }
        if (plain == 0) {
            return bottom * FastMath.sqrt(minor);
        }
        if (plain >= bottom) {
            return FastMath.sqrt(plain * (1 + (bottom / plain) * (bottom * minor)));
        }
        return FastMath.sqrt(bottom * ((plain / bottom) + (bottom * minor)));
    }'''
EXT = '''    /**
     * Returns the sum of squares of the values expressed relative to the
     * given scale.
     *
     * @param values Values.
     * @param scale Scale.
     * @return the sum of squares of the values, relative to the scale.
     */
    public static double scaledSumOfSquares(double[] values, double scale) {
        double sum = 0;
        for (int i = 0; i < values.length; i++) {
            sum += values[i] * values[i];
        }
        return Precision.residue(sum, scale);
    }'''
EXT_TEST = '''    @Test
    public void testScaledSumOfSquares() {
        Assert.assertEquals(2.0, MathArrays.scaledSumOfSquares(new double[] { 2.0, 2.0 }, 2.0), 0d);
        Assert.assertEquals(1.0, MathArrays.scaledSumOfSquares(new double[] { 3.0, 4.0 }, 5.0), 0d);
        Assert.assertEquals(8.0, MathArrays.scaledSumOfSquares(new double[] { 2.0, 2.0 }, 0.0), 0d);
    }'''
PIN = '''    /**
     * Tests {@link Precision#residue(double, double)}.
     */
    @Test
    public void testResidue() {
        Assert.assertEquals(1.0, Precision.residue(25.0, 5.0), 0d);
        Assert.assertEquals(0.5625, Precision.residue(9.0, 4.0), 0d);
        Assert.assertEquals(2.5e-19, Precision.residue(1.0e20, 2.0e19), 1e-34);
        Assert.assertEquals(25.0, Precision.residue(25.0, 0.0), 0d);
    }'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "survey", H1)
    B.replace_once(work, F["H1"], "import org.apache.commons.math3.util.MathUtils;\n", "")
    B.add_import(work, F["H1"], "import org.apache.commons.math3.util.Precision;"); B.add_import(work, F["H1"], "import org.apache.commons.math3.linear.MatrixUtils;")
    B.replace_method(work, F["H2"], "residue", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_once(work, F["H2"], "import org.apache.commons.math3.linear.MatrixUtils;\n", "")
    B.replace_method(work, F["H3"], "settle", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK))
    B.replace_method(work, F["H4"], "merge", H4)
    B.replace_method(work, F["H5"], "balance", H5)
    B.insert_before_class_end(work, F["EXT"], EXT)
    B.insert_before_class_end(work, T_PIN, PIN)
    B.insert_before_class_end(work, T_EXT, EXT_TEST)
spec = {"pair_id": "LB-MATH-05", "project": P, "bug": "05", "base_version": "Math-1f", "seed_variant": SEED, "level": "B", "converted_from": "OCFLB-MATH-05", "revision": 2,
  "family": "scale units (plain sum of squares merged into a doubly scaled sum)",
  "convention": "residue = plain sum of squares divided by the scale twice, i.e. plain / (scale * scale), directly addable to the scaled sum s1 so that scale * sqrt(s1 + residue) is the norm; decided by MathArrays.scaledSumOfSquares, whose test expects scaledSumOfSquares({2, 2}, 2) == 2.0",
  "effect": "the intermediate entries are merged into the scaled sum divided by the scale only once, so their weight is inflated by the scale (2.0E19 becomes 4.898979485566356E19)",
  "equivalence_note": "omitting the second division in the definer (arm A) and lifting the correctly scaled residue by the top magnitude once before adding it in the adapter (arm B) both give s1 + s2 / x1max for every input, so the final norm is identical",
  "adapter_fault_note": "settle multiplies the residue by the top magnitude before adding it to the scaled sum (the residue is already in the domain of the scaled sum)",
  "trigger": "org.apache.commons.math3.util.MathArraysTest::testMath1142", "expected_signature": "expected:<2.0E19> but was:<4.898979485566356E19>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.apache.commons.math3.util.PrecisionTest::testResidue",
  "second_caller": "org.apache.commons.math3.util.MathArrays#scaledSumOfSquares (production; returns Precision.residue(sum of squares, scale) and its test expects the doubly scaled value)",
  "external_evidence_tests": ["org.apache.commons.math3.util.MathArraysTest::testScaledSumOfSquares"],
  "chain": {"facade": {"class": "org.apache.commons.math3.util.MathArrays", "method": "safeNorm", "file": F["facade"]},
            "H1": {"class": "org.apache.commons.math3.stat.StatUtils", "method": "survey", "file": F["H1"]}, "H2": {"class": "org.apache.commons.math3.util.Precision", "method": "residue", "file": F["H2"]},
            "H3": {"class": "org.apache.commons.math3.linear.MatrixUtils", "method": "settle", "file": F["H3"]}, "H4": {"class": "org.apache.commons.math3.util.FastMath", "method": "merge", "file": F["H4"]},
            "H5": {"class": "org.apache.commons.math3.util.MathUtils", "method": "balance", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN],
  "changed_files": [{"file": F["facade"], "role": "facade + external second caller (scaledSumOfSquares)"}] + [{"file": F[k], "role": k} for k in ("H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger + external evidence test"}, {"file": T_PIN, "role": "pin"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "LB-MATH-05-DEFINER", "gold_role": "H2", "gold": {"class": "org.apache.commons.math3.util.Precision", "method": "residue", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_ABSORB}, "declared_collateral": ["org.apache.commons.math3.util.PrecisionTest::testResidue", "org.apache.commons.math3.util.MathArraysTest::testScaledSumOfSquares"]},
           "ADAPTER_FAULT": {"variant_id": "LB-MATH-05-ADAPTER", "gold_role": "H3", "gold": {"class": "org.apache.commons.math3.linear.MatrixUtils", "method": "settle", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_ABSORB}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Math/bug-05"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
