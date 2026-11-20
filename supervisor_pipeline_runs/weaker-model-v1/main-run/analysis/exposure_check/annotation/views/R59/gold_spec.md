# Run R59: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.jfree.chart.ChartFactory::putItemValue`
- Gold file in the workspace: `source/org/jfree/chart/ChartFactory.java` (lines 2092–2111)
- Method the failing test calls (facade): `org.jfree.data.xy.XYSeries::addOrUpdate`
- Failing test: `org.jfree.data.xy.junit.XYSeriesTests::testAddOrUpdate2`
- Text removed from the gold (the omission): `if (order > 0 && series.getAutoSort()) {`
- The same place in the variant now reads: `if (order > 0) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 2092        public static XYDataItem putItemValue(XYSeries series, List items,
 2093                Number x, Number y) {
 2094            XYDataItem entry = new XYDataItem(x, y);
 2095            int position = 0;
 2096            while (position < series.getItemCount()) {
 2097                XYDataItem item = series.getDataItem(position);
 2098                int order = item.compareTo(entry);
 2099                if (order == 0) {
 2100                    XYDataItem previous = new XYDataItem(item.getX(), item.getY());
 2101                    item.setY(y);
 2102                    return previous;
 2103                }
 2104 >>             if (order > 0) {
 2105                    break;
 2106                }
 2107                position++;
 2108            }
 2109            items.add(position, entry);
 2110            return null;
 2111        }
```
