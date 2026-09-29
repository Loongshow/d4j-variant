"""ADV-DEFINER-01 (idea CMB-01): CHART-PIE-03 rebuilt so the definer (PlotUtilities.drift) is a pure Point2D function pinned
by its own passing unit test, the gold moves to the NON-TERMINAL adapter Plot.nudge (missing negation), and the terminal
ShapeUtilities.shift is a correct textbook '+delta' utility. Usage: build_definer.py <work> <pkgdir>"""
import sys, json, os, re
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W, PKG = sys.argv[1], sys.argv[2]; os.makedirs(PKG, exist_ok=True)
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
HIST = f"{SP}/core-benchmark-scaleup-v1/chart/bug-03/packages/CHART-PIE-TREATMENT-03/variant.patch"; HIST_TEST = HIST.replace("variant.patch", "test.patch")
PU = "source/org/jfree/chart/plot/PlotUtilities.java"; SD = "source/org/jfree/chart/plot/dial/StandardDialScale.java"; PL = "source/org/jfree/chart/plot/Plot.java"
PT = "tests/org/jfree/chart/plot/junit/PiePlotTests.java"; PUT = "tests/org/jfree/chart/plot/junit/PlotUtilitiesTests.java"; PPT = "tests/org/jfree/chart/plot/junit/PlotPackageTests.java"
B.reset(W)
# ---- test.patch: PIE-03 trigger + a real unit test that pins the definer's convention
B.apply_patch(W, HIST_TEST)
B.new_file(W, PUT, """/* ===========================================================
 * JFreeChart : a free chart library for the Java(tm) platform
 * ===========================================================
 *
 * (C) Copyright 2000-2009, by Object Refinery Limited and Contributors.
 *
 * Project Info:  http://www.jfree.org/jfreechart/index.html
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2.1 of the License, or
 * (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
 * License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
 * USA.
 *
 * [Java is a trademark or registered trademark of Sun Microsystems, Inc.
 * in the United States and other countries.]
 *
 * -----------------------
 * PlotUtilitiesTests.java
 * -----------------------
 * (C) Copyright 2009, by Object Refinery Limited and Contributors.
 *
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
     * Checks the drift between two points on the unexploded and exploded rings.
     */
    public void testDrift() {
        Point2D d = PlotUtilities.drift(new Point2D.Double(100.0, 200.0),
                new Point2D.Double(50.0, 200.0));
        assertEquals(50.0, d.getX(), 0.0);
        assertEquals(0.0, d.getY(), 0.0);
    }

}
""")
B.replace_once(W, PPT, "        suite.addTestSuite(PiePlotTests.class);", "        suite.addTestSuite(PiePlotTests.class);\n        suite.addTestSuite(PlotUtilitiesTests.class);")
B.diff_to(W, f"{PKG}/test.patch", [PT, PUT, PPT]); B.diff_to(W, f"{PKG}/trigger_test.patch", [PT]); B.sh(["git", "reset", "-q", "--", "."], W); B.sh(["git", "checkout", "--", "."], W); B.sh(["git", "clean", "-fdq", "--", "tests"], W)
# ---- variant.patch: PIE-03 chain with three hops rewritten
B.apply_patch(W, HIST)
t, eol = B.read(W, PU); k = t.index("    /**", t.index("import java.awt.geom.Rectangle2D;")); s = t.index("public static Rectangle2D drift("); k = t.rfind("    /**", 0, s); e = t.index("    }\n", s) + len("    }\n")
B.write(W, PU, t[:k] + """    /**
     * Computes the drift between a point on the unexploded ring and the
     * corresponding point on the exploded ring.
     *
     * @param point1  the point on the unexploded ring.
     * @param point2  the point on the exploded ring.
     *
     * @return The drift.
     */
    public static Point2D drift(Point2D point1, Point2D point2) {
        return new Point2D.Double(point1.getX() - point2.getX(),
                point1.getY() - point2.getY());
    }
""" + t[e:], eol)
B.replace_once(W, SD, "        return PlotUtilities.drift(unexploded, explodePercent, point1, point2);",
               "        return Plot.nudge(unexploded, explodePercent,\n                PlotUtilities.drift(point1, point2));")
B.add_import(W, SD, "import org.jfree.chart.plot.Plot;")
t, eol = B.read(W, PL); s = t.index("public static Rectangle2D nudge("); k = t.rfind("    /**", 0, s); e = t.index("    }\n", s) + len("    }\n")
B.write(W, PL, t[:k] + """    /**
     * Scales a drift by an explode percentage and resolves the bounds of the
     * exploded section.
     *
     * @param unexploded  the bounds of the unexploded section.
     * @param explodePercent  the explode percentage.
     * @param drift  the drift of the section.
     *
     * @return The bounds of the exploded section.
     */
    public static Rectangle2D nudge(Rectangle2D unexploded, double explodePercent,
            Point2D drift) {
        double deltaX = drift.getX() * explodePercent;
        double deltaY = drift.getY() * explodePercent;
        return ShapeUtilities.shift(unexploded, deltaX, deltaY);
    }
""" + t[e:], eol)
B.add_import(W, PL, "import java.awt.geom.Point2D;")
B.diff_to(W, f"{PKG}/variant.patch"); B.reset(W)
chain = [{"tag": "facade", "class": "org.jfree.chart.plot.PiePlot", "method": "getArcBounds", "decl": "protected Rectangle2D getArcBounds(Rectangle2D unexploded,"},
         {"tag": "H1", "class": "org.jfree.chart.plot.CompassPlot", "method": "ring", "decl": "public static Rectangle2D ring(Rectangle2D unexploded"},
         {"tag": "H2", "class": "org.jfree.chart.plot.dial.StandardDialScale", "method": "rim", "decl": "public static Rectangle2D rim(Rectangle2D unexploded"},
         {"tag": "H3", "class": "org.jfree.chart.plot.PlotUtilities", "method": "drift", "decl": "public static Point2D drift(Point2D point1"},
         {"tag": "H4", "class": "org.jfree.chart.plot.Plot", "method": "nudge", "decl": "public static Rectangle2D nudge(Rectangle2D unexploded"},
         {"tag": "H5", "class": "org.jfree.chart.util.ShapeUtilities", "method": "shift", "decl": "public static Rectangle2D shift(Rectangle2D area"}]
cfg = {"variant_id": "ADV-DEFINER-01", "attack_id": "CMB-01", "title": "CHART-PIE-03 rebuilt: pure definer (drift, pinned by its own unit test) + NON-TERMINAL gold (nudge drops the negation) + correct textbook terminal (shift)",
       "project": "Chart", "base_version": "Chart-1f", "trigger": "org.jfree.chart.plot.junit.PiePlotTests::test2986548", "related_tests": [], "companion_tests": ["org.jfree.chart.plot.junit.PlotUtilitiesTests::testDrift"], "test_file": PT,
       "expected_signature": "expected:<87.5> but was:<112.5>", "assertion_class_regex": "AssertionFailedError|AssertionError",
       "gold": {"class": "org.jfree.chart.plot.Plot", "method": "nudge", "file": PL, "decl": "public static Rectangle2D nudge(Rectangle2D unexploded",
                "bug_line": "        double deltaX = drift.getX() * explodePercent;\n        double deltaY = drift.getY() * explodePercent;",
                "orig_line": "        double deltaX = -drift.getX() * explodePercent;\n        double deltaY = -drift.getY() * explodePercent;"},
       "mechanism": "composes the only measured double-model failure (both models blame the method that DEFINES the wrong-looking quantity, drift = point1 - point2) with a non-terminal gold: the missing negation now lives in the adapter Plot.nudge, which both models ranked 2nd in every PIE-03 run; drift's convention is pinned by a passing unit test and shift is a textbook utility whose javadoc matches its body",
       "classification": ["ATTRIBUTION_TRAP", "OWNERSHIP_TRAP", "DEPTH_PRIOR_TRAP", "CONTEXT_TRAP"], "family": "sign convention split across definer and adapter",
       "effect": "the exploded section is displaced away from the pie centre by the drift instead of toward it: expected 87.5, actual 112.5",
       "predicted_wrong_top1": "org.jfree.chart.plot.PlotUtilities#drift (definer) at rank 1; gold Plot#nudge rank 2",
       "roles": {"org.jfree.chart.plot.PlotUtilities#drift": "producer", "org.jfree.chart.util.ShapeUtilities#shift": "deeper-stage", "org.jfree.chart.plot.dial.StandardDialScale#rim": "shallower-stage",
                 "org.jfree.chart.plot.CompassPlot#ring": "shallower-stage", "org.jfree.chart.plot.PiePlot#getArcBounds": "facade"},
       "candidates": [f"{h['class']}#{h['method']}" for h in chain], "structure": "five-hop chain, gold at H4, definer at H3 pinned by PlotUtilitiesTests.testDrift", "hops": 5, "chain": chain,
       "changed_files": [{"file": "source/org/jfree/chart/plot/PiePlot.java", "role": "facade"}, {"file": "source/org/jfree/chart/plot/CompassPlot.java", "role": "H1"}, {"file": SD, "role": "H2"}, {"file": PU, "role": "H3 definer"}, {"file": PL, "role": "gold H4"}, {"file": "source/org/jfree/chart/util/ShapeUtilities.java", "role": "H5"}, {"file": PT, "role": "trigger"}, {"file": PUT, "role": "definer unit test"}, {"file": PPT, "role": "suite"}],
       "trigger_only_test_patch": f"{PKG}/trigger_test.patch", "package_dir": PKG}
json.dump(cfg, open(f"{PKG}/attack.json", "w"), indent=1); print("built ADV-DEFINER-01:", os.path.getsize(f"{PKG}/variant.patch"), "B variant,", os.path.getsize(f"{PKG}/test.patch"), "B test")
