"""OCFLB-CHART-02: count x offset (per-boundary gap accumulated once instead of once per preceding category). Seed CHART-AXIS-TREATMENT-01.
Facade CategoryAxis.getCategoryStart -> H1 RectangleEdge.locate -> H2 Range.pad (definer) -> H3 RectangleAnchor.place (adapter)
-> H4 RectangleInsets.inset -> H5 AxisSpace.cell.
H2 returns the padding range of a cell: lower bound = accumulated gap before the cell (index * gap), upper bound = accumulated gap
before the next cell, so the length of the range is one boundary's gap. H3 adds the lower bound (the accumulated gap) to the offset.
Usage: build_chart02.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Chart"; SEED = "CHART-AXIS-TREATMENT-01"
F = {"facade": "source/org/jfree/chart/axis/CategoryAxis.java", "H1": "source/org/jfree/chart/util/RectangleEdge.java", "H2": "source/org/jfree/data/Range.java",
     "H3": "source/org/jfree/chart/util/RectangleAnchor.java", "H4": "source/org/jfree/chart/util/RectangleInsets.java", "H5": "source/org/jfree/chart/axis/AxisSpace.java"}
T_TRIG = "tests/org/jfree/chart/axis/junit/CategoryAxisTests.java"; T_PIN = "tests/org/jfree/data/junit/RangeTests.java"
H1 = '''    /**
     * Returns the coordinate of one cell of a run of cells laid out along
     * the specified edge of a rectangle.  The run starts after a leading
     * space, the cells share a fraction of the length, and each boundary
     * between two cells carries a gap.
     *
     * @param area  the rectangle.
     * @param edge  the edge.
     * @param index  the index of the cell.
     * @param count  the number of cells.
     * @param lead  the space before the run (as a percentage of the length).
     * @param trail  the space after the run (as a percentage of the length).
     * @param spread  the space within the run (as a percentage of the
     *                length).
     *
     * @return The coordinate.
     */
    public static double locate(Rectangle2D area, RectangleEdge edge,
                                int index, int count, double lead,
                                double trail, double spread) {
        double start = 0.0;
        double length = 0.0;
        if ((edge == RectangleEdge.TOP) || (edge == RectangleEdge.BOTTOM)) {
            start = area.getX();
            length = area.getWidth();
        }
        else if ((edge == RectangleEdge.LEFT)
                || (edge == RectangleEdge.RIGHT)) {
            start = area.getMinY();
            length = area.getHeight();
        }
        double fraction = 1.0 - lead - trail;
        if (count > 1) {
            fraction = fraction - spread;
        }
        Range padding = Range.pad(length, spread, index, count);
        return RectangleAnchor.place(start, length, lead, fraction, index,
                count, padding);
    }'''
H2_OK = "        return new Range(index * gap, (index + 1) * gap);"
H2_BUG = "        return new Range(gap, (index + 1) * gap);"
H2 = '''    /**
     * Returns the padding of one cell of a run of cells: the space within
     * the run is shared equally by the boundaries between the cells, and the
     * padding before a cell accumulates one gap per boundary that precedes
     * the cell.  The lower bound of the returned range is the accumulated
     * padding before the cell with the given index (the index times the
     * gap), and the upper bound is the accumulated padding before the next
     * cell, so the length of the range is the gap at one boundary.
     *
     * @param length  the available length.
     * @param spread  the space within the run (as a percentage of the
     *                length).
     * @param index  the index of the cell.
     * @param count  the number of cells.
     *
     * @return The padding range.
     */
    public static Range pad(double length, double spread, int index,
                            int count) {
        double gap = 0.0;
        if (count > 1) {
            gap = length * spread / (count - 1);
        }
%s
    }'''
H3_OK = "        double gaps = padding.getLowerBound();"
H3_BUG = "        double gaps = padding.getLength();"
H3 = '''    /**
     * Resolves the placement of one cell of a run: the accumulated padding
     * that precedes the cell (the lower bound of its padding range) and the
     * size of one cell (the shared fraction of the length divided by the
     * number of cells), and hands them on together with the leading space.
     *
     * @param start  the coordinate at which the available length starts.
     * @param length  the available length.
     * @param lead  the space before the run (as a percentage of the length).
     * @param fraction  the fraction of the length shared by the cells.
     * @param index  the index of the cell.
     * @param count  the number of cells.
     * @param padding  the padding range of the cell.
     *
     * @return The coordinate.
     */
    public static double place(double start, double length, double lead,
                               double fraction, int index, int count,
                               Range padding) {
%s
        double size = length * fraction / count;
        return RectangleInsets.inset(start, length, lead, index, size, gaps);
    }'''
H4 = '''    /**
     * Applies the leading inset to the start of the available length and
     * resolves the coordinate of a cell relative to the inset origin.
     *
     * @param start  the coordinate at which the available length starts.
     * @param length  the available length.
     * @param lead  the leading inset (as a percentage of the length).
     * @param index  the index of the cell.
     * @param size  the size of one cell.
     * @param gaps  the accumulated padding before the cell.
     *
     * @return The coordinate.
     */
    public static double inset(double start, double length, double lead,
                               int index, double size, double gaps) {
        double inset = length * lead;
        double origin = start + inset;
        return AxisSpace.cell(origin, index, size, gaps);
    }'''
H5 = '''    /**
     * Returns the coordinate of a cell: the origin of the run plus the cells
     * that precede it plus the accumulated padding before it.
     *
     * @param origin  the coordinate at which the run starts.
     * @param index  the index of the cell.
     * @param size  the size of one cell.
     * @param gaps  the accumulated padding before the cell.
     *
     * @return The coordinate.
     */
    public static double cell(double origin, int index, double size,
                              double gaps) {
        double offset = index * size + gaps;
        double coordinate = origin + offset;
        return coordinate;
    }'''
PIN = '''    /**
     * The padding before a cell accumulates one gap per preceding boundary:
     * the lower bound of the padding range is the index times the gap and
     * the range extends by one further gap.
     */
    public void testPad() {
        Range p0 = Range.pad(400.0, 0.20, 0, 4);
        assertEquals(0.0, p0.getLowerBound(), 0.0000001);
        assertEquals(26.666666666666668, p0.getUpperBound(), 0.0000001);
        Range p2 = Range.pad(400.0, 0.20, 2, 4);
        assertEquals(53.333333333333336, p2.getLowerBound(), 0.0000001);
        assertEquals(80.0, p2.getUpperBound(), 0.0000001);
        Range p3 = Range.pad(300.0, 0.10, 3, 4);
        assertEquals(30.0, p3.getLowerBound(), 0.0000001);
        assertEquals(40.0, p3.getUpperBound(), 0.0000001);
        Range p1 = Range.pad(400.0, 0.20, 0, 1);
        assertEquals(0.0, p1.getLowerBound(), 0.0000001);
        assertEquals(0.0, p1.getUpperBound(), 0.0000001);
    }'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "locate", H1); B.add_import(work, F["H1"], "import org.jfree.data.Range;")
    B.replace_method(work, F["H2"], "pad", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_once(work, F["H2"], "import java.io.Serializable;\n\nimport org.jfree.chart.util.RectangleAnchor;\n", "import java.io.Serializable;\n")
    B.replace_method(work, F["H3"], "place", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK)); B.add_import(work, F["H3"], "import org.jfree.data.Range;")
    B.replace_method(work, F["H4"], "inset", H4)
    B.replace_method(work, F["H5"], "cell", H5)
    B.replace_once(work, F["H5"], "import org.jfree.chart.util.RectangleEdge;\nimport org.jfree.data.Range;\n", "import org.jfree.chart.util.RectangleEdge;\n")
    B.insert_before_class_end(work, T_PIN, PIN)
spec = {"pair_id": "OCFLB-CHART-02", "project": P, "bug": "02", "base_version": "Chart-1f", "seed_variant": SEED,
  "family": "count x offset (per-boundary gap accumulated once instead of once per preceding category)",
  "convention": "pad returns the padding range of a cell: its lower bound is the accumulated gap before the cell (index * gap, one gap per preceding boundary) and its upper bound is the accumulated gap before the next cell, so its length is the gap at one boundary",
  "effect": "the start of every category is displaced by exactly one gap instead of by one gap per preceding category (category 0 starts at 56.67 instead of 30.0)",
  "equivalence_note": "in arm A the lower bound of the padding range is gap instead of index * gap and place adds the lower bound; in arm B the lower bound is index * gap and place adds the length of the range, which is (index + 1) * gap - index * gap = gap; both arms therefore compute origin + index * size + gap for every index >= 0, and the two mistakes cancel exactly (lower bound gap, length (index + 1) * gap - gap = index * gap)",
  "adapter_fault_note": "place adds the length of the padding range (the gap at one boundary) instead of its lower bound (the accumulated gap before the cell)",
  "trigger": "org.jfree.chart.axis.junit.CategoryAxisTests::test2064767", "expected_signature": "expected:<30.0> but was:<56.66666666666667>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.jfree.data.junit.RangeTests::testPad", "second_caller": None,
  "chain": {"facade": {"class": "org.jfree.chart.axis.CategoryAxis", "method": "getCategoryStart", "file": F["facade"]},
            "H1": {"class": "org.jfree.chart.util.RectangleEdge", "method": "locate", "file": F["H1"]}, "H2": {"class": "org.jfree.data.Range", "method": "pad", "file": F["H2"]},
            "H3": {"class": "org.jfree.chart.util.RectangleAnchor", "method": "place", "file": F["H3"]}, "H4": {"class": "org.jfree.chart.util.RectangleInsets", "method": "inset", "file": F["H4"]},
            "H5": {"class": "org.jfree.chart.axis.AxisSpace", "method": "cell", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "OCFLB-CHART-02-DEFINER", "gold_role": "H2", "gold": {"class": "org.jfree.data.Range", "method": "pad", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_BUG}, "declared_collateral": ["org.jfree.data.junit.RangeTests::testPad"]},
           "ADAPTER_FAULT": {"variant_id": "OCFLB-CHART-02-ADAPTER", "gold_role": "H3", "gold": {"class": "org.jfree.chart.util.RectangleAnchor", "method": "place", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_BUG}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Chart/bug-02"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
