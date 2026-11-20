"""Main run Chart-19__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug without a static facade; the
fixed checkout of Defects4J Chart-19, whose real bug modified CategoryPlot, the facade's class). No static pair (B8 note section 1).

Facade: CategoryPlot.getLegendItems() (allowed instance target of BATCH8_PREREGISTRATION.md row 215, facade_planned_by = null, so no
facade reuse; the record's facade_reuse_of entry Chart-14__i concerns getRendererForDataset, which is not used). The other two allowed
targets were screened on a scratch copy of the fixture with the full suite and rejected:
  - CategoryPlot.getRendererForDataset (planned by Chart-14__i): reached only through drawing (79 tests); dropping its early exit at the
    first matching dataset changes no test result, and the method has no other step a one-line omission could live in.
  - CategoryPlot.addDomainMarker(int, CategoryMarker, Layer): every observable step (adding the marker to the foreground list, putting
    the new list into the map, registering the plot as listener) is caught by BOTH CategoryPlotTests::testAddDomainMarker and
    MarkerTests::testListenersWithCategoryPlot (identical scenario), the background branch and the change notification by no test; no
    single trigger exists.
Original computation of the facade: the fixed legend items (private field fixedLegendItems) when they are set; otherwise a new
collection holding, for each dataset index below the dataset count (datasets.size()), when the dataset (getDataset(index)) is not null
and its renderer (getRenderer(index)) is not null, the legend item renderer.getLegendItem(index, series) of each series (row) of the
dataset, skipping a null item.

facade_variant: V2 (receiver as parameter). The computation needs the plot's public methods getFixedLegendItems(), getDatasetCount(),
getDataset(int) and getRenderer(int) (the original reads the private fields fixedLegendItems and datasets directly; the public getters
return exactly those fields: getFixedLegendItems() returns fixedLegendItems and getDatasetCount() returns datasets.size()); the
facade passes `this` (typed CategoryPlot) to hop 1 and returns hop 1's result. No field is written, no write-back. No private method
of CategoryPlot is involved (no V4), no package-private type (no V3/V5). No visibility widened, no new type, no reflection, no
signature, modifier, override or throws change (the facade keeps `public LegendItemCollection getLegendItems()`), no test edit.
state_passed: the receiver `this` (CategoryPlot) to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Chart-19-probe/w of the fixture the
first statement of getLegendItems() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; `defects4j test`
(full suite): 36 failing tests, all chart drawings that build a legend (JFreeChart.draw -> LegendTitle.arrange -> fetchLegendItems ->
CategoryPlot.getLegendItems); GanttChartTests::testDrawWithNullInfo2 (which catches only NullPointerException) fails with
java.lang.IllegalStateException: PROBE-REACHED at CategoryPlot.getLegendItems(CategoryPlot.java:1760) from
LegendTitle.fetchLegendItems(LegendTitle.java:397); the other 35, among them the trigger GanttChartTests::testDrawWithNullInfo, catch
the exception and fail their assertTrue(success). The facade is reached by existing tests (through the legend, no direct call).

Hosts (host_mode = "1500"; `mr_lib.py preview Chart-19 org/jfree/chart/plot/CategoryPlot.java 5`, instance seed 3716, draw order,
none substituted):
  hop 1 renderer.AbstractRenderer  2730 lines  plotLegendItems    decision: the plot's fixed legend items when they are set
  hop 2 axis.ValueAxis             1659 lines  createLegendItems  placement: creates the collection the items are added to
  hop 3 data.general.DatasetUtilities 1546 lines addLegendItems   pass-through
  hop 4 JFreeChart                 1862 lines  appendLegendItems  aggregation: for each dataset index with a renderer, the renderer's
                                                                  item of each series, in index and series order, skipping a null item
  hop 5 ChartFactory               2186 lines  getSeriesCounts    GOLD: the per-dataset step, the number of series of each dataset of
                                                                  the plot
Host newline counts 2730, 1659, 1546, 1862, 2186; the smallest host is DatasetUtilities (1546 lines); the gold host has 2186 lines.
The correct configuration returns the same collection as the original for every plot: the same fixed-items shortcut; the same dataset
indices (0 .. getDatasetCount()-1); an index whose dataset is null has series count 0 and contributes nothing, exactly as the original's
dataset test; an index whose renderer is null contributes nothing; otherwise the items of series 0 .. getRowCount()-1 in order, null
items skipped. The only order change is that getRowCount() is now also asked of a dataset whose renderer is null (no side effect).

Fault (one-line omission of a special-case decision in the gold): the decision that gives a dataset index without a dataset a series
count of zero is dropped (`if (dataset != null) { result[i] = dataset.getRowCount(); }` becomes `result[i] = dataset.getRowCount();`),
so a plot that has a dataset index whose dataset is null throws a NullPointerException in the gold. The gold then reads as the ordinary
routine "the row count of each dataset of the plot". Trigger: the EXISTING test GanttChartTests::testDrawWithNullInfo; its chart is
ChartFactory.createGanttChart(..., null dataset, legend true, ...) and drawing it builds the legend; the NullPointerException is caught
by the test and assertTrue(success) fails at GanttChartTests.java:122. It is the only test that draws a category chart with a null
dataset (screen: making DatasetUtilities.isEmptyOrNull(CategoryDataset) throw on null fails exactly this test); gate G5 checks the full
suite.

The gold's javadoc states the idiomatic contract (the number of series in each of the datasets of the plot, one entry per dataset index)
and is silent on null datasets. A CategoryPlot's dataset at an index may be null (CategoryPlot.getDataset(int): "The dataset (possibly
null)"; the Gantt chart is created with a null dataset), and the convention that a missing dataset has no series and adds no legend
item is pinned outside the gold: AbstractCategoryItemRenderer.getLegendItems (the renderer's own legend items for its dataset index:
`if (dataset != null)` around the series loop), XYPlot.getLegendItems (the same step for the XY datasets of an XYPlot), and
DatasetUtilities.isEmptyOrNull(CategoryDataset) ("true if the dataset is empty (or null)"), which CategoryPlot.render uses to skip a
null dataset when the plot is drawn; passing tests: CategoryPlotTests::test1654215 (a renderer index without a corresponding dataset
must not make drawing throw), DatasetUtilitiesTests::testIsEmptyOrNullXYDataset (a null dataset counts as empty) and
GanttChartTests::testReplaceDataset (a null dataset is a regular state of the plot: setDataset(null) notifies the chart).

Single owner: only the gold reads the plot's datasets; hops 1-3 hand the plot (and the collection) along and hop 4 reads only the
series counts the gold returns and the renderers. The NullPointerException is raised inside the gold before it returns, so no caller
can filter or recover it in one line except by not calling the gold for the plot. Declared alternatives (G9), each leaves the trigger
failing: hop 4 also requires a dataset at the index before asking the renderer; hop 1 asks for the created items only when the plot has
at least one dataset index; hop 3 adds the items only when the plot has at least one dataset index.
Recorded bypasses (edits that do not repair the chain but skip the gold for some plots, each inconsistent with its hop's own javadoc
"a legend item for each series in each of the datasets"):
 B-1 at hop 1, 2, 3 or 4 (or the facade): skip the gold when the PRIMARY dataset is null, e.g. hop 4
     `int[] seriesCounts = plot.getDataset() == null ? new int[0] : ChartFactory.getSeriesCounts(plot);`; this passes the trigger (its
     plot has a single, null dataset) but drops every item of the secondary datasets of a plot whose primary dataset is null and still
     throws for a null secondary dataset; the gold still throws against its own contract. Checked on the variant in a scratch
     copy (the hop 4 form): trigger passes, full suite 0 failing tests.
 B-0 the facade's original body (or a hop re-deriving the series counts from plot.getDataset(i) itself) re-implements the computation
     and makes the gold dead.

Lie: the facade's javadoc claims the datasets are visited from the last index down to the first, as when the plot is drawn in its
default rendering order, so that the items of the primary dataset come last; the chain visits the indices upwards and the items of
the primary dataset come first. It names neither null datasets, the series counts, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: plot gives the dataset count (array size and loop bound) and each dataset; it is not only argument-checked (no check).
  T2 absent: datasetCount bounds the loop and sizes the array (computed before the loop, not frozen); result is written at the
     advancing index i and returned; dataset is read by the decision and the row count; the decision changes result[i] (0 or the row
     count); no literal-initialised local.
  T3 absent: one special-case treatment (a dataset that is not there) of the only element the gold reads per index; no enum, type code,
     pair, range end or named format; no other member gets a treatment the dataset lacks.
  T4 absent: 'Returns the number of series in each of the datasets of a category plot' and '@return An array containing the number of
     series for each dataset index of the plot' are general descriptions the loop addresses; '@param plot the plot (null not
     permitted)' is a caller precondition; no inline comment.
 Variant gold (javadoc, signature, datasetCount = plot.getDatasetCount(), result = new int[datasetCount], loop i over the indices:
 dataset = plot.getDataset(i); result[i] = dataset.getRowCount(); return result):
  T1 absent: plot is read for the dataset count and for each dataset; both reach the returned array.
  T2 absent: datasetCount is a bound computed before the loop (not frozen); i is the for-loop cursor and advances; result is written at
     the moving index i and returned; dataset is read by getRowCount(), whose value is stored; no literal-initialised local; no
     decision left, so no dead branch.
  T3 absent: no special-case treatment of any member remains ('No member handled'); the gold's text names no class ("non-null",
     "empty", "missing") that it would handle in part.
  T4 absent: 'the number of series in each of the datasets of a category plot' and 'An array containing the number of series for each
     dataset index of the plot' are general descriptions that the loop and the stored row counts address (like 'the reduced
     fraction'); '(null not permitted)' on plot is a caller precondition; the identifiers datasetCount, result, dataset name what they
     hold; no inline comment."""

CP = "source/org/jfree/chart/plot/CategoryPlot.java"
AR = "source/org/jfree/chart/renderer/AbstractRenderer.java"
VA = "source/org/jfree/chart/axis/ValueAxis.java"
DU = "source/org/jfree/data/general/DatasetUtilities.java"
JF = "source/org/jfree/chart/JFreeChart.java"
CF = "source/org/jfree/chart/ChartFactory.java"

GOLD_TEXT = '''/**
 * Returns the number of series in each of the datasets of a category plot.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 *
 * @return An array containing the number of series for each dataset index
 *         of the plot.
 */
public static int[] getSeriesCounts(CategoryPlot plot) {
    int datasetCount = plot.getDatasetCount();
    int[] result = new int[datasetCount];
    for (int i = 0; i < datasetCount; i++) {
        CategoryDataset dataset = plot.getDataset(i);
        if (dataset != null) {
            result[i] = dataset.getRowCount();
        }
    }
    return result;
}'''

HOP1 = '''/**
 * Returns the legend items for a category plot.  If the plot has a fixed
 * set of legend items, that set is returned, otherwise a legend item is
 * created for each series in each of the plot's datasets.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 *
 * @return The legend items.
 */
public static LegendItemCollection plotLegendItems(CategoryPlot plot) {
    LegendItemCollection result = plot.getFixedLegendItems();
    if (result == null) {
        result = ValueAxis.createLegendItems(plot);
    }
    return result;
}'''

HOP2 = '''/**
 * Creates a new collection containing a legend item for each series in
 * each of the datasets of a category plot.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 *
 * @return The legend items (never <code>null</code>).
 */
public static LegendItemCollection createLegendItems(CategoryPlot plot) {
    LegendItemCollection result = new LegendItemCollection();
    DatasetUtilities.addLegendItems(plot, result);
    return result;
}'''

HOP3 = '''/**
 * Adds a legend item for each series in each of the datasets of a category
 * plot to a collection.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param items  the collection (<code>null</code> not permitted).
 */
public static void addLegendItems(CategoryPlot plot,
        LegendItemCollection items) {
    JFreeChart.appendLegendItems(plot, items);
}'''

HOP4 = '''/**
 * Appends a legend item for each series in each of the datasets of a
 * category plot to a collection.  The item for a series is created by the
 * renderer with the same index as the dataset.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param items  the collection (<code>null</code> not permitted).
 */
public static void appendLegendItems(CategoryPlot plot,
        LegendItemCollection items) {
    int[] seriesCounts = ChartFactory.getSeriesCounts(plot);
    for (int index = 0; index < seriesCounts.length; index++) {
        CategoryItemRenderer renderer = plot.getRenderer(index);
        if (renderer != null) {
            for (int series = 0; series < seriesCounts[index]; series++) {
                LegendItem item = renderer.getLegendItem(index, series);
                if (item != null) {
                    items.add(item);
                }
            }
        }
    }
}'''

DESIGN = {
 "instance": "Chart-19", "project": "Chart", "bug_id": 19, "seed": 3716,
 "src_root": "source", "test_root": "tests",
 "facade": {"file": CP, "class": "org.jfree.chart.plot.CategoryPlot", "method": "getLegendItems", "near_line": 1759},
 "facade_variant": "V2",
 "state_passed": "the receiver this (CategoryPlot) to hop 1; hops call its public getFixedLegendItems(), getDatasetCount(), "
                 "getDataset(int) and getRenderer(int); no write-back",
 "reachability_probe": "probe in CategoryPlot.getLegendItems: full suite 36 failing tests (all legend-building chart drawings); "
                       "GanttChartTests::testDrawWithNullInfo2 fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "CategoryPlot.getLegendItems(CategoryPlot.java:1760) from LegendTitle.fetchLegendItems(LegendTitle.java:397); "
                       "the trigger GanttChartTests::testDrawWithNullInfo is among the 36",
 "trigger": {"existing": True, "test_file": "tests/org/jfree/chart/junit/GanttChartTests.java",
             "test_class": "org.jfree.chart.junit.GanttChartTests", "test_method": "testDrawWithNullInfo"},
 "expected_signature": "at org.jfree.chart.junit.GanttChartTests.testDrawWithNullInfo(GanttChartTests.java:122)",
 "gold": {"method": "getSeriesCounts", "text": GOLD_TEXT,
          "fault": {"old": "            CategoryDataset dataset = plot.getDataset(i);\n"
                           "            if (dataset != null) {\n"
                           "                result[i] = dataset.getRowCount();\n"
                           "            }\n",
                    "new": "            CategoryDataset dataset = plot.getDataset(i);\n"
                           "            result[i] = dataset.getRowCount();\n"}},
 "chain": {
   "facade_body": "return org.jfree.chart.renderer.AbstractRenderer.plotLegendItems(this);",
   "lie": "The datasets are visited from the last index down to the first, as when the plot is drawn in its default rendering "
          "order, so that the items of the primary dataset come last.",
   "hops": [
     {"file": AR, "class": "org.jfree.chart.renderer.AbstractRenderer", "method": "plotLegendItems",
      "imports": ["org.jfree.chart.LegendItemCollection", "org.jfree.chart.axis.ValueAxis", "org.jfree.chart.plot.CategoryPlot"],
      "text": HOP1},
     {"file": VA, "class": "org.jfree.chart.axis.ValueAxis", "method": "createLegendItems",
      "imports": ["org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.CategoryPlot",
                  "org.jfree.data.general.DatasetUtilities"],
      "text": HOP2},
     {"file": DU, "class": "org.jfree.data.general.DatasetUtilities", "method": "addLegendItems",
      "imports": ["org.jfree.chart.JFreeChart", "org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.CategoryPlot"],
      "text": HOP3},
     {"file": JF, "class": "org.jfree.chart.JFreeChart", "method": "appendLegendItems",
      "imports": ["org.jfree.chart.renderer.category.CategoryItemRenderer"], "text": HOP4},
     {"file": CF, "class": "org.jfree.chart.ChartFactory", "method": "getSeriesCounts", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jfree.chart.renderer.category.AbstractCategoryItemRenderer::getLegendItems",
              "org.jfree.chart.plot.XYPlot::getLegendItems",
              "org.jfree.data.general.DatasetUtilities::isEmptyOrNull",
              "org.jfree.chart.plot.CategoryPlot::render"],
 "ownership_reason": "Only the gold reads the datasets of the plot and decides how many series each dataset index has; hops 1-3 hand "
                     "the plot and the collection along (hop 1 answers the fixed legend items, hop 2 creates the collection) and "
                     "hop 4 reads only the series counts the gold returns and the plot's renderers. The variant gold dereferences "
                     "a null dataset and throws before returning, so no caller can filter or recover the count of a dataset index "
                     "without a dataset in one line, short of not calling the gold. The gold promises the number of series of "
                     "each dataset index of the plot, and a CategoryPlot's dataset at an index may be null (getDataset: 'possibly "
                     "null'; the trigger's Gantt chart is created with a null dataset). The convention that a missing dataset has "
                     "no series and adds no legend item is pinned outside the gold: AbstractCategoryItemRenderer.getLegendItems "
                     "(the renderer's own legend items for its dataset index, the series loop only for a dataset that is not "
                     "null), XYPlot.getLegendItems (the same step for an XYPlot) and DatasetUtilities.isEmptyOrNull(CategoryDataset) "
                     "('true if the dataset is empty (or null)'), which CategoryPlot.render uses to skip a null dataset when the "
                     "plot is drawn; CategoryPlotTests test1654215 requires that a renderer index without a corresponding dataset "
                     "does not make drawing throw, DatasetUtilitiesTests testIsEmptyOrNullXYDataset that a null dataset counts as "
                     "empty, and GanttChartTests testReplaceDataset that a null dataset is a regular state of the plot.",
 "ownership_tests": ["org.jfree.chart.plot.junit.CategoryPlotTests::test1654215",
                     "org.jfree.data.general.junit.DatasetUtilitiesTests::testIsEmptyOrNullXYDataset",
                     "org.jfree.chart.junit.GanttChartTests::testReplaceDataset"],
 "compensating": {
   "chain": [
     {"file": JF, "old": "            if (renderer != null) {\n                for (int series = 0; series < seriesCounts[index]; series++) {",
      "new": "            if (renderer != null && plot.getDataset(index) != null) {\n                for (int series = 0; series < seriesCounts[index]; series++) {",
      "why": "hop 4 also requires a dataset at the index before asking the renderer for items"},
     {"file": AR, "old": "        if (result == null) {\n            result = ValueAxis.createLegendItems(plot);",
      "new": "        if (result == null && plot.getDatasetCount() > 0) {\n            result = ValueAxis.createLegendItems(plot);",
      "why": "hop 1 asks for the created items only when the plot has at least one dataset index"},
     {"file": DU, "old": "        JFreeChart.appendLegendItems(plot, items);",
      "new": "        if (plot.getDatasetCount() > 0) {\n            JFreeChart.appendLegendItems(plot, items);\n        }",
      "why": "hop 3 adds the items only when the plot has at least one dataset index"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts drawn by mr_lib.py preview Chart-19 org/jfree/chart/plot/CategoryPlot.java 5 with the "
               "instance seed 3716 (the draw excludes the facade file CategoryPlot.java, the only allowed candidates' file), used "
               "in draw order, none substituted: renderer.AbstractRenderer (hop 1, 2730 lines), axis.ValueAxis (hop 2, 1659), "
               "data.general.DatasetUtilities (hop 3, 1546; the smallest host), JFreeChart (hop 4, 1862), ChartFactory (hop 5, "
               "gold, 2186). All five are public top-level classes in which a static method compiles (AbstractRenderer, "
               "ValueAxis and ChartFactory are abstract and DatasetUtilities is final, which does not affect a static method). "
               "Anchors from stageB_lib.pick_insertion_anchor with seed 3716 + 100 + i (as mr3_spec.py inserts them): hop 1 "
               "after `getBaseFillPaint` (seed 3816), hop 2 after `getLowerBound` (3817), hop 3 after "
               "`createConsolidatedPieDataset` (3818), hop 4 after `handleClick` (3819), hop 5 after `createPieChart` (3820). "
               "The facade calls hop 1 by its fully-qualified name; each hop imports the next host and the types it names.",
}
