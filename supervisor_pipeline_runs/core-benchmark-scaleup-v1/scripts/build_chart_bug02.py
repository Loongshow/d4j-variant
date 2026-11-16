"""Deterministic construction of CHART-POLAR-CONTROL-02 / CHART-POLAR-TREATMENT-02 on a fresh Chart-1f checkout. No LLM.
Usage: build_chart_bug02.py <control|treatment> <work_checkout> <package_dir>. Exact, asserted string edits; patches emitted with git diff (byte-exact, CRLF kept).
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
def insert_before(path, anchor, block):
    t = rd(path); assert t.count(anchor) == 1, f"{os.path.basename(path)}: anchor not unique ({t.count(anchor)}): {anchor[:60]!r}"; wr(path, t.replace(anchor, block + anchor, 1))
def append_before_class_end(path, block):
    t = rd(path); assert t.rstrip().endswith("}"); k = t.rstrip().rfind("\n}")
    if t[:k + 1].endswith("\n\n") and block.startswith("\n"): block = block[1:]
    wr(path, t[:k + 1] + block + t[k + 1:])
def method_end(t, decl):
    i = t.find(decl); assert i > 0 and t.count(decl) == 1, decl; d = 0; st = False; j = i
    while j < len(t):
        c = t[j]; d += (c == "{") - (c == "}"); st = st or c == "{"
        if st and d == 0: return j + 1
        j += 1
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
S = lambda *p: os.path.join(work, "source/org/jfree", *p)
PP, AL, DP, TU, RU, LU = S("chart/plot/PolarPlot.java"), S("chart/util/Align.java"), S("chart/plot/dial/DialPlot.java"), S("chart/text/TextUtilities.java"), S("chart/renderer/RendererUtilities.java"), S("chart/util/LineUtilities.java")
TEST = os.path.join(work, "tests/org/jfree/chart/plot/junit/PolarPlotTests.java")
# ---- trigger (both arms): two imports + one test method with a neutral bug-number style name ----
edit(TEST, "import java.awt.GradientPaint;\nimport java.awt.Stroke;\n", "import java.awt.GradientPaint;\nimport java.awt.Point;\nimport java.awt.Stroke;\nimport java.awt.geom.Rectangle2D;\n")
t = rd(TEST); assert t.rstrip().endswith("}")
test_src = ('    /**\n     * Some checks for the translation of polar coordinates.\n     */\n    public void test3078463() {\n'
            '        PolarPlot plot = new PolarPlot(null, new NumberAxis("Radius"),\n                new DefaultPolarItemRenderer());\n        plot.getAxis().setRange(10.0, 30.0);\n'
            '        Rectangle2D area = new Rectangle2D.Double(0.0, 0.0, 240.0, 240.0);\n'
            '        assertEquals(new Point(220, 120),\n                plot.translateValueThetaRadiusToJava2D(90.0, 30.0, area));\n'
            '        assertEquals(new Point(120, 120),\n                plot.translateValueThetaRadiusToJava2D(90.0, 10.0, area));\n'
            '        assertEquals(new Point(170, 120),\n                plot.translateValueThetaRadiusToJava2D(90.0, 20.0, area));\n'
            '        assertEquals(new Point(120, 170),\n                plot.translateValueThetaRadiusToJava2D(180.0, 20.0, area));\n    }\n\n')
k = t.rstrip().rfind("\n}"); wr(TEST, t[:k + 1] + test_src + t[k + 1:])
ORIG_BLOCK = ("        float x = (float) (midX + (xv * (adjustedRadius - axisMin)\n                / (axisMax - axisMin)));\n"
              "        float y = (float) (midY + (yv * (adjustedRadius - axisMin)\n                / (axisMax - axisMin)));\n")
BUG_BLOCK = ("        float x = (float) (midX + (xv * (adjustedRadius - axisMin)\n                / axisMax));\n"
             "        float y = (float) (midY + (yv * (adjustedRadius - axisMin)\n                / axisMax));\n")
if arm == "control":
    edit(PP, ORIG_BLOCK, BUG_BLOCK); files = ["source/org/jfree/chart/plot/PolarPlot.java"]
else:
    # facade: keep the javadoc, the angle convention, the axis bounds and the margin constant; delegate the layout to hop 1
    t = rd(PP); decl = "    public Point translateValueThetaRadiusToJava2D(double angleDegrees,"; i = t.find(decl); assert i > 0 and t.count(decl) == 1
    end = method_end(t, decl); sig_end = t.find("{\n", i) + 2; old_body = t[sig_end:end]; assert ORIG_BLOCK in old_body and "return p;" in old_body
    new_body = ("\n        double radians = Math.toRadians(angleDegrees - 90.0);\n        double axisMin = this.axis.getLowerBound();\n        double axisMax =  getMaxRadius();\n"
                "        return Align.frame(dataArea, MARGIN, radians, radius, axisMin,\n                axisMax);\n    }")
    wr(PP, t[:sig_end] + new_body + t[end:])
    edit(PP, "import org.jfree.chart.util.ObjectUtilities;\n", "import org.jfree.chart.util.Align;\nimport org.jfree.chart.util.ObjectUtilities;\n")
    # hop 1: Align.frame - the framed (margin-inset) drawing area
    edit(AL, "import java.awt.geom.Rectangle2D;\n", "import java.awt.Point;\nimport java.awt.geom.Rectangle2D;\n\nimport org.jfree.chart.plot.dial.DialPlot;\n")
    hop1 = ('\n    /**\n     * Frames an area by a margin and resolves a polar location inside the\n     * framed area.\n     *\n     * @param area  the area.\n     * @param margin  the margin (in Java2D units).\n'
            '     * @param radians  the angle (in radians).\n     * @param radius  the radial value.\n     * @param lower  the lowest radial value.\n     * @param upper  the highest radial value.\n     *\n'
            '     * @return The resolved point.\n     */\n    public static Point frame(Rectangle2D area, int margin, double radians,\n            double radius, double lower, double upper) {\n'
            '        double minx = area.getMinX() + margin;\n        double maxx = area.getMaxX() - margin;\n        double miny = area.getMinY() + margin;\n        double maxy = area.getMaxY() - margin;\n'
            '        return DialPlot.centre(minx, maxx, miny, maxy, radians, radius, lower,\n                upper);\n    }\n\n')
    append_before_class_end(AL, hop1)
    # hop 2: DialPlot.centre - centre and ring radius of the framed area
    edit(DP, "import java.awt.Graphics2D;\nimport java.awt.Shape;\n", "import java.awt.Graphics2D;\nimport java.awt.Point;\nimport java.awt.Shape;\n")
    edit(DP, "import org.jfree.chart.plot.PlotState;\n", "import org.jfree.chart.plot.PlotState;\nimport org.jfree.chart.text.TextUtilities;\n")
    hop2 = ('\n    /**\n     * Derives the centre and the ring radius of a framed area and resolves\n     * a polar location within it.\n     *\n     * @param minx  the left edge of the framed area.\n'
            '     * @param maxx  the right edge of the framed area.\n     * @param miny  the top edge of the framed area.\n     * @param maxy  the bottom edge of the framed area.\n'
            '     * @param radians  the angle (in radians).\n     * @param radius  the radial value.\n     * @param lower  the lowest radial value.\n     * @param upper  the highest radial value.\n     *\n'
            '     * @return The resolved point.\n     */\n    public static Point centre(double minx, double maxx, double miny,\n            double maxy, double radians, double radius, double lower,\n            double upper) {\n'
            '        double lengthX = maxx - minx;\n        double lengthY = maxy - miny;\n        double length = Math.min(lengthX, lengthY);\n        double midX = minx + lengthX / 2.0;\n        double midY = miny + lengthY / 2.0;\n'
            '        return TextUtilities.heading(midX, midY, length, radians, radius,\n                lower, upper);\n    }\n\n')
    append_before_class_end(DP, hop2)
    # hop 3: TextUtilities.heading - the direction vector of the ring radius at the angle
    edit(TU, "import java.awt.Paint;\nimport java.awt.Shape;\n", "import java.awt.Paint;\nimport java.awt.Point;\nimport java.awt.Shape;\n")
    edit(TU, "import java.awt.geom.Rectangle2D;\n", "import java.awt.geom.Rectangle2D;\n\nimport org.jfree.chart.renderer.RendererUtilities;\n")
    hop3 = ('\n    /**\n     * Computes the heading of a ring radius at an angle and resolves a\n     * polar location from the centre.\n     *\n     * @param midX  the x-coordinate of the centre.\n'
            '     * @param midY  the y-coordinate of the centre.\n     * @param length  the ring diameter.\n     * @param radians  the angle (in radians).\n     * @param radius  the radial value.\n'
            '     * @param lower  the lowest radial value.\n     * @param upper  the highest radial value.\n     *\n     * @return The resolved point.\n     */\n'
            '    public static Point heading(double midX, double midY, double length,\n            double radians, double radius, double lower, double upper) {\n'
            '        double xv = length / 2.0 * Math.cos(radians);\n        double yv = length / 2.0 * Math.sin(radians);\n'
            '        return RendererUtilities.pin(midX, midY, xv, yv, radius, lower,\n                upper);\n    }\n\n')
    append_before_class_end(TU, hop3)
    # hop 4: RendererUtilities.pin - placement from the centre and rounding to device pixels
    edit(RU, "import org.jfree.data.DomainOrder;\n", "import java.awt.Point;\nimport java.awt.geom.Point2D;\n\nimport org.jfree.chart.util.LineUtilities;\nimport org.jfree.data.DomainOrder;\n")
    hop4 = ('\n    /**\n     * Pins a polar location to device pixels: the stretched direction\n     * vector is applied to the centre and rounded.\n     *\n     * @param midX  the x-coordinate of the centre.\n'
            '     * @param midY  the y-coordinate of the centre.\n     * @param xv  the x-component of the direction vector.\n     * @param yv  the y-component of the direction vector.\n'
            '     * @param radius  the radial value.\n     * @param lower  the lowest radial value.\n     * @param upper  the highest radial value.\n     *\n     * @return The pinned point.\n     */\n'
            '    public static Point pin(double midX, double midY, double xv, double yv,\n            double radius, double lower, double upper) {\n'
            '        Point2D d = LineUtilities.stretch(xv, yv, radius, lower, upper);\n        float x = (float) (midX + d.getX());\n        float y = (float) (midY + d.getY());\n'
            '        int ix = Math.round(x);\n        int iy = Math.round(y);\n        return new Point(ix, iy);\n    }\n\n')
    append_before_class_end(RU, hop4)
    # hop 5 (gold): LineUtilities.stretch - the direction vector stretched by the radial value's position in the range; the BUGGY lines
    edit(LU, "import java.awt.geom.Line2D;\nimport java.awt.geom.Rectangle2D;\n", "import java.awt.geom.Line2D;\nimport java.awt.geom.Point2D;\nimport java.awt.geom.Rectangle2D;\n")
    hop5 = ('\n    /**\n     * Stretches a direction vector by the position of a radial value within\n     * the radial range.\n     *\n     * @param xv  the x-component of the direction vector.\n'
            '     * @param yv  the y-component of the direction vector.\n     * @param radius  the radial value.\n     * @param lower  the lowest radial value.\n     * @param upper  the highest radial value.\n     *\n'
            '     * @return The stretched vector.\n     */\n    public static Point2D stretch(double xv, double yv, double radius,\n            double lower, double upper) {\n'
            '        double adjusted = Math.max(radius, lower);\n        double dx = xv * (adjusted - lower) / upper;\n        double dy = yv * (adjusted - lower) / upper;\n'
            '        return new Point2D.Double(dx, dy);\n    }\n\n')
    append_before_class_end(LU, hop5)
    files = ["source/org/jfree/chart/plot/PolarPlot.java", "source/org/jfree/chart/util/Align.java", "source/org/jfree/chart/plot/dial/DialPlot.java", "source/org/jfree/chart/text/TextUtilities.java", "source/org/jfree/chart/renderer/RendererUtilities.java", "source/org/jfree/chart/util/LineUtilities.java"]
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "wb").write(run_bytes(["git", "diff", "--"] + files)); open(os.path.join(pkg, "test.patch"), "wb").write(run_bytes(["git", "diff", "--", "tests/org/jfree/chart/plot/junit/PolarPlotTests.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
