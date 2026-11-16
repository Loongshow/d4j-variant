"""Counterfactual variants V1..V5 of the successful adversarial Chart pair (ADV-DEFINER-01). Each variant changes ONE thing.
Usage: build_counterfactuals.py <chart-checkout>   -> counterfactuals/packages/CF-Vn/{variant.patch,test.patch,cf.json}"""
import sys, os, json, re; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"; D = f"{SP}/ocflb-differential-analysis-v1"; ADV = f"{SP}/adversarial-break-v1/construction/packages/ADV-DEFINER-01"
W = sys.argv[1]
F = {"H1": "source/org/jfree/chart/plot/CompassPlot.java", "H2p": "source/org/jfree/chart/plot/StandardDialScale.java", "H2": "source/org/jfree/chart/plot/PlotUtilities.java", "H3": "source/org/jfree/chart/plot/Plot.java", "H5": "source/org/jfree/chart/util/ShapeUtilities.java", "facade": "source/org/jfree/chart/plot/PiePlot.java", "rim": "source/org/jfree/chart/plot/dial/StandardDialScale.java"}
PROD = [F["facade"], F["H1"], F["rim"], F["H2"], F["H3"], F["H5"]]
T_TRIG = "tests/org/jfree/chart/plot/junit/PiePlotTests.java"; T_PIN = "tests/org/jfree/chart/plot/junit/PlotUtilitiesTests.java"; T_PKG = "tests/org/jfree/chart/plot/junit/PlotPackageTests.java"; T_SHAPE = "tests/org/jfree/chart/util/junit/ShapeUtilitiesTests.java"
NUDGE_BUG = "        double deltaX = drift.getX() * explodePercent;\n        double deltaY = drift.getY() * explodePercent;"
NUDGE_OK = "        double deltaX = -drift.getX() * explodePercent;\n        double deltaY = -drift.getY() * explodePercent;"
DRIFT_IN = "        return new Point2D.Double(point1.getX() - point2.getX(),\n                point1.getY() - point2.getY());"
DRIFT_OUT = "        return new Point2D.Double(point2.getX() - point1.getX(),\n                point2.getY() - point1.getY());"
H2_DOC_V0 = "    /**\n     * Computes the drift between a point on the unexploded ring and the\n     * corresponding point on the exploded ring.\n"
H2_DOC_V3 = "    /**\n     * Computes the drift of a section: the displacement from the point on the\n     * exploded ring back to the corresponding point on the unexploded ring\n     * (point1 minus point2). The drift points toward the pie centre; a section\n     * is exploded by displacing it against the drift.\n"
H3_DOC_V0 = "    /**\n     * Scales a drift by an explode percentage and resolves the bounds of the\n     * exploded section.\n"
H3_DOC_V4 = "    /**\n     * Scales the drift of a section by the explode percentage and displaces\n     * the section against the scaled drift: the drift points toward the pie\n     * centre, so the exploded section moves away from it.\n"
PIN_IN = "        assertEquals(50.0, d.getX(), 0.0);"; PIN_OUT = "        assertEquals(-50.0, d.getX(), 0.0);"
RETREAT = '''    /**
     * Moves an exploded section back toward the pie centre by a fraction of
     * its drift.
     *
     * @param exploded  the bounds of the exploded section.
     * @param point1  the point on the unexploded ring.
     * @param point2  the corresponding point on the exploded ring.
     * @param percent  the fraction of the drift to move back by.
     *
     * @return The bounds of the retreated section.
     */
    public static Rectangle2D retreat(Rectangle2D exploded, Point2D point1,
            Point2D point2, double percent) {
        Point2D drift = drift(point1, point2);
        double x = exploded.getX() + drift.getX() * percent;
        double y = exploded.getY() + drift.getY() * percent;
        return new Rectangle2D.Double(x, y, exploded.getWidth(),
                exploded.getHeight());
    }'''
RETREAT_TEST = '''    /**
     * Retreating an exploded section by its whole drift returns it to the
     * unexploded position.
     */
    public void testRetreat() {
        Rectangle2D exploded = new Rectangle2D.Double(50.0, 200.0, 20.0, 20.0);
        Rectangle2D back = PlotUtilities.retreat(exploded,
                new Point2D.Double(100.0, 200.0), new Point2D.Double(50.0, 200.0),
                1.0);
        assertEquals(100.0, back.getX(), 0.0);
        assertEquals(200.0, back.getY(), 0.0);
        assertEquals(20.0, back.getWidth(), 0.0);
    }'''
EXPLODE = '''    /**
     * Explodes a section: displaces an area from a point on the unexploded
     * ring toward the corresponding point on the exploded ring by a fraction
     * of the distance between them.
     *
     * @param area  the area of the unexploded section.
     * @param point1  the point on the unexploded ring.
     * @param point2  the corresponding point on the exploded ring.
     * @param explodePercent  the explode percentage.
     *
     * @return The exploded area.
     */
    public static Rectangle2D explode(Rectangle2D area, Point2D point1,
            Point2D point2, double explodePercent) {
        double x = area.getX() + (point2.getX() - point1.getX()) * explodePercent;
        double y = area.getY() + (point2.getY() - point1.getY()) * explodePercent;
        return new Rectangle2D.Double(x, y, area.getWidth(), area.getHeight());
    }'''
EXPLODE_TEST = '''    /**
     * Exploding an area moves it toward the exploded ring.
     */
    public void testExplode() {
        Rectangle2D area = new Rectangle2D.Double(100.0, 100.0, 200.0, 200.0);
        Rectangle2D exploded = ShapeUtilities.explode(area,
                new Point2D.Double(100.0, 200.0), new Point2D.Double(50.0, 200.0),
                0.25);
        assertEquals(87.5, exploded.getX(), 0.0);
        assertEquals(100.0, exploded.getY(), 0.0);
    }'''
VARIANTS = {
 "V1": {"title": "V0 + production second caller of drift (PlotUtilities.retreat, inward semantics) with its own passing test", "changes": "second caller only"},
 "V2": {"title": "V0 + external ownership evidence: a sibling inline implementation ShapeUtilities.explode (correct end-to-end formula) with its own passing test; not on the chain", "changes": "external evidence only"},
 "V3": {"title": "V0 + explicit H2 javadoc stating drift = point1 - point2, pointing toward the centre, sections exploded against it", "changes": "H2 javadoc only"},
 "V4": {"title": "V0 + explicit H3 javadoc stating nudge displaces the section against the scaled drift", "changes": "H3 javadoc only"},
 "V5": {"title": "V0 with the subtle adapter error replaced by an obvious one: drift = point2 - point1 (outward, pin updated), nudge negates explicitly", "changes": "adapter error made locally obvious (explicit unary minus); definer convention natural"},
}
def base(work):
    B.apply_patch(work, f"{ADV}/variant.patch"); B.apply_patch(work, f"{ADV}/test.patch"); B.sh(["git", "add", "-N", T_PIN], work)
def build(work, v):
    base(work)
    if v == "V1":
        B.replace_once(work, F["H2"], "                point1.getY() - point2.getY());\n    }\n", "                point1.getY() - point2.getY());\n    }\n\n" + RETREAT + "\n")
        B.replace_once(work, T_PIN, "        assertEquals(0.0, d.getY(), 0.0);\n    }\n", "        assertEquals(0.0, d.getY(), 0.0);\n    }\n\n" + RETREAT_TEST + "\n")
        B.add_import(work, T_PIN, "import java.awt.geom.Rectangle2D;")
    elif v == "V2":
        B.replace_once(work, F["H5"], "        return new Rectangle2D.Double(x, y, area.getWidth(), area.getHeight());\n    }\n", "        return new Rectangle2D.Double(x, y, area.getWidth(), area.getHeight());\n    }\n\n" + EXPLODE + "\n")
        B.add_import(work, F["H5"], "import java.awt.geom.Point2D;")
        B.insert_before_class_end(work, T_SHAPE, EXPLODE_TEST); B.add_import(work, T_SHAPE, "import java.awt.geom.Point2D;"); B.add_import(work, T_SHAPE, "import java.awt.geom.Rectangle2D;")
    elif v == "V3": B.replace_once(work, F["H2"], H2_DOC_V0, H2_DOC_V3)
    elif v == "V4": B.replace_once(work, F["H3"], H3_DOC_V0, H3_DOC_V4)
    elif v == "V5":
        B.replace_once(work, F["H2"], DRIFT_IN, DRIFT_OUT); B.replace_once(work, F["H3"], NUDGE_BUG, NUDGE_OK); B.replace_once(work, T_PIN, PIN_IN, PIN_OUT)
for v, meta in VARIANTS.items():
    B.reset(W); build(W, v); d = f"{D}/counterfactuals/packages/CF-{v}"; os.makedirs(d, exist_ok=True)
    tests = [T_TRIG, T_PIN, T_PKG] + ([T_SHAPE] if v == "V2" else [])
    B.diff_to(W, f"{d}/variant.patch", PROD); B.diff_to(W, f"{d}/test.patch", tests)
    gold_bug, gold_orig = (NUDGE_OK, NUDGE_BUG) if v == "V5" else (NUDGE_BUG, NUDGE_OK)
    cf = {"variant_id": f"CF-{v}", "project": "Chart", "base_version": "Chart-1f", "parent": "ADV-DEFINER-01", **meta, "trigger": "org.jfree.chart.plot.junit.PiePlotTests::test2986548", "expected_signature": "expected:<87.5> but was:<112.5>",
          "pin_test": "org.jfree.chart.plot.junit.PlotUtilitiesTests::testDrift", "extra_passing_tests": (["org.jfree.chart.plot.junit.PlotUtilitiesTests::testRetreat"] if v == "V1" else ["org.jfree.chart.util.junit.ShapeUtilitiesTests::testExplode"] if v == "V2" else []),
          "gold": {"class": "org.jfree.chart.plot.Plot", "method": "nudge", "file": F["H3"], "bug_line": gold_bug, "orig_line": gold_orig}, "h2": "org.jfree.chart.plot.PlotUtilities#drift", "h3": "org.jfree.chart.plot.Plot#nudge",
          "candidates": ["org.jfree.chart.plot.PiePlot#getArcBounds", "org.jfree.chart.plot.CompassPlot#ring", "org.jfree.chart.plot.dial.StandardDialScale#rim", "org.jfree.chart.plot.PlotUtilities#drift", "org.jfree.chart.plot.Plot#nudge", "org.jfree.chart.util.ShapeUtilities#shift"],
          "package_dir": d, "prod_files": PROD, "test_files": tests}
    json.dump(cf, open(f"{d}/cf.json", "w"), indent=1); print("emitted", v, os.path.getsize(f"{d}/variant.patch"), os.path.getsize(f"{d}/test.patch"))
B.reset(W)
