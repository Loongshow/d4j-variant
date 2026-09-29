"""ADV-COMPOSITE-01 (Part 17, maximum difficulty). Base: ADV-DEFINER-01 (pure pinned definer + non-terminal gold). Stacked:
 - witness inversion on the gold: nudge becomes `resolve(r, f, d)` with generic locals and NO javadoc (LEX-01 mechanism);
 - guard padding: ~22 lines of real-idiom argument checks and a zero-percent fast path before the two delta lines, so a
   -A20 grep window on the gold shows only guards (CLAUDE-07);
 - loud, correct terminal: ShapeUtilities.shift's javadoc claims the exploded-section semantics and its y-line is written
   as an odd-looking equivalent (MASK / CTX-06 strengthening);
 - coarse failure: the trigger asserts one boolean over both coordinates, so the failure text carries no 87.5/112.5 clue.
Gold = Plot#resolve (drops the negation). Usage: build_composite.py <work> <pkgdir>"""
import sys, json, os
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/adversarial-break-v1/scripts"); import buildlib as B
W, PKG = sys.argv[1], sys.argv[2]; os.makedirs(PKG, exist_ok=True)
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"; DEF = f"{SP}/adversarial-break-v1/construction/packages/ADV-DEFINER-01"
PU = "source/org/jfree/chart/plot/PlotUtilities.java"; SD = "source/org/jfree/chart/plot/dial/StandardDialScale.java"; PL = "source/org/jfree/chart/plot/Plot.java"
SU = "source/org/jfree/chart/util/ShapeUtilities.java"; PT = "tests/org/jfree/chart/plot/junit/PiePlotTests.java"; PUT = "tests/org/jfree/chart/plot/junit/PlotUtilitiesTests.java"; PPT = "tests/org/jfree/chart/plot/junit/PlotPackageTests.java"
B.reset(W)
# ---- tests: definer test.patch, then coarsen the trigger's assertion to a bare boolean
B.apply_patch(W, f"{DEF}/test.patch"); B.sh(["git", "add", "-N", PUT], W)   # git apply leaves the new test file untracked
t, eol = B.read(W, PT)
blk1 = "        assertEquals(87.5, bounds.getX(), 0.0);\n        assertEquals(100.0, bounds.getY(), 0.0);\n        assertEquals(200.0, bounds.getWidth(), 0.0);\n        assertEquals(200.0, bounds.getHeight(), 0.0);"
blk2 = "        assertEquals(117.67766952966369, bounds.getX(), 0.0000001);\n        assertEquals(82.32233047033631, bounds.getY(), 0.0000001);"
assert t.count(blk1) == 1 and t.count(blk2) == 1, "trigger assertions not found"
t = t.replace(blk1, "        assertTrue(bounds.getX() == 87.5 && bounds.getY() == 100.0\n                && bounds.getWidth() == 200.0 && bounds.getHeight() == 200.0);", 1)
t = t.replace(blk2, "        assertTrue(Math.abs(bounds.getX() - 117.67766952966369) < 0.0000001\n                && Math.abs(bounds.getY() - 82.32233047033631) < 0.0000001);", 1)
B.write(W, PT, t, eol)
B.diff_to(W, f"{PKG}/test.patch", [PT, PUT, PPT]); B.diff_to(W, f"{PKG}/trigger_test.patch", [PT])
B.sh(["git", "reset", "-q", "--", "."], W); B.sh(["git", "checkout", "--", "."], W); B.sh(["git", "clean", "-fdq", "--", "tests", "source"], W)
# ---- production: definer variant, then the stacked manipulations
B.apply_patch(W, f"{DEF}/variant.patch")
B.replace_once(W, SD, "        return Plot.nudge(unexploded, explodePercent,\n                PlotUtilities.drift(point1, point2));",
               "        return Plot.resolve(unexploded, explodePercent,\n                PlotUtilities.drift(point1, point2));")
t, eol = B.read(W, PL); s = t.index("public static Rectangle2D nudge("); k = t.rfind("    /**", 0, s); e = t.index("    }\n", s) + len("    }\n")
B.write(W, PL, t[:k] + """    public static Rectangle2D resolve(Rectangle2D r, double f, Point2D d) {
        if (r == null) {
            throw new IllegalArgumentException("Null 'r' argument.");
        }
        if (d == null) {
            throw new IllegalArgumentException("Null 'd' argument.");
        }
        if (Double.isNaN(f) || Double.isInfinite(f)) {
            throw new IllegalArgumentException("Requires a finite 'f'.");
        }
        if (f < 0.0) {
            throw new IllegalArgumentException("Requires 'f' >= 0.0.");
        }
        if (Double.isNaN(d.getX()) || Double.isNaN(d.getY())) {
            throw new IllegalArgumentException("Requires finite 'd' coordinates.");
        }
        if (r.isEmpty()) {
            return (Rectangle2D) r.clone();
        }
        if (f == 0.0) {
            return (Rectangle2D) r.clone();
        }
        double dx = d.getX() * f;
        double dy = d.getY() * f;
        return ShapeUtilities.shift(r, dx, dy);
    }
""" + t[e:], eol)
# loud, correct terminal
B.replace_once(W, SU, "     * Shifts an area by a displacement.", "     * Resolves the bounds of an exploded pie section from the unexploded area and\n     * its scaled drift: the section is displaced along the drift.")
B.replace_once(W, SU, "        double y = area.getY() + deltaY;", "        double y = area.getMaxY() - area.getHeight() + deltaY;")
B.diff_to(W, f"{PKG}/variant.patch"); B.reset(W)
chain = [{"tag": "facade", "class": "org.jfree.chart.plot.PiePlot", "method": "getArcBounds", "decl": "protected Rectangle2D getArcBounds(Rectangle2D unexploded,"},
         {"tag": "H1", "class": "org.jfree.chart.plot.CompassPlot", "method": "ring", "decl": "public static Rectangle2D ring(Rectangle2D unexploded"},
         {"tag": "H2", "class": "org.jfree.chart.plot.dial.StandardDialScale", "method": "rim", "decl": "public static Rectangle2D rim(Rectangle2D unexploded"},
         {"tag": "H3", "class": "org.jfree.chart.plot.PlotUtilities", "method": "drift", "decl": "public static Point2D drift(Point2D point1"},
         {"tag": "H4", "class": "org.jfree.chart.plot.Plot", "method": "resolve", "decl": "public static Rectangle2D resolve(Rectangle2D r"},
         {"tag": "H5", "class": "org.jfree.chart.util.ShapeUtilities", "method": "shift", "decl": "public static Rectangle2D shift(Rectangle2D area"}]
cfg = {"variant_id": "ADV-COMPOSITE-01", "attack_id": "MAX-01", "title": "maximum-difficulty composite: pinned pure definer + non-terminal generic undocumented guard-padded gold + loud correct terminal + boolean-only failure",
       "project": "Chart", "base_version": "Chart-1f", "trigger": "org.jfree.chart.plot.junit.PiePlotTests::test2986548", "related_tests": [], "companion_tests": ["org.jfree.chart.plot.junit.PlotUtilitiesTests::testDrift"],
       "test_file": PT, "expected_signature": "AssertionFailedError", "assertion_class_regex": "AssertionFailedError|AssertionError",
       "gold": {"class": "org.jfree.chart.plot.Plot", "method": "resolve", "file": PL, "decl": "public static Rectangle2D resolve(Rectangle2D r",
                "bug_line": "        double dx = d.getX() * f;\n        double dy = d.getY() * f;", "orig_line": "        double dx = -d.getX() * f;\n        double dy = -d.getY() * f;"},
       "mechanism": "stacks every mechanism that worked in screening/confirmation on the one that worked best: definer attribution with a non-terminal gold (0/5 Opus, 0/3 Sonnet), witness inversion of the gold, a loud terminal whose javadoc claims the exploded-section semantics, guard padding that keeps the delta lines out of a -A20 window, and a boolean-only failure that removes the 87.5/112.5 clue both models used to infer the sign direction",
       "classification": ["ATTRIBUTION_TRAP", "OWNERSHIP_TRAP", "DEPTH_PRIOR_TRAP", "LEXICAL_TRAP", "TOOL_BEHAVIOR_TRAP", "FAILURE_SIGNAL_TRAP", "CONTEXT_TRAP", "ARTIFACT"],
       "family": "sign convention split across definer and adapter, adapter stripped of witnesses", "effect": "the exploded section is displaced away from the pie centre instead of toward it",
       "predicted_wrong_top1": "org.jfree.chart.plot.PlotUtilities#drift (definer) or ShapeUtilities#shift (loud terminal); gold rank 3+",
       "roles": {"org.jfree.chart.plot.PlotUtilities#drift": "producer", "org.jfree.chart.util.ShapeUtilities#shift": "deeper-stage", "org.jfree.chart.plot.dial.StandardDialScale#rim": "shallower-stage",
                 "org.jfree.chart.plot.CompassPlot#ring": "shallower-stage", "org.jfree.chart.plot.PiePlot#getArcBounds": "facade"},
       "candidates": [f"{h['class']}#{h['method']}" for h in chain], "structure": "five-hop chain, gold at H4 (generic, undocumented, guard-padded), definer at H3 pinned by a unit test, loud terminal at H5", "hops": 5, "chain": chain,
       "changed_files": [{"file": "source/org/jfree/chart/plot/PiePlot.java", "role": "facade"}, {"file": "source/org/jfree/chart/plot/CompassPlot.java", "role": "H1"}, {"file": SD, "role": "H2"}, {"file": PU, "role": "H3 definer"}, {"file": PL, "role": "gold H4"}, {"file": SU, "role": "H5 loud terminal"}, {"file": PT, "role": "trigger (boolean)"}, {"file": PUT, "role": "definer unit test"}, {"file": PPT, "role": "suite"}],
       "trigger_only_test_patch": f"{PKG}/trigger_test.patch", "package_dir": PKG}
json.dump(cfg, open(f"{PKG}/attack.json", "w"), indent=1); print("built ADV-COMPOSITE-01:", os.path.getsize(f"{PKG}/variant.patch"), "B variant,", os.path.getsize(f"{PKG}/test.patch"), "B test")
