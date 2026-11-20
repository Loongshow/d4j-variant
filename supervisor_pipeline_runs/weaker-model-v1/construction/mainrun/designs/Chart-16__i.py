"""Main run Chart-16__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade; the
fixed checkout of Defects4J Chart-16, fixed revision 743; the real bug modified DefaultIntervalCategoryDataset, the facade's class).
No static pair exists (pool v2: no_tested_static), so addendum section 2 has nothing to refer to.

Facade: DefaultIntervalCategoryDataset.getSeriesIndex(Comparable) (instance method; allowed targets getSeriesIndex / getCategoryIndex /
getColumnKeys, BATCH8_PREREGISTRATION.md row 213; facade_planned_by null for all three; no facade reuse). getColumnKeys was not used: the
only test that reaches it reads the key list of an empty dataset (testGetColumnKeys), and no quiet one-line omission in a list copy changes
the empty list. getCategoryIndex is the same scan over the category keys; it stays intact and is the sibling pin below.
Original computation: result = -1; a scan over the private field seriesKeys from the first key; the first key equal to seriesKey
(seriesKey.equals(key)) gives its index and ends the scan; result is returned (-1 when no key is equal, including an empty dataset).

facade_variant: V1 (state as parameters). state_passed: the private field seriesKeys (Comparable[]) and the parameter seriesKey, handed to
hop 1; no field is written, no write-back. The facade body is one call to hop 1 (the original has no guard). The computation calls no
method of the receiver and no private helper (no V2/V4), and no package-private type is involved (no V3/V5). No visibility is widened, no
type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Chart-16-probe-getSeriesIndex of the fixture, the first
statement of getSeriesIndex was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; full suite
(defects4j test): 5 failing tests, each java.lang.IllegalStateException: PROBE-REACHED at
DefaultIntervalCategoryDataset.getSeriesIndex(DefaultIntervalCategoryDataset.java:241): DefaultIntervalCategoryDatasetTests::testGetValue,
::testSetStartValue, ::testSetEndValue, ::testGetSeriesIndex, ::testGetRowIndex. (The same probe on getCategoryIndex: 6 tests, all in
DefaultIntervalCategoryDatasetTests; on getColumnKeys: 1 test, testGetColumnKeys.) The facade is reached by existing tests, directly and
through getValue/getStartValue/getEndValue(Comparable, Comparable) and getRowIndex.

Hosts (host_mode = "1500"; `mr_lib.py preview Chart-16 org/jfree/data/category/DefaultIntervalCategoryDataset.java 5`, seed 3208, used
in draw order, none substituted):
  hop 1 chart.axis.ValueAxis                        1659 lines  findKeyIndex      pass-through (documents the -1 convention)
  hop 2 chart.plot.CategoryPlot                     3941 lines  indexOfKey        pass-through
  hop 3 chart.plot.XYPlot                           4951 lines  getKeyIndex       pass-through
  hop 4 chart.renderer.xy.AbstractXYItemRenderer    1753 lines  resolveKeyIndex   pass-through
  hop 5 chart.axis.SegmentedTimeline                1763 lines  positionOfKey     GOLD: the scan over the keys, the per-key comparison and
                                                                                  the decision for a scan that ends without an equal key
Host newline counts 1659, 3941, 4951, 1753, 1763; the smallest host is ValueAxis (1659 lines); the gold host has 1763 lines.
The correct configuration returns the original result for every input: the gold advances index from -1 one key at a time while no key
has been equal and keys remain, so it stops at the first equal key (found) or after the last key; a scan that ends without an equal key
resets index to -1; an empty array never enters the loop and returns -1. A null seriesKeys (a dataset created with null data) or a null
key fails with NullPointerException as in the original.

Fault (one-line omission of the not-found decision in the gold): `if (!found) { index = -1; }` is dropped, so a scan that ends without an
equal key returns the index of the last key it compared. The gold then reads as the ordinary routine "advance over the keys until one is
equal, return where the scan stopped". Empty arrays still give -1 and every key that is present still gives its own index. Trigger: the
EXISTING test DefaultIntervalCategoryDatasetTests::testGetValue. Its twelve value assertions (Series 1/2 x Category 1/2/3) still hold;
d.getValue("XX", "Category 1") no longer throws UnknownKeyException, because getSeriesIndex("XX") returns 1 (the last of the two series)
instead of -1 and getValue reads the end value of series 1, so assertTrue(pass) at DefaultIntervalCategoryDatasetTests.java:128 fails
(junit.framework.AssertionFailedError). It is the only test that looks up an absent series key in a dataset with series: testSetStartValue
and testSetEndValue look up "Series 1" (present, index 0), testGetSeriesIndex and testGetRowIndex look up "ABC" in an empty dataset (still
-1); the probe's full-suite run lists every test that reaches the facade, and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it returns the index of a key in an array of keys) and is silent on keys that are not
in the array. For "XX" the variant returns 1, which is not the index of "XX" in {"Series 1", "Series 2"}; the convention is pinned outside
the gold: hop 1's javadoc and the interface KeyedValues2D.getRowIndex ("The row index, or -1 if the key is unrecognised"), which
getRowIndex of the facade's class implements through the facade; the intact sibling DefaultIntervalCategoryDataset.getCategoryIndex (the
same scan over the category keys, -1 when no key is equal), KeyedObjects.getIndex (return -1 after the scan) and DefaultKeyedValues.getIndex
(return -1 // key not found), used in production by getColumnIndex/getValue/setStartValue/setEndValue and by KeyedObjects.getObject /
DefaultKeyedValues.setValue. Passing tests: DefaultIntervalCategoryDatasetTests::testGetSeriesIndex (through the chain: -1 for an empty
dataset), ::testGetCategoryIndex (the sibling), CategoryToPieDatasetTests::testGetIndex (-1 for "XX" among two present keys) and
DefaultKeyedValuesTests::testRemoveValue (-1 for a removed key among three present keys).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: keys bounds the loop and supplies every compared key; key is compared with each of them; neither is only argument-checked.
  T2 absent: index is advanced in the loop and returned; found is assigned in the loop, read by the loop condition and by the not-found
     decision; both literal initialisers are reassigned; the not-found decision changes the result when the loop ends after the last key.
  T3 absent: no closed set of cases; one comparison per key, applied to every key the scan reaches; no enum, type code or named format.
  T4 absent: 'Returns the index of a key in an array of keys' and '@return The index of the key' are general descriptions that the
     scan addresses; '(null not permitted)' are caller preconditions; no inline comment; identifiers index/found name what they hold.
 Variant gold (javadoc, signature, `int index = -1; boolean found = false; while (!found && index < keys.length - 1) { index++;
 found = key.equals(keys[index]); } return index;`):
  T1 absent: keys bounds the loop and supplies the compared keys; key is compared with each; both change the return value.
  T2 absent: index is the cursor, assigned (index++) inside the loop and returned; found is the flag, assigned inside the loop and read
     by the loop condition, which decides whether index advances (a live statement); neither literal-initialised local is left
     unassigned; there is no if/else, switch or ternary at all, so no dead decision.
  T3 absent: the gold has no case analysis and no not-found treatment at all ('No member handled'); every key the scan reaches gets the
     same comparison; its text names no class (no "present", "absent", "unrecognised", "-1") that it would handle in part.
  T4 absent: 'the index of a key in an array of keys' / 'The index of the key' are general descriptions addressed by the scan (like 'the
     index of the first match'); the @param clauses are caller preconditions; no inline comment; no identifier names a rule or value
     class the body does not meet.

Single owner: only the gold compares keys and decides what a scan without an equal key gives; hops 1-4 pass the array and the key along
unchanged and return the gold's result. Once the gold returns the index of the last key for an absent key, a caller cannot tell it from a
match at the last position without comparing that key again (a second implementation of the gold's per-key decision). Declared
alternatives (G9): hop 4 answers an empty array itself; hop 2 maps an index at or past the end of the array to -1; hop 3 answers a single
key itself. None makes the trigger pass (the absent key's result is 1, inside the array of two).
Recorded bypasses (edits that replace or re-derive the gold's result, not repairs of the chain):
 B-0 the facade's original body, or any hop returning java.util.Arrays.asList(keys).indexOf(key), discards the chain below it including
     the gold.
 B-1 a hop re-compares the key at the returned index (for example hop 4:
     `return keys.length > 0 && key.equals(keys[SegmentedTimeline.positionOfKey(keys, key)]) ? SegmentedTimeline.positionOfKey(keys, key) : -1;`):
     a second implementation of the gold's per-key comparison applied to its output.

Lie: the facade's javadoc claims the index is read from a hash table that maps each series key to its position and is rebuilt whenever
the series keys are replaced; the chain builds no table (one scan over the array on every call) and nothing is rebuilt by setSeriesKeys.
It names neither absent keys nor -1 nor any hop."""

DICD = "source/org/jfree/data/category/DefaultIntervalCategoryDataset.java"
VA = "source/org/jfree/chart/axis/ValueAxis.java"
CP = "source/org/jfree/chart/plot/CategoryPlot.java"
XYP = "source/org/jfree/chart/plot/XYPlot.java"
AXYR = "source/org/jfree/chart/renderer/xy/AbstractXYItemRenderer.java"
ST = "source/org/jfree/chart/axis/SegmentedTimeline.java"

GOLD_TEXT = '''/**
 * Returns the index of a key in an array of keys.
 *
 * @param keys  the keys (<code>null</code> not permitted).
 * @param key  the key (<code>null</code> not permitted).
 *
 * @return The index of the key.
 */
public static int positionOfKey(Comparable[] keys, Comparable key) {
    int index = -1;
    boolean found = false;
    while (!found && index < keys.length - 1) {
        index++;
        found = key.equals(keys[index]);
    }
    if (!found) {
        index = -1;
    }
    return index;
}'''

HOP1 = '''/**
 * Returns the index of a key in an array of keys.
 *
 * @param keys  the keys (<code>null</code> not permitted).
 * @param key  the key (<code>null</code> not permitted).
 *
 * @return The index of the key, or <code>-1</code> if the key is not
 *     recognised.
 */
public static int findKeyIndex(Comparable[] keys, Comparable key) {
    return CategoryPlot.indexOfKey(keys, key);
}'''

HOP2 = '''/**
 * Returns the index of a key in an array of keys.
 *
 * @param keys  the keys (<code>null</code> not permitted).
 * @param key  the key (<code>null</code> not permitted).
 *
 * @return The index.
 */
public static int indexOfKey(Comparable[] keys, Comparable key) {
    return XYPlot.getKeyIndex(keys, key);
}'''

HOP3 = '''/**
 * Returns the index of a key in an array of keys.
 *
 * @param keys  the keys (<code>null</code> not permitted).
 * @param key  the key (<code>null</code> not permitted).
 *
 * @return The index of the key.
 */
public static int getKeyIndex(Comparable[] keys, Comparable key) {
    return AbstractXYItemRenderer.resolveKeyIndex(keys, key);
}'''

HOP4 = '''/**
 * Returns the index of a key in an array of keys.
 *
 * @param keys  the keys (<code>null</code> not permitted).
 * @param key  the key (<code>null</code> not permitted).
 *
 * @return The index of the key.
 */
public static int resolveKeyIndex(Comparable[] keys, Comparable key) {
    return SegmentedTimeline.positionOfKey(keys, key);
}'''

DESIGN = {
 "instance": "Chart-16", "project": "Chart", "bug_id": 16, "seed": 3208,
 "src_root": "source", "test_root": "tests",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field seriesKeys (Comparable[]) and the parameter seriesKey, passed to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [1659, 3941, 4951, 1753, 1763],
 "reachability_probe": "getSeriesIndex first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Chart-16-probe-getSeriesIndex: full suite 5 failing tests (testGetValue, testSetStartValue, "
                       "testSetEndValue, testGetSeriesIndex, testGetRowIndex of DefaultIntervalCategoryDatasetTests), each with "
                       "PROBE-REACHED at DefaultIntervalCategoryDataset.getSeriesIndex(DefaultIntervalCategoryDataset.java:241)",
 "facade": {"file": DICD, "class": "org.jfree.data.category.DefaultIntervalCategoryDataset", "method": "getSeriesIndex",
            "near_line": 240},
 "trigger": {"existing": True, "test_file": "tests/org/jfree/data/category/junit/DefaultIntervalCategoryDatasetTests.java",
             "test_class": "org.jfree.data.category.junit.DefaultIntervalCategoryDatasetTests", "test_method": "testGetValue"},
 "expected_signature": "DefaultIntervalCategoryDatasetTests.testGetValue(DefaultIntervalCategoryDatasetTests.java:128)",
 "gold": {"method": "positionOfKey", "text": GOLD_TEXT,
          "fault": {"old": "            found = key.equals(keys[index]);\n"
                           "        }\n"
                           "        if (!found) {\n"
                           "            index = -1;\n"
                           "        }\n"
                           "        return index;",
                    "new": "            found = key.equals(keys[index]);\n"
                           "        }\n"
                           "        return index;"}},
 "chain": {
   "facade_body": "return org.jfree.chart.axis.ValueAxis.findKeyIndex(this.seriesKeys, seriesKey);",
   "lie": "The index is read from a hash table that maps each series key to its position, and the table is rebuilt whenever the "
          "series keys are replaced.",
   "hops": [
     {"file": VA, "class": "org.jfree.chart.axis.ValueAxis", "method": "findKeyIndex",
      "imports": ["org.jfree.chart.plot.CategoryPlot"], "text": HOP1},
     {"file": CP, "class": "org.jfree.chart.plot.CategoryPlot", "method": "indexOfKey", "imports": [], "text": HOP2},
     {"file": XYP, "class": "org.jfree.chart.plot.XYPlot", "method": "getKeyIndex",
      "imports": ["org.jfree.chart.renderer.xy.AbstractXYItemRenderer"], "text": HOP3},
     {"file": AXYR, "class": "org.jfree.chart.renderer.xy.AbstractXYItemRenderer", "method": "resolveKeyIndex",
      "imports": ["org.jfree.chart.axis.SegmentedTimeline"], "text": HOP4},
     {"file": ST, "class": "org.jfree.chart.axis.SegmentedTimeline", "method": "positionOfKey", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jfree.data.category.DefaultIntervalCategoryDataset::getCategoryIndex",
              "org.jfree.data.KeyedObjects::getIndex",
              "org.jfree.data.DefaultKeyedValues::getIndex",
              "org.jfree.data.KeyedValues2D::getRowIndex"],
 "ownership_reason": "Only the gold compares the key with the keys and decides what a scan that ends without an equal key gives; hops "
                     "1-4 pass the array and the key along unchanged and return the gold's result. The gold's javadoc promises the "
                     "index of the key in the array; for the absent key \"XX\" the variant returns 1, the index of \"Series 2\". A "
                     "caller cannot tell that result from a match at the last position without comparing the key at that index "
                     "again, a second implementation of the gold's per-key decision. The convention is pinned outside the gold: hop "
                     "1's javadoc and KeyedValues2D.getRowIndex ('The row index, or -1 if the key is unrecognised'), implemented by "
                     "the facade's class through getRowIndex -> getSeriesIndex; the intact sibling getCategoryIndex of the same class "
                     "(the same scan over the category keys, -1 when no key is equal, used by getColumnIndex, getValue, "
                     "setStartValue and setEndValue), KeyedObjects.getIndex (return -1 after the scan) and DefaultKeyedValues.getIndex "
                     "(return -1 when the key is not found). Passing tests: testGetSeriesIndex (through the chain, an empty dataset "
                     "gives -1), testGetCategoryIndex (the sibling), CategoryToPieDatasetTests.testGetIndex (-1 for 'XX' among two "
                     "present keys) and DefaultKeyedValuesTests.testRemoveValue (-1 for a removed key among three present keys).",
 "ownership_tests": ["org.jfree.data.category.junit.DefaultIntervalCategoryDatasetTests::testGetSeriesIndex",
                     "org.jfree.data.category.junit.DefaultIntervalCategoryDatasetTests::testGetCategoryIndex",
                     "org.jfree.data.category.junit.CategoryToPieDatasetTests::testGetIndex",
                     "org.jfree.data.junit.DefaultKeyedValuesTests::testRemoveValue"],
 "compensating": {
   "chain": [
     {"file": AXYR, "old": "return SegmentedTimeline.positionOfKey(keys, key);",
      "new": "return keys.length == 0 ? -1 : SegmentedTimeline.positionOfKey(keys, key);",
      "why": "hop 4 answers an empty array of keys itself"},
     {"file": CP, "old": "return XYPlot.getKeyIndex(keys, key);",
      "new": "return XYPlot.getKeyIndex(keys, key) >= keys.length ? -1 : XYPlot.getKeyIndex(keys, key);",
      "why": "hop 2 maps an index at or past the end of the array to -1"},
     {"file": XYP, "old": "return AbstractXYItemRenderer.resolveKeyIndex(keys, key);",
      "new": "return keys.length == 1 ? (key.equals(keys[0]) ? 0 : -1) : AbstractXYItemRenderer.resolveKeyIndex(keys, key);",
      "why": "hop 3 answers an array of a single key itself"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts from `mr_lib.py preview Chart-16 org/jfree/data/category/DefaultIntervalCategoryDataset.java 5` "
               "with the instance seed 3208 (the draw excludes the facade's file, which is also the file of the other two allowed "
               "candidates), in draw order, none substituted: axis.ValueAxis (hop 1, 1659 lines; the smallest host), "
               "plot.CategoryPlot (hop 2, 3941), plot.XYPlot (hop 3, 4951), renderer.xy.AbstractXYItemRenderer (hop 4, 1753), "
               "axis.SegmentedTimeline (hop 5, gold, 1763). ValueAxis and AbstractXYItemRenderer are abstract, which does not affect "
               "a static method; all five are public top-level classes. Anchors from stageB_lib.pick_insertion_anchor with seed "
               "3208 + 100 + i, as mr3_spec.py inserts them: hop 1 after setRange (seed 3308), hop 2 after removeRangeMarker "
               "(3309), hop 3 after getQuadrantOrigin (3310), hop 4 after getBaseToolTipGenerator (3311), hop 5 after getSegment "
               "(3312, in the outer class SegmentedTimeline, before its inner classes). The facade calls hop 1 by its "
               "fully-qualified name; hop 1 imports plot.CategoryPlot, hop 2 calls XYPlot in its own package, hop 3 imports "
               "renderer.xy.AbstractXYItemRenderer, hop 4 imports axis.SegmentedTimeline. Comparable is java.lang.Comparable "
               "everywhere (SegmentedTimeline's inner class Segment implements it but declares no type of that name).",
}
