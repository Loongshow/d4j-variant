"""OCFLB-CHART-01 (template pair): sign / direction of an exploded pie section. Seed CHART-PIE-TREATMENT-03.
Facade PiePlot.getArcBounds -> H1 CompassPlot.ring -> H2 PlotUtilities.drift (definer) -> H3 Plot.nudge (adapter) -> H4 StandardDialScale.rim -> H5 ShapeUtilities.shift.
Usage: build_chart01.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "Chart"; SEED = "CHART-PIE-TREATMENT-03"
F = {"facade": "source/org/jfree/chart/plot/PiePlot.java", "H1": "source/org/jfree/chart/plot/CompassPlot.java", "H2": "source/org/jfree/chart/plot/PlotUtilities.java",
     "H3": "source/org/jfree/chart/plot/Plot.java", "H4": "source/org/jfree/chart/plot/dial/StandardDialScale.java", "H5": "source/org/jfree/chart/util/ShapeUtilities.java"}
T_TRIG = "tests/org/jfree/chart/plot/junit/PiePlotTests.java"; T_PIN = "tests/org/jfree/chart/plot/junit/PlotUtilitiesTests.java"; T_PKG = "tests/org/jfree/chart/plot/junit/PlotPackageTests.java"
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
        Point2D drift = PlotUtilities.drift(point1, point2);
        return Plot.nudge(unexploded, explodePercent, drift);
    }'''
H2_OK = "        double dx = point2.getX() - point1.getX();\n        double dy = point2.getY() - point1.getY();"
H2_BUG = "        double dx = point1.getX() - point2.getX();\n        double dy = point1.getY() - point2.getY();"
H2 = '''    /**
     * Computes the drift of a section: the displacement from a point on the
     * unexploded ring to the corresponding point on the exploded ring, so
     * that adding the drift to the unexploded point gives the exploded point.
     *
     * @param point1  the point on the unexploded ring.
     * @param point2  the corresponding point on the exploded ring.
     *
     * @return The drift.
     */
    public static Point2D drift(Point2D point1, Point2D point2) {
%s
        return new Point2D.Double(dx, dy);
    }'''
H3_OK = "        double deltaX = drift.getX() * explodePercent;\n        double deltaY = drift.getY() * explodePercent;"
H3_BUG = "        double deltaX = -drift.getX() * explodePercent;\n        double deltaY = -drift.getY() * explodePercent;"
H3 = '''    /**
     * Scales the drift of a section by the explode percentage and displaces
     * the section bounds along the scaled drift.
     *
     * @param unexploded  the bounds of the unexploded section.
     * @param explodePercent  the explode percentage.
     * @param drift  the drift of the section.
     *
     * @return The bounds of the exploded section.
     */
    public static Rectangle2D nudge(Rectangle2D unexploded, double explodePercent,
            Point2D drift) {
%s
        return StandardDialScale.rim(unexploded, deltaX, deltaY);
    }'''
H4 = '''    /**
     * Displaces the anchor of an area and resolves the area at the displaced
     * anchor.
     *
     * @param area  the area.
     * @param deltaX  the x-displacement of the anchor.
     * @param deltaY  the y-displacement of the anchor.
     *
     * @return The displaced area.
     */
    public static Rectangle2D rim(Rectangle2D area, double deltaX,
            double deltaY) {
        double x = area.getX() + deltaX;
        double y = area.getY() + deltaY;
        return ShapeUtilities.shift(area, x, y);
    }'''
H5 = '''    /**
     * Rebuilds an area at the given anchor, preserving its size.
     *
     * @param area  the area.
     * @param x  the x-coordinate of the new anchor.
     * @param y  the y-coordinate of the new anchor.
     *
     * @return The rebuilt area.
     */
    public static Rectangle2D shift(Rectangle2D area, double x, double y) {
        double w = area.getWidth();
        double h = area.getHeight();
        return new Rectangle2D.Double(x, y, w, h);
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
     * Adding the drift to the unexploded point gives the exploded point.
     */
    public void testDrift() {
        Point2D unexploded = new Point2D.Double(100.0, 200.0);
        Point2D exploded = new Point2D.Double(50.0, 200.0);
        Point2D drift = PlotUtilities.drift(unexploded, exploded);
        assertEquals(-50.0, drift.getX(), 0.0000001);
        assertEquals(0.0, drift.getY(), 0.0000001);
        assertEquals(exploded.getX(), unexploded.getX() + drift.getX(),
                0.0000001);
        assertEquals(exploded.getY(), unexploded.getY() + drift.getY(),
                0.0000001);
    }

}
'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "ring", H1)
    B.replace_method(work, F["H2"], "drift", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_method(work, F["H3"], "nudge", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK)); B.add_import(work, F["H3"], "import org.jfree.chart.plot.dial.StandardDialScale;")
    B.replace_method(work, F["H4"], "rim", H4); B.add_import(work, F["H4"], "import org.jfree.chart.util.ShapeUtilities;")
    B.replace_method(work, F["H5"], "shift", H5)
    B.new_file(work, T_PIN, PIN)
    B.replace_once(work, T_PKG, "        suite.addTestSuite(PiePlotTests.class);\n", "        suite.addTestSuite(PiePlotTests.class);\n        suite.addTestSuite(PlotUtilitiesTests.class);\n")
spec = {"pair_id": "OCFLB-CHART-01", "project": P, "bug": "01", "base_version": "Chart-1f", "seed_variant": SEED,
  "family": "sign / direction (offset direction of an exploded pie section)",
  "convention": "drift = exploded point - unexploded point; adding the drift to the unexploded point gives the exploded point, and the scaled drift displaces the section away from the pie centre",
  "effect": "the exploded section is displaced toward the pie centre instead of away from it (x 112.5 instead of 87.5)",
  "equivalence_note": "negating the definer's output (arm A) and negating inside the adapter (arm B) produce the same displaced rectangle for every input",
  "adapter_fault_note": "nudge negates the drift before scaling it",
  "trigger": "org.jfree.chart.plot.junit.PiePlotTests::test2986548", "expected_signature": "expected:<87.5> but was:<112.5>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "org.jfree.chart.plot.junit.PlotUtilitiesTests::testDrift", "second_caller": None,
  "chain": {"facade": {"class": "org.jfree.chart.plot.PiePlot", "method": "getArcBounds", "file": F["facade"]},
            "H1": {"class": "org.jfree.chart.plot.CompassPlot", "method": "ring", "file": F["H1"]}, "H2": {"class": "org.jfree.chart.plot.PlotUtilities", "method": "drift", "file": F["H2"]},
            "H3": {"class": "org.jfree.chart.plot.Plot", "method": "nudge", "file": F["H3"]}, "H4": {"class": "org.jfree.chart.plot.dial.StandardDialScale", "method": "rim", "file": F["H4"]},
            "H5": {"class": "org.jfree.chart.util.ShapeUtilities", "method": "shift", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN, T_PKG],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}, {"file": T_PKG, "role": "test registration"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "OCFLB-CHART-01-DEFINER", "gold_role": "H2", "gold": {"class": "org.jfree.chart.plot.PlotUtilities", "method": "drift", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_BUG}, "declared_collateral": ["org.jfree.chart.plot.junit.PlotUtilitiesTests::testDrift"]},
           "ADAPTER_FAULT": {"variant_id": "OCFLB-CHART-01-ADAPTER", "gold_role": "H3", "gold": {"class": "org.jfree.chart.plot.Plot", "method": "nudge", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_BUG}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/Chart/bug-01"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
