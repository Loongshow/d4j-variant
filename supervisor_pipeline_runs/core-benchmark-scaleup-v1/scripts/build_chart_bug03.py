"""Deterministic construction of CHART-PIE-CONTROL-03 / CHART-PIE-TREATMENT-03 on a fresh Chart-1f checkout. No LLM.
Usage: build_chart_bug03.py <control|treatment> <work_checkout> <package_dir>. Exact, asserted string edits; patches emitted with git diff (byte-exact, CRLF kept).
NON-CANONICAL / CORE BENCHMARK SCALE-UP / NO GPT-5.6 RUNS PERFORMED."""
import os, subprocess, sys, hashlib
arm, work, pkg = sys.argv[1], sys.argv[2], sys.argv[3]
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def run_bytes(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True); assert p.returncode == 0, p.stdout.decode() + p.stderr.decode(); return p.stdout
EOL = {}
def rd(p):
    raw = open(p, "rb").read().decode("utf-8"); EOL[p] = "\r\n" if "\r\n" in raw else "\n"; return raw.replace("\r\n", "\n")
def wr(p, t): open(p, "wb").write(t.replace("\n", EOL.get(p, "\n")).encode("utf-8"))
def edit(path, old, new):
    t = rd(path); assert t.count(old) == 1, f"{os.path.basename(path)}: expected exactly one match for {old[:70]!r}, got {t.count(old)}"; wr(path, t.replace(old, new, 1))
def append_before_class_end(path, block):
    t = rd(path); assert t.rstrip().endswith("}"); k = t.rstrip().rfind("\n}")
    if t[:k + 1].endswith("\n\n") and block.startswith("\n"): block = block[1:]
    wr(path, t[:k + 1] + block + t[k + 1:])
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
S = lambda *p: os.path.join(work, "source/org/jfree", *p)
PP, CP, SD, PU, PL, SU = S("chart/plot/PiePlot.java"), S("chart/plot/CompassPlot.java"), S("chart/plot/dial/StandardDialScale.java"), S("chart/plot/PlotUtilities.java"), S("chart/plot/Plot.java"), S("chart/util/ShapeUtilities.java")
TEST = os.path.join(work, "tests/org/jfree/chart/plot/junit/PiePlotTests.java")
# ---- trigger (both arms): one test method with a neutral bug-number style name + a small probe subclass (getArcBounds is protected) ----
t = rd(TEST); assert t.rstrip().endswith("}")
test_src = ('    /**\n     * Some checks for the bounds of exploded pie sections.\n     */\n    public void test2986548() {\n'
            '        ArcProbe plot = new ArcProbe();\n'
            '        Rectangle2D unexploded = new Rectangle2D.Double(100.0, 100.0, 200.0,\n                200.0);\n'
            '        Rectangle2D exploded = new Rectangle2D.Double(50.0, 50.0, 300.0, 300.0);\n'
            '        Rectangle2D bounds = plot.arc(unexploded, exploded, 135.0, 90.0, 0.25);\n'
            '        assertEquals(87.5, bounds.getX(), 0.0);\n        assertEquals(100.0, bounds.getY(), 0.0);\n'
            '        assertEquals(200.0, bounds.getWidth(), 0.0);\n        assertEquals(200.0, bounds.getHeight(), 0.0);\n'
            '        bounds = plot.arc(unexploded, exploded, 0.0, 90.0, 0.5);\n'
            '        assertEquals(117.67766952966369, bounds.getX(), 0.0000001);\n        assertEquals(82.32233047033631, bounds.getY(), 0.0000001);\n'
            '        assertSame(unexploded, plot.arc(unexploded, exploded, 0.0, 90.0, 0.0));\n    }\n\n'
            '    /**\n     * A plot that exposes the bounds of its sections.\n     */\n    static class ArcProbe extends PiePlot {\n'
            '        Rectangle2D arc(Rectangle2D unexploded, Rectangle2D exploded,\n                double angle, double extent, double explodePercent) {\n'
            '            return getArcBounds(unexploded, exploded, angle, extent,\n                    explodePercent);\n        }\n    }\n\n')
k = t.rstrip().rfind("\n}"); wr(TEST, t[:k + 1] + test_src + t[k + 1:])
ORIG_BLOCK = "            return new Rectangle2D.Double(unexploded.getX() - deltaX,\n                    unexploded.getY() - deltaY, unexploded.getWidth(),\n"
BUG_BLOCK = "            return new Rectangle2D.Double(unexploded.getX() + deltaX,\n                    unexploded.getY() + deltaY, unexploded.getWidth(),\n"
if arm == "control":
    edit(PP, ORIG_BLOCK, BUG_BLOCK); files = ["source/org/jfree/chart/plot/PiePlot.java"]
else:
    old_else = ("        else {\n            Arc2D arc1 = new Arc2D.Double(unexploded, angle, extent / 2,\n                    Arc2D.OPEN);\n            Point2D point1 = arc1.getEndPoint();\n"
                "            Arc2D.Double arc2 = new Arc2D.Double(exploded, angle, extent / 2,\n                    Arc2D.OPEN);\n            Point2D point2 = arc2.getEndPoint();\n"
                "            double deltaX = (point1.getX() - point2.getX()) * explodePercent;\n            double deltaY = (point1.getY() - point2.getY()) * explodePercent;\n"
                + ORIG_BLOCK + "                    unexploded.getHeight());\n        }\n")
    new_else = "        else {\n            return CompassPlot.ring(unexploded, exploded, angle, extent,\n                    explodePercent);\n        }\n"
    edit(PP, old_else, new_else)
    # hop 1: CompassPlot.ring - the mid-angle point on the unexploded ring
    edit(CP, "import java.awt.geom.Area;\nimport java.awt.geom.Ellipse2D;\n", "import java.awt.geom.Arc2D;\nimport java.awt.geom.Area;\nimport java.awt.geom.Ellipse2D;\n")
    edit(CP, "import org.jfree.chart.util.RectangleInsets;\n", "import org.jfree.chart.plot.dial.StandardDialScale;\nimport org.jfree.chart.util.RectangleInsets;\n")
    hop1 = ('\n    /**\n     * Locates a section on the unexploded ring and resolves the bounds of the\n     * section once exploded.\n     *\n     * @param unexploded  the area of the unexploded ring.\n'
            '     * @param exploded  the area of the exploded ring.\n     * @param angle  the start angle.\n     * @param extent  the extent of the section.\n     * @param explodePercent  the explode percentage.\n     *\n'
            '     * @return The bounds of the exploded section.\n     */\n    public static Rectangle2D ring(Rectangle2D unexploded, Rectangle2D exploded,\n            double angle, double extent, double explodePercent) {\n'
            '        Arc2D arc1 = new Arc2D.Double(unexploded, angle, extent / 2,\n                Arc2D.OPEN);\n        Point2D point1 = arc1.getEndPoint();\n'
            '        return StandardDialScale.rim(unexploded, exploded, angle, extent,\n                explodePercent, point1);\n    }\n\n')
    append_before_class_end(CP, hop1)
    # hop 2: StandardDialScale.rim - the mid-angle point on the exploded ring
    edit(SD, "import org.jfree.chart.plot.dial.DialPlot;\n", "import org.jfree.chart.plot.PlotUtilities;\nimport org.jfree.chart.plot.dial.DialPlot;\n") if "import org.jfree.chart.plot.dial.DialPlot;\n" in rd(SD) else None
    if "import org.jfree.chart.plot.PlotUtilities;" not in rd(SD): edit(SD, "import java.awt.geom.Rectangle2D;\n", "import java.awt.geom.Rectangle2D;\n\nimport org.jfree.chart.plot.PlotUtilities;\n")
    hop2 = ('\n    /**\n     * Locates a section on the exploded rim and resolves the bounds of the\n     * section once exploded.\n     *\n     * @param unexploded  the area of the unexploded ring.\n'
            '     * @param exploded  the area of the exploded ring.\n     * @param angle  the start angle.\n     * @param extent  the extent of the section.\n     * @param explodePercent  the explode percentage.\n'
            '     * @param point1  the mid-angle point on the unexploded ring.\n     *\n     * @return The bounds of the exploded section.\n     */\n'
            '    public static Rectangle2D rim(Rectangle2D unexploded, Rectangle2D exploded,\n            double angle, double extent, double explodePercent,\n            Point2D point1) {\n'
            '        Arc2D.Double arc2 = new Arc2D.Double(exploded, angle, extent / 2,\n                Arc2D.OPEN);\n        Point2D point2 = arc2.getEndPoint();\n'
            '        return PlotUtilities.drift(unexploded, explodePercent, point1, point2);\n    }\n\n')
    append_before_class_end(SD, hop2)
    # hop 3: PlotUtilities.drift - the drift between the two ring points
    edit(PU, "import org.jfree.data.general.DatasetUtilities;\n", "import java.awt.geom.Point2D;\nimport java.awt.geom.Rectangle2D;\n\nimport org.jfree.data.general.DatasetUtilities;\n")
    hop3 = ('\n    /**\n     * Computes the drift between a point on the unexploded ring and the\n     * corresponding point on the exploded ring, and resolves the bounds of\n     * the exploded section.\n     *\n'
            '     * @param unexploded  the area of the unexploded ring.\n     * @param explodePercent  the explode percentage.\n     * @param point1  the point on the unexploded ring.\n     * @param point2  the point on the exploded ring.\n     *\n'
            '     * @return The bounds of the exploded section.\n     */\n    public static Rectangle2D drift(Rectangle2D unexploded, double explodePercent,\n            Point2D point1, Point2D point2) {\n'
            '        double dx = point1.getX() - point2.getX();\n        double dy = point1.getY() - point2.getY();\n        return Plot.nudge(unexploded, explodePercent, dx, dy);\n    }\n\n')
    append_before_class_end(PU, hop3)
    # hop 4: Plot.nudge - the drift scaled by the explode percentage
    edit(PL, "import org.jfree.chart.util.RectangleInsets;\n", "import org.jfree.chart.util.RectangleInsets;\nimport org.jfree.chart.util.ShapeUtilities;\n")
    hop4 = ('\n    /**\n     * Scales a drift by an explode percentage and resolves the bounds of the\n     * exploded section.\n     *\n     * @param unexploded  the area of the unexploded ring.\n'
            '     * @param explodePercent  the explode percentage.\n     * @param dx  the x-drift.\n     * @param dy  the y-drift.\n     *\n     * @return The bounds of the exploded section.\n     */\n'
            '    public static Rectangle2D nudge(Rectangle2D unexploded, double explodePercent,\n            double dx, double dy) {\n        double deltaX = dx * explodePercent;\n        double deltaY = dy * explodePercent;\n'
            '        return ShapeUtilities.shift(unexploded, deltaX, deltaY);\n    }\n\n')
    append_before_class_end(PL, hop4)
    # hop 5 (gold): ShapeUtilities.shift - the area shifted by the displacement; the BUGGY lines
    hop5 = ('\n    /**\n     * Shifts an area by a displacement.\n     *\n     * @param area  the area.\n     * @param deltaX  the x-displacement.\n     * @param deltaY  the y-displacement.\n     *\n'
            '     * @return The shifted area.\n     */\n    public static Rectangle2D shift(Rectangle2D area, double deltaX,\n            double deltaY) {\n'
            '        double x = area.getX() + deltaX;\n        double y = area.getY() + deltaY;\n        return new Rectangle2D.Double(x, y, area.getWidth(), area.getHeight());\n    }\n\n')
    append_before_class_end(SU, hop5)
    files = ["source/org/jfree/chart/plot/PiePlot.java", "source/org/jfree/chart/plot/CompassPlot.java", "source/org/jfree/chart/plot/dial/StandardDialScale.java", "source/org/jfree/chart/plot/PlotUtilities.java", "source/org/jfree/chart/plot/Plot.java", "source/org/jfree/chart/util/ShapeUtilities.java"]
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "wb").write(run_bytes(["git", "diff", "--"] + files)); open(os.path.join(pkg, "test.patch"), "wb").write(run_bytes(["git", "diff", "--", "tests/org/jfree/chart/plot/junit/PiePlotTests.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
