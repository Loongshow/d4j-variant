"""Stage B bug B3 (Chart): DatasetUtilities.findStackedRangeBounds(CategoryDataset, double base). Gold = the per-column signed
totals; the fault admits NaN into the negative total (the strict `< 0.0` guard becomes `else`), so the trigger's last block
(adds Double.NaN, expects [2, 8]) sees a NaN lower bound. Pins: StackedAreaRenderer.getStackValues (!Double.isNaN), the
TableXYDataset overload of the facade (isNaN test), StackedBarRenderer3D.createStackedValueList (two strict tests),
StackedBarRenderer.findRangeBounds passing getBase() with its own passing test. The facade's final guard is rewritten to the
equivalent `categoryCount > 0` in every cell so the fault surfaces as a value (Range(NaN, 8)) rather than a null range."""
GOLD_TEXT = '''/**
 * Returns the totals of the values in one column of a category dataset,
 * with the negative values and the positive values summed separately.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param column  the column index.
 *
 * @return A two element array containing the total of the negative
 *         values and the total of the positive values.
 */
public static double[] signedSums(CategoryDataset dataset, int column) {
    double below = 0.0;
    double above = 0.0;
    int rowCount = dataset.getRowCount();
    for (int row = 0; row < rowCount; row++) {
        Number n = dataset.getValue(row, column);
        if (n != null) {
            double v = n.doubleValue();
            if (v > 0.0) {
                above = above + v;
            }
            if (v < 0.0) {
                below = below + v;
            }
        }
    }
    return new double[] {below, above};
}'''
PLACE_DOC = '''/**
 * Returns the bottom and the top of a stack of bars with the given totals
 * of negative and positive values, when the bars rise and fall from the
 * specified base.
 *
 * @param sums  the total of the negative values and the total of the
 *              positive values.
 * @param base  the base value for the bars.
 *
 * @return A two element array containing the bottom and the top of the
 *         stack.
 */'''
SIB_PLAIN = PLACE_DOC + '''
public static double[] placeTotals(double[] sums, double base) {
    double bottom = base + sums[0];
    double top = base + sums[1];
    return new double[] {bottom, top};
}'''
SIB_ODD = PLACE_DOC + '''
public static double[] placeTotals(double[] sums, double base) {
    double top = base + sums[1];
    double height = sums[1] - sums[0];
    return new double[] {top - height, top};
}'''
H3_DOC = '''/**
 * Returns the bottom and the top of the stack of bars for one column of a
 * category dataset, when the bars rise and fall from the specified base.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param column  the column index.
 * @param base  the base value for the bars.
 *
 * @return A two element array containing the bottom and the top of the
 *         stack.
 */'''
DESIGN = {
 "bug": "B3", "project": "Chart", "src_root": "source", "test_root": "tests",
 "facade": {"file": "source/org/jfree/data/general/DatasetUtilities.java", "class": "org.jfree.data.general.DatasetUtilities",
            "method": "findStackedRangeBounds", "near_line": 1877},
 "trigger": {"existing": True, "test_file": "tests/org/jfree/data/general/junit/DatasetUtilitiesTests.java",
             "test_class": "org.jfree.data.general.junit.DatasetUtilitiesTests", "test_method": "testFindStackedRangeBounds_CategoryDataset2"},
 "expected_signature": "expected:<2.0> but was:<NaN>",
 "gold": {"method": "signedSums", "text": GOLD_TEXT,
          "fault": {"old": "                if (v < 0.0) {\n                    below = below + v;",
                    "new": "                else {\n                    below = below + v;"}},
 "one_hop": {
   "facade_old": '''        for (int item = 0; item < categoryCount; item++) {
            double positive = base;
            double negative = base;
            int seriesCount = dataset.getRowCount();
            for (int series = 0; series < seriesCount; series++) {
                Number number = dataset.getValue(series, item);
                if (number != null) {
                    double value = number.doubleValue();
                    if (value > 0.0) {
                        positive = positive + value;
                    }
                    if (value < 0.0) {
                        negative = negative + value;
                        // '+', remember value is negative
                    }
                }
            }
            minimum = Math.min(minimum, negative);
            maximum = Math.max(maximum, positive);
        }
        if (minimum <= maximum) {
            result = new Range(minimum, maximum);
        }
        return result;''',
   "facade_new": '''        for (int item = 0; item < categoryCount; item++) {
            double[] limits = placeTotals(signedSums(dataset, item), base);
            minimum = Math.min(minimum, limits[0]);
            maximum = Math.max(maximum, limits[1]);
        }
        if (categoryCount > 0) {
            result = new Range(minimum, maximum);
        }
        return result;''',
   "sibling": {"method": "placeTotals", "plain": SIB_PLAIN, "odd": SIB_ODD},
 },
 "chain": {
   "facade_body": "if (dataset == null) {\n            throw new IllegalArgumentException(\"Null 'dataset' argument.\");\n        }\n        return org.jfree.chart.StandardChartTheme.extentOfCategories(dataset, base);",
   "lie": "The bounds are gathered in a single pass over the series, each series carrying its own running total across the categories, and the extreme running totals of all the series are returned.",
   "hops": [
     {"file": "source/org/jfree/chart/StandardChartTheme.java", "class": "org.jfree.chart.StandardChartTheme", "method": "extentOfCategories",
      "imports": ["org.jfree.data.category.CategoryDataset", "org.jfree.data.Range", "org.jfree.chart.renderer.xy.AbstractXYItemRenderer"],
      "text": '''/**
 * Returns the range of the values in a category dataset when the series
 * in each category are stacked on the specified base.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param base  the base value for the bars.
 *
 * @return The range (<code>null</code> if the dataset has no columns).
 */
public static Range extentOfCategories(CategoryDataset dataset, double base) {
    Range result = null;
    double minimum = Double.POSITIVE_INFINITY;
    double maximum = Double.NEGATIVE_INFINITY;
    int categoryCount = dataset.getColumnCount();
    for (int item = 0; item < categoryCount; item++) {
        double[] limits = AbstractXYItemRenderer.categoryLimits(dataset, item, base);
        minimum = Math.min(minimum, limits[0]);
        maximum = Math.max(maximum, limits[1]);
    }
    if (categoryCount > 0) {
        result = new Range(minimum, maximum);
    }
    return result;
}'''},
     {"file": "source/org/jfree/chart/renderer/xy/AbstractXYItemRenderer.java", "class": "org.jfree.chart.renderer.xy.AbstractXYItemRenderer", "method": "categoryLimits",
      "imports": ["org.jfree.data.category.CategoryDataset"],
      "text": '''/**
 * Returns the bottom and the top of the stack of bars for one column of a
 * category dataset.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param column  the column index.
 * @param base  the base value for the bars.
 *
 * @return A two element array containing the bottom and the top of the
 *         stack.
 */
public static double[] categoryLimits(CategoryDataset dataset, int column,
        double base) {
    return AbstractRenderer.placeTotals(dataset, column, base);
}'''},
     {"file": "source/org/jfree/chart/renderer/AbstractRenderer.java", "class": "org.jfree.chart.renderer.AbstractRenderer", "method": "placeTotals",
      "imports": ["org.jfree.data.category.CategoryDataset", "org.jfree.chart.axis.ValueAxis"],
      "plain": H3_DOC + '''
public static double[] placeTotals(CategoryDataset dataset, int column,
        double base) {
    double[] sums = ValueAxis.collectValues(dataset, column);
    double bottom = base + sums[0];
    double top = base + sums[1];
    return new double[] {bottom, top};
}''',
      "odd": H3_DOC + '''
public static double[] placeTotals(CategoryDataset dataset, int column,
        double base) {
    double[] sums = ValueAxis.collectValues(dataset, column);
    double top = base + sums[1];
    double height = sums[1] - sums[0];
    return new double[] {top - height, top};
}'''},
     {"file": "source/org/jfree/chart/axis/ValueAxis.java", "class": "org.jfree.chart.axis.ValueAxis", "method": "collectValues",
      "imports": ["org.jfree.data.category.CategoryDataset", "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer"],
      "text": '''/**
 * Collects the totals of the negative and the positive values in one
 * column of a category dataset.
 *
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param column  the column index.
 *
 * @return A two element array containing the total of the negative
 *         values and the total of the positive values.
 */
public static double[] collectValues(CategoryDataset dataset, int column) {
    return AbstractCategoryItemRenderer.signedSums(dataset, column);
}'''},
     {"file": "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java", "class": "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer",
      "method": "signedSums", "imports": ["org.jfree.data.category.CategoryDataset"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.chart.renderer.category.StackedAreaRenderer::getStackValues", "org.jfree.chart.renderer.category.StackedBarRenderer3D::createStackedValueList",
              "org.jfree.chart.renderer.category.StackedBarRenderer::findRangeBounds", "org.jfree.data.general.DatasetUtilities::findStackedRangeBounds"],
 "ownership_reason": "Only the per-column totals inspect individual values; once a NaN has entered a total no later hop can recover the finite "
                     "total (the facade, fold and extent hops see only the sums). The project's stacking code skips NaN everywhere else "
                     "(StackedAreaRenderer.getStackValues, the TableXYDataset overload, StackedBarRenderer3D's two strict tests) and the trigger "
                     "adds Double.NaN expecting the range to stay [2, 8].",
 "ownership_tests": ["org.jfree.chart.renderer.category.junit.StackedBarRendererTests::testFindRangeBounds",
                     "org.jfree.chart.renderer.category.junit.StackedBarRenderer3DTests::testFindRangeBounds",
                     "org.jfree.data.general.junit.DatasetUtilitiesTests::testFindStackedRangeBounds_CategoryDataset1"],
 "compensating": {
   "one_hop": [
     {"file": "source/org/jfree/data/general/DatasetUtilities.java", "old": "            minimum = Math.min(minimum, limits[0]);",
      "new": "            minimum = Double.isNaN(limits[0]) ? minimum : Math.min(minimum, limits[0]);", "why": "facade fold skips a NaN bottom"},
     {"file": "source/org/jfree/data/general/DatasetUtilities.java", "old": "        double bottom = base + sums[0];",
      "new": "        double bottom = Double.isNaN(sums[0]) ? base : base + sums[0];", "why": "plain sibling treats a NaN total as empty", "cells": ["C00"]},
     {"file": "source/org/jfree/data/general/DatasetUtilities.java", "old": "        double height = sums[1] - sums[0];",
      "new": "        double height = Double.isNaN(sums[0]) ? sums[1] : sums[1] - sums[0];", "why": "odd sibling treats a NaN total as empty", "cells": ["C01"]},
   ],
   "chain": [
     {"file": "source/org/jfree/chart/StandardChartTheme.java", "old": "            minimum = Math.min(minimum, limits[0]);",
      "new": "            minimum = Double.isNaN(limits[0]) ? minimum : Math.min(minimum, limits[0]);", "why": "hop 1 fold skips a NaN bottom"},
     {"file": "source/org/jfree/chart/renderer/AbstractRenderer.java", "old": "        double bottom = base + sums[0];",
      "new": "        double bottom = Double.isNaN(sums[0]) ? base : base + sums[0];", "why": "plain hop 3 treats a NaN total as empty", "cells": ["C10"]},
     {"file": "source/org/jfree/chart/renderer/AbstractRenderer.java", "old": "        double height = sums[1] - sums[0];",
      "new": "        double height = Double.isNaN(sums[0]) ? sums[1] : sums[1] - sums[0];", "why": "odd hop 3 treats a NaN total as empty", "cells": ["C11"]},
   ],
 },
}
