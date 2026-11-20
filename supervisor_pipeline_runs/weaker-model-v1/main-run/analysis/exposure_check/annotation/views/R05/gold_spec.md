# Run R05: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.jfree.chart.ChartPanel::removeOldItems`
- Gold file in the workspace: `source/org/jfree/chart/ChartPanel.java` (lines 812–825)
- Method the failing test calls (facade): `org.jfree.data.time.TimeSeries::removeAgedItems`
- Failing test: `org.jfree.data.time.junit.TimeSeriesTests::testRemoveAgedItems`
- Text removed from the gold (the omission): `long latest = series.getTimePeriod(count - 1).getSerialIndex();         if (latest - series.getTimePeriod(0).getSerialIndex() <= maximumAge) {             return;         }`
- The same place in the variant now reads: `long latest = series.getTimePeriod(count - 1).getSerialIndex();`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  812        public static void removeOldItems(TimeSeries series, List data,
  813                long maximumAge, boolean notify) {
  814            int count = series.getItemCount();
  815            if (count < 2) {
  816                return;
  817            }
  818 >>         long latest = series.getTimePeriod(count - 1).getSerialIndex();
  819            while (latest - series.getTimePeriod(0).getSerialIndex() > maximumAge) {
  820                data.remove(0);
  821            }
  822            if (notify) {
  823                series.fireSeriesChanged();
  824            }
  825        }
```
