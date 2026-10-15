"""Stage B bug B4 = B2' (Math): StatUtils.mode(double[]). Gold = the frequency tally of a slice; the fault omits the NaN skip
inside the tally loop, so NaN (4 occurrences) becomes the mode and the trigger (StatUtilsTest::testMode, nanInfested block) sees
NaN where it expects 0. Frequency keeps NaN keys by contract (FrequencyTest.testModeDoubleNan), so the skip can only live in the
tally; no caller can pre-filter the array in one line and no later hop can recover the counts of 0 and 2 from a mode list [NaN].
The original private getMode is removed in every cell (it held the skip and would be a duplicate implementation). Replaces B2
(withdrawn, W14). Target class StatUtils is below the recipe's 1800-line target gate (recorded, W15)."""
GOLD_TEXT = '''/** Tabulates the frequency of each value in the slice {@code [begin, begin + length)}
 * of an array. Assumes the parameters have been validated.
 * @param values input data
 * @param begin index (0-based) of the first array element to include
 * @param length the number of elements to include
 * @return the frequency table of the values
 */
public static Frequency tabulate(double[] values, final int begin, final int length) {
    Frequency freq = new Frequency();
    for (int i = begin; i < begin + length; i++) {
        final double value = values[i];
        if (!Double.isNaN(value)) {
            freq.addValue(Double.valueOf(value));
        }
    }
    return freq;
}'''
SIB_DOC = '''/** Returns the most frequently occurring value(s) of a frequency table, in
 * ascending order.
 * @param freq the frequency table
 * @return the most frequent value(s), sorted in ascending order
 */'''
SIB_PLAIN = SIB_DOC + '''
public static double[] mostFrequent(Frequency freq) {
    List<Comparable<?>> list = freq.getMode();
    double[] modes = new double[list.size()];
    int i = 0;
    for (Comparable<?> c : list) {
        modes[i++] = ((Double) c).doubleValue();
    }
    return modes;
}'''
SIB_ODD = SIB_DOC + '''
public static double[] mostFrequent(Frequency freq) {
    List<Comparable<?>> list = freq.getMode();
    double[] modes = new double[list.size()];
    final int last = modes.length - 1;
    for (int i = 0; i <= last; i++) {
        modes[last - i] = ((Double) list.get(last - i)).doubleValue();
    }
    return modes;
}'''
H3_DOC = '''/** Returns the most frequently occurring value(s) of the slice
 * {@code [begin, begin + length)} of an array, in ascending order.
 * @param values input data
 * @param begin index (0-based) of the first array element to include
 * @param length the number of elements to include
 * @return the most frequent value(s), sorted in ascending order
 */'''
GETMODE = '''
    /**
     * Private helper method.
     * Assumes parameters have been validated.
     * @param values input data
     * @param begin index (0-based) of the first array element to include
     * @param length the number of elements to include
     * @return array of array of the most frequently occurring element(s) sorted in ascending order.
     */
    private static double[] getMode(double[] values, final int begin, final int length) {
        // Add the values to the frequency table
        Frequency freq = new Frequency();
        for (int i = begin; i < begin + length; i++) {
            final double value = values[i];
            if (!Double.isNaN(value)) {
                freq.addValue(Double.valueOf(value));
            }
        }
        List<Comparable<?>> list = freq.getMode();
        // Convert the list to an array of primitive double
        double[] modes = new double[list.size()];
        int i = 0;
        for(Comparable<?> c : list) {
            modes[i++] = ((Double) c).doubleValue();
        }
        return modes;
    }
'''
SU = "src/main/java/org/apache/commons/math3/stat/StatUtils.java"
DESIGN = {
 "bug": "B4", "project": "Math", "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SU, "class": "org.apache.commons.math3.stat.StatUtils", "method": "mode", "near_line": 817},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math3/stat/StatUtilsTest.java",
             "test_class": "org.apache.commons.math3.stat.StatUtilsTest", "test_method": "testMode"},
 "expected_signature": "expected:<0.0> but was:<NaN>",
 "gold": {"method": "tabulate", "text": GOLD_TEXT,
          "fault": {"old": "            final double value = values[i];\n            if (!Double.isNaN(value)) {\n                freq.addValue(Double.valueOf(value));\n            }",
                    "new": "            final double value = values[i];\n            freq.addValue(Double.valueOf(value));"}},
 "pre_edits": {
   "all": [{"file": SU, "old": GETMODE, "new": ""}],
   "one_hop": [{"file": SU, "old": "        return getMode(sample, begin, length);", "new": "        return mostFrequent(tabulate(sample, begin, length));"}],
   "chain": [{"file": SU, "old": "        return getMode(sample, begin, length);", "new": "        return org.apache.commons.math3.linear.BlockFieldMatrix.leadingValues(sample, begin, length);"}],
 },
 "one_hop": {
   "facade_old": "        return getMode(sample, 0, sample.length);",
   "facade_new": "        return mostFrequent(tabulate(sample, 0, sample.length));",
   "insert_after_method": "mode", "insert_after_line": 845,
   "sibling": {"method": "mostFrequent", "plain": SIB_PLAIN, "odd": SIB_ODD},
 },
 "chain": {
   "facade_body": "if (sample == null) {\n            throw new NullArgumentException(LocalizedFormats.INPUT_ARRAY);\n        }\n        return org.apache.commons.math3.linear.BlockFieldMatrix.leadingValues(sample, 0, sample.length);",
   "lie": "The sample is sorted in place and scanned once, each run of equal values being compared with the longest run found so far, and the values of the longest runs are returned in the order met.",
   "hops": [
    {
     "file": "src/main/java/org/apache/commons/math3/linear/BlockFieldMatrix.java",
     "class": "org.apache.commons.math3.linear.BlockFieldMatrix",
     "method": "leadingValues",
     "imports": [
      "org.apache.commons.math3.analysis.differentiation.DSCompiler"
     ],
     "text": "/** Returns the most frequently occurring value(s) of a slice of an array.\n * @param values input data\n * @param begin index (0-based) of the first array element to include\n * @param length the number of elements to include\n * @return the most frequent value(s), sorted in ascending order\n */\npublic static double[] leadingValues(double[] values, final int begin, final int length) {\n    return DSCompiler.dominantEntries(values, begin, length);\n}"
    },
    {
     "file": "src/main/java/org/apache/commons/math3/analysis/differentiation/DSCompiler.java",
     "class": "org.apache.commons.math3.analysis.differentiation.DSCompiler",
     "method": "dominantEntries",
     "imports": [
      "org.apache.commons.math3.util.MathArrays"
     ],
     "text": "/** Returns the most frequently occurring value(s) of a slice of an array.\n * @param values input data\n * @param begin index (0-based) of the first array element to include\n * @param length the number of elements to include\n * @return the most frequent value(s), sorted in ascending order\n */\npublic static double[] dominantEntries(double[] values, final int begin, final int length) {\n    return MathArrays.mostFrequent(values, begin, length);\n}"
    },
    {
     "file": "src/main/java/org/apache/commons/math3/util/MathArrays.java",
     "class": "org.apache.commons.math3.util.MathArrays",
     "method": "mostFrequent",
     "imports": [
      "java.util.List",
      "org.apache.commons.math3.stat.Frequency",
      "org.apache.commons.math3.dfp.Dfp"
     ],
     "plain": "/** Returns the most frequently occurring value(s) of the slice\n * {@code [begin, begin + length)} of an array, in ascending order.\n * @param values input data\n * @param begin index (0-based) of the first array element to include\n * @param length the number of elements to include\n * @return the most frequent value(s), sorted in ascending order\n */\npublic static double[] mostFrequent(double[] values, final int begin, final int length) {\n    Frequency freq = Dfp.countEntries(values, begin, length);\n    List<Comparable<?>> list = freq.getMode();\n    double[] modes = new double[list.size()];\n    int i = 0;\n    for (Comparable<?> c : list) {\n        modes[i++] = ((Double) c).doubleValue();\n    }\n    return modes;\n}",
     "odd": "/** Returns the most frequently occurring value(s) of the slice\n * {@code [begin, begin + length)} of an array, in ascending order.\n * @param values input data\n * @param begin index (0-based) of the first array element to include\n * @param length the number of elements to include\n * @return the most frequent value(s), sorted in ascending order\n */\npublic static double[] mostFrequent(double[] values, final int begin, final int length) {\n    Frequency freq = Dfp.countEntries(values, begin, length);\n    List<Comparable<?>> list = freq.getMode();\n    double[] modes = new double[list.size()];\n    final int last = modes.length - 1;\n    for (int i = 0; i <= last; i++) {\n        modes[last - i] = ((Double) list.get(last - i)).doubleValue();\n    }\n    return modes;\n}"
    },
    {
     "file": "src/main/java/org/apache/commons/math3/dfp/Dfp.java",
     "class": "org.apache.commons.math3.dfp.Dfp",
     "method": "countEntries",
     "imports": [
      "org.apache.commons.math3.stat.Frequency",
      "org.apache.commons.math3.util.FastMath"
     ],
     "text": "/** Tabulates the frequency of each value in a slice of an array.\n * @param values input data\n * @param begin index (0-based) of the first array element to include\n * @param length the number of elements to include\n * @return the frequency table of the values\n */\npublic static Frequency countEntries(double[] values, final int begin, final int length) {\n    return FastMath.tabulate(values, begin, length);\n}"
    },
    {
     "file": "src/main/java/org/apache/commons/math3/util/FastMath.java",
     "class": "org.apache.commons.math3.util.FastMath",
     "method": "tabulate",
     "imports": [
      "org.apache.commons.math3.stat.Frequency"
     ],
     "gold": True
    }
   ],
 },
 "evidence": ["org.apache.commons.math3.stat.Frequency::getMode", "org.apache.commons.math3.util.MathArrays::normalizeArray", "org.apache.commons.math3.stat.StatUtils::mode"],
 "ownership_reason": "Only the tally inspects individual sample values; Frequency keeps NaN keys by its own contract (FrequencyTest.testModeDoubleNan), "
                     "so once NaN has been counted the mode list is [NaN] and the counts of the real modes are gone: no caller can pre-filter the array in one "
                     "line (no NaN-removal utility exists) and no later hop can recover them. The facades' javadocs state that NaN values are ignored.",
 "ownership_tests": ["org.apache.commons.math3.stat.FrequencyTest::testModeDoubleNan", "org.apache.commons.math3.stat.FrequencyTest::testMode",
                     "org.apache.commons.math3.stat.FrequencyTest::testModeFloatNan"],
 "compensating": {
   "one_hop": [{"file": SU, "old": "        List<Comparable<?>> list = freq.getMode();",
                "new": "        List<Comparable<?>> list = freq.getMode(); list.remove(Double.valueOf(Double.NaN));", "why": "sibling drops a NaN mode from the list"},
               {"file": SU, "old": "        return mostFrequent(tabulate(sample, 0, sample.length));",
                "new": "        return mostFrequent(tabulate(sample, 0, sample.length - 1));", "why": "facade shortens the slice"}],
   "chain": [{"file": "src/main/java/org/apache/commons/math3/util/MathArrays.java", "old": "        List<Comparable<?>> list = freq.getMode();",
              "new": "        List<Comparable<?>> list = freq.getMode(); list.remove(Double.valueOf(Double.NaN));", "why": "hop 3 drops a NaN mode from the list"},
             {"file": "src/main/java/org/apache/commons/math3/dfp/Dfp.java", "old": "        return FastMath.tabulate(values, begin, length);",
              "new": "        return FastMath.tabulate(values, begin, length - 1);", "why": "hop 4 shortens the slice"}],
 },
}
