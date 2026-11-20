# Run R17: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.ArrayUtils::replicate`
- Gold file in the workspace: `src/java/org/apache/commons/lang3/ArrayUtils.java` (lines 1124–1130)
- Method the failing test calls (facade): `org.apache.commons.lang3.StringUtils::repeat`
- Failing test: `org.apache.commons.lang3.StringUtilsTest::testRepeat_StringStringInt`
- Text removed from the gold (the omission): `System.arraycopy(source, 0, target, index, source.length);             index += source.length;         }`
- The same place in the variant now reads: `System.arraycopy(source, 0, target, index, source.length);         }`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1124        public static int replicate(char[] source, char[] target, int count) {
 1125            int index = 0;
 1126            for (int i = 0; i < count; i++) {
 1127 >>             System.arraycopy(source, 0, target, index, source.length);
 1128            }
 1129            return index;
 1130        }
```
