# Run R33: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang.ArrayUtils::lowestValue`
- Gold file in the workspace: `src/java/org/apache/commons/lang/ArrayUtils.java` (lines 1944–1953)
- Method the failing test calls (facade): `org.apache.commons.lang.NumberUtils::minimum`
- Failing test: `org.apache.commons.lang.NumberUtilsTest::testMinimumLong`
- Text removed from the gold (the omission): `final long value = array[i];             if (i == startIndexInclusive || value < lowest) {                 lowest = value;`
- The same place in the variant now reads: `final long value = array[i];             if (value < lowest) {                 lowest = value;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1944        public static long lowestValue(long[] array, int startIndexInclusive, int endIndexExclusive) {
 1945            long lowest = 0;
 1946            for (int i = startIndexInclusive; i < endIndexExclusive; i++) {
 1947 >>             final long value = array[i];
 1948 >>             if (value < lowest) {
 1949 >>                 lowest = value;
 1950                }
 1951            }
 1952            return lowest;
 1953        }
```
