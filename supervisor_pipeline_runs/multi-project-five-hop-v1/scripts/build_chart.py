"""Deterministic construction of CHART-AXIS-CONTROL-01 / CHART-AXIS-TREATMENT-01 on a fresh Chart-1f checkout. No LLM.
Usage: build_chart.py <control|treatment> <work_checkout> <package_dir>. Exact, asserted string edits; patches emitted with git diff."""
import os, subprocess, sys, hashlib
arm, work, pkg = sys.argv[1], sys.argv[2], sys.argv[3]
def run(cmd):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True); assert p.returncode == 0, p.stdout + p.stderr; return p.stdout
def run_bytes(cmd):   # git diff must be captured byte-exact so that CRLF context lines keep their CR (otherwise git apply rejects the patch)
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
    if t[:k + 1].endswith("\n\n") and block.startswith("\n"): block = block[1:]   # keep exactly one blank line before the inserted method
    wr(path, t[:k + 1] + block + t[k + 1:])
assert not [l for l in run(["git", "status", "--short"]).splitlines() if not l.startswith("??")], "work tree not clean"
S = lambda *p: os.path.join(work, "source/org/jfree", *p)
CA, RE, RI, AS_, RG, RA = S("chart/axis/CategoryAxis.java"), S("chart/util/RectangleEdge.java"), S("chart/util/RectangleInsets.java"), S("chart/axis/AxisSpace.java"), S("data/Range.java"), S("chart/util/RectangleAnchor.java")
TEST = os.path.join(work, "tests/org/jfree/chart/axis/junit/CategoryAxisTests.java")
# ---- trigger (both arms): two imports + one test method with a neutral bug-number style name ----
edit(TEST, "import java.awt.GradientPaint;\n", "import java.awt.GradientPaint;\nimport java.awt.geom.Rectangle2D;\n")
edit(TEST, "import org.jfree.chart.axis.CategoryLabelPositions;\n", "import org.jfree.chart.axis.CategoryLabelPositions;\nimport org.jfree.chart.util.RectangleEdge;\n")
t = rd(TEST); assert t.rstrip().endswith("}\n\n}") or t.rstrip().endswith("}")
test_src = ('    /**\n     * Some checks for the category start coordinates.\n     */\n    public void test2064767() {\n'
            '        CategoryAxis axis = new CategoryAxis("Category");\n        axis.setLowerMargin(0.05);\n        axis.setUpperMargin(0.05);\n        axis.setCategoryMargin(0.20);\n'
            '        Rectangle2D area = new Rectangle2D.Double(10.0, 20.0, 400.0, 200.0);\n'
            '        assertEquals(30.0, axis.getCategoryStart(0, 4, area,\n                RectangleEdge.BOTTOM), 0.0000001);\n'
            '        assertEquals(126.66666666666667, axis.getCategoryStart(1, 4, area,\n                RectangleEdge.BOTTOM), 0.0000001);\n'
            '        assertEquals(223.33333333333334, axis.getCategoryStart(2, 4, area,\n                RectangleEdge.BOTTOM), 0.0000001);\n'
            '        assertEquals(175.0, axis.getCategoryStart(3, 4, area,\n                RectangleEdge.LEFT), 0.0000001);\n    }\n\n')
k = t.rstrip().rfind("\n}"); wr(TEST, t[:k + 1] + test_src + t[k + 1:])
ORIG_LINE = "        result = result + category * (categorySize + categoryGapWidth);"; BUG_LINE = "        result = result + (category * categorySize + categoryGapWidth);"
if arm == "control":
    edit(CA, ORIG_LINE, BUG_LINE); files = ["source/org/jfree/chart/axis/CategoryAxis.java"]
else:
    old_body = ('        double result = 0.0;\n        if ((edge == RectangleEdge.TOP) || (edge == RectangleEdge.BOTTOM)) {\n            result = area.getX() + area.getWidth() * getLowerMargin();\n        }\n'
                '        else if ((edge == RectangleEdge.LEFT)\n                || (edge == RectangleEdge.RIGHT)) {\n            result = area.getMinY() + area.getHeight() * getLowerMargin();\n        }\n\n'
                '        double categorySize = calculateCategorySize(categoryCount, area, edge);\n        double categoryGapWidth = calculateCategoryGapSize(categoryCount, area,\n                edge);\n\n'
                '        result = result + category * (categorySize + categoryGapWidth);\n        return result;\n')
    new_body = ('        return RectangleEdge.locate(area, edge, category, categoryCount,\n                getLowerMargin(), getUpperMargin(), getCategoryMargin());\n')
    edit(CA, old_body, new_body)
    SER = '    /**\n     * Ensures that serialization returns the unique instances.\n'
    hop1 = ('    /**\n     * Returns the coordinate of one cell of a run of cells laid out along\n     * the specified edge of a rectangle.\n     *\n'
            '     * @param area  the rectangle.\n     * @param edge  the edge.\n     * @param index  the index of the cell.\n     * @param count  the number of cells.\n'
            '     * @param lead  the space before the run (as a percentage of the length).\n     * @param trail  the space after the run (as a percentage of the length).\n'
            '     * @param spread  the space within the run (as a percentage of the\n     *                length).\n     *\n     * @return The coordinate.\n     */\n'
            '    public static double locate(Rectangle2D area, RectangleEdge edge,\n                                int index, int count, double lead,\n                                double trail, double spread) {\n'
            '        double start = 0.0;\n        double length = 0.0;\n        if ((edge == RectangleEdge.TOP) || (edge == RectangleEdge.BOTTOM)) {\n            start = area.getX();\n            length = area.getWidth();\n        }\n'
            '        else if ((edge == RectangleEdge.LEFT)\n                || (edge == RectangleEdge.RIGHT)) {\n            start = area.getMinY();\n            length = area.getHeight();\n        }\n'
            '        return RectangleInsets.inset(start, length, index, count, lead, trail,\n                spread);\n    }\n\n')
    insert_before(RE, SER, hop1)
    hop2 = ('\n    /**\n     * Returns the coordinate of one cell of a run of cells that starts after\n     * a leading inset.\n     *\n'
            '     * @param start  the start of the available length.\n     * @param length  the available length.\n     * @param index  the index of the cell.\n     * @param count  the number of cells.\n'
            '     * @param lead  the leading inset (as a percentage of the length).\n     * @param trail  the trailing inset (as a percentage of the length).\n'
            '     * @param spread  the space within the run (as a percentage of the\n     *                length).\n     *\n     * @return The coordinate.\n     */\n'
            '    public static double inset(double start, double length, int index,\n                               int count, double lead, double trail,\n                               double spread) {\n'
            '        double origin = start + length * lead;\n        double fraction;\n        if (count > 1) {\n            fraction = 1 - lead - trail - spread;\n        }\n        else {\n            fraction = 1 - lead - trail;\n        }\n'
            '        return AxisSpace.cell(origin, length, fraction, index, count, spread);\n    }\n\n')
    append_before_class_end(RI, hop2)
    edit(RI, "import java.io.Serializable;\n", "import java.io.Serializable;\n\nimport org.jfree.chart.axis.AxisSpace;\n")
    hop3 = ('\n    /**\n     * Returns the coordinate of one cell of a run of cells that share a\n     * fraction of the available length.\n     *\n'
            '     * @param origin  the coordinate at which the run starts.\n     * @param length  the available length.\n     * @param fraction  the fraction of the length shared by the cells.\n'
            '     * @param index  the index of the cell.\n     * @param count  the number of cells.\n     * @param spread  the space within the run (as a percentage of the\n     *                length).\n     *\n     * @return The coordinate.\n     */\n'
            '    public static double cell(double origin, double length, double fraction,\n                              int index, int count, double spread) {\n'
            '        double cell = length * fraction;\n        if (count > 1) {\n            cell = cell / count;\n        }\n        return Range.pad(origin, length, cell, index, count, spread);\n    }\n\n')
    append_before_class_end(AS_, hop3)
    edit(AS_, "import org.jfree.chart.util.RectangleEdge;\n", "import org.jfree.chart.util.RectangleEdge;\nimport org.jfree.data.Range;\n")
    hop4 = ('\n    /**\n     * Returns the coordinate of one cell of a padded run of cells.\n     *\n'
            '     * @param origin  the coordinate at which the run starts.\n     * @param length  the available length.\n     * @param cell  the length of one cell.\n'
            '     * @param index  the index of the cell.\n     * @param count  the number of cells.\n     * @param spread  the space within the run (as a percentage of the\n     *                length).\n     *\n     * @return The coordinate.\n     */\n'
            '    public static double pad(double origin, double length, double cell,\n                             int index, int count, double spread) {\n'
            '        double pad = 0.0;\n        if (count > 1) {\n            pad = length * spread / (count - 1);\n        }\n        return RectangleAnchor.place(origin, index, cell, pad);\n    }\n\n')
    append_before_class_end(RG, hop4)
    edit(RG, "import java.io.Serializable;\n", "import java.io.Serializable;\n\nimport org.jfree.chart.util.RectangleAnchor;\n")
    hop5 = ('    /**\n     * Returns the coordinate of the cell with the given index.\n     *\n'
            '     * @param origin  the coordinate at which the first cell starts.\n     * @param index  the index of the cell.\n     * @param cell  the length of one cell.\n     * @param pad  the padding.\n     *\n     * @return The coordinate.\n     */\n'
            '    public static double place(double origin, int index, double cell,\n                               double pad) {\n        double offset = index * cell + pad;\n        return origin + offset;\n    }\n\n')
    insert_before(RA, SER, hop5)
    files = ["source/org/jfree/chart/axis/CategoryAxis.java", "source/org/jfree/chart/util/RectangleEdge.java", "source/org/jfree/chart/util/RectangleInsets.java", "source/org/jfree/chart/axis/AxisSpace.java", "source/org/jfree/data/Range.java", "source/org/jfree/chart/util/RectangleAnchor.java"]
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "variant.patch"), "wb").write(run_bytes(["git", "diff", "--"] + files)); open(os.path.join(pkg, "test.patch"), "wb").write(run_bytes(["git", "diff", "--", "tests/org/jfree/chart/axis/junit/CategoryAxisTests.java"]))
for f in ("variant.patch", "test.patch"): print(arm, f, hashlib.sha256(open(os.path.join(pkg, f), "rb").read()).hexdigest()[:16], len(open(os.path.join(pkg, f)).read().splitlines()), "lines")
print(arm, "built:", run(["git", "status", "--short"]).replace("\n", " "))
