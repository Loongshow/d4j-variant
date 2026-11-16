"""LB-CHART-01 (Level B reference): sign / direction of an exploded pie section. Converted from OCFLB-CHART-01 (seed CHART-PIE-TREATMENT-03).
Facade PiePlot.getArcBounds -> H1 CompassPlot.ring -> H2 PlotUtilities.offset (definer) -> H3 Plot.nudge (adapter) -> H4 StandardDialScale.rim -> H5 ShapeUtilities.shift.
Convention decided externally: the offset points from the exploded ring back to the unexploded ring (point1 - point2), as the production
second caller RingPlot.collapse (adds the offset to move a section back toward the centre) and its test rely on.
Usage: build_lb_chart01.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Chart"; SEED = "CHART-PIE-TREATMENT-03"
F = {"facade": "source/org/jfree/chart/plot/PiePlot.java", "H1": "source/org/jfree/chart/plot/CompassPlot.java", "H2": "source/org/jfree/chart/plot/PlotUtilities.java",
     "H3": "source/org/jfree/chart/plot/Plot.java", "H4": "source/org/jfree/chart/plot/dial/StandardDialScale.java", "H5": "source/org/jfree/chart/util/ShapeUtilities.java",
     "EXT": "source/org/jfree/chart/plot/RingPlot.java"}
T_TRIG = "tests/org/jfree/chart/plot/junit/PiePlotTests.java"; T_PIN = "tests/org/jfree/chart/plot/junit/PlotUtilitiesTests.java"; T_PKG = "tests/org/jfree/chart/plot/junit/PlotPackageTests.java"; T_EXT = "tests/org/jfree/chart/plot/junit/RingPlotTests.java"
H1 = '''    /**
     * Locates the mid-angle point of a section on the unexploded ring and on
     * the exploded ring, and resolves the bounds of the exploded section.
     *
     * @param unexploded  the area of the unexploded ring.
     * @param exploded  the area of the exploded ring.
     * @param angle  the start angle.
     * @param extent  the extent of the section.
     * @param explodePercent  the explode percentage.
     *
     * @return The bounds of the exploded section.
     */
    public static Rectangle2D ring(Rectangle2D unexploded, Rectangle2D exploded,
            double angle, double extent, double explodePercent) {
        Arc2D arc1 = new Arc2D.Double(unexploded, angle, extent / 2,
                Arc2D.OPEN);
        Point2D point1 = arc1.getEndPoint();
        Arc2D arc2 = new Arc2D.Double(exploded, angle, extent / 2,
                Arc2D.OPEN);
        Point2D point2 = arc2.getEndPoint();
        Point2D offset = PlotUtilities.offset(point1, point2);
        return Plot.nudge(unexploded, explodePercent, offset);
    }'''
H2_OK = "        double dx = point1.getX() - point2.getX();\n        double dy = point1.getY() - point2.getY();"
H2_BUG = "        double dx = point2.getX() - point1.getX();\n        double dy = point2.getY() - point1.getY();"
H2 = '''    /**
     * Computes the offset between the mid-angle point of a section on the
     * unexploded ring and the corresponding point on the exploded ring.
     *
     * @param point1  the point on the unexploded ring.
     * @param point2  the corresponding point on the exploded ring.
     *
     * @return The offset.
     */
    public static Point2D offset(Point2D point1, Point2D point2) {
%s
        return new Point2D.Double(dx, dy);
    }'''
H3_OK = "        double x = unexploded.getX() - offset.getX() * explodePercent;\n        double y = unexploded.getY() - offset.getY() * explodePercent;"
H3_BUG = "        double x = unexploded.getX() + offset.getX() * explodePercent;\n        double y = unexploded.getY() + offset.getY() * explodePercent;"
H3 = '''    /**
     * Displaces the bounds of a section by its offset scaled by the explode
     * percentage.
     *
     * @param unexploded  the bounds of the unexploded section.
     * @param explodePercent  the explode percentage.
     * @param offset  the offset of the section.
     *
     * @return The bounds of the exploded section.
     */
    public static Rectangle2D nudge(Rectangle2D unexploded, double explodePercent,
            Point2D offset) {
%s
        return StandardDialScale.rim(unexploded, x, y);
    }'''
H4 = '''    /**
     * Re-anchors an area at the given point and resolves the re-anchored
     * area.
     *
     * @param area  the area.
     * @param x  the x-coordinate of the new anchor.
     * @param y  the y-coordinate of the new anchor.
     *
     * @return The re-anchored area.
     */
    public static Rectangle2D rim(Rectangle2D area, double x, double y) {
        double deltaX = x - area.getX();
        double deltaY = y - area.getY();
        return ShapeUtilities.shift(area, deltaX, deltaY);
    }'''
H5 = '''    /**
     * Shifts an area by a displacement, preserving its size.
     *
     * @param area  the area.
     * @param deltaX  the x-displacement.
     * @param deltaY  the y-displacement.
     *
     * @return The shifted area.
     */
    public static Rectangle2D shift(Rectangle2D area, double deltaX,
            double deltaY) {
        double x = area.getX() + deltaX;
        double y = area.getY() + deltaY;
        return new Rectangle2D.Double(x, y, area.getWidth(), area.getHeight());
    }'''
EXT = '''    /**
     * Moves an exploded section back toward the centre of the plot by a
     * fraction of its offset.
     *
     * @param exploded  the bounds of the exploded section.
     * @param point1  the mid-angle point of the section on the unexploded ring.
     * @param point2  the corresponding point on the exploded ring.
     * @param percent  the fraction of the offset to move back by.
     *
     * @return The bounds of the moved section.
     */
    public static Rectangle2D collapse(Rectangle2D exploded, Point2D point1,
            Point2D point2, double percent) {
        Point2D offset = PlotUtilities.offset(point1, point2);
        double x = exploded.getX() + offset.getX() * percent;
        double y = exploded.getY() + offset.getY() * percent;
        return new Rectangle2D.Double(x, y, exploded.getWidth(),
                exploded.getHeight());
    }'''
EXT_TEST = '''    /**
     * Moving an exploded section back by its whole offset returns it to the
     * unexploded position.
     */
    public void testCollapse() {
        Rectangle2D exploded = new Rectangle2D.Double(50.0, 200.0, 20.0, 20.0);
        Rectangle2D back = RingPlot.collapse(exploded,
                new Point2D.Double(100.0, 200.0), new Point2D.Double(50.0, 200.0),
                1.0);
        assertEquals(100.0, back.getX(), 0.0000001);
        assertEquals(200.0, back.getY(), 0.0000001);
        assertEquals(20.0, back.getWidth(), 0.0000001);
        Rectangle2D half = RingPlot.collapse(exploded,
                new Point2D.Double(100.0, 200.0), new Point2D.Double(50.0, 200.0),
                0.5);
        assertEquals(75.0, half.getX(), 0.0000001);
    }'''
PIN = '''/* ===========================================================
 * JFreeChart : a free chart library for the Java(tm) platform
 * ===========================================================
 *
 * Tests for the {@link org.jfree.chart.plot.PlotUtilities} class.
 */

package org.jfree.chart.plot.junit;

import java.awt.geom.Point2D;

import junit.framework.Test;
import junit.framework.TestCase;
import junit.framework.TestSuite;

import org.jfree.chart.plot.PlotUtilities;

/**
 * Tests for the {@link PlotUtilities} class.
 */
public class PlotUtilitiesTests extends TestCase {

    /**
     * Returns the tests as a test suite.
     *
     * @return The test suite.
     */
    public static Test suite() {
        return new TestSuite(PlotUtilitiesTests.class);
    }

    /**
     * Constructs a new set of tests.
     *
     * @param name  the name of the tests.
     */
    public PlotUtilitiesTests(String name) {
        super(name);
    }

    /**
     * Some checks for the offset of a section.
     */
    public void testOffset() {
        Point2D offset = PlotUtilities.offset(new Point2D.Double(100.0, 200.0),
                new Point2D.Double(50.0, 200.0));
        assertEquals(50.0, offset.getX(), 0.0000001);
        assertEquals(0.0, offset.getY(), 0.0000001);
        offset = PlotUtilities.offset(new Point2D.Double(10.0, 20.0),
                new Point2D.Double(13.0, 24.0));
        assertEquals(-3.0, offset.getX(), 0.0000001);
        assertEquals(-4.0, offset.getY(), 0.0000001);
    }

}
'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "ring", H1)
    B.replace_method(work, F["H2"], "drift", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))
    B.replace_method(work, F["H3"], "nudge", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK)); B.add_import(work, F["H3"], "import org.jfree.chart.plot.dial.StandardDialScale;")
    B.replace_method(work, F["H4"], "rim", H4); B.add_import(work, F["H4"], "import org.jfree.chart.util.ShapeUtilities;")
    B.replace_method(work, F["H5"], "shift", H5)
    B.insert_before_class_end(work, F["EXT"], EXT); B.add_import(work, F["EXT"], "import java.awt.geom.Point2D;"); B.add_import(work, F["EXT"], "import java.awt.geom.Rectangle2D;")
    B.new_file(work, T_PIN, PIN)
    B.replace_once(work, T_PKG, "        suite.addTestSuite(PiePlotTests.class);\n", "        suite.addTestSuite(PiePlotTests.class);\n        suite.addTestSuite(PlotUtilitiesTests.class);\n")
    B.insert_before_class_end(work, T_EXT, EXT_TEST); B.add_import(work, T_EXT, "import java.awt.geom.Point2D;"); B.add_import(work, T_EXT, "import java.awt.geom.Rectangle2D;")
spec = {"pair_id": "LB-CHART-01", "project": P, "bug": "01", "base_version": "Chart-1f", "seed_variant": SEED, "level": "B", "converted_from": "OCFLB-CHART-01",
  "family": "sign / direction (offset direction of an exploded pie section)",
  "convention": "offset = point1 - point2 (from the exploded ring back to the unexploded ring); decided by RingPlot.collapse, which adds the scaled offset to move a section back toward the centre",
  "effect": "the exploded section is displaced toward the pie centre instead of away from it (x 112.5 instead of 87.5)",
  "equivalence_note": "reversing the operand order in the definer (arm A) and using addition instead of subtraction in the adapter (arm B) produce the same displaced rectangle for every input",
  "adapter_fault_note": "nudge adds the scaled offset to the anchor instead of subtracting it (the offset points inward)",
  "trigger": "org.jfree.chart.plot.junit.PiePlotTests::test2986548", "expected_signature": "expected:<87.5> but was:<112.5>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.jfree.chart.plot.junit.PlotUtilitiesTests::testOffset", "second_caller": "org.jfree.chart.plot.RingPlot#collapse (production; adds the offset to move a section back toward the centre)",
  "external_evidence_tests": ["org.jfree.chart.plot.junit.RingPlotTests::testCollapse"],
  "chain": {"facade": {"class": "org.jfree.chart.plot.PiePlot", "method": "getArcBounds", "file": F["facade"]},
            "H1": {"class": "org.jfree.chart.plot.CompassPlot", "method": "ring", "file": F["H1"]}, "H2": {"class": "org.jfree.chart.plot.PlotUtilities", "method": "offset", "file": F["H2"]},
            "H3": {"class": "org.jfree.chart.plot.Plot", "method": "nudge", "file": F["H3"]}, "H4": {"class": "org.jfree.chart.plot.dial.StandardDialScale", "method": "rim", "file": F["H4"]},
            "H5": {"class": "org.jfree.chart.util.ShapeUtilities", "method": "shift", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5", "EXT")], "test_files": [T_TRIG, T_PIN, T_PKG, T_EXT],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5", "EXT")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}, {"file": T_PKG, "role": "test registration"}, {"file": T_EXT, "role": "external evidence test"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "LB-CHART-01-DEFINER", "gold_role": "H2", "gold": {"class": "org.jfree.chart.plot.PlotUtilities", "method": "offset", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_BUG}, "declared_collateral": ["org.jfree.chart.plot.junit.PlotUtilitiesTests::testOffset", "org.jfree.chart.plot.junit.RingPlotTests::testCollapse"]},
           "ADAPTER_FAULT": {"variant_id": "LB-CHART-01-ADAPTER", "gold_role": "H3", "gold": {"class": "org.jfree.chart.plot.Plot", "method": "nudge", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_BUG}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Chart/bug-01"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
