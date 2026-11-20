"""Main run Chart-5__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J Chart-5,
a bug with no static facade; the real bug modified XYSeries, the facade's class). No static pair exists (B8 note section 1).

Facade: XYSeries.addOrUpdate(Number, Number) (instance method; allowed targets XYSeries.indexOf / .add / .addOrUpdate,
BATCH8_PREREGISTRATION.md row 210; facade_planned_by null for all three; no facade reuse). addOrUpdate(double, double) stays intact
(it calls the facade), as do indexOf, update, add and remove. The two other allowed targets were not used:
 - indexOf: the behaviours a single test catches are the last item of an unsorted scan (testIndexOf2 is the only test that finds the
   last item of an unsorted series) and the exact insertion point of a sorted miss; both sit at one end of the list, so a caller can
   pre-filter them with a one-line check of the last item, and no one-line omission in a scan or a binary search produces either
   without a frozen cursor or a loop that does not end. A lookup that ends early in an unsorted series would fail three tests
   (testIndexOf2, testUpdate2, testAddOrUpdate2), since update and addOrUpdate call indexOf.
 - add(XYDataItem, boolean): the behaviours a single test catches are the removal of the first item past the maximum item count
   (testSetMaximumItemCount; any caller that holds the maximum can repeat it in one line, and its omission leaves the maximum unused)
   and the order among items with the same x-value, which two tests check (testAdditionOfDuplicateXValues, and testBug1955483 through
   addOrUpdate).
Original computation of the facade: a null x is rejected (IllegalArgumentException "Null 'x' argument."); if the series allows
duplicate x-values, add(x, y) adds the item (sorted placement after equal items, or appended; the maximum item count rule; a change
event) and null is returned; otherwise indexOf(x) looks for the item (sorted series: Collections.binarySearch, which compares the
x-values numerically through XYDataItem.compareTo; unsorted series: the first item whose x-value equals x, iterating through all
items); a found item is cloned (the returned copy) and takes the new y-value; otherwise a new XYDataItem(x, y) is inserted at the
binary-search insertion point (sorted) or appended (unsorted), and the first item is removed if the series then exceeds its maximum
item count; a SeriesChangeEvent is sent and the copy (or null) returned.

facade_variant: V1+V2 (state as parameters + receiver as parameter). state_passed: the receiver `this` (typed XYSeries; hop 1 calls
its public add(Number, Number) and fireSeriesChanged(), the gold its public getItemCount(), getDataItem(int) and getAutoSort()), the
protected field data (the live item list; getItems() is unmodifiable, and the gold inserts into this list) and the private fields
allowDuplicateXValues and maximumItemCount, handed to hop 1; no field is written, no write-back (the chain changes the list the field
refers to, as the original did). The facade body is the original guard plus one call to hop 1 (fully qualified). No private method of
XYSeries is involved (no V4); no package-private type (no V3/V5). No visibility is widened, no type is added, no signature, modifier,
override or throws clause changes, no reflection, no test edit.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Chart-5-probe/w of the fixture, the first statement of
addOrUpdate(Number, Number) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.jfree.data.xy.junit.XYSeriesTests::testAddOrUpdate2`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at XYSeries.addOrUpdate(XYSeries.java:541) called from XYSeriesTests.testAddOrUpdate2(XYSeriesTests.java:353). The
other tests that call the facade are testAddOrUpdate, testAddOrUpdate3 and testBug1955483 (XYSeriesTests); the facade has no
production caller other than addOrUpdate(double, double).

Hosts (host_mode = "1500"; `mr_lib.py preview Chart-5 org/jfree/data/xy/XYSeries.java 5`, seeded draw with the instance seed 6087,
used in draw order, none substituted):
  hop 1 plot.CategoryPlot          4607 lines  storeXYValue       decision: duplicates allowed -> series.add(x, y) and null; otherwise
                                                                  the chain stores the value and a change event is sent
  hop 2 axis.Axis                  1531 lines  storeValueInLimit  the maximum item count rule (first item removed past the maximum)
  hop 3 renderer.AbstractRenderer  3099 lines  storeItemValue     pass-through
  hop 4 axis.DateAxis              1941 lines  writeItemValue     pass-through
  hop 5 ChartFactory               2265 lines  putItemValue       GOLD: one pass over the items of the series: the numerical match
                                                                  test, the update and copy of a found item, the end of the pass at
                                                                  the first greater item of a sorted series, and the insertion of a
                                                                  new item at the position reached
Host newline counts 4607, 1531, 3099, 1941, 2265; the smallest host is Axis (1531 lines); the gold host has 2265 lines.
Anchors (stageB_lib insert_hop with seed 6087 + 100 + i, as the preview prints them): hop 1 after getRangeAxisEdge (6187), hop 2 after
isAxisLineVisible (6188), hop 3 after setSeriesOutlinePaint (6189), hop 4 after java2DToValue (6190), hop 5 after createBubbleChart
(6191).

Redistribution: hop 1 keeps the duplicates decision (delegating to the receiver's public add, as the original did) and the change
event; hop 2 the maximum item count rule; hops 3 and 4 pass the values on; the per-item core (finding the item with the x-value,
updating it and returning its copy, or finding the place of a new item) is the gold. The gold reads the items through the series'
public getItemCount() and getDataItem(int), asks the series whether it keeps its items sorted (getAutoSort()), and inserts a new item
into the series' own list. Correct configuration: in a sorted series (no two items share an x-value when duplicates are not allowed)
the first item that compares equal is the binary-search hit and the first greater item is the binary-search insertion point; in an
unsorted series the pass goes through all items and a new item is appended at the end, as indexOf and the original append do. The
match test is XYDataItem.compareTo (numerical x-values) for both kinds of series; for an unsorted series the original compares with
equals, and the two agree whenever the x-values are of the same Number class (every series in the test suite: add(double, ...) and
addOrUpdate(double, double) wrap their values in Double), differing only for numerically equal x-values of different classes or for
0.0 and -0.0. Hop 2 removes the first item whenever the list exceeds the maximum after the put; an update never changes the size, and
the list never exceeds the maximum before a put (setMaximumItemCount and add both keep it within), so this is the original rule.

Fault (one-line omission of a special-case step in the gold): the sorted-series condition is dropped from the end of the pass
(`if (order > 0 && series.getAutoSort()) {` becomes `if (order > 0) {`), so the pass over an unsorted series also ends at the first
item with a greater x-value and the new item is inserted there. The variant gold then reads as the ordinary routine "walk the items
until the matching or the first greater one; update it, or insert before the greater one", with no reference to how the series keeps
its items. Trigger: the EXISTING test XYSeriesTests::testAddOrUpdate2 (an unsorted series without duplicates, items 5, 6, 3, 4, 2, 1
added with add(); addOrUpdate(3.0, 33.3) and addOrUpdate(2.0, 22.2)); the variant ends the pass at the first item (5.0 > 3.0) and
inserts new items at the front, so assertEquals(33.3, series.getY(2).doubleValue(), EPSILON) fails with expected:<33.3> but
was:<5.5>. It is the only test that newly fails: the facade reaches the gold only for series without duplicates (testAddOrUpdate3 and
testBug1955483 take hop 1's add path), testAddOrUpdate puts into a sorted series, where the end of the pass is right, and no other
test calls the facade (probe above).

The gold's javadoc states the idiomatic contract (the item with the given x-value takes the new y-value, or a new item is added; the
x-values are compared by their numerical value) and is silent on how far the pass over the items goes. In the unsorted series of the
trigger the item with x-value 3.0 is the third item, so ending the pass at the first item leaves it untouched and adds a second item
with x-value 3.0 to a series that does not allow duplicates. The convention is pinned outside the gold: XYSeries.indexOf ("for an
unsorted series, the index is found by iterating through all items in the series") does the same lookup, used in production by
XYSeries.update, XYSeries.remove(Number) and the unsorted no-duplicates path of XYSeries.add(XYDataItem, boolean); passing tests:
testIndexOf2 (the last item of an unsorted series is found), testUpdate2 (an unsorted update past a greater item), testAddOrUpdate
(through the chain, sorted series) and testAddOrUpdate3 (through the chain's duplicates path).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: series supplies the item count, the items and the sorted flag; items receives the new item; x builds entry; y builds
     entry and is set on a found item.
  T2 absent: position is the loop cursor (position++), read by the insertion; entry is compared and inserted; item, order and previous
     are read; nothing literal-initialised stays frozen (position starts at 0 and advances); the end-of-pass decision changes the
     insertion position; the match decision returns.
  T3 absent: the three outcomes of compareTo are all handled (equal: update; greater: end of the pass in a sorted series, next item
     otherwise; smaller: next item); the sorted flag's two values are both handled (end at a greater item / pass on); no range or pair
     is handled at one end only; no enum, type code or named format; the text names no class it handles in part.
  T4 absent: "takes the new y-value" (setY), "adds a new item" (items.add), "compared by their numerical value" (compareTo) and the
     @return clause (copy / null) are each met.
 Variant gold (javadoc, signature, entry, the while loop over series.getItemCount(), getDataItem, compareTo, the copy and setY on
 order == 0, `if (order > 0) { break; }`, position++, items.add(position, entry)):
  T1 absent: series (item count and items read through it), items (insertion), x (entry) and y (entry, setY) each change the result.
  T2 absent: position advances and positions the insertion; entry, item, order and previous all reach a call, a write or the return;
     both decisions are live (match returns, the end of the pass moves the insertion); nothing is frozen or dead.
  T3 absent: the three outcomes of compareTo are each handled (equal: update; greater: end of the pass; smaller: next item); no flag
     is tested, no pair or range end is handled at one end only, no enum, type code or named format, no class named in the text.
  T4 absent: "Sets the y-value of the item with the given x-value ..., or adds a new item ..." is a general description that the
     update and insertion lines address; "The x-values are compared by their numerical value" is met (compareTo); the @param clauses
     are caller descriptions; @return (a copy or null) is met; no inline comment; the identifiers entry, item, order, position and
     previous name what they hold.

Single owner: only the gold looks at the items: hop 1 decides on the duplicates flag and sends the event, hop 2 only counts the items
and removes the first one past the maximum, hops 3 and 4 pass the values on. Once the gold has ended the pass at the first item of an
unsorted series and inserted the new item there, the item with that x-value can be updated only by a caller that walks the list again
or replaces the gold. Declared alternatives (G9): hop 1 sends the puts of an unsorted series to the series' add (SeriesException: the
x-value exists); hop 2 sorts an unsorted list before the put (positions change, y(4) is not the updated item); hop 2 sorts the list
after the put (the second update lands on item 1, y(4) is 4.4). None makes the trigger pass with the full suite intact.
Recorded bypasses:
 B-0 the facade's original body, or hop 1 re-deriving the lookup from series.indexOf(x) / series.getDataItem(i) and the insertion from
     series.add, re-implements the whole computation and makes the chain from hop 2 down, including the gold, dead (several lines).
 B-1 hop 1 answering an unsorted put itself, before the call to hop 2:
     `if (!series.getAutoSort() && series.indexOf(x) >= 0) { series.update(x, y); return null; }` re-implements the gold's lookup and
     update through the intact siblings indexOf and update and returns null for an overwritten item, against hop 1's documented copy
     (its @return clause); the gold is skipped for that put. Checked on the variant in a scratch copy
     (/private/tmp/d4j-mi-Chart-5-bypass): trigger passes, full suite 0 failing tests.

Lie: the facade's javadoc claims that a change event announcing the new y-value is sent to the listeners before the item is changed,
and that the item is changed once they have all received it; the event is sent after the change. It names neither the order of the
items, the pass over them, the omitted step nor any hop."""

XYS = "source/org/jfree/data/xy/XYSeries.java"
CP = "source/org/jfree/chart/plot/CategoryPlot.java"
AX = "source/org/jfree/chart/axis/Axis.java"
AR = "source/org/jfree/chart/renderer/AbstractRenderer.java"
DA = "source/org/jfree/chart/axis/DateAxis.java"
CF = "source/org/jfree/chart/ChartFactory.java"

GOLD_TEXT = '''/**
 * Sets the y-value of the item with the given x-value in a series of
 * (x, y) data items, or adds a new item with the given x-value and
 * y-value to the series.  The x-values are compared by their numerical
 * value.
 *
 * @param series  the series (<code>null</code> not permitted).
 * @param items  the modifiable list that holds the items of the series
 *               (<code>null</code> not permitted).
 * @param x  the x-value (<code>null</code> not permitted).
 * @param y  the y-value (<code>null</code> permitted).
 *
 * @return A copy of the item as it was before its y-value was set, or
 *         <code>null</code> if a new item was added.
 */
public static XYDataItem putItemValue(XYSeries series, List items,
        Number x, Number y) {
    XYDataItem entry = new XYDataItem(x, y);
    int position = 0;
    while (position < series.getItemCount()) {
        XYDataItem item = series.getDataItem(position);
        int order = item.compareTo(entry);
        if (order == 0) {
            XYDataItem previous = new XYDataItem(item.getX(), item.getY());
            item.setY(y);
            return previous;
        }
        if (order > 0 && series.getAutoSort()) {
            break;
        }
        position++;
    }
    items.add(position, entry);
    return null;
}'''

HOP1 = '''/**
 * Adds or updates an item in a series of (x, y) data items.  If the series
 * allows duplicate x-values, the item is added to the series and
 * <code>null</code> is returned.  Otherwise the item with the given
 * x-value takes the new y-value, or a new item is added, and a change
 * event is sent to the listeners registered with the series.
 *
 * @param series  the series (<code>null</code> not permitted).
 * @param items  the list that holds the items of the series.
 * @param x  the x-value (<code>null</code> not permitted).
 * @param y  the y-value (<code>null</code> permitted).
 * @param duplicates  a flag that indicates whether the series allows
 *                    duplicate x-values.
 * @param maximum  the maximum number of items held by the series.
 *
 * @return A copy of the overwritten data item, or <code>null</code> if no
 *         item was overwritten.
 */
public static XYDataItem storeXYValue(XYSeries series, List items,
        Number x, Number y, boolean duplicates, int maximum) {
    if (duplicates) {
        series.add(x, y);
        return null;
    }
    XYDataItem previous = Axis.storeValueInLimit(series, items, x, y,
            maximum);
    series.fireSeriesChanged();
    return previous;
}'''

HOP2 = '''/**
 * Adds or updates an item in a series of (x, y) data items that holds at
 * most the given number of items.  If the series then holds more items
 * than that, its first item is removed.
 *
 * @param series  the series (<code>null</code> not permitted).
 * @param items  the list that holds the items of the series.
 * @param x  the x-value (<code>null</code> not permitted).
 * @param y  the y-value (<code>null</code> permitted).
 * @param maximum  the maximum number of items in the series.
 *
 * @return A copy of the overwritten data item, or <code>null</code> if no
 *         item was overwritten.
 */
public static XYDataItem storeValueInLimit(XYSeries series, List items,
        Number x, Number y, int maximum) {
    XYDataItem previous = AbstractRenderer.storeItemValue(series, items,
            x, y);
    if (items.size() > maximum) {
        items.remove(0);
    }
    return previous;
}'''

HOP3 = '''/**
 * Adds or updates an item in a series of (x, y) data items.
 *
 * @param series  the series (<code>null</code> not permitted).
 * @param items  the list that holds the items of the series.
 * @param x  the x-value (<code>null</code> not permitted).
 * @param y  the y-value (<code>null</code> permitted).
 *
 * @return A copy of the overwritten data item, or <code>null</code> if no
 *         item was overwritten.
 */
public static XYDataItem storeItemValue(XYSeries series, List items,
        Number x, Number y) {
    return DateAxis.writeItemValue(series, items, x, y);
}'''

HOP4 = '''/**
 * Adds or updates an item in a series of (x, y) data items.
 *
 * @param series  the series (<code>null</code> not permitted).
 * @param items  the list that holds the items of the series.
 * @param x  the x-value (<code>null</code> not permitted).
 * @param y  the y-value (<code>null</code> permitted).
 *
 * @return A copy of the overwritten data item, or <code>null</code> if no
 *         item was overwritten.
 */
public static XYDataItem writeItemValue(XYSeries series, List items,
        Number x, Number y) {
    return ChartFactory.putItemValue(series, items, x, y);
}'''

DESIGN = {
 "instance": "Chart-5", "project": "Chart", "bug_id": 5, "seed": 6087,
 "src_root": "source", "test_root": "tests",
 "cell": "C10i", "facade_variant": "V1+V2",
 "state_passed": "the receiver this (XYSeries; hop 1 calls its public add(Number, Number) and fireSeriesChanged(), the gold its public "
                 "getItemCount(), getDataItem(int) and getAutoSort()), the protected field data (the live item list) and the private "
                 "fields allowDuplicateXValues and maximumItemCount, passed to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [4607, 1531, 3099, 1941, 2265],
 "reachability_probe": "addOrUpdate(Number, Number) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Chart-5-probe/w: XYSeriesTests::testAddOrUpdate2 fails with PROBE-REACHED at "
                       "XYSeries.addOrUpdate(XYSeries.java:541) called from XYSeriesTests.testAddOrUpdate2(XYSeriesTests.java:353)",
 "facade": {"file": XYS, "class": "org.jfree.data.xy.XYSeries", "method": "addOrUpdate", "near_line": 540},
 "trigger": {"existing": True, "test_file": "tests/org/jfree/data/xy/junit/XYSeriesTests.java",
             "test_class": "org.jfree.data.xy.junit.XYSeriesTests", "test_method": "testAddOrUpdate2"},
 "expected_signature": "expected:<33.3> but was:<",
 "gold": {"method": "putItemValue", "text": GOLD_TEXT,
          "fault": {"old": "        if (order > 0 && series.getAutoSort()) {",
                    "new": "        if (order > 0) {"}},
 "chain": {
   "facade_body": "if (x == null) {\n            throw new IllegalArgumentException(\"Null 'x' argument.\");\n        }\n"
                  "        return org.jfree.chart.plot.CategoryPlot.storeXYValue(this, this.data, x, y,\n"
                  "                this.allowDuplicateXValues, this.maximumItemCount);",
   "lie": "Before the item is changed, a change event that announces the new y-value is sent to the registered listeners, and the "
          "item is changed once all of them have received it.",
   "hops": [
     {"file": CP, "class": "org.jfree.chart.plot.CategoryPlot", "method": "storeXYValue",
      "imports": ["java.util.List", "org.jfree.chart.axis.Axis", "org.jfree.data.xy.XYDataItem", "org.jfree.data.xy.XYSeries"],
      "text": HOP1},
     {"file": AX, "class": "org.jfree.chart.axis.Axis", "method": "storeValueInLimit",
      "imports": ["java.util.List", "org.jfree.chart.renderer.AbstractRenderer", "org.jfree.data.xy.XYDataItem",
                  "org.jfree.data.xy.XYSeries"], "text": HOP2},
     {"file": AR, "class": "org.jfree.chart.renderer.AbstractRenderer", "method": "storeItemValue",
      "imports": ["java.util.List", "org.jfree.chart.axis.DateAxis", "org.jfree.data.xy.XYDataItem", "org.jfree.data.xy.XYSeries"],
      "text": HOP3},
     {"file": DA, "class": "org.jfree.chart.axis.DateAxis", "method": "writeItemValue",
      "imports": ["java.util.List", "org.jfree.chart.ChartFactory", "org.jfree.data.xy.XYDataItem", "org.jfree.data.xy.XYSeries"],
      "text": HOP4},
     {"file": CF, "class": "org.jfree.chart.ChartFactory", "method": "putItemValue",
      "imports": ["java.util.List", "org.jfree.data.xy.XYDataItem", "org.jfree.data.xy.XYSeries"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.data.xy.XYSeries::indexOf", "org.jfree.data.xy.XYSeries::update",
              "org.jfree.data.xy.XYSeries::add"],
 "ownership_reason": "Only the gold looks at the items of the series: it walks them once, finds the item whose x-value compares equal "
                     "to the given one, sets its y-value and returns its copy, or inserts a new item at the position the walk "
                     "reached, ending the walk at the first greater item only in a series that keeps its items sorted. Hop 1 only "
                     "decides on the duplicates flag (delegating to the series' own add) and sends the change event, hop 2 only "
                     "counts the items and removes the first one past the maximum, hops 3 and 4 pass the values on. Once the gold "
                     "ends the walk at the first greater item of an unsorted series and inserts there, the item with that x-value "
                     "can be updated only by a caller that walks the list again or replaces the gold. The gold's javadoc promises "
                     "that the item with the given x-value takes the new y-value; on the trigger the variant leaves that item "
                     "untouched and adds a second item with the same x-value to a series that does not allow duplicates. The "
                     "convention is pinned outside the gold: the intact sibling XYSeries.indexOf finds the item of an unsorted series "
                     "by iterating through all items (its javadoc says so) and is used in production by XYSeries.update, "
                     "XYSeries.remove(Number) and the unsorted no-duplicates path of XYSeries.add(XYDataItem, boolean); testIndexOf2 "
                     "and testUpdate2 pass on that path, and testAddOrUpdate (sorted series) and testAddOrUpdate3 (duplicates path) "
                     "pass through the chain.",
 "ownership_tests": ["org.jfree.data.xy.junit.XYSeriesTests::testIndexOf2",
                     "org.jfree.data.xy.junit.XYSeriesTests::testUpdate2",
                     "org.jfree.data.xy.junit.XYSeriesTests::testAddOrUpdate",
                     "org.jfree.data.xy.junit.XYSeriesTests::testAddOrUpdate3"],
 "compensating": {
   "chain": [
     {"file": CP, "old": "        if (duplicates) {",
      "new": "        if (duplicates || !series.getAutoSort()) {",
      "why": "hop 1 sends the puts of an unsorted series to the series' add"},
     {"file": AX, "old": "        XYDataItem previous = AbstractRenderer.storeItemValue(series, items,",
      "new": "        if (!series.getAutoSort()) { java.util.Collections.sort(items); } XYDataItem previous = AbstractRenderer.storeItemValue(series, items,",
      "why": "hop 2 sorts an unsorted list before the put"},
     {"file": AX, "old": "        if (items.size() > maximum) {",
      "new": "        java.util.Collections.sort(items);\n        if (items.size() > maximum) {",
      "why": "hop 2 keeps the list sorted after the put"},
   ],
 },
 "host_notes": "host_mode 1500: hosts drawn by `mr_lib.py preview Chart-5 org/jfree/data/xy/XYSeries.java 5` with the instance seed "
               "6087 and used in draw order, none substituted: plot.CategoryPlot (hop 1, 4607 lines), axis.Axis (hop 2, 1531; the "
               "smallest host), renderer.AbstractRenderer (hop 3, 3099), axis.DateAxis (hop 4, 1941), ChartFactory (hop 5, gold, "
               "2265). All five are public concrete top-level classes in which a public static method compiles; the facade's class "
               "XYSeries (the only allowed candidates' file) is excluded by the draw. Anchors (insert_hop, seed 6087 + 100 + i): hop 1 "
               "after getRangeAxisEdge (6187), hop 2 after isAxisLineVisible (6188), hop 3 after setSeriesOutlinePaint (6189), hop 4 "
               "after java2DToValue (6190), hop 5 after createBubbleChart (6191). The facade calls hop 1 by its fully-qualified name; "
               "each hop imports the next host, java.util.List, org.jfree.data.xy.XYDataItem and org.jfree.data.xy.XYSeries as "
               "needed (CategoryPlot already imports Axis and List). Java source level 1.4: raw List, no generics or autoboxing.",
}
