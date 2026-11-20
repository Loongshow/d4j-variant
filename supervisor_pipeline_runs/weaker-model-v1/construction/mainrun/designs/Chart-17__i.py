"""Main run Chart-17__i (cell C10i, batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Chart-17; the real bug modified org.jfree.data.time.TimeSeries, the facade's class). No static pair (B8 note section 1: pool v2
found no strictly tested public static method in TimeSeries).

Facade: TimeSeries.removeAgedItems(boolean) (allowed instance target of BATCH9_PREREGISTRATION.md row 342, facade_planned_by
null; the 15-line overload whose own public calls are getItemCount, getTimePeriod and fireSeriesChanged, as the task record lists;
the overload removeAgedItems(long, boolean) stays intact and is the sibling pin below). The other allowed targets were not used:
TimeSeries.addOrUpdate is planned by Chart-9__i (distinctness preferred, B8 note section 3), and TimeSeries.delete is a single
index lookup plus one removal (nothing a five-hop chain could redistribute without leaving the per-element core empty).
Original computation of the facade: if the series has more than one item, latest = the serial index of the time period of the
last item; while latest minus the serial index of the first item's period exceeds the field maximumItemAge, the first item is
removed from the field data; if any item was removed and notify is true, fireSeriesChanged() is called. It is called with
notify = false by add(TimeSeriesDataItem, boolean) and addOrUpdate(RegularTimePeriod, Number), and with notify = true by
setMaximumItemAge(long).

facade_variant: V1+V2. state_passed: the receiver `this` (typed TimeSeries; the hops call only its public getItemCount(),
getTimePeriod(int) and fireSeriesChanged()), the protected field data (the List of TimeSeriesDataItem, from which the gold removes
the aged items in place; the field itself is never assigned), the private field maximumItemAge (long) and the parameter notify,
handed to hop 1; no write-back. The facade body is one call to hop 1 (the original has no argument guard; its item-count check
moves to hop 1). No visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no
reflection, no test edit. The facade calls no private method, so V4 does not apply.

Redistribution of the computation: hop 1 keeps the item-count check (series with fewer than two items are left as they are); hop 2
reads the reference, the serial index of the period of the last item; hops 3 and 4 pass the values on; the gold holds the
per-item core: it counts the leading items whose age (reference minus the serial index of their period) exceeds the maximum age,
removes them from the list in one block and notifies the listeners of the series.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Chart-17-probe of the fixture, the first
statement of removeAgedItems(boolean) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile
OK; `defects4j test -t org.jfree.data.time.junit.TimeSeriesTests::testRemoveAgedItems`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at TimeSeries.removeAgedItems(TimeSeries.java:736), reached from TimeSeries.add
(TimeSeries.java:540) in TimeSeriesTests.setUp; the test also calls the facade directly (removeAgedItems(true)) and through
setMaximumItemAge.

Hosts (host_mode = "1500"; the recipe's seeded draw `mr_lib.py preview Chart-17 org/jfree/data/time/TimeSeries.java 5`, seed 8760,
used in draw order, none substituted):
  hop 1 chart.renderer.AbstractRenderer          2730 lines  pruneHistory        plumbing: the item-count check
  hop 2 chart.plot.ThermometerPlot               1724 lines  pruneFromLatest     plumbing: the reference = serial index of the last period
  hop 3 chart.plot.SpiderWebPlot                 1652 lines  pruneOlderPeriods   pass-through
  hop 4 chart.renderer.xy.AbstractXYItemRenderer 1753 lines  pruneOlderItems     pass-through
  hop 5 chart.axis.DateAxis                      1813 lines  removeEarlyPeriods  GOLD: per item, the age test; block removal; notification
Host sizes 2730, 1724, 1652, 1753, 1813; the smallest host is SpiderWebPlot (1652 lines).
The correct configuration is behaviour-identical to the original: the same items are removed (a prefix of the ascending list, ending
at the first item within the maximum age; the last item has age 0 and is never removed since maximumItemAge >= 0), and the event is
sent exactly when the original sends it (at least one item removed and notify true).

Fault (one-line omission in the gold): the removal condition is dropped from the gold's notification decision
(`if (aged > 0 && notify) {` becomes `if (notify) {`), so the gold notifies the listeners of the series whenever notify is true, also
when no item was removed. The gold then reads as the ordinary routine "remove the old items; notify the listeners if asked to".
Trigger: the EXISTING test TimeSeriesTests::testRemoveAgedItems: with two items (1999, 2001) and maximum age 10, the listener flag is
cleared and setMaximumItemAge(2) is called (removeAgedItems(true): age 2 does not exceed 2, nothing is removed); the variant sends a
SeriesChangeEvent anyway and assertFalse(this.gotSeriesChangeEvent) fails (junit.framework.AssertionFailedError at
TimeSeriesTests.java:739). It is the only test that asks for notification (removeAgedItems(true) or setMaximumItemAge) on a series of
two or more items with a registered listener whose flag it then checks; add() and addOrUpdate() pass notify = false, and gate G5 checks
the full suite.

The gold's javadoc states the idiomatic contract (it removes the leading items older than the maximum age and, if notify is true,
notifies the listeners of the series, i.e. calls Series.fireSeriesChanged(), documented as "signalling to registered listeners that the
series has been changed"; a SeriesChangeEvent is "an event with details of a change to a series") and is silent on the case in which
nothing is removed. On the trigger input nothing is removed and the variant still signals a change. The convention is pinned outside
the gold: the intact sibling overload TimeSeries.removeAgedItems(long, boolean) does the same step (`if (removed && notify)
fireSeriesChanged()`), TimeSeries.delete(RegularTimePeriod) fires only when an item was found ("If there is no item with the specified
time period, this method does nothing"), TimeSeries.clear() fires only when the list was not empty, and the facade's own @param says an
event is sent "IF any items are removed". Passing tests: testRemoveAgedItems2 (the sibling overload: no event when nothing is removed),
testDelete2 (no event when the period is absent), testAddOrUpdate and testSetMaximumItemCount (series edits through add/addOrUpdate,
which reach the chain with notify = false).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: series receives the event; items supplies every period and loses the aged block; latest and maximumAge decide the age
     test; notify decides the event.
  T2 absent: count bounds the loop (computed before it, not frozen); aged is the loop counter, advanced in the loop, and is read by
     subList and the event decision; the event branch has an effect.
  T3 absent: no closed set is involved (one age test per item, one event); no class named in the gold's text is handled in part.
  T4 absent: 'at the start of a list whose time periods lie more than a number of periods before a reference period' is met by the
     loop and the block removal; the @param clauses are caller preconditions or descriptions met by the body.
 Variant gold (javadoc, signature, `int count`, the while loop, `items.subList(0, aged).clear()`, `if (notify)`, the event):
  T1 absent: series, items, latest, maximumAge and notify each change the effect; none is only argument-checked.
  T2 absent: aged advances in the loop and is read by subList (the removed block); count is a bound; the `if (notify)` decision decides
     whether the event is sent; no local is dead or frozen.
  T3 absent: the event decision tests the flag only; no set of siblings, pair halves or range ends is handled in part ('No member
     handled' for any no-change case); the age test is applied to every leading item.
  T4 absent: the summary sentence is met by the loop and the removal; '@param notify  notify the listeners of the series?' is met by
     `if (notify)`; no inline comment; the identifiers (count, aged, latest, maximumAge) name nothing the body does not meet.

Single owner: only the gold decides, per item, whether the item is older than the maximum age, removes the aged items and sends the
event; hop 1 only decides whether the series has enough items to age, hop 2 only reads the reference period, hops 3 and 4 pass the
values on. Once the gold has sent the event for an unchanged series, no caller can withdraw it. Declared alternatives (G9): hop 1 leaves
series of two items as they are; hop 2 takes the first period as the reference; hop 4 passes notify = false. None makes the trigger
pass.
Recorded bypasses (not declared, each replaces part of the gold's decision):
 B-0 the facade's original body (or any hop) removes the items and sends the event itself, discarding the chain from that point,
     including the gold.
 B-1 a hop pre-filters the flag with a second implementation of the gold's age test on the first item (hop 4:
     `DateAxis.removeEarlyPeriods(series, items, latest, maximumAge, notify && latest - series.getTimePeriod(0).getSerialIndex()
     > maximumAge);`), duplicating the gold's per-item decision above it.
 B-2 a hop calls the gold with notify = false and sends the event itself after comparing the item count before and after the call
     (more than one statement), taking the notification away from the gold.

Lie: the facade's javadoc claims the first item to keep is located by a binary search over the serial indices of the time periods; no
step of the chain searches (hop 5 scans the leading items one by one). It names neither the notification nor any hop."""

TS = "source/org/jfree/data/time/TimeSeries.java"
AR = "source/org/jfree/chart/renderer/AbstractRenderer.java"
TP = "source/org/jfree/chart/plot/ThermometerPlot.java"
SW = "source/org/jfree/chart/plot/SpiderWebPlot.java"
AX = "source/org/jfree/chart/renderer/xy/AbstractXYItemRenderer.java"
DA = "source/org/jfree/chart/axis/DateAxis.java"

GOLD_TEXT = '''/**
 * Removes the data items at the start of a list whose time periods lie
 * more than a number of periods before a reference period.
 *
 * @param series  the series that holds the items (<code>null</code> not
 *                permitted).
 * @param items  the data items of the series, in ascending order of time
 *               period (<code>null</code> not permitted).
 * @param latest  the serial index of the reference period.
 * @param maximumAge  the maximum age of an item, in time periods.
 * @param notify  notify the listeners of the series?
 */
public static void removeEarlyPeriods(TimeSeries series, List items,
        long latest, long maximumAge, boolean notify) {
    int count = items.size();
    int aged = 0;
    while (aged < count && latest - ((TimeSeriesDataItem) items.get(
            aged)).getPeriod().getSerialIndex() > maximumAge) {
        aged++;
    }
    items.subList(0, aged).clear();
    if (aged > 0 && notify) {
        series.fireSeriesChanged();
    }
}'''

HOP1 = '''/**
 * Removes the oldest data items from a time series, so that the time
 * periods of the remaining items lie within a maximum age of the period of
 * the last item.
 *
 * @param series  the series (<code>null</code> not permitted).
 * @param items  the data items of the series (<code>null</code> not
 *               permitted).
 * @param maximumAge  the maximum age, in time periods.
 * @param notify  notify the listeners of the series?
 */
public static void pruneHistory(TimeSeries series, List items,
        long maximumAge, boolean notify) {
    if (series.getItemCount() > 1) {
        ThermometerPlot.pruneFromLatest(series, items, maximumAge, notify);
    }
}'''

HOP2 = '''/**
 * Removes the data items of a time series whose time periods lie more than
 * a maximum age before the period of the last item.
 *
 * @param series  the series, with at least one item (<code>null</code> not
 *                permitted).
 * @param items  the data items of the series (<code>null</code> not
 *               permitted).
 * @param maximumAge  the maximum age, in time periods.
 * @param notify  notify the listeners of the series?
 */
public static void pruneFromLatest(TimeSeries series, List items,
        long maximumAge, boolean notify) {
    long latest = series.getTimePeriod(
            series.getItemCount() - 1).getSerialIndex();
    SpiderWebPlot.pruneOlderPeriods(series, items, latest, maximumAge,
            notify);
}'''

HOP3 = '''/**
 * Removes the data items of a time series whose time periods lie more than
 * a maximum age before a reference period.
 *
 * @param series  the series (<code>null</code> not permitted).
 * @param items  the data items of the series (<code>null</code> not
 *               permitted).
 * @param latest  the serial index of the reference period.
 * @param maximumAge  the maximum age, in time periods.
 * @param notify  notify the listeners of the series?
 */
public static void pruneOlderPeriods(TimeSeries series, List items,
        long latest, long maximumAge, boolean notify) {
    AbstractXYItemRenderer.pruneOlderItems(series, items, latest,
            maximumAge, notify);
}'''

HOP4 = '''/**
 * Removes the data items of a time series whose time periods lie more than
 * a maximum age before a reference period.
 *
 * @param series  the series (<code>null</code> not permitted).
 * @param items  the data items of the series (<code>null</code> not
 *               permitted).
 * @param latest  the serial index of the reference period.
 * @param maximumAge  the maximum age, in time periods.
 * @param notify  notify the listeners of the series?
 */
public static void pruneOlderItems(TimeSeries series, List items,
        long latest, long maximumAge, boolean notify) {
    DateAxis.removeEarlyPeriods(series, items, latest, maximumAge, notify);
}'''

DESIGN = {
 "instance": "Chart-17", "project": "Chart", "bug_id": 17, "seed": 8760,
 "src_root": "source", "test_root": "tests",
 "cell": "C10i", "facade_variant": "V1+V2",
 "state_passed": "the receiver this (TimeSeries; public getItemCount/getTimePeriod/fireSeriesChanged only), the protected field data "
                 "(List, items removed in place by the gold; the field is never assigned), the private field maximumItemAge and the "
                 "parameter notify, passed to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [2730, 1724, 1652, 1753, 1813],
 "reachability_probe": "removeAgedItems(boolean) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Chart-17-probe: TimeSeriesTests::testRemoveAgedItems fails with PROBE-REACHED at "
                       "TimeSeries.removeAgedItems(TimeSeries.java:736)",
 "facade": {"file": TS, "class": "org.jfree.data.time.TimeSeries", "method": "removeAgedItems", "near_line": 735},
 "trigger": {"existing": True, "test_file": "tests/org/jfree/data/time/junit/TimeSeriesTests.java",
             "test_class": "org.jfree.data.time.junit.TimeSeriesTests", "test_method": "testRemoveAgedItems"},
 "expected_signature": "TimeSeriesTests.testRemoveAgedItems(TimeSeriesTests.java:739)",
 "gold": {"method": "removeEarlyPeriods", "text": GOLD_TEXT,
          "fault": {"old": "        if (aged > 0 && notify) {\n            series.fireSeriesChanged();",
                    "new": "        if (notify) {\n            series.fireSeriesChanged();"}},
 "chain": {
   "facade_body": "org.jfree.chart.renderer.AbstractRenderer.pruneHistory(this, this.data,\n"
                  "                this.maximumItemAge, notify);",
   "lie": "The first item to keep is located by a binary search over the serial indices of the time periods.",
   "hops": [
     {"file": AR, "class": "org.jfree.chart.renderer.AbstractRenderer", "method": "pruneHistory",
      "imports": ["java.util.List", "org.jfree.chart.plot.ThermometerPlot", "org.jfree.data.time.TimeSeries"], "text": HOP1},
     {"file": TP, "class": "org.jfree.chart.plot.ThermometerPlot", "method": "pruneFromLatest",
      "imports": ["java.util.List", "org.jfree.data.time.TimeSeries"], "text": HOP2},
     {"file": SW, "class": "org.jfree.chart.plot.SpiderWebPlot", "method": "pruneOlderPeriods",
      "imports": ["java.util.List", "org.jfree.chart.renderer.xy.AbstractXYItemRenderer", "org.jfree.data.time.TimeSeries"],
      "text": HOP3},
     {"file": AX, "class": "org.jfree.chart.renderer.xy.AbstractXYItemRenderer", "method": "pruneOlderItems",
      "imports": ["java.util.List", "org.jfree.chart.axis.DateAxis", "org.jfree.data.time.TimeSeries"], "text": HOP4},
     {"file": DA, "class": "org.jfree.chart.axis.DateAxis", "method": "removeEarlyPeriods",
      "imports": ["java.util.List", "org.jfree.data.time.TimeSeries", "org.jfree.data.time.TimeSeriesDataItem"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.data.time.TimeSeries::removeAgedItems",
              "org.jfree.data.time.TimeSeries::delete",
              "org.jfree.data.time.TimeSeries::clear",
              "org.jfree.data.general.Series::fireSeriesChanged"],
 "ownership_reason": "Only the gold decides, for each leading item, whether its time period lies more than the maximum age before "
                     "the reference period, removes those items and notifies the listeners of the series. Hop 1 only checks that "
                     "the series has more than one item, hop 2 only reads the serial index of the last period, hops 3 and 4 pass the "
                     "values on. Once the gold has sent the event for a series it left unchanged, no caller can withdraw it. The "
                     "gold notifies through Series.fireSeriesChanged(), documented as signalling to the listeners that the series "
                     "has been changed (a SeriesChangeEvent is an event with details of a change to a series); the variant sends "
                     "that signal when no item was removed. The convention is pinned outside the gold: the intact sibling overload "
                     "TimeSeries.removeAgedItems(long, boolean) does the same step (`if (removed && notify) fireSeriesChanged()`), "
                     "TimeSeries.delete(RegularTimePeriod) fires only when the period is present and TimeSeries.clear() only when the "
                     "series is not empty, and the facade's own @param notify says the event is sent IF any items are removed; "
                     "testRemoveAgedItems2 (the sibling: no event when nothing is removed) and testDelete2 (no event for an absent "
                     "period) pass, as do testAddOrUpdate and testSetMaximumItemCount, whose edits reach the chain with "
                     "notify = false.",
 "ownership_tests": ["org.jfree.data.time.junit.TimeSeriesTests::testRemoveAgedItems2",
                     "org.jfree.data.time.junit.TimeSeriesTests::testDelete2",
                     "org.jfree.data.time.junit.TimeSeriesTests::testAddOrUpdate",
                     "org.jfree.data.time.junit.TimeSeriesTests::testSetMaximumItemCount"],
 "compensating": {
   "chain": [
     {"file": AR, "old": "    if (series.getItemCount() > 1) {",
      "new": "    if (series.getItemCount() > 2) {",
      "why": "hop 1 leaves series of two items as they are"},
     {"file": TP, "old": "            series.getItemCount() - 1).getSerialIndex();",
      "new": "            0).getSerialIndex();",
      "why": "hop 2 takes the period of the first item as the reference"},
     {"file": AX, "old": "    DateAxis.removeEarlyPeriods(series, items, latest, maximumAge, notify);",
      "new": "    DateAxis.removeEarlyPeriods(series, items, latest, maximumAge, false);",
      "why": "hop 4 asks the next step not to notify"},
   ],
 },
 "host_notes": "host_mode 1500: hosts from the recipe's seeded draw (mr_lib.py preview Chart-17 org/jfree/data/time/TimeSeries.java 5, "
               "seed 8760; the facade's file TimeSeries.java, 1037 lines, is not in the pool), used in draw order, none substituted: "
               "chart.renderer.AbstractRenderer (hop 1, 2730 lines, anchor after getSeriesVisible, seed 8860), chart.plot.ThermometerPlot "
               "(hop 2, 1724, after zoomRangeAxes, 8861), chart.plot.SpiderWebPlot (hop 3, 1652, after setToolTipGenerator, 8862; the "
               "smallest host), chart.renderer.xy.AbstractXYItemRenderer (hop 4, 1753, after getURLGenerator, 8863), chart.axis.DateAxis "
               "(hop 5, gold, 1813, after java2DToValue, 8864). All five are public top-level classes (two abstract) in which a public "
               "static method compiles. The facade calls hop 1 by its fully-qualified name; each hop imports java.util.List, "
               "org.jfree.data.time.TimeSeries and the next host (ThermometerPlot and SpiderWebPlot share a package); the gold imports "
               "TimeSeriesDataItem.",
}
