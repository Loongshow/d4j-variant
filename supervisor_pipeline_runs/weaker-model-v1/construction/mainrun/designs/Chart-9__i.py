"""Main run Chart-9__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Chart-9, revision 1083; the real bug modified org.jfree.data.time.TimeSeries, the facade's class). No static pair (B8 note
section 1: pool v2 no_tested_static); the task record's paired_* fields are null.

Facade: TimeSeries.removeAgedItems(boolean notify) (line 737; allowed candidate of BATCH9_PREREGISTRATION.md row 340,
facade_planned_by null, no facade reuse). The other two allowed candidates were not used:
 - TimeSeries.addOrUpdate(RegularTimePeriod, Number): its three existing tests (testAddOrUpdate, testClone2, testBug1075255) each see
   one step of it (the item-count limit on insertion, the value stored into the existing item, no second item for an existing
   period). Every one of these steps is a mutation that a hop above the gold, holding the same series, can redo after the gold
   returns in one line (trim the first item, set the value again, delete the second item), so no single owner; a quiet omission
   of the update decision also cannot be one line.
 - TimeSeries.delete(int start, int end) (8 lines: guard, removal loop, event): one removal loop; its tests (testDelete,
   testSetMaximumItemCount) leave no one-line omission that does not freeze the loop or leave a parameter unused.
Original computation of the facade: when the series has more than one item, latest = serial index of the last item's period; the
first item is removed while latest minus the serial index of the first item's period exceeds maximumItemAge; a SeriesChangeEvent
is sent only if at least one item was removed AND notify is true (the facade's javadoc: "notify controls whether or not a
SeriesChangeEvent is sent to registered listeners IF any items are removed").

facade_variant: V1+V2. The computation reads two fields (the protected list data, from which it removes, and the private long
maximumItemAge) and calls three public methods of the receiver (getItemCount, getTimePeriod, Series.fireSeriesChanged). The facade
passes the receiver `this` (typed TimeSeries, the declaring class; V2), the value of the field data (the java.util.List itself, so
the gold can remove from it; V1) and the value of maximumItemAge (V1), together with its own parameter notify, to hop 1; it writes
no field back (the original writes none). No private method is called (no V4), no package-private type is involved (no V3/V5).
No visibility change, no new type, no reflection, no signature/modifier/override/throws change, no test edit.
state_passed: receiver this (TimeSeries) + field values this.data (List) and this.maximumItemAge (long) + the parameter notify,
to hop 1; no write-back.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Chart-9-probe/w the first statement of
removeAgedItems(boolean) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t org.jfree.data.time.junit.TimeSeriesTests::testRemoveAgedItems`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at TimeSeries.removeAgedItems(TimeSeries.java:738) (reached through
TimeSeries.add, which calls removeAgedItems(false), and directly). Full suite with the probe: 28 failing tests, all with
PROBE-REACHED (every TimeSeries.add reaches the facade). The facade is reached by existing tests directly and in production code
(TimeSeries.add(TimeSeriesDataItem, boolean), TimeSeries.addOrUpdate, TimeSeries.setMaximumItemAge).

Hosts (host_mode = "1500"; mr_lib.py preview Chart-9 org/jfree/data/time/TimeSeries.java 5 with the instance seed 4325, used in draw
order, none substituted):
  hop 1 renderer.xy.AbstractXYItemRenderer 1786 lines  ageTimeSeries        pass-through
  hop 2 plot.SpiderWebPlot                 1652 lines  trimAgedItems        pass-through
  hop 3 JFreeChart                         1865 lines  discardAgedItems     pass-through
  hop 4 axis.ValueAxis                     1659 lines  pruneSeriesHistory   pass-through
  hop 5 ChartPanel                         2538 lines  removeOldItems       GOLD: the whole aging computation (fewer than two
                                                       items: nothing to do; latest serial index; nothing aged: nothing to do;
                                                       removal of the oldest items while the timespan exceeds the maximum age;
                                                       the event)
Host newline counts 1786, 1652, 1865, 1659, 2538; the smallest host is SpiderWebPlot (1652 lines); the gold host has 2538 lines.
The correct configuration is behaviour-identical to the original for every series: a series with fewer than two items is left
alone without an event; when the oldest item is not aged nothing is removed and no event is sent (original: removed stays false);
otherwise at least one item is removed and the event is sent iff notify (original: removed && notify).

Fault (one-line omission of a special-case decision in the gold): the "nothing is aged" early exit (`if (latest - <oldest serial>
<= maximumAge) { return; }`) is dropped. The removal loop is unchanged (its own test covers that case), so the items are aged
exactly as before, but a series of two or more items with nothing aged now sends a SeriesChangeEvent when notify is true: the
listeners are told of a change that did not happen. The gold then reads as the ordinary routine "fewer than two items: nothing to
do; remove the oldest items while the timespan exceeds the maximum age; notify listeners if asked".
Trigger: the EXISTING test TimeSeriesTests::testRemoveAgedItems. Its empty-series and one-item checks still hold (the count < 2
exit sends nothing); after setMaximumItemAge(10), add(2001) and the flag reset, setMaximumItemAge(2) calls removeAgedItems(true) on
[1999, 2001] (timespan 2, nothing aged): the variant keeps both items but sends an event, and assertFalse(this.gotSeriesChangeEvent)
at TimeSeriesTests.java:740 fails (junit.framework.AssertionFailedError). It is the only test that newly fails: the facade is
called with notify = true only by setMaximumItemAge and by direct calls; the only other tests doing so (testRemoveAgedItems2 on 0-
and 1-item series, testEquals on a 2-item series without a listener assertion) see no difference; TimeSeries.add and addOrUpdate
call it with notify = false, where nothing changes. The new hops have no other caller.

The gold's javadoc states the idiomatic contract (the oldest items are removed until the timespan from the oldest to the youngest
item is no more than the maximum age; "notify listeners?", the house phrase of TimeSeries.add(TimeSeriesDataItem, boolean)) and is
silent on when an event is due. The convention that a SeriesChangeEvent reports a change, and is not sent when nothing changed, is
pinned outside the gold: the facade's own javadoc (kept unchanged): "a SeriesChangeEvent is sent to registered listeners IF any
items are removed"; Series.fireSeriesChanged ("signalling to registered listeners that the series has been changed");
TimeSeries.removeAgedItems(long, boolean), the sibling overload (`if (removed && notify)`), with TimeSeriesTests::
testRemoveAgedItems2 (assertFalse after a call that removes nothing, passing); TimeSeries.delete(RegularTimePeriod) (event only when
the period exists) with TimeSeriesTests::testDelete2 (assertFalse after deleting an absent period, passing); TimeSeries.clear (event
only when the series was not empty).

Single owner: only the gold decides whether anything is aged and whether an event is sent; hops 1-4 pass the series, the list, the
maximum age and the flag along unchanged. One-line edits above the gold that keep the gold used as documented leave the trigger
failing, because the gold sends the event whenever it is asked to notify and the series has two or more items. Declared
alternatives (G9): hop 1 asks for an event only when the series has more than one item; hop 2 returns early for an empty list;
hop 3 widens the maximum age by one period. Each leaves the trigger failing.
Recorded bypasses (edits that replace a part of the gold's computation with another implementation, not repairs of the chain):
 B-1 a pre-filter at hop 4 (or any hop) that re-implements the gold's age comparison: `if (series.getItemCount() > 1 &&
     series.getTimePeriod(series.getItemCount() - 1).getSerialIndex() - series.getTimePeriod(0).getSerialIndex() <= maximumAge)
     { return; }` before the call. It recomputes, above the gold, the comparison the gold itself makes (its loop condition), so for
     the case it filters the gold's result is replaced by a second implementation of the gold's own aging rule.
 B-2 a hop calls the next hop with notify = false and sends the event itself when the list has become shorter (`int count =
     data.size();` before the call, `if (notify && data.size() < count) { series.fireSeriesChanged(); }` after it): the gold's
     notify parameter becomes dead and the event decision is re-implemented above it.
     B-1 and B-2 were each checked at hop 4 (ValueAxis.pruneSeriesHistory) on the variant in a scratch copy: trigger passes,
     full suite 0 failing tests.
 B-0 the facade's original body (re-implements the whole computation and makes the chain, including the gold, dead).

Lie: the facade's javadoc claims the aged items are first located by a binary search over the serial indices of their periods and
then removed together in a single step; the chain searches nothing (it compares the oldest remaining item with the latest one) and
removes the items one at a time from the front. It names neither events, the early exit, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: series gives the count, the serial indices and the event; data is removed from; maximumAge decides the early exit and
     the loop; notify decides the event; no parameter is only argument-checked.
  T2 absent: count is read by the guard and indexes the latest item; latest is read by the early exit and the loop condition (a
     value computed before the loop, not frozen); no literal-initialised local; every decision (count < 2, nothing aged, the loop,
     notify) changes the side effects.
  T3 absent: no enum, type code or named format; the two ends of the timespan (oldest, youngest) are both read in every comparison;
     no special values.
  T4 absent: 'removes the oldest items ... until the timespan from the oldest to the youngest item is no more than the given
     maximum age' is met by the loop; the @param clauses are caller preconditions ('null not permitted') or name no rule ('notify
     listeners?').
 Variant gold (javadoc, signature, count = series.getItemCount(), `if (count < 2) { return; }`, latest = serial index of item
 count - 1, `while (latest - <serial index of item 0> > maximumAge) { data.remove(0); }`, `if (notify) { series.fireSeriesChanged(); }`):
  T1 absent: series supplies the count, both serial indices and the event; data is removed from inside the loop; maximumAge bounds
     the loop; notify decides the event; none is read only in an argument check.
  T2 absent: count is read by the guard and gives the index of the latest item; latest is read by the loop condition (computed
     before the loop and only read in it, which the checklist excludes from 'frozen'); the loop advances by removing the first
     item and re-reading item 0 (no cursor, counter, flag or best-so-far that the loop fails to move); no literal-initialised local;
     the guard returns before any read of item count - 1 and before the event, the loop removes, the notify test sends the event.
  T3 absent: both ends of the timespan (the oldest item 0 and the youngest item count - 1) enter the comparison; no enum, type code,
     format or named class; the only early exit is the count < 2 guard, with no sibling set; no member of a closed set is handled
     while another is left out.
  T4 absent: 'Removes the oldest items from a time series until the timespan from the oldest to the youngest item is no more than
     the given maximum age' is met by the loop (a series of fewer than two items has a timespan of zero); '@param series the time
     series (<code>null</code> not permitted)' is a caller precondition; '@param data the list of data items in the series' and
     '@param maximumAge the maximum item age (in time periods)' name what is passed; '@param notify notify listeners?' names no
     rule; no inline comment; the identifiers count, latest and removeOldItems name what they hold or do."""

TS = "source/org/jfree/data/time/TimeSeries.java"
H1 = "source/org/jfree/chart/renderer/xy/AbstractXYItemRenderer.java"
H2 = "source/org/jfree/chart/plot/SpiderWebPlot.java"
H3 = "source/org/jfree/chart/JFreeChart.java"
H4 = "source/org/jfree/chart/axis/ValueAxis.java"
H5 = "source/org/jfree/chart/ChartPanel.java"

GOLD_TEXT = '''/**
 * Removes the oldest items from a time series until the timespan from the
 * oldest to the youngest item is no more than the given maximum age.
 *
 * @param series  the time series (<code>null</code> not permitted).
 * @param data  the list of data items in the series.
 * @param maximumAge  the maximum item age (in time periods).
 * @param notify  notify listeners?
 */
public static void removeOldItems(TimeSeries series, List data,
        long maximumAge, boolean notify) {
    int count = series.getItemCount();
    if (count < 2) {
        return;
    }
    long latest = series.getTimePeriod(count - 1).getSerialIndex();
    if (latest - series.getTimePeriod(0).getSerialIndex() <= maximumAge) {
        return;
    }
    while (latest - series.getTimePeriod(0).getSerialIndex() > maximumAge) {
        data.remove(0);
    }
    if (notify) {
        series.fireSeriesChanged();
    }
}'''

HOP1 = '''/**
 * Ages the items in a time series: the oldest items are removed until the
 * timespan from the oldest to the youngest item does not exceed the given
 * maximum age.
 *
 * @param series  the time series (<code>null</code> not permitted).
 * @param data  the list of data items in the series.
 * @param maximumAge  the maximum item age (in time periods).
 * @param notify  notify listeners?
 */
public static void ageTimeSeries(TimeSeries series, List data,
        long maximumAge, boolean notify) {
    SpiderWebPlot.trimAgedItems(series, data, maximumAge, notify);
}'''

HOP2 = '''/**
 * Trims the aged items from a time series, so that the timespan from the
 * oldest to the youngest item is no more than the given maximum age.
 *
 * @param series  the time series (<code>null</code> not permitted).
 * @param data  the list of data items in the series.
 * @param maximumAge  the maximum item age (in time periods).
 * @param notify  notify listeners?
 */
public static void trimAgedItems(TimeSeries series, List data,
        long maximumAge, boolean notify) {
    JFreeChart.discardAgedItems(series, data, maximumAge, notify);
}'''

HOP3 = '''/**
 * Discards the aged items of a time series: the oldest items are removed
 * until the timespan from the oldest to the youngest item is no more than
 * the given maximum age.
 *
 * @param series  the time series (<code>null</code> not permitted).
 * @param data  the list of data items in the series.
 * @param maximumAge  the maximum item age (in time periods).
 * @param notify  notify listeners?
 */
public static void discardAgedItems(TimeSeries series, List data,
        long maximumAge, boolean notify) {
    ValueAxis.pruneSeriesHistory(series, data, maximumAge, notify);
}'''

HOP4 = '''/**
 * Prunes the history of a time series, removing the oldest items until the
 * timespan from the oldest to the youngest item is no more than the given
 * maximum age.
 *
 * @param series  the time series (<code>null</code> not permitted).
 * @param data  the list of data items in the series.
 * @param maximumAge  the maximum item age (in time periods).
 * @param notify  notify listeners?
 */
public static void pruneSeriesHistory(TimeSeries series, List data,
        long maximumAge, boolean notify) {
    ChartPanel.removeOldItems(series, data, maximumAge, notify);
}'''

DESIGN = {
 "instance": "Chart-9", "project": "Chart", "bug_id": 9, "seed": 4325,
 "src_root": "source", "test_root": "tests",
 "facade": {"file": TS, "class": "org.jfree.data.time.TimeSeries", "method": "removeAgedItems", "near_line": 737},
 "facade_variant": "V1+V2",
 "state_passed": "receiver this (TimeSeries) and the values of the fields data (java.util.List, removed from by the gold) and "
                 "maximumItemAge (long), with the parameter notify, to hop 1; no write-back",
 "reachability_probe": "testRemoveAgedItems fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "TimeSeries.removeAgedItems(TimeSeries.java:738); full suite with the probe: 28 failing tests, all "
                       "PROBE-REACHED (TimeSeries.add reaches the facade)",
 "host_mode": "1500",
 "trigger": {"existing": True, "test_file": "tests/org/jfree/data/time/junit/TimeSeriesTests.java",
             "test_class": "org.jfree.data.time.junit.TimeSeriesTests", "test_method": "testRemoveAgedItems"},
 "expected_signature": "TimeSeriesTests.testRemoveAgedItems(TimeSeriesTests.java:740)",
 "gold": {"method": "removeOldItems", "text": GOLD_TEXT,
          "fault": {"old": "        long latest = series.getTimePeriod(count - 1).getSerialIndex();\n"
                           "        if (latest - series.getTimePeriod(0).getSerialIndex() <= maximumAge) {\n"
                           "            return;\n"
                           "        }\n",
                    "new": "        long latest = series.getTimePeriod(count - 1).getSerialIndex();\n"}},
 "chain": {
   "facade_body": "org.jfree.chart.renderer.xy.AbstractXYItemRenderer.ageTimeSeries(this, this.data,\n"
                  "                this.maximumItemAge, notify);",
   "lie": "The aged items are first located by a binary search over the serial indices of their time periods, and are then "
          "removed together in a single step.",
   "hops": [
     {"file": H1, "class": "org.jfree.chart.renderer.xy.AbstractXYItemRenderer", "method": "ageTimeSeries",
      "imports": ["org.jfree.chart.plot.SpiderWebPlot", "org.jfree.data.time.TimeSeries"], "text": HOP1},
     {"file": H2, "class": "org.jfree.chart.plot.SpiderWebPlot", "method": "trimAgedItems",
      "imports": ["org.jfree.chart.JFreeChart", "org.jfree.data.time.TimeSeries"], "text": HOP2},
     {"file": H3, "class": "org.jfree.chart.JFreeChart", "method": "discardAgedItems",
      "imports": ["org.jfree.chart.axis.ValueAxis", "org.jfree.data.time.TimeSeries"], "text": HOP3},
     {"file": H4, "class": "org.jfree.chart.axis.ValueAxis", "method": "pruneSeriesHistory",
      "imports": ["org.jfree.chart.ChartPanel", "org.jfree.data.time.TimeSeries"], "text": HOP4},
     {"file": H5, "class": "org.jfree.chart.ChartPanel", "method": "removeOldItems",
      "imports": ["java.util.List", "org.jfree.data.time.TimeSeries"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.data.general.Series::fireSeriesChanged",
              "org.jfree.data.time.TimeSeries::delete",
              "org.jfree.data.time.TimeSeries::clear"],
 "ownership_reason": "Only the gold decides whether any item of the series is aged and whether a SeriesChangeEvent is sent; hops "
                     "1-4 pass the series, its data list, the maximum age and the notify flag along unchanged. On the trigger "
                     "input (two items, timespan 2, maximum age 2, notify true) nothing is aged and the series does not change, "
                     "yet the gold sends a SeriesChangeEvent, which reports a change. The convention that the event is sent only "
                     "when items were removed is pinned outside the gold: the facade's own javadoc ('a SeriesChangeEvent is sent "
                     "to registered listeners IF any items are removed'); Series.fireSeriesChanged ('signalling to registered "
                     "listeners that the series has been changed'); the sibling overload TimeSeries.removeAgedItems(long, "
                     "boolean) ('if (removed && notify)'), with TimeSeriesTests testRemoveAgedItems2 asserting no event after a "
                     "call that removes nothing; TimeSeries.delete(RegularTimePeriod), which sends the event only when the period "
                     "exists, with TimeSeriesTests testDelete2 asserting no event after deleting an absent period; TimeSeries.clear, "
                     "which sends it only for a non-empty series. No one-line change of the values passed above the gold restores "
                     "the behaviour: the gold notifies whenever it is asked to and the series has two or more items, and the "
                     "trigger needs an event on [1999, 2001] with maximum age 1 and none with maximum age 2.",
 "ownership_tests": ["org.jfree.data.time.junit.TimeSeriesTests::testRemoveAgedItems2",
                     "org.jfree.data.time.junit.TimeSeriesTests::testDelete2"],
 "compensating": {
   "chain": [
     {"file": H1, "old": "SpiderWebPlot.trimAgedItems(series, data, maximumAge, notify);",
      "new": "SpiderWebPlot.trimAgedItems(series, data, maximumAge, notify && series.getItemCount() > 1);",
      "why": "hop 1 asks for an event only when the series has more than one item"},
     {"file": H2, "old": "        JFreeChart.discardAgedItems(series, data, maximumAge, notify);",
      "new": "        if (data.isEmpty()) {\n            return;\n        }\n        JFreeChart.discardAgedItems(series, data, maximumAge, notify);",
      "why": "hop 2 returns early for an empty data list"},
     {"file": H3, "old": "ValueAxis.pruneSeriesHistory(series, data, maximumAge, notify);",
      "new": "ValueAxis.pruneSeriesHistory(series, data, maximumAge + 1, notify);",
      "why": "hop 3 counts the maximum age inclusively (one more period)"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts from mr_lib.py preview Chart-9 org/jfree/data/time/TimeSeries.java 5 with the instance seed "
               "4325 (the draw excludes the facade's file, which is the only allowed candidates' file), used in draw order, none "
               "substituted: renderer.xy.AbstractXYItemRenderer (hop 1, 1786 lines), plot.SpiderWebPlot (hop 2, 1652; the "
               "smallest host), JFreeChart (hop 3, 1865), axis.ValueAxis (hop 4, 1659), ChartPanel (hop 5, gold, 2538). All five "
               "are public top-level classes in which a static method compiles (AbstractXYItemRenderer and ValueAxis are "
               "abstract, which does not affect a static method). Anchors from stageB_lib.pick_insertion_anchor with seed 4325 + "
               "100 + i (as mr3_spec.py inserts them): hop 1 after `getBaseToolTipGenerator` (line idx 476, seed 4425), hop 2 "
               "after `getPlotType` (333, 4426), hop 3 after `draw` (1118, 4427), hop 4 after `setRangeWithMargins` (1306, "
               "4428), hop 5 after `getPopupMenu` (799, 4429). The facade calls hop 1 by its fully-qualified name; each hop "
               "imports the next host and org.jfree.data.time.TimeSeries (ChartPanel also java.util.List). The facade's class "
               "TimeSeries is not a host.",
}
