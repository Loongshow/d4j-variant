# Run R29: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.time.DateUtils::locateLargest`
- Gold file in the workspace: `src/main/java/org/apache/commons/lang3/time/DateUtils.java` (lines 366–375)
- Method the failing test calls (facade): `org.apache.commons.lang3.math.NumberUtils::max`
- Failing test: `org.apache.commons.lang3.math.NumberUtilsTest::testMaxLong`
- Text removed from the gold (the omission): `if (array[i] > largest) {                 largest = array[i];                 index = i;             }`
- The same place in the variant now reads: `if (array[i] > largest) {                 largest = array[i];             }`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  366        public static int locateLargest(long[] array, int startIndex, int endIndex) {
  367            int index = startIndex;
  368            long largest = array[startIndex];
  369            for (int i = startIndex + 1; i < endIndex; i++) {
  370 >>             if (array[i] > largest) {
  371 >>                 largest = array[i];
  372                }
  373            }
  374            return index;
  375        }
```
