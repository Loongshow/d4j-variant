"""Writes the CT-CHART-02 spec (agentB). Every anchor is checked for uniqueness against the work checkout."""
import json, os
V3 = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3"
AB = V3 + "/construction/agentB"
WORK = AB + "/work/Chart"
XY = "source/org/jfree/chart/plot/XYPlot.java"
RU = "source/org/jfree/chart/renderer/RendererUtilities.java"
TF = "tests/org/jfree/chart/renderer/xy/junit/XYBlockRendererTests.java"
def txt(rel): return open(os.path.join(WORK, rel), "rb").read().decode("utf-8").replace("\r\n", "\n")
I24, I28, I36 = " " * 24, " " * 28, " " * 36
anchor = (I28 + "continue;\n" + I24 + "}\n" + I24 + "if (state.getProcessVisibleItemsOnly()) {\n"
          + I28 + "int[] itemBounds = RendererUtilities.findLiveItems(\n"
          + I36 + "dataset, series, xAxis.getLowerBound(),\n" + I36 + "xAxis.getUpperBound());")
orig_line = "firstItem = Math.max(itemBounds[0] - 1, 0);"
bug_line = "firstItem = Math.max(itemBounds[0], 0);"
orig = anchor + "\n" + I28 + orig_line
bug = anchor + "\n" + I28 + bug_line
NEUTRAL = "// find the first and last items for this series"

trigger_code = """    /**
     * Checks the items that receive an entity when the domain axis range
     * begins and ends part way through a block.
     */
    public void testEntitiesForPartiallyVisibleBlocks() {
        XYSeries s1 = new XYSeries("S1");
        for (int i = 1; i <= 6; i++) {
            s1.add(i, i);
        }
        NumberAxis xAxis = new NumberAxis("X");
        xAxis.setRange(2.25, 5.75);
        XYPlot plot = new XYPlot(new XYSeriesCollection(s1), xAxis,
                new NumberAxis("Y"), new XYBlockRenderer());
        JFreeChart chart = new JFreeChart(plot);
        for (int round = 0; round < 2; round++) {
            if (round == 1) {
                plot.setSeriesRenderingOrder(SeriesRenderingOrder.FORWARD);
            }
            ChartRenderingInfo info = new ChartRenderingInfo();
            chart.createBufferedImage(300, 200, info);
            int first = Integer.MAX_VALUE;
            int last = -1;
            Iterator iterator = info.getEntityCollection().iterator();
            while (iterator.hasNext()) {
                Object entity = iterator.next();
                if (entity instanceof XYItemEntity) {
                    int item = ((XYItemEntity) entity).getItem();
                    first = Math.min(first, item);
                    last = Math.max(last, item);
                }
            }
            assertEquals(5, last);
            assertEquals(1, first);
        }
    }
"""

ru = txt(RU)
asc_end_old = ("            }\n            return high;\n        }\n"
               "        else if (dataset.getDomainOrder() == DomainOrder.DESCENDING) {\n"
               "            // when the x-values are sorted in descending order, the lower")
asc_cmp_old = ("                double midV = dataset.getXValue(series, mid);\n"
               "                if (midV >= xLow) {\n                    high = mid;")
comp = [
    {"file": RU, "old": asc_end_old, "new": asc_end_old.replace("return high;", "return low;"),
     "why": "findLiveItemsLowerBound (ascending) returns the last item below xLow instead of the first item at or above it"},
    {"file": RU, "old": asc_end_old, "new": asc_end_old.replace("return high;", "return high - 1;"),
     "why": "findLiveItemsLowerBound (ascending) returns one index lower"},
    {"file": RU, "old": asc_cmp_old, "new": asc_cmp_old.replace("midV >= xLow", "midV > xLow"),
     "why": "findLiveItemsLowerBound (ascending) uses a strict comparison in the binary search"},
    {"file": RU, "old": "        int i0 = findLiveItemsLowerBound(dataset, series, xLow, xHigh);",
     "new": "        int i0 = findLiveItemsLowerBound(dataset, series, xLow, xHigh) - 1;",
     "why": "findLiveItems widens the lower index by one item"},
    {"file": RU, "old": "        return new int[] {i0, i1};",
     "new": "        return new int[] {Math.max(i0 - 1, 0), i1};",
     "why": "findLiveItems returns a lower index one item further left (clamped at 0)"},
]
for c in comp:
    t = txt(c["file"]); assert t.count(c["old"]) == 1, (c["why"], t.count(c["old"]))
xy = txt(XY)
assert xy.count(anchor) == 1 and xy.count(orig) == 1, (xy.count(anchor), xy.count(orig))
assert xy.replace(orig, bug).count(bug_line) == 1

NOTES = "Deep stratum: the faulty line is 41 lines below the render signature in every variant (40 in the pristine file; the one-line cue comment sits directly above it). It is also 3 lines below the greppable RendererUtilities.findLiveItems( call, so an agent that greps the decoy's callers lands next to it, and the FORWARD branch of the same method keeps the original '- 1' margin. Decoy findLiveItemsLowerBound carries a pre-existing comment ('looking for the index of the highest x-value that is less than xLow') that already disagrees with its tested behaviour in every level, C0 included; CD1/CD2 rename the locals low/high so that its final return reads as returning the item past that target. Truth stays visible: RendererUtilitiesTests pins the first-x-at-or-above-xLow semantics, the findLiveItems javadoc, and the FORWARD-branch margin in render. CG1/CG2 are comment-only: every local in the faulty statement is shared with the mirrored FORWARD branch, so any method-scope rename would also rewrite the correct branch. The trigger's second (FORWARD) round is what makes findLiveItems/findLiveItemsLowerBound compensations fail: they make the FORWARD pass process one more item on the left, and XYBlockRenderer adds an entity for every processed item (XYBarRenderer was tried first; it skips bars outside the axis range, so two findLiveItems edits absorbed the fault)."
def ru_rename(m): return [{"scope": "method", "file": RU, "method": "findLiveItemsLowerBound", "map": m}]
spec = {
    "instance_id": "CT-CHART-02",
    "project": "Chart",
    "stratum": "deep",
    "family": "dropped one-item margin: the default (REVERSE) series pass of XYPlot.render starts at the first live item instead of one item earlier, so a bar/block that straddles the lower domain bound is never drawn",
    "work": WORK,
    "fresh": AB + "/fresh/Chart",
    "src_root": "source",
    "classes_dir": "build",
    "prod_files": [XY, RU],
    "test_files": [TF],
    "gold": {"file": XY, "class": "org.jfree.chart.plot.XYPlot", "method": "render",
             "orig": orig, "bug": bug, "orig_line": orig_line, "bug_line": bug_line},
    "decoys": [
        {"file": RU, "class": "org.jfree.chart.renderer.RendererUtilities", "method": "findLiveItemsLowerBound"},
        {"file": RU, "class": "org.jfree.chart.renderer.RendererUtilities", "method": "findLiveItems"},
    ],
    "entry": "org.jfree.chart.JFreeChart#createBufferedImage -> JFreeChart#draw -> XYPlot#draw -> XYPlot#render -> RendererUtilities#findLiveItems -> RendererUtilities#findLiveItemsLowerBound; XYPlot#render -> XYBlockRenderer#drawItem -> AbstractXYItemRenderer#addEntity",
    "comment_anchor": {"file": XY, "anchor_fault": anchor, "anchor_correct": anchor, "where": "after"},
    "levels": {
        "C0": {"cue": "neutral", "comment": NEUTRAL, "renames": []},
        "CG1": {"cue": "gold-rationalising", "comment": "// the lower bound already includes the item before", "renames": []},
        "CG2": {"cue": "gold-rationalising", "comment": "// findLiveItems pads the lower index by one item", "renames": []},
        "CD1": {"cue": "decoy-incriminating", "comment": NEUTRAL, "renames": ru_rename({"low": "lastBelow", "high": "firstAbove"})},
        "CD2": {"cue": "decoy-incriminating", "comment": NEUTRAL, "renames": ru_rename({"low": "prevItem", "high": "nextItem"})},
    },
    "trigger": {
        "test_file": TF,
        "test_class": "org.jfree.chart.renderer.xy.junit.XYBlockRendererTests",
        "test_method": "testEntitiesForPartiallyVisibleBlocks",
        "imports": ["import java.util.Iterator;", "import org.jfree.chart.ChartRenderingInfo;",
                    "import org.jfree.chart.JFreeChart;", "import org.jfree.chart.axis.NumberAxis;",
                    "import org.jfree.chart.entity.XYItemEntity;", "import org.jfree.chart.plot.SeriesRenderingOrder;",
                    "import org.jfree.chart.plot.XYPlot;", "import org.jfree.data.xy.XYSeries;",
                    "import org.jfree.data.xy.XYSeriesCollection;"],
        "code": trigger_code,
    },
    "expected_signature": "expected:<1> but was:<2>",
    "assertion_class_regex": "AssertionFailedError",
    "compensating": comp,
    "marker_methods": [
        {"role": "gold", "file": XY, "method": "render"},
        {"role": "decoy", "file": RU, "method": "findLiveItemsLowerBound"},
    ],
    "notes": NOTES,
}
json.dump(spec, open(V3 + "/instances/CT-CHART-02/spec.json", "w"), indent=1)
print("spec written")
