"""Main run Chart-14__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Chart-14, a bug with no static facade; the real bug modified CategoryPlot and XYPlot, and the facade is in XYPlot). No static pair
(BUILD_BRIEF_C10I_B8_NOTE section 1).

Facade: XYPlot.getLegendItems() (allowed instance target of BATCH8_PREREGISTRATION.md row 212; facade_planned_by null, no facade
reuse). The other two allowed targets were not used: CategoryPlot.getRendererForDataset has no direct test caller (it is reached only
through CategoryPlot.getDataRange, which every category chart test drawing a plot passes through, so no omission in it is caught by a
single test), and CategoryPlot.getLegendItems is reached only by drawing (LegendTitle) in many chart tests, with no test asserting its
result.
Original computation: if the fixed legend items are set (private field fixedLegendItems) they are returned; otherwise a new
LegendItemCollection is filled by visiting the dataset indices 0 .. datasets.size() - 1 in order; an index with a null dataset adds
nothing; the renderer is getRenderer(index), or getRenderer(0) when that is null; with a non-null renderer, for each series 0 ..
getSeriesCount() - 1 that is visible (isSeriesVisible) and visible in the legend (isSeriesVisibleInLegend), the renderer's
getLegendItem(index, series) is added when it is not null.

facade_variant: V2 (receiver as parameter). The computation needs the plot's public methods getDatasetCount(), getDataset(int),
getRenderer(int) and getRenderer() (the original calls getDataset(int) and getRenderer(int) on this, so an override still applies);
the facade keeps the original early return of the private field fixedLegendItems (state read inside the class) and passes `this`,
typed XYPlot, to hop 1. getDatasetCount() returns datasets.size(), and getRenderer() is getRenderer(0), so the chain computes the
original result. No field is written, no write-back. No private method of XYPlot is involved (no V4), no package-private type (no
V3/V5). No visibility widened, no type added, no signature, modifier, override or throws change, no reflection, no test edit.
state_passed: the receiver `this` (XYPlot) to hop 1, after the facade's own fixedLegendItems check; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Chart-14-probe of the fixture, the
first statement of XYPlot.getLegendItems() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j
compile OK; `defects4j test -t org.jfree.chart.plot.junit.XYPlotTests::testGetLegendItems`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at org.jfree.chart.plot.XYPlot.getLegendItems(XYPlot.java:4674), called from
XYPlotTests.testGetLegendItems(XYPlotTests.java:828). The facade is reached directly by the trigger.
Screen (same scratch copy, before designing the chain): with only the renderer-0 fallback removed from the original
getLegendItems, the full suite has exactly 1 failing test, XYPlotTests::testGetLegendItems (baseline full suite: 0 failing).

Hosts (host_mode = "1500"; `mr_lib.py preview Chart-14 org/jfree/chart/plot/XYPlot.java 5` with the instance seed 6675, used in draw
order, none substituted):
  hop 1 axis.ValueAxis                          1659 lines  legendItemsFor         aggregation: creates the collection, returns it
  hop 2 renderer.category.AbstractCategoryItemRenderer 1700 lines  addLegendItems  fold: visits the dataset indices in order
  hop 3 ChartFactory                            2186 lines  addDatasetLegendItems  placement: reads the dataset at the index, an index
                                                                                   with no dataset adds nothing
  hop 4 axis.DateAxis                           1813 lines  appendLegendItems      pass-through
  hop 5 renderer.AbstractRenderer               2758 lines  addSeriesLegendItems   GOLD: chooses the renderer for the dataset and adds
                                                                                   the items of its visible series
Host newline counts 1659, 1700, 2186, 1813, 2758; the smallest host is ValueAxis (1659 lines); the gold host has 2758 lines.

Fault (one-statement omission of a special-case step in the gold's decision): the fallback to the plot's primary renderer is dropped
(`if (renderer == null) { renderer = plot.getRenderer(); }` is removed after `XYItemRenderer renderer = plot.getRenderer(datasetIndex);`),
so a dataset whose index has no renderer of its own adds no legend items. The gold then reads as the ordinary routine "take the
dataset's renderer; if there is one, add an item for each visible series". Trigger: the EXISTING test
XYPlotTests::testGetLegendItems (dataset 0 with renderer 0, dataset 1 with no renderer of its own; one series each):
assertEquals(2, items.getItemCount()) fails with expected:<2> but was:<1>. It is the only failing test of the full suite under the
equivalent omission in the original method (screen above), and gate G5 checks the full suite on the variant.

The gold's javadoc states the idiomatic contract (it adds the legend items for the series of the given dataset: those that are visible
and visible in the legend, created by the plot's renderer) and is silent on which renderer serves a dataset whose index has none. The
plot draws such a dataset with its primary renderer, so the variant leaves out the items of a dataset the plot shows, and the
contract "the legend items for the series of the dataset" is violated on the trigger input (dataset 1 has a visible series and gets no
item). The convention is pinned outside the gold: XYPlot.getRendererForDataset ("checks if there is a renderer with the same index (if
not, the method returns renderer(0)") and XYPlot.render (`renderer = getRenderer(index); if (renderer == null) { renderer =
getRenderer(); ... }`) do the same step in production; passing tests XYPlotTests::testGetRendererForDataset (dataset 1 without a
renderer maps to r0) and XYLineAndShapeRendererTests::testGetLegendItemSeriesIndex (the primary renderer creates the item for series 2
of dataset 1, which has no renderer of its own).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: plot supplies the renderers; datasetIndex selects the renderer and is passed to getLegendItem; dataset bounds the
     series loop; items receives every add.
  T2 absent: renderer is read by the null test and by the three renderer calls (and reassigned by the fallback); seriesCount bounds
     the loop; series advances; item is read by the null test and the add; the fallback branch and the renderer null test both change
     the result (renderer 0 may also be null).
  T3 absent: both visibility flags (isSeriesVisible, isSeriesVisibleInLegend) are tested; a null renderer and a null item are both
     handled; no class named in the gold's text is handled in part.
  T4 absent: 'the legend items for the series of one dataset', 'created by the plot's renderer', 'visible and visible in the legend',
     'in series order' and the @param clauses are met by lines of the body; caller preconditions ('null not permitted') are not T4.
 Variant gold (javadoc, signature, `renderer = plot.getRenderer(datasetIndex)`, `if (renderer != null)`, the series loop):
  T1 absent: plot, datasetIndex, dataset and items each change the result; none is only argument-checked.
  T2 absent: renderer is read by the null test and by the renderer calls (a null renderer adds nothing, a non-null one adds items);
     seriesCount bounds the loop, series advances, item reaches the add; the two if statements each decide live statements; no
     literal-initialised or frozen local.
  T3 absent: the gold has no renderer-substitution treatment at all ('No member handled'); both visibility flags are tested; null
     renderer and null item are both handled; the gold names no set it handles in part.
  T4 absent: no phrase names a renderer rule, an index rule or a case the body visibly does not meet; 'created by the plot's renderer'
     is met by plot.getRenderer(datasetIndex); 'visible and visible in the legend' and 'in series order' are met; no inline comment;
     identifiers (renderer, seriesCount, series, item) name nothing the body does not meet.

Single owner: only the gold chooses the renderer that creates the items of a dataset; hop 1 creates and returns the collection, hop 2
visits the dataset indices, hop 3 reads the dataset at the index and skips an index with none, hop 4 passes the values along. No
non-gold hop sees a renderer, so once the gold finds no renderer at the index, the items of that dataset can appear only if a caller
replaces the gold, re-creates its items from another renderer, or alters the plot. Declared alternatives (G9): hop 2 visits the
indices from the last down to the first; hop 3 reads the primary dataset when the index has none; hop 4 re-derives the dataset index
with plot.indexOf(dataset). None makes the trigger pass.
Recorded bypasses (not declared; each contradicts a hop's documentation or the plot's state):
 B-0 the facade's original body (or any hop computing the items itself, e.g. hop 1 returning the primary renderer's
     getLegendItems() added to the chain's) discards or duplicates the gold's work.
 B-1 hop 4 (or hop 2/3) passes index 0 instead of the dataset's index: the trigger counts 2 items, but they are the items of dataset
     0 created for dataset 1's series count (contradicts 'the index of the dataset in the plot').
 B-2 a hop assigns the primary renderer to the plot at the empty index (plot.setRenderer), mutating the plot (fires a change event)
     where every hop only reads it.

Lie: the facade's javadoc claims the items of all datasets are first gathered in a single list that is sorted by dataset index and
series index before it is copied into the result; no step of the chain builds such a list or sorts anything (items are added to the
result collection directly, in visiting order). It names neither renderers nor datasets without a renderer nor any hop."""

XYP = "source/org/jfree/chart/plot/XYPlot.java"
VA = "source/org/jfree/chart/axis/ValueAxis.java"
ACIR = "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java"
CF = "source/org/jfree/chart/ChartFactory.java"
DA = "source/org/jfree/chart/axis/DateAxis.java"
AR = "source/org/jfree/chart/renderer/AbstractRenderer.java"

GOLD_TEXT = '''/**
 * Adds the legend items for the series of one dataset of an XY plot to a
 * collection.
 * <P>
 * The items are created by the plot's renderer for the series that are
 * visible and visible in the legend, in series order.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param datasetIndex  the index of the dataset in the plot.
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param items  the collection to add the items to (<code>null</code> not
 *     permitted).
 */
public static void addSeriesLegendItems(XYPlot plot, int datasetIndex,
        XYDataset dataset, LegendItemCollection items) {
    XYItemRenderer renderer = plot.getRenderer(datasetIndex);
    if (renderer == null) {
        renderer = plot.getRenderer();
    }
    if (renderer != null) {
        int seriesCount = dataset.getSeriesCount();
        for (int series = 0; series < seriesCount; series++) {
            if (renderer.isSeriesVisible(series)
                    && renderer.isSeriesVisibleInLegend(series)) {
                LegendItem item = renderer.getLegendItem(datasetIndex,
                        series);
                if (item != null) {
                    items.add(item);
                }
            }
        }
    }
}'''

HOP1 = '''/**
 * Returns the legend items for an XY plot: the items for the series of
 * each of the plot's datasets, in the order of the dataset indices.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 *
 * @return The legend items (never <code>null</code>).
 */
public static LegendItemCollection legendItemsFor(XYPlot plot) {
    LegendItemCollection result = new LegendItemCollection();
    AbstractCategoryItemRenderer.addLegendItems(plot, result);
    return result;
}'''

HOP2 = '''/**
 * Adds the legend items for the series of each dataset of an XY plot to a
 * collection, in the order of the dataset indices.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param items  the collection to add the items to (<code>null</code> not
 *     permitted).
 */
public static void addLegendItems(XYPlot plot, LegendItemCollection items) {
    int count = plot.getDatasetCount();
    for (int datasetIndex = 0; datasetIndex < count; datasetIndex++) {
        ChartFactory.addDatasetLegendItems(plot, datasetIndex, items);
    }
}'''

HOP3 = '''/**
 * Adds the legend items for the series of the dataset at an index of an XY
 * plot to a collection.  An index that holds no dataset adds no items.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param datasetIndex  the dataset index.
 * @param items  the collection to add the items to (<code>null</code> not
 *     permitted).
 */
public static void addDatasetLegendItems(XYPlot plot, int datasetIndex,
        LegendItemCollection items) {
    XYDataset dataset = plot.getDataset(datasetIndex);
    if (dataset != null) {
        DateAxis.appendLegendItems(plot, datasetIndex, dataset, items);
    }
}'''

HOP4 = '''/**
 * Adds the legend items for the series of a dataset of an XY plot to a
 * collection.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param datasetIndex  the index of the dataset in the plot.
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param items  the collection to add the items to (<code>null</code> not
 *     permitted).
 */
public static void appendLegendItems(XYPlot plot, int datasetIndex,
        XYDataset dataset, LegendItemCollection items) {
    AbstractRenderer.addSeriesLegendItems(plot, datasetIndex, dataset, items);
}'''

DESIGN = {
 "instance": "Chart-14", "project": "Chart", "bug_id": 14, "seed": 6675,
 "src_root": "source", "test_root": "tests",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (XYPlot) to hop 1, after the facade's own early return of the private field fixedLegendItems; "
                 "no write-back",
 "host_mode": "1500", "host_lines": [1659, 1700, 2186, 1813, 2758],
 "reachability_probe": "XYPlot.getLegendItems() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Chart-14-probe: XYPlotTests::testGetLegendItems fails with PROBE-REACHED at "
                       "XYPlot.getLegendItems(XYPlot.java:4674), called from XYPlotTests.java:828",
 "facade": {"file": XYP, "class": "org.jfree.chart.plot.XYPlot", "method": "getLegendItems", "near_line": 4673},
 "trigger": {"existing": True, "test_file": "tests/org/jfree/chart/plot/junit/XYPlotTests.java",
             "test_class": "org.jfree.chart.plot.junit.XYPlotTests", "test_method": "testGetLegendItems"},
 "expected_signature": "expected:<2> but was:<1>",
 "gold": {"method": "addSeriesLegendItems", "text": GOLD_TEXT,
          "fault": {"old": "        XYItemRenderer renderer = plot.getRenderer(datasetIndex);\n"
                           "        if (renderer == null) {\n"
                           "            renderer = plot.getRenderer();\n"
                           "        }",
                    "new": "        XYItemRenderer renderer = plot.getRenderer(datasetIndex);"}},
 "chain": {
   "facade_body": "if (this.fixedLegendItems != null) {\n            return this.fixedLegendItems;\n        }\n"
                  "        return ValueAxis.legendItemsFor(this);",
   "lie": "The items of all the datasets are first gathered in a single list, which is sorted by dataset index and series index "
          "before it is copied into the result.",
   "hops": [
     {"file": VA, "class": "org.jfree.chart.axis.ValueAxis", "method": "legendItemsFor",
      "imports": ["org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.XYPlot",
                  "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer"], "text": HOP1},
     {"file": ACIR, "class": "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer", "method": "addLegendItems",
      "imports": ["org.jfree.chart.ChartFactory", "org.jfree.chart.plot.XYPlot"], "text": HOP2},
     {"file": CF, "class": "org.jfree.chart.ChartFactory", "method": "addDatasetLegendItems",
      "imports": [], "text": HOP3},
     {"file": DA, "class": "org.jfree.chart.axis.DateAxis", "method": "appendLegendItems",
      "imports": ["org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.XYPlot",
                  "org.jfree.chart.renderer.AbstractRenderer", "org.jfree.data.xy.XYDataset"], "text": HOP4},
     {"file": AR, "class": "org.jfree.chart.renderer.AbstractRenderer", "method": "addSeriesLegendItems",
      "imports": ["org.jfree.chart.LegendItem", "org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.XYPlot",
                  "org.jfree.chart.renderer.xy.XYItemRenderer", "org.jfree.data.xy.XYDataset"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.chart.plot.XYPlot::getRendererForDataset",
              "org.jfree.chart.plot.XYPlot::render"],
 "ownership_reason": "Only the gold chooses the renderer that creates the legend items of a dataset: hop 1 creates and returns the "
                     "collection, hop 2 visits the dataset indices in order, hop 3 reads the dataset at the index and skips an "
                     "index with none, hop 4 passes the values along; no other hop sees a renderer. With the fallback dropped, a "
                     "dataset whose index has no renderer of its own adds no items, although the plot draws it with its primary "
                     "renderer, so the gold's contract (the legend items for the series of the dataset) is violated on the "
                     "trigger input. The convention is pinned outside the gold: XYPlot.getRendererForDataset (the renderer with "
                     "the same index, or renderer 0 if there is none) and XYPlot.render (getRenderer(index), or getRenderer() if "
                     "that is null) do the same step in production; XYPlotTests::testGetRendererForDataset (a dataset without a "
                     "renderer maps to renderer 0) and XYLineAndShapeRendererTests::testGetLegendItemSeriesIndex (the primary "
                     "renderer creates the item for a series of dataset 1, which has no renderer of its own) pass.",
 "ownership_tests": ["org.jfree.chart.plot.junit.XYPlotTests::testGetRendererForDataset",
                     "org.jfree.chart.renderer.xy.junit.XYLineAndShapeRendererTests::testGetLegendItemSeriesIndex"],
 "compensating": {
   "chain": [
     {"file": ACIR, "old": "    for (int datasetIndex = 0; datasetIndex < count; datasetIndex++) {\n"
                           "            ChartFactory.addDatasetLegendItems(plot, datasetIndex, items);",
      "new": "    for (int datasetIndex = count - 1; datasetIndex >= 0; datasetIndex--) {\n"
             "            ChartFactory.addDatasetLegendItems(plot, datasetIndex, items);",
      "why": "hop 2 visits the dataset indices from the last down to the first"},
     {"file": CF, "old": "XYDataset dataset = plot.getDataset(datasetIndex);\n        if (dataset != null) {\n"
                         "            DateAxis.appendLegendItems(",
      "new": "XYDataset dataset = plot.getDataset(datasetIndex) != null ? plot.getDataset(datasetIndex) : plot.getDataset();\n"
             "        if (dataset != null) {\n            DateAxis.appendLegendItems(",
      "why": "hop 3 reads the primary dataset when the index holds none"},
     {"file": DA, "old": "AbstractRenderer.addSeriesLegendItems(plot, datasetIndex, dataset, items);",
      "new": "AbstractRenderer.addSeriesLegendItems(plot, plot.indexOf(dataset), dataset, items);",
      "why": "hop 4 re-derives the dataset index from the plot"},
   ],
 },
 "host_notes": "host_mode 1500: hosts drawn by `mr_lib.py preview Chart-14 org/jfree/chart/plot/XYPlot.java 5` with seed 6675, "
               "used in draw order, none substituted: axis.ValueAxis (hop 1, 1659 lines), renderer.category."
               "AbstractCategoryItemRenderer (hop 2, 1700), ChartFactory (hop 3, 2186), axis.DateAxis (hop 4, 1813), "
               "renderer.AbstractRenderer (hop 5, gold, 2758); the smallest host is ValueAxis (1659). All five are public "
               "top-level classes (ValueAxis, AbstractCategoryItemRenderer and AbstractRenderer abstract) in which a public "
               "static method compiles; neither allowed-candidate file (XYPlot, CategoryPlot) is a host. Anchors as previewed "
               "(seed 6675 + 100 + i): hop 1 after getLowerMargin (6775), hop 2 after addAnnotation (6776), hop 3 after "
               "createPieChart3D (6777), hop 4 after draw (6778), hop 5 after isSeriesVisible (6779). The facade calls hop 1 "
               "through XYPlot's existing import of ValueAxis; each hop imports the next host and the plot/legend/dataset types "
               "it names (ChartFactory already imports XYPlot, XYDataset and DateAxis and shares the package of "
               "LegendItemCollection).",
}
