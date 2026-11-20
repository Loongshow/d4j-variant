# Run R43: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.jfree.chart.axis.SegmentedTimeline::positionOfKey`
- Gold file in the workspace: `source/org/jfree/chart/axis/SegmentedTimeline.java` (lines 1075–1083)
- Method the failing test calls (facade): `org.jfree.data.category.DefaultIntervalCategoryDataset::getSeriesIndex`
- Failing test: `org.jfree.data.category.junit.DefaultIntervalCategoryDatasetTests::testGetValue`
- Text removed from the gold (the omission): `found = key.equals(keys[index]);         }         if (!found) {             index = -1;         }         return index;`
- The same place in the variant now reads: `found = key.equals(keys[index]);         }         return index;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1075        public static int positionOfKey(Comparable[] keys, Comparable key) {
 1076            int index = -1;
 1077            boolean found = false;
 1078            while (!found && index < keys.length - 1) {
 1079                index++;
 1080 >>             found = key.equals(keys[index]);
 1081            }
 1082 >>         return index;
 1083        }
```
