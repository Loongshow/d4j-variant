# Run R39: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.ArrayUtils::concatWith`
- Gold file in the workspace: `src/main/java/org/apache/commons/lang3/ArrayUtils.java` (lines 2144–2154)
- Method the failing test calls (facade): `org.apache.commons.lang3.StringUtils::join`
- Failing test: `org.apache.commons.lang3.StringUtilsTest::testJoin_ArrayChar`
- Text removed from the gold (the omission): `if (item != null) {                 buf.append(item);             }`
- The same place in the variant now reads: `buf.append(item);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 2144        public static String concatWith(Object[] array, char separator, int startIndex, int endIndex, int capacity) {
 2145            final StringBuilder buf = new StringBuilder(capacity);
 2146            for (int i = startIndex; i < endIndex; i++) {
 2147                if (i > startIndex) {
 2148                    buf.append(separator);
 2149                }
 2150                final Object item = array[i];
 2151 >>             buf.append(item);
 2152            }
 2153            return buf.toString();
 2154        }
```
