"""Main-run instance Chart-2 (C10 recipe on the fixed checkout of Defects4J Chart-2, target class DatasetUtilities, the class the
real bug modified). Facade: DatasetUtilities.findCumulativeRangeBounds(CategoryDataset) (pool candidate 3; findStackedRangeBounds
is excluded because Stage B used it). Its body becomes the null guard plus one delegating call into a five-hop chain drawn with
the instance seed 4456: PiePlot (hop 1, range assembly), AbstractCategoryItemRenderer (hop 2, fold over the rows),
ValueAxis (hop 3, pass-through), CategoryPlot (hop 4, pass-through), DateAxis (hop 5 = gold, the per-row running total).

Gold = the per-row running-total extremes; the fault omits the NaN skip inside the column loop, so a Double.NaN item turns the
running total into NaN and Math.min/Math.max propagate it into both extremes. Trigger: the EXISTING test
DatasetUtilitiesTests::testCumulativeRange_NaN (10, 15, NaN in one series; expects [0, 25]) fails with
"expected:<0.0> but was:<NaN>". It is the only test that feeds NaN to the cumulative range, so it is the only new failure.

Ownership: only the gold sees individual values; once NaN has entered the running total the extreme 25 reached before it is lost,
so no hop above the gold can recover [0, 25] in one line, and a CategoryDataset cannot be pre-filtered in one line. The NaN-skip
convention is pinned outside the gold: DatasetUtilities.calculateStackTotal (a running total that skips NaN),
StackedAreaRenderer.getStackValues, DatasetUtilities.iterateRangeBounds and the TableXYDataset findStackedRangeBounds, plus the
passing NaN tests of the stacked-range methods. The gold javadoc states the running-total contract and is silent on NaN.
Lie: the facade is said to keep ONE running total carried across the categories over all series (the code keeps one per row)."""

GOLD_TEXT = '''/**
 * Returns the lowest and the highest values reached by the running total
 * of the items in one row of a category dataset, the items being added in
 * column order to a total that starts at zero.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param row  the row index (zero-based).
 *
 * @return A two element array containing the lowest and the highest
 *         values of the running total, or <code>null</code> if the row
 *         contains no data items.
 */
public static double[] runningExtremes(CategoryDataset dataset, int row) {
    boolean found = false;
    double minimum = 0.0;
    double maximum = 0.0;
    double runningTotal = 0.0;
    int columnCount = dataset.getColumnCount();
    for (int column = 0; column < columnCount; column++) {
        Number n = dataset.getValue(row, column);
        if (n != null) {
            found = true;
            double value = n.doubleValue();
            if (!Double.isNaN(value)) {
                runningTotal = runningTotal + value;
                minimum = Math.min(minimum, runningTotal);
                maximum = Math.max(maximum, runningTotal);
            }
        }
    }
    if (!found) {
        return null;
    }
    return new double[] {minimum, maximum};
}'''

HOP1 = '''/**
 * Returns the range of the running totals in a category dataset, where
 * each row of the dataset keeps its own running total.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 *
 * @return The range (<code>null</code> if the dataset contains no data
 *         items).
 */
public static Range accumulatedExtent(CategoryDataset dataset) {
    double[] bounds = AbstractCategoryItemRenderer.combinedSeriesBounds(
            dataset);
    if (bounds == null) {
        return null;
    }
    return new Range(bounds[0], bounds[1]);
}'''

HOP2 = '''/**
 * Returns the lowest and the highest values reached by the running totals
 * of the rows of a category dataset, each row keeping its own running
 * total from zero.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 *
 * @return A two element array containing the lowest and the highest
 *         values, or <code>null</code> if the dataset contains no data
 *         items.
 */
public static double[] combinedSeriesBounds(CategoryDataset dataset) {
    boolean found = false;
    double minimum = 0.0;
    double maximum = 0.0;
    int rowCount = dataset.getRowCount();
    for (int row = 0; row < rowCount; row++) {
        double[] limits = ValueAxis.boundsForSeries(dataset, row);
        if (limits != null) {
            found = true;
            minimum = Math.min(minimum, limits[0]);
            maximum = Math.max(maximum, limits[1]);
        }
    }
    if (!found) {
        return null;
    }
    return new double[] {minimum, maximum};
}'''

HOP3 = '''/**
 * Returns the lowest and the highest values reached by the running total
 * of one row of a category dataset.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param row  the row index (zero-based).
 *
 * @return A two element array containing the lowest and the highest
 *         values, or <code>null</code> if the row contains no data items.
 */
public static double[] boundsForSeries(CategoryDataset dataset, int row) {
    return CategoryPlot.dataExtentForSeries(dataset, row);
}'''

HOP4 = '''/**
 * Returns the lowest and the highest values reached by the running total
 * of one row of a category dataset.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param row  the row index (zero-based).
 *
 * @return A two element array containing the lowest and the highest
 *         values, or <code>null</code> if the row contains no data items.
 */
public static double[] dataExtentForSeries(CategoryDataset dataset,
        int row) {
    return DateAxis.runningExtremes(dataset, row);
}'''

DU = "source/org/jfree/data/general/DatasetUtilities.java"
PIE = "source/org/jfree/chart/plot/PiePlot.java"
ACIR = "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java"
VA = "source/org/jfree/chart/axis/ValueAxis.java"
CP = "source/org/jfree/chart/plot/CategoryPlot.java"
DA = "source/org/jfree/chart/axis/DateAxis.java"

DESIGN = {
 "instance": "Chart-2", "project": "Chart", "bug_id": 2, "seed": 4456, "src_root": "source", "test_root": "tests",
 "facade": {"file": DU, "class": "org.jfree.data.general.DatasetUtilities", "method": "findCumulativeRangeBounds", "near_line": 2148},
 "trigger": {"existing": True, "test_file": "tests/org/jfree/data/general/junit/DatasetUtilitiesTests.java",
             "test_class": "org.jfree.data.general.junit.DatasetUtilitiesTests", "test_method": "testCumulativeRange_NaN"},
 "expected_signature": "expected:<0.0> but was:<NaN>",
 "gold": {"method": "runningExtremes", "text": GOLD_TEXT,
          "fault": {"old": "                double value = n.doubleValue();\n"
                           "                if (!Double.isNaN(value)) {\n"
                           "                    runningTotal = runningTotal + value;\n"
                           "                    minimum = Math.min(minimum, runningTotal);\n"
                           "                    maximum = Math.max(maximum, runningTotal);\n"
                           "                }",
                    "new": "                double value = n.doubleValue();\n"
                           "                runningTotal = runningTotal + value;\n"
                           "                minimum = Math.min(minimum, runningTotal);\n"
                           "                maximum = Math.max(maximum, runningTotal);"}},
 "chain": {
   "facade_body": "if (dataset == null) {\n            throw new IllegalArgumentException(\"Null 'dataset' argument.\");\n        }\n"
                  "        return org.jfree.chart.plot.PiePlot.accumulatedExtent(dataset);",
   "lie": "The totals are accumulated in a single pass over the categories, the values of every series in a category being added "
          "in turn to one running total that is carried from each category to the next.",
   "hops": [
     {"file": PIE, "class": "org.jfree.chart.plot.PiePlot", "method": "accumulatedExtent",
      "imports": ["org.jfree.data.Range", "org.jfree.data.category.CategoryDataset",
                  "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer"],
      "text": HOP1},
     {"file": ACIR, "class": "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer", "method": "combinedSeriesBounds",
      "imports": ["org.jfree.data.category.CategoryDataset", "org.jfree.chart.axis.ValueAxis"],
      "text": HOP2},
     {"file": VA, "class": "org.jfree.chart.axis.ValueAxis", "method": "boundsForSeries",
      "imports": ["org.jfree.data.category.CategoryDataset", "org.jfree.chart.plot.CategoryPlot"],
      "text": HOP3},
     {"file": CP, "class": "org.jfree.chart.plot.CategoryPlot", "method": "dataExtentForSeries",
      "imports": ["org.jfree.data.category.CategoryDataset", "org.jfree.chart.axis.DateAxis"],
      "text": HOP4},
     {"file": DA, "class": "org.jfree.chart.axis.DateAxis", "method": "runningExtremes",
      "imports": ["org.jfree.data.category.CategoryDataset"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.data.general.DatasetUtilities::calculateStackTotal",
              "org.jfree.chart.renderer.category.StackedAreaRenderer::getStackValues",
              "org.jfree.data.general.DatasetUtilities::iterateRangeBounds",
              "org.jfree.data.general.DatasetUtilities::findStackedRangeBounds"],
 "ownership_reason": "Only the per-row running total inspects individual values; once a NaN item has entered the running total, "
                     "Math.min/Math.max carry NaN into both extremes and the highest total reached before it (25 on the trigger) is "
                     "lost, so the fold over the rows, the range assembly and the pass-through hops cannot recover [0, 25] with a "
                     "one-line change, and a CategoryDataset cannot be pre-filtered in one line. The project's totals skip NaN "
                     "elsewhere (DatasetUtilities.calculateStackTotal, StackedAreaRenderer.getStackValues, iterateRangeBounds, the "
                     "TableXYDataset findStackedRangeBounds, the stacked-range NaN tests) and the trigger adds Double.NaN expecting "
                     "the cumulative range to stay [0, 25].",
 "ownership_tests": ["org.jfree.data.general.junit.DatasetUtilitiesTests::testCumulativeRange1",
                     "org.jfree.data.general.junit.DatasetUtilitiesTests::testCumulativeRange2",
                     "org.jfree.data.general.junit.DatasetUtilitiesTests::testFindStackedRangeBounds_CategoryDataset2",
                     "org.jfree.data.general.junit.DatasetUtilitiesTests::testFindMaximumStackedRangeValue",
                     "org.jfree.data.general.junit.DatasetUtilitiesTests::testIterateRangeBounds2_CategoryDataset"],
 "compensating": {
   "chain": [
     {"file": ACIR, "old": "                minimum = Math.min(minimum, limits[0]);",
      "new": "                minimum = Double.isNaN(limits[0]) ? minimum : Math.min(minimum, limits[0]);",
      "why": "hop 2 fold skips a NaN lowest value"},
     {"file": ACIR, "old": "            if (limits != null) {",
      "new": "            if (limits != null && !Double.isNaN(limits[0]) && !Double.isNaN(limits[1])) {",
      "why": "hop 2 fold skips a row whose extremes are NaN"},
     {"file": PIE, "old": "        return new Range(bounds[0], bounds[1]);",
      "new": "        return new Range(Double.isNaN(bounds[0]) ? 0.0 : bounds[0], Double.isNaN(bounds[1]) ? 0.0 : bounds[1]);",
      "why": "hop 1 reads NaN bounds as zero"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4456 (n=5, target org/jfree/data/general/DatasetUtilities.java): PiePlot (hop 1), "
               "AbstractCategoryItemRenderer (hop 2), ValueAxis (hop 3), CategoryPlot (hop 4), DateAxis (hop 5, gold). All five "
               "are public classes in which a static method compiles; none was skipped.",
}
