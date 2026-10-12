"""Writes the CT-CHART-03 spec (kept as code so every anchor is checked for uniqueness before the build)."""
import json, os
A = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3/construction/agentC"
V3 = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3"
DU = "source/org/jfree/data/general/DatasetUtilities.java"
NA = "source/org/jfree/chart/axis/NumberAxis.java"
AX = "source/org/jfree/chart/renderer/xy/AbstractXYItemRenderer.java"
XP = "source/org/jfree/chart/plot/XYPlot.java"
TF = "tests/org/jfree/chart/axis/junit/NumberAxisTests.java"
ORIG = "        double minimum = Double.POSITIVE_INFINITY;\n        double maximum = Double.NEGATIVE_INFINITY;\n\n        if (includeInterval && dataset instanceof IntervalXYDataset) {\n            // handle special case of IntervalXYDataset\n            IntervalXYDataset ixyd"
BUG = ORIG.replace("double maximum = Double.NEGATIVE_INFINITY;", "double maximum = 0;")
NEUTRAL = "// scan the visible series for the smallest and largest x-values"
trigger_code = '''    /**
     * Checks the auto-range for the domain axis on an XYPlot when all the
     * x-values are below zero and one of the series is not visible.
     */
    public void testXYAutoRange3() {
        XYSeries s1 = new XYSeries("Series 1");
        s1.add(-4.0, 1.0);
        s1.add(-3.0, 2.0);
        s1.add(-2.0, 3.0);
        XYSeries s2 = new XYSeries("Series 2");
        s2.add(-1.0, 4.0);
        XYSeriesCollection dataset = new XYSeriesCollection();
        dataset.addSeries(s1);
        dataset.addSeries(s2);
        JFreeChart chart = ChartFactory.createScatterPlot("Test", "X", "Y",
                dataset, false);
        XYPlot plot = (XYPlot) chart.getPlot();
        plot.getRenderer().setSeriesVisible(1, Boolean.FALSE);
        NumberAxis axis = (NumberAxis) plot.getDomainAxis();
        axis.setAutoRangeIncludesZero(false);
        assertEquals(-1.9, axis.getUpperBound(), EPSILON);
        assertEquals(-4.1, axis.getLowerBound(), EPSILON);
    }
'''
spec = {
 "instance_id": "CT-CHART-03",
 "project": "Chart",
 "stratum": "shallow",
 "family": "wrong accumulator seed: the running maximum of the visible x-values starts at 0 instead of negative infinity, so an all-negative domain is stretched up to zero",
 "work": f"{A}/work/Chart",
 "fresh": f"{A}/fresh/Chart",
 "src_root": "source",
 "classes_dir": "build",
 "prod_files": [DU, NA],
 "test_files": [TF],
 "gold": {"file": DU, "class": "org.jfree.data.general.DatasetUtilities", "method": "iterateToFindDomainBounds",
          "orig": ORIG, "bug": BUG,
          "orig_line": "double maximum = Double.NEGATIVE_INFINITY;", "bug_line": "double maximum = 0;"},
 "decoys": [
  {"file": NA, "class": "org.jfree.chart.axis.NumberAxis", "method": "autoAdjustRange"},
  {"file": NA, "class": "org.jfree.chart.axis.NumberAxis", "method": "getAutoRangeIncludesZero"}],
 "entry": "org.jfree.chart.axis.NumberAxis#setAutoRangeIncludesZero -> NumberAxis#autoAdjustRange -> XYPlot#getDataRange -> AbstractXYItemRenderer#findDomainBounds(XYDataset, boolean) -> DatasetUtilities#findDomainBounds(XYDataset, List, boolean) -> DatasetUtilities#iterateToFindDomainBounds",
 "comment_anchor": {"file": DU,
   "anchor_fault": "        double minimum = Double.POSITIVE_INFINITY;\n        double maximum = 0;\n",
   "anchor_correct": ORIG, "where": "before"},
 "levels": {
  "C0": {"cue": "neutral", "comment": NEUTRAL, "renames": []},
  "CG1": {"cue": "gold-rationalising", "comment": "// the first visible x-value replaces both starting bounds",
          "renames": [{"scope": "method", "file": DU, "method": "iterateToFindDomainBounds", "map": {"minimum": "minSoFar", "maximum": "maxSoFar"}}]},
  "CG2": {"cue": "gold-rationalising", "comment": "// placeholder bounds only, overwritten when the first item is read",
          "renames": [{"scope": "method", "file": DU, "method": "iterateToFindDomainBounds", "map": {"minimum": "pendingMin", "maximum": "pendingMax"}}]},
  "CD1": {"cue": "decoy-incriminating", "comment": NEUTRAL,
          "renames": [{"scope": "fields", "file": NA, "class": "org/jfree/chart/axis/NumberAxis",
                       "map": {"autoRangeIncludesZero": "autoRangeStickyZero", "autoRangeStickyZero": "autoRangeIncludesZero"}}]},
  "CD2": {"cue": "decoy-incriminating", "comment": NEUTRAL,
          "renames": [{"scope": "fields", "file": NA, "class": "org/jfree/chart/axis/NumberAxis",
                       "map": {"autoRangeIncludesZero": "autoRangeExcludesZero"}}]}},
 "trigger": {"test_file": TF, "test_class": "org.jfree.chart.axis.junit.NumberAxisTests", "test_method": "testXYAutoRange3",
             "imports": [], "code": trigger_code},
 "expected_signature": "expected:<-1.9> but was:<0.0>",
 "assertion_class_regex": "AssertionFailedError",
 "compensating": [
  {"file": NA, "old": "                upper = Math.max(upper, 0.0);\n", "new": "",
   "why": "decoy autoAdjustRange: drop the include-zero widening of the upper bound"},
  {"file": NA, "old": "            if (getAutoRangeIncludesZero()) {\n                lower = Math.min(lower, 0.0);",
   "new": "            if (!getAutoRangeIncludesZero()) {\n                lower = Math.min(lower, 0.0);",
   "why": "decoy autoAdjustRange: negate the include-zero test"},
  {"file": NA, "old": "                        upper = Math.min(0.0, upper + getUpperMargin() * range);",
   "new": "                        upper = upper + getUpperMargin() * range;",
   "why": "decoy autoAdjustRange: remove the sticky-zero clamp on the upper margin"},
  {"file": NA, "old": "        return this.autoRangeIncludesZero;", "new": "        return false;",
   "why": "decoy getAutoRangeIncludesZero: always report false"},
  {"file": AX, "old": "            return DatasetUtilities.findDomainBounds(dataset,\n                    visibleSeriesKeys, includeInterval);",
   "new": "            return DatasetUtilities.findDomainBounds(dataset,\n                    includeInterval);",
   "why": "caller-side (AbstractXYItemRenderer.findDomainBounds): bypass the visible-series bounds"},
  {"file": XP, "old": "                        result = Range.combine(result, r.findDomainBounds(d));",
   "new": "                        result = Range.combine(result, DatasetUtilities.findDomainBounds(d, false));",
   "why": "caller-side (XYPlot.getDataRange): take the dataset bounds instead of the renderer bounds"},
  {"file": DU, "old": "            result = iterateToFindDomainBounds(dataset, visibleSeriesKeys,\n                    includeInterval);",
   "new": "            result = iterateDomainBounds(dataset,\n                    includeInterval);",
   "why": "caller-side (DatasetUtilities.findDomainBounds 3-arg): use the all-series iteration"}],
 "marker_methods": [
  {"role": "gold", "file": DU, "method": "iterateToFindDomainBounds"},
  {"role": "decoy", "file": NA, "method": "autoAdjustRange"},
  {"role": "decoy_getter", "file": NA, "method": "getAutoRangeIncludesZero"}],
 "notes": "Shallow stratum: the faulty line (double maximum = 0;) is line 1333 in every shipped level, 13 lines below the iterateToFindDomainBounds signature at 1320 (12 in the pristine file; the shared comment line sits just above it). Gold file DatasetUtilities.java has 2,180 lines (>= 2,000, chosen per the spare-instance brief to keep clear of CT-CHART-02's AbstractRenderer/PiePlot); the key DatasetUtilities::iterateToFindDomainBounds is unique and the method is 58 lines. Ownership: one direct production caller (DatasetUtilities.findDomainBounds(XYDataset, List, boolean), reached from AbstractXYItemRenderer.findDomainBounds for every XY renderer under the default visible-series-only setting); the gold's own javadoc states the violated contract (the range of x-values of the items in the visible series). Decoy: NumberAxis.autoAdjustRange's sticky-zero clamp Math.min(0.0, upper + margin) is where the observed 0.0 is produced from the stretched data range, and its include-zero widening and getAutoRangeIncludesZero are the natural suspects once the test has called setAutoRangeIncludesZero(false). CD1 swaps the private flags autoRangeIncludesZero/autoRangeStickyZero so the two getters appear to read each other's flag; CD2 renames autoRangeIncludesZero to autoRangeExcludesZero so the getter and setter appear inverted. The truth stays visible: setter and getter share one field, the field javadoc keeps the include-zero description, and implanting the implied defect on the correct code breaks 10+ existing tests (NumberAxisTests.testAutoRange2, testXYAutoRange1, ...; CD1 also changes the trigger value to 0.2), see construction/agentC/screen/cue_refute_CT-CHART-03.json. CG cues assert the false local fact that the first visible x-value replaces the starting bounds (Math.max(0, x) keeps 0 for x < 0); they never touch the javadoc. The hidden second series (x = -1) blocks caller-side bypasses of the visible-series bounds (G9 caller-side edits give -0.85)."}
# uniqueness checks on the pristine checkout
W = spec["work"]
def cnt(rel, s): return open(os.path.join(W, rel)).read().count(s)
assert cnt(DU, ORIG) == 1, cnt(DU, ORIG)
for c in spec["compensating"]: assert cnt(c["file"], c["old"]) == 1, (c["why"], cnt(c["file"], c["old"]))
out = f"{V3}/instances/CT-CHART-03/spec.json"; json.dump(spec, open(out, "w"), indent=1); print("wrote", out)
