"""Main run Math-4__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static-facade
instance; fixed checkout of Defects4J Math-4, whose real bug modified geometry.euclidean.threed.SubLine and
geometry.euclidean.twod.SubLine). No static pair (BUILD_BRIEF_C10I_B8_NOTE section 1).

Facade: threed.SubLine.getSegments() (allowed instance target of BATCH8_PREREGISTRATION.md row 282, facade_planned_by null, no facade
reuse). The other two allowed targets were not used: twod.SubLine.split is called by every BSP-tree operation of the 2-D and 3-D
regions (PolygonsSet, PolyhedronsSet, OutlineExtractor), so any omission in its computation is caught by dozens of tests, not one;
twod.SubLine.intersection distinguishes its seven tests only by the (closed/open) x (INSIDE/BOUNDARY/OUTSIDE) pair of the two
sub-lines, which no one-line omission of a per-sub-line decision can split into a single failing test without treating one of the
two sub-lines differently from the other, and the parallel-lines case (testIntersectionParallel) is caught only by dropping the
null check of the crossing point, which is the real Defects4J Math-4 fault itself (avoided) and which every hop could pre-filter.
Original computation of the facade: the remaining region's intervals (remainingRegion.asList(), disjoint, increasing) are mapped,
one segment per interval, to Segment(line.toSpace(inf), line.toSpace(sup), line); an empty region gives an empty list (javadoc:
"If the sub-line is empty, the returned list will contain 0 segments").

facade_variant: V1 (state as parameters). state_passed: the private fields line (threed.Line) and remainingRegion
(oned.IntervalsSet), read inside SubLine and passed to hop 1; no field is written, no write-back. The facade body is one call to hop 1
(the original has no guard). No private method of SubLine is called (no V4); every type involved is public (no V3/V5); no visibility
is widened, no type added, no signature, modifier, override or throws change, no reflection, no test edit.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Math-4-probe of the fixture, the
first statement of each of the three allowed facades was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`;
defects4j compile OK; `defects4j test -t org.apache.commons.math3.geometry.euclidean.threed.SubLineTest::testEndPoints`,
`::testSeveralSegments` and `::testNoSegments`: each 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
threed.SubLine.getSegments(SubLine.java:82) called from SubLineTest (lines 36, 74 and the testNoSegments call). (Also reached:
twod.SubLine.intersection by twod.SubLineTest::testIntersectionParallel, twod.SubLine.split by PolygonsSetTest::testSimplyConnected.)
The chosen facade is reached directly by the trigger.

Hosts (host_mode = "1500"; `mr_lib.py preview Math-4 org/apache/commons/math3/geometry/euclidean/threed/SubLine.java 6`, seed 7879,
used in draw order; FastMathLiteralArrays is in the pool but marked unusable by the draw). Drawn host 4, linear.RealVector (1651 lines),
cannot carry the hop: UnmodifiableRealVectorAbstractTest::testAllButExcluded reflectively calls
every public method of RealVector.class.getMethods(), static ones included, with generated arguments, and throws
IllegalArgumentException("could not create class ...Line") for any parameter type other than int, double, double[], RealVector or
UnivariateFunction, so ANY new public static method with a Line parameter there fails existing tests in the correct configuration
(G1). It was therefore skipped and the next drawn host (drawn host 6, analysis.differentiation.DSCompiler) taken; the remaining hosts
keep their draw order:
  hop 1 optim.nonlinear.scalar.noderiv.BOBYQAOptimizer 2460 lines coveredSegments     plumbing: region -> its ordered interval list
  hop 2 optimization.direct.BOBYQAOptimizer            2465 lines segmentsOfIntervals aggregation (fold): the range the intervals
                                                                                      span (min of lower bounds, max of upper
                                                                                      bounds; no interval -> +inf .. -inf) and the
                                                                                      gaps between consecutive intervals
  hop 3 dfp.Dfp                                         2883 lines segmentsWithin      pass-through
  hop 4 util.FastMath                                   3883 lines segmentList         aggregation: creates the result list
  hop 5 analysis.differentiation.DSCompiler             1781 lines addSegments         GOLD: walks the range [lower, upper] across
                                                                                      the gaps, adding one segment per piece
Host newline counts 2460, 2465, 2883, 3883, 1781; the smallest host is DSCompiler (1781 lines), which is also the gold host.
Anchors (stageB_lib.pick_anchor, seed 7879 + 100 + i, as mr3_spec.py inserts them): hop 1 after the BOBYQAOptimizer constructor
(seed 7979), hop 2 after the BOBYQAOptimizer constructor (seed 7980), hop 3 after linearCombination (seed 7981), hop 4 after asin
(seed 7982), hop 5 after cosh (seed 7983).

Redistribution of the computation: hop 2 folds the interval list into the range it spans and the list of gaps; the gold rebuilds the
segments from them: from the range's lower bound to the first gap's lower bound, from each gap's upper bound to the next gap's lower
bound, and from the last gap's upper bound to the range's upper bound, each as Segment(line.pointAt(a), line.pointAt(b), line)
(line.toSpace(new Vector1D(x)) is line.pointAt(x)). The correct configuration returns exactly the original list on every test input
(checked on the six regions of threed.SubLineTest and on 19253 random IntervalsSets built by union/difference/xor of up to five
intervals: identical segment lists, except the 134 regions whose asList() itself yields an interval with inf > sup, for which the
original emits a backward segment and the chain none). No test builds such a region.

Fault (one-line omission of a special-case step in the gold): the gold's empty-range guard `if (lower > upper) { return; }` is
dropped, so the gold always adds the final piece. Hop 2 gives an empty interval list the range from +inf down to -inf (the identity
of its min/max fold, the same convention as IntervalsSet.getInf()/getSup(), which return +inf / -inf for an empty set), so on an
empty region the variant adds Segment(pointAt(+inf), pointAt(-inf)). Trigger: the EXISTING test
threed.SubLineTest::testNoSegments (a SubLine whose region is the complement of the whole line) fails with
assertEquals(0, segments.size()): expected:<0> but was:<1>. It is the only test that passes an empty region to threed
getSegments (the other five threed.SubLineTest getSegments tests have one or two intervals and are unaffected), getSegments of the
threed SubLine has no production caller, and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the segments that cover "the interval [lower, upper] of the line's abscissae", less
the gaps) and is silent on an empty range; for lower = +inf > upper = -inf the interval [lower, upper] holds no abscissa (hop 2's
javadoc says so explicitly for the range of no interval), so adding a segment violates the contract on the trigger input. Pinned
outside the gold: the intact sibling twod.SubLine.getSegments (an empty region gives no segment; its test
twod.SubLineTest::testNoSegments passes), IntervalsSet.getInf/getSup (documented: +inf / -inf "if the instance is empty") and
IntervalsSet.asList ("An empty tree will build an empty list"); passing tests through the chain: threed.SubLineTest::
testSeveralSegments (two intervals, one gap), ::testHalfInfinitePos (an unbounded upper end), ::testEndPoints (one bounded interval).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, guard, cursor loop over the gaps, final piece):
  T1 absent: line maps every bound to a point and is stored in every segment; lower starts the walk (and the guard); upper ends the
     final piece (and the guard); gaps drive the loop and supply both bounds of each gap; segments receives every piece.
  T2 absent: from is initialised from a parameter and reassigned in the loop (it advances to each gap's upper bound); the guard has a
     different effect (no piece) from the fall-through; no dead or frozen local.
  T3 absent: both ends of the range (lower, upper) and both bounds of each gap (getInf, getSup) are used; no enumeration; no class
     named in the text is handled in part.
  T4 absent: 'cover ... the interval [lower, upper] ... less some gaps', 'Each segment runs from the start of the range or the end of
     a gap to the start of the next gap or the end of the range' and 'added in increasing abscissa order' are met by lines of the body;
     the @param clauses are caller descriptions.
 Variant gold (the same without the guard):
  T1 absent: line, lower (initial from), upper (end of the final piece), gaps (loop and both gap bounds) and segments (every add) each
     change the result; none is only argument-checked.
  T2 absent: from advances in the loop; the pieces it bounds are added; no if/else, switch or ternary remains; no literal-initialised
     local; no dead local.
  T3 absent: lower and upper are both segment ends; getInf and getSup of each gap are both used; the gold has no emptiness or ordering
     treatment at all ('No member handled'); no special value of double is named.
  T4 absent: the text names no case, limit or value class that the body visibly misses: '[lower, upper]' and 'less some gaps' are the
     general description that the walk addresses; 'the gaps lie inside it, in increasing order' is a caller precondition; 'Each
     segment runs from ... to ...' and 'in increasing abscissa order' are met; no inline comment; identifiers (from, gap, segments)
     name nothing the body does not do.

Single owner: only the gold turns the range and the gaps into segments, and in the variant it adds at least one segment for every
input, so no input that a caller hands it, and no one-line change to how hops 1-4 compute or pass the range, the gaps or the list,
gives an empty result; 0 segments can only come from not calling the gold or from discarding what it added. Hop 2 documents and
implements the range of no interval as +inf .. -inf, "which holds no abscissa"; hops 1, 3 and 4 only pass values along or create the
list. Declared alternatives (G9): hop 2 starts an empty list's range at negative infinity; hop 3 passes the range with its bounds in
increasing order; hop 2 records only gaps of positive length. None makes the trigger pass.
Recorded bypasses (not competing repairs: each skips or rewrites the gold's result):
 B-0 the facade's original body (asList + one Segment per interval) discards the chain including the gold.
 B-1 a hop returns an empty list without calling down when the interval list is empty or lower > upper (for example hop 4:
     `if (lower > upper) { return segments; }` before the call): the gold is not used for that input.
 B-2 hop 4 (or a caller) removes from the list a segment whose start abscissa exceeds its end abscissa after the gold has added it.

Lie: the facade's javadoc claims the intervals are visited from the highest abscissa downwards and the list is put back in increasing
order before it is returned; no step of the chain visits the intervals downwards or reorders the list (hop 2 folds them in increasing
order and the gold adds the pieces in increasing order). It names neither the empty case nor any hop."""

SUB = "src/main/java/org/apache/commons/math3/geometry/euclidean/threed/SubLine.java"
H1 = "src/main/java/org/apache/commons/math3/optim/nonlinear/scalar/noderiv/BOBYQAOptimizer.java"
H2 = "src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java"
H3 = "src/main/java/org/apache/commons/math3/dfp/Dfp.java"
H4 = "src/main/java/org/apache/commons/math3/util/FastMath.java"
H5 = "src/main/java/org/apache/commons/math3/analysis/differentiation/DSCompiler.java"

GOLD_TEXT = '''/**
 * Adds the segments of a line that cover an abscissa range, less some gaps,
 * to a list.
 * <p>
 * The range is the interval [lower, upper] of the line's abscissae, and the
 * gaps lie inside it, in increasing order. Each segment runs from the start
 * of the range or the end of a gap to the start of the next gap or the end
 * of the range; the segments are added in increasing abscissa order.
 * </p>
 * @param line line holding the segments
 * @param lower lower bound of the range
 * @param upper upper bound of the range
 * @param gaps gaps to leave out of the range, in increasing order
 * @param segments list to which the segments are added
 */
public static void addSegments(final Line line, final double lower, final double upper,
                               final List<Interval> gaps, final List<Segment> segments) {
    if (lower > upper) {
        return;
    }
    double from = lower;
    for (final Interval gap : gaps) {
        segments.add(new Segment(line.pointAt(from), line.pointAt(gap.getInf()), line));
        from = gap.getSup();
    }
    segments.add(new Segment(line.pointAt(from), line.pointAt(upper), line));
}'''

HOP1 = '''/**
 * Gets the segments of a line covered by a region of its abscissae.
 *
 * @param line Line holding the segments.
 * @param region Region of the line's abscissae.
 * @return the segments of the line covered by the region, in increasing
 * abscissa order.
 */
public static List<Segment> coveredSegments(final Line line, final IntervalsSet region) {
    return org.apache.commons.math3.optimization.direct.BOBYQAOptimizer.segmentsOfIntervals(line, region.asList());
}'''

HOP2 = '''/**
 * Gets the segments of a line covered by a list of intervals of its
 * abscissae.
 * <p>
 * The intervals are disjoint and given in increasing order. They are
 * replaced by the range they span, from the lowest lower bound to the
 * highest upper bound, and by the gaps between consecutive intervals. A
 * list without intervals spans the range from positive infinity down to
 * negative infinity, which holds no abscissa.
 * </p>
 *
 * @param line Line holding the segments.
 * @param intervals Disjoint intervals of the line's abscissae, in
 * increasing order.
 * @return the segments of the line covered by the intervals, in increasing
 * abscissa order.
 */
public static List<Segment> segmentsOfIntervals(final Line line, final List<Interval> intervals) {
    double lower = Double.POSITIVE_INFINITY;
    double upper = Double.NEGATIVE_INFINITY;
    final List<Interval> gaps = new ArrayList<Interval>();
    for (int i = 0; i < intervals.size(); i++) {
        final Interval interval = intervals.get(i);
        if (i > 0) {
            gaps.add(new Interval(intervals.get(i - 1).getSup(), interval.getInf()));
        }
        lower = FastMath.min(lower, interval.getInf());
        upper = FastMath.max(upper, interval.getSup());
    }
    return Dfp.segmentsWithin(line, lower, upper, gaps);
}'''

HOP3 = '''/** Get the segments of a line covering an abscissa range, less some gaps.
 * @param line line holding the segments
 * @param lower lower bound of the range
 * @param upper upper bound of the range
 * @param gaps gaps to leave out of the range, in increasing order
 * @return the segments covering the range [lower, upper] less the gaps,
 * in increasing abscissa order
 */
public static List<Segment> segmentsWithin(final Line line, final double lower, final double upper,
                                           final List<Interval> gaps) {
    return FastMath.segmentList(line, lower, upper, gaps);
}'''

HOP4 = '''/**
 * Creates the list of the segments of a line covering an abscissa range,
 * less some gaps.
 *
 * @param line Line holding the segments.
 * @param lower Lower bound of the range.
 * @param upper Upper bound of the range.
 * @param gaps Gaps to leave out of the range, in increasing order.
 * @return a new list holding the segments, in increasing abscissa order.
 */
public static List<Segment> segmentList(final Line line, final double lower, final double upper,
                                        final List<Interval> gaps) {
    final List<Segment> segments = new ArrayList<Segment>();
    DSCompiler.addSegments(line, lower, upper, gaps, segments);
    return segments;
}'''

DESIGN = {
 "instance": "Math-4", "project": "Math", "bug_id": 4, "seed": 7879,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private fields line (threed.Line) and remainingRegion (oned.IntervalsSet), passed to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [2460, 2465, 2883, 3883, 1781],
 "reachability_probe": "getSegments() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-4-probe: threed.SubLineTest::testEndPoints, ::testSeveralSegments and "
                       "::testNoSegments each fail with PROBE-REACHED at threed.SubLine.getSegments(SubLine.java:82)",
 "facade": {"file": SUB, "class": "org.apache.commons.math3.geometry.euclidean.threed.SubLine", "method": "getSegments",
            "near_line": 81},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/math3/geometry/euclidean/threed/SubLineTest.java",
             "test_class": "org.apache.commons.math3.geometry.euclidean.threed.SubLineTest", "test_method": "testNoSegments"},
 "expected_signature": "expected:<0> but was:<1>",
 "gold": {"method": "addSegments", "text": GOLD_TEXT,
          "fault": {"old": "        if (lower > upper) {\n            return;\n        }\n        double from = lower;",
                    "new": "        double from = lower;"}},
 "chain": {
   "facade_body": "return org.apache.commons.math3.optim.nonlinear.scalar.noderiv.BOBYQAOptimizer.coveredSegments(line, "
                  "remainingRegion);",
   "lie": "The intervals are visited from the highest abscissa downwards, and the list is put back in increasing order before "
          "it is returned.",
   "hops": [
     {"file": H1, "class": "org.apache.commons.math3.optim.nonlinear.scalar.noderiv.BOBYQAOptimizer", "method": "coveredSegments",
      "imports": ["java.util.List", "org.apache.commons.math3.geometry.euclidean.oned.IntervalsSet",
                  "org.apache.commons.math3.geometry.euclidean.threed.Line",
                  "org.apache.commons.math3.geometry.euclidean.threed.Segment"], "text": HOP1},
     {"file": H2, "class": "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer", "method": "segmentsOfIntervals",
      "imports": ["java.util.ArrayList", "java.util.List", "org.apache.commons.math3.dfp.Dfp",
                  "org.apache.commons.math3.geometry.euclidean.oned.Interval",
                  "org.apache.commons.math3.geometry.euclidean.threed.Line",
                  "org.apache.commons.math3.geometry.euclidean.threed.Segment",
                  "org.apache.commons.math3.util.FastMath"], "text": HOP2},
     {"file": H3, "class": "org.apache.commons.math3.dfp.Dfp", "method": "segmentsWithin",
      "imports": ["java.util.List", "org.apache.commons.math3.geometry.euclidean.oned.Interval",
                  "org.apache.commons.math3.geometry.euclidean.threed.Line",
                  "org.apache.commons.math3.geometry.euclidean.threed.Segment",
                  "org.apache.commons.math3.util.FastMath"], "text": HOP3},
     {"file": H4, "class": "org.apache.commons.math3.util.FastMath", "method": "segmentList",
      "imports": ["java.util.ArrayList", "java.util.List", "org.apache.commons.math3.analysis.differentiation.DSCompiler",
                  "org.apache.commons.math3.geometry.euclidean.oned.Interval",
                  "org.apache.commons.math3.geometry.euclidean.threed.Line",
                  "org.apache.commons.math3.geometry.euclidean.threed.Segment"], "text": HOP4},
     {"file": H5, "class": "org.apache.commons.math3.analysis.differentiation.DSCompiler", "method": "addSegments",
      "imports": ["java.util.List", "org.apache.commons.math3.geometry.euclidean.oned.Interval",
                  "org.apache.commons.math3.geometry.euclidean.threed.Line",
                  "org.apache.commons.math3.geometry.euclidean.threed.Segment"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.geometry.euclidean.twod.SubLine::getSegments",
              "org.apache.commons.math3.geometry.euclidean.oned.IntervalsSet::getInf",
              "org.apache.commons.math3.geometry.euclidean.oned.IntervalsSet::getSup",
              "org.apache.commons.math3.geometry.euclidean.oned.IntervalsSet::asList"],
 "ownership_reason": "Only the gold turns the abscissa range and the gaps into segments: hop 1 passes the region's ordered "
                     "interval list, hop 2 folds it into the range the intervals span (the lowest lower bound to the highest "
                     "upper bound; for no interval the range from positive infinity down to negative infinity, 'which holds no "
                     "abscissa', as its javadoc says) and the gaps between consecutive intervals, hop 3 passes them on and hop 4 "
                     "creates the list the gold fills. The gold's javadoc promises the segments covering 'the interval [lower, "
                     "upper]' less the gaps; on the trigger input that interval is empty (+inf .. -inf), yet the variant adds a "
                     "segment from pointAt(+inf) to pointAt(-inf), and since it adds at least one segment for every input, no "
                     "caller can obtain 0 segments from it except by not calling it or by discarding its result. The convention "
                     "is pinned outside the gold: the intact sibling twod.SubLine.getSegments gives no segment for an empty "
                     "region (twod.SubLineTest::testNoSegments passes), IntervalsSet.getInf/getSup document +inf / -inf for an "
                     "empty set and IntervalsSet.asList an empty list; through the chain, threed.SubLineTest::testSeveralSegments "
                     "(one gap), ::testHalfInfinitePos (an unbounded upper end) and ::testEndPoints pass.",
 "ownership_tests": ["org.apache.commons.math3.geometry.euclidean.twod.SubLineTest::testNoSegments",
                     "org.apache.commons.math3.geometry.euclidean.threed.SubLineTest::testSeveralSegments",
                     "org.apache.commons.math3.geometry.euclidean.threed.SubLineTest::testHalfInfinitePos",
                     "org.apache.commons.math3.geometry.euclidean.threed.SubLineTest::testEndPoints"],
 "compensating": {
   "chain": [
     {"file": H2, "old": "double lower = Double.POSITIVE_INFINITY;",
      "new": "double lower = intervals.isEmpty() ? Double.NEGATIVE_INFINITY : Double.POSITIVE_INFINITY;",
      "why": "hop 2 starts the range of an empty list at negative infinity"},
     {"file": H3, "old": "return FastMath.segmentList(line, lower, upper, gaps);",
      "new": "return FastMath.segmentList(line, FastMath.min(lower, upper), FastMath.max(lower, upper), gaps);",
      "why": "hop 3 passes the range with its bounds in increasing order"},
     {"file": H2, "old": "if (i > 0) {\n                gaps.add(new Interval(",
      "new": "if (i > 0 && intervals.get(i - 1).getSup() < interval.getInf()) {\n                gaps.add(new Interval(",
      "why": "hop 2 records only gaps of positive length"},
   ],
 },
 "host_notes": "host_mode 1500: hosts from `mr_lib.py preview Math-4 org/apache/commons/math3/geometry/euclidean/threed/"
               "SubLine.java 6` with the instance seed 7879, in draw order: optim.nonlinear.scalar.noderiv.BOBYQAOptimizer (hop 1, "
               "2460 lines), optimization.direct.BOBYQAOptimizer (hop 2, 2465), dfp.Dfp (hop 3, 2883), util.FastMath (hop 4, 3883; "
               "drawn host 5), analysis.differentiation.DSCompiler (hop 5, gold, 1781; drawn host 6; the smallest host). Drawn host "
               "4, linear.RealVector (1651), was skipped as unusable: UnmodifiableRealVectorAbstractTest::testAllButExcluded calls "
               "every public method of RealVector.class.getMethods() (static ones included) with generated arguments and throws "
               "IllegalArgumentException for a Line parameter, so a public static hop there fails existing tests even in the "
               "correct configuration. FastMathLiteralArrays (6176 lines) is in the pool but marked unusable by the draw. Neither "
               "SubLine file is a host. Anchors (seed 7879 + 100 + i): hop 1 after the BOBYQAOptimizer constructor, hop 2 after "
               "the BOBYQAOptimizer constructor, hop 3 after linearCombination, hop 4 after asin, hop 5 after cosh. Hops 1 and 2 "
               "are both named BOBYQAOptimizer, so the facade calls hop 1 and hop 1 calls hop 2 by fully-qualified name; each hop "
               "imports java.util types, threed.Line, threed.Segment, oned.Interval / IntervalsSet and the next host as needed "
               "(Dfp already imports util.FastMath, DSCompiler already imports java.util.List and ArrayList).",
}
