"""Main run Chart-1__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Chart-1; the real bug modified AbstractCategoryItemRenderer, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE
section 1: pool v2 found no tested public static method in the modified class).

Facade: AbstractCategoryItemRenderer.getLegendItems() (allowed instance target of BATCH9_PREREGISTRATION.md row 337,
facade_planned_by = null, no facade reuse). The other allowed target, addAnnotation(CategoryAnnotation, Layer), was not used: its
computation is one layer decision and one list add per branch, with no iteration or per-element core to hand to hop 5, and its only
tester (AbstractCategoryItemRendererTests::testEquals) cannot see an annotation placed in the other layer's list, so the only
omissions it catches leave an empty branch (a dead decision) or a one-of-two layer treatment.
Original computation of the facade: a renderer without a plot gives an empty collection; otherwise the renderer's dataset index in
the plot (plot.getIndexOf(this)) selects the dataset, a null dataset gives an empty collection, and the series 0..n-1 of the dataset
(n = getRowCount()) are visited upward when the plot's row rendering order is SortOrder.ASCENDING and downward otherwise; for every
series that isSeriesVisibleInLegend, the item getLegendItem(index, series) is added when it is not null.
isSeriesVisibleInLegend(series) is AbstractRenderer's lookup "the per-series flag getSeriesVisibleInLegend(series) when it is not
null, else the base flag getBaseSeriesVisibleInLegend()"; it is declared only in AbstractRenderer (no renderer overrides it), so
the gold's lookup through the two public getters of the CategoryItemRenderer interface gives exactly the original decision for every
renderer the facade can pass.

facade_variant: V2 (receiver as parameter) with V1 (state as parameters). The chain needs the renderer's public methods
getSeriesVisibleInLegend(int), getBaseSeriesVisibleInLegend() and getLegendItem(int, int) (getLegendItem is overridden per renderer
subclass, so its logic cannot be moved): the facade passes `this`, typed as the interface CategoryItemRenderer that the class
implements, which declares all three. The private field plot is read by the facade and passed as a value (CategoryPlot). The
facade keeps the original guard (no plot -> empty collection). No private method of the class is called by the computation (no V4),
no package-private type is involved (no V3/V5). No signature, modifier, override or throws change; no new type; no reflection; no
test edit; no field written.
state_passed: `this` (as CategoryItemRenderer) and the private field plot (CategoryPlot) to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Chart-1-probe/w of the fixture, the
first statement of getLegendItems was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests::test2947660`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at AbstractCategoryItemRenderer.getLegendItems(AbstractCategoryItemRenderer.java:1791)
called from AbstractCategoryItemRendererTests.test2947660(AbstractCategoryItemRendererTests.java:398). Other tests reach the facade
only through CategoryPlot.getLegendItems while drawing, serializing or notifying; only test2947660 inspects the returned items.

Hosts (host_mode = "1500"; `mr_lib.py preview Chart-1 org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java 5`, instance
seed 2094; the seeded draw used in draw order, nothing substituted):
  hop 1 axis.DateAxis              1951 lines  rendererLegendItems  the renderer's dataset index in the plot
  hop 2 plot.SpiderWebPlot         1669 lines  datasetLegendItems   the dataset lookup; no dataset -> empty collection; the row
                                                                    rendering order of the plot
  hop 3 plot.XYPlot                6028 lines  legendItemsForRows   the series count of the dataset (getRowCount)
  hop 4 ChartFactory               1671 lines  createLegendItems    placement: the row rendering order as a first series index and
                                                                    an index step (ASCENDING: 0 and +1; otherwise n-1 and -1)
  hop 5 renderer.AbstractRenderer  3311 lines  collectLegendItems   GOLD: the walk over the series, the per-series legend visibility
                                                                    decision, the null-item check and the adds
Host sizes 1951, 1669, 6028, 1671, 3311; the smallest host is SpiderWebPlot (1669 lines); the gold host has 3311 lines. The correct
configuration returns exactly the original collection for every renderer and plot.

Fault (one-line omission of a special-case step in the gold's per-series decision): the gold reads the series' own legend flag and,
when that flag is unset (null), falls back to the renderer's base flag; the fallback step (`if (flag == null) { flag =
Boolean.valueOf(renderer.getBaseSeriesVisibleInLegend()); }`) is dropped, so a series is listed only when its own flag is
Boolean.TRUE. The gold then reads as the ordinary routine "list the series flagged visible in the legend". Every series of a
renderer with default settings has an unset flag, so its legend becomes empty. Trigger: the EXISTING test
AbstractCategoryItemRendererTests::test2947660 (the real Chart-1 trigger). Its first three assertions (no plot -> not null and 0
items; empty dataset -> 0 items) still hold; after dataset.addValue(1.0, "S1", "C1"), assertEquals(1, lic.getItemCount()) fails with
expected:<1> but was:<0>. It is the only test that newly fails (gate G5): the other tests that reach the facade draw charts (an
empty legend is drawn without error) or compare and serialize plots, and the tests that inspect legend visibility call
getLegendItem directly (BarRendererTests / BoxAndWhiskerRendererTests testGetLegendItem), which keeps its own visibility check.

The gold's javadoc states the idiomatic contract (the legend items for the series of one dataset; series not visible in the legend
and series without an item are skipped) and is silent on how visibility is looked up; a series with default settings is visible in
the legend, so an empty collection for one default series is not the collection the javadoc promises. The convention (an unset
per-series flag falls back to the base flag) is pinned outside the gold: AbstractRenderer.isSeriesVisibleInLegend (the lookup
itself), the CategoryItemRenderer javadoc of getSeriesVisibleInLegend ("returns only the per series settings", pointing to
isSeriesVisibleInLegend for the fallback), AbstractCategoryItemRenderer.getLegendItem and the XY sibling
AbstractXYItemRenderer.getLegendItems, both of which use the fallback lookup; passing tests BarRendererTests::testGetLegendItem (a
default series has an item; an explicit FALSE removes it) and XYPlotTests::testGetLegendItems (default series give 2 items).

Single owner: only the gold decides per series whether its item is listed; hops 1-4 resolve the index, the dataset, the count and
the walk (first index and step) and pass them on. The variant drops every series whose own flag is unset whatever index, dataset,
count, first index or step it receives, so no one-line change of those values restores the trigger's item while keeping the hops'
documentation; making the series visible would need a hop to write the renderer's flags (a side effect no hop documents).
Declared alternatives (G9): hop 3 passes one series more; hop 4 always starts at the first series; hop 2 also returns an empty
collection for a dataset without rows. Each leaves the trigger failing (0 items).
Recorded bypass (not a repair of the chain): B-0 the facade's original body (or a hop rebuilding the items itself with
renderer.isSeriesVisibleInLegend and renderer.getLegendItem) re-implements the computation and makes the chain, including the gold,
dead.

Lie: the facade's javadoc claims that each legend item is made from a copy of the renderer's base legend shape scaled to the height
of the series label; the method copies and scales no shape (the items come from getLegendItem, which looks the shape up unchanged).
It names neither the visibility lookup, the walk, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: renderer is read for the flag, the base flag and the item; datasetIndex is passed to getLegendItem; seriesCount bounds
     the walk; first and step give each series index; there is no argument check.
  T2 absent: result is added to and returned; k advances (k++); series is computed every iteration and read three times; flag is
     reassigned in the fallback and read by the visibility test; item is tested and added; no literal-initialised local; the
     null-flag decision assigns a live flag, the visibility and null-item decisions guard the live add.
  T3 absent: the flag's states are all treated (null by the fallback, then TRUE/FALSE by one test); no enum or type code is read;
     no range pair is named (the walk is a first index, a step and a count); no named class is handled in part.
  T4 absent: 'Series that are not visible in the legend, and series for which the renderer supplies no legend item, are skipped'
     is met by the visibility test and the item != null test; 'never null' by the new collection returned; the @param clauses
     describe the values or are caller preconditions.
 Variant gold (javadoc, signature, the walk with `int series = first + k * step;`,
 `Boolean flag = renderer.getSeriesVisibleInLegend(series);`, `if (Boolean.TRUE.equals(flag))`, the item test and add, `return
 result;`):
  T1 absent: renderer (flag and item), datasetIndex (item), seriesCount (bound), first and step (series index) all change the
     result; none is only argument-checked.
  T2 absent: result is added to and returned; k advances; series is read by both calls; flag decides whether the item is fetched
     and added (live); item is tested and added; no literal-initialised local; no empty, duplicate or constant decision.
  T3 absent: the gold reads one flag and tests it once (listed when TRUE, skipped otherwise); no enum, type code, pair half or
     range end is read and left untreated; the text names no class (no 'default', 'base', 'unset' or 'finite').
  T4 absent: the skipping sentence is met (a series whose flag is not TRUE and a null item are skipped); 'never null' is met; the
     javadoc names no default, fallback, count or order rule; there is no inline comment; the identifiers (result, series, flag,
     item, k, collectLegendItems) name what they hold."""

ACIR = "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java"
DA = "source/org/jfree/chart/axis/DateAxis.java"
SWP = "source/org/jfree/chart/plot/SpiderWebPlot.java"
XYP = "source/org/jfree/chart/plot/XYPlot.java"
CF = "source/org/jfree/chart/ChartFactory.java"
AR = "source/org/jfree/chart/renderer/AbstractRenderer.java"

GOLD_TEXT = '''/**
 * Returns a collection of legend items for the series in one dataset of
 * a category plot, visiting the series that start at the given index and
 * follow each other at the given index step.  Series that are not visible
 * in the legend, and series for which the renderer supplies no legend
 * item, are skipped.
 *
 * @param renderer  the renderer (<code>null</code> not permitted).
 * @param datasetIndex  the dataset index (zero-based).
 * @param seriesCount  the number of series to visit.
 * @param first  the index of the first series to visit.
 * @param step  the index step from one series to the next.
 *
 * @return The legend item collection (never <code>null</code>).
 */
public static LegendItemCollection collectLegendItems(
        CategoryItemRenderer renderer, int datasetIndex, int seriesCount,
        int first, int step) {
    LegendItemCollection result = new LegendItemCollection();
    for (int k = 0; k < seriesCount; k++) {
        int series = first + k * step;
        Boolean flag = renderer.getSeriesVisibleInLegend(series);
        if (flag == null) {
            flag = Boolean.valueOf(renderer.getBaseSeriesVisibleInLegend());
        }
        if (Boolean.TRUE.equals(flag)) {
            LegendItem item = renderer.getLegendItem(datasetIndex, series);
            if (item != null) {
                result.add(item);
            }
        }
    }
    return result;
}'''

HOP1 = '''/**
 * Returns a (possibly empty) collection of legend items for the series
 * that a category renderer draws in a plot.
 *
 * @param renderer  the renderer (<code>null</code> not permitted).
 * @param plot  the plot that the renderer is assigned to
 *              (<code>null</code> not permitted).
 *
 * @return The legend item collection (never <code>null</code>).
 */
public static LegendItemCollection rendererLegendItems(
        CategoryItemRenderer renderer, CategoryPlot plot) {
    int index = plot.getIndexOf(renderer);
    return SpiderWebPlot.datasetLegendItems(renderer, plot, index);
}'''

HOP2 = '''/**
 * Returns a (possibly empty) collection of legend items for the series in
 * a dataset of a category plot, taking the series in the plot's row
 * rendering order.  If the plot has no dataset at the given index, the
 * collection is empty.
 *
 * @param renderer  the renderer (<code>null</code> not permitted).
 * @param plot  the plot (<code>null</code> not permitted).
 * @param datasetIndex  the dataset index.
 *
 * @return The legend item collection (never <code>null</code>).
 */
public static LegendItemCollection datasetLegendItems(
        CategoryItemRenderer renderer, CategoryPlot plot, int datasetIndex) {
    CategoryDataset dataset = plot.getDataset(datasetIndex);
    if (dataset == null) {
        return new LegendItemCollection();
    }
    return XYPlot.legendItemsForRows(renderer, datasetIndex, dataset,
            plot.getRowRenderingOrder());
}'''

HOP3 = '''/**
 * Returns a collection of legend items for the rows (series) of a
 * category dataset, taking the rows in the given row rendering order.
 *
 * @param renderer  the renderer (<code>null</code> not permitted).
 * @param datasetIndex  the dataset index.
 * @param dataset  the dataset (<code>null</code> not permitted).
 * @param order  the plot's row rendering order (<code>null</code> not
 *               permitted).
 *
 * @return The legend item collection (never <code>null</code>).
 */
public static LegendItemCollection legendItemsForRows(
        CategoryItemRenderer renderer, int datasetIndex,
        CategoryDataset dataset, SortOrder order) {
    return ChartFactory.createLegendItems(renderer, datasetIndex,
            dataset.getRowCount(), order);
}'''

HOP4 = '''/**
 * Creates a collection of legend items for the series of a category
 * dataset, taking the series in the given row rendering order: upward
 * from the first series for {@link SortOrder#ASCENDING}, and downward
 * from the last series for any other order.
 *
 * @param renderer  the renderer (<code>null</code> not permitted).
 * @param datasetIndex  the dataset index.
 * @param seriesCount  the number of series in the dataset.
 * @param order  the plot's row rendering order (<code>null</code> not
 *               permitted).
 *
 * @return The legend item collection (never <code>null</code>).
 */
public static LegendItemCollection createLegendItems(
        CategoryItemRenderer renderer, int datasetIndex, int seriesCount,
        SortOrder order) {
    boolean ascending = order.equals(SortOrder.ASCENDING);
    return AbstractRenderer.collectLegendItems(renderer, datasetIndex,
            seriesCount, ascending ? 0 : seriesCount - 1, ascending ? 1 : -1);
}'''

DESIGN = {
 "instance": "Chart-1", "project": "Chart", "bug_id": 1, "seed": 2094,
 "src_root": "source", "test_root": "tests",
 "facade": {"file": ACIR, "class": "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer", "method": "getLegendItems",
            "near_line": 1790},
 "facade_variant": "V2+V1",
 "state_passed": "`this` (typed as the interface CategoryItemRenderer) and the private field plot (CategoryPlot) to hop 1; the "
                 "original no-plot guard stays in the facade; no write-back",
 "reachability_probe": "test2947660 fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "AbstractCategoryItemRenderer.getLegendItems(AbstractCategoryItemRenderer.java:1791) from "
                       "AbstractCategoryItemRendererTests.java:398 (defects4j test -t on the scratch copy, 1 failing test)",
 "trigger": {"existing": True, "test_file": "tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java",
             "test_class": "org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests",
             "test_method": "test2947660"},
 "expected_signature": "expected:<1> but was:<0>",
 "gold": {"method": "collectLegendItems", "text": GOLD_TEXT,
          "fault": {"old": "            Boolean flag = renderer.getSeriesVisibleInLegend(series);\n"
                           "            if (flag == null) {\n"
                           "                flag = Boolean.valueOf(renderer.getBaseSeriesVisibleInLegend());\n"
                           "            }\n"
                           "            if (Boolean.TRUE.equals(flag)) {\n",
                    "new": "            Boolean flag = renderer.getSeriesVisibleInLegend(series);\n"
                           "            if (Boolean.TRUE.equals(flag)) {\n"}},
 "chain": {
   "facade_body": "if (this.plot == null) {\n"
                  "            return new LegendItemCollection();\n"
                  "        }\n"
                  "        return org.jfree.chart.axis.DateAxis.rendererLegendItems(this, this.plot);",
   "lie": "Each legend item is made from a copy of the renderer's base legend shape, which is scaled to the height of the "
          "series label.",
   "hops": [
     {"file": DA, "class": "org.jfree.chart.axis.DateAxis", "method": "rendererLegendItems",
      "imports": ["org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.CategoryPlot",
                  "org.jfree.chart.plot.SpiderWebPlot", "org.jfree.chart.renderer.category.CategoryItemRenderer"],
      "text": HOP1},
     {"file": SWP, "class": "org.jfree.chart.plot.SpiderWebPlot", "method": "datasetLegendItems",
      "imports": ["org.jfree.chart.renderer.category.CategoryItemRenderer"], "text": HOP2},
     {"file": XYP, "class": "org.jfree.chart.plot.XYPlot", "method": "legendItemsForRows",
      "imports": ["org.jfree.chart.ChartFactory", "org.jfree.chart.renderer.category.CategoryItemRenderer",
                  "org.jfree.chart.util.SortOrder", "org.jfree.data.category.CategoryDataset"], "text": HOP3},
     {"file": CF, "class": "org.jfree.chart.ChartFactory", "method": "createLegendItems",
      "imports": ["org.jfree.chart.renderer.AbstractRenderer", "org.jfree.chart.util.SortOrder"], "text": HOP4},
     {"file": AR, "class": "org.jfree.chart.renderer.AbstractRenderer", "method": "collectLegendItems",
      "imports": ["org.jfree.chart.LegendItem", "org.jfree.chart.LegendItemCollection",
                  "org.jfree.chart.renderer.category.CategoryItemRenderer"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.chart.renderer.AbstractRenderer::isSeriesVisibleInLegend",
              "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer::getLegendItem",
              "org.jfree.chart.renderer.xy.AbstractXYItemRenderer::getLegendItems"],
 "ownership_reason": "Only the gold decides, series by series, whether a legend item is listed; hops 1-4 resolve the renderer's "
                     "dataset index, the dataset (an absent dataset gives an empty collection), the series count and the walk "
                     "(the first series index and the index step of the plot's row rendering order) and pass them on unchanged. "
                     "The gold's javadoc promises the legend items for the series of one dataset, skipping only series not "
                     "visible in the legend and series without an item; a series with default settings is visible in the "
                     "legend, so an empty collection for one default series is not that collection. No one-line change of the "
                     "index, the dataset, the count, the first index or the step above the gold lists a series whose own flag "
                     "is unset under the variant gold. The convention that an unset per-series flag falls back to the base flag "
                     "is pinned outside the gold by AbstractRenderer.isSeriesVisibleInLegend (the lookup itself, described by "
                     "the getSeriesVisibleInLegend javadoc as the fallback lookup), by AbstractCategoryItemRenderer.getLegendItem "
                     "and the XY sibling AbstractXYItemRenderer.getLegendItems, which both use it, and by the passing tests "
                     "BarRendererTests testGetLegendItem (a default series has an item, an explicit FALSE removes it) and "
                     "XYPlotTests testGetLegendItems (two default one-series datasets give 2 items).",
 "ownership_tests": ["org.jfree.chart.renderer.category.junit.BarRendererTests::testGetLegendItem",
                     "org.jfree.chart.plot.junit.XYPlotTests::testGetLegendItems",
                     "org.jfree.chart.renderer.category.junit.BoxAndWhiskerRendererTests::testGetLegendItem"],
 "compensating": {
   "chain": [
     {"file": XYP, "old": "dataset.getRowCount(), order);",
      "new": "dataset.getRowCount() + 1, order);",
      "why": "hop 3 hands the gold one series more"},
     {"file": CF, "old": "ascending ? 0 : seriesCount - 1, ascending ? 1 : -1);",
      "new": "0, ascending ? 1 : -1);",
      "why": "hop 4 always starts the walk at the first series"},
     {"file": SWP, "old": "if (dataset == null) {",
      "new": "if (dataset == null || dataset.getRowCount() == 0) {",
      "why": "hop 2 also answers a dataset without rows with an empty collection"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are the recipe's seeded draw: mr_lib.py preview Chart-1 "
               "org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java 5 with the instance seed 2094 (the facade's file "
               "is excluded by the draw), used in draw order, none substituted: axis.DateAxis (hop 1, 1951 lines), "
               "plot.SpiderWebPlot (hop 2, 1669; the smallest host), plot.XYPlot (hop 3, 6028), ChartFactory (hop 4, 1671), "
               "renderer.AbstractRenderer (hop 5, gold, 3311). All five are public top-level classes in which a static method "
               "compiles (ChartFactory and AbstractRenderer are abstract, which does not affect a static method). Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 2094 + 100 + i (as mr3_spec.py inserts them): hop 1 after "
               "`valueToJava2D` (seed 2194), hop 2 after `setBaseSeriesOutlineStroke` (2195), hop 3 after `setRangeAxisLocation` "
               "(2196), hop 4 after `createRingChart` (2197), hop 5 after `setSeriesVisible` (2198). The facade calls hop 1 by its "
               "fully-qualified name; each hop imports the next host where it is in another package (SpiderWebPlot and XYPlot "
               "share org.jfree.chart.plot). The facade's class is not a host.",
}
