"""Main-run instance Chart-11 (C10 recipe on the fixed checkout of Defects4J Chart-11; target class ShapeUtilities, the class the
real bug modified). Facade = ShapeUtilities.equal(GeneralPath, GeneralPath), the 32-line pool candidate (the method the real bug
lived in). The other equal overloads were set aside: every assertFalse on two Line2D, Ellipse2D or Arc2D values in the suite
differs in all compared values (no omission is caught by exactly one test), and the Polygon block of testEqualShapes differs only
in xpoints[0], which no special-case step of a per-vertex comparison can let through.

The facade keeps its argument guard (the two null checks) and delegates the comparison of the two paths' iterators to a five-hop
chain drawn with the instance seed 7454 (mr_lib preview, n=5, draw order, no substitution):
  hop 1 axis.SegmentedTimeline.matchesSegmentRun            decision: the winding rules of the two iterators must agree
  hop 2 plot.SpiderWebPlot.outlinesMatch                    fold: walks both iterators in step (the original loop: both done ->
                                                            equal, one done -> unequal, any unequal pair -> unequal)
  hop 3 renderer.category.AbstractCategoryItemRenderer.itemStepsMatch   pass-through for the current pair of segments
  hop 4 plot.XYPlot.pathStepsMatch                          pass-through for the current pair of segments
  hop 5 ChartFactory.segmentsMatch                          GOLD: the per-segment comparison: reads the current segment of each
                                                            iterator, compares the segment types, and compares the coordinates
                                                            the segment type uses (move/line 2, cubic 6, quadratic 4, close 0)
The chain performs the original computation in the original order (null guard, winding rule, lock-step walk with the same
end-of-path rules, type then coordinates per segment). The original compared all six slots of two shared arrays; once the earlier
segments and the current types agree, the unused slots of both arrays hold the same values, so comparing the used coordinates is
the same verdict (correct configuration behaviour-preserving for every caller: LegendItem, LegendGraphic and the renderers' equals,
the XYAreaRenderer/XYAreaRenderer2 GeneralPath legend area through cloning and SerialUtilities round trips).

Fault (omission in the gold, special-case step): the quadratic-segment case of the coordinate count is dropped, so a SEG_QUADTO
segment falls through with no coordinates compared; two quadratic segments with different control and end points compare equal.
The gold still reads as an ordinary routine for ordinary input (move, line, cubic and close segments: every chart legend shape in
the library). Trigger: the EXISTING test ShapeUtilitiesTests::testEqualGeneralPaths, whose quadTo block (line 236: quadTo(11, 22,
33, 44) against quadTo(1, 2, 3, 4)) expects false and gets true; the earlier blocks (move, line, cubic) still fail as expected.
It is the only test that compares two different GeneralPaths: testEqualShapes and the renderer equals/cloning/serialization tests
compare equal paths (the omission only makes the comparison more lenient), and no production shape uses quadTo.

The gold's javadoc states the contract (equal segments = same segment type and same coordinates) and is silent on how many
coordinates each type carries. External pins: SerialUtilities.readShape rebuilds a SEG_QUADTO segment from four coordinates
(quadTo(args[0..3])) next to move/line (2) and cubic (6); SerialUtilities.writeShape writes the type and the coordinates of every
segment; the sibling equal overloads compare every defining value of their shape (Line2D both points, Arc2D frame, angles and
type, Polygon both coordinate arrays). Passing tests: testEqualShapes (a path with a quadratic segment equals its copy),
testEqualLine2Ds, XYAreaRendererTests::testSerialization (a GeneralPath round trip through read/writeShape compares equal).

Single owner: only the gold reads segment coordinates; hops 1-4 hold nothing but the two iterators, and a one-line edit there
cannot compare coordinates (it would need the two coordinate arrays and a comparison, a second implementation of the gold).
Declared alternatives (G9): hop 4 compares the segment types before delegating (types agree on the trigger), hop 2 ends the walk
when either iterator ends (the quadratic pair is still reported equal), hop 3 refuses quadratic segments (identical paths become
unequal, first block and testEqualShapes fail).

Recorded bypasses (not declared, they pass the trigger and the suite; the builder applied B-0 in its bounds form and B-1 in its
hop 1 form to a scratch copy of the variant: each passes the trigger and the full suite with 0 failing tests):
 B-0 facade pre-check on the bounds, e.g. `if (!p1.getBounds2D().equals(p2.getBounds2D())) { return false; }` before the
     delegation (or the same with new java.awt.geom.Area(p1).equals(new Area(p2))): a second, partial equality test that decides
     the trigger's quadratic block before the chain runs; the gold still reports two quadratic segments with different
     coordinates as equal whenever the bounds agree, so its documented contract stays violated.
 B-1 flattening at the facade or hop 1, e.g. hop 1 delegating with
     `new java.awt.geom.FlatteningPathIterator(iterator1, 1.0), new java.awt.geom.FlatteningPathIterator(iterator2, 1.0)`:
     quadratic and cubic segments never reach the gold (its curve branches become dead) and two paths with different segments
     (a curve and its line approximation) compare equal, against hop 1's own javadoc.
 B-2 the facade restoring the pre-chain body (multi-line), which makes all five hops dead.

Lie: the facade's javadoc claims both paths are copied into point lists read from the last segment back to the first and compared
with one equals() call; the code walks the segments forward and compares type and coordinates pair by pair. It names neither the
quadratic segment nor the coordinate count nor any hop."""

SU = "source/org/jfree/chart/util/ShapeUtilities.java"
STL = "source/org/jfree/chart/axis/SegmentedTimeline.java"
SWP = "source/org/jfree/chart/plot/SpiderWebPlot.java"
ACIR = "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java"
XYP = "source/org/jfree/chart/plot/XYPlot.java"
CF = "source/org/jfree/chart/ChartFactory.java"

PARAMS = ''' * @param iterator1  the first iterator (<code>null</code> not permitted).
 * @param iterator2  the second iterator (<code>null</code> not permitted).
 *
 * @return A boolean.
 */'''

GOLD_TEXT = '''/**
 * Returns <code>true</code> if the current segments of two path iterators
 * are equal, that is, if they have the same segment type and the same
 * coordinates, and <code>false</code> otherwise.
 *
''' + PARAMS + '''
public static boolean segmentsMatch(PathIterator iterator1,
        PathIterator iterator2) {
    double[] coords1 = new double[6];
    double[] coords2 = new double[6];
    int type = iterator1.currentSegment(coords1);
    if (iterator2.currentSegment(coords2) != type) {
        return false;
    }
    int count = 0;
    if (type == PathIterator.SEG_MOVETO
            || type == PathIterator.SEG_LINETO) {
        count = 2;
    }
    else if (type == PathIterator.SEG_CUBICTO) {
        count = 6;
    }
    else if (type == PathIterator.SEG_QUADTO) {
        count = 4;
    }
    for (int i = 0; i < count; i++) {
        if (coords1[i] != coords2[i]) {
            return false;
        }
    }
    return true;
}'''

STEP_DOC = '''/**
 * Returns <code>true</code> if the current segments of two path iterators
 * are equal, and <code>false</code> otherwise.
 *
''' + PARAMS

DESIGN = {
 "instance": "Chart-11", "project": "Chart", "bug_id": 11, "seed": 7454,
 "src_root": "source", "test_root": "tests",
 "facade": {"file": SU, "class": "org.jfree.chart.util.ShapeUtilities", "method": "equal", "near_line": 264},
 "trigger": {"existing": True, "test_file": "tests/org/jfree/chart/util/junit/ShapeUtilitiesTests.java",
             "test_class": "org.jfree.chart.util.junit.ShapeUtilitiesTests", "test_method": "testEqualGeneralPaths"},
 "expected_signature": "ShapeUtilitiesTests.java:236",
 "gold": {"method": "segmentsMatch", "text": GOLD_TEXT,
          "fault": {"old": "        else if (type == PathIterator.SEG_CUBICTO) {\n            count = 6;\n        }\n"
                           "        else if (type == PathIterator.SEG_QUADTO) {\n            count = 4;\n        }",
                    "new": "        else if (type == PathIterator.SEG_CUBICTO) {\n            count = 6;\n        }"}},
 "chain": {
   "facade_body": "if (p1 == null) {\n            return (p2 == null);\n        }\n"
                  "        if (p2 == null) {\n            return false;\n        }\n"
                  "        return org.jfree.chart.axis.SegmentedTimeline.matchesSegmentRun(\n"
                  "                p1.getPathIterator(null), p2.getPathIterator(null));",
   "lie": "Each path is first copied into a list of its points, read from the last segment back to the first, and the two "
          "lists are then compared with a single call to <code>equals()</code>.",
   "hops": [
     {"file": STL, "class": "org.jfree.chart.axis.SegmentedTimeline", "method": "matchesSegmentRun",
      "imports": ["java.awt.geom.PathIterator", "org.jfree.chart.plot.SpiderWebPlot"],
      "text": '''/**
 * Returns <code>true</code> if two path iterators have the same winding
 * rule and deliver the same sequence of segments, and <code>false</code>
 * otherwise.
 *
''' + PARAMS + '''
public static boolean matchesSegmentRun(PathIterator iterator1,
        PathIterator iterator2) {
    if (iterator1.getWindingRule() != iterator2.getWindingRule()) {
        return false;
    }
    return SpiderWebPlot.outlinesMatch(iterator1, iterator2);
}'''},
     {"file": SWP, "class": "org.jfree.chart.plot.SpiderWebPlot", "method": "outlinesMatch",
      "imports": ["java.awt.geom.PathIterator", "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer"],
      "text": '''/**
 * Returns <code>true</code> if two path iterators deliver equal segments
 * in the same order and come to their end together, and
 * <code>false</code> otherwise.  The iterators are advanced as the
 * segments are compared.
 *
''' + PARAMS + '''
public static boolean outlinesMatch(PathIterator iterator1,
        PathIterator iterator2) {
    boolean done = iterator1.isDone() && iterator2.isDone();
    while (!done) {
        if (iterator1.isDone() != iterator2.isDone()) {
            return false;
        }
        if (!AbstractCategoryItemRenderer.itemStepsMatch(iterator1,
                iterator2)) {
            return false;
        }
        iterator1.next();
        iterator2.next();
        done = iterator1.isDone() && iterator2.isDone();
    }
    return true;
}'''},
     {"file": ACIR, "class": "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer", "method": "itemStepsMatch",
      "imports": ["java.awt.geom.PathIterator", "org.jfree.chart.plot.XYPlot"],
      "text": STEP_DOC + '''
public static boolean itemStepsMatch(PathIterator iterator1,
        PathIterator iterator2) {
    return XYPlot.pathStepsMatch(iterator1, iterator2);
}'''},
     {"file": XYP, "class": "org.jfree.chart.plot.XYPlot", "method": "pathStepsMatch",
      "imports": ["java.awt.geom.PathIterator", "org.jfree.chart.ChartFactory"],
      "text": STEP_DOC + '''
public static boolean pathStepsMatch(PathIterator iterator1,
        PathIterator iterator2) {
    return ChartFactory.segmentsMatch(iterator1, iterator2);
}'''},
     {"file": CF, "class": "org.jfree.chart.ChartFactory", "method": "segmentsMatch",
      "imports": ["java.awt.geom.PathIterator"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.chart.util.SerialUtilities::readShape", "org.jfree.chart.util.SerialUtilities::writeShape",
              "org.jfree.chart.util.ShapeUtilities::equal"],
 "ownership_reason": "Only the per-segment comparison reads the coordinates of a segment; the facade, the winding-rule check, "
                     "the lock-step walk and the two pass-throughs hold nothing but the two path iterators, so none of them "
                     "can bring the coordinates of a quadratic segment into the verdict with a one-line change. The number of "
                     "coordinates each segment type carries is fixed outside the gold: SerialUtilities.readShape rebuilds a "
                     "SEG_QUADTO segment from four coordinates (quadTo(args[0], args[1], args[2], args[3])) beside move/line "
                     "(two) and cubic (six), and writeShape writes every segment's coordinates; the sibling equal overloads "
                     "compare every defining value of their shapes (both end points of a Line2D, frame, angles and type of an "
                     "Arc2D, both coordinate arrays of a Polygon). The gold's javadoc promises that equal segments have the "
                     "same coordinates, which two quadratic segments with different points violate.",
 "ownership_tests": ["org.jfree.chart.util.junit.ShapeUtilitiesTests::testEqualShapes",
                     "org.jfree.chart.util.junit.ShapeUtilitiesTests::testEqualLine2Ds",
                     "org.jfree.chart.renderer.xy.junit.XYAreaRendererTests::testSerialization"],
 "compensating": {
   "chain": [
     {"file": XYP, "old": "        return ChartFactory.segmentsMatch(iterator1, iterator2);",
      "new": "        return iterator1.currentSegment(new double[6]) == iterator2.currentSegment(new double[6]) && ChartFactory.segmentsMatch(iterator1, iterator2);",
      "why": "hop 4 compares the segment types before delegating"},
     {"file": SWP, "old": "            done = iterator1.isDone() && iterator2.isDone();",
      "new": "            done = iterator1.isDone() || iterator2.isDone();",
      "why": "hop 2 ends the walk as soon as either iterator ends"},
     {"file": ACIR, "old": "        return XYPlot.pathStepsMatch(iterator1, iterator2);",
      "new": "        return iterator1.currentSegment(new double[6]) != PathIterator.SEG_QUADTO && XYPlot.pathStepsMatch(iterator1, iterator2);",
      "why": "hop 3 refuses quadratic segments"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 7454 (mr_lib preview, n=5, target org/jfree/chart/util/ShapeUtilities.java): "
               "axis.SegmentedTimeline (hop 1), plot.SpiderWebPlot (hop 2), renderer.category.AbstractCategoryItemRenderer "
               "(hop 3), plot.XYPlot (hop 4), ChartFactory (hop 5, gold). All five are public classes in which a static method "
               "compiles (AbstractCategoryItemRenderer is abstract, which does not matter for a static method); none was "
               "skipped. Every hop imports java.awt.geom.PathIterator; hops 2 and 4 share the package org.jfree.chart.plot. "
               "The facade calls hop 1 by its fully-qualified name, so ShapeUtilities gains no import.",
}
