"""Main run Chart-4__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Chart-4; the real bug modified XYPlot, the facade's class). No static pair (B8 note section 1: pool v2 found no strictly
tested public static method in XYPlot; the task record's paired_* fields are null).

Facade: XYPlot.getLegendItems() (instance method; allowed targets XYPlot.getLegendItems / getDomainAxisForDataset /
getRangeAxisForDataset, BATCH9_PREREGISTRATION.md rank 339). facade_planned_by = Chart-14__i: this is a planned-elsewhere candidate,
used because neither null-planned candidate can carry the recipe validly (facade_reuse_of Chart-14__i, recorded). The two null-planned
candidates were examined first: getDomainAxisForDataset and getRangeAxisForDataset are an argument guard (which stays in the facade)
followed by one map lookup, `axisIndices.get(0)` and one getDomainAxis/getRangeAxis call. There is no iteration, and the only decision
is the unmapped-dataset fallback to axis 0. A one-line omission there either leaves a literal-initialised axis index that is never
reassigned (T2(b)(i)) or drops the fallback; the fallback is taken by every unmapped dataset on every XY rendering path, so the whole
chart suite fails (no single trigger). Omitting one end of the guard's range check is T3(b), and the guard is not part of the chain.
Original computation of the facade: fixed legend items, when set, are returned as they are; otherwise a new LegendItemCollection
receives, for each dataset slot 0..datasets.size()-1 whose dataset is not null, the items of the dataset's renderer (the renderer
with the dataset's index, or renderer 0 when that slot is empty; none when both are null): for each series i that the renderer
reports as visible and visible in the legend, renderer.getLegendItem(datasetIndex, i), unless that is null.

facade_variant: V2 (receiver as parameter). The facade keeps the original's guard (the early return of the private field
fixedLegendItems, read inside XYPlot, so no visibility change) and makes one call to hop 1 with `this`, typed as XYPlot. The hops use
only public methods of the receiver: getDatasetCount() (which is datasets.size()), getDataset(int) and getRenderer(int). No private
method of XYPlot is called (no V4), and no package-private type is involved (no V3/V5). No signature, modifier, override or throws
change; no new type; no reflection; no test edit.
state_passed: the receiver `this` (XYPlot) to hop 1; the private field fixedLegendItems is read only by the facade's guard; nothing is
written back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Chart-4-probe of the fixture, the first
statement of getLegendItems was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. `defects4j test -t
org.jfree.chart.plot.junit.XYPlotTests::testGetLegendItems`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
XYPlot.getLegendItems(XYPlot.java:5274) from XYPlotTests.testGetLegendItems(XYPlotTests.java:905). Full suite with the probe: 25 failing
tests (testGetLegendItems directly; the rest through LegendTitle when XY charts are drawn, e.g. XYLineChartTests::testDrawWithNullInfo,
XYPlotTests::test1654215, CombinedDomainXYPlotTests::testNotification). The facade is reached by an existing test directly and by
production callers.

Hosts (host_mode = "1500"; `mr_lib.py preview Chart-4 org/jfree/chart/plot/XYPlot.java 5` with the instance seed 5271, used in draw
order; nothing substituted):
  hop 1 data.general.DatasetUtilities          2152 lines  createLegendItems     creates the collection, hands it on, returns it
  hop 2 ChartFactory                           2263 lines  addLegendItems        pass-through
  hop 3 axis.ValueAxis                         1751 lines  appendLegendItems     pass-through
  hop 4 renderer.xy.AbstractXYItemRenderer     1914 lines  addPlotLegendItems    pass-through
  hop 5 axis.Axis                              1578 lines  addSeriesLegendItems  GOLD: the iteration over the datasets, the renderer
                                                                                 for each dataset, and the per-series visibility
                                                                                 decisions and item creation
Host sizes 2152, 2263, 1751, 1914, 1578; the smallest host is Axis (1578 lines), which is also the gold host.
The correct configuration returns the original collection for every plot: the same dataset slots in the same order, the same renderer
choice (slot renderer, else renderer 0, else none), the same series filter and the same null-item skip, into a new collection created
by hop 1; the fixed-items guard is unchanged in the facade.

Fault (a one-line omission of a special-case step in the gold): the step that falls back to renderer 0 when the dataset's own renderer
slot is empty is dropped, so a dataset that the plot draws with its primary renderer gets no legend items. The gold then reads as the
ordinary routine "for each non-null dataset with a renderer, one item per visible series" (CategoryPlot.getLegendItems in this
checkout has exactly that shape). Trigger: the EXISTING test XYPlotTests::testGetLegendItems (two datasets, only renderer 0 set):
assertEquals(2, items.getItemCount()) fails with expected:<2> but was:<1>. It is the only test that newly fails: the same omission
applied to the original getLegendItems in the scratch copy /private/tmp/d4j-mi-Chart-4-omit gave a full suite with exactly 1 failing
test (testGetLegendItems); the drawing tests that reach the facade do not count legend items.

The gold's javadoc states the idiomatic contract (for each dataset, the renderer that draws the dataset supplies one item for every
series that is visible and visible in the legend) and is silent on how that renderer is found; with the omission, the second dataset
of the trigger, which the plot draws with renderer 0, gets no item. The convention is pinned outside the gold: XYPlot.render (the
dataset's renderer, else getRenderer(), else nothing is drawn), XYPlot.getRendererForDataset (javadoc: "if not, the method returns
renderer(0)") and XYPlot.getDataRange (uses getRendererForDataset for each mapped dataset), with XYPlotTests::testGetRendererForDataset
passing (renderer 0 for a dataset whose slot 1 has no renderer); the facade's own javadoc ("Each legend item is generated by the
plot's renderer, since the renderer is responsible for the visual representation of the data") is kept.

Single owner: only the gold reads the plot's datasets and renderers and creates items; hop 1 creates the empty collection and returns
it after the chain; hops 2-4 hand the plot and the collection on unchanged. No one-line change above the gold can give the gold a
renderer for a dataset whose slot is empty, because the gold fetches the renderer from the plot itself. Declared alternatives (G9):
hop 1 hands on the root plot; hop 4 asks for items only when the plot has a primary renderer. Each leaves the trigger failing.
Recorded bypasses (edits that are not repairs of the chain):
 B-0 the facade's original body (or a hop re-implementing the iteration) re-derives the whole collection and makes the chain,
     including the gold, dead.
 B-1 a hop that mutates the plot (for example a loop line in hop 2-4 that calls plot.setRenderer(i, plot.getRenderer(0)) for every
     empty slot) makes the gold see a renderer; it changes the plot's renderer list, registers listeners and fires change events from
     a query, against every hop's documentation ("adds the legend items"). Checked on the variant in a scratch copy (the loop line
     before hop 4's call): trigger passes, full suite 0 failing tests.
 B-2 the trigger only counts items, so a hop that adds some other item (for example items.addAll(plot.getRenderer().getLegendItems())
     in hop 2-4, which repeats the first dataset's items) reaches the count; the legend then lists the first dataset twice and never
     the second dataset's series, against every hop's documentation. Checked on the variant in a scratch copy (appended to hop 4's
     call): trigger passes, full suite 1 failing test (XYPlotTests::testDrawRangeGridlines, a plot without a primary renderer).

Lie: the facade's javadoc claims a legend item is first made for every series of every dataset and the items of hidden series are
then removed from the collection; the chain makes no item for a hidden series and removes nothing. It names neither the renderer
choice, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: plot gives the dataset count, the datasets and the renderers; items receives every created item; no argument check.
  T2 absent: count bounds the outer loop, datasetIndex advances and is passed to getDataset/getRenderer/getLegendItem; dataset, renderer
     (reassigned by the fallback), seriesCount, i and item are each read by a decision or a call that adds; no literal-initialised
     local; every decision (dataset null, the fallback, renderer null, the visibility pair, item null) changes what is added.
  T3 absent: both visibility flags are tested; the null treatment (skip) is given to the dataset, the renderer and the item alike; no
     enum, type code or named format; the slot renderer and renderer 0 are not a pair of the same role.
  T4 absent: 'the renderer that draws the dataset supplies one item for every series that is visible and visible in the legend' is
     met by the renderer lookup, the two visibility tests and getLegendItem; the @param clauses are caller preconditions.
 Variant gold (javadoc, signature, loop over the dataset slots, skip of a null dataset, renderer = plot.getRenderer(datasetIndex),
 skip of a null renderer, loop over the series with the two visibility tests, skip of a null item, add):
  T1 absent: plot gives the count, the datasets and the renderers; items receives the items; both decide the effect.
  T2 absent: count is a bound computed before the loop; datasetIndex and i are advanced by their loops; dataset, renderer,
     seriesCount and item are each read by a decision or a call that leads to items.add; nothing is initialised to a literal and left
     unassigned; each decision skips or adds, so none is dead.
  T3 absent: visible and visible-in-legend are both tested; every null (dataset, renderer, item) gets the same skip; the gold names no
     class ('every', 'primary', 'default') that it handles in part, and no renderer fallback remains for any slot ('No member
     handled').
  T4 absent: 'Adds the legend items for an XY plot to a collection' and 'For each dataset of the plot, the renderer that draws the
     dataset supplies one item for every series that is visible and visible in the legend' are general descriptions that the loops,
     the getRenderer call, the two visibility tests and items.add address; '@param plot  the plot (null not permitted)' and '@param
     items  the collection that the items are added to (null not permitted)' are caller preconditions; no inline comment; the
     identifiers (count, datasetIndex, dataset, renderer, seriesCount, i, item) name what they hold."""

XYP = "source/org/jfree/chart/plot/XYPlot.java"
DSU = "source/org/jfree/data/general/DatasetUtilities.java"
CF = "source/org/jfree/chart/ChartFactory.java"
VA = "source/org/jfree/chart/axis/ValueAxis.java"
AXIR = "source/org/jfree/chart/renderer/xy/AbstractXYItemRenderer.java"
AX = "source/org/jfree/chart/axis/Axis.java"

GOLD_TEXT = '''/**
 * Adds the legend items for an XY plot to a collection.  For each dataset
 * of the plot, the renderer that draws the dataset supplies one item for
 * every series that is visible and visible in the legend.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param items  the collection that the items are added to
 *               (<code>null</code> not permitted).
 */
public static void addSeriesLegendItems(XYPlot plot,
        LegendItemCollection items) {
    int count = plot.getDatasetCount();
    for (int datasetIndex = 0; datasetIndex < count; datasetIndex++) {
        XYDataset dataset = plot.getDataset(datasetIndex);
        if (dataset == null) {
            continue;
        }
        XYItemRenderer renderer = plot.getRenderer(datasetIndex);
        if (renderer == null) {
            renderer = plot.getRenderer(0);
        }
        if (renderer == null) {
            continue;
        }
        int seriesCount = dataset.getSeriesCount();
        for (int i = 0; i < seriesCount; i++) {
            if (renderer.isSeriesVisible(i)
                    && renderer.isSeriesVisibleInLegend(i)) {
                LegendItem item = renderer.getLegendItem(datasetIndex, i);
                if (item != null) {
                    items.add(item);
                }
            }
        }
    }
}'''

HOP1 = '''/**
 * Creates a collection containing the legend items for an XY plot.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 *
 * @return The legend items.
 */
public static LegendItemCollection createLegendItems(XYPlot plot) {
    LegendItemCollection result = new LegendItemCollection();
    ChartFactory.addLegendItems(plot, result);
    return result;
}'''

HOP2 = '''/**
 * Adds the legend items for an XY plot to a collection.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param items  the legend items (<code>null</code> not permitted).
 */
public static void addLegendItems(XYPlot plot,
        LegendItemCollection items) {
    ValueAxis.appendLegendItems(plot, items);
}'''

HOP3 = '''/**
 * Appends the legend items for an XY plot to a collection.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param items  the legend items (<code>null</code> not permitted).
 */
public static void appendLegendItems(XYPlot plot,
        LegendItemCollection items) {
    AbstractXYItemRenderer.addPlotLegendItems(plot, items);
}'''

HOP4 = '''/**
 * Adds the legend items for the datasets in an XY plot to a collection.
 *
 * @param plot  the plot (<code>null</code> not permitted).
 * @param items  the legend items (<code>null</code> not permitted).
 */
public static void addPlotLegendItems(XYPlot plot,
        LegendItemCollection items) {
    Axis.addSeriesLegendItems(plot, items);
}'''

DESIGN = {
 "instance": "Chart-4", "project": "Chart", "bug_id": 4, "seed": 5271,
 "src_root": "source", "test_root": "tests",
 "facade": {"file": XYP, "class": "org.jfree.chart.plot.XYPlot", "method": "getLegendItems", "near_line": 5273},
 "facade_variant": "V2",
 "state_passed": "the receiver this (XYPlot) to hop 1; the private field fixedLegendItems is read only by the facade's guard (the "
                 "original early return); no write-back",
 "reachability_probe": "testGetLegendItems fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "XYPlot.getLegendItems(XYPlot.java:5274) from XYPlotTests.java:905; full suite with the probe: 25 failing "
                       "tests (the trigger directly, the others through LegendTitle when XY charts are drawn)",
 "trigger": {"existing": True, "test_file": "tests/org/jfree/chart/plot/junit/XYPlotTests.java",
             "test_class": "org.jfree.chart.plot.junit.XYPlotTests", "test_method": "testGetLegendItems"},
 "expected_signature": "expected:<2> but was:<1>",
 "gold": {"method": "addSeriesLegendItems", "text": GOLD_TEXT,
          "fault": {"old": "            XYItemRenderer renderer = plot.getRenderer(datasetIndex);\n"
                           "            if (renderer == null) {\n"
                           "                renderer = plot.getRenderer(0);\n"
                           "            }\n",
                    "new": "            XYItemRenderer renderer = plot.getRenderer(datasetIndex);\n"}},
 "chain": {
   "facade_body": "if (this.fixedLegendItems != null) {\n"
                  "            return this.fixedLegendItems;\n"
                  "        }\n"
                  "        return org.jfree.data.general.DatasetUtilities.createLegendItems(this);",
   "lie": "A legend item is first created for every series of every dataset, and the items for the hidden series are then "
          "removed from the collection.",
   "hops": [
     {"file": DSU, "class": "org.jfree.data.general.DatasetUtilities", "method": "createLegendItems",
      "imports": ["org.jfree.chart.ChartFactory", "org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.XYPlot"],
      "text": HOP1},
     {"file": CF, "class": "org.jfree.chart.ChartFactory", "method": "addLegendItems",
      "imports": ["org.jfree.chart.axis.ValueAxis", "org.jfree.chart.plot.XYPlot"], "text": HOP2},
     {"file": VA, "class": "org.jfree.chart.axis.ValueAxis", "method": "appendLegendItems",
      "imports": ["org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.XYPlot",
                  "org.jfree.chart.renderer.xy.AbstractXYItemRenderer"], "text": HOP3},
     {"file": AXIR, "class": "org.jfree.chart.renderer.xy.AbstractXYItemRenderer", "method": "addPlotLegendItems",
      "imports": ["org.jfree.chart.axis.Axis", "org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.XYPlot"],
      "text": HOP4},
     {"file": AX, "class": "org.jfree.chart.axis.Axis", "method": "addSeriesLegendItems",
      "imports": ["org.jfree.chart.LegendItem", "org.jfree.chart.LegendItemCollection", "org.jfree.chart.plot.XYPlot",
                  "org.jfree.chart.renderer.xy.XYItemRenderer", "org.jfree.data.xy.XYDataset"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.chart.plot.XYPlot::render",
              "org.jfree.chart.plot.XYPlot::getRendererForDataset",
              "org.jfree.chart.plot.XYPlot::getDataRange"],
 "ownership_reason": "Only the gold reads the plot's datasets and renderers and creates the legend items; hop 1 creates the empty "
                     "collection and returns it after the chain, and hops 2-4 hand the plot and the collection on unchanged. The "
                     "gold's javadoc promises, for each dataset, the items supplied by the renderer that draws the dataset; the "
                     "plot draws a dataset whose renderer slot is empty with renderer 0, and the variant gold gives that dataset "
                     "no item. No one-line change above the gold can give the gold a renderer for an empty slot, since the gold "
                     "fetches the renderer from the plot itself. The convention is pinned outside the gold: XYPlot.render draws "
                     "with the dataset's renderer, else getRenderer(), else nothing; XYPlot.getRendererForDataset ('if not, the "
                     "method returns renderer(0)') and XYPlot.getDataRange, which ranges each mapped dataset with "
                     "getRendererForDataset; XYPlotTests testGetRendererForDataset (renderer 0 for the dataset whose slot 1 is "
                     "empty) passes; the facade's javadoc says each legend item is generated by the plot's renderer.",
 "ownership_tests": ["org.jfree.chart.plot.junit.XYPlotTests::testGetRendererForDataset"],
 "compensating": {
   "chain": [
     {"file": DSU, "old": "ChartFactory.addLegendItems(plot, result);",
      "new": "ChartFactory.addLegendItems((XYPlot) plot.getRootPlot(), result);",
      "why": "hop 1 gathers the items of the root plot"},
     {"file": AXIR, "old": "Axis.addSeriesLegendItems(plot, items);",
      "new": "if (plot.getRenderer() != null) { Axis.addSeriesLegendItems(plot, items); }",
      "why": "hop 4 asks for items only when the plot has a primary renderer"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts from mr_lib.py preview Chart-4 org/jfree/chart/plot/XYPlot.java 5 with the instance seed 5271, "
               "in draw order, none substituted: data.general.DatasetUtilities (hop 1, 2152 lines), ChartFactory (hop 2, 2263), "
               "axis.ValueAxis (hop 3, 1751), renderer.xy.AbstractXYItemRenderer (hop 4, 1914), axis.Axis (hop 5, gold, 1578; the "
               "smallest host). All five are public top-level classes in which a static method compiles (DatasetUtilities is "
               "final; ChartFactory, ValueAxis, AbstractXYItemRenderer and Axis are abstract, which does not affect a static "
               "method). Anchors from stageB_lib.pick_insertion_anchor with seed 5271 + 100 + i (as mr3_spec.py inserts them): "
               "hop 1 after `findRangeBounds` (line 861, seed 5371), hop 2 after `createPieChart3D` (772, 5372), hop 3 after "
               "`isNegativeArrowVisible` (395, 5373), hop 4 after `removeAnnotations` (704, 5374), hop 5 after "
               "`getAxisLinePaint` (629, 5375). The facade calls hop 1 by its fully-qualified name; each hop imports the next "
               "host where it is in another package. The facade's file XYPlot.java is excluded from the draw.",
}
